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
| Workforce-API (FastAPI) | `nas-startup/workforce-api/` | läuft — laufende Version in `production_state.txt` |
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
- **Kein `docker system prune`, kein `docker volume prune`, kein `image prune`** (`G-038`). Diese Befehle wirken **NAS-weit**, nicht auf das eigene Projekt, und was sie entfernen, ist nicht rekonstruierbar. Ein Wegwerf-Container wird mit `--rm` oder gezielt mit `docker rm -f <name>` beseitigt, ein Netz mit `docker network rm <name>`. Am 2026-09-01 habe ich das Gegenteil getan, um einen Testcontainer aufzuräumen; nachweisbar blieb nur, dass Produktivstack und Projekt-Images noch da waren.
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

Zwei Details dieses Befehls sind nicht verhandelbar, beide am 2026-09-01 durch je einen falschen Fehlschlag bezahlt:

- **Die Verzeichnisstruktur bleibt erhalten.** `test_the_denial_audit_knows_the_knowledge_record_type` liest `postgres-init/005_bus_denial_audit.sql` relativ zu `app.py`. Wer alles flach nach `/tmp` kopiert, bekommt `FileNotFoundError` und hält ihn für einen Codefehler.
- **`psycopg`, nicht `psycopg2`.** `app.py` importiert `psycopg` (Version 3). Das falsche Paket erzeugt einen Sammelfehler, bei dem die ganze Suite gar nicht erst startet. Die verbindlichen Versionen stehen im `Dockerfile` — dort nachschlagen, nicht schätzen (Regel 4).

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

**Ein Fehlschlag ist erst dann die erwartete Ablehnung, wenn Statuscode *und* Kennung stimmen** (`G-014`). „Irgendein Fehler kam zurück" ist kein bestandener Negativtest — ein `401`, ein `500` oder ein geschlossener Kanal bestünde ihn ebenfalls. **Das gilt auch dort, wo der Fehlschlag das erwünschte Ergebnis ist** (Nachcheck 2026-09-02, Nummer offen). `g045_owner_probe.py` wertete `Exitcode != 0` als „Zugriff verweigert" — ein weggeräumter Container, eine abgerissene SSH-Sitzung oder ein Tippfehler im Tabellennamen hätten den zentralen Sicherheitsnachweis der Datei erbracht. Die Ablehnung wird deshalb an die **SQLSTATE** gebunden: Der Aufruf läuft in einem `DO`-Block mit `EXCEPTION WHEN OTHERS`, meldet die tatsächliche Kennung, und nur `42501` gilt. Bemerkenswert ist, dass diese Regel schon dastand — ich habe sie beim Umstellen auf Exitcodes verloren, weil die vorige Textprüfung wenigstens *eine* Bindung hatte. Eine Härtung an einer Stelle kann eine Kontrolle an einer anderen aufheben.

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

**Das gilt auch dort, wo die Request-Id keine Laufkennung trägt** (`G-059`). Der Agent leitet `AGENT-REPLY-…` und `AGENT-ACK-…` deterministisch aus der eingehenden Nachrichten-Id ab; ein `LIKE 'AGENT-REPLY-%'` ist damit die Liste **aller** Antworten, die er je geschrieben hat. Die Klammer ist dann nicht das Präfix, sondern der Datensatz: Die Antwort hängt am `parent_message_id` der Anfrage, und die Anfrage kommt aus der Request-Id, die eine Laufkennung hat. Mein erster `chain_audit.sql` band den letzten Schritt an `min(record_key)` über alle Antworten des Agenten — bei zwei Kettenläufen ein fremder Datensatz. Aufgefallen ist es nur deshalb nicht, weil vor `G-053` nie bestätigt wurde und der Schritt so oder so fehlte: **ein Fehler, den ein zweiter Fehler verdeckt hat.**

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
7. **Ein Gate schützt nur den Weg, auf dem es sitzt** (`G-041`). `postgres-init/` darf nie unter `/docker-entrypoint-initdb.d` gemountet werden: Das Postgres-Entrypoint führt dort bei leerem Datenverzeichnis **alle** `*.sql` alphabetisch aus — bevor `registry-migrate` existiert und ohne dessen `APPLY_MIGRATION_*`-Prüfung. Der Ordner gehört ausschließlich dem Gate-Runner unter `/opt/startup/migrations`. Solange dort nur `001`–`003` lagen, war die Wirkung unsichtbar; mit `004`–`008` im selben Ordner würde eine Wiederherstellung Knowledge als Nebenwirkung anwenden und danach an `007` abbrechen. **Und: Eine Compose-Änderung wirkt erst nach `--force-recreate`** — der laufende Container behält seine Mounts. Wer die Datei ändert und den Container stehen lässt, hat die Absicherung dokumentiert, nicht hergestellt.

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
- **Jede Kontrolle braucht einen Test, der sie absichtlich schwächt** und verlangt, dass es auffällt: `test_weakened_control_is_detected`, `test_injected_instructions_cannot_redirect_the_reply`, `WeakenedControlIsDetectedTest`. Ein Test, der nur den Gutfall sieht, unterscheidet eine wirksame Kontrolle nicht von einer stillgelegten. **Seit dem 2026-09-03 wird das nachgemessen statt vorausgesetzt:** `test_guard_counterprobes.py` findet jeden Scanner des Pakets über seine Namenskonvention und verlangt, dass mindestens eine Zusicherung über ihm **nicht** die Form `assertEqual([], scanner(...))` hat. Anlass war Regel 47 — die Prüffrage „gibt es einen Zustand, in dem dieser Wächter rot wird" gilt für die Wächter selbst. Der Bestand hielt sie bereits vollständig; erzwungen hat sie nichts. Beim Bauen ist die Prüfung zweimal an derselben Stelle gescheitert wie `NoHardcodedCountsTest` vor ihr: Zusicherung und Aufruf stehen fast immer auf **zwei Zeilen**, ein Muster ohne Zeilenübertritt meldet Lücken, die es nicht gibt.
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
6. **Der deployte Stand ist benannt oder er gilt nicht.** `deploy_manifest.sh` vor dem Deploy, `verify_manifest.sh` auf der NAS. Ein Nachweislauf ohne bestandene Prüfung ist keiner. **Deployt werden versionierte Dateien, nie ganze Verzeichnisse** (`G-020`): Ein Archiv über ein Verzeichnis nimmt lokale Secrets und Laufzeitdateien mit, und eine Prüfung, die nur die gelisteten Dateien kennt, übersieht alten Code, der danebenliegt. Das Manifest kommt aus `git ls-files`; die Prüfung meldet **fehlend, abweichend und unerwartet**. Den kompletten NAS-Iststand liefert ein einzelner Lesebefehl: `nas_status.sh` (Container, API-Version, Migrationsstand, Kanal, Rollen, Manifest, Backup-Rechte, Rückfallpunkte). Er endet mit `RESULT: PASS` oder `FAIL` und passendem Exit-Code und taugt damit auch als Preflight. Ein Statusskript, dessen Teilprüfung fehlschlägt, während es selbst `PASS` meldet, ist schlimmer als keines — Rückgabewerte hinter einer Pipe (`prüfung | tail`) gehören zum letzten Befehl, nicht zur Prüfung.
7. **Ein Kommentar, der eine Absicherung behauptet, muss sie belegen können.** Das ist die häufigste Fehlerklasse in diesem Projekt: die Anforderung richtig aufgeschrieben, etwas anderes gebaut, und der Text bleibt als Zusicherung stehen. Wo sich eine Zusicherung nicht prüfen lässt, steht hin, dass sie **nicht belegt** ist.

