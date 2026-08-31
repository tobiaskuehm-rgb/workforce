# Nachweis: Bus-Realtest Karl ↔ Thorsten und Negativtests

**Datum:** 2026-08-31
**Quellreferenz:** `DEC-027/ENG-003`
**Durchführung:** per SSH und `sudo docker compose` direkt auf der NAS, nicht über die DSM-Oberfläche
**Ergebnis:** alle vier Schritte `PASS`; Kanal nach Abschluss wieder `DISABLED`

Dieses Dokument schließt die Punkte 4 und 6 des Aktivierungsgates aus `WORKFORCE_BUS_ROLLOUT.md`.

## Ausgangszustand

| Prüfung | Ergebnis |
|---|---|
| `startup-db-1` | `Up (healthy)` |
| `startup-workforce-api-1` | `Up (healthy)`, API `v6` |
| `/health` | `{"status":"ok"}` |
| `/db-check` | `{"database":"ok"}` |
| `/bus/v1/status` | `channel_status: DISABLED` |
| Frisches DB-Backup | `workforce-2026-08-31_02-05-01.sql`, 192 KB |
| Neue Ports auf Router/NAS | keine |

## Vorgeschalteter Erreichbarkeitstest

Vor jeder Zustandsänderung lief ein tokenfreier Probe-Container mit derselben festen Quelladresse `172.31.254.2` im isolierten Netz `172.31.254.0/29`, der ausschließlich die drei öffentlichen GET-Endpunkte aufruft.

**Erster Lauf — vor der Firewall-Regel:**

```text
FAIL /health       -> URLError: <urlopen error timed out>
FAIL /db-check     -> URLError: <urlopen error timed out>
FAIL /bus/v1/status -> URLError: <urlopen error timed out>
```

Damit war belegt, dass die DSM-Firewall das Testsubnetz blockt — **bevor** ein Credential erzeugt oder der Kanal umgestellt wurde. Nach Anlegen der temporären Regel (TCP 8443, Quelle `172.31.254.2/32`, `Zulassen`, oberhalb der Verweigern-Regeln):

```text
PASS /health        -> 200 {"status":"ok"}
PASS /db-check      -> 200 {"database":"ok"}
PASS /bus/v1/status -> 200 {... "channel_status":"DISABLED" ...}
```

Dieser Vorabtest war im Runbook nicht vorgesehen. Er sollte dort als fester Schritt aufgenommen werden: Ohne ihn wäre der Kanal auf `TESTING` gestanden und zwei Credentials wären ausgegeben gewesen, bevor der erste HTTPS-Aufruf in einen Timeout gelaufen wäre.

## Schritt 3 — Vorbereitung

```text
PASS: short-lived token created at /run/startup-bus-secrets/bus_token_karl.
PASS: short-lived token created at /run/startup-bus-secrets/bus_token_thorsten.
INSERT 0 2
UPDATE 1
 result | channel_status | employee_id | credential_scope | credential_status | credential_unexpired
 PASS   | TESTING        | RAS-001     | ACCEPTANCE       | ACTIVE            | t
 PASS   | TESTING        | SAO-001     | ACCEPTANCE       | ACTIVE            | t
```

Ablaufzeitpunkt beider Zugänge: `2026-08-31 11:31 UTC`, rund 30 Minuten Gültigkeit.

## Schritt 4 — Bidirektionaler Realtest (Gate-Punkt 4)

`"result": "PASS"` mit siebenteiligem Transcript:

| # | Schritt | Nachricht |
|---:|---|---|
| 1 | `status_check` | `channel_status: TESTING` |
| 2 | `karl_sends_message` | `MSG-8117FBD9FA7C4BBFFB0C14BACE2F0A94` |
| 3 | `thorsten_reads_inbox` | dieselbe ID gefunden |
| 4 | `thorsten_acknowledges` | `ACCEPTED` |
| 5 | `thorsten_sends_reply` | `MSG-73BEAF3AD1115949A484AD7387C72F9D` |
| 6 | `karl_reads_inbox` | Antwort gefunden |
| 7 | `karl_acknowledges` | `ACCEPTED` |

Damit sind Projektgrenze, Zustellung, Annahme, Antwort und Audit über den realen HTTPS-Weg belegt — nicht nur transaktional in SQL.

## Schritt 4b — Negativtests (Gate-Punkt 6)

`"result": "PASS"`, `"cases_total": 20`, `"cases_failed": 0`. Jeder Fall wurde nicht nur auf den Statuscode, sondern auch auf die stabile Fehlerkennung geprüft; „aus dem falschen Grund abgelehnt" zählt als Fehlschlag.

