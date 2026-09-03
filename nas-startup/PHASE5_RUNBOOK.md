# Phase 5 — Contract, Core und Audit auf dem neuen Stand

**Status: nicht ausgeführt.** Blocker ist eine CEO-Freigabe im Chat für genau
dieses Fenster; Gerds technischer Zielcheck galt dem Phase-4-Fenster und deckt
dieses nicht ab.

Dieses Dokument wird im Fenster von oben nach unten abgearbeitet. Jeder Schritt
hat einen Befehl und ein Abbruchkriterium. Wer abbricht, springt zu Abschnitt 9.

**Container werden nicht beim Namen genannt** (`G-042`). Ein Containername ist
eine Ableitung aus Projektordner, Dienst und Index. Alle Befehle laufen deshalb
über `docker compose exec -T <dienst>` aus `/volume1/docker/Startup` heraus.
`test_runbook_targets.py` prüft das zusammen mit Tabellen-, Spalten- und
Routennamen gegen die Migrationen, die dieses Fenster wirklich angewendet hat.

**Die Adresse kommt aus `production_state.txt`** (`G-051`). Sie ist ein
abgeleiteter Name und war am 2026-09-02 einen Tag lang tot. Der erste Schritt
misst sie nach, bevor irgendetwas anderes passiert.

## 1. Was sich ändert

| | vorher | nachher |
|---|---|---|
| Kanal | `DISABLED` | `TESTING` im Fenster, danach wieder `DISABLED` |
| Aktive Credentials | 0 | drei kurzlebige im Fenster, danach 0 |
| Contract-Test | `PASS` vom 2026-08-31, alter Stand | gegen den heutigen Bus |
| Auditrekonstruktion Core | `PASS` vom 2026-08-31, alter Stand | gegen den heutigen Bus |
| Auditrekonstruktion Kette | gab es nicht | `chain_audit.sql` |
| Zwei Nachrichten vom 2026-09-01 | `DELIVERED` | bestätigt (`G-053`) |
| Migrationen | unverändert | unverändert — **kein Gate wird geöffnet** |
| API-Image | unverändert | unverändert |

**Dieses Fenster ändert weder Schema noch Image.** Es öffnet einen Kanal,
gibt kurzlebige Zugänge aus, fährt Nachweise und räumt auf. Knowledge `004`
und `008` bleiben zu.

**Kein Modell.** `AGENT_PROVIDER=echo` überall. `DEC-027`/`ENG-008` untersagen
einen kostenpflichtigen Dienst, und Gerds Phase 5 sagt ausdrücklich, dass sie
ohne einen auskommt.

## 2. Vorbedingungen

```bash
ssh synology "cd /volume1/docker/Startup && sh nas_status.sh"
```

Abbruch, wenn nicht `RESULT: PASS` und Exit 0. Erwartet: beide Container
`healthy`, Kanal `DISABLED`, 0 aktive Credentials, Migrationen `001`–`003` und
`005`–`007`, fünf Gates `PASS` — darunter **Bus-Adresse**, die seit `G-051`
prüft, ob die Adresse in `production_state.txt` noch dieser Maschine gehört.

Der laufende Stand muss dem Repo entsprechen:

```bash
cd "/Users/Tobi/Documents/Codex/workorce claude/nas-startup" && sh verify_production_state.sh
```

## 3. Frische Sicherung

**Der Auftrag wird in DSM gestartet, nicht über SSH** (`G-072`). Die
passwortlose sudo-Regel dieser NAS lautet auf `/usr/local/bin/docker` und auf
sonst nichts; `sudo sh …` fragt nach dem Passwort und stirbt in einer
nicht-interaktiven SSH-Sitzung. Ein Fenster, das mit einer Sicherung beginnt,
die es nie gab, ist schlimmer als eines ohne — deshalb steht der Weg hier, den
es wirklich gibt: DSM → Aufgabenplaner → die nächtliche Sicherungsaufgabe →
**Ausführen**. Sie ruft `backup_task.sh` als Root auf, schreibt in den
gehärteten Backup-Ordner, prüft die Abschlusszeile des Dumps, setzt die Rechte
und räumt erst danach Altes weg.

