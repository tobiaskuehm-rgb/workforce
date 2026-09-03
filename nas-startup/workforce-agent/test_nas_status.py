"""`nas_status.sh` - das Preflight, gegen Attrappen gefahren.

Review finding G-085. Das Skript ist der Waechter, an dem jedes Gate haengt:
Abschnitt 2, 6.4 und 8 des Phase-5-Runbooks lesen sein `RESULT`. Es hatte zwei
Wege, `PASS` zu melden, ohne hinzusehen. Der API-Block nannte den Container
beim abgeleiteten Namen (`G-042`) und druckte bei einem Fehlschlag nur
"(API nicht erreichbar)"; der Datenbankblock haengte ein `| grep` an, und der
Status einer Pipeline ist der ihres letzten Befehls - `grep` ist erfolgreich,
sobald es eine Zeile ausgibt, auch "psql: error: ...". Und die Sollwerte, auf
die das Runbook sich beruft, standen als Leseaufgabe da.

Hier laeuft das Skript in einer Kopie seines Ordners mit Stubs fuer `sudo`
und `docker` vorn im PATH, fuenf Stub-Gates, einer Vorlage von
`production_state.txt` und einem Backup-Ordner daneben. Nichts davon
beruehrt die NAS. Jeder Fall verlangt Exitcode **und** `RESULT`-Zeile.
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
SKRIPT = NAS / "nas_status.sh"

MIGRATIONEN = ("001_employee_registry,002_workforce_bus,003_workforce_bus_trigger_fix,"
               "005_bus_denial_audit,006_legacy_registry_tables,007_least_privilege_roles")
GATES = ("verify_manifest.sh", "check_backup_permissions.sh", "check_backup_integrity.sh",
         "check_bus_address.sh", "check_unmanaged.sh")


def db_ausgabe(*, kanal="DISABLED", credentials="0", migrationen=MIGRATIONEN) -> str:
    return "\n".join((
        f"Migrationen|{migrationen}",
        f"Kanal|{kanal}",
        f"aktive Credentials|{credentials}",
        "Knowledge 004|nicht angewendet",
        "Ablehnungs-Audit 005|angewendet",
        "Rolle workforce_api|vorhanden",
        "Rolle workforce_backup|vorhanden",
        "workforce_app SUPERUSER|ja - G-045: nicht per ALTER ROLE entziehbar",
        "Datenbankgroesse|12 MB",
    ))


class Attrappen:
    def __init__(self, ordner: pathlib.Path) -> None:
        self.ordner = ordner
        self.protokoll = ordner / "aufrufe.log"
        self.bin = ordner / "bin"
        self.bin.mkdir()
        self.arbeit = ordner / "Startup"
        self.arbeit.mkdir()
        shutil.copy(SKRIPT, self.arbeit / "nas_status.sh")
        (self.arbeit / "production_state.txt").write_text(
            f"PRODUCTION_COMMIT=abc1234\nAPPLIED_MIGRATIONS={MIGRATIONEN}\n", encoding="utf-8")
        (self.arbeit / "startup.db.env").write_text("POSTGRES_USER=x\n", encoding="utf-8")
        for gate in GATES:
            self._stub(self.arbeit / gate, f'echo "RESULT: PASS"; exit "${{STUB_GATE_FAIL_{gate.split(".")[0].upper()}:-0}}"')
        backups = ordner / "Startup-Backups"
        backups.mkdir()
        (backups / "preflight-1.sql").write_text("x", encoding="utf-8")
        (backups / "preflight-1.globals.sql").write_text("x", encoding="utf-8")
        (backups / "rollback-1.tar.gz").write_text("x", encoding="utf-8")

        # sudo: den Programmpfad ignorieren, unseren docker-Stub nehmen. Das
        # Skript ruft sudo /usr/local/bin/docker - der absolute Pfad ist die
        # NAS-Regel, nicht dieser Rechner.
        self._stub(self.bin / "sudo", 'shift; exec "$(dirname "$0")/docker" "$@"')
        self._stub(self.bin / "docker", """
            printf 'docker %s\\n' "$*" >> "$STUB_LOG"
            case "$1 $2" in
              "ps --format") echo "startup-db-1 | postgres:17-alpine | Up (healthy)"; exit 0;;
              "compose ps") printf '%s' "${STUB_API_ID-api0001}"; exit 0;;
              "exec "*) [ "${STUB_API_CODE:-0}" -eq 0 ] && echo '{"api_version": "v9", "channel_status": "DISABLED"}' || echo "Error response from daemon: no such container"; exit "${STUB_API_CODE:-0}";;
              "run --rm") printf '%s\\n' "$STUB_DB_OUT"; exit "${STUB_DB_CODE:-0}";;
            esac
            echo "unerwarteter docker-Aufruf: $*" >&2; exit 99
        """)

    @staticmethod
    def _stub(pfad: pathlib.Path, rumpf: str) -> None:
        pfad.write_text("#!/bin/sh\n" + "\n".join(z.strip() for z in rumpf.strip().splitlines()) + "\n",
                        encoding="utf-8")
        pfad.chmod(0o755)

    def lauf(self, *, db_out: str | None = None, **umgebung: str) -> tuple[int, str]:
        env = dict(os.environ)
        env.update({"PATH": f"{self.bin}{os.pathsep}{env.get('PATH', '')}",
                    "STUB_LOG": str(self.protokoll),
                    "STUB_DB_OUT": db_ausgabe() if db_out is None else db_out})
        env.update(umgebung)
        ergebnis = subprocess.run(["sh", str(self.arbeit / "nas_status.sh")],
                                  capture_output=True, text=True, env=env)
        return ergebnis.returncode, ergebnis.stdout + ergebnis.stderr

    def docker_aufrufe(self) -> list[str]:
        if not self.protokoll.exists():
            return []
        return self.protokoll.read_text(encoding="utf-8").splitlines()


class NasStatusBehaviourTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.att = Attrappen(pathlib.Path(self.tmp.name))

    def assertFail(self, code: int, ausgabe: str, teil: str) -> None:
        self.assertNotEqual(0, code, ausgabe)
        self.assertIn("RESULT: FAIL", ausgabe)
        self.assertIn(teil, ausgabe)

    def test_a_healthy_nas_passes(self) -> None:
        code, ausgabe = self.att.lauf()
        self.assertEqual(0, code, ausgabe)
        self.assertIn("RESULT: PASS", ausgabe)
        self.assertIn("PASS: Kanal = DISABLED", ausgabe)
        self.assertIn("PASS: aktive Credentials = 0", ausgabe)
        self.assertIn("PASS: Migrationen = 001_employee_registry", ausgabe)

    def test_the_api_container_is_resolved_not_named(self) -> None:
        self.att.lauf()
        aufrufe = self.att.docker_aufrufe()
        self.assertTrue(any(a.startswith("docker compose ps -q workforce-api") for a in aufrufe), aufrufe)
        self.assertFalse(any("startup-workforce-api-1" in a for a in aufrufe),
                         "ein abgeleiteter Containername (G-042)")
        self.assertTrue(any(a.startswith("docker exec api0001 ") for a in aufrufe), aufrufe)

    def test_a_missing_api_container_fails(self) -> None:
        code, ausgabe = self.att.lauf(STUB_API_ID="")
        self.assertFail(code, ausgabe, "kein Container fuer den Dienst workforce-api")

    def test_a_failed_api_query_fails(self) -> None:
        # Vorher: "(API nicht erreichbar)" und darunter PASS.
        code, ausgabe = self.att.lauf(STUB_API_CODE="1")
        self.assertFail(code, ausgabe, "API-Abfrage Exitcode 1")

    def test_a_psql_error_fails_even_though_it_prints_a_line(self) -> None:
        # Der Befund selbst: Ausgabe vorhanden, Exitcode 2, vorher PASS.
        code, ausgabe = self.att.lauf(
            db_out='psql: error: connection to server at "db" failed: FATAL: password authentication failed',
            STUB_DB_CODE="2")
        self.assertFail(code, ausgabe, "Datenbankabfrage Exitcode 2")

    def test_an_open_channel_fails_the_preflight(self) -> None:
        code, ausgabe = self.att.lauf(db_out=db_ausgabe(kanal="TESTING"))
        self.assertFail(code, ausgabe, "FAIL: Kanal = TESTING, erwartet DISABLED")

    def test_an_active_credential_fails_the_preflight(self) -> None:
        code, ausgabe = self.att.lauf(db_out=db_ausgabe(credentials="1"))
        self.assertFail(code, ausgabe, "FAIL: aktive Credentials = 1, erwartet 0")

    def test_an_unexpected_migration_fails_the_preflight(self) -> None:
        code, ausgabe = self.att.lauf(db_out=db_ausgabe(migrationen=MIGRATIONEN + ",009_bus_function_owner"))
        self.assertFail(code, ausgabe, "FAIL: Migrationen = ")

    def test_a_missing_value_is_a_failure_not_a_gap(self) -> None:
        # Regel 45: Ein nicht gemessener Punkt ist ein Fehlschlag.
        code, ausgabe = self.att.lauf(db_out="Migrationen|" + MIGRATIONEN + "\nKanal|DISABLED\n")
        self.assertFail(code, ausgabe, "aktive Credentials nicht gemessen")

    def test_the_expected_migrations_come_from_production_state(self) -> None:
        (self.att.arbeit / "production_state.txt").write_text("PRODUCTION_COMMIT=abc1234\n", encoding="utf-8")
        code, ausgabe = self.att.lauf()
        self.assertFail(code, ausgabe, "production_state.txt nennt keine APPLIED_MIGRATIONS")

    def test_an_open_window_can_be_measured_when_said_so(self) -> None:
        code, ausgabe = self.att.lauf(db_out=db_ausgabe(kanal="TESTING", credentials="3"),
                                      EXPECT_CHANNEL="TESTING", EXPECT_ACTIVE_CREDENTIALS="3")
        self.assertEqual(0, code, ausgabe)
        self.assertIn("PASS: Kanal = TESTING", ausgabe)

    def test_a_failing_gate_still_fails(self) -> None:
        code, ausgabe = self.att.lauf(STUB_GATE_FAIL_VERIFY_MANIFEST="1")
        self.assertFail(code, ausgabe, "RESULT: FAIL")


if __name__ == "__main__":
    unittest.main()
