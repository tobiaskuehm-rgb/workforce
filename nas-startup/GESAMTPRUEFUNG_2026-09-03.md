# Gesamtprüfung des aktiven Release-Kandidaten – Stand `557df50`

**Auftrag:** Gerds verbindlicher nächster Schritt vor dem Integrationslauf
(`REVIEW_GERD.md`, Commit `b7c593b`), im Auftrag des CEO. Drei Pässe über den
aktiven Umfang, nur neue, konkrete Befunde, kein Umbau, kein Testlauf.

**Prüfstand:** `557df50` — der saubere Commit nach `G-080`/`G-081`. Während
der Prüfung wurde nichts korrigiert und nichts eingemischt; dieses Dokument ist
das einzige Ergebnis.

**Kennzeichnung:** Die Befunde tragen das Präfix `GP-2026-09-03-NN`
(Gesamtprüfung) und **keine `G-`Nummer** — die vergibt Gerd (`G-006`). Er
übernimmt, nummeriert um oder weist zurück; Antworten folgen unter demselben
Tag in `REVIEW_ANTWORTEN.md`, sobald er entschieden hat.

**Umfang:** die über `deploy_paths.txt` ausgelieferten Pfade — `workforce-api`,
`workforce-agent`, `telegram-connector`, `chain-test`, `bus-realtest`,
`postgres-init`, `postgres-tests`, `compose.yaml`, die Betriebsskripte und
das Phase-5-Runbook — gegen `CLAUDE.md`, `DEC-027`/`ENG-008`, die CEO-Ergänzung
zu Phase 5 und die dokumentierten Betriebsgrenzen. Historische ZIPs und
Altberichte nur bei konkretem Widerspruch; es gab keinen.

**Grenzen:** Auf der NAS wurde nichts ausgeführt und nichts gelesen. Jede
Gegenprobe unten lief lokal gegen die echten Module mit den projekteigenen
Testdoubles (`FakeBus`, `ScriptedProvider`, `AuditStore` auf einer
Temp-Datei) oder als Shell-Reproduktion der fraglichen Zeile. Wo eine Aussage
nur auf der NAS entscheidbar wäre, steht das dabei.

## Ergebnis

Der Kern hält, was die Dokumentation behauptet, und die drei Pässe haben das
nachgemessen statt nachgelesen — Einzelheiten unter „Geprüft und nicht
bestätigt". **Neun neue Befunde**, keiner davon `hoch`: fünf `mittel`, vier
`niedrig`. Zwei der fünf liegen auf dem Weg, den der Integrationslauf nehmen
soll (`GP-01`, `GP-02`), zwei in der Betriebsdokumentation, an der Gerds Gate
hängt (`GP-04`, `GP-05`), einer an der zweiten Datengrenze (`GP-03`).

Keiner der neun blockiert den Integrationslauf für sich; `GP-04` und `GP-05`
gehören **vor** das Fenster, weil das Fenster genau diese Zeilen ausführt.

---

## `GP-2026-09-03-01` – Ein Budgetstopp vor dem Provideraufruf lässt den Claim stehen

**Schwere:** mittel — die Nachricht wird im nächsten Lauf als Dublette
übergangen, und ihre Versuche verbraucht die Decke des Laufs, nicht sie selbst

**Dateien:** `workforce-agent/agent_worker.py`:225-231, 310-324, 426-429;
`workforce-agent/state_store.py`:144-158

**Beobachtung.** `handle_message()` nimmt den Claim (`state.claim()`,
Z. 226) und reserviert danach das Providerbudget (`reserve_provider_call()`,
Z. 315). Scheitert die Reservierung — `check_message()` prüft `>=` auf den
Ist-Stand, die Reservierung `>` auf Ist **plus** konservative Ein- und
Ausgabe, dazwischen liegt am Ende jedes Laufs ein Fenster —, propagiert
`BudgetExhausted` aus der Funktion heraus, **ohne** dass der Claim
freigegeben wird. `record_failure()` wird nur beim gescheiterten Senden
gerufen (Z. 427). Gegenprobe, lokal gegen die echten Module:

```
Lauf 1: BudgetExhausted tokens      Provider gesehen: 0 | gesendet: 0 | acks: 0
Zustand nach Lauf 1: state='IN_PROGRESS', attempts=1
Lauf 2 (5 min spaeter, frisches Budget): ALREADY_HANDLED | Provider gesehen: 0
Lauf 3 (nach Ablauf der Lease):          Claim(state='IN_PROGRESS', attempts=2)
```

