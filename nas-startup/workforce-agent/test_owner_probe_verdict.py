"""Das Urteil der Owner-Probe, lokal gegen seine Negativfaelle gefahren.

Review finding G-070. `g045_owner_probe.py` berechnete, ob der Audit-Trigger
unter `workforce_owner` gefeuert hat, druckte das Ergebnis - und liess es aus
der Erfolgsbedingung heraus. Ein nicht ausgeloester Audit-Trigger erschien
sichtbar als `NEIN` und die Probe meldete `RESULT: PASS`. Der zentrale
Nachweis der Datei konnte falschgruen ausgehen.

Die Probe ist nie gelaufen und laeuft nicht ohne Freigabe. Damit ist ihr
Urteil das einzige an ihr, was sich vorher pruefen laesst - und weil es die
Bewertung ist, an der `G-070` haengt, gehoert genau sie geprueft. Dieselbe
Trennung wie bei `bus_rules.py`: die Entscheidung in eine reine Funktion, die
Messung daneben.

Vier Faelle, und die ersten drei sind die, die vorher durchgegangen waeren.
"""

from __future__ import annotations

import ast
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROBE = ROOT / "nas-startup" / "g045_owner_probe.py"

_spec = importlib.util.spec_from_file_location("g045_owner_probe", PROBE)
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


def guter_lauf() -> list[tuple[str, str]]:
    """Ein Ergebnis, in dem jede Zusicherung erfuellt ist."""
    return [("Ausgangsstand", "6 Migrationen angewendet"),
            ("SECURITY DEFINER beim Superuser, vorher", "12"),
            ("bus_events vorher/nachher", "41 -> 42")] + \
           [(schluessel, soll) for schluessel, soll in probe.ERWARTET.items()]


class VerdictTest(unittest.TestCase):
    def test_a_complete_run_passes(self) -> None:
        gut, beanstandungen = probe.bewertung(guter_lauf())
        self.assertEqual([], beanstandungen)
        self.assertTrue(gut)

    def test_an_audit_trigger_that_did_not_fire_fails(self) -> None:
        """Genau der Fall aus `G-070`.

        Vorher stand hier `NEIN` in der Ausgabe und `PASS` in der letzten
        Zeile.
        """
        lauf = [(k, "0" if k == "Audit-Event mit Request-Id, Akteur, Typ und Operation" else v)
                for k, v in guter_lauf()]
        gut, beanstandungen = probe.bewertung(lauf)
        self.assertFalse(gut)
        self.assertIn("Audit-Event mit Request-Id, Akteur, Typ und Operation: '0' statt '1'",
                      beanstandungen)

    def test_a_failed_write_fails(self) -> None:
        lauf = [(k, "ERROR: permission denied for table bus_channels"
                 if k == "Schreibversuch als workforce_owner" else v)
                for k, v in guter_lauf()]
        self.assertFalse(probe.bewertung(lauf)[0])

    def test_a_foreign_event_does_not_count(self) -> None:
        """Der Zaehler waechst, aber nicht durch diesen Schreibvorgang.

        Der Zuwachs stimmt, die gebundene Abfrage findet nichts - das ist
        "irgendein Datensatz dieses Typs", und den lassen die Auditregeln
        dieses Projekts ausdruecklich nicht als Nachweis gelten.
        """
        lauf = [(k, "0" if k == "Audit-Event mit Request-Id, Akteur, Typ und Operation" else v)
                for k, v in guter_lauf()]
        self.assertEqual("1", dict(lauf)["Eventzuwachs"])
        self.assertFalse(probe.bewertung(lauf)[0])

    def test_a_missing_measurement_fails(self) -> None:
        """Ein Schritt, der gar nicht stattgefunden hat, ist kein Erfolg.

        Die erste Fassung las die Ergebnisse mit `dict(...).get(...)`; ein
        abgebrochener Lauf lieferte damit fuer die nicht erreichten Punkte
        einfach nichts.
        """
        for fehlend in probe.ERWARTET:
            with self.subTest(schluessel=fehlend):
                lauf = [(k, v) for k, v in guter_lauf() if k != fehlend]
                gut, beanstandungen = probe.bewertung(lauf)
                self.assertFalse(gut)
                self.assertIn(f"{fehlend}: nicht gemessen", beanstandungen)

    def test_an_abandoned_run_fails(self) -> None:
        # Der Abbruch nach einer fehlgeschlagenen Migration: die Probe raeumt
        # auf und druckt, was sie hat. Das darf nie PASS sein.
        self.assertFalse(probe.bewertung([("Migration 002_workforce_bus.sql",
                                           "FEHLER: syntax error")])[0])
        self.assertFalse(probe.bewertung([])[0])


