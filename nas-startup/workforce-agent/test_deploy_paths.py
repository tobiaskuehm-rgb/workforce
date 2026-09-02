"""What gets deployed was never written down anywhere that survives.

Review finding G-052. The path list existed as an argument line in a terminal
and - as a side effect - in the header of the generated DEPLOY_MANIFEST.txt.
That file is gitignored, correctly, because it is a build artefact. So a fresh
clone of this repository does not know what to deploy, and the only way to
find out was to read a file that is not in the repository.

Same class as the nightly backup that lived as a text field in DSM's task
database (G-047): what fills production belongs in the repo. And it had teeth
already - G-043 was, in part, a helper script missing from the target
manifest, which is not reported as missing. It simply stops being covered.

The list is `deploy_paths.txt` now. These tests hold the two properties that
make it worth having: it names things that exist, and it covers every script
the status report actually runs. The second one is the reason a path list
matters at all - a gate script that never reaches the NAS turns nas_status.sh
into a failure on a healthy system.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
LISTE = NAS / "deploy_paths.txt"
STATUS = NAS / "nas_status.sh"


def pfade() -> list[str]:
    out = []
    for zeile in LISTE.read_text(encoding="utf-8").splitlines():
        zeile = zeile.split("#", 1)[0].strip()
        if zeile:
            out.append(zeile)
    return out


def gate_skripte() -> list[str]:
    """Every script nas_status.sh runs through run_gate."""
    text = STATUS.read_text(encoding="utf-8")
    return re.findall(r'run_gate\s+"[^"]+"\s+(\S+\.sh)', text)


class TheListIsRealTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pfade = pfade()

    def test_it_names_something(self) -> None:
        self.assertGreater(len(self.pfade), 10)

    def test_every_path_exists(self) -> None:
        fehlend = [p for p in self.pfade if not (NAS / p).exists()]
        self.assertEqual([], fehlend, "Pfad in der Liste, aber nicht im Baum")

    def test_no_path_is_listed_twice(self) -> None:
        doppelt = sorted({p for p in self.pfade if self.pfade.count(p) > 1})
        self.assertEqual([], doppelt)

    def test_no_path_escapes_the_folder(self) -> None:
        # Ein `..` im Deploy-Pfad waere ein Archiv ueber halb den Mac.
        for p in self.pfade:
            with self.subTest(pfad=p):
                self.assertNotIn("..", p)
                self.assertFalse(p.startswith("/"))

    def test_every_path_is_versioned(self) -> None:
        # Ein Pfad, den git nicht kennt, kommt nicht ins Manifest - und
        # deploy_manifest.sh blockiert dann, statt still weniger auszurollen.
        ergebnis = subprocess.run(["git", "ls-files", "--", *self.pfade],
                                  cwd=NAS, capture_output=True, text=True)
        self.assertEqual(0, ergebnis.returncode, ergebnis.stderr)
        bekannt = {zeile.split("/", 1)[0] for zeile in ergebnis.stdout.splitlines()}
        unbekannt = sorted(p for p in self.pfade if p.split("/", 1)[0] not in bekannt)
        self.assertEqual([], unbekannt, "git kennt diese Pfade nicht")


class TheListCoversWhatRunsTest(unittest.TestCase):
    """The property the list exists for."""

    def setUp(self) -> None:
        self.pfade = set(pfade())
        self.gates = gate_skripte()

    def test_nas_status_has_gates_at_all(self) -> None:
        # Ohne diese Zusicherung waere der Test unten gruen ueber einer
        # leeren Liste - genau der Fall, den ein Glob-Waechter braucht.
        self.assertGreaterEqual(len(self.gates), 4, self.gates)

    def test_every_gate_script_is_deployed(self) -> None:
        fehlend = sorted(s for s in self.gates if s not in self.pfade)
        self.assertEqual([], fehlend,
                         "Gate-Skript nicht im Deploy - nas_status.sh liefe ins Leere")

    def test_the_status_script_itself_is_deployed(self) -> None:
        self.assertIn("nas_status.sh", self.pfade)

    def test_a_gate_script_dropped_from_the_list_would_be_caught(self) -> None:
        ohne = self.pfade - {"check_backup_integrity.sh"}
        fehlend = [s for s in self.gates if s not in ohne]
        self.assertEqual(["check_backup_integrity.sh"], fehlend)


class TheScriptUsesTheListTest(unittest.TestCase):
    def setUp(self) -> None:
        self.script = (NAS / "deploy_manifest.sh").read_text(encoding="utf-8")

    def test_it_falls_back_to_the_file(self) -> None:
        self.assertIn("deploy_paths.txt", self.script)
        self.assertIn('if [ "$#" -eq 0 ]; then', self.script)

    def test_arguments_still_win(self) -> None:
        # Ein Zielmanifest fuer ein Fenster braucht eine andere Pfadmenge als
        # der laufende Stand; das war der Grund fuer MANIFEST_OUT (Phase 4).
        self.assertIn("MANIFEST_OUT", self.script)
        self.assertIn('files="$(git ls-files -- "$@")"', self.script)

    def test_comments_and_blank_lines_are_stripped(self) -> None:
        # Die Extraktion in der Shell, gegen eine Attrappe gefahren statt
        # nachgedacht: `#` am Zeilenende zaehlt auch.
        probe = "# Kopf\n\nalpha\nbeta   # dahinter\n\n"
        ergebnis = subprocess.run(
            ["sh", "-c", "sed -e 's/#.*//' -e '/^[[:space:]]*$/d' /dev/stdin"],
            input=probe, capture_output=True, text=True)
        self.assertEqual(0, ergebnis.returncode, ergebnis.stderr)
        self.assertEqual(["alpha", "beta"], ergebnis.stdout.split())


if __name__ == "__main__":
    unittest.main()
