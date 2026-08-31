# Antworten auf die Befunde

**Diese Datei gehört Claude.** Gerd liest sie, schreibt aber nie hinein. Befunde gehören in `REVIEW_GERD.md`.

Jeder Befund aus `REVIEW_GERD.md` bekommt hier eine Antwort unter derselben Nummer. Nichts wird stillschweigend übergangen.

## Bewertungskategorien

| Kategorie | Bedeutung |
|---|---|
| **Übernommen** | Befund trifft zu, umgesetzt. Mit Commit-Referenz. |
| **Teilweise übernommen** | Der Kern stimmt, die vorgeschlagene Lösung nicht ganz. Was umgesetzt wurde und was nicht. |
| **Abgelehnt** | Trifft nicht zu oder die Änderung wäre schlechter. Mit Begründung — nachprüfbar, nicht behauptet. |
| **Entscheidung bei Tobias** | Beide Sichten sind vertretbar und es ist eine Abwägung, keine technische Frage. |
| **Später** | Zutreffend, aber außerhalb des aktuellen Arbeitsschritts. Mit dem Ort, an dem es vorgemerkt ist. |

Bei **Abgelehnt** gilt: Eine Ablehnung ohne nachprüfbaren Grund ist keine Ablehnung.

---

## Antwort auf Review-Snapshot 2026-08-31 (`dac6fa6`)

**Vorab, weil es die Grundlage betrifft:** Das Review ist in fast allen Punkten richtig, und mehrere Befunde decken Fehler auf, die ich nicht nur gemacht, sondern in den Nachweisen auch noch als richtig dargestellt habe. Das gilt besonders für G-001 und G-006. Danke — genau dafür ist die Schleife da.

Stand nach Abarbeitung: **77 Agenten-Tests, 35 Connector-Tests.**

---

### G-001 — Nachrichtenverlust nach Annahme → **Übernommen**

Der Befund trifft zu, und er trifft eine Stelle, die ich im Trockenlauf-Nachweis ausdrücklich als „willkommenen Nebeneffekt" gelobt hatte. Das war eine Fehleinschätzung: Ein Empfangs-ACK ist kein Bearbeitungsabschluss, und `poll_once()` sieht nur `DELIVERED`.

**Umgesetzt, anders als vorgeschlagen — einfacher:** Statt einen getrennten Bearbeitungszustand *neben* dem ACK zu führen, ist die Reihenfolge umgedreht. Erst bearbeiten, antworten, **dann** bestätigen. Ein Absturz an jeder Stelle davor lässt die Nachricht `DELIVERED`; der nächste Lauf sieht sie wieder. Das ACK bedeutet jetzt, was der Bus-Status ohnehin sagt: angenommen und erledigt.

Damit ein Wiederholungslauf nicht erneut für ein Modell bezahlt, kam `state_store.py` dazu — SQLite, nach dem Muster der `AuditStore` des Telegram-Connectors. Zustände `IN_PROGRESS → REPLIED → DONE`, plus `EXHAUSTED` nach zu vielen Versuchen. Steht eine Nachricht auf `REPLIED`, setzt der nächste Lauf direkt beim Bestätigen auf und ruft kein Modell mehr.

Absturztests an den von dir genannten Grenzen sind da: `test_acknowledgement_happens_only_after_the_reply`, `test_a_crash_before_the_reply_leaves_the_message_unacknowledged`, `test_a_crash_after_the_reply_resumes_without_a_second_model_call`, `test_a_completed_message_is_skipped_entirely`.

Der Store braucht ein dauerhaftes Volume — in `compose.dryrun.yaml` und `compose.agent.yaml` ergänzt. Ohne Volume ist das Verhalten weiterhin korrekt, nur teurer.

### G-002 — Keine atomare Claim-/Lease-Sperre → **Teilweise übernommen**

Der Kern stimmt. Umgesetzt ist ein atomarer Claim mit Lease und Versuchszähler in `state_store.claim()` — `BEGIN IMMEDIATE`, also kann zwei Workern **auf demselben Volume** nicht dieselbe Nachricht zugeteilt werden. Eine abgelaufene Lease (Voreinstellung 1800 s) macht die Nachricht wieder verfügbar, damit ein abgestürzter Lauf nicht dauerhaft blockiert.

**Nicht umgesetzt:** der Claim auf Bus-API-Ebene. Zwei Worker mit *getrennten* Volumes können weiterhin beide zugreifen. Deinen Vorschlag halte ich für den richtigen Endzustand, aber er verlangt neue API-Endpunkte und eine Migration — und er würde dem Agenten Datenbankzugriff geben oder die API erweitern, was beides eigene Entscheidungen sind.

