"""Model providers behind one narrow interface.

A provider takes a system prompt and one block of already-filtered content and
returns text. That is the entire contract. It cannot call tools, read files or
reach the bus - see agent_worker.py for why that matters.

Adding a provider means implementing `complete()` and registering it in
`build_provider()`. Nothing else in the package changes.

Available today:
  claude        the Anthropic API via the official SDK (default)
  echo          deterministic, no network, no credentials - for tests

Withdrawn:
  subscription  a CLI authenticated by a Claude or ChatGPT subscription. The
                class is still here; build_provider() refuses to return it.
                See SubscriptionProvider for what has to exist first.
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
        # Zero, not three (review finding G-034). The worker reserves exactly
        # one provider call against the budget; an SDK that silently retries
        # would turn that one reservation into several real external calls,
        # and the hard ceiling would stop being hard. Retrying is the worker's
        # decision, made against the budget, not the SDK's.
        max_retries: int = 0,
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


class SubscriptionProvider:
    """WITHDRAWN. A CLI authenticated by a subscription rather than an API key.

    `build_provider()` refuses to hand this out. The class stays here because
    the work is worth keeping and the requirements below are the specification
    for bringing it back - not because it is usable today.

    **Why it was withdrawn (review finding G-016).** The docstring this
    replaces demanded "a container with no mounts, no route to the bus and
    nothing worth reaching" and then ran `subprocess.run()` inside the worker
    container, which has the bus token, the persistent state mount, a route to
    the bus and, during a model run, a route to the internet. Clearing the
    inherited environment removes variables; it does not remove the file system
    or the network. The control the comment described did not exist.

    That gap is worse than a missing control. These CLIs exist to *act* - read
    files, run commands, reach the network - and the whole argument for
    pointing this agent at untrusted message content is that a successful
    prompt injection has nothing to act on. A comment claiming isolation that
    is not there tells the next reader not to check.

    **What it would take to reinstate:**

    1. A provider container of its own, short-lived, with no bus token, no
       state mount, no project mount and no route to the NAS bus - only the
       one external destination the CLI needs.
    2. A text-in/text-out channel between worker and that container, narrow
       enough that a compromised CLI can return a string and nothing else.
    3. Hard output and runtime ceilings enforced outside the CLI.
    4. `is_paid = True` (below): a shared subscription quota is a cost even
       when no invoice follows.
    5. A decision that permits the path at all. DEC-027 and ENG-008 rule out
       an external paid service; whether a subscription is one is the CEO's
       call, not this file's.

    Isolation, not flags. A flag that disables tools is welcome, but it is not
    the control - the control is that there is nothing to act on.

    Configure with (once reinstated):
      AGENT_SUBSCRIPTION_COMMAND   argv, JSON list, e.g. ["claude", "-p"]
      AGENT_SUBSCRIPTION_TIMEOUT   seconds, default 180

    The prompt is written to the process's stdin. If your CLI expects it as an
    argument instead, append a placeholder `{prompt}` to the argv and it will
    be substituted.
    """

    name = "subscription"
    # No invoice follows, but the plan's quota is consumed - the same quota the
    # humans use interactively. `is_paid = False` let it past a 0.00 cost
    # ceiling, which is the one gate that can stop a provider before its first
    # call (review findings G-004, G-016). A metered shared resource is a cost.
    is_paid = True

    # Refuses to be selected. Kept as a constant so the test that pins the
    # withdrawal and the error the operator sees cannot drift apart.
    WITHDRAWN_REASON = "AGENT_PROVIDER_SUBSCRIPTION_WITHDRAWN_G016"

    def __init__(self, command: list[str], *, timeout: float = 180.0,
                 model: str = "subscription-cli") -> None:
        if not command:
            raise ProviderError("AGENT_SUBSCRIPTION_COMMAND_MISSING")
        self.command = command
        self.timeout = timeout
        self.model = model

    def complete(self, *, system: str, content: str) -> Reply:
        import subprocess

        prompt = f"{system}\n\n{content}"
        argv = [part.replace("{prompt}", prompt) for part in self.command]
        stdin_input = None if any("{prompt}" in part for part in self.command) else prompt

        try:
            finished = subprocess.run(
                argv,
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                # Nothing inherited: the CLI gets its credentials from its own
                # config, and passing this process's environment could hand it
                # bus tokens or an API key it has no business seeing.
                env={"HOME": os.environ.get("HOME", "/home/startup"),
                     "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")},
            )
        except FileNotFoundError as exc:
            raise ProviderError("AGENT_SUBSCRIPTION_COMMAND_NOT_FOUND") from exc
        except subprocess.TimeoutExpired as exc:
            raise ProviderError("AGENT_SUBSCRIPTION_TIMEOUT") from exc

        if finished.returncode != 0:
            # stderr may carry a rate-limit message; the code is stable, the
            # text is not, so only the code travels.
            raise ProviderError(f"AGENT_SUBSCRIPTION_EXIT_{finished.returncode}")

        text = (finished.stdout or "").strip()
        if not text:
            raise ProviderError("AGENT_SUBSCRIPTION_EMPTY_REPLY")

        return Reply(text=text, provider=self.name, model=self.model)


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
    # No default (review finding G-029). It used to fall back to "claude",
    # so a forgotten variable selected the paid provider - the one choice
    # that costs money and sends content outside. An unset provider is an
    # incomplete configuration, and an incomplete configuration must not
    # decide anything.
    name = env.get("AGENT_PROVIDER", "").strip().lower()
    if not name:
        raise ProviderError("AGENT_PROVIDER_NOT_CONFIGURED")

    if name == "echo":
        return EchoProvider()
    if name == "subscription":
        # Fail closed and say why. Selecting it used to start a tool-capable
        # CLI inside the worker container - see SubscriptionProvider for what
        # has to exist before this line may come back.
        raise ProviderError(SubscriptionProvider.WITHDRAWN_REASON)
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
