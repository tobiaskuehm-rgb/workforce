"""Weicht eine Produktionsdatei vom benannten Commit ab, ohne dass es dasteht?

`production_state.txt` nennt den Quellstand, den die NAS laeuft, und listet die
Dateien, die ihn ausmachen. `verify_production_state.sh` haelt die Dateien auf
der NAS dagegen - aber nur, wenn jemand es von Hand aufruft, und `nas_status.sh`
ruft es nicht auf.

Genau daran ist am 2026-09-02 etwas vorbeigelaufen (Vertretungsreview,
`SV-2026-09-03-05`): Commit `ab0f719` ergaenzte den gegateten Block
`APPLY_MIGRATION_009_FUNCTION_OWNER` in `compose.yaml`, der Deploy brachte die
Datei auf die NAS, und `PRODUCTION_COMMIT` blieb auf `672e0a7` stehen. Die
Pruefung meldete ab da `FAIL` - aus einem harmlosen Grund, aber still, und eine
spaetere echte Abweichung haette sich hinter derselben roten Zeile versteckt.

Dieser Test braucht **keine NAS**. Er vergleicht jede `FILE=`-Zeile zwischen
`PRODUCTION_COMMIT` und `HEAD` im Repo und haette am Tag der Aenderung
angeschlagen statt Wochen spaeter.

**Warum eine Ausnahmeliste und kein hartes Rot:** Zwischen einer Aenderung im
Repo und ihrem Deploy liegt oft Zeit, manchmal ein Freigabefenster. Ein Test,
der in dieser Zeit dauerhaft rot ist, wird abgeschaltet statt gelesen (`G-069`).
Die Liste haelt die Abweichung sichtbar und macht ihr Schliessen zu einer
bewussten Handlung - dieselbe Bauform wie `KNOWN_GAPS` in
`test_migration_acceptance.py` (Regel 20). Sie schlaegt in **beide** Richtungen
an: eine neue Abweichung ebenso wie eine, die still verschwunden ist.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
STATE = NAS / "production_state.txt"

# Datei -> Begruendung. Leer heisst: der Quellstand im Repo ist genau der, den
# `PRODUCTION_COMMIT` nennt. Ein Eintrag gehoert hierher, sobald eine
# Produktionsdatei im Repo geaendert, aber noch nicht deployt ist.
ABWEICHUNGEN: dict[str, str] = {}


def produktionsstand() -> tuple[str, list[str]]:
    text = STATE.read_text(encoding="utf-8")
    commit = re.search(r"^PRODUCTION_COMMIT=(\S+)", text, re.MULTILINE)
    dateien = re.findall(r"^FILE=(\S+)", text, re.MULTILINE)
    assert commit, "production_state.txt nennt keinen PRODUCTION_COMMIT"
    return commit.group(1), dateien


def abweichende_dateien(commit: str, dateien: list[str]) -> list[str]:
    """Welche der genannten Dateien unterscheiden sich zwischen commit und HEAD?

    Ueber `git diff --name-only`, damit der Vergleich byteweise ist und nicht
    an einer Heuristik haengt.
    """
    pfade = [f"nas-startup/{datei}" for datei in dateien]
    ergebnis = subprocess.run(
        ["git", "diff", "--name-only", f"{commit}..HEAD", "--", *pfade],
        cwd=ROOT, capture_output=True, text=True, check=True)
    praefix = "nas-startup/"
    return sorted(zeile[len(praefix):] if zeile.startswith(praefix) else zeile
                  for zeile in ergebnis.stdout.split("\n") if zeile.strip())


class ProductionStateMatchesHeadTest(unittest.TestCase):
    def test_no_undocumented_drift(self) -> None:
        commit, dateien = produktionsstand()
        self.assertEqual(sorted(ABWEICHUNGEN), abweichende_dateien(commit, dateien),
                         "eine Produktionsdatei weicht vom benannten Commit ab - "
                         "entweder deployen und PRODUCTION_COMMIT ziehen, oder "
                         "die Abweichung hier mit Begruendung eintragen")

    def test_every_exception_carries_a_reason(self) -> None:
        # Ein Eintrag ohne Begruendung ist eine stille Ausnahme, und genau das
        # soll diese Liste verhindern.
        for datei, grund in ABWEICHUNGEN.items():
            with self.subTest(datei=datei):
                self.assertGreater(len(grund.strip()), 30, datei)

    def test_the_named_commit_exists(self) -> None:
        commit, _ = produktionsstand()
        vorhanden = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, vorhanden.returncode,
                         f"PRODUCTION_COMMIT={commit} gibt es in diesem Repo nicht")

    def test_the_file_list_is_not_empty(self) -> None:
        # Sonst waere die Aussage oben gruen ueber einer leeren Menge.
        _, dateien = produktionsstand()
        self.assertGreaterEqual(len(dateien), 9)
        self.assertIn("compose.yaml", dateien)
        self.assertIn("workforce-api/app.py", dateien)


class DriftIsActuallyDetectedTest(unittest.TestCase):
    """Die Gegenprobe, und sie braucht keine erfundenen Daten.

    Der Fall aus `SV-2026-09-03-05` liegt in der echten Historie: Gegen
    `672e0a7` - den Commit, auf dem die Datei bis zum 2026-09-03 stand - muss
    genau `compose.yaml` als abweichend herausfallen. Faende der Vergleich dort
    nichts, waere die Zusicherung oben wertlos.
    """

    def test_the_historical_drift_is_found(self) -> None:
        _, dateien = produktionsstand()
        self.assertEqual(["compose.yaml"], abweichende_dateien("672e0a7", dateien))

    def test_the_comparison_is_scoped_to_the_named_files(self) -> None:
        """Nur die genannten Dateien, nicht der ganze Commitbereich.

        Zwischen `672e0a7` und `HEAD` liegen Dutzende geaenderter Dateien.
        Wird die Liste auf `app.py` eingegrenzt - das sich in diesem Bereich
        nicht geaendert hat -, muss der Vergleich leer bleiben. Sonst meldete
        er den Commitbereich statt der Dateien und die Aussage oben waere
        beliebig.
        """
        self.assertEqual([], abweichende_dateien("672e0a7", ["workforce-api/app.py"]))
        self.assertEqual(["compose.yaml"],
                         abweichende_dateien("672e0a7", ["compose.yaml"]))


if __name__ == "__main__":
    unittest.main()
