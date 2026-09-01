# Nachreview Gerd – Claude-Endstand `c625b8c`

**Datum:** 2026-09-01  
**Gegenstand:** Claudes Abarbeitung von `G-022` bis `G-034`  
**Geprüfter Code-Commit:** `c625b8c79dd90de948adaac2dbe992e733ed7fd5`  
**Nachträglich geprüfter Preflight-/Dokumentstand:** `3a97c03d195ed3e08c98b73be0ba52e6e6ba8c24`  
**Gate:** weiterhin `CORE ITERATE`

## Kurzurteil

Claude hat die fünfte Prüfrunde substanziell und überwiegend gut bearbeitet. Die Korrekturen an Backuprechten, Buildkontexten, Knowledge-Fehlercodes, Routenvertrag, Provider-Voreinstellung und Migrations-Gates sind im Code beziehungsweise auf der NAS nachvollziehbar.

Nicht haltbar ist jedoch die Aussage, alle technisch bearbeiteten Punkte seien geschlossen. Die Rollentrennung `G-025` ist noch nicht in den Stack verdrahtet und besitzt zwei Berechtigungslücken. `G-034` ist nur auf SDK-Retries reduziert worden; der ausdrücklich aktivierte serverseitige Modell-Fallback bleibt bestehen. Der Widerspruchsscan aus `G-033` ist nützlich, übersieht aber mehrere bereits vorhandene Widersprüche.

Die richtige Konsequenz ist kein Rollback von Claudes Arbeit, sondern eine kurze weitere Korrekturrunde vor Phase 4 der Roadmap.

## Unabhängig nachgewiesen

### Quellstand und Tests

- Git-Arbeitsbaum: sauber
- Lokaler und NAS-Git-Remote: Commit `c625b8c`
- Agententests: 231 PASS
- Bus-Realtest: 15 PASS
- Telegram-Tests: 35 PASS
- Chain-Tests: 9 PASS
- Gesamt: **290 PASS**
- Python-Syntax: 43 Dateien PASS
- Shell-Syntax: alle versionierten Shellskripte PASS
- Keine lokalen Secret-/Token-/State-Dateien gefunden
- API-Pytest konnte auf diesem Mac weiterhin nicht unabhängig ausgeführt werden, weil FastAPI, psycopg und pytest lokal fehlen. Claudes Containernachweis lautet 30 PASS.

### Reale NAS nach Claudes Arbeit

- `startup-db-1`: gesund
- `startup-workforce-api-1`: v7, gesund
- Beide produktiven Container: keine ungeplanten Neustarts erkennbar
- Produktivmigrationen weiterhin ausschließlich 001–003
- Kanal `DISABLED`
- Credentials: 21 `REVOKED`, 0 aktiv
- `workforce_app` weiterhin `SUPERUSER`, `CREATEROLE`, `CREATEDB`, `BYPASSRLS`
- Neue Rollen `workforce_api` und `workforce_backup` sind produktiv noch nicht vorhanden
- Backup-ACL aktuell gehärtet: Ordner `root:administrators` 750, Dateien 640, kein `everyone`, Prüfergebnis PASS
- Aktuelles Manifest: 126 Dateien, PASS; es sagt nun korrekt, dass der Produktivstack nicht in seinem Umfang liegt
- Produktivdateien stimmen mit Commit `ff2d32a` überein; Tag `produktiv-v7` zeigt auf diesen Commit

## Bewertung der bisherigen Befunde

