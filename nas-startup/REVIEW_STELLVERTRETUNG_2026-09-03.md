# Sechzehnter Zielnachcheck – in Vertretung, Stand `0238768`

**Diese Datei ist nicht `REVIEW_GERD.md`.** Gerd ist bis zum 2026-09-07 nicht
verfügbar; geprüft hat hier eine Vertretung nach seinem Verfahren und in seinem
Format. `REVIEW_GERD.md` bleibt unangetastet — es ist seine Datei.

**Kennzeichnung der Befunde.** Sie tragen keine `G-`Nummer: Eine Befundnummer
wird nicht erfunden (`G-006`), und die Nummernfolge gehört dem Prüfer. Statt
dessen trägt jeder Punkt das Präfix

```
SV-2026-09-03-NN        SV = Stellvertretung, danach Prüfdatum und laufende Nummer
```

Gerd kann jeden Punkt beim nächsten Durchgang übernehmen, eine `G-`Nummer
vergeben oder ihn zurückweisen; die Antworten stehen bis dahin unter dem
`SV-`Tag in `REVIEW_ANTWORTEN.md`. Ein zurückgewiesener Befund ist ebenfalls ein
Ergebnis.

## Geprüfter Stand und Betriebsgrenze

Geprüft wurden die Commits `ea5ae2a..0238768` — Claudes Korrektur von `G-074`
bis `G-076`, die drei Punkte aus Gerds Gegencheck ohne Nummer und der neue
`test_sql_structure.py`.

**Auf der NAS wurde nichts ausgeführt und nichts gelesen.** Kein Container,
keine Migration, kein `ssh`. Alle Messungen unten laufen auf dem Mac gegen das
Repo. Wo eine Aussage nur auf der NAS entschieden werden kann, steht das dabei.

Lokal nachgefahren zu Beginn: `565 + 15 + 44 + 27 = 651` Tests **PASS**,
Spiegeldateien byteidentisch (`CLAUDE.md`/`AGENTS.md`/`nas-startup/AGENTS.md`,
`HANDOVER.md`/`nas-startup/HANDOVER.md`).

**Während dieses Durchgangs hat eine zweite Sitzung im selben Arbeitsbaum
geschrieben** — `workforce-agent/test_guard_counterprobes.py` (neu, `+7` Tests)
und je eine Zeile in `CLAUDE.md`, `AGENTS.md` und `nas-startup/AGENTS.md` zur
neuen Regel 47. Diese Arbeit war beim Start nicht da, ist nicht committet und
ist **nicht Gegenstand dieses Reviews**; geprüft wurde `ea5ae2a..0238768`. Sie
ist hier nur deshalb vermerkt, weil sie die Testzahl unter der Prüfung verändert
hat: am Ende `572 + 15 + 44 + 27`. `HANDOVER.md` sagte zu diesem Zeitpunkt
„Aktive Arbeit: keine" — die Anmeldepflicht aus Regel 2 des Projektkontexts hat
also nicht gegriffen.

## Ergebnis

- **`G-074` geschlossen.** Der Abnahmetest fragt nicht mehr nach dem effektiven
  Recht, sondern liest den direkten ACL-Eintrag über `aclexplode`; der
  Rechtevergleich trägt das Schema im Schlüssel.
- **`G-075` geschlossen.** Migration, Abnahmetest und Wächter pinnen dieselben
  zwölf vollständigen Identitätssignaturen, aufgelöst über `to_regprocedure()`,
  und handeln danach über die OID. Der Gegenfall — ein Parametertyp bei gleicher
  Stelligkeit — ist als Test hinterlegt und schlägt an.
- **`G-076` geschlossen.** `ssh()` gibt Exitcode und Ausgabe; `lauf_ergebnis()`
  verlangt Exitcode 0 **und** den Schlussmarker.
- **Die drei Gegencheck-Punkte sind sachlich behoben** — SQLSTATE-Bindung im
  Trigger-Negativtest, zwei getrennte Abfragen in der PUBLIC-Selbstprüfung,
  `REVOKE ALL ON SCHEMA workforce` vor dem `GRANT USAGE`.