**Auswirkung.** Die Nachricht bleibt auf dem Bus `DELIVERED` (richtig), ist
aber lokal 30 Minuten lang „in Arbeit", obwohl niemand an ihr arbeitet. Der
nächste Lauf meldet `ALREADY_HANDLED` und bucht im Effizienzbericht
`DUPLICATE_SUPPRESSED` — ein Vorgang, den es nie gab. Jede abgelaufene Lease
kostet einen Versuch; nach drei Budgetstopps an derselben Stelle ist die
Nachricht `EXHAUSTED` und bekommt die Schlussmeldung „konnte nach mehreren
Versuchen nicht bearbeitet werden" — ausgelöst von der Decke des Laufs, nicht
von der Nachricht. Das ist `G-013` mit umgekehrtem Vorzeichen: Dort wurde der
Claim zu Recht **nicht** freigegeben, weil etwas Dauerhaftes entstanden war.
Hier ist nichts entstanden — kein Aufruf, keine Antwort —, und der eigene Satz
aus `agent_worker.py` Z. 424 gilt: „Nothing durable was produced, so hand the
message back for a retry."

**Kleinste sichere Korrektur.**

- `BudgetExhausted` aus `reserve_provider_call()` fangen, `state.record_failure()`
  rufen (Claim frei, Versuch **nicht** hochzählen — `record_failure` erhöht ihn
  nicht, der nächste `claim()` schon; deshalb `attempts` in diesem Pfad
  zurücknehmen oder den Zähler an einen echten Fehlschlag binden) und die
  Ausnahme dann weiterreichen.
- Ein Test: Budgetstopp vor dem Aufruf → Bus unberührt, Provider ungesehen,
  Claim frei, `attempts` unverändert; Gegenprobe der heutige Zustand.
- Nicht `check_message()` verschärfen: Die Lücke ist die Reservierung, nicht
  die Vorprüfung.

## `GP-2026-09-03-02` – Der Connector verliert ein Update, wenn er zwischen Claim und Abschluss stirbt

**Schwere:** mittel — ein `/task`-Befehl des CEO verschwindet ohne Antwort und
ohne Auditzeile, die es sagt

**Dateien:** `telegram-connector/telegram_connector.py`:525-555, 743-763,
874-885

**Beobachtung.** `process_update()` schreibt das Update als `CLAIMED` in
`processed_updates` (Z. 754) und setzt es erst am Ende auf `PROCESSED` oder
`FAILED`. Stirbt der Prozess dazwischen — Container-Neustart, OOM, Stromausfall
—, bleibt `CLAIMED` stehen. Der Telegram-Offset wurde noch nicht
weitergerückt (Z. 880-882 laufen nach `process_update`), also liefert
`getUpdates` dasselbe Update erneut. `claim_update()` sieht den Primärschlüssel,
vergleicht nur den Payload-Hash und antwortet `DUPLICATE` — unabhängig vom
`processing_status`. Gegenprobe gegen `AuditStore` auf einer Temp-Datei:

```
1. Lauf, claim: CLAIMED           (kein finish_update - der Prozess stirbt)
2. Lauf, dasselbe Update erneut:  DUPLICATE
Zustand im Speicher:              CLAIMED
```

Anders als der Agent (`state_store.py`, Lease von 1800 s, `BEGIN IMMEDIATE`,
`attempts`) kennt der Connector-Speicher **keine Lease** und keinen Weg
zurück aus `CLAIMED`.

**Auswirkung.** Der Befehl ist weg: kein Task, keine Nachricht, keine
`FEHLER`-Antwort im Chat, und die Auditzeile lautet `DUPLICATE_IGNORED` — die
Datenbank des Connectors sagt „schon erledigt" über etwas, das nie begonnen
hat. Dieselbe Klasse wie `G-001`/`G-002`, auf der Eingangsseite: Der Claim ist
dauerhaft, die Arbeit nicht. Im Kettenfenster ist die Task-Id auf genau eine
festgelegt (`chain-run.env`); ein verlorener Befehl lässt sich dort nicht
„einfach nochmal" schicken, ohne dass der zweite `update_id` eine zweite
Nachricht an den Agenten erzeugt (`bus_create_task` ist idempotent, die
Nachricht mit `IDEM-TG-<update_id>` nicht).

