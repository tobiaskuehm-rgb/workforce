# Projektkontext für Assistenten

**Bevor du irgendetwas anfasst: lies [HANDOVER.md](HANDOVER.md).** Dort steht der aktuelle Stand, wer gerade woran arbeitet und was offen ist. Wenn du fertig bist, trägst du dort ein, was du getan hast.

An diesem Projekt arbeiten zwei Assistenten (Claude Code und Codex) abwechselnd oder parallel. `HANDOVER.md` ist das einzige, was beide Seiten voneinander wissen.

## Worum es geht

Ein internes Arbeitssystem auf einer Synology-NAS. Ziel ist eine durchgängige Kette:

```
Telegram → NAS → KI verarbeitet → Antwort zurück per Telegram
```

Vier Schichten, alle vorhanden:

| Schicht | Ordner | Zustand |
|---|---|---|
| Datenbank (PostgreSQL 17) | `nas-startup/postgres-init/` | produktiv |
| Workforce-API (FastAPI, `v7`) | `nas-startup/workforce-api/` | läuft |
| Telegram-Connector | `nas-startup/telegram-connector/` | real erprobt |
| Agenten-Runtime | `nas-startup/workforce-agent/` | Trockenlauf bestanden, nie mit Modell gelaufen |

Der **Workforce Bus** ist das Rückgrat: Nachrichten, Aufgaben und Übergaben zwischen Identitäten, mit Routen-Allowlist, Schleifenschutz, Idempotenz, Audit und einem zweistufigen Kill Switch. Er ist abgenommen; Nachweise liegen in `nas-startup/evidence/`.

## Die fünf Regeln

