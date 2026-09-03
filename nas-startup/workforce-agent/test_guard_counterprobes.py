"""Jeder Scanner braucht eine Gegenprobe - maschinell statt aus Disziplin.

`CLAUDE.md`, Testkonventionen: „Jede Kontrolle braucht einen Test, der sie
absichtlich schwaecht und verlangt, dass es auffaellt. Ein Test, der nur den
Gutfall sieht, unterscheidet eine wirksame Kontrolle nicht von einer
stillgelegten." Die Regel steht dort seit Langem und wurde bisher von
Disziplin gehalten. Dieselbe Ueberlegung wie bei `test_mirrors.py`: Disziplin
ist die schwaechste Absicherung, also wird sie hier nachgemessen.

Anlass ist Regel 47 vom 2026-09-03: Ein Waechter, dessen Bedingung sich selbst
ausschliesst, kann nie anschlagen - und sieht dabei aus wie eine bestandene
Kontrolle. Die Prueffrage lautet nicht „ist die Bedingung richtig", sondern
**„gibt es einen Zustand, in dem dieser Waechter rot wird"**. Genau das ist
eine Gegenprobe.

Was hier als Gegenprobe zaehlt: irgendeine Zusicherung ueber dem Scanner, die
**nicht** die Form `assertEqual([], scanner(...))` hat - also ein `assertIn`,
ein `assertNotEqual`, ein `assertEqual` mit einer erwarteten Fundliste. Es
zaehlt nicht, wie gut sie ist; das entscheidet der Review. Es zaehlt, dass es
sie gibt.

**Eine Falle beim Bauen dieser Datei, und sie gehoert zur Sache:** Meine erste
Fassung suchte Zusicherung und Aufruf in derselben Zeile. Fast jede echte
Gegenprobe in diesem Bestand verteilt sich aber auf zwei Zeilen - der Scan
meldete deshalb eine Luecke, die es nicht gibt. Dieselbe Zeilengrenze, an der
`NoHardcodedCountsTest` in `test_document_consistency.py` schon einmal
vorbeigelesen hat. `test_a_counterprobe_across_two_lines_counts` haelt das
fest.
"""

from __future__ import annotations

import pathlib
import re
import unittest

PAKET = pathlib.Path(__file__).resolve().parent

# Die Namenskonvention dieses Bestands. `offenders` ist die dominante Form;
# die beiden anderen stehen fuer kuenftige Waechter bereit, damit ein neuer
# Name nicht stillschweigend aus der Pruefung faellt.
SCANNER_NAME = re.compile(r"^def ((?:\w+_)?(?:offenders|violations|gaps))\(", re.MULTILINE)

# Zusicherung und Aufruf duerfen auf verschiedenen Zeilen stehen - deshalb
# DOTALL und ein Fenster statt `[^\n]*`. Das Fenster begrenzt, damit nicht ein
# `assertEqual` zwanzig Zeilen weiter oben faelschlich als Klammer gilt.
def zusicherungen(test_quelle: str, name: str) -> list[str]:
    """Die Zusicherungsarten, mit denen `name` in einer Testquelle vorkommt."""
    gefunden = []
    for treffer in re.finditer(
            rf"assert(\w+)\((.{{0,200}}?)\b{re.escape(name)}\(", test_quelle, re.DOTALL):
        art, dazwischen = treffer.group(1), treffer.group(2)
        erwartet_leer = art == "Equal" and re.match(r"\s*\[\]\s*,", dazwischen)
        gefunden.append("leer" if erwartet_leer else "gegenprobe")
    return gefunden


def scanner_im_paket() -> dict[str, str]:
    """Scannername -> Datei, in der er definiert ist."""
    gefunden: dict[str, str] = {}
    for pfad in sorted(PAKET.glob("*.py")):
        for treffer in SCANNER_NAME.finditer(pfad.read_text(encoding="utf-8")):
            gefunden.setdefault(treffer.group(1), pfad.name)
    return gefunden


def testquellen() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(PAKET.glob("test_*.py"))}


def ohne_gegenprobe(scanner: dict[str, str], tests: dict[str, str]) -> list[str]:
    """Scanner, die nur mit `assertEqual([], ...)` geprueft werden."""
    fehlend = []
    for name in sorted(scanner):
        arten = [art for quelle in tests.values() for art in zusicherungen(quelle, name)]
        if arten and "gegenprobe" not in arten:
            fehlend.append(f"{name} ({scanner[name]})")
    return fehlend


