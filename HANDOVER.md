# Arbeitsstand und Prüfschleife

**Zuletzt aktualisiert:** 2026-09-01, nach dem ersten vollständigen Kettenlauf — von Claude Code

## Wie die Zusammenarbeit läuft

**Claude Code programmiert. Codex (Gerd) prüft.** Nur eine Seite ändert Code — damit kann nichts kollidieren.

| Datei | Wer schreibt | Wer liest | Wo |
|---|---|---|---|
| `REVIEW_GERD.md` | **nur Gerd** | Claude | NAS `/docker/Startup/` |
| `REVIEW_ANTWORTEN.md` | **nur Claude** | Gerd | NAS `/docker/Startup/` |
| `HANDOVER.md` (diese) | Claude | Gerd | NAS + Repo |
| Quellcode | **nur Claude** | Gerd | Repo, deployt auf NAS |

Jede Seite schreibt ausschließlich ihre eigene Datei. Niemand editiert die des anderen — deshalb braucht es keine Sperren und keine Absprache über Reihenfolge.

**Ablauf:** Gerd trägt Befunde in `REVIEW_GERD.md` ein → Claude liest sie beim nächsten Mal, arbeitet sie ab und antwortet in `REVIEW_ANTWORTEN.md` → offen bleibt, was der Nutzer entscheiden muss.

Ein Befund wird nie gelöscht, sondern beantwortet. Auch „stimmt nicht, weil …" ist ein Ergebnis.

## Der maßgebliche Quellensatz

```
~/Library/Mobile Documents/com~apple~CloudDocs/Startup_Codex/
    START_UP_Codex_Projektquellen_2026-08-13/
```

Entscheidungen bis `DEC-027`, `ENG-008` vorhanden, Projektanweisung v1.2. **Das ist der gültige Stand.**

Nicht verwenden: `~/.codex/.chatgpt-projects/…/sources/` bzw. `/mnt/data/…` — Stand 10.08., nur bis `DEC-009`, `ENG-008` fehlt dort ganz.

Zwei Grenzen aus `DEC-027` und `ENG-008`, die gelten:

- **Kein externer kostenpflichtiger Dienst.** `AGENT_PROVIDER=claude` ist ohne neue Entscheidung nicht freigegeben.
- **Der Core sind Gerd, Karl und Anastasia.** Frühere Bus-Abnahmen sind Evidenz, ersetzen den Core-Roundtrip aber nicht.

## Wo die Wahrheit liegt

```
Mac-Repo  /Users/Tobi/Documents/Codex/workorce claude/nas-startup/   ← Quelle der Wahrheit
NAS       /volume1/docker/Startup/                                    ← Ziel, kein Git
```

Die NAS hat **kein Git**. Am Code wird im Repo gearbeitet, auf die NAS wird deployt. Ausnahme sind die beiden Review-Dateien: Die leben auf der NAS, weil Gerd nur dort hinkommt.

Deploy (`rsync` und `scp` funktionieren auf dieser DSM nicht). **Versionierte Dateien, nie ganze Verzeichnisse** — ein verzeichnisweites Archiv nimmt Secrets und Laufzeitdateien mit (Befund `G-020`). Die Dateiliste geht über `-T` in `tar`, nicht über `$(…)`: **zsh zerlegt eine unquotierte Variable nicht in Wörter**, und die Pfade kämen als ein einziges Argument an.

```bash
cd "/Users/Tobi/Documents/Codex/workorce claude/nas-startup"
sh deploy_manifest.sh <pfade>
git ls-files -- <pfade> > /tmp/liste.txt && echo DEPLOY_MANIFEST.txt >> /tmp/liste.txt
tar czf - -T /tmp/liste.txt \
  | ssh synology "cd /volume1/docker/Startup && tar xzf - && find . -name '._*' -delete"
ssh synology "cd /volume1/docker/Startup && sh verify_manifest.sh"
```

---

## Stand der Arbeit

### Fertig und nachgewiesen

