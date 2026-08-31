"""Fail-closed Telegram transport for the START-UP Workforce Bus.

The module uses only Python's standard library.  It deliberately keeps Telegram
as a transport boundary: authoritative tasks and messages remain in the
Workforce Bus, while the local SQLite database stores only delivery state and
secret-free audit metadata.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import socket
import sqlite3
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


EMPLOYEE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")
TASK_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")
SOURCE_REF_PATTERN = re.compile(r"^DEC-[0-9]{3}/ENG-[0-9]{3}$")

# What may be forwarded from the bus into the Telegram chat.
#
#   METADATA_ONLY  ids, sender, task reference, delivery status, subject.
#                  Never the message body. The long-standing default and the
#                  only behaviour this connector had before 2026-08-31.
#   BODY           adds a shortened message body, so an answer is actually
#                  readable in Telegram instead of only announced.
#
# Telegram bot chats are cloud chats, not end-to-end encrypted secret chats.
# Moving to BODY means the content of internal work messages is stored on
# Telegram's servers. That is a deliberate decision to be taken by the
# operator, not a default - hence the switch rather than a rewrite.
OUTBOUND_POLICIES = ("METADATA_ONLY", "BODY")

# Hard ceiling regardless of configuration. Telegram itself accepts far more,
# but a short summary is the point: the bus stays the system of record.
MAX_OUTBOUND_BODY_CHARS = 1500
HELP_TEXT = (
    "START-UP Telegram-Pilot\n"
    "/status – technischen Busstatus lesen\n"
    "/task MITARBEITER-ID TASK-ID | Titel | erwarteter Output\n"
    "Neue Aufträge werden ausschließlich als PENDING angelegt."
)


class ConfigurationError(ValueError):
    """Raised when runtime configuration would not be fail-closed."""


class ConnectorError(RuntimeError):
    """Stable, non-secret operational error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _workforce_transport_error(exc: BaseException) -> str:
    """Map transport failures to stable codes without exposing raw details."""

    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, ssl.SSLCertVerificationError):
        return "WORKFORCE_TLS_CERTIFICATE_REJECTED"
    if isinstance(reason, ssl.SSLError):
        return "WORKFORCE_TLS_HANDSHAKE_FAILED"
    if isinstance(reason, socket.gaierror):
        return "WORKFORCE_DNS_UNAVAILABLE"
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "WORKFORCE_CONNECT_TIMEOUT"
    if isinstance(reason, ConnectionRefusedError):
        return "WORKFORCE_CONNECTION_REFUSED"
    if isinstance(reason, OSError):
        if reason.errno == errno.ETIMEDOUT:
            return "WORKFORCE_CONNECT_TIMEOUT"
        if reason.errno == errno.ECONNREFUSED:
            return "WORKFORCE_CONNECTION_REFUSED"
        if reason.errno in {errno.ENETUNREACH, errno.EHOSTUNREACH}:
            return "WORKFORCE_NETWORK_UNREACHABLE"
    return "WORKFORCE_API_UNAVAILABLE"


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError("BOOLEAN_CONFIGURATION_INVALID")


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ConfigurationError(f"{name}_REQUIRED")
    return value


def _secret(env: Mapping[str, str], name: str) -> str:
    direct_value = env.get(name, "").strip()
    file_value = env.get(f"{name}_FILE", "").strip()
    if direct_value and file_value:
        raise ConfigurationError(f"{name}_SOURCE_CONFLICT")
    if file_value:
        try:
            value = Path(file_value).read_text(encoding="utf-8").strip()
        except OSError:
            raise ConfigurationError(f"{name}_FILE_UNREADABLE") from None
        if not value:
            raise ConfigurationError(f"{name}_FILE_EMPTY")
        return value
    if direct_value:
        return direct_value
    raise ConfigurationError(f"{name}_REQUIRED")