Danach wird das Ergebnis **gemessen**, nicht geglaubt:

```bash
ssh synology "cd /volume1/docker/Startup && BACKUP_MAX_AGE_HOURS=0 sh check_backup_integrity.sh"
```

`BACKUP_MAX_AGE_HOURS=0` ist die eigentliche Frischeprüfung. Das Skript rechnet
in ganzen Stunden, `0` verlangt also einen Dump, der jünger als eine Stunde
ist; der Vorgabewert `26` ließe die Sicherung der vergangenen Nacht durchgehen
— und genau die ist hier nicht gemeint. Geprüft werden außerdem Abschlusszeile,
`restrict`/`unrestrict`-Paarigkeit, Größe gegen die vorige Sicherung und das
Konfigurationsarchiv. Das Skript liest nur und braucht kein Root.

Abbruch, wenn nicht `RESULT: PASS`.

**Kein Rollen-Dump, und das ist Absicht.** Dieses Fenster legt keine Rolle an
und ändert keine — die Rollenlage ist die vom Phase-4-Fenster, und der
zugehörige `*.globals.sql` liegt dort seit dem 2026-09-01 neben seinem Dump.
`nas_status.sh` nennt beide unter „Rückfallpunkte" und prüft, dass sie
zusammengehören. Wer hier trotzdem einen zweiten Rollen-Dump zieht, sichert
denselben Inhalt ein zweites Mal.

## 4. Zielmanifest und Deploy

```bash
cd "/Users/Tobi/Documents/Codex/workorce claude/nas-startup" && sh deploy_to_nas.sh
```

**Ein Aufruf, kein abgeschriebener Einzeiler** (`G-086`). Bis zum 2026-09-03
standen hier drei Zeilen, die die Prozedur ein zweites Mal enthielten — mit
der `tar | ssh`-Pipeline ohne `pipefail` und dem `find … -delete` über den
ganzen Zielordner, die `G-080` aus dem Skript entfernt hat. Das Runbook führte
den unsicheren Weg also weiter aus, während der getestete daneben lag.
Dieselbe Klasse wie die Deployliste vor `G-052`: Zwei Abschriften derselben
Sache laufen auseinander, und die, die im Fenster gelesen wird, ist die
falsche.

Das Skript fährt die drei Schritte, fail-closed und jeder mit eigenem
Exitstatus: Manifest nur bei sauberem Git-Baum, aus genau der Dateimenge,
deren Hashes im Manifest stehen; Archiv **lokal fertig gebaut**, dann
übertragen — ein nur lokal erzeugtes Manifest ist noch kein Deploy
(`G-064`); danach auf der NAS `dirty=no`, keine fehlende, abweichende oder
unerwartete Datei und kein unverwalteter Top-Level-Pfad. Es löscht nichts auf
der NAS; was eine Umbenennung dort zurücklässt, meldet `verify_manifest.sh`
als `UNERWARTET`, und aufgeräumt wird das sichtbar und von Hand. Host und
Zielpfad sind im Skript fest gebunden (`G-091`), nicht aus der Umgebung.
Die Pfadliste steht seit `G-052` versioniert in `deploy_paths.txt`; ein
Skript, das dort fehlt, ist sonst schlicht nicht abgedeckt.

Abbruch, wenn nicht beide `RESULT: PASS` am Ende stehen.

### 4.1 Beide Agent-Images bauen und aus ihrem echten Dateisatz importieren

Der lokale Wächter baut den `COPY`-Satz beider Dockerfiles nach. Der
verbindliche zweite Beleg ist der echte Build auf der NAS — **vor** Kanal,
Credentials und Firewall. Die beiden temporären Prüftags ersetzen kein
Produktivimage und werden unmittelbar danach entfernt (`G-061`).