**Kleinste sichere Korrektur.**

- `claim_update()` behandelt `CLAIMED` mit gleichem Hash und abgelaufener Frist
  wie `FAILED` bei Benachrichtigungen (`claim_notification()` kennt das Muster
  schon, Z. 579-589): zurück auf `CLAIMED`, Rückgabe `RETRY`, Versuch zählen.
- Ohne Frist geht es nicht — sonst nimmt ein zweiter Prozess ein laufendes
  Update weg. Dieselbe Lease-Idee wie im Agenten, gern derselbe Wert.
- Ein Test: Claim, kein Abschluss, zweiter Store auf derselben Datei, dasselbe
  Update → wird verarbeitet; Gegenprobe innerhalb der Frist → nicht.

## `GP-2026-09-03-03` – Die zweite Datengrenze behandelt den Betreff als Metadatum

**Schwere:** mittel — unter der Voreinstellung `METADATA_ONLY` erreicht
Betrefftext interner Nachrichten die Telegram-Server; `G-029` hat denselben
Text für die erste Grenze als Inhalt eingestuft

**Dateien:** `telegram-connector/telegram_connector.py`:35-41, 970-978,
1012-1015; `chain-test/chain.env.example` (Absatz zu `METADATA_ONLY`)

**Beobachtung.** Der Kommentar zur Outbound-Policy führt unter
`METADATA_ONLY` ausdrücklich „subject" (Z. 37). `publish_inbox_notifications()`
baut die Benachrichtigung unter **jeder** Policy mit `Betreff: {subject}`
(Z. 1015), bis 120 Zeichen. `G-029` hat für `data_boundary.py` festgehalten:
„Der Betreff ist Inhalt, nicht Metadatum — Menschen schreiben die eigentliche
Anfrage hinein", und die Korrektur nahm ihn aus `METADATA_ONLY` heraus. Die
zweite Grenze — dieselbe Klasse Empfänger, nämlich ein fremder Cloud-Dienst,
und das sagt der Kommentar Z. 43-46 selbst — hat diese Entscheidung nie
bekommen. `REVIEW_GERD.md` Z. 407 und 503 betreffen ausschließlich den
Agenten.

**Auswirkung.** Im Kettenlauf ist der Betreff `Re: CEO-Pilotauftrag <Task>`
und harmlos. Im Betrieb schreibt ein Mensch „Kündigung Müller prüfen" in den
Betreff, und die Voreinstellung, die „nur Metadaten" verspricht, trägt genau
diesen Satz zu Telegram. Zwei Grenzen desselben Projekts beantworten dieselbe
Frage entgegengesetzt, und beide nennen ihre Antwort `METADATA_ONLY`.

**Kleinste sichere Korrektur.**

- Betreff nur unter `BODY` mitsenden; unter `METADATA_ONLY` Nachrichten-Id,
  Absender, Task-Referenz und Status — nichts, das ein Mensch getippt hat.
- Der Fingerabdruck (`safe_payload`, Z. 973-978) enthält den Betreff und
  bliebe davon unberührt; er ist lokal.
- Kommentar Z. 35-41 und die Prosa in `chain.env.example` nachziehen, und den
  Feldsatz je Policy als Konstante führen, gegen die ein Test prüft — wie
  `_ALLOWED_FIELDS` in `data_boundary.py` (`G-054`).
- Falls der Betreff im Chat bewusst gewollt ist: dann heißt die Policy nicht
  `METADATA_ONLY`, und die Entscheidung gehört datiert daneben.

## `GP-2026-09-03-04` – `nas_status.sh` hat zwei Wege, bei denen es `PASS` meldet, ohne hinzusehen

**Schwere:** mittel — es ist das Preflight, an dem Gerds Gate und Abschnitt 2
des Runbooks hängen

**Datei:** `nas_status.sh`:35-39, 61-68

**Beobachtung, erste Hälfte.** Der API-Block ruft
`docker exec startup-workforce-api-1 …` (Z. 35) — ein abgeleiteter
Containername, gegen den dieses Projekt seit `G-042` eine Regel hat und den
`backup_task.sh` deshalb über `docker compose ps -q` auflöst. Schlägt der
Aufruf fehl, druckt `|| echo "(API nicht erreichbar)"` einen Hinweis und
**zählt kein Problem**. Heute stimmt der Name; er ist kein Versprechen.

