"""The closing artefact of Phase 5, and the four proofs it has to carry.

CEO addition to Phase 5: "Der Testlauf weist pro Vorgang Datenmenge, Felder,
Provideraufrufe, Tokens beziehungsweise belastbare Schaetzung, Kostenobergrenze,
Route und Dublettenentscheidung aus", and the report must be "ohne kopierte
Vollpayloads oder Secrets".

The last clause is the one worth testing hardest, because it is the one a
report naturally violates: the easiest way to make a run explainable is to
write down what was in it. So the first test here feeds a message whose body
and subject are unmistakable strings and demands that neither reaches the
report, in either half.

The duplicate proof is the other one that matters: "Eine doppelt zugestellte
Nachricht erzeugt genau einen Provideraufruf und ein Ergebnis." That is not a
property of the report but of the worker; the report is where it becomes
visible, which is why it is checked here through both at once.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import agent_worker
import budget as budget_module
import efficiency_report
import model_allowlist
import state_store
from test_agent_worker import FakeBus, ScriptedProvider, message

GEHEIM = "Kontostand 4711 und das Passwort lautet hunter2"
BETREFF = "Streng vertrauliche Betreffzeile"


def bericht() -> efficiency_report.Report:
    return efficiency_report.Report(run_id="TEST-1")


class NothingLeaksIntoTheReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.report = bericht()
        agent_worker.handle_message(
            FakeBus(), ScriptedProvider(), message(body=GEHEIM, subject=BETREFF),
            policy="BODY", report=self.report,
        )

    def test_the_operation_was_recorded_at_all(self) -> None:
        # Ohne das waeren die beiden Tests unten gruen ueber einem leeren Bericht.
        self.assertEqual(1, len(self.report.operations))
        self.assertEqual("ANSWERED", self.report.operations[0].outcome)

    def test_neither_half_contains_the_payload(self) -> None:
        for name, text in (("json", self.report.as_json()),
                           ("summary", self.report.as_summary())):
            with self.subTest(haelfte=name):
                self.assertNotIn(GEHEIM, text)
                self.assertNotIn("hunter2", text)
                self.assertNotIn(BETREFF, text)

    def test_it_records_the_shape_instead_of_the_content(self) -> None:
        operation = self.report.operations[0]
        self.assertIn("body", operation.fields_sent)
        self.assertGreater(operation.chars_sent, len(GEHEIM))
        self.assertEqual(64, len(operation.payload_sha256 or ""))


class EveryRequiredFigureIsPresentTest(unittest.TestCase):
    """The list from the CEO addition, item by item."""

    def setUp(self) -> None:
        self.report = bericht()
        agent_worker.handle_message(
            FakeBus(), ScriptedProvider(), message(), policy="BODY",
            budget=budget_module.Budget(max_cost_usd=0.50), report=self.report)
        self.operation = self.report.operations[0].as_dict()

    def test_data_volume_and_fields(self) -> None:
        self.assertGreater(self.operation["chars_sent"], 0)
        self.assertTrue(self.operation["fields_sent"])

    def test_provider_calls(self) -> None:
        self.assertEqual(1, self.operation["provider_calls"])

    def test_tokens_are_marked_as_an_estimate_when_they_are_one(self) -> None:
        # Die Attrappe meldet keine Nutzung, wie der Echo-Provider auch. Eine
        # Schaetzung, die sich nicht von einer Messung unterscheiden laesst,
        # waere schlechter als gar keine.
        self.assertTrue(self.operation["tokens_estimated"])
        self.assertGreater(self.operation["input_tokens"], 0)
        self.assertEqual(
            model_allowlist.ALLOWLIST["echo-v1"].max_output_tokens,
            self.operation["output_tokens"],
            "fehlende Usage muss die konservative Ausgabe-Reserve behalten",
        )

    def test_the_cost_ceiling_stands_next_to_the_estimate(self) -> None:
        # Eine Zahl ohne ihre Grenze sagt nichts darueber, ob der Lauf drin blieb.
        self.assertEqual(0.50, self.operation["cost_ceiling_usd"])
        self.assertIn("estimated_cost_usd", self.operation)

    def test_the_route_is_the_sender_from_the_bus_record(self) -> None:
        self.assertEqual("SAO-001", self.operation["sender_id"])
        self.assertEqual("SAO-001", self.operation["reply_recipient_id"])

    def test_the_duplicate_decision_is_recorded(self) -> None:
        self.assertEqual(efficiency_report.FIRST_DELIVERY,
                         self.operation["duplicate_decision"])

    def test_the_model_is_named(self) -> None:
        self.assertIn(self.operation["model"], model_allowlist.ALLOWLIST)


class ADoubleDeliveryCostsOneCallTest(unittest.TestCase):
    """Verbindlicher Phase-5-Nachweis, ueber Worker und Bericht zugleich."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = state_store.AgentStateStore(
            Path(self.tempdir.name) / "state.sqlite3")

    def tearDown(self) -> None:
        self.store.close()
        self.tempdir.cleanup()

    def test_the_same_message_twice_is_one_call_and_one_result(self) -> None:
        report = bericht()
        provider = ScriptedProvider()
        bus = FakeBus()
        zustellung = message()
        for _ in range(2):
            agent_worker.handle_message(bus, provider, zustellung, policy="BODY",
                                        state=self.store, report=report)

        self.assertEqual(1, len(provider.seen), "das Modell darf einmal gefragt werden")
        self.assertEqual(1, report.provider_calls)
        self.assertEqual(1, len(bus.sent), "und genau eine Antwort entstehen")

        ergebnisse = [o.outcome for o in report.operations]
        self.assertEqual(["ANSWERED", "ALREADY_HANDLED"], ergebnisse)
        entscheidungen = [o.duplicate_decision for o in report.operations]
        self.assertEqual(
            [efficiency_report.FIRST_DELIVERY,
             efficiency_report.DUPLICATE_SUPPRESSED], entscheidungen)
        self.assertEqual(1, report.as_dict()["totals"]["duplicates_suppressed"])

    def test_identical_content_under_two_ids_is_two_operations(self) -> None:
        """"Inhaltsaehnlichkeit allein darf keine automatische Wiederverwendung
        ausloesen, weil dadurch Daten zwischen Aufgaben vermischt werden
        koennten." (CEO-Ergaenzung Phase 5, Punkt 3.)

        Die Kontrolle ist hier eine Abwesenheit - es gibt keinen
        Aehnlichkeitsvergleich -, und Abwesenheiten verschwinden lautlos.
        Deshalb steht sie als Test da: zwei Nachrichten mit identischem Rumpf
        und verschiedener Id sind zwei Vorgaenge, nicht einer.
        """
        report = bericht()
        provider = ScriptedProvider()
        bus = FakeBus()
        for kennung in ("MSG-" + "C" * 32, "MSG-" + "D" * 32):
            agent_worker.handle_message(
                bus, provider, message(message_id=kennung, body="Wortgleich."),
                policy="BODY", state=self.store, report=report)

        self.assertEqual(2, len(provider.seen), "beide muessen gefragt werden")
        self.assertEqual(2, report.provider_calls)
        self.assertEqual(
            [efficiency_report.FIRST_DELIVERY, efficiency_report.FIRST_DELIVERY],
            [o.duplicate_decision for o in report.operations])
        # Und der Digest taugt auch nicht versehentlich als
        # Wiederverwendungsschluessel: Er deckt die ganze uebertragene Nutzlast
        # ab, zu der die Nachrichten-Id gehoert. Zwei wortgleiche Nachrichten
        # haben deshalb verschiedene Digests. Er weist aus, *was uebertragen
        # wurde*, nicht *welcher Text darin stand* - was die staerkere
        # Eigenschaft ist, aber nicht die, die ich zuerst erwartet hatte.
        self.assertNotEqual(report.operations[0].payload_sha256,
                            report.operations[1].payload_sha256)
        self.assertEqual(report.operations[0].chars_sent,
                         report.operations[1].chars_sent,
                         "gleich lang waren sie trotzdem")

    def test_without_the_store_the_suppression_would_not_happen(self) -> None:
        # Die Gegenprobe: der Nachweis oben belegt eine Kontrolle, nicht einen
        # Zufall. Ohne Zustandsspeicher wird zweimal gefragt - genau der
        # Zustand, gegen den der Speicher existiert.
        report = bericht()
        provider = ScriptedProvider()
        zustellung = message()
        for _ in range(2):
            agent_worker.handle_message(FakeBus(), provider, zustellung,
                                        policy="BODY", report=report)
        self.assertEqual(2, len(provider.seen))
        self.assertEqual(2, report.provider_calls)


