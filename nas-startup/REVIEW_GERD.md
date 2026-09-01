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
