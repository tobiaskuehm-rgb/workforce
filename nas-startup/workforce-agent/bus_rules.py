"""The bus transition rules, transcribed from the migration.

Why this file exists: on 2026-08-31 the core roundtrip needed four attempts,
and every failure was a place where my test double disagreed with the real
bus. The double had been written from what I assumed the rules were, so the
local suite happily confirmed my assumption and the real bus refused.

Three divergences in one day is a pattern, not bad luck. So the rules live
here once, transcribed line by line from `postgres-init/002_workforce_bus.sql`
with the source lines named, and the test double is built *from* this table
rather than from memory. A double can still be wrong - but now it is wrong in
exactly one place, and `test_bus_rules.py` compares it against the table
rather than against my expectations.

This is documentation with teeth, not a second implementation: the bus stays
the authority. If the migration changes, this file is stale until someone
updates it - and `test_bus_rules.py` makes that loud rather than silent by
fingerprinting the two SQL functions this table transcribes. Edit the
migration and the test fails with a message telling you to re-verify here.

A fingerprint proves nothing about correctness. It only guarantees that a
change to the source cannot slip past unnoticed, which is the failure mode a
transcription actually has: not being wrong from the start, but quietly
becoming wrong later.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Role = Literal["creator", "owner", "sender", "recipient", "coordinator"]

# The one identity the bus names explicitly rather than by role.
COORDINATOR = "SAO-001"
# Owners the coordinator may lift out of PENDING.
COORDINATABLE_OWNERS = ("AI-ENG-001", "RAS-001", "PEO-001")


@dataclass(frozen=True)
class Rule:
    role: Role
    from_status: tuple[str, ...]
    to_status: tuple[str, ...]
    source: str


# --- Tasks -----------------------------------------------------------------
# workforce.bus_transition_task, the v_allowed assignment.
TASK_RULES: tuple[Rule, ...] = (
    Rule("owner", ("OPEN",), ("IN_PROGRESS", "BLOCKED", "HOLD", "REVIEW"),
         "002_workforce_bus.sql, bus_transition_task, v_allowed line 1"),
    Rule("owner", ("IN_PROGRESS", "BLOCKED", "HOLD"),
         ("IN_PROGRESS", "BLOCKED", "HOLD", "REVIEW"),
         "002_workforce_bus.sql, bus_transition_task, v_allowed line 2"),
    Rule("creator", ("PENDING",), ("CANCELLED",),
         "002_workforce_bus.sql, bus_transition_task, v_allowed line 3"),
    # The only rule naming a concrete identity: coordination out of PENDING is
    # Karl's, and only towards the three named owners. This is the one that
    # cost the first roundtrip attempt - the owner cannot open his own task.
    Rule("coordinator", ("PENDING",), ("OPEN",),
         "002_workforce_bus.sql, bus_transition_task, v_allowed line 4"),
    Rule("creator", ("REVIEW",), ("DONE", "IN_PROGRESS"),
         "002_workforce_bus.sql, bus_transition_task, v_allowed line 5"),
)

# DONE without evidence is refused before permissions are even considered.
TASK_EVIDENCE_REQUIRED_FOR = ("DONE",)

# --- Handoffs --------------------------------------------------------------
# workforce.bus_transition_handoff, the v_allowed assignment. Same shape as
# tasks: the sender finalises, then the other side rules. Attempt two of the
# roundtrip died here, because the recipient cannot decide a PENDING handoff.
HANDOFF_RULES: tuple[Rule, ...] = (
    Rule("sender", ("PENDING",), ("OPEN", "CANCELLED"),
         "002_workforce_bus.sql, bus_transition_handoff, v_allowed line 1"),
    Rule("sender", ("OPEN",), ("CANCELLED",),
         "002_workforce_bus.sql, bus_transition_handoff, v_allowed line 2"),
    Rule("recipient", ("OPEN",), ("ACCEPTED", "REJECTED"),
         "002_workforce_bus.sql, bus_transition_handoff, v_allowed line 3"),
)

HANDOFF_NOTE_REQUIRED_FOR = ("REJECTED",)

# Asking for the status a record already has is answered as an idempotency
# conflict *before* permissions are checked. Attempt three of the roundtrip
# died here: a negative case aimed at a permission check never reached it.
SAME_STATUS_IS_CONFLICT = True


def transition_allowed(
    rules: tuple[Rule, ...], role: Role, current: str, target: str
) -> bool:
    """Whether a role may move a record from current to target."""
    return any(
        rule.role == role and current in rule.from_status and target in rule.to_status
        for rule in rules
    )


def roles_for_task(identity: str, creator_id: str, owner_id: str) -> set[Role]:
    """Every role an identity holds for one task. They can overlap."""
    roles: set[Role] = set()
    if identity == creator_id:
        roles.add("creator")
    if identity == owner_id:
        roles.add("owner")
    if identity == COORDINATOR and owner_id in COORDINATABLE_OWNERS:
        roles.add("coordinator")
    return roles


def roles_for_handoff(identity: str, sender_id: str, recipient_id: str) -> set[Role]:
    roles: set[Role] = set()
    if identity == sender_id:
        roles.add("sender")
    if identity == recipient_id:
        roles.add("recipient")
    return roles


def may_transition_task(
    identity: str, *, creator_id: str, owner_id: str, current: str, target: str
) -> bool:
    return any(
        transition_allowed(TASK_RULES, role, current, target)
        for role in roles_for_task(identity, creator_id, owner_id)
    )


def may_transition_handoff(
    identity: str, *, sender_id: str, recipient_id: str, current: str, target: str
) -> bool:
    return any(
        transition_allowed(HANDOFF_RULES, role, current, target)
        for role in roles_for_handoff(identity, sender_id, recipient_id)
    )


# --- Drift guard ------------------------------------------------------------
# SHA-256 of the two SQL function bodies this file transcribes, as of the
# transcription on 2026-08-31. `test_bus_rules.py` recomputes them and fails
# when they differ. On failure: read the changed function, update the rules
# above, run the contract test against a live bus, then record the new digest.
#
# Never update a digest without re-reading the function. Doing so turns the
# guard into a rubber stamp and reintroduces exactly the silent drift it
# exists to prevent.
SQL_SOURCE = Path(__file__).resolve().parents[1] / "postgres-init" / "002_workforce_bus.sql"

TRANSCRIBED_FROM: dict[str, str] = {
    "bus_transition_task":
        "d130809a147ec662d7c46c863883b49db2c63d293a5d4c358c59961f2b2a8f32",
    "bus_transition_handoff":
        "bede0a19fa23b48f496639577ada1ebfc5dc0302381385e876dedddce4220fb9",
}


def sql_function_body(name: str, source: Path | None = None) -> str | None:
    """The text of one SQL function, from CREATE FUNCTION to the closing $$;"""
    path = SQL_SOURCE if source is None else source
    try:
        sql = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(rf"FUNCTION workforce\.{name}\b.*?\n\$\$;", sql, re.S)
    return match.group(0) if match else None


def sql_function_digest(name: str, source: Path | None = None) -> str | None:
    body = sql_function_body(name, source)
    if body is None:
        return None
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