class RefusalsAreVisibleTest(unittest.TestCase):
    """"Ein nicht freigegebenes Feld, Modell oder Ziel wird verweigert und ist
    im Audit sichtbar." Sichtbar heisst hier: mit Kennung, nicht als Luecke."""

    def test_a_data_boundary_refusal_names_itself(self) -> None:
        report = bericht()
        agent_worker.handle_message(
            FakeBus(), ScriptedProvider(), message(body="x" * 9000),
            policy="BODY", report=report)
        operation = report.operations[0]
        self.assertEqual("REFUSED", operation.outcome)
        self.assertIn("AGENT_OUTBOUND_TOO_LARGE", operation.refusal or "")
        self.assertEqual(0, operation.provider_calls)

    def test_a_model_refusal_names_itself(self) -> None:
        class OhneModell(ScriptedProvider):
            model = ""

        report = bericht()
        agent_worker.handle_message(FakeBus(), OhneModell(), message(),
                                    policy="BODY", report=report)
        operation = report.operations[0]
        self.assertEqual("REFUSED", operation.outcome)
        self.assertIn("AGENT_MODEL_NOT_CONFIGURED", operation.refusal or "")
        self.assertEqual(0, operation.provider_calls)

    def test_a_failed_provider_is_not_reported_as_zero_usage(self) -> None:
        report = bericht()
        agent_worker.handle_message(
            FakeBus(), ScriptedProvider(error="AGENT_PROVIDER_UNREACHABLE"),
            message(), policy="BODY", report=report,
            budget=budget_module.Budget(max_cost_usd=1.0),
        )
        operation = report.operations[0]
        self.assertEqual(1, operation.provider_calls)
        self.assertTrue(operation.tokens_estimated)
        self.assertGreater(operation.input_tokens + operation.output_tokens, 0)