**Beobachtung, zweite Hälfte.** Der Datenbankblock endet mit
`… psql -f /tmp/q.sql' 2>&1 | grep -vE "^\(|^$" || problems=$((problems + 1))`.
Der Status der Pipeline ist der von `grep`, und `grep` ist erfolgreich, sobald
es eine Zeile ausgibt — auch wenn diese Zeile `psql: error: …` lautet.
Gegenprobe, lokal:

```
(printf 'psql: error: … FATAL: password authentication failed\n'; exit 2) 2>&1 | grep -vE "^\(|^$" || echo "PROBLEM GEZAEHLT"
psql: error: … FATAL: password authentication failed
Exit der Pipeline: 0                       <- nicht gezaehlt
(exit 2) 2>&1 | grep -vE "^\(|^$" || echo … -> PROBLEM GEZAEHLT (nur bei leerer Ausgabe)
```

Genau die Klasse, die der Kommentar acht Zeilen tiefer (Z. 71-74) für
`run_gate()` beschreibt und dort behebt — hier ist sie stehen geblieben.

**Auswirkung.** Ein `nas_status.sh`, dessen API-Aufruf ins Leere geht oder
dessen `psql` an einem falschen Passwort scheitert, endet mit `RESULT: PASS`,
solange die fünf Gates grün sind. Die Zeilen „Kanal `DISABLED`, 0 aktive
Credentials, Migrationen …", die das Runbook in Abschnitt 2, 6.4 und 8 als
Abbruchkriterium liest, fehlen dann schlicht in der Ausgabe — und ein
fehlender Wert ist kein Abbruch, wenn niemand ihn vermisst. Das ist die
Fehlerklasse aus Regel 45: Ein nicht gemessener Punkt muss ein Fehlschlag
sein.

**Kleinste sichere Korrektur.**

- Beide Blöcke wie `run_gate()`: Ausgabe in eine Variable, Exitcode
  festhalten, danach drucken, `problems` bei Exitcode ≠ 0 erhöhen.
- Den API-Container über `docker compose ps -q workforce-api` auflösen, wie
  `backup_task.sh` es für `db` tut.
- Die Werte, auf die das Runbook sich beruft (Kanal, Credentials,
  Migrationen), gegen Erwartungswerte prüfen, wenn `nas_status.sh` als
  Preflight läuft — sonst bleibt „Abbruch, wenn nicht Kanal `DISABLED`" eine
  Leseaufgabe.

## `GP-2026-09-03-05` – Das Phase-5-Runbook führt den `G-080`-Deploy weiter aus

**Schwere:** mittel — ein ausführbares Dokument, das im Fenster Zeile für
Zeile abgearbeitet wird, enthält den Befehl, den `G-080` gerade entfernt hat

**Datei:** `PHASE5_RUNBOOK.md`:94-98

**Beobachtung.** Abschnitt 4 lautet unverändert:

```
COPYFILE_DISABLE=1 tar czf - -T /tmp/startup-phase5-files.txt | ssh synology "cd /volume1/docker/Startup && tar xzf - && find . -name '._*' -delete"
```

Das ist die Pipeline ohne `pipefail` **und** das rekursive Löschen außerhalb
des Manifests — beides `G-080`, in `deploy_to_nas.sh` und `HANDOVER.md`
behoben, hier nicht. Dazu ist der Abschnitt jetzt eine zweite Kopie der
Prozedur, die als `deploy_to_nas.sh` versioniert und getestet ist — dieselbe
Klasse wie die Deployliste vor `G-052`: Zwei Abschriften derselben Sache
laufen auseinander, und die, die im Fenster gelesen wird, ist die falsche.
`test_runbook_targets.py` prüft Namen und Verhalten, aber kein Verbot eines
Remote-`-delete`, deshalb blieb es grün.

**Auswirkung.** Wer das Fenster nach Dokument fährt, löscht auf der NAS
außerhalb des Manifests — mit CEO-Freigabe für das Fenster, aber ohne dass
jemand diesen Effekt freigegeben hätte.

**Kleinste sichere Korrektur.**

- Abschnitt 4 auf `sh deploy_to_nas.sh` zurückführen; die drei Zeilen darunter
  entfernen, nicht „auch noch" stehen lassen.
