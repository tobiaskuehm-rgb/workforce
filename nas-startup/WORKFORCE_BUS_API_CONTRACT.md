# Workforce Bus API v0.1 – Implementierungsvertrag

**Status:** Gültig für `workforce-api:v9` (Stand 2026-09-02). Geschrieben für `v6`; die hier beschriebenen Bus-Endpunkte haben sich seither nicht geändert. Dazugekommen sind seit `v7` die `/knowledge/v1`-Endpunkte — nicht Gegenstand dieses Vertrags, Migration `004` ist nicht angewendet —, und seit `v9` verlangt `/openapi.json` den API-Schlüssel (`G-040`). Kanal weiterhin `DISABLED`.

**Bezug:** `DEC-015`, `DEC-016`, `ENG-003`, `HO-020`

Die Zeile darüber hieß bis 2026-09-02 „in `workforce-api:v6` implementiert … HTTPS-/Real-E2E-Abnahme ausstehend" und war damit vier Versionen alt (`G-046`). Beides ist überholt: Der reale Lauf über HTTPS auf Port 8443 mit echten, kurzlebigen Token fand am 2026-08-31 statt, nachgewiesen in `evidence/2026-08-31_bus_realtest_karl_thorsten.md`. **Nicht** gelaufen ist dagegen das Ruby-Abnahmeskript `workforce-api/e2e_acceptance.rb` — es trägt den Hinweis inzwischen im eigenen Kopf.

Dieses Dokument ist **nicht datiert und wird deshalb als aktuell gelesen.** Wer eine Aussage darin nicht mehr halten kann, ändert sie hier, statt sie stehen zu lassen.

## Sicherheitsgrundsätze

- Nur Projekt `START-UP`; andere Projektwerte werden nicht still umgedeutet.
- Bus-Endpunkte funktionieren nur bei Kanalstatus `TESTING` beziehungsweise `ACTIVE`.
- Zugang über `Authorization: Bearer <opaque-token>`; der Klartext-Token wird nur im Arbeitsspeicher gehasht und weder gespeichert noch geloggt.
- Bus-Zugangsdaten werden ausschließlich über geprüfte HTTPS-Verbindungen übertragen. Der bisherige HTTP-Port 8080 bleibt bis dahin auf Health-/Datenbankprüfungen begrenzt.
- `X-Request-ID` ist für jede schreibende Anfrage Pflicht; `Idempotency-Key` ist für neue Nachrichten Pflicht.
- Die API ruft ausschließlich die kontrollierten `workforce.bus_*`-Funktionen auf und bietet keinen beliebigen SQL-Zugriff.
- Authorization-Header, Token, Token-Hash und vollständige Nachrichteninhalte werden nicht in das normale API-Protokoll geschrieben.
- Keine Endpunkte für externe Nachrichten, E-Mail, WhatsApp, Käufe, Verträge, Rollen-/Rechteverwaltung oder produktive Systemänderungen.
- Kanalaktivierung, Credential-Ausgabe und Allowlist-Änderungen sind kein normaler API-Endpunkt, sondern ein getrenntes, dokumentiertes Admin-Verfahren.

## Endpunkte

### Status

`GET /bus/v1/status`

Antwortet nur mit Migration, Projekt, Kanalstatus und maximaler Nachrichtengröße. Keine Mitarbeiter-, Credential- oder Nachrichteninhalte.

### Nachrichten

- `GET /bus/v1/messages?scope=INBOX|OUTBOX|PROJECT&limit=100`
- `POST /bus/v1/messages`
- `POST /bus/v1/messages/{message_id}/ack`

`PROJECT` ist nur für Karl und Nora erlaubt. Einträge mit `NEED_TO_KNOW` bleiben auch dort auf Absender und Empfänger begrenzt; `PROJECT_INTERNAL` ist für die projektweite Sicht freigegeben.

Beispiel für eine neue Nachricht:

```json
{
  "recipient_id": "AI-ENG-001",
  "subject": "Technikstatus",
  "body": "Bitte Registry- und Busstatus prüfen.",
  "action_class": "INTERNAL_REVIEW",
  "confidentiality": "NEED_TO_KNOW",
  "task_ref": "ENG-003",
  "handoff_ref": "HO-020",
  "parent_message_id": null
}
```

Die API erzeugt `message_id` und setzt den Absender ausschließlich aus der geprüften Credential-Identität, niemals aus dem Request-Body.

Annahme oder Ablehnung:

```json
{
  "decision": "ACCEPTED",
  "note": "Prüfung übernommen."
}
```

Nur der tatsächliche Empfänger darf bestätigen.

### Tasks

- `GET /bus/v1/tasks?scope=OWNED|CREATED|PROJECT&limit=100`
- `POST /bus/v1/tasks`
- `POST /bus/v1/tasks/{task_id}/transition`

Karl darf innerhalb `DEC-015` vollständig beschriebene `OPEN`-Tasks an Gerd, Anastasia und Thorsten koordinieren. Andere neue Tasks beginnen als `PENDING`. Der Owner bearbeitet bis `REVIEW`; der Ersteller schließt mit Evidenz als `DONE`.

### Handoffs

- `GET /bus/v1/handoffs?scope=INBOX|OUTBOX|PROJECT&limit=100`
- `POST /bus/v1/handoffs`
- `POST /bus/v1/handoffs/{handoff_id}/transition`

Ein Handoff dokumentiert Übergabe und Status. Er überträgt keine Berechtigung. Eine suspendierte Route bleibt trotz Handoff gesperrt.

## Antwort- und Fehlerlogik

| Situation | HTTP |
|---|---:|
| erfolgreich gelesen/erstellt/geändert | 200/201 |
| fehlende oder formal ungültige Eingabe | 400 |
| fehlender/ungültiger/abgelaufener/widerrufener Zugang | 401 |
| Identität, Projekt, Route, Scope oder Aktion nicht erlaubt | 403 |
| Datensatz nicht gefunden | 404 |
| Idempotenzkonflikt oder bereits finaler Zustand | 409 |
| Nachrichtenlänge überschritten | 413 |
| Schleifenlimit überschritten | 422 |
| Kanal `DISABLED`/`REVOKED` oder Datenbank nicht bereit | 503 |

Fehlerantworten enthalten eine stabile interne Fehlerkennung und die Request-ID, aber keine SQL-Anweisung, Tabellenstruktur, Zugangsdaten oder Stacktraces.

## Aktivierungsreihenfolge

1. Bestehenden API-Quellordner sichern und reviewen.
2. Endpunkte implementieren und automatisiert testen.
3. API-Image mit neuer Versionsnummer bauen; `v5` bleibt als Rückfallstand erhalten.
4. HTTPS-Zugang und Firewallgrenze prüfen.
5. Nur zeitlich begrenzte `ACCEPTANCE`-Credentials erzeugen.
6. Kanal auf `TESTING` setzen und den dokumentierten E2E-Test durchführen.
7. Testzugänge widerrufen und Kill Switch prüfen.
8. Erst nach `PASS` und Security-Review getrennte produktive Aktivierung entscheiden und dokumentieren.
