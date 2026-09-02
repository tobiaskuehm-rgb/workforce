# Kill-Switch-Dokumentation und Testplan Karl ↔ Thorsten

**Stand: 2026-08-31, historisch.** Beim Schreiben rein planerisch — kein Kill-Switch aktiviert, keine Migration ausgeführt, kein Container verändert. Diese Sätze beschreiben den Zustand von damals und **nicht den von heute**: Der geplante Test hat am 2026-08-31 stattgefunden (`evidence/2026-08-31_bus_realtest_karl_thorsten.md`), und seit dem Phase-4-Fenster am 2026-09-01 sind die Migrationen `005`–`007` angewendet. Den laufenden Stand nennt `production_state.txt` (`G-046`).

**Bezug:** `DEC-015`, `DEC-016`, `ENG-003`, `DG-003`, `HO-020`

---

## Teil 1 — Kill-Switch der Workforce-Bus-API

### Wo er sitzt

Der Kill-Switch ist zweistufig implementiert (Defense-in-Depth), nicht nur ein einzelnes Flag.

**1) Datenbank-Ebene — Quelle der Wahrheit**

`postgres-init/002_workforce_bus.sql:8-27` — Tabelle `workforce.bus_channels`:

```sql
channel_status text NOT NULL DEFAULT 'DISABLED',
CONSTRAINT bus_channels_status CHECK (channel_status IN ('DISABLED', 'TESTING', 'ACTIVE', 'REVOKED')),
```

Seed-Zeile für Projekt `START-UP` (`002_workforce_bus.sql:1491-1502`):

```sql
INSERT INTO workforce.bus_channels (project_id, channel_status, ...)
VALUES ('START-UP', 'DISABLED', 4, 8000, 'DEC-016/ENG-003');
```

Jede Bus-Funktion (`bus_send_message`, `bus_create_task`, `bus_create_handoff`, …) ruft zuerst `workforce.bus_resolve_credential()` auf (`002_workforce_bus.sql:576-616`). Diese Funktion prüft unabhängig vom API-Layer erneut:

```sql
AND (
    (ch.channel_status = 'TESTING' AND c.credential_scope = 'ACCEPTANCE')
    OR (ch.channel_status = 'ACTIVE' AND c.credential_scope = 'PRODUCTION')
)
```

Kein Treffer → `BUS_AUTH_FAILED` (SQLSTATE `42501`). Selbst bei einem fehlerhaften API-Layer bleibt die DB fail-closed.

**2) API-Ebene — zusätzliches Gate vor jedem Bus-Request**

`workforce-api/app.py:114-129` (`require_bus_ready`), aufgerufen aus `require_bus_token` (`app.py:132-142`), als Dependency an jedem schreibenden/lesenden `/bus/v1/*`-Endpunkt außer `/bus/v1/status` (bewusst offen, aber inhaltsleer):

```python
if row is None or row[0] not in {"TESTING", "ACTIVE"}:
    raise HTTPException(status_code=503, detail="BUS_CHANNEL_NOT_ACTIVE")
```

### Zwei verschiedene „Aus“-Zustände

- `DISABLED` — Normalzustand vor Aktivierung, **reversibel**.
- `REVOKED` — echter Notaus-Schalter, aber **permanent**. Der Trigger `workforce.bus_guard_channel_update` (`002_workforce_bus.sql:405-423`) verweigert jeden Rückweg aus `REVOKED`:

```sql
IF OLD.channel_status = 'REVOKED' AND NEW.channel_status <> 'REVOKED' THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'BUS_CHANNEL_REVOCATION_FINAL';
```

Das wird im Acceptance-Test aktiv negativ geprüft (`postgres-tests/002_workforce_bus_acceptance.sql:643-689`, dort mit `app.request_id = 'TEST-BUS-KILL-SWITCH'`). Für Tests ist daher `DISABLED` der richtige Zielzustand nach Abschluss, nicht `REVOKED`.

### Aktuelle Konfiguration (Ist-Zustand)

- `channel_status = 'DISABLED'` für Projekt `START-UP` (Default + explizite Seed-Zeile).
- `workforce.bus_credentials` ist leer (0 Zeilen) — die Migration legt bewusst keine Zugangsdaten an.
- `BUS_REQUIRE_HTTPS: "true"` in `compose.yaml:96`, plus `BUS_TRUSTED_PROXY_CIDRS: "172.20.0.1/32"` (`compose.yaml:99`) für den Synology-Reverse-Proxy.
- Zuletzt bestätigt am 2026-08-13 (`WORKFORCE_BUS_ROLLOUT.md`, `ACCEPTANCE_CHECKLIST.md`) sowie per tokenfreiem Netzcheck am 2026-08-21 (`telegram-connector/README.md`, `DEC-025`): `/bus/v1/status` → `channel_status=DISABLED`.

