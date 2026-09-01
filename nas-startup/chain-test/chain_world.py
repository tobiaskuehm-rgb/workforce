"""One shared bus world with two faces, for the local chain test.

The chain has two components that talk to the bus through *different*
interfaces: the connector through its `WorkforceGateway` protocol, the agent
through `bus_client.BusClient`. A single fake that satisfied only one of them
would leave exactly the seam the chain test exists to check.

So: one world, two adapters. The world behaves like the real bus where it
matters for this test:

  * `send_message` is idempotent on (sender, idempotency key), as the real bus
    is - it derives the message id from them
  * acknowledging moves a message from DELIVERED to ACCEPTED, so the agent
    stops seeing it
  * the route allowlist is enforced in both directions, because the return leg
    being structurally impossible is the defect this whole package was written
    after
  * `task_ref` is stored and returned, because the connector withholds a body
    whose task is not allowlisted (finding G-003)

Only Telegram and the bus are faked. The connector and the worker are real.
"""

from __future__ import annotations

import hashlib
from typing import Any


class BusRefusal(RuntimeError):
    """What the fake bus raises. Adapters translate it into their own error."""

    def __init__(self, detail: str, status: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status = status


class ChainWorld:
    def __init__(self, *, connector_id: str, agent_id: str,
                 channel_status: str = "TESTING") -> None:
        self.connector_id = connector_id
        self.agent_id = agent_id
        self.channel_status = channel_status
        self.tasks: dict[str, dict[str, Any]] = {}
        self.messages: dict[str, dict[str, Any]] = {}
        self.by_idempotency: dict[tuple[str, str], str] = {}
        # Exactly what chain_prepare.sql creates: out and back.
        self.routes: set[tuple[str, str, str]] = {
            (connector_id, agent_id, "TASK"),
            (connector_id, agent_id, "MESSAGE"),
            (agent_id, connector_id, "MESSAGE"),
        }

    # -- writes ------------------------------------------------------------
    def create_task(self, *, sender: str, task_id: str, owner_id: str,
                    title: str, expected_output: str, source_ref: str) -> dict[str, Any]:
        if (sender, owner_id, "TASK") not in self.routes:
            raise BusRefusal("BUS_TASK_ROUTE_DENIED", 403)
        existing = self.tasks.get(task_id)
        if existing is not None:
            return dict(existing)
        task = {
            "task_id": task_id, "creator_id": sender, "owner_id": owner_id,
            "task_status": "PENDING", "title": title,
            "expected_output": expected_output, "source_ref": source_ref,
        }
        self.tasks[task_id] = task
        return dict(task)

    def send_message(self, *, sender: str, recipient_id: str, subject: str,
                     body: str, idempotency_key: str,
                     parent_message_id: str | None = None,
                     task_ref: str | None = None,
                     action_class: str = "INTERNAL_COMMUNICATION") -> dict[str, Any]:
        if sender == recipient_id:
            raise BusRefusal("BUS_SELF_ROUTE_DENIED", 403)
        if (sender, recipient_id, "MESSAGE") not in self.routes:
            raise BusRefusal("BUS_ROUTE_DENIED", 403)
        key = (sender, idempotency_key)
        if key in self.by_idempotency:
            return dict(self.messages[self.by_idempotency[key]])
        message_id = "MSG-" + hashlib.sha256(
            f"{sender}:{idempotency_key}".encode("utf-8")
        ).hexdigest().upper()[:32]
        self.by_idempotency[key] = message_id
        self.messages[message_id] = {
            "message_id": message_id, "sender_id": sender,
            "recipient_id": recipient_id, "subject": subject, "body": body,
            "parent_message_id": parent_message_id, "task_ref": task_ref,
            "action_class": action_class, "delivery_status": "DELIVERED",
        }
        return dict(self.messages[message_id])

    def acknowledge(self, *, actor: str, message_id: str,
                    decision: str) -> dict[str, Any]:
        message = self.messages.get(message_id)
        if message is None:
            raise BusRefusal("BUS_RECORD_NOT_FOUND", 404)
        if message["recipient_id"] != actor:
            raise BusRefusal("BUS_ACK_DENIED", 403)
        if message["delivery_status"] != "DELIVERED":
            raise BusRefusal("BUS_ACK_ALREADY_FINAL", 409)
        message["delivery_status"] = "ACCEPTED"
        return dict(message)

    # -- reads -------------------------------------------------------------
    def inbox(self, actor: str, limit: int = 20) -> list[dict[str, Any]]:
        return [dict(m) for m in self.messages.values()
                if m["recipient_id"] == actor][:limit]

    def status(self) -> dict[str, Any]:
        return {"api_version": "v8", "project_id": "START-UP",
                "channel_status": self.channel_status,
                "migration": "002_workforce_bus"}