8. **Ein Dokument, dessen Zeilen ausgeführt werden, nennt keinen abgeleiteten Namen** (`G-042`). Ein Containername entsteht aus Projektordner, Dienst und Index — `startup-db-1`, nicht `startup-postgres` —, ein Tabellenname aus einer Migration. Befehle gehen deshalb über `docker compose exec -T <dienst>` aus `/volume1/docker/Startup` heraus, `docker inspect` holt sein Ziel aus `docker compose ps -q`, und jeder `workforce.`-Bezeichner wird gegen die Migrationen aufgelöst, die das Fenster **wirklich anwendet** — ein Objekt aus dem gegateten `004` existiert in der Quelle und fehlt in der Datenbank. `test_runbook_targets.py` prüft das; er liest nur Codeblöcke, weil Prosa über einen Befehl kein Befehl ist.

9. **Ein ausführbares Dokument wird gegen die Lage geprüft, in der es läuft — nicht nur gegen die Namen, die es nennt** (`G-043`). `G-042` waren erfundene Bezeichner, `G-043` ist erfundenes Verhalten, und das ist die teurere Hälfte. Vier Formen davon sind belegt: Eine Umleitung nach `/volume1/docker/Startup-Backups` wird von der **SSH-Sitzung** ausgeführt, nicht von Docker, und scheitert am gehärteten Ordner (`G-022`) — geschrieben wird über einen Wegwerf-Container unter `sudo docker`, danach `chown 0:101` und `chmod 640`, weil auch `docker save -o` sonst `600 root:root` hinterlässt. Ein Nachweis, der über einen Schalter läuft, der im Fenster **aus** bleibt, ist keiner: Bei Kanal `DISABLED` antwortet `require_bus_ready()` vor jeder Tokenprüfung mit `503`, also wird die Ablehnung dort belegt, wo sie verbucht wird (`bus_record_denial` als `workforce_api`), samt Gegenprobe, dass dieselbe Rolle nicht lesen darf. `DROP ROLE` scheitert an jeder erteilten Berechtigung (`cannot be dropped because some objects depend on it`), also erst `DROP OWNED BY`, und das Aufräumen steht in einem **eigenen** Befehl, weil eine `&&`-Kette es nach einem fehlgeschlagenen Negativtest überspringt. Und jedes Skript, das das Dokument ausführt, gehört in das Manifest, das es ausrollt — ein Pfad, der aus der Liste fällt, wird nicht als fehlend gemeldet, er ist einfach nicht mehr abgedeckt. `test_runbook_targets.py` prüft alle vier, jede mit Negativprobe. **Ergänzt am 2026-09-02 (`G-058`), drei weitere Fälle derselben Regel aus dem eigenen Phase-5-Entwurf:** Ein Absatz versprach einen Wegwerf-Container und den gehärteten Ordner, der Befehl darunter schrieb aus der SSH-Sitzung nach `/tmp`. Ein Satz verlangte einen leeren Secret-Ordner und nannte als Prüfung `check_secret_files.sh`, das die **Form** vorhandener Geheimnisse prüft und über einen leeren Ordner nichts sagt — ein Skript, das nichts findet und nichts meldet, liest sich wie ein bestandener Test. Und ein Querverweis schickte den Leser in den Abbruch statt in den Rückbau, ausgerechnet in dem Satz, den man im Abbruchfall in Eile liest; der Wächter prüft Abschnittsverweise jetzt gegen die Überschriften.

10. **Ein Containerbenutzer und die Rechte seiner Dateien gehören zusammen — und die Zahlen stehen fest** (`G-044`). Compose hängt ein `file:`-Secret als **Bind-Mount der Host-Datei** ein; `uid`, `gid` und `mode` in der Langform ändern daran nichts. Ein Container, der nicht als Root läuft, kommt an eine `600`-Datei eines anderen Benutzers ebenso wenig heran wie an eine root-eigene `0400`. Der Host gibt also nach **Nummer** frei — `chgrp 101`, `chmod 640` —, und das `Dockerfile` pinnt `uid`/`gid` ausdrücklich, statt sie dem nächsten freien Systemwert des Basis-Image zu überlassen. Dieselbe Klasse wie das Zustandsverzeichnis im Image: Eine Härtung verschiebt, wer worauf zugreift, und das fällt erst beim nächsten Lauf auf. Am 2026-09-01 stand v8 deswegen in einem Neustart-Loop mit `PermissionError: /run/secrets/workforce_api_key`.

11. **Ein Gate wird für einen Aufruf geöffnet, nicht im versionierten Stand** (`G-044`). `docker compose run --rm -T -e APPLY_MIGRATION_X=true registry-migrate` öffnet es genau so lange, wie der Befehl läuft. Ein Commit mit `"true"` macht dagegen `test_review_fixes.py` rot, den Wächter, der die Fail-closed-Voreinstellung aus `G-031` hält, und muss hinterher zurückgenommen werden — der Schritt, den man vergisst. Der Beleg, dass nichts offen blieb, kommt von selbst: Beim nächsten `up` meldet der Runner `already applied` **und** `gate closed`.

