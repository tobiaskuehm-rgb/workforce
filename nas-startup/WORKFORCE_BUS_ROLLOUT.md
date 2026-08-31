# Workforce Bus v0.1 – NAS-Rollout und Abnahme

**Stand:** 2026-08-13  
**Ziel:** Datenbankbasis für `ENG-003` kontrolliert ergänzen, ohne den Kommunikationskanal produktiv zu aktivieren.  
**NAS-Pfad:** `/docker/Startup`  
**Container-Manager-Projekt:** `startup`

## Was dieses Paket macht

- ergänzt die Migration `002_workforce_bus.sql`;
- ergänzt die bestandswahrende Korrekturmigration `003_workforce_bus_trigger_fix.sql`;
- ergänzt den transaktionalen Test `002_workforce_bus_acceptance.sql`;
- erweitert den bestehenden Einmaldienst `registry-migrate`, damit er Migration 001, 002 und 003 in der richtigen Reihenfolge prüft beziehungsweise ausführt;
- legt projektbezogene Identitäten, Inbox/Outbox-Nachrichten, Tasks, Handoffs, Zustell-/Annahmestatus, Audit, Allowlist, Widerruf, Dubletten- und Schleifenschutz an;
- hält den Kanal nach der Migration ausdrücklich auf `DISABLED`;
- erzeugt keine produktiven Zugangsdaten.

## Was unverändert bleibt

- `startup.env` und das darin enthaltene Datenbankpasswort;
- das produktive Volume `workforce_database_v1`;
- PostgreSQL 17;
- der Ordner `workforce-api/` und das Image `startup-workforce-api:v5`;
- Port 8080 und die bereits geprüften Firewall-Regeln;
- die vorhandenen Registry-Daten.

## Vor dem Austausch

- [ ] Alle drei vorhandenen Dienste sind im bisherigen Stand gesund beziehungsweise der Einmaldienst ist erfolgreich beendet.
- [ ] Ein frisches SQL-Backup liegt in `Startup-Backups` und ist größer als 0 Byte.
- [ ] `compose.yaml` wurde nach `Versionen/compose_pre_bus_2026-08-13.yaml` kopiert.
- [ ] Der bisherige Ordner `workforce-api/` wurde unverändert gesichert; das bisherige Image `startup-workforce-api:v5` bleibt als Rückfallstand vorhanden.
- [ ] `startup.env` und `workforce_database_v1` werden nicht gelöscht, bereinigt oder ersetzt.

## Dateien auf die NAS kopieren

1. `postgres-init/002_workforce_bus.sql` nach `/docker/Startup/postgres-init/` hochladen.
2. `postgres-tests/002_workforce_bus_acceptance.sql` nach `/docker/Startup/postgres-tests/` hochladen.
3. Den vollständig gelieferten Ordner `workforce-api/` nach `/docker/Startup/workforce-api/` kopieren und dabei `Dockerfile` sowie `app.py` durch die v6-Fassung ersetzen; `test_app.py` ist nur lokaler Prüfnachweis und muss nicht auf die NAS.
4. Die neue `compose.yaml` nach `/docker/Startup/compose.yaml` hochladen und nur die bisherige Compose-Datei ersetzen.
5. Kontrollieren, dass in `postgres-init/` jetzt `001_employee_registry.sql`, `002_workforce_bus.sql` und `003_workforce_bus_trigger_fix.sql` liegen.
6. Kontrollieren, dass in `postgres-tests/` jetzt beide Abnahmetests liegen.

## Projekt neu erstellen

1. Projekt `startup` stoppen.
2. Projekt über die vorhandene `compose.yaml` neu erstellen/aufbauen.
3. Erwarteter Zustand:
   - `db` wird grün/gesund;
   - `registry-migrate` endet einmalig erfolgreich und darf danach orange/beendet erscheinen;
   - `workforce-api` wird grün/gesund.
4. Im Protokoll von `registry-migrate` muss entweder
   `Workforce Bus migration applied; channel remains DISABLED.` oder
   `Workforce Bus migration already applied.` stehen. Danach muss die Korrekturmigration 003 angewendet oder als bereits angewendet erkannt werden.

Bei einem Fehler nicht bereinigen und nicht das Volume löschen. Projekt stoppen, Protokoll sichern und den vorherigen Compose-Stand aus `Versionen/` wieder einsetzen.

## Abnahmetest

Im Terminal des laufenden Datenbank-Containers ausführen:

```text
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /opt/startup/tests/002_workforce_bus_acceptance.sql
```

Erwartetes Ende:

```text
PASS: Workforce Bus identity, project scope, inbox/outbox, tasks, handoffs, acknowledgement, immutable payloads, redacted audit, idempotency, loop protection, revocation and fail-closed controls
ROLLBACK
```

Der Test erzeugt nur kurzlebige Testzugänge und Testnachrichten innerhalb einer Transaktion. Durch `ROLLBACK` bleiben sie nicht in der produktiven Datenbank.

## Danach prüfen

```text
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT channel_status FROM workforce.bus_channels WHERE project_id='START-UP';"
```

Erwartet: `DISABLED`

```text
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT count(*) FROM workforce.bus_credentials;"
```

Erwartet: `0`

Zusätzlich im Browser erneut prüfen:

- `/health` → `ok`
- `/db-check` → Datenbank `ok`

## Aktivierungsgate

Ein bestandener SQL-Test allein aktiviert `ENG-003` nicht. Vor `TESTING` beziehungsweise `ACTIVE` fehlen noch:

1. Erweiterung und Review der bestehenden API;
2. ein projektbezogener HTTPS-Zugang, zum Beispiel über Synology Reverse Proxy mit geprüftem Zertifikat; über den bisherigen unverschlüsselten Port 8080 dürfen keine Bus-Zugangsdaten übertragen werden;
3. getrennte, nur lokal gespeicherte Testzugänge für Karl, mindestens einen Fachmitarbeiter und Nora;
4. realer bidirektionaler API-Test Karl ↔ Fachmitarbeiter ↔ Nora;
5. Nachweis von Projektgrenze, Zustellung, Annahme, Antwort und Audit;
6. negative Tests außerhalb `START-UP`, für privilegierte/externe Aktionen, nach Widerruf sowie jenseits des Schleifenlimits;
7. dokumentiertes Engineering-/Security-Review.

Bis alle Punkte bestanden sind, bleibt `DG-003` blockiert und der Kanal `DISABLED`.

## Reales Ergebnis vom 2026-08-13

- Quellstand vor v6 als `/docker/Startup/Versionen/Vor_v6_2026-08-13.zip` gesichert.
- Produktives Volume und `startup.env` unverändert erhalten.
- `startup-workforce-api:v6` erfolgreich gebaut; Datenbank und API gesund, Einmaldienst regulär beendet.
- Der erste Abnahmelauf fand den fehlenden `updated_at`-Zeitstempel in `bus_credentials`; kein Testfehler wurde übergangen.
- Migration `003_workforce_bus_trigger_fix` bestandswahrend angewendet und Installationsablauf für Neu- und Bestandsinstallationen korrigiert.
- Wiederholter vollständiger SQL-Test endet mit dem erwarteten `PASS` und `ROLLBACK`.
- `/health`, `/db-check` und `/bus/v1/status` erneut erfolgreich; Kanalstatus weiterhin `DISABLED`.

Vollständiger Nachweis: `evidence/2026-08-13_workforce_bus_nas_deployment.md`.
