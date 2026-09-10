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
| `G-108` | mittel | `/volume1/docker/workforce` und `secrets/` sind `drwxrwxrwx`, `config.json` und `deploy_nas.sh` `-rwxrwxrwx`. `640` auf der Secretdatei ist in einem 777-Ordner ersetzbar, ohne dass `verify` etwas merkt. | Behoben 2026-09-10 (CEO R-2): Ordner und `secrets/` `750`, `config.json` `640`, `deploy_nas.sh` `750`, Gruppe `10001`, Eigentümer bleibt `1026`; Container liest weiter, `verify` PASS, `tar`-Ziel beschreibbar. Nachweis `workforce/evidence/2026-09-10_deploy_phase3_und_rechte.md`. Review nach dem Lauf offen. |

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
| `G-112` | mittel | `app.py`, `check_schedule()`: `set_setting(key, day)` steht vor `record_inbound()`, jede Anweisung ihr eigener Commit. Stirbt der Prozess dazwischen, gilt der Tag als erledigt — ohne Nachricht, ohne `SCHEDULED`, ohne `SCHEDULE_MISSED`. Gemessen: nächste Runde 0 Feuerungen, 0 Provideraufrufe; eine Woche später 0 `MISSED`-Zeilen. Eine Marke ohne dauerhafte Wirkung, die nicht zurückgegeben wird — Invariante 5 in der Klausel aus `G-082`; aus der Datenbank allein nicht erklärbar (6). Das ist der Ausgang von `G-111` über den Absturzpfad. | Behoben 2026-09-10: Reihenfolge `record_inbound` → `SCHEDULED` → `set_setting` → `process()`. Abweichung von der vorgeschlagenen Korrektur: `SCHEDULED` hängt nicht an `created`, sondern an `audit_count("SCHEDULED") == 0` — stirbt der Prozess zwischen Datensatz und Zeile, wäre `created` in der nächsten Runde falsch und die Zeile entfiele; so entsteht sie genau einmal. Test wie vorgeschlagen (Absturz nach dem Datensatz, zweite Runde: eine Nachricht, eine Zeile, ein Aufruf), ohne Fix rot. Nachcheck offen. |
| `G-113` | niedrig | Der `SCHEDULE_MISSED`-Zweig schreibt die Auditzeile in einer Transaktion und die Einstellung in einer zweiten. Absturz dazwischen: die nächste Runde schreibt dieselbe Request-Id `SCHED-MONTAG-2023-11-06-MISSED` erneut — gemessen zwei Zeilen mit identischer Request-Id (Invariante 11, Klasse `G-101`). | Behoben 2026-09-10: `Store.audit_and_set()` schreibt Zeile und Einstellung unter einem `BEGIN IMMEDIATE`. Test: Einstellung wirft in der Transaktion, danach null Zeilen, zweite Runde genau eine, keine Request-Id doppelt, Kette intakt; ohne Fix rot. Nachcheck offen. |

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

## 2026-09-10 — Review nach dem Lauf: Deploy `35e7ae3` und Rechte `R-2` (Gerd via Claude Code, Auftrag Karl vom 2026-09-10, Prüftag 2026-09-10)

NAS nur lesend geprüft.

