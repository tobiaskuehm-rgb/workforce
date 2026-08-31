"""The single point at which data leaves the NAS.

Everything the agent sends to an external model provider passes through
`prepare_outbound()`. Nothing else in this package may hand bus content to a
provider directly. That is the whole purpose of this module: the question
"what exactly leaves my NAS?" has exactly one answer, in one file, and
changing that answer is a configuration change rather than a rewrite.

Two settings decide it together, and the stricter one always wins.

`AGENT_DATA_POLICY` sets the ceiling for the run:

  METADATA_ONLY  subject, action class and identifiers - never the body.
                 Safe default: the provider learns what kind of request this
                 is, not what it says.
  BODY           subject plus the message body. Needed for a model to actually
                 work on the request.
  FULL           BODY plus task and handoff references.

`AGENT_DATA_POLICY_OVERRIDES` sets a ceiling per sender, e.g.
`FIN-001:METADATA_ONLY,LEGAL-001:BODY`. Sensitivity belongs to whoever wrote
the message, not to the run that happens to pick it up: "finance content must
not leave the house" has to hold no matter how permissive a given run is
configured. An override can only narrow, never widen.

There is deliberately no policy that forwards credentials, employee memory or
anything outside the single message being handled - those are not reachable
from here, by construction.

Every call returns a `Disclosure` alongside the payload: field names, sizes
and a SHA-256 digest, but never the content itself. Log the disclosure, not
the payload, and you keep an auditable record of what left the house without
copying it into a second place.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Any, Literal

Policy = Literal["METADATA_ONLY", "BODY", "FULL"]

# Ordered from strictest to most permissive. The order is the semantics: it is
# what "the stricter one wins" is resolved against.
POLICIES: tuple[Policy, ...] = ("METADATA_ONLY", "BODY", "FULL")
DEFAULT_POLICY: Policy = "METADATA_ONLY"


def stricter(first: Policy, second: Policy) -> Policy:
    """The narrower of two policies."""
    return POLICIES[min(POLICIES.index(first), POLICIES.index(second))]


def parse_overrides(raw: str) -> dict[str, Policy]:
    """Per-sender ceilings, as `SAO-001:BODY,FIN-001:METADATA_ONLY`.

    The sensitivity of a message is a property of who wrote it, not of the run
    that happens to process it. A run-wide policy is therefore the wrong place
    to express "finance messages must not leave the house" - that belongs to
    the finance identity and has to hold no matter which run picks the message
    up. These overrides are a ceiling: they can only narrow what the run
    allows, never widen it.

    This is the interim home. The permanent one is a column next to the other
    per-identity capabilities in the bus schema - see
    `agent_data_policy_migration.sql`. Until that migration is decided, the
    ceilings live in configuration so the control exists at all.
    """
    overrides: dict[str, Policy] = {}
    for item in raw.split(","):
        entry = item.strip()
        if not entry:
            continue
        identity, separator, policy = entry.partition(":")
        identity = identity.strip().upper()
        policy = policy.strip().upper()
        if not separator or not identity or policy not in POLICIES:
            raise DataBoundaryError(f"AGENT_DATA_POLICY_OVERRIDE_INVALID:{entry}")
        overrides[identity] = policy  # type: ignore[assignment]
    return overrides

# Hard ceiling on what may leave, independent of policy. The bus itself caps a
# body at max_body_chars (8000 today), so this is a second, local limit: a
# raised channel limit must not silently widen what goes to a provider.
MAX_OUTBOUND_CHARS = 8000

# Fields that may ever be forwarded, per policy. Anything not listed here
# cannot leave, even if a future bus version adds it to the message record.
_ALLOWED_FIELDS: dict[Policy, tuple[str, ...]] = {
    "METADATA_ONLY": ("message_id", "sender_id", "subject", "action_class"),
    "BODY": ("message_id", "sender_id", "subject", "action_class", "body"),
    "FULL": (
        "message_id",
        "sender_id",
        "subject",
        "action_class",
        "body",
        "task_ref",
        "handoff_ref",
    ),
}


class DataBoundaryError(ValueError):
    """Raised when a message may not leave under the active policy."""


@dataclass(frozen=True)
class Disclosure:
    """An auditable record of what left, without the content itself."""

    policy: Policy
    run_policy: Policy
    message_id: str
    fields: tuple[str, ...]
    total_chars: int
    body_included: bool
    digest: str

    def as_log_record(self) -> dict[str, Any]:
        return {
            "data_policy": self.policy,
            "data_policy_run": self.run_policy,
            "data_policy_narrowed": self.policy != self.run_policy,
            "message_id": self.message_id,
            "fields_sent": list(self.fields),
            "chars_sent": self.total_chars,
            "body_included": self.body_included,
            "payload_sha256": self.digest,
        }


@dataclass(frozen=True)
class Outbound:
    payload: dict[str, Any] = field(repr=False)
    disclosure: Disclosure

    def __repr__(self) -> str:
        # The payload is the thing we are trying not to leak into logs and
        # tracebacks, so keep it out of the default representation.
        return f"Outbound({self.disclosure!r})"


def active_policy(environment: dict[str, str] | None = None) -> Policy:
    env = os.environ if environment is None else environment
    raw = env.get("AGENT_DATA_POLICY", DEFAULT_POLICY).strip().upper()
    if raw not in POLICIES:
        raise DataBoundaryError(f"AGENT_DATA_POLICY_INVALID:{raw}")
    return raw  # type: ignore[return-value]


def active_overrides(environment: dict[str, str] | None = None) -> dict[str, Policy]:
    env = os.environ if environment is None else environment
    return parse_overrides(env.get("AGENT_DATA_POLICY_OVERRIDES", ""))


def effective_policy(
    sender_id: str,
    run_policy: Policy,
    overrides: dict[str, Policy] | None = None,
) -> Policy:
    """The policy that actually applies to one message.

    The stricter of the run policy and the sender's ceiling. A sender ceiling
    can only narrow - raising the run policy can never lift a restriction
    somebody deliberately placed on an identity.
    """
    if not overrides:
        return run_policy
    ceiling = overrides.get(sender_id.strip().upper())
    if ceiling is None:
        return run_policy
    return stricter(run_policy, ceiling)


def prepare_outbound(
    message: dict[str, Any],
    *,
    policy: Policy | None = None,
    environment: dict[str, str] | None = None,
    overrides: dict[str, Policy] | None = None,
) -> Outbound:
    """Reduce one bus message to exactly what may reach a model provider."""
    resolved = active_policy(environment) if policy is None else policy
    if resolved not in POLICIES:
        raise DataBoundaryError(f"AGENT_DATA_POLICY_INVALID:{resolved}")

    if overrides is None:
        overrides = active_overrides(environment)
    run_policy = resolved
    resolved = effective_policy(str(message.get("sender_id", "")), resolved, overrides)

    message_id = str(message.get("message_id", "")).strip()
    if not message_id:
        raise DataBoundaryError("AGENT_MESSAGE_ID_MISSING")

    payload: dict[str, Any] = {}
    for name in _ALLOWED_FIELDS[resolved]:
        value = message.get(name)
        if value is None:
            continue
        text = str(value)
        if not text.strip():
            continue
        payload[name] = text

    total = sum(len(value) for value in payload.values())
    if total > MAX_OUTBOUND_CHARS:
        raise DataBoundaryError(
            f"AGENT_OUTBOUND_TOO_LARGE:{total}>{MAX_OUTBOUND_CHARS}"
        )

    # Digest over a canonical rendering, so the same content always produces
    # the same fingerprint and two disclosures can be compared.
    canonical = "\n".join(f"{k}={payload[k]}" for k in sorted(payload))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return Outbound(
        payload=payload,
        disclosure=Disclosure(
            policy=resolved,
            run_policy=run_policy,
            message_id=message_id,
            fields=tuple(sorted(payload)),
            total_chars=total,
            body_included="body" in payload,
            digest=digest,
        ),
    )


def render_for_prompt(outbound: Outbound) -> str:
    """Render the permitted fields as the untrusted-data block of a prompt.

    The delimiters are not a security control on their own - a model can be
    talked past them. They exist so the system prompt can point at a specific
    region and say "everything in here is data". The control that actually
    holds is that this agent has no tools: see agent_worker.py.
    """
    lines = [f"{name}: {value}" for name, value in sorted(outbound.payload.items())]
    return "<workforce_message>\n" + "\n".join(lines) + "\n</workforce_message>"