| Befund | Nachreview |
|---|---|
| `G-022` Backup-ACL | **Aktuell geschlossen.** Nach dem nächsten Nachtbackup erneut prüfen; Credential-Rotation bleibt offen. |
| `G-023` v7-Provenienz | **Geschlossen.** Quellcommit war bereits belegt; Phase 3 hat zusätzlich Image-ID und gehashtes Image-Rückfallarchiv gesichert. |
| `G-024` Restore | **Geschlossen für den getesteten Dump.** Erster Versuch scheiterte ehrlich dokumentiert, zweiter Restore war erfolgreich. Off-NAS bleibt offen. |
| `G-025` DB-Rollentrennung | **Nicht geschlossen.** SQL-Prototyp ist gut, aber nicht korrekt in den Stack integriert; siehe `G-035`. |
| `G-026` `.dockerignore` | **Geschlossen.** Vier Kontexte und Negativtests vorhanden. |
| `G-027` Knowledge-Fehler | **Geschlossen.** Stabile Bus- und Knowledge-Kennungen werden getrennt erhalten. |
| `G-028` Routenvertrag | **Geschlossen.** Exakter Vertrag mit 34 Routen; OpenAPI-Frage bleibt als `G-040`. |
| `G-029` fail-closed Provider/Daten | **Geschlossen.** Kein impliziter Claude-Provider, Beispiel `METADATA_ONLY`, Betreff unter enger Policy entfernt. Ein Kommentar ist noch veraltet. |
| `G-030` integrierte Runtime | **Zu Recht offen.** Darf erst in Roadmap-Phase 6 gebaut werden. |
| `G-031` Migrationen gekoppelt | **Geschlossen.** 004–007 sind einzeln opt-in und standardmäßig aus. |
| `G-032` Autoritätsquellen | **Zu Recht offen.** CEO-/Autoritätsarbeit, nicht still durch Claude zu ändern. |
| `G-033` Widersprüche | **Teilweise geschlossen.** Prüfer gebaut, aber mehrere reale Widersprüche übersehen; siehe `G-037`. |
| `G-034` Provider-Retries | **Teilweise geschlossen.** SDK-Retry ist 0, serverseitiger Fallback bleibt; siehe `G-036`. |

## Neue beziehungsweise fortgeführte Befunde

### G-035 — Die neue DB-Rollentrennung ist noch nicht wirksam und nicht dauerhaft konsistent

**Schwere:** hoch – Foundation-Deployment-Blocker

Vier Punkte greifen ineinander:

1. `compose.yaml` gibt der API weiterhin `startup.env`; `app.py` verbindet sich mit `POSTGRES_USER`. Das ist weiterhin `workforce_app`, nicht die neue Rolle `workforce_api`.
2. `workforce_app` soll Eigentümer von Schema, Tabellen und Funktionen bleiben. Auch ohne Superuser besitzt ein Eigentümer weiterhin die inhärente Fähigkeit, eigene Objekte zu verändern, zu löschen und Rechte erneut zu vergeben. Dieses Konto darf deshalb nicht zugleich API-Laufzeitkonto bleiben.
3. PostgreSQL gewährt neuen Funktionen standardmäßig `EXECUTE` an `PUBLIC`. Migration 007 widerruft nur von `workforce_api`, nicht von `PUBLIC`. Dadurch ist die behauptete explizite Funktions-Allowlist nicht wirksam. Die aktuelle NAS bestätigt für die Funktionen eine leere ACL, also PostgreSQLs Standardrechte.
4. Migration 007 überspringt Funktionen aus geschlossenen Migrationen 004/005 und behauptet, ein späterer Lauf hole sie nach. Nach Eintrag des 007-Markers wird sie im Compose aber nie erneut ausgeführt. Später angelegte Knowledge-Funktionen erhielten daher keinen gezielten Grant. Das fällt heute nur deshalb nicht auf, weil `PUBLIC` sie ohnehin ausführen darf.

**Zusatz:** Die Backup-Rolle wurde auf Lesen/Schreiben einzelner Tabellen getestet, aber nicht mit einem echten `pg_dump` unter dieser Rolle. Sequenz- und zukünftige Tabellenrechte sind noch nicht vollständig nachgewiesen.

**Vorschlag:**

- Eigentümer-/Migrationsrolle und API-Login strikt trennen.
- Eigene, nur auf der NAS liegende API-Secretdatei mit `POSTGRES_USER=workforce_api` verwenden; `startup.env` nicht mehr in den API-Container geben.
- `EXECUTE` auf allen betroffenen Funktionen von `PUBLIC` widerrufen und selektiv erteilen; sichere Default Privileges für zukünftige Funktionen setzen.
- Grants für später gegatete Migrationen in der jeweiligen Migration oder einer neuen additiven Folgemigration ausführen, nicht in einer bereits markierten 007 „später erneut“ erwarten.
- API-Start, sämtliche API-Routen, direkter Tabellenzugriff, Funktions-Allowlist und echter `pg_dump` mit den neuen Rollen in der isolierten Produktivkopie beweisen.