| Befund | Schwere | Beobachtung | Korrektur/Nachweis |
|---|---|---|---|
| `G-114` | mittel | Der Deploy lief auf `35e7ae3`. Mein Gate vom 2026-09-09 stand **ROT** und sagte wörtlich „Nicht freigegeben: … ein Deploy vor der Korrektur"; `G-112` und `G-113` sind unverändert im ausgerollten Code (`workforce/app.py:98–106`, `set_setting` vor `record_inbound`; `SCHEDULE_MISSED` und Einstellung in zwei Transaktionen). Der Nachweis `evidence/2026-09-10_deploy_phase3_und_rechte.md` beruft sich auf die Vorab-Freigabe `a15a129` und nennt beide Befunde nicht; die Vorlage P-2 ebenfalls nicht. Damit läuft Invariante 5 (Klausel `G-082`) produktiv verletzt: stirbt der Prozess zwischen Marke und Nachricht, entfällt der Termin stumm. Kein Schaden eingetreten — der Lauf vom 2026-09-10 ist vollständig. | Bestätigt, Verfahrensfehler von Karl: `REVIEW_GERD.md` vor dem Deploy nicht neu gelesen, Vorlage P-2 nannte den Stand vom 2026-09-08. Regel 71 in `CLAUDE.md`. `G-112`/`G-113` behoben; zweiter Deploy als Vorlage P-3 vor dem 2026-09-14. |
| `G-115` | mittel | Karls Frage „gibt es einen Zustand, in dem `verify` das nicht bemerkt hätte": ja, denselben wie vor `R-2`. `config.py:275–291` prüft den Modus der **Datei** (`600`/`640`), nie den des Verzeichnisses, und läuft im Container, der den Host-Ordner nicht sieht. `chmod 777 /volume1/docker/workforce/secrets` bei unveränderter `640`-Datei ergäbe weiter `RESULT: PASS`. `deploy_nas.sh` setzt Ordnerrechte nicht; die `R-2`-Befehle liefen von Hand im Wegwerf-Container und stehen in keiner versionierten Datei (Bauform-Zusage 3, Regel 21 mit umgekehrtem Vorzeichen: setzen ersetzt prüfen nicht). Nicht gemessen, weil die Gegenprobe eine Zustandsänderung wäre; aus dem Code abgeleitet. | Behoben 2026-09-10: `deploy_nas.sh` setzt im Wegwerf-Container `chgrp -R 10001`, Ordner `750`, Dateien `640`, Skript `750`, liest `stat` für Ordner, `secrets/`, `config.json` und Token zurück und bricht bei Abweichung vor `up` ab. Test gegen die Attrappe: `stat` antwortet `777` → Abbruch, kein `up`. Nachcheck offen. |
| `G-116` | niedrig | Die 24 ausgerollten Dateien unter `/volume1/docker/workforce` stehen weiter `-rwxrwxrwx+` (DSM-ACL); nur der Elternordner ist `750`. Laufzeitwirksam ist das nicht (`Dockerfile` `COPY`, kein Bind-Mount), aber sie sind die Bauquelle des nächsten Image. Und der Commit in der `STARTUP`-Zeile ist ein `--build-arg` aus `deploy_nas.sh`, also eine Behauptung über den Baum, keine Messung an ihm: Ein verändertes `app.py` im Ordner ergäbe dieselbe Zeile `35e7ae36717d`. Die Byte-Identität habe ich von Hand gemessen (identisch); das System misst sie nicht. | Behoben 2026-09-10: Manifest aus `git archive HEAD workforce` (SHA-256 je Datei), `sha256sum -c` auf der NAS im Wegwerf-Container, Abbruch vor Rechten und `up`; die Dateirechte `640` setzt derselbe Schritt wie `G-115`. Test: Manifest enthält `app.py` und keine Secrets, Attrappe meldet Abweichung → Abbruch. Was nicht gemessen wird: der Container hat den Baum, den er baut; der Commit in `STARTUP` bleibt eine Angabe des Deploys, jetzt aber eine, die der Prüfsummenschritt deckt. Nachcheck offen. |

### Unabhängiger Nachweis (2026-09-10, NAS lesend)

Baum byte-identisch mit `35e7ae3`: 28 Dateien unter `workforce/` und alle unter `skills/`,
SHA-256 je Datei gegen `git ls-tree 35e7ae3`, kein Unterschied. Die zwei Abweichungen gegen
`HEAD` sind der Dokumentationscommit `3b6cae3` **nach** dem Deploy, kein Driftbefund.
Konfiguration: `3490e16af4cc…` auf Mac, NAS und in `/etc/workforce/config.json` identisch.
Zwei `STARTUP`-Zeilen (`seq 61`, `69`), beide `commit 35e7ae36717d…`, `config_sha256
3490e16af4cc…`, Kanal `ACTIVE` — `G-105` und `G-107` **geschlossen**, gemessen am realen Lauf.
Zeitplan: `SCHEDULED` genau einmal (`seq 62`), `schedule_seen_DONNERSTAG_ENTSCHEIDUNGEN =
2026-09-10`, `schedule_seen_MONTAG_LAGE = 2026-09-07` (Basis, kein Fehlschlag), null
`SCHEDULE_MISSED`-Zeilen; der Neustart nach `R-2` hat **nicht** ein zweites Mal gefeuert —
`G-110`/`G-111` in Produktion bestätigt. Zustellung: `OUT-57C856AC…` `SENT`, `external_id 43`,
kein `OUT` ohne externe Id, keine doppelte externe Id, keine doppelte `SENT`-Zeile, jede
`IN`-Nachricht mit `DONE` genau eine Antwort (die zwei `IGNORED` keine, wie vorgesehen) —
Invariante 16 belegt. Audit-Kette selbst nachgerechnet, nicht `verify` geglaubt: 69 Zeilen
intakt; Gegenprobe mit einer im Speicher veränderten Nutzlast schlägt bei `seq 6` an
(Invariante 6). Rechte: Ordner und `secrets/` `750 1026:10001`, `config.json` und beide
Secrets `640 1026:10001`, im Container `uid=10001 gid=10001` — die Gruppe hat auf dem Ordner
`r-x`, also ist die Secretdatei aus dem Container nicht ersetzbar. `G-108` in der Sache
**geschlossen**, der Wächter dazu fehlt (`G-115`).

