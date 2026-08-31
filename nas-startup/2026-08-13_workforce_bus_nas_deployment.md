# Workforce Bus v6 – NAS-Deployment und Datenbankabnahme

**Datum:** 2026-08-13  
**Ausführung:** Tobi und Gerd/Codex  
**Ziel:** `/docker/Startup`, Container-Manager-Projekt `startup`  
**Ergebnis:** `PASS` für Deployment, Migration, Datenbank-Sicherheitsmodell und Basisendpunkte; Kommunikationskanal weiterhin `DISABLED`

## Bestandswahrung

- Der alte Compose-/API-Quellstand wurde vor dem Austausch als `/docker/Startup/Versionen/Vor_v6_2026-08-13.zip` gesichert.
- `startup.env`, PostgreSQL 17 und das benannte Volume `workforce_database_v1` wurden nicht gelöscht oder ersetzt.
- Das bestehende v5-Image bleibt Rückfallstand.

## Deployment

- `compose.yaml`, Migration 002, Bus-Abnahmetest und der reale API-Quellordner wurden durch die geprüfte v6-Fassung ergänzt beziehungsweise ersetzt.
- Das Projekt wurde gestoppt, ohne Volume-Bereinigung neu erstellt und erfolgreich gebaut.
- Ergebnis: Datenbank und `startup-workforce-api:v6` gesund; `registry-migrate` regulär mit Exit-Code 0 beendet.

## Gefundener und behobener Fehler

Der erste reale Bus-Abnahmelauf brach bei der Credential-Widerrufsprüfung ab. Ursache war, dass der gemeinsame Versions-Trigger `bus_touch_versioned_row` das Feld `updated_at` erwartete, dieses Feld in `workforce.bus_credentials` aber fehlte.

Die Behebung wurde nicht durch Datenbank-Reset oder Testabschwächung vorgenommen:

1. Migration 002 enthält `updated_at` nun direkt für Neuinstallationen.
2. `003_workforce_bus_trigger_fix.sql` ergänzt und initialisiert das Feld bestandswahrend für bereits migrierte Installationen.
3. `compose.yaml` prüft und appliziert Migration 003 genau einmal.
4. Migration 003 lief auf dem NAS mit `BEGIN`, `ALTER TABLE`, `UPDATE 0`, `ALTER TABLE`, `INSERT 0 1`, `COMMIT` durch.

Der danach erreichte Audit-Zähler wurde anhand der tatsächlich ausgelösten kontrollierten Änderungen geprüft: fünf Nachrichten-, vier Task- und zwei Handoff-Ereignisse ergeben exakt elf attribuierte E2E-Auditereignisse. Der Test erwartet deshalb explizit genau elf statt eines unbegründeten Mindestwerts von zwölf.

## Vollständiger SQL-Abnahmetest

Ausgeführt im laufenden Datenbank-Container:

```text
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /opt/startup/tests/002_workforce_bus_acceptance.sql
```

Nachgewiesenes Ende:

```text
PASS: Workforce Bus identity, project scope, inbox/outbox, tasks, handoffs, acknowledgement, immutable payloads, redacted audit, idempotency, loop protection, revocation and fail-closed controls
ROLLBACK
```

Das abschließende `ROLLBACK` entfernt die kurzlebigen Test-Credentials, Nachrichten, Tasks und Handoffs vollständig.

## Betriebsprüfung nach dem Test

| Prüfung | Ergebnis |
|---|---|
| `/health` | `{"status":"ok"}` |
| `/db-check` | `{"database":"ok"}` |
| `/bus/v1/status` | API `v6`, Projekt `START-UP`, Migration `002_workforce_bus`, Kanal `DISABLED`, `max_hops=4`, `max_body_chars=8000` |
| Firewall | bestehende lokale TCP-8080-Regel unverändert aktiv |
| Produktive Bus-Credentials | keine angelegt |

## Verbleibendes Gate

Dieser Nachweis aktiviert den Kommunikationskanal nicht. Vor `TESTING` oder `ACTIVE` fehlen weiterhin:

- ein geprüfter HTTPS-Zugang;
- getrennte, kurzlebige Testzugänge für Karl, mindestens einen Fachmitarbeiter und Nora;
- der reale bidirektionale API-Test einschließlich Projektgrenze, Zustellung, Annahme, Antwort, Audit, Widerruf und Fail-Closed-Negativfällen;
- das abschließende Engineering-/Security-Review.