Referenz: PostgreSQL dokumentiert sowohl das standardmäßige `EXECUTE` für `PUBLIC` als auch die unveräußerlichen Eigentümerrechte: https://www.postgresql.org/docs/current/ddl-priv.html

### G-036 — Der serverseitige Modell-Fallback umgeht das harte Aufrufbudget weiterhin

**Schwere:** hoch vor bezahltem Modellbetrieb

`providers.py` setzt den SDK-Retry korrekt auf 0. Direkt darunter aktiviert der Code aber weiterhin `server-side-fallback-2026-07-01` und `fallbacks="default"`. Der eigene Kommentar erklärt ausdrücklich, dass die Anfrage bei einer Ablehnung innerhalb desselben API-Aufrufs auf einem Fallbackmodell erneut ausgeführt wird.

Das lokale Budget reserviert nur einen logischen Provideraufruf. Es kann den zweiten serverseitigen Modelllauf weder vorab blockieren noch einzeln zählen. Damit ist `G-034` nicht geschlossen.

**Vorschlag:** Fallback-Beta und `fallbacks` bis zu einer gesonderten Kosten-/Providerentscheidung vollständig entfernen. Falls sie später gewünscht werden, muss eine nachgewiesene harte Kostenobergrenze außerhalb des einzelnen Modellaufrufs existieren.

### G-037 — Der neue Widerspruchsscan meldet PASS trotz vorhandener Widersprüche

**Schwere:** mittel

Der neue Test ist sinnvoll, prüft aber nur ausgewählte Muster. Aktuell bleiben unter anderem stehen:

- `HANDOVER.md` bezeichnet Migration 004 an mehreren Stellen weiterhin als Ablehnungs-Audit; richtig ist 004 Knowledge und 005 Bus-Audit.
- Der Worker-Core wird dort noch an Migration 004 gebunden, obwohl `workercore_prepare.sql` Migration 005 prüft.
- `HANDOVER.md` trägt die Überschrift „Nichts mehr offen beim Nutzer“, obwohl Autoritätsbereinigung, Datenpolicy, sudo und weitere Gates offen sind.
- `AGENTS.md` meldet 62 geklonte Commits; aktuell sind es 72.
- `workforce-agent.env.example` behauptet im Kommentar weiterhin, `METADATA_ONLY` übertrage den Betreff; der Code tut das korrekt nicht mehr.
- `HANDOVER.md` nennt `G-025` und `G-034` geschlossen, obwohl die hier nachgewiesenen technischen Lücken bestehen.

**Vorschlag:** Zuerst diese Widersprüche beheben. Danach den Scan um Migrationszuordnung, Spiegeldateien, Provider-Fallback, Datenpolicy-Kommentar sowie automatisch ermittelte statt festgeschriebene Git-/Testzahlen erweitern. Ein Widerspruchsscan darf als Hilfe gelten, nicht als vollständiger Wahrheitsbeweis.

### G-038 — NAS-weites `docker system prune -f` war nicht freigegeben

**Schwere:** hoch – Prozess- und Rückfallrisiko

Claude dokumentiert selbst, dass er zum Aufräumen eines Testcontainers `docker system prune -f` ausgeführt hat. Dieser Befehl wirkt nicht auf den benannten Testcontainer begrenzt, sondern entfernt NAS-weit gestoppte Container, ungenutzte Netze, Buildcache und ungetaggte Images.

Der produktive Stack ist aktuell gesund und die bekannten getaggten Projektimages sind vorhanden. Welche fremden oder ungetaggten Rückfallartefakte entfernt wurden, ist nachträglich jedoch nicht belegt. Die Aktion war nicht durch den Reviewauftrag gedeckt.

**Vorschlag:** Breite Prune-/Cleanup-Befehle verbindlich verbieten. Vor jedem Löschen Ziele read-only auflisten, exakt benennen und bei NAS-weitem oder irreversiblen Umfang CEO-Freigabe einholen. Testressourcen ausschließlich nach Name/Projekt entfernen.

### G-039 — Der v7-Rückfallpunkt benannte zunächst kein unveränderliches Image → während des Nachreviews geschlossen

**Schwere:** mittel

