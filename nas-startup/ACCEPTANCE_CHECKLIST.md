# PostgreSQL, Employee Registry und deaktivierter Workforce Bus – NAS-Abnahme

**Datum:** 2026-08-13  
**Prüfer:** Tobi (Ausführung), Gerd/Codex (Protokollauswertung)  
**Ergebnis:** `PASS` – Employee Registry, API v6, deaktivierte Workforce-Bus-Basis, Persistenz, Backup/Restore und DSM-Firewallgrenze abgenommen

| Prüfschritt | Erwartung | Nachweis | Ergebnis |
|---|---|---|---|
| Projektstart | Projekt `startup` startet ohne Fehler | Containerstatus: `db` und `workforce-api` grün; Migration regulär beendet | PASS |
| DB-Healthcheck | Dienst `db` wird `healthy` | Containerstatus grün | PASS |
| Bestehendes Volume | `workforce_database_v1` bleibt eingebunden; keine Neuanlage unter anderem Namen | unveränderte Volume-Deklaration und erfolgreiche bestehende DB/API | PASS |
| DB-Identität | Datenbank und Benutzer entsprechen unverändert `startup.env` | unveränderte Secret-Datei; Migration und API-Verbindung erfolgreich | PASS |
| Migration | `registry-migrate` endet genau mit Exit-Code 0 | Exportlog: `COMMIT` und `Employee Registry migration applied.` ohne Fehler | PASS |
| Registry-Schema | Schema `workforce`, Migration `001_employee_registry` | Migrationslog und Registry-Abnahmetest | PASS |
| Mitarbeiter | fünf dokumentierte Identitäten und fünf aktive `START-UP`-Mitgliedschaften | Registry-Abnahmetest | PASS |
| Registry-Schutz | ungültige ID und Hard Delete werden abgewiesen | negativer Registry-Abnahmetest | PASS |
| Registry-Audit | Versionierung, Actor/Request und Append-only funktionieren | Registry-Abnahmetest | PASS |
| API-Healthcheck | `workforce-api` wird `healthy`; `/health` und `/db-check` funktionieren | Containerstatus grün; beide Browserprüfungen `ok` | PASS |
| Netzgrenze DB | PostgreSQL besitzt keinen veröffentlichten Host-Port | Projekt-/Containerkonfiguration | PASS |
| Netzgrenze API | Port 8080 ist nur im vertrauenswürdigen lokalen Netz erreichbar | DSM-Regeln: lokales `/24` zulassen, danach alle übrigen Quellen verweigern; `/health` und `/db-check` danach `ok` | PASS |
| Persistenz | Testdatensatz bleibt nach kontrolliertem Neustart vorhanden | Registry nach DB-Stopp/-Start vorhanden und Dump in frische Testdatenbank wiederhergestellt | PASS |
| Secret-Hygiene | bestehende Secrets bleiben ausschließlich in `startup.env`/Secret-Ablage | `startup.env` unverändert; keine Secret-Werte protokolliert | PASS |
| Wiederanlauf | Dump-/Backup- und Restore-Weg dokumentiert oder getestet | Post-Migration-Dump statisch geprüft und in getrenntem PostgreSQL-17-Projekt erfolgreich wiederhergestellt | PASS |
| API-v6-Build | reales NAS-API-Quellverzeichnis baut als separates v6-Image | `startup-workforce-api:v6` gebaut und Container gesund | PASS |
| Bus-Migration | Migration 002 und bestandswahrende Korrektur 003 sind vorhanden | Migrationsmarker und realer 003-Lauf mit `COMMIT` | PASS |
| Bus-Sicherheitsmodell | Positiv-/Negativtest für Scope, Zustellung, Audit, Widerruf, Idempotenz und Fail Closed | `002_workforce_bus_acceptance.sql`: `PASS`, danach `ROLLBACK` | PASS |
| Bus-Basisendpunkt | Status meldet v6, `START-UP` und keine Aktivierung | `/bus/v1/status`: `channel_status=DISABLED` | PASS |

**Registry-Test im DB-Container:** `psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /opt/startup/tests/001_employee_registry_acceptance.sql`

**Nachweise:**

- `evidence/2026-08-13_registry_migration_and_acceptance.md`
- `evidence/2026-08-13_backup_dump_static_validation.md`
- `evidence/2026-08-13_isolated_restore_test.md`
- `evidence/2026-08-13_firewall_8080_validation.md`
- `evidence/2026-08-13_workforce_bus_nas_deployment.md`

## Freigaberegel

Alle Pflichtprüfungen der NAS-/Registry- und deaktivierten Bus-Basis sind `PASS`. Das erlaubt als nächsten Schritt HTTPS und den realen API-Ende-zu-Ende-Test, aktiviert aber weder den Workforce-Bus noch interne oder externe Kommunikationsrechte.
