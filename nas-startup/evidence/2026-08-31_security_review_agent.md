# Security-Review Agentenschicht

**Datum:** 2026-08-31
**Gegenstand:** `workforce-agent/` (`agent_worker.py`, `data_boundary.py`, `providers.py`, `budget.py`, `bus_client.py`, Prepare-/Cleanup-Paket), sowie die Rückrichtung in `telegram-connector/telegram_connector.py`
**Grundlage:** Codeanalyse, 44 lokale Tests, der Echo-Trockenlauf vom selben Tag (`2026-08-31_agent_dryrun.md`) und der Laufzeitzustand der NAS
**Zweck:** Gate für den ersten Betrieb mit einem echten Modell

## Gesamturteil

Die Absicherung gegen Prompt-Injection trägt. Sie beruht nicht auf Formulierungen im System-Prompt, sondern auf drei strukturellen Eigenschaften, die ich einzeln geprüft habe: Der Agent hat keine Werkzeuge, das Routing kommt nie aus Modellausgabe, und der Bus setzt seine eigenen Kontrollen unabhängig durch. Eine erfolgreiche Injection bleibt damit ein Qualitätsproblem der Antwort.

**Der Befund, der den Betrieb blockiert, ist ein anderer: Der Agent handelt unter der Identität eines Menschen.**

**Empfehlung:** Modellbetrieb zurückstellen, bis A1 behoben ist. A2 und A3 vor Dauerbetrieb. Alles Übrige ist vertretbar.

## Was nachweislich hält

| Kontrolle | Prüfung | Ergebnis |
|---|---|---|
| Werkzeuglosigkeit | `Provider.complete()` nimmt Text, gibt Text | keine Tool-Schleife, kein Datei- oder Netzzugriff für das Modell |
| Routing nicht modellgesteuert | Empfänger aus dem Bus-Datensatz | `test_injected_instructions_cannot_redirect_the_reply` |
| Datengrenze einziger Ausgang | `grep` über alle Aufrufstellen | genau **ein** Aufruf, hinter `prepare_outbound()` |
| Feld-Allowlist | unbekannte Felder werden verworfen | `test_fields_outside_the_allowlist_never_leave` |
| Grenze hält im Echtbetrieb | Trockenlauf, vier Nachrichten | `body_included: false` in allen vier Zeilen |
| Budget vor Bestätigung | erschöpftes Budget lässt Nachricht `DELIVERED` | `test_exhausted_budget_leaves_the_message_untouched` |
| Fehlerpfade enden in einer Antwort | Provider-Ausfall, Grenzverletzung | jeweils eigener Test, im Trockenlauf zweimal real ausgelöst |
| Idempotenz | Schlüssel deterministisch aus `message_id` | ein Neustart erzeugt keine zweite Antwort |
| Protokollierung ohne Inhalte | `Disclosure`, `Reply.as_log_record()` | `test_disclosure_record_carries_no_content` |
| Container-Härtung | `read_only`, `cap_drop: ALL`, UID 10001 | wie im übrigen Projekt |

## Befunde

### A1 — Der Agent handelt unter der Identität eines Menschen (hoch, blockierend)

Der Agent nutzt das Credential von `AI-ENG-001`. Der Registry-Eintrag dazu:

```text
employee_id       | AI-ENG-001
display_name      | Gerd
role_title        | AI Engineer / KI-Systemarchitekt
employment_status | PROBATION
```

Das ist ein Personendatensatz. Jede Antwort, die der Agent erzeugt, erscheint im Bus als Nachricht von Gerd — nicht unterscheidbar von einer, die Gerd selbst geschrieben hätte. Es gibt keinen Vermerk im Nachrichtentext, keine abweichende Rolle, kein Feld, an dem ein Empfänger die maschinelle Herkunft erkennen könnte.

Das Projekt hat für genau dieses Problem bereits die richtige Antwort gefunden — an anderer Stelle. Der Telegram-Connector bekam eine eigene Identität:

```text
employee_id | CEO-TG-002
role_code   | SYSTEM_CONNECTOR
role_title  | Technical Acceptance Connector – not an employee
```

Der Titel sagt es ausdrücklich. `DEC-026` nennt es „ausdrücklich kein Mitarbeiter und keine CEO-Imitation". Für den Agenten wurde dieselbe Sorgfalt nicht angewendet.

Die Folge ist nicht theoretisch: Wenn Karl eine Antwort von „Gerd" liest und danach handelt, hält er sie für die Einschätzung eines Kollegen in der Probezeit. Bei einer falschen Antwort ist unklar, wem sie zuzurechnen ist — und ein Mensch, dem maschinelle Aussagen zugerechnet werden, kann sich nicht dagegen wehren.

Erschwerend: „Gerd" ist zugleich der Name, unter dem der zweite Assistent im Projekt auftritt. Drei Dinge teilen sich einen Namen.

**Empfehlung:** Eine eigene Identität nach dem Muster von `CEO-TG-002` — etwa `AGENT-ENG-001`, `role_code = SYSTEM_AGENT`, Titel mit ausdrücklichem „not an employee". Zusätzlich ein Herkunftsvermerk am Anfang jeder Antwort. Beides zusammen, nicht eines davon: Die eigene Identität schützt die Zurechnung, der Vermerk schützt den Leser, der nur den Text sieht.

### A2 — Kein Herkunftsvermerk in der Antwort (mittel)