| Baustein | Zustand | Nachweis in `evidence/` |
|---|---|---|
| PostgreSQL-Schema (Migrationen 001–003) | produktiv | — |
| Migration `004` (Ablehnungs-Audit) | **geschrieben, nie angewendet** | — |
| Workforce-API `v7` (FastAPI) | läuft, gesund — **im Repo steht `v8`**, nicht ausgerollt | — |
| HTTPS über Reverse Proxy 8443 | verifiziert | — |
| Bus-Realtest Karl ↔ Thorsten | **PASS** | `2026-08-31_bus_realtest_karl_thorsten.md` |
| 20 Negativtests über die echte API | **PASS** | dito |
| Widerrufstest (Gate-Punkt 6 komplett) | **PASS** | `2026-08-31_telegram_realtest_2_und_widerrufstest.md` |
| Telegram-Realtest 2 | **PASS** | dito |
| Security-Review Bus | erledigt | `2026-08-31_security_review_workforce_bus.md` |
| Agenten-Trockenlauf (Echo) | **PASS** | `2026-08-31_agent_dryrun.md` |
| **ENG-008 Core-Roundtrip** | **`BUS LIFECYCLE PASS`**, Gate `CORE ITERATE` (`G-015`) | `2026-08-31_eng008_core_roundtrip.md` |
| Security-Review Agentenschicht | erledigt | `2026-08-31_security_review_agent.md` |
| **Kette Telegram → Bus → Agent → Bus → Telegram** | **`CHAIN PASS`** | `2026-09-01_chain_realtest.md` |
| Contract-Test gegen den echten Bus | **überholt** — die alte Fassung zählte jeden Fehler als Ablehnung (`G-014`) | `2026-08-31_contract_test_und_aufraeumen.md` |

Die Kette **Telegram → NAS → Bus → PostgreSQL** ist real belegt. Der Bus ist abgenommen.

**Der deployte Quellstand dieser Läufe ist nicht rekonstruierbar** (`G-019`). Ab jetzt trägt jeder Deploy ein `DEPLOY_MANIFEST.txt`, und ein Nachweislauf ohne bestandenes `verify_manifest.sh` zählt nicht.

### Gebaut, aber nie mit einem Modell gelaufen

`workforce-agent/` — Worker, Provider-Abstraktion, Datengrenze, Prepare-/Cleanup-Paket, Budget, lokale Tests ohne Netz. Der Echo-Trockenlauf hat den Bus-Weg belegt; `AGENT_PROVIDER=claude` ist noch nie ausgeführt worden und durch `DEC-027`/`ENG-008` auch nicht freigegeben. `AGENT_PROVIDER=subscription` ist zurückgezogen (`G-016`).

### Systemzustand

Kanal `DISABLED`, 0 aktive Credentials, keine Secrets abgelegt, keine temporären Firewall-Regeln, nur der Produktivstack läuft.

**Das ist der Stand laut letztem Rückbauprotokoll, nicht laut Nachmessung.** Einmal an diesem Tag stimmte eine dokumentierte Firewall-Rücknahme nicht mit der Wirklichkeit überein (Nachtrag im Trockenlauf-Nachweis). Vor dem nächsten Lauf nachsehen, nicht nachlesen.

---

## Offene Punkte

### Entscheidungen beim Nutzer

1. **Datengrenze** — `AGENT_DATA_POLICY`. Voreinstellung `METADATA_ONLY` (kein Nachrichtentext verlässt die NAS). Für echte fachliche Arbeit braucht es `BODY`. **Das blockiert den Modellbetrieb.**
2. **sudo-Regel** (Befund F5) — `/etc/sudoers.d/tobkum-docker`, passwortloser Docker-Zugriff, faktisch Root. Wann zurücknehmen?

### Technisch offen

| Punkt | Stand |
|---|---|
| **A1 — Agent handelt unter Menschen-Identität** | **blockiert den Modellbetrieb.** `agent_identity_create.sql` liegt bereit. Ob `AGENT-ENG-001` auf der NAS existiert, ist **nicht belegt** — der Trockenlauf lief unter `AI-ENG-001`, `agent_prepare.sql` setzt die neue Identität inzwischen voraus. Vor dem nächsten Lauf in der Registry nachsehen |
| A2 Herkunftsvermerk | behoben |
| A3 Laufzeitgrenze | behoben |
| A5 Rückzug bei Busausfall | behoben |
| F8 Ratenbegrenzung / Kostenlimit | behoben, fünf Decken in `budget.py` |
| Rückrichtung Bus → Telegram | konfigurierbar, Voreinstellung unverändert `METADATA_ONLY` |
| Freigabeentscheidung (`DEC-`Nummer) für Modellbetrieb | fehlt |

---

## Hier weitermachen