@dataclass(frozen=True)
class Settings:
    enabled: bool
    kill_switch: bool
    allowed_chat_id: int
    allowed_user_id: int
    allowed_recipient_ids: frozenset[str]
    workforce_base_url: str
    state_path: Path
    allowed_task_ids: frozenset[str] = field(default_factory=frozenset)
    source_ref: str = "DEC-023/ENG-007"
    poll_timeout_seconds: int = 25
    # What of an inbound bus message may be forwarded into the Telegram chat.
    # This is the second data boundary in the chain: the first governs what
    # reaches a model provider (workforce-agent/data_boundary.py), this one
    # governs what reaches Telegram. Telegram bot chats are cloud chats, not
    # end-to-end encrypted, so the default stays metadata-only - exactly the
    # behaviour this connector has always had.
    outbound_policy: str = "METADATA_ONLY"
    outbound_body_chars: int = 500
    telegram_bot_token: str = field(default="", repr=False)
    workforce_bus_token: str = field(default="", repr=False)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if env is None else env
        enabled = _parse_bool(values.get("TELEGRAM_CONNECTOR_ENABLED"), default=False)
        kill_switch = _parse_bool(values.get("TELEGRAM_KILL_SWITCH"), default=True)

        if not enabled:
            raise ConfigurationError("TELEGRAM_CONNECTOR_DISABLED")

        telegram_bot_token = _secret(values, "TELEGRAM_BOT_TOKEN")
        workforce_bus_token = _secret(values, "WORKFORCE_BUS_TOKEN")
        base_url = _required(values, "WORKFORCE_API_BASE_URL").rstrip("/")
        if urllib.parse.urlparse(base_url).scheme.lower() != "https":
            raise ConfigurationError("WORKFORCE_HTTPS_REQUIRED")

        try:
            allowed_chat_id = int(_required(values, "TELEGRAM_ALLOWED_CHAT_ID"))
            allowed_user_id = int(_required(values, "TELEGRAM_ALLOWED_USER_ID"))
        except ValueError as exc:
            raise ConfigurationError("TELEGRAM_ALLOWLIST_ID_INVALID") from exc

        recipient_text = _required(values, "TELEGRAM_ALLOWED_RECIPIENT_IDS")
        recipients = frozenset(
            item.strip() for item in recipient_text.split(",") if item.strip()
        )
        if not recipients or any(not EMPLOYEE_ID_PATTERN.fullmatch(item) for item in recipients):
            raise ConfigurationError("RECIPIENT_ALLOWLIST_INVALID")

        task_id_text = _required(values, "TELEGRAM_ALLOWED_TASK_IDS")
        allowed_task_ids = frozenset(
            item.strip() for item in task_id_text.split(",") if item.strip()
        )
        if not allowed_task_ids or any(
            not TASK_ID_PATTERN.fullmatch(item) for item in allowed_task_ids
        ):
            raise ConfigurationError("TASK_ALLOWLIST_INVALID")

        source_ref = values.get("TELEGRAM_SOURCE_REF", "DEC-023/ENG-007").strip()
        if not SOURCE_REF_PATTERN.fullmatch(source_ref):
            raise ConfigurationError("TELEGRAM_SOURCE_REF_INVALID")

        try:
            poll_timeout = int(values.get("TELEGRAM_POLL_TIMEOUT_SECONDS", "25"))
        except ValueError as exc:
            raise ConfigurationError("POLL_TIMEOUT_INVALID") from exc
        if not 1 <= poll_timeout <= 50:
            raise ConfigurationError("POLL_TIMEOUT_INVALID")

        outbound_policy = values.get(
            "TELEGRAM_OUTBOUND_POLICY", "METADATA_ONLY"
        ).strip().upper()
        if outbound_policy not in OUTBOUND_POLICIES:
            raise ConfigurationError("TELEGRAM_OUTBOUND_POLICY_INVALID")

        try:
            outbound_body_chars = int(values.get("TELEGRAM_OUTBOUND_BODY_CHARS", "500"))
        except ValueError as exc:
            raise ConfigurationError("TELEGRAM_OUTBOUND_BODY_CHARS_INVALID") from exc
        if not 1 <= outbound_body_chars <= MAX_OUTBOUND_BODY_CHARS:
            raise ConfigurationError("TELEGRAM_OUTBOUND_BODY_CHARS_INVALID")

        return cls(
            enabled=enabled,
            kill_switch=kill_switch,
            telegram_bot_token=telegram_bot_token,
            allowed_chat_id=allowed_chat_id,
            allowed_user_id=allowed_user_id,
            allowed_recipient_ids=recipients,
            allowed_task_ids=allowed_task_ids,
            source_ref=source_ref,
            workforce_base_url=base_url,
            workforce_bus_token=workforce_bus_token,
            state_path=Path(
                values.get(
                    "TELEGRAM_STATE_PATH",
                    "/var/lib/startup-telegram/state.sqlite3",
                )
            ),
            poll_timeout_seconds=poll_timeout,
            outbound_policy=outbound_policy,
            outbound_body_chars=outbound_body_chars,
        )


