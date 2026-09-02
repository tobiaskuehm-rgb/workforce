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
                           "Abnahmetest 009"):
            with self.subTest(schluessel=schluessel):
                self.assertIn(schluessel, probe.ERWARTET)
        self.assertEqual(8, len(probe.ERWARTET))

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
