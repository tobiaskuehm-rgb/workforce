"""Local tests for the revocation probe. No network, no tokens.

The property that matters: the probe must not report PASS when the refusal came
from something other than the revocation. A channel-wide outage refuses both
tokens and would otherwise look identical to a targeted revocation.
"""

from __future__ import annotations

import json
import unittest
import urllib.error
from unittest.mock import patch

import bus_revoketest_run

KARL_TOKEN = "karl-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
THORSTEN_TOKEN = "thorsten-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def _urlopen(channel_status="TESTING", thorsten=(401, "BUS_AUTH_FAILED"), karl_status=200):
    def fake_urlopen(request, timeout=None, context=None):
        path = request.full_url.split("workforce.example", 1)[1]
        if path == "/bus/v1/status":
            return FakeResponse(200, {"channel_status": channel_status})

        authorization = {k.lower(): v for k, v in request.headers.items()}["authorization"]
        if THORSTEN_TOKEN in authorization:
            status, detail = thorsten
            if status == 200:
                return FakeResponse(200, [])
            error = urllib.error.HTTPError(
                "https://workforce.example", status, detail, {}, None
            )
            error.read = lambda: json.dumps({"detail": detail}).encode("utf-8")
            raise error

        if karl_status == 200:
            return FakeResponse(200, [])
        error = urllib.error.HTTPError(
            "https://workforce.example", karl_status, "denied", {}, None
        )
        error.read = lambda: json.dumps({"detail": "BUS_AUTH_FAILED"}).encode("utf-8")
        raise error

    return fake_urlopen


def _run(**kwargs):
    with patch("urllib.request.urlopen", _urlopen(**kwargs)):
        return bus_revoketest_run.run(
            "https://workforce.example", KARL_TOKEN, THORSTEN_TOKEN
        )


class BusRevoketestRunTest(unittest.TestCase):
    def test_targeted_revocation_passes(self):
        result = _run()
        self.assertEqual("PASS", result["result"])
        self.assertEqual(0, result["cases_failed"])
        self.assertEqual(3, result["cases_total"])

    def test_channel_wide_outage_is_not_mistaken_for_revocation(self):
        # Both tokens refused: the revoked one looks correct in isolation, but
        # Karl's failure exposes that this was not a targeted revocation.
        result = _run(karl_status=401)
        self.assertEqual("FAIL", result["result"])
        failed = {case["case"] for case in result["cases"] if case["result"] == "FAIL"}
        self.assertIn("untouched_credential_still_works", failed)

    def test_revoked_token_that_still_works_fails(self):
        result = _run(thorsten=(200, None))
        self.assertEqual("FAIL", result["result"])
        failed = {case["case"] for case in result["cases"] if case["result"] == "FAIL"}
        self.assertIn("revoked_credential_refused", failed)

    def test_refusal_for_the_wrong_reason_fails(self):
        result = _run(thorsten=(503, "BUS_CHANNEL_NOT_ACTIVE"))
        self.assertEqual("FAIL", result["result"])
        failed = {case["case"] for case in result["cases"] if case["result"] == "FAIL"}
        self.assertIn("revoked_credential_refused", failed)

    def test_disabled_channel_blocks_instead_of_passing(self):
        result = _run(channel_status="DISABLED")
        self.assertEqual("BLOCKED", result["result"])
        self.assertEqual("BUS_REVOKETEST_CHANNEL_NOT_TESTING", result["reason"])

    def test_rejects_non_https_base_url(self):
        with self.assertRaises(ValueError):
            bus_revoketest_run.run(
                "http://workforce.example", KARL_TOKEN, THORSTEN_TOKEN
            )


if __name__ == "__main__":
    unittest.main()
