"""Minimal HTTPS client for the Workforce Bus, for one agent identity.

Same transport rules as the realtest package: HTTPS only, bearer token read
from a file, mandatory X-Request-ID and Idempotency-Key on writes. Raw tokens
and full message bodies never reach the log.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

TIMEOUT_SECONDS = 10


class BusError(RuntimeError):
    """A bus call failed. Carries the stable identifier, never a stacktrace."""

    def __init__(self, detail: str, status: int | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status = status


def validate_base_url(value: str) -> str:
    base_url = value.strip().rstrip("/")
    parsed = urllib.parse.urlparse(base_url)
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("AGENT_BUS_BASE_URL_INVALID")
    return base_url


def read_token(token_file: str) -> str:
    with open(token_file, encoding="utf-8") as handle:
        token = handle.read().strip()
    if not 32 <= len(token) <= 512:
        raise ValueError(f"AGENT_BUS_TOKEN_INVALID:{token_file}")
    return token


@dataclass
class BusClient:
    base_url: str
    token: str
    context: ssl.SSLContext | None = None

    def __post_init__(self) -> None:
        self.base_url = validate_base_url(self.base_url)
        if self.context is None:
            self.context = ssl.create_default_context()

    def _call(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        request_id: str | None = None,
        idempotency_key: str | None = None,
        authenticated: bool = True,
    ) -> Any:
        headers = {"Accept": "application/json"}
        if authenticated:
            headers["Authorization"] = f"Bearer {self.token}"
        if request_id:
            headers["X-Request-ID"] = request_id
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            f"{self.base_url}{path}", data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(
                request, timeout=TIMEOUT_SECONDS, context=self.context
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
                detail = payload.get("detail", f"HTTP_{exc.code}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                detail = f"HTTP_{exc.code}"
            raise BusError(str(detail), status=exc.code) from None
        except urllib.error.URLError as exc:
            raise BusError("AGENT_BUS_UNREACHABLE") from None
        except TimeoutError:
            raise BusError("AGENT_BUS_TIMEOUT") from None

    def status(self) -> dict[str, Any]:
        return self._call("GET", "/bus/v1/status", authenticated=False)

    def inbox(self, limit: int = 25) -> list[dict[str, Any]]:
        return self._call("GET", f"/bus/v1/messages?scope=INBOX&limit={limit}")

    def acknowledge(
        self, message_id: str, *, decision: str, note: str, request_id: str
    ) -> dict[str, Any]:
        return self._call(
            "POST",
            f"/bus/v1/messages/{message_id}/ack",
            body={"decision": decision, "note": note[:1000]},
            request_id=request_id,
        )

    def send_message(
        self,
        *,
        recipient_id: str,
        subject: str,
        body: str,
        parent_message_id: str | None,
        request_id: str,
        idempotency_key: str,
        action_class: str = "INTERNAL_COMMUNICATION",
        confidentiality: str = "NEED_TO_KNOW",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "recipient_id": recipient_id,
            "subject": subject,
            "body": body,
            "action_class": action_class,
            "confidentiality": confidentiality,
        }
        if parent_message_id:
            payload["parent_message_id"] = parent_message_id
        return self._call(
            "POST",
            "/bus/v1/messages",
            body=payload,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )
