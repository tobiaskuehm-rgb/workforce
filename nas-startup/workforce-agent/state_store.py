"""Crash-recovery record for the agent, in SQLite.

Review finding G-001: the worker used to acknowledge a message first and work
on it afterwards. `poll_once()` only ever picks up DELIVERED messages, so a
process that died between the acknowledgement and the reply left the message
ACCEPTED, unanswered, and invisible to every later run. It was lost.

The order is now reversed - work, reply, then acknowledge - so a crash leaves
the message DELIVERED and the next run sees it again. That alone fixes the
loss, but it introduces a second question: a retry would call the model again,
and a model call costs money. This store answers that question. It records how
far each message got, so a retry resumes instead of restarting.

It is deliberately **not** an audit trail. The bus is the system of record for
messages, acknowledgements and their audit rows; this is local operational
state, and losing it costs at most one repeated model call.

States per message:

  IN_PROGRESS  claimed, model not yet answered
  REPLIED      the reply reached the bus; only the acknowledgement is missing
  DONE         acknowledged, nothing left to do
  EXHAUSTED    too many failed attempts; stop trying and say so

The same file also serves as the single-writer guard (G-002): claiming a
message is an atomic INSERT, so two workers sharing this volume cannot both
take the same message. Two workers with *separate* volumes still can - that
needs a claim at the bus API level, which is noted as remaining work.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MAX_ATTEMPTS = 3
# A message claimed but never finished - because the process died - becomes
# claimable again after this. Long enough that a slow model call is not stolen
# mid-flight, short enough that a crash is not stuck for a working day.
DEFAULT_LEASE_SECONDS = 1800

SCHEMA = """
CREATE TABLE IF NOT EXISTS message_state (
    message_id        TEXT PRIMARY KEY,
    state             TEXT NOT NULL,
    attempts          INTEGER NOT NULL DEFAULT 0,
    reply_message_id  TEXT,
    last_detail       TEXT,
    claimed_at        REAL NOT NULL,
    updated_at        REAL NOT NULL
);
"""


@dataclass(frozen=True)
class Claim:
    """What a worker is allowed to do with a message right now."""

    message_id: str
    state: str
    attempts: int
    reply_message_id: str | None = None

    @property
    def needs_model(self) -> bool:
        return self.state == "IN_PROGRESS"

    @property
    def needs_acknowledgement(self) -> bool:
        return self.state in {"IN_PROGRESS", "REPLIED", "EXHAUSTED"}


class AgentStateStore:
    def __init__(
        self,
        path: str | Path,
        *,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        clock=time.time,
    ) -> None:
        self.max_attempts = max_attempts
        self.lease_seconds = lease_seconds
        self.clock = clock
        self._connection = sqlite3.connect(str(path), isolation_level=None)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.executescript(SCHEMA)

    def close(self) -> None:
        self._connection.close()

    def claim(self, message_id: str) -> Claim | None:
        """Take the message, or return None if it is not ours to work on.

        None means: already finished, or held by another worker whose lease has
        not run out. Anything else returns what still has to happen.
        """
        now = self.clock()
        cursor = self._connection.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        try:
            row = cursor.execute(
                "SELECT state, attempts, reply_message_id, claimed_at "
                "FROM message_state WHERE message_id = ?",
                (message_id,),
            ).fetchone()

            if row is None:
                cursor.execute(
                    "INSERT INTO message_state "
                    "(message_id, state, attempts, claimed_at, updated_at) "
                    "VALUES (?, 'IN_PROGRESS', 1, ?, ?)",
                    (message_id, now, now),
                )
                cursor.execute("COMMIT")
                return Claim(message_id, "IN_PROGRESS", 1)

            state, attempts, reply_message_id, claimed_at = row

            if state == "DONE":
                cursor.execute("COMMIT")
                return None

            if state == "REPLIED":
                # The reply is already on the bus; only the acknowledgement is
                # missing. Resume there and do not pay for a second model call.
                cursor.execute("COMMIT")
                return Claim(message_id, "REPLIED", attempts, reply_message_id)

            if state == "EXHAUSTED":
                # Deliberately still claimable. The transition into EXHAUSTED
                # is consumed by whichever run triggers it; if that run dies
                # before its final notice is out, returning None here would
                # mean the notice never goes out at all and the message stays
                # DELIVERED in the bus forever - the G-001 class one step
                # further along. Recording the notice moves the row to REPLIED,
                # which is what actually ends the retries.
                cursor.execute("COMMIT")
                return Claim(message_id, "EXHAUSTED", attempts)

            # IN_PROGRESS: someone holds it. Only take it over once the lease
            # has run out, otherwise a slow model call would be duplicated.
            if now - claimed_at < self.lease_seconds:
                cursor.execute("COMMIT")
                return None

            attempts += 1
            if attempts > self.max_attempts:
                cursor.execute(
                    "UPDATE message_state SET state = 'EXHAUSTED', attempts = ?, "
                    "updated_at = ? WHERE message_id = ?",
                    (attempts, now, message_id),
                )
                cursor.execute("COMMIT")
                return Claim(message_id, "EXHAUSTED", attempts)

            cursor.execute(
                "UPDATE message_state SET attempts = ?, claimed_at = ?, "
                "updated_at = ? WHERE message_id = ?",
                (attempts, now, now, message_id),
            )
            cursor.execute("COMMIT")
            return Claim(message_id, "IN_PROGRESS", attempts)
        except Exception:
            cursor.execute("ROLLBACK")
            raise

    def record_reply(self, message_id: str, reply_message_id: str) -> None:
        now = self.clock()
        self._connection.execute(
            "UPDATE message_state SET state = 'REPLIED', reply_message_id = ?, "
            "updated_at = ? WHERE message_id = ?",
            (reply_message_id, now, message_id),
        )

    def record_done(self, message_id: str) -> None:
        now = self.clock()
        self._connection.execute(
            "UPDATE message_state SET state = 'DONE', updated_at = ? "
            "WHERE message_id = ?",
            (now, message_id),
        )

    def release_untouched(self, message_id: str) -> bool:
        """Give a claim back without charging an attempt (review finding G-082).

        For the one case in which a run stops *after* claiming and *before*
        anything durable happened: the provider budget could not be reserved.
        No model was asked, no reply exists, so there is nothing to protect
        and nothing the message did wrong - holding the claim would make the
        next run report it as a duplicate for the length of the lease, and
        every expired lease would cost it an attempt it never used.

        One statement, hence atomic; guarded on the state so it can never
        touch a REPLIED or DONE row. Returns whether a row was released.
        """
        now = self.clock()
        cursor = self._connection.execute(
            "UPDATE message_state SET claimed_at = 0, attempts = attempts - 1, "
            "updated_at = ? WHERE message_id = ? AND state = 'IN_PROGRESS' "
            "AND reply_message_id IS NULL AND attempts > 0",
            (now, message_id),
        )
        return cursor.rowcount == 1

    def record_failure(self, message_id: str, detail: str) -> None:
        """Leave the message claimable again, with the reason recorded."""
        now = self.clock()
        self._connection.execute(
            "UPDATE message_state SET last_detail = ?, claimed_at = 0, "
            "updated_at = ? WHERE message_id = ?",
            (detail[:200], now, message_id),
        )

    def snapshot(self) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            "SELECT message_id, state, attempts, reply_message_id, last_detail "
            "FROM message_state ORDER BY updated_at"
        ).fetchall()
        return [
            {
                "message_id": r[0],
                "state": r[1],
                "attempts": r[2],
                "reply_message_id": r[3],
                "last_detail": r[4],
            }
            for r in rows
        ]
