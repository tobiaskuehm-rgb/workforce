# Gesamtreview Gerd – 2026-09-01

## Auftrag und Prüfgrenze

Geprüft wurden der aktuelle Claude-Quellstand, die verbindlichen Projektquellen bis `DEC-027`/`ENG-008`, die vorhandenen Reviews und Übergaben, die lokalen Testpakete, das Git- und Manifestverfahren sowie der tatsächlich laufende Stand auf der Synology-NAS.

Die Prüfung war bis zur Ablage dieses Berichts read-only. Es wurden keine Container, Migrationen, Rechte, Zugangsdaten, Firewallregeln oder Produktivdaten verändert.

## Kurzurteil

**Technische Codequalität:** gut, mit mehreren sehr guten Sicherheits- und Testbausteinen. Claude hat die frühere Kritik nicht nur kosmetisch beantwortet, sondern Claim/Retry, Idempotenz, Datenbegrenzung, Contract-Tests, Rückbau und Nachweisführung deutlich verbessert.

**Betriebsreife für das nächste NAS-Update:** noch nicht gegeben. Der neue Quellstand ist lokal weit fortgeschritten, aber die Verbindung zum real laufenden v7-System, der genaue Migrationsumfang, die Datenbankrechte, die Sicherungsrechte und der vollständige Core-Abnahmelauf sind noch nicht ausreichend abgesichert.

**Gate:** `CORE ITERATE`.

Das laufende v7-System ist aktuell gesund. Ein sofortiges v8-Deployment wäre trotzdem unnötig riskant und ist ohne eigenes CEO-Gate nicht freigegeben.

## Nachgewiesener Stand

### Lokaler Claude-Quellstand

- Git-Commit: `226d6698ca7df9e20a832f8a8c29a99b44225878`
- Arbeitsbaum beim Abschluss der Prüfung: sauber
- Git-Remote auf der NAS zeigt auf denselben Commit
- Git-Prüfung: keine beschädigten Objekte
- Secret-Mustersuche im aktuellen Stand und in der Historie: kein Treffer
- Python-Syntaxprüfung: 40 Dateien ohne Fehler
- Shell-Syntaxprüfung: alle versionierten Shellskripte ohne Fehler
- Tests:
  - Workforce Agent: 194/194 PASS
  - Bus Realtest: 15/15 PASS
  - Telegram Connector: 35/35 PASS
  - Chain Test: 9/9 PASS
  - Summe: **253/253 PASS**
- API-Tests: von Claude als 30/30 PASS dokumentiert; auf diesem Mac mangels lokaler API-Testabhängigkeiten nicht unabhängig wiederholt

### Tatsächlich laufende NAS

- `startup-db-1`: gesund, PostgreSQL 17 Alpine, 0 Neustarts
- `startup-workforce-api-1`: gesund, Image `startup-workforce-api:v7`, 0 Neustarts, read-only Root-Dateisystem
- PostgreSQL ist nicht als Host-Port veröffentlicht
- API-Port 8080 ist am NAS-Host veröffentlicht und wird durch die DSM-Firewall begrenzt
- `/health`: OK
- `/db-check`: OK
- `/bus/v1/status`: API v7, Migration 002, Kanal `DISABLED`
- `/knowledge/v1/status`: 404; die laufende API enthält die Knowledge-Routen nicht
- Datenbankmigrationen: 001, 002 und 003
- Aktive, nicht abgelaufene Credentials: 0
- Busbestand: 28 Nachrichten, 9 Tasks, 8 Handoffs, 248 Events
- Laufende API und NAS-Quelldatei haben denselben Hash; dieser Produktivstand lässt sich jedoch keinem Commit des aktuellen Claude-Repositories zuordnen

### Sicherungen und Git

- Nachtbackup vom 2026-09-01 vorhanden
- SQL-Dump: 330.502 Byte, nicht leer, Abschlussmarker vorhanden
- Konfigurationsarchiv: 12.833 Byte, gzip-Prüfung PASS
- Git-Remote auf der NAS: aktueller Commit `226d669`
- Zusätzliches Git-Bundle: gültig, aber einen Commit zurück
- Der letzte dokumentierte Restore-Test stammt nicht vom aktuellen September-Backup
- Git-Remote, Git-Bundle, Produktivdaten und Backups liegen auf derselben NAS und schützen deshalb nicht gegen einen Ausfall oder Verlust dieser NAS