class RunResultTest(unittest.TestCase):
    """`lauf_ergebnis()` - Exitcode und Ausgabe gemeinsam.

    Review finding G-076. Die erste Fassung wertete den Abnahmetest ueber
    `"ERROR" not in ausgabe` aus und kannte den Prozess-Exitcode gar nicht.
    Die vier Faelle unten sind genau die, die damit als bestandener SQL-Test
    durchgegangen waeren - drei davon enthalten das Wort `error` in einer
    Schreibweise, die die Grossbuchstabenpruefung nicht trifft, und der vierte
    enthaelt ueberhaupt nichts.
    """

    def test_a_clean_run_with_the_marker_is_ok(self) -> None:
        self.assertEqual("ok", probe.lauf_ergebnis(
            0, f"NOTICE:  {probe.ABNAHME_MARKER}\nROLLBACK", probe.ABNAHME_MARKER))

    def test_a_lowercase_psql_error_is_not_ok(self) -> None:
        code, ausgabe = 2, "psql: error: connection to server failed"
        self.assertNotIn("ERROR", ausgabe)          # die alte Pruefung sah nichts
        ergebnis = probe.lauf_ergebnis(code, ausgabe, probe.ABNAHME_MARKER)
        self.assertNotEqual("ok", ergebnis)
        self.assertIn("Exitcode 2", ergebnis)

    def test_a_docker_error_is_not_ok(self) -> None:
        code, ausgabe = 125, "Error response from daemon: No such container: g045probe"
        self.assertNotEqual("ok", probe.lauf_ergebnis(code, ausgabe, probe.ABNAHME_MARKER))

    def test_a_nonzero_exit_without_any_error_word_is_not_ok(self) -> None:
        # Exit 127 = command not found. Die Ausgabe nennt kein Fehlerwort.
        ergebnis = probe.lauf_ergebnis(127, "sh: psql: not found", probe.ABNAHME_MARKER)
        self.assertNotEqual("ok", ergebnis)
        self.assertIn("Exitcode 127", ergebnis)

    def test_an_empty_output_is_not_ok(self) -> None:
        # Der gefaehrlichste Fall: nichts zu lesen liest sich wie nichts zu
        # beanstanden. Beide Richtungen - mit und ohne Exitcode.
        self.assertIn("Exitcode 1", probe.lauf_ergebnis(1, "", probe.ABNAHME_MARKER))
        stiller_erfolg = probe.lauf_ergebnis(0, "", probe.ABNAHME_MARKER)
        self.assertNotEqual("ok", stiller_erfolg)
        self.assertIn("Schlussmarker fehlt", stiller_erfolg)
        self.assertIn("(keine Ausgabe)", stiller_erfolg)

    def test_exit_zero_without_the_marker_is_not_ok(self) -> None:
        """Der Fall, den der Exitcode allein nicht faengt.

        `psql -f` auf eine Datei, die nicht angekommen ist, oder ein Test, der
        vor seiner letzten Aussage endet: Der Prozess kann sauber enden und
        trotzdem nichts belegt haben.
        """
        ergebnis = probe.lauf_ergebnis(0, "BEGIN\nROLLBACK", probe.ABNAHME_MARKER)
        self.assertNotEqual("ok", ergebnis)
        self.assertIn("Schlussmarker fehlt", ergebnis)

    def test_without_a_marker_the_exit_code_alone_decides(self) -> None:
        # So werden die Migrationsaufrufe ausgewertet: dieselbe Funktion,
        # nur ohne Schlussmarker.
        self.assertEqual("ok", probe.lauf_ergebnis(0, "COMMIT"))
        self.assertNotEqual("ok", probe.lauf_ergebnis(3, "COMMIT"))

    def test_the_acceptance_test_really_writes_that_marker(self) -> None:
        # Sonst waere der Waechter oben gruen ueber einem Marker, den niemand
        # schreibt - und der Abnahmetest dauerhaft rot.
        abnahme = (ROOT / "nas-startup" / "postgres-tests"
                   / "009_bus_function_owner_acceptance.sql").read_text(encoding="utf-8")
        self.assertIn(probe.ABNAHME_MARKER, abnahme)


