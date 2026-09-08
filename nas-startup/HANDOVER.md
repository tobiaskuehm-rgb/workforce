# Arbeitsstand und Prüfschleife

**Zuletzt aktualisiert:** 2026-09-08, morgens — von Claude Code (Karl).

**Offenes Entscheidungsgate: Neubau oder Weiterführung.** Der CEO hat dem
Neubau am 2026-09-03 im Chat zugestimmt; Gerd hat am selben Abend festgehalten,
dass das für eine Entscheidung dieser Tragweite **nicht autoritativ** ist:
`PENDING-DEC` genügt nicht, im maßgeblichen Decision Log ist `DEC-037` der
jüngste Eintrag, `PEO-007` und `HO-027` stehen offen. Alles Folgende ist
deshalb **Vorschlag**, bis der CEO ausdrücklich entscheidet — Vorlage dafür:
`ENTSCHEIDUNGSVORLAGE_NEUBAU.md` im Repo-Wurzelverzeichnis.

Der Vorschlag, in drei Teilen:

1. **Prototyp einfrieren, Stand `781cc84`.** Kein neues Feature, keine neue
   Migration, keine neue Regel; er liefert dem Neubau die Befundliste als
   Spezifikation, die Produkttests als Vorlage und das Bedrohungsmodell.
2. **Eine Seite Invarianten als `DEC`.** Entwurf in `INVARIANTEN.md` im
   Repo-Wurzelverzeichnis, geschrieben von Claude Code, von Gerd um fünf
   Punkte ergänzt; der CEO unterschreibt, die Nummer entsteht im
   iCloud-Quellensatz, nicht hier.
3. **`HO-027` pausieren**, bis die Bauform entschieden ist; Marlene käme in
   den Neubau. Bis zur Entscheidung ruht sie ohnehin, weil keine Änderung am
   Prototyp beginnt.

Ebenfalls Vorschlag, nicht Beschluss: **Der isolierte 009/010-Wegwerflauf
entfällt**, weil er einen Eigentümerwechsel für einen Prototyp beweisen würde,
der keine Produktivmigration mehr bekäme; die Eigenschaft dahinter —
Eigentümerrolle statt Superuser vom ersten Tag — steht auf der
Invariantenseite. Gerds Freigabe des Laufs aus `e022862` bleibt gültig, falls
der CEO die Weiterführung wählt.

Vorgeschlagene Bauform: „ein Prozess" — ein Python-Programm, eine
SQLite-Datei, ein Container, hash-verkettetes Audit, Provider Anthropic und
Ollama hinter derselben Text-rein-Text-raus-Schnittstelle, Telegram als dünner
Adapter, Paperless-ngx nur fürs Private Office. Läuft auf dem Mac wie auf der
NAS. Drei Meilensteine, jeder endet mit einem echten Lauf; Review nach dem
Lauf gegen die Invariantenseite.

**Gerds Stand (2026-09-03 abends):** `G-082` bis `G-091` akzeptiert, der
Prototyp bleibt vorläufig unverändert und wird nicht weiter geprüft. Seine
fünf Auflagen an die Invariantenseite und die Entscheidungsvorlage sind
abgearbeitet, Antwort in `REVIEW_ANTWORTEN.md`, letzter Abschnitt.

**Bis zur ausdrücklichen CEO-Entscheidung gilt: kein NAS-Lauf, kein Neubau,
keine Änderung am Prototyp, kein weiterer Prüfzyklus.**

**Nachtrag 2026-09-03, spät — CEO im Chat: „mach einfach, jede Zeile kostet".** Der CEO
hat das Gate im Chat geschlossen: Neubau, jetzt, ohne weitere Vorlage. Das ist eine
Chat-Freigabe (`CEO-CHAT-2026-09-03/PENDING-DEC`); der Eintrag im Decision Log bleibt
seine Aufgabe. Der Neubau liegt in `workforce/` im Repo-Wurzelverzeichnis — ein Paket,
Standardbibliothek, eigene Tests unter `workforce/tests/`, Anleitung in
`workforce/README.md`. Nichts auf der NAS; der erste echte Lauf ist auf dem Mac mit
Echo-Provider und dem Telegram-Bot geplant. Prototyp unter `nas-startup/` unverändert.

**Erste echte Antwort: 2026-09-03, abends, auf dem Mac.** Neuer Telegram-Bot, Kern aus
`workforce/` (Stand `827e64b`), Echo-Provider, kein Modell, keine NAS. Aus der
Zustandsdatei: eine Nachricht bei Kanal `DISABLED` als `IGNORED` verbucht, `/start` als
`CHANNEL ACTIVE` mit Akteur `CEO`, dann für eine Nachricht die Kette `RECEIVED`, `CLAIM`,
`BOUNDARY`, `RESERVED`, `REPLIED`, `SENT` mit externer Telegram-Id, `DONE`. `verify`:
Audit intakt, Zustellabgleich `PASS`. Der Prototyp hat diesen Weg in vier Tagen nie
gegeben; der Neubau nach einem Abend.

