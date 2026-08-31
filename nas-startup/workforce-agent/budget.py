"""Hard limits for one agent run: messages, model calls, tokens, money.

Security review 2026-08-31, F8: nothing bounded how much the agent could do.
`AGENT_MAX_CYCLES` limits passes over the inbox, not messages per pass and not
spend. The review's own wording is the reason this exists - a misfiring agent
does not get tired.

Five independent ceilings, any one of which stops the run:

  messages        how many inbox messages may be handled at all
  provider_calls  how many times a model may be asked
  tokens          input + output tokens across the run
  cost            estimated spend in USD
  runtime         wall-clock seconds the run may take

The runtime ceiling exists because the others do not bound time (security
review 2026-08-31, A3). A provider call can take minutes with retries, and an
ACCEPTANCE credential is only valid for 30 minutes - without this a run would
grind on past its own credential and fail on every remaining message.

The cost figure is an estimate for a safety stop, not billing. Prices are
configurable because they change; the defaults below are the Claude Opus 5
list prices as of 2026-06 ($5 per 1M input, $25 per 1M output). If a price is
wrong the estimate is wrong - which is exactly why the token and call ceilings
exist alongside it rather than relying on money alone.

The check runs *before* a message is acknowledged. An exhausted budget must
leave the remaining messages untouched and DELIVERED, so a later run picks
them up - never acknowledged-and-dropped.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

# USD per 1M tokens. Only used for the estimated-cost ceiling.
DEFAULT_PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}
FALLBACK_PRICE = (5.00, 25.00)

DEFAULTS = {
    "messages": 25,
    "provider_calls": 25,
    "tokens": 200_000,
    "cost_usd": 1.00,
    # Comfortably inside the 30-minute lifetime of an ACCEPTANCE credential.
    "runtime_seconds": 900,
}


class BudgetExhausted(RuntimeError):
    """A ceiling was reached. Carries which one, for the log and the operator."""

    def __init__(self, limit_name: str, used: float, ceiling: float) -> None:
        super().__init__(f"AGENT_BUDGET_EXHAUSTED:{limit_name}")
        self.limit_name = limit_name
        self.used = used
        self.ceiling = ceiling


@dataclass
class Budget:
    max_messages: int = DEFAULTS["messages"]
    max_provider_calls: int = DEFAULTS["provider_calls"]
    max_tokens: int = DEFAULTS["tokens"]
    max_cost_usd: float = DEFAULTS["cost_usd"]
    max_runtime_seconds: int = DEFAULTS["runtime_seconds"]
    prices: dict[str, tuple[float, float]] = field(default_factory=lambda: dict(DEFAULT_PRICES))
    # Injected so tests can drive the clock instead of sleeping.
    clock: Any = time.monotonic

    messages_handled: int = 0
    provider_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (
            ("max_messages", self.max_messages),
            ("max_provider_calls", self.max_provider_calls),
            ("max_tokens", self.max_tokens),
            ("max_runtime_seconds", self.max_runtime_seconds),
        ):
            if value < 0:
                raise ValueError(f"AGENT_BUDGET_INVALID:{name}")
        if self.max_cost_usd < 0:
            raise ValueError("AGENT_BUDGET_INVALID:max_cost_usd")
        self._started_at = self.clock()

    # -- gates ------------------------------------------------------------
    @property
    def elapsed_seconds(self) -> float:
        return self.clock() - self._started_at

    def check_message(self) -> None:
        """Call before touching the next message - before the acknowledgement."""
        if self.elapsed_seconds >= self.max_runtime_seconds:
            raise BudgetExhausted(
                "runtime_seconds", self.elapsed_seconds, self.max_runtime_seconds
            )
        if self.messages_handled >= self.max_messages:
            raise BudgetExhausted("messages", self.messages_handled, self.max_messages)
        if self.provider_calls >= self.max_provider_calls:
            raise BudgetExhausted(
                "provider_calls", self.provider_calls, self.max_provider_calls
            )
        if self.total_tokens >= self.max_tokens:
            raise BudgetExhausted("tokens", self.total_tokens, self.max_tokens)
        # Retrospective by nature: a call's cost is only known once it returns,
        # so this ceiling can be overshot by at most one call. The call and
        # token ceilings bound the run in advance; this one is the money
        # backstop behind them.
        #
        # The `> 0` guard is what makes a ceiling of 0.00 useful rather than
        # paralysing: it reads as "this run must not cost anything". A free
        # provider keeps cost at 0 and runs; the first paid call trips it.
        if self.cost_usd > 0 and self.cost_usd >= self.max_cost_usd:
            raise BudgetExhausted("cost_usd", self.cost_usd, self.max_cost_usd)

    # -- accounting -------------------------------------------------------
    def record_message(self) -> None:
        self.messages_handled += 1

    def reserve_provider_call(self) -> None:
        """Count an attempt before it is made.

        Review finding G-004: counting only successful returns let failures and
        SDK-internal retries pass unbilled against the ceiling, although they
        cost load and can cost money. A reserved attempt is never given back -
        an attempt that failed still happened.
        """
        self.provider_calls += 1

    def record_provider_usage(
        self, *, model: str, input_tokens: int | None, output_tokens: int | None
    ) -> None:
        """Book what a returned call actually consumed. Does not count the call
        again - reserve_provider_call() did that before it was made."""
        used_in = input_tokens or 0
        used_out = output_tokens or 0
        self.input_tokens += used_in
        self.output_tokens += used_out
        price_in, price_out = self.prices.get(model, FALLBACK_PRICE)
        self.cost_usd += (used_in * price_in + used_out * price_out) / 1_000_000

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def exhausted(self) -> bool:
        try:
            self.check_message()
        except BudgetExhausted:
            return True
        return False

    def as_log_record(self) -> dict[str, Any]:
        return {
            "messages_handled": self.messages_handled,
            "messages_max": self.max_messages,
            "provider_calls": self.provider_calls,
            "provider_calls_max": self.max_provider_calls,
            "tokens_used": self.total_tokens,
            "tokens_max": self.max_tokens,
            "cost_usd_estimated": round(self.cost_usd, 4),
            "cost_usd_max": self.max_cost_usd,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "runtime_seconds_max": self.max_runtime_seconds,
        }


def _positive_int(environment: dict[str, str], name: str, default: int) -> int:
    raw = environment.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"AGENT_BUDGET_INVALID:{name}") from exc
    if value < 0:
        raise ValueError(f"AGENT_BUDGET_INVALID:{name}")
    return value


def build_budget(environment: dict[str, str] | None = None) -> Budget:
    env = os.environ if environment is None else environment
    raw_cost = env.get("AGENT_MAX_COST_USD", "").strip()
    try:
        cost = float(raw_cost) if raw_cost else DEFAULTS["cost_usd"]
    except ValueError as exc:
        raise ValueError("AGENT_BUDGET_INVALID:AGENT_MAX_COST_USD") from exc

    return Budget(
        max_messages=_positive_int(env, "AGENT_MAX_MESSAGES", DEFAULTS["messages"]),
        max_provider_calls=_positive_int(
            env, "AGENT_MAX_PROVIDER_CALLS", DEFAULTS["provider_calls"]
        ),
        max_tokens=_positive_int(env, "AGENT_MAX_TOKENS", DEFAULTS["tokens"]),
        max_cost_usd=cost,
        max_runtime_seconds=_positive_int(
            env, "AGENT_MAX_RUNTIME_SECONDS", DEFAULTS["runtime_seconds"]
        ),
    )