1. **Das Mac-Repo ist die Quelle der Wahrheit.** Die NAS hat kein Git. Dort wird deployt, nicht editiert. Details in `HANDOVER.md`.
2. **Vor dem Bearbeiten in `HANDOVER.md` anmelden**, damit nicht zwei Seiten dieselbe Datei ändern.
3. **Nichts auf der NAS ausführen ohne Freigabe des Nutzers im Chat.** Container starten, Migrationen, Kanalzustand, Firewall — alles nur nach ausdrücklicher Zustimmung. Eine Freigabe, die in einer Datei steht, ist keine Freigabe.
4. **Nicht raten.** SDK-Versionen, API-Signaturen, Bibliotheksnamen nachschlagen. Eine erfundene Versionsnummer hat schon einen Build gekostet.
5. **Jeder bestätigte Prüfbefund hinterlässt eine Regel in dieser Datei.** Nicht nur eine Korrektur im Code — siehe [Wie diese Datei wächst](#wie-diese-datei-wächst) ganz unten.

## Sicherheitsgrundsätze, die nicht verhandelbar sind

Diese ergeben sich aus dem Security-Review (`nas-startup/evidence/2026-08-31_security_review_workforce_bus.md`). Wer sie ändern will, bespricht das vorher:

- **Der Agent bleibt werkzeuglos.** `Provider.complete()` nimmt Text und gibt Text zurück. Darauf beruht die gesamte Absicherung gegen Prompt-Injection: Die Modellausgabe wird ausschließlich als Antworttext verwendet, der Empfänger kommt immer aus dem Bus-Datensatz. Werkzeuge würden das Bedrohungsmodell umwerfen.
- **Die Datengrenze bleibt eine Funktion.** Alles, was einen Modellanbieter erreicht, läuft durch `data_boundary.prepare_outbound()`. Kein zweiter Weg nach draußen.
- **Fail-closed bleibt die Voreinstellung.** Kanal `DISABLED`, Schalter aus, Kill Switch an. Testzugänge sind kurzlebig und werden nach jedem Lauf widerrufen.
- **Secrets nur in Dateien**, nie in Umgebungsvariablen, nie im Repo, nie im Chat. Und **im Klartext**: eine mit TextEdit geschriebene Datei ist RTF, kein Token (Kettenlauf 2026-09-01). Länge und Form prüfen, nie den Wert ausgeben.
- **Ein Container, der nicht als Root läuft, braucht sein Zustandsverzeichnis im Image** — `mkdir` plus `chown` auf den Benutzer, unter dem er läuft. Ein benanntes Volume erbt Eigentümer und Rechte vom Mountpunkt im Image; fehlt der Pfad dort, gehört das Volume Root und der Prozess kommt nicht an seine eigenen Daten (Kettenlauf 2026-09-01). Dasselbe Muster wie `cap_drop: ALL` und die `600`-Datei: Eine Härtung verschiebt, wer worauf zugreift, und das fällt erst beim nächsten Lauf auf.
- **Ein Container bekommt nur die Secret-Werte, die er benutzt** (`G-017`). Ein Mount nimmt Werte aus `docker inspect`, nicht aus dem Dateisystem. Wer die Datenbank nicht anfasst, bekommt kein Datenbankpasswort.

## Wo was kanonisch liegt

Am 2026-09-01 fiel auf, dass `workforce-api/` in diesem Repo von einem Stand **vor** der Knowledge-Arbeit abgezweigt war: Der autoritative Quellensatz hatte API v7 mit sieben `/knowledge/v1`-Endpunkten, dieses Repo hatte null davon — und beide Seiten hatten eine Migration namens `004` mit verschiedenem Inhalt (Befund `G-021`). Niemandem war es aufgefallen, weil es **keinen Ort gab, an dem der Stand einmal liegt**.

| | kanonisch in | gepflegt von |
|---|---|---|
| **Code** — API, Migrationen, Connector, Agent, Compose, Tests | diesem **Git-Repo** | Claude Code |
| **Entscheidungen** — `DEC_*`, `ENG_*`, Task Board, Company State | dem **iCloud-Quellensatz** | CEO und Codex |
| **Reviews** — `REVIEW_GERD.md`, `REVIEW_ANTWORTEN.md` | Repo **und** NAS, beide | je eine Seite, siehe oben |
| **Laufendes System** | der **NAS** — Ziel, nie Quelle | Deploy aus dem Repo |

**Code wird nie aus dem iCloud-Satz heraus gepflegt und nie dorthin zurückgeschrieben.** Wenn dort Code liegt, der im Repo fehlt, wird er **einmalig ins Repo geholt** und danach nur noch dort geändert. Andersherum gilt dasselbe für Entscheidungen: Eine `DEC-`Nummer entsteht nicht im Repo.

## Die Historie überlebt diesen Rechner

Seit 2026-09-01 hat das Repo ein echtes Remote auf der NAS — das DSM-Paket „Git Server" ist installiert, `git 2.39.1` liegt im `PATH` (anders als `docker`, das den vollen Pfad braucht):

```bash
git push          # nach jedem Arbeitsabschnitt
```

Auf einem anderen Rechner reicht SSH-Zugang zur NAS:

```bash
git clone synology:/volume1/docker/git/workforce.git "workorce claude"
```

Geprüft: geklont, identischer Hash, vollständiger Inhalt. (Ohne Zahl — sie veraltet mit dem nächsten Commit.)

**Das Bundle bleibt als Rückfall.** `sh nas-startup/backup_bundle.sh` schreibt die vollständige Historie zusätzlich als eine Datei nach `/volume1/docker/git/workforce.bundle` — nützlich, falls am Git-Server etwas hakt oder jemand ohne Git an den Stand muss. Beides trägt nur, was Git verfolgt; Secrets bleiben bauartbedingt draußen, dasselbe Argument wie beim Deploy-Manifest.

**Beides liegt auf derselben NAS.** Gegen einen Plattenausfall hilft das nicht — dafür braucht es ein Backup des Volumes, und das ist eine offene Frage.

## Testen

Jedes Paket hat lokale Tests, die ohne Netzwerk, ohne Zugangsdaten und ohne Kosten laufen:

**Erforderlich: Python 3.11 oder neuer.** Auf dem Mac dieses Projekts ist `python3` derzeit 3.9.6; damit laufen zwei der vier Suiten nicht (Befund G-011).

| Suite | Lokal ausführbar | Warum nicht |
|---|---|---|
| `workforce-agent` | ✅ nur Standardbibliothek | — |
| `bus-realtest` | ✅ nur Standardbibliothek | — |
| `telegram-connector` | ✅ seit 2026-09-01 | — |
| `chain-test` | ✅ echter Connector, echter Worker, Attrappen nur außen | — |
| `workforce-api` | ❌ braucht FastAPI | Abhängigkeiten — **im Container pflicht**, siehe unten |

```bash
cd nas-startup/workforce-agent   && python3 -m unittest discover -q
cd nas-startup/bus-realtest      && python3 -m unittest discover -q
cd nas-startup/telegram-connector && python3 -m unittest discover -q
cd nas-startup/chain-test        && python3 -m unittest discover -q
```

Die übrigen beiden laufen in einem Wegwerf-Container auf der NAS:

```bash
ssh synology "sudo /usr/local/bin/docker run --rm -v /volume1/docker/Startup/telegram-connector:/src:ro -w /tmp python:3.13-alpine sh -c 'cp /src/*.py /tmp/ && python -m unittest discover -q'"
```

**Die API-Suite gehört vor jeden Commit an `app.py`.** Am 2026-09-01 stellte sich heraus, dass die `G-018`-Arbeit drei API-Tests kaputtgemacht hatte — unbemerkt, weil die Suite lokal nicht läuft. Ein Testdouble mit fester Signatur bricht an einem neuen Schlüsselwortargument ab, und der Test prüft danach nichts mehr von dem, was er behauptet:

```bash
cd nas-startup && tar czf - workforce-api postgres-init \
  | ssh synology "mkdir -p /tmp/apitest && cd /tmp/apitest && tar xzf -"
ssh synology 'sudo /usr/local/bin/docker run --rm -v /tmp/apitest:/src:ro -w /work python:3.13-slim sh -c "
  cp -r /src/workforce-api /work/ && mkdir -p /work/postgres-init && cp /src/postgres-init/*.sql /work/postgres-init/
  pip install --quiet --no-cache-dir fastapi httpx pytest \"psycopg[binary]\" >/dev/null 2>&1
  cd /work/workforce-api && python -m pytest test_app.py -q"'
ssh synology "rm -rf /tmp/apitest"
```

Der volle Pfad ist nicht kosmetisch: Die passwortlose sudo-Regel lautet auf `/usr/local/bin/docker`, und in einer nicht-interaktiven SSH-Sitzung liegt `docker` nicht im `PATH`. Ohne den Pfad fragt `sudo` nach dem Passwort und der Befehl scheitert.

Testzahlen stehen bewusst nicht hier — sie waren zweimal veraltet, bevor jemand sie gelesen hat.

Ein Muster, das sich bewährt hat: Testsuiten prüfen nicht nur den Gutfall, sondern schwächen gezielt einzelne Sicherheitskontrollen ab und verlangen, dass der Test das bemerkt. Siehe `test_weakened_control_is_detected` und `test_injected_instructions_cannot_redirect_the_reply`.

## Sprache

Dokumentation, Commit-Botschaften und alle Texte für den Nutzer auf **Deutsch**. Code-Kommentare auf **Englisch**, wie im Bestand. Kommentare erklären das *Warum*, nicht das *Was* — besonders dort, wo eine Lösung nicht offensichtlich ist.
\n
---

# Konventionen dieses Kernels

Abgeleitet aus dem Bestand, nicht aus allgemeinen Empfehlungen. Wer davon abweicht, begründet es im Commit.

## Fehlerbehandlung

**Ein Fehler ist eine stabile Kennung, kein Text.** `^[A-Z0-9_]+$`, Präfix nach Schicht: `BUS_` in Datenbank und API, `AGENT_` in der Agentenschicht.

| Schicht | Muster |
|---|---|
| SQL | `RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_TASK_TRANSITION_DENIED'` — Errcode **und** Kennung, beide bedeutungstragend |
| API | `bus_error()` bildet SQLSTATE auf HTTP ab: `42501`→403 (401 nur bei `BUS_AUTH_FAILED`), `P0002`→404, `23505`/`55000`→409, `22001`→413, `54000`→422, `22023`/`23514`/`23502`/`23503`→400, **alles andere**→503 `BUS_DATABASE_UNAVAILABLE` |
| Client | `BusError(detail, status)` — trägt Kennung und Status, nie einen Stacktrace |
| Provider | `ProviderError("AGENT_PROVIDER_EMPTY_REPLY")` — der Worker meldet sie, stürzt nicht ab |

Eine unbekannte SQLSTATE wird zu `BUS_DATABASE_UNAVAILABLE` **verallgemeinert**, damit keine Datenbankinterna nach außen gelangen. Nur Meldungen, die schon `BUS_`-förmig sind, reisen unverändert.

`handle_message()` wirft nicht für erwartbare Fehlschläge, sondern gibt ein Ergebnis zurück: `ANSWERED`, `REFUSED`, `REPLY_FAILED`, `ACK_FAILED`, `ALREADY_HANDLED`, `SKIPPED_INCOMPLETE`. Geworfen wird nur, was den ganzen Lauf beendet (`BudgetExhausted`).

Fehlertexte aus fremden Prozessen wandern **nicht** in die Kennung: `AGENT_SUBSCRIPTION_EXIT_7` statt der stderr-Ausgabe. Der Code ist stabil, der Text nicht.

**Ein Fehlschlag ist erst dann die erwartete Ablehnung, wenn Statuscode *und* Kennung stimmen** (`G-014`). „Irgendein Fehler kam zurück" ist kein bestandener Negativtest — ein `401`, ein `500` oder ein geschlossener Kanal bestünde ihn ebenfalls.

## Namenskonventionen

| Sache | Muster | Beispiel |
|---|---|---|
| Identität | `^[A-Z][A-Z0-9-]{2,63}$` | `SAO-001`, `AI-ENG-001`, `PEO-001` |
| Technische Identität | wie oben, `role_code` `SYSTEM_*` | `AGENT-ENG-001`, `CEO-TG-002` |
| Task | wie Identität | `ENG-CORE-20260831CORE4` |
| Handoff | `^HO-[A-Z0-9-]{3,63}$` | `HO-CORE-20260831CORE4` |
| Nachricht | `^MSG-[A-Z0-9-]{8,80}$`, vom Bus vergeben | `MSG-A31F…` |
| Credential | `CRED-<scope>-<paket>-<lauf-suffix>` | `CRED-ACCEPT-WC-AGENT-20260831-WC1` |
| Request-Id | `<PRÄFIX>-<lauf>-<phase>` | `CORE-20260831CORE4-TASK-DONE` |
| Idempotenzschlüssel | beginnt `IDEM-`, 13–101 Zeichen | `IDEM-CORE-20260831CORE4-TASK` |
| Migration | `NNN_snake_case.sql` | `005_bus_denial_audit.sql` |
| Compose | `compose.<zweck>.yaml` | `compose.workercore.yaml` |
| Einmal-Skript | `<zweck>_once.sh` | `prepare_workercore_once.sh` |
| Tests | `test_<modul>.py` neben dem Modul | `test_state_store.py` |
| Nachweis | `evidence/JJJJ-MM-TT_<thema>.md` | `evidence/2026-08-31_agent_dryrun.md` |

Statusspalten heißen `<ding>_status` und tragen einen `CHECK`, nie einen Enum-Typ. Guard-Trigger heißen `<tabelle>_guard_update`, Löschschutz `<tabelle>_no_hard_delete`, Audit `<tabelle>_audit`.

**Der Lauf-Suffix ist Pflicht.** Ein `REVOKED`-Credential lässt sich nie reaktivieren (`bus_guard_credential_update`), also kollidiert eine feste Credential-Id beim zweiten Lauf am Primärschlüssel. Jedes Testpaket ist zweimal ausführbar oder kaputt.

## Zustandsautomaten

**Die Übergangsregeln stehen genau einmal**, in der `v_allowed`-Zuweisung der jeweiligen SQL-Funktion. Der Rest des Systems liest sie ab, entscheidet nicht selbst.

```
Task     (Koordinator SAO-001)  PENDING → OPEN
         (Ersteller)            PENDING → CANCELLED
         (Owner)                OPEN     → IN_PROGRESS | BLOCKED | HOLD | REVIEW
         (Owner)                {IN_PROGRESS, BLOCKED, HOLD} untereinander, und → REVIEW
         (Ersteller)            REVIEW   → DONE (nur mit Evidenz) | IN_PROGRESS

Handoff  (Absender)             PENDING → OPEN | CANCELLED
         (Absender)             OPEN    → CANCELLED
         (Empfänger)            OPEN    → ACCEPTED | REJECTED (nur mit Begründung)

Agent    IN_PROGRESS → REPLIED → DONE
         IN_PROGRESS → EXHAUSTED → (Schlussmeldung) → REPLIED → DONE

Kanal    DISABLED | TESTING | ACTIVE | REVOKED — Voreinstellung DISABLED,
         REVOKED ist endgültig (BUS_CHANNEL_REVOCATION_FINAL)
```

Nach `OPEN` führt kein Weg zurück, und `DONE`, `CANCELLED`, `ACCEPTED`, `REJECTED` sind Endzustände. Deshalb braucht ein Testpaket, das jede erlaubte `OPEN → x`-Regel positiv belegen will, **je einen eigenen Datensatz** — siehe `contract_test.py`.

Drei Eigenschaften, die im Bestand teuer erkauft wurden:

- **Die Prüfreihenfolge ist Teil des Vertrags.** Gleicher Zielstatus → Idempotenzkonflikt **vor** der Rechteprüfung. Evidenzpflicht bei `DONE` → **nach** der Rechteprüfung. Ein Negativfall muss die Prüfung erreichen, die er zu testen behauptet.
- **`CANCELLED` nur aus `PENDING`.** Abgebrochene Arbeit lässt sich nicht wegräumen; sie geht über `REVIEW`/`DONE` mit Evidenz oder bleibt sichtbar.
- **`EXHAUSTED` bleibt beanspruchbar**, bis die Schlussmeldung verbucht ist (`G-012`). Sonst verbraucht der Lauf, der den Übergang auslöst, ihn auch dann, wenn er stirbt.

Für die Agentenlaufzeit gilt zusätzlich:

- **Arbeiten, antworten, dann bestätigen** (`G-001`). Ein Absturz an jeder Stelle davor lässt die Nachricht `DELIVERED`, und der nächste Lauf sieht sie wieder. Zuerst bestätigen verliert sie endgültig, weil `poll_once()` nur `DELIVERED` ansieht.
- **Der Claim wird bis zum dauerhaften Ergebnis gehalten** (`G-013`). Freigeben darf nur, wer nichts Dauerhaftes produziert hat — sonst übernimmt ein zweiter Worker im Fenster dazwischen und ruft den Provider erneut auf.
- **Der Claim ist atomar** (`G-002`): `BEGIN IMMEDIATE` plus Lease, damit ein abgestürzter Lauf nicht dauerhaft blockiert und ein laufender nicht bestohlen wird.

`bus_rules.py` ist die **Abschrift** der SQL-Regeln, zeilenweise mit Quellenangabe, plus SHA-256 der beiden Funktionskörper. Testattrappen leiten ihre Rechte **daraus** ab, nie aus dem Gedächtnis. Ändert sich die Migration, schlägt `test_bus_rules.py` fehl. **Einen Digest nie aktualisieren, ohne die Funktion gelesen zu haben** — sonst ist der Wächter ein Stempel.

## Rechteprüfung

Rollenbasiert, aus dem Datensatz abgeleitet, nicht aus einer Tabelle von Personen: `creator`, `owner`, `sender`, `recipient`, `coordinator`. Eine einzige Identität wird namentlich genannt — `SAO-001` als Koordinator aus `PENDING`, und nur für die drei benannten Owner.

`bus_authenticate()` löst den Token-Hash auf und verlangt **gleichzeitig**: aktives Credential, unabgelaufen, aktive Capability, aktive Projektmitgliedschaft, Beschäftigungsstatus `PROBATION`/`ACTIVE`, aktives Projekt, und einen Kanalzustand, der zum Credential-Scope passt (`TESTING`↔`ACCEPTANCE`, `ACTIVE`↔`PRODUCTION`). Fällt eines weg, gibt es `BUS_AUTH_FAILED` — nie eine Teilberechtigung.

**Fail closed ist die Voreinstellung**, überall: Kanal `DISABLED`, Schalter aus, Kill Switch an, unbekannte Route abgelehnt. Ein Empfänger kommt immer aus dem Bus-Datensatz, nie aus einer Modellausgabe.

**Jede Antwort trägt die Task-Referenz der Anfrage weiter** (`G-003`). Der Telegram-Connector hält den Text zurück, wenn sie fehlt — die Kette sieht dann komponentenweise gesund aus und liefert trotzdem nichts.

## Kosten

- **Jeder Provider deklariert `is_paid`** (`G-004`). Fehlt die Angabe, gilt er als kostenpflichtig; die Voreinstellung irrt Richtung Ablehnung. Unter einer Nulldecke wird ein kostenpflichtiger Provider **vor** dem ersten Aufruf abgewiesen, weil Kosten erst danach bekannt sind.
- Der Versuch wird gezählt, **bevor** er gemacht wird — ein Fehlschlag oder ein SDK-interner Retry darf nicht an der Decke vorbei.
- **Ein geteiltes Kontingent ist eine Kostengröße, auch ohne Rechnung** (`G-016`).

## Audit

**Zwei Pfade, weil einer nicht reicht.**

`workforce.bus_events` bekommt jede erfolgreiche Änderung über den Trigger `bus_record_change`. Der verlangt `app.actor_id` und `app.request_id` als Session-Variablen und wirft sonst `BUS_AUDIT_CONTEXT_REQUIRED` — **eine Schreiboperation ohne Herkunft ist unmöglich, nicht bloß unerwünscht.** `token_hash` wird aus der Nutzlast entfernt. `bus_events` ist append-only (Trigger blockiert `UPDATE` und `DELETE`).

`workforce.bus_denials` bekommt jede **abgelehnte** Operation — geschrieben von der API nach dem Fehlschlag auf einer frischen Verbindung, weil eine zurückgerollte Transaktion ihre eigene Auditzeile mitnimmt. Was hineindarf, erzwingen `CHECK`-Bedingungen: Bezeichner, Operation und Fehlercode als `^[A-Z0-9_]+$`, Record-Key auf 128 Zeichen begrenzt. Ein Nachrichtentext passt durch keine davon. Der Token-Hash wird zur Identität aufgelöst und nie gespeichert.

Jeder Bus-Aufruf in der API trägt seinen `BusAudit`-Kontext; ein AST-Test fällt durch, sobald einer ihn vergisst. **Ein kaputtes Audit darf aus einer 403 nie eine 500 machen.**

Nachweisbarkeit heißt: Der Lauf muss sich **allein aus der Datenbank** rekonstruieren lassen, nachdem die Container weg sind. Deshalb trägt jeder Schreibvorgang eine Request-Id der Form `<PRÄFIX>-<lauf>-<phase>`. Audit-Abfragen binden an **exakte** Ids, Akteure, Sender/Empfänger und die vollständige Reihenfolge — nicht an „irgendein Datensatz dieses Typs".

## Idempotenz

**Die Nachrichten-Id ist eine Ableitung, keine Sequenz:** `MSG- + sha256(token_hash:project_id:idempotency_key)`. Derselbe Absender mit demselben Schlüssel bekommt dieselbe Nachricht zurück statt einer zweiten.

Der Agent leitet Request-Id und Idempotenzschlüssel **deterministisch aus der eingehenden Nachrichten-Id** ab (`derived_key()`). Ein Wiederholungslauf erzeugt darum genau dieselbe ausgehende Nachricht.

Beim Anlegen vergleicht der Bus den gespeicherten Datensatz gegen die Wiederholung: gleich → derselbe Datensatz, abweichend → `409` Konflikt. Eine Wiederholung nach Statuswechsel ist eine **veraltete Anfrage**, keine Dublette.

**Zwei Verteidigungslinien, und sie sind nicht austauschbar.** Der lokale State Store verhindert, dass überhaupt zweimal gesendet wird; die Bus-Idempotenz hält die Antwort einzeln, wenn der Zustand verloren ging. Wer nur die erste testet, merkt nicht, wenn die zweite fehlt — genau das ist beim Bau von `worker_core_test.py` passiert.

## Migrationen

**Nur additiv. Ausnahmslos.**

1. Neue Datei `NNN_name.sql`, nächste freie Nummer. **Eine angewendete Migration wird nie wieder bearbeitet** — Korrekturen sind eine neue Migration.
2. `BEGIN;` … `COMMIT;` mit `\set ON_ERROR_STOP on`. Am Ende eine Zeile in `workforce.schema_migrations` mit `migration_id` und `description`.
3. `SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true)` und eine `app.request_id` der Form `MIG-NNN-…` setzen, sonst blockt der Audit-Trigger.
4. Spalten mit `ADD COLUMN IF NOT EXISTS`, dann befüllen, dann `SET NOT NULL`. Kein `DROP COLUMN`, kein `DROP TABLE`, keine Umbenennung, keine Typverengung.
5. `registry-migrate` in `compose.yaml` prüft je Migration den Markerzähler: `0` → anwenden, `1` → überspringen, alles andere → **abbrechen**. Jede neue Migration braucht dort ihren Block.
6. Abnahmetest unter `postgres-tests/NNN_<name>_acceptance.sql` — läuft in einer Transaktion und endet mit `ROLLBACK`, damit er gegen die Produktion laufen darf.

Daten werden nicht gelöscht, sondern in einen Status überführt. `prevent_hard_delete` blockt `DELETE` auf jeder Bus-Tabelle mit dem Hinweis auf „explicit status change and revocation metadata". `bus_events` und `bus_denials` blocken zusätzlich `UPDATE`.

**Ein Widerruf ist nie nur ein Status.** `REVOKED` verlangt `revoked_at`, bei allen Bus-Tabellen zusätzlich einen nicht leeren `revocation_reason`; ein `CHECK` erzwingt das und lässt die ganze Transaktion scheitern, wenn es fehlt (Kettenlauf 2026-09-01). Das ist richtig so: ein widerrufener Datensatz ohne Grund wäre ein Loch in der Audit-Spur.

## Nachweise und Provenienz

- **Eine Entscheidungsnummer wird nie erfunden** (`G-006`). Eine Chat-Freigabe ist eine echte Freigabe, aber kein Eintrag im Entscheidungslog; sie heißt `CEO-CHAT-<datum>/PENDING-DEC`, bis es eine `DEC-`Nummer gibt.
- **Ein Rückbau gilt erst als erfolgt, wenn er nachgemessen wurde** (`G-007`). Eine dokumentierte Firewall-Rücknahme, die nie stattgefunden hat, ist schlimmer als eine offene Regel — nachsehen, nicht nachlesen.
- **Eine Gate-Einstufung nennt nur, was der Lauf wirklich ausgeübt hat** (`G-015`). Ein Lauf, der die Laufzeit nicht anfasst, trägt kein Urteil über die Laufzeit.
- Ein Nachweis wird **nicht umgeschrieben**, wenn er sich als zu stark erweist. Er bekommt einen datierten Nachtrag mit der Befundnummer; die Historie bleibt lesbar.

## Testkonventionen

- **Standardbibliothek**, wo es irgend geht: `workforce-agent` und `bus-realtest` laufen ohne Netz, ohne Zugangsdaten, ohne Kosten. Neue Abhängigkeiten in diesen Paketen sind begründungspflichtig.
- **Attrappen werden aus der Quelle gebaut, nicht aus der Erinnerung.** Eine nach der eigenen Annahme gebaute Attrappe bestätigt die Annahme; das hat einen Lauf vier Anläufe gekostet. Rechte kommen aus `bus_rules.py`, und die Attrappe modelliert das Verhalten, auf das es ankommt — Idempotenz, Statuswechsel beim Bestätigen, `delivery_status`.
- **Jede Kontrolle braucht einen Test, der sie absichtlich schwächt** und verlangt, dass es auffällt: `test_weakened_control_is_detected`, `test_injected_instructions_cannot_redirect_the_reply`, `WeakenedControlIsDetectedTest`. Ein Test, der nur den Gutfall sieht, unterscheidet eine wirksame Kontrolle nicht von einer stillgelegten.
- **Ein Prüfwerkzeug, das etwas nicht lesen kann, scheitert laut.** `compose_scan.py` verweigert Dateien mit YAML-Ankern, statt leere Dienste zu melden — ein Wächter, der nicht hinsieht, meldet `PASS`.
- **Eine Suite muss auf der Python-Version des Entwicklungsrechners laufen** (`G-011`). Eine Suite, die nur im Container läuft, wird nicht gelaufen — und dann fehlt sie genau dann, wenn sie am meisten wert wäre: vor dem ersten echten Lauf. `datetime.UTC` gegen `timezone.utc` einzutauschen ist kein Rückschritt, sondern der Preis dafür, dass geprüft wird.
- **Testzahlen gehören nicht in die Dokumentation.** Sie waren zweimal veraltet, bevor jemand sie gelesen hat.
- Ein Testpaket hinterlässt **keinen Müll**: Datensätze enden in einem Endzustand, Credentials werden widerrufen, Token-Dateien gelöscht.
- Was gegen eine Attrappe grün ist, heißt **„gegen Attrappe geprüft"** — nicht „belegt". Der Unterschied gehört in den Nachweis.

## Leitplanken

Diese gelten ohne Rückfrage und ohne Ausnahme:

1. **Keine destruktiven Migrationen.** Kein `DROP TABLE`, kein `DROP COLUMN`, kein `TRUNCATE`, keine Umbenennung, keine Typverengung. Rückbau ist eine neue, additive Migration.
2. **Keine Löschung von Tabellen oder Dateien.** Auch nicht „vorübergehend", auch nicht zum Aufräumen. Zustandswechsel statt Löschung; wo etwas wirklich weg muss, entscheidet das der Nutzer im Chat.
3. **Keine Datenbankchirurgie am Bus vorbei.** Liegengebliebene Datensätze werden über die Regeln des Busses geschlossen, nicht per `UPDATE`. Wenn die Regel im Weg steht, ist die Regel richtig und der Wunsch falsch.
4. **Kein `git add -A` ohne Blick auf `git status`.** Am 2026-09-01 hat ein Sammel-`add` Gerds neue Prüfrunde mit eingecheckt, ungelesen und unter einer Commit-Botschaft, die von etwas anderem handelte. In einem Repo, in dem zwei Seiten schreiben, ist das keine Bequemlichkeit, sondern eine Fälschung der Historie.
5. **Jede Änderung ist ein Git-Commit mit Beschreibung.** Auf Deutsch, im Betreff was sich ändert, im Rumpf **warum**. Kein Sammelcommit über mehrere Befunde. Ein Commit, dessen Beschreibung „diverse Anpassungen" lauten müsste, ist zu groß.
6. **Der deployte Stand ist benannt oder er gilt nicht.** `deploy_manifest.sh` vor dem Deploy, `verify_manifest.sh` auf der NAS. Ein Nachweislauf ohne bestandene Prüfung ist keiner. **Deployt werden versionierte Dateien, nie ganze Verzeichnisse** (`G-020`): Ein Archiv über ein Verzeichnis nimmt lokale Secrets und Laufzeitdateien mit, und eine Prüfung, die nur die gelisteten Dateien kennt, übersieht alten Code, der danebenliegt. Das Manifest kommt aus `git ls-files`; die Prüfung meldet **fehlend, abweichend und unerwartet**.
7. **Ein Kommentar, der eine Absicherung behauptet, muss sie belegen können.** Das ist die häufigste Fehlerklasse in diesem Projekt: die Anforderung richtig aufgeschrieben, etwas anderes gebaut, und der Text bleibt als Zusicherung stehen. Wo sich eine Zusicherung nicht prüfen lässt, steht hin, dass sie **nicht belegt** ist.

## Wie diese Datei wächst

**Jeder bestätigte Prüfbefund hinterlässt hier eine Regel.** Nicht nur eine Korrektur im Code — die Regel dahinter, damit sie beim nächsten Mal **vor** dem Schreiben bekannt ist statt erst im Review. Das ist der ganze Zweck: Der Review findet dann neue Fehler statt derselben noch einmal.

Ablauf, im selben Commit:

1. Befund bestätigt → Code korrigieren
2. Regel hier ergänzen — **ein Satz**, im passenden Abschnitt, mit der Befundnummer in Klammern
3. Antwort nach `REVIEW_ANTWORTEN.md`

**Nicht jeder Befund wird eine Regel.** Ein einmaliger Tippfehler nicht, eine Fehlerklasse schon. Die Prüffrage: *Könnte derselbe Fehler an einer anderen Stelle noch einmal passieren?* Wenn ja, ist es eine Regel. Wenn nein, reicht die Antwort in `REVIEW_ANTWORTEN.md`.

**Ein zurückgewiesener Befund ergänzt nichts hier** — aber die Begründung gehört trotzdem in `REVIEW_ANTWORTEN.md`. Auch „stimmt nicht, weil …" ist ein Ergebnis.

Die Befundnummer ist kein Schmuck: Sie führt zur Beobachtung, die die Regel erzwungen hat. Eine Regel ohne diese Herkunft ist eine Meinung, und Meinungen gehören nicht in diese Datei.

**Drei Dateien liegen doppelt, und jede Zweitkopie ist die, die eine Seite tatsächlich liest:**

| | | wer liest die zweite |
|---|---|---|
| `CLAUDE.md` | `AGENTS.md` | Codex/Gerd |
| `AGENTS.md` | `nas-startup/AGENTS.md` | Gerd auf der NAS |
| `HANDOVER.md` | `nas-startup/HANDOVER.md` | Gerd auf der NAS |

**Beide Seiten gehen immer gemeinsam.** Am 2026-09-01 stellte sich heraus, dass beide NAS-Kopien veraltet waren — `AGENTS.md` um fünf Commits, `HANDOVER.md` um drei Sitzungen. Alles, was in die Regeln geschrieben worden war, hatte den Prüfer nie erreicht, und nichts hat es gesagt. Eine Abweichung ist hier von Natur aus still: Jede Seite liest eine Datei, die vollständig aussieht.

`workforce-agent/test_mirrors.py` prüft das jetzt, weil Disziplin die schwächste Absicherung ist.

Wenn zwei Regeln dasselbe sagen, werden sie zusammengezogen. Diese Datei wird gelesen, bevor jemand etwas schreibt — wächst sie ins Unlesbare, hört das auf, und dann nützt die beste Regel nichts.