### Geprüft und nicht bestätigt

Invariante 8: `BOUNDARY` `policy BODY`, `fields_sent [body, message_id, sender_id]`, 195
Zeichen, Nutzlast-Hash gesetzt — hat gehalten. Invariante 9: `RESERVED worst 0.152105` vor
`REPLIED usd 0.047385`, Tagesstand `0.0474 von 2.00` — hat gehalten. Invariante 12: keine
Secretdatei außerhalb `secrets/`, kein Wert gelesen. Nicht anwendbar in einem reinen
Lesefenster: 1 (fail-closed beim Leerstart), 2 (Kill Switch), 4, 7, 13, 15 — 4/7/13/15 stehen
in `INVARIANTEN.md` datiert offen, unverändert. Invariante 3, 10, 11, 14: an diesem Lauf nicht
gegenprobbar, weil er nur einen Termin und keine Ablehnung enthält. Karls Auftrag nennt „neue
Befunde ab `G-112`"; `G-112` und `G-113` sind seit dem 2026-09-09 vergeben, die Reihe läuft ab
`G-114`.

### Gate und Auftrag an Claude Code

**ROT** für den Zeitplanbetrieb, unverändert aus dem Nachcheck vom 2026-09-09: `G-112` läuft
jetzt produktiv. Der Lauf selbst ist sauber und `G-105`, `G-107`, `G-108` sind geschlossen.
**Freigegeben:** der ausgerollte Stand `35e7ae3` als Nachweislage — Baum, Konfiguration,
Startzeile, Zustellung und Audit sind gemessen und tragen. **Nicht freigegeben:** der
Weiterbetrieb des Zeitplans über den nächsten Termin (2026-09-14) hinaus ohne `G-112`/`G-113`;
`G-115` und `G-116`; ein weiterer Deploy ohne Rechte- und Prüfsummenschritt im Skript.
Auftrag: `G-112`, `G-113` beheben (je ein Commit), `G-115` und `G-116` in `deploy_nas.sh`, dann
ein zweiter Deploy vor dem 2026-09-14.

**Letzte vergebene Befundnummer: `G-116`.**

## 2026-09-10 — Nachcheck `3b6cae3..6cda0c5` (Gerd via Claude Code, Auftrag Karl)

67 Tests, `sh -n` sauber, Spiegel identisch. Gegenprobe je Korrektur in einer Kopie: Reihenfolge
zurückgedreht → `G-112`-Test rot; `audit_and_set` auf zwei Transaktionen → `G-113`-Test rot;
Rechte- und Prüfsummenblock entfernt → drei Skripttests rot. **`G-112`, `G-113`, `G-115`,
`G-116` geschlossen.** Abweichung bei `G-112` (`audit_count` statt `created`): richtig, kein
neues Loch — Sonde mit Absturz nach der Zeile, vor der Marke: eine Nachricht, eine Zeile, ein
Aufruf. `stat -c '%a %g %n'` ist busybox-tauglich, die Erwartung stimmt nach dem `sed`.

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-117` | mittel, abgeleitet | Die Rückmessung misst Modusbits von vier Pfaden. (a) Die Dateien auf der NAS tragen ein `+` (DSM-ACL); `%a` liest keine ACL, ein „750" kann grün sein, während eine ACL weiter breit erlaubt. (b) `secrets/anthropic_api_key` wird gesetzt, aber nie zurückgelesen. | offen, keine Deploy-Sperre. Vorschlag Gerd: ACL neben `stat` lesen (`getfacl`/`synoacltool`), Erwartung je Secret aus `$secrets` erzeugen statt fest schreiben. |
| `G-118` | niedrig | Der Prüfsummenschritt deckt `workforce/`, nicht `skills/`, obwohl der Baum nach `/etc/workforce/skills` gemountet ist; und `sha256sum -c` meldet keine unerwartete Datei (Klasse `G-020`/`G-047`). Regel 73 sagt mehr, als der Schritt misst. | offen, keine Deploy-Sperre. Vorschlag: zweites Manifest für `skills/`, und ein `find`-Vergleich gegen die Manifestliste für Unerwartetes. |

Geprüft und nicht bestätigt: Manifestformat `shasum` → `sha256sum -c`, keine Secrets im
Manifest, Reihenfolge Prüfsumme → Rechte → Abbruch vor `up`, `chmod 640` bricht nichts.

Freigabe Gerd: `6cda0c5` für den zweiten Deploy (P-3, Option a). Nicht freigegeben: der
Logsatz „offen danach: keine" — offen bleiben `G-117`, `G-118`.

**Letzte vergebene Befundnummer: `G-118`.**
