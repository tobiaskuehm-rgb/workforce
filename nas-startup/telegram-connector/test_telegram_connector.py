import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from telegram_connector import (
    MAX_OUTBOUND_BODY_CHARS,
    AuditStore,
    ConfigurationError,
    ConnectorError,
    Settings,
    TelegramConnector,
    parse_task_command,
)


BOT_TOKEN = "test-bot-token-never-real"
BUS_TOKEN = "test-bus-token-never-real-000000000000"


class FakeTelegram:
    def __init__(self, updates=None):
        self.updates = list(updates or [])
        self.sent = []
        self.last_offset = None

    def get_updates(self, offset, timeout_seconds):
        self.last_offset = offset
        return [item for item in self.updates if item["update_id"] >= offset]

    def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


class FakeWorkforce:
    def __init__(self):
        self.tasks = []
        self.inbox = []
        self.status = {
            "project_id": "START-UP",
            "api_version": "v8",
            "channel_status": "TESTING",
            "secret_field": "must-not-be-returned",
        }

    def get_status(self):
        return self.status

    def get_inbox(self, limit=20):
        return self.inbox[:limit]

    def propose_task(self, **kwargs):
        self.tasks.append(kwargs)
        return {"task_status": "PENDING"}


def update(update_id, text, *, chat_id=111, user_id=222, chat_type="private"):
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id + 1000,
            "chat": {"id": chat_id, "type": chat_type},
            "from": {"id": user_id},
            "text": text,
        },
    }


class TelegramConnectorTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tempdir.name) / "state.sqlite3"
        self.settings = Settings(
            enabled=True,
            kill_switch=False,
            telegram_bot_token=BOT_TOKEN,
            allowed_chat_id=111,
            allowed_user_id=222,
            allowed_recipient_ids=frozenset({"RAS-001", "AI-ENG-001"}),
            allowed_task_ids=frozenset(
                {"CEO-TG-TEST-001", "CEO-TG-TEST-002", "CEO-TG-TEST-003"}
            ),
            workforce_base_url="https://nas.example.test:8443",
            workforce_bus_token=BUS_TOKEN,
            state_path=self.state_path,
            poll_timeout_seconds=1,
        )
        self.store = AuditStore(self.state_path)
        self.telegram = FakeTelegram()
        self.workforce = FakeWorkforce()
        self.connector = TelegramConnector(
            self.settings,
            self.store,
            self.telegram,
            self.workforce,
        )

    def tearDown(self):
        self.store.close()
        self.tempdir.cleanup()

    def test_authorized_task_is_pending_and_audited(self):
        raw_text = "/task RAS-001 CEO-TG-TEST-001 | Marktcheck | Drei Quellen und Gegenhypothese"
        result = self.connector.process_update(update(10, raw_text))

        self.assertEqual("PROCESSED", result)
        self.assertEqual(1, len(self.workforce.tasks))
        self.assertEqual("CEO-TG-TEST-001", self.workforce.tasks[0]["task_id"])
        self.assertEqual("RAS-001", self.workforce.tasks[0]["recipient_id"])
        self.assertIn("PENDING", self.telegram.sent[0][1])
        events = self.store.list_audit()
        self.assertTrue(any(event["event_type"] == "TASK_PROPOSED" for event in events))
        serialized = json.dumps(events)
        self.assertNotIn("Drei Quellen und Gegenhypothese", serialized)
        self.assertNotIn(BOT_TOKEN, serialized)
        self.assertNotIn(BUS_TOKEN, serialized)

    def test_unknown_chat_is_denied_and_never_reaches_bus(self):
        result = self.connector.process_update(
            update(11, "/status", chat_id=999, user_id=888)
        )

        self.assertEqual("DENIED", result)
        self.assertEqual([], self.workforce.tasks)
        self.assertEqual([], self.telegram.sent)
        self.assertTrue(
            any(event["event_type"] == "ACCESS_DENIED" for event in self.store.list_audit())
        )

    def test_group_chat_is_denied_even_with_allowed_ids(self):
        result = self.connector.process_update(update(12, "/status", chat_type="group"))
        self.assertEqual("DENIED", result)
        self.assertEqual([], self.telegram.sent)

    def test_duplicate_update_is_not_processed_twice(self):
        item = update(
            13,
            "/task AI-ENG-001 CEO-TG-TEST-002 | Technikcheck | Kurzer Bericht",
        )
        first = self.connector.process_update(item)
        second = self.connector.process_update(item)

        self.assertEqual("PROCESSED", first)
        self.assertEqual("DUPLICATE", second)
        self.assertEqual(1, len(self.workforce.tasks))
        self.assertTrue(
            any(
                event["event_type"] == "DUPLICATE_IGNORED"
                for event in self.store.list_audit()
            )
        )

    def test_same_update_id_with_changed_payload_is_conflict(self):
        self.connector.process_update(update(14, "/status"))
        result = self.connector.process_update(update(14, "/help"))
        self.assertEqual("CONFLICT", result)
        self.assertTrue(
            any(
                event["event_type"] == "IDEMPOTENCY_CONFLICT"
                for event in self.store.list_audit()
            )
        )

    def test_kill_switch_blocks_all_commands(self):
        blocked = Settings(
            **{**self.settings.__dict__, "kill_switch": True},
        )
        connector = TelegramConnector(
            blocked,
            self.store,
            self.telegram,
            self.workforce,
        )
        result = connector.process_update(update(15, "/status"))
        self.assertEqual("BLOCKED", result)
        self.assertEqual([], self.telegram.sent)

    def test_status_reply_exposes_only_safe_fields(self):
        result = self.connector.process_update(update(16, "/status"))
        self.assertEqual("PROCESSED", result)
        reply = self.telegram.sent[0][1]
        self.assertIn("Kanal=TESTING", reply)
        self.assertNotIn("secret_field", reply)
        self.assertNotIn("must-not-be-returned", reply)

    def test_settings_repr_redacts_both_tokens(self):
        rendered = repr(self.settings)
        self.assertNotIn(BOT_TOKEN, rendered)
        self.assertNotIn(BUS_TOKEN, rendered)

    def test_recipient_allowlist_is_fail_closed(self):
        result = self.connector.process_update(
            update(17, "/task EAC-001 CEO-TG-TEST-003 | Test | Ergebnis")
        )
        self.assertEqual("FAILED", result)
        self.assertEqual([], self.workforce.tasks)
        self.assertIn("RECIPIENT_NOT_ALLOWED", self.telegram.sent[0][1])

    def test_task_allowlist_is_fail_closed(self):
        restricted = Settings(
            **{
                **self.settings.__dict__,
                "allowed_task_ids": frozenset({"ENG-TG-REALTEST-001"}),
            }
        )
        connector = TelegramConnector(
            restricted,
            self.store,
            self.telegram,
            self.workforce,
        )
        result = connector.process_update(
            update(18, "/task AI-ENG-001 ENG-TG-OTHER-001 | Test | Ergebnis")
        )
        self.assertEqual("FAILED", result)
        self.assertEqual([], self.workforce.tasks)
        self.assertIn("TASK_ID_NOT_ALLOWED", self.telegram.sent[0][1])

    def test_poll_offset_advances_after_denied_and_processed_updates(self):
        self.telegram.updates = [
            update(20, "/status", chat_id=999, user_id=888),
            update(21, "/help"),
        ]
        handled = self.connector.poll_once()
        self.assertEqual(2, handled)
        self.assertEqual(22, self.store.get_offset())

    def test_workforce_inbox_sends_safe_notification_once(self):
        self.workforce.inbox = [
            {
                "message_id": "MSG-ABCDEF123456",
                "sender_id": "AI-ENG-001",
                "task_ref": "ENG-007",
                "delivery_status": "CREATED",
                "subject": "Connector-Bericht",
                "body": "Sehr sensibler Volltext bleibt auf der NAS",
            }
        ]
        first = self.connector.publish_inbox_notifications()
        second = self.connector.publish_inbox_notifications()

        self.assertEqual(1, first)
        self.assertEqual(0, second)
        self.assertEqual(1, len(self.telegram.sent))
        reply = self.telegram.sent[0][1]
        self.assertIn("MSG-ABCDEF123456", reply)
        self.assertIn("Connector-Bericht", reply)
        self.assertNotIn("Sehr sensibler Volltext", reply)
        serialized = json.dumps(self.store.list_audit())
        self.assertNotIn("Sehr sensibler Volltext", serialized)

    def test_kill_switch_blocks_workforce_notifications(self):
        self.workforce.inbox = [
            {
                "message_id": "MSG-ABCDEF123457",
                "sender_id": "AI-ENG-001",
                "subject": "Nicht senden",
            }
        ]
        blocked = Settings(**{**self.settings.__dict__, "kill_switch": True})
        connector = TelegramConnector(
            blocked,
            self.store,
            self.telegram,
            self.workforce,
        )
        self.assertEqual(0, connector.publish_inbox_notifications())
        self.assertEqual([], self.telegram.sent)


