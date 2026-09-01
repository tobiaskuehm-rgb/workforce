"""The two faces of ChainWorld, plus a fake Telegram.

Each adapter speaks exactly the interface its real counterpart speaks, and
translates the world's refusals into that side's error type. That translation
is the point: if the connector and the agent disagree about what an error looks
like, the chain breaks there, and this is where it would show.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

_HERE = Path(__file__).resolve().parent
for package in ("telegram-connector", "workforce-agent"):
    candidate = str(_HERE.parent / package)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import bus_client  # noqa: E402  (path set above)
import telegram_connector  # noqa: E402

from chain_world import BusRefusal, ChainWorld  # noqa: E402


class ConnectorGateway:
    """Satisfies telegram_connector.WorkforceGateway."""

    def __init__(self, world: ChainWorld, *, source_ref: str) -> None:
        self.world = world
        self.source_ref = source_ref

    def get_status(self) -> Mapping[str, Any]:
        return self.world.status()

    def get_inbox(self, limit: int = 20) -> Sequence[Mapping[str, Any]]:
        return self.world.inbox(self.world.connector_id, limit=limit)

    def propose_task(self, *, update_id: int, recipient_id: str, task_id: str,
                     title: str, expected_output: str) -> Mapping[str, Any]:
        # Mirrors WorkforceApiClient.propose_task: a task *and* a message that
        # carries the task reference. The message is what the agent answers;
        # the reference is what lets the answer back out again (finding G-003).
        try:
            self.world.create_task(
                sender=self.world.connector_id, task_id=task_id,
                owner_id=recipient_id, title=title,
                expected_output=expected_output, source_ref=self.source_ref,
            )
            return self.world.send_message(
                sender=self.world.connector_id, recipient_id=recipient_id,
                subject=f"CEO-Pilotauftrag {task_id}",
                body=f"{title}\nErwarteter Output: {expected_output}",
                idempotency_key=f"IDEM-TG-{update_id}-MESSAGE",
                task_ref=task_id, action_class="INTERNAL_COORDINATION",
            )
        except BusRefusal as refusal:
            raise telegram_connector.ConnectorError("WORKFORCE_REJECTED") from refusal


class AgentBusClient:
    """Satisfies the subset of bus_client.BusClient the worker uses."""

    def __init__(self, world: ChainWorld) -> None:
        self.world = world

    def status(self) -> dict[str, Any]:
        return self.world.status()

    def inbox(self, limit: int = 25) -> list[dict[str, Any]]:
        return self.world.inbox(self.world.agent_id, limit=limit)

    def acknowledge(self, message_id: str, *, decision: str, note: str,
                    request_id: str) -> dict[str, Any]:
        try:
            return self.world.acknowledge(
                actor=self.world.agent_id, message_id=message_id, decision=decision
            )
        except BusRefusal as refusal:
            raise bus_client.BusError(refusal.detail, status=refusal.status) from None

    def send_message(self, *, recipient_id: str, subject: str, body: str,
                     parent_message_id: str | None, request_id: str,
                     idempotency_key: str, task_ref: str | None = None,
                     **kwargs: Any) -> dict[str, Any]:
        try:
            return self.world.send_message(
                sender=self.world.agent_id, recipient_id=recipient_id,
                subject=subject, body=body, idempotency_key=idempotency_key,
                parent_message_id=parent_message_id, task_ref=task_ref,
            )
        except BusRefusal as refusal:
            raise bus_client.BusError(refusal.detail, status=refusal.status) from None


class FakeTelegram:
    """Satisfies telegram_connector.TelegramTransport.

    Records what would have gone into the chat. That record is the end of the
    chain: if it is empty, the answer never reached the human, whatever the
    bus says.
    """

    def __init__(self, updates: Sequence[dict[str, Any]] | None = None) -> None:
        self.pending = list(updates or [])
        self.chat: list[tuple[int, str]] = []
        self.fail_send_times = 0

    def get_updates(self, offset: int, timeout_seconds: int) -> Sequence[dict[str, Any]]:
        ready = [u for u in self.pending if u.get("update_id", 0) >= offset]
        self.pending = [u for u in self.pending if u not in ready]
        return ready

    def send_message(self, chat_id: int, text: str) -> None:
        if self.fail_send_times > 0:
            self.fail_send_times -= 1
            raise telegram_connector.ConnectorError("TELEGRAM_API_UNAVAILABLE")
        self.chat.append((chat_id, text))


def telegram_update(update_id: int, text: str, *, chat_id: int, user_id: int) -> dict[str, Any]:
    return {
        "update_id": update_id,
        "message": {
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": user_id},
            "text": text,
        },
    }
