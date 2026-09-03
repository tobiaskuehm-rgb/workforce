import json
import sqlite3
import pathlib
import tempfile
import unittest
from pathlib import Path

import telegram_connector
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
        self.acknowledged = []
        self.ack_error = None
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

    def acknowledge(self, message_id, *, note):
        # Modelliert das Verhalten, auf das es ankommt - aus der Quelle, nicht
        # aus der Erinnerung: Der Bus setzt den Zustand der Nachricht, und ein
        # zweiter Versuch auf einem nicht mehr offenen Datensatz wird mit
        # BUS_ACK_ALREADY_FINAL abgelehnt (002_workforce_bus.sql). Die erste
        # Fassung vermerkte nur und liess den Posteingang unveraendert - und
        # verdeckte damit genau den Pfad, um den es bei G-056 geht.
        if self.ack_error is not None:
            raise telegram_connector.ConnectorError(self.ack_error)
        for message in self.inbox:
            if message.get("message_id") == message_id:
                if message.get("delivery_status") != "DELIVERED":
                    raise telegram_connector.ConnectorError("BUS_ACK_ALREADY_FINAL")
                message["delivery_status"] = "ACCEPTED"
                break
        self.acknowledged.append((message_id, note))
        return {"message_id": message_id, "delivery_status": "ACCEPTED"}


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


