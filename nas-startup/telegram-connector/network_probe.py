"""Secret-free HTTPS preflight for the START-UP Workforce API."""

from __future__ import annotations

import json
import os
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

from telegram_connector import _workforce_transport_error


OpenUrl = Callable[..., Any]


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
        raise ValueError("WORKFORCE_HTTPS_URL_INVALID")
    return base_url


def _failure(reason: str, endpoint: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"result": "FAIL", "reason": reason}
    if endpoint:
        result["endpoint"] = endpoint
    return result


def run_probe(
    base_url: str,
    *,
    expected_channel: str = "DISABLED",
    urlopen: OpenUrl = urllib.request.urlopen,
    timeout_seconds: int = 8,
) -> dict[str, Any]:
    base_url = validate_base_url(base_url)
    context = ssl.create_default_context()
    payloads: dict[str, Mapping[str, Any]] = {}

    for endpoint in ("/health", "/db-check", "/bus/v1/status"):
        request = urllib.request.Request(
            f"{base_url}{endpoint}",
            headers={"Accept": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=timeout_seconds, context=context) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return _failure(f"WORKFORCE_HTTP_{exc.code}", endpoint)
        except urllib.error.URLError as exc:
            return _failure(_workforce_transport_error(exc), endpoint)
        except (TimeoutError, socket.timeout) as exc:
            return _failure(_workforce_transport_error(exc), endpoint)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _failure("WORKFORCE_RESPONSE_INVALID", endpoint)
        if not isinstance(payload, dict):
            return _failure("WORKFORCE_RESPONSE_INVALID", endpoint)
        payloads[endpoint] = payload

    if payloads["/health"].get("status") != "ok":
        return _failure("WORKFORCE_HEALTH_NOT_OK", "/health")
    if payloads["/db-check"].get("database") != "ok":
        return _failure("WORKFORCE_DATABASE_NOT_OK", "/db-check")
    status = payloads["/bus/v1/status"]
    if status.get("project_id") != "START-UP":
        return _failure("WORKFORCE_PROJECT_MISMATCH", "/bus/v1/status")
    if status.get("channel_status") != expected_channel:
        return _failure("WORKFORCE_CHANNEL_STATE_UNEXPECTED", "/bus/v1/status")

    return {
        "result": "PASS",
        "transport": "HTTPS_VERIFIED",
        "project_id": "START-UP",
        "api_version": status.get("api_version", "UNKNOWN"),
        "channel_status": expected_channel,
        "checked_endpoints": 3,
        "credential_used": False,
    }


def main() -> int:
    try:
        base_url = validate_base_url(os.environ.get("WORKFORCE_API_BASE_URL", ""))
        expected_channel = os.environ.get(
            "WORKFORCE_EXPECTED_CHANNEL_STATUS", "DISABLED"
        ).strip()
        if expected_channel not in {"DISABLED", "TESTING"}:
            raise ValueError("WORKFORCE_EXPECTED_CHANNEL_INVALID")
    except ValueError as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}))
        return 2

    result = run_probe(base_url, expected_channel=expected_channel)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