class TelegramTransport(Protocol):
    def get_updates(self, offset: int, timeout_seconds: int) -> Sequence[dict[str, Any]]: ...

    def send_message(self, chat_id: int, text: str) -> None: ...


class WorkforceGateway(Protocol):
    def get_status(self) -> Mapping[str, Any]: ...

    def get_inbox(self, limit: int = 20) -> Sequence[Mapping[str, Any]]: ...

    def propose_task(
        self,
        *,
        update_id: int,
        recipient_id: str,
        task_id: str,
        title: str,
        expected_output: str,
    ) -> Mapping[str, Any]: ...


class TelegramBotClient:
    """Small Bot API client.  The token is never included in exceptions."""

    def __init__(self, token: str, *, timeout_seconds: int = 40):
        self._base_url = f"https://api.telegram.org/bot{token}"
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context()

    def _call(self, method: str, payload: Mapping[str, Any]) -> Any:
        body = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/{method}",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self._timeout_seconds,
                context=self._ssl_context,
            ) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            raise ConnectorError("TELEGRAM_API_UNAVAILABLE") from None
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise ConnectorError("TELEGRAM_API_REJECTED")
        return result.get("result")

    def get_updates(self, offset: int, timeout_seconds: int) -> Sequence[dict[str, Any]]:
        result = self._call(
            "getUpdates",
            {
                "offset": offset,
                "timeout": timeout_seconds,
                "allowed_updates": json.dumps(["message"]),
            },
        )
        if not isinstance(result, list):
            raise ConnectorError("TELEGRAM_UPDATES_INVALID")
        return [item for item in result if isinstance(item, dict)]

    def send_message(self, chat_id: int, text: str) -> None:
        self._call(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": "true",
            },
        )