### Konkrete Schritte zur Aktivierung (nicht ausgeführt, nur dokumentiert)

Es gibt keinen API-Endpunkt dafür. Laut `WORKFORCE_BUS_API_CONTRACT.md`: *„Kanalaktivierung, Credential-Ausgabe und Allowlist-Änderungen sind kein normaler API-Endpunkt, sondern ein getrenntes, dokumentiertes Admin-Verfahren.“* Das exakte Muster ist im Acceptance-Test vorgeführt (`postgres-tests/002_workforce_bus_acceptance.sql:74-89`):

1. `UPDATE workforce.bus_channels SET channel_status = 'TESTING' WHERE project_id = 'START-UP';` — direktes, manuelles SQL, kein API-Call.
2. Pro Testperson eine Zeile in `workforce.bus_credentials` einfügen: `credential_scope = 'ACCEPTANCE'`, `token_hash` (SHA-256 des Klartext-Tokens), `expires_at` zwingend gesetzt (CHECK-Constraint `002_workforce_bus.sql:106-108`).
3. Reale Bearer-Tokens lokal generieren (z. B. `openssl rand -hex 32`); nur der Hash landet in der DB, das Klartext-Token wird nie gespeichert oder geloggt (`app.py:142`).
4. HTTPS-Pfad sicherstellen (Reverse Proxy mit geprüftem Zertifikat) — über den bisherigen unverschlüsselten Port 8080 dürfen laut Contract keine Bus-Credentials übertragen werden.
5. Nach dem Test: Credentials auf `REVOKED` setzen (`credential_status`, mit `revocation_reason`) und Kanal zurück auf `DISABLED`.

Laut `WORKFORCE_BUS_ROLLOUT.md` (Abschnitt „Aktivierungsgate“) fehlen vor einer echten Aktivierung noch: geprüfter HTTPS-Zugang, getrennte Testzugänge für Karl/Fachmitarbeiter/Nora, der reale bidirektionale Test, Negativtests (außerhalb Projekt, privilegierte Aktionen, nach Widerruf, Schleifenlimit) sowie ein dokumentiertes Security-Review.

---

## Teil 2 — Plan: Erster bidirektionaler Bus-Test Karl (SAO-001) ↔ Thorsten (RAS-001)

### Ausgangslage laut Seed-Migration

Karl und Thorsten sind bereits in `bus_member_capabilities` und in der `bus_route_allowlist` für alle drei Routentypen (`MESSAGE`, `TASK`, `HANDOFF`) in beide Richtungen freigegeben (`002_workforce_bus.sql:1505-1552`, Seed-Filter `employee_id IN ('AI-ENG-001', 'RAS-001', 'PEO-001', 'SAO-001', 'EAC-001')`). An der Routing-Freigabe muss für diesen engen Test **nichts** geändert werden — sie existiert bereits.

### Schrittfolge

**Schritt 0 — Freigabe**
Analog zum Telegram-Realtest-Muster (`DEC-024`/`DEC-025`/`DEC-026`): eine explizite, eng gescopte Entscheidung nur für „Karl ↔ Thorsten, Kanal höchstens `TESTING`, Ablaufzeit ≤ 60 Min, definierter Cleanup“ — keine generelle Bus-Aktivierung.

**Schritt 1 — Preflight**
Frisches DB-Backup, `/health`, `/db-check`, `/bus/v1/status` prüfen (`DISABLED` erwartet), HTTPS-Erreichbarkeit über den Reverse Proxy bestätigen (Muster: tokenfreier Netzcheck wie `DEC-025`, diesmal aber mit Fokus auf den authentifizierten Pfad).

**Schritt 2 — Kurzlebige Zugänge**
Zwei Tokens lokal erzeugen, Kanal auf `TESTING`, zwei `ACCEPTANCE`-Credentials einfügen (`CRED-ACCEPT-KARL` → `SAO-001`, `CRED-ACCEPT-THORSTEN` → `RAS-001`), `expires_at` kurz halten (30–60 Min, wie beim Telegram-Realtest).

**Schritt 3 — Bidirektionaler Nachrichtenfluss über die echte HTTPS-API**
Bewusst über die reale API, nicht direkt über die SQL-Funktion, damit der reale Transportweg mitgetestet wird:

- Karl → Thorsten: `POST /bus/v1/messages` mit `Authorization: Bearer <Karl-Token>`, `X-Request-ID`, `Idempotency-Key`, `recipient_id=RAS-001`.
- Thorsten: `GET /bus/v1/messages?scope=INBOX`, dann `POST /bus/v1/messages/{id}/ack` (`ACCEPTED`).
- Thorsten → Karl: Antwort mit `parent_message_id` gesetzt.
- Karl liest Inbox, bestätigt.