class TheReturnLegIsAcknowledgedTest(unittest.TestCase):
    """G-053: der Rueckweg bestaetigte nie, und das kostete zwei Dinge.

    Erstens den Nachweis. Ohne Bestaetigung bleibt eine Nachricht fuer immer
    `DELIVERED`, und aus der Datenbank allein laesst sich damit nie sagen, ob
    eine Benachrichtigung den CEO erreicht hat - genau das, was Phase 5
    rekonstruierbar verlangt.

    Zweitens die zweite Verteidigungslinie. Der Dublettenschutz des Rueckwegs
    lag ausschliesslich im lokalen SQLite-Speicher. Geht der Datentraeger
    verloren - der Fall, den dieses Projekt fuer den Agenten seit `G-002`
    ausdruecklich testet -, wird jede Nachricht im Posteingang erneut
    angekuendigt. Der Agent hat dafuer zwei Linien; der Rueckweg hatte eine.

    Reihenfolge wie im Agenten (`G-001`): erst senden, dann bestaetigen.
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tempdir.name) / "state.sqlite3"
        self.store = AuditStore(self.state_path)
        self.settings = Settings(
            enabled=True, kill_switch=False, telegram_bot_token=BOT_TOKEN,
            allowed_chat_id=111, allowed_user_id=222,
            allowed_recipient_ids=frozenset({"AI-ENG-001"}),
            allowed_task_ids=frozenset({"CEO-TG-TEST-001"}),
            workforce_base_url="https://nas.example.test:8443",
            workforce_bus_token=BUS_TOKEN, state_path=self.state_path,
            poll_timeout_seconds=1,
        )

    def tearDown(self):
        self.store.close()
        self.tempdir.cleanup()

    def _connector(self):
        telegram = FakeTelegram()
        workforce = FakeWorkforce()
        workforce.inbox = [{
            "message_id": "MSG-" + "A" * 32,
            "sender_id": "AI-ENG-001",
            "subject": "Re: Bitte pruefen",
            "body": "Antworttext.",
            "task_ref": "CEO-TG-TEST-001",
            "delivery_status": "DELIVERED",
        }]
        connector = TelegramConnector(self.settings, self.store, telegram, workforce)
        connector.workforce = workforce
        return connector, telegram, workforce

    def test_a_delivered_notification_is_acknowledged(self):
        connector, telegram, workforce = self._connector()
        self.assertEqual(1, connector.publish_inbox_notifications())
        self.assertEqual(1, len(telegram.sent))
        self.assertEqual([("MSG-" + "A" * 32, "Per Telegram an den CEO zugestellt.")],
                         workforce.acknowledged)

    def test_a_failed_send_is_not_acknowledged(self):
        # Die Reihenfolge ist der ganze Punkt: Bestaetigen, was nie ankam,
        # macht aus einer verlorenen Nachricht eine erledigte.
        connector, telegram, workforce = self._connector()

        def kaputt(chat_id, text):
            raise telegram_connector.ConnectorError("TELEGRAM_SEND_FAILED")

        telegram.send_message = kaputt
        self.assertEqual(0, connector.publish_inbox_notifications())
        self.assertEqual([], workforce.acknowledged)

    def test_a_failed_acknowledgement_does_not_lose_the_notification(self):
        # Umgekehrt: Die Nachricht *ist* beim CEO. Dass der Bus es noch nicht
        # weiss, darf die Runde nicht abbrechen - es wird vermerkt.
        connector, telegram, workforce = self._connector()
        workforce.ack_error = "WORKFORCE_HTTP_503"
        self.assertEqual(1, connector.publish_inbox_notifications())
        self.assertEqual(1, len(telegram.sent))
        ereignisse = [eintrag["event_type"] for eintrag in self.store.list_audit()]
        self.assertIn("WORKFORCE_NOTIFICATION_ACK_FAILED", ereignisse)
        self.assertIn("WORKFORCE_NOTIFICATION_SENT", ereignisse)

    def test_the_acknowledgement_is_audited_locally_as_well(self):
        connector, _, _ = self._connector()
        connector.publish_inbox_notifications()
        ereignisse = [eintrag["event_type"] for eintrag in self.store.list_audit()]
        self.assertIn("WORKFORCE_NOTIFICATION_ACKNOWLEDGED", ereignisse)
        self.assertLess(ereignisse.index("WORKFORCE_NOTIFICATION_SENT"),
                        ereignisse.index("WORKFORCE_NOTIFICATION_ACKNOWLEDGED"),
                        "erst senden, dann bestaetigen")

    def test_a_suppressed_duplicate_is_not_acknowledged_twice(self):
        connector, _, workforce = self._connector()
        connector.publish_inbox_notifications()
        connector.publish_inbox_notifications()
        self.assertEqual(1, len(workforce.acknowledged))

    def test_a_failed_acknowledgement_is_caught_up_on_the_next_round(self):
        """G-056: sonst bleibt die Nachricht ueber den Fehlerpfad fuer immer offen.

        Erste Runde: Versand klappt, Bestaetigung scheitert. Der lokale
        Speicher steht damit auf SENT, und beim naechsten Mal wuerde der
        Dublettenschutz die Nachricht ueberspringen - fuer immer. Genau der
        Zustand, gegen den G-053 gebaut wurde, nur ueber den Fehlerpfad
        erreicht.
        """
        connector, telegram, workforce = self._connector()
        workforce.ack_error = "WORKFORCE_HTTP_503"
        self.assertEqual(1, connector.publish_inbox_notifications())
        self.assertEqual([], workforce.acknowledged)
        self.assertEqual("DELIVERED", workforce.inbox[0]["delivery_status"])

        workforce.ack_error = None
        connector.publish_inbox_notifications()
        self.assertEqual(1, len(telegram.sent), "kein zweiter Versand")
        self.assertEqual(1, len(workforce.acknowledged), "aber die Bestaetigung")
        self.assertEqual("ACCEPTED", workforce.inbox[0]["delivery_status"])

    def test_an_already_acknowledged_message_is_left_alone(self):
        # Die Gegenprobe zum Nachholen: Ist der Bus zufrieden, wird nicht bei
        # jedem Durchgang erneut bestaetigt. get_inbox liefert die Nachricht
        # weiterhin - sie verschwindet nie -, also braucht es diese Grenze.
        connector, _, workforce = self._connector()
        connector.publish_inbox_notifications()
        self.assertEqual(1, len(workforce.acknowledged))
        for _ in range(3):
            connector.publish_inbox_notifications()
        self.assertEqual(1, len(workforce.acknowledged))

    def test_the_fingerprint_ignores_the_delivery_status(self):
        """G-056: sonst wird jede bestaetigte Nachricht zum Dauerkonflikt.

        Der Fingerabdruck soll die Nachricht kennzeichnen, nicht ihren
        Zustand. Solange der Connector nicht bestaetigte, aenderte sich der
        Zustand nie und der Fehler war unsichtbar.
        """
        connector, _, workforce = self._connector()
        connector.publish_inbox_notifications()
        self.assertEqual("ACCEPTED", workforce.inbox[0]["delivery_status"])
        connector.publish_inbox_notifications()
        gruende = [eintrag["metadata"].get("reason")
                   for eintrag in self.store.list_audit()
                   if eintrag["event_type"] == "WORKFORCE_NOTIFICATION_SKIPPED"]
        self.assertEqual(["DUPLICATE"], gruende,
                         "ein CONFLICT hiesse, der Fingerabdruck haengt am Zustand")

    def test_the_request_id_names_the_message(self):
        # Damit die Auditrekonstruktion Bestaetigung und Nachricht ohne
        # Zwischenschicht aneinanderbinden kann.
        quelle = pathlib.Path(telegram_connector.__file__).read_text(encoding="utf-8")
        self.assertIn('request_id=f"TG-ACK-{message_id}"', quelle)


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


class ClaimLeaseTest(unittest.TestCase):
    """`G-083`: Ein Update in CLAIMED verfaellt nach einer Frist - und nur dann.

    Gemessen in der Gesamtpruefung vom 2026-09-03: Claim, kein Abschluss,
    zweiter Prozess, dasselbe Update von Telegram erneut geliefert -
    DUPLICATE, fuer immer. Ein /task des CEO war weg, und die Auditzeile sagte
    "schon erledigt".
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pfad = Path(self.tmp.name) / "state.sqlite3"
        self.now = 1000.0

    def _store(self, **extra):
        return AuditStore(self.pfad, clock=lambda: self.now, **extra)

    def _connector(self, store):
        settings = Settings(
            enabled=True, kill_switch=False, telegram_bot_token=BOT_TOKEN,
            allowed_chat_id=111, allowed_user_id=222,
            allowed_recipient_ids=frozenset({"AI-ENG-001"}),
            allowed_task_ids=frozenset({"CEO-TG-TEST-002"}),
            workforce_base_url="https://nas.example.test:8443",
            workforce_bus_token=BUS_TOKEN, state_path=self.pfad,
        )
        telegram, workforce = FakeTelegram(), FakeWorkforce()
        return TelegramConnector(settings, store, telegram, workforce), telegram, workforce

    def test_a_redelivery_within_the_lease_is_still_a_duplicate(self):
        erster = self._store()
        self.assertEqual("CLAIMED", erster.claim_update(4711, "h"))
        erster.close()                       # der Prozess stirbt vor finish_update
        self.now += 5
        zweiter = self._store()
        self.assertEqual("DUPLICATE", zweiter.claim_update(4711, "h"))

    def test_a_crashed_claim_is_retried_after_the_lease(self):
        erster = self._store()
        erster.claim_update(4711, "h")
        erster.close()
        self.now += telegram_connector.UPDATE_LEASE_SECONDS + 1
        zweiter = self._store()
        self.assertEqual("RETRY", zweiter.claim_update(4711, "h"))
        row = zweiter._connection.execute(
            "SELECT processing_status, attempts FROM processed_updates WHERE update_id = 4711"
        ).fetchone()
        self.assertEqual(("CLAIMED", 2), row)

    def test_the_connector_processes_a_retried_update_and_says_so(self):
        # Ende zu Ende: der CEO-Befehl kommt beim zweiten Anlauf durch.
        item = update(4712, "/task AI-ENG-001 CEO-TG-TEST-002 | Technikcheck | Kurzer Bericht")
        erster = self._store()
        erster.claim_update(4712, TelegramConnector._fingerprint(item))
        erster.close()
        self.now += telegram_connector.UPDATE_LEASE_SECONDS + 1
        connector, telegram, workforce = self._connector(self._store())
        self.assertEqual("PROCESSED", connector.process_update(item))
        self.assertEqual(1, len(workforce.tasks))
        ereignisse = [e["event_type"] for e in connector.store.list_audit()]
        self.assertIn("UPDATE_RETRIED", ereignisse)
        self.assertNotIn("DUPLICATE_IGNORED", ereignisse)

    def test_two_processes_cannot_both_take_an_expired_claim(self):
        erster = self._store()
        erster.claim_update(4713, "h")
        erster.close()
        self.now += telegram_connector.UPDATE_LEASE_SECONDS + 1
        a, b = self._store(), self._store()
        self.assertEqual("RETRY", a.claim_update(4713, "h"))
        self.assertEqual("DUPLICATE", b.claim_update(4713, "h"),
                         "der zweite sieht die frische Lease des ersten")

    def test_a_finished_update_never_becomes_a_retry(self):
        store = self._store()
        store.claim_update(4714, "h")
        store.finish_update(4714, "PROCESSED")
        self.now += 10 * telegram_connector.UPDATE_LEASE_SECONDS
        self.assertEqual("DUPLICATE", store.claim_update(4714, "h"))

    def test_attempts_run_out_and_the_update_is_abandoned_audibly(self):
        item = update(4715, "/status")
        fp = TelegramConnector._fingerprint(item)
        store = self._store(max_attempts=3)
        store.claim_update(4715, fp)                       # Versuch 1
        for erwartet in ("RETRY", "RETRY"):                 # Versuche 2 und 3
            self.now += telegram_connector.UPDATE_LEASE_SECONDS + 1
            self.assertEqual(erwartet, store.claim_update(4715, fp))
        self.now += telegram_connector.UPDATE_LEASE_SECONDS + 1
        connector, telegram, _ = self._connector(store)
        self.assertEqual("EXHAUSTED", connector.process_update(item))
        self.assertEqual([], telegram.sent)
        ereignisse = [e["event_type"] for e in store.list_audit()]
        self.assertIn("UPDATE_ABANDONED", ereignisse)
        row = store._connection.execute(
            "SELECT processing_status FROM processed_updates WHERE update_id = 4715").fetchone()
        self.assertEqual("FAILED", row[0])

    def test_a_store_from_before_the_lease_is_upgraded_in_place(self):
        # Die Datei auf dem Kettenvolume ist aelter als G-083. Sie bekommt die
        # zwei Spalten dazu, nichts wird umgeschrieben, und ein alter
        # haengengebliebener CLAIMED-Eintrag wird genau einmal nachgeholt.
        alt = sqlite3.connect(self.pfad)
        alt.executescript("""
            CREATE TABLE processed_updates (
                update_id INTEGER PRIMARY KEY, payload_hash TEXT NOT NULL,
                processing_status TEXT NOT NULL, created_at TEXT NOT NULL, finished_at TEXT);
            INSERT INTO processed_updates VALUES (1, 'h', 'CLAIMED', '2026-09-01T00:00:00+00:00', NULL);
            INSERT INTO processed_updates VALUES (2, 'h', 'PROCESSED', '2026-09-01T00:00:00+00:00', '2026-09-01T00:00:01+00:00');
        """)
        alt.commit(); alt.close()
        store = self._store()
        spalten = {r[1] for r in store._connection.execute("PRAGMA table_info(processed_updates)")}
        self.assertTrue({"claimed_at", "attempts"} <= spalten)
        self.assertEqual("RETRY", store.claim_update(1, "h"))
        self.assertEqual("DUPLICATE", store.claim_update(2, "h"))
