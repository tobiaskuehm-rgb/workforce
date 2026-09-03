"""`deploy_to_nas.sh` - gegen Attrappen gefahren, nicht nur gelesen.

Review finding G-080. Die erste Fassung des Deploy-Helfers versprach im Kopf
"It never deletes anything on the NAS" und liess nach dem Entpacken ein
`find . -name '._*' -delete` ueber den ganzen Zielordner laufen - ein
rekursives Loeschen, dessen Ziele nicht aus dem Manifest kamen und Laufzeit-
oder Secretpfade haetten treffen koennen, die absichtlich nicht deployt
werden. Dazu lief der Transfer als Pipeline `tar | ssh` unter `set -eu` ohne
`pipefail`: Der Status der Pipeline war der von `ssh`, nicht der von `tar`,
und "a failed transfer skips verification" war damit eine Behauptung.

Gerds Korrektur verlangt einen fokussierten Test fuer drei Dinge: kein
Remote-`delete`, ein Tar-Fehler verhindert `ssh`, eine erfolgreiche
Uebertragung ruft beide NAS-Pruefungen auf. Ein Textvergleich koennte das
erste pruefen; die anderen beiden sind **Verhalten**, und Verhalten wird
hier gemessen: Das Skript laeuft in einer Kopie neben einem Stub fuer
`deploy_manifest.sh`, mit Stubs fuer `tar` und `ssh` vorn im `PATH`, die
protokollieren, womit sie aufgerufen wurden. Nichts davon beruehrt die NAS.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
SKRIPT = NAS / "deploy_to_nas.sh"


class Attrappen:
    """Ein Ordner mit `tar`, `ssh` und einem `deploy_manifest.sh`-Stub."""

    def __init__(self, ordner: pathlib.Path) -> None:
        self.ordner = ordner
        self.protokoll = ordner / "aufrufe.log"
        self.bin = ordner / "bin"
        self.bin.mkdir()
        self.arbeit = ordner / "arbeit"
        self.arbeit.mkdir()
        shutil.copy(SKRIPT, self.arbeit / "deploy_to_nas.sh")

        # Der Manifest-Stub: schreibt eine Dateiliste dorthin, wo das Skript
        # sie erwartet, oder scheitert, wenn STUB_MANIFEST_FAIL gesetzt ist.
        self._stub(self.arbeit / "deploy_manifest.sh", """
            [ -n "${STUB_MANIFEST_FAIL:-}" ] && { echo "manifest: dirty tree"; exit 1; }
            printf 'a.txt\\nb/c.txt\\n' > "$DEPLOY_FILE_LIST_OUT"
            echo "manifest-stub ok"
        """)
        # tar: legt das Zielarchiv an oder scheitert auf Wunsch.
        self._stub(self.bin / "tar", """
            printf 'tar %s\\n' "$*" >> "$STUB_LOG"
            [ -n "${STUB_TAR_FAIL:-}" ] && { echo "tar: a.txt: Cannot stat" >&2; exit 1; }
            while [ $# -gt 0 ]; do
              case "$1" in czf) shift; : > "$1";; esac
              shift
            done
            exit 0
        """)
        # ssh: protokolliert den Remote-Befehl; scheitert auf Wunsch beim
        # ersten Aufruf (dem Transfer).
        self._stub(self.bin / "ssh", """
            printf 'ssh %s\\n' "$*" >> "$STUB_LOG"
            if [ -n "${STUB_SSH_FAIL_FIRST:-}" ] && [ "$(grep -c '^ssh ' "$STUB_LOG")" = "1" ]; then
              echo "ssh: connect to host: Connection refused" >&2; exit 255
            fi
            cat > /dev/null
            exit 0
        """)

    @staticmethod
    def _stub(pfad: pathlib.Path, rumpf: str) -> None:
        pfad.write_text("#!/bin/sh\n" + "\n".join(z.strip() for z in rumpf.strip().splitlines()) + "\n",
                        encoding="utf-8")
        pfad.chmod(0o755)

    def lauf(self, **umgebung: str) -> tuple[int, str]:
        env = dict(os.environ)
        env.update({"PATH": f"{self.bin}{os.pathsep}{env.get('PATH', '')}",
                    "STUB_LOG": str(self.protokoll)})
        env.update(umgebung)
        ergebnis = subprocess.run(["sh", str(self.arbeit / "deploy_to_nas.sh")],
                                  capture_output=True, text=True, env=env)
        return ergebnis.returncode, ergebnis.stdout + ergebnis.stderr

    def aufrufe(self, programm: str) -> list[str]:
        if not self.protokoll.exists():
            return []
        return [z for z in self.protokoll.read_text(encoding="utf-8").splitlines()
                if z.startswith(programm + " ")]


class DeployScriptBehaviourTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.att = Attrappen(pathlib.Path(self.tmp.name))

    def test_a_successful_run_transfers_then_verifies_with_both_checks(self) -> None:
        code, ausgabe = self.att.lauf()
        self.assertEqual(0, code, ausgabe)
        ssh = self.att.aufrufe("ssh")
        self.assertEqual(2, len(ssh), ssh)
        self.assertIn("tar xzf -", ssh[0])
        self.assertIn("verify_manifest.sh", ssh[1])
        self.assertIn("check_unmanaged.sh", ssh[1])
        self.assertIn("dirty=no", ssh[1])

    def test_no_remote_command_deletes(self) -> None:
        # Der Befund selbst: kein `-delete`, kein `rm` auf der NAS.
        self.att.lauf()
        for aufruf in self.att.aufrufe("ssh"):
            with self.subTest(aufruf=aufruf):
                self.assertNotIn("-delete", aufruf)
                self.assertNotRegex(aufruf, r"\brm\b")
                self.assertNotIn("find ", aufruf)

    def test_a_tar_failure_prevents_any_ssh(self) -> None:
        code, ausgabe = self.att.lauf(STUB_TAR_FAIL="1")
        self.assertNotEqual(0, code)
        self.assertEqual([], self.att.aufrufe("ssh"), ausgabe)

    def test_a_failed_transfer_skips_the_verification(self) -> None:
        code, ausgabe = self.att.lauf(STUB_SSH_FAIL_FIRST="1")
        self.assertNotEqual(0, code)
        ssh = self.att.aufrufe("ssh")
        self.assertEqual(1, len(ssh), ssh)
        self.assertNotIn("verify_manifest.sh", ssh[0])

    def test_a_dirty_tree_prevents_the_archive_and_the_transfer(self) -> None:
        code, ausgabe = self.att.lauf(STUB_MANIFEST_FAIL="1")
        self.assertNotEqual(0, code)
        self.assertEqual([], self.att.aufrufe("tar"), ausgabe)
        self.assertEqual([], self.att.aufrufe("ssh"), ausgabe)

    def test_the_archive_is_built_before_ssh_starts(self) -> None:
        # Kein `tar | ssh`: tar schreibt in eine Datei, ssh liest sie. Im
        # Protokoll steht tar deshalb vor dem ersten ssh, mit einem Zielpfad
        # statt "-".
        self.att.lauf()
        zeilen = self.att.protokoll.read_text(encoding="utf-8").splitlines()
        self.assertTrue(zeilen[0].startswith("tar czf "), zeilen)
        self.assertNotIn("tar czf - ", zeilen[0])
        self.assertTrue(zeilen[1].startswith("ssh "), zeilen)


class DeployScriptTextTest(unittest.TestCase):
    """Zwei Zusicherungen, die man auch dem Text ansieht - als zweite Linie."""

    def setUp(self) -> None:
        self.text = SKRIPT.read_text(encoding="utf-8")
        self.aktiv = "\n".join(z for z in self.text.splitlines() if not z.lstrip().startswith("#"))

    def test_no_pipeline_into_ssh(self) -> None:
        self.assertNotIn("| ssh", self.aktiv)

    def test_no_delete_in_the_executed_lines(self) -> None:
        self.assertNotIn("-delete", self.aktiv)

    def test_the_stub_run_would_notice_a_delete(self) -> None:
        # Gegenprobe: dieselbe Attrappe mit der alten Zeile faellt durch.
        with tempfile.TemporaryDirectory() as tmp:
            att = Attrappen(pathlib.Path(tmp))
            skript = att.arbeit / "deploy_to_nas.sh"
            alt = skript.read_text(encoding="utf-8").replace(
                "tar xzf -\"", "tar xzf - && find . -name '._*' -delete\"", 1)
            self.assertNotEqual(skript.read_text(encoding="utf-8"), alt)
            skript.write_text(alt, encoding="utf-8")
            att.lauf()
            self.assertTrue(any("-delete" in a for a in att.aufrufe("ssh")))


if __name__ == "__main__":
    unittest.main()