**Stand:** Gerds Befunde `G-012` bis `G-019` sind **alle abgearbeitet**, einzeln beantwortet in `REVIEW_ANTWORTEN.md`. Das Gate bleibt **`CORE ITERATE`** — nicht weil noch Befunde offen wären, sondern weil vier der Korrekturen **nur gegen Attrappen geprüft** sind.

### Was in dieser Runde geschlossen wurde

| # | Was | Wo |
|---|---|---|
| `G-012` | `EXHAUSTED` bleibt beanspruchbar, bis die Schlussmeldung verbucht ist | `agent_worker.py`, `state_store.py` |
| `G-013` | Claim wird bis zum dauerhaften Ergebnis gehalten | `agent_worker.py` |
| `G-014` | Ablehnung mit falschem Grund fällt durch; jedes erlaubte Paar wird positiv ausgeführt (17/17, 5/5) | `contract_test.py` |
| `G-015` | `CORE PASS` zurückgenommen → `BUS LIFECYCLE PASS`, Gate `CORE ITERATE` | Evidenz |
| `G-016` | Abo-Provider zurückgezogen, nicht scheinbar isoliert | `providers.py` |
| `G-017` | Runner mit Außenroute bekommt keine Secret-Datei; DB-Helfer lesen `startup.db.env` | Compose-Dateien, `derive_db_env_once.sh` |
| `G-018` | Migration `004`: append-only `bus_denials`; Audit prüft exakte Ids und volle Reihenfolge | `postgres-init/`, `workforce-api/`, `core_audit.sql` |
| `G-019` | Deploy-Manifest mit Prüfsummen; „nicht belegt" heißt jetzt so | `deploy_manifest.sh`, `verify_manifest.sh` |

### Vier Nachweise, die noch fehlen — alle im selben Fenster einsammelbar

Keiner davon kostet Geld, keiner braucht ein Modell. Alle brauchen **eine Freigabe im Chat** und die temporäre Firewall-Regel:

1. **Migration `004` anwenden.** Der Produktivstack zieht sie beim nächsten `up` selbst. Danach `postgres-tests/004_bus_denial_audit_acceptance.sql`. **Die SQL ist auf diesem Mac nie gelaufen** — hier gibt es weder `psql` noch Docker.
2. **API `v8` bauen und ausrollen.** Sie schreibt die Ablehnungen; ohne sie bleibt `bus_denials` leer.
3. **Contract-Test in der neuen Fassung gegen den echten Bus.** Erwartung: `deny` vollständig, `allow` 17/17 und 5/5, `wrong_reason` 0.
4. **`verify_secret_isolation_once.sh`** — braucht keine Firewall-Regel und keine Zugangsdaten.
5. **Der Kettenlauf** (`chain-test/`) — braucht zusätzlich einen Telegram-Testbot und die breitere Firewall-Regel
6. **Der Worker-Core-Lauf** (`compose.workercore.yaml`) — setzt `AGENT-ENG-001` in der Registry, Migration `004` und API `v8` voraus; `workercore_prepare.sql` prüft alle drei und bricht ab, statt halb zu laufen.

**Erledigt:** `startup.db.env` liegt auf der NAS — `root:users` mit `660`, genau drei Schlüssel, kein API-Schlüssel darin. `startup.env` unverändert.

Eine Lehre dabei, die in den Runbooks steht: `sudo docker` scheitert über eine **nicht-interaktive** SSH-Sitzung, weil die NOPASSWD-Regel auf `/usr/local/bin/docker` lautet und `docker` dort nicht im `PATH` liegt. Mit vollem Pfad läuft es. `sudo sh …` geht gar nicht — die passwortlose Regel gilt nur für Docker.

### Die Kette ist real gelaufen — `CHAIN PASS`

**2026-09-01: Das System hat zum ersten Mal getan, wofür es existiert.** Zwei vollständige Durchläufe Telegram → Connector → Bus → Agent → Bus → Connector → Telegram, je genau eine Anfrage und genau eine Antwort, Task-Bezug in beide Richtungen erhalten. Echo-Provider, kein Modell, 0,00 $. Nachweis: `evidence/2026-09-01_chain_realtest.md`.

**Drei Defekte, die kein lokaler Test finden konnte:**