class EveryGuardHasACounterprobeTest(unittest.TestCase):
    def test_no_scanner_is_only_checked_for_emptiness(self) -> None:
        self.assertEqual([], ohne_gegenprobe(scanner_im_paket(), testquellen()),
                         "ein Scanner ohne Gegenprobe kann stillgelegt sein, "
                         "ohne dass ein Test rot wird")

    def test_the_discovery_finds_the_known_guards(self) -> None:
        """Ohne das waere die Aussage oben gruen ueber einer leeren Menge.

        Genau der Fehler, den `compose_scan.py` als Regel hinterlassen hat:
        Ein Waechter, der nicht hinsieht, meldet PASS.
        """
        scanner = scanner_im_paket()
        self.assertGreaterEqual(len(scanner), 15)
        for erwartet in ("helper_script_offenders", "privileged_command_offenders",
                         "token_cleanup_offenders", "service_offenders"):
            with self.subTest(scanner=erwartet):
                self.assertIn(erwartet, scanner)


class DetectionIsRealTest(unittest.TestCase):
    """Die Gegenprobe dieser Datei - sie prueft ihren eigenen Pruefer."""

    QUELLE = "def beispiel_offenders(text):\n    return []\n"

    def test_a_scanner_with_only_an_empty_assertion_is_reported(self) -> None:
        test = ("class T(unittest.TestCase):\n"
                "    def test_x(self):\n"
                "        self.assertEqual([], beispiel_offenders(self.text))\n")
        self.assertEqual(["beispiel_offenders (beispiel.py)"],
                         ohne_gegenprobe({"beispiel_offenders": "beispiel.py"},
                                         {"test_beispiel.py": test}))

    def test_a_counterprobe_across_two_lines_counts(self) -> None:
        """Der Fall, an dem meine erste Fassung vorbeigelesen hat.

        Fast jede echte Gegenprobe in diesem Bestand steht auf zwei Zeilen.
        Ein Muster ohne Zeilenuebertritt meldet deshalb Luecken, die es nicht
        gibt - und wer dem glaubt, schreibt Gegenproben, die schon da sind.
        """
        test = ("class T(unittest.TestCase):\n"
                "    def test_x(self):\n"
                "        self.assertEqual([], beispiel_offenders(self.text))\n"
                "    def test_y(self):\n"
                "        self.assertIn('etwas',\n"
                "                      beispiel_offenders(kaputt))\n")
        self.assertEqual([], ohne_gegenprobe({"beispiel_offenders": "beispiel.py"},
                                             {"test_beispiel.py": test}))

    def test_an_expected_finding_list_counts_as_a_counterprobe(self) -> None:
        # `assertEqual(["x: fehlt"], f(...))` ist eine Gegenprobe, auch wenn
        # sie mit assertEqual geschrieben ist - unterschieden wird an der
        # erwarteten Liste, nicht an der Zusicherungsart.
        test = ("        self.assertEqual(['x'], beispiel_offenders(kaputt))\n")
        self.assertEqual([], ohne_gegenprobe({"beispiel_offenders": "beispiel.py"},
                                             {"test_beispiel.py": test}))

    def test_a_scanner_nobody_asserts_on_is_not_reported_here(self) -> None:
        """Bewusste Grenze: Diese Datei prueft die Form der Zusicherungen.

        Ein Scanner ganz ohne Test ist ein anderer Mangel und gehoert nicht in
        dieselbe Meldung - sonst vermischen sich zwei Befunde in einer Zeile.
        Heute gibt es keinen solchen Scanner; faende sich einer, waere das ein
        eigener Befund.
        """
        self.assertEqual([], ohne_gegenprobe({"beispiel_offenders": "beispiel.py"},
                                             {"test_beispiel.py": "nichts\n"}))
        alle = scanner_im_paket()
        tests = testquellen()
        ohne_jede = [n for n in alle
                     if not any(zusicherungen(q, n) for q in tests.values())]
        self.assertEqual([], ohne_jede, "Scanner ohne jede Zusicherung")


if __name__ == "__main__":
    unittest.main()