class TriggerDenialTest(unittest.TestCase):
    """Der Negativtest muss die **erwartete** Ablehnung erkennen, nicht irgendeine.

    `CLAUDE.md` haelt das seit `G-014` fest: "Ein Fehlschlag ist erst dann die
    erwartete Ablehnung, wenn Statuscode *und* Kennung stimmen." Die erste
    Fassung dieser Probe wertete `Exitcode != 0` als "Zugriff verweigert" - ein
    weggeraeumter Container, eine abgerissene Verbindung oder ein Tippfehler im
    Tabellennamen haetten den zentralen Sicherheitsnachweis erbracht.
    """

    def test_the_expected_denial_is_recognised(self) -> None:
        ergebnis = probe.trigger_urteil(0, f"NOTICE:  {probe.TRIGGER_ABGELEHNT}")
        self.assertEqual(probe.ERWARTET["Trigger abschaltbar"], ergebnis)

    def test_a_successful_disable_is_not_a_pass(self) -> None:
        ergebnis = probe.trigger_urteil(0, f"NOTICE:  {probe.TRIGGER_ERLAUBT}")
        self.assertNotEqual(probe.ERWARTET["Trigger abschaltbar"], ergebnis)
        self.assertIn("verfehlt ihren Zweck", ergebnis)

    def test_a_foreign_sqlstate_is_not_a_pass(self) -> None:
        """Abgelehnt, aber aus einem anderen Grund - etwa weil die Tabelle fehlt.

        Das ist der Fall, den eine reine "wurde abgelehnt"-Pruefung nicht von
        der gemeinten Ablehnung unterscheidet.
        """
        ergebnis = probe.trigger_urteil(0, "NOTICE:  PROBE_TRIGGER_DENIED_42P01")
        self.assertNotEqual(probe.ERWARTET["Trigger abschaltbar"], ergebnis)
        self.assertIn("42P01", ergebnis)

    def test_a_process_failure_is_not_a_denial(self) -> None:
        # Genau der Befund: jeder dieser Faelle galt vorher als bestanden.
        for code, ausgabe in ((125, "Error response from daemon: No such container"),
                              (2, "psql: error: connection to server failed"),
                              (127, "sh: psql: not found"),
                              (1, "")):
            with self.subTest(code=code):
                ergebnis = probe.trigger_urteil(code, ausgabe)
                self.assertNotEqual(probe.ERWARTET["Trigger abschaltbar"], ergebnis)
                self.assertTrue(ergebnis.startswith("unbestimmt"), ergebnis)

    def test_exit_zero_without_any_marker_is_not_a_denial(self) -> None:
        ergebnis = probe.trigger_urteil(0, "SET")
        self.assertTrue(ergebnis.startswith("unbestimmt"), ergebnis)

    def test_the_probe_sends_a_statement_that_can_report_its_sqlstate(self) -> None:
        # Ohne den EXCEPTION-Block gaebe es keinen Marker, und die Auswertung
        # oben waere gruen ueber einer Ausgabe, die es nie gibt.
        quelle = PROBE.read_text(encoding="utf-8")
        for teil in ("EXCEPTION WHEN OTHERS THEN",
                     "RAISE NOTICE 'PROBE_TRIGGER_DENIED_%', SQLSTATE",
                     "DISABLE TRIGGER USER"):
            with self.subTest(teil=teil):
                self.assertIn(teil, quelle)