## Neue Befunde

### G-022 — Backups sind für alle NAS-Benutzer lesbar

**Schwere:** hoch – sofortige Sicherheitsmaßnahme

Der Ordner `/volume1/docker/Startup-Backups` gewährt über seine Synology-ACL `everyone` Leserechte. Das aktuelle Konfigurationsarchiv enthält unter anderem `startup.env`; die SQL-Dumps enthalten betriebliche Daten.

**Risiko:** Jeder normale NAS-Benutzer kann potenziell Datenbankpasswort, API-Schlüssel und Datenbankinhalte aus den Backups lesen.

**Empfehlung:** ACL des Backupordners auf Administratoren und den notwendigen Sicherungsdienst begrenzen. Danach beweisen, dass der geplante Backupjob weiter schreiben kann und ein normaler Benutzer nicht lesen kann. Anschließend prüfen, ob wegen der bisherigen Lesbarkeit eine kontrollierte Rotation der betroffenen Zugangsdaten erforderlich ist. Die Rotation bleibt eine gesondert freizugebende Aktion.

### G-023 — Der laufende v7-Stand ist nicht an einen Git-Commit gebunden

**Schwere:** hoch – Deployment-Blocker

Die Hashes der tatsächlich laufenden v7-Dateien passen weder zu einem Commit des Claude-Repositories noch vollständig zu einem versionierten Stand der autoritativen Projektablage. Das aktuelle Deploy-Manifest umfasst Agent, Telegram, Chain und Reviewdateien, aber nicht `compose.yaml`, `workforce-api/` und `postgres-init/` des Produktivstacks.

**Risiko:** Vor einem Update existiert kein eindeutig versionierter Rückfallpunkt des real laufenden Systems. „Manifest PASS“ beweist derzeit nicht den vollständigen Produktivstack.

**Empfehlung:** Vor jedem Update den exakten v7-Bestand als unveränderlichen Rollback-Snapshot mit Image-ID, Dateien, Hashes und Git-Tag/Commit sichern. Das Manifest anschließend auf alle produktiven Compose-, API-, Dockerfile-, Migrations- und Testpfade ausweiten.

### G-024 — Backup ist vorhanden, aber Wiederherstellung und NAS-Ausfall sind nicht aktuell abgedeckt

**Schwere:** hoch

Die aktuellen Sicherungsdateien sehen formal plausibel aus. Ein isolierter Restore des neuesten Dumps wurde aber nicht nachgewiesen. Git-Remote, Bundle und Backup liegen sämtlich auf derselben NAS.

**Risiko:** Ein syntaktisch gültiger Dump kann sich trotzdem als unvollständig oder nicht sauber migrierbar erweisen. Bei Defekt, Diebstahl oder Verlust der NAS fallen Original und Sicherungen gemeinsam aus.

**Empfehlung:** Neueste Sicherung in einem isolierten Testprojekt wiederherstellen und fachlich prüfen. Danach eine verschlüsselte, versionierte Off-NAS-Sicherung einrichten; kein neues kostenpflichtiges Produkt ohne CEO-Entscheidung.

### G-025 — Die API arbeitet mit einem PostgreSQL-Superuser

**Schwere:** hoch – spätestens vor externem Kanal oder Modellbetrieb schließen

Der von der Anwendung verwendete Datenbanknutzer besitzt `SUPERUSER`, `CREATEROLE` und `CREATEDB`.

**Risiko:** Ein Fehler oder eine Kompromittierung der API kann Schutztrigger und Auditregeln umgehen, Rechte verändern sowie die gesamte Datenbank ändern oder löschen. Die Datenbank ist zwar nicht extern veröffentlicht, aber die Anwendung selbst hat unnötig weitreichende Rechte.

**Empfehlung:** Rollen trennen: Migration/Administration, Backup und API-Laufzeit. Die API erhält nur die notwendigen Tabellen-, Funktions- und Sequenzrechte. Migrationen laufen nicht mehr mit dem API-Laufzeitkonto.

### G-026 — Docker-Buildkontexte schließen Secret- und Laufzeitdateien nicht aus

