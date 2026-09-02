"""The script that stops the backup folder from eroding overnight.

Review finding G-048: the nightly DSM task writes `644 root:root`. The files
from 2026-09-01 had been tightened by hand while closing G-022, but the job was
never changed, so the very next night produced a world-readable database dump
and a config archive containing startup.env.

check_backup_permissions.sh *found* it. Finding it every morning is not the
same as preventing it, so harden_backup_permissions.sh sets the state and is
meant to be called by the same scheduled task that writes the files.

These tests are properties of the script's text, not of a run: the run needs
root and a NAS, and was done separately in a throwaway container (evidence
2026-09-02). What is checked here is what a later reader could quietly break -
the refusal without root, the numeric group, and the absence of anything that
deletes.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
SCRIPT = NAS / "harden_backup_permissions.sh"


def code_only(body: str) -> str:
    """Drop comment lines.

    The first version of the delete check flagged this script's own help text,
    which shows a `docker run --rm` fallback. Same lesson as the runbook
    guard: prose about a command is not a command.
    """
    return "\n".join(line for line in body.split("\n")
                     if not line.lstrip().startswith("#"))


class ScriptShapeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SCRIPT.read_text(encoding="utf-8")
        self.code = code_only(self.text)

    def test_it_refuses_without_root(self) -> None:
        self.assertIn("id -u", self.text)
        # And really exits rather than warning and carrying on.
        self.assertRegex(self.text, r"id -u.*\n(?:.*\n){0,6}?\s*exit 1")

    def test_the_refusal_actually_returns_nonzero(self) -> None:
        # Measured, not read: the first version of this check was piped into
        # `head`, which reported the exit code of head. Same trap as
        # nas_status.sh, one directory over.
        result = subprocess.run(["sh", str(SCRIPT)], cwd=NAS,
                                env={"BACKUP_DIR": "/tmp", "PATH": "/usr/bin:/bin"},
                                capture_output=True, text=True)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("nicht als root", result.stdout + result.stderr)

    def test_the_group_is_a_number(self) -> None:
        # G-044: inside a container the name `administrators` does not exist.
        self.assertIn('group="${BACKUP_GROUP:-101}"', self.text)
        self.assertNotIn("chown 0:administrators", self.text)

    # A command, not a substring: "rm -" also occurs inside `-perm -o=r`, which
    # cost this check its first two runs.
    LOESCHT = re.compile(r"(?:^|[;&|]\s*|-exec\s+|\$\(\s*)(rm|unlink|shred|truncate)\b"
                         r"|docker\s+\w*\s*prune", re.MULTILINE)

    def test_it_never_deletes(self) -> None:
        # Guardrail 2, and a backup folder is the last place for an exception.
        self.assertIsNone(self.LOESCHT.search(self.code),
                          "das Skript ruft einen loeschenden Befehl auf")

    def test_the_delete_check_finds_a_real_delete(self) -> None:
        for probe in ("rm -f /backup/x", "find /backup -exec rm {} +",
                      "chmod 640 /backup/x; rm /backup/y",
                      "sudo docker system prune -f"):
            with self.subTest(probe=probe):
                self.assertIsNotNone(self.LOESCHT.search(probe))

    def test_the_delete_check_does_not_trip_over_perm_flags(self) -> None:
        # The false positive itself, kept as a case.
        self.assertIsNone(self.LOESCHT.search(
            'find "$backups" -type f \\( -perm -o=r -o -perm -o=w \\)'))

    def test_the_delete_check_looks_at_code_not_at_prose(self) -> None:
        # Guard against the guard being satisfied by moving code into a
        # comment, and against it going blind if the script loses its header.
        self.assertIn("--rm", self.text)
        self.assertNotIn("--rm", self.code)
        self.assertIn("chmod", self.code)

    def test_it_reports_a_result_line_and_a_count(self) -> None:
        self.assertIn("RESULT: PASS", self.text)
        self.assertIn("RESULT: FAIL", self.text)
        self.assertIn("geprueft:", self.text)

    def test_it_measures_again_after_changing(self) -> None:
        # A script that only sets modes and then claims success would report
        # PASS on a folder it failed to touch. It counts before and after.
        self.assertIn('vorher="$(find', self.text)
        self.assertIn('nachher="$(find', self.text)
        self.assertRegex(self.text, r'if \[ "\$nachher" -eq 0 \]')

    def test_it_prints_names_never_contents(self) -> None:
        self.assertNotIn("cat ", self.text)
        self.assertNotIn("head -c", self.text)

    def test_a_weakened_check_would_be_noticed(self) -> None:
        # Drop the post-check and the script would always claim PASS.
        broken = self.text.replace('if [ "$nachher" -eq 0 ]; then', 'if true; then', 1)
        self.assertNotEqual(self.text, broken)
        self.assertNotRegex(broken, r'if \[ "\$nachher" -eq 0 \]')


class ItIsShippedTest(unittest.TestCase):
    def test_the_permission_check_and_the_fix_agree_on_the_folder(self) -> None:
        check = (NAS / "check_backup_permissions.sh").read_text(encoding="utf-8")
        fix = SCRIPT.read_text(encoding="utf-8")
        pfad = "/volume1/docker/Startup-Backups"
        for name, body in (("check", check), ("fix", fix)):
            with self.subTest(skript=name):
                self.assertIn(pfad, body)
                self.assertIn("BACKUP_DIR", body)

    def test_the_fix_satisfies_what_the_check_demands(self) -> None:
        # The check fails on world-read and world-write. The fix has to clear
        # exactly those, or the pair would disagree every night.
        check = (NAS / "check_backup_permissions.sh").read_text(encoding="utf-8")
        self.assertIn("-perm -o=r", check)
        self.assertIn("-perm -o=w", check)
        # Every chmod in the script has to close the world bits, or the pair
        # would disagree every night. Checked over all of them, not the first.
        modi = re.findall(r"chmod (\S+)", code_only(SCRIPT.read_text(encoding="utf-8")))
        self.assertTrue(modi)
        for modus in modi:
            with self.subTest(modus=modus):
                self.assertRegex(modus, r"o=(?:,|$)")


if __name__ == "__main__":
    unittest.main()