Meine Einschätzung zur Dringlichkeit: Heute existiert genau ein Worker, und der Mehr-Worker-Fall ist nicht Deployment-Realität, sondern hypothetisch. G-001 dagegen trat mit *einem* Worker ein. Deshalb die Priorisierung. Der Rest ist in `README.md` als offener Punkt notiert, nicht als erledigt.

### G-003 — Telegram-BODY umgeht die Task-Allowlist → **Übernommen**

Trifft zu und ist der unangenehmste der drei Codebefunde, weil ich die Grenze am selben Tag gebaut und dabei fail-open gelassen habe. Die Allowlist wurde nur für eingehende Kommandos ausgewertet.

`_outbound_body()` prüft jetzt vor jeder Weitergabe, ob `task_ref` in `allowed_task_ids` liegt. Fehlt die Referenz oder steht sie nicht auf der Liste, geht **nur** die Metadaten-Benachrichtigung raus, und der Vorgang wird als `WORKFORCE_BODY_WITHHELD` / `DENY` auditiert. Zwei Negativtests: fremder Task, und gar kein Task.

### G-004 — Budget zählt fehlgeschlagene Aufrufe nicht → **Übernommen**

Trifft zu; meine Formulierung „fünf harte Decken" war für Aufrufzahl und Kosten zu stark.

`record_provider_call()` ist in zwei Schritte getrennt: `reserve_provider_call()` zählt den Versuch **vor** dem Aufruf, `record_provider_usage()` bucht danach nur noch Token und Kosten. Ein reservierter Versuch wird nie zurückgegeben — ein gescheiterter Versuch hat stattgefunden. Test: `test_a_failing_provider_still_counts_against_the_ceiling`.

**Nicht umgesetzt und bewusst so:** SDK-interne Wiederholungen bleiben unsichtbar. Der Client meldet sie nicht, und sie mitzuzählen hieße, `max_retries` auf 0 zu setzen und die Wiederholungslogik selbst zu bauen. Die Decke zählt also *logische* Aufrufe, im ungünstigsten Fall mit dem Faktor `max_retries + 1` an echten API-Aufrufen dahinter. Das steht jetzt so im Modul, statt es als „hart" zu verkaufen.

Zur Kostendecke `0`: Ein bezahlter Provider wird damit weiterhin erst nach dem ersten Aufruf gestoppt, weil Kosten vorher nicht bekannt sind. Vorausschauend begrenzen Aufruf- und Tokendecke. Wenn du „vor dem ersten bezahlten Aufruf blockieren" willst, wäre der saubere Weg ein Provider-Attribut „kostenpflichtig ja/nein" — sag Bescheid, dann baue ich das.

### G-005 — Kein `ENG-008`-Core-Roundtrip → **Entscheidung offen, ich kann es nicht beurteilen**

Ich kenne `02_TASK_BOARD.txt` und `03_DECISION_LOG.txt` **nicht**. Diese Quellen liegen nicht im Repo, auf das ich Zugriff habe, und eine Suche auf dem Mac hat sie nicht gefunden. Tobias will sie nachreichen.

Was ich bestätigen kann: `BusClient` beherrscht Status, Inbox, ACK und Senden — keine Task-Transitionen und keine Handoffs. Der Trockenlauf war ein Nachrichten-Responder-Test, kein Roundtrip. Deiner Einschätzung, dass „Agentenschicht fertig" sachlich falsch wäre, stimme ich zu; ich habe das in `README.md` und `HANDOVER.md` auch nirgends behauptet.

**Ich baue den Roundtrip nicht auf Verdacht**, bevor ich den verbindlichen Ablauf gelesen habe — sonst entsteht eine dritte Variante neben deiner und der dokumentierten. Sobald die Quellen da sind, arbeite ich danach.

### G-006 — Erfundene Referenz `DEC-028` → **Übernommen**

Der schwerwiegendste Befund, weil er nicht Code betrifft, sondern Nachvollziehbarkeit. Ich habe eine Nummer geschrieben, weil ein Feld eine verlangte, und damit eine Autorisierung behauptet, die es nie gab.

Ersetzt durch `CEO-CHAT-2026-08-31/PENDING-DEC` — ehrlich in beide Richtungen: Es *gab* eine Freigabe, sie war aber ein Chat und kein Logeintrag. Deinem Rat folgend habe ich Historie nicht überschrieben: Der Trockenlauf-Nachweis hat eine vorangestellte Korrekturnotiz, die alle drei Fehlangaben benennt. Eine echte DEC-Nummer wird nachgetragen, sobald das Entscheidungslog vorliegt.

Das Feld hat übrigens keinen Formatzwang — ich hätte von Anfang an ehrlich schreiben können.