**Schwere:** mittel bis hoch

In den Buildkontexten fehlt eine `.dockerignore`. Die Dockerfiles kopieren zwar nur ausgewählte Dateien in das fertige Image, Docker überträgt jedoch zunächst den gesamten Kontext an Builder beziehungsweise Daemon.

**Risiko:** Lokale `secrets/`-, State-, Environment- oder Backupdateien können in Buildkontext und Cache gelangen.

**Empfehlung:** Für jeden Buildkontext eine strenge `.dockerignore` ergänzen und automatisiert beweisen, dass Secrets, SQLite-State, `.env`, Evidenz und Backups nicht im Kontext oder Image liegen.

### G-027 — Knowledge-Datenbankfehler werden als falscher Busfehler ausgegeben

**Schwere:** mittel

`workforce-api/app.py` akzeptiert in der Fehlernormalisierung nur Fehlercodes mit `BUS_`. Fehler wie `KNOWLEDGE_AUTH_FAILED` werden deshalb vor der HTTP-Zuordnung durch `BUS_DATABASE_UNAVAILABLE` ersetzt.

**Risiko:** Knowledge-Zugriffe liefern falsche Statuscodes und Gründe; Audit, Fehlersuche und Zugriffstests können ein Sicherheitsproblem als Datenbankausfall darstellen.

**Empfehlung:** Stabile Bus- und Knowledge-Fehler getrennt und explizit abbilden. Tests für Authentifizierung, Berechtigung, Nichtvorhandensein und DB-Ausfall auf jedem Knowledge-Endpunkt ergänzen.

### G-028 — Der API-Regressionsschutz erfasst nicht alle vorhandenen Routen

**Schwere:** mittel

Der Test mit dem Anspruch, alle Bus- und Knowledge-Routen zu inventarisieren, lässt mehrere bestehende Legacy-/UI-Routen aus, unter anderem Kernel, Rollen, Worker, Tasks, Dokumente und Aktivitäten.

**Risiko:** Ein späterer Merge kann bestehende Funktionalität entfernen, während der angeblich vollständige Regressionstest weiter grün bleibt.

**Empfehlung:** Route-Inventar aus der realen Anwendung ableiten oder alle gewollten Routen vollständig als Vertrag festhalten. Nicht mehr gewünschte Routen nur mit bewusster Entscheidung entfernen.

### G-029 — Modell- und Datengrenze starten nicht vollständig fail-closed

**Schwere:** hoch vor echtem Modellbetrieb

Ohne `AGENT_PROVIDER` fällt der Provider auf `claude` zurück. Die Beispieldatei setzt `AGENT_DATA_POLICY=FULL`, obwohl die Dokumentation `METADATA_ONLY` als sicheren Ausgangspunkt bezeichnet. Auch `METADATA_ONLY` überträgt den Betreff und damit möglichen Nachrichteninhalt.

**Risiko:** Eine unvollständige Konfiguration kann unbeabsichtigt einen kostenpflichtigen externen Provider starten und mehr Inhalt senden als erwartet.

**Empfehlung:** Fehlender Provider muss den Start verweigern oder explizit `echo`/`disabled` ergeben. Datenpolicy standardmäßig `DENY` beziehungsweise strikt metadatenarm; Betreff als Inhaltsfeld behandeln. Reale Provider nur mit explizitem CEO-, Kosten- und Datengate.

### G-030 — Der verbindliche Core-Ablauf wird noch nicht von der tatsächlichen Runtime ausgeführt

**Schwere:** hoch – Core-Blocker

Der Core-Roundtrip skriptet die Rollen und Lebenszyklusübergänge direkt über den Bus. Der Worker-Core-Test verwendet den realen Worker, prüft aber nur Nachrichten zwischen Karl und dem Agenten. Der Worker selbst verarbeitet keine vollständige Task-/Handoff-Kette.

**Risiko:** Beide Tests sind wertvoll, beweisen zusammengenommen aber nicht, dass die Mitarbeiter-Runtime den verbindlichen Ablauf `Task → Ergebnis → Handoff → ACCEPTED → Arbeit → Ergebnis → DONE → Audit` tatsächlich selbst ausführt.