**Erste Modellantwort: 2026-09-03, später Abend, auf dem Mac.** `claude-sonnet-5` über die
Messages-API ohne SDK, Datengrenze `BODY`. Aus der Datei: 296 Eingabe- und 112 Ausgabe-Token,
0,0017 USD, keine Ablehnung, `SENT` mit externer Id, `DONE`, `verify` `PASS`. Davor zwei 400er,
weil ein identitätsgebundener Schlüssel den Header `anthropic-workspace-id` verlangt; die Id
steht seitdem in der Konfiguration (`602095d`), und eine abgewiesene Anfrage gibt ihre
Reservierung zurück (`47afbb4`).

**Auf der NAS seit 2026-09-03, 23:25:** CEO im Chat „mach weiter". `workforce/deploy_nas.sh`
(Stand `42a371f`) hat nach `/volume1/docker/workforce` ausgerollt: Archiv aus `git ls-files`,
Konfiguration und Secrets über ssh-stdin (die NAS hat kein SFTP, `scp` bricht ab), Gruppe
`10001` und `640` über einen Wegwerf-Container, `compose build` und `up`. Container
`workforce-workforce-1`, Image `workforce:v1`, Kanal beim Start `DISABLED`. Ein Bot-Token
verträgt einen Abfrager: Solange der Mac-Prozess lief, antwortete Telegram mit 409; nach
dessen Ende verstummte das. Der Mac-Prozess ist beendet, die NAS ist der einzige Abfrager.

**Für Gerd:** Review nach dem Lauf gegen `INVARIANTEN.md`, Stand `42a371f`, Auditzeilen in
der Zustandsdatei des Containers (`docker compose exec workforce python -m workforce verify
--config /etc/workforce/config.json`). Kein Prüfzyklus am Prototyp.

**Skills eingesammelt, 2026-09-06.** Ein Ort, eine Form: `skills/NAME/SKILL.md` im Repo ist
zugleich Skill für Claude Code (Verweis aus `~/.claude/skills`) und Systemtext der Identität im
Bot (`system_prompt_file`). Marlene aus `~/.claude/skills` geholt; Karl, Thorsten, Anastasia
aus dem iCloud-Quellensatz (`00_COMPANY_STATE.txt`, `interim-bus/rules`, Thorstens
Opportunity-Filter v0.2) geschrieben; CFO neu, Name offen; Gerd aus seinen Prüfrunden, nur
für Claude Code und Codex. **Für Codex/Gerd:** Die Skill-Kopien im iCloud-Satz sind ab jetzt
Archiv; Änderungen nur noch im Repo. Register in `skills/README.md`, geführt von Anastasia.
Auf der NAS läuft Stand `39a3bc5` mit fünf Identitäten, Karl als Standard, `@NAME` im Chat.

**Karl v2, 2026-09-07:** erster Skill nach Marvs Verfahren — Feld mit Quellen, drei Fassungen,
sechs Prüffälle, zwei Runden mit fremden Instanzen (39/43 gegen 27/43 ohne Skill), Praxistest an
den echten Berichten vom 2026-09-07. Übergabe in `skills/karl-workspace/05_uebergabe.md`. Auf der
NAS seit 11:53 UTC (Stand `de8818b`). Deploy rollt seitdem den committeten Baum aus (`git archive`).

**Aktive Arbeit:** **Claude Code, Neubau in `workforce/`.** Nächster Schritt: Gerds Review des
Neubaus nach dem Lauf gegen `INVARIANTEN.md`, Stand `39a3bc5`, Befunde ab `G-092` in
`REVIEW_GERD.md` im Wurzelverzeichnis. `HO-027` (Anmeldung unten) ruht.

**Gerd abgeschlossen, 2026-09-08:** eng begrenzter Nachcheck und Korrektur ausschließlich
in `workforce/config.py`, `workforce/providers.py`, `workforce/store.py` und den zugehörigen
Tests. Vier reproduzierte Befunde `G-092` bis `G-095` stehen in `REVIEW_GERD.md`; Regeln
57–60 sind hier im Repo ergänzt. Lokaler Nachweis: 30/30 Tests und `git diff --check` PASS.
Keine Skill-, Marlene-, NAS- oder Produktivänderung. Ollama auf dem Mac mini ist ausdrücklich
noch **nicht** angebunden: Dafür fehlen gemessene Zieladresse und freigegebener Netzweg.