- `test_runbook_targets.py`: kein ausgeführter Codeblock enthält `-delete`
  oder `| ssh`; Gegenprobe mit der alten Zeile.

## `GP-2026-09-03-06` – Die Bestätigungsnotiz sagt „bearbeitet und beantwortet", auch wenn der Agent abgelehnt hat

**Schwere:** niedrig — aus der Datenbank allein ist Antwort und Ablehnung nur
über den Antworttext zu unterscheiden

**Datei:** `workforce-agent/agent_worker.py`:438-444, 362-366

**Beobachtung.** Der Acknowledge trägt in allen Ausgängen dieselbe Notiz.
Gegenprobe:

```
ANSWERED        result=ANSWERED  ack=ACCEPTED note='Vom Agenten bearbeitet und beantwortet.'
Providerfehler  result=REFUSED   ack=ACCEPTED note='Vom Agenten bearbeitet und beantwortet.'
                Antworttext: 'Diese Anfrage konnte technisch nicht bearbeitet werden (…'
Modell-Refusal  result=REFUSED   ack=ACCEPTED note='Vom Agenten bearbeitet und beantwortet.'
```

Der Antworttext beim Providerfehler sagt zugleich „Sie bleibt offen und
braucht eine manuelle Pruefung" (Z. 363-364), der Bus-Datensatz sagt
`ACCEPTED` mit „bearbeitet".

**Auswirkung.** Die Auditregel dieses Projekts verlangt Rekonstruktion allein
aus der Datenbank. Ein `SELECT` über `bus_messages` sieht bei einer
Ratenbegrenzung des Providers dasselbe wie bei einer fachlichen Antwort; erst
das Lesen des Antwortkörpers unterscheidet. Der Effizienzbericht weiß es —
aber der liegt auf einem Volume, nicht im Bus.

**Kleinste sichere Korrektur.** Die Notiz trägt den Ausgang und bei Ablehnung
die Kennung: `Vom Agenten beantwortet.` / `Vom Agenten abgelehnt:
AGENT_PROVIDER_RATE_LIMITED`. Sie ist auf 1000 Zeichen begrenzt und unterliegt
keiner Bezeichner-`CHECK`; die Kennung ist ohnehin `^[A-Z0-9_]+$`. Und den
Satz „bleibt offen" gegen die Wirklichkeit tauschen — die Nachricht ist
bestätigt, offen ist die fachliche Frage.

## `GP-2026-09-03-07` – Der Effizienzbericht überschreibt sich bei jedem Lauf, entgegen dem Kommentar

**Schwere:** niedrig — das Abschlussartefakt der CEO-Ergänzung überlebt genau
einen Lauf

**Dateien:** `workforce-agent/agent_worker.py`:611-616, 637, 577-579;
`workforce-agent/workforce-agent.env.example` (`AGENT_REPORT_PATH`)

**Beobachtung.** `main()` begründet die `run_id` mit „damit zwei Berichte sich
nie ueberschreiben" (Z. 613). Die `run_id` steht aber nur **im** JSON; der
Dateipfad ist `AGENT_REPORT_PATH` — in der Beispielkonfiguration
`/var/lib/startup-agent/efficiency.json`, für jeden Lauf derselbe —, und
`write_report()` öffnet ihn mit `"w"`. Der zweite Lauf ersetzt den ersten.

**Auswirkung.** Leitplanke 7: Ein Kommentar behauptet eine Absicherung, die
der Code nicht hat. Nach zwei Läufen im selben Fenster gibt es einen Bericht.

**Kleinste sichere Korrektur.** `run_id` in den Dateinamen (`efficiency-<run_id>.json`)
oder mit `"x"` öffnen und eine vorhandene Datei als Fehler melden; den
Kommentar entsprechend. Ein Test, der zwei Läufe schreibt und zwei Dateien
verlangt.

## `GP-2026-09-03-08` – `compose.agent.yaml` verlangt und mountet den Anthropic-Schlüssel auch für einen Echo-Lauf

**Schwere:** niedrig — ein Container bekommt ein Geheimnis, das er nicht
benutzt (`G-017`), und der Kopf der Datei sagt das Gegenteil

**Datei:** `workforce-agent/compose.agent.yaml`:7-11, 28-30, 51-55

