#!/usr/bin/env python3
"""Probe fuer Migration 009: laufen die Funktionen danach ohne Superuser weiter?

Review finding G-045. Die Migration verschiebt das Eigentum der zwoelf
SECURITY-DEFINER-Funktionen auf `workforce_owner` - eine Rolle ohne
Superuser-Attribut, die die Tabellen **nicht** besitzt. Der Gewinn ist genau
das: Nur der Eigentuemer einer Tabelle oder ein Superuser kann
`ALTER TABLE ... DISABLE TRIGGER`, und darauf beruhen die
Append-only-Zusicherungen aus 006/007.

**Diese Probe laeuft in einem Wegwerf-Container, nicht gegen die Produktion.**
Sie ist nie gelaufen - ein Lauf ist eine Ausfuehrung auf der NAS und braucht
die Freigabe des CEO.

Regel 15 ist der Grund fuer den Zuschnitt: Eine Probe muss die **Rollenlage**
der Produktion nachbauen, nicht nur ihr Schema. `initdb` macht `POSTGRES_USER`
zum Bootstrap-Superuser; auf der NAS ist das `workforce_app`. Ein Container mit
dem Vorgabebenutzer `postgres` haette eine Lage, die es nicht gibt - genau
daran ist die erste `G-025`-Probe gescheitert und hat Gruen fuer etwas
Unmoegliches gemeldet.

Drei Fragen, und die zweite ist die, wegen der es diese Datei gibt:

  1. Bleibt nach 009 keine SECURITY-DEFINER-Funktion beim Superuser, und
     besitzt der neue Eigentuemer keine Tabelle?
  2. **Feuert der Audit-Trigger weiter, wenn `workforce_owner` schreibt?**
     Die neun Trigger- und Guardfunktionen bleiben bei `workforce_app`, und
     `007` hat EXECUTE von PUBLIC entzogen. Die PostgreSQL-Dokumentation zu
     CREATE TRIGGER sagt, EXECUTE werde beim Anlegen geprueft und nicht beim
     Ausloesen - deshalb erteilt 009 das Recht bewusst nicht. Diese Probe
     misst nach, ob die Dokumentation hier traegt.
  3. Kann `workforce_owner` das Audit abschalten? Er darf es nicht koennen.

    ssh-Zugang zur NAS vorausgesetzt:
        python3 g045_owner_probe.py
"""

from __future__ import annotations

import subprocess
import sys

HOST = "synology"
DOCKER = "sudo /usr/local/bin/docker"
NAME = "g045probe"
IMAGE = "postgres:17-alpine"
SRC = "/volume1/docker/Startup/postgres-init"
TESTS = "/volume1/docker/Startup/postgres-tests"

# Genau die Reihenfolge, die auf der NAS angewendet ist. 004 und 008 bleiben
# aussen vor - sie sind produktiv nicht angewendet, und eine Probe, die mehr
# anwendet als das Ziel, prueft eine andere Datenbank.
MIGRATIONEN = (
    "001_employee_registry.sql",
    "002_workforce_bus.sql",
    "003_workforce_bus_trigger_fix.sql",
    "005_bus_denial_audit.sql",
    "006_legacy_registry_tables.sql",
    "007_least_privilege_roles.sql",
)


def ssh(command: str, check: bool = True) -> str:
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=600", HOST, command],
        capture_output=True, text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"{command}\n{result.stdout}\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


def psql(sql: str) -> str:
    escaped = sql.replace("'", "'\\''")
    return ssh(f"{DOCKER} exec {NAME} psql -U workforce_app -d workforce -Atc '{escaped}' 2>&1",
               check=False)


def aufraeumen() -> None:
    # Gezielt, nie ein prune: der wirkt NAS-weit (G-038).
    ssh(f"{DOCKER} rm -f {NAME} >/dev/null 2>&1", check=False)


def start() -> None:
    aufraeumen()
    ssh(
        f"{DOCKER} run -d --name {NAME} "
        f"-e POSTGRES_USER=workforce_app "        # Regel 15: wie in der Produktion
        f"-e POSTGRES_DB=workforce "
        f"-e POSTGRES_PASSWORD=wegwerf-nur-fuer-diese-probe "
        f"-v {SRC}:/probe/migrations:ro -v {TESTS}:/probe/tests:ro "
        f"{IMAGE} >/dev/null"
    )
    for _ in range(60):
        if "accepting connections" in ssh(
                f"{DOCKER} exec {NAME} pg_isready -U workforce_app -d workforce 2>&1",
                check=False):
            return
        ssh("sleep 2", check=False)
    raise RuntimeError("Probe-Datenbank wurde nicht bereit")


def anwenden(datei: str) -> str:
    return ssh(
        f"{DOCKER} exec {NAME} psql -U workforce_app -d workforce "
        f"-v ON_ERROR_STOP=1 -f /probe/migrations/{datei} 2>&1", check=False)