12. **Ein Negativtest, der eine Funktion aufruft, muss ihre Stelligkeit treffen** (`G-044`). PostgreSQL antwortet auf eine falsche Argumentzahl mit `function ... does not exist` — genau die Meldung, die auch käme, wenn die Rechtemigration nie gelaufen wäre. Fünf Argumente statt dreizehn haben so einen Nachweis erzeugt, der grün aussah und nichts prüfte. Signaturen kommen aus der Migration oder aus `pg_get_function_identity_arguments`, nie aus dem Gedächtnis; `test_runbook_targets.py` vergleicht sie inzwischen.

13. **Ein Schemaendpunkt ist eine Zugangsdatenfrage, keine Bequemlichkeit** (`G-040`). `/openapi.json` beschreibt jede Route und jedes Requestmodell — die interne Angriffsoberfläche, aufgeschrieben. FastAPI liefert sie ohne Credential aus, auch wenn `docs_url` und `redoc_url` längst aus sind; abgeschaltet wird sie mit `openapi_url=None`, und wer sie braucht, bekommt eine **eigene** Route am selben Pfad hinter `require_api_key` (das seinerseits Klartext verweigert). Authentifiziert statt entfernt, wo ein Abnahmetest daran hängt: Einen Befund zu schließen, indem man die Prüfung löscht, die ihn gefunden hätte, ist der schlechtere Tausch. Und die Korrektur hat zwei Hälften — nur die eigene Route hinzuzufügen ließe FastAPIs Original bestehen, deshalb prüft ein Test `app.openapi_url is None`.

14. **Ein Attribut, das nur der Bootstrap-Superuser hat, ist keins, das man ihm nehmen kann** (`G-045`). `initdb` macht `POSTGRES_USER` zum Bootstrap-Superuser — hier `workforce_app`, OID 10 —, und PostgreSQL lehnt `ALTER ROLE … NOSUPERUSER` darauf ab (`The bootstrap superuser must have the SUPERUSER attribute`); die Anweisung scheitert als Ganzes. `NOCREATEROLE NOCREATEDB NOBYPASSRLS` geht zwar durch, ist aber wirkungslos, weil ein Superuser alle drei überschreibt. Wer den Superuser aus dem Datenpfad haben will, braucht einen **eigenen Eigentümer**, nicht ein entzogenes Attribut — und das betrifft die `SECURITY DEFINER`-Funktionen, die als ihr Eigentümer laufen. Zwei Dinge kommen dazu, beide gemessen: Es gibt genau **einen** Superuser, ein gelungener Entzug wäre also nicht rücknehmbar gewesen; und der **Eigentümer** kann die Append-only-Trigger ohnehin abschalten, `NOSUPERUSER` hätte diese Begründung aus `006`/`007` nicht eingelöst.

15. **Eine Probe muss die Rollenlage der Produktion nachbauen, nicht nur ihr Schema** (`G-045`). Dieselbe Anweisung lief in einem Wegwerf-Container durch und wurde produktiv abgelehnt — der Unterschied war allein, wer dort der Bootstrap-Superuser ist. Eine Probe, die die Zieldatenbank mit dem Vorgabebenutzer `postgres` aufsetzt und die Rollen aus einem Dump nachlädt, prüft eine Lage, die es nicht gibt, und meldet Grün für etwas Unmögliches. Wer eine Rechteänderung probt, setzt `POSTGRES_USER` wie im Ziel.

16. **Ein Artefakt, das nie gelaufen ist, begründet keine Entscheidung — es sei denn, daneben steht, dass es nie gelaufen ist** (`G-046`). `/openapi.json` blieb erreichbar-mit-Schlüssel statt entfernt, begründet damit, dass `e2e_acceptance.rb` die Pfadliste prüft. Kein Nachweis nennt einen Lauf dieses Skripts, und kein Runbook ruft es auf; die Begründung bewahrt also eine **Möglichkeit**, keine laufende Prüfung. Der Tausch bleibt richtig, die Einschränkung gehört trotzdem dorthin, wo das Argument gemacht wird. Umgekehrt gilt: **Ein Dokument ohne Datum wird als aktuell gelesen.** Der Bus-Vertrag behauptete vier Versionen lang „in `workforce-api:v6` implementiert, E2E-Abnahme ausstehend", obwohl der reale HTTPS-Lauf am 2026-08-31 stattgefunden hatte. Wer eine Aussage nicht mehr halten kann, ändert sie oder datiert das Dokument.

17. **Ein Runbook wechselt nach dem Lauf den Aggregatzustand** (`G-046`). Vorher nennt sein Kopf den offenen Blocker, nachher „ausgeführt am ⟨Datum⟩" samt Nachweisdatei — und die Versionsnummern darin sind ab dann historisch, nicht aktuell; den laufenden Stand nennt `production_state.txt`. Ein Wächter, der nur den Vorher-Zustand kennt, wird beim Erfolg rot und damit abgeschaltet: `test_document_consistency.py` prüft deshalb beide Zustände, jeden mit eigener Gegenprobe.

18. **Ein Ordner, der in die Produktion gemountet wird, gehört ins Manifest** (`G-047`). `compose.yaml` hängt `./postgres-tests` schreibgeschützt in den Datenbankcontainer, aber der Ordner stand in keiner Deploy-Pfadliste: Das Manifest meldete `PASS`, während dort auf der NAS lag, was historisch gewachsen war. Anders als `G-041` ist das kein Ausführungsweg — nichts startet die Dateien automatisch —, aber es ist dieselbe blinde Stelle wie `G-020`. Die Prüffrage ist nicht „wird es ausgeführt", sondern „kann die Prüfung sehen, was dort liegt".

19. **Ein Namensmuster ist eine Zusage, und `_acceptance.sql` sagt: läuft in einer Transaktion, endet mit `ROLLBACK`** (`G-047`). Eine Datei im Verzeichnis hielt das nicht — sie setzt den Kanal, legt Credentials an und committet. Sie heißt deshalb seit dem 2026-09-02 `visible_communication_demo.sql`: ohne Nummer und ohne `_acceptance`, weil sie ein Demo ist und keine Abnahme. Offen war die Tür ohnehin nicht, sie verweigert den Dienst ohne `app.visible_demo = ENABLED`, und diese Sperre wird geprüft statt vorausgesetzt. **Umbenannt statt nur dokumentiert**, weil die falsche Nummer die Regel unerfüllbar machte: Ein korrekt benannter Abnahmetest für Migration `003` konnte nicht danebengelegt werden, solange eine fremde Datei diese Nummer belegte. Mein Einwand dagegen — die alten Namen stünden in Nachweisen — war ungeprüft und falsch; kein Nachweis nennt sie. Dieselbe Klasse wie `G-046`: Ein Name behauptet etwas, das der Inhalt nicht einlöst.

