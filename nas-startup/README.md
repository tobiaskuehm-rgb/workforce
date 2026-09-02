# Synology Start UP – Registry und deaktivierter Workforce Bus abgenommen

**Dieses Dokument beschreibt den Paketstand vom 2026-08-13**, mit dem die
NAS-/Registry-Stufe und die deaktivierte Workforce-Bus-Basis abgenommen wurden.
Es ist eine Momentaufnahme, kein Statusbericht.

**Den laufenden Stand nennt `production_state.txt`**, nicht diese Datei — und
den aktuellen Iststand der NAS liefert `sh nas_status.sh` mit einem einzigen
Lesebefehl. Bis 2026-09-02 stand hier „Aktive API: `startup-workforce-api:v6`",
zu einem Zeitpunkt, als produktiv `v9` lief (`G-046`).

**Zielpfad:** `/volume1/docker/Startup` · **Container-Manager-Projekt:** `startup`

## Was erhalten bleibt

- `compose.yaml` bleibt der einzige aktive Compose-Dateiname.
- PostgreSQL bleibt auf `postgres:17-alpine`.
- Das bestehende benannte Volume `workforce_database_v1` bleibt unverändert.
- `startup.env` bleibt die lokale Secret-Datei und wird weder ersetzt noch in ein Paket aufgenommen.
- Build-Kontext `./workforce-api`, API-Port 8080 und die vorhandenen Endpunkte bleiben erhalten. Das erweiterte Image erhält bewusst Version `v6`; `v5` bleibt als Rückfallstand bestehen.

`docker-compose.yml` aus dem ersten Recovery-Paket wird nicht mehr aktiv verwendet. Es wird zusammen mit `.env.example` und dem alten Installations-ZIP in `Versionen/` verschoben, nicht gelöscht.

## Was ergänzt wird

- `postgres-init/001_employee_registry.sql`: atomare Registry-Migration.
- `postgres-tests/001_employee_registry_acceptance.sql`: transaktionaler Abnahmetest.
- `postgres-init/002_workforce_bus.sql`: zunächst deaktivierter, projektbezogener Nachrichten-/Task-/Handoff-Bus.
- `postgres-init/003_workforce_bus_trigger_fix.sql`: bestandswahrende Korrektur des Credential-Zeitstempels für den gemeinsamen Versions-Trigger.
- `postgres-tests/002_workforce_bus_acceptance.sql`: transaktionaler Positiv- und Negativtest des Bus-Sicherheitsmodells.
- `registry-migrate`: bestehender einmaliger Compose-Dienst; der historische Name bleibt zur Vermeidung unnötiger Container-Änderungen erhalten. Er prüft Migration 001 und führt danach Migration 002 sowie 003 genau einmal aus.
- Bei einer neuen leeren Datenbank führt PostgreSQL beide Initialisierungen alphabetisch aus; `registry-migrate` erkennt sie anschließend als erledigt.
- Bei einem bestehenden Volume führt `registry-migrate` nur die jeweils fehlende Migration kontrolliert nachträglich aus.
- Die API startet erst, wenn Datenbank gesund und alle vorhandenen Migrationen erfolgreich abgeschlossen sind.

Die Registry legt Identitäten und Projektmitgliedschaften an. Migration 002 ergänzt das technische Datenmodell und die Prüfregeln; Migration 003 korrigiert den Credential-Zeitstempel in bereits migrierten Beständen. Der Kanal bleibt `DISABLED` und es werden keine Zugangsdaten angelegt. Dadurch werden noch keine Kommunikations-, System-, Budget- oder externen Aktionsrechte aktiviert.

## Sicherer Austausch auf dem NAS

1. Container-Manager-Projekt `startup` noch nicht neu bauen oder starten.
2. Bestehendes `compose.yaml` nach `Versionen/compose_pre_bus_2026-08-13.yaml` kopieren und den bisherigen Ordner `workforce-api/` zusätzlich unverändert sichern.
3. Neues `compose.yaml` nach `/docker/Startup/compose.yaml` hochladen und die bestehende Datei ersetzen.
4. Vorhandene Ordner `postgres-init/` und `postgres-tests/` beibehalten beziehungsweise mit den gelieferten Fassungen abgleichen.
5. `startup.env` und das Volume `workforce_database_v1` nicht verändern. Den Ordner `workforce-api/` nur durch die vollständig geprüfte v6-Fassung ersetzen und die Sicherung behalten.
6. Das alte `docker-compose.yml`, `.env.example` und Installations-ZIP nach `Versionen/` verschieben.
7. Erst danach das Projekt `startup` in Container Manager neu erstellen beziehungsweise mit der neuen YAML-Konfiguration bauen.