**Gesamtreview und Wiederaufnahme, 2026-09-08 (Karl, Claude Code):** Der CEO hat im Chat ein
Review über alle Identitäten angeordnet (`CEO-CHAT-2026-09-08/PENDING-DEC`); sechs Berichte,
Ergebnis in `workforce/reviews/2026-09-08_gesamtreview_karl.md`, Prozess ITERATE, Fortschritt
PASS. Gerds Befunde daraus `G-096` bis `G-099` stehen in `REVIEW_GERD.md`. `G-096` (Deploy aus
`HEAD` ohne die Korrekturen) ist durch `4392ab7` behoben, `G-097` (Budgetwarter ging still
verloren) durch `App.resume()` mit Regel 61 und drei Tests; `G-098` (`158e061`) und `G-099`
(`46022eb`) sind behoben. Gerds Nachcheck hat `G-096`/`G-097` freigegeben und `G-100`
(Budgetwarter ohne Ende und ohne zweite Meldung) und `G-101` (Request-Ids der Wiederaufnahme
doppelt) gestellt; beide behoben, Regeln 62–65. Zweiter Nachcheck: `G-098` bis `G-101`
geschlossen, `G-102` bis `G-104` (niedrig) gestellt und behoben, Regeln 66–68, Nachcheck dafür
offen. **Gerds Freigabe: `226f0b9` ist deploybar, sobald der CEO P-1 entscheidet**, nur über
`deploy_nas.sh` aus sauberem Baum. Die
vier ungecommitteten Skillbündel sind in fünf Commits gesichert. **Kein Deploy, nichts auf
der NAS.** **Deploy `ca1bd20` ausgeführt, 2026-09-08 vormittags** (CEO-Freigabe im Chat): `verify` PASS,
Kanal `ACTIVE`, Decke 2,00 USD; Nachweis `workforce/evidence/2026-09-08_deploy_ca1bd20.md`.
CEO-Entscheidungen desselben Chats: `FILTER.md` ist das Instrument für C, kein
Nebentätigkeitsantrag jetzt, Decke 2,0 USD/100 Aufrufe, CFO heißt **Wolle**, Marlene bleibt in
Probezeit, Marv ist Mitarbeiter, Marlene bis Phase 4 auf Kopien, **Karl ist COO auf Probe**.
Gerds Review nach dem Lauf: Stand freigegeben, `G-105` bis `G-108` offen (Startup-Auditzeile,
Konfiguration nicht versioniert, 777-Rechte auf der NAS; `G-106` behoben). 3-Loop über das
Projekt und Organigramm: `workforce/reviews/2026-09-08_3loop_projekt_karl.md`, drei Fragen an
den CEO bis 2026-09-12. **3-Loop angenommen (CEO, 2026-09-08):** Organigramm in `skills/ORGANIGRAMM.md` mit Wächter
`skills/test_organigramm.py`; Takt Montag Lage, Donnerstag Entscheidungen, Wochenende Betrieb,
in Karls Skill; Phase 3 nächster Meilenstein; `G-105` behoben (Startzeile mit Commit, Regel 69),
wirkt ab dem nächsten Deploy. **Für Anastasia:** Register um Verweis auf `ORGANIGRAMM.md` oder
Spalte Vorgesetzter ergänzen; deine Datei war offen, ich habe sie nicht angefasst.
**Für Marv:** Karl nach der Skilländerung (Takt) gegen seine sechs Prüffälle nachmessen.
**Phase 3 gebaut, 2026-09-08:** `Config.schedule` (`weekday`, `hour` in UTC, `identity`, `prompt`, Route muss vorher
erlaubt sein), `App.check_schedule()` legt an fälligen Tagen eine Nachricht an, die danach den
normalen Pfad läuft (Budget, Wiederaufnahme aus `G-097`/`G-100`, Audit) — kein eigener
Zweitpfad. Montag 06:00 UTC Wochenlage, Donnerstag 06:00 UTC Entscheidungstermin, an Karl
(`config.nas.json`). 60 Tests, Gegenprobe bestanden (`workforce/evidence/2026-09-08_phase3_schedule.md`).
Regel 70. **Noch nicht deployt** — der Bot auf der NAS hat den Zeitplan noch nicht.
`G-107` behoben über den Konfigurations-Hash (`config.load()`, `STARTUP`-Zeile, `status`,
Deploy-Ausgabe); Invarianten 4, 7, 13, 15 in `INVARIANTEN.md` datiert offen gekennzeichnet.
Donnerstagsvorlagen in `workforce/reviews/2026-09-10_donnerstag_vorlagen.md`: P-2 Deploy
Phase 3, R-2 `G-108` Ordnerrechte, S-2 C-Kandidaten. Gerds Nachcheck des Phase-3-Diffs
läuft. Nächster Schritt: Nachcheck eintragen, dann Donnerstag.

**Zur Historie:** Commit `781cc84` trägt die Botschaft „die Schleife bekommt
ein Ende", enthält aber nur die `HO-027`-Anmeldung der Parallelsitzung — mein
Edit war am inzwischen veränderten Kopf gescheitert, die Befehlskette lief
trotzdem weiter. Die Entscheidung, die dort stehen sollte, ist durch den
Block oben ersetzt und überholt.

**Übergabe an:** **Gerd.** Er hat seit dem 2026-09-03 wieder Nutzungsguthaben;
die Vertretung ist damit beendet. Ihre acht Befunde stehen unter dem Tag
`SV-2026-09-03-NN` in `nas-startup/REVIEW_STELLVERTRETUNG_2026-09-03.md` —
ohne `G-`Nummer, die vergibt er (`G-006`). Was er zuerst lesen sollte, steht
unten unter „Leseweg für Gerd".

