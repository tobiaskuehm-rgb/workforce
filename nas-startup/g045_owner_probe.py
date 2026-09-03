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
import time

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

# Die letzte Aussage des Abnahmetests. Ohne sie ist ein Exitcode 0 nur
# "psql hat nichts zu meckern gehabt" - zum Beispiel, weil die Datei gar
# nicht ankam (`G-076`).
ABNAHME_MARKER = "Bus function owner acceptance: PASS"

# Der Negativtest "kann der Eigentuemer das Audit abschalten" braucht eine
# gebundene Ablehnung, keinen beliebigen Fehlschlag. `CLAUDE.md` haelt das seit
# `G-014` fest - "irgendein Fehler kam zurueck" ist kein bestandener
# Negativtest -, und die erste Fassung dieser Probe hat trotzdem jeden
# Prozessfehler als "Zugriff verweigert" gewertet: ein weggeraeumter Container,
# eine abgerissene SSH-Sitzung, ein Tippfehler im Tabellennamen oder eine
# fehlende Rolle haetten den Nachweis erbracht, um den es hier geht.
#
# PostgreSQL weist `ALTER TABLE ... DISABLE TRIGGER` durch einen Nicht-
# Eigentuemer mit `insufficient_privilege` ab. Die Probe faengt die Ausnahme
# und druckt die **tatsaechliche** SQLSTATE, statt eine zu behaupten; erwartet
# wird genau `42501`. Kommt eine andere, faellt die Probe auf und nennt sie.
TRIGGER_ERWARTETE_SQLSTATE = "42501"
TRIGGER_ABGELEHNT = "PROBE_TRIGGER_DENIED_" + TRIGGER_ERWARTETE_SQLSTATE
TRIGGER_ERLAUBT = "PROBE_TRIGGER_ALLOWED"

# Der echte Durchlauf. Kein Geheimnis: `bus_authenticate` vergleicht den
# uebergebenen Wert mit dem gespeicherten, es ist ein Nachschlagewert in einem
# Wegwerf-Container und nirgendwo sonst gueltig.
PROBE_HASH = "a" * 64
PROBE_MSG_ID = "MSG-PROBE-G045-ROUNDTRIP"
PROBE_IDEM = "IDEM-PROBE-G045-ROUNDTRIP"
PROBE_SENDER = "SAO-001"
PROBE_RECIPIENT = "AI-ENG-001"
REQUEST_ID_SEND = "PROBE-G045-SEND"

