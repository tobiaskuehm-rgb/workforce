# Workforce Agent

**Status:** gebaut und lokal getestet (27 Tests), noch nie auf der NAS ausgeführt. Kein Dauerbetrieb freigegeben.

Das fehlende Glied in der Kette. Bisher:

```
Telegram → Connector → Bus → PostgreSQL → (nichts)
```

Mit dieser Komponente:

```
Telegram → Connector → Bus → Agent → Modell → Bus → Connector → Telegram
```

Der Agent liest die Inbox **einer** Bus-Identität, lässt ein Modell antworten und schreibt die Antwort als Bus-Nachricht an den ursprünglichen Absender zurück.

## Warum das gegenüber einem Sprachmodell verantwortbar ist

Das Security-Review vom 2026-08-31 hat die neue Risikoklasse benannt: Sobald ein Agent Nachrichteninhalte liest und daraufhin handelt, kann ein Nachrichtentext Anweisungen an den Agenten enthalten. Ein System-Prompt allein ist dagegen keine Kontrolle — er lässt sich überreden.

Die Absicherung ist deshalb **strukturell**:

| Kontrolle | Umsetzung |
|---|---|
| **Der Agent hat keine Werkzeuge** | `Provider.complete()` nimmt Text und gibt Text zurück. Keine Tool-Schleife, kein Datei- oder Systemzugriff, kein für das Modell erreichbares Netz. |
| **Das Routing kommt nie vom Modell** | Empfänger ist der Absender aus dem Bus-Datensatz. Die Modellausgabe wird für genau eine Sache verwendet: den Text der Antwort. |
| **Der Bus greift unabhängig weiter** | Routen-Allowlist, Schleifenlimit, Größenlimit und Kill Switch gelten für jeden Schreibvorgang — nachgewiesen durch die 20 Negativtests. |
| **Die Datengrenze ist eine Funktion** | Alles, was zu einem Provider geht, läuft durch `data_boundary.prepare_outbound()`. |

Damit ist eine erfolgreiche Prompt-Injection ein **Qualitätsproblem der Antwort**, kein Eskalationspfad. Das Schlimmste, was sie erreicht, ist eine falsche oder unhöfliche Antwort an denjenigen, der die Anfrage gestellt hat.

**Das gilt nur, solange der Agent werkzeuglos bleibt.** Bekommt er je Werkzeuge, bricht diese Argumentation zusammen und das Bedrohungsmodell muss neu aufgestellt werden. Der Test `test_injected_instructions_cannot_redirect_the_reply` hält die Eigenschaft fest.

## Die Datengrenze

`data_boundary.py` ist der einzige Ort, an dem Daten die NAS verlassen. Die Frage „was genau geht an die KI?" hat genau eine Antwort, in einer Datei.

| Policy | Was übertragen wird |
|---|---|
| `METADATA_ONLY` | Betreff, Aktionsklasse, IDs — **nie** der Nachrichtentext. Voreinstellung. |
| `BODY` | zusätzlich der Nachrichtentext. Nötig, damit ein Modell fachlich arbeiten kann. |
| `FULL` | zusätzlich Task- und Handoff-Referenzen. |

Eine Feld-Allowlist begrenzt das zusätzlich: Felder, die dort nicht stehen, können nicht hinausgehen, selbst wenn eine künftige Bus-Version sie dem Datensatz hinzufügt. Ein zweites, lokales Größenlimit (8000 Zeichen) gilt unabhängig vom Kanallimit.

Jeder Aufruf erzeugt eine `Disclosure`: Feldnamen, Zeichenzahl und ein SHA-256-Fingerabdruck — **nie der Inhalt**. Die landet im Protokoll. So ist nachvollziehbar, was das Haus verlassen hat, ohne es an einer zweiten Stelle zu kopieren.

## Provider

| Name | Beschreibung |
|---|---|
| `echo` | Deterministisch, kein Netzwerk, kein Schlüssel, keine Kosten. Für Tests und den ersten Trockenlauf. |
| `claude` | Anthropic-API über das offizielle SDK, Modell `claude-opus-5`. |

Ein weiterer Provider braucht nur `complete()` und einen Eintrag in `build_provider()`. Sonst ändert sich nichts.

Der Claude-Provider behandelt eine Modell-Ablehnung (`stop_reason: refusal`) als regulären Fall und schreibt eine erklärende Antwort in den Bus, statt abzustürzen. Server-seitige Fallbacks sind aktiviert, damit ein Grenzfall nicht stumm im Bus liegen bleibt.

## Verhalten bei Fehlern

Jeder Fehlerpfad endet mit einer Antwort im Bus — nie mit stillem Verschlucken:

- Provider nicht erreichbar → Antwort nennt den Fehlercode und bittet um manuelle Prüfung
- Datengrenze verletzt → Antwort nennt die Verletzung; **nichts** erreicht den Provider
- Bereits bestätigte Nachricht → kein Fehler, der vorherige Lauf kam bis hierher
- Antwort zu lang → auf das Buslimit gekürzt

Bestätigt wird **vor** der Bearbeitung. Scheitert danach etwas, sieht der Absender trotzdem, dass die Nachricht angekommen ist, und bekommt eine erklärende Antwort.

