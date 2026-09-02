"""What one run actually cost, per operation, without copying anything.

CEO addition to Phase 5: "Der Testlauf weist pro Vorgang Datenmenge, Felder,
Provideraufrufe, Tokens beziehungsweise belastbare Schaetzung, Kostenobergrenze,
Route und Dublettenentscheidung aus" and "Abschlussartefakt ist ein kompakter
maschinenlesbarer Effizienzbericht plus kurze menschenlesbare Zusammenfassung,
ohne kopierte Vollpayloads oder Secrets."

The second half is the harder constraint, and it decides the shape of this
module: **nothing here holds content.** The record carries field *names*, a
character count and the SHA-256 the data boundary already computed - never a
subject, never a body, never a token. A report that quoted payloads would be a
second copy of exactly the data the boundary exists to meter, which is the
opposite of data minimisation.

Two numbers deserve care.

*Tokens.* A provider may or may not report usage; the echo provider never
does. Where a count is missing it is estimated at four characters per token
and the record says `tokens_estimated: true`. An estimate that cannot be told
apart from a measurement is worse than no estimate, so the flag is not
optional and the summary repeats it.

*Cost.* Always an estimate from the listed tariff, never a bill. It is
reported next to the ceiling it is measured against, because a number without
its limit says nothing about whether the run stayed inside it.

The duplicate decision is recorded per operation rather than derived
afterwards: whether a message was seen for the first time, suppressed as
already handled, or resumed after a crash is a decision the worker makes, and
reconstructing it from counts later would be guesswork.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

# Characters per token, for the estimate. Rough on purpose: it is a safety
# figure, and every place it is used says that it is estimated.
CHARS_PER_TOKEN = 4

# The decisions the worker can make about a message it is handed.
FIRST_DELIVERY = "FIRST_DELIVERY"
DUPLICATE_SUPPRESSED = "DUPLICATE_SUPPRESSED"
RESUMED_AFTER_CRASH = "RESUMED_AFTER_CRASH"
ATTEMPTS_EXHAUSTED = "ATTEMPTS_EXHAUSTED"
DECISIONS = (FIRST_DELIVERY, DUPLICATE_SUPPRESSED, RESUMED_AFTER_CRASH,
             ATTEMPTS_EXHAUSTED)


def estimate_tokens(chars: int) -> int:
    return max(0, chars) // CHARS_PER_TOKEN


@dataclass
class Operation:
    """One inbound message, from arrival to result."""

    message_id: str
    sender_id: str
    reply_recipient_id: str | None
    task_class: str
    outcome: str
    duplicate_decision: str
    data_policy: str | None = None
    fields_sent: tuple[str, ...] = ()
    chars_sent: int = 0
    payload_sha256: str | None = None
    model: str | None = None
    provider_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    tokens_estimated: bool = False
    estimated_cost_usd: float = 0.0
    cost_ceiling_usd: float | None = None
    refusal: str | None = None

    def as_dict(self) -> dict[str, Any]:
        record = asdict(self)
        record["fields_sent"] = list(self.fields_sent)
        record["estimated_cost_usd"] = round(self.estimated_cost_usd, 6)
        return record


@dataclass
class Report:
    run_id: str
    operations: list[Operation] = field(default_factory=list)

    def record(self, operation: Operation) -> Operation:
        if operation.duplicate_decision not in DECISIONS:
            raise ValueError(
                f"AGENT_REPORT_UNKNOWN_DECISION:{operation.duplicate_decision}")
        self.operations.append(operation)
        return operation

    # -- aggregates -------------------------------------------------------
    @property
    def provider_calls(self) -> int:
        return sum(o.provider_calls for o in self.operations)

    @property
    def chars_sent(self) -> int:
        return sum(o.chars_sent for o in self.operations)

    @property
    def estimated_cost_usd(self) -> float:
        return sum(o.estimated_cost_usd for o in self.operations)

    @property
    def any_estimated(self) -> bool:
        return any(o.tokens_estimated for o in self.operations)

    def counted(self, outcome: str) -> int:
        return sum(1 for o in self.operations if o.outcome == outcome)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "operations": [o.as_dict() for o in self.operations],
            "totals": {
                "operations": len(self.operations),
                "provider_calls": self.provider_calls,
                "chars_sent": self.chars_sent,
                "tokens": sum(o.input_tokens + o.output_tokens for o in self.operations),
                "tokens_estimated": self.any_estimated,
                "estimated_cost_usd": round(self.estimated_cost_usd, 6),
                "answered": self.counted("ANSWERED"),
                "refused": self.counted("REFUSED"),
                "duplicates_suppressed": sum(
                    1 for o in self.operations
                    if o.duplicate_decision == DUPLICATE_SUPPRESSED
                ),
            },
        }

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False, sort_keys=True, indent=2)

    def as_summary(self) -> str:
        """The short human half. Deliberately a handful of lines."""
        t = self.as_dict()["totals"]
        schaetzung = " (Tokens teilweise geschaetzt)" if t["tokens_estimated"] else ""
        zeilen = [
            f"Lauf {self.run_id}",
            f"  Vorgaenge:        {t['operations']} "
            f"({t['answered']} beantwortet, {t['refused']} abgelehnt)",
            f"  Provideraufrufe:  {t['provider_calls']}",
            f"  Dubletten:        {t['duplicates_suppressed']} unterdrueckt",
            f"  Uebertragen:      {t['chars_sent']} Zeichen, "
            f"{t['tokens']} Tokens{schaetzung}",
            f"  Geschaetzte Kosten: {t['estimated_cost_usd']:.4f} USD",
        ]
        return "\n".join(zeilen)
