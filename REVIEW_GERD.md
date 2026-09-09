# Gerd-Review — Neubau `workforce/`

## 2026-09-08 — fokussierter Lauf nach dem ersten Modellbetrieb

Prüfumfang: `workforce/config.py`, `workforce/providers.py`, `workforce/store.py`
und die zugehörigen Tests. Keine NAS-, Kanal-, Credential-, Skill- oder
Produktivänderung.

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-092` | hoch | `ollama_url` akzeptierte beliebige HTTP-Ziele. Damit konnte ein als lokal deklarierter Provider Inhalte außer Haus senden. | Nur Loopback und die ausdrücklich benannte lokale Container-Brücke `host.docker.internal` sind zulässig; Konfiguration und Provider prüfen unabhängig. Fremdziel-Gegenprobe rot. |
| `G-093` | mittel | Negative Lease-Werte und unbrauchbare Retry-/Aufrufgrenzen wurden beim Start akzeptiert. Dadurch konnten Claims sofort verfallen oder der Betrieb unkontrollierbar werden. | Ganzzahlige, positive und begrenzte Werte werden beim Start erzwungen; String und Bool sind ebenfalls abgelehnt. |
| `G-094` | hoch | Eine Secret-Datei mit Modus `0660` galt als geschützt, obwohl der Vertrag ausschließlich `0600` oder `0640` erlaubt. Außerdem wurde eine übergroße Datei nur abgeschnitten gelesen. | Exakte Modusprüfung und Größenabbruch oberhalb 4096 Byte; Werte werden nie protokolliert. |
| `G-095` | hoch | Kanalzustand und Auditzeile waren zwei Transaktionen. Bei Auditfehler konnte der Kanal ohne Nachweis aktiv bleiben. | Zustandswechsel und Hash-Ketteneintrag sind eine Transaktion; injizierter Auditfehler lässt den Kanal nachweislich `DISABLED`. |

Lokaler Nachweis: **30/30 Tests PASS**, `git diff --check` PASS.

Bekannte Grenze: Das Ollama auf dem Mac mini ist damit nicht angebunden. Die
zulässige Container-Brücke bezeichnet den Host des jeweiligen Containers, nicht
automatisch einen anderen Rechner. Für NAS → Mac mini fehlen weiterhin die
gemessene Zieladresse und ein ausdrücklich festgelegter, abgesicherter Netzweg.
Das ist kein stiller Fallback auf eine beliebige LAN-Adresse.


## 2026-09-08 — Systemscreening im Gesamtreview (Gerd via Claude Code, Auftrag Karl)

Prüfumfang: `058329a` plus Arbeitsbaum, gegen `INVARIANTEN.md`; 30/30 Tests unter
Python 3.9.6. Nur gelesen. Belegt mit Test: Invarianten 1, 2, 3, 5 (teilweise), 6, 8, 9,
10, 12, 14, 16. Nicht belegt: 4 (kein Hop-Zähler, Routen nur CEO→Identität), 7
(Ablehnung kein eigener Datensatztyp, „Audit kaputt bleibt Ablehnung" ungeprüft), 13
(Wiederherstellung in leeren Container und Wiederanlauf nach Absturz ungetestet), 15
(CEO-Meldung läuft über denselben Kanal, der gerade endgültig gescheitert ist).

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-096` | hoch | `deploy_nas.sh` rollt `git archive HEAD` aus; `HEAD` enthielt zum Prüfzeitpunkt weder die Ollama-Zielprüfung noch die exakte Modusprüfung (`G-092`/`G-094` lagen ungecommittet). Ein Deploy hätte die Fassung **vor** den Korrekturen geliefert, während lokal 30 Tests grün waren. | Behoben durch `4392ab7` (05:50, alle vier Korrekturen committet). Regel: kein Deploy aus einem Baum mit ungecommitteten Änderungen an `workforce/`. Nachcheck des Diffs offen. |
| `G-097` | hoch | Budgeterschöpfung verlor die Nachricht dauerhaft: `release_untouched` setzte sie auf `RECEIVED`, aber `poll_once()` sah nur neue Updates, der Telegram-Offset war vorgerückt, `messages_with_status()` rief niemand. Die Zusage „wartet bis zum nächsten Tag" wurde nicht eingelöst. | `App.resume()` zu Rundenbeginn: `RECEIVED` wird am Folgetag wieder aufgenommen (nicht jede Runde, sonst wiederholt sich der Hinweis), abgelaufene `IN_PROGRESS`-Leases sofort; Auditzeile `RESUME`. Drei Tests, zwei davon ohne Fix rot. Nachcheck offen. |
| `G-098` | mittel | `compose.yaml` mountet `anthropic_api_key` unbedingt, auch für reine Echo- oder Ollama-Konfiguration. Invariante 12 verlangt das Gegenteil; der vorhandene Test prüft nur den Code, nicht Compose. | Behoben `158e061`: Basis nur mit Bot-Token, Overlay `compose.claude.yaml`, `deploy_nas.sh` wählt aus `config.nas.json`; Tests gegen ssh-Attrappe (Claude lädt Overlay, Echo nicht, fehlender Schlüssel bricht ab). Nachcheck: geschlossen. |
| `G-099` | mittel | `deploy_nas.sh` und `backup_pull.sh` haben keinen Test. Bauform-Zusage 3 verlangt Datei plus Test gegen Attrappen plus Exitcode. | Behoben `46022eb`: `workforce/tests/test_scripts.py` — Archiv ist der committete Baum ohne Secrets/Zustand/unversionierte Dateien, Sicherung mit `600`, manipulierte Kette Exit 1, Rotation behält vierzehn. Nachcheck: geschlossen. |

