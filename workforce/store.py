"""The one state: messages, claims, budget, audit - a single SQLite file.

A process that dies leaves nothing another store would need to know. The
audit is a hash chain: every row hashes the previous one, so a changed or
removed row is detectable from the file alone. Audit rows carry identifiers,
sizes and codes - never message text.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    direction TEXT NOT NULL CHECK (direction IN ('IN', 'OUT')),
    kind TEXT NOT NULL CHECK (kind IN ('MESSAGE', 'REPLY', 'NOTICE')),
    update_id INTEGER UNIQUE,
    chat_id INTEGER NOT NULL,
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    text TEXT NOT NULL,
    status TEXT NOT NULL,
    reply_to TEXT,
    external_id TEXT,
    refusal TEXT,
    claimed_at REAL NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    actor TEXT NOT NULL,
    request_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    record_key TEXT NOT NULL,
    payload TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS budget_days (
    day TEXT PRIMARY KEY,
    calls INTEGER NOT NULL DEFAULT 0,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    usd REAL NOT NULL DEFAULT 0
);
"""
GENESIS = "0" * 64


def _canonical(row: Dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class Store:
    def __init__(self, path: str, *, clock: Callable[[], float] = time.time) -> None:
        self.path = path
        self.clock = clock
        self._db = sqlite3.connect(path, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.executescript(SCHEMA)
        self._db.execute("PRAGMA user_version=1")
        if path != ":memory:":
            os.chmod(path, 0o600)

    def close(self) -> None:
        self._db.close()

    # -- settings: the kill switch and the Telegram offset ---------------------
    def setting(self, key: str, default: str) -> str:
        row = self._db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return default if row is None else str(row["value"])

    def set_setting(self, key: str, value: str) -> None:
        self._db.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                         "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))

    def channel(self) -> str:
        return self.setting("channel", "DISABLED")  # fail closed: a fresh file answers nobody

    def set_channel(self, value: str, *, actor: str, request_id: str) -> None:
        if value not in ("DISABLED", "ACTIVE"):
            raise ValueError("CHANNEL_STATE_UNKNOWN")
        # The switch and its evidence are one fact. A crash or failed audit may
        # leave both old, never an unaudited active channel.
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            self._db.execute(
                "INSERT INTO settings (key, value) VALUES ('channel', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (value,))
            self._append_audit(actor, request_id, "CHANNEL", value, {})

    # -- audit hash chain ------------------------------------------------------
    def audit(self, actor: str, request_id: str, kind: str, record_key: str, payload: Dict[str, Any]) -> str:
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            return self._append_audit(actor, request_id, kind, record_key, payload)

    def _append_audit(self, actor: str, request_id: str, kind: str, record_key: str,
                      payload: Dict[str, Any]) -> str:
        """Append inside the caller's transaction; caller owns BEGIN/COMMIT."""
        last = self._db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        prev = GENESIS if last is None else str(last["hash"])
        ts = self.clock()
        row = {"ts": ts, "actor": actor, "request_id": request_id, "kind": kind,
               "record_key": record_key, "payload": payload, "prev_hash": prev}
        digest = hashlib.sha256(_canonical(row).encode("utf-8")).hexdigest()
        self._db.execute(
            "INSERT INTO audit (ts, actor, request_id, kind, record_key, payload, prev_hash, hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ts, actor, request_id, kind, record_key, _canonical(payload), prev, digest))
        return digest

    def verify_audit(self) -> Tuple[bool, Optional[int]]:
        """(True, None) when every row hashes its predecessor; else (False, first bad seq)."""
        prev = GENESIS
        for r in self._db.execute("SELECT * FROM audit ORDER BY seq"):
            row = {"ts": r["ts"], "actor": r["actor"], "request_id": r["request_id"], "kind": r["kind"],
                   "record_key": r["record_key"], "payload": json.loads(r["payload"]), "prev_hash": prev}
            if r["prev_hash"] != prev or hashlib.sha256(_canonical(row).encode("utf-8")).hexdigest() != r["hash"]:
                return False, int(r["seq"])
            prev = r["hash"]
        return True, None

    def audit_rows(self, request_prefix: str) -> List[sqlite3.Row]:
        return list(self._db.execute("SELECT * FROM audit WHERE request_id LIKE ? ORDER BY seq",
                                     (request_prefix + "%",)))

    # -- inbound messages and claims -------------------------------------------
    def record_inbound(self, *, message_id: str, update_id: int, chat_id: int, sender: str,
                       recipient: str, text: str, status: str = "RECEIVED") -> bool:
        now = self.clock()
        cursor = self._db.execute(
            "INSERT OR IGNORE INTO messages (message_id, direction, kind, update_id, chat_id, sender, "
            "recipient, text, status, created_at, updated_at) VALUES (?, 'IN', 'MESSAGE', ?, ?, ?, ?, ?, ?, ?, ?)",
            (message_id, update_id, chat_id, sender, recipient, text, status, now, now))
        return cursor.rowcount == 1

    def claim(self, message_id: str, *, lease_seconds: int, max_attempts: int) -> str:
        """CLAIMED | RETRY | DUPLICATE | DONE | EXHAUSTED - atomic, with a lease.

        RETRY is a claim after an expired lease (a crashed run); it counts an
        attempt. DUPLICATE is a live lease. EXHAUSTED means the attempts are used up.
        """
        now = self.clock()
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            row = self._db.execute("SELECT status, claimed_at, attempts FROM messages WHERE message_id = ?",
                                   (message_id,)).fetchone()
            if row is None:
                raise KeyError(message_id)
            if row["status"] in ("REPLIED", "DONE", "ABANDONED", "IGNORED"):
                return "DONE"
            if row["status"] == "IN_PROGRESS" and now - row["claimed_at"] < lease_seconds:
                return "DUPLICATE"
            if row["attempts"] >= max_attempts:
                self._db.execute("UPDATE messages SET status = 'ABANDONED', updated_at = ? WHERE message_id = ?",
                                 (now, message_id))
                return "EXHAUSTED"
            outcome = "RETRY" if row["status"] == "IN_PROGRESS" else "CLAIMED"
            self._db.execute("UPDATE messages SET status = 'IN_PROGRESS', claimed_at = ?, attempts = attempts + 1, "
                             "updated_at = ? WHERE message_id = ?", (now, now, message_id))
            return outcome

    def release_untouched(self, message_id: str) -> bool:
        """Give a claim back when nothing durable happened (G-082): no attempt is charged."""
        cursor = self._db.execute(
            "UPDATE messages SET status = 'RECEIVED', claimed_at = 0, attempts = attempts - 1, updated_at = ? "
            "WHERE message_id = ? AND status = 'IN_PROGRESS' AND attempts > 0", (self.clock(), message_id))
        return cursor.rowcount == 1

    def set_status(self, message_id: str, status: str, **fields: Any) -> None:
        assignments = ", ".join(f"{k} = ?" for k in fields)
        sql = "UPDATE messages SET status = ?, updated_at = ?" + (", " + assignments if fields else "") + \
              " WHERE message_id = ?"
        self._db.execute(sql, (status, self.clock(), *fields.values(), message_id))

    def message(self, message_id: str) -> Optional[sqlite3.Row]:
        return self._db.execute("SELECT * FROM messages WHERE message_id = ?", (message_id,)).fetchone()

    def messages_with_status(self, status: str) -> List[sqlite3.Row]:
        return list(self._db.execute("SELECT * FROM messages WHERE status = ? ORDER BY created_at", (status,)))

    def resumable_inbound(self, *, lease_seconds: int, day_of: Callable[[float], str]) -> List[sqlite3.Row]:
        """Inbound work that no Telegram update will bring back (G-097).

        A claim given back under an exhausted budget waits, as the notice promised, until the
        day changes; resuming it every round would repeat the notice each poll. A claim whose
        lease expired belongs to a crashed run and is resumed at once - claim() charges the
        attempt (G-002).
        """
        now = self.clock()
        rows = self._db.execute("SELECT * FROM messages WHERE direction = 'IN' AND status IN ('RECEIVED', 'IN_PROGRESS') "
                                "ORDER BY created_at").fetchall()
        return [r for r in rows
                if (r["status"] == "RECEIVED" and day_of(r["updated_at"]) != day_of(now))
                or (r["status"] == "IN_PROGRESS" and now - r["claimed_at"] >= lease_seconds)]

    # -- outbound -----------------------------------------------------------------
    def create_outbound(self, *, message_id: str, kind: str, chat_id: int, sender: str, recipient: str,
                        text: str, reply_to: Optional[str]) -> bool:
        now = self.clock()
        cursor = self._db.execute(
            "INSERT OR IGNORE INTO messages (message_id, direction, kind, chat_id, sender, recipient, text, "
            "status, reply_to, created_at, updated_at) VALUES (?, 'OUT', ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?)",
            (message_id, kind, chat_id, sender, recipient, text, reply_to, now, now))
        return cursor.rowcount == 1

    def pending_outbound(self) -> List[sqlite3.Row]:
        return list(self._db.execute(
            "SELECT * FROM messages WHERE direction = 'OUT' AND status IN ('PENDING', 'SENDING') ORDER BY created_at"))

    def mark_sending(self, message_id: str) -> None:
        self._db.execute("UPDATE messages SET status = 'SENDING', attempts = attempts + 1, updated_at = ? "
                         "WHERE message_id = ?", (self.clock(), message_id))

    # -- budget: reserve before the call, reconcile after ------------------------
    def reserve(self, day: str, *, max_calls: int, max_usd: float, worst_usd: float) -> bool:
        with self._db:
            self._db.execute("BEGIN IMMEDIATE")
            self._db.execute("INSERT OR IGNORE INTO budget_days (day) VALUES (?)", (day,))
            row = self._db.execute("SELECT calls, usd FROM budget_days WHERE day = ?", (day,)).fetchone()
            if row["calls"] + 1 > max_calls or row["usd"] + worst_usd > max_usd + 1e-9:
                return False
            self._db.execute("UPDATE budget_days SET calls = calls + 1, usd = usd + ? WHERE day = ?", (worst_usd, day))
            return True

    def reconcile(self, day: str, *, worst_usd: float, actual_usd: Optional[float],
                  input_tokens: Optional[int], output_tokens: Optional[int]) -> None:
        # Unknown usage keeps the reservation: an unknown amount is not free.
        if actual_usd is not None:
            self._db.execute("UPDATE budget_days SET usd = usd - ? + ? WHERE day = ?", (worst_usd, actual_usd, day))
        self._db.execute("UPDATE budget_days SET input_tokens = input_tokens + ?, output_tokens = output_tokens + ? "
                         "WHERE day = ?", (input_tokens or 0, output_tokens or 0, day))

    def budget(self, day: str) -> Dict[str, Any]:
        row = self._db.execute("SELECT * FROM budget_days WHERE day = ?", (day,)).fetchone()
        return dict(row) if row else {"day": day, "calls": 0, "input_tokens": 0, "output_tokens": 0, "usd": 0.0}

    # -- proofs ----------------------------------------------------------------------
    def reconcile_deliveries(self) -> List[str]:
        """Every REPLIED/DONE inbound has exactly one SENT reply with an external id, or an
        ABANDONED one. Anything else is listed - the invariant 16 check."""
        problems = []
        for m in self._db.execute("SELECT message_id, status FROM messages WHERE direction = 'IN' "
                                  "AND status IN ('REPLIED', 'DONE')"):
            replies = list(self._db.execute("SELECT status, external_id FROM messages WHERE reply_to = ? "
                                            "AND kind = 'REPLY'", (m["message_id"],)))
            sent = [r for r in replies if r["status"] == "SENT" and r["external_id"]]
            abandoned = [r for r in replies if r["status"] == "ABANDONED"]
            if len(sent) == 1 and not abandoned:
                continue
            if len(sent) == 0 and len(abandoned) == 1 and m["status"] == "DONE":
                continue
            problems.append(f"{m['message_id']}: {len(sent)} SENT, {len(abandoned)} ABANDONED, {len(replies)} gesamt")
        return problems

    def backup(self, target: str) -> None:
        """A consistent copy with fixed rights - the thing the nightly job calls."""
        copy = sqlite3.connect(target)
        try:
            self._db.backup(copy)
        finally:
            copy.close()
        os.chmod(target, 0o600)
