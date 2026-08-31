import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bus_realtest_run


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


def _script(messages_by_id):
    """Build a fake urlopen that answers the fixed realtest call sequence."""

    calls = []

    def fake_urlopen(request, timeout=None, context=None):
        calls.append(request.full_url)
        path = request.full_url.split("workforce.example", 1)[1]

        if path == "/bus/v1/status":
            return FakeResponse(200, {"channel_status": "TESTING"})

        if path == "/bus/v1/messages" and request.data:
            body = json.loads(request.data.decode("utf-8"))
            message_id = f"MSG-{body['recipient_id']}-{len(calls)}"
            messages_by_id[body["recipient_id"]] = message_id
            return FakeResponse(
                201,
                {
                    "message_id": message_id,
                    "recipient_id": body["recipient_id"],
                    "delivery_status": "DELIVERED",
                },
            )

        if path.startswith("/bus/v1/messages?scope=INBOX"):
            return FakeResponse(200, [{"message_id": m} for m in messages_by_id.values()])

        if path.endswith("/ack"):
            return FakeResponse(200, {"decision": "ACCEPTED"})

        raise AssertionError(f"unexpected call: {path}")

    return fake_urlopen, calls


class BusRealtestRunTest(unittest.TestCase):
    def test_full_bidirectional_exchange_passes(self):
        fake_urlopen, calls = _script({})
        with patch("urllib.request.urlopen", fake_urlopen):
            result = bus_realtest_run.run(
                "https://workforce.example", "karl-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "thorsten-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            )

        self.assertEqual("PASS", result["result"])
        self.assertIn("outbound_message_id", result)
        self.assertIn("reply_message_id", result)
        self.assertEqual(7, len(result["transcript"]))
        self.assertTrue(calls)

    def test_channel_not_testing_fails_closed(self):
        def fake_urlopen(request, timeout=None, context=None):
            return FakeResponse(200, {"channel_status": "DISABLED"})

        with patch("urllib.request.urlopen", fake_urlopen):
            result = bus_realtest_run.run(
                "https://workforce.example", "karl-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "thorsten-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            )

        self.assertEqual("FAIL", result["result"])
        self.assertEqual("status_check", result["step"])

    def test_rejects_non_https_base_url(self):
        with self.assertRaises(ValueError):
            bus_realtest_run.run(
                "http://workforce.example", "karl-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "thorsten-token-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            )

    def test_read_token_rejects_short_file_content(self):
        with tempfile.TemporaryDirectory() as tempdir:
            token_file = Path(tempdir) / "token"
            token_file.write_text("too-short", encoding="utf-8")
            with self.assertRaises(ValueError):
                bus_realtest_run.read_token(str(token_file))


if __name__ == "__main__":
    unittest.main()