**Ruht seit 2026-09-03 abends (Entscheidungsgate oben) — davor aktive Arbeit:** **Claude Code, seit 2026-09-03 nachmittags: `HO-027`** — Marlene (`POA-001`) technisch integrieren. Betroffen: `postgres-init/011_*`, `postgres-tests/011_*`, `compose.yaml` (neues Gate), `private-office/`, `PRIVATE_OFFICE_RUNBOOK.md`, `deploy_paths.txt`, neue Wächter unter `workforce-agent/`, und das Skillpaket `marlene/skills/private-office-assistant/` im Repo-Wurzelverzeichnis. Nichts auf der NAS. Die vorige Zeile lautete „keine" und gilt für alles andere weiter. Gerds neunzehnter Zielnachcheck (`b4149de`) ist
abgearbeitet: **`G-082` bis `G-091` bestätigt und behoben**, je Befund ein
Commit, jede Gegenprobe der Gesamtprüfung als dauerhafter Test, Regeln 53–56.
Antworten in `REVIEW_ANTWORTEN.md`. **Kein NAS-Lauf, kein Integrationslauf.**
Sein Gate gilt weiter: ROT bis zu seinem diff-basierten Nachcheck, danach die
gesonderte CEO-Freigabe für den isolierten 009/010-Wegwerflauf.

Davor: Gerds verbindlicher nächster Schritt aus `b7c593b`
ist abgearbeitet: `G-080`/`G-081` behoben (Antworten in `REVIEW_ANTWORTEN.md`),
Prüfstand `557df50` festgehalten, und die **Gesamtprüfung des aktiven
Release-Kandidaten** liegt in `nas-startup/GESAMTPRUEFUNG_2026-09-03.md` —
neun neue Befunde unter dem Tag `GP-2026-09-03-NN` (fünf `mittel`, vier
`niedrig`, keiner `hoch`), sechs davon mit lokaler Gegenprobe, dazu der
Abschnitt „Geprüft und nicht bestätigt". Keine `G-`Nummer (`G-006`); Gerd
übernimmt oder weist zurück. **Kein Integrationslauf, nichts auf der NAS
ausgeführt.** Der Teststatus bleibt ROT bis zu Gerds Nachcheck und der
anschließenden CEO-Freigabe.

Davor: Gerds siebzehnter Zielnachcheck (`b3deb78`,
`G-077` bis `G-079`) ist abgearbeitet — alle drei bestätigt und behoben,
Antworten in `REVIEW_ANTWORTEN.md`, Regeln 51 und 52. Dazu die von ihm
verlangte Erweiterung des Probelaufs. **Sein Gate gilt weiter:** `009`/`010`
und das Phase-5-Fenster bleiben ROT bis zu seinem Nachcheck.

## Leseweg für Gerd

Damit dein Guthaben ins Prüfen geht und nicht ins Suchen — in dieser Reihenfolge:

0. **`REVIEW_ANTWORTEN.md`, letzter Abschnitt** — deine fünf Auflagen zum
   Entscheidungsgate, abgearbeitet; davor der Neubau-Vorschlag und deine Rolle darin; im Abschnitt davor deine zehn Befunde
   `G-082` bis `G-091`, je einer bestätigt, behoben, mit Commit und Test;
   die Commits `3345fff..8484c4f` sind der Diff für deinen Nachcheck.
0a. **`GESAMTPRUEFUNG_2026-09-03.md`** — deine Anweisung aus `b7c593b`,
   ausgeführt: neun neue Befunde `GP-2026-09-03-01` bis `-09` mit Beleg,
   Auswirkung und kleinster sicherer Korrektur, Prüfstand `557df50`.
1. **`REVIEW_STELLVERTRETUNG_2026-09-03.md`** — acht Befunde einer Vertretung
   nach deinem Verfahren, Tag `SV-2026-09-03-01` bis `-08`, plus ein Nachcheck.
   Keine `G-`Nummer, keine Zeile in deiner Datei: Du übernimmst, nummerierst um
   oder weist zurück. Auch „stimmt nicht, weil …" ist ein Ergebnis.
2. **`REVIEW_ANTWORTEN.md`**, drei Abschnitte von hinten: „Gerds Gegencheck vom
   2026-09-02" — das sind **deine drei** Befunde, deren Schreibvorgang
   abgelehnt wurde, bevor dein Limit griff; sie warten auf deine Nummer.
   Dann „Sechzehnter Zielnachcheck (Vertretung)" und „Nachcheck der
   Vertretung" mit den Antworten auf die acht `SV-`Punkte.
3. **Von niemandem außer Claude gelesen:**
   `postgres-init/010_bus_function_owner_rollback.sql` samt Abnahmetest und
   `workforce-agent/test_bus_function_owner_rollback.py` (der Rückbau zu 009,
   Antwort auf `SV-…-04`, nie gelaufen, auch nicht im Wegwerf-Container);
   Regel 50 in `AGENTS.md`; die Umbauten an `g045_owner_probe.py` und ihr
   Lauf in `evidence/2026-09-03_g045_owner_probe_run.md`.
4. **Zwei Dinge, die nur du entscheiden kannst:** ob die Schließung von
   `SV-…-04` durch `010` trägt, und ob `009` damit freigabereif ist. Bis dahin
   bleibt beides zu.

Eine Einschränkung, die du kennen musst: Die Vertretung hat am selben Tag
Befunde gestellt und — als Claude Code — teils selbst behoben. Das ist ein
Selbstgespräch mit Protokoll, kein Review. Deshalb steht es hier oben.

## Was seit dem sechzehnten Zielnachcheck (`0238768`) passiert ist