```bash
ssh synology "cd /volume1/docker/Startup/workforce-agent && sudo /usr/local/bin/docker build --pull=false -t startup-workforce-agent:phase5-smoke -f Dockerfile . && sudo /usr/local/bin/docker run --rm --entrypoint python startup-workforce-agent:phase5-smoke -c 'import agent_worker'"
ssh synology "cd /volume1/docker/Startup/workforce-agent && sudo /usr/local/bin/docker build --pull=false -t startup-worker-core:phase5-smoke -f Dockerfile.workercore . && sudo /usr/local/bin/docker run --rm --entrypoint python startup-worker-core:phase5-smoke -c 'import worker_core_test'"
ssh synology "sudo /usr/local/bin/docker image rm startup-workforce-agent:phase5-smoke startup-worker-core:phase5-smoke"
```

Abbruch, wenn ein Build oder Import scheitert. Auch dann die zwei exakten
Prüftags entfernen; es wurde zu diesem Zeitpunkt noch kein Berechtigungsfenster
geöffnet.

## 5. Netzweg öffnen — beim CEO

Der Contract-Test und der Core-Lauf sprechen über HTTPS mit der API und
brauchen die temporäre DSM-Regel für `172.31.254.2/32` auf TCP 8443. Der
Rückbau steht in Abschnitt 8 und wird dort **nachgemessen**, nicht nachgelesen
(`G-007`).

## 6. Das Fenster

Der Lauf-Suffix ist Pflicht und muss neu sein: Ein `REVOKED`-Credential lässt
sich nie reaktivieren, eine feste Id kollidiert beim zweiten Lauf am
Primärschlüssel. Er wird als Umgebungsvariable übergeben, **nicht** in die
versionierten Compose-Dateien geschrieben — dieselbe Begründung wie beim
Migrations-Gate (`G-044`): Ein Commit mit dem Wert müsste hinterher
zurückgenommen werden, und das ist der Schritt, den man vergisst.

**Deshalb `run --rm --no-deps` statt `up` für das Core-Paket.** `up` kennt
keine Umgebungsüberschreibung, und `run` ohne `--no-deps` würde `prepare` über
`depends_on` ein zweites Mal starten — beim zweiten Mal steht der Kanal schon
auf `TESTING`, und `core_prepare.sql` bricht genau darauf ab. Die Reihenfolge
macht damit dieses Dokument, nicht Compose: Die drei Schritte werden von oben
nach unten gefahren und keiner übersprungen.

### 6.1 Zugänge ausgeben und Kanal öffnen

```bash
ssh synology "cd /volume1/docker/Startup/workforce-agent && sudo /usr/local/bin/docker compose -f compose.core.yaml run --rm --no-deps -T -e CORE_RUN_SUFFIX=20260902-PHASE5 prepare"
```

Erwartet: drei Token mit `mode 600`, drei Credentials `ACTIVE`, Kanal
`TESTING`. Abbruch bei allem anderen — insbesondere, wenn der Kanal vorher
nicht `DISABLED` war.

### 6.2 Contract-Test

Er fragt den echten Bus, ob er so antwortet, wie `bus_rules.py` behauptet.
Das ist die einzige Prüfung, die eine Abweichung zwischen Abschrift und
Migration findet, und sie gehört **vor** alles andere: Läuft der Core zuerst,
ist sein Nachweis gegen eine unbestätigte Annahme gefahren.

```bash
ssh synology "cd /volume1/docker/Startup/workforce-agent && sudo /usr/local/bin/docker compose -f compose.contract.yaml run --rm -T -e CORE_RUN_ID=20260902CONTRACT1 contract"
```

Erwartet: `deny` vollständig, `allow` alle Paare belegt, `wrong_reason` 0.
**Ein Fehlschlag ist erst dann die erwartete Ablehnung, wenn Statuscode *und*
Kennung stimmen** (`G-014`) — der Test prüft das selbst, aber die Ausgabe wird
gelesen und nicht überflogen.

