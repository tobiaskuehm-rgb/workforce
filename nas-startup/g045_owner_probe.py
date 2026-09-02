#!/usr/bin/env python3
"""Probe fuer Migration 009: laufen die Funktionen danach ohne Superuser weiter?

Review finding G-045. Die Migration verschiebt das Eigentum der zwoelf
SECURITY-DEFINER-Busfunktionen auf `workforce_owner` - eine Rolle ohne
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
     besitzt der neue Eigentuemer keine Relation?
  2. **Feuert der Audit-Trigger weiter, wenn `workforce_owner` schreibt?**
     Die neun Trigger- und Guardfunktionen bleiben bei `workforce_app`, und
     `007` hat EXECUTE von PUBLIC entzogen. Die PostgreSQL-Dokumentation zu
     CREATE TRIGGER sagt, EXECUTE werde beim Anlegen geprueft und nicht beim
     Ausloesen - deshalb erteilt 009 das Recht bewusst nicht. Diese Probe
     misst nach, ob die Dokumentation hier traegt. Sie beantwortet dabei
     zugleich die offene Frage aus `009` Abschnitt 3c: `bus_events` hat einen
     Identity-Schluessel, also zeigt derselbe Schreibvorgang, ob die Allowlist
     ohne Sequenzrechte reicht.
  3. Kann `workforce_owner` das Audit abschalten? Er darf es nicht koennen.

**Zum Urteil selbst, Review finding G-070.** Die erste Fassung berechnete
`gefeuert` und liess es dann aus `gut` heraus: Ein nicht ausgeloester
Audit-Trigger wurde als `NEIN` gedruckt und die Probe meldete trotzdem
`RESULT: PASS` - der zentrale Nachweis dieser Datei konnte falschgruen
ausgehen. Dazu kamen zwei Fehler, die einander verdeckt haetten: Der
Zaehlbefehl begann mit `RESET ROLE`, dessen Statuszeile `str.isdigit()`
scheitern laesst - jede psql-Sitzung ist ohnehin eine eigene Verbindung, das
`RESET` war ueberfluessig -, und ein blosser Zuwachs der Gesamtzahl haette
auch von einem fremden Ereignis kommen koennen.

Das Urteil liegt deshalb jetzt in `bewertung()`: eine reine Funktion ueber
`ERWARTET`, in der **jede** Zusicherung namentlich steht und ein fehlender
Schluessel ein Fehlschlag ist. Sie wird von `test_owner_probe_verdict.py`
lokal gegen ihre Negativfaelle gefahren - eine Probe, die nie gelaufen ist,
muss wenigstens in ihrer Bewertung geprueft sein.

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

AKTEUR = "SYSTEM-PROBE"
REQUEST_ID = "PROBE-G045-WRITE"
MARKE = "PROBE-G045"

# Jede Zusicherung, die diese Probe belegen soll, mit ihrem genauen Sollwert.
# Ein Schluessel, der im Ergebnis fehlt, ist ein Fehlschlag - nicht ein
# uebergangener Punkt. Genau daran ist die erste Fassung gescheitert.
ERWARTET = {
    "009 angewendet": "ja",
    "SECURITY DEFINER beim Superuser, nachher": "0",
    "Relationen im Besitz von workforce_owner": "0",
    "Schreibversuch als workforce_owner": "ok",
    "Eventzuwachs": "1",
    "Audit-Event mit Request-Id, Akteur, Typ und Operation": "1",
    "Trigger abschaltbar": "NEIN",
    "Abnahmetest 009": "PASS",
}


def bewertung(ergebnisse: list[tuple[str, str]]) -> tuple[bool, list[str]]:
    """(bestanden, Beanstandungen) - rein, ohne NAS, damit pruefbar.

    Ein fehlender Schluessel zaehlt als Beanstandung. Das ist der Kern von
    `G-070`: Ein Urteil, das nur die Punkte ansieht, die es findet, wird von
    einem ausgefallenen Schritt nicht rot, sondern still.
    """
    gemessen = dict(ergebnisse)
    beanstandungen: list[str] = []
    for schluessel, soll in ERWARTET.items():
        if schluessel not in gemessen:
            beanstandungen.append(f"{schluessel}: nicht gemessen")
        elif gemessen[schluessel] != soll:
            beanstandungen.append(
                f"{schluessel}: {gemessen[schluessel]!r} statt {soll!r}")
    return not beanstandungen, beanstandungen


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


def skalar(sql: str) -> str:
    """Der letzte Ausgabewert - psql schreibt Statuszeilen mit in denselben Strom."""
    ausgabe = psql(sql)
    zeilen = [z.strip() for z in ausgabe.splitlines() if z.strip()]
    return zeilen[-1] if zeilen else ""


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


def messen(ergebnisse: list[tuple[str, str]]) -> None:
    start()

    # 007 verlangt die beiden Login-Rollen; auf der NAS kommen sie aus dem
    # Secret-Store, hier aus Wegwerfwerten.
    psql("CREATE ROLE workforce_api LOGIN PASSWORD 'wegwerf1'")
    psql("CREATE ROLE workforce_backup LOGIN PASSWORD 'wegwerf2'")

    for datei in MIGRATIONEN:
        ausgabe = anwenden(datei)
        if "ERROR" in ausgabe:
            ergebnisse.append((f"Migration {datei}", f"FEHLER: {ausgabe[-200:]}"))
            return
    ergebnisse.append(("Ausgangsstand", f"{len(MIGRATIONEN)} Migrationen angewendet"))

    superuser_definer = (
        "SELECT count(*) FROM pg_proc p "
        "JOIN pg_namespace n ON n.oid = p.pronamespace "
        "JOIN pg_roles r ON r.oid = p.proowner "
        "WHERE n.nspname = 'workforce' AND p.prosecdef AND r.rolsuper")
    ergebnisse.append(("SECURITY DEFINER beim Superuser, vorher",
                       skalar(superuser_definer)))

    # --- 009 anwenden -------------------------------------------------------
    ausgabe = anwenden("009_bus_function_owner.sql")
    if "ERROR" in ausgabe:
        ergebnisse.append(("009 angewendet", f"FEHLER: {ausgabe[-200:]}"))
        return
    ergebnisse.append(("009 angewendet", "ja"))
    ergebnisse.append(("SECURITY DEFINER beim Superuser, nachher",
                       skalar(superuser_definer)))
    ergebnisse.append(("Relationen im Besitz von workforce_owner", skalar(
        "SELECT count(*) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "JOIN pg_roles r ON r.oid = c.relowner "
        "WHERE n.nspname IN ('workforce','public') AND r.rolname = 'workforce_owner'")))

    # --- Frage 2: feuert der Audit-Trigger unter workforce_owner? -----------
    # Das ist der Kern. workforce_owner hat auf bus_record_change kein
    # EXECUTE; laut Dokumentation wird das beim Ausloesen nicht geprueft.
    vor_events = skalar("SELECT count(*) FROM workforce.bus_events")

    # Der abschliessende SELECT belegt den Schreibvorgang aus den Daten heraus,
    # statt sich auf psqls Statuszeile zu verlassen. Er laeuft noch als
    # workforce_owner und braucht damit auch dessen SELECT-Recht.
    schreiben = psql(
        f"SET ROLE workforce_owner; "
        f"SELECT set_config('app.actor_id', '{AKTEUR}', true); "
        f"SELECT set_config('app.request_id', '{REQUEST_ID}', true); "
        f"UPDATE workforce.bus_channels SET source_ref = '{MARKE}' "
        f"WHERE project_id = 'START-UP'; "
        f"SELECT source_ref FROM workforce.bus_channels WHERE project_id = 'START-UP'")
    geschrieben = schreiben.splitlines()[-1].strip() if schreiben.strip() else ""
    ergebnisse.append(("Schreibversuch als workforce_owner",
                       "ok" if geschrieben == MARKE else schreiben[-200:]))

    # Jede psql-Sitzung ist eine eigene Verbindung; das SET ROLE oben ist hier
    # schon wieder weg. Ein `RESET ROLE` haette nur eine Statuszeile in den
    # Zaehlwert geschrieben - und genau daran waere die Auswertung gescheitert.
    nach_events = skalar("SELECT count(*) FROM workforce.bus_events")
    ergebnisse.append(("bus_events vorher/nachher", f"{vor_events} -> {nach_events}"))
    ergebnisse.append(("Eventzuwachs",
                       str(int(nach_events) - int(vor_events))
                       if vor_events.isdigit() and nach_events.isdigit()
                       else f"nicht numerisch: {vor_events!r} -> {nach_events!r}"))

    # Und der Zuwachs ist **dieses** Ereignis. Ein blosser Zaehlerstand waere
    # "irgendein Datensatz dieses Typs" - was die Auditregeln dieses Projekts
    # ausdruecklich nicht als Nachweis gelten lassen.
    ergebnisse.append((
        "Audit-Event mit Request-Id, Akteur, Typ und Operation",
        skalar("SELECT count(*) FROM workforce.bus_events "
               f"WHERE request_id = '{REQUEST_ID}' AND actor_id = '{AKTEUR}' "
               "AND record_type = 'CHANNEL' AND event_type = 'UPDATE'")))

    # --- Frage 3: kann er das Audit abschalten? -----------------------------
    abschalten = psql(
        "SET ROLE workforce_owner; "
        "ALTER TABLE workforce.bus_messages DISABLE TRIGGER USER")
    ergebnisse.append(("Trigger abschaltbar",
                       "NEIN" if "ERROR" in abschalten
                       else "JA - die Migration verfehlt ihren Zweck"))

    # --- Abnahmetest --------------------------------------------------------
    test = ssh(
        f"{DOCKER} exec {NAME} psql -U workforce_app -d workforce "
        f"-v ON_ERROR_STOP=1 -f /probe/tests/009_bus_function_owner_acceptance.sql 2>&1",
        check=False)
    ergebnisse.append(("Abnahmetest 009", "PASS" if "ERROR" not in test else test[-200:]))


def main() -> int:
    ergebnisse: list[tuple[str, str]] = []
    try:
        messen(ergebnisse)
    finally:
        aufraeumen()

    breite = max((len(k) for k, _ in ergebnisse), default=1)
    print("\n=== G-045 Eigentuemertrennung, Wegwerf-Container ===\n")
    for kennung, wert in ergebnisse:
        print(f"  {kennung.ljust(breite)}  {wert}")
    print()

    gut, beanstandungen = bewertung(ergebnisse)
    for zeile in beanstandungen:
        print(f"  FAIL: {zeile}")
    if beanstandungen:
        print()
    print("RESULT: PASS" if gut else "RESULT: FAIL")
    return 0 if gut else 1


if __name__ == "__main__":
    sys.exit(main())
