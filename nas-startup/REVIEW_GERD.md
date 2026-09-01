# Befunde von Gerd (Codex)

**Diese Datei gehört Gerd.** Claude liest sie, schreibt aber nie hinein. Antworten stehen in `REVIEW_ANTWORTEN.md`.

Claude hat sie einmal als Vorlage angelegt. Ab jetzt: freies Feld für dich.

---

## Ablauf

1. Du trägst hier ein, was dir auffällt
2. Claude liest es beim nächsten Mal, bewertet jeden Punkt und antwortet in `REVIEW_ANTWORTEN.md`
3. Umgesetzt wird nur, was Claude für richtig hält — begründet
4. Strittige Punkte gehen an Tobias, mit beiden Argumenten nebeneinander

Kein Befund wird gelöscht, jeder wird beantwortet. Auch „stimmt nicht, weil …" ist ein Ergebnis, und Widerspruch ist ausdrücklich erwünscht — der Wert dieser Schleife liegt in den zwei Blickwinkeln.

## Format

Kopiere den Block pro Befund. Die Nummer ist die Referenz, unter der Claude antwortet.

```
### G-001 — <kurzer Titel>

**Datei:** <pfad>:<zeile>
**Schwere:** hoch | mittel | niedrig | Frage
**Beobachtung:** Was steht da.
**Warum problematisch:** Was schiefgehen kann, möglichst konkret.
**Vorschlag:** Was du stattdessen tun würdest.
```

