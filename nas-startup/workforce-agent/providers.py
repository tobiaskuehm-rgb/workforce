"""Model providers behind one narrow interface.

A provider takes a system prompt and one block of already-filtered content and
returns text. That is the entire contract. It cannot call tools, read files or
reach the bus - see agent_worker.py for why that matters.

Adding a provider means implementing `complete()` and registering it in
`build_provider()`. Nothing else in the package changes.

Available today:
  claude  the Anthropic API via the official SDK (default)
  echo    deterministic, no network, no credentials - for tests and dry runs
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

# A bus body is capped at max_body_chars (8000 today) and the reply has to fit,
# so a deliberately small output ceiling is correct here rather than a lowball.
# Roughly 4 chars per token leaves comfortable headroom over 8000 chars.
MAX_REPLY_TOKENS = 4096

DEFAULT_CLAUDE_MODEL = "claude-opus-5"


class ProviderError(RuntimeError):
    """Provider failed in a way the worker should report, not crash on."""


@dataclass(frozen=True)
class Reply:
    text: str
    provider: str
    model: str
    refused: bool = False
    refusal_category: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    def as_log_record(self) -> dict[str, Any]:
        """Metadata only - never the reply text."""
        return {
            "provider": self.provider,
            "model": self.model,
            "refused": self.refused,
            "refusal_category": self.refusal_category,
            "reply_chars": len(self.text),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


class Provider(Protocol):
    name: str
    # Whether asking this provider costs money. Declared rather than inferred,
    # so a cost ceiling can be enforced *before* the first call instead of
    # after it (review finding G-004). Cost is only known once a call returns,
    # so without this a ceiling of 0.00 could not stop a paid provider at all.
    is_paid: bool

    def complete(self, *, system: str, content: str) -> Reply:
        """Answer one request. Must not raise for ordinary model refusals."""
        ...


class EchoProvider:
    """Deterministic stand-in. No network, no API key, no cost.

    Used by the test suite and by AGENT_PROVIDER=echo for a dry run that
    exercises the whole bus path without involving an external service.
    """

    name = "echo"
    is_paid = False

    def __init__(self, model: str = "echo-v1") -> None:
        self.model = model

    def complete(self, *, system: str, content: str) -> Reply:
        lines = [line for line in content.splitlines() if line.startswith("subject:")]
        subject = lines[0][len("subject:"):].strip() if lines else "ohne Betreff"
        return Reply(
            text=(
                f"Automatische Testantwort zu: {subject}\n"
                "Dieser Lauf verwendet den Echo-Provider. Es war kein Modell "
                "beteiligt und es haben keine Daten die NAS verlassen."
            ),
            provider=self.name,
            model=self.model,
        )


class ClaudeProvider:
    """Anthropic API via the official SDK."""

    name = "claude"
    is_paid = True

    def __init__(
        self,
        model: str = DEFAULT_CLAUDE_MODEL,
        *,
        api_key: str | None = None,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - import guard
            raise ProviderError("AGENT_ANTHROPIC_SDK_MISSING") from exc

        self._anthropic = anthropic
        self.model = model
        # A zero-arg client resolves ANTHROPIC_API_KEY or an `ant auth login`
        # profile on its own; only pass a key when one was handed to us.
        self._client = (
            anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=max_retries)
            if api_key
            else anthropic.Anthropic(timeout=timeout, max_retries=max_retries)
        )

    def complete(self, *, system: str, content: str) -> Reply:
        anthropic = self._anthropic
        try:
            response = self._client.beta.messages.create(
                model=self.model,
                max_tokens=MAX_REPLY_TOKENS,
                system=system,
                messages=[{"role": "user", "content": content}],
                thinking={"type": "adaptive"},
                output_config={"effort": "medium"},
                # Opt in to server-side refusal fallbacks: on a policy decline
                # the request is re-run on a fallback model inside the same
                # call, so a borderline work item still gets an answer instead
                # of silently stalling in the bus.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.RateLimitError as exc:
            raise ProviderError("AGENT_PROVIDER_RATE_LIMITED") from exc
        except anthropic.AuthenticationError as exc:
            raise ProviderError("AGENT_PROVIDER_AUTH_FAILED") from exc
        except anthropic.BadRequestError as exc:
            raise ProviderError("AGENT_PROVIDER_REQUEST_INVALID") from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderError("AGENT_PROVIDER_UNREACHABLE") from exc
        except anthropic.APIStatusError as exc:
            raise ProviderError(f"AGENT_PROVIDER_HTTP_{exc.status_code}") from exc

        usage = getattr(response, "usage", None)
        common = {
            "provider": self.name,
            "model": getattr(response, "model", self.model),
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
        }

        # Check stop_reason before reading content: a refusal is an HTTP 200.
        if getattr(response, "stop_reason", None) == "refusal":
            details = getattr(response, "stop_details", None)
            return Reply(
                text=(
                    "Diese Anfrage wurde vom Modell aus Sicherheitsgruenden "
                    "nicht bearbeitet. Bitte fachlich pruefen."
                ),
                refused=True,
                refusal_category=getattr(details, "category", None),
                **common,
            )

        text = "\n".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        if not text:
            raise ProviderError("AGENT_PROVIDER_EMPTY_REPLY")

        return Reply(text=text, **common)


def read_api_key(environment: dict[str, str]) -> str | None:
    """Prefer a key file over an environment variable.

    Same pattern the rest of this project uses for the bus and bot tokens: a
    secret in a file cannot be read out of `docker inspect` or a process
    listing the way an environment variable can.

    `AGENT_STRICT_SECRETS=true` removes the environment fallback entirely and
    refuses to start rather than accept a key that way (review finding G-010).
    The NAS profiles set it; local experiments outside Docker do not, which is
    the only place the fallback is worth having.
    """
    strict = environment.get("AGENT_STRICT_SECRETS", "").strip().lower() == "true"

    key_file = environment.get("ANTHROPIC_API_KEY_FILE", "").strip()
    if key_file:
        with open(key_file, encoding="utf-8") as handle:
            key = handle.read().strip()
        if not key:
            raise ProviderError(f"AGENT_PROVIDER_KEY_FILE_EMPTY:{key_file}")
        return key

    if environment.get("ANTHROPIC_API_KEY"):
        if strict:
            # Refusing to start beats starting with a secret that any
            # `docker inspect` can read back.
            raise ProviderError("AGENT_PROVIDER_KEY_FROM_ENVIRONMENT_REFUSED")
        return environment["ANTHROPIC_API_KEY"]

    if strict:
        raise ProviderError("AGENT_PROVIDER_KEY_FILE_REQUIRED")
    return None


def build_provider(environment: dict[str, str] | None = None) -> Provider:
    env = os.environ if environment is None else environment
    name = env.get("AGENT_PROVIDER", "claude").strip().lower()

    if name == "echo":
        return EchoProvider()
    if name == "claude":
        try:
            api_key = read_api_key(env)
        except OSError as exc:
            raise ProviderError("AGENT_PROVIDER_KEY_FILE_UNREADABLE") from exc
        return ClaudeProvider(
            model=env.get("AGENT_MODEL", DEFAULT_CLAUDE_MODEL).strip()
            or DEFAULT_CLAUDE_MODEL,
            api_key=api_key,
        )
    raise ProviderError(f"AGENT_PROVIDER_UNKNOWN:{name}")
