"""The check that asks whether a backup is worth restoring from.

`check_backup_permissions.sh` answers "may the wrong people read it".
`check_backup_integrity.sh` answers "is there anything worth reading". Neither
implies the other, and the second was missing (review finding G-047).

The gap is concrete. The nightly task runs

    docker exec startup-db-1 pg_dump ... > "$BACKUP_DIR/workforce-$STAMP.sql"

and the redirection belongs to the task's shell. A failing `docker exec` still
leaves a file - empty or truncated - and the task continues. The NAS powers on
at 02:00 and this runs at 02:05, so the database has five minutes to become
healthy; a slow start would produce exactly that file.

These tests are properties of the script's text. Its behaviour was proven on
the NAS against five fixtures - truncated, empty, stale, damaged archive, empty
folder - because the script uses `date -r <file>`, which is GNU semantics and
means something else on this Mac. Testing it locally would test the wrong
platform.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
SCRIPT = NAS / "check_backup_integrity.sh"


def code_only(body: str) -> str:
    return "\n".join(line for line in body.split("\n")
                     if not line.lstrip().startswith("#"))


class ScriptShapeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SCRIPT.read_text(encoding="utf-8")
        self.code = code_only(self.text)

    LOESCHT = re.compile(r"(?:^|[;&|]\s*|-exec\s+|\$\(\s*)(rm|unlink|shred|truncate)\b"
                         r"|docker\s+\w*\s*prune", re.MULTILINE)

    def test_it_never_deletes(self) -> None:
        self.assertIsNone(self.LOESCHT.search(self.code))

    def test_it_lists_the_archive_and_never_extracts_it(self) -> None:
        # startup.env is in there. Listing reads the table of contents; a wrong
        # flag would unpack the owner's password into the backup folder.
        self.assertIn("tar -tzf", self.code)
        self.assertNotIn("tar -xzf", self.code)
        self.assertNotIn("tar xzf", self.code)

    def test_it_never_prints_file_contents(self) -> None:
        for verboten in ("cat \"$newest", "head -1 \"$newest", "head \"$newest"):
            with self.subTest(befehl=verboten):
                self.assertNotIn(verboten, self.code)

    def test_it_checks_completeness_and_not_only_size(self) -> None:
        # Size alone would accept a file that pg_dump never finished. The
        # trailer is what makes it a whole dump.
        self.assertIn("PostgreSQL database dump complete", self.code)
        self.assertIn("restrict", self.code)

    def test_the_trailer_pattern_is_anchored(self) -> None:
        # `^...$` matters: the phrase also appears inside the dump's own header
        # comment block on some versions, and a loose match would accept a file
        # that contains the words but not the line.
        self.assertIn("'^-- PostgreSQL database dump complete$'", self.code)

    def test_it_checks_age_and_shrinkage(self) -> None:
        self.assertIn("BACKUP_MAX_AGE_HOURS", self.code)
        self.assertIn("BACKUP_MIN_RATIO_PERCENT", self.code)

    def test_every_finding_counts_and_the_result_follows_it(self) -> None:
        # A check that printed FAIL and exited 0 would be read as green by
        # nas_status.sh, which judges by the exit code.
        self.assertIn("problems=$((problems + 1))", self.code)
        self.assertRegex(self.code, r'if \[ "\$problems" -eq 0 \]')
        self.assertIn("exit 1", self.code)

    def test_a_weakened_result_line_would_be_noticed(self) -> None:
        broken = self.code.replace('if [ "$problems" -eq 0 ]; then', 'if true; then', 1)
        self.assertNotEqual(self.code, broken)
        self.assertNotRegex(broken, r'if \[ "\$problems" -eq 0 \]')

    def test_the_dump_glob_excludes_the_preflight_dumps(self) -> None:
        # The preflight dumps carry their own prefix, so `workforce-*.sql` sees
        # only the nightly ones. If that ever changes, a manual preflight would
        # be mistaken for a successful nightly run.
        self.assertIn('"$backups"/workforce-*.sql', self.code)
        self.assertNotIn("preflight-*", self.code)


class ItIsWiredIntoTheStatusReportTest(unittest.TestCase):
    """A check nobody runs is a file, not a guard."""

    def test_nas_status_runs_it_as_a_gate(self) -> None:
        status = (NAS / "nas_status.sh").read_text(encoding="utf-8")
        self.assertIn('run_gate "Backup-Inhalt" check_backup_integrity.sh', status)

    def test_it_runs_through_run_gate_and_not_through_a_pipe(self) -> None:
        # The reason run_gate exists: a pipeline returns the exit code of its
        # last command, so `check | tail` reports whether tail worked. That
        # once made nas_status.sh print PASS under a failing manifest.
        status = (NAS / "nas_status.sh").read_text(encoding="utf-8")
        self.assertNotIn("check_backup_integrity.sh |", status)
        self.assertIn('output="$(sh "$script" 2>&1)"', status)

    def test_the_two_backup_checks_are_separate_gates(self) -> None:
        status = (NAS / "nas_status.sh").read_text(encoding="utf-8")
        self.assertIn("check_backup_permissions.sh", status)
        self.assertIn("check_backup_integrity.sh", status)


if __name__ == "__main__":
    unittest.main()
