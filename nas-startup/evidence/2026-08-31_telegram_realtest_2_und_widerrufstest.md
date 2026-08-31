# Nachweis: Telegram-Realtest 2 und Bus-Widerrufstest

**Datum:** 2026-08-31
**Freigaben:** `DEC-026/ENG-007` (Telegram), `DEC-027/ENG-003` (Bus)
**Ergebnis:** beide `PASS`; Kanal nach Abschluss wieder `DISABLED`, 0 aktive Zugänge

Zwei getrennte Läufe in einem gemeinsamen Firewall-Fenster. Beide nutzen dieselbe feste Quelladresse `172.31.254.2` und liefen daher nacheinander, nie gleichzeitig.

---

## Teil 1 — Widerrufstest (Aktivierungsgate Punkt 6, Befund F7)

Der letzte offene Nachweis aus dem Security-Review: „widerrufenes Credential ⇒ 401". Nach dem regulären Cleanup steht der Kanal auf `DISABLED`, und dann antwortet jeder Endpunkt schon vor der Tokenprüfung mit 503 — der Nachweis braucht deshalb einen eigenen Zwischenschritt bei laufendem `TESTING`.

`bus_revoketest.sql` widerruft gezielt **nur** Thorstens Zugang und lässt Karls ausdrücklich `ACTIVE`:

```text
 result | channel_status | employee_id | credential_id                    | credential_status
 PASS   | TESTING        | RAS-001     | CRED-ACCEPT-THORSTEN-20260831-F7 | REVOKED
 PASS   | TESTING        | SAO-001     | CRED-ACCEPT-KARL-20260831-F7     | ACTIVE
```

Anschließend über die echte HTTPS-API:

| Fall | Erwartet | Ergebnis |
|---|---|---|
| `channel_still_testing` | `TESTING` | **PASS** |
| `revoked_credential_refused` | 401 `BUS_AUTH_FAILED` | **PASS** |
| `untouched_credential_still_works` | 200 | **PASS** |

Der dritte Fall trägt den Beweis: Ein Kanalausfall würde beide Tokens gleichermaßen abweisen. Erst weil Karls Zugang weiterhin 200 liefert, ist belegt, dass die Ablehnung aus der Credential-Prüfung stammt und nicht aus dem Kill Switch.

**Damit ist Aktivierungsgate Punkt 6 vollständig.**

---

## Teil 2 — Telegram-Realtest 2

### Vorbedingungen

| Prüfung | Ergebnis |
|---|---|
| Lokale Connector-Tests | 25/25 `OK` |
| Preflight gegen Produktiv-DB (`READ ONLY`, `ROLLBACK`) | `PASS` |
| Kanal / aktive Credentials | `DISABLED` / `0` |
| Alte Identität `CEO-TG-001` | `REVOKED` |
| `CEO-TG-002`, `ENG-TG-REALTEST-002` | noch nicht vorhanden |
| Ziel `AI-ENG-001` | aktiv |
| Frisches DB-Backup | `workforce-2026-08-31_02-05-01.sql`, 192 KB |

### Bot und Identität

Neuer Testbot über `@BotFather`; Token ausschließlich als Datei auf der NAS, nie in Chat, Quelltext oder Git. Die Identitäts-Prüfung ergab genau einen privaten Chat:

```text
{"identities": [{"chat_id": …, "chat_type": "private", "user_id": …}], "status": "ok"}
```

`chat_type=private` ist Bedingung; Gruppen werden abgewiesen. Die numerischen IDs stehen nur lokal in `telegram-realtest-2.env` (Modus 600) und bewusst nicht in diesem Nachweis.

### Vorbereitung

```text
 PASS | TESTING | CEO-TG-002 | PARTICIPANT | PROPOSE | Senden=t | Handoff=f | ACCEPTANCE | ACTIVE | unverfallen | Routen=2
```

`CEO-TG-002` ist eine technische Acceptance-Identität — ausdrücklich kein Mitarbeiter und keine CEO-Imitation. Handoff-Recht bewusst `false`.

### Durchführung

Zwei Nachrichten im privaten Bot-Chat, sonst nichts:

| Gesendet | Antwort |
|---|---|
| `/status` | `Kanal=TESTING` |
| `/task AI-ENG-001 ENG-TG-REALTEST-002 \| Telegram-NAS-Realtest 2 \| Technische PENDING-Bestätigung ohne automatische Bearbeitung` | `PENDING ENG-TG-REALTEST-002 für AI-ENG-001 registriert.` |

### Nachweis in der Datenbank