**Beobachtung.** Der Kopf: „With `AGENT_PROVIDER=echo` it needs neither a key
nor the internet." Der Dienst listet `secrets: anthropic_api_key` ohne
Bedingung, und `secrets.anthropic_api_key.file: ./secrets/anthropic_api_key`
lässt Compose ohne die Datei gar nicht starten. Ein Echo-Lauf braucht also
eine Schlüsseldatei, und der Container, der keinen Provider erreicht, hält
den bezahlten Schlüssel unter `/run/secrets`. `compose.chain-run.yaml` macht
es richtig: nur `agent_bus_token`.

**Kleinste sichere Korrektur.** Zwei Dienste oder zwei Dateien — Echo ohne
den Schlüssel, Modell mit —, und `test_compose_secrets.py` verlangt, dass ein
Dienst mit `AGENT_PROVIDER=echo` keinen Modellschlüssel gemountet hat.

## `GP-2026-09-03-09` – Die Beispielkonfiguration des Agenten startet nicht

**Schwere:** niedrig — fail-closed, aber der erste dokumentierte Trockenlauf
endet mit einer Kennung, die auf das Falsche zeigt

**Datei:** `workforce-agent/workforce-agent.env.example`
(`AGENT_PROVIDER=echo`, `AGENT_MODEL=claude-opus-5`)

**Beobachtung.** Unverändert kopiert, wie der Kopf der Datei es vorsieht:

```
AGENT_PROVIDER = echo | AGENT_MODEL = claude-opus-5
build_provider verweigert: AGENT_MODEL_PROVIDER_MISMATCH:claude-opus-5
```

`build_provider()` nimmt `AGENT_MODEL`, wenn gesetzt, und bindet es an den
Provider; `claude-opus-5` gehört zu `claude`. Die Kennung sagt „Modell passt
nicht zum Provider" — richtig, aber der Operator hat nur die Vorlage kopiert.
`agent.chain.env.example` setzt kein `AGENT_MODEL` und läuft.

**Kleinste sichere Korrektur.** In der Vorlage `AGENT_MODEL` leer lassen
(auskommentiert, mit dem Hinweis, dass es nur beim Modellprovider gesetzt
wird), und ein Test, der jede `.env.example` des Pakets durch
`build_provider()` schickt — die Vorlage ist die Konfiguration, die kopiert
wird.

---

## Geprüft und nicht bestätigt

Damit Gerd diese Wege nicht noch einmal geht. Jeder Punkt ist gemessen, nicht
gelesen, wo das lokal ging:

- **Die Datengrenze ist eine Funktion.** Außer `agent_worker.py` ruft kein
  Modul `Provider.complete()`, `prepare_outbound()` oder `render_for_prompt()`
  (`worker_core_test.py` reicht einen Provider durch, ist ein Testharness).
  Kein zweiter Weg nach draußen.
- **Der Agent ist werkzeuglos**, Routing kommt aus dem Bus-Datensatz
  (`_send_reply`, Empfänger = `sender_id`); der Injektionstest
  (`test_injected_instructions_cannot_redirect_the_reply`) prüft den
  Empfänger am `FakeBus`, nicht am Text — substanziell, nicht formal.
- **Idempotenz auf dem Bus:** `bus_send_message` und `bus_create_task`
  geben bei identischer Wiederholung den Datensatz zurück und werfen `23505`
  bei abweichendem Inhalt; die Nachrichten-Id wird in der API aus
  `token_hash:project:idempotency_key` abgeleitet, so wie `CLAUDE.md` es sagt.
  Die Attrappe `ChainWorld` modelliert dasselbe.
- **Rückbaubarkeit 009/010:** `010` liest sein Ziel aus zwei Ankern, nimmt
  Tabellen-, Sequenz-, Funktions-, Schema- und Vorgabe-Rechte pauschal
  zurück, lässt die Rolle bewusst stehen; `009` prüft seit `G-078`/`G-079`
  dieselben Anker und die Mitgliedschaften vor der ersten Änderung; beide
  Gates schließen einander aus. Die eine dokumentierte Grenze bleibt: ein
  zweiter Anlauf ist `011`, kein zweites `009`. **Nicht gemessen** — `010` ist
  auf keiner Instanz gelaufen; das ist der Integrationslauf.