**Aber `g045_owner_probe.py` ist nicht freizugeben.** Der zentrale Schreibtest
der Probe kann nicht gelingen; drei weitere Zusicherungen hängen an ihm und
fallen mit. Dazu misst die Probe die Frage nicht, die in ihrer eigenen
Kopfzeile steht. Details unter `SV-2026-09-03-01` und `-02`.

---

## `SV-2026-09-03-01` – Die Probe schreibt auf eine Tabelle, auf die 009 ihr kein UPDATE gibt

**Schwere:** hoch — der zentrale Nachweis der Datei kann nicht bestehen, und die
naheliegende Reparatur weitet die Allowlist genau dort auf, wo `G-071` sie
verengt hat

**Dateien:** `g045_owner_probe.py`:303-333,
`postgres-init/009_bus_function_owner.sql`:144-171,
`workforce-agent/test_owner_probe_verdict.py`:59-62

**Beobachtung.** Der Schreibversuch, mit dem die Probe misst, ob der
Audit-Trigger unter dem neuen Eigentümer feuert, lautet:

```
SET ROLE workforce_owner; ... UPDATE workforce.bus_channels SET source_ref = 'PROBE-G045' ...
```

Migration 009 erteilt `workforce_owner` auf `bus_channels` ausschließlich
`SELECT`. Schreibrechte hat die Rolle auf `bus_messages`, `bus_tasks`,
`bus_handoffs` (`SELECT, INSERT, UPDATE`) sowie `bus_events` und `bus_denials`
(`INSERT`). Gegenprobe mit dem projekteigenen Wächtermodul, damit die Aussage
nicht an meinem Lesen hängt:

```
workforce_owner darf schreiben auf: ['bus_denials', 'bus_events', 'bus_handoffs', 'bus_messages', 'bus_tasks']
die Probe schreibt auf:             ['bus_channels']
nicht abgedeckt:                    ['bus_channels']
Rechte auf dem Ziel:                {'bus_channels': ['SELECT']}
```

Die Ursache ist eindeutig das fehlende Recht, nicht ein Guard und nicht ein
fehlender Datensatz: `bus_guard_channel_update` lässt `source_ref` ausdrücklich
zu (unveränderlich sind nur `project_id` und `created_at`), und `002` legt die
Zeile `project_id = 'START-UP'` an. Nachgesehen, bevor ich das Recht
beschuldigt habe.

**Warum problematisch.** `UPDATE` scheitert mit `42501`, der Schritt meldet
nicht `ok`, und mit ihm fallen drei weitere Zeilen der `ERWARTET`-Tabelle:
`Eventzuwachs` bliebe `0`, das an Request-Id, Akteur, Datensatztyp und Operation
gebundene Audit-Ereignis bliebe `0`, und die offene Frage aus `009` Abschnitt 3c
— ob die Allowlist ohne Sequenzrechte reicht — bliebe unbeantwortet, weil der
Schreibvorgang, der sie beantworten sollte, nie stattfindet. Die Probe endet mit
vier `FAIL`-Zeilen.

Das Urteil aus `G-070` funktioniert also — es wird rot statt still, und das ist
gut. Teuer ist die zweite Ordnung: Der Fehlschlag liest sich als „die Allowlist
ist zu eng", und die schnellste Reparatur im Fenster wäre ein `UPDATE` auf
`bus_channels` in der Migration. Damit hätte `workforce_owner` ein Schreibrecht,
das keine der zwölf Funktionen braucht — genau die Verbreiterung, gegen die
`G-071` die Allowlist gebaut hat. `test_bus_function_owner.py` würde das
bemerken; die zweite naheliegende Reparatur wäre dann, diesen Test zu lockern.

Bemerkenswert ist, dass die Zeichenkette
`"ERROR: permission denied for table bus_channels"` bereits als Negativfixture
in `test_owner_probe_verdict.py` steht. Der Fall war gedacht — als Hypothese,
nicht als der sichere Ausgang des Laufs. Kein lokaler Test bindet das
Schreibziel der Probe an die Allowlist der Migration.

**Kleinste sichere Korrektur.**

- Das Schreibziel aus der **Schreib**-Allowlist wählen, nicht aus der
  Leseliste. `bus_messages`, `bus_tasks` und `bus_handoffs` tragen denselben
  `bus_record_change`-Trigger; der erwartete `record_type` wandert entsprechend
  von `CHANNEL` auf `MESSAGE`/`TASK`/`HANDOFF` mit (`002`, `bus_record_change`,
  `CASE TG_TABLE_NAME`).
