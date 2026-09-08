"""Model providers behind one narrow interface: text in, text out.

A provider cannot call tools, read files or reach the store. That is the whole
defence against prompt injection: whatever the model says is only ever used as
reply text, and the recipient comes from the record. Standard library only -
the Anthropic Messages API and Ollama's chat API are plain HTTPS/HTTP JSON.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

from . import models

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class ProviderError(RuntimeError):
    """Stable identifier; the caller reports it, it does not crash."""


@dataclass(frozen=True)
class Reply:
    text: str
    model: str
    refused: bool = False
    refusal_category: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


def _post_json(url: str, body: Dict[str, Any], headers: Dict[str, str], timeout: float) -> Dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST",
                                     headers={"content-type": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        codes = {401: "PROVIDER_AUTH_FAILED", 429: "PROVIDER_RATE_LIMITED", 400: "PROVIDER_REQUEST_INVALID"}
        # The error *type* travels as a stable suffix; the message text does not.
        try:
            kind = str(json.loads(exc.read() or b"{}").get("error", {}).get("type", ""))
        except (ValueError, OSError):
            kind = ""
        code = codes.get(exc.code, f"PROVIDER_HTTP_{exc.code}")
        raise ProviderError(f"{code}:{kind}" if kind else code) from exc
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        raise ProviderError("PROVIDER_UNREACHABLE") from exc
    except json.JSONDecodeError as exc:
        raise ProviderError("PROVIDER_BAD_JSON") from exc


class EchoProvider:
    """No network, no key, no cost. For tests and dry runs."""
    name = "echo"
    is_paid = False

    def __init__(self, model: models.Model) -> None:
        self.model = model

    def complete(self, *, system: str, content: str) -> Reply:
        body = [l for l in content.splitlines() if l.startswith("body:")]
        seen = body[0][len("body:"):].strip() if body else "(kein Text)"
        return Reply(text=f"Echo: {seen[:200]}\nKein Modell beteiligt, nichts hat das Haus verlassen.",
                     model=self.model.name)


class OllamaProvider:
    """A local model. Unpaid; nothing leaves the machine."""
    name = "ollama"
    is_paid = False

    def __init__(self, model: models.Model, *, base_url: str, timeout: float = 300.0) -> None:
        try:
            parsed = urllib.parse.urlsplit(base_url)
            port = parsed.port
        except ValueError as exc:
            raise ProviderError("PROVIDER_OLLAMA_ENDPOINT_DENIED") from exc
        if not (
            parsed.scheme == "http"
            and parsed.hostname in ("127.0.0.1", "localhost", "::1", "host.docker.internal")
            and parsed.username is None
            and parsed.password is None
            and parsed.path in ("", "/")
            and not parsed.query
            and not parsed.fragment
            and (port is None or 1 <= port <= 65535)
        ):
            raise ProviderError("PROVIDER_OLLAMA_ENDPOINT_DENIED")
        self.model = model
        self._url = base_url.rstrip("/") + "/api/chat"
        self._timeout = timeout

    def complete(self, *, system: str, content: str) -> Reply:
        response = _post_json(self._url, {
            "model": self.model.name, "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
            "options": {"num_predict": self.model.max_output_tokens},
        }, {}, self._timeout)
        text = str(response.get("message", {}).get("content", "")).strip()
        if not text:
            raise ProviderError("PROVIDER_EMPTY_REPLY")
        return Reply(text=text, model=str(response.get("model", self.model.name)),
                     input_tokens=response.get("prompt_eval_count"),
                     output_tokens=response.get("eval_count"))


class ClaudeProvider:
    """Anthropic Messages API. No SDK, no retries: one reservation is one call."""
    name = "claude"
    is_paid = True

    def __init__(self, model: models.Model, *, api_key: str, workspace_id: str = "", timeout: float = 120.0) -> None:
        self.model = model
        self._key = api_key
        self._timeout = timeout
        # An identity-linked key must name the workspace it acts in (HTTP 400 otherwise).
        self._headers = {"x-api-key": api_key, "anthropic-version": ANTHROPIC_VERSION}
        if workspace_id:
            self._headers["anthropic-workspace-id"] = workspace_id

    def complete(self, *, system: str, content: str) -> Reply:
        response = _post_json(ANTHROPIC_URL, {
            "model": self.model.name, "max_tokens": self.model.max_output_tokens,
            "system": system, "messages": [{"role": "user", "content": content}],
        }, self._headers, self._timeout)
        usage = response.get("usage") or {}
        common = {"model": str(response.get("model", self.model.name)),
                  "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens")}
        if response.get("stop_reason") == "refusal":
            return Reply(text="Das Modell hat diese Anfrage aus Sicherheitsgruenden nicht bearbeitet.",
                         refused=True, refusal_category="refusal", **common)
        text = "\n".join(b.get("text", "") for b in response.get("content", [])
                         if b.get("type") == "text").strip()
        if not text:
            raise ProviderError("PROVIDER_EMPTY_REPLY")
        return Reply(text=text, **common)


def build(provider: str, model_name: str, *, ollama_url: str, api_key: Optional[str],
          workspace_id: str = "") -> Any:
    """The key is only handed in for claude; nobody else may even receive it."""
    model = models.resolve(model_name, provider=provider)
    if provider == "echo":
        return EchoProvider(model)
    if provider == "ollama":
        return OllamaProvider(model, base_url=ollama_url)
    if provider == "claude":
        if not api_key:
            raise ProviderError("PROVIDER_KEY_MISSING")
        return ClaudeProvider(model, api_key=api_key, workspace_id=workspace_id)
    raise ProviderError(f"PROVIDER_UNKNOWN:{provider}")