### 6.3 Core-Roundtrip und Auditrekonstruktion

```bash
ssh synology "cd /volume1/docker/Startup/workforce-agent && sudo /usr/local/bin/docker compose -f compose.core.yaml run --rm --no-deps -T -e CORE_RUN_ID=20260902CORE1 run"
ssh synology "cd /volume1/docker/Startup/workforce-agent && sudo /usr/local/bin/docker compose -f compose.core.yaml run --rm --no-deps -T -e CORE_RUN_ID=20260902CORE1 audit"
```

Erwartet: `BUS LIFECYCLE PASS`, danach `positiv_audit = PASS` und
`negativ_audit = PASS`. Die Audit-Abfragen binden an exakte Ids, Akteure und
die vollständige Reihenfolge — „irgendein Datensatz dieses Typs" genügt nicht.

### 6.4 Kernfenster vollständig schließen

Core und Kette sind zwei getrennte Berechtigungsfenster. Der Ketten-Prepare
verlangt zu Recht `DISABLED` und null aktive Credentials; deshalb wird der
Core **vor** jedem Ketten-Prepare zurückgebaut und nachgemessen (`G-062`).

```bash
ssh synology "cd /volume1/docker/Startup/workforce-agent && sudo /usr/local/bin/docker compose -f compose.core-cleanup.yaml run --rm --no-deps -T -e CORE_RUN_SUFFIX=20260902-PHASE5 core-cleanup"
ssh synology "sudo /usr/local/bin/docker run --rm -v /volume1/docker/Startup/workforce-agent/secrets:/secrets postgres:17-alpine sh -c 'rm -f /secrets/core_token_karl /secrets/core_token_gerd /secrets/core_token_anastasia && test ! -e /secrets/core_token_karl && test ! -e /secrets/core_token_gerd && test ! -e /secrets/core_token_anastasia'"
ssh synology "cd /volume1/docker/Startup && sh nas_status.sh"
```

Abbruch, wenn nicht Kanal `DISABLED`, 0 aktive Credentials, fünf Gates
`PASS` und Exit 0. Erst danach darf ein separates Kettenfenster beginnen.

**Die drei Namen sind die, die `prepare_core_once.sh` wirklich anlegt** —
`karl`, `gerd`, `anastasia` (`G-068`). Ein `rm -f` auf einen Namen, den es nie
gab, meldet Erfolg und lässt die echte Datei liegen; deshalb steht hinter
jedem Löschen ein `test ! -e`, genau wie im Kettenrückbau in Abschnitt 8.

**Gelöscht wird durch einen Wegwerf-Container, nicht durch `sudo rm`** (`G-072`).
Die Tokendateien legt der Prepare-Container an; über SSH gehören sie einem
fremden Benutzer, und `sudo rm` ist von der passwortlosen Regel nicht gedeckt.
Ein gescheiterter Rückbau ist hier der teuerste Ausgang überhaupt: Die
Credentials sind widerrufen, aber die Tokendateien lägen weiter auf der NAS.
Gemountet wird genau der Secretordner dieses Pakets — kein breiteres Ziel —,
und `postgres:17-alpine` ist das Image, das der Schritt eine Zeile darüber
ohnehin gerade benutzt hat, also kein Pull und kein neues Image.

### 6.5 Die zwei liegengebliebenen Nachrichten

`G-053`: Zwei Antworten des Agenten vom 2026-09-01 stehen im Posteingang der
Identität `CEO-TG-CHAIN20260901` auf `DELIVERED`. Sie werden über die Regeln
des Busses geschlossen, nicht per `UPDATE` (Leitplanke 3).