**Empfehlung:** Einen einzigen integrierten, kostenlosen Echo-Core-Test bauen. Der reale Runtime-/Orchestratorpfad muss Task, Handoff, Ablehnung, Retry, Neustart, Idempotenz und Abschluss bearbeiten. Ein Skript darf Fixtures und Prüfung steuern, aber nicht die fachliche Mitarbeiterarbeit stellvertretend ausführen.

### G-031 — Compose würde Knowledge-Migration 004 als Nebenwirkung ausführen

**Schwere:** hoch – Deployment-Blocker

Der zusammengeführte Compose-Stand startet im Migrationslauf nacheinander `004_knowledge_capability` und `005_bus_denial_audit`. Auf der realen NAS sind nur 001 bis 003 installiert. Knowledge besitzt weiterhin ein eigenes NAS-/Rechte-/Produktivgate und ist keine Voraussetzung für den Core-Test.

**Risiko:** Ein vermeintliches Core-/Audit-Update aktiviert ungefragt einen gesondert gegateten Funktionsbereich.

**Empfehlung:** Migration 004 und 005 technisch entkoppeln. Für das Core-Fenster darf nur die ausdrücklich freigegebene Bus-Audit-Migration laufen. Knowledge wird in einem separaten, späteren Gate migriert.

### G-032 — Die autoritative Projektsteuerung ist hinter dem technischen Stand zurück

**Schwere:** mittel bis hoch – Governance

Die autoritative Ablage enthält umfangreiche uncommittete Änderungen. `SOURCE_MANIFEST.md` ist auf 2026-08-27 datiert, benennt aber in seiner Übersicht noch DEC-026/ENG-007, obwohl die Quellen bereits DEC-027/ENG-008 enthalten. Offene Gates und Statusdateien bilden die späteren Telegram-/Chain-Nachweise nicht konsistent ab.

**Risiko:** Code, Entscheidung, Gate und Bericht können jeweils einen anderen Zustand behaupten. Eine technische Umsetzung darf dadurch weder unbemerkt zur CEO-Entscheidung noch eine alte Statusdatei zum Rollout-Blocker werden.

**Empfehlung:** Vor dem nächsten Gate die Autoritätsquellen append-only auf einen konsistenten Stand bringen, Änderungen committen und die Grenze zwischen Entscheidungsablage und Code-Repository als CEO-Entscheidung festhalten.

### G-033 — Dokumentation und Manifest enthalten noch überstarke Aussagen

**Schwere:** mittel

Beispiele: Der Kopf von `deploy_manifest.sh` zeigt noch den alten Archivierungsbefehl, obwohl `HANDOVER.md` bereits `tar -T` nutzt. Das Manifest meldet einen exakten Stand, deckt aber den Produktivstack nicht ab. In `HANDOVER.md` stehen an einzelnen Stellen alte Migrationsbezeichnungen beziehungsweise widersprüchliche Offen-/Erledigt-Aussagen.

**Risiko:** Ein Bediener kann den falschen Befehl kopieren oder einen Teilnachweis als Gesamtnachweis verstehen.

**Empfehlung:** Runbooks aus ausführbaren/prüfbaren Quellen ableiten, Manifest-Scope sichtbar ausgeben und nach jedem materiellen Schritt einen Widerspruchsscan über AGENTS, HANDOVER, Review, Evidenz und Autoritätsdateien ausführen.

### G-034 — Das Kostenbudget zählt SDK-Retries und Modell-Fallback nicht sicher als einzelne Versuche

**Schwere:** hoch vor bezahltem Modellbetrieb

Der Worker reserviert einen logischen Provideraufruf, der Anthropic-Client kann intern jedoch mehrfach wiederholen und ein Fallbackmodell verwenden. Diese Netzwerk-/Modellversuche erscheinen nicht einzeln im lokalen Budget.

**Risiko:** Die konfigurierte Aufrufgrenze ist für einen kostenpflichtigen Provider keine harte Obergrenze der tatsächlichen externen Versuche oder Kosten.

**Empfehlung:** Automatische SDK-Retries deaktivieren oder jeden tatsächlichen Versuch zentral budgetieren. Kostendecke vor dem ersten bezahlten Versuch reservieren; Usage und unbekannte Kosten fail-closed behandeln. Bis dahin nur Echo verwenden.

