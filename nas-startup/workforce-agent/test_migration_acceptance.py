"""Every migration is supposed to have an acceptance test. Four do not.

CLAUDE.md, section Migrationen, point 6: "Abnahmetest unter
`postgres-tests/NNN_<name>_acceptance.sql` - laeuft in einer Transaktion und
endet mit `ROLLBACK`, damit er gegen die Produktion laufen darf."

The rule is stated and not held (review finding G-047). Rather than leave that
in prose where it decays, this test writes the gap down and fails when it
*changes in either direction*: a new migration without an acceptance test is a
regression, and closing one of the known gaps without updating this list means
the list has started lying.

A guard that simply went red on the current state would have been switched off
by the second day. A guard that fixes the current state in place keeps the gap
visible and makes closing it a deliberate act.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
MIGRATIONS = NAS / "postgres-init"
ACCEPTANCE = NAS / "postgres-tests"

# Migration id -> why it has no acceptance test yet. Emptying an entry is the
# way to close a gap: write the test, then delete the line here.
KNOWN_GAPS = {
    "003_workforce_bus_trigger_fix":
        "Korrektur an 002; die Wirkung wird von 002_workforce_bus_acceptance mitgeprueft, "
        "ein eigener Test fehlt trotzdem",
    # 006 und 007 sind am 2026-09-02 geschlossen worden: beide Tests laufen
    # gegen die Produktion (Katalog lesen, ROLLBACK) und wurden mit je einer
    # umgedrehten Erwartung geprueft, die auch anschlug.
    "008_knowledge_api_grants":
        "gegatet und nicht angewendet - der Abnahmetest gehoert in dasselbe Fenster "
        "wie die Anwendung",
    "004_knowledge_capability":
        "der Test existiert, heisst aber 003_knowledge_capability_acceptance.sql - "
        "gefunden erst von diesem Waechter, weil die Nummer nicht zur Migration passt",
}

# `_acceptance.sql` promises: runs in a transaction, ends with ROLLBACK, may be
# pointed at production. One file in this folder does not keep that promise -
# it changes state and commits. It is a demo script wearing an acceptance
# test's name (G-047). It is not an open door: it refuses to run unless
# `app.visible_demo` is ENABLED. The exemption is listed by name and the guard
# it relies on is asserted, so this stays a known property instead of a
# surprise.
STATE_CHANGING = {
    "004_visible_communication_acceptance.sql": "VISIBLE_DEMO_GUARD_REQUIRED",
}

# Acceptance files whose number does not match the migration they belong to.
# Renaming them is not free: the numbers appear in evidence documents that must
# not be rewritten (a proof gets a dated addendum, never an edit).
MISNUMBERED = {
    "003_knowledge_capability_acceptance.sql": "004_knowledge_capability",
    "004_visible_communication_acceptance.sql": None,  # keine Migration dieses Namens
}


def migrations() -> list[str]:
    return sorted(p.stem for p in MIGRATIONS.glob("*.sql"))


def acceptance_files() -> list[str]:
    return sorted(p.name for p in ACCEPTANCE.glob("*.sql"))


def has_acceptance(migration: str) -> bool:
    return (ACCEPTANCE / f"{migration}_acceptance.sql").is_file()


class AcceptanceCoverageTest(unittest.TestCase):
    def test_the_gap_is_exactly_what_is_written_down(self) -> None:
        actual = {m for m in migrations() if not has_acceptance(m)}
        expected = set(KNOWN_GAPS)
        neu = sorted(actual - expected)
        geschlossen = sorted(expected - actual)
        self.assertEqual([], neu, "Migration ohne Abnahmetest und ohne Eintrag")
        self.assertEqual([], geschlossen,
                         "Luecke geschlossen? Dann den Eintrag in KNOWN_GAPS entfernen")

    def test_every_known_gap_names_a_real_migration(self) -> None:
        for name in KNOWN_GAPS:
            with self.subTest(migration=name):
                self.assertTrue((MIGRATIONS / f"{name}.sql").is_file())

    def test_every_gap_carries_a_reason(self) -> None:
        # An entry without a reason is a silent exception, which is the thing
        # this file exists to prevent.
        for name, reason in KNOWN_GAPS.items():
            with self.subTest(migration=name):
                self.assertGreater(len(reason.strip()), 30, name)

    def test_the_misnumbered_files_are_still_misnumbered(self) -> None:
        # Documents the second half of G-047: the acceptance numbering is not
        # the migration numbering. If somebody renames them, this fails and the
        # evidence documents that cite the old names need an addendum.
        present = set(acceptance_files())
        for name, belongs_to in MISNUMBERED.items():
            with self.subTest(datei=name):
                self.assertIn(name, present)
                if belongs_to is not None:
                    self.assertTrue((MIGRATIONS / f"{belongs_to}.sql").is_file())

    def test_a_new_migration_without_a_test_would_be_caught(self) -> None:
        erfunden = "009_neue_migration"
        actual = {m for m in migrations() if not has_acceptance(m)} | {erfunden}
        self.assertNotIn(erfunden, KNOWN_GAPS)
        self.assertTrue(sorted(actual - set(KNOWN_GAPS)))


class AcceptanceFilesAreShippedTest(unittest.TestCase):
    """The folder is mounted into the production database container.

    compose.yaml line 22: `./postgres-tests:/opt/startup/tests:ro`. It is
    mounted read-only and nothing runs it automatically, so this is not the
    execution hazard G-041 was - but the folder appeared in no deploy path
    list, so the manifest could not see what was actually lying there
    (G-047, same shape as G-020).
    """

    def test_the_folder_is_mounted_into_the_database(self) -> None:
        compose = (NAS / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("./postgres-tests:/opt/startup/tests:ro", compose)

    def test_nothing_auto_executes_it(self) -> None:
        # The distinction from G-041: not under /docker-entrypoint-initdb.d.
        compose = (NAS / "compose.yaml").read_text(encoding="utf-8")
        self.assertNotIn("postgres-tests:/docker-entrypoint-initdb.d", compose)

    def test_every_acceptance_file_rolls_back(self) -> None:
        # The rule says these run against production, so a file that commits
        # would change it. Checked here because it is cheap and the cost of
        # being wrong is a modified production database.
        for path in sorted(ACCEPTANCE.glob("*.sql")):
            if path.name in STATE_CHANGING:
                continue
            with self.subTest(datei=path.name):
                body = path.read_text(encoding="utf-8")
                self.assertTrue(re.search(r"\bROLLBACK\b", body, re.IGNORECASE),
                                f"{path.name} endet nicht mit ROLLBACK")
                self.assertFalse(re.search(r"^\s*COMMIT\s*;", body,
                                           re.IGNORECASE | re.MULTILINE),
                                 f"{path.name} enthaelt ein COMMIT")

    def test_the_state_changing_script_keeps_its_own_guard(self) -> None:
        for name, guard in STATE_CHANGING.items():
            with self.subTest(datei=name):
                body = (ACCEPTANCE / name).read_text(encoding="utf-8")
                self.assertIn(guard, body)
                self.assertIn("app.visible_demo", body)

    def test_the_exemption_list_is_not_a_blanket(self) -> None:
        # Every other file has to keep the promise its name makes.
        ohne_rollback = {
            path.name for path in ACCEPTANCE.glob("*.sql")
            if not re.search(r"\bROLLBACK\b", path.read_text(encoding="utf-8"), re.IGNORECASE)
        }
        self.assertEqual(set(STATE_CHANGING), ohne_rollback)


if __name__ == "__main__":
    unittest.main()