| Bereich | Fall | Ergebnis |
|---|---|---|
| Auth | unbekanntes Token | 401 `BUS_AUTH_FAILED` |
| Auth | zu kurzes Token | 401 `BUS_BEARER_TOKEN_REQUIRED` |
| Auth | kein Header | 401 `BUS_BEARER_TOKEN_REQUIRED` |
| Header | ohne `Idempotency-Key` | 400 `BUS_IDEMPOTENCY_KEY_REQUIRED` |
| Header | ohne `X-Request-ID` | 400 `BUS_REQUEST_ID_REQUIRED` |
| Form | `scope=EVERYTHING` | 400 `BUS_REQUEST_INVALID` |
| Form | untergeschobenes `sender_id` | 400 `BUS_REQUEST_INVALID` |
| Routing | Karl an Karl | 403 `BUS_SELF_ROUTE_DENIED` |
| Routing | Empfänger `ZZZ-999` | 403 `BUS_RECIPIENT_NOT_ACTIVE` |
| Routing | Thorsten liest `scope=PROJECT` | 403 `BUS_PROJECT_READ_DENIED` |
| Ack | Absender bestätigt selbst | 403 `BUS_ACK_DENIED` |
| Ack | unbekannte `message_id` | 403 `BUS_ACK_DENIED` |
| Ack | regulär durch Empfänger | 200 |
| Ack | gleiche Entscheidung erneut | 200 (idempotent) |
| Ack | `ACCEPTED` dann `REJECTED` | 409 `BUS_ACK_ALREADY_FINAL` |
| Idempotenz | gleicher Key, gleicher Inhalt | dieselbe `message_id` |
| Idempotenz | gleicher Key, anderer Inhalt | 409 `BUS_IDEMPOTENCY_CONFLICT` |
| Grenze | Body 8001 Zeichen | 413 `BUS_BODY_TOO_LARGE` |
| Grenze | Antwortkette `hop_count` 5 | 422 `BUS_LOOP_LIMIT_EXCEEDED` |

Hervorzuheben: Eine unbekannte `message_id` wird mit `BUS_ACK_DENIED` beantwortet und **nicht** mit 404. Der Bus verrät damit nicht, ob eine Nachrichten-ID existiert. Das ist im SQL so angelegt (`002_workforce_bus.sql`, `bus_acknowledge_message`: `IF NOT FOUND OR v_message.recipient_id <> v_actor_id`) und hält über den realen Weg.

## Schritt 5 — Bereinigung

```text
UPDATE 2
UPDATE 1
 result | channel_status | employee_id | credential_status | active_unexpired_credentials_total
 PASS   | DISABLED       | RAS-001     | REVOKED           | 0
 PASS   | DISABLED       | SAO-001     | REVOKED           | 0
```

Nachgelagert erledigt:

- Beide Token-Dateien in `bus-realtest/secrets/` gelöscht; nur `.keep` verbleibt.
- Alle vier temporären Compose-Projekte entfernt; keine Testcontainer, keine Testnetze verblieben.
- `/health`, `/db-check`, `/bus/v1/status` erneut geprüft — Kanal wieder `DISABLED`.
- Produktivstack durchgehend `Up (healthy)`, kein Neustart, Volume und `startup.env` unberührt.
- Temporäre Firewall-Regel für `172.31.254.2/32` auf TCP 8443 nach dem Test wieder entfernt.

## Beobachtung für das Runbook

Das Subnetz `172.31.254.0/29` bleibt nach `docker compose up --abort-on-container-exit` weiterhin belegt, weil das Netz nicht mit abgebaut wird. Der darauffolgende Lauf scheitert dann mit `Pool overlaps with other one on this address space`. Zwischen den Schritten 4, 4b und 5 ist daher jeweils ein `docker compose -f <datei> down` nötig. In der DSM-Oberfläche entspricht das dem Entfernen des jeweiligen Projekts vor dem Anlegen des nächsten.

## Was dieser Nachweis nicht abdeckt

- **Negativtest nach Widerruf bei laufendem Kanal.** Nach dem Cleanup steht der Kanal auf `DISABLED`, wodurch jeder Bus-Endpunkt schon vor der Tokenprüfung mit 503 `BUS_CHANNEL_NOT_ACTIVE` antwortet. Ein sauberer 401-Nachweis nach Widerruf braucht einen eigenen Zwischenschritt, der genau ein Credential widerruft, während der Kanal noch `TESTING` ist. Offen.
- **Projektgrenze über die API.** `BUS_PROJECT_ID` ist in `workforce-api/app.py:17` fest verdrahtet und wird nicht aus dem Request übernommen; ein fremdes Projekt ist über die API konstruktiv nicht adressierbar. Auf SQL-Ebene ist die Grenze in `postgres-tests/002_workforce_bus_acceptance.sql` geprüft.
- **Dauerbetrieb.** Dieser Lauf war ein einmaliger Test unter `TESTING`. Er begründet keine Freigabe für `ACTIVE`.

Die im Test erzeugten Nachrichten, Bestätigungen und Audit-Einträge bleiben absichtlich in PostgreSQL erhalten. Das ist ein Nachweis, kein aktives Recht.