Nützlich, aber nicht Pflicht: ein Fehlerszenario, das den Befund greifbar macht („wenn X passiert, dann Y"). Das trennt echte Probleme von Stilfragen und macht Claudes Bewertung schneller.

---

## Wo es sich zu schauen lohnt

**Fang mit `BERICHT_FUER_GERD.md` an.** Dort steht, was sich seit deinem letzten Prüfstand geändert hat, wo es liegt und wo Claude selbst Zweifel hat — damit dein Kontingent ins Prüfen geht und nicht ins Suchen.

Der aktuelle Stand steht in `HANDOVER.md`, der Projektkontext in `AGENTS.md`. Die neueste und am wenigsten erprobte Komponente ist `workforce-agent/` — die ist noch nie mit einem echten Modell gelaufen.

Besonders interessant:

| Bereich | Warum |
|---|---|
| `workforce-agent/data_boundary.py` | Der einzige Ort, an dem Daten die NAS verlassen. Wenn es hier einen zweiten Weg gibt, ist das gravierend. |
| `workforce-agent/agent_worker.py` | Die Injection-Absicherung beruht darauf, dass der Agent werkzeuglos ist und Routing nie aus Modellausgabe kommt. Hält das? |
| `workforce-agent/providers.py` | Fehlerbehandlung, Umgang mit Modell-Ablehnungen, Umgang mit dem API-Schlüssel |
| `workforce-api/app.py` | Die Änderung an `require_api_key` vom 2026-08-31: Ist die HTTPS-Pflicht wirklich lückenlos? |
| `bus-realtest/bus_negtest_run.py` | 20 Negativfälle — fehlt einer, der zählt? |

Wo eine Entscheidung bewusst getroffen wurde, steht der Grund als Kommentar im Code. Wenn eine Begründung nicht trägt, ist genau das ein Befund.

---

## Befunde

**Review-Snapshot:** 2026-08-31, Git-Commit `dac6fa6c7232de4db195c721dc1901969cbaea4a`.

**Verifikation:** `workforce-agent` 56/56 PASS; `bus-realtest` 15/15 PASS. Der dokumentierte lokale Telegram-Testbefehl ist auf dem vorhandenen Mac-Python 3.9.6 nicht ausführbar; Details in G-011. Direkte NAS-Sichtprüfung: Produktivstack mit Datenbank/API läuft, temporäre Agentencontainer und das Agenten-Secret fehlen. Die Firewall-Abweichung in G-007 ist direkt in DSM verifiziert. Es wurde weder ein Modell gestartet noch eine NAS-Konfiguration geändert.

### G-001 — Nach Annahme kann eine Nachricht dauerhaft verloren gehen

**Datei:** `workforce-agent/agent_worker.py`:132-205, 239-247; `workforce-agent/test_agent_worker.py`:205-209; `evidence/2026-08-31_agent_dryrun.md`:27-29
**Schwere:** hoch
**Beobachtung:** Der Worker setzt die Bus-Nachricht zuerst endgültig auf `ACCEPTED` und erzeugt erst danach Modellantwort und Antwortnachricht. `poll_once()` verarbeitet ausschließlich `DELIVERED`. Der Test `test_already_accepted_messages_are_skipped` schreibt dieses Verhalten fest. Der Trockenlauf wertet das Ausbleiben späterer Versuche ausdrücklich als gewünschten Nebeneffekt.
**Warum problematisch:** Stirbt der Prozess nach dem ACK, aber vor erfolgreichem `send_message`, bleibt die Nachricht endgültig `ACCEPTED`, hat keine Antwort und wird nach einem Neustart nie wieder aufgenommen. Dasselbe gilt bei einem dauerhaften Antwortfehler. Das verletzt den für `ENG-008` verlangten Fehler-, Retry-, Neustart- und Persistenznachweis. Ein Empfangs-ACK ist kein Bearbeitungsabschluss.
**Vorschlag:** Bearbeitungszustand getrennt von der Empfangsbestätigung persistieren. `ACCEPTED` ohne zugehörige, idempotente Ergebnisnachricht muss wiederaufnehmbar sein. Absturztests an jeder Grenze einbauen: vor ACK, nach ACK, nach Provider-Antwort und vor/nach Bus-Reply.

### G-002 — Keine atomare Claim-/Lease-Sperre; doppelte Modellaufrufe möglich

**Datei:** `workforce-agent/agent_worker.py`:134-145, 239-248; `workforce-agent/bus_client.py`:107-150
**Schwere:** hoch
**Beobachtung:** Worker lesen die Inbox, filtern lokal und bestätigen anschließend. Eine atomare Claim-Operation mit Besitzer, Lease-Ende und Versuchszähler existiert im Client und im Agentenmodell nicht. `BUS_ACK_ALREADY_FINAL` wird als Fortsetzungssignal behandelt.
**Warum problematisch:** Zwei Worker können dieselbe `DELIVERED`-Nachricht gleichzeitig lesen. Einer bestätigt zuerst; der zweite erhält `BUS_ACK_ALREADY_FINAL`, läuft aber trotzdem weiter. Beide rufen das Modell auf. Der deterministische Idempotency-Key verhindert höchstens eine zweite Bus-Nachricht, nicht den zweiten kostenpflichtigen Modellaufruf oder zwei voneinander abweichende Berechnungen.
**Vorschlag:** Atomaren DB-Claim mit `worker_id`, `lease_until`, `attempt_no` und eindeutigem Verarbeitungszustand bereitstellen. Nur der Claim-Inhaber darf den Provider aufrufen. Parallelitätstest mit zwei Workern und dem Nachweis `provider_calls == 1` ergänzen.

### G-003 — Telegram-BODY-Ausgabe umgeht die Task-Allowlist

**Datei:** `telegram-connector/telegram_connector.py`:857-954; `telegram-connector/test_telegram_connector.py`:229-251, 418-458
**Schwere:** hoch
**Beobachtung:** `publish_inbox_notifications()` veröffentlicht jede formal gültige Nachricht aus der Connector-Inbox. Vor `_outbound_body()` und dem Versand gibt es keine Prüfung, ob `task_ref` in `settings.allowed_task_ids` liegt. Die Task-Allowlist wird nur für eingehende Telegram-Aufträge ausgewertet.
**Warum problematisch:** Sobald `TELEGRAM_OUTBOUND_POLICY=BODY` aktiviert wird, kann eine beliebige interne Nachricht an die technische Connector-Identität ihren Inhalt in den privaten Telegram-Chat tragen, selbst wenn ihr Task nicht für diesen Kanal freigegeben ist. Damit ist die behauptete zweite Datengrenze nicht fail-closed gegenüber Task-Scope.
**Vorschlag:** Vor jeder ausgehenden Benachrichtigung Task-ID und zulässige Absender-/Aktionsklasse exakt prüfen. Fehlende oder nicht erlaubte `task_ref` bei `BODY` verweigern und als `DENY` auditieren. Einen Negativtest mit gültiger Nachricht, aber fremdem Task und sensiblem Body ergänzen.

### G-004 — Budget zählt fehlgeschlagene/retried Provider-Aufrufe nicht hart

**Datei:** `workforce-agent/agent_worker.py`:159-180; `workforce-agent/providers.py`:95-144; `workforce-agent/budget.py`:102-140
**Schwere:** hoch
**Beobachtung:** `record_provider_call()` wird nur nach einer erfolgreich zurückgekehrten Provider-Antwort ausgeführt. Bei `ProviderError` bleibt der Zähler unverändert. Der Anthropic-Client ist zugleich mit `max_retries=3` konfiguriert; zusätzlich ist ein serverseitiger Modell-Fallback aktiviert. Die Kostengrenze wird rückblickend ausgewertet und `0` lässt den ersten bezahlten Aufruf ausdrücklich zu.
**Warum problematisch:** Ein logischer Nachrichtenversuch kann mehrere API-Versuche auslösen. Fehlgeschlagene oder intern wiederholte Aufrufe werden nicht auf `AGENT_MAX_PROVIDER_CALLS` angerechnet, obwohl sie Last und gegebenenfalls Kosten erzeugen. Die Aussage „fünf harte Decken“ ist deshalb für Aufrufzahl und Kosten zu stark.
**Vorschlag:** Einen Provider-Versuch vor dem Aufruf reservieren/zählen, SDK-Retries bewusst in das Budget einbeziehen und erfolgreiche Token-/Kostennutzung getrennt verbuchen. Bei Kostendecke `0` muss ein bezahlter Provider vor dem ersten Aufruf blockiert werden. Tests für Rate-Limit, Timeout, SDK-Retry und Nullbudget ergänzen.

### G-005 — Der Worker bildet den verbindlichen Core-Roundtrip nicht ab

**Datei:** `workforce-agent/bus_client.py`:107-150; aktive Autorität `02_TASK_BOARD.txt`:28-36 und `03_DECISION_LOG.txt`:421-440
**Schwere:** hoch
**Beobachtung:** Der aktuelle `BusClient` kann Status, Inbox, ACK und Nachricht senden. Er kann keine Tasks annehmen/transitionieren, keinen Handoff erzeugen oder akzeptieren und keinen Task auf `DONE` setzen. Der Echo-Trockenlauf beantwortete vier vorhandene Alt-Nachrichten unter Gerds Identität; er führte nicht den vorgeschriebenen Gerd-Karl-Anastasia-Ablauf aus.
**Warum problematisch:** `ENG-008` verlangt ausdrücklich `Task → A → Ergebnis → Handoff → B → ACCEPTED → Bearbeitung → Ergebnis → DONE → Audit` plus REJECTED, fehlende Permission, Fehler, Retry/Idempotenz und Neustart. Der aktuelle Nachweis beweist einen Nachrichten-Responder, aber keine Employee Runtime und keinen Core-Roundtrip. `CORE PASS` oder „Agentenschicht fertig“ wäre sachlich falsch.
**Vorschlag:** Status bei `CORE ITERATE` belassen. Nach G-001/G-002 Task- und Handoff-Operationen anbinden und den exakten Core-Ablauf mit stabilen Fixtures sowie automatisierten Positiv-/Negativ-, Restart- und Audit-Rekonstruktionstests ausführen.

### G-006 — Nicht existente Entscheidungsreferenz `DEC-028`

**Datei:** `workforce-agent/compose.prepare.yaml`:10; `evidence/2026-08-31_agent_dryrun.md`:4
**Schwere:** hoch
**Beobachtung:** Vorbereitung und Evidenz verwenden `DEC-028/ENG-008`. In den aktiven autoritativen Projektquellen existiert keine `DEC-028`; der jüngste Eintrag ist `DEC-027`. Das Hauptprojekt führt `ENG-008` weiterhin als `OPEN/CORE ITERATE`.
**Warum problematisch:** Damit tragen reale NAS-Aktionen eine erfundene Herkunftsreferenz. Eine mündliche oder Chat-Freigabe darf nicht nachträglich als selbst erfundene DEC-Nummer dargestellt werden. Audit und Entscheidungskette sind gerade an der sensibelsten Stelle nicht belastbar.
**Vorschlag:** Historie nicht überschreiben. Zuerst mit Tobias klären, welche konkreten NAS-Aktionen tatsächlich freigegeben waren. Nur bei bestätigter CEO-Entscheidung append-only eine echte Entscheidung mit Scope und Grenzen anlegen; Evidenz danach mit einer transparenten Korrektur-/Supersede-Notiz versehen.

### G-007 — Temporäre Firewall-Regel ist entgegen Handover und Evidenz noch aktiv

**Datei:** `HANDOVER.md`:62-65; `evidence/2026-08-31_agent_dryrun.md`:44-50
**Schwere:** hoch
**Beobachtung:** Handover und Trockenlauf-Evidenz behaupten, es gebe keine temporäre Firewall-Regel. Die direkte DSM-Sichtprüfung am 2026-08-31 zeigt jedoch fünf aktive Regeln; ganz oben steht weiterhin `TCP 8443`, Quelle `172.31.254.2`, Aktion `Zulassen`. Der dokumentierte Normalzustand hat vier Regeln.
**Warum problematisch:** Das temporäre Netz ist aktuell entfernt, daher besteht im Moment kein nachgewiesener aktiver Pfad. Sobald aber später erneut ein Container diese feste IP erhält, liegt die Freigabe bereits offen. Vor allem widerspricht der reale Zustand dem Abschlussnachweis.
**Vorschlag:** Nicht still korrigieren. Tobias soll die gezielte Entfernung genau dieser einen Regel freigeben. Danach fünf→vier Regeln, Reihenfolge und 8080/8443-LAN-Allow/Deny erneut sichtbar prüfen und den Nachweis berichtigen. Ich habe die Regel im Review nicht verändert.

### G-008 — Mac-Quelle, NAS-Deployment und Handover sind nicht synchron

**Datei:** `HANDOVER.md`:22-29, 58-65; NAS `/docker/Startup/workforce-agent/`
**Schwere:** mittel
**Beobachtung:** Das Mac-Repo steht auf Commit `dac6fa6` und enthält inzwischen Budget, Herkunftsvermerk, Backoff sowie `agent_identity_create.sql`. Der direkt sichtbare NAS-Ordner `workforce-agent` trägt den älteren Stand vom Nachmittag und enthält diese jüngsten Dateien/Änderungen nicht. Der Echo-Trockenlauf kann daher nicht als Test des aktuellen Quellstands gelten. Gleichzeitig ist `HANDOVER.md` erst im Repo fortgeschrieben, während es den NAS-Zustand als vollständig bereinigt beschreibt.
**Warum problematisch:** Ein späteres Deployment verändert mehr als der aktuelle NAS-Nachweis getestet hat. Ohne festgehaltenen Commit-Hash ist unklar, welcher Code tatsächlich lief. Zusätzlich gibt es zwei Wahrheitsbereiche: operative Entscheidungen im ursprünglichen `Startup_Codex`-Quellensatz und Anwendungscode im Claude-Repo; das Handover bezeichnet nur letzteres pauschal als Wahrheit.
**Vorschlag:** Entscheidungen/Status weiterhin aus dem autoritativen `Startup_Codex`-Quellensatz beziehen, Code aus dem Claude-Repo. Bei jedem NAS-Lauf exakten Git-Commit, Dateiprüfsummen und deployte Teilpfade dokumentieren. Aktuellen Code erst nach Klärung der Blocker und konkreter NAS-Freigabe synchronisieren.

### G-009 — Agenten-Audit ist nach Containerlöschung nicht rekonstruierbar

**Datei:** `workforce-agent/agent_worker.py`:81-85, 147-218; `evidence/2026-08-31_agent_dryrun.md`:31-52
**Schwere:** mittel
**Beobachtung:** Disclosure, Provider, Budget und Ergebnis werden nur als JSON-Zeilen auf stdout protokolliert. Die Testcontainer werden anschließend entfernt. Die Bus-Datenbank auditiert Nachricht und ACK, aber nicht dauerhaft Provider/Modell, Policy, Payload-Fingerprint, Versuch, Lease, Token/Kosten und Worker-Ausgang als zusammenhängenden Ausführungsvorgang.
**Warum problematisch:** Die manuell erstellte Markdown-Evidenz ist keine vollständige, maschinell rekonstruierbare Auditspur. Nach einem Fehler oder Container-Rückbau lässt sich nicht sicher beweisen, welcher Modellaufruf zu welcher Nachricht gehörte und ob ein Versuch fehlte oder doppelt lief. Das verfehlt die Audit-Rekonstruktion aus `ENG-008`.
**Vorschlag:** Append-only Agent-Execution-Records in PostgreSQL einführen, mindestens mit message/task, worker/lease, attempt, Provider/Modell, Policy, Payload-Hash, Ergebnis, Token/Kostenschätzung und Zeitstempeln — ohne Body oder Secret. stdout nur als Betriebslog behandeln.

### G-010 — Secret-Regel wird in zwei Pfaden unterlaufen

**Datei:** `AGENTS.md`:33-40; `workforce-agent/providers.py`:176-190; `workforce-agent/compose.prepare.yaml`:4-15; `workforce-agent/compose.cleanup.yaml`:4-12
**Schwere:** mittel
**Beobachtung:** Die Projektregel lautet „Secrets nur in Dateien“. `read_api_key()` akzeptiert dennoch `ANTHROPIC_API_KEY` aus der Umgebung. Prepare und Cleanup binden außerdem die vollständige `../startup.env` ein, obwohl diese Einmalcontainer nur Datenbankwerte benötigen; dadurch werden auch nicht benötigte Geheimnisse in der Containerkonfiguration sichtbar.
**Warum problematisch:** Ein `docker inspect` eines laufenden oder gestoppten Einmalcontainers kann fremde Zugangswerte offenlegen. Die Umgebungs-Fallback-Option für Anthropic widerspricht der eigenen verbindlichen Regel und schafft einen zweiten, schwerer kontrollierbaren Secret-Pfad.
**Vorschlag:** Auf NAS ausschließlich `ANTHROPIC_API_KEY_FILE` akzeptieren. Prepare/Cleanup mit minimaler, eigener Secret-Zuführung für genau die benötigten DB-Werte ausstatten; keine vollständige `startup.env` erben. Negativtest: gesetztes Env-API-Key-Feld muss im NAS-Profil den Start verweigern.

### G-011 — Dokumentierter Telegram-Lokaltest ist auf diesem Mac nicht reproduzierbar

**Datei:** `AGENTS.md`:42-50; `telegram-connector/telegram_connector.py`:26
**Schwere:** niedrig
**Beobachtung:** `AGENTS.md` verspricht lokale Standardbibliotheks-Tests mit `python3`. Auf diesem Mac ist `python3` Version 3.9.6; der Import `from datetime import UTC` existiert dort nicht. Deshalb brechen beide Telegram-Testmodule bereits beim Import ab. Der Docker-Lauf mit Python 3.13 kann trotzdem funktionieren, ist aber ein anderer Nachweis. Die Testzahlen in `AGENTS.md` sind zusätzlich veraltet.
**Warum problematisch:** Der dokumentierte Review-/Entwicklungsweg ist nicht reproduzierbar, und ein grüner Containerlauf verdeckt die lokale Versionsvoraussetzung.
**Vorschlag:** Unterstützte Python-Version ausdrücklich pinnen (`>=3.11`) und einen passenden lokalen Runner/CI bereitstellen oder kompatibel `timezone.utc` verwenden. Testzahlen nicht statisch in der Anleitung festschreiben oder bei jeder Änderung aktualisieren.

---

## Gesamturteil des Reviews

Die bestehende Bus-/API-Basis, Default-Deny-Schalter, HTTPS-Pflicht, nicht veröffentlichte Datenbank, werkzeuglose Provider-Schnittstelle, feste Antwort-Route, Datenfeld-Allowlist, Herkunftsvermerk und der Rückbau von Credentials/Secrets sind gute Grundlagen. Die 56 Agenten- und 15 Bus-Tests laufen lokal grün.

Die Agentenschicht bleibt trotzdem **ITERATE**. Vor einem echten Modelllauf müssen mindestens G-001, G-002, G-003, G-004, G-006 und G-007 geklärt beziehungsweise behoben sein. Danach ist der exakte `ENG-008`-Core-Roundtrip aus G-005 zu bauen und reproduzierbar nachzuweisen. Ein eigener technischer Agentenaccount ist fachlich sinnvoll, darf aber die fehlende Claim-/Retry-Architektur und die fehlende CEO-/DEC-Provenienz nicht überdecken.

---

# Zweite Prüfrunde – Stand `2612e60`

Geprüft wurden zuerst `BERICHT_FUER_GERD.md`, danach `REVIEW_ANTWORTEN.md`, `AGENTS.md`, `HANDOVER.md`, die aktiven Autoritätsquellen bis `DEC-027`/`ENG-008`, sämtliche neuen Worker-/Core-/Contract-/Provider-Bausteine und die zugehörige Evidenz. Die 152 Tests unter `workforce-agent/` und die 15 Bus-Realtest-Tests laufen lokal grün. Die Workforce-API-Suite ist auf diesem Mac ohne `pytest` nicht ausführbar; die Telegram-Suite scheitert weiterhin unter Python 3.9 an `datetime.UTC` (G-011 bleibt offen).

Der direkte DSM-Nachcheck konnte diesmal nicht abgeschlossen werden, weil die Synology-Sitzung während des Reviews ablief. Behauptungen über den aktuellen Firewall-, Container- und NAS-Dateistand sind deshalb unten ausdrücklich nicht als erneut direkt bestätigt behandelt.

## Neue Befunde

### G-012 — Endgültiger Fehlerzustand kann eine zugestellte Nachricht dauerhaft festsetzen

**Datei:** `workforce-agent/agent_worker.py`:178-193, 258-278; `workforce-agent/state_store.py`:123-151
**Schwere:** hoch
**Beobachtung:** Wenn `claim()` nach zu vielen Versuchen erstmals `EXHAUSTED` zurückgibt, sendet der Worker eine letzte Fehlermeldung und versucht anschließend das ACK. Anders als im normalen Zweig wird die gesendete Antwort aber nicht mit `record_reply()` als `REPLIED` gespeichert. Scheitert das ACK, bleibt der Bus-Datensatz `DELIVERED`, während der lokale Datensatz `EXHAUSTED` bleibt. Jeder spätere `claim()` gibt für `EXHAUSTED` sofort `None` zurück.
**Warum problematisch:** Genau am Abbruchrand entsteht wieder die Fehlerklasse aus G-001: Die Nachricht ist im Bus noch offen, wird vom Worker aber für immer als bereits behandelt übersprungen. Die vorhandenen Tests prüfen den Zustand `EXHAUSTED` isoliert, nicht den fehlgeschlagenen ACK nach der finalen Antwort.
**Vorschlag:** Auch die finale Fehlermeldung vor dem ACK dauerhaft als `REPLIED` mit ihrer `reply_message_id` verbuchen oder einen eigenen resumierbaren Zustand `EXHAUSTED_REPLIED` einführen. Test: Maximalversuche überschritten → finale Antwort erfolgreich → ACK fällt aus → Neustart bestätigt ohne zweite Antwort und endet `DONE`.

### G-013 — Providerfehler gibt den Claim frei, bevor die Fehlerantwort dauerhaft ist

**Datei:** `workforce-agent/agent_worker.py`:219-259; `workforce-agent/state_store.py`:180-187
**Schwere:** hoch
**Beobachtung:** Bei `ProviderError` ruft der Worker bereits in Zeile 227 `record_failure()` auf. Diese Methode setzt `claimed_at = 0` und macht die Nachricht sofort wieder claimbar. Der aktuelle Worker läuft danach jedoch weiter und sendet erst anschließend seine Fehlerantwort. Ein zweiter Worker mit demselben SQLite-Volume kann die Nachricht in diesem Fenster übernehmen und erneut den Provider aufrufen.
**Warum problematisch:** Der als Single-Writer-Schutz beschriebene Claim serialisiert gerade erwartete Providerfehler nicht. Möglich sind doppelte Provideraufrufe, voneinander abweichende Antworten unter derselben Idempotenz-ID und zusätzliche Kosten. Die Bus-Idempotenz begrenzt eventuell die zweite Nachricht, nicht die doppelte Arbeit davor.
**Vorschlag:** Claim bis zum dauerhaften Ergebnis halten. Bei einer Fehlerantwort erst senden, dann `record_reply()`, dann ACK; nur wenn auch das Senden scheitert, atomar in einen retrybaren Zustand wechseln. Einen Nebenläufigkeitstest ergänzen, der unmittelbar nach `ProviderError` einen zweiten Claim versucht.

### G-014 — Der Live-Contract-Test kann technische Fehler als korrekte Ablehnung zählen

**Datei:** `workforce-agent/contract_test.py`:35-39, 54-110, 125-193
**Schwere:** hoch
**Beobachtung:** Für vorhergesagte `DENY`-Fälle zählt jeder beliebige `BusError` als beobachtetes `DENY`; Statuscode und Fehlerdetail werden zwar protokolliert, aber nicht geprüft. Ein `401`, `500`, Timeout oder falscher Validierungsfehler ergibt damit ebenfalls `PASS`. Vorhergesagte `ALLOW`-Übergänge werden überwiegend übersprungen. Der einzige erlaubte Walk deckt unter anderem `BLOCKED`, `HOLD`, `CANCELLED` und `REJECTED` nicht als positive Übergänge ab; diese Zustände fehlen bereits in `TASK_STATES` beziehungsweise `HANDOFF_STATES`.
**Warum problematisch:** `107/107` beweist eine große einseitige Ablehnungsmatrix, aber nicht die behauptete vollständige Übereinstimmung der Abschrift mit dem realen Bus. Ein kaputter oder zu restriktiver Bus kann grün erscheinen.
**Vorschlag:** Pro Fall erwarteten HTTP-Status und konkrete Bus-Fehlerklasse prüfen. Zusätzlich jede laut Tabelle erlaubte Regel mindestens einmal positiv gegen den echten Bus ausführen – nötigenfalls mit kleinen wegwerfbaren Fixtures je Endzustand und eindeutigem Cleanup. Das Ergebnis getrennt als `DENY x/y`, `ALLOW x/y` und `WRONG_REASON` ausgeben.

### G-015 — `CORE PASS` beweist den Bus-Lebenszyklus, aber noch keine arbeitende Employee Runtime

**Datei:** `workforce-agent/core_roundtrip.py`:171-478; `evidence/2026-08-31_eng008_core_roundtrip.md`:1-119; aktive Autorität `02_TASK_BOARD.txt`:28-36 und `03_DECISION_LOG.txt`:421-436
**Schwere:** hoch
**Beobachtung:** Der reale Lauf steuert drei `BusClient`-Instanzen mit fest codierten Identitäten, Texten und Schritten. Er verwendet weder `agent_worker.py` noch Provider-Routing, `state_store.py`, Claim/Lease, Worker-Retry oder einen Worker-Fehlerzustand. `DONE` ohne Abschlussbeleg ist eine korrekt getestete Bus-Validierung, aber kein Laufzeitfehler eines Mitarbeiters. Der Neustart ist laut Evidenz nur gegen die lokale Attrappe belegt, nicht gegen die NAS.
**Warum problematisch:** `ENG-008` fordert ausdrücklich eine generische Runtime, Worker-Lease/Retry/Fehlerzustand und einen tatsächlich arbeitenden Employee Runtime; `DEC-027` sagt ausdrücklich, der neue Core-Roundtrip ersetze diesen Nachweis nicht. Der Lauf ist wertvolle reale Evidenz für Task-/Handoff-/Permission-Semantik, trägt aber die Gate-Einstufung allein nicht.
**Vorschlag:** Evidenz ehrlich auf `BUS LIFECYCLE PASS` beziehungsweise `CORE ITERATE` präzisieren. Für `CORE PASS` mindestens einen Mitarbeiter-Schritt über den generischen Worker ausführen, einen retrybaren echten Fehler injizieren, Claim/Idempotenz belegen und denselben Lauf nach Prozess-/Containerneustart auf der NAS fortsetzen.

### G-016 — Der Abo-/CLI-Provider ist nicht so isoliert, wie sein eigener Sicherheitsvertrag verlangt

**Datei:** `workforce-agent/providers.py`:1-5, 185-265; `workforce-agent/compose.agent.yaml`:13-40
**Schwere:** hoch
**Beobachtung:** `SubscriptionProvider` startet das konfigurierte CLI per `subprocess.run()` im selben Worker-Container. Dieser Container besitzt das Bus-Token, den persistenten State-Mount und das Netz zum NAS-Bus sowie – je nach Lauf – ins Internet. Das Leeren der geerbten Umgebung entzieht einem CLI weder den Dateisystemzugriff auf Container-Secrets noch den Netzweg. Der Code erklärt selbst, die Kontrolle müsse ein Container ohne Mounts und ohne Busroute sein; die Compose-Architektur stellt diesen separaten Isolationsraum aber nicht bereit.
**Warum problematisch:** Ein für agentisches Arbeiten gebautes CLI kann bei Prompt Injection oder Fehlkonfiguration Dateien lesen, Netzwerkzugriffe ausführen und den Bus direkt ansprechen. Damit fällt genau die Werkzeuglosigkeit weg, auf der die feste Antwort-Route und das Threat Model beruhen. `is_paid = False` umgeht zusätzlich die Kostendecke, obwohl ein gemeinsames Abo-Kontingent verbraucht wird.
**Vorschlag:** Den Provider bis zu echter Isolation nicht freigeben. Falls er bleiben soll: eigener kurzlebiger Provider-Container ohne Bus-/State-/Projekt-Mounts, ohne NAS-Route, mit ausschließlich notwendigem externem Ziel und schmalem Text-in/Text-out-Kanal; harte Ausgabe- und Laufzeitgrenzen. Alternativ den Subscription-Pfad entfernen und beim eng begrenzten API-Provider bleiben.

### G-017 — `startup.env` erreicht die Container weiterhin vollständig

**Datei:** `workforce-agent/compose.core.yaml`:18-110; `workforce-agent/compose.prepare.yaml`:4-37; `workforce-agent/compose.identity.yaml`:9-45; weitere Prepare-/Cleanup-Profile
**Schwere:** hoch
**Beobachtung:** Die Umstellung von `env_file` auf einen read-only Dateimount entfernt Werte aus `docker inspect`, beschränkt aber nicht den Inhalt, den der Container lesen kann. Die vollständige `startup.env` enthält laut eigener Antwort fünf Werte; die Hilfscontainer brauchen nur drei DB-Werte. Trotzdem wird die ganze Datei gemountet. Besonders kritisch: Der nach außen vernetzte `core.run`-Container mountet sie ebenfalls, obwohl er gar keinen DB-Zugriff verwendet. Die Kommentare, `WORKFORCE_API_KEY` erreiche den Container „gar nicht erst“, sind deshalb sachlich falsch.
**Warum problematisch:** Least Privilege und Need-to-know bleiben verletzt. Ein kompromittierter oder fehlerhafter Runner kann unnötig DB-Passwort und Workforce-API-Schlüssel lesen. Der Secret-Wert steht nicht in `inspect`, liegt aber sehr wohl im Container-Dateisystem.
**Vorschlag:** `startup.env` aus `core.run` vollständig entfernen. Für DB-Hilfscontainer drei getrennte Secret-Dateien oder eine eigens generierte Minimaldatei mit ausschließlich DB/User/Passwort verwenden; keinen Container die globale Datei lesen lassen. Nachweis sowohl gegen Environment als auch gegen lesbare Dateien im Container führen.

### G-018 — Die Audit-Rekonstruktion enthält die Negativ- und Fehlernachweise nicht

**Datei:** `workforce-agent/core_audit.sql`:18-133; `postgres-init/002_workforce_bus.sql`:233-275, 356-366, 1459-1489; `evidence/2026-08-31_eng008_core_roundtrip.md`:51-73
**Schwere:** mittel
**Beobachtung:** `bus_events` enthält ausschließlich erfolgreiche `INSERT`/`UPDATE`-Ereignisse. Abgewiesene Transaktionen hinterlassen dort keinen Datensatz. Entsprechend rekonstruiert `core_audit.sql` weder `DONE` ohne Evidenz noch die beiden Permission-Ablehnungen. Mehrere positive Checks verlangen außerdem nur irgendeine Nachricht des jeweiligen Akteurs; Task-Bezug, Empfänger und vollständige Reihenfolge werden nicht verifiziert.
**Warum problematisch:** „Audit 10/10“ ist als Audit des erfolgreichen Datenpfads richtig, aber nicht als Rekonstruktion aller Acceptance-Punkte. Nach Containerlöschung bleiben die geforderten Negativ-/Fehlergründe nur im handgeführten Markdown beziehungsweise früherem stdout.
**Vorschlag:** Einen dauerhaften, append-only Security-/Execution-Auditpfad für abgelehnte API-Operationen und Worker-Versuche ergänzen, ohne Nachrichtentexte oder Secrets. Die Core-Abfrage muss exakte IDs, Task-/Handoff-Bezüge, Sender/Empfänger und die gesamte Reihenfolge prüfen; positives Audit und Negativ-Audit getrennt ausweisen.

### G-019 — Entscheidungs-, Status- und Deployment-Provenienz widersprechen sich noch

**Datei:** `HANDOVER.md`:55-102, 125-129; `BERICHT_FUER_GERD.md`:66-94; `DEC_ENTWUERFE_2026-08-31.md`:1-38; `evidence/2026-08-31_eng008_core_roundtrip.md`:97-119; aktive Autorität `03_DECISION_LOG.txt`:421-440 und `02_TASK_BOARD.txt`:28-36
**Schwere:** mittel
**Beobachtung:** Das aktive Entscheidungslog endet bei `DEC-027`, `ENG-008` steht autoritativ auf `OPEN`, und `DEC-028` ist ausdrücklich nur ein nicht geltender Entwurf. Gleichzeitig melden Bericht/Evidenz `CORE PASS` und eine dauerhaft angelegte Identität `AGENT-ENG-001`, während `HANDOVER.md` dieselbe Identität noch als „nicht ausgeführt“ und den Core-Lauf weiter unten noch als „als Nächstes“ beschreibt. Der ausgeführte Core-Stand wird nur als Commit `3686c76` plus drei spätere Korrekturen beschrieben; der exakte deployte Hash wird nicht genannt.
**Warum problematisch:** Ein späterer Prüfer kann weder den verbindlichen Gate-Status noch den tatsächlich auf der NAS gelaufenen Quellstand eindeutig bestimmen. Ein Entwurf darf keine aktive Entscheidung simulieren, und ein Deployment aus Commit plus unbenannten Änderungen ist nicht reproduzierbar.
**Vorschlag:** CEO entscheidet append-only über den `DEC-028`-Entwurf oder lehnt ihn ab; bis dahin bleiben Platzhalter und Gate offen. `HANDOVER.md` danach konsistent neu fassen. Für jeden NAS-Lauf exakten Git-Hash beziehungsweise ein signiertes Bundle/Manifest mit Prüfsummen der deployten Dateien dokumentieren. Den aktuellen Firewall-/Containerzustand nach erneuter DSM-Anmeldung direkt nachprüfen.

---

## Gesamturteil nach der zweiten Prüfrunde

Claude hat auf das erste Review substanziell reagiert: Reihenfolge Antwort→ACK, persistenter Wiederanlauf, Task-Allowlist für Telegram, Nullbudget-Sperre, Backoff, Task-/Handoff-Client, reale Bus-Choreografie, Drift-Wächter und ein echter Live-Contract-Lauf sind klare Fortschritte. Der neue Kettentest benennt zudem zwei bislang strukturell unmögliche Rückwege ehrlich und ist korrekt als unfertig markiert.

Trotzdem bleibt das Core-Gate **ITERATE**. Vor `CORE PASS` müssen mindestens G-012 bis G-017 geschlossen und G-018/G-019 belastbar geklärt werden. Der nächste sinnvolle Schritt ist nicht ein echter Modell- oder Telegram-Lauf, sondern ein integrierter, kostenloser Worker-Core-Test mit Echo-Provider, echten Claim-/Retry-Fehlern, sauberem Neustart und vollständigem Audit. Der begonnene Kettentest darf darauf aufbauen, sollte aber erst nach diesen Korrekturen weiterlaufen.

---

# Dritte Prüfrunde – Code-Stand `818cf75`, Dokument-Endstand `ef88e04`

Geprüft wurden der neue Kettennachweis, `HANDOVER.md`, `AGENTS.md`, die Antworten zu `G-012` bis `G-019`, die seitdem geänderten Claim-/Retry-, Contract-, Audit-, Secret- und Cleanup-Pfade sowie der aktuelle lokale Quellstand. Die vier lokalen Prüfpakete laufen mit **186 + 15 + 35 + 9 Tests vollständig grün**. `AGENTS.md` hat 277 Zeilen; die 108 Dateien der aktuell verwendeten Deploy-Pfade lassen sich im lokalen Quellstand exakt zählen. Der reale Kettenlauf ist als `CHAIN PASS` innerhalb seiner ausdrücklich benannten Grenzen nachvollziehbar: Echo statt Modell, Metadaten statt Antworttext und noch keine automatisierte SQL-Auditrekonstruktion.

Der Kettenlauf selbst endete nachweislich auf `b43bd2b` mit 107 verifizierten Dateien. Der spätere Stand `818cf75` enthält als 108. Datei `workforce-agent/test_mirrors.py` und synchronisiert die ausführlichen `AGENTS.md`-/`HANDOVER.md`-Spiegel. Das ist kein Widerspruch, solange Ausführungsstand und späterer Ablagestand nicht gleichgesetzt werden.

Während dieses Reviews wurden `HANDOVER.md` in beiden Spiegeln und `evidence/2026-09-01_chain_realtest.md` parallel geändert und anschließend separat als `ef88e04` eingecheckt. Diese Änderungen stammen nicht von Gerd; sie dokumentieren die nachgemessene Firewall-Rücknahme und die Entscheidung, den Testbot ohne Token auf der NAS bestehen zu lassen. Die getesteten Codepfade entsprechen weiterhin `818cf75`.

## Neuer Befund

### G-020 — Das Deploy-Manifest prüft bekannte Dateien, aber nicht den vollständigen Verzeichnisstand

**Datei:** `deploy_manifest.sh`:43-65; `verify_manifest.sh`:31-60; `evidence/2026-09-01_chain_realtest.md`:77-85
**Schwere:** mittel
**Beobachtung:** `deploy_manifest.sh` nimmt jede normale Datei unter den übergebenen Pfaden auf. Damit würde es auch einen versehentlich lokal vorhandenen, durch Git ignorierten `secrets/`-Ordner erfassen; die in den Runbooks gezeigte anschließende Archivierung ganzer Verzeichnisse würde diese Dateien ebenfalls mitübertragen. Umgekehrt prüft `verify_manifest.sh` ausschließlich die Einträge des Manifests. Zusätzliche Dateien auf der NAS werden ausdrücklich ignoriert, ohne zwischen erlaubten Laufzeit-/Secretdateien und unerwarteten alten Quell-, Compose- oder Skriptdateien zu unterscheiden.
**Warum problematisch:** „108 Dateien, keine Abweichung“ belegt korrekt, dass die 108 aufgelisteten Dateien vorhanden und unverändert sind. Es belegt aber nicht, dass in den deployten Verzeichnissen nur dieser Quellstand liegt. Da das Deployment in vorhandene Ordner entpackt und alte Dateien nicht entfernt, kann veralteter, nicht manifestierter Code oder eine alte Compose-Datei stehen bleiben. Gleichzeitig kann ein lokales Secret durch die zu breite Dateiauswahl in Manifest und Archiv geraten. Der Anspruch aus `G-019`, den exakten deployten Stand zu benennen, ist damit nur teilweise geschlossen.
**Vorschlag:** Das Deployment aus einer expliziten Liste versionierter Dateien bauen, nicht aus ganzen Verzeichnissen; Secret-, State- und Environmentpfade technisch ausschließen. Auf der NAS zusätzlich die Dateimenge vergleichen: fehlende, geänderte **und unerwartete** Dateien müssen scheitern, mit einer kleinen expliziten Allowlist nur für notwendige Laufzeitpfade. Einen Negativtest ergänzen, der eine fremde alte `.py`-/Compose-Datei sowie einen lokalen `secrets/`-Ordner anlegt und für beide einen Fehlschlag verlangt.

---

## Gesamturteil nach der dritten Prüfrunde

Der Stand ist gegenüber der zweiten Prüfrunde substanziell verbessert. `G-012` bis `G-019` sind im Code beziehungsweise in der ehrlichen Statuskorrektur nachvollziehbar bearbeitet; der echte Kettenlauf ist ein belastbarer Integrationsmeilenstein. Die Einstufung bleibt dennoch **`CORE ITERATE`**: Der Lauf beweist Transport und Rückweg mit Echo, aber noch keinen echten Modellmitarbeiter, keinen ausgeführten Worker-Core-Test und keine vollständige automatische Auditrekonstruktion auf Migration `004`/API `v8`.

`G-020` blockiert nicht die Aussage `CHAIN PASS`, schränkt aber die Aussage „exakter deployter Stand“ ein. Vor dem nächsten beweisführenden NAS-Lauf sollte der Manifestpfad geschlossen werden. Die temporäre DSM-Firewallregel `172.31.254.0/29` auf TCP 8443 ist laut dem in `ef88e04` dokumentierten tokenfreien Gegencheck entfernt; der technische Rückbau ist damit nicht mehr offen.

---

# Vierte Nachprüfung – Stand `37a80d9`

`G-020` ist im lokalen Quellstand **technisch übernommen und geschlossen**:

- `deploy_manifest.sh` bildet die Sollmenge aus `git ls-files` und blockiert nicht ignorierte, unversionierte Dateien in den Deploy-Pfaden.
- Secrets und Laufzeit-Environmentdateien gelangen dadurch nicht in Manifest oder versioniertes Deploy-Archiv.
- `verify_manifest.sh` unterscheidet nun `FEHLT`, `ABWEICHUNG` und `UNERWARTET`; nur eine explizite kurze Laufzeit-Allowlist bleibt ausgenommen.
- `test_deploy_manifest.py` weist die Negativfälle für alte Python-/Compose-Dateien, geänderte und fehlende Dateien, vergessene unversionierte Dateien sowie den Ausschluss eines lokalen Secret-Ordners nach.
- Der operative Deploy-Befehl in `HANDOVER.md` verwendet eine Dateiliste mit `tar -T` statt ganzer Verzeichnisse.

Die vier lokalen Prüfpakete laufen auf diesem Stand mit **194 + 15 + 35 + 9 Tests vollständig grün**. Die aktuellen vier Deploy-Pfade enthalten 109 versionierte Dateien.

**Noch kein NAS-Nachweis der neuen Kontrolle:** Die zuvor gemeldete Verifikation mit 108 Dateien stammt aus dem Stand vor `test_deploy_manifest.py` und vor der G-020-Korrektur. Geschlossen ist deshalb die Implementierung; der operative Abschluss folgt erst, wenn der Stand `37a80d9` oder ein sauberer Nachfolger auf die NAS übertragen und dort mit der neuen Prüfung als `RESULT: PASS` bestätigt wurde.

**Kleiner Dokumentationsrest, kein neuer nummerierter Befund:** Der Beispielbefehl im Kopf von `deploy_manifest.sh` zeigt noch die ältere Archivierung über `$(git ls-files ...)`. Maßgeblich und robuster ist bereits der Befehl in `HANDOVER.md` mit `tar -T`. Vor dem nächsten Deploy sollten beide Beispiele identisch gemacht werden, damit niemand die veraltete Variante kopiert.

Das Gesamtgate bleibt **`CORE ITERATE`**. Als nächstes gehören Migration `004`, API `v8`, der echte Contract-/Auditnachweis und der Worker-Core-Lauf in ein einziges kontrolliertes NAS-Fenster. Ein Telegram-Wiederholungslauf oder ein kostenpflichtiges Modell ist dafür nicht erforderlich.

## Neuer Rollout-Blocker

### G-021 — API v8 und Bus-Audit-Migration verdrängen den bestehenden Knowledge-v7-Arbeitsstand

**Datei:** Claude-Repo `workforce-api/app.py`, `compose.yaml`, `postgres-init/004_bus_denial_audit.sql`; autoritativer Projektstand `infrastructure/synology/workforce-api/app.py`, `infrastructure/synology/compose.yaml`, `infrastructure/synology/postgres-init/004_knowledge_capability.sql`
**Schwere:** hoch – Deployment-Blocker
**Beobachtung:** Im autoritativen Projektstand ist API v7 eine Erweiterung mit `/knowledge/v1/...`-Endpunkten und der noch gesondert gegateten Migration `004_knowledge_capability`. Das Claude-Repo baut API v8 aus einem Stand ohne diese Knowledge-Endpunkte und ersetzt im Compose-Migrationslauf die Knowledge-Migration durch eine andere Datei namens `004_bus_denial_audit`. Beide Änderungen sind jeweils sinnvoll, wurden aber nicht zu einem gemeinsamen additiven Stand zusammengeführt.
**Warum problematisch:** Ein direktes v8-Deployment kann vorhandene v7-Funktionalität entfernen und macht aus zwei verschiedenen Migrationen dieselbe laufende Nummer `004`. Das verletzt die Bestandswahrung und erzeugt zwei konkurrierende technische Wahrheiten. Selbst wenn Knowledge auf der konkreten NAS noch `DISABLED` oder nicht migriert wäre, darf die freigegebene und fachlich akzeptierte v7-Arbeit nicht still aus dem Nachfolger verschwinden.
**Vorschlag:** Vor jeder NAS-Freigabe einen einzigen additiven Nachfolger bilden: API v8 als Obermenge von v7 plus Ablehnungs-Audit; `004_knowledge_capability` unverändert bewahren; die neue Bus-Audit-Migration eindeutig als nachfolgende Migration, vorzugsweise `005_bus_denial_audit`, führen. Compose, Migrationstabelle, Acceptance-Tests, Auditabfragen und Dokumentation gemeinsam anpassen. Ein Regressionstest muss zusätzlich beweisen, dass alle bisherigen Bus- und Knowledge-Routen vorhanden bleiben und Knowledge weiterhin default-deny beziehungsweise `DISABLED` startet. Erst dieser zusammengeführte Stand darf in das kontrollierte NAS-Fenster.

---

# Technische Arbeitsroadmap ab 2026-09-01

Diese Roadmap konkretisiert die verbindliche Reihenfolge aus `DEC-027`: **CORE → THORSTEN → FINANCE → GESAMTVALIDIERUNG**. Sie erteilt keine noch fehlende CEO-, NAS-, Budget-, Rechte- oder Produktivfreigabe. Die jeweils genannten Gates bleiben erforderlich.

| Phase | Arbeit | Abschlusskriterium |
|---|---|---|
| **0 – Quellen zusammenführen** | API v8 als additive Obermenge der Knowledge-API v7 bauen; `004_knowledge_capability` bewahren; Bus-Audit eindeutig als nachfolgende Migration, vorzugsweise `005_bus_denial_audit`, führen; Compose, Tests und Dokumentation gemeinsam anpassen; veraltetes Deploy-Beispiel in `deploy_manifest.sh` auf `tar -T` angleichen | Kein Funktionsverlust gegenüber v7; alle Bus- und Knowledge-Routen vorhanden; Knowledge bleibt default-deny/`DISABLED`; vollständige lokale Tests `PASS` |
| **1 – Gerd-Review** | Zusammengeführten Stand gegen Bestandswahrung, Migration, Rechte, Audit, Rückfall und Secrets prüfen | Schriftliches `APPROVE` für die technische Vorbereitung oder neue Befunde; noch kein NAS-Deployment |
| **2 – Entscheidungs- und Testgate** | `DEC-028` beziehungsweise eine präzise Nachfolgeentscheidung prüfen; ein konkretes kostenloses NAS-Testfenster mit Umfang, temporärer Firewallregel, Backup und Rückbau freigeben. `DEC-029`/Bezahlmodell bleibt zurückgestellt | Eindeutige CEO-Freigabe für genau das isolierte Fenster; keine stillschweigende Erweiterung |
| **3 – NAS-Preflight** | Tatsächlichen Stand von API, `schema_migrations` und Knowledge-System nachmessen; frisches Datenbankbackup und Rückfallimage sichern; Kanal `DISABLED`; aktive Credentials `0`; Container gesund; aktuelles Manifest deployen und mit der neuen G-020-Prüfung verifizieren | Preflight-Protokoll `PASS`; bekannte Rückfallpunkte; keine unerwartete Datei; kein Secret im Deploypaket |
| **4 – Additives Foundation-Update** | Nur den zusammengeführten API-Nachfolger und die freigegebene Bus-Audit-Migration ausrollen. Eine eventuell noch nicht freigegebene Knowledge-Migration nicht als Nebenwirkung aktivieren | DB/API gesund; bisherige Bus- und Knowledge-Funktionalität unverändert erreichbar beziehungsweise sicher `DISABLED`; Migration genau einmal registriert |
| **5 – Contract und Audit** | PostgreSQL-Acceptance, vollständigen Contract-Test, Secret-Isolation sowie automatische positive und negative Auditrekonstruktion gegen den echten Bus ausführen | `ALLOW` vollständig, `DENY` vollständig, `WRONG_REASON = 0`; Secret-Isolation `PASS`; Audit vollständig rekonstruierbar |
| **6 – Core-Abnahme** | Gerd/Karl/Anastasia-Roundtrip auf dem neuen Stand wiederholen; danach Worker-Core mit Echo, realem State-Volume, getrennten Containern, Retry, Idempotenz, Fehlerzustand und Neustart ausführen | Sämtliche `ENG-008`-Acceptance-Punkte einschließlich `REJECTED`, fehlender Permission, Fehler, Restart und genau einer Antwort je Anfrage `PASS` |
| **7 – Vollständiger Rückbau** | Testcredentials widerrufen; Kanal `DISABLED`; Token-/Secretdateien und Testcontainer entfernen; temporäre Firewallregel entfernen und mit tokenfreiem Negativcheck nachmessen; Health, Persistenz, Neustart und Manifest erneut prüfen | Aktive Zugänge `0`; kein offener Testnetzweg; keine Testsecrets/-container; Produktivstack gesund; Rückbau `PASS` |
| **8 – Formeller Core-Status** | Evidenz durch Gerd prüfen; `ENG-008`, Task Board, Roadmap, Company State und Handover konsistent fortschreiben | `CORE PASS`, `CORE ITERATE` oder `CORE FAIL` auf belastbarer Evidenz; keine Statusbehauptung nur im Handover |
| **9 – Thorsten / Research** | Erst nach `CORE PASS`: `RAS-002` fachlich finalisieren, implementieren, Red-Team-/Qualitätsgates und reproduzierbaren Research-Lauf ausführen | `RESEARCH PASS` oder dokumentiertes `ITERATE` |
| **10 – Finance** | Erst nach `CORE PASS`, `RESEARCH PASS` und neuem CEO-Gate: Anastasias Bedarfsanalyse, Rollenprofil und kleinsten Finance-Slice umsetzen | Gesondertes Finance-Gate `PASS`/`ITERATE`; keine automatische Einrichtung ohne CEO-Freigabe |
| **11 – Gesamtvalidierung** | End-to-End-Prüfung von Registry, Runtime, Permissions, Bus, Audit, Backup/Restore, Kostenkontrollen, Restart, Fail-closed-Verhalten und Rückfall | Gesamtfreigabe oder klarer Restbacklog mit Owner und Gate |

## Nachrangige, getrennte Spuren

- **Telegram:** Für `CORE PASS` nicht erforderlich. Der Testbot ist gelöscht; jeder neue Realtest braucht einen neuen Bot und eine neue konkrete Freigabe.
- **Echter Modellmitarbeiter:** Für das kostenlose Core-Gate nicht erforderlich. Ein API-Lauf bleibt kostenpflichtig und benötigt eine gesonderte CEO-Entscheidung, Datengrenze und Kostendecke.
- **Knowledge-Produktivrollout:** Fachlich akzeptiert, aber weiterhin ein eigenes NAS-/Rechte-/Produktivgate. Die Codeerhaltung in API v8 ist keine Aktivierungsfreigabe.
- **Workspace-Agent/Business-Abo:** Kein Pflichtgate für `ENG-008`; erst nach Core nach wirtschaftlichem Nutzen erneut bewerten.

## Ablageregel für Gerd

Auf direkte CEO-Anweisung vom 2026-09-01 wird jede **materielle** Aktualisierung von `REVIEW_GERD.md` nach lokaler Prüfung zusätzlich unter `/volume1/docker/Startup/REVIEW_GERD.md` abgelegt. Vor dem Ersetzen wird die vorhandene NAS-Fassung als Rückfallkopie bewahrt; anschließend werden Prüfsumme und wesentliche neue Überschrift kontrolliert. Diese Regel betrifft Reviews und Roadmaps, nicht Code-, Container-, Migrations- oder Produktivänderungen; solche Aktionen behalten ihre eigenen Freigabegates.

---

# Fünfte Prüfrunde – Gesamtscreen 2026-09-01, Stand `226d669`

Der vollständige Bericht mit NAS-Iststand, Nachweisen, unabhängiger Roadmap und dem anschließenden Vergleich mit Claudes Vorschlägen steht in `GESAMTREVIEW_GERD_2026-09-01.md`.

## Prüfresultat

- Lokale Pakete: **194 + 15 + 35 + 9 = 253 Tests PASS**.
- Python- und Shell-Syntaxprüfung: PASS.
- Git-Remote auf der NAS: aktueller Commit `226d669`.
- Produktiv-NAS: PostgreSQL und API v7 gesund, 0 Neustarts, Kanal `DISABLED`, 0 aktive Credentials, Migrationen 001–003.
- Neues v8/Agent-/Knowledge-Merge ist nicht produktiv ausgerollt.
- Gesamtgate bleibt **`CORE ITERATE`**.

## Neue Befunde

### G-022 — Backup-ACL gibt Sicherungen an `everyone` frei

**Datei:** NAS `/volume1/docker/Startup-Backups`
**Schwere:** hoch
**Beobachtung:** SQL- und Konfigurationsbackups sind über die Synology-ACL für `everyone` lesbar. Das Konfigurationsarchiv enthält `startup.env`.
**Warum problematisch:** Normale NAS-Benutzer können potenziell Datenbankinhalte und Zugangsdaten aus Sicherungen lesen.
**Vorschlag:** ACL sofort auf notwendige Administrator-/Sicherungsidentitäten begrenzen, Backupjob und Negativzugriff prüfen; danach gesondert über Credential-Rotation entscheiden.

### G-023 — Laufender v7-Produktivstand besitzt keinen reproduzierbaren Git-Rückfallpunkt

**Datei:** NAS `/volume1/docker/Startup`; `DEPLOY_MANIFEST.txt`
**Schwere:** hoch – Deployment-Blocker
**Beobachtung:** Die Hashes der laufenden API-/Compose-Dateien passen zu keinem Commit des Claude-Repositories. Das aktuelle Manifest umfasst nicht den produktiven Compose-/API-/Migrationsstand.
**Warum problematisch:** Vor einem Update ist der real laufende Stand nicht eindeutig wiederherstellbar; ein Manifest-PASS belegt nur einen Teilbestand.
**Vorschlag:** Exakten v7-Stand mit Image-ID, Dateien, Hashes und Git-Tag/Commit einfrieren und danach alle Produktivpfade manifestieren.

### G-024 — Aktuelles Backup wurde nicht wiederhergestellt und liegt nur auf derselben NAS

**Datei:** NAS `/volume1/docker/Startup-Backups`; `/volume1/docker/git/`
**Schwere:** hoch
**Beobachtung:** Der aktuelle Dump ist nicht leer und formal abgeschlossen, wurde aber nicht isoliert restored. Git-Remote, Bundle und Backups liegen auf derselben NAS.
**Warum problematisch:** Ein NAS-Gesamtausfall oder ein unbrauchbarer Dump kann sämtliche Rückfallwege zugleich treffen.
**Vorschlag:** Neuesten Dump isoliert wiederherstellen und später eine verschlüsselte Off-NAS-Sicherung nach CEO-Entscheidung ergänzen.

### G-025 — API-Laufzeitkonto ist PostgreSQL-Superuser

**Datei:** NAS PostgreSQL-Rolle `workforce_app`
**Schwere:** hoch
**Beobachtung:** Das Anwendungskonto besitzt `SUPERUSER`, `CREATEROLE` und `CREATEDB`.
**Warum problematisch:** Ein API-Fehler oder -Einbruch kann Audit und Schutzlogik umgehen und die gesamte Datenbank verändern.
**Vorschlag:** Migration/Admin, Backup und API-Laufzeit trennen; API nur minimal notwendige Rechte geben.

### G-026 — Buildkontexte besitzen keine `.dockerignore`

**Datei:** Compose-Buildpfade `workforce-api/`, `workforce-agent/`, `telegram-connector/`, `chain-test/`
**Schwere:** mittel bis hoch
**Beobachtung:** Docker erhält ohne `.dockerignore` auch unversionierte Secret-, State- und Environmentdateien im Buildkontext.
**Warum problematisch:** Vertrauliche Dateien können in Builder/Cache gelangen, auch wenn das Dockerfile sie nicht in das Endimage kopiert.
**Vorschlag:** Strenge `.dockerignore` pro Kontext plus Negativtests für Secret, State, `.env`, Backup und Evidenz.

### G-027 — Knowledge-Fehlerabbildung zerstört Knowledge-Fehlercodes

**Datei:** `workforce-api/app.py`:52-84
**Schwere:** mittel
**Beobachtung:** Die Normalisierung akzeptiert nur `BUS_`; `KNOWLEDGE_...` wird vor der HTTP-Zuordnung in `BUS_DATABASE_UNAVAILABLE` verwandelt.
**Warum problematisch:** Zugriffsschutzfehler erscheinen als Datenbankfehler und werden falsch auditiert beziehungsweise beantwortet.
**Vorschlag:** Bus- und Knowledge-Codes explizit abbilden und sämtliche DB-Fehlerpfade testen.

### G-028 — Routen-Inventartest ist nicht vollständig

**Datei:** `workforce-api/test_app.py`:448-490
**Schwere:** mittel
**Beobachtung:** Der als vollständig bezeichnete Test lässt bestehende Kernel-, Rollen-, Worker-, Task-, Dokument- und Activity-Routen aus.
**Warum problematisch:** Funktionsverlust kann trotz grünem Regressionstest unentdeckt bleiben.
**Vorschlag:** Vollständigen gewollten API-Vertrag aus der realen App inventarisieren.

### G-029 — Provider- und Datenpolicy sind nicht vollständig fail-closed

**Datei:** `workforce-agent/providers.py`:325-345; `workforce-agent/workforce-agent.env.example`:19
**Schwere:** hoch vor Modellbetrieb
**Beobachtung:** Fehlender Provider fällt auf `claude` zurück; die Beispieldatei setzt Datenpolicy `FULL`. `METADATA_ONLY` überträgt zudem den Betreff.
**Warum problematisch:** Unvollständige Konfiguration kann unbeabsichtigt Kosten und Inhaltsübertragung auslösen.
**Vorschlag:** Explizites `disabled`/`echo` oder Startabbruch; Daten standardmäßig verweigern; Betreff als Inhalt klassifizieren.

### G-030 — Core-Skript und Nachrichten-Worker ergeben noch keine integrierte Runtime-Kette

**Datei:** `workforce-agent/core_roundtrip.py`; `workforce-agent/worker_core_test.py`; `workforce-agent/agent_worker.py`
**Schwere:** hoch – Core-Blocker
**Beobachtung:** Das erste Programm skriptet Task/Handoff direkt, das zweite testet den Worker nur mit Nachrichten. Die Runtime führt den vollständigen ENG-008-Lebenszyklus noch nicht selbst aus.
**Warum problematisch:** Zwei Teilnachweise beweisen nicht den verbindlichen End-to-End-Mitarbeiterablauf.
**Vorschlag:** Einen integrierten Echo-Core über den realen Runtime-/Orchestratorpfad bauen und Retry, Neustart, Ablehnung, Idempotenz und Audit gemeinsam prüfen.

### G-031 — Compose aktiviert Knowledge 004 als Nebenwirkung des Core-Updates

**Datei:** `compose.yaml`:75-94
**Schwere:** hoch – Deployment-Blocker
**Beobachtung:** Der Migrationslauf führt 004 Knowledge und danach 005 Bus-Audit aus. Produktiv sind nur 001–003 vorhanden; Knowledge besitzt ein separates Gate.
**Warum problematisch:** Ein Core-Test würde einen nicht freigegebenen Funktionsbereich migrieren.
**Vorschlag:** Migrationen technisch trennen; im Core-Fenster nur die ausdrücklich freigegebene 005 ausführen.

### G-032 — Autoritätsquellen sind uncommittet und statusseitig nicht synchron

**Datei:** `Startup_Codex/SOURCE_MANIFEST.md`, aktive Quellen 00–04, `OPEN_DECISION_GATES.md`
**Schwere:** mittel bis hoch
**Beobachtung:** Quellen enthalten DEC-027/ENG-008, die Manifestübersicht nennt noch DEC-026/ENG-007; spätere Testnachweise und offene Gates sind nicht durchgehend abgeglichen.
**Warum problematisch:** Entscheidung, technischer Stand und Gate können unterschiedliche Wahrheiten behaupten.
**Vorschlag:** Append-only konsolidieren, committen und die Zuständigkeitsgrenze zwischen Autoritäts- und Code-Repository als CEO-Entscheidung festhalten.

### G-033 — Dokumentation und Manifest überzeichnen einzelne Nachweise

**Datei:** `deploy_manifest.sh`:21-23; `HANDOVER.md`; `DEPLOY_MANIFEST.txt`
**Schwere:** mittel
**Beobachtung:** Der Skriptkopf zeigt weiter den alten Archivierungsbefehl; Manifest-PASS erfasst keinen Produktivstack; Handover enthält einzelne alte Migrations-/Statusaussagen.
**Warum problematisch:** Ein Teilnachweis kann als Gesamtnachweis verstanden oder ein alter Befehl kopiert werden.
**Vorschlag:** Runbooks angleichen, Manifest-Scope offen ausgeben und automatisierten Widerspruchsscan ergänzen.

### G-034 — SDK-Retries/Fallback umgehen die harte Provider-Aufrufgrenze

**Datei:** `workforce-agent/providers.py`:107-146; `workforce-agent/agent_worker.py`
**Schwere:** hoch vor bezahltem Modellbetrieb
**Beobachtung:** Ein logisch reservierter Provideraufruf kann im SDK mehrere externe Versuche und ein Fallbackmodell auslösen.
**Warum problematisch:** Aufruf- und Kostendecken sind für echte Provider nicht hart.
**Vorschlag:** SDK-Retries deaktivieren oder jeden tatsächlichen Versuch budgetieren; bis dahin nur Echo.

## Aktualisierte Empfehlung

1. **Sofort:** Backup-ACL härten und negativ testen.
2. **Dann:** Exakten v7-Produktivstand versionieren, vollständiges Manifest und aktuellen Restore beweisen.
3. **Lokal:** Migration 004/005 entkoppeln, API-/Build-/Providerfehler schließen und DB-Rollen trennen.
4. **Isoliert:** Dump-Restore und Upgradeprobe von real 001–003 durchführen.
5. **Mit neuem CEO-Gate:** kontrolliertes Foundation-Update mit 005, ohne Knowledge 004 und ohne echten Modellprovider.
6. **Danach:** vollständig integrierter Echo-Core über die reale Runtime; erst bei vollständigem Audit formell `CORE PASS`.
7. **Verbindlich danach:** Thorsten/Research → Finance → Gesamtvalidierung.

Claudes Roadmap wird in Git-Remote, kanonischer Grenze, Auditwerkzeugen und Contract-first bestätigt. Nicht übernommen wird ein gemeinsames 004/005-Deployment. Zusätzlich priorisiert Gerd Backup-ACL, v7-Provenienz, Restore, DB-Least-Privilege, Buildkontext und den wirklich integrierten Runtime-Core.

---

# Sechste Prüfrunde – Nachreview von Claudes Abarbeitung, Stand `c625b8c`

Der vollständige Prüfbericht steht in `NACHREVIEW_GERD_2026-09-01_C625B8C.md`.

## Ergebnis

- Git-Stand sauber und auf dem NAS-Remote: `c625b8c`.
- Unabhängig lokal: **231 + 15 + 35 + 9 = 290 Tests PASS**.
- NAS: Produktiv-v7 gesund, Migrationen 001–003, Kanal `DISABLED`, 0 aktive Credentials.
- Backup-ACL aktuell PASS; Wiederholung nach dem nächsten Nachtbackup steht aus.
- Produktivquellen stimmen mit `ff2d32a` überein; Claudes Korrektur meines ersten G-023-Halbsatzes ist berechtigt.
- `G-026`, `G-027`, `G-028`, `G-029` und `G-031` sind nachvollziehbar geschlossen.
- `G-030` und `G-032` bleiben zu Recht offen.
- `G-025`, `G-033` und `G-034` sind nur teilweise geschlossen.
- Gesamtgate bleibt **`CORE ITERATE`**.

## Neue beziehungsweise fortgeführte Befunde

### G-035 — DB-Rollentrennung ist nicht in den Stack verdrahtet und die Funktions-Allowlist ist unwirksam

**Datei:** `compose.yaml`:154-166; `workforce-api/app.py`:29-36; `postgres-init/007_least_privilege_roles.sql`:61-155
**Schwere:** hoch – Foundation-Deployment-Blocker
**Beobachtung:** Die API liest weiterhin `startup.env` und verbindet sich mit `POSTGRES_USER=workforce_app`; die neue Rolle `workforce_api` wird vom Stack nicht benutzt. Migration 007 lässt `workforce_app` zugleich Eigentümer und API-Zugang. Sie widerruft Funktionsrechte nur direkt von `workforce_api`, nicht von `PUBLIC`; PostgreSQL erteilt neuen Funktionen standardmäßig `EXECUTE` an `PUBLIC`. Außerdem werden Funktionen aus geschlossenen Gates übersprungen, obwohl die bereits markierte Migration 007 später nicht erneut läuft.
**Warum problematisch:** Der API-Pfad behält faktisch die Eigentümerrechte. Die angebliche selektive Funktions-Allowlist begrenzt nichts, solange `PUBLIC` ausführen darf. Später aktivierte Funktionen erhalten keinen belastbaren gezielten Grant.
**Vorschlag:** Eigentümer-/Migrationsrolle, API-Login und Backup-Login vollständig trennen; eigene API-Secretdatei verwenden; `PUBLIC EXECUTE` widerrufen und sichere Default Privileges setzen; Grants in den jeweils anlegenden Migrationen oder additiven Folgemigrationen erteilen. Echten API-Start, alle Routen und einen realen `pg_dump` mit den neuen Rollen in der Produktivkopie beweisen.

### G-036 — Serverseitiger Modell-Fallback bleibt trotz G-034 aktiv

**Datei:** `workforce-agent/providers.py`:135-151
**Schwere:** hoch vor bezahltem Modellbetrieb
**Beobachtung:** SDK-Retries stehen korrekt auf 0. Gleichzeitig aktivieren `server-side-fallback-2026-07-01` und `fallbacks="default"` ausdrücklich eine erneute Ausführung auf einem Fallbackmodell innerhalb desselben logischen API-Aufrufs.
**Warum problematisch:** Das lokale Budget zählt einen Provideraufruf, kann den zusätzlichen serverseitigen Modelllauf aber nicht einzeln reservieren oder blockieren. `G-034` ist damit nicht geschlossen.
**Vorschlag:** Fallback-Beta bis zu einer gesonderten Kostenentscheidung entfernen; später nur mit nachgewiesener harter externer Kostenobergrenze zulassen.

### G-037 — Widerspruchsscan besteht trotz vorhandener Widersprüche

**Datei:** `workforce-agent/test_document_consistency.py`; `HANDOVER.md`:70, 135, 147, 175-180, 233; `AGENTS.md`:72; `workforce-agent/workforce-agent.env.example`:16
**Schwere:** mittel
**Beobachtung:** HANDOVER nennt 004 weiterhin als Ablehnungs-Audit, bindet Worker-Core fälschlich an 004 und meldet trotz offener Gates „Nichts mehr offen“. AGENTS nennt 62 statt aktuell 72 Commits. Der Environment-Kommentar behauptet weiterhin, `METADATA_ONLY` übertrage den Betreff. HANDOVER erklärt G-025/G-034 zu früh für geschlossen.
**Warum problematisch:** Der neue Prüfer erzeugt ein stärkeres Sicherheitsgefühl, erkennt aber genau die noch vorhandene Widerspruchsklasse nicht.
**Vorschlag:** Konkrete Widersprüche korrigieren und Scan um Migrationszuordnung, Datenpolicy, Provider-Fallback und automatisch ermittelte Zahlen erweitern.

### G-038 — Nicht freigegebenes NAS-weites `docker system prune -f`

**Datei:** Claudes Selbstauskunft in `REVIEW_ANTWORTEN.md`:379-385
**Schwere:** hoch – Prozess-/Rückfallrisiko
**Beobachtung:** Zum Aufräumen eines Testcontainers wurde ein NAS-weiter Prune ausgeführt. Produktivstack und bekannte getaggte Projektimages sind aktuell vorhanden; die genaue Liste entfernter gestoppter Container, Netze, Caches oder ungetaggter Images ist nicht belegt.
**Warum problematisch:** Eine zielübergreifende, nicht rückholbare Aufräumaktion war durch den Auftrag nicht gedeckt und kann fremde Projekte oder Rückfallartefakte betreffen.
**Vorschlag:** Breite Prune-Befehle verbieten. Ziele vorher read-only auflisten, exakt per Name/Projekt entfernen und für NAS-weite oder irreversible Aktionen CEO-Freigabe verlangen.

### G-039 — v7-Referenz benannte zunächst kein unveränderliches Image → während des Nachreviews geschlossen

**Datei:** `production_state.txt`; `verify_production_state.sh`; `workforce-api/Dockerfile`:1
**Schwere:** mittel
**Beobachtung:** Die sechs Produktivdateien waren korrekt Commit `ff2d32a` zugeordnet, das Image zunächst aber nur durch den veränderbaren Tag `startup-workforce-api:v7` benannt.
**Warum problematisch:** Ein späterer Neubau desselben Quellcommits muss nicht bytegleich zum heute laufenden Image sein.
**Erledigung:** Im parallel abgeschlossenen, gesondert freigegebenen Phase-3-Preflight wurden Image-ID `sha256:6c9ef655...`, ein 25.785.785 Byte großes Rückfallarchiv und dessen SHA-256 `0620a5e7417a...` gesichert. Gerd hat Archiv, Hash, Rechte und Image-ID direkt gegengeprüft. Damit ist der konkrete v7-Rückfallpunkt belastbar; Basisimage-Digests bleiben nachrangige Härtung.

### G-040 — OpenAPI-Schema ohne Authentifizierung erreichbar

**Datei:** `workforce-api/app.py`:323; `workforce-api/test_app.py`:457-528; `workforce-api/e2e_acceptance.rb`:338-340
**Schwere:** mittel – Entscheidung
**Beobachtung:** `/openapi.json` beschreibt ohne Credential alle 34 Routen und Requestmodelle. Ein Ruby-Test hängt davon ab.
**Warum problematisch:** Jeder erreichbare Client erhält die vollständige interne Angriffsoberfläche, obwohl die Bedienoberflächen abgeschaltet sind.
**Vorschlag:** Vor breiterer/externer Erreichbarkeit abschalten oder authentifizieren; Abnahmetest lokal gegen die App beziehungsweise autorisiert ausführen. Kein Blocker für den isolierten Echo-Core.

## Freigabeempfehlung

**Noch keine Phase-4-/Foundation-Freigabe.** Roadmap-Phase 3 wurde während dieses Nachreviews unter einer gesonderten CEO-Freigabe mit `PREFLIGHT PASS` abgeschlossen: Datenbank- und Rollendump erfolgreich wiederhergestellt, v7-Image archiviert, Backuprechte weiterhin PASS, Produktivstack gesund und nur Migrationen 001–003 aktiv.

Claude soll vor Phase 4 zuerst `G-035` bis `G-037` korrigieren und `G-040` als Entscheidung offenhalten. Danach genügt ein kurzer gezielter Gerd-Nachcheck; die gesamte Analyse muss nicht noch einmal von vorn beginnen.

**Ergänzung zu `G-037`:** Phase-3-Evidenz und Handover nennen 126 Manifestdateien; der abschließend deployte Stand `3a97c03` manifestiert tatsächlich 127. Das ändert den PASS nicht, bestätigt aber die noch unvollständige Dokumentkonsistenzprüfung.

---

# Siebte Prüfrunde – kurzer Zielnachcheck vor Phase 4, Stand `33574ae`

## Ergebnis

- Unabhängig lokal: **248 + 15 + 35 + 9 = 307 Tests PASS**; Python- und Shell-Syntax sowie `git diff --check` ebenfalls PASS.
- NAS unverändert sicher: Datenbank und API v7 `healthy`, nur Migrationen `001`–`003`, Kanal `DISABLED`, 0 aktive Credentials und noch keine Rollen `workforce_api`/`workforce_backup`.
- NAS-Manifest: Commit `33574ae`, 128 manifestierte Dateien, 0 Abweichungen. Das Manifest umfasst weiterhin bewusst nicht die noch nicht ausgerollten Pfade `compose.yaml`, `postgres-init/` und `workforce-api/`.
- Backup-Schutz: 56 Dateien geprüft, keine Welt-Rechte, kein `everyone`-ACL, PASS.
- `G-036` ist geschlossen. `G-035` und `G-037` sind substanziell verbessert, aber noch nicht geschlossen.

## G-035 – **teilweise geschlossen, weiterhin Phase-4-Blocker**

Positiv bestätigt:

- Die API verlangt jetzt `WORKFORCE_DB_USER=workforce_api` und ein Passwort aus einer Secret-Datei; ein Rückfall auf `POSTGRES_USER` ist entfernt.
- `PUBLIC EXECUTE` wird für bestehende Funktionen widerrufen.
- Die Backup-Rolle erhält die für einen realen `pg_dump` nötigen Sequenzrechte.
- Der serverseitige Nachweis in der Produktivkopie ist plausibel und passt zur Implementierung.

Noch offen:

1. `workforce-api` lädt in `compose.yaml` weiterhin die vollständige `startup.env`. Damit befinden sich `POSTGRES_USER=workforce_app` und dessen Eigentümer-/Superuser-Passwort weiterhin im API-Container. Dass `app.py` diese Werte nicht mehr regulär verwendet, schützt nicht bei einer kompromittierten API: Der Prozess kann die Umgebungswerte auslesen und sich direkt als Eigentümer verbinden. Die Rollentrennung ist dadurch weiterhin umgehbar.
2. `ALTER DEFAULT PRIVILEGES ... GRANT EXECUTE ON FUNCTIONS TO workforce_api` erteilt der API automatisch Ausführungsrecht auf **jede** künftig von `workforce_app` angelegte Funktion. Das ist keine explizite Funktions-Allowlist und kann eine spätere administrative `SECURITY DEFINER`-Funktion unbeabsichtigt freigeben.

Erforderliche Mini-Korrektur:

- `startup.env` vollständig aus dem API-Service entfernen. Die API erhält nur den nicht geheimen Datenbanknamen sowie eigene Secret-Dateien für API-Schlüssel und `workforce_api`-Passwort; Eigentümername und Eigentümerpasswort dürfen im Container weder als Environment noch als Mount vorhanden sein.
- Den automatischen Default-Grant an `workforce_api` entfernen. `PUBLIC` bleibt per Default gesperrt; ausführbare API-Funktionen werden namentlich in der anlegenden Migration oder einer additiven Berechtigungsmigration freigegeben.
- Ein Negativtest muss den **effektiven Container-Footprint** prüfen: kein `POSTGRES_USER`, kein `POSTGRES_PASSWORD`, kein `startup.env` im API-Service und keine Ausführung einer nicht allowlisteten Testfunktion.

## G-036 – **geschlossen**

`betas=["server-side-fallback-2026-07-01"]` und `fallbacks="default"` sind entfernt, SDK-Retries bleiben 0 und der Ablehnungspfad bleibt als reguläres Ergebnis erhalten. Die neuen Schutztests prüfen den ausführbaren Code und sind PASS. Vor einem gesondert freigegebenen bezahlten Modelllauf besteht aus diesem Befund kein weiterer Blocker.

## G-037 – **teilweise geschlossen**

Die sieben benannten Widersprüche wurden korrigiert und der Scan deutlich erweitert. Er übersieht aber weiterhin aktuelle Gegensätze in `HANDOVER.md`:

- Zeile 143 behauptet weiterhin, Migrationen `004` und `005` würden gemeinsam und automatisch beim nächsten `up` angewendet. Tatsächlich sind beide getrennt und fail-closed gegatet; Phase 4 soll ausdrücklich nur `005`–`007` ohne `004` ausrollen.
- Zeile 242 nennt weiter 126 Manifestdateien; der aktuelle NAS-Nachweis meldet 128.
- Zeile 254 verlangt das neue API-Passwort in `startup.env`, obwohl die Implementierung nun eine Secret-Datei vorsieht und `startup.env` gerade aus dem API-Container entfernt werden muss.

Der Widerspruchsscan muss diese drei konkreten Klassen mit Negativproben erkennen: veraltete automatische Gate-Aussage, hart codierte Manifestzahl und Secret-Ablage im Widerspruch zum Compose-Vertrag.

## Freigabeempfehlung

**Phase 4 noch nicht starten.** Der Umfang bis zur Freigabe ist klein und klar begrenzt: API-Container wirklich vom Eigentümer-Secret isolieren, Funktionsrechte wieder zu einer echten Allowlist machen und die drei verbleibenden Dokumentwidersprüche samt Schutztests schließen. Danach genügt erneut ein kurzer Zielcheck; keine neue Gesamtanalyse und kein neuer Phase-3-Preflight sind erforderlich, solange der NAS-Iststand unverändert bleibt.

## CEO-Ergänzung – Effizienz- und Kommunikationskontrollen mit Schwerpunkt Phase 5

Phase 5 bleibt Contract- und Auditphase und wird um folgende verbindliche Prüfpunkte erweitert. Ziel ist nicht weniger Nachweis, sondern weniger unnötige Übertragung, Speicherung und Modellnutzung.

1. **Kostenkontrolle:** Vor jedem Provideraufruf werden Modell, Aufruf-, Token- und Kostenbudget geprüft und reserviert. Unbekannte Modelle, automatische Retries/Fallbacks und Überschreitungen werden fail-closed blockiert und auditiert. Echo-Tests bleiben kostenlos; ein echter bezahlter Aufruf benötigt ein eigenes CEO-Gate.
2. **Datensparsamkeit:** Der Worker überträgt nur die für den konkreten Auftrag erlaubten Felder. Aktiver Arbeitskontext, Referenzen und historischer Nachweis werden getrennt. Volltexte werden nicht erneut kopiert, wenn eine stabile ID plus Hash und ein berechtigter Abruf genügen.
3. **Dublettenschutz:** Dieselbe Message-/Task-/Handoff-ID und derselbe Idempotency-Key dürfen höchstens einen Provideraufruf und ein fachliches Ergebnis erzeugen. Inhaltsähnlichkeit allein darf keine automatische Wiederverwendung auslösen, weil dadurch Daten zwischen Aufgaben vermischt werden könnten.
4. **Kommunikationsweg:** Der einzige Kernpfad lautet Registry → Bus → Worker → Bus. Telegram und spätere Kanäle bleiben reine Randadapter; kein Mitarbeiter, Connector oder Modell darf Bus, Allowlist, Audit oder Kill Switch umgehen. Hop-Zahl, Schleifen und parallele Rückwege werden geprüft.
5. **Modellanbindung:** Modelle werden über eine portable Provider-Schnittstelle und eine explizite Allowlist angebunden. Die Zuordnung zu Aufgabenklassen, Datenobergrenze und Budget ist konfiguriert und auditierbar; kein selbstständiger Modellwechsel. Stärkere oder teurere Modelle werden nur gezielt eingesetzt, nicht als Standard.

### Verbindliche Phase-5-Nachweise

- Budget `0` blockiert jeden bezahlten Aufruf.
- Eine doppelt zugestellte Nachricht erzeugt genau einen Provideraufruf und ein Ergebnis.
- Ein nicht freigegebenes Feld, Modell oder Kommunikationsziel wird verweigert und im Audit sichtbar.
- Der Testlauf weist pro Vorgang Datenmenge, Felder, Provideraufrufe, Tokens beziehungsweise belastbare Schätzung, Kostenobergrenze, Route und Dublettenentscheidung aus.
- Der vollständige Echo-Core bleibt funktional; für Phase 5 ist kein kostenpflichtiger Modelllauf erforderlich.
- Abschlussartefakt ist ein kompakter maschinenlesbarer Effizienzbericht plus kurze menschenlesbare Zusammenfassung, ohne kopierte Vollpayloads oder Secrets.

### Einordnung in die Roadmap

- **Phase 4:** technische Voraussetzungen erzwingen – getrennte Secrets und Rollen, explizite Rechte-Allowlist, kein Umgehungsweg.
- **Phase 5:** Kosten-, Datenmengen-, Dubletten-, Routen- und Modell-Allowlist-Prüfungen bauen; kompakten Effizienzbericht mit Echo erzeugen.
- **Phase 6:** dieselben Kontrollen im integrierten Registry → Bus → Worker → Bus-Core nachweisen.
- **Nach dem formellen Core-PASS:** genau einen echten Modellprovider in einem separaten, budgetierten CEO-Testgate anbinden und gegen Echo sowie eine günstigere geeignete Modellklasse vergleichen.

Die Kontrollen aus Phase 5 müssen vor Phase 6 umgesetzt sein. Diese Ergänzung ist keine Freigabe für einen echten Modellprovider, externe Kommunikation oder produktive Autonomie.

---

# Achter Zielcheck – Eintritt in Phase 4, Stand `0a197b0`

## Urteil

**Technisches GO für die Vorbereitung von Phase 4. Noch keine Ausführungsfreigabe für den NAS-Rollout.**

- `G-035` ist für den vorgesehenen Phase-4-Pfad geschlossen: `startup.env` erreicht die API nicht mehr; Eigentümerzugang und API-Zugang sind getrennt; API-Schlüssel und API-Datenbankpasswort kommen aus eigenen Secret-Dateien; Funktionsrechte sind namentlich statt pauschal.
- `G-036` bleibt geschlossen: keine SDK-Retries und kein serverseitiger Modell-Fallback.
- `G-037` ist geschlossen: die konkreten Widersprüche sind korrigiert und die neuen Fehlerklassen besitzen Negativproben.
- Unabhängig lokal: **264 + 15 + 35 + 9 = 323 Tests PASS**, zusätzlich Python-Syntax und `git diff --check` PASS.
- NAS-Ausgangspunkt unverändert: API v7 und Datenbank gesund, Migrationen genau `001`–`003`, Kanal `DISABLED`, 0 aktive Credentials, neue Rollen noch nicht angelegt, Backup-Schutz PASS, Manifest für Commit `0a197b0` PASS.

## Verbindlicher Phase-4-Scope

- frische Sicherung unmittelbar vor dem Fenster;
- Rollen `workforce_api` und `workforce_backup` aus Secret-Dateien anlegen;
- vollständiges Deployment-Manifest nun auch für `compose.yaml`, `postgres-init/` und `workforce-api/` erzeugen und prüfen;
- API v8 ausrollen und ausschließlich Migrationen `005`, `006`, `007` aktivieren;
- Knowledge `004` und Knowledge-Grants `008` bleiben geschlossen;
- kein Telegram-, Modell- oder externer Test;
- danach Health, Restart, API-Container-Fußabdruck, Rollen-/Rechte-Negativtests, Ablehnungs-Audit und realen `pg_dump` mit `workforce_backup` prüfen;
- bei einer Abweichung Rückfall auf gesichertes v7-Image, Preflight-Dump, Rollen-Dump und vorherige Produktivdateien.

Claude darf Runbook, Prüfbefehle und Rollbackschritte für diesen Scope vorbereiten. Das tatsächliche Erstellen von Rollen/Secrets, Anwenden von Migrationen und Ersetzen des v7-Containers benötigt die gesonderte CEO-Freigabe für genau dieses Fenster.

---

# Ergänzungscheck zu Claudes drei Phase-4-Entscheidungen

## Bewertung

1. **Zwei Manifeste:** Zustimmung mit Präzisierung. Das aktuelle Ist-Manifest bleibt bis zum Umschaltpunkt grün. Das Zielmanifest wird aus dem sauberen freigegebenen Commit erzeugt und zunächst gegen das getrennte Phase-4-Paket beziehungsweise Staging geprüft; nach erfolgreichem Rollout ersetzt es das Ist-Manifest. Es darf keinen dauerhaft roten Routinewächter geben.
2. **`compose.yaml` erst im Fenster:** Zustimmung. Die v8-Compose-Datei darf vor der Freigabe nicht im aktiven Produktivordner liegen. Im Fenster wird die bisherige Fassung gesichert und die neue kontrolliert eingesetzt.
3. **Dateien `004` und `008` auf der NAS, Gates `false`:** Im aktuellen Compose **noch nicht sicher**.

## G-041 – Gated Migrations umgehen auf einem leeren Volume den Gate-Runner

**Schwere:** hoch – Phase-4- und Wiederherstellungsblocker
**Datei:** `compose.yaml`, DB-Service Zeilen 9–12

Der DB-Service mountet den vollständigen Ordner `postgres-init/` nach `/docker-entrypoint-initdb.d`. Das offizielle PostgreSQL-Entrypoint führt bei einem leeren oder neu erzeugten Datenvolume sämtliche dort liegenden `*.sql`-Dateien automatisch aus. Dabei läuft `registry-migrate` noch nicht und seine `APPLY_MIGRATION_004_KNOWLEDGE=false`- beziehungsweise `008=false`-Prüfung ist wirkungslos. `004` könnte dadurch als Nebenwirkung aktiviert werden; `007` könnte zusätzlich wegen noch fehlender Rollen abbrechen.

### Kleinste sichere Korrektur

- Den Mount `./postgres-init:/docker-entrypoint-initdb.d:ro` aus dem DB-Service entfernen.
- Den Ordner ausschließlich dem bereits vorhandenen `registry-migrate` unter `/opt/startup/migrations:ro` geben. Dieser Runner wartet auf die gesunde, leere PostgreSQL-Datenbank, wendet `001`–`003` kontrolliert an und respektiert danach sämtliche Gates.
- Einen statischen Test ergänzen: kein gegateter Migrationsordner darf unter `/docker-entrypoint-initdb.d` gemountet sein.
- Einen isolierten Empty-Volume-Test ergänzen:
  - mit allen Gates `false` entstehen ausschließlich `001`–`003`;
  - mit dem Phase-4-Satz entstehen ausschließlich `001`, `002`, `003`, `005`, `006`, `007`;
  - `004` und `008` bleiben in beiden Fällen nicht angewendet.

## Aktualisiertes Gate

Das zuvor erteilte technische GO für Phase 4 wird durch diesen Ergänzungscheck **pausiert**, bis `G-041` geschlossen und der Empty-Volume-Negativtest bestanden ist. Die Zwei-Manifest-Strategie und das späte Einspielen von `compose.yaml` werden bestätigt. Danach genügt wieder ein kurzer Zielcheck; die übrige Phase-4-Vorbereitung muss nicht neu begonnen werden.

---

# Neunter Zielcheck – Nachprüfung `G-041`, Stand `eea959e`

## Urteil zu `G-041`

**`G-041` ist technisch geschlossen.**

- Der DB-Dienst mountet `postgres-init/` nicht mehr nach `/docker-entrypoint-initdb.d`.
- `registry-migrate` behält den einzigen kontrollierten Zugriff unter `/opt/startup/migrations` und respektiert die einzelnen Gates.
- Der statische Schutztest erkennt die ursprünglich gefährliche Mount-Zeile beim Wiedereinsetzen und lässt einen anderen, ungegateten Seed-Ordner bewusst zu.
- Das Empty-Volume-Testskript übernimmt den echten Runner aus `compose.yaml` statt ihn nachzubauen. Claudes NAS-Evidenz weist für geschlossene Gates genau `001`–`003`, für Phase 4 genau `001`–`003`,`005`–`007` und in beiden Fällen kein `004`/`008` aus. Die absichtlich wiederhergestellte Falle führt `004` aus und endet bei `007` mit einem abgebrochenen Container; der Test kann den ursprünglichen Fehler also tatsächlich erkennen.
- Unabhängig lokal: **282 + 15 + 35 + 9 = 341 Tests PASS**, Python- und Shell-Syntax sowie `git diff --check` PASS.
- Read-only auf der NAS bestätigt: keine `g041`-Container, keine `g041`-Netze und kein `/tmp/g041`; Evidenz- und Review-Dateien stimmen bytegleich mit dem lokalen Stand überein.

Der reale v7-DB-Container trägt den alten `/docker-entrypoint-initdb.d`-Mount erwartungsgemäß noch. Das ist kein neuer Produktivschaden: Das bestehende Volume ist nicht leer und auf der NAS liegen dort weiterhin nur `001`–`003`. Im Phase-4-Fenster muss der DB-Container aber zwingend mit `--force-recreate` ersetzt und der fehlende Mount danach am tatsächlichen Container geprüft werden.

Der zustandsändernde Empty-Volume-Test wurde in diesem Nachcheck nicht ein zweites Mal auf der NAS ausgeführt. Geprüft wurden Implementierung, Roh-Evidenz, Schutztest, vollständige lokale Tests und der aufgeräumte NAS-Nachzustand. Eine Wiederholung ohne eigenes Testgate hätte keinen zusätzlichen Produktivschutz erzeugt.

## `G-042` – Phase-4-Runbook verwendet falsche Laufzeitobjekte

**Schwere:** hoch – Ausführungsblocker des Rolloutfensters
**Datei:** `PHASE4_RUNBOOK.md`

`G-041` ist behoben, aber das mitgeänderte Runbook ist noch nicht ausführbar:

1. Zahlreiche Befehle verwenden `startup-postgres` und `startup-workforce-api`. Die realen Compose-Containernamen sind `startup-db-1` und `startup-workforce-api-1`; die falschen Namen existieren auf der NAS nicht.
2. Der Nachweis für Migration `005` fragt `workforce.bus_denial_audit` und `created_at` ab. Angelegt werden tatsächlich `workforce.bus_denials` und `occurred_at`.

### Kleinste sichere Korrektur

- Alle hart codierten Containernamen durch die realen Compose-Namen ersetzen oder – robuster – sämtliche Befehle über `docker compose exec -T db ...` und `docker compose exec -T workforce-api ...` ausführen.
- Auditabfrage auf `SELECT count(*), max(occurred_at) FROM workforce.bus_denials` korrigieren.
- Einen statischen Runbook-Test ergänzen, der unbekannte Container- und Tabellenbezeichner erkennt.

## Aktualisiertes Gate

Der **Codeblocker `G-041` ist aufgehoben**. Das technische GO zur tatsächlichen Phase-4-Ausführung bleibt ausschließlich wegen `G-042` pausiert. Nach dessen kleiner Korrektur genügt ein kurzer Runbook-Nachcheck; der Empty-Volume-Nachweis und die übrige Phase-4-Vorbereitung müssen nicht wiederholt werden.

---

# Zehnter Zielcheck – Runbook-Nachprüfung, Stand `c4abc84`

## Urteil zu `G-042`

**`G-042` ist geschlossen.**

- Alle containerbezogenen Runbook-Befehle verwenden jetzt `docker compose` und stabile Dienstnamen; `docker inspect` bezieht die Container-ID aus `docker compose ps -q`.
- Jeder Compose-Befehl startet im Projektordner `/volume1/docker/Startup`.
- Die Auditabfrage nennt jetzt die tatsächlich von Migration `005` erzeugten Bezeichner `workforce.bus_denials` und `occurred_at`.
- Der neue Wächter liest die Dienste aus `compose.yaml`, Tabellen und Spalten aus den im Fenster tatsächlich angewendeten Migrationen und erkennt die ursprünglichen Fehler beim absichtlichen Wiedereinsetzen.
- Unabhängig lokal: **299 + 15 + 35 + 9 = 358 Tests PASS**, Python- und Shell-Syntax sowie `git diff --check` PASS.
- Read-only auf der NAS bestätigt: die Dienste `db`, `registry-migrate` und `workforce-api` werden korrekt aufgelöst; `docker compose exec -T db ...` erreicht die laufende Datenbank als `workforce_app`.

## `G-043` – Runbook bleibt an drei realen Ausführungspunkten blockiert

**Schwere:** hoch – Ausführungsblocker des bereits freigegebenen Fensters
**Datei:** `PHASE4_RUNBOOK.md`

Der neue Namenswächter ist wirksam, deckt aber drei andere ausführbare Fehler im selben Runbook nicht ab:

1. **Die frischen Dumps und die Compose-Sicherung können nicht geschrieben werden.** Die Umleitungen in Abschnitt 3 und das `cp` in Abschnitt 5 laufen als `TOBKUM`. `/volume1/docker/Startup-Backups` ist nach `G-022` absichtlich nur für Root beschreibbar. Der direkte NAS-Nachweis ergibt `NOT_WRITABLE`; `HANDOVER.md` dokumentiert dieselbe Grenze bereits ausdrücklich. Das Fenster würde vor der ersten Sicherung mit `Permission denied` abbrechen.
2. **Der Ablehnungs-Audit-Test kann keinen Auditdatensatz erzeugen.** `/bus/messages` existiert nicht; der direkte NAS-Aufruf liefert `404`. Der echte Pfad ist `/bus/v1/messages`, erwartet `Authorization: Bearer ...` statt `X-API-Key` und wird bei dem im Fenster verbindlich `DISABLED` bleibenden Kanal bereits mit `503` abgewiesen, bevor `record_denial` erreicht wird. Eine bloße Pfadkorrektur reicht daher nicht.
3. **Die Testrolle bleibt zurück.** Der Negativtest erteilt `niemand` `USAGE` auf dem Schema und versucht danach unmittelbar `DROP ROLE niemand`. PostgreSQL verweigert das Löschen einer Rolle mit verbliebenen Berechtigungsabhängigkeiten. Vor `DROP ROLE` muss mindestens `DROP OWNED BY niemand` beziehungsweise ein ausdrückliches `REVOKE` erfolgen; die Bereinigung muss auch nach einem fehlgeschlagenen Negativtest laufen.

Zusätzlich verliert das Phase-4-Zielmanifest die Abdeckung von `check_secret_files.sh`, obwohl das Runbook dieses Skript unmittelbar ausführt. Das aktuelle Ist-Manifest führt die Datei; die Befehlslisten in Abschnitt 5 tun es nicht.

### Kleinste sichere Korrektur

- Dumps und Compose-Sicherung über einen nachweislich privilegierten, eng begrenzten Schreibweg erzeugen; danach Größe, Eigentümer `root:administrators`, Modus `640` und Lesbarkeit prüfen. Keine Lockerung des Backup-Ordners.
- Den Auditnachweis ohne Öffnen des Kanals durchführen, beispielsweise über den realen `record_denial`-Pfad im v8-API-Container oder die freigegebene Funktion `workforce.bus_record_denial` als `workforce_api`, mit eindeutiger Test-Request-ID und anschließender Abfrage genau dieses Datensatzes.
- Testrolle mit garantiertem `DROP OWNED BY niemand; DROP ROLE niemand` aufräumen und den Nichtbestand danach prüfen.
- `check_secret_files.sh` in Zielmanifest und Übertragung aufnehmen.
- Den Runbook-Wächter um Backup-Schreibweg, reale API-Routen beziehungsweise Auditpfad, Testrollen-Cleanup und alle im Runbook ausgeführten lokalen Hilfsskripte erweitern; jeweils mit Negativprobe.

## Aktualisiertes Gate

`G-041` und `G-042` bleiben geschlossen. Das bereits freigegebene Phase-4-Fenster **noch nicht starten**, bis `G-043` korrigiert und kurz nachgeprüft ist. Es ist keine Wiederholung der Migrationstests oder der übrigen Phase-4-Vorbereitung nötig; nur diese vier eng begrenzten Runbook-Punkte sind offen.

---

# Elfter Zielcheck – Nachprüfung `G-043`, Stand `0966cbb`

## Urteil

**`G-043` ist geschlossen. Technisches GO für das bereits freigegebene Phase-4-Fenster.**

- Dumps und Compose-Sicherung werden nun über einen eng begrenzten privilegierten Wegwerf-Container in den gehärteten Backup-Ordner geschrieben. Der Ordner bleibt unverändert geschützt; Eigentümergruppe `administrators` ist auf der NAS GID `101`, das benötigte Image `postgres:17-alpine` liegt lokal vor. Größe, Eigentümer, Modus und Lesbarkeit werden anschließend geprüft.
- Datenbank- und Rollen-Dump verwenden einen gemeinsamen Zeitstempel; `nas_status.sh` prüft jetzt das tatsächlich zusammengehörige Paar statt irgendeinen neuesten Rollen-Dump.
- Der Auditnachweis umgeht den verbindlich `DISABLED` bleibenden Kanal nicht: Er ruft `workforce.bus_record_denial` als `workforce_api` auf, prüft den eindeutig markierten Datensatz als Eigentümer und weist anschließend nach, dass `workforce_api` die Audit-Tabelle nicht lesen darf.
- Die temporäre Rolle wird in einem getrennten Aufräumschritt mit `DROP OWNED BY` und `DROP ROLE` entfernt; ihr Nichtbestand wird danach geprüft.
- `check_secret_files.sh` und zusätzlich `g041_empty_volume_test.py` stehen jetzt sowohl im Zielmanifest als auch in der Übertragungsliste.
- Die Schutztests decken Backup-Schreibweg, reale API-Routen, Testrollen-Cleanup, Hilfsskript-Abdeckung, Dump-Paarung und einen veralteten Runbook-Statuskopf jeweils mit Gegenproben ab.
- Unabhängig lokal: **318 + 15 + 35 + 9 = 377 Tests PASS**, Python- und Shell-Syntax sowie `git diff --check` PASS.
- Read-only auf der NAS bestätigt: alle geprüften Runbook-, Test- und Handover-Dateien sind bytegleich zum lokalen Stand; keine `g043`-Testreste; Manifest, Backup-Rechte und Gesamtstatus PASS.

## Freigabegrenze

Der Startpunkt ist unverändert und nachgemessen: API v7 und Datenbank gesund, Migrationen genau `001`–`003`, Kanal `DISABLED`, 0 aktive Credentials, `004`/`005` nicht angewendet und die neuen Rollen noch nicht vorhanden. Der Nachcheck selbst hat den Produktivstack nicht verändert.

Das Runbook kann nun für das bereits durch den CEO freigegebene Phase-4-Fenster von oben nach unten abgearbeitet werden. Verbindlich bleiben alle dort genannten Abbruch- und Rückfallkriterien; Knowledge `004`/`008`, Telegram, Modellaufrufe und externe Tests bleiben außerhalb dieses Fensters.