20. **Eine bekannte Lücke wird festgeschrieben, nicht verschwiegen** (`G-047`). Vier Migrationen haben keinen Abnahmetest, zwei davon sind seit dem Phase-4-Fenster produktiv. Ein Wächter, der darauf einfach rot wird, ist am zweiten Tag abgeschaltet; einer, der die Lücke als Liste mit Begründung hält und **in beide Richtungen** anschlägt — neue Lücke *und* stillschweigend geschlossene —, hält sie sichtbar und macht das Schließen zu einer bewussten Handlung.

21. **Einen Zustand zu prüfen ersetzt nicht, ihn zu setzen** (`G-048`). `check_backup_permissions.sh` sagt seit dem 2026-09-01 voraus, dass der nächtliche Job neue Dateien mit seiner eigenen Umask anlegt und die Verschärfung „über Nacht erodiert". Genau das geschah in der ersten Nacht danach: ein vollständiger Datenbank-Dump und ein Konfigurationsarchiv mit `startup.env` lagen `644 root:root` im Backup-Ordner. Der Wächter hat es gefunden — und Finden ist nicht Verhindern. Wo ein fremder Prozess regelmäßig Dateien erzeugt, gehört neben die Prüfung ein Skript, das den Zustand **setzt** (`harden_backup_permissions.sh`), aufgerufen von demselben Auftrag, der die Dateien schreibt. Solange das nicht eingehängt ist, ist der Befund behoben und nicht geschlossen.

22. **Ein Deploy fügt hinzu und entfernt nie** (`G-047`). `tar xzf -` legt Dateien an und überschreibt sie, aber eine umbenannte oder entfallene Datei bleibt auf der NAS liegen. Gefunden hat das nur das Manifest, und zwar als `UNERWARTET` — genau der Fall, für den `G-020` die dritte Meldeart eingeführt hat. Nach jeder Umbenennung oder Entfernung gehört deshalb ein Manifestlauf, **bevor** man den Stand für sauber hält. Aufgeräumt wird nicht durch Löschen: Die Altdatei wandert nach `Versionen/` mit einem datierten Namenszusatz, wie es das Projekt schon für `compose.yaml` und die alten Pakete hält. Leitplanke 2 gilt auch für Dateien, die man selbst gerade überflüssig gemacht hat.

23. **Was die Produktion füllt, gehört ins Repo — auch wenn es in einer fremden Oberfläche steht** (`G-047`). Die nächtliche Sicherung lebte als Textfeld in der DSM-Aufgabendatenbank: nicht in Git, nicht im Manifest, nicht geprüft, nicht testbar; lesbar nur durch Öffnen der Aufgabe. Sie enthielt dabei genau die Fehler, gegen die dieses Projekt Regeln hat — einen fest eingetragenen Containernamen (`G-042`), eine Umleitung, die bei gescheitertem `docker exec` eine abgeschnittene Datei hinterlässt, und ein Aufräumen alter Sicherungen **vor** jeder Prüfung der neuen. Die Logik liegt jetzt in `backup_task.sh`; die Aufgabe ruft nur noch eine Zeile auf. Und `/tmp` ist auf dieser NAS `noexec` — ein Wegwerf-Skript wird von dort nicht ausgeführt, sondern muss aufs Volume.

24. **Ein Abnahmetest prüft Eigenschaften, keine Bestandszahlen** (`G-049`). `001` und `002` behaupteten „genau 5 Mitarbeiter", „genau 5 aktive Capabilities", „genau 60 Routen", „gar keine Credentials". Alles war am Tag der Migration wahr und ist es heute nicht mehr — die Registry ist auf neun gewachsen, es gibt 21 widerrufene Zugänge aus dokumentierten Läufen. Damit ließen sich beide Tests **genau einmal** gegen die Produktion fahren, obwohl ihr eigener Kopf sagt, sie dürften es jederzeit. Die Grenze verläuft nicht bei „Zahl ja/nein", sondern beim Umfang: Eine Zählung ist zulässig, wenn sie auf das eingegrenzt ist, was die Migration oder der Test **selbst** erzeugt hat (`WHERE request_id = 'MIG-001-…'`, `LIKE 'REQ-E2E-%'`), und unzulässig, wenn sie die lebende Population zählt. Ersetzt wurden sie durch Aussagen, die mit dem System mitwachsen: die Bootstrap-Identitäten sind da, keine Route zeigt auf ein Nichtmitglied oder auf sich selbst, kein Widerruf ohne Zeitpunkt und Begründung.

25. **Ein Statusabschnitt nennt keine Versionsnummer, er verweist** (`G-050`). Am 2026-09-02 sagte die Schichtentabelle in `CLAUDE.md` „Workforce-API (FastAPI, `v7`) … läuft" und `HANDOVER.md` „die NAS läuft auf `v8`", während seit einem Tag `v9` produktiv war — in genau den beiden Dateien, die jede Seite zuerst liest, und mit 35 grünen Dokumententests daneben. `G-046` hat dieselbe Klasse an zwei anderen Dateien behoben, aber nur die **Dateien** in die Prüfung genommen, nicht die **Aussage**; die Versionsprüfung dort vergleicht `app.py`, `Dockerfile` und `compose.yaml` untereinander und nie gegen ein Dokument. Die Abhilfe ist keine schlauere Suche: `production_state.txt` nennt den laufenden Stand bereits und `nas_status.sh` misst ihn, also ist jede zweite Angabe derselben Tatsache eine Kopie — und **eine Zahl, die nirgends steht, kann nicht veralten**. Anderswo bleibt eine Versionsnummer richtig, weil sie dort zu einer Geschichte gehört: `v7` → `v8` im Fenster, die Rückfallmarke, ein `docker save`. Geprüft wird deshalb abschnittsweise und nicht dateiweit, mit drei Gegenproben: dass das Muster `/bus/v1/` und `produktiv-v8` **nicht** trifft, dass die alten Zeilen es **doch** tun, und dass die genannte Überschrift noch existiert — ein umbenannter Abschnitt schaltet den Wächter sonst still ab.