**Das braucht einen Zugang für diese Identität**, und deren Credential ist
widerrufen. Ein `REVOKED`-Credential lässt sich nie reaktivieren, es braucht
also ein neues mit eigenem Lauf-Suffix. Der Schritt ist damit größer als er
aussieht und **steht bewusst als offene Entscheidung**: Entweder ein neuer
Zugang für die Altidentität, oder die beiden Nachrichten bleiben als
dokumentierter Altbestand stehen, bis der nächste Kettenlauf ohnehin unter
neuer Identität läuft. Ich schlage das Zweite vor — der Befund ist behoben,
der Altbestand ist benannt, und ein Zugang für eine stillgelegte Identität
schafft mehr Angriffsfläche als er Ordnung schafft.

### 6.6 Separates Kettenfenster und `chain_audit.sql`

Braucht zusätzlich einen Telegram-Testbot und die breitere Firewall-Regel.
**Ohne Bot-Token entfällt dieser Schritt**, und dann bleibt `G-030` offen —
das ist der Preis und er gehört benannt, nicht übersprungen.

Vor Beginn wird genau eine frische Laufkonfiguration angelegt. Sie bleibt bis
nach Audit und Cleanup dieselbe; dadurch können Suffix, Identität, Task und
Rückbau nicht mehr auseinanderlaufen (`G-063`):

```bash
ssh synology "cd /volume1/docker/Startup/chain-test && cp chain-run.env.example chain-run.env"
```

Jetzt in `chain-run.env` einen neuen Suffix und den dazu passenden Task setzen,
dann prüfen. Keine Zugangsdaten gehören in diese Datei.

```bash
ssh synology "cd /volume1/docker/Startup/chain-test && sh validate_chain_run_config.sh chain-run.env"
```

Die weitere Schrittfolge steht auch in `chain-test/README.md`:

```bash
ssh synology "cd /volume1/docker/Startup/chain-test && sudo /usr/local/bin/docker compose --env-file chain-run.env -f compose.chain-prepare.yaml run --rm --no-deps -T chain-prepare"
ssh synology "cd /volume1/docker/Startup/chain-test && sudo /usr/local/bin/docker compose --env-file chain-run.env -f compose.chain-run.yaml up --build"
```

**Der nächste Schritt ist von Hand.** Der Kettenlauf startet zwei Container,
die auf Telegram warten; die Anfrage tippt der CEO im Chat:

```text
/task AGENT-ENG-001 <CHAIN_TASK_ID aus chain-run.env> | Kurze Lagebeurteilung | Drei Saetze
```

Erwartet: erst `PENDING … registriert`, dann eine `NACHRICHT`-Benachrichtigung.
Danach beide Container beenden:

```bash
ssh synology "cd /volume1/docker/Startup/chain-test && sudo /usr/local/bin/docker compose --env-file chain-run.env -f compose.chain-run.yaml down"
```

Danach die Rekonstruktion, lesend:

```bash
ssh synology "cd /volume1/docker/Startup/chain-test && sh validate_chain_run_config.sh chain-run.env && . ./chain-run.env && sudo /usr/local/bin/docker compose -f ../compose.yaml cp chain_audit.sql db:/tmp/chain_audit.sql && sudo /usr/local/bin/docker compose -f ../compose.yaml exec -T db psql -U workforce_app -d workforce -v ON_ERROR_STOP=1 -v run_suffix=\"\$CHAIN_RUN_SUFFIX\" -v task_id=\"\$CHAIN_TASK_ID\" -f /tmp/chain_audit.sql"
```

Erwartet: `positiv_audit = PASS` mit fünf von fünf Etappen — einschließlich
`connector_acknowledges_the_reply`, das vor `G-053` strukturell fehlte — und
`nichts_offen = PASS`. Die Telegram-Update-ID wird aus dem Task-Ereignis
abgeleitet; `update_id=0` oder eine manuell kopierte ID gibt es nicht mehr.
Danach die Kopie im Container entfernen:

```bash
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db rm -f /tmp/chain_audit.sql"
```

## 7. Effizienzbericht

Der Abschlussartefakt aus der CEO-Ergänzung. Der Worker schreibt ihn nach
`AGENT_REPORT_PATH`; die kurze Zusammenfassung steht ohnehin im Protokoll des
Laufs. Er enthält bauartbedingt keine Nutzlast und kein Geheimnis.