class AnAbortedRunSaysSoTest(unittest.TestCase):
    """Ein Lauf, der drei von zwanzig geschafft hat, liest sich sonst wie
    einer mit drei Nachrichten - und das ist die gefaehrlichere Lesart."""

    class InboxBus(FakeBus):
        def __init__(self, anzahl):
            super().__init__()
            self.messages = [message(message_id="MSG-" + chr(65 + i) * 32)
                             for i in range(anzahl)]

        def status(self):
            return {"channel_status": "TESTING"}

        def inbox(self, limit=25):
            return self.messages[:limit]

    def test_a_budget_stop_is_named_in_the_report(self) -> None:
        report = bericht()
        bus = self.InboxBus(5)
        agent_worker.poll_once(
            bus, ScriptedProvider(), policy="BODY", report=report,
            budget=budget_module.Budget(max_messages=2))
        totals = report.as_dict()["totals"]
        self.assertFalse(totals["complete"])
        self.assertIn("AGENT_BUDGET_EXHAUSTED:messages", totals["stopped_reason"])
        self.assertEqual(3, totals["left_untouched"])
        self.assertIn("ABGEBROCHEN", report.as_summary())

    def test_a_complete_run_says_nothing_about_stopping(self) -> None:
        # Die Gegenprobe: sonst waere jeder Lauf "abgebrochen".
        report = bericht()
        agent_worker.poll_once(self.InboxBus(2), ScriptedProvider(),
                               policy="BODY", report=report)
        totals = report.as_dict()["totals"]
        self.assertTrue(totals["complete"])
        self.assertIsNone(totals["stopped_reason"])
        self.assertNotIn("ABGEBROCHEN", report.as_summary())

    def test_the_first_reason_wins(self) -> None:
        # Der Grund ist die Ursache, nicht die letzte Meldung.
        report = bericht()
        report.stopped("ERSTER", left_untouched=2)
        report.stopped("ZWEITER", left_untouched=1)
        self.assertEqual("ERSTER", report.stopped_reason)
        self.assertEqual(3, report.left_untouched)


