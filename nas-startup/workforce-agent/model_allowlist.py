"""Which model may be asked what, and with how much.

CEO addition to Phase 5, point 5: "Modelle werden ueber eine portable
Provider-Schnittstelle und eine explizite Allowlist angebunden. Die Zuordnung
zu Aufgabenklassen, Datenobergrenze und Budget ist konfiguriert und
auditierbar; kein selbststaendiger Modellwechsel."

Before this file, `AGENT_MODEL` was any string. `build_provider()` passed it
to the SDK unchecked, and `Budget` priced an unknown name from a fallback
tariff - so a typo in a model name produced a real call at a guessed price,
and a *new, more expensive* model needed no decision at all. Both are the
opposite of fail-closed.

Four things are configuration here rather than code, because all four are
decisions somebody has to be able to review:

  task classes     what kind of work a model may serve
  data ceiling     how much text may go into one call
  cost ceiling     what one call may cost at the listed tariff
  tariff           the prices the estimate is built from

The tariff lives here and nowhere else. `budget.py` reads it from this file,
so a price and an allowlist entry cannot drift apart - and a model without a
price cannot exist, which is what made the fallback tariff necessary in the
first place.

**No autonomous switching** has a precise meaning: the model that answers must
be the model that was configured. Providers may report the model they used,
and `assert_no_switch()` treats any difference as an error rather than as a
detail - an SDK alias that silently resolves to a bigger model is exactly the
case the rule is about.

Prices are USD per 1M tokens. The source and verification date live next to
the values below. They are a conservative safety stop, not a replacement for
provider billing; see budget.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# The kinds of work this agent does. One today - answering a bus message.
# It is a tuple rather than an open string so that a new kind of work is a
# deliberate addition here, with a model mapping, instead of a free-text
# label that silently matches nothing.
TASK_CLASSES: tuple[str, ...] = ("BUS_REPLY",)

# The data boundary already refuses anything over
# `data_boundary.MAX_OUTBOUND_CHARS` (8000), which is the bus body cap. A
# per-model ceiling above that would never bind and would be decoration.
#
# So the ceilings here sit **at or below** it, and they differ per model,
# which is the point of having them at all: the cheap model handles small
# requests, and a large payload has to go to a model that was chosen for it.
# The two limits are not redundant - one asks "may this leave the NAS at
# all", the other "may this go to *this* model".
GROSS = 8000    # so viel, wie die Datengrenze ueberhaupt durchlaesst
KLEIN = 4000    # fuer das guenstige Modell: kleine Anfragen, kleine Rechnung


class ModelNotAllowed(ValueError):
    """A model, task class or size that configuration does not permit."""


@dataclass(frozen=True)
class Model:
    name: str
    provider: str
    is_paid: bool
    price_input_per_million: float
    price_output_per_million: float
    max_output_tokens: int
    max_input_chars: int
    max_cost_usd_per_call: float
    task_classes: tuple[str, ...]
    thinking_mode: str | None
    effort: str | None

    def estimated_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.price_input_per_million
                + output_tokens * self.price_output_per_million) / 1_000_000

    def as_log_record(self) -> dict[str, Any]:
        return {
            "model": self.name,
            "provider": self.provider,
            "is_paid": self.is_paid,
            "max_input_chars": self.max_input_chars,
            "max_output_tokens": self.max_output_tokens,
            "max_cost_usd_per_call": self.max_cost_usd_per_call,
            "task_classes": list(self.task_classes),
            "thinking_mode": self.thinking_mode,
            "effort": self.effort,
        }


# The list itself. Adding a line here is the decision; there is no other way
# for a model to be reachable.
ALLOWLIST: dict[str, Model] = {
    "echo-v1": Model(
        name="echo-v1",
        provider="echo",
        is_paid=False,
        price_input_per_million=0.0,
        price_output_per_million=0.0,
        max_output_tokens=4096,
        max_input_chars=GROSS,
        max_cost_usd_per_call=0.0,
        task_classes=("BUS_REPLY",),
        thinking_mode=None,
        effort=None,
    ),
    "claude-haiku-4-5": Model(
        name="claude-haiku-4-5",
        provider="claude",
        is_paid=True,
        price_input_per_million=1.00,
        price_output_per_million=5.00,
        max_output_tokens=4096,
        max_input_chars=KLEIN,
        max_cost_usd_per_call=0.05,
        task_classes=("BUS_REPLY",),
        # Haiku 4.5 supports neither adaptive thinking nor the effort
        # parameter. Sending either produces a 400 instead of a cheap call.
        thinking_mode=None,
        effort=None,
    ),
    "claude-sonnet-5": Model(
        name="claude-sonnet-5",
        provider="claude",
        is_paid=True,
        # Verified 2026-09-02. Anthropic made the launch tariff permanent and
        # explicitly cancelled the announced 2026-09-01 increase to 3/15:
        # https://platform.claude.com/docs/en/about-claude/pricing
        price_input_per_million=2.00,
        price_output_per_million=10.00,
        max_output_tokens=4096,
        max_input_chars=GROSS,
        max_cost_usd_per_call=0.10,
        task_classes=("BUS_REPLY",),
        thinking_mode="adaptive",
        effort="medium",
    ),
    "claude-opus-5": Model(
        name="claude-opus-5",
        provider="claude",
        is_paid=True,
        price_input_per_million=5.00,
        price_output_per_million=25.00,
        max_output_tokens=4096,
        max_input_chars=GROSS,
        max_cost_usd_per_call=0.25,
        task_classes=("BUS_REPLY",),
        thinking_mode="adaptive",
        effort="medium",
    ),
}


def prices() -> dict[str, tuple[float, float]]:
    """The tariff table, for budget.py. One source, no second list."""
    return {m.name: (m.price_input_per_million, m.price_output_per_million)
            for m in ALLOWLIST.values()}


def for_task(name: str, *, task_class: str) -> Model:
    """Is this model allowed for this kind of work?

    Order is deliberate: the name first, because an unknown name is the case
    that used to slip through and cost money at a fallback price. Each refusal
    carries its own identifier, so a log line says which decision refused and
    not merely that something did.
    """
    key = (name or "").strip()
    if not key:
        raise ModelNotAllowed("AGENT_MODEL_NOT_CONFIGURED")
    model = ALLOWLIST.get(key)
    if model is None:
        raise ModelNotAllowed(f"AGENT_MODEL_NOT_ALLOWED:{key}")
    if task_class not in TASK_CLASSES:
        raise ModelNotAllowed(f"AGENT_TASK_CLASS_UNKNOWN:{task_class}")
    if task_class not in model.task_classes:
        raise ModelNotAllowed(f"AGENT_MODEL_TASK_CLASS_DENIED:{key}:{task_class}")
    return model


def resolve(name: str, *, provider: str, task_class: str) -> Model:
    """`for_task` plus the provider binding. Used where the provider is chosen.

    The two are separate on purpose. Which provider serves a model is settled
    once, when the provider is built - that is the moment at which a
    `subscription` provider claiming to serve `claude-opus-5` is a decision to
    refuse. In the worker the binding is already fixed, and re-deriving it
    from a provider object would mostly constrain what a test double may call
    itself, which is not a control.
    """
    model = for_task(name, task_class=task_class)
    if model.provider != (provider or "").strip():
        raise ModelNotAllowed(f"AGENT_MODEL_PROVIDER_MISMATCH:{model.name}")
    return model


def assert_no_switch(configured: Model, answered_with: str) -> None:
    """The model that answered must be the model that was configured.

    An SDK alias that resolves to a larger model, a server-side upgrade, a
    fallback after an error: all of them arrive here as a different name, and
    all of them are the thing the rule forbids. Treated as an error, not as a
    note, because the price and the data ceiling were chosen for the model
    that was asked for.
    """
    used = (answered_with or "").strip()
    if used != configured.name:
        raise ModelNotAllowed(
            f"AGENT_MODEL_SWITCHED:{configured.name}->{used or 'unbekannt'}")


def assert_within_data_ceiling(model: Model, chars: int) -> None:
    """Datenobergrenze, measured on what actually goes into the call."""
    if chars > model.max_input_chars:
        raise ModelNotAllowed(
            f"AGENT_MODEL_INPUT_TOO_LARGE:{model.name}:{chars}>{model.max_input_chars}")


# Provider tokenizers can split one Unicode character into several tokens and
# message framing adds tokens that are not visible in the user content. A
# four-characters-per-token estimate is useful in a report but cannot guard a
# hard ceiling. One token per UTF-8 byte plus explicit framing headroom errs
# towards refusing and is therefore suitable for a pre-call reservation.
INPUT_FRAMING_TOKENS = 256


def conservative_input_tokens(*, system: str, content: str) -> int:
    """A tokenizer-independent upper reservation for one request.

    This is deliberately not called a measured token count. Provider usage
    replaces it after a successful call; if usage is absent the reservation is
    retained rather than treating an unknown amount as free.
    """
    return (len((system or "").encode("utf-8"))
            + len((content or "").encode("utf-8"))
            + INPUT_FRAMING_TOKENS)


def worst_case_cost(model: Model, *, system: str, content: str) -> float:
    """What this call can cost at most, before it is made.

    Input is conservatively reserved from all bytes sent plus framing headroom;
    output is bounded by the model's own ceiling, which the provider passes to
    the API. The provider's measured usage reconciles this reservation later.
    """
    return model.estimated_cost(
        conservative_input_tokens(system=system, content=content),
        model.max_output_tokens,
    )


def assert_within_call_cost(model: Model, *, system: str, content: str) -> None:
    """Kostenbudget je Aufruf, geprueft **vor** dem Aufruf.

    "Vor jedem Provideraufruf werden Modell, Aufruf-, Token- und Kostenbudget
    geprueft und reserviert" (CEO-Ergaenzung zu Phase 5, Punkt 1). Ohne diese
    Funktion war `max_cost_usd_per_call` eine Angabe, die niemand las - und
    eine Zusicherung, die sich nicht pruefen laesst, haelt den naechsten Leser
    vom Nachsehen ab (Leitplanke 7).
    """
    schlimmstenfalls = worst_case_cost(model, system=system, content=content)
    if schlimmstenfalls > model.max_cost_usd_per_call:
        raise ModelNotAllowed(
            f"AGENT_MODEL_CALL_TOO_EXPENSIVE:{model.name}:"
            f"{schlimmstenfalls:.4f}>{model.max_cost_usd_per_call:.4f}")