- Den Guard des gewählten Ziels vorher lesen, nicht annehmen — die
  Übergangsregeln stehen in `bus_guard_*`, und ein abgelehnter Übergang wäre
  derselbe Fehlschlag mit einer anderen Ursache.
- Einen lokalen Test ergänzen, der das Schreibziel der Probe aus ihrer Quelle
  auflöst und gegen die `INSERT`/`UPDATE`-Menge aus 009 hält, mit Gegenprobe:
  Ein Ziel, das nur `SELECT` hat, muss ihn rot machen. Der Zehnzeiler oben ist
  dafür schon der Beweis, dass es billig geht.

## `SV-2026-09-03-02` – Die Probe ruft keine der zwölf Funktionen auf, obwohl ihre Kopfzeile genau das fragt

**Schwere:** hoch — die Frage, deren Antwort das Fenster entscheidet, steht
nicht in der `ERWARTET`-Tabelle

**Dateien:** `g045_owner_probe.py`:2, 109-128, 259-369

**Beobachtung.** Die erste Zeile der Datei lautet „laufen die Funktionen danach
ohne Superuser weiter?". Die zehn Schlüssel in `ERWARTET` messen: den
Migrationslauf, zwei Katalogzählungen, einen rohen `UPDATE` unter `SET ROLE`,
den Eventzuwachs, das gebundene Auditereignis, den Trigger-Negativtest, zwei
Schemarechte-Zahlen und den Abnahmetest. **Kein Schlüssel misst einen Aufruf
einer der zwölf Funktionen.** Der Abnahmetest fragt `has_function_privilege` —
das ist die Rechtezeile im Katalog, nicht ein Lauf.

**Warum problematisch.** Der teuerste Ausgang von 009 ist eine zu **enge**
Allowlist: Der Bus steht, und zwar erst beim ersten echten Aufruf im Fenster.
Genau das sagt die Migration in ihrem eigenen Kommentar zu `bus_events`. Was die
Probe stattdessen prüft, ist ein Schreibvorgang, den keine der zwölf Funktionen
so ausführt. Selbst nach der Korrektur aus `SV-2026-09-03-01` bliebe die Aussage
„eine Rolle darf auf eine Tabelle schreiben" — nicht „`bus_send_message` läuft".

Damit gilt `G-046` in seiner ursprünglichen Form: Ein Artefakt begründet keine
Entscheidung, wenn daneben nicht steht, was es nicht geprüft hat. Die Datei
behauptet im Kopf mehr, als ihre Bewertungstabelle einlöst.

**Kleinste sichere Korrektur.** Eine von beidem, nicht beides halb:

- Entweder **einen** vollständigen Durchlauf messen — im Wegwerf-Container
  Kanal auf `TESTING` setzen, ein Credential anlegen, `bus_send_message` als
  `workforce_api` aufrufen, Ergebnis und Auditzeile binden — und ihn als
  eigenen Schlüssel in `ERWARTET` aufnehmen. Die Maschinerie dafür existiert in
  `bus-realtest`; sie muss nicht neu erfunden werden.
- Oder die Kopfzeile auf das zurücknehmen, was gemessen wird, und ausdrücklich
  hinschreiben, dass ein Funktionsaufruf unter dem neuen Eigentümer **nicht**
  belegt ist. Dann ist die Freigabe von 009 eine Entscheidung mit benannter
  Lücke statt einer mit unbemerkter.

Der erste Weg ist der bessere, weil er `SV-2026-09-03-01` mit erledigt: Ein
echter Aufruf schreibt über die Funktion in `bus_messages`, löst denselben
Trigger aus und beantwortet die Sequenzfrage aus 3c im selben Zug.

## `SV-2026-09-03-03` – Die Selbstprüfung des Abnahmetests hängt an einer Vorbedingung, die 009 nicht herstellt

**Schwere:** mittel — der Abnahmetest kann in einer korrekten Datenbank rot
werden, und seine Fehlermeldung schickt den Leser in die falsche Richtung

**Datei:** `postgres-tests/009_bus_function_owner_acceptance.sql`, Abschnitt 6,
Teil (a); Gegenstück in Abschnitt 4b