Request-IDs und Idempotenzschlüssel werden deterministisch aus der Nachrichten-ID abgeleitet. Da der Bus seine `message_id` aus dem Idempotenzschlüssel bildet, erzeugt dieselbe eingehende Nachricht immer dieselbe ausgehende — ein Neustart nach Absturz antwortet nicht doppelt.

## Lokale Prüfung ohne Netzwerk

```text
python3 -m unittest discover -v
```

27 Tests, keine Netzwerkverbindung, kein API-Schlüssel, keine Kosten.

## Vor einem echten Lauf

Nicht ausführen, bevor das nicht steht:

1. Eine Bus-Identität für den Agenten und ein kurzlebiges `ACCEPTANCE`-Credential — analog zum Realtest-Paket. Der Agent hat heute **kein** eigenes Prepare-Skript.
2. Eine ausdrückliche Freigabeentscheidung mit engem Scope, wie bei `DEC-026` und `DEC-027`.
3. Entscheidung über `AGENT_DATA_POLICY`. Voreinstellung ist `METADATA_ONLY`; für echte fachliche Arbeit braucht es `BODY`, und das ist die Entscheidung, die im Security-Review offengeblieben ist.
4. Ein eigenes Security-Review für die Agentenschicht.
5. Erster Lauf mit `AGENT_PROVIDER=echo` und `AGENT_MAX_CYCLES=1` — belegt den gesamten Bus-Weg, ohne dass ein einziges Byte die NAS verlässt.
6. Temporäre Firewall-Regel für `172.31.254.2/32` auf TCP 8443, danach wieder entfernen.

## Harte Grenzen für einen Lauf

`budget.py`, fünf voneinander unabhängige Decken. Jede einzelne beendet den Lauf:

| Decke | Voreinstellung | Wozu |
|---|---:|---|
| `AGENT_MAX_MESSAGES` | 25 | wie viele Nachrichten überhaupt bearbeitet werden |
| `AGENT_MAX_PROVIDER_CALLS` | 25 | wie oft ein Modell gefragt wird |
| `AGENT_MAX_TOKENS` | 200 000 | Ein- und Ausgabetoken zusammen |
| `AGENT_MAX_COST_USD` | 1,00 | geschätzte Ausgaben |
| `AGENT_MAX_RUNTIME_SECONDS` | 900 | Laufzeit |

Zwei Eigenschaften, die dabei zählen:

**Geprüft wird vor der Bestätigung, nie danach.** Ein erschöpftes Budget lässt die Nachricht unberührt auf `DELIVERED` stehen, damit ein späterer Lauf sie noch sieht. Bestätigen und dann die Arbeit verweigern würde sie stillschweigend verschlucken.

**Die Kostendecke ist rückblickend — mit einer Ausnahme.** Kosten stehen erst fest, wenn ein Aufruf zurückkommt; die Decke kann also um einen Aufruf überschritten werden. Die Aufruf- und Tokendecken begrenzen deshalb vorausschauend, Geld ist der Rückhalt dahinter.

Die Ausnahme ist die Decke `0`. Jeder Provider deklariert über `is_paid`, ob er Geld kostet, und ein kostenpflichtiger Provider wird unter einer Nulldecke **vor** dem ersten Aufruf abgewiesen — nicht danach. Ein Provider, der die Angabe vergisst, gilt als kostenpflichtig; die Voreinstellung irrt in Richtung Ablehnung. Der Echo-Provider läuft unter `0` weiter, weil er nichts kostet.

Damit heißt eine Decke von `0` genau das, wonach es aussieht: „dieser Lauf darf nichts kosten".

Die Laufzeitdecke gibt es, weil die anderen vier Arbeit begrenzen, nicht Zeit. Ein `ACCEPTANCE`-Zugang gilt 30 Minuten; ohne Zeitdecke liefe ein Lauf an seinem eigenen Credential vorbei.

## Herkunftsvermerk

Jede Antwort beginnt mit einer festen Zeile, die der Worker voranstellt:

```text
[Maschinell erzeugte Antwort. Vor Verwendung fachlich pruefen.]
```

Bewusst **nicht** über den System-Prompt: Was das Modell schreiben soll, kann das Modell auch weglassen. Eine überlange Antwort kann den Vermerk nicht verdrängen — er wird nach dem Kürzen gesetzt.

## Noch offen

- **Der Agent handelt unter der Identität eines Menschen** (Security-Review A1, blockierend). Er nutzt das Credential von `AI-ENG-001` — „Gerd", `AI Engineer`, `PROBATION`. Antworten erscheinen im Bus als Nachrichten einer Person. `agent_identity_create.sql` legt `AGENT-ENG-001` nach dem Muster von `CEO-TG-002` an, ist aber **noch nicht ausgeführt**: eine dauerhafte Registry-Änderung braucht eine Freigabeentscheidung.
- **Entscheidung zur Datengrenze.** Voreinstellung `METADATA_ONLY`; fachliche Arbeit braucht `BODY`.
- **Freigabeentscheidung** (`DEC-`Nummer) für den Modellbetrieb.
- **Die Rückrichtung zu Telegram** ist jetzt über `TELEGRAM_OUTBOUND_POLICY` konfigurierbar, steht aber weiter auf `METADATA_ONLY` — eine Agentenantwort würde per Telegram nur angekündigt, nicht lesbar zugestellt. Auch das ist eine Entscheidung, keine Voreinstellung.