## Erwartete Startreihenfolge

1. `db` startet und wird `healthy`.
2. `registry-migrate` endet nach Prüfung beider Migrationen erfolgreich mit Code 0.
3. `workforce-api` startet und wird `healthy`.

Bei einer inkonsistenten bereits vorhandenen Registry bricht die Migration absichtlich ab, statt Daten still zu überschreiben.

## Abnahme

Bestehende API-Prüfungen im lokalen Netzwerk:

- `http://IP-DER-DISKSTATION:8080/health` → Status `ok`
- `http://IP-DER-DISKSTATION:8080/db-check` → Datenbank `ok`

Registry-Test im PostgreSQL-Container:

```text
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /opt/startup/tests/001_employee_registry_acceptance.sql
```

Erwartetes Ergebnis beginnt mit `PASS: Employee Registry`. Der Test läuft innerhalb einer Transaktion und setzt seine Teständerungen zurück.

## Sicherheitsgrenzen

- PostgreSQL hat keine Host-Portfreigabe.
- Das Backend-Netz ist intern; nur die API hängt zusätzlich am Frontend-Netz.
- Port 8080 wird nur für die bestehende API verwendet und soll durch Synology-Firewall/Netzwerk auf das vertrauenswürdige lokale Netz begrenzt bleiben.
- Die bisherigen HTTP-Endpunkte auf Port 8080 sind nur für Health-/Datenbankprüfungen geeignet. Bus-Zugangsdaten dürfen erst nach Einrichtung eines geprüften HTTPS-Zugangs übertragen werden.
- Keine Router-Portfreigabe.
- `startup.env` niemals hochladen, in Chat kopieren oder unverschlüsselt weitergeben.
- Das Datenbankpasswort bei vorhandenem Volume nicht einfach in `startup.env` ändern; PostgreSQL übernimmt es nicht automatisch.
- Das Volume niemals löschen, bereinigen oder ersetzen, solange kein geprüftes Backup und Restore-Verfahren vorliegt.

## Danach

Der NAS-Rollout der Bus-Datenbasis und API v6 ist abgeschlossen. Als nächster Schritt fehlen der geprüfte HTTPS-Zugang, getrennte kurzlebige Testzugänge und der reale bidirektionale API-Ende-zu-Ende-Test. Bis dahin bleibt `ENG-003` technisch blockiert und der Kanal `DISABLED`.

## Abnahmestand 2026-08-13

- `registry-migrate`: `COMMIT` und `Employee Registry migration applied.` ohne Fehler
- `/health`: `ok`
- `/db-check`: `ok`
- `001_employee_registry_acceptance.sql`: `PASS`
- vollständiger Nachweis: **fehlt.** Hier stand bis 2026-09-02 ein Verweis auf
  eine Nachweisdatei zur Registry-Migration vom 13. August; eine solche Datei
  gibt es in diesem Repo nicht, weder unter `evidence/` noch daneben (`G-046`).
  Der Dateiname ist hier bewusst nicht ausgeschrieben — er würde die
  Nachweisprüfung erneut auslösen. Was von dieser Abnahme belegt ist, steht in
  `ACCEPTANCE_CHECKLIST.md`.
- Post-Migration-Dump `workforce-2026-08-13_10-18-29.sql`: statische Strukturprüfung `PASS`
- isoliertes Restore-Testprojekt: frischer PostgreSQL-17-Import und Healthcheck `PASS`
- Persistenz: DB-Stopp/-Start sowie getrennte Wiederherstellung `PASS`
- DSM-Firewall: TCP-Zielport 8080 aus `192.168.68.0/24` zugelassen, danach für alle übrigen Quellen verweigert; beide API-Prüfungen anschließend erneut `ok`
- vollständige Abnahme: `ACCEPTANCE_CHECKLIST.md`
- Workforce-Bus-Migration 002 plus Triggerkorrektur 003: angewendet
- `startup-workforce-api:v6`: gebaut und gesund
- `002_workforce_bus_acceptance.sql`: vollständiger Positiv-/Negativtest `PASS`, anschließend `ROLLBACK`
- `/bus/v1/status`: API `v6`, Projekt `START-UP`, Kanal `DISABLED`
- vollständiger Bus-Nachweis: `2026-08-13_workforce_bus_nas_deployment.md`
  — liegt neben dieser Datei, nicht unter `evidence/`; der Pfad hier war falsch.