Gelesen wird er als Ganzes: Datenmenge, Felder, Provideraufrufe, Tokens
beziehungsweise gekennzeichnete Schätzung, Kostenobergrenze, Route und
Dublettenentscheidung je Vorgang.

## 8. Rückbau des Kettenfensters

In dieser Reihenfolge, und jeder Schritt wird **nachgemessen**:

```bash
ssh synology "cd /volume1/docker/Startup/chain-test && sudo /usr/local/bin/docker compose --env-file chain-run.env -f compose.chain-cleanup.yaml run --rm --no-deps -T chain-cleanup"
ssh synology "sudo /usr/local/bin/docker run --rm -v /volume1/docker/Startup/chain-test/secrets:/secrets postgres:17-alpine sh -c 'rm -f /secrets/chain_token_connector /secrets/chain_token_agent /secrets/telegram_bot_token && test ! -e /secrets/chain_token_connector && test ! -e /secrets/chain_token_agent && test ! -e /secrets/telegram_bot_token'"
```

Auch hier löscht ein Wegwerf-Container und nicht `sudo rm` (`G-072`),
gemountet auf genau den Secretordner dieses Pakets. `telegram_bot_token` legt
kein Skript an — es kommt von Hand dorthin —, muss aber genauso weg: Es ist das
einzige Geheimnis dieses Fensters, das nach draußen reicht.

Danach:

```bash
ssh synology "cd /volume1/docker/Startup && sh nas_status.sh"
```

Erwartet: Kanal `DISABLED`, 0 aktive Credentials, fünf Gates `PASS`, Exit 0.

**Die Firewall-Regel wird nachgesehen, nicht nachgelesen** (`G-007`). Eine
dokumentierte Rücknahme, die nie stattgefunden hat, ist schlimmer als eine
offene Regel.

Die drei exakten Ketten-Tokenpfade werden gelöscht und ihre Abwesenheit wird
im selben Befehl geprüft. Wildcards und ein bloßes leeres `ls` sind kein
Nachweis. `chain-run.env` enthält keine Zugangsdaten; sie bleibt für die
Zuordnung des Nachweises erhalten und kann anschließend in `Versionen/`
datiert abgelegt werden.

## 9. Abbruch

Bei einem Abbruch im Core-Fenster: Abschnitt 6.4 fahren. Bei einem Abbruch
**nach erfolgreichem Ketten-Prepare**: Abschnitt 8 fahren. Chain-Cleanup darf
nicht mit einem unbekannten Suffix probeweise gestartet werden; sein Guard
verweigert das zu Recht. Danach immer `nas_status.sh`. Das Fenster ändert weder
Schema noch Image, ein Rückfall auf die Sicherung ist deshalb **nicht** nötig
— zurückzunehmen sind Kanalzustand, Credentials und Token-Dateien.

Sollte doch ein Schemazustand entstanden sein, der nicht vorgesehen war: Die
Sicherung aus Abschnitt 3 ist der Rückfallpunkt, und der Weg dahin steht in
`evidence/2026-09-01_backup_acl_und_restore.md` — erst Rollen-Dump, dann
Datenbank-Dump.

## 10. Was dieses Fenster nicht leistet

- **Kein Modelllauf.** Echo überall. Ein bezahlter Aufruf braucht ein eigenes
  CEO-Gate, so steht es in der CEO-Ergänzung.
- **Keine Migration.** Alle Gates bleiben zu, `004` und `008` unangewendet.
- **`G-045` bleibt offen.** Die Eigentümertrennung ist eine eigene Migration
  mit eigener Probe und eigener Freigabe.
- **Ohne Telegram-Bot-Token bleibt `G-030` offen**, auch wenn alles andere
  `PASS` meldet. Eine Gate-Einstufung nennt nur, was der Lauf wirklich
  ausgeübt hat (`G-015`).