1. Das Bot-Token war eine **RTF-Datei** — mit TextEdit geschrieben. 433 Bytes Auszeichnung statt 46 Zeichen Token.
2. Das **Agenten-Image legte sein Zustandsverzeichnis nicht an**. Das Volume gehörte damit Root, der Container läuft als UID 10001 → `unable to open database file`, sofortiger Absturz. **Das hätte jeden künftigen Agentenlauf getroffen**, auch den Worker-Core-Test. Behoben im `Dockerfile`.
3. `chain_cleanup.sql` setzte **`REVOKED` ohne Widerrufsmetadaten**. Die `CHECK`-Bedingung brach die Transaktion ab — richtig so, ein Widerruf ohne Grund wäre ein Loch in der Audit-Spur.

Alle drei sind behoben und als Regeln in `CLAUDE.md` eingetragen.

**Rückbau nachgemessen:** Kanal `DISABLED`, null aktive Zugänge im ganzen Projekt, null aktive Kettenrouten, Connector-Identität `REVOKED`, alle vier Token-Dateien gelöscht, keine Testcontainer mehr, Produktivstack unberührt und gesund.

**Nebenbefund:** `AGENT-ENG-001` existiert und ist aktives Projektmitglied — vor dem Lauf gegen die Registry geprüft. Der Punkt aus `G-019` ist damit nachgemessen statt nachgelesen.

**Testbot gelöscht** (entschieden 2026-09-01). Damit ist der letzte lebende Zugangsweg des Laufs weg, nicht nur von der NAS entfernt. Ein nächster Kettenlauf braucht einen **neuen Bot** und sein Token in `chain-test/secrets/telegram_bot_token`, als **Klartext**. Chat- und Nutzer-Id bleiben voraussichtlich gleich — im privaten Chat ist die Chat-Id die Nutzer-Id, und die gehört dem Menschen; die Identity-Probe prüft es nach.

**Firewall-Regel zurückgenommen, nachgemessen** mit dem tokenfreien Netz-Check: `WORKFORCE_CONNECT_TIMEOUT` von `172.31.254.2`. Der Rückbau ist damit vollständig — kein offener Netzweg, kein aktiver Zugang, kein Secret auf der Platte, keine Testcontainer, Kanal `DISABLED`.

### Gerds dritte Prüfrunde: `G-020` behoben

**Ein neuer Befund, Schwere mittel, trifft zu.** Das Deploy-Manifest prüfte die gelisteten Dateien korrekt, erkannte aber keine **unerwarteten** — und hätte umgekehrt einen lokal vorhandenen `secrets/`-Ordner mit ins Archiv genommen. Auf der NAS nachgemessen: vier Dateien in den deployten Pfaden fehlten im Manifest (alles `*.env`, legitim — aber die Prüfung konnte das nicht unterscheiden).

Beide Richtungen zu: Das Manifest kommt jetzt aus `git ls-files` statt aus `find`, womit Secrets und Laufzeitdateien **strukturell** draußen sind; die Prüfung meldet fehlend, abweichend **und unerwartet**, mit einer kurzen Ausnahmeliste an genau einer Stelle. Der Deploy-Befehl im Runbook oben archiviert versionierte Dateien statt Verzeichnisse — sonst wäre die Korrektur halb. `test_deploy_manifest.py` verlangt für jeden Fall einen Fehlschlag.

**Zwei eigene Fehler dabei aufgefallen:**

1. Gerds Prüfrunde geriet mit einem `git add -A` ungelesen in einen Commit, der von etwas anderem handelte. Steht als Leitplanke 4 in `CLAUDE.md`.
2. `REVIEW_ANTWORTEN.md` auf der NAS war 169 Zeilen alt — **Gerd hat gegen einen Stand geprüft, dem meine Antworten zu `G-012` bis `G-019` fehlten.** Beide Review-Dateien gehen ab jetzt bei jedem Deploy mit.

### Noch offen für `CORE PASS`

Gerds Liste, der ich zustimme:

1. Migration `004` und API `v8` real ausrollen und testen
2. Automatisierte Auditrekonstruktion ausführen
3. Worker-Core-Test auf der NAS fahren
4. Später ein echter Modellmitarbeiter — braucht eine Entscheidung

### Nichts mehr offen beim Nutzer

**Erster Einsatz des Deploy-Manifests:** Der Lauf begann auf `f59e757`, 99 Dateien verifiziert. Zwei Korrekturen wurden während des Laufs nachdeployt — das steht im Nachweis, statt als „Commit plus Änderungen" verschleiert zu werden (`G-019`).

### Der Kettentest lokal

**Die Kette schließt sich auch lokal.** `chain-test/test_chain.py` fährt Telegram → Connector → Bus → Agent → Bus → Connector → Telegram mit dem **echten** Connector und dem **echten** Worker; Attrappen nur an den zwei Außenrändern. Neun Tests grün.