## Unabhängig hergeleitete Roadmap

Diese Roadmap ist eine **Empfehlung von Gerd und keine CEO-Freigabe**. Sie wurde aus Autorität, Code und realem NAS-Zustand hergeleitet, bevor Claudes Vorschläge zum Vergleich übernommen wurden.

### Phase 0 – Sofortige Begrenzung

1. Backup-ACL schließen und Negativzugriff prüfen.
2. Bis zum gesicherten v7-Rückfallstand keine Produktivmigration und kein v8-Deployment.
3. Danach bewerten, ob kontrollierte Credential-Rotation erforderlich ist.

### Phase 1 – Wahrheit und Rückfallpunkt sichern

1. Exakten laufenden v7-Stand als versionierten Rollback-Snapshot sichern.
2. Produktive Pfade in das vollständige Manifest aufnehmen.
3. Autoritätsquellen bis DEC-027/ENG-008 konsistent machen und committen.
4. Per CEO-Entscheidung festhalten: Entscheidungen/Status liegen in der Autoritätsablage, ausführbarer Code im Claude-Repository; Parallelentwicklungen werden importiert oder archiviert.
5. Git-Bundle aktualisieren und eine Off-NAS-Sicherungsentscheidung vorbereiten.

### Phase 2 – Lokale Rollout-Blocker schließen

1. Knowledge 004 vom Bus-Audit 005 entkoppeln.
2. Knowledge-Fehlerabbildung und vollständiges Routeninventar korrigieren.
3. `.dockerignore` und Buildkontext-Negativtests ergänzen.
4. Provider-/Datenpolicy fail-closed machen.
5. Tatsächliche Provider-Retries hart budgetieren.
6. Rollenmodell für Migration, Backup und API-Laufzeit vorbereiten.

### Phase 3 – Isolierte Wiederherstellungs- und Upgradeprobe

1. Neuesten NAS-Dump in einem separaten Projekt wiederherstellen.
2. Upgrade von real 001–003 auf den vorgesehenen Core-Stand proben.
3. Im Core-Zweig ausschließlich die freigegebene Migration 005 testen; Knowledge 004 separat und ohne Produktivaktivierung prüfen.
4. Alle 30 API-Tests unabhängig im Zielcontainer, SQL-Acceptance, Route-Inventar, Secret-Isolation, Restart und Rollback ausführen.

### Phase 4 – Kontrolliertes NAS-Foundation-Fenster

Erst mit neuem konkretem CEO-Gate: frisches Backup, bestätigtes v7-Rollbackimage, sauberer Commit, vollständiges Manifest, Migration 005 ohne Knowledge-Nebenwirkung, anschließend Health-, Persistenz-, Restart-, Negativ- und Rollbackprüfung.

### Phase 5 – Vollständiger Runtime-Core

1. Minimalen modellunabhängigen Runtime-/Orchestratorpfad fertigstellen.
2. Karl/Gerd/Anastasia-Kette vollständig durch die Runtime ausführen.
3. `REJECTED`, Permission-Denial, Providerfehler, Retry, Doppelzustellung, Neustart und genau eine Ergebnisverarbeitung beweisen.
4. Positive und negative Auditspur automatisiert aus PostgreSQL rekonstruieren.
5. Weiterhin Echo, kein kostenpflichtiges Modell.

### Phase 6 – Rückbau und formelles Core-Gate

Alle Testcredentials widerrufen, Kanal `DISABLED`, Secrets/Testcontainer/Testnetz entfernen, Firewall negativ nachmessen, Backupjob erneut prüfen und Manifest verifizieren. Erst danach `CORE PASS`, `ITERATE` oder `FAIL` in allen Autoritätsdateien konsistent festhalten.

### Phase 7 – Verbindliche Reihenfolge fortsetzen

Nach `CORE PASS`: Thorsten/Research. Erst nach dessen PASS und eigenem CEO-Gate: Finance. Danach Gesamtvalidierung. Knowledge, Telegram, echter Modellprovider und Workspace-Agent bleiben getrennte spätere Gates und dürfen den Core nicht nebenbei erweitern.

## Vergleich mit Claudes Roadmap

### Übereinstimmung