Nicht geprüft: NAS-Zustand, laufende Container, Kanalzustand, echte Telegram- und
Anthropic-Aufrufe, `deploy_nas.sh`/`backup_pull.sh` im Lauf, Ollama-Anbindung, Inhalte der
Secret-Dateien. Annahme, nicht gemessen: die NAS fährt den Stand vor `G-092`.

**Letzte vergebene Befundnummer: `G-099`.**

## 2026-09-08 — Nachcheck `4392ab7..9767ccb` (Gerd via Claude Code, Auftrag Karl)

`G-096` geschlossen: `HEAD:workforce/config.py` trägt Ollama-Zielprüfung und exakte
Modusprüfung. `G-097` geschlossen für Wiederaufnahme nach Absturz und Tageswechsel:
Gegenprobe gemessen, `app.py`/`store.py` auf `4392ab7` zurückgesetzt, zwei der drei
neuen Tests rot; der Kanaltest allein ist ein Stempel und hält nur zusammen mit den
anderen. Geprüft und nicht bestätigt: Absturz zwischen `record_inbound` und `claim`
(Offset wird nach `handle_update` gesetzt, Telegram liefert erneut), Kanal `DISABLED`
über Tage, Doppellieferung nach Resume, UTC-Tagesgrenze, Versuchszählung. Regel 61 ist
eine Regel mit Herkunft, keine Meinung.

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-100` | mittel | Der Budgetwarter meldete sich genau einmal, dann schwieg er für immer: `notice()` leitet die Id aus `(message_id, text)` ab, der Text war konstant, `create_outbound` dedupliziert. Reichte das Budget dauerhaft nicht, wartete die Nachricht unbegrenzt, kein Versuch wurde geladen, `max_attempts` war unerreichbar, der CEO erfuhr nichts (Invariante 15 sinngemäß). Gemessen mit `max_usd_per_day=1e-7` über vier Tage: eine Notiz. | Der Tag steht im Text der Notiz; nach `max_attempts` Tagen ohne Budget wird die Nachricht `ABANDONED` mit Code `BUDGET_NEVER_SUFFICIENT` und sichtbarer Meldung. Test über vier Tage: zwei Tagesmeldungen, eine Aufgabe, ohne Fix rot. Nachcheck: geschlossen. |
| `G-101` | niedrig | Die Wiederaufnahme schrieb fremde Request-Ids doppelt: nach Resume standen `TG-2-CLAIM` und `TG-2-BOUNDARY` je zweimal im Audit; nur `RESUME` hatte ein eigenes Suffix (Invariante 11). | Jeder Durchlauf trägt `-R<n>` in der Request-Id, `n` aus der Zahl der bisherigen `RESUME`-Zeilen der Nachricht. Test: keine Request-Id doppelt, `TG-2-R1-CLAIM` existiert; ohne Fix rot. Nachcheck: geschlossen. |

Freigabe Gerd: `9767ccb` als Schließung von `G-096` und `G-097`. Nicht freigegeben: `G-098`
bis `G-101` und der Arbeitsbaum zum Zeitpunkt des Nachchecks.

**Letzte vergebene Befundnummer: `G-101`.**

## 2026-09-08 — Nachcheck `9767ccb..226f0b9` (Gerd via Claude Code, Auftrag Karl)

43/43 Tests, `test_mirrors` 2/2. `G-098` bis `G-101` geschlossen, je mit Gegenprobe in einem
Wegwerf-Klon (Overlay entfernt: drei Tests rot; ohne Aufgabe-Zweig: rot; ohne Suffix:
`TG-2-CLAIM` doppelt). Alle drei Compose-Aufrufe in `deploy_nas.sh` tragen die `-f`-Liste;
`backup_pull.sh` ruft `compose exec` ohne sie, unschädlich, weil der Projektname aus dem
Verzeichnis kommt. Geprüft und nicht bestätigt: Projektnamengleichheit, Statuswortschatz
`ABANDONED`, Doppelzählung nach erneuter Freigabe, Archivdichtigkeit, Rotationsgrenze.

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-102` | niedrig | Die Aufgabe nach `G-100` zählte Budgetfehlschläge und nannte sie „Tage": Ein Absturz nach `claim` führt über die Lease-Wiederaufnahme zu einem zweiten Fehlschlag am selben Tag, die Aufgabe kam früher als angekündigt. | Gezählt werden die verschiedenen `day`-Werte der `BUDGET_EXHAUSTED`-Zeilen plus heute. Test: zwei Fehlschläge an Tag 1 bleiben `RECEIVED`, Tag 2 gibt auf. Nachcheck offen. |
| `G-103` | niedrig | `deploy_nas.sh` las jeden Nicht-Null-Exit des Python-Ausdrucks als „kein Claude", auch defektes JSON oder fehlendes `python3`; und ein unbehandelter Python-Fehler endet mit Exit 1, also genau dem „Nein". | Exit 0 heißt Claude, 1 heißt kein Claude, alles andere bricht ab; der Ausdruck fängt Fehler und endet mit 2. Die Entscheidung fällt jetzt **vor** dem Archiv: Beim ersten Testlauf brach das Skript zwar ab, hatte aber Archiv und Konfiguration schon gestreamt. Test: defektes JSON, kein einziger ssh-Aufruf. Nachcheck offen. |
| `G-104` | niedrig | `README.md` nannte als ersten Betriebsbefehl `docker compose up -d --build` ohne `-f`-Liste; ein Handneustart hätte den Schlüssel-Mount verloren, fail-closed, aber der Satz führt in den Ausfall. | README verweist auf `deploy_nas.sh` und nennt für den Handneustart beide vollständigen Listen. Nachcheck offen. |

