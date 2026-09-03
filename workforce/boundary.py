"""The single point at which data leaves the process.

Everything that goes to a model provider passes through `prepare_outbound()`.
Taken from the prototype's data_boundary.py (G-029, G-054, G-084): the field
set per policy is a constant, the body and any context are content, and a
`Disclosure` records what left without copying it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

POLICIES = ("METADATA_ONLY", "BODY", "FULL")
MAX_OUTBOUND_CHARS = 8000

# Anything not listed here cannot leave, whatever a future record carries.
ALLOWED_FIELDS: Dict[str, Tuple[str, ...]] = {
    "METADATA_ONLY": ("message_id", "sender_id"),
    "BODY": ("message_id", "sender_id", "body"),
    "FULL": ("message_id", "sender_id", "body", "context"),
}


class DataBoundaryError(ValueError):
    pass


def stricter(first: str, second: str) -> str:
    return POLICIES[min(POLICIES.index(first), POLICIES.index(second))]


@dataclass(frozen=True)
class Disclosure:
    policy: str
    message_id: str
    fields: Tuple[str, ...]
    total_chars: int
    digest: str

    def as_log_record(self) -> Dict[str, Any]:
        return {"data_policy": self.policy, "message_id": self.message_id,
                "fields_sent": list(self.fields), "chars_sent": self.total_chars,
                "payload_sha256": self.digest}


@dataclass(frozen=True)
class Outbound:
    payload: Dict[str, str] = field(repr=False)
    disclosure: Disclosure = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"Outbound({self.disclosure!r})"


def prepare_outbound(message: Dict[str, Any], *, policy: str) -> Outbound:
    if policy not in POLICIES:
        raise DataBoundaryError(f"DATA_POLICY_INVALID:{policy}")
    message_id = str(message.get("message_id", "")).strip()
    if not message_id:
        raise DataBoundaryError("MESSAGE_ID_MISSING")
    payload: Dict[str, str] = {}
    for name in ALLOWED_FIELDS[policy]:
        value = message.get(name)
        if value is None or not str(value).strip():
            continue
        payload[name] = str(value)
    total = sum(len(v) for v in payload.values())
    if total > MAX_OUTBOUND_CHARS:
        raise DataBoundaryError(f"OUTBOUND_TOO_LARGE:{total}>{MAX_OUTBOUND_CHARS}")
    canonical = "\n".join(f"{k}={payload[k]}" for k in sorted(payload))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return Outbound(payload=payload, disclosure=Disclosure(
        policy=policy, message_id=message_id, fields=tuple(sorted(payload)),
        total_chars=total, digest=digest))


def render(outbound: Outbound) -> str:
    """The untrusted-data block of the prompt. The delimiters are a pointer for
    the system prompt, not a control; the control is that the agent has no tools."""
    lines = [f"{k}: {v}" for k, v in sorted(outbound.payload.items())]
    return "<workforce_message>\n" + "\n".join(lines) + "\n</workforce_message>"