26. **Eine Adresse, die ihren eigenen Standort abbildet, ist ein abgeleiteter Name — kein Bezeichner** (`G-051`). Die Bus-Adresse `https://192-168-68-81.<id>.direct.quickconnect.to:8443` entsteht aus der LAN-Adresse der NAS; ändert DHCP die Adresse, zeigt der Name ins Leere. Am 2026-09-02 stand er nach einem Neustart in **17 Dateien** quer durch alle Laufzeitpakete — Contract-Test, Kettenlauf, Worker-Core, Telegram, Agent — und antwortete überall mit `Connection refused`. Dieselbe Klasse wie ein Containername aus Projektordner, Dienst und Index (`G-042`), nur schwerer zu sehen: Die lokalen Suiten laufen **absichtlich ohne Netz**, und ein Deploy-Manifest vergleicht Prüfsummen, keine Adressen. Das NAS-Zertifikat trägt `*.<id>.direct.quickconnect.to`, also verifiziert TLS **jede** Adressvariante des Musters — eine falsche Adresse fällt nie am Zertifikat auf, sondern erst beim Verbinden, im Fenster. Die Adresse steht deshalb als `BUS_BASE_URL` in `production_state.txt` und sonst nirgends als Tatsache; `test_bus_address.py` hält alle Vorkommen dagegen, und weil nur die Maschine selbst weiß, welche Adresse sie hat, entscheidet `check_bus_address.sh` das auf der NAS — als Gate in `nas_status.sh`, mit Gegenprobe. **Der Bequemlichkeitsweg wäre gewesen, überall `.78` durch `.81` zu ersetzen**; das hätte bis zum nächsten Neustart gehalten.

27. **Wer eine Nachricht entgegennimmt, bestätigt sie — auch am Rand des Systems** (`G-053`). Der Telegram-Connector las seinen Posteingang und schickte Benachrichtigungen an den CEO, bestätigte aber nie auf dem Bus. Zwei Dinge folgten daraus, und beide sind teurer als der fehlende Aufruf. **Der Nachweis:** Eine Nachricht bleibt damit für immer `DELIVERED`, und aus der Datenbank allein ist nie zu sagen, ob eine Benachrichtigung den CEO erreicht hat — genau das, was Phase 5 rekonstruierbar verlangt. **Die zweite Linie:** Der Dublettenschutz des Rückwegs lag ausschließlich im lokalen SQLite-Speicher des Connectors. Geht dieser Datenträger verloren — der Fall, den dieses Projekt für den Agenten seit `G-002` ausdrücklich testet —, wird jede Nachricht im Posteingang erneut angekündigt. Der Agent hat dafür zwei Linien, der Rückweg hatte eine, und „zwei Verteidigungslinien, und sie sind nicht austauschbar" stand längst in dieser Datei. Die Reihenfolge ist dieselbe wie im Agenten (`G-001`): erst senden, dann bestätigen — und ein fehlgeschlagenes Bestätigen beendet die Runde nicht, weil die Nachricht beim Empfänger *ist*. **Nicht bestätigt hat sich der naheliegende zweite Verdacht:** Der Posteingang sortiert `created_at DESC`, neue Nachrichten verschwinden also nicht hinter alten. Nachgesehen, bevor ich es behauptet hätte.

28. **Prosa darf beschreiben, aber die Zusicherung steht maschinenlesbar daneben** (`G-054`). Das Agenten-README nannte in seiner Policy-Tabelle den Betreff unter `METADATA_ONLY` — genau davon hatte `G-029` den Code befreit, weil Menschen die eigentliche Anfrage in den Betreff schreiben. Und „Server-seitige Fallbacks sind aktiviert" stand dort weiter, obwohl `G-036` sie abgeschaltet hat. Zwei sicherheitsrelevante Aussagen, beide im Präsens, beide falsch, beide in der Datei, die man liest, bevor man eine Policy wählt. Die erste ist die gefährlichere: Wer Code und Dokument angleicht, hätte `G-029` wieder eingebaut. **Ein Sprachvergleich taugt als Wächter nicht** — der korrigierte Satz lautet „Weder Text noch Betreff", nennt das Wort also und meint das Gegenteil. Deshalb steht die Feldliste jetzt als maschinenlesbarer Block im README und wird gegen `data_boundary.py` geprüft; die Prosa darum herum darf formulieren, wie sie will. Dieselbe Trennung wie bei `bus_rules.py`, das die SQL-Regeln abschreibt und per Digest gegen die Migration hält.

29. **Ein Dienstname wird gegen die Compose-Datei geprüft, die der Befehl wirklich nennt** (`G-055`). Der Runbook-Wächter löste jeden Dienstnamen gegen die Produktions-`compose.yaml` auf und kannte `docker compose run` gar nicht — und weil `-f <datei>` **vor** dem Unterbefehl steht, traf sein Muster ausgerechnet jeden Aufruf einer Paketdatei nicht. Vier erfundene Dienstnamen im ersten Entwurf von `PHASE5_RUNBOOK.md` gingen wortlos durch: `cleanup` statt `core-cleanup`, `prepare` statt `chain-prepare`, `chain` statt zweier Dienste. Dieselbe Klasse wie `G-042`, in derselben Sorte Dokument. **Und die Aufrufform gehört dazu:** `run` ohne `--no-deps` startet über `depends_on` das `prepare` ein zweites Mal, das beim zweiten Mal am schon geöffneten Kanal abbricht — die Reihenfolge macht dann das Dokument, nicht Compose, und das muss dort stehen. Zwei Fallen beim Nachziehen des Wächters, beide gemessen statt vermutet: Ein Dienstname beginnt nie mit `-`, sonst liest das Muster `--abort-on-container-exit` als Dienst; und eine Umgebungszuweisung `-e VAR=wert` muss übersprungen werden, sonst wird `VAR` zum Dienst. **Eine dokumentierte Schrittfolge wird nicht neu erfunden** — die des Kettenlaufs stand in `chain-test/README.md`, war einmal real gelaufen und hatte dabei ihre Form bekommen.