Claudes Vorschläge, zuerst den Git-Remote zu schaffen, die kanonische Grenze zu entscheiden, Auditwerkzeuge vor dem nächsten großen Gate zu bauen und den Mitarbeitervertrag vor weiterer Runtime-Automation zu stabilisieren, sind fachlich richtig. Der Git-Remote ist inzwischen eingerichtet und aktuell.

### Wichtige Ergänzungen durch dieses Review

- Backup-ACL ist dringender als neue Funktionalität.
- Der reale v7-Produktivstand braucht vor jedem Update einen reproduzierbaren Rückfallpunkt.
- Ein formaler Backup- und Manifest-PASS reicht ohne Restore und vollständigen Produktivscope nicht aus.
- Datenbank-Superuser und Docker-Buildkontext müssen gehärtet werden.
- Die Knowledge-Migration darf nicht im Core-Fenster nebenbei ausgeführt werden.
- Zwei getrennte grüne Tests ersetzen noch keinen integrierten Runtime-Core.
- Git auf derselben NAS ist Versionssicherung, aber keine Ausfallsicherung.

### Abweichung

Der bisherige Vorschlag, im nächsten Fenster Migration 004 und 005 gemeinsam auszurollen, wird nicht übernommen. Er widerspricht dem getrennten Knowledge-Gate. Ebenfalls wird ein echter Modelllauf nicht als nächster Meilenstein empfohlen; Echo reicht für den vollständigen Core-Nachweis und vermeidet Kosten- und Datenrisiko.

## Empfohlene nächste CEO-Entscheidungen

Noch keine davon ist durch diesen Bericht erteilt:

1. Freigabe, ausschließlich die ACL des Backupordners zu härten und den Zugriff negativ zu testen.
2. Festlegung der kanonischen Zuständigkeit von Autoritätsablage und Code-Repository.
3. Entscheidung über eine verschlüsselte Off-NAS-Sicherung.
4. Später ein exakt begrenztes, kostenloses NAS-Foundation-/Core-Testfenster mit Migration 005, aber ohne Knowledge 004 und ohne echten Modellprovider.

## Abschlussurteil

Claude/Opus hat hier insgesamt **gute bis sehr gute Entwicklungsarbeit** geleistet. Besonders Tests, Rückbau, Default-Deny-Grundstruktur und die Reaktion auf frühere Reviews sind deutlich über einem bloßen Prototypniveau. Die offenen Punkte liegen weniger in schlechtem Code als in den kritischen Übergängen zwischen Code, realem Produktivstand, Migration, Berechtigungen und beweisbarer End-to-End-Runtime.

Der richtige nächste Schritt ist deshalb kein weiterer Feature-Sprint, sondern: **Sicherungen absichern → Produktivstand versionieren → Migrationen entkoppeln → isoliert wiederherstellen und upgraden → integrierten Echo-Core beweisen.**

## Ablagenachweis

- Lokale Arbeitsfassung: `GESAMTREVIEW_GERD_2026-09-01.md`
- NAS-Fassung: `/volume1/docker/Startup/GESAMTREVIEW_GERD_2026-09-01.md`
- Aktualisierte Befunddatei: `/volume1/docker/Startup/REVIEW_GERD.md`
- Rückfallkopie der vorherigen Befunddatei: `/volume1/docker/Startup/REVIEW_GERD.before-gesamtreview-2026-09-01.md`
- SHA-256 der vorherigen Befunddatei: `cefed29557bac52fe6fb44a87ae299873669483b1bad2f8fced22eae2c0d63ff`
- SHA-256 der aktualisierten Befunddatei: `4b25dbc06897ca807fa345dd16a6d10e00ab4be19ffb465872a9c811d51000b0`

Der vorhandene Deploy-Manifestprüfer meldet nach der Ablage genau eine erwartete Abweichung: `REVIEW_GERD.md`. Das Manifest wurde bewusst nicht unter dem unveränderten Commit `226d669` umgeschrieben, weil dies eine falsche Provenienz behaupten würde. Claude soll beide Reviewdateien prüfen, versionieren und erst danach ein neues Manifest aus dem dann sauberen Commit erzeugen. Der Produktivcode selbst wurde durch die Reviewablage nicht verändert.
