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

The cost figure is a conservative safety reservation, not billing. Prices are
read from model_allowlist.py. Before a provider is called, its call slot,
maximum output and conservative input/cost are reserved atomically. Measured
usage reconciles the reservation afterwards; missing usage retains the
conservative amount instead of turning an unknown call into zero cost.

The check runs *before* a message is acknowledged. An exhausted budget must
leave the remaining messages untouched and DELIVERED, so a later run picks
them up - never acknowledged-and-dropped.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any

import model_allowlist

# USD per 1M tokens, for the estimated-cost ceiling. The table comes from the
# model allowlist and is not repeated here: a price and an allowlist entry that
# drift apart would give a defensible-looking estimate for the wrong model.
DEFAULT_PRICES: dict[str, tuple[float, float]] = model_allowlist.prices()

# What an unlisted model is charged at. The allowlist blocks unknown models
# before a call is made, so this should be unreachable - it is the second line,
# and second lines are only worth having if they are not weaker than the first.
# Derived as the **most expensive** entry in the allowlist rather than written
# down, so a new, dearer model raises the fallback by itself instead of
# quietly making the ceiling harder to reach.
FALLBACK_PRICE = (
    max((p[0] for p in DEFAULT_PRICES.values()), default=0.0),
    max((p[1] for p in DEFAULT_PRICES.values()), default=0.0),
)

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


@dataclass(frozen=True)
class ProviderReservation:
    """One in-flight provider call, reserved before external work starts."""

    reservation_id: int
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


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
    estimated_usage_calls: int = 0
    _reserved_input_tokens: int = field(default=0, init=False, repr=False)
    _reserved_output_tokens: int = field(default=0, init=False, repr=False)
    _reserved_cost_usd: float = field(default=0.0, init=False, repr=False)
    _next_reservation_id: int = field(default=1, init=False, repr=False)
    _reservations: dict[int, ProviderReservation] = field(
        default_factory=dict, init=False, repr=False)
    _lock: Any = field(default_factory=threading.Lock, init=False, repr=False)

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
        with self._lock:
            elapsed = self.elapsed_seconds
            if elapsed >= self.max_runtime_seconds:
                raise BudgetExhausted(
                    "runtime_seconds", elapsed, self.max_runtime_seconds
                )
            if self.messages_handled >= self.max_messages:
                raise BudgetExhausted(
                    "messages", self.messages_handled, self.max_messages)
            if self.provider_calls >= self.max_provider_calls:
                raise BudgetExhausted(
                    "provider_calls", self.provider_calls, self.max_provider_calls
                )
            if self.total_tokens + self.reserved_tokens >= self.max_tokens:
                raise BudgetExhausted(
                    "tokens", self.total_tokens + self.reserved_tokens,
                    self.max_tokens)
            if (self.cost_usd + self._reserved_cost_usd > 0
                    and self.cost_usd + self._reserved_cost_usd
                    >= self.max_cost_usd):
                raise BudgetExhausted(
                    "cost_usd", self.cost_usd + self._reserved_cost_usd,
                    self.max_cost_usd)

    # -- accounting -------------------------------------------------------
    def record_message(self) -> None:
        self.messages_handled += 1

    def reserve_provider_call(
        self,
        *,
        model: model_allowlist.Model,
        system: str,
        content: str,
        is_paid: bool,
    ) -> ProviderReservation:
        """Atomically reserve every provider-related ceiling before the call.

        The call slot is never returned: a failed attempt still happened. The
        token/cost reservation is reconciled with measured usage on success;
        a failure or missing usage consumes the conservative reservation.
        """
        reserve_in = model_allowlist.conservative_input_tokens(
            system=system, content=content)
        reserve_out = model.max_output_tokens
        reserve_cost = model.estimated_cost(reserve_in, reserve_out)

        with self._lock:
            if self.provider_calls + 1 > self.max_provider_calls:
                raise BudgetExhausted(
                    "provider_calls", self.provider_calls + 1,
                    self.max_provider_calls)
            projected_tokens = (
                self.total_tokens + self.reserved_tokens
                + reserve_in + reserve_out
            )
            if projected_tokens > self.max_tokens:
                raise BudgetExhausted("tokens", projected_tokens, self.max_tokens)
            projected_cost = self.cost_usd + self._reserved_cost_usd + reserve_cost
            if is_paid and self.max_cost_usd <= 0:
                raise BudgetExhausted("cost_usd", projected_cost, self.max_cost_usd)
            if projected_cost > self.max_cost_usd:
                raise BudgetExhausted("cost_usd", projected_cost, self.max_cost_usd)

            reservation = ProviderReservation(
                reservation_id=self._next_reservation_id,
                model=model.name,
                input_tokens=reserve_in,
                output_tokens=reserve_out,
                cost_usd=reserve_cost,
            )
            self._next_reservation_id += 1
            self.provider_calls += 1
            self._reserved_input_tokens += reserve_in
            self._reserved_output_tokens += reserve_out
            self._reserved_cost_usd += reserve_cost
            self._reservations[reservation.reservation_id] = reservation
            return reservation

    def _take_reservation(
        self, reservation: ProviderReservation
    ) -> ProviderReservation:
        current = self._reservations.pop(reservation.reservation_id, None)
        if current != reservation:
            raise ValueError("AGENT_BUDGET_RESERVATION_UNKNOWN")
        self._reserved_input_tokens -= current.input_tokens
        self._reserved_output_tokens -= current.output_tokens
        self._reserved_cost_usd -= current.cost_usd
        return current

    def record_provider_usage(
        self,
        *,
        reservation: ProviderReservation,
        model: str,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> None:
        """Reconcile one reservation with measured or conservative usage."""
        # Validate before consuming the reservation. A malformed SDK usage
        # record must not make the corresponding in-flight charge disappear.
        if input_tokens is not None and input_tokens < 0:
            raise ValueError("AGENT_BUDGET_USAGE_INVALID")
        if output_tokens is not None and output_tokens < 0:
            raise ValueError("AGENT_BUDGET_USAGE_INVALID")
        with self._lock:
            current = self._take_reservation(reservation)
            missing = input_tokens is None or output_tokens is None
            used_in = current.input_tokens if input_tokens is None else input_tokens
            used_out = current.output_tokens if output_tokens is None else output_tokens
            self.input_tokens += used_in
            self.output_tokens += used_out
            price_in, price_out = self.prices.get(model, FALLBACK_PRICE)
            self.cost_usd += (
                used_in * price_in + used_out * price_out
            ) / 1_000_000
            if missing:
                self.estimated_usage_calls += 1

    def record_provider_failure(self, reservation: ProviderReservation) -> None:
        """A failed external attempt keeps its conservative token/cost charge."""
        with self._lock:
            current = self._take_reservation(reservation)
            self.input_tokens += current.input_tokens
            self.output_tokens += current.output_tokens
            self.cost_usd += current.cost_usd
            self.estimated_usage_calls += 1

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def reserved_tokens(self) -> int:
        return self._reserved_input_tokens + self._reserved_output_tokens

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
            "tokens_reserved": self.reserved_tokens,
            "tokens_max": self.max_tokens,
            "cost_usd_estimated": round(self.cost_usd, 4),
            "cost_usd_reserved": round(self._reserved_cost_usd, 4),
            "cost_usd_max": self.max_cost_usd,
            "usage_estimated_calls": self.estimated_usage_calls,
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