class ConfigurationTest(unittest.TestCase):
    def valid_env(self):
        return {
            "TELEGRAM_CONNECTOR_ENABLED": "true",
            "TELEGRAM_KILL_SWITCH": "false",
            "TELEGRAM_BOT_TOKEN": BOT_TOKEN,
            "TELEGRAM_ALLOWED_CHAT_ID": "111",
            "TELEGRAM_ALLOWED_USER_ID": "222",
            "TELEGRAM_ALLOWED_RECIPIENT_IDS": "AI-ENG-001",
            "TELEGRAM_ALLOWED_TASK_IDS": "ENG-TG-REALTEST-001",
            "WORKFORCE_API_BASE_URL": "https://nas.example.test:8443",
            "WORKFORCE_BUS_TOKEN": BUS_TOKEN,
        }

    def test_disabled_is_default(self):
        with self.assertRaisesRegex(ConfigurationError, "TELEGRAM_CONNECTOR_DISABLED"):
            Settings.from_env({})

    def test_https_is_mandatory(self):
        env = self.valid_env()
        env["WORKFORCE_API_BASE_URL"] = "http://nas.example.test:8080"
        with self.assertRaisesRegex(ConfigurationError, "WORKFORCE_HTTPS_REQUIRED"):
            Settings.from_env(env)

    def test_required_secrets_are_not_optional(self):
        env = self.valid_env()
        env.pop("TELEGRAM_BOT_TOKEN")
        with self.assertRaisesRegex(ConfigurationError, "TELEGRAM_BOT_TOKEN_REQUIRED"):
            Settings.from_env(env)

    def test_secrets_can_be_loaded_from_files(self):
        with tempfile.TemporaryDirectory() as tempdir:
            bot_file = Path(tempdir) / "bot_token"
            bus_file = Path(tempdir) / "bus_token"
            bot_file.write_text(BOT_TOKEN, encoding="utf-8")
            bus_file.write_text(BUS_TOKEN, encoding="utf-8")
            env = self.valid_env()
            env.pop("TELEGRAM_BOT_TOKEN")
            env.pop("WORKFORCE_BUS_TOKEN")
            env["TELEGRAM_BOT_TOKEN_FILE"] = str(bot_file)
            env["WORKFORCE_BUS_TOKEN_FILE"] = str(bus_file)
            settings = Settings.from_env(env)
            self.assertEqual(BOT_TOKEN, settings.telegram_bot_token)
            self.assertEqual(BUS_TOKEN, settings.workforce_bus_token)

    def test_direct_and_file_secret_sources_conflict(self):
        env = self.valid_env()
        env["TELEGRAM_BOT_TOKEN_FILE"] = "/run/secrets/telegram_bot_token"
        with self.assertRaisesRegex(ConfigurationError, "TELEGRAM_BOT_TOKEN_SOURCE_CONFLICT"):
            Settings.from_env(env)

    def test_task_allowlist_is_parsed(self):
        env = self.valid_env()
        settings = Settings.from_env(env)
        self.assertEqual(frozenset({"ENG-TG-REALTEST-001"}), settings.allowed_task_ids)

    def test_recipient_allowlist_is_required(self):
        env = self.valid_env()
        env.pop("TELEGRAM_ALLOWED_RECIPIENT_IDS")
        with self.assertRaisesRegex(
            ConfigurationError, "TELEGRAM_ALLOWED_RECIPIENT_IDS_REQUIRED"
        ):
            Settings.from_env(env)

    def test_task_allowlist_is_required(self):
        env = self.valid_env()
        env.pop("TELEGRAM_ALLOWED_TASK_IDS")
        with self.assertRaisesRegex(
            ConfigurationError, "TELEGRAM_ALLOWED_TASK_IDS_REQUIRED"
        ):
            Settings.from_env(env)

    def test_task_parser_rejects_non_allowlisted_recipient(self):
        with self.assertRaisesRegex(ConnectorError, "RECIPIENT_NOT_ALLOWED"):
            parse_task_command(
                "/task UNKNOWN-001 CEO-TG-001 | Titel | Output",
                frozenset({"RAS-001"}),
                frozenset({"CEO-TG-001"}),
            )

    def test_task_parser_rejects_non_allowlisted_task(self):
        with self.assertRaisesRegex(ConnectorError, "TASK_ID_NOT_ALLOWED"):
            parse_task_command(
                "/task RAS-001 ENG-TG-OTHER-001 | Titel | Output",
                frozenset({"RAS-001"}),
                frozenset({"ENG-TG-REALTEST-001"}),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)