Dritter struktureller Blocker gefunden und aufgelöst: Der Connector validiert `source_ref` als `^DEC-\d{3}/ENG-\d{3}$` und kann den ehrlichen Platzhalter aus `G-006` nicht schreiben. Er schreibt `DEC-023/ENG-007` — wahr, denn das ist die Entscheidung, die ihn erlaubt. Die Provenienz des Kettentests selbst steht im SQL.

`G-011` ist behoben statt weiter umgangen: `timezone.utc` statt `datetime.UTC`, zwei Zeilen. Damit laufen **alle vier** Suiten auf dem Mac — vorher zwei.

**Was der Lauf noch braucht, und zwar von dir:** ein neuer Telegram-Testbot mit Token in `chain-test/secrets/telegram_bot_token`, die beiden Chat-/User-Ids aus `identity_probe.py`, die Firewall-Regel für **`172.31.254.0/29`** (breiter als früher — zwei Container, zwei Adressen), und die Freigabe. Schrittfolge in `chain-test/README.md`.

**Entschieden am 2026-09-01:** `TELEGRAM_OUTBOUND_POLICY=METADATA_ONLY` für den ersten Lauf. Die Benachrichtigung im Chat belegt die Rückrichtung; der Antworttext bleibt auf der NAS. Ein späterer Wechsel auf `BODY` ist eine eigene Entscheidung.

### Der Worker-Core-Test ist gebaut

`worker_core_test.py` — die echte Laufzeit unter Last: `agent_worker.poll_once()`, echter `AgentStateStore` auf echter Datei, echte Datengrenze, echtes Budget. Sechs Szenarien: Gutfall, Absturz vor der Bestätigung mit Neustart, wiederholbarer Fehler, Erschöpfung inklusive verworfener Schlussmeldung (`G-012`), verlorenes State-Volume, verbotene Route. Lokal grün, `test_worker_core_test.py`.

Auf der NAS sind `phase1` und `phase2` **zwei Container** über demselben Volume — ein echter Neustart, kein neues Objekt im selben Prozess. Paket: `compose.workercore.yaml`, `workercore_prepare.sql`, `workercore_cleanup.sql`, `workercore_audit.sql`, `Dockerfile.workercore`. **Geschrieben, nicht gelaufen.**

Zwei Funde beim Bauen, beide vom Typ „die Prüfung sah nicht hin":

1. Die erste Fassung der Suite ließ einen absichtlich **nicht-idempotenten Bus** durchgehen. Bei intakter State-Datei sendet der Worker nie zweimal, also wurde die Bus-Idempotenz nie erreicht — die Einmaligkeit trug allein der State Store. Szenario E (verlorenes Volume) belastet die zweite Linie und benennt nebenbei die Kosten: ein wiederholter Modellaufruf je Nachricht in Arbeit.
2. Der Compose-Scanner las **YAML-Anker** nicht und hätte `phase1`/`phase2` als leere Dienste durchgewunken. Ein Wächter, der nicht sieht, meldet `PASS`. Er scheitert jetzt an Ankern; die Compose-Datei kommt ohne aus.

Danach: den begonnenen `chain-test/` fertigbauen.

### Beim CEO

- `DEC-028` und `DEC-029` aus `DEC_ENTWUERFE_2026-08-31.md` prüfen und ins Log übernehmen — bis dahin bleibt das Gate formal offen
- sudo-Regel `/etc/sudoers.d/tobkum-docker` entfernen, wenn nicht gebraucht (faktisch Root)
- Firewall- und Containerzustand nach erneuter DSM-Anmeldung nachprüfen (`G-019`)

---

## Was zuletzt passiert ist

### 2026-08-31, spät — Claude Code

Gerds zweite Prüfrunde vollständig abgearbeitet, `G-012` bis `G-019`.

**Die interessanteste Erkenntnis** war nicht einer der Befunde, sondern das Muster hinter dreien davon. `G-014`, `G-016` und `G-017` sind derselbe Fehler: Ein Kommentar behauptet eine Absicherung, die der Code daneben nicht herstellt. In allen drei Fällen hatte ich die Anforderung **richtig aufgeschrieben** und dann etwas anderes gebaut — die Absicht blieb als Text stehen, während die Umsetzung woanders hinging. Der Kommentar wurde damit zur Absichtserklärung im Gewand einer Zusicherung, und die ist schlimmer als gar keine: Sie hält den nächsten Leser vom Nachprüfen ab.