30. **Ein Dublettenschutz merkt sich „erledigt", nicht „teilweise erledigt" — und ein Fingerabdruck trägt keinen veränderlichen Zustand** (`G-056`). Beides fiel an derselben Stelle an, im Rückweg des Connectors, und beides ist mein eigener Fehler vom selben Tag wie `G-053`. Der Versand an Telegram und die Bestätigung auf dem Bus sind **zwei** dauerhafte Wirkungen; der lokale Speicher kannte dafür eine einzige Marke. Scheiterte die Bestätigung, stand die Nachricht lokal auf `SENT`, wurde beim nächsten Mal als Dublette übersprungen und blieb auf dem Bus **für immer** `DELIVERED` — genau der Zustand, gegen den `G-053` gebaut wurde, nur über den Fehlerpfad erreicht. Die Abhilfe braucht keine zweite Spalte: Der Bus ist die Idempotenzinstanz, `BUS_ACK_ALREADY_FINAL` heißt „war schon" und nicht „ging schief", also darf die Bestätigung gefahrlos nachgeholt werden, solange der Bus die Nachricht noch offen führt. **Und der Fingerabdruck enthielt `delivery_status`.** Solange nie bestätigt wurde, änderte der sich nie und der Fehler war unsichtbar; mit `G-053` wurde aus jeder erledigten Nachricht ein dauerhafter `CONFLICT`. Ein Kennzeichen kennzeichnet die Sache, nicht ihren Zustand. Gefunden hat das kein Test, sondern das Lesen des eigenen Codes vom selben Tag — und die Attrappe verdeckte es, weil sie die Bestätigung nur vermerkte, statt den Posteingang zu ändern.

31. **Ein Feld in einer Allowlist, das niemand liest, ist eine Zusicherung ohne Deckung** (`G-057`). `model_allowlist.py` erklärte je Modell `max_output_tokens` und `max_cost_usd_per_call` — und der Provider gab weiter die Modulkonstante `MAX_REPLY_TOKENS` an die API, während den Kostendeckel gar nichts las. Beides am selben Tag geschrieben wie die Datei selbst, beides beim Nachlesen gefunden, nicht beim Schreiben. Das ist Leitplanke 7 in ihrer unauffälligsten Form: Nicht ein Kommentar behauptet die Absicherung, sondern ein **Konfigurationsfeld** — und das wirkt noch verbindlicher. Die Ausgabedecke ist jetzt die des Modells; der Kostendeckel wird **vor** dem Aufruf geprüft, und das geht nur, weil die Ausgabe durch dieselbe Decke begrenzt ist: geschätzte Eingabe mal Tarif plus maximale Ausgabe mal Tarif ist eine echte Obergrenze, keine Schätzung. Die laufweite Kostendecke kann das nicht leisten — Kosten sind erst hinterher bekannt, und genau deshalb steht in der CEO-Ergänzung „vor jedem Provideraufruf … geprüft und reserviert". **Eine Decke, die schon der Normalfall reißt, wäre keine Kontrolle, sondern eine Abschaltung**; ein Test hält deshalb fest, dass jedes gelistete Modell bei voller Datenmenge unter seiner eigenen Decke bleibt.

32. **Der Manifestumfang braucht eine zweite Prüfung auf der obersten Ebene** (`G-060`): `verify_manifest.sh` sieht nur genannte Pfade, deshalb muss `check_unmanaged.sh` jeden übrigen Top-Level-Namen ohne Shell-Worttrennung entweder begründet erlauben oder als genau einen Fund melden.

33. **Ein Container-Build wird gegen die Importmenge seines tatsächlichen `COPY` geprüft** (`G-061`): Ein lokal grünes Modul nützt nichts, wenn der Dockerfile seine Abhängigkeit nicht ins Image nimmt; der Einstiegspunkt muss aus einem nachgebauten Copy-Set importierbar sein.

34. **Zwei Testpakete mit Kanal und Credentials sind zwei Berechtigungsfenster** (`G-062`): Das erste wird vollständig zurückgebaut und mit `DISABLED` plus null aktiven Credentials nachgemessen, bevor der Prepare des zweiten startet.

35. **Ein Lauf hat genau eine validierte Parameterquelle** (`G-063`): Identität, Task, Prepare, Audit und Cleanup leiten sich daraus ab, fremd vergebene IDs werden aus der Auditspur ermittelt, und jede Secretdatei wird über ihren exakten Pfad gelöscht und auf Abwesenheit geprüft.

36. **Ein Deploy-Schritt überträgt genau die Dateimenge, die sein Manifest gehasht hat** (`G-064`): Ein Rollout verlangt einen sauberen Git-Baum, verwendet eine gemeinsam erzeugte Transferliste und akzeptiert auf dem Ziel nur `dirty=no`; Manifest-Erzeugung allein ist kein Deploy.

37. **Providerbudget wird vor externer Arbeit atomar reserviert** (`G-065`): Aufrufslot, konservative Eingabe, maximale Ausgabe und Kosten müssen gemeinsam in den Rest passen; fehlende oder fehlerhafte Usage darf die Reserve niemals zu null machen.

38. **Modellname, Tarif und Request-Fähigkeiten sind ein Vertrag mit Prüftag** (`G-066`): Jeder Allowlist-Eintrag sendet nur unterstützte Parameter; angekündigte Preisänderungen werden am Wirksamkeitstag erneut gegen die offizielle Quelle geprüft und weder vorschnell noch aus einem stillen Fallback übernommen.

39. **Aktive Betriebsdokumentation trennt belegte Gegenwart, datierte Historie und geplante Phase** (`G-067`): Entscheidungskopf und Roadmap nennen den aktuellen Autoritätsstand, während alte Versionen oder „noch nie gelaufen" nur in eindeutig historischem Kontext stehen dürfen.

40. **Ein Rückbau löscht die Dateien, die der Prepare wirklich anlegt — mit Namen und mit Nachweis** (`G-068`). Der Kernfenster-Rückbau in `PHASE5_RUNBOOK.md` löschte `core_token_connector` und `core_token_thorsten`; beide legt kein Skript je an. `prepare_core_once.sh` erzeugt `karl`, `gerd`, `anastasia` — zwei davon blieben liegen. **`rm -f` auf einen Namen, den es nie gab, meldet Erfolg**, also las sich der Schritt wie ein sauberer Abschluss, während zwei gültige Bus-Tokens auf der NAS lagen. Der richtige Umgang stand im selben Dokument: Der Kettenrückbau nennt drei exakte Pfade und hängt an jedes Löschen ein `test ! -e`. `test_runbook_targets.py` prüft jetzt alle drei Fragen — ist der Name überhaupt ein Tokendateiname des Projekts, wird die **vollständige** Menge je Präfix gelöscht, und steht hinter jedem Löschen ein Abwesenheitsnachweis. Dieselbe Klasse wie `G-058`: ein Aufräumschritt, der etwas anderes tut, als sein Satz verspricht, und dabei nichts beweist.