Freigabe Gerd: `226f0b9` deploybar, sobald P-1 entschieden ist, ausschließlich über
`deploy_nas.sh` aus sauberem Baum, mit Echo- oder Claude-Konfiguration. Nicht freigegeben:
Compose-Aufrufe von Hand, Ollama-Anbindung, NAS-Zustand.

**Letzte vergebene Befundnummer: `G-104`.**

## 2026-09-08 — Review nach dem Deploy `ca1bd20` (Gerd via Claude Code, NAS nur lesend)

Der ausgerollte Baum ist byte-identisch mit `ca1bd20`: 307 Dateien unter `workforce/` und
`skills/`, `sha256` je Datei gegen `git archive ca1bd20`, kein Unterschied, keine überzählige
Datei. Image `workforce:v1` gebaut 08:32:46, Container gestartet 08:33:11, kein Restart-Loop.
`docker inspect`: `User 10001:10001`, `ReadonlyRootfs true`, `CapDrop [ALL]`,
`no-new-privileges`, beide Secrets als `rw=false`-Binds, kein Secret in `Env`.

Je Invariante: 1 belegt aus dem Code — `Store.channel()` liest mit Vorgabe `DISABLED`, nur
`set_channel()` schreibt, und nur aus `/start`|`/stop` mit Auditzeile; `ACTIVE` nach Neustart
ist persistierter, früher auditierter Zustand, **kein Fail-closed-Verstoß**. 6 und 16 belegt:
`verify` PASS, Exit 0. 12 belegt für die Dateien (`-rw-r----- 1026:workforce`, Prozess
`10001`). 9 teilweise (`status`: 0 Aufrufe, 0.0000 von 2.00). 2, 3, 4, 5, 7, 8, 10, 13, 14, 15
nicht anwendbar, der Lauf hat keine Nachricht verarbeitet.

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-105` | mittel | Ein Deploy und ein Neustart hinterlassen keine Auditzeile. Aus der Datenbank allein ist nicht zu sagen, welcher Codestand seit wann antwortet (Invarianten 6, 13). | Behoben: `App.startup()` schreibt `STARTUP` mit Commit, Kanal und Standardidentität; der Commit kommt als `--build-arg` aus `deploy_nas.sh` ins Image (`WORKFORCE_COMMIT`, kein Geheimnis); `status` zeigt Stand und Datum. Tests für Zeile, Status und Deploy-Befehl. Wirkt ab dem nächsten Deploy; Nachcheck offen. |
| `G-106` | niedrig | Der im Nachweis berichtete Befehl `exec -T workforce python -m workforce verify` läuft ohne `--config` nicht (Exit 2 `CONFIG_FILE_MISSING`); die Zahlen stimmen mit `--config`, der Nachweis war nicht wortgleich reproduzierbar. | Behoben: Nachweis nennt den vollständigen Befehl. |
| `G-107` | mittel | `config.nas.json` ist gitignoriert. „deployed ca1bd20" nennt den Code, nicht die laufende Konfiguration; Budgetdecke, `allowed_chat_id`, Modellwahl liegen nur auf Mac und NAS. | Behoben über den Hash, nicht über Versionierung: `config.load()` trägt den SHA-256 der Datei, die `STARTUP`-Zeile und `status` nennen ihn, `deploy_nas.sh` druckt denselben. Der Stand ist damit Code-Commit plus Konfigurations-Hash, beides aus der Datenbank lesbar. Versionieren bleibt dem CEO (Chat-Id), ist aber nicht mehr nötig. Nachcheck offen. |
| `G-108` | mittel | `/volume1/docker/workforce` und `secrets/` sind `drwxrwxrwx`, `config.json` und `deploy_nas.sh` `-rwxrwxrwx`. `640` auf der Secretdatei ist in einem 777-Ordner ersetzbar, ohne dass `verify` etwas merkt. | offen. Korrektur ändert Rechte auf der NAS, braucht CEO-Freigabe im Chat. |

Geprüft und nicht bestätigt: Auditzeilen des Neustarts (keine vorhanden), Zustellabgleich
unter Last, Wiederherstellung aus `backup_pull.sh`, Telegram- und Anthropic-Aufruf, `/stop`,
`workforce.db-wal` von 1,1 MB ohne Checkpoint.

Freigabe Gerd: `ca1bd20` als laufender Stand auf der NAS im Claude-Betrieb, Budget 2.00, Kanal
`ACTIVE`. Nicht freigegeben: `G-105` bis `G-108`, `config.nas.json` als Konfigurationsquelle,
ein erster echter Modelllauf ohne beobachtete Runde.

**Letzte vergebene Befundnummer: `G-108`.**

## 2026-09-08 — Nachcheck Phase 3, `8d59d10..a15a129` (Gerd via Claude Code, Auftrag Karl)

60/60 Tests gegen `a15a129`, Gegenprobe in Kopie: 20 rot ohne die Änderung. Je Invariante
gemessen: 1 (Kanal aus, null Feuerungen), 3 (Route muss vorher erlaubt sein, kein Termin legt
eine an), 5 (zweiter Aufruf, eine Stunde später, Neustart mitten am Tag, Rückwärtssprung im
Tag: je null; erschöpftes Budget: `resume()` am Folgetag, ein Aufruf), 8 (Kette
`SCHEDULED, CLAIM, BOUNDARY, RESERVED, REPLIED`, der Prompt läuft durch `prepare_outbound`),
9 (Reserve vor dem Aufruf), 11 (`SCHED-<hash>-…`, keine Kollision mit `TG-<int>`). 06:00 UTC ist
08:00 CEST und 07:00 CET; die Umstellung fällt auf einen Sonntag, die Termine auf Mo/Do.

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-110` | niedrig | Springt die Uhr um eine Woche oder mehr zurück, feuert derselbe Termin erneut: gemessen zwei Provideraufrufe. | Behoben: je Termin hält der Store `schedule_seen_<id>`, das letzte berücksichtigte Fälligkeitsdatum; es bewegt sich nur vorwärts, gefeuert wird nur bei `seen < heute`. Test: Rückwärtssprung um sieben Tage, ein Aufruf. Nachcheck offen. |
| `G-111` | niedrig | Ein Termin, an dessen Tag das System nicht läuft, entfällt stumm: Dienstag nach ausgefallenem Montag null Feuerungen, keine Auditzeile, keine Meldung. | Behoben: liegt die letzte Fälligkeit vor heute hinter `seen`, entsteht einmal `SCHEDULE_MISSED` mit Tag; der allererste Lauf setzt nur die Basis, damit die Vorwoche nicht als verpasst gilt. Test: Sonntag Basis, Dienstag eine Zeile, zweite Runde keine zweite. Nachcheck offen. |