class WorkforceApiClient:
    """Narrow client for status plus PENDING task/message creation."""

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        source_ref: str = "DEC-023/ENG-007",
        timeout_seconds: int = 10,
    ):
        if urllib.parse.urlparse(base_url).scheme.lower() != "https":
            raise ConfigurationError("WORKFORCE_HTTPS_REQUIRED")
        if not SOURCE_REF_PATTERN.fullmatch(source_ref):
            raise ConfigurationError("TELEGRAM_SOURCE_REF_INVALID")
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._source_ref = source_ref
        self._timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context()

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, Any] | None = None,
        request_id: str | None = None,
        idempotency_key: str | None = None,
        authenticated: bool = True,
    ) -> Any:
        headers = {"Accept": "application/json"}
        if authenticated:
            headers["Authorization"] = f"Bearer {self._token}"
        if request_id:
            headers["X-Request-ID"] = request_id
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        body = None
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self._base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self._timeout_seconds,
                context=self._ssl_context,
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            stable = {
                400: "WORKFORCE_REQUEST_INVALID",
                401: "WORKFORCE_AUTH_FAILED",
                403: "WORKFORCE_ACCESS_DENIED",
                404: "WORKFORCE_RECORD_NOT_FOUND",
                409: "WORKFORCE_CONFLICT",
                503: "WORKFORCE_CHANNEL_UNAVAILABLE",
            }.get(exc.code, "WORKFORCE_API_REJECTED")
            raise ConnectorError(stable) from None
        except urllib.error.URLError as exc:
            raise ConnectorError(_workforce_transport_error(exc)) from None
        except (TimeoutError, socket.timeout) as exc:
            raise ConnectorError(_workforce_transport_error(exc)) from None
        except json.JSONDecodeError:
            raise ConnectorError("WORKFORCE_RESPONSE_INVALID") from None

    def get_status(self) -> Mapping[str, Any]:
        result = self._request("GET", "/bus/v1/status", authenticated=False)
        if not isinstance(result, dict):
            raise ConnectorError("WORKFORCE_STATUS_INVALID")
        return result

    def get_inbox(self, limit: int = 20) -> Sequence[Mapping[str, Any]]:
        result = self._request(
            "GET",
            f"/bus/v1/messages?scope=INBOX&limit={min(max(limit, 1), 20)}",
        )
        if not isinstance(result, list) or any(not isinstance(item, dict) for item in result):
            raise ConnectorError("WORKFORCE_INBOX_INVALID")
        return result

    def propose_task(
        self,
        *,
        update_id: int,
        recipient_id: str,
        task_id: str,
        title: str,
        expected_output: str,
    ) -> Mapping[str, Any]:
        request_prefix = f"TG-{update_id}"
        task = self._request(
            "POST",
            "/bus/v1/tasks",
            payload={
                "task_id": task_id,
                "owner_id": recipient_id,
                "task_status": "PENDING",
                "priority": "MEDIUM",
                "title": title,
                "expected_output": expected_output,
                "source_ref": self._source_ref,
                "review_at": None,
            },
            request_id=f"{request_prefix}-TASK",
        )
        message = self._request(
            "POST",
            "/bus/v1/messages",
            payload={
                "recipient_id": recipient_id,
                "subject": f"CEO-Pilotauftrag {task_id}",
                "body": f"{title}\nErwarteter Output: {expected_output}",
                "action_class": "INTERNAL_COORDINATION",
                "confidentiality": "NEED_TO_KNOW",
                "task_ref": task_id,
                "handoff_ref": None,
                "parent_message_id": None,
            },
            request_id=f"{request_prefix}-MESSAGE",
            idempotency_key=f"IDEM-TG-{update_id}-MESSAGE",
        )
        return {"task": task, "message": message}