Die Vertretung hat am 2026-09-03 nach Gerds Verfahren geprüft und sechs Befunde
unter `SV-2026-09-03-01` bis `-06` in
`nas-startup/REVIEW_STELLVERTRETUNG_2026-09-03.md` abgelegt. `REVIEW_GERD.md`
blieb unangetastet, es gibt keine erfundene `G-`Nummer (`G-006`).

**Alle sechs selbst nachgemessen, alle sechs bestätigt und behoben.** Antworten
in `REVIEW_ANTWORTEN.md`, Regel 49 in `CLAUDE.md`. Danach ist
`g045_owner_probe.py` gelaufen.

## Der Punkt, den die Vertretung zuerst ansehen sollte

Ihre Freigabe lautete wörtlich: **„Kein OK für `g045_owner_probe.py`, solange
`-01` und `-02` offen sind."**

Die Reihenfolge war: erst `-01` und `-02` behoben, dann eine Freigabe des CEO im
Chat, dann der Lauf. Die genannte Bedingung war damit erfüllt — **aber die
Vertretung hat den Lauf nicht selbst erneut freigegeben.** Das ist die Stelle,
an der dieser Stand nachgesehen und nicht nachgelesen gehört. Ich lege sie
offen, statt sie als gedeckt zu behandeln.

Dieselbe Einschränkung gilt für die Aufhebung der Sperren insgesamt: Der CEO hat
sie am 2026-09-02/03 im Chat erteilt und verlangt, dass alles dokumentiert wird.
Das ist eine echte Freigabe, aber **kein Eintrag im Entscheidungslog** —
geführt als `CEO-CHAT-2026-09-02/PENDING-DEC` (`G-006`).

## Der Probe-Lauf: `RESULT: PASS`, elf Zusicherungen

Nachweis: `evidence/2026-09-03_g045_owner_probe_run.md`. Wegwerf-Container auf
der NAS mit `POSTGRES_USER=workforce_app`, also der Bootstrap-Superuser-Lage der
Produktion (Regel 15). Aufgeräumt mit `docker rm -f`, nie ein `prune` (`G-038`);
nachgesehen, kein Container blieb zurück.

**Vier Annahmen sind dadurch Messungen geworden:**

| bis dahin | jetzt |
|---|---|
| Braucht eine Identity-Spalte Sequenzrechte? Doku schweigt | **Nein** — `bus_events` wurde beschrieben, `009` erteilt keine. Abschnitt 3c beantwortet |
| Feuert der Audit-Trigger unter `workforce_owner`? | **Ja** — genau ein Ereignis, gebunden an Request-Id, Akteur, `MESSAGE`, `INSERT`, `record_key` |
| Ist `42501` die richtige SQLSTATE? | **Ja** — das Abschalten wird mit genau dieser Kennung abgewiesen |
| `G-074`-Gegenprobe auf echter Instanz | **Beide Hälften** — `has_schema_privilege` meldet `t`, direkte Schema-Grants außerhalb `workforce`: `0` |

Dazu das, was `SV-...-02` verlangt hatte: **`bus_send_message` läuft als
`workforce_api` durch.** Die Allowlist reicht auf dem Weg, den die Funktion
wirklich nimmt — der teuerste Ausgang einer Rechtemigration ist eine zu **enge**
Allowlist, und der zeigt sich nur dort.

**Der erste Lauf war rot**, und das gehört in diese Übergabe:
`FAIL: Eventzuwachs '3' statt '1'`. Die Ursache lag bei mir — der Zähler stand
**vor** dem Prepare, der selbst zwei Auditzeilen schreibt. Das Urteil aus
`G-070` wurde also **rot statt still** und nannte Soll und Ist; die gebundene
Abfrage stand im selben Lauf schon richtig auf `1`. Der Zähler steht jetzt
hinter dem Prepare.

**Was der Lauf nicht belegt:** nichts über die Produktion. `009` ist dort nicht
angewendet. Ein Durchlauf mit einer Nachricht, kein Dauerbetrieb; Last,
Nebenläufigkeit und die übrigen elf Funktionen sind nicht gemessen. Und die
Korrekturen an `009` selbst hat außer der Vertretung niemand gelesen.

## Was offen ist

- **`SV-2026-09-03-04` ist geschlossen: der Rückbau existiert.**
  `postgres-init/010_bus_function_owner_rollback.sql`, gegatet über
  `APPLY_MIGRATION_010_FUNCTION_OWNER_ROLLBACK`, mit Abnahmetest daneben.
  Er gibt das Eigentum an den **gelesenen** Schemaeigentümer zurück, nimmt
  `workforce_owner` jedes Recht und **löscht nichts** — kein `DROP OWNED BY`,
  kein `DROP ROLE`. Die Begründung steht in `REVIEW_ANTWORTEN.md` und als
  Regel 50; sie weicht von meiner eigenen ersten Antwort ab.
- **`G-077` bis `G-079` sind behoben, aber von Gerd nicht nachgeprüft.**
  Der Ausschluss beider Gates steht vor dem ersten `psql` in `compose.yaml`;
  `009` prüft vor der ersten Änderung Mitgliedschaften in beide Richtungen
  (`1b`) und den bisherigen Eigentümer der zwölf gegen dieselben zwei Anker,
  die `010` liest (`4d`). Jede Vorbedingung hat einen lokalen Wächter mit
  Gegenprobe.