Geprüft und nicht bestätigt: echter NAS-Lauf über eine Woche, `flush_outbound` bei
Kanalwechsel in der Runde, Exception in `process()` innerhalb `check_schedule()`.

Freigabe Gerd: `a15a129` deploybar für den Zeitplanbetrieb Mo/Do 06:00 UTC an eine Identität
mit erlaubter Route. Nicht freigegeben zum Zeitpunkt des Nachchecks: der damals ungesicherte
`G-107`-Baum (seit `2bea5c6` committet), `G-110`/`G-111` (seither behoben), `G-108`.

**Letzte vergebene Befundnummer: `G-111`.**

## 2026-09-09 — Nachcheck `G-110`/`G-111`, Diff `7858fa2`, Stand `3ce525d` (Gerd via Claude Code, Auftrag: Vorlage P-2 vom 2026-09-08)

Prüfauftrag 2026-09-08 („sobald Gerd den Diff nachgeprüft hat"), Prüftag 2026-09-09. Der
Gegenstand liegt im Neubau: `workforce/app.py` und `workforce/tests/test_workforce.py`; seit
`6b70971` hat sich unter `workforce/` nur `reviews/` geändert. 63/63 Tests unter Python 3.9.6
(`python3 -m unittest discover -s workforce/tests -t . -q`, 2026-09-09). Gegenprobe: `app.py`
aus `7858fa2^` in einer Kopie, genau die zwei neuen Tests rot, die übrigen sechs der Klasse grün.

`G-110` und `G-111` sind geschlossen: Rückwärtssprung um sieben Tage ein Aufruf; verschlafener
Montag eine Zeile, zweite Runde keine zweite. Zusätzlich gemessen: zwei verschlafene Wochen
ergeben **eine** Zeile mit `day=2023-11-20, seen=2023-11-06`; der Montag dazwischen ist aus
der Zeile rekonstruierbar, nicht als eigene Zeile. Reicht.

Die Korrektur hat aber den Boden unter einer anderen Kontrolle verschoben (Klasse `G-014`).
Vor `7858fa2` war der **Datensatz** die Sperre für den Tag (`store.message(message_id) is not
None`): Wer ihn nicht geschrieben hatte, hatte nicht gefeuert. Jetzt ist es eine Einstellung,
die **vor** dem Datensatz geschrieben wird — und der Store läuft im Autocommit
(`isolation_level=None`), `set_setting` ohne eigene Transaktion. Beides gemessen mit einer
Sonde, die den Prozess zwischen zwei Anweisungen sterben lässt.

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-112` | mittel | `app.py`, `check_schedule()`: `set_setting(key, day)` steht vor `record_inbound()`, jede Anweisung ihr eigener Commit. Stirbt der Prozess dazwischen, gilt der Tag als erledigt — ohne Nachricht, ohne `SCHEDULED`, ohne `SCHEDULE_MISSED`. Gemessen: nächste Runde 0 Feuerungen, 0 Provideraufrufe; eine Woche später 0 `MISSED`-Zeilen. Eine Marke ohne dauerhafte Wirkung, die nicht zurückgegeben wird — Invariante 5 in der Klausel aus `G-082`; aus der Datenbank allein nicht erklärbar (6). Das ist der Ausgang von `G-111` über den Absturzpfad. | offen. Kleinste Korrektur: Reihenfolge tauschen — erst `record_inbound` (ist `INSERT OR IGNORE`, also wiederholbar), `SCHEDULED` nur bei `created`, **dann** `set_setting`, dann `process()` (der Claim ist idempotent). Test: `record_inbound` genau einmal werfen lassen, zweite Runde derselbe Tag: genau eine Nachricht, eine `SCHEDULED`-Zeile, ein Provideraufruf. Gegenprobe: gegen `3ce525d` ist dieser Test rot, gemessen. |
| `G-113` | niedrig | Der `SCHEDULE_MISSED`-Zweig schreibt die Auditzeile in einer Transaktion und die Einstellung in einer zweiten. Absturz dazwischen: die nächste Runde schreibt dieselbe Request-Id `SCHED-MONTAG-2023-11-06-MISSED` erneut — gemessen zwei Zeilen mit identischer Request-Id (Invariante 11, Klasse `G-101`). | offen. Kleinste Korrektur: beides unter demselben `BEGIN IMMEDIATE` — eine Store-Methode, die `_append_audit` und das `INSERT … ON CONFLICT` in einer Transaktion ausführt. Die umgekehrte Reihenfolge wäre die falsche Korrektur: dann ginge die Zeile verloren statt doppelt. Test: `set_setting` innerhalb der Transaktion werfen lassen — danach null Zeilen; zweite Runde genau eine. |

## Geprüft und nicht bestätigt

Rücksprung der Uhr innerhalb desselben Tages; Kanal `DISABLED` am Fälligkeitstag, `ACTIVE`
am Folgetag → `MISSED`-Zeile (aus dem Code abgeleitet, nicht gemessen); Exception in
`process()` innerhalb der Terminschleife (weiter offen seit 2026-09-08); NAS nicht angefasst,
sie läuft nach Aktenlage auf `ca1bd20` ohne Zeitplan.

## Unabhängiger Nachweis

`git diff --stat 6b70971..HEAD -- workforce/`: nur `reviews/`. Testlauf 63/63. Gegenprobe
ohne Fix: 2 rot. Sonde `G-112`: `seen=2023-11-06`, `message exists: False`, `fired in next
round: 0`, `MISSED rows a week later: 0`. Sonde `G-113`: `rows with identical request_id: 2`.
Sonde zwei Wochen: eine Zeile, Nutzlast `{day: 2023-11-20, seen: 2023-11-06}`, ein Aufruf.
`deploy_nas.sh` prüft den Baum nur mit Hinweis und rollt `git archive HEAD` aus — kein
Befund, weil der Arbeitsbaum die NAS nicht erreichen kann.

Ohne Nummer, weil Dokument und nicht Code: Vorlage P-2 sagt im Sachverhalt „`G-110`, `G-111`
sind behoben … Damit ist Option (b) erfüllt", geschrieben **vor** diesem Nachcheck. Der Satz
fürs Log ist richtig, der Sachverhalt lief der Messung voraus. `INVARIANTEN.md`, „Stand der
Belege" (`6c5903b`), gibt mein Screening vom 2026-09-08 korrekt wieder: **abgenommen**; 7 und
15 tragen einen Meilenstein statt eines Datums, das reicht, solange „nach Phase 3" der
nächste ist. Der Arbeitsbaum ist heute nicht sauber (`skills/marlene/…`,
`skills/gedaechtnis/thorsten.md`): vor dem Fenster committen oder bewusst stehen lassen.

## Nicht blockierendes Backlog nach dem Lauf

`G-113`. Die beiden Sonden gehören als Tests in `ScheduleTest`, nicht in mein Scratch.
Exception in `process()` innerhalb der Schleife: ein Test, der den zweiten Termin nach einem
werfenden ersten noch feuern sieht — oder die Entscheidung, dass er es nicht soll.

## Gate und Auftrag an Claude Code

**ROT** für P-2 auf Stand `3ce525d`. `G-112` widerlegt Invariante 5 in der Klausel, die
`G-082` hineingeschrieben hat, und zwar gemessen, nicht gelesen; das Fenster ist zwei
Anweisungen breit, aber die Reihenfolge ist die verkehrte, und der Eingriff ist eine
Umstellung von drei Zeilen plus Test. Auftrag: `G-112` und `G-113` beheben, je ein Commit,
Antwort in der Spalte Korrektur/Nachweis wie bisher. Nach dem Nachcheck (Gegenprobe rot ohne
Fix, Sonden grün) ist der Stand für den Zeitplanbetrieb Mo/Do 06:00 UTC freigegeben; dann
kann P-2 laufen, und ich prüfe nach dem Lauf gegen `INVARIANTEN.md`. Nicht freigegeben:
`G-108` (unverändert, braucht das NAS-Fenster), ein Deploy vor der Korrektur.

**Letzte vergebene Befundnummer: `G-113`.**
