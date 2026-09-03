"""Telegram Bot API, the thin adapter. Long polling: no inbound port on the NAS."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List

MAX_TEXT = 4096  # Telegram's limit per sendMessage


class TelegramError(RuntimeError):
    pass


class TelegramClient:
    def __init__(self, token: str, *, base_url: str = "https://api.telegram.org", timeout: int = 40) -> None:
        if not base_url.startswith("https://"):
            raise TelegramError("TELEGRAM_NOT_HTTPS")
        self._base = f"{base_url.rstrip('/')}/bot{token}/"
        self._timeout = timeout

    def _call(self, method: str, payload: Dict[str, Any]) -> Any:
        body = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(self._base + method, data=body, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise TelegramError(f"TELEGRAM_HTTP_{exc.code}") from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError, json.JSONDecodeError) as exc:
            raise TelegramError("TELEGRAM_UNREACHABLE") from exc
        if not parsed.get("ok"):
            raise TelegramError("TELEGRAM_NOT_OK")
        return parsed.get("result")

    def get_updates(self, offset: int, timeout_seconds: int) -> List[Dict[str, Any]]:
        result = self._call("getUpdates", {"offset": offset, "timeout": timeout_seconds,
                                           "allowed_updates": json.dumps(["message"])})
        return list(result or [])

    def send_message(self, chat_id: int, text: str) -> str:
        """Returns the external message id(s) - the anchor for delivery reconciliation."""
        ids = []
        for start in range(0, max(len(text), 1), MAX_TEXT):
            result = self._call("sendMessage", {"chat_id": chat_id, "text": text[start:start + MAX_TEXT]})
            ids.append(str((result or {}).get("message_id", "")))
        return ",".join(ids)