- **`g045_owner_probe.py` ist umgebaut und in dieser Form nicht gelaufen.**
  Sie führt jetzt `009 → Abnahme 009 → 010 → Abnahme 010 → bus_send_message`
  und davor die zwei Negativfälle zu `G-078`/`G-079`, an den benannten
  Abbruch gebunden (`abbruch_urteil()`, `G-014`). 21 Zusicherungen, davon
  zehn neu und **ungemessen**. Der Lauf braucht die gesonderte CEO-Freigabe,
  die Gerd genannt hat — und die Berechtigungsprüfung des Werkzeugs, die den
  ersten Probe-Versuch abwies, könnte ihn erneut abweisen.
- **Freigabereif ist `009` trotzdem nicht — der Grund heißt jetzt anders.**
  Vorher fehlte der Rückbau, jetzt fehlt das Review: `010` ist auf **keiner**
  Instanz gelaufen, auch nicht im Wegwerf-Container, und beide Dateien hat
  außer der Vertretung niemand gelesen. Geprüft ist die Struktur
  (`test_sql_structure.py`) und die Übereinstimmung mit `009`
  (`test_bus_function_owner_rollback.py`).
- **Migration `009` ist gegatet und nicht angewendet.** Produktion: Migrationen
  `001`–`003` und `005`–`007`, Kanal `DISABLED`, 0 aktive Credentials,
  `workforce_owner` existiert nicht.
- **Phase 5 bleibt ROT.** Kein Kanal, kein Credential, kein Modellaufruf, kein
  Build auf der NAS. `G-030` — die Kette ist nie durchgelaufen — bleibt offen.
- **Gerds drei Gegencheck-Befunde vom 2026-09-02 haben weiterhin keine Nummer.**
  Sein Schreibvorgang in `REVIEW_GERD.md` (`+130` Zeilen) wurde abgelehnt, bevor
  sein Limit griff. Sie stehen vollständig in `REVIEW_ANTWORTEN.md` und im
  Tagesbericht; behoben sind sie (Regeln 47 und 48, plus die Verschärfung von
  `G-014`). Gerd kann sie ab dem 07.09. übernehmen oder zurückweisen.

## Stand

- **Deployt ist `0dc2ad0`** — über `deploy_to_nas.sh` (seit `G-080` ohne
  Remote-Löschen, seit `G-091` mit festem Ziel) und die enge
  Berechtigungsregel dafür (`.claude/settings.local.json`, nur dieser eine
  Befehlsweg). Auf der NAS gemessen für `0dc2ad0` — `dirty=no`, 242 Dateien,
  0 fehlend, 0 abweichend, 0 unerwartet, `RESULT: PASS`; `check_unmanaged`
  64 Einträge, `PASS`. Damit liegen die Korrekturen zu `G-082` bis `G-091`,
  die neuen Wächter und die Antworten dort, wo Gerd liest. Das umgebaute
  `nas_status.sh` ist dort **nicht** gelaufen — sein erster Lauf auf der NAS
  ist Gerds Nachcheck vorbehalten. `compose.yaml` weicht bis dahin vom benannten
  Produktionsstand ab und steht mit Begründung in der Ausnahmeliste von
  `test_production_state_drift.py`.
- **795 lokale Tests `PASS`** (698 / 15 / 55 / 27), auf `python3` 3.9.6 des
  Projektrechners.
- **Nicht gelaufen und nicht behauptet:** die API-Suite (braucht den Container),
  jedes SQL gegen einen echten PostgreSQL-Parser außerhalb des Probe-Containers.

`workforce-agent/test_sql_structure.py` schließt fünf SQL-Fehlerklassen aus
(Dollar-Quote-Balance, deklarierte gegen benutzte Variablen,
`RAISE`-Platzhalter gegen Argumente, Transaktionsklammer) und **ersetzt keinen
Parser** — Katalogspalten, Typen und Semantik sieht er nicht. Vier Gegenproben
gehören dazu.

## Vorschlag für den nächsten Schritt

Ein Lauf von `009` **und** `010` hintereinander im Wegwerf-Container, als
Erweiterung von `g045_owner_probe.py`: erst der Eigentumswechsel, dann ein
`bus_send_message` als `workforce_api`, dann der Rückbau, dann derselbe Aufruf
noch einmal. Das ist die Aussage, auf die es im Fenster ankommt — **der Bus
läuft vor und nach dem Rückbau** —, und sie ist heute nirgends gemessen. Der
Lauf berührt die Produktion nicht.

Ich habe ihn **nicht** gemacht: Ein Probelauf braucht eine Freigabe im Chat,
und die vom 2026-09-02/03 galt der Probe in ihrer damaligen Form.

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

Entscheidungen bis `DEC-029`, `ENG-008` vorhanden, Projektanweisung v1.2.
`DEC-028`/`DEC-029` betreffen Thorstens lokalen Opportunity-Filter und geben
keine Workforce-, NAS- oder Modellaktivierung frei. **Das ist der gültige
Stand.**

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

