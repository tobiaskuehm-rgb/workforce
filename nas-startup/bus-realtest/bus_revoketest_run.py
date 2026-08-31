"""Proves that a revoked credential is refused while the channel stays TESTING.

Closes the last gap in activation-gate item 6 (security review 2026-08-31, F7).
Run directly after bus_revoketest.sql has revoked Thorsten's credential and
before the regular cleanup.

Three assertions, and all three matter:

1. Thorsten's revoked token is refused with 401 BUS_AUTH_FAILED.
2. Karl's untouched token still works. Without this the first result would be
   worthless -- a channel-wide outage would also produce a refusal.
3. The channel still reports TESTING, so the refusal really came from the
   credential check and not from the kill switch.

Never logs a raw token or a full message body.
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
        raise ValueError("BUS_REVOKETEST_BASE_URL_INVALID")
    return base_url


def read_token(token_file: str) -> str:
    with open(token_file, encoding="utf-8") as handle:
        token = handle.read().strip()
    if not 32 <= len(token) <= 512:
        raise ValueError(f"BUS_REVOKETEST_TOKEN_INVALID:{token_file}")
    return token


def call(base_url: str, path: str, token: str | None, context: ssl.SSLContext) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{base_url}{path}", headers=headers, method="GET")
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


def run(base_url: str, karl_token: str, thorsten_token: str) -> dict[str, Any]:
    base_url = validate_base_url(base_url)
    context = ssl.create_default_context()
    cases: list[dict[str, Any]] = []

    status, payload = call(base_url, "/bus/v1/status", None, context)
    channel_status = payload.get("channel_status") if isinstance(payload, dict) else None
    if status != 200 or channel_status != "TESTING":
        return {
            "result": "BLOCKED",
            "reason": "BUS_REVOKETEST_CHANNEL_NOT_TESTING",
            "channel_status": channel_status,
        }
    cases.append(
        {
            "case": "channel_still_testing",
            "result": "PASS",
            "channel_status": channel_status,
        }
    )

    status, payload = call(base_url, "/bus/v1/messages?scope=INBOX&limit=1", thorsten_token, context)
    detail = payload.get("detail") if isinstance(payload, dict) else None
    cases.append(
        {
            "case": "revoked_credential_refused",
            "result": "PASS" if status == 401 and detail == "BUS_AUTH_FAILED" else "FAIL",
            "expected_status": 401,
            "expected_detail": "BUS_AUTH_FAILED",
            "actual_status": status,
            "actual_detail": detail,
        }
    )

    status, payload = call(base_url, "/bus/v1/messages?scope=INBOX&limit=1", karl_token, context)
    cases.append(
        {
            # Without this the refusal above would prove nothing: a channel-wide
            # outage would refuse both tokens just the same.
            "case": "untouched_credential_still_works",
            "result": "PASS" if status == 200 else "FAIL",
            "expected_status": 200,
            "actual_status": status,
        }
    )

    failed = [case for case in cases if case["result"] == "FAIL"]
    return {
        "result": "PASS" if not failed else "FAIL",
        "cases_total": len(cases),
        "cases_failed": len(failed),
        "cases": cases,
    }


def main() -> int:
    try:
        base_url = validate_base_url(os.environ.get("BUS_REVOKETEST_BASE_URL", ""))
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
