"""One-shot bidirectional Karl (SAO-001) <-> Thorsten (RAS-001) bus realtest.

Reads two already-issued ACCEPTANCE bearer tokens from local files (created
by prepare_realtest_once.sh) and drives the real HTTPS API end to end:
Karl sends a message, Thorsten reads and acknowledges it and replies,
Karl reads and acknowledges the reply. Never logs a raw token or a full
message body; only stable identifiers and statuses.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

TIMEOUT_SECONDS = 8


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
        raise ValueError("BUS_REALTEST_BASE_URL_INVALID")
    return base_url


def read_token(token_file: str) -> str:
    with open(token_file, encoding="utf-8") as handle:
        token = handle.read().strip()
    if not 32 <= len(token) <= 512:
        raise ValueError(f"BUS_REALTEST_TOKEN_INVALID:{token_file}")
    return token


def call(
    base_url: str,
    method: str,
    path: str,
    token: str,
    *,
    body: dict[str, Any] | None = None,
    request_id: str | None = None,
    idempotency_key: str | None = None,
    context: ssl.SSLContext,
) -> tuple[int, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if request_id:
        headers["X-Request-ID"] = request_id
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    request = urllib.request.Request(
        f"{base_url}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(
            request, timeout=TIMEOUT_SECONDS, context=context
        ) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {"detail": f"HTTP_{exc.code}"}
        return exc.code, payload


def _failure(step: str, detail: Any) -> dict[str, Any]:
    return {"result": "FAIL", "step": step, "detail": detail}


def run(base_url: str, karl_token: str, thorsten_token: str) -> dict[str, Any]:
    base_url = validate_base_url(base_url)
    context = ssl.create_default_context()
    transcript: list[dict[str, Any]] = []

    status, status_payload = call(
        base_url, "GET", "/bus/v1/status", karl_token, context=context
    )
    if status != 200 or status_payload.get("channel_status") != "TESTING":
        return _failure("status_check", status_payload)
    transcript.append({"step": "status_check", "channel_status": status_payload.get("channel_status")})

    status, sent = call(
        base_url,
        "POST",
        "/bus/v1/messages",
        karl_token,
        body={
            "recipient_id": "RAS-001",
            "subject": "Bus-Realtest Karl -> Thorsten",
            "body": "Kurzer bidirektionaler Realtest ueber den Message Bus.",
            "action_class": "INTERNAL_COMMUNICATION",
            "confidentiality": "NEED_TO_KNOW",
        },
        request_id="BUS-REALTEST-KARL-TO-THORSTEN",
        idempotency_key="IDEM-BUS-REALTEST-K2T-001",
        context=context,
    )
    if status != 201 or sent.get("delivery_status") != "DELIVERED":
        return _failure("karl_sends_message", sent)
    outbound_message_id = sent["message_id"]
    transcript.append({"step": "karl_sends_message", "message_id": outbound_message_id})

    status, inbox = call(
        base_url,
        "GET",
        "/bus/v1/messages?scope=INBOX&limit=50",
        thorsten_token,
        context=context,
    )
    if status != 200 or not any(m.get("message_id") == outbound_message_id for m in inbox):
        return _failure("thorsten_reads_inbox", inbox)
    transcript.append({"step": "thorsten_reads_inbox", "found": outbound_message_id})

    status, ack = call(
        base_url,
        "POST",
        f"/bus/v1/messages/{outbound_message_id}/ack",
        thorsten_token,
        body={"decision": "ACCEPTED", "note": "Realtest erhalten."},
        request_id="BUS-REALTEST-THORSTEN-ACK-1",
        context=context,
    )
    if status != 200:
        return _failure("thorsten_acknowledges", ack)
    transcript.append({"step": "thorsten_acknowledges", "message_id": outbound_message_id})

    status, reply = call(
        base_url,
        "POST",
        "/bus/v1/messages",
        thorsten_token,
        body={
            "recipient_id": "SAO-001",
            "subject": "Re: Bus-Realtest Karl -> Thorsten",
            "body": "Antwort im bidirektionalen Realtest.",
            "action_class": "INTERNAL_COMMUNICATION",
            "confidentiality": "NEED_TO_KNOW",
            "parent_message_id": outbound_message_id,
        },
        request_id="BUS-REALTEST-THORSTEN-TO-KARL",
        idempotency_key="IDEM-BUS-REALTEST-T2K-001",
        context=context,
    )
    if status != 201 or reply.get("delivery_status") != "DELIVERED":
        return _failure("thorsten_sends_reply", reply)
    reply_message_id = reply["message_id"]
    transcript.append({"step": "thorsten_sends_reply", "message_id": reply_message_id})

    status, karl_inbox = call(
        base_url,
        "GET",
        "/bus/v1/messages?scope=INBOX&limit=50",
        karl_token,
        context=context,
    )
    if status != 200 or not any(m.get("message_id") == reply_message_id for m in karl_inbox):
        return _failure("karl_reads_inbox", karl_inbox)
    transcript.append({"step": "karl_reads_inbox", "found": reply_message_id})

    status, karl_ack = call(
        base_url,
        "POST",
        f"/bus/v1/messages/{reply_message_id}/ack",
        karl_token,
        body={"decision": "ACCEPTED", "note": "Antwort erhalten."},
        request_id="BUS-REALTEST-KARL-ACK-1",
        context=context,
    )
    if status != 200:
        return _failure("karl_acknowledges", karl_ack)
    transcript.append({"step": "karl_acknowledges", "message_id": reply_message_id})

    return {
        "result": "PASS",
        "outbound_message_id": outbound_message_id,
        "reply_message_id": reply_message_id,
        "transcript": transcript,
    }


def main() -> int:
    try:
        base_url = validate_base_url(os.environ.get("BUS_REALTEST_BASE_URL", ""))
        karl_token = read_token(os.environ["KARL_BUS_TOKEN_FILE"])
        thorsten_token = read_token(os.environ["THORSTEN_BUS_TOKEN_FILE"])
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}))
        return 2

    result = run(base_url, karl_token, thorsten_token)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
