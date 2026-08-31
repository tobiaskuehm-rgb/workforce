"""Read Telegram numeric IDs without printing token or message contents."""

from __future__ import annotations

import json
import os
import sys

from telegram_connector import ConfigurationError, ConnectorError, TelegramBotClient, _secret


def main() -> int:
    try:
        token = _secret(os.environ, "TELEGRAM_BOT_TOKEN")
        updates = TelegramBotClient(token).get_updates(offset=0, timeout_seconds=1)
    except (ConfigurationError, ConnectorError) as exc:
        code = exc.code if isinstance(exc, ConnectorError) else str(exc)
        print(json.dumps({"status": "blocked", "reason": code}))
        return 2

    identities = []
    seen = set()
    for update in updates:
        message = update.get("message")
        if not isinstance(message, dict):
            continue
        chat = message.get("chat")
        sender = message.get("from")
        if not isinstance(chat, dict) or not isinstance(sender, dict):
            continue
        chat_id = chat.get("id")
        user_id = sender.get("id")
        chat_type = chat.get("type")
        if not isinstance(chat_id, int) or not isinstance(user_id, int):
            continue
        key = (chat_id, user_id, str(chat_type))
        if key in seen:
            continue
        seen.add(key)
        identities.append(
            {"chat_id": chat_id, "user_id": user_id, "chat_type": str(chat_type)}
        )

    print(json.dumps({"status": "ok", "identities": identities}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
