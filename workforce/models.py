"""Which model may be asked, at what price, with what ceilings.

Taken from the prototype's model_allowlist.py. Prices are USD per million
tokens, looked up on 2026-09-02 in the model/price reference; they are a
conservative safety stop, not a replacement for provider billing. Adding a
paid model is adding a line here - there is no other way for one to be reachable.
Local Ollama models are unpaid and any name is allowed; nothing leaves the house.
"""

from __future__ import annotations

from dataclasses import dataclass

GROSS = 8000  # what the boundary lets through at all
KLEIN = 4000  # for the cheap model: small requests, small bill
INPUT_FRAMING_TOKENS = 256


class ModelNotAllowed(ValueError):
    pass


@dataclass(frozen=True)
class Model:
    name: str
    provider: str
    is_paid: bool
    price_in: float
    price_out: float
    max_output_tokens: int
    max_input_chars: int
    max_usd_per_call: float

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.price_in + output_tokens * self.price_out) / 1_000_000


ALLOWLIST = {
    "echo-v1": Model("echo-v1", "echo", False, 0.0, 0.0, 4096, GROSS, 0.0),
    "claude-haiku-4-5": Model("claude-haiku-4-5", "claude", True, 1.00, 5.00, 4096, KLEIN, 0.05),
    "claude-sonnet-5": Model("claude-sonnet-5", "claude", True, 2.00, 10.00, 4096, GROSS, 0.10),
    "claude-opus-5": Model("claude-opus-5", "claude", True, 5.00, 25.00, 4096, GROSS, 0.25),
}


def resolve(name: str, *, provider: str) -> Model:
    key = (name or "").strip()
    if not key:
        raise ModelNotAllowed("MODEL_NOT_CONFIGURED")
    model = ALLOWLIST.get(key)
    if model is not None:
        # A listed name is bound to its provider; nobody re-labels a paid model as local.
        if model.provider != provider:
            raise ModelNotAllowed(f"MODEL_PROVIDER_MISMATCH:{key}")
        return model
    if provider == "ollama":
        return Model(key, "ollama", False, 0.0, 0.0, 2048, GROSS, 0.0)
    raise ModelNotAllowed(f"MODEL_NOT_ALLOWED:{key}")


def assert_no_switch(configured: Model, answered_with: str) -> None:
    used = (answered_with or "").strip()
    if used != configured.name:
        raise ModelNotAllowed(f"MODEL_SWITCHED:{configured.name}->{used or 'unbekannt'}")


def conservative_input_tokens(system: str, content: str) -> int:
    # One token per UTF-8 byte plus framing: errs towards refusing, which is
    # the right direction for a reservation made before the call.
    return len(system.encode("utf-8")) + len(content.encode("utf-8")) + INPUT_FRAMING_TOKENS


def worst_case_cost(model: Model, system: str, content: str) -> float:
    return model.cost(conservative_input_tokens(system, content), model.max_output_tokens)


def check_call(model: Model, system: str, content: str) -> float:
    """Data ceiling and per-call cost ceiling, both before the call. Returns the worst case."""
    if len(content) > model.max_input_chars:
        raise ModelNotAllowed(f"MODEL_INPUT_TOO_LARGE:{model.name}:{len(content)}>{model.max_input_chars}")
    worst = worst_case_cost(model, system, content)
    if worst > model.max_usd_per_call:
        raise ModelNotAllowed(f"MODEL_CALL_TOO_EXPENSIVE:{model.name}:{worst:.4f}>{model.max_usd_per_call:.4f}")
    return worst