class TheArtefactIsWritableTest(unittest.TestCase):
    def setUp(self) -> None:
        self.report = bericht()
        agent_worker.handle_message(FakeBus(), ScriptedProvider(), message(),
                                    policy="BODY", report=self.report)

    def test_it_writes_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as ordner:
            vorlage = Path(ordner) / "efficiency.json"
            geschrieben = agent_worker.write_report(self.report, str(vorlage))
            self.assertEqual(str(Path(ordner) / "efficiency-TEST-1.json"), geschrieben)
            geladen = json.loads(Path(geschrieben).read_text(encoding="utf-8"))
        self.assertEqual("TEST-1", geladen["run_id"])
        self.assertEqual(1, geladen["totals"]["operations"])

    # --- G-088: ein Artefakt je Lauf, kleine Aufbewahrungsregel -------------

    def test_two_runs_leave_two_files(self) -> None:
        # Vorher: derselbe Pfad fuer jeden Lauf, geoeffnet mit "w" - der zweite
        # ersetzte den ersten, waehrend der Kommentar in main() das Gegenteil
        # behauptete.
        zweiter = efficiency_report.Report(run_id="TEST-2")
        with tempfile.TemporaryDirectory() as ordner:
            vorlage = str(Path(ordner) / "efficiency.json")
            agent_worker.write_report(self.report, vorlage)
            agent_worker.write_report(zweiter, vorlage)
            dateien = sorted(p.name for p in Path(ordner).iterdir())
        self.assertEqual(["efficiency-TEST-1.json", "efficiency-TEST-2.json"], dateien)

    def test_an_existing_report_for_the_same_run_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as ordner:
            vorlage = str(Path(ordner) / "efficiency.json")
            erster = agent_worker.write_report(self.report, vorlage)
            inhalt = Path(erster).read_text(encoding="utf-8")
            nochmal = efficiency_report.Report(run_id="TEST-1")   # anderer Inhalt
            self.assertIsNone(agent_worker.write_report(nochmal, vorlage))
            self.assertEqual(inhalt, Path(erster).read_text(encoding="utf-8"))

    def test_retention_keeps_the_newest_and_leaves_foreign_files_alone(self) -> None:
        import os, time
        with tempfile.TemporaryDirectory() as ordner:
            vorlage = str(Path(ordner) / "efficiency.json")
            fremd = Path(ordner) / "efficiency-notes.txt"
            fremd.write_text("nicht anfassen", encoding="utf-8")
            basis = time.time() - 100
            for i, run in enumerate(("A", "B", "C")):
                pfad = agent_worker.write_report(efficiency_report.Report(run_id=run),
                                                 vorlage, keep=2)
                os.utime(pfad, (basis + i, basis + i))
            # Der dritte Lauf hat die Regel ausgeloest: A ist weg, B und C da.
            agent_worker.write_report(efficiency_report.Report(run_id="D"), vorlage, keep=2)
            dateien = sorted(p.name for p in Path(ordner).iterdir())
        self.assertNotIn("efficiency-A.json", dateien)
        self.assertNotIn("efficiency-B.json", dateien)
        self.assertEqual(["efficiency-C.json", "efficiency-D.json", "efficiency-notes.txt"], dateien)

    def test_the_run_id_is_made_safe_for_a_file_name(self) -> None:
        self.assertEqual("/v/efficiency-RUN_2026_x.json",
                         agent_worker.report_path_for("/v/efficiency.json", "RUN/2026 x"))
        self.assertEqual("/v/efficiency-RUN.json",
                         agent_worker.report_path_for("/v/efficiency.json", ""))

    def test_keep_never_drops_below_one(self) -> None:
        # Eine Aufbewahrung von null hiesse: das eben geschriebene Artefakt
        # sofort wieder loeschen.
        with tempfile.TemporaryDirectory() as ordner:
            vorlage = str(Path(ordner) / "efficiency.json")
            agent_worker.write_report(self.report, vorlage, keep=0)
            self.assertEqual(["efficiency-TEST-1.json"], [p.name for p in Path(ordner).iterdir()])

    def test_an_unwritable_path_does_not_end_the_run(self) -> None:
        # Ein Lauf ist nicht gescheitert, weil sein Bericht nicht abzulegen war.
        agent_worker.write_report(self.report, "/kein/verzeichnis/report.json")

    def test_without_a_path_nothing_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as ordner:
            agent_worker.write_report(self.report, "")
            self.assertEqual([], list(Path(ordner).iterdir()))

    def test_an_unknown_decision_is_refused(self) -> None:
        # Der Bericht ist eine Nachweisdatei; eine erfundene Entscheidung
        # darin waere eine Behauptung ohne Herkunft.
        with self.assertRaises(ValueError):
            bericht().record(efficiency_report.Operation(
                message_id="MSG-1", sender_id="A", reply_recipient_id="A",
                task_class="BUS_REPLY", outcome="ANSWERED",
                duplicate_decision="AUSGEDACHT"))


if __name__ == "__main__":
    unittest.main()
