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
