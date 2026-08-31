"""Local tests for the bus negative-test runner. No network, no tokens.

The important property under test is not that a correct bus passes, but that a
bus with a *weakened* control fails: a negative test suite that cannot detect a
missing control is worthless as evidence for activation-gate item 6.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bus_negtest_run

KARL_TOKEN = "karl-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
THORSTEN_TOKEN = "thorsten-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
IDENTITIES = {KARL_TOKEN: "SAO-001", THORSTEN_TOKEN: "RAS-001"}
KNOWN_RECIPIENTS = {"SAO-001", "RAS-001"}


class FakeResponse:
    def __init__(self, status: int, payload):
        self.status = status
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class FakeHTTPError(Exception):
    def __init__(self, code: int, detail: str):
        super().__init__(detail)
        self.code = code
        self._payload = json.dumps({"detail": detail}).encode("utf-8")

    def read(self):
        return self._payload


class FakeBus:
    """Minimal stand-in for the real bus, with individually disableable controls."""

    def __init__(self, weakened: str | None = None):
        self.weakened = weakened
        self.messages: dict[str, dict] = {}
        self.by_idempotency: dict[tuple[str, str], str] = {}
        self.counter = 0

    # -- helpers ------------------------------------------------------------
    def _enabled(self, control: str) -> bool:
        return self.weakened != control

    def _new_id(self) -> str:
        self.counter += 1
        return f"MSG-FAKE{self.counter:028d}"

    # -- request handling ---------------------------------------------------
    def handle(self, request):
        path = request.full_url.split("workforce.example", 1)[1]
        headers = {key.lower(): value for key, value in request.headers.items()}
        body = json.loads(request.data.decode("utf-8")) if request.data else None

        if path == "/bus/v1/status":
            return FakeResponse(200, {"channel_status": "TESTING"})

        actor = self._authenticate(headers)

        if path.startswith("/bus/v1/messages?scope="):
            return self._read(path, actor)
        if path == "/bus/v1/messages":
            return self._send(headers, body, actor)
        if path.endswith("/ack"):
            message_id = path.split("/bus/v1/messages/", 1)[1][: -len("/ack")]
            return self._acknowledge(headers, body, actor, message_id)

        raise AssertionError(f"unexpected call: {path}")

    def _authenticate(self, headers) -> str:
        authorization = headers.get("authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if separator != " " or scheme.lower() != "bearer" or not 32 <= len(token) <= 512:
            raise FakeHTTPError(401, "BUS_BEARER_TOKEN_REQUIRED")
        if token not in IDENTITIES:
            raise FakeHTTPError(401, "BUS_AUTH_FAILED")
        return IDENTITIES[token]

    def _read(self, path, actor):
        scope = path.split("scope=", 1)[1].split("&", 1)[0]
        if scope not in {"INBOX", "OUTBOX", "PROJECT"}:
            raise FakeHTTPError(400, "BUS_REQUEST_INVALID")
        if scope == "PROJECT" and actor != "SAO-001" and self._enabled("project_scope"):
            raise FakeHTTPError(403, "BUS_PROJECT_READ_DENIED")
        return FakeResponse(200, [])

    def _send(self, headers, body, actor):
        if "x-request-id" not in headers:
            raise FakeHTTPError(400, "BUS_REQUEST_ID_REQUIRED")
        if "idempotency-key" not in headers:
            raise FakeHTTPError(400, "BUS_IDEMPOTENCY_KEY_REQUIRED")
        allowed_fields = {
            "recipient_id", "subject", "body", "action_class",
            "confidentiality", "task_ref", "handoff_ref", "parent_message_id",
        }
        if set(body) - allowed_fields:
            raise FakeHTTPError(400, "BUS_REQUEST_INVALID")

        recipient = body["recipient_id"]
        if recipient == actor and self._enabled("self_route"):
            raise FakeHTTPError(403, "BUS_SELF_ROUTE_DENIED")
        if recipient not in KNOWN_RECIPIENTS and self._enabled("route_allowlist"):
            raise FakeHTTPError(403, "BUS_ROUTE_DENIED")
        if len(body["body"]) > bus_negtest_run.MAX_BODY_CHARS and self._enabled("body_size"):
            raise FakeHTTPError(413, "BUS_BODY_TOO_LARGE")

        hop = 0
        parent_id = body.get("parent_message_id")
        if parent_id is not None:
            parent = self.messages[parent_id]
            hop = parent["hop"] + 1
            if hop > bus_negtest_run.MAX_HOPS and self._enabled("loop_limit"):
                raise FakeHTTPError(422, "BUS_LOOP_LIMIT_EXCEEDED")

        key = (actor, headers["idempotency-key"])
        if key in self.by_idempotency:
            existing_id = self.by_idempotency[key]
            existing = self.messages[existing_id]
            if existing["body"] != body["body"] and self._enabled("idempotency"):
                raise FakeHTTPError(409, "BUS_IDEMPOTENCY_CONFLICT")
            return FakeResponse(
                201, {"message_id": existing_id, "delivery_status": "DELIVERED"}
            )

        message_id = self._new_id()
        self.messages[message_id] = {
            "sender": actor,
            "recipient": recipient,
            "body": body["body"],
            "hop": hop,
            "status": "DELIVERED",
        }
        self.by_idempotency[key] = message_id
        return FakeResponse(201, {"message_id": message_id, "delivery_status": "DELIVERED"})

    def _acknowledge(self, headers, body, actor, message_id):
        if "x-request-id" not in headers:
            raise FakeHTTPError(400, "BUS_REQUEST_ID_REQUIRED")
        message = self.messages.get(message_id)
        # Unknown id and wrong recipient deliberately share one answer so the
        # bus does not reveal whether a message id exists.
        if (message is None or message["recipient"] != actor) and self._enabled("ack_identity"):
            raise FakeHTTPError(403, "BUS_ACK_DENIED")
        if message is None:
            return FakeResponse(200, {"decision": body["decision"]})
        if message["status"] == body["decision"]:
            return FakeResponse(200, {"decision": body["decision"]})
        if message["status"] != "DELIVERED" and self._enabled("ack_final"):
            raise FakeHTTPError(409, "BUS_ACK_ALREADY_FINAL")
        message["status"] = body["decision"]
        return FakeResponse(200, {"decision": body["decision"]})


def _run(bus: FakeBus):
    import urllib.error

    def fake_urlopen(request, timeout=None, context=None):
        try:
            return bus.handle(request)
        except FakeHTTPError as error:
            http_error = urllib.error.HTTPError(
                "https://workforce.example", error.code, str(error), {}, None
            )
            http_error.read = error.read
            raise http_error from None

    with patch("urllib.request.urlopen", fake_urlopen):
        return bus_negtest_run.run(
            "https://workforce.example", KARL_TOKEN, THORSTEN_TOKEN, "TEST"
        )


class BusNegtestRunTest(unittest.TestCase):
    def test_correct_bus_passes_every_case(self):
        result = _run(FakeBus())
        failed = [case for case in result["cases"] if case["result"] == "FAIL"]
        self.assertEqual([], failed, f"unexpected failures: {failed}")
        self.assertEqual("PASS", result["result"])
        self.assertEqual(0, result["cases_failed"])
        self.assertGreaterEqual(result["cases_total"], 18)

    def test_weakened_control_is_detected(self):
        for control, expected_case in [
            ("self_route", "self_route_rejected"),
            ("route_allowlist", "unlisted_recipient_rejected"),
            ("project_scope", "project_scope_denied_for_specialist"),
            ("ack_identity", "ack_by_non_recipient_rejected"),
            ("ack_final", "conflicting_ack_decision_rejected"),
            ("idempotency", "idempotency_key_reuse_with_different_body_rejected"),
            ("body_size", "oversized_body_rejected"),
            ("loop_limit", "loop_limit_enforced"),
        ]:
            with self.subTest(control=control):
                result = _run(FakeBus(weakened=control))
                self.assertEqual("FAIL", result["result"])
                failed = {
                    case["case"] for case in result["cases"] if case["result"] == "FAIL"
                }
                self.assertIn(expected_case, failed)

    def test_channel_not_testing_blocks(self):
        def fake_urlopen(request, timeout=None, context=None):
            return FakeResponse(200, {"channel_status": "DISABLED"})

        with patch("urllib.request.urlopen", fake_urlopen):
            result = bus_negtest_run.run(
                "https://workforce.example", KARL_TOKEN, THORSTEN_TOKEN, "TEST"
            )

        self.assertEqual("BLOCKED", result["result"])
        self.assertEqual("BUS_NEGTEST_CHANNEL_NOT_TESTING", result["reason"])

    def test_rejects_non_https_base_url(self):
        with self.assertRaises(ValueError):
            bus_negtest_run.run(
                "http://workforce.example", KARL_TOKEN, THORSTEN_TOKEN, "TEST"
            )

    def test_read_token_rejects_short_file_content(self):
        with tempfile.TemporaryDirectory() as tempdir:
            token_file = Path(tempdir) / "token"
            token_file.write_text("too-short", encoding="utf-8")
            with self.assertRaises(ValueError):
                bus_negtest_run.read_token(str(token_file))


if __name__ == "__main__":
    unittest.main()
