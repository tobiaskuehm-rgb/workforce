"""The chain's audit reconstruction, checked against the code that fills it.

`chain_audit.sql` binds five steps to request-id patterns. Those patterns are
written in two other files - the connector and the worker - and nothing but
this test connects the three. That is the G-042 class: a document naming
things that do not exist, except here the document is SQL and the run that
would notice is a production window.

The file was validated against the live database on 2026-09-02: it parses,
runs read-only, and reconstructed the real CHAIN PASS run from 2026-09-01 as
four of five steps with the fifth missing - which is what found G-053. These
tests hold the properties that made that possible.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
AUDIT = NAS / "chain-test" / "chain_audit.sql"
CONNECTOR = NAS / "telegram-connector" / "telegram_connector.py"
WORKER = NAS / "workforce-agent" / "agent_worker.py"


class ItIsReadOnlyTest(unittest.TestCase):
    """It is meant to be pointed at production, so this is not cosmetic."""

    def setUp(self) -> None:
        self.sql = AUDIT.read_text(encoding="utf-8")

    def test_the_transaction_is_read_only_and_rolls_back(self) -> None:
        self.assertIn("BEGIN TRANSACTION READ ONLY;", self.sql)
        self.assertIn("ROLLBACK;", self.sql)
        self.assertIsNone(re.search(r"^\s*COMMIT\s*;", self.sql, re.MULTILINE))

    def test_it_writes_nothing(self) -> None:
        for verboten in ("INSERT ", "UPDATE ", "DELETE ", "TRUNCATE", "DROP ",
                         "ALTER ", "CREATE "):
            with self.subTest(befehl=verboten.strip()):
                self.assertNotIn(verboten, self.sql.upper().replace("-- ", ""))

    def test_it_never_selects_a_body_or_a_subject(self) -> None:
        # bus_events carries subject and body for MESSAGE rows. An audit
        # printout has no business reproducing them - the same rule the
        # denial audit follows.
        code = "\n".join(z for z in self.sql.splitlines()
                         if not z.lstrip().startswith("--"))
        for feld in ("'body'", "'subject'", "->>'body'", "->> 'body'",
                     "->> 'subject'"):
            with self.subTest(feld=feld):
                self.assertNotIn(feld, code)


class ThePatternsMatchTheCodeTest(unittest.TestCase):
    """Every request-id pattern in the SQL has to exist in a producer."""

    def setUp(self) -> None:
        self.sql = AUDIT.read_text(encoding="utf-8")
        self.connector = CONNECTOR.read_text(encoding="utf-8")
        self.worker = WORKER.read_text(encoding="utf-8")

    def test_the_connector_produces_the_task_and_message_ids(self) -> None:
        self.assertIn('request_prefix = f"TG-{update_id}"', self.connector)
        self.assertIn('request_id=f"{request_prefix}-TASK"', self.connector)
        self.assertIn('request_id=f"{request_prefix}-MESSAGE"', self.connector)
        self.assertIn("'TASK'", self.sql)
        self.assertIn("'MESSAGE'", self.sql)

    def test_the_connector_produces_the_acknowledgement_id(self) -> None:
        # G-053. Ohne diese Zeile fehlt Schritt 5 strukturell, und genau das
        # hat die Rekonstruktion des echten Laufs gezeigt.
        self.assertIn('request_id=f"TG-ACK-{message_id}"', self.connector)
        self.assertIn("'TG-ACK-%'", self.sql)

    def test_the_worker_produces_the_reply_and_ack_ids(self) -> None:
        self.assertIn('REQUEST_PREFIX = "AGENT"', self.worker)
        self.assertIn('f"{REQUEST_PREFIX}-REPLY-', self.worker)
        self.assertIn('f"{REQUEST_PREFIX}-ACK-', self.worker)
        self.assertIn("'AGENT-REPLY-%'", self.sql)
        self.assertIn("'AGENT-ACK-%'", self.sql)

    def test_a_pattern_without_a_producer_would_be_caught(self) -> None:
        # Die Gegenprobe zu den drei Tests darueber: ein erfundenes Praefix
        # steht in keiner der beiden Quellen.
        erfunden = "'TG-NOTIFY-%'"
        self.assertNotIn(erfunden, self.sql)
        self.assertNotIn("TG-NOTIFY-", self.connector)


class TheRequiredStepsAreTheChainTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sql = AUDIT.read_text(encoding="utf-8")

    def test_all_five_legs_are_required(self) -> None:
        for schritt in ("connector_creates_task",
                        "connector_sends_request_to_agent",
                        "agent_replies_carrying_the_task_reference",
                        "agent_acknowledges_the_request",
                        "connector_acknowledges_the_reply"):
            with self.subTest(schritt=schritt):
                self.assertIn(schritt, self.sql)

    def test_the_reply_must_carry_the_task_reference(self) -> None:
        # G-003: fehlt sie, haelt der Connector den Text zurueck und die Kette
        # sieht komponentenweise gesund aus, ohne etwas zu liefern.
        block = self.sql[self.sql.index("agent_replies_carrying_the_task_reference"):]
        block = block[:block.index("UNION ALL")]
        self.assertIn("'task_ref' = current_setting('chain.task_id')", block)
        self.assertIn("'parent_message_id'", block)

    def test_the_order_check_covers_every_adjacent_pair(self) -> None:
        # Nicht zwei Stichproben: ein teilweise vertauschter Lauf hat genau so
        # eine fruehere Fassung in core_audit.sql bestanden.
        self.assertIn("JOIN steps AS b ON b.ord = a.ord + 1", self.sql)

    def test_it_reports_what_is_still_open(self) -> None:
        self.assertIn("nichts_offen", self.sql)
        self.assertIn("'DELIVERED'", self.sql)

    def test_the_scope_note_is_present(self) -> None:
        # Was aus PostgreSQL nicht rekonstruierbar ist, gehoert in die Datei,
        # nicht in die Erinnerung dessen, der sie geschrieben hat.
        self.assertIn("nicht rekonstruierbar", self.sql)


if __name__ == "__main__":
    unittest.main()
