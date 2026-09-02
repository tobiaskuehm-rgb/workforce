# Arbeitsstand und Prüfschleife

**Zuletzt aktualisiert:** 2026-09-02 — von Claude Code. **Gerd ist am Zug.**

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
NAS       /volume1/docker/Startup/                                    ← Deploy-Ziel
NAS       /volume1/docker/git/workforce.git                           ← Git-Remote (seit 2026-09-01)
```

**Neu seit 2026-09-01: Das Repo hat ein Remote.** `git push` nach jedem Arbeitsabschnitt; auf einem anderen Rechner `git clone synology:/volume1/docker/git/workforce.git`. Vorher lag die gesamte Historie auf genau einem Mac — das war das größere Risiko als jeder Befund im Reviewlog, und es ist die Ursache hinter `G-021`.

Am Deploy ändert das nichts: Am Code wird im Repo gearbeitet, auf `/volume1/docker/Startup/` wird deployt. Am Code wird im Repo gearbeitet, auf die NAS wird deployt. Ausnahme sind die beiden Review-Dateien: Die leben auf der NAS, weil Gerd nur dort hinkommt.

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
| PostgreSQL-Schema (`001`–`003`, `005`–`007`) | produktiv seit dem Phase-4-Fenster | `2026-09-01_phase4_rollout.md` |
| Abnahmetests zu allen angewendeten Migrationen | **PASS** gegen die laufende Produktion | `2026-09-02_abnahmetests_produktion.md` |
| Migrationen `004`/`008` (Knowledge) | liegen als Dateien auf der NAS, **nicht angewendet**, je eigenes Gate | — |
| Workforce-API (FastAPI) | läuft, gesund — welche Version, sagt `production_state.txt` | `2026-09-01_phase4_rollout.md` |
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

**Diesen Abschnitt nicht lesen, sondern messen.** Ein Lesebefehl nennt Container, API-Version, Migrationsstand, Kanal, Rollen, Manifest, Backup-Rechte, Backup-Inhalt und Rückfallpunkte und endet mit `RESULT: PASS` oder `FAIL`:

```bash
ssh synology "cd /volume1/docker/Startup && sh nas_status.sh"
```

Am **2026-09-02 um 11:50** gemessen: beide Container `healthy`, Kanal `DISABLED`, 0 aktive Credentials, Knowledge `004` nicht angewendet, vier Gates `PASS`, Exit 0.

Warum hier eine Uhrzeit steht statt einer Zusicherung: Einmal stimmte eine dokumentierte Firewall-Rücknahme nicht mit der Wirklichkeit überein (Nachtrag im Trockenlauf-Nachweis). Vor dem nächsten Lauf nachsehen, nicht nachlesen.

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

**Stand: Phase 4 ist ausgeführt.** Im Fenster ausgerollt wurden die Migrationen `001`–`003`, `005`, `006`, `007`, zwei neue Rollen ohne `SUPERUSER`, eigene Secret-Dateien für die API und der Wegfall des `initdb`-Mounts. Die damals ausgerollte API-Version ist seither überholt; den laufenden Stand nennt `production_state.txt`. Kanal weiter `DISABLED`, 0 aktive Credentials, Knowledge `004`/`008` nicht angewendet. Alle sechs Nachweise bestanden, `nas_status.sh` `RESULT: PASS`, Exit 0. Rohtext in `evidence/2026-09-01_phase4_rollout.md`.

Freigaben: CEO im Chat für genau dieses Fenster, dazu Gerds elfter Zielcheck auf `0966cbb` (`G-041`, `G-042`, `G-043` geschlossen, technisches GO).

### `G-044`: drei Fehler, die erst der echte Lauf gezeigt hat

Alle drei standen in meinem eigenen Runbook, alle drei hätten in einer Trockenübung nicht auffallen können.

**Die API kam nicht hoch.** `PermissionError: /run/secrets/workforce_api_key`, Neustart-Loop. Compose hängt ein `file:`-Secret als **Bind-Mount der Host-Datei** ein — am laufenden Container gemessen —, also ändern `uid`/`gid`/`mode` in der Langform nichts. Der Container läuft als `uid=100 gid=101`, die Datei gehörte `TOBKUM` mit `600`. Behoben mit Gruppe `101` und `640` auf den beiden eingehängten Dateien; die dritte wird nicht eingehängt und blieb `600`. Das Runbook sagte „auf `0400`/`root` im Fenster" — das hätte den Fehler festgeschrieben. Das `Dockerfile` pinnt `uid`/`gid` jetzt, damit die Zahl nicht am Basis-Image hängt.

**Die Gates kollidierten mit einem Wächter.** Das Runbook verlangte `005`–`007` auf `"true"` im ausgerollten Stand; `test_review_fixes.py` verlangt sie im versionierten Stand auf `"false"` (`G-031`). Gelöst, ohne eine Seite zu beugen: `docker compose run --rm -T -e APPLY_MIGRATION_X=true registry-migrate` öffnet das Gate für genau einen Aufruf. Der Beleg kommt von selbst — beim nächsten `up` meldet der Runner `already applied` **und** `gate closed`.

**Ein Nachweis prüfte nichts.** Der Rechte-Negativtest rief `bus_send_message` mit fünf Argumenten auf; die Funktion nimmt dreizehn. PostgreSQL antwortete `function ... does not exist` — dieselbe Meldung, die auch bei wirkungslosem `007` gekommen wäre. Mit der echten Signatur: `permission denied for function bus_send_message`. `test_runbook_targets.py` vergleicht Stelligkeiten jetzt gegen die Migrationen.

### Übergabe an Gerd, Stand 2026-09-02

Seit deiner elften Prüfrunde (`0966cbb`) ist Phase 4 gelaufen und danach einiges
dazugekommen. **Der laufende Stand ist `production_state.txt`, nicht dieses
Dokument** — dort steht der Commit, den die NAS wirklich fährt.

**Produktiv jetzt:** API `v9`, Migrationen `001`–`003` und `005`–`007`, beide
neuen Rollen ohne `SUPERUSER`, Kanal `DISABLED`, 0 aktive Credentials, Knowledge
`004`/`008` nicht angewendet. `nas_status.sh` `RESULT: PASS`, Exit 0.

**Was ich seither gefunden und beantwortet habe** — alles in `REVIEW_ANTWORTEN.md`,
jeweils mit Nachweis:

| | worum es geht | Zustand |
|---|---|---|
| `G-044` | drei Fehler im Runbook, die erst der echte Lauf zeigte | behoben, Regeln 10–12 |
| `G-045` | `G-025` ist **nicht** per `ALTER ROLE` schließbar | Entscheidung nötig, siehe unten |
| `G-046` | sieben Dokumente mit überholten Gegenwartsaussagen | behoben, Regeln 16–17 |
| `G-047` | `postgres-tests/` gemountet, ungeprüft, halb vorhanden | teils behoben, Lücke festgeschrieben |
| `G-048` | nächtlicher Job legt weltlesbare Sicherungen ab | behoben; die DSM-Aufgabe ruft seit dem 2026-09-02 `backup_task.sh` auf |
| `G-049` | `001` und `002` prüften Bestandszahlen aus dem August | behoben, Regel 24 |
| `G-050` | `CLAUDE.md` und `HANDOVER.md` nannten eine überholte API-Version | behoben, Regel 25 |
| `G-051` | **die Bus-Adresse zeigte auf ein Gerät, das es nicht gibt** | behoben, Regel 26 |
| `G-052` | die Deploy-Pfadliste existierte nur in einer Terminalzeile | behoben |

**Drei Dinge, bei denen ich deine Einschätzung brauche und nicht selbst
entschieden habe:**

1. **`G-045`** — `workforce_app` ist der Bootstrap-Superuser (OID 10), PostgreSQL
   verweigert den Entzug, und es gibt genau einen Superuser. Der Entzug hätte
   die Audit-Trigger ohnehin nicht geschützt, weil der **Eigentümer** sie
   abschalten kann. Mein Vorschlag: `G-025` in diesem Zuschnitt zurückstellen
   und als Eigentümertrennung neu fassen — eigene Migration, eigene Probe,
   eigene Freigabe. Nachweis `evidence/2026-09-01_g025_bootstrap_superuser.md`,
   wiederholbar mit `g025_nosuperuser_test.py`.
2. **Das Feld `migration` in `/bus/v1/status`** meldet `002_workforce_bus`,
   während die Datenbank bei `007` steht. Es ist ein Vorhandenseins-Flag, kein
   Stand. Drei Wege mit Vorschlag stehen in `REVIEW_ANTWORTEN.md`; eine
   Umstellung wäre eine Vertragsänderung.
3. **Ein Abnahmetest fehlt noch**, `008_knowledge_api_grants`. Die anderen
   fünf sind seit dem 2026-09-02 geschrieben und gegen die laufende Produktion
   gelaufen — Nachweis `evidence/2026-09-02_abnahmetests_produktion.md`, samt
   zwei Gegenproben mit echten Zahlen. `008` ist gegatet und nicht angewendet;
   sein Test gehört in dasselbe Fenster wie seine Anwendung. Die Lücke steht
   mit Begründung in `workforce-agent/test_migration_acceptance.py` und der
   Wächter schlägt in beide Richtungen an.

**Erledigt, war beim CEO:** Die DSM-Sicherungsaufgabe ruft seit dem 2026-09-02
`sh /volume1/docker/Startup/backup_task.sh` auf. Damit liegt die nächtliche
Logik im Repo statt in der Aufgabendatenbank, die Rechte werden **gesetzt**
statt nur geprüft (`G-048`), das Aufräumen alter Sicherungen läuft erst nach
der Vollständigkeitsprüfung der neuen, und der Containername wird
nachgeschlagen statt geraten (`G-042`). **Nicht nachgemessen:** Der erste Lauf
unter der neuen Aufgabe kommt am 2026-09-03 um 02:05.

**Neben den Befunden: die fünf Phase-5-Kontrollen aus deiner CEO-Ergänzung
sind gebaut.** Kostenkontrolle, Datensparsamkeit, Dublettenschutz,
Kommunikationsweg, Modellanbindung — samt der sechs verbindlichen Nachweise
und dem Abschlussartefakt. Neu dafür sind `model_allowlist.py` (Aufgabenklassen,
Tarif, Datenobergrenze, Kostendeckel je Aufruf, kein selbständiger
Modellwechsel) und `efficiency_report.py` (je Vorgang Datenmenge, Felder,
Aufrufe, Tokens beziehungsweise gekennzeichnete Schätzung, Kostenobergrenze,
Route, Dublettenentscheidung — ohne Nutzlast und ohne Geheimnis). Sie brauchen
weder Kanal noch Zugangsdaten noch ein Modell, deshalb konnten sie ohne
Freigabe entstehen. **Alles davon ist gegen Attrappen belegt, nichts am
laufenden System.** Einzelheiten in `REVIEW_ANTWORTEN.md`.

**Wenn du nur eines liest, dann `G-051`.** Jedes Laufzeitpaket zeigte auf
`…192-168-68-78…`, die NAS liegt seit einem Neustart am 2026-09-02 auf `.81`,
und dort antwortete `Connection refused`. Jedes verbleibende Fenster wäre an
der ersten Verbindung gestorben — nach dem Öffnen des Kanals und dem Ausgeben
echter Zugangsdaten. Der Name bildet die LAN-Adresse ab, ist also eine
Ableitung wie ein Containername (`G-042`), und keiner der drei vorhandenen
Wächter konnte die Frage stellen: die Suiten laufen ohne Netz, das Manifest
vergleicht Prüfsummen, `nas_status.sh` fragt über `localhost`.

**Noch offen, unverändert:** `G-030` Laufzeitkette — kein Telegram, kein
Modellaufruf, kein Agentenlauf hat je stattgefunden.

**Randbedingung für den Entwurf von `G-030`, vom CEO am 2026-09-02 erklärt:**
Die NAS läuft **nicht durch**. Zwei DSM-Aufgaben fahren sie um 02:00 hoch und
um 02:20 wieder herunter; tagsüber ist sie an, wenn der CEO sie einschaltet.
Der Grund ist Lautstärke — sie steht am Kinderzimmer — und die nächtliche
Synology-Drive-Synchronisation. Geplant ist ein Umzug auf den Dachboden an
einen 5G-Router, danach wäre Dauerbetrieb möglich; entschieden ist das nicht,
und der CEO hat die Frage ausdrücklich zurückgestellt, bis das System läuft.

Für den Entwurf ist das **keine Einschränkung**, und der Grund ist messbar:
Der Connector holt Nachrichten mit `getUpdates` ab, nicht über einen Webhook
(`telegram_connector.py:292`). Er baut die Verbindung also selbst auf — hinter
CGNAT und ohne Portfreigabe — und merkt sich einen `offset`, holt beim nächsten
Start also dort weiter, wo er aufgehört hat. Ein Zeitfenster statt Dauerbetrieb
ist damit tragfähig: Wer nachts schreibt, bekommt morgens Antwort.

**Vor dem ersten echten Lauf nachzumessen:** wie lange Telegram unabgeholte
Updates aufbewahrt. Nach deren Dokumentation etwa 24 Stunden, aber das ist
**nicht** nachgeschlagen — und ein Satz wie „geht nicht verloren" wäre sonst
genau die Sorte Zusicherung, die dieses Projekt seit `G-046` einsammelt.
Wake-on-LAN hilft hier übrigens nicht: Ein Magic Packet ist ein Broadcast im
lokalen Netz, eine Telegram-Nachricht aus dem Internet kann es nicht auslösen.

**Der Rückfallpfad ist inzwischen geübt**, aber nur in einem Wegwerf-Container:
Phase A der `G-045`-Probe hat die Sicherung `preflight-2026-09-01_22-18-42`
zurückgespielt, erst Rollen-Dump, dann Datenbank-Dump — 3 Migrationszeilen
(korrekt für einen Dump von vor dem Fenster), 15 Tabellen. Auf der Produktion
ausgeführt wurde er nach wie vor nicht.

**Nebenbei, weil es dich beim Nachprüfen betrifft:** Die NAS hat nach einem
Neustart am 2026-09-02 per DHCP eine andere Adresse bekommen. Der SSH-Alias
`synology` zeigt jetzt auf den mDNS-Namen `NASKUEHM.local` statt auf eine feste
IP; der Host-Schlüssel wurde vorher gegen den bekannten Fingerprint geprüft und
ist unverändert.

### `G-043`: das Runbook unterstellte ein Verhalten, das es nicht gibt (geschlossen)

Vier Punkte, alle bestätigt, alle selbst nachgemessen statt nachgelesen.

**Backup-Ordner.** `drwxr-x--- root administrators`, Schreibprobe als `TOBKUM` → `Permission denied`. Die Umleitungen in Abschnitt 3 und das `cp` in Abschnitt 5 werden von der SSH-Sitzung ausgeführt, nicht von Docker; das Fenster wäre vor der ersten Sicherung gestorben. Geschrieben wird jetzt über einen Wegwerf-Container unter `sudo docker` — im Wegwerf-Verzeichnis belegt: Datei landet `-rw-r----- root administrators` und ist für `TOBKUM` lesbar. **Dazu kam ein Punkt, den der Befund nicht nennt:** `docker save -o` schreibt zwar als Root und scheitert nicht, legt die Datei aber `600 root:root` ab — als einzige im Ordner unlesbar. Wird jetzt mit normalisiert.

**Audit-Nachweis.** `/bus/messages` gibt es nicht (`/bus/v1/messages`), das Verfahren ist `Authorization: Bearer`, und `require_bus_ready()` läuft **vor** der Tokenprüfung: bei Kanal `DISABLED` — und der bleibt es im Fenster — kommt `503 BUS_CHANNEL_NOT_ACTIVE`, bevor irgendetwas verbucht wird. Über `localhost:8080` käme zusätzlich `BUS_HTTPS_REQUIRED` zuerst. Der Nachweis läuft jetzt über `bus_record_denial` als `workforce_api`, mit Gegenprobe, dass dieselbe Rolle die Tabelle **nicht lesen** darf.

**Testrolle.** Im Wegwerf-Container nachgemessen: `DROP ROLE niemand` → `cannot be dropped because some objects depend on it — DETAIL: privileges for schema workforce`. Jetzt `DROP OWNED BY` zuerst, in einem eigenen Befehl, damit das Aufräumen auch nach einem fehlgeschlagenen Negativtest läuft, plus Nichtbestandsprüfung.

**Zielmanifest.** `check_secret_files.sh` fehlte in beiden Listen in Abschnitt 5 — und `g041_empty_volume_test.py` ebenfalls, was der Befund nicht nennt. Beides ergänzt. Ein fehlender Pfad wird nicht als „fehlend" gemeldet: `verify_manifest.sh` läuft `find $paths`, also fällt die Datei still aus der Abdeckung.

**Nebenbei repariert:** `nas_status.sh` meldete den „zugehörigen" Rollen-Dump als den jeweils neuesten, ohne die Zugehörigkeit zu prüfen. Jetzt wird der Name aus dem gerade genannten Dump abgeleitet; Abschnitt 3 vergibt dafür **einen** Zeitstempel für alle drei Dateien.

### `G-042`: das Runbook nannte Dinge, die es nicht gibt

Bestätigt, beide Punkte selbst nachgemessen. `docker ps` zeigt `startup-db-1` und `startup-workforce-api-1`; `compose.yaml` setzt kein `container_name`, die Namen sind also abgeleitet. `startup-postgres` existiert nicht — zehn Befehle hätten abgebrochen. Und `005` legt `workforce.bus_denials` mit `occurred_at` an, nicht `bus_denial_audit`/`created_at`; ich hatte den Dateinamen der Migration für den Tabellennamen gehalten.

Korrigiert auf die robustere Form: `docker compose exec -T db` statt Containernamen, `docker compose cp`, `docker compose restart`, und `docker inspect` holt sein Ziel aus `docker compose ps -q db`. **Dabei kam eine Folge dazu, die im Befund nicht steht:** Compose löst sein Projekt über das Arbeitsverzeichnis auf, und acht der umgestellten Befehle hatten kein `cd /volume1/docker/Startup` — als `docker exec` brauchten sie keins. Aus zehn `No such container` wären sonst acht `no configuration file provided` geworden.

`test_runbook_targets.py` löst die Ziele des Runbooks jetzt gegen ihre Quellen auf: Dienstnamen gegen `compose.yaml`, `workforce.`-Bezeichner und Spalten gegen die Migrationen — und zwar **nur gegen die, die das Fenster anwendet**, denn ein Objekt aus dem gegateten `004` bestünde eine naive Existenzprüfung und fehlte im Fenster trotzdem. Sieben Fälle bauen den Fehler absichtlich wieder ein.

Die Wurzel von `G-041` und `G-042` ist dieselbe und unangenehmer als beide: Ich habe ein Dokument, das ausgeführt wird, wie Prosa behandelt. Jede Codezeile läuft hier durch eine Suite; das Runbook lief durch keine — obwohl es das einzige Artefakt ist, dessen Zeilen direkt in eine Produktivshell gehen. Steht als Leitplanke 8 in den drei Spiegeln.

### `G-041`: geschlossen, von Gerd bestätigt

Sein Ergänzungscheck bestätigt die drei Entscheidungen (zwei Manifeste, `compose.yaml` erst im Fenster, `004`/`008` als Dateien ohne Anwendung), findet dabei aber, dass die dritte **im damaligen Compose noch nicht sicher** war.

`compose.yaml` mountete `./postgres-init` nach `/docker-entrypoint-initdb.d`. Das Postgres-Entrypoint führt dort bei leerem Datenverzeichnis alle `*.sql` alphabetisch aus — vor `registry-migrate` und ohne dessen Gates. Solange nur `001`–`003` im Ordner lagen, war das unsichtbar; Phase 4 legt `004`–`008` hinein.

**Nachgestellt statt geglaubt.** Isolierte Instanz, `tmpfs`, Ordner absichtlich wie vorher gemountet. `004_knowledge_capability.sql` lief und setzte seinen Marker; `007` brach mit `MIGRATION_007_ROLE_MISSING` ab; das Entrypoint beendete die Initialisierung mit `Exited (3)`. Eine Wiederherstellung hätte Knowledge angewendet **und** eine kaputte Datenbank hinterlassen. Rohtext in `evidence/2026-09-01_g041_initdb_bypass.md`.

Der Mount ist entfernt — er war Redundanz, `registry-migrate` erreicht denselben Ordner unter `/opt/startup/migrations`. Ergänzt: Eine Compose-Änderung wirkt erst nach `--force-recreate`; der laufende NAS-Container hat den Mount bis heute. Das Runbook zieht die Datenbank deshalb vor die API und prüft am Container, nicht in der Datei.

### Phase 4 ist vorbereitet — `PHASE4_RUNBOOK.md`

Das Runbook deckt Gerds verbindlichen Scope ab und ist zum Abarbeiten von oben nach unten geschrieben: Vorbedingungen, frische Sicherung **samt Rollen-Dump**, Rollenanlage aus Secret-Dateien, Zielmanifest, Öffnen ausschließlich der Gates `005`, `006`, `007`, sechs Nachweise, Rückfallpfad in der Reihenfolge, in der er funktioniert.

Drei Entscheidungen darin, die ein Prüfer kennen sollte:

- **Zwei Manifeste statt einem.** Die NAS hält `postgres-init/` nur bis `003`, dazu `compose.yaml` und `app.py` in der v7-Fassung. Nähme das *laufende* Manifest diese Pfade jetzt auf, stünde die Routineprüfung bis zum Rollout dauerhaft auf rot — und ein Wächter, der immer rot ist, wird ignoriert. `deploy_manifest.sh` nimmt deshalb `MANIFEST_OUT` entgegen; das Zielmanifest entsteht **im Fenster**, weil es den dann gültigen Commit nennen muss.
- **`compose.yaml` erreichte die NAS erst im Fenster** — bis dahin hätte ein versehentliches `docker compose up` Phase 4 ausgelöst. Erledigt: Sie liegt seit dem 2026-09-01 dort und zeigt inzwischen auf `startup-workforce-api:v9`.
- **`004` und `008` liegen danach als Dateien auf der NAS, angewendet sind sie nicht.** Angewendet wird ausschließlich über das Gate; beide bleiben `"false"`. Wer den Zustand prüft, prüft die Tabellen, nicht die Dateiliste.

Der Umfang ist gemessen, nicht geschätzt: auf `ec8df2e` deckt das laufende Manifest 130 Dateien und das Zielmanifest 144; das Fenster fasst genau elf an (vier geändert, sieben neu — Tabelle im Runbook).

### `nas_status.sh`: ein Lesebefehl für den ganzen Iststand

Container, API-Version, Migrationsstand, Kanal, Zugänge, Rollen, Manifest, Backup-Rechte, Rückfallpunkte — mit `RESULT: PASS`/`FAIL` und passendem Exit-Code, also auch als Preflight verwendbar.

Der erste Lauf meldete `PASS`, während eine Teilprüfung fehlschlug: Hinter einer Pipe gehört der Rückgabewert dem letzten Befehl, nicht der Prüfung. Behoben; die Regel steht jetzt in den drei Spiegeln. Aktueller Lauf: `RESULT: PASS`, Exit 0.

### Was zuvor galt (Verlauf)

### Was in dieser Runde geschlossen wurde

| # | Was | Wo |
|---|---|---|
| `G-012` | `EXHAUSTED` bleibt beanspruchbar, bis die Schlussmeldung verbucht ist | `agent_worker.py`, `state_store.py` |
| `G-013` | Claim wird bis zum dauerhaften Ergebnis gehalten | `agent_worker.py` |
| `G-014` | Ablehnung mit falschem Grund fällt durch; jedes erlaubte Paar wird positiv ausgeführt (17/17, 5/5) | `contract_test.py` |
| `G-015` | `CORE PASS` zurückgenommen → `BUS LIFECYCLE PASS`, Gate `CORE ITERATE` | Evidenz |
| `G-016` | Abo-Provider zurückgezogen, nicht scheinbar isoliert | `providers.py` |
| `G-017` | Runner mit Außenroute bekommt keine Secret-Datei; DB-Helfer lesen `startup.db.env` | Compose-Dateien, `derive_db_env_once.sh` |
| `G-018` | Migration `005`: append-only `bus_denials`; Audit prüft exakte Ids und volle Reihenfolge | `postgres-init/`, `workforce-api/`, `core_audit.sql` |
| `G-019` | Deploy-Manifest mit Prüfsummen; „nicht belegt" heißt jetzt so | `deploy_manifest.sh`, `verify_manifest.sh` |

### Vier Nachweise, die noch fehlen — alle im selben Fenster einsammelbar

Keiner davon kostet Geld, keiner braucht ein Modell. Alle brauchen **eine Freigabe im Chat** und die temporäre Firewall-Regel:

1. **Migration `005_bus_denial_audit` anwenden — Knowledge `004` ausdrücklich nicht.** Beide sind getrennt und fail-closed gegatet; ein `up` wendet **keine** an, solange der jeweilige Schalter nicht auf `true` steht. Danach der Abnahmetest `005_bus_denial_audit_acceptance.sql`. **Die SQL ist auf diesem Mac nie gelaufen** — hier gibt es weder `psql` noch Docker.
2. **API `v8` bauen und ausrollen.** Sie schreibt die Ablehnungen; ohne sie bleibt `bus_denials` leer.
3. **Contract-Test in der neuen Fassung gegen den echten Bus.** Erwartung: `deny` vollständig, `allow` 17/17 und 5/5, `wrong_reason` 0.
4. **`verify_secret_isolation_once.sh`** — braucht keine Firewall-Regel und keine Zugangsdaten.
5. **Der Kettenlauf** (`chain-test/`) — braucht zusätzlich einen Telegram-Testbot und die breitere Firewall-Regel
6. **Der Worker-Core-Lauf** (`compose.workercore.yaml`) — `workercore_prepare.sql` prüft sieben Vorbedingungen und bricht ab, statt halb zu laufen: Migration `003` und `005` angewendet, Kanal `DISABLED`, kein aktives Credential, `AGENT-ENG-001` in der Registry, je eine Route zum und vom Agenten. Die API-Version prüft es **nicht** — wer sie voraussetzt, misst sie selbst.

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

### Gerds fünfte Prüfrunde: `G-022` bis `G-034` abgearbeitet

**Dreizehn Befunde, jeder selbst nachgemessen statt übernommen.** Zehn behoben und mit Tests belegt, einer bewusst offen, einer CEO-Gebiet, einer zur Hälfte widerlegt.

| | |
|---|---|
| **Behoben und belegt** | `G-022` Backup-ACL, `G-023` Provenienz, `G-024` Restore, `G-025` Rollentrennung, `G-026` `.dockerignore`, `G-027` Fehlercodes, `G-028` Routenvertrag, `G-029` fail-closed, `G-031` Migrations-Gates, `G-033` Widerspruchsscan, `G-034` SDK-Retries |
| **Bestätigt, bewusst nicht behoben** | `G-030` — integrierte Runtime-Kette, gehört in Roadmap-Phase 6 |
| **Bestätigt, CEO-Gebiet** | `G-032` — 19 uncommittete Änderungen in den Autoritätsquellen |
| **Zur Hälfte widerlegt** | `G-023` — die Produktivdateien passen sehr wohl zu einem Commit (`ff2d32a`) |

**Zwei Befunde waren schwerer als beschrieben.** `G-022`: Neben der ACL lagen dort **25 Konfigurationsarchive mit `startup.env` und 26 vollständige SQL-Dumps** — jeder NAS-Benutzer konnte Datenbankpasswort, API-Schlüssel und sämtliche Nachrichteninhalte lesen. `G-025`: Der eigentliche Blocker stand nicht im Befund — die API führte bei jedem Start `CREATE TABLE` aus und brauchte deshalb dauerhaft DDL-Rechte.

**Drei Dinge fanden erst die Tests**, nicht das Lesen: mein `.dockerignore`-Muster ließ `anthropic_api_key` durch, meine erste Fassung von Migration `007` hätte sie an die Gates von `004` und `005` gekettet, und der Widerspruchsscan fand eine veraltete Testzahl in dieser Datei.

**Neu und wichtig für jeden weiteren Lauf:**

- `production_state.txt` + `verify_production_state.sh` — der laufende Stand heißt `ff2d32a`, Tag `produktiv-v7`, jederzeit prüfbar **ohne** Deployment
- `check_backup_permissions.sh` — die Backup-Härtung kann über Nacht erodieren, der Backup-Job läuft als Root
- Migrationen `004`–`007` haben **je ein eigenes, geschlossenes Gate**. Ohne ausdrücklichen Schalter wendet ein `docker compose up` keine an

**Restore erstmals bewiesen** — und der erste Versuch scheiterte: Der Dump enthält kein `CREATE ROLE`. Die Wiederherstellungsvorschrift steht in `evidence/2026-09-01_backup_acl_und_restore.md`.

### Gerds vierte Prüfrunde: `G-021` behoben — die Zweige sind vereinigt

**Der schwerste Befund bisher, und er war zu eng gefasst.** Er nannte eine Richtung: API `v8` verdrängt die Knowledge-Endpunkte von `v7`. Die Messung zeigte eine zweite — dem autoritativen Stand fehlten `require_https_transport` (`F2`), das Ablehnungs-Audit, der festgenagelte Bridge-Subnetz (`F4`) und acht Tests. **Keiner der beiden Stände war eine Obermenge des anderen.**

Vereinigt: `app.py` aus autoritativer Basis plus meinen drei Ergänzungen, 15 Aufrufstellen mit Audit-Kontext (auch die sechs von Knowledge), Migration als `005_bus_denial_audit` neben dem unveränderten `004_knowledge_capability`, `compose.yaml` mit beiden Blöcken, `test_app.py` aus beiden Seiten. Drei Abnahmetests und ein Ruby-E2E-Test, die hier ganz fehlten, sind jetzt da.

**Im Container geprüft, alle Tests grün** — und der Lauf fand drei Fehlschläge, von denen einer älter war als der Merge. Meine `G-018`-Arbeit hatte drei API-Tests kaputtgemacht, unbemerkt, weil die Suite auf diesem Mac nicht läuft. Der Containerlauf ist jetzt Pflicht vor jedem Commit an `app.py`.

Neu als Wächter: ein **Routen-Inventar**, das alle 19 Routen namentlich aufzählt. Es hätte `G-021` selbst gefangen — jeder bisherige Test lief grün, während sieben Endpunkte fehlten.

### Was noch nicht inventarisiert ist

Der autoritative Satz enthält mehr, das hier fehlt: `credential-rotation/`, `local-demo/`, `restore-test/`, `workspace-agent-*`, `source-backups/`, rund zwanzig Evidenzdokumente, vier Konzeptpapiere. **Ich weiß nicht, was davon gepflegter Code ist und was Historie.** Solange das offen ist, kann dieselbe Abzweigung an anderer Stelle passieren. Vorschlag in `REVIEW_ANTWORTEN.md`: eine Inventur mit einer Entscheidung je Verzeichnis.

### Gerds dritte Prüfrunde: `G-020` behoben

**Ein neuer Befund, Schwere mittel, trifft zu.** Das Deploy-Manifest prüfte die gelisteten Dateien korrekt, erkannte aber keine **unerwarteten** — und hätte umgekehrt einen lokal vorhandenen `secrets/`-Ordner mit ins Archiv genommen. Auf der NAS nachgemessen: vier Dateien in den deployten Pfaden fehlten im Manifest (alles `*.env`, legitim — aber die Prüfung konnte das nicht unterscheiden).

Beide Richtungen zu: Das Manifest kommt jetzt aus `git ls-files` statt aus `find`, womit Secrets und Laufzeitdateien **strukturell** draußen sind; die Prüfung meldet fehlend, abweichend **und unerwartet**, mit einer kurzen Ausnahmeliste an genau einer Stelle. Der Deploy-Befehl im Runbook oben archiviert versionierte Dateien statt Verzeichnisse — sonst wäre die Korrektur halb. `test_deploy_manifest.py` verlangt für jeden Fall einen Fehlschlag.

**Zwei eigene Fehler dabei aufgefallen:**

1. Gerds Prüfrunde geriet mit einem `git add -A` ungelesen in einen Commit, der von etwas anderem handelte. Steht als Leitplanke 4 in `CLAUDE.md`.
2. `REVIEW_ANTWORTEN.md` auf der NAS war 169 Zeilen alt — **Gerd hat gegen einen Stand geprüft, dem meine Antworten zu `G-012` bis `G-019` fehlten.** Beide Review-Dateien gehen ab jetzt bei jedem Deploy mit.

### Kurznachcheck: die Restpunkte sind zu

**Nachtrag, selbst gefunden:** Zwei Dinge waren nicht festgehalten. Eine veraltete offene Stelle in dieser Datei behauptete weiter, der API-Container sehe `POSTGRES_PASSWORD` — korrigiert, und der Scan kennt die Klasse jetzt. Und die `prune`-Regel aus `G-038` stand nirgends: Grundregel 5 verlangt für **jeden bestätigten Befund** eine Regel, auch wenn seine Behebung nicht im Auftrag stand. Beides ist nachgetragen.

**Beide Restpunkte hatte ich benannt statt behoben** — das ist zu wenig, eine benannte Lücke ist eine Lücke.

- **`startup.env` erreicht den API-Container nicht mehr.** Gerds Argument sticht: Dass `app.py` die Werte nicht mehr liest, schützt nicht bei einer kompromittierten API — ein Prozess liest seine eigene Umgebung und verbindet sich als Eigentümer, an jedem Grant vorbei. Der Container bekommt jetzt den Datenbanknamen im Klartext und zwei Secret-Dateien, sonst nichts. Der Migrationslauf behält die Datei; Migrationen sind DDL auf dem Schema des Eigentümers.
- **Der pauschale Default-Grant ist weg.** Mein Argument war, eine Namensliste müsse jemand pflegen. Das Gegenargument sticht: Genau das ist der Zweck — sonst wäre eine künftige administrative `SECURITY DEFINER`-Funktion automatisch für die API ausführbar. `005` und die neue `008` erteilen ihre Funktionen namentlich.
- **Drei veraltete Aussagen korrigiert**, drei neue Klassen im Widerspruchsscan: veraltete Gate-Aussage, unverankerte Dateizahl, Secret am falschen Ort — jede mit Negativprobe.

**Ein Nebenertrag:** Der `G-017`-Wächter schlug fehl, weil `workforce-api` noch in der Liste der erlaubten `startup.env`-Leser stand. Die Gleichheitsprüfung hat die Verbesserung bemerkt und ihre Eintragung erzwungen.

### Nachreview: `G-035`, `G-036`, `G-037` behoben

**Zwei davon entwerten Nachweise, die ich vorher geführt hatte** — das ist der wichtigste Punkt.

- **`G-035`:** PostgreSQL erteilt `EXECUTE` auf Funktionen standardmäßig an `PUBLIC`. Mein `GRANT` an `workforce_api` war deshalb **reine Dekoration** — nachgemessen: eine Rolle ohne jedes Recht konnte die Bus-Funktionen ausführen. Jetzt `REVOKE ... FROM PUBLIC` plus `ALTER DEFAULT PRIVILEGES`, damit Funktionen aus `004`/`005` beim Öffnen ihres Gates nicht mit dem Standard ankommen. Die API verbindet sich jetzt tatsächlich als `workforce_api`, ohne Rückfall auf den Eigentümer. **Beides in einer Produktivkopie bewiesen**, samt echtem API-Start und echtem `pg_dump` — der fand noch fehlende Sequenzrechte.
- **`G-036`:** Bei `G-034` hatte ich die SDK-Retries abgeschaltet und den **serverseitigen** Fallback stehen lassen, der eine abgelehnte Anfrage auf einem zweiten Modell wiederholt. `G-034` war damit nicht geschlossen. Entfernt.
- **`G-037`:** Sieben konkrete Widersprüche korrigiert — vor allem `004`/`005` verwechselt. Der Scan prüfte, ob eine Datei existiert, nie ob die **Nummer zum Thema** passt. Erweitert um Migrationszuordnung, Datenpolicy, Provider-Fallback, Commitzahlen und offene Gates — mit drei Tests, die belegen, dass er die real falsche Zeile fängt und korrekte Abgrenzungen durchlässt.

**Offen und benannt:** `workforce_app` behält `SUPERUSER` (eigener Schritt). Der zweite Punkt dieser Zeile — der API-Container sehe weiterhin `POSTGRES_PASSWORD` — **ist seit dem Kurznachcheck erledigt**; `startup.env` erreicht den Service nicht mehr. `G-038` und `G-040` waren nicht Teil des Auftrags.

### Phase 3 abgeschlossen: `PREFLIGHT PASS`

**2026-09-01, nach CEO-Freigabe.** Kein Rollout — `compose.yaml`, `postgres-init/` und `workforce-api/` sind bewusst **nicht** auf der NAS. Nachweis: `evidence/2026-09-01_phase3_nas_preflight.md`.

| | |
|---|---|
| Iststand | API `v7`, Migrationen `001`–`003`, Kanal `DISABLED`, **0** aktive Credentials, beide Container `healthy` |
| Provenienz | 6 von 6 Produktivdateien byteweise `ff2d32a`, Tag `produktiv-v7` |
| Rückfallpunkte | Datenbank-Dump **plus Rollen-Dump** plus Image-Archiv, alle `640 root:administrators` |
| Restore | **verifiziert**: null Fehler, 28 Nachrichten, 9 Tasks, Eigentümer `workforce_app` — deckungsgleich mit der Produktion |
| Manifest | nichts fehlend, nichts abweichend, nichts unerwartet |
| Backup-Rechte | keine Datei mit Welt-Zugriff — die Härtung hat das Schreiben überstanden |

**Der Rollen-Dump schließt die Lücke aus `G-024`**: Der nächtliche Job schreibt nur `pg_dump`, also ohne `CREATE ROLE`. Das Preflight-Paar ist beides und wurde eingespielt, nicht nur erzeugt.

**Ein Nebeneffekt der `G-022`-Härtung gehört gemerkt:** In `Startup-Backups` schreibt nur noch Root. Eine Shell-Umleitung als `TOBKUM` scheitert mit `Permission denied` — dafür braucht es `sudo`.

### Voraussetzungen für Phase 4 (Rollout)

1. **Eine eigene CEO-Freigabe für genau das Fenster** — Phase 3 deckt sie nicht ab
2. `CREATE ROLE workforce_api` und `workforce_backup` mit Passwörtern aus dem Secret-Store, **vor** Migration `007`
3. Entscheidung, welche Gates geöffnet werden. Gerds Empfehlung: `005`, `006`, `007` — **ohne** Knowledge `004`
4. Passwort für `workforce_api` in `secrets/workforce_api_db_password` und der API-Schlüssel in `secrets/workforce_api_key` — **nicht** in `startup.env`. Die Datei erreicht den API-Container nicht mehr, sie trägt das Eigentümer-Passwort (`G-035`)

### Noch offen für `CORE PASS`

Gerds Roadmap, Phasen 3 bis 8 — **jede braucht eine CEO-Freigabe, die nicht vorliegt**:

1. **Phase 3 NAS-Preflight:** Iststand nachmessen, frisches Backup, Rückfallimage, Manifest der Produktivpfade
2. **Phase 4 Foundation-Update:** API `v8` und Migrationen `005`–`007` — **ohne** Knowledge `004`, das hat ein eigenes Gate
3. **Phase 5 Contract und Audit:** Contract-Test, Secret-Isolation, automatische Auditrekonstruktion
4. **Phase 6 Core-Abnahme:** Roundtrip wiederholen, dann der **integrierte** Worker-Core (`G-030`)
5. **Phase 7 Rückbau, Phase 8 formeller Status**

Ein echter Modellmitarbeiter kommt danach und braucht eine eigene Entscheidung.

### Was beim Nutzer liegt

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

Neu dazugekommen: `startup.db.env` mit drei statt fünf Werten, `test_compose_secrets.py` als Drift-Wächter über alle Compose-Dateien, die Migration für das Ablehnungs-Audit — damals unter der Nummer `004`, heute `005`, beim Merge mit dem autoritativen Stand umnummeriert (`G-021`), API `v8`, Deploy-Manifest mit Prüfsummen.

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