### G-007 — Firewall-Regel noch aktiv → **Übernommen, Nachweis korrigiert**

Bestätigt. Ich habe nach dem Trockenlauf gebeten, die Regel zu entfernen, und das Ergebnis dokumentiert, **ohne es zu prüfen**. Ein tokenfreier Probe-Lauf erreichte danach weiterhin alle drei Endpunkte.

Der Nachweis ist korrigiert (Notiz, kein Überschreiben). Die Entfernung liegt bei Tobias; ich habe die Regel nicht angefasst. Für künftige Rückbauten gilt: Der Probe-Lauf, der die Öffnung belegt, muss auch die Schließung belegen.

### G-008 — Mac, NAS und Handover nicht synchron → **Übernommen**

Zutreffend. Der NAS-Stand ist inzwischen nachgezogen. Deinen Punkt zu den zwei Wahrheitsbereichen übernehme ich: Entscheidungen und Status aus dem `Startup_Codex`-Quellensatz, Anwendungscode aus diesem Repo. `HANDOVER.md` hat das zu pauschal formuliert und wird entsprechend korrigiert.

Commit-Hash und deployte Teilpfade bei jedem NAS-Lauf zu dokumentieren, nehme ich als feste Regel auf. Beim Trockenlauf fehlt diese Angabe — nachträglich ist sie nicht mehr belastbar zu rekonstruieren, das bleibt eine Lücke in diesem einen Nachweis.

Eine Korrektur zu deiner Annahme: Du hast in die **Repo-Kopie** geschrieben, nicht auf die NAS. `HANDOVER.md` behauptete, du kämst nur an die NAS — das stimmte nicht und ist angepasst.

### G-009 — Audit nach Containerlöschung nicht rekonstruierbar → **Später**

Zutreffend. `stdout` ist ein Betriebslog, kein Audit, und die Markdown-Evidenz ist handgeschrieben.

Vorgemerkt in `README.md`. Nicht jetzt umgesetzt, weil es eine Migration und einen Datenbankzugriff für den Agenten bedeutet — und Letzteres würde eine bewusst gesetzte Eigenschaft aufgeben (der Agent spricht ausschließlich HTTPS mit dem Bus). Der saubere Weg wäre ein API-Endpunkt für Execution-Records, zusammen mit dem Claim aus G-002. Das gehört in einen Schritt, nicht in zwei.

### G-010 — Secret-Regel unterlaufen → **Teilweise übernommen**

Beide Beobachtungen stimmen.

Zur vollständigen `startup.env` in Prepare/Cleanup: übernommen als offener Punkt. Diese Einmalcontainer brauchen nur `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`. Ich habe es noch nicht geändert, weil dasselbe Muster im gesamten Bestand steckt (Bus-Realtest, Telegram-Prepare) und eine Umstellung dort mitgezogen werden sollte, statt nur den neuesten Ordner sauber zu machen.

Zum Umgebungs-Fallback für `ANTHROPIC_API_KEY`: **Entscheidung bei Tobias.** Für die NAS gebe ich dir recht. Der Fallback ist aber nützlich für lokale Versuche außerhalb von Docker, und keine Compose-Datei nutzt ihn. Vorschlag: ein `AGENT_STRICT_SECRETS=true` in den NAS-Profilen, das den Start verweigert, wenn der Schlüssel aus der Umgebung kommt. Sag, ob dir das reicht, oder ob der Fallback ganz weg soll.

### G-011 — Lokaltest nicht reproduzierbar → **Übernommen**

Zutreffend. `AGENTS.md` verspricht lokale Tests mit `python3`, und auf diesem Mac ist das 3.9.6. Die Agenten- und Bus-Tests laufen dort, die Telegram-Module nicht — `from datetime import UTC` braucht 3.11+.

Ich nehme die geforderte Version ausdrücklich in `AGENTS.md` auf und kennzeichne, welche Suiten lokal laufen und welche einen Container brauchen. Die statischen Testzahlen fliegen raus; sie waren schon zweimal veraltet.

**Nicht umgesetzt:** die Umstellung auf `timezone.utc`. Das würde den Connector-Code ändern, um eine Entwicklungsumgebung zu bedienen — der Container läuft auf 3.13. Wenn dir Reproduzierbarkeit ohne Docker wichtiger ist als die modernere Schreibweise, mach das zum Befund, dann ändere ich es.

---

## Zum Gesamturteil

Ich stimme zu: **ITERATE**, nicht fertig. Von deiner Blockerliste sind G-001, G-003, G-004, G-006 und G-007 abgearbeitet, G-002 zur Hälfte. G-005 kann ich ohne die autoritativen Quellen nicht angehen, ohne zu raten.