41. **Ein Pfad, der schon durch einen anderen abgedeckt ist, macht das Manifest dauerhaft rot** (`G-069`). `verify_manifest.sh` läuft `find $paths -type f`. Standen `chain-test` **und** `chain-test/validate_chain_run_config.sh` in `deploy_paths.txt`, fand `find` die Datei zweimal, während `git ls-files` sie einmal nennt — die zweite Fundstelle wurde als `UNERWARTET` gemeldet. Das Gate, das `PHASE5_RUNBOOK.md` in Abschnitt 4 verlangt, wäre nie grün geworden, und ein Wächter, der immer rot ist, wird abgeschaltet statt gelesen. Ein Eintrag deckt sich selbst und alles darunter ab; einen Unterpfad zusätzlich zu nennen ist keine Betonung, sondern ein Fehler. `test_deploy_paths.py` prüft das jetzt mit Gegenprobe in beide Richtungen — `chain-test/x` ist überdeckt, `chain-testing` nicht.

42. **Ein Wächter vergleicht gegen eine Menge exakter Pfade, nie gegen einen zusammengesetzten Text** (`G-073`). `helper_script_offenders()` hängte Pfadliste und aufgelöste Dateinamen zu einem Block zusammen und fragte `name not in block` — eine Teilstringprüfung, unter der ein nirgends ausgerolltes `status.sh` als abgedeckt galt, sobald `nas_status.sh` irgendwo vorkam. Dieselbe Klasse wie `G-055`: Der Wächter sah hin und sah das Falsche an. Und wo der Befehl einen Pfad hergibt, wird der ganze Pfad gebunden — derselbe Basename in einem anderen Paket ist ein anderes Skript. Beide Richtungen haben eine Gegenprobe, die genau einen Verstoß verlangt.

43. **Ein privilegierter Befehl im Runbook muss einer sein, den die Maschine auch ausführt** (`G-072`). Die passwortlose Regel dieser NAS lautet auf `/usr/local/bin/docker` und auf sonst nichts; `sudo sh …` und `sudo rm …` fragen nach dem Passwort und sterben in einer nicht-interaktiven SSH-Sitzung. Das Runbook verlangte beides — beim Backup hieße das, das Fenster beginnt ohne Sicherung, beim Rückbau, dass gültige Bus-Tokens liegen bleiben, derselbe Ausgang wie `G-068`, nur über den Fehlerpfad. Gesichert wird jetzt über die DSM-Aufgabe plus eine gemessene Frischeprüfung (`BACKUP_MAX_AGE_HOURS=0`), gelöscht über einen Wegwerf-Container auf genau den Secretordner des Pakets. `privileged_command_offenders()` liest dafür `all_commands()` und nicht `commands()`: Dass die Backup-Zeile überhaupt geprüft worden wäre, hätte allein am `docker` in ihrem Pfad gelegen. Dieselbe Klasse wie `G-043` — nicht ein erfundener Name, sondern erfundenes Verhalten.

44. **Eine Rechtemigration wählt ihre Ziele gepinnt, nicht dynamisch — und ihre Zusicherung reicht genau so weit wie ihr Zugriff** (`G-071`). Migration 009 sprach im Kommentar von den zwölf SECURITY-DEFINER-Busfunktionen und wählte im Code jede SECURITY-DEFINER-Funktion des Schemas; heute dieselbe Menge, nach einer Anwendung von `004` wären die sieben Knowledge-Funktionen als Nebenwirkung in den Bus-Eigentümerkontext gewandert — genau die Grenze, die getrennt bleiben soll. Dasselbe galt für `GRANT … ON ALL TABLES` in zwei Schemata. Gepinnt wird über Name und **Stelligkeit**, nie über abgeschriebene Typnamen (der Katalog schreibt `timestamptz` als `timestamp with time zone`); die Signatur kommt aus `regprocedure`. Die Rechte sind eine Allowlist, aus den Funktionsrümpfen abgeleitet — **einschließlich der Trigger auf den Tabellen, in die sie schreiben**, denn die sind nicht SECURITY DEFINER und laufen als der neue Eigentümer: Ohne `INSERT` auf `bus_events` stünde die Auditspur still, der teuerste Ausgang einer zu engen Allowlist. Und die Nachprüfung am Ende nennt nur die zwölf: Eine schemaweite Aussage wäre nach einer späteren `004` stillschweigend falsch. `test_bus_function_owner.py` leitet beide Mengen erneut aus `002` und `005` ab und hält sie gegen Migration und Abnahmetest, mit Gegenproben in beide Richtungen.

45. **Ein Urteil zählt jede Zusicherung namentlich, und ein nicht gemessener Punkt ist ein Fehlschlag** (`G-070`). `g045_owner_probe.py` berechnete, ob der Audit-Trigger unter dem neuen Eigentümer feuert, druckte das Ergebnis und ließ es aus der Erfolgsbedingung heraus: sichtbar `NEIN`, darunter `RESULT: PASS` — der zentrale Nachweis der Datei konnte falschgrün ausgehen. Dieselbe Klasse wie eine Prüfung hinter einer Pipe, deren Rückgabewert am letzten Befehl hängt (Leitplanke 6). Das Urteil steht deshalb in einer reinen Funktion über einer Erwartungstabelle: fehlender Schlüssel → Fehlschlag, abweichender Wert → Fehlschlag. Und der Nachweis bindet an **Request-Id, Akteur, Datensatztyp und Operation** statt an einen Zählerstand — „irgendein Datensatz dieses Typs“ ist nach den Auditregeln dieses Projekts kein Nachweis. Eine Probe, die nie gelaufen ist, hat genau ein prüfbares Teil, nämlich ihre Bewertung; die läuft lokal gegen ihre Negativfälle.