**Schritt 4 — Negativ-/Grenztests**
Analog zum bestehenden Acceptance-SQL, aber über die echte API: falscher/fremder Empfänger → 403, abgelaufenes/ungültiges Token → 401, fehlende `Idempotency-Key`/`X-Request-ID` → 400, Wiederholung mit gleichem Idempotency-Key → kein Duplikat.

**Schritt 5 — Audit-Nachweis**
`workforce.bus_events` für diese Test-Request-IDs prüfen, Nachweisdokument im bestehenden `evidence/`-Muster ablegen.

**Schritt 6 — Cleanup (zwingend)**
Beide Credentials auf `REVOKED` setzen, Kanal zurück auf `DISABLED` (nicht `REVOKED` — das wäre final, siehe Teil 1), erneuter Statuscheck.

### Noch fehlende Teile

- **Agenten-Client**: Es existiert aktuell keine Laufzeit-Komponente, die Karl bzw. Thorsten als KI-Agenten autonom gegen die Bus-API sprechen lässt. Recherche im Repository (`grep` nach `SAO-001`/`RAS-001` in `*.py`) findet nur Referenzen im `telegram-connector` (`test_telegram_connector.py`, `local_demo.py`) — das ist ein separater Transport-Adapter für Telegram, kein Bus-Client für Karl/Thorsten. Für Schritt 3 oben braucht es entweder manuelle curl-/Skript-Aufrufe (Mensch-in-der-Schleife) oder einen neu zu bauenden schlanken Agenten-Client, der Token, `X-Request-ID` und `Idempotency-Key` korrekt setzt.
- **Credentials**: Aktuell 0 Zeilen in `bus_credentials` — für Karl und Thorsten existiert noch nichts; müssen laut Schritt 2 frisch angelegt werden.
- **HTTPS-Reverse-Proxy für den echten Credential-Pfad**: Der bisherige Netzcheck (2026-08-21, `DEC-025`) hat nur tokenfrei die drei GET-Endpunkte bei `DISABLED` geprüft, nicht den authentifizierten `TESTING`-Pfad mit echtem Bearer-Token.
- **Runbook/Skript-Paket**: Für den reinen Bus-Test gibt es bislang kein Äquivalent zu `telegram-connector/compose.identity/prepare/run/cleanup.yaml`. Der vorhandene `postgres-tests/002_workforce_bus_acceptance.sql` endet mit `ROLLBACK` und ist daher kein echter API-Realtest, sondern nur ein transaktionaler DB-Test.
- **Formale Freigabe-Entscheidung**: Eine DEC-Nummer für genau diesen engen Testscope (Schritt 0) existiert noch nicht.

---

## Update 2026-08-31 — ausführbares Runbook-Paket erstellt

Auf Basis dieses Plans existiert jetzt `../BUS_REALTEST_KARL_THORSTEN_RUNBOOK.md` mit dem zugehörigen Paket `bus-realtest/` (Prepare-/Run-/Cleanup-Compose-Dienste, SQL-Skripte, ein schlankes HTTPS-Testskript als Ersatz für den fehlenden Agenten-Client, plus lokal ausführbare Tests ohne Netzwerkzugriff). Das deckt die vorher genannten fehlenden Teile ab:

- **Agenten-Client** → `bus-realtest/bus_realtest_run.py` (führt den echten bidirektionalen HTTPS-Nachrichtenwechsel; kein autonomer KI-Agent, aber ein lauffähiger Ersatz für den manuellen curl-Weg).
- **Credentials** → `bus-realtest/bus_realtest_prepare.sql` legt zwei kurzlebige `ACCEPTANCE`-Zugänge für `SAO-001`/`RAS-001` an.
- **Routing-Freigaben** → keine Änderung nötig, bereits seit Migration 002 vorhanden; wird im Prepare-Skript nur noch einmal geprüft, nicht neu angelegt.

Noch offen: HTTPS-Reverse-Proxy-Verbindungsdaten in `bus-realtest.env` eintragen, eine DEC-Nummer für `BUS_REALTEST_SOURCE_REF` vergeben, und die eigentliche Ausführung auf der NAS (siehe Runbook, Schritte 1–5). Bisher wurde nichts davon ausgeführt — dieses Dokument bleibt bis zur echten Durchführung weiterhin planerisch.

---

*Erstellt als reine Planungs-/Dokumentationsgrundlage. Keine Migration, kein Kill-Switch-Wechsel, kein Container-Neustart wurde im Zuge dieser Dokumentation durchgeführt.*