```text
task_id             | ENG-TG-REALTEST-002
creator_id          | CEO-TG-002
owner_id            | AI-ENG-001
task_status         | PENDING
source_ref          | DEC-026/ENG-007
completion_evidence | (leer)
version             | 1
```

Audit (`workforce.bus_events`), beide mit Akteur `CEO-TG-002`:

- **196** — `TASK` `INSERT`, `ENG-TG-REALTEST-002`, Request `TG-<update>-TASK`
- **197** — `MESSAGE` `INSERT`, `DELIVERED` an `AI-ENG-001`, `hop_count 0`, `action_class INTERNAL_COORDINATION`, `confidentiality NEED_TO_KNOW`, Idempotenzschlüssel aus der Telegram-Update-ID

`completion_evidence` ist leer und der Status blieb `PENDING`: Es wurde nichts automatisch bearbeitet, genau wie im Scope vorgesehen.

**Damit ist die Kette Telegram → NAS → Workforce Bus → PostgreSQL erstmals durchgängig belegt.**

### Rückbau

```text
 PASS | DISABLED | Credential=REVOKED | Capability=REVOKED | Membership=REVOKED | Identity=REVOKED | aktive Credentials=0
```

Zusätzlich: Connector gestoppt, Schalter zurück auf `ENABLED=false` / `KILL_SWITCH=true`, alle v2-Projekte und das Volume `telegram_realtest_state_v2` entfernt, Workforce- und Bot-Token-Datei gelöscht. Endprüfung: API `v7` gesund, Kanal `DISABLED`, 0 aktive Credentials, Produktivstack durchgehend `Up (healthy)` ohne Neustart.

Das Volume `startup-telegram-run_telegram_realtest_state_v1` aus dem abgebrochenen `DEC-024`-Versuch bleibt absichtlich erhalten — das README verlangt, dass die `…-001`-Belege unverändert bleiben.

---

## Unterwegs behobene Defekte

Vier Probleme, die den Lauf blockiert hätten und vorher niemandem aufgefallen waren:

**1. Falscher Reverse-Proxy-Host in vier Telegram-Dateien.** `192-168-68-77` statt `-78`. Im Bus-Paket war das am selben Tag korrigiert, im Connector nicht nachgezogen worden. Der Realtest hätte die API nicht erreicht.

**2. Das Bus-Realtest-Paket war nur einmal ausführbar.** Prepare legt Credentials mit festen IDs an, Cleanup setzt sie auf `REVOKED` — und der Trigger `bus_guard_credential_update` verbietet jede Reaktivierung (`BUS_CREDENTIAL_REVOCATION_FINAL`). Ein zweiter Lauf scheiterte am Primärschlüssel. Behoben durch `BUS_REALTEST_RUN_SUFFIX`, der in Prepare, Cleanup und Widerrufstest dieselbe ID-Endung erzeugt.

**3. psql ersetzt Variablen nicht in `DO`-Blöcken.** Die naheliegende Lösung `:'run_suffix'` funktioniert außerhalb von Dollar-Quoting, innerhalb nicht — dort kommt `syntax error at or near ":"`. Empirisch geprüft, dann auf `set_config`/`current_setting` umgestellt, das an beiden Stellen trägt.

**4. `cap_drop: ALL` nimmt `root` mehr, als es scheint.** Die Container laufen als `root`, aber ohne `CAP_DAC_OVERRIDE`, `CAP_FOWNER` und `CAP_CHOWN`. Solange die Verzeichnisse `777` waren, fiel das nie auf. Nach der Verschärfung aus Befund F3 zeigte sich die Kette:

- Verzeichnis `755` und fremder Eigentümer ⇒ `root` kann nicht schreiben (kein `CAP_DAC_OVERRIDE`). Behoben durch Eigentümer `root:users`, Modus `775`.
- `chown` auf UID 10001 scheitert ohne `CAP_CHOWN` — und das ursprüngliche `|| true` verschluckte den Fehler. Jetzt `cap_add: CHOWN` und lauter Abbruch statt stiller Übergehung.
- `chmod` **nach** `chown` scheitert, weil `root` die Datei dann nicht mehr besitzt (kein `CAP_FOWNER`). Reihenfolge umgedreht.
- Das Skript konnte die Datei nach der Übergabe nicht mehr lesen, um den Hash zu bilden. Die Übergabe erfolgt jetzt erst **nach** dem Hashen.

Das Ergebnis ist enger als der Ausgangszustand: Token-Dateien liegen als `600` bei genau der UID, die sie braucht, statt für jedes Konto auf der NAS lesbar zu sein.
