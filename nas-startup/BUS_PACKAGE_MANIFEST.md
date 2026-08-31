# Paketmanifest – NAS Workforce Bus Complete v3

**Erstellt:** 2026-08-13  
**Zielpfad:** `/docker/Startup`

## Enthalten

| Datei | Ziel | Wirkung |
|---|---|---|
| `compose.yaml` | `/docker/Startup/compose.yaml` | Migrationsdienst prüft Migration 001, 002 und 003 |
| `postgres-init/002_workforce_bus.sql` | `/docker/Startup/postgres-init/` | legt den deaktivierten Bus und seine Sicherheitskontrollen an |
| `postgres-init/003_workforce_bus_trigger_fix.sql` | `/docker/Startup/postgres-init/` | ergänzt bei bestehenden Installationen den fehlenden Credential-Zeitstempel für den Versions-Trigger |
| `postgres-tests/002_workforce_bus_acceptance.sql` | `/docker/Startup/postgres-tests/` | führt den rückrollbaren Positiv-/Negativtest aus |
| `workforce-api/Dockerfile` | `/docker/Startup/workforce-api/` | baut das neue Image `startup-workforce-api:v6` mit festgelegten Abhängigkeiten |
| `workforce-api/app.py` | `/docker/Startup/workforce-api/` | erhält bestehende Funktionen und ergänzt den projektbegrenzten Bus-Zugang |
| `workforce-api/test_app.py` | lokaler Prüfnachweis | 14 automatisierte API-Sicherheits- und Regressionstests |
| `WORKFORCE_BUS_ROLLOUT.md` | Dokumentation | Schritt-für-Schritt-Rollout und Aktivierungsgate |
| `WORKFORCE_BUS_API_CONTRACT.md` | Dokumentation | verbindliche Grenzen für die spätere Erweiterung der bestehenden API |
| `ACCEPTANCE_CHECKLIST.md` | Dokumentation | zusammengefasster realer NAS-Abnahmestand |
| `evidence/2026-08-13_workforce_bus_nas_deployment.md` | Dokumentation | detaillierter Deployment-, Fehlerkorrektur- und Prüfnachweis |
| `README.md` | Dokumentation | technischer Gesamtstand |

## Nicht enthalten

- `startup.env` oder andere Secrets;
- produktive oder bleibende Testzugänge;
- Datenbankdump oder produktives Volume;
- eine produktive Aktivierung des Kommunikationskanals.

## Sicherheitszustand nach Migration

- Projekt: `START-UP`
- Kanalstatus: `DISABLED`
- produktive Credentials: `0`
- externe und privilegierte Aktionsklassen: nicht zulässig
- Audit: append-only, Actor- und Request-Kontext zwingend
- Credential-Hashes: aus allgemeinem Audit-Payload entfernt
- Revocation: endgültig; Kanal-Kill-Switch kann nicht still zurückgesetzt werden

## Reale NAS-Abnahme

- `startup-workforce-api:v6` gebaut und gesund gestartet;
- Migration 002 und Korrekturmigration 003 angewendet;
- vollständiger transaktionaler Workforce-Bus-Test: `PASS` und `ROLLBACK`;
- `/health`: `ok`;
- `/db-check`: `ok`;
- `/bus/v1/status`: API `v6`, Projekt `START-UP`, Kanal `DISABLED`.

Die technische Kommunikationsaktivierung bleibt bis zum geprüften HTTPS-Zugang und realen bidirektionalen API-Ende-zu-Ende-Nachweis gesperrt.