Auch unabhängig von A1: Der Antworttext ist reine Modellausgabe. Wer ihn per Telegram bekommt oder in der Weboberfläche liest, sieht keinen Hinweis darauf, dass er maschinell erzeugt wurde. Das Telegram-Format zeigt nur `NACHRICHT … von …` — bei `TELEGRAM_OUTBOUND_POLICY=BODY` steht der Text dann ohne jede Einordnung im Chat.

**Empfehlung:** Eine feste, nicht vom Modell beeinflussbare Zeile, die der Worker voranstellt. Sie darf nicht Teil des System-Prompts sein — was das Modell schreibt, kann das Modell auch weglassen.

### A3 — Keine zeitliche Obergrenze für einen Lauf (mittel)

Die vier Decken in `budget.py` begrenzen Nachrichten, Aufrufe, Token und Kosten. Keine begrenzt die **Laufzeit**. Der Claude-Provider arbeitet mit 120 Sekunden Zeitlimit und drei Wiederholungen, also bis etwa sechs Minuten je Aufruf. Bei der Voreinstellung von 25 Nachrichten sind das im ungünstigsten Fall über zwei Stunden, in denen ein Credential gültig bleiben müsste — es läuft aber nach 30 Minuten ab. Der Lauf endet dann mitten in der Arbeit mit `BUS_AUTH_FAILED` auf jeder weiteren Nachricht.

Kein Sicherheitsloch, aber ein absehbarer Betriebsfehler.

**Empfehlung:** `AGENT_MAX_RUNTIME_SECONDS` als fünfte Decke, Voreinstellung deutlich unter der Credential-Laufzeit.

### A4 — Kostendecke ist rückblickend (niedrig, dokumentiert)

Kosten stehen erst fest, wenn ein Aufruf zurückkommt. Die Decke kann daher um einen Aufruf überschritten werden. Das ist im Modul dokumentiert und der Grund, warum Aufruf- und Tokendecken daneben stehen. Bei Opus-5-Preisen und `max_tokens = 4096` liegt die mögliche Überschreitung bei etwa zehn Cent.

Kein Handlungsbedarf, gehört aber in die Betriebsdokumentation, damit niemand die Kostendecke für eine harte Grenze hält.

### A5 — Kein Rückzug bei anhaltendem Busausfall (niedrig)

`run()` protokolliert `poll_failed` und wartet dann das reguläre Intervall. Ist der Bus längere Zeit weg, fragt der Agent unverändert weiter an, ohne Verzögerungsanstieg und ohne Abbruch nach wiederholtem Fehlschlag.

**Empfehlung:** Zähler für aufeinanderfolgende Fehlschläge mit Abbruch, plus wachsendes Warteintervall.

### A6 — Schlüssel per Umgebungsvariable weiterhin möglich (niedrig)

`read_api_key()` bevorzugt die Datei, akzeptiert aber `ANTHROPIC_API_KEY` als Rückfall. Wer die Variable setzt, macht den Schlüssel in `docker inspect` sichtbar. Der Rückfall ist bequem für lokale Versuche und in den Compose-Dateien nicht verwendet.

**Empfehlung:** Belassen, aber im README als ausdrücklich nicht für die NAS gedacht kennzeichnen.

### A7 — Die Kette endet nicht beim Menschen (informativ)

Der Agent schreibt seine Antwort in den Bus. Ob sie jemanden erreicht, hängt am Telegram-Connector — und der lief bisher nie zusammen mit der Agentenschicht. Solange `TELEGRAM_OUTBOUND_POLICY` auf `METADATA_ONLY` steht, kommt ohnehin nur die Ankündigung an, nicht der Text.

Kein Sicherheitsbefund, aber die Zielkette ist damit noch nicht geschlossen.

## Zur Injection-Absicherung im Besonderen

Die Argumentation lautet: Injection kann höchstens den Antworttext verfälschen, weil der Agent nichts anderes tun kann als antworten. Ich habe die Voraussetzungen einzeln geprüft und sie halten heute.

Zwei Dinge, die sie umwerfen würden:

1. **Werkzeuge für den Agenten.** Sobald `complete()` etwas anderes als Text zurückgeben kann, ist die Kette offen. Das steht als nicht verhandelbarer Grundsatz in `AGENTS.md`.
2. **Antworten, die weiterverarbeitet werden.** Heute wird die Modellausgabe ausschließlich als Nachrichtentext verwendet. Würde jemand sie parsen — Kommandos, Task-IDs, Empfänger daraus lesen —, wäre das ein neuer Weg vom Inhalt zur Handlung.

Der zweite Punkt ist der leiser eintretende. Er sähe wie eine Bequemlichkeit aus („der Agent soll auch Tasks anlegen können") und wäre eine Änderung des Bedrohungsmodells.

## Bewertung

| Befund | Schwere | Vor Modellbetrieb | Vor Dauerbetrieb |
|---|---|---|---|
| A1 Identität eines Menschen | hoch | **erforderlich** | erforderlich |
| A2 Kein Herkunftsvermerk | mittel | empfohlen | erforderlich |
| A3 Keine Laufzeitgrenze | mittel | empfohlen | erforderlich |
| A4 Kostendecke rückblickend | niedrig | dokumentieren | dokumentieren |
| A5 Kein Rückzug bei Ausfall | niedrig | — | empfohlen |
| A6 Schlüssel per Variable | niedrig | — | kennzeichnen |
| A7 Kette endet nicht beim Menschen | informativ | — | — |

Weiterhin offen und außerhalb dieses Reviews: die Entscheidung über `AGENT_DATA_POLICY`, eine Freigabeentscheidung für den Modellbetrieb, und die Frage, ob `TELEGRAM_OUTBOUND_POLICY` auf `BODY` gehen soll.