# Jede Zusicherung, die diese Probe belegen soll, mit ihrem genauen Sollwert.
# Ein Schluessel, der im Ergebnis fehlt, ist ein Fehlschlag - nicht ein
# uebergangener Punkt. Genau daran ist die erste Fassung gescheitert.
ERWARTET = {
    "009 angewendet": "ja",
    "SECURITY DEFINER beim Superuser, nachher": "0",
    "Relationen im Besitz von workforce_owner": "0",
    # Der Kern, und er hat sich am 2026-09-03 geaendert. Vorher stand hier ein
    # roher `UPDATE workforce.bus_channels` unter `SET ROLE workforce_owner` -
    # eine Tabelle, auf die 009 der Rolle nur `SELECT` gibt. Der Lauf haette
    # mit `42501` geendet und sich gelesen wie "die Allowlist ist zu eng"; die
    # schnelle Reparatur im Fenster waere ein `UPDATE`-Grant gewesen, also
    # genau die Verbreiterung, gegen die `G-071` gebaut wurde
    # (Vertretungsreview, `SV-2026-09-03-01`).
    #
    # Und die Kopfzeile dieser Datei fragt "laufen die Funktionen danach ohne
    # Superuser weiter?" - gemessen wurde bis dahin keine einzige von ihnen
    # (`SV-2026-09-03-02`). Jetzt laeuft ein echter `bus_send_message` als
    # `workforce_api`. Das prueft in einem Zug: die Allowlist auf dem Weg, den
    # die Funktion wirklich nimmt, den Audit-Trigger unter dem neuen
    # Eigentuemer, und die offene Sequenzfrage aus `009` Abschnitt 3c - denn
    # `bus_events` traegt einen Identity-Schluessel.
    "Kanal und Credential vorbereitet": "ok",
    "bus_send_message als workforce_api": "ok",
    "Eventzuwachs": "1",
    "Audit-Event mit Request-Id, Akteur, Typ und Operation": "1",
    "Trigger abschaltbar": "NEIN - abgewiesen mit SQLSTATE 42501",
    # Die Integrationsgegenprobe zu `G-074`, und sie hat zwei Haelften. Die
    # erste belegt, dass die Voreinstellung wirklich existiert: PostgreSQL
    # erteilt `USAGE` auf `public` an die Pseudorolle `PUBLIC`, also meldet
    # `has_schema_privilege` fuer jede Rolle `t`. Genau daran waere mein
    # erster Abnahmetest auf jeder frischen Instanz gescheitert. Die zweite
    # zeigt, dass 009 trotzdem keinen **direkten** Eintrag hinterlaesst - die
    # Aussage, die die Migration wirklich macht. Ohne die erste Haelfte waere
    # die zweite gruen, ohne dass jemand wuesste warum.
    "public-USAGE ueber PUBLIC (Voreinstellung)": "t",
    "direkte Schema-Grants ausserhalb workforce": "0",
    "Abnahmetest 009": "ok",
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


def ssh(command: str) -> tuple[int, str]:
    """(Exitcode, Ausgabe). Beides, immer.

    Review finding G-076. Die erste Fassung gab bei `check=False` nur den Text
    zurueck, und der Aufrufer entschied ueber `"ERROR" not in ausgabe`. Damit
    haetten `psql: error: connection ...` (klein geschrieben),
    `Error response from daemon ...` mit anderem Wortlaut, ein Exit 127 oder
    eine leere Ausgabe als bestandener Schritt gegolten. Der Exitcode ist die
    einzige Auskunft, die nicht von einer Wortwahl abhaengt - also wird er
    zurueckgegeben und ausgewertet.
    """
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=600", HOST, command],
        capture_output=True, text=True,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def lauf_ergebnis(code: int, ausgabe: str, marker: str | None = None) -> str:
    """"ok" nur bei Exitcode 0 und - wo verlangt - eindeutigem Schlussmarker.

    Rein und ohne NAS, damit `test_owner_probe_verdict.py` die Negativfaelle
    lokal fahren kann. Eine leere Ausgabe wird benannt statt weggekuerzt: Sie
    ist der Fall, in dem eine Textpruefung am staerksten luegt.
    """
    schwanz = ausgabe.strip()[-200:] or "(keine Ausgabe)"
    if code != 0:
        return f"Exitcode {code}: {schwanz}"
    if marker is not None and marker not in ausgabe:
        return f"Schlussmarker fehlt: {schwanz}"
    return "ok"


def trigger_urteil(code: int, ausgabe: str) -> str:
    """Hat PostgreSQL das Abschalten mit der erwarteten SQLSTATE abgelehnt?

    Rein und ohne NAS, damit die Negativfaelle lokal laufen. Drei Ausgaenge,
    und nur der erste ist ein bestandener Nachweis:

      * abgelehnt mit `42501` - der Eigentuemer kommt an das Audit nicht heran
      * durchgelassen - die Migration verfehlt ihren Zweck
      * alles andere - der Versuch hat gar nicht stattgefunden

    Der dritte Fall ist der, den die erste Fassung als Erfolg gewertet hat.
    """
    if code != 0:
        return f"unbestimmt: Exitcode {code}: {ausgabe.strip()[-160:] or '(keine Ausgabe)'}"
    if TRIGGER_ABGELEHNT in ausgabe:
        return f"NEIN - abgewiesen mit SQLSTATE {TRIGGER_ERWARTETE_SQLSTATE}"
    if TRIGGER_ERLAUBT in ausgabe:
        return "JA - die Migration verfehlt ihren Zweck"
    if "PROBE_TRIGGER_DENIED_" in ausgabe:
        fremd = ausgabe.split("PROBE_TRIGGER_DENIED_", 1)[1].split()[0].strip()
        return f"abgewiesen, aber mit SQLSTATE {fremd} statt {TRIGGER_ERWARTETE_SQLSTATE}"
    return f"unbestimmt: kein Marker: {ausgabe.strip()[-160:] or '(keine Ausgabe)'}"


def psql(sql: str) -> tuple[int, str]:
    escaped = sql.replace("'", "'\\''")
    return ssh(f"{DOCKER} exec {NAME} psql -U workforce_app -d workforce -Atc '{escaped}' 2>&1")


def skalar(sql: str) -> str:
    """Der letzte Ausgabewert - psql schreibt Statuszeilen in denselben Strom.

    Bei einem Fehlschlag wird das Ergebnis ausdruecklich als Fehler
    gekennzeichnet, damit es unter keinen Umstaenden wie eine Zahl aussieht.
    """
    code, ausgabe = psql(sql)
    if code != 0:
        return f"FEHLER (Exitcode {code}): {ausgabe[-160:] or '(keine Ausgabe)'}"
    zeilen = [z.strip() for z in ausgabe.splitlines() if z.strip()]
    return zeilen[-1] if zeilen else "(keine Ausgabe)"


def aufraeumen() -> None:
    # Gezielt, nie ein prune: der wirkt NAS-weit (G-038).
    ssh(f"{DOCKER} rm -f {NAME} >/dev/null 2>&1")


def start() -> None:
    aufraeumen()
    code, ausgabe = ssh(
        f"{DOCKER} run -d --name {NAME} "
        f"-e POSTGRES_USER=workforce_app "        # Regel 15: wie in der Produktion
        f"-e POSTGRES_DB=workforce "
        f"-e POSTGRES_PASSWORD=wegwerf-nur-fuer-diese-probe "
        f"-v {SRC}:/probe/migrations:ro -v {TESTS}:/probe/tests:ro "
        f"{IMAGE} >/dev/null"
    )
    if code != 0:
        raise RuntimeError(f"Probe-Container startete nicht (Exitcode {code}): {ausgabe[-200:]}")
    for _ in range(60):
        if "accepting connections" in ssh(
                f"{DOCKER} exec {NAME} pg_isready -U workforce_app -d workforce 2>&1")[1]:
            return
        # Lokal warten, nicht per `ssh "sleep 2"`. Die erste Fassung baute
        # dafuer je Runde eine eigene SSH-Verbindung auf - eine Sitzung zur
        # NAS, um nichts zu tun. Das kostet mehr Zeit als das Warten selbst
        # und macht die Wartezeit von der Netzlage abhaengig.
        time.sleep(2)
    raise RuntimeError("Probe-Datenbank wurde nicht bereit")


def anwenden(datei: str) -> str:
    """"ok" oder eine benannte Fehlerursache. Dieselbe Auswertung wie beim
    Abnahmetest (`G-076`): `ON_ERROR_STOP=1` laesst psql mit einem Exitcode
    ungleich 0 enden, und der entscheidet - nicht die Frage, ob irgendwo das
    Wort ERROR steht."""
    return lauf_ergebnis(*ssh(
        f"{DOCKER} exec {NAME} psql -U workforce_app -d workforce "
        f"-v ON_ERROR_STOP=1 -f /probe/migrations/{datei} 2>&1"))


def messen(ergebnisse: list[tuple[str, str]]) -> None:
    start()

    # 007 verlangt die beiden Login-Rollen; auf der NAS kommen sie aus dem
    # Secret-Store, hier aus Wegwerfwerten.
    #
    # Der Rueckgabewert wird geprueft. Die erste Fassung warf ihn weg - genau
    # die Klasse, die `G-076` an anderer Stelle getroffen hat. Scheitert eine
    # Rollenanlage, bricht spaeter `007` ab und die Meldung zeigt auf die
    # Migration statt auf die Ursache.
    for rolle, passwort in (("workforce_api", "wegwerf1"),
                            ("workforce_backup", "wegwerf2")):
        code, ausgabe = psql(f"CREATE ROLE {rolle} LOGIN PASSWORD '{passwort}'")
        if code != 0:
            ergebnisse.append((f"Rolle {rolle}", lauf_ergebnis(code, ausgabe)))
            return

    for datei in MIGRATIONEN:
        ergebnis = anwenden(datei)
        if ergebnis != "ok":
            ergebnisse.append((f"Migration {datei}", ergebnis))
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
    ergebnis = anwenden("009_bus_function_owner.sql")
    ergebnisse.append(("009 angewendet", "ja" if ergebnis == "ok" else ergebnis))
    if ergebnis != "ok":
        return
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

    # Kanal und Credential, damit `bus_authenticate` ueberhaupt aufloest. Beides
    # als `workforce_app`, also nicht Teil der Messung - nur ihre Voraussetzung.
    # `002` seedet die Routenmatrix bereits, `SAO-001 -> AI-ENG-001` existiert.
    vorbereiten_code, vorbereiten = psql(
        f"SELECT set_config('app.actor_id', '{AKTEUR}', true); "
        f"SELECT set_config('app.request_id', 'PROBE-G045-PREPARE', true); "
        f"UPDATE workforce.bus_channels SET channel_status = 'TESTING', "
        f"source_ref = '{MARKE}' WHERE project_id = 'START-UP'; "
        f"INSERT INTO workforce.bus_credentials (credential_id, project_id, "
        f"employee_id, token_hash, credential_scope, credential_status, "
        f"source_ref, expires_at) VALUES ('CRED-PROBE-G045', 'START-UP', "
        f"'{PROBE_SENDER}', '{PROBE_HASH}', 'ACCEPTANCE', 'ACTIVE', '{MARKE}', "
        f"clock_timestamp() + interval '1 hour'); "
        f"SELECT channel_status FROM workforce.bus_channels "
        f"WHERE project_id = 'START-UP'")
    bereit = vorbereiten.splitlines()[-1].strip() if vorbereiten.strip() else ""
    ergebnisse.append(("Kanal und Credential vorbereitet",
                       "ok" if vorbereiten_code == 0 and bereit == "TESTING"
                       else lauf_ergebnis(vorbereiten_code, vorbereiten, "TESTING")))
    if vorbereiten_code != 0 or bereit != "TESTING":
        return

    # **Der eigentliche Nachweis.** Ein echter Aufruf einer der zwoelf
    # Funktionen, als `workforce_api` - also auf dem Weg, den die API im
    # Betrieb nimmt. Die Funktion ist SECURITY DEFINER und laeuft nach 009 als
    # `workforce_owner`; sie schreibt in `bus_messages` und loest dabei
    # `bus_record_change` aus, das als Aufrufer laeuft. Geht das durch, ist
    # belegt: die Allowlist reicht, der Audit-Trigger feuert, und der
    # Identity-Schluessel von `bus_events` braucht kein Sequenzrecht.
    #
    # Der Rueckgabewert wird gelesen, nicht die Statuszeile: Die Funktion gibt
    # die Nachrichtenzeile zurueck, also muss die Nachrichten-Id herauskommen.
    aufruf_code, aufruf = psql(
        f"SET ROLE workforce_api; "
        f"SELECT set_config('app.actor_id', '{PROBE_SENDER}', true); "
        f"SELECT set_config('app.request_id', '{REQUEST_ID_SEND}', true); "
        f"SELECT (workforce.bus_send_message('{PROBE_HASH}', '{REQUEST_ID_SEND}', "
        f"'{PROBE_MSG_ID}', 'START-UP', '{PROBE_RECIPIENT}', '{PROBE_IDEM}', "
        f"'Probe G045', 'Ein Aufruf, kein roher Schreibvorgang.', "
        f"'INTERNAL_COMMUNICATION', 'NEED_TO_KNOW', NULL, NULL, NULL)).message_id")
    gesendet = aufruf.splitlines()[-1].strip() if aufruf.strip() else ""
    ergebnisse.append((
        "bus_send_message als workforce_api",
        "ok" if aufruf_code == 0 and gesendet == PROBE_MSG_ID
        else lauf_ergebnis(aufruf_code, aufruf, PROBE_MSG_ID)))

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
    # ausdruecklich nicht als Nachweis gelten lassen. Gebunden wird an
    # Request-Id, Akteur, Datensatztyp und Operation der **Nachricht**.
    ergebnisse.append((
        "Audit-Event mit Request-Id, Akteur, Typ und Operation",
        skalar("SELECT count(*) FROM workforce.bus_events "
               f"WHERE request_id = '{REQUEST_ID_SEND}' AND actor_id = '{PROBE_SENDER}' "
               f"AND record_type = 'MESSAGE' AND event_type = 'INSERT' "
               f"AND record_key = '{PROBE_MSG_ID}'")))

    # --- G-074: die Gegenprobe zur Schemafreigabe ---------------------------
    ergebnisse.append(("public-USAGE ueber PUBLIC (Voreinstellung)", skalar(
        "SELECT has_schema_privilege('workforce_owner', 'public', 'USAGE')")))
    ergebnisse.append(("direkte Schema-Grants ausserhalb workforce", skalar(
        "SELECT count(*) FROM pg_namespace n "
        "CROSS JOIN LATERAL aclexplode(n.nspacl) AS a "
        "JOIN pg_roles r ON r.oid = a.grantee "
        "WHERE r.rolname = 'workforce_owner' AND n.nspname <> 'workforce'")))

    # --- Frage 3: kann er das Audit abschalten? -----------------------------
    # Hier ist der Fehlschlag das erwuenschte Ergebnis - und genau deshalb
    # muss er **gebunden** sein. Der Aufruf laeuft erfolgreich durch (Exitcode
    # 0) und meldet in der Ausgabe, ob die Anweisung durchging oder mit welcher
    # SQLSTATE sie abgewiesen wurde. Ein Container-, Verbindungs- oder
    # Tippfehler hat dann weder Exitcode 0 noch einen der beiden Marker.
    abschalt_code, abschalten = psql(
        "SET ROLE workforce_owner; "
        "DO $x$ BEGIN "
        "EXECUTE 'ALTER TABLE workforce.bus_messages DISABLE TRIGGER USER'; "
        f"RAISE NOTICE '{TRIGGER_ERLAUBT}'; "
        "EXCEPTION WHEN OTHERS THEN "
        "RAISE NOTICE 'PROBE_TRIGGER_DENIED_%', SQLSTATE; "
        "END $x$;")
    ergebnisse.append(("Trigger abschaltbar",
                       trigger_urteil(abschalt_code, abschalten)))

    # --- Abnahmetest --------------------------------------------------------
    # Exitcode **und** der eindeutige Schlussmarker, den der Test als letzte
    # Aussage schreibt (`G-076`). Ein Transport- oder Containerfehler kann so
    # nicht mehr als bestandener SQL-Abnahmetest durchgehen: Er hat entweder
    # keinen Exitcode 0 oder er hat den Marker nicht.
    ergebnisse.append(("Abnahmetest 009", lauf_ergebnis(*ssh(
        f"{DOCKER} exec {NAME} psql -U workforce_app -d workforce "
        f"-v ON_ERROR_STOP=1 -f /probe/tests/009_bus_function_owner_acceptance.sql 2>&1"),
        ABNAHME_MARKER)))


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