Am Deploy ändert das nichts: Am Code wird im Repo gearbeitet, auf
`/volume1/docker/Startup/` wird deployt. Ausnahme sind die beiden
Review-Dateien: Sie werden zusätzlich auf der NAS gespiegelt.

**Seit dem 2026-09-03 als Skript:** `sh nas-startup/deploy_to_nas.sh` — dieselben
drei Schritte, fail-closed, versioniert. Der Block darunter dokumentiert, was
das Skript tut.

Deploy (`rsync` und `scp` funktionieren auf dieser DSM nicht). **Versionierte Dateien, nie ganze Verzeichnisse** — ein verzeichnisweites Archiv nimmt Secrets und Laufzeitdateien mit (Befund `G-020`). Die Dateiliste geht über `-T` in `tar`, nicht über `$(…)`: **zsh zerlegt eine unquotierte Variable nicht in Wörter**, und die Pfade kämen als ein einziges Argument an.

```bash
cd "/Users/Tobi/Documents/Codex/workorce claude/nas-startup"
REQUIRE_CLEAN=1 DEPLOY_FILE_LIST_OUT=/tmp/liste.txt sh deploy_manifest.sh <pfade>
COPYFILE_DISABLE=1 tar czf /tmp/archiv.tgz -T /tmp/liste.txt
ssh synology "cd /volume1/docker/Startup && tar xzf -" < /tmp/archiv.tgz
ssh synology "cd /volume1/docker/Startup && grep -qx 'dirty=no' DEPLOY_MANIFEST.txt && sh verify_manifest.sh && sh check_unmanaged.sh"
```

Kein `find … -delete` auf der NAS mehr und keine Pipeline in `ssh` (`G-080`):
Das Archiv ist fertig, bevor `ssh` startet, und ein Tar-Fehler bleibt ein
Tar-Fehler. Was eine Umbenennung auf der NAS zurücklässt, meldet
`verify_manifest.sh` als `UNERWARTET`; aufgeräumt wird das sichtbar und von
Hand, nie als Nebenwirkung des Deploys.

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
| A1 — getrennte Agenten-Identität | `AGENT-ENG-001` wurde beim echten Kettenlauf als aktives Projektmitglied belegt; vor jedem neuen Fenster erneut per Preflight messen |
| A2 Herkunftsvermerk | behoben |
| A3 Laufzeitgrenze | behoben |
| A5 Rückzug bei Busausfall | behoben |
| F8 Ratenbegrenzung / Kostenlimit | lokal behoben: Aufruf, konservative Ein-/Ausgabetoken und Kosten werden vor dem Provider atomar reserviert; fehlende Usage behält die Reserve |
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
| `G-053` | **der Rückweg der Kette bestätigte nie auf dem Bus** | behoben, Regel 27 |
| `G-054` | zwei falsche Zusicherungen im Agenten-README (`G-029`, `G-036`) | behoben, Regel 28 |
| `G-055` | vier erfundene Dienstnamen im **eigenen** Phase-5-Runbook | behoben, Regel 29 |
| `G-056` | der `G-053`-Fix hatte selbst einen Fehlerpfad | behoben, Regel 30 |
| `G-057` | zwei Felder der Modell-Allowlist wirkten nicht | behoben, Regel 31 |
| `G-058` | drei Sätze im Phase-5-Entwurf lösten ihr Kommando nicht ein | behoben, Regel 9 geschärft |
| `G-059` | zwei Bindungsfehler im eigenen Auditskript | behoben, Auditregel geschärft |

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

**Sechs der Befunde sind an meiner eigenen Arbeit von heute entstanden**,
gefunden beim Nachlesen statt beim Schreiben. `G-055`: Mein erster
Runbook-Entwurf nannte vier Dienste, die es nicht gibt, und eine Aufrufform,
die das Fenster im dritten Schritt getötet hätte — der Wächter sah es nicht,
weil `-f <datei>` **vor** dem Unterbefehl steht und sein Muster deshalb
ausgerechnet jeden Aufruf einer Paketdatei verfehlte. `G-056`: Mein
`G-053`-Fix ließ eine Nachricht über den Fehlerpfad in genau dem Zustand
zurück, gegen den er gebaut wurde. `G-057`: Zwei Felder der Modell-Allowlist waren
deklariert und wurden nie gelesen — Leitplanke 7 in ihrer unauffälligsten
Form, weil ein Konfigurationsfeld verbindlicher wirkt als ein Kommentar. Alle
drei sind behoben und haben eine Regel hinterlassen; ich nenne sie hier, weil
sie zeigen, wo du bei mir suchen solltest — und weil alle beim **Nachlesen**
gefunden wurden, nicht beim Schreiben. Der lehrreichste ist `G-059`: Mein
Auditskript band den letzten Schritt an einen fremden Datensatz, und das fiel
nur deshalb nicht auf, weil ein **zweiter** Fehler denselben Schritt ohnehin
als fehlend meldete. Mein „an der Produktion validiert" war damit schwächer,
als ich es aufgeschrieben hatte.