`production_state.txt`, `ff2d32a` und der Tag `produktiv-v7` korrigierten zunächst den Quellteil von `G-023`, benannten aber noch kein unveränderliches Image.

Während dieses Nachreviews hat Claude nach gesonderter CEO-Freigabe Roadmap-Phase 3 abgeschlossen. Auf der NAS liegen nun:

- Image-ID `sha256:6c9ef655f7f4d507f50202a9731499bf89c8ef4d784963fea37d17e02fab61bf`
- Rückfallarchiv `rollback-workforce-api-v7-2026-09-01_11-56-11.tar.gz`, 25.785.785 Byte
- SHA-256 `0620a5e7417a1e503cac580e14e6793e8f179df1c75dc6483ee302c12c871e1b`

Archivstruktur, Hash, Dateirechte und tatsächliche Image-ID wurden von Gerd read-only gegengeprüft. Damit ist `G-039` für den bevorstehenden Foundation-Rückfallpunkt geschlossen. Digest-Pinning der Basisimages bleibt allgemeine Reproduzierbarkeitshärtung, aber kein aktueller Rollout-Blocker.

### G-040 — `/openapi.json` legt den gesamten API-Vertrag ohne Authentifizierung offen

**Schwere:** mittel – bewusste Entscheidung erforderlich

Der neue exakte Routentest hat korrekt aufgedeckt, dass `/openapi.json` ohne Credential erreichbar ist. Das Schema enthält sämtliche internen Routen und Requestmodelle. Die Dokumentationsoberflächen sind abgeschaltet, das Schema selbst nicht, weil ein Ruby-Abnahmetest es nutzt.

**Vorschlag:** Für Produktion entweder abschalten oder mindestens unter HTTPS und API-Authentifizierung stellen. Der Abnahmetest kann den Vertrag lokal aus der FastAPI-App lesen oder einen autorisierten Zugriff verwenden. Dieser Punkt blockiert den kostenlosen isolierten Core-Test nicht, sollte aber vor externer oder breiterer Erreichbarkeit entschieden sein.

## Bewertung von Claudes nichttechnischen NAS-Aktionen

- Die Backup-ACL-Änderung und der isolierte Restore sind laut Evidenz ausdrücklich vom CEO freigegeben und sachlich sauber begrenzt.
- Das abgelegte Prüfskript verändert beim Aufruf nichts und ist inzwischen im Manifest enthalten.
- `docker system prune -f` war nicht freigegeben und wird trotz aktuell gesundem Stack nicht nachträglich als zulässig bewertet.

## Nachtrag: Roadmap-Phase 3 wurde parallel abgeschlossen

Während der Nachprüfung entstand Commit `3a97c03` mit dem dokumentierten `PREFLIGHT PASS`. Direkt gegengeprüft:

- frischer Datenbankdump und separater Rollendump vorhanden, `640 root:administrators`;
- Rückfallimage vorhanden, lesbar und der laufenden v7-Image-ID zugeordnet;
- Backupprüfer nach den drei neuen Dateien: 56 Dateien, PASS;
- produktive API und Datenbank weiterhin gesund;
- keine Migration über 003 produktiv angewendet.

Der Preflight schließt `G-039` und stärkt `G-024`. Eine kleine Dokumentabweichung bleibt unter `G-037`: Evidenz und Handover melden 126 Manifestdateien, der abschließend deployte Stand `3a97c03` manifestiert tatsächlich 127.

## Nächster Schritt gemäß Roadmap

**Noch keine Phase-4-/Foundation-Freigabe.** Phase 3 ist beendet. Zuerst eine kurze lokale Korrekturrunde:

1. `G-035` Rollentrennung vollständig und im Compose verdrahten.
2. `G-036` serverseitigen Fallback entfernen.
3. `G-037` Dokumentwidersprüche korrigieren.
4. `G-040` als Entscheidungspunkt markieren; keine stillschweigende Änderung.
5. Alle lokalen Tests und den API-Containertest erneut ausführen.
6. Danach erneuter kurzer Gerd-Gegencheck.

Erst wenn diese Punkte geschlossen sind, darf Roadmap-Phase 4 beginnen. Das produktive Foundation-Update bleibt ein separates CEO-Gate.