class OutboundDataBoundaryTest(unittest.TestCase):
    """The second data boundary: what of a bus message reaches Telegram.

    Telegram bot chats are cloud chats, not end-to-end encrypted. The default
    must stay metadata-only; forwarding a body is an explicit operator choice.
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tempdir.name) / "state.sqlite3"
        self.base = dict(
            enabled=True,
            kill_switch=False,
            telegram_bot_token=BOT_TOKEN,
            allowed_chat_id=111,
            allowed_user_id=222,
            allowed_recipient_ids=frozenset({"AI-ENG-001"}),
            allowed_task_ids=frozenset({"CEO-TG-TEST-001"}),
            workforce_base_url="https://nas.example.test:8443",
            workforce_bus_token=BUS_TOKEN,
            state_path=self.state_path,
            poll_timeout_seconds=1,
        )
        self.store = AuditStore(self.state_path)

    def tearDown(self):
        self.store.close()
        self.tempdir.cleanup()

    def _connector(self, **overrides):
        telegram = FakeTelegram()
        workforce = FakeWorkforce()
        workforce.inbox = [
            {
                "message_id": "MSG-" + "A" * 32,
                "sender_id": "AI-ENG-001",
                "subject": "Re: Bitte pruefen",
                "body": "Die fachliche Antwort des Agenten mit Details.",
                "task_ref": "CEO-TG-TEST-001",
                "delivery_status": "DELIVERED",
            }
        ]
        settings = Settings(**{**self.base, **overrides})
        connector = TelegramConnector(settings, self.store, telegram, workforce)
        connector.workforce = workforce
        return connector, telegram

    def test_default_policy_never_forwards_the_body(self):
        connector, telegram = self._connector()
        connector.publish_inbox_notifications()
        sent = "\n".join(text for _, text in telegram.sent)
        self.assertIn("MSG-", sent)
        self.assertIn("Re: Bitte pruefen", sent)
        self.assertNotIn("Die fachliche Antwort", sent)

    def test_body_is_withheld_when_the_task_is_not_allowlisted(self):
        # Review finding G-003: without this, BODY would carry the content of
        # any message reaching the connector identity into the private chat,
        # including work never approved for this channel.
        connector, telegram = self._connector(outbound_policy="BODY")
        connector.workforce.inbox[0]["task_ref"] = "FIN-GEHEIM-001"
        connector.publish_inbox_notifications()
        sent = telegram.sent[0][1]
        self.assertIn("MSG-", sent, "metadata still goes out")
        self.assertNotIn("Die fachliche Antwort", sent, "body must be withheld")

    def test_body_is_withheld_when_there_is_no_task_reference(self):
        connector, telegram = self._connector(outbound_policy="BODY")
        connector.workforce.inbox[0].pop("task_ref")
        connector.publish_inbox_notifications()
        self.assertNotIn("Die fachliche Antwort", telegram.sent[0][1])

    def test_body_policy_forwards_a_shortened_body(self):
        connector, telegram = self._connector(outbound_policy="BODY")
        connector.publish_inbox_notifications()
        sent = "\n".join(text for _, text in telegram.sent)
        self.assertIn("Die fachliche Antwort des Agenten mit Details.", sent)

    def test_body_is_truncated_to_the_configured_length(self):
        connector, telegram = self._connector(
            outbound_policy="BODY", outbound_body_chars=20
        )
        connector.publish_inbox_notifications()
        body_line = telegram.sent[0][1].split("\n\n", 1)[1]
        self.assertLessEqual(len(body_line), 20)
        self.assertTrue(body_line.endswith("…"))

    def test_hard_ceiling_wins_over_a_larger_configured_value(self):
        connector, telegram = self._connector(
            outbound_policy="BODY", outbound_body_chars=99999
        )
        connector.publish_inbox_notifications()
        body_line = telegram.sent[0][1].split("\n\n", 1)[1]
        self.assertLessEqual(len(body_line), MAX_OUTBOUND_BODY_CHARS)

    def test_one_notification_per_message_even_across_a_policy_change(self):
        # Deduplication is keyed on the bus message, not on how it is rendered.
        # Turning the policy on must not re-announce everything already sent -
        # that would be a notification storm. The new policy applies to what
        # arrives after it.
        metadata_only, first = self._connector()
        metadata_only.publish_inbox_notifications()
        with_body, second = self._connector(outbound_policy="BODY")
        with_body.publish_inbox_notifications()
        self.assertEqual(1, len(first.sent))
        self.assertEqual(0, len(second.sent), "already announced, must stay silent")
        self.assertNotIn("Die fachliche Antwort", first.sent[0][1])

    def test_a_new_message_under_the_body_policy_carries_the_body(self):
        connector, telegram = self._connector(outbound_policy="BODY")
        connector.publish_inbox_notifications()
        self.assertEqual(1, len(telegram.sent))
        self.assertIn("Die fachliche Antwort", telegram.sent[0][1])

    def test_invalid_policy_is_refused_at_configuration_time(self):
        with self.assertRaises(ConfigurationError):
            Settings.from_env({
                "TELEGRAM_CONNECTOR_ENABLED": "true",
                "TELEGRAM_KILL_SWITCH": "false",
                "TELEGRAM_BOT_TOKEN": BOT_TOKEN,
                "WORKFORCE_BUS_TOKEN": BUS_TOKEN,
                "WORKFORCE_API_BASE_URL": "https://nas.example.test:8443",
                "TELEGRAM_ALLOWED_CHAT_ID": "111",
                "TELEGRAM_ALLOWED_USER_ID": "222",
                "TELEGRAM_ALLOWED_RECIPIENT_IDS": "AI-ENG-001",
                "TELEGRAM_ALLOWED_TASK_IDS": "CEO-TG-TEST-001",
                "TELEGRAM_OUTBOUND_POLICY": "EVERYTHING",
            })

    def test_default_from_environment_is_metadata_only(self):
        settings = Settings.from_env({
            "TELEGRAM_CONNECTOR_ENABLED": "true",
            "TELEGRAM_KILL_SWITCH": "false",
            "TELEGRAM_BOT_TOKEN": BOT_TOKEN,
            "WORKFORCE_BUS_TOKEN": BUS_TOKEN,
            "WORKFORCE_API_BASE_URL": "https://nas.example.test:8443",
            "TELEGRAM_ALLOWED_CHAT_ID": "111",
            "TELEGRAM_ALLOWED_USER_ID": "222",
            "TELEGRAM_ALLOWED_RECIPIENT_IDS": "AI-ENG-001",
            "TELEGRAM_ALLOWED_TASK_IDS": "CEO-TG-TEST-001",
        })
        self.assertEqual("METADATA_ONLY", settings.outbound_policy)