**Das nächste Fenster ist abarbeitbar: `PHASE5_RUNBOOK.md`.** Contract-Test,
Core-Roundtrip, beide Auditrekonstruktionen, Rückbau — von oben nach unten,
jeder Schritt mit Abbruchkriterium. Es öffnet **kein** Gate und tauscht **kein**
Image; es öffnet einen Kanal, gibt drei kurzlebige Zugänge aus, fährt Nachweise
und räumt auf. Blocker ist eine CEO-Freigabe, nicht ein offener Befund — dein
technischer Zielcheck galt dem Phase-4-Fenster. Wenn du eine Sache mit dem
Rotstift lesen willst, dann diese: Meine letzten drei Runbook-Runden haben
`G-042`, `G-043` und `G-044` produziert.

**Wenn du nur eines liest, dann `G-051`.** Jedes Laufzeitpaket zeigte auf
`…192-168-68-78…`, die NAS liegt seit einem Neustart am 2026-09-02 auf `.81`,
und dort antwortete `Connection refused`. Jedes verbleibende Fenster wäre an
der ersten Verbindung gestorben — nach dem Öffnen des Kanals und dem Ausgeben
echter Zugangsdaten. Der Name bildet die LAN-Adresse ab, ist also eine
Ableitung wie ein Containername (`G-042`), und keiner der drei vorhandenen
Wächter konnte die Frage stellen: die Suiten laufen ohne Netz, das Manifest
vergleicht Prüfsummen, `nas_status.sh` fragt über `localhost`.

**`G-053` ist an der Produktion belegt, nicht nur am Code.** `chain_audit.sql`
gegen den echten `CHAIN PASS`-Lauf vom 2026-09-01 gefahren: vier von fünf
Etappen belegt, Reihenfolge korrekt, fehlend genau
`connector_acknowledges_the_reply` — und zwei Antworten des Agenten stehen
seit dem 2026-09-01 auf `DELIVERED`. Dein `CHAIN PASS` ist deshalb **nicht**
falsch; die Benachrichtigungen sind bei Telegram angekommen. Nicht
rekonstruierbar war es, und genau das verlangt Phase 5, Punkt 4. Die beiden
liegengebliebenen Nachrichten gehören über die Regeln des Busses geschlossen
(Leitplanke 3) und damit in dasselbe Fenster wie der nächste Kettenlauf.

**`G-030` ist präzisiert:** Eine Telegram→Bus→Agent→Bus→Telegram-Kette mit
Echo lief am 2026-09-01 real. Nach dem daraus entstandenen `G-053`-Fix ist die
vollständige Kette noch nicht wiederholt; der integrierte Worker-Core ist auf
der NAS ebenfalls noch nicht gelaufen. Ein echter Modellaufruf fand nie statt
und bleibt separat gesperrt.

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

### Verbindliche Phasenabgrenzung ab jetzt

Die frühere Roadmapdarstellung ist historisch: Phase 3 (NAS-Preflight) und
Phase 4 (Foundation-Update auf API v9, Migrationen `005`–`007`) sind
ausgeführt. Der nächste Ablauf ist:

1. **Phase 5 – lokale Korrekturen und isolierte NAS-Abnahme:** sauberer und
   reproduzierbarer Deploy, Contract-Test, Core-Roundtrip, getrenntes
   Telegram-Kettenfenster mit Echo, beide
   Auditrekonstruktionen und vollständiger Rückbau. Ausführbarer Ablauf:
   `PHASE5_RUNBOOK.md`. Das Schließen von `G-061`–`G-067` ist lokal; der
   NAS-Lauf bleibt bis zu einer gesonderten CEO-Freigabe ausstehend.
2. **Phase 6 – integrierter Worker-Core mit Echo:** echte Runtime,
   Wiederaufsetzen, verlorener lokaler Zustand, Bus-Idempotenz und Audit gegen
   die NAS belegen, weiterhin ohne Modellkosten.
3. **Phase 7 – kontrollierter Modellpilot:** genau ein Modell, eine
   Aufgabenklasse, kleine Daten- und Kostengrenze. Erst nach eigener
   CEO-Entscheidung zu Provider/Kosten, `AGENT_DATA_POLICY`, Dateninhalt und
   genauem Testfenster. Kein stiller Übergang aus Phase 5.
   Danach Kommunikationswege, Datenkopien, Aufbewahrung, Berichte,
   Modellzuordnung und Kosten anhand der gemessenen Daten verschlanken; keine
   neue Plattform vor diesem Nachweis.
4. **Phase 8 – formeller Status und Betriebsempfehlung:** Evidenz,
   Restbefunde, Rechte, Kosten und Rückfall gemeinsam bewerten; erst dann ein
   Dauerbetriebs-Gate formulieren.

Jede NAS-Ausführung, externe Modellnutzung, Kosten- oder Rechteänderung braucht
ihre konkrete Freigabe. Lokale Dokumentations- und Testkorrekturen erteilen
keine solche Freigabe.

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

- Für Phase 5 das konkrete isolierte NAS-Fenster erst nach sauberem Commit und technischem Zielnachcheck freigeben oder zurückstellen
- Für Phase 6 separat Provider, maximales Budget, Datengrenze und Testinhalt entscheiden; bis dahin kein echter Modellaufruf
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