class AuditStore:
    """Append-only audit metadata plus Telegram update deduplication."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS processed_updates (
                update_id INTEGER PRIMARY KEY,
                payload_hash TEXT NOT NULL,
                processing_status TEXT NOT NULL
                    CHECK (processing_status IN ('CLAIMED', 'PROCESSED', 'FAILED')),
                created_at TEXT NOT NULL,
                finished_at TEXT
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_id INTEGER,
                event_type TEXT NOT NULL,
                outcome TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS connector_state (
                state_key TEXT PRIMARY KEY,
                state_value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS outbound_deliveries (
                message_id TEXT PRIMARY KEY,
                payload_hash TEXT NOT NULL,
                delivery_status TEXT NOT NULL
                    CHECK (delivery_status IN ('CLAIMED', 'SENT', 'FAILED')),
                created_at TEXT NOT NULL,
                finished_at TEXT
            );
            """
        )
        self._connection.commit()
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def claim_update(self, update_id: int, payload_hash: str) -> str:
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO processed_updates (
                        update_id, payload_hash, processing_status, created_at
                    ) VALUES (?, ?, 'CLAIMED', ?)
                    """,
                    (update_id, payload_hash, self._now()),
                )
            return "CLAIMED"
        except sqlite3.IntegrityError:
            row = self._connection.execute(
                "SELECT payload_hash FROM processed_updates WHERE update_id = ?",
                (update_id,),
            ).fetchone()
            return "DUPLICATE" if row and row[0] == payload_hash else "CONFLICT"

    def finish_update(self, update_id: int, status: str) -> None:
        if status not in {"PROCESSED", "FAILED"}:
            raise ValueError("UPDATE_STATUS_INVALID")
        with self._connection:
            self._connection.execute(
                """
                UPDATE processed_updates
                SET processing_status = ?, finished_at = ?
                WHERE update_id = ? AND processing_status = 'CLAIMED'
                """,
                (status, self._now(), update_id),
            )

    def claim_notification(self, message_id: str, payload_hash: str) -> str:
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO outbound_deliveries (
                        message_id, payload_hash, delivery_status, created_at
                    ) VALUES (?, ?, 'CLAIMED', ?)
                    """,
                    (message_id, payload_hash, self._now()),
                )
            return "CLAIMED"
        except sqlite3.IntegrityError:
            row = self._connection.execute(
                """
                SELECT payload_hash, delivery_status
                FROM outbound_deliveries WHERE message_id = ?
                """,
                (message_id,),
            ).fetchone()
            if not row or row[0] != payload_hash:
                return "CONFLICT"
            if row[1] == "FAILED":
                with self._connection:
                    self._connection.execute(
                        """
                        UPDATE outbound_deliveries
                        SET delivery_status = 'CLAIMED', finished_at = NULL
                        WHERE message_id = ? AND delivery_status = 'FAILED'
                        """,
                        (message_id,),
                    )
                return "RETRY"
            return "DUPLICATE"

    def finish_notification(self, message_id: str, status: str) -> None:
        if status not in {"SENT", "FAILED"}:
            raise ValueError("DELIVERY_STATUS_INVALID")
        with self._connection:
            self._connection.execute(
                """
                UPDATE outbound_deliveries
                SET delivery_status = ?, finished_at = ?
                WHERE message_id = ? AND delivery_status = 'CLAIMED'
                """,
                (status, self._now(), message_id),
            )

    def audit(
        self,
        event_type: str,
        outcome: str,
        *,
        update_id: int | None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        safe_metadata = {} if metadata is None else dict(metadata)
        encoded = json.dumps(safe_metadata, sort_keys=True, separators=(",", ":"))
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO audit_events (
                    update_id, event_type, outcome, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (update_id, event_type, outcome, encoded, self._now()),
            )

    def get_offset(self) -> int:
        row = self._connection.execute(
            "SELECT state_value FROM connector_state WHERE state_key = 'telegram_offset'"
        ).fetchone()
        return int(row[0]) if row else 0

    def set_offset(self, offset: int) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO connector_state (state_key, state_value)
                VALUES ('telegram_offset', ?)
                ON CONFLICT(state_key) DO UPDATE SET state_value = excluded.state_value
                """,
                (str(offset),),
            )

    def list_audit(self) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT update_id, event_type, outcome, metadata_json, created_at
            FROM audit_events ORDER BY event_id
            """
        ).fetchall()
        return [
            {
                "update_id": row[0],
                "event_type": row[1],
                "outcome": row[2],
                "metadata": json.loads(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]

    def close(self) -> None:
        self._connection.close()


@dataclass(frozen=True)
class TaskCommand:
    recipient_id: str
    task_id: str
    title: str
    expected_output: str


def parse_task_command(
    text: str,
    allowed_recipients: frozenset[str],
    allowed_task_ids: frozenset[str] = frozenset(),
) -> TaskCommand:
    sections = [section.strip() for section in text.split("|")]
    if len(sections) != 3:
        raise ConnectorError("TASK_COMMAND_FORMAT_INVALID")
    head = sections[0].split()
    if len(head) != 3 or head[0].split("@", 1)[0].lower() != "/task":
        raise ConnectorError("TASK_COMMAND_FORMAT_INVALID")
    recipient_id, task_id = head[1], head[2]
    if recipient_id not in allowed_recipients:
        raise ConnectorError("RECIPIENT_NOT_ALLOWED")
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise ConnectorError("TASK_ID_INVALID")
    if task_id not in allowed_task_ids:
        raise ConnectorError("TASK_ID_NOT_ALLOWED")
    title, expected_output = sections[1], sections[2]
    if not 1 <= len(title) <= 240:
        raise ConnectorError("TASK_TITLE_INVALID")
    if not 1 <= len(expected_output) <= 4000:
        raise ConnectorError("TASK_OUTPUT_INVALID")
    return TaskCommand(recipient_id, task_id, title, expected_output)


class TelegramConnector:
    def __init__(
        self,
        settings: Settings,
        store: AuditStore,
        telegram: TelegramTransport,
        workforce: WorkforceGateway,
    ):
        self.settings = settings
        self.store = store
        self.telegram = telegram
        self.workforce = workforce

    @staticmethod
    def _fingerprint(update: Mapping[str, Any]) -> str:
        encoded = json.dumps(update, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _message_fields(update: Mapping[str, Any]) -> tuple[int, int, str, str]:
        message = update.get("message")
        if not isinstance(message, dict):
            raise ConnectorError("TELEGRAM_MESSAGE_REQUIRED")
        chat = message.get("chat")
        sender = message.get("from")
        text = message.get("text")
        if not isinstance(chat, dict) or not isinstance(sender, dict) or not isinstance(text, str):
            raise ConnectorError("TELEGRAM_TEXT_MESSAGE_REQUIRED")
        try:
            chat_id = int(chat["id"])
            user_id = int(sender["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ConnectorError("TELEGRAM_IDENTITY_INVALID") from exc
        chat_type = str(chat.get("type", ""))
        return chat_id, user_id, chat_type, text.strip()

    def _reply(self, chat_id: int, text: str, update_id: int) -> None:
        self.telegram.send_message(chat_id, text)
        self.store.audit(
            "TELEGRAM_REPLY_SENT",
            "PASS",
            update_id=update_id,
            metadata={"reply_code": text.split(" ", 1)[0], "text_length": len(text)},
        )

    def process_update(self, update: Mapping[str, Any]) -> str:
        raw_update_id = update.get("update_id")
        if not isinstance(raw_update_id, int) or raw_update_id < 0:
            self.store.audit(
                "UPDATE_REJECTED",
                "DENY",
                update_id=None,
                metadata={"reason": "UPDATE_ID_INVALID"},
            )
            return "REJECTED"
        update_id = raw_update_id
        claim = self.store.claim_update(update_id, self._fingerprint(update))
        if claim != "CLAIMED":
            event = "DUPLICATE_IGNORED" if claim == "DUPLICATE" else "IDEMPOTENCY_CONFLICT"
            self.store.audit(
                event,
                "DENY",
                update_id=update_id,
                metadata={"reason": claim},
            )
            return claim

        self.store.audit("UPDATE_RECEIVED", "PASS", update_id=update_id)
        authorized_chat_id: int | None = None
        try:
            chat_id, user_id, chat_type, text = self._message_fields(update)
            authorized_chat_id = chat_id
            if not self.settings.enabled or self.settings.kill_switch:
                self.store.audit(
                    "KILL_SWITCH_BLOCK",
                    "DENY",
                    update_id=update_id,
                    metadata={"reason": "CONNECTOR_NOT_ACTIVE"},
                )
                self.store.finish_update(update_id, "PROCESSED")
                return "BLOCKED"
            if (
                chat_type != "private"
                or chat_id != self.settings.allowed_chat_id
                or user_id != self.settings.allowed_user_id
            ):
                self.store.audit(
                    "ACCESS_DENIED",
                    "DENY",
                    update_id=update_id,
                    metadata={"chat_type": chat_type, "reason": "CEO_ALLOWLIST_MISMATCH"},
                )
                self.store.finish_update(update_id, "PROCESSED")
                return "DENIED"
            if not text or len(text) > 4500:
                raise ConnectorError("COMMAND_TEXT_INVALID")

            command_name = text.split(None, 1)[0].split("@", 1)[0].lower()
            if command_name in {"/start", "/help"}:
                self._reply(chat_id, HELP_TEXT, update_id)
                event_type = "HELP_RETURNED"
            elif command_name == "/status":
                status = self.workforce.get_status()
                safe_status = {
                    "Projekt": status.get("project_id", "UNKNOWN"),
                    "API": status.get("api_version", "UNKNOWN"),
                    "Kanal": status.get("channel_status", "UNKNOWN"),
                }
                response = "STATUS " + " · ".join(
                    f"{key}={value}" for key, value in safe_status.items()
                )
                self._reply(chat_id, response, update_id)
                event_type = "STATUS_RETURNED"
            elif command_name == "/task":
                command = parse_task_command(
                    text,
                    self.settings.allowed_recipient_ids,
                    self.settings.allowed_task_ids,
                )
                self.workforce.propose_task(
                    update_id=update_id,
                    recipient_id=command.recipient_id,
                    task_id=command.task_id,
                    title=command.title,
                    expected_output=command.expected_output,
                )
                self.store.audit(
                    "TASK_PROPOSED",
                    "PASS",
                    update_id=update_id,
                    metadata={
                        "recipient_id": command.recipient_id,
                        "task_id": command.task_id,
                        "task_status": "PENDING",
                    },
                )
                self._reply(
                    chat_id,
                    f"PENDING {command.task_id} für {command.recipient_id} registriert.",
                    update_id,
                )
                event_type = "COMMAND_COMPLETED"
            else:
                raise ConnectorError("COMMAND_NOT_ALLOWED")

            self.store.audit(event_type, "PASS", update_id=update_id)
            self.store.finish_update(update_id, "PROCESSED")
            return "PROCESSED"
        except ConnectorError as exc:
            self.store.audit(
                "COMMAND_FAILED",
                "DENY",
                update_id=update_id,
                metadata={"error_code": exc.code},
            )
            if authorized_chat_id == self.settings.allowed_chat_id:
                try:
                    self._reply(
                        authorized_chat_id,
                        f"FEHLER {exc.code}",
                        update_id,
                    )
                except ConnectorError:
                    pass
            self.store.finish_update(update_id, "FAILED")
            return "FAILED"
        except Exception:
            self.store.audit(
                "PROCESSING_FAILED",
                "FAIL",
                update_id=update_id,
                metadata={"error_code": "UNEXPECTED_PROCESSING_FAILURE"},
            )
            self.store.finish_update(update_id, "FAILED")
            return "FAILED"

    def poll_once(self) -> int:
        offset = self.store.get_offset()
        updates = self.telegram.get_updates(offset, self.settings.poll_timeout_seconds)
        handled = 0
        for update in sorted(updates, key=lambda item: int(item.get("update_id", -1))):
            self.process_update(update)
            update_id = update.get("update_id")
            if isinstance(update_id, int) and update_id >= 0:
                self.store.set_offset(max(self.store.get_offset(), update_id + 1))
            handled += 1
        self.publish_inbox_notifications()
        return handled

    def _outbound_body(self, message: Mapping[str, Any]) -> str | None:
        """The message body, if and only if the policy allows forwarding it.

        Returns None under METADATA_ONLY - not an empty string - so callers can
        tell "not permitted" apart from "permitted but empty". This is the only
        place a bus body can reach Telegram.
        """
        if self.settings.outbound_policy != "BODY":
            return None
        raw = message.get("body")
        if not isinstance(raw, str):
            return None
        collapsed = " ".join(raw.split())
        if not collapsed:
            return ""
        limit = min(self.settings.outbound_body_chars, MAX_OUTBOUND_BODY_CHARS)
        if len(collapsed) <= limit:
            return collapsed
        return collapsed[: limit - 1].rstrip() + "…"

    def publish_inbox_notifications(self) -> int:
        if not self.settings.enabled or self.settings.kill_switch:
            return 0
        messages = self.workforce.get_inbox(limit=20)
        sent = 0
        for message in reversed(messages):
            message_id = str(message.get("message_id", ""))
            sender_id = str(message.get("sender_id", ""))
            if not message_id.startswith("MSG-") or not EMPLOYEE_ID_PATTERN.fullmatch(sender_id):
                self.store.audit(
                    "WORKFORCE_NOTIFICATION_REJECTED",
                    "DENY",
                    update_id=None,
                    metadata={"reason": "MESSAGE_METADATA_INVALID"},
                )
                continue
            task_ref = str(message.get("task_ref") or "-")
            delivery_status = str(message.get("delivery_status") or "UNKNOWN")
            subject = " ".join(str(message.get("subject") or "Ohne Betreff").split())[:120]
            safe_payload = {
                "message_id": message_id,
                "sender_id": sender_id,
                "task_ref": task_ref,
                "delivery_status": delivery_status,
                "subject": subject,
            }
            # The fingerprint identifies the bus message, not how it is
            # rendered - so the body excerpt stays out of it deliberately.
            # One bus message yields at most one Telegram notification, ever.
            # Including the rendering would make a policy change re-notify
            # every already-announced message at once, which is a notification
            # storm, not a feature. A changed policy applies to what comes
            # after it.
            body_excerpt = self._outbound_body(message)
            payload_hash = hashlib.sha256(
                json.dumps(safe_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            claim = self.store.claim_notification(message_id, payload_hash)
            if claim in {"DUPLICATE", "CONFLICT"}:
                self.store.audit(
                    "WORKFORCE_NOTIFICATION_SKIPPED",
                    "DENY",
                    update_id=None,
                    metadata={"message_id": message_id, "reason": claim},
                )
                continue
            notification = (
                f"NACHRICHT {message_id} von {sender_id}\n"
                f"Task={task_ref} · Status={delivery_status}\n"
                f"Betreff: {subject}"
            )
            if body_excerpt:
                notification += f"\n\n{body_excerpt}"

            try:
                self.telegram.send_message(self.settings.allowed_chat_id, notification)
            except ConnectorError:
                self.store.finish_notification(message_id, "FAILED")
                self.store.audit(
                    "WORKFORCE_NOTIFICATION_FAILED",
                    "FAIL",
                    update_id=None,
                    metadata={"message_id": message_id},
                )
                continue
            self.store.finish_notification(message_id, "SENT")
            self.store.audit(
                "WORKFORCE_NOTIFICATION_SENT",
                "PASS",
                update_id=None,
                metadata={
                    "message_id": message_id,
                    "sender_id": sender_id,
                    "task_ref": task_ref,
                },
            )
            sent += 1
        return sent

    def run_forever(self) -> None:
        while True:
            try:
                self.poll_once()
            except ConnectorError as exc:
                self.store.audit(
                    "POLL_FAILED",
                    "FAIL",
                    update_id=None,
                    metadata={"error_code": exc.code},
                )
                time.sleep(5)


def build_connector(settings: Settings) -> TelegramConnector:
    store = AuditStore(settings.state_path)
    telegram = TelegramBotClient(settings.telegram_bot_token)
    workforce = WorkforceApiClient(
        settings.workforce_base_url,
        settings.workforce_bus_token,
        source_ref=settings.source_ref,
    )
    return TelegramConnector(settings, store, telegram, workforce)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="START-UP Telegram CEO connector")
    parser.add_argument("--once", action="store_true", help="poll exactly once")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="validate fail-closed configuration without network access",
    )
    args = parser.parse_args(argv)
    try:
        settings = Settings.from_env()
    except ConfigurationError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 2
    if settings.kill_switch:
        print(json.dumps({"status": "blocked", "reason": "TELEGRAM_KILL_SWITCH_ACTIVE"}))
        return 2
    if args.check_config:
        print(json.dumps({"status": "ok", "network_access": False}))
        return 0

    connector = build_connector(settings)
    if args.once:
        handled = connector.poll_once()
        print(json.dumps({"status": "ok", "handled_updates": handled}))
        return 0
    connector.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