46. **Ein Rechtetest fragt nach dem direkten Katalogeintrag, nicht nach dem effektiven Recht** (`G-074`). Mein Abnahmetest für `009` verlangte `has_schema_privilege('workforce_owner','public','USAGE') = false` und wäre auf **jeder** frischen PostgreSQL-17-Instanz falsch rot geworden: Die Dokumentation zu Schemata sagt für `public`, dass dieses Recht standardmäßig jeder besitzt — erteilt an die Pseudorolle `PUBLIC`, und ein Widerruf bei einer einzelnen Rolle hebt ein geerbtes Recht nicht auf. Das global zu entziehen wäre eine datenbankweite Entscheidung außerhalb einer Busmigration; also lautet die Zusicherung „kein direkter Grant" und wird über `aclexplode` gelesen, dessen Grantee-OID `0` für `PUBLIC` beim Join auf `pg_roles` von selbst herausfällt. **Und ein Rechtevergleich trägt das Schema im Schlüssel** — nach `table_name` allein gruppiert fielen `public.bus_messages` und `workforce.bus_messages` zusammen. Dieselbe Klasse wie `G-045`: eine SQL-Aussage, die syntaktisch stimmt und die falsche Frage stellt; ein rein statischer Test sieht das nie.

47. **Ein Wächter, dessen Bedingung sich selbst ausschließt, kann nie anschlagen** (Nachcheck 2026-09-02, Nummer offen). Die Selbstprüfung im `009`-Abnahmetest verlangte `a.grantee = 0` und jointe gleichzeitig auf `pg_roles`, wo es zur OID `0` keine Zeile gibt: Der Join entfernte jede Zeile, `EXISTS` war **immer** falsch. Ausgerechnet die Prüfung, die belegen sollte, dass die Pseudorolle `PUBLIC` richtig ausgeblendet wird, belegte nichts — und sie sah dabei aus wie eine bestandene Kontrolle. Zwei Tatsachen brauchen zwei Abfragen: eine ohne den Join (die Vorgabe existiert überhaupt) und eine mit ihm (genau sie wird ausgeblendet). Die Prüffrage ist nicht „ist die Bedingung richtig", sondern **„gibt es einen Zustand, in dem dieser Wächter rot wird"** — dieselbe Frage wie bei `compose_scan.py`, nur eine Ebene tiefer: dort las ein Wächter die Datei nicht, hier las er sie und stellte eine leere Menge zusammen.

48. **Ein Rechte-Rückbau erfasst den Behälter, nicht nur seinen Inhalt** (Nachcheck 2026-09-02, Nummer offen). Migration `009` setzte Tabellen- und Sequenzrechte zurück und entzog einen direkten Grant auf `public` — aber nie das Schema `workforce` selbst. Eine Rolle, die die Migration bereits vorfindet, hätte ein `CREATE` darauf behalten, und `CREATE` auf einem Schema ist hier kein kleines Extra: Damit legt die Rolle eigene Relationen an, ist deren Eigentümerin und kann auf ihnen Trigger abschalten — genau der Weg, den `009` zumachen soll. Der Eigentümer ohne Tabelleneigentum wäre dann nur eine Momentaufnahme gewesen. Ein `GRANT` setzt deshalb einen `REVOKE ALL` auf dasselbe Objekt voraus, sonst hängt der Endzustand an der Vorgeschichte; und der Abnahmetest verlangt **genau** die erlaubte Rechtemenge, nie „mindestens".

49. **Eine Probe misst den Weg, den der echte Aufrufer nimmt — nicht einen daneben** (Vertretungsreview 2026-09-03, `SV-2026-09-03-01`/`-02`). `g045_owner_probe.py` fragte in ihrer ersten Zeile „laufen die Funktionen danach ohne Superuser weiter?" und maß dann keine einzige von ihnen: Sie schrieb roh per `UPDATE` auf `bus_channels` — eine Tabelle, auf die `009` der Rolle nur `SELECT` gibt. Der Lauf wäre mit `42501` gescheitert, hätte sich wie „die Allowlist ist zu eng" gelesen, und die schnelle Reparatur im Fenster wäre ein `UPDATE`-Grant gewesen: genau die Verbreiterung, gegen die `G-071` die Allowlist gebaut hat. **Der teuerste Ausgang einer Rechtemigration ist eine zu enge Allowlist, und der zeigt sich nur auf dem echten Pfad** — die Probe ruft deshalb `bus_send_message` als `workforce_api` auf und liest den Rückgabewert. Entstanden ist der Fehler, weil das Schreibziel aus der Zeit stammte, als `009` noch `ALL TABLES` erteilte: dieselbe Bewegung wie bei `G-014`, eine Härtung verschob den Boden unter einer Kontrolle, die niemand mitzog. Ein Test bindet das Schreibziel jetzt an die Allowlist der Migration, mit dem historischen Fall als Gegenprobe.

50. **Ein Rückbau, den ein Kopf verspricht, ist eine Datei mit Namen — und der Verweis darauf ist maschinenlesbar** (`SV-2026-09-03-04`). Der Kopf von `009` nannte den „Rückbau als Teil derselben Entscheidung", und es gab keinen: keine Migration `010`, kein Runbook-Abschnitt, kein Nachweis. Der Satz stand in dem Absatz, den man liest, **während** man über die Freigabe entscheidet. Die Korrektur ist nicht, den Satz zu streichen, sondern die Datei zu schreiben und den Verweis so abzulegen, dass er nicht wieder unbemerkt falsch wird: `-- RUECKBAU: <datei>` in der Migration, `-- ROLLBACK-FUER: <datei>` im Rückbau, beide aufgelöst von einem Test. Ein Sprachvergleich taugt dafür nicht — der alte Absatz sagte „gibt es nicht", der neue sagt „ist eine Datei", beide enthalten dasselbe Wort und meinen das Gegenteil (`G-054`). Drei Eigenschaften hat der Rückbau selbst: Er **bricht ab**, wenn es nichts zurückzubauen gibt, sonst ist er `G-068` mit anderem Vorzeichen — ein `rm -f` auf einen Namen, den es nie gab. Er liest sein Ziel aus dem Katalog, statt eine Rolle beim Namen zu nennen (`G-042`). Und er **löscht nichts**: `DROP OWNED BY` entfernt Objekte und nicht bloß Rechte, sein Umfang hängt am Laufzeitzustand, und ob ein `DROP ROLE` danach durchginge, kann eine Migration gar nicht wissen — `pg_shdepend` ist clusterweit, sie sieht eine Datenbank. Eine `NOLOGIN`-Rolle ohne Recht und ohne Objekt stehen zu lassen ist die belegbare Aussage; sie zu entfernen wäre eine unbelegte.

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
