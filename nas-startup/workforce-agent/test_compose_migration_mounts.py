"""G-041: a gated migration folder must never be auto-executed on startup.

The db service mounted ./postgres-init at /docker-entrypoint-initdb.d. The
official postgres entrypoint runs every *.sql in that directory, in
alphabetical order, whenever the data directory is empty - which is exactly
the restore case. registry-migrate, which owns the APPLY_MIGRATION_* gates,
has not even started at that point.

While the folder held only 001-003 the consequence was invisible: a volume
reset replayed what was already applied. Phase 4 puts 004-008 into the same
folder, and from that moment a restore would apply Knowledge 004 as a side
effect - against an explicit standing instruction - and then abort at 007,
whose login roles do not exist yet.

The mount was pure redundancy: registry-migrate mounts the same folder at
/opt/startup/migrations and creates 001-003 itself when the marker table is
missing. Removing it costs nothing and closes the bypass.
"""

import pathlib
import tempfile
import unittest

import compose_scan

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Where the postgres image auto-runs whatever it finds.
AUTORUN = "/docker-entrypoint-initdb.d"

# Directories whose contents are gated and must therefore never be auto-run.
GATED = ("postgres-init",)


def offenders(services: dict[str, compose_scan.Service]) -> list[str]:
    found = []
    for name, service in services.items():
        for mount in service.volume_mounts:
            parts = mount.split(":")
            if len(parts) < 2:
                continue
            source, destination = parts[0], parts[1]
            if destination.rstrip("/") != AUTORUN:
                continue
            if any(g in source for g in GATED):
                found.append(f"{name}: {mount}")
    return found


class NoGatedMigrationIsAutoExecutedTest(unittest.TestCase):

    def test_no_compose_file_auto_runs_a_gated_migration_folder(self) -> None:
        bad = []
        for path, services in compose_scan.scan_tree(ROOT).items():
            for entry in offenders(services):
                bad.append(f"{path.name} -> {entry}")
        self.assertEqual([], sorted(bad),
                         "ein gegateter Migrationsordner wird beim Start "
                         "automatisch ausgefuehrt und umgeht die Gates")

    def test_the_gated_folder_is_still_reachable_for_the_gate_runner(self) -> None:
        """Removing the mount must not orphan the migrations.

        A fix that deletes the bypass and the only remaining path to the files
        would turn a silent risk into a broken deployment.
        """
        services = compose_scan.scan(ROOT / "compose.yaml")
        self.assertIn("registry-migrate", services)
        mounts = services["registry-migrate"].volume_mounts
        self.assertTrue(
            any("postgres-init" in m and "/opt/startup/migrations" in m
                for m in mounts),
            f"registry-migrate erreicht die Migrationen nicht mehr: {mounts}",
        )

    def test_the_db_service_no_longer_mounts_the_migration_folder(self) -> None:
        services = compose_scan.scan(ROOT / "compose.yaml")
        sources = services["db"].volume_sources
        self.assertNotIn("./postgres-init", sources,
                         "der DB-Dienst sieht den Migrationsordner wieder")

    def test_the_check_detects_the_mount_it_was_written_for(self) -> None:
        """The weakened-control probe: reintroduce the exact line and look."""
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "compose.yaml"
            path.write_text(
                "services:\n"
                "  db:\n"
                "    image: postgres:17-alpine\n"
                "    volumes:\n"
                "      - ./postgres-init:/docker-entrypoint-initdb.d:ro\n",
                encoding="utf-8",
            )
            self.assertEqual(
                ["db: ./postgres-init:/docker-entrypoint-initdb.d:ro"],
                offenders(compose_scan.scan(path)),
            )

    def test_an_ungated_initdb_mount_is_not_flagged(self) -> None:
        """A guard that fires on everything gets switched off.

        Mounting some other seed folder there is a legitimate pattern; only
        directories holding gated migrations are the problem.
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "compose.yaml"
            path.write_text(
                "services:\n"
                "  db:\n"
                "    image: postgres:17-alpine\n"
                "    volumes:\n"
                "      - ./seed-data:/docker-entrypoint-initdb.d:ro\n",
                encoding="utf-8",
            )
            self.assertEqual([], offenders(compose_scan.scan(path)))


if __name__ == "__main__":
    unittest.main()
