"""The nightly backup, moved out of the Task Scheduler into a versioned file.

Until 2026-09-02 the logic lived only inside DSM's own database: not in git,
not in the manifest, not reviewed, not testable. Reading it required opening
the task or querying esynoscheduler. That is the deeper half of G-047 - the
folder was unmanaged, and so was the script filling it.

What these tests hold is mostly **order**, because order was the actual defect:
the old version deleted 31-day-old backups before anything had established
that today's was worth keeping, and it set permissions never.

Behaviour was proven on the NAS against the real stack: container resolved,
database healthy, dump complete at 380952 bytes, archive at 27722, and the
permissions step correctly refusing because the run was not root. The run wrote
into a scratch directory, so no production backup was created and no retention
prune took place; the production folder still held its 64 files afterwards.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
SCRIPT = NAS / "backup_task.sh"


def code_only(body: str) -> str:
    return "\n".join(line for line in body.split("\n")
                     if not line.lstrip().startswith("#"))


class OrderIsTheContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.code = code_only(SCRIPT.read_text(encoding="utf-8"))

    def position(self, needle: str) -> int:
        index = self.code.find(needle)
        self.assertNotEqual(-1, index, f"nicht gefunden: {needle}")
        return index

    def test_the_prune_runs_after_the_completeness_check(self) -> None:
        # The whole point. Deleting old backups is safe exactly when a new good
        # one exists, and not a step earlier.
        self.assertLess(self.position("PostgreSQL database dump complete"),
                        self.position("-delete"))

    def test_the_prune_runs_after_the_permissions_step(self) -> None:
        self.assertLess(self.position("harden_backup_permissions.sh"),
                        self.position("-delete"))

    def test_permissions_are_set_before_the_run_ends(self) -> None:
        # G-048: otherwise the files sit world-readable from 02:05 until
        # somebody notices.
        self.assertIn("harden_backup_permissions.sh", self.code)
        self.assertLess(self.position("config-$STAMP.tar.gz"),
                        self.position("harden_backup_permissions.sh"))


class WhatItRefusesToDoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SCRIPT.read_text(encoding="utf-8")
        self.code = code_only(self.text)

    def test_the_container_name_is_not_hard_coded(self) -> None:
        # G-042: a container name is derived from project directory, service
        # and index. It is right today and nobody promised to keep it.
        self.assertNotIn("startup-db-1", self.code)
        self.assertIn("compose ps -q db", self.code)

    def test_it_waits_for_the_database_to_be_healthy(self) -> None:
        # The NAS powers on at 02:00 and the task runs at 02:05.
        self.assertIn("healthy", self.code)
        self.assertIn("DB_HEALTH_TRIES", self.code)

    def test_an_incomplete_dump_is_marked_and_not_removed(self) -> None:
        # Guardrail 2: it is renamed, so a later reader can see what happened.
        # The suffix also takes it out of the `workforce-*.sql` glob, so
        # check_backup_integrity.sh reports the real age gap instead of
        # accepting a broken file as the newest backup.
        # Two failure paths - pg_dump exits non-zero, and pg_dump exits zero
        # but the trailer is missing - and each has to rename, not just say so.
        self.assertEqual(2, self.code.count('mv "$dump" "$dump.unvollstaendig"'),
                         "beide Fehlerpfade muessen die Datei umbenennen")
        self.assertNotIn('rm "$dump"', self.code)

    def test_the_only_delete_is_the_retention_prune(self) -> None:
        loeschend = re.findall(r"(?:^|[;&|]\s*|-exec\s+)(rm|unlink|shred)\b|(-delete)\b",
                               self.code, re.MULTILINE)
        treffer = [a or b for a, b in loeschend]
        self.assertEqual(["-delete"], treffer, f"unerwartet loeschend: {treffer}")

    def test_the_retention_window_is_unchanged(self) -> None:
        # 30 days is the CEO's decision. Changing it while fixing something
        # else would be a second change hidden inside the first.
        self.assertIn('RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"', self.code)

    def test_a_broken_docker_is_reported_as_such(self) -> None:
        # Without this the `|| true` on the next line turns "the CLI could not
        # run" into "there is no container", and the operator goes looking for
        # a stopped stack that is running fine.
        self.assertIn('"$DOCKER" version', self.code)
        self.assertLess(self.code.find('"$DOCKER" version'),
                        self.code.find("compose ps -q db"))

    def test_it_does_not_change_the_scheduler_itself(self) -> None:
        # The task is the CEO's to edit. Nothing here may reach DSM.
        for verboten in ("synoschedtask", "esynoscheduler", "synoschedule.d"):
            with self.subTest(begriff=verboten):
                self.assertNotIn(verboten, self.code)
        self.assertIn("sh /volume1/docker/Startup/backup_task.sh", self.text)


class ItAgreesWithTheCheckerTest(unittest.TestCase):
    """The writer and the checker have to mean the same thing by "complete"."""

    def test_both_use_the_same_anchored_trailer(self) -> None:
        muster = "'^-- PostgreSQL database dump complete$'"
        for name in ("backup_task.sh", "check_backup_integrity.sh"):
            with self.subTest(datei=name):
                self.assertIn(muster, (NAS / name).read_text(encoding="utf-8"))

    def test_both_write_and_look_in_the_same_place(self) -> None:
        for name in ("backup_task.sh", "check_backup_integrity.sh"):
            with self.subTest(datei=name):
                body = (NAS / name).read_text(encoding="utf-8")
                self.assertIn("/volume1/docker/Startup-Backups", body)
                self.assertIn("BACKUP_DIR", body)

    def test_the_filenames_the_writer_produces_match_the_checker_glob(self) -> None:
        writer = code_only(SCRIPT.read_text(encoding="utf-8"))
        checker = code_only((NAS / "check_backup_integrity.sh").read_text(encoding="utf-8"))
        self.assertIn("workforce-$STAMP.sql", writer)
        self.assertIn("workforce-*.sql", checker)
        self.assertIn("config-$STAMP.tar.gz", writer)
        self.assertIn("config-*.tar.gz", checker)


if __name__ == "__main__":
    unittest.main()
