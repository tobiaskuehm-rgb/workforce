"""Deterministic, network-free demonstration of the Telegram connector."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from telegram_connector import AuditStore, Settings, TelegramConnector


class DemoTelegram:
    def __init__(self):
        self.replies: list[dict[str, object]] = []

    def get_updates(self, offset: int, timeout_seconds: int):
        return []

    def send_message(self, chat_id: int, text: str) -> None:
        self.replies.append({"chat_id": chat_id, "text": text})


class DemoWorkforce:
    def __init__(self):
        self.tasks: list[dict[str, object]] = []
        self.inbox = [
            {
                "message_id": "MSG-DEMO12345678",
                "sender_id": "AI-ENG-001",
                "task_ref": "ENG-007",
                "delivery_status": "CREATED",
                "subject": "Lokaler Connector-Bericht",
                "body": "Dieser simulierte Volltext darf nicht an Telegram gehen.",
            }
        ]

    def get_status(self):
        return {
            "project_id": "START-UP",
            "api_version": "v7",
            "channel_status": "SIMULATED",
        }

    def get_inbox(self, limit=20):
        return self.inbox[:limit]

    def propose_task(self, **payload):
        self.tasks.append(payload)
        return {"task_status": "PENDING"}


def telegram_update(
    update_id: int,
    text: str,
    *,
    chat_id: int = 111,
    user_id: int = 222,
):
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id + 1000,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": user_id},
            "text": text,
        },
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        state_path = Path(tempdir) / "state.sqlite3"
        settings = Settings(
            enabled=True,
            kill_switch=False,
            telegram_bot_token="demo-token-never-real",
            allowed_chat_id=111,
            allowed_user_id=222,
            allowed_recipient_ids=frozenset({"RAS-001", "AI-ENG-001"}),
            allowed_task_ids=frozenset({"CEO-TG-DEMO-001"}),
            workforce_base_url="https://nas.invalid:8443",
            workforce_bus_token="demo-bus-token-never-real",
            state_path=state_path,
            poll_timeout_seconds=1,
        )
        store = AuditStore(state_path)
        telegram = DemoTelegram()
        workforce = DemoWorkforce()
        connector = TelegramConnector(settings, store, telegram, workforce)

        task_update = telegram_update(
            100,
            "/task RAS-001 CEO-TG-DEMO-001 | Opportunity prüfen | Drei Quellen und Gegenhypothese",
        )
        results = {
            "authorized_task": connector.process_update(task_update),
            "duplicate_task": connector.process_update(task_update),
            "unauthorized_status": connector.process_update(
                telegram_update(101, "/status", chat_id=999, user_id=888)
            ),
            "authorized_status": connector.process_update(
                telegram_update(102, "/status")
            ),
        }
        notifications_first = connector.publish_inbox_notifications()
        notifications_second = connector.publish_inbox_notifications()
        audit = store.list_audit()
        serialized_audit = json.dumps(audit, sort_keys=True)
        output = {
            "result": "PASS"
            if results
            == {
                "authorized_task": "PROCESSED",
                "duplicate_task": "DUPLICATE",
                "unauthorized_status": "DENIED",
                "authorized_status": "PROCESSED",
            }
            and len(workforce.tasks) == 1
            and "Drei Quellen und Gegenhypothese" not in serialized_audit
            and "Dieser simulierte Volltext" not in json.dumps(telegram.replies)
            and notifications_first == 1
            and notifications_second == 0
            else "FAIL",
            "network_calls": 0,
            "task_status": "PENDING",
            "workforce_task_count": len(workforce.tasks),
            "outbound_notification_count": notifications_first,
            "outbound_duplicate_count": notifications_second,
            "checks": results,
            "audit_event_types": [event["event_type"] for event in audit],
            "full_task_content_in_audit": "Drei Quellen und Gegenhypothese"
            in serialized_audit,
            "full_message_body_in_telegram": "Dieser simulierte Volltext"
            in json.dumps(telegram.replies),
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        store.close()


if __name__ == "__main__":
    main()
