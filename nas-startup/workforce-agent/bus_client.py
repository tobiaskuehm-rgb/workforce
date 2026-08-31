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

    # -- Tasks -------------------------------------------------------------
    # ENG-008 needs the full lifecycle, not just messages. The API already
    # exposes these; the client simply never used them.

    def tasks(self, scope: str = "OWNED", limit: int = 50) -> list[dict[str, Any]]:
        return self._call("GET", f"/bus/v1/tasks?scope={scope}&limit={limit}")

    def create_task(
        self,
        *,
        task_id: str,
        owner_id: str,
        title: str,
        expected_output: str,
        source_ref: str,
        request_id: str,
        idempotency_key: str,
        task_status: str = "PENDING",
        priority: str = "MEDIUM",
    ) -> dict[str, Any]:
        return self._call(
            "POST",
            "/bus/v1/tasks",
            body={
                "task_id": task_id,
                "owner_id": owner_id,
                "task_status": task_status,
                "priority": priority,
                "title": title,
                "expected_output": expected_output,
                "source_ref": source_ref,
            },
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    def transition_task(
        self,
        task_id: str,
        *,
        new_status: str,
        request_id: str,
        completion_evidence: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"new_status": new_status}
        if completion_evidence is not None:
            # DONE without evidence is refused by the bus itself
            # (BUS_TASK_COMPLETION_EVIDENCE_REQUIRED); passing it only when
            # present keeps that check where it belongs.
            body["completion_evidence"] = completion_evidence[:8000]
        return self._call(
            "POST",
            f"/bus/v1/tasks/{task_id}/transition",
            body=body,
            request_id=request_id,
        )

    # -- Handoffs ----------------------------------------------------------

    def handoffs(self, scope: str = "INBOX", limit: int = 50) -> list[dict[str, Any]]:
        return self._call("GET", f"/bus/v1/handoffs?scope={scope}&limit={limit}")

    def create_handoff(
        self,
        *,
        handoff_id: str,
        recipient_id: str,
        input_summary: str,
        expected_output: str,
        source_ref: str,
        request_id: str,
        idempotency_key: str,
        task_ref: str | None = None,
        handoff_status: str = "PENDING",
        risks_and_assumptions: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "handoff_id": handoff_id,
            "recipient_id": recipient_id,
            "handoff_status": handoff_status,
            "input_summary": input_summary,
            "expected_output": expected_output,
            "source_ref": source_ref,
        }
        if task_ref:
            body["task_ref"] = task_ref
        if risks_and_assumptions:
            body["risks_and_assumptions"] = risks_and_assumptions
        return self._call(
            "POST",
            "/bus/v1/handoffs",
            body=body,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    def transition_handoff(
        self,
        handoff_id: str,
        *,
        new_status: str,
        request_id: str,
        response_note: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"new_status": new_status}
        if response_note is not None:
            body["response_note"] = response_note[:4000]
        return self._call(
            "POST",
            f"/bus/v1/handoffs/{handoff_id}/transition",
            body=body,
            request_id=request_id,
        )

    # -- Messages ----------------------------------------------------------

    def send_message(
        self,
        *,
        recipient_id: str,
        subject: str,
        body: str,
        parent_message_id: str | None,
        request_id: str,
        idempotency_key: str,
        task_ref: str | None = None,
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
        if task_ref:
            payload["task_ref"] = task_ref
        return self._call(
            "POST",
            "/bus/v1/messages",
            body=payload,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )
