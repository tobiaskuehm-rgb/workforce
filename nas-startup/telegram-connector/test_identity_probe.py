import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import identity_probe


class FakeTelegramClient:
    seen_token = None

    def __init__(self, token):
        type(self).seen_token = token

    def get_updates(self, offset, timeout_seconds):
        return [
            {
                "update_id": 1,
                "message": {
                    "chat": {"id": 111, "type": "private"},
                    "from": {"id": 222},
                    "text": "secret message content",
                },
            },
            {
                "update_id": 2,
                "message": {
                    "chat": {"id": 111, "type": "private"},
                    "from": {"id": 222},
                    "text": "second message",
                },
            },
        ]


class IdentityProbeTest(unittest.TestCase):
    def test_probe_outputs_only_deduplicated_ids(self):
        with tempfile.TemporaryDirectory() as tempdir:
            token_file = Path(tempdir) / "bot_token"
            token_file.write_text("probe-token-never-real", encoding="utf-8")
            output = io.StringIO()
            with (
                patch.dict(
                    os.environ,
                    {"TELEGRAM_BOT_TOKEN_FILE": str(token_file)},
                    clear=True,
                ),
                patch.object(identity_probe, "TelegramBotClient", FakeTelegramClient),
                redirect_stdout(output),
            ):
                result = identity_probe.main()

        self.assertEqual(0, result)
        payload = json.loads(output.getvalue())
        self.assertEqual(
            [{"chat_id": 111, "chat_type": "private", "user_id": 222}],
            payload["identities"],
        )
        rendered = output.getvalue()
        self.assertNotIn("probe-token-never-real", rendered)
        self.assertNotIn("secret message content", rendered)
        self.assertNotIn("second message", rendered)

    def test_probe_fails_closed_without_token(self):
        output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), redirect_stdout(output):
            result = identity_probe.main()
        self.assertEqual(2, result)
        self.assertEqual("TELEGRAM_BOT_TOKEN_REQUIRED", json.loads(output.getvalue())["reason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
