# Workforce Agent

**Status:** gebaut, lokal getestet und im Echo-Trockenlauf auf der NAS bewährt. Betrieb mit einem echten Modell ist **nicht** freigegeben — `DEC-027` und `ENG-008` untersagen einen externen kostenpflichtigen Dienst.

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
- Budget erschöpft → Nachricht bleibt unberührt auf `DELIVERED`, ein späterer Lauf sieht sie
- Zu viele Fehlversuche → eine abschließende Antwort, danach kein weiterer Versuch
- Antwort zu lang → auf das Buslimit gekürzt

## Reihenfolge und Wiederaufsetzen

**Erst bearbeiten, antworten, dann bestätigen.** Das war einmal andersherum, und das war ein Fehler (Review-Befund G-001): Weil `poll_once()` nur `DELIVERED`-Nachrichten sieht, war eine Nachricht nach einem Absturz zwischen Bestätigung und Antwort dauerhaft verloren. Jetzt lässt ein Absturz an jeder Stelle davor die Nachricht `DELIVERED`, und der nächste Lauf sieht sie wieder.

Damit ein Wiederholungslauf nicht erneut für ein Modell bezahlt, führt `state_store.py` lokalen Zustand in SQLite: `IN_PROGRESS → REPLIED → DONE`, dazu `EXHAUSTED` nach zu vielen Versuchen. Steht eine Nachricht auf `REPLIED`, setzt der nächste Lauf direkt beim Bestätigen auf. Der Claim ist atomar (`BEGIN IMMEDIATE`) und hat eine Lease, damit ein abgestürzter Lauf nicht dauerhaft blockiert.

Das ist **kein** Audit — der Bus ist die verbindliche Aufzeichnung. Geht dieser Zustand verloren, kostet das höchstens einen wiederholten Modellaufruf.

Request-IDs und Idempotenzschlüssel werden deterministisch aus der Nachrichten-ID abgeleitet. Da der Bus seine `message_id` aus dem Idempotenzschlüssel bildet, erzeugt dieselbe eingehende Nachricht immer dieselbe ausgehende.

## Lokale Prüfung ohne Netzwerk

```text
python3 -m unittest discover -q
```

Kein Netzwerk, kein API-Schlüssel, keine Kosten. Braucht Python 3.11 oder neuer.

## Secret-Zuführung der Hilfscontainer

Alle Einmalcontainer dieses Pakets — Prepare, Cleanup, Identity, Audit — brauchen genau drei Werte: `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`. Sie bekommen deshalb nicht `startup.env` (fünf Werte), sondern die daraus abgeleitete `startup.db.env`:

```bash
sudo sh workforce-agent/derive_db_env_once.sh
```

Einmal auf der NAS, in `/volume1/docker/Startup`, und erneut nach jeder Änderung an `startup.env`. Die Datei wird `root:users` mit `660` angelegt — genau wie `startup.env`, damit die Container sie als Eigentümer lesen können; `cap_drop: ALL` nimmt ihnen `CAP_DAC_OVERRIDE`.

**Der `run`-Container des Core-Roundtrips bekommt gar keine Secret-Datei.** Er ist der einzige mit einer Route nach draußen und fasst die Datenbank nie an; er liest nur die drei kurzlebigen Token unter `./secrets`. Das war Review-Befund `G-017`: Vorher lag dort die vollständige `startup.env` — nicht in `docker inspect`, aber sehr wohl im Dateisystem.

Zwei Prüfungen halten das fest:

| Prüfung | Wo | Was |
|---|---|---|
| `test_compose_secrets.py` | lokal, ohne Netz | keine Compose-Datei mountet `startup.env`; kein Dienst am `outbound`-Netz trägt überhaupt eine geteilte Secret-Datei |
| `verify_secret_isolation_once.sh` | NAS | dasselbe am laufenden Container, gegen Umgebung **und** lesbares Dateisystem — ohne je einen Wert auszugeben |

## Vor einem echten Lauf

Nicht ausführen, bevor das nicht steht:

1. ~~Bus-Identität und Credential~~ — erledigt: `AGENT-ENG-001` existiert, `compose.prepare.yaml` gibt den Zugang aus.
2. ~~Eigenes Security-Review~~ — erledigt: `evidence/2026-08-31_security_review_agent.md`.
3. ~~Erster Trockenlauf mit `echo`~~ — erledigt: `evidence/2026-08-31_agent_dryrun.md`.
4. **Eine Entscheidung, die den kostenpflichtigen Modellbetrieb überhaupt erlaubt.** `DEC-027` und `ENG-008` untersagen ihn ausdrücklich („keine neuen kostenpflichtigen externen Dienste", „kein externer kostenpflichtiger Dienst"). Ohne neue CEO-Entscheidung ist `AGENT_PROVIDER=claude` gesperrt.
5. Entscheidung über `AGENT_DATA_POLICY` und gegebenenfalls `AGENT_DATA_POLICY_OVERRIDES`.
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

- **Kein Claim über die Bus-API** (Review-Befund G-002, halb erledigt). Der Claim in `state_store.py` ist atomar, aber an ein Volume gebunden — zwei Worker mit getrennten Volumes könnten dieselbe Nachricht bearbeiten. Der saubere Endzustand wäre ein Claim auf API-Ebene, was einen neuen Endpunkt und eine Migration bedeutet. Heute existiert genau ein Worker.
- **Kein dauerhafter Ausführungsnachweis** (G-009, für den Agenten offen). Provider, Modell, Policy und Versuch stehen nur im stdout-Protokoll; nach Containerrückbau sind sie weg. Für den Core-Roundtrip ist die Audit-Rekonstruktion gelöst, für den Agenten nicht.
- **Freigabeentscheidung** (`DEC-`Nummer) für den Modellbetrieb — siehe oben, derzeit ausdrücklich untersagt.
- **Die Rückrichtung zu Telegram** ist jetzt über `TELEGRAM_OUTBOUND_POLICY` konfigurierbar, steht aber weiter auf `METADATA_ONLY` — eine Agentenantwort würde per Telegram nur angekündigt, nicht lesbar zugestellt. Auch das ist eine Entscheidung, keine Voreinstellung.