**Beobachtung.** Abschnitt 4b behandelt einen leeren ACL-Eintrag ausdrücklich
als zulässig: „Ist `nspacl` NULL, gilt die Voreinstellung und es gibt
definitionsgemäß keinen direkten Eintrag." Abschnitt 6(a) verlangt vom selben
Katalogfeld das Gegenteil — er bricht mit
`keine PUBLIC-Vorgabe auf public - dann prueft Abschnitt 4b nichts` ab, wenn
`aclexplode(n.nspacl)` für `public` keine Zeile mit `grantee = 0` liefert.

Zwei Wege führen dorthin, und beide liegen außerhalb dessen, was 009 zusichert.
Erstens: Ob ein `REVOKE`, das nichts ändert, einen `NULL`-ACL überhaupt
materialisiert, ist eine Implementierungsfrage von PostgreSQL — sie ist hier
nicht gemessen, und Regel 4 sagt, dass sie dann auch nicht angenommen wird.
Zweitens, und unabhängig davon: Sobald jemand `USAGE ON SCHEMA public FROM
PUBLIC` entzieht — eine Härtung, die dieses Projekt an anderer Stelle selbst
vornehmen würde —, ist 6(a) rot, obwohl die Zusicherung von 009 („kein direkter
Grant an `workforce_owner`") unverändert gilt.

**Warum problematisch.** Es ist die Spiegelform von `G-074`: Dort fragte der
Test nach dem effektiven Recht und band sich damit an eine Voreinstellung, die
er nicht besitzt. Hier bindet sich die Selbstprüfung an dieselbe Voreinstellung,
nur mit umgekehrtem Vorzeichen. Der Schaden ist derselbe — ein Wächter, der aus
einem Grund rot wird, den sein Text falsch benennt, wird beim nächsten Mal
übergangen (`G-069`).

**Kleinste sichere Korrektur.**

- Die Aussage, die 6(a) belegen soll, ist „der Katalogblick **kann** eine
  PUBLIC-Zeile sehen", nicht „`public` trägt sie". Also über `pg_namespace`
  suchen, statt `nspname = 'public'` festzuschreiben, und erst dann abbrechen,
  wenn es nirgends eine gibt.
- Findet sich nirgends eine PUBLIC-Zeile, gehört das als benannte Aussage in die
  Ausgabe („Voraussetzung entfallen"), nicht als Abbruch, der eine bestandene
  Migration blockiert.
- Der Widerspruch zwischen 4b und 6(a) gehört in jedem Fall aufgelöst: Beide
  reden über dasselbe Katalogfeld und dürfen nicht Gegenteiliges verlangen.

## `SV-2026-09-03-04` – Migration 009 verspricht einen Rückbau, den es nicht gibt

**Schwere:** mittel — der Weg zurück müsste im Fenster improvisiert werden, in
dem Moment, in dem der Bus steht

**Dateien:** `postgres-init/009_bus_function_owner.sql`:52; kein Gegenstück im
Repo

**Beobachtung.** Der Kopf der Migration schließt mit: „Ein Fehlgriff bei den
Rechten legt den Bus still - deshalb der Abnahmetest daneben und der **Rückbau
als Teil derselben Entscheidung**." Eine Suche über `*.md`, `*.sh`, `*.sql`,
`*.yaml` und `*.txt` findet `009_bus_function_owner` beziehungsweise
`workforce_owner` nur in `AGENTS.md`, `HANDOVER.md`, den beiden Reviewdateien,
`compose.yaml` (das Gate) und `DEPLOY_MANIFEST.txt`. Es gibt **keine**
Rückbaumigration, **keinen** Runbook-Abschnitt und **keinen** Nachweis dazu;
`PHASE5_RUNBOOK.md` erwähnt 009 mit keinem Wort.

**Warum problematisch.** Das ist Leitplanke 7 an einer Stelle, an der sie
operativ wird: Ein Kommentar behauptet eine Absicherung, die es nicht gibt, und
er tut es in dem Absatz, den man liest, während man über die Freigabe
entscheidet. Der Rückbau ist hier auch nicht trivial — er ist ein
Eigentumswechsel für zwölf Funktionen und danach die Frage, was mit Rolle und
Rechten geschieht; `DROP ROLE` scheitert an jeder erteilten Berechtigung, was
dieses Projekt in `G-043` schon einmal bezahlt hat. Genau so etwas will man
nicht um 23 Uhr entwerfen, während die API 503 liefert.

**Kleinste sichere Korrektur.**

- Den Rückbau als das schreiben, was er nach den Regeln dieses Projekts ist:
  eine **additive** Migration `010`, die das Eigentum zurückgibt, mit `DROP
  OWNED BY` vor jedem Versuch, die Rolle zu entfernen — oder mit der bewussten
  Entscheidung, die Rolle stehen zu lassen.
- Oder den Satz streichen und stattdessen hinschreiben, dass es keinen
  vorbereiteten Rückbau gibt. Beides ist vertretbar; die jetzige Fassung ist es
  nicht.
- 009 braucht ohnehin ein benanntes Fenster mit Vorher-, Nachher- und
  Abbruchschritt. Solange das fehlt, ist die Migration nicht freigabereif —
  unabhängig davon, wie gut ihr SQL inzwischen ist.

## `SV-2026-09-03-05` – `production_state.txt` pinnt `compose.yaml` auf einen überholten Commit

**Schwere:** mittel — die einzige Prüfung, die den laufenden Stand an einen
benannten Commit bindet, meldet ab jetzt `FAIL`

**Dateien:** `production_state.txt`:`PRODUCTION_COMMIT`/`FILE=compose.yaml`,
`verify_production_state.sh`:20-58

**Beobachtung.** `production_state.txt` nennt `PRODUCTION_COMMIT=672e0a7` und
listet `compose.yaml` unter den Dateien, die den laufenden Stand ausmachen.
`compose.yaml` hat sich seit `672e0a7` geändert — Commit `ab0f719` hat den
`APPLY_MIGRATION_009_FUNCTION_OWNER`-Block ergänzt (+17 Zeilen), und dieser
Stand ist mit dem Deploy von `21c40a7` auf der NAS. Am Mac gemessen:

```
git diff --stat 672e0a7..HEAD -- <alle FILE=-Einträge>   ->  nur compose.yaml, +17
```

`verify_production_state.sh` vergleicht die NAS-Datei gegen den Blob aus
`PRODUCTION_COMMIT`. Für `compose.yaml` muss dieser Vergleich abweichen; das
Skript endet dann mit `RESULT: FAIL - der laufende Stand ist nicht 672e0a7`.
**Auf der NAS nicht nachgemessen** — dort wurde in diesem Durchgang nichts
ausgeführt. Die Abweichung folgt aus dem Repo und dem dokumentierten Deploy.

**Warum problematisch.** `nas_status.sh` ruft dieses Skript nicht auf, also ist
das Preflight-Gate nicht betroffen — der Fehlschlag ist dafür umso stiller: Er
tritt erst auf, wenn jemand von Hand nachsieht, und das tut man am ehesten
unmittelbar vor einem Fenster. Dort steht dann eine rote Zeile, die aus einem
harmlosen Grund rot ist, und die Entscheidung „harmlos oder echt" fällt unter
Zeitdruck. Eine echte spätere Abweichung in `compose.yaml` verstecken sich
hinter derselben roten Zeile.

Der Zustand entsteht sauber aus den eigenen Regeln: Das Gate gehört in die
versionierte Datei, sein Wert bleibt `"false"`, am laufenden System ändert sich
nichts — aber `production_state.txt` kennt für „Datei deployt, System
unverändert" keinen Platz.

**Kleinste sichere Korrektur.**

- `PRODUCTION_COMMIT` auf den deployten Commit ziehen und mit einer datierten
  Notiz versehen, warum sich am laufenden System nichts geändert hat. Die Datei
  führt solche Notizen bereits; das ist ihre Bauform.
- Dazu ein lokaler Test, der jede `FILE=`-Zeile zwischen `PRODUCTION_COMMIT` und
  `HEAD` byteweise vergleicht und eine Abweichung entweder als benannte
  Ausnahme verlangt oder rot wird. Das läuft **auf dem Mac**, ohne NAS, und
  hätte den Tag der Änderung angeschlagen statt Wochen später.

## `SV-2026-09-03-06` – Der Kopf des `G-075`-Wächters beschreibt den Stand vor `G-075`

**Schwere:** niedrig — aber wer Code und Dokument angleicht, baut den Befund
wieder ein

**Datei:** `workforce-agent/test_bus_function_owner.py`:1-27

**Beobachtung.** Der Moduldocstring sagt: „Die Migration pinnt jetzt Namen und
Stelligkeit und bricht ab, wenn der Katalog etwas anderes enthält", und begründet
das im Absatz darunter ausdrücklich: „Warum Name und Stelligkeit und nicht der
Typ: … Eine abgeschriebene Typliste wäre genau die Gedächtnisleistung, die
`G-044` verboten hat." Beides ist seit der `G-075`-Korrektur falsch: Migration,
Abnahmetest und dieser Wächter pinnen zwölf **vollständige Identitätssignaturen
mit Typen**. Die Docstrings von `signatur()` und `security_definer()` weiter
unten sagen das Richtige — der Kopf widerspricht dem Rumpf derselben Datei.

**Warum problematisch.** Es ist `G-054` in seiner unauffälligen Form: eine
sicherheitsrelevante Aussage im Präsens, die das Gegenteil des Codes behauptet,
in der Datei, die man liest, bevor man an den Pins arbeitet. Der Absatz
argumentiert dabei nicht neutral, sondern **gegen** die heutige Lösung und
beruft sich dafür auf eine Regel. Das ist die Sorte Text, nach der jemand den
Code „zurückrepariert".

**Kleinste sichere Korrektur.** Den Kopf auf den heutigen Stand ziehen und die
Auflösung, die `signatur()` schon nennt, dort hinschreiben: Die Typen kommen aus
der Quelle und werden von `to_regprocedure()` normalisiert — abgeschrieben wird
nichts, `G-044` bleibt eingehalten.

---

## Nachgesehen und **nicht** bestätigt

Damit der nächste Durchgang diese Wege nicht noch einmal geht:

- **Die Allowlist in 009 ist nicht zu eng.** Unabhängig aus `002`, `003` und
  `005` abgeleitet: Die zwölf Funktionen berühren genau
  `active_project_members`, `bus_channels`, `bus_credentials`, `bus_denials`,
  `bus_handoffs`, `bus_member_capabilities`, `bus_messages`,
  `bus_route_allowlist`, `bus_tasks`, `employee_project_memberships`,
  `employees`, `projects` — plus `bus_events` über den Trigger
  `bus_record_change`, der nicht `SECURITY DEFINER` ist und deshalb als
  `workforce_owner` läuft. Die Migration deckt alle ab, `DELETE` erteilt sie
  nirgends. Statisch geprüft; ein Lauf bleibt `SV-2026-09-03-02`.
- **Die Lückenliste der Abnahmetests ist intakt.** Mein erster Verdacht war,
  `test_the_gap_is_exactly_what_is_written_down` habe beim `009`-Umbau seine
  Zusicherungen verloren. Nachgesehen: Beide `assertEqual` stehen unverändert
  seit `7bfc90f` in `HEAD`. Der Verdacht kam von einem eigenen abgeschnittenen
  Ausschnitt — genau der Fehler, den dieses Projekt „nachsehen, nicht
  nachlesen" nennt.
- **Der ROLLBACK-Vertrag der Abnahmetests ist gedeckt.** `test_sql_structure.py`
  prüft ihn nicht, aber `test_migration_acceptance.py` tut es seit `G-047`,
  einschließlich der benannten Ausnahme und ihrer Gegenprobe. Keine Lücke.
- **Der Kanal-Guard ist nicht die Ursache von `SV-2026-09-03-01`.**
  `bus_guard_channel_update` lässt `source_ref` zu; die Seedzeile `START-UP`
  existiert seit `002`. Es bleibt allein das fehlende Recht.
- **Die Spiegeldateien sind synchron**, alle vier, byteidentisch.

## Nachweis und Gate

- Zu Beginn: `workforce-agent` **565**, `bus-realtest` **15**,
  `telegram-connector` **44**, `chain-test` **27** — zusammen **651 PASS**, auf
  `python3` 3.9.6 des Projektrechners. Am Ende **658**, weil eine parallele
  Sitzung sieben Tests hinzugefügt hat (siehe oben); ebenfalls **PASS**.
- Auf der NAS wurde nichts ausgeführt, nichts gelesen, nichts geändert.
- Nicht geprüft: die API-Suite (braucht den Container), jedes SQL gegen einen
  echten Parser, das Verhalten von 009 in einer laufenden Datenbank.

**Freigabe:** lokal mit `SV-2026-09-03-01` bis `-06` weitermachen. **Kein OK für
`g045_owner_probe.py`**, solange `-01` und `-02` offen sind — ein Lauf würde
vier `FAIL`-Zeilen erzeugen und die Frage, wegen der es die Datei gibt, weiter
nicht beantworten. **Kein OK für Migration 009**, solange `-04` offen ist: Eine
Migration, die den Bus stilllegen kann, wird nicht ohne benannten Rückbau
angewendet. Für das Phase-5-Fenster ändert dieser Durchgang nichts; es bleibt
rot aus den Gründen, die `HANDOVER.md` nennt.

---

# Nachcheck derselben Vertretung — Stand `e38b3d7`

Geprüft am 2026-09-03 nach der Übergabe: die Commits `cbd1887..e38b3d7`, also
Claudes Antworten auf `SV-2026-09-03-01` bis `-06`, den Probe-Lauf und den
neuen Übergabestand. Wieder ohne NAS-Zugriff; alle Messungen laufen auf dem Mac.

## Ergebnis

- **`SV-…-01` und `-02` geschlossen.** Die Probe ruft `bus_send_message` als
  `workforce_api` auf, liest den Rückgabewert und bindet das Auditereignis an
  Request-Id, Akteur, `MESSAGE`, `INSERT` und `record_key`. Die
  Parameterreihenfolge stimmt mit der Signatur aus `002` überein (nachgesehen,
  nicht angenommen), `p_message_id` ist wirklich ein Eingabewert, und die Route
  `SAO-001 → AI-ENG-001` entsteht aus dem Routen-Seed in `002`.
  **Entscheidend: die Allowlist in `009` wurde nicht angefasst** — der Diff
  ändert dort nur Kommentare. Genau die Verbreiterung, vor der `-01` gewarnt
  hat, ist ausgeblieben.
- **`SV-…-03` geschlossen.** Die Selbstprüfung sucht über alle Schemata und
  meldet die fehlende Voraussetzung als `NOTICE` statt als Abbruch. Beide
  Hälften binden weiter, und die Konstruktion kann rot werden.
- **`SV-…-04` bleibt offen — richtig so.** Der Satz im Migrationskopf ist
  richtiggestellt statt eingelöst, die Entscheidung ist benannt: keine
  ungeprüfte `010` in einer Woche ohne Review. Der Befund bleibt das Gate vor
  `009`.
- **`SV-…-05` geschlossen.** `PRODUCTION_COMMIT=0238768`, datierte Notiz,
  `produktiv-v9` zeigt tatsächlich auf `0238768` (nachgesehen). Der neue
  `test_production_state_drift.py` nimmt den historischen Fall
  (`672e0a7` → `compose.yaml`) als Gegenprobe — er kann also rot werden.
- **`SV-…-06` geschlossen.**
- **Regel 49** steht in `CLAUDE.md`, alle vier Spiegeldateien sind identisch.
  `583 + 15 + 44 + 27 = 669` Tests **PASS**.

## Zum Probe-Lauf: angenommen

Die Freigabe lautete „kein OK, solange `-01` und `-02` offen sind". Beide waren
behoben, bevor gelaufen wurde, dann kam die Freigabe des CEO im Chat, und die
Produktion blieb unberührt. **Die Bedingung war erfüllt; der Lauf ist gedeckt.**
Die Zweideutigkeit lag in meiner Formulierung, nicht in der Ausführung — gemeint
war „nicht bevor die Korrektur nachgeprüft ist", geschrieben stand die schwächere
Fassung. Dass die Übergabe die Stelle von sich aus offengelegt hat, statt sie als
gedeckt zu behandeln, ist das erwünschte Verhalten.

Der Nachweis selbst ist plausibel und intern stimmig: Die Reihenfolge der Zeilen
in der Messwerttabelle folgt der **Anhängereihenfolge im Code**, nicht der
Reihenfolge in `ERWARTET` — die beiden unterscheiden sich, und eine
nachträglich zusammengeschriebene Tabelle hätte eher der Erwartung gefolgt. Elf
Zusicherungen, vierzehn Zeilen, drei davon informativ: stimmt mit `ERWARTET`
überein. Der dokumentierte erste rote Lauf gehört zu den nützlicheren Teilen des
Nachweises.

## `SV-2026-09-03-07` – `REVIEW_ANTWORTEN.md` sagt, die Probe sei nicht gelaufen

**Schwere:** mittel — der Widerspruch steht in dem Dokument, das der Prüfer
liest, um zu sehen, was geschehen ist

**Datei:** `REVIEW_ANTWORTEN.md`, Abschnitt „Nachweis" am Ende des sechzehnten
Zielnachchecks

**Beobachtung.** Dort steht: „**Nicht ausgeführt und nicht behauptet:** … 
`g045_owner_probe.py`, Migration `009`. Der Probe-Lauf wurde am 2026-09-03
erneut versucht und erneut von der Berechtigungsprüfung des Werkzeugs
abgewiesen." Daneben liegen `evidence/2026-09-03_g045_owner_probe_run.md` mit
`RESULT: PASS` und ein `HANDOVER.md`, das den Lauf ausführlich beschreibt.

Die Reihenfolge erklärt es: `99e28ff` schrieb die Antworten, `86491b0` führte
die Probe aus. `REVIEW_ANTWORTEN.md` ist danach nicht mehr angefasst worden —
nachgemessen über `git log -- REVIEW_ANTWORTEN.md`, genau ein Commit im
Bereich `cbd1887..HEAD`.

**Warum problematisch.** Es ist `G-067` in Reinform: eine Gegenwartsaussage, die
zum Zeitpunkt des Schreibens stimmte und beim Lesen falsch ist. Gerd liest ab
dem 07.09. zuerst diese Datei; sie sagt ihm, der zentrale Lauf habe nicht
stattgefunden, während zwei andere Dokumente das Gegenteil belegen. Zwei
Wahrheiten im selben Übergabesatz sind schlimmer als eine fehlende — er müsste
raten, welches Dokument jünger ist.

**Kleinste sichere Korrektur.** Den Absatz auf den Stand nach dem Lauf ziehen
und den Nachweis verlinken; „nicht ausgeführt" bleibt für die API-Suite und den
echten SQL-Parser richtig. Der Nachweis wird nicht umgeschrieben, sondern die
Aussage datiert — dieselbe Bauform, die `production_state.txt` schon verwendet.

## `SV-2026-09-03-08` – Der neue Probe-Wächter misst in einem festen Zeichenabstand

**Schwere:** niedrig — heute wirkungslos, aber genau die Fragilität, die dieses
Projekt zweimal bezahlt hat

**Datei:** `workforce-agent/test_bus_function_owner.py`,
`ProbeWritesWithinTheAllowlistTest.als_owner()`

**Beobachtung.** Der Wächter sammelt Schreibziele aus den **800 Zeichen** nach
jedem `SET ROLE workforce_owner`. Ein Schreibvorgang, der weiter hinten in
derselben Anweisung steht, fällt heraus — und das ist die Richtung, in der ein
Wächter blind wird, nicht die, in der er zu viel meldet.

Drei Commits vorher steht in derselben Testdatei die Begründung dagegen:
„Abgegrenzt wird an seinem eigenen `IF NOT EXISTS (` — ein fester
Zeichenabstand hätte die vorige Prüfung mit erfasst." Dieselbe Klasse wie die
Zeilengrenze, an der `NoHardcodedCountsTest` schon zweimal vorbeigelesen hat.

**Kleinste sichere Korrektur.** Das Fenster an die Struktur binden statt an eine
Zahl: bis zum nächsten `SET ROLE`, zum nächsten `psql(`-Aufruf oder zum Ende des
Strings. Die Gegenprobe dazu ist billig — ein Schreibziel jenseits der Grenze
muss den Wächter rot machen.

## Gate

Unverändert: **kein OK für Migration `009`**, solange `SV-2026-09-03-04` offen
ist — daran ändert der `PASS` der Probe nichts, und die Übergabe sagt das selbst.
Die beiden neuen Punkte sind klein und blockieren nichts; `-07` gehört vor dem
07.09. erledigt, damit Gerd nicht zwei widersprechende Dokumente vorfindet.
Phase 5 bleibt rot aus den Gründen, die `HANDOVER.md` nennt.