Jede der drei Stellen hat jetzt eine Prüfung, die scheitert, wenn die Zusicherung nicht mehr gilt. Wo sich eine Zusicherung nicht prüfen lässt, steht hin, dass sie nicht belegt ist.

Neu dazugekommen: `startup.db.env` mit drei statt fünf Werten, `test_compose_secrets.py` als Drift-Wächter über alle Compose-Dateien, Migration `004` mit `workforce.bus_denials`, API `v8`, Deploy-Manifest mit Prüfsummen.

**Ehrliche Grenze dieser Runde:** Vier Korrekturen sind gegen Attrappen grün und **nie gegen die NAS gelaufen**. Auf diesem Mac gibt es weder `psql` noch Docker; die neue SQL ist gelesen, nicht ausgeführt.

### 2026-08-31 — Claude Code

Bus abgenommen (alle sieben Gate-Punkte), Telegram-Kette real belegt, Agentenschicht gebaut und im Trockenlauf bewiesen. Security-Befunde F1–F4, F6, F7 behoben.

Vier Defekte gefunden und behoben, die den Betrieb blockiert hätten:

- Falscher Reverse-Proxy-Host (`-77` statt `-78`) in vier Telegram-Dateien
- Das Bus-Realtest-Paket war nur einmal ausführbar — widerrufene Credentials lassen sich per Trigger nie reaktivieren, also kollidierte ein zweiter Lauf am Primärschlüssel
- psql ersetzt `:'var'` **nicht** innerhalb von `DO`-Blöcken; umgestellt auf `set_config`/`current_setting`
- `cap_drop: ALL` entzieht `root` auch `CAP_DAC_OVERRIDE`, `CAP_FOWNER` und `CAP_CHOWN`. Fiel erst auf, nachdem die Verzeichnisrechte verschärft waren, in einer Kette von vier Fehlschlägen

Ein eigener Fehler: erfundene SDK-Version `anthropic==1.4.0` (real `1.2.0`) kostete einen Build.

**Nachmittag, autonom weitergearbeitet:** Budget mit fünf Decken (F8), zweite Datengrenze zu Telegram, Security-Review der Agentenschicht mit sieben Befunden, davon A2/A3/A5 direkt behoben.

Der wichtigste Fund ist A1: Der Agent nutzt das Credential von `AI-ENG-001` — und dessen Registry-Eintrag ist eine **Person** (`Gerd`, `AI Engineer`, `PROBATION`). Jede Antwort erscheint als Nachricht eines Menschen. Der Telegram-Connector hatte für genau dieses Problem bereits eine eigene technische Identität bekommen (`CEO-TG-002`, Titel „not an employee"); beim Agenten war dieselbe Sorgfalt nicht angewendet worden. `agent_identity_create.sql` legt `AGENT-ENG-001` nach diesem Muster an — nicht ausgeführt, weil eine dauerhafte Registry-Änderung eine Freigabe braucht.

**Abend:** Alle elf Review-Befunde beantwortet, sechs behoben. Der maßgebliche Quellensatz wurde gefunden — und er ändert die Richtung: `DEC-027` und `ENG-008` schließen den bezahlten Modellbetrieb aus, auf den ich hingearbeitet hatte. Der Echo-Provider ist das Geforderte, nicht die Notlösung.

`ENG-008` ist gebaut: Bus-Client um Tasks und Handoffs erweitert, `core_roundtrip.py` fährt die von `DEC-027` verlangte Sequenz in 18 Schritten inklusive Negativfällen, `core_audit.sql` rekonstruiert den Lauf allein aus der Audit-Spur. Prepare für drei Zugänge, Cleanup, Compose-Dateien.

**Als Nächstes:** Core-Roundtrip ausführen — braucht die temporäre Firewall-Regel und eine Freigabe. 89 Agenten-Tests, 35 Connector-Tests.

---

**Hinweis zur Ablage:** Diese Datei liegt zweimal im Repo — im Wurzelverzeichnis und in `nas-startup/`. Nur die zweite wird auf die NAS deployt und ist die, die Gerd liest. **Beide gehen immer gemeinsam.** Am 2026-09-01 fiel auf, dass die NAS-Kopie drei Sitzungen alt war; Gerd hätte gegen einen veralteten Stand geprüft.