- **Secrets:** API-Schlüssel und DB-Passwort nur aus Dateien, kein
  `startup.env` im API-Container, `AGENT_STRICT_SECRETS` in beiden
  Agenten-Vorlagen, Tokens der Läufe als `secrets:`-Mounts; `docker inspect`
  sähe keinen Wert. Ausnahme ist `GP-08` — ein Schlüssel zu viel, nicht einer
  im Klartext.
- **Rollen:** die API verbindet sich als `workforce_api` (`007`), ohne
  Rückfall auf den Eigentümer; `bus_error()` verallgemeinert unbekannte
  SQLSTATEs zu `503`; jede Ablehnung landet über eine frische Verbindung in
  `bus_denials`, und ein kaputtes Audit macht aus einer 403 keine 500.
- **Kosten:** Reservierung vor dem Aufruf, Aufruf zählt vor dem Versuch, kein
  SDK-Retry, kein Server-Fallback, `is_paid` je Provider; die Allowlist hält
  jedes Modell bei voller Datenmenge unter seiner Aufrufdecke. Randfall: Ein
  8000-Zeichen-Text aus Vier-Byte-Zeichen überschreitet die Opus-Decke über
  die Byte-Reservierung und wird **abgelehnt** — fail-closed, kein Befund.
- **Wiederanlauf des Agenten:** Arbeiten → antworten → bestätigen; `REPLIED`
  wird ohne zweiten Modellaufruf wieder aufgenommen; `EXHAUSTED` bleibt
  beanspruchbar bis zur Schlussmeldung; `BUS_ACK_ALREADY_FINAL` gilt als
  erledigt. Die eine Lücke ist `GP-01`.
- **Telegram-Eingang:** Chat-, Nutzer-, Empfänger- und Task-Allowlist
  fail-closed; Kill Switch vor jeder Verarbeitung; Body nur unter `BODY` und
  nur mit allowlisteter Task-Referenz; erst senden, dann bestätigen; das
  Nachholen einer gescheiterten Bestätigung ist idempotent. Die zwei Lücken
  sind `GP-02` und `GP-03`.
- **Backup:** `backup_task.sh` wartet auf `healthy`, prüft die Abschlusszeile,
  härtet Rechte vor dem Löschen Alter; `check_backup_integrity.sh` prüft
  Alter, Abschlusszeile, `restrict`-Paarigkeit, Größe und das Archiv. Das
  Archiv enthält `startup.env` — deshalb die Rechte — und **nicht**
  `postgres-init/`; die Migrationen liegen im Git auf derselben NAS, ein
  Restore braucht beides. Kein Befund, aber es gehört ins Restore-Runbook.
- **Doppelte Kommunikationswege:** keine. Der Connector meldet, der Agent
  antwortet nur dem Absender, der Core-Roundtrip und `worker_core_test` sind
  Harnesse hinter eigenen Gates.
- **Falschgrüne Tests:** Stichproben an den sicherheitsrelevanten Tests
  (Injektion, Providerfehler, Datengrenze, Telegram-Allowlists, Dubletten)
  prüfen Wirkungen an Attrappen, nicht Text. `test_provider_failure_still_produces_a_reply`
  pinnt dabei den Satz „manuelle Pruefung" — mit `GP-06` ändert sich der Test
  mit.

## Nachweis und Gate

- Prüfstand `557df50`, lokal: `645 + 15 + 44 + 27 = 731` Tests **PASS** auf
  `python3` 3.9.6. Keine Datei außer diesem Dokument und seiner Registrierung
  geändert.
- Sechs Gegenproben lokal gefahren (`GP-01`, `-02`, `-04`, `-06`, `-09`,
  Datengrenze); Ergebnisse stehen bei den Befunden.
- Nicht ausgeführt: NAS-Testlauf, Migration 009/010, Container-Änderung,
  Kanal/Credential, Modellaufruf, produktive Rechteänderung — wie verlangt.

**Übergabe an Gerd.** Empfohlene Reihenfolge, wenn er die Befunde übernimmt:
`GP-05` und `GP-04` vor dem Fenster (das Fenster führt diese Zeilen aus),
`GP-01` und `GP-02` vor dem ersten Lauf, der länger als eine Nachricht dauert,
`GP-03` als Entscheidung des CEO über die zweite Grenze, der Rest gebündelt.
Der Teststatus bleibt, wie Gerd ihn festgelegt hat: **ROT – wartet auf
Gerd-Nachcheck und danach CEO-Freigabe.**