class ProbeUsesExitCodesTest(unittest.TestCase):
    """Statisch: die Textpruefung ist wirklich weg, nicht nur ueberschrieben."""

    def _baum(self) -> ast.AST:
        return ast.parse(PROBE.read_text(encoding="utf-8"))

    def test_no_call_passes_a_check_flag_any_more(self) -> None:
        # `ssh(..., check=False)` war die Stelle, an der der Exitcode verloren
        # ging. Es gibt den Parameter nicht mehr.
        for knoten in ast.walk(self._baum()):
            if isinstance(knoten, ast.Call):
                for schluesselwort in knoten.keywords:
                    self.assertNotEqual("check", schluesselwort.arg)

    def test_the_migration_and_acceptance_calls_go_through_lauf_ergebnis(self) -> None:
        aufrufe = [k for k in ast.walk(self._baum())
                   if isinstance(k, ast.Call) and isinstance(k.func, ast.Name)
                   and k.func.id == "lauf_ergebnis"]
        self.assertGreaterEqual(len(aufrufe), 3)


class VerdictCoversEveryAssuranceTest(unittest.TestCase):
    """Die Erwartungsliste selbst ist die Zusicherung - also wird sie gebunden.

    Ein Schluessel, der still aus `ERWARTET` verschwindet, macht die Probe
    wieder schwaecher, ohne dass ein Test rot wird.
    """

    def test_every_assurance_is_named(self) -> None:
        for schluessel in ("009 angewendet",
                           "SECURITY DEFINER beim Superuser, nachher",
                           "Relationen im Besitz von workforce_owner",
                           "Schreibversuch als workforce_owner",
                           "Eventzuwachs",
                           "Audit-Event mit Request-Id, Akteur, Typ und Operation",
                           "Trigger abschaltbar",
                           "public-USAGE ueber PUBLIC (Voreinstellung)",
                           "direkte Schema-Grants ausserhalb workforce",
                           "Abnahmetest 009"):
            with self.subTest(schluessel=schluessel):
                self.assertIn(schluessel, probe.ERWARTET)
        self.assertEqual(10, len(probe.ERWARTET))

    def test_the_probe_binds_the_audit_event_to_the_run(self) -> None:
        quelle = PROBE.read_text(encoding="utf-8")
        for teil in ("request_id = '{REQUEST_ID}'", "actor_id = '{AKTEUR}'",
                     "record_type = 'CHANNEL'", "event_type = 'UPDATE'"):
            with self.subTest(teil=teil):
                self.assertIn(teil, quelle)

    def test_the_probe_no_longer_resets_the_role_in_a_scalar_query(self) -> None:
        """Die Statuszeile eines `RESET ROLE` macht den Zaehlwert unbrauchbar.

        Die alte Auswertung las das als "Trigger nicht gefeuert" und meldete
        trotzdem PASS. Geprueft wird das an den **Zeichenketten, die in einen
        Aufruf gehen**, nicht am Dateitext: Ein Textvergleich waere ueber der
        Erklaerung oben rot geworden, die das Wort nennt und das Gegenteil
        meint. Genau die Falle aus `G-054`.
        """
        baum = ast.parse(PROBE.read_text(encoding="utf-8"))
        argumente = [knoten.value
                     for aufruf in ast.walk(baum) if isinstance(aufruf, ast.Call)
                     for knoten in ast.walk(aufruf)
                     if isinstance(knoten, ast.Constant) and isinstance(knoten.value, str)]
        self.assertTrue(argumente, "keine Aufrufargumente gefunden - Scan kaputt")
        self.assertEqual([], [a for a in argumente if "RESET ROLE" in a])
        # Gegenprobe: derselbe Scan findet das SET ROLE, das dort stehen muss.
        self.assertTrue(any("SET ROLE workforce_owner" in a for a in argumente))


if __name__ == "__main__":
    unittest.main()