def main() -> int:
    ergebnisse: list[tuple[str, str]] = []
    try:
        start()

        # 007 verlangt die beiden Login-Rollen; auf der NAS kommen sie aus dem
        # Secret-Store, hier aus Wegwerfwerten.
        psql("CREATE ROLE workforce_api LOGIN PASSWORD 'wegwerf1'")
        psql("CREATE ROLE workforce_backup LOGIN PASSWORD 'wegwerf2'")

        for datei in MIGRATIONEN:
            ausgabe = anwenden(datei)
            if "ERROR" in ausgabe:
                ergebnisse.append((f"Migration {datei}", f"FEHLER: {ausgabe[-200:]}"))
                raise SystemExit(1)
        ergebnisse.append(("Ausgangsstand", f"{len(MIGRATIONEN)} Migrationen angewendet"))

        vorher = psql(
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
            "JOIN pg_roles r ON r.oid = p.proowner "
            "WHERE n.nspname = 'workforce' AND p.prosecdef AND r.rolsuper")
        ergebnisse.append(("SECURITY DEFINER beim Superuser, vorher", vorher))

        # --- 009 anwenden -------------------------------------------------
        ausgabe = anwenden("009_bus_function_owner.sql")
        ergebnisse.append(("009 angewendet",
                           "ja" if "ERROR" not in ausgabe else f"FEHLER: {ausgabe[-200:]}"))
        if "ERROR" in ausgabe:
            raise SystemExit(1)

        nachher = psql(
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
            "JOIN pg_roles r ON r.oid = p.proowner "
            "WHERE n.nspname = 'workforce' AND p.prosecdef AND r.rolsuper")
        ergebnisse.append(("SECURITY DEFINER beim Superuser, nachher", nachher))

        # --- Frage 2: feuert der Audit-Trigger unter workforce_owner? -----
        # Das ist der Kern. workforce_owner hat auf bus_record_change kein
        # EXECUTE; laut Dokumentation wird das beim Ausloesen nicht geprueft.
        vor_events = psql("SELECT count(*) FROM workforce.bus_events")
        schreiben = psql(
            "SET ROLE workforce_owner; "
            "SELECT set_config('app.actor_id', 'SYSTEM-PROBE', true); "
            "SELECT set_config('app.request_id', 'PROBE-G045-WRITE', true); "
            "UPDATE workforce.bus_channels SET source_ref = 'PROBE-G045' "
            "WHERE project_id = 'START-UP'")
        nach_events = psql("RESET ROLE; SELECT count(*) FROM workforce.bus_events")
        ergebnisse.append(("Schreibversuch als workforce_owner",
                           "ok" if "ERROR" not in schreiben else schreiben[-160:]))
        ergebnisse.append(("bus_events vorher/nachher", f"{vor_events} -> {nach_events}"))
        gefeuert = (vor_events.isdigit() and nach_events.isdigit()
                    and int(nach_events) > int(vor_events))
        ergebnisse.append(("Audit-Trigger gefeuert",
                           "JA - Dokumentation traegt, kein GRANT noetig" if gefeuert
                           else "NEIN - 009 braucht das EXECUTE doch"))

        # --- Frage 3: kann er das Audit abschalten? -----------------------
        abschalten = psql(
            "SET ROLE workforce_owner; "
            "ALTER TABLE workforce.bus_messages DISABLE TRIGGER USER")
        ergebnisse.append(("Trigger abschaltbar",
                           "NEIN - abgewiesen" if "ERROR" in abschalten
                           else "JA - die Migration verfehlt ihren Zweck"))

        # --- Abnahmetest --------------------------------------------------
        test = ssh(
            f"{DOCKER} exec {NAME} psql -U workforce_app -d workforce "
            f"-v ON_ERROR_STOP=1 -f /probe/tests/009_bus_function_owner_acceptance.sql 2>&1",
            check=False)
        ergebnisse.append(("Abnahmetest 009",
                           "PASS" if "ERROR" not in test else test[-200:]))
    finally:
        aufraeumen()

    breite = max(len(k) for k, _ in ergebnisse)
    print("\n=== G-045 Eigentuemertrennung, Wegwerf-Container ===\n")
    for kennung, wert in ergebnisse:
        print(f"  {kennung.ljust(breite)}  {wert}")
    print()
    gut = (dict(ergebnisse).get("SECURITY DEFINER beim Superuser, nachher") == "0"
           and dict(ergebnisse).get("Trigger abschaltbar", "").startswith("NEIN")
           and dict(ergebnisse).get("Abnahmetest 009") == "PASS")
    print("RESULT: PASS" if gut else "RESULT: FAIL")
    return 0 if gut else 1


if __name__ == "__main__":
    sys.exit(main())
