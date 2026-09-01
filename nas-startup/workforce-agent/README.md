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
| ~~`subscription`~~ | **Zurückgezogen** (Befund `G-016`). |

Ein weiterer Provider braucht nur `complete()` und einen Eintrag in `build_provider()`. Sonst ändert sich nichts.

**Warum `subscription` zurückgezogen ist.** Der Provider startete eine werkzeugfähige CLI mit `subprocess.run()` — im Worker-Container, also genau dort, wo das Bus-Token, der State-Mount und die Route zum Bus liegen. Sein eigener Docstring verlangte einen Container ohne all das. Das Leeren der geerbten Umgebung nimmt Variablen weg, nicht das Dateisystem und nicht das Netz.

Ein Kommentar, der eine Absicherung behauptet, die es nicht gibt, ist schlimmer als eine fehlende Absicherung: Er hält den nächsten Leser vom Nachprüfen ab. `build_provider()` weist `AGENT_PROVIDER=subscription` deshalb ab. Die Klasse bleibt als Spezifikation stehen — was für eine Reaktivierung existieren muss, steht in ihrem Docstring.

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

## Der Worker-Core-Test

Der Nachweis, den `ENG-008` verlangt und den `core_roundtrip.py` **nicht** erbringt (Befund `G-015`): Dort steuern drei Bus-Clients den Ablauf direkt — `agent_worker.py` und `state_store.py` kommen gar nicht vor.

`worker_core_test.py` lässt die echte Laufzeit arbeiten: `agent_worker.poll_once()`, den echten `AgentStateStore` auf einer echten Datei, die echte Datengrenze, das echte Budget. Einziger Platzhalter ist das Modell — und das ist die Anforderung, nicht die Abkürzung: `DEC-027` und `ENG-008` schließen einen externen kostenpflichtigen Dienst aus.

| Szenario | Was es beansprucht |
|---|---|
| **A** Gutfall | beantwortet, bestätigt, `DONE` |
| **C** Absturz vor der Bestätigung | Antwort liegt im Bus, ACK fällt aus, **Prozess startet neu** und setzt fort — bewiesen durch einen Provider, der beim Aufruf laut scheitert |
| **B** wiederholbarer Fehler | zwei verworfene Antworten, dann Erfolg — am Ende genau **eine** Antwort im Bus |
| **D** Erschöpfung | Antworten scheitern über `max_attempts` hinaus, **und die Schlussmeldung scheitert auch**. Der Lauf, der den Übergang nach `EXHAUSTED` verbraucht, ist der, der stirbt — genau der Fall aus `G-012` |
| **E** verlorener Zustand | die State-Datei wird zwischen zwei Läufen gelöscht. Der Store kann nichts mehr verhindern; die **Bus-Idempotenz** muss die Antwort einzeln halten |
| **F** verbotene Route | der Bus lehnt eine Nachricht des Agenten an sich selbst ab — die Kontrolle, auf der das ganze Injection-Argument ruht |

**Szenario E kam nachträglich dazu, und der Grund ist der interessante Teil.** Die erste Fassung der Suite ließ einen absichtlich kaputten, nicht-idempotenten Bus durchgehen. Sie bestand, weil der Worker bei intakter State-Datei ohnehin nie zweimal sendet — die Bus-Idempotenz wurde nie erreicht. Die Einmaligkeit in A bis D trägt der State Store; E ist das Szenario, das die zweite Verteidigungslinie tatsächlich belastet. Nebenbei benennt es die echten Kosten eines verlorenen Volumes: ein wiederholter Modellaufruf je Nachricht in Arbeit — keine verlorene und keine doppelte Antwort.

**Wie die Fehler eingespeist werden.** Ein wiederholbarer Fehler lässt sich vom echten Bus nicht bestellen, also injiziert ihn ein Client-Wrapper. Der wirft **vor** dem Delegieren: Die Anfrage erreicht den Bus nie, was genau dem Bild einer abgebrochenen Verbindung entspricht. Er tut nie so, als hätte der Bus etwas abgelehnt, das er angenommen hat, und jeder verworfene Aufruf steht im Protokoll.

**Der Neustart ist auf der NAS ein echter.** `compose.workercore.yaml` fährt `phase1` und `phase2` als **zwei Container** über demselben State-Volume. Phase 2 bekommt von Phase 1 nichts außer dem Bus und dem Volume: Sie sendet dieselben Anfragen mit denselben Idempotenzschlüsseln erneut und bekommt dieselben Nachrichten-Ids zurück. Lokal entspricht dem ein frischer Store über derselben Datei — das, was ein neuer Prozess vorfindet.

```bash
cd nas-startup/workforce-agent && python3 -m unittest test_worker_core_test -v
```

**Noch nicht auf der NAS gelaufen.** Der Lauf braucht `AGENT-ENG-001` in der Registry, die Migration `004`, die API `v8`, zwei kurzlebige Zugänge und die temporäre Firewall-Regel. `workercore_prepare.sql` prüft jede dieser Voraussetzungen und bricht ab, statt halb zu laufen.

## Was der Audit belegt — und was nicht

`workforce.bus_events` enthält ausschließlich **erfolgreiche** Vorgänge. Eine abgelehnte Bus-Operation wirft, ihre Transaktion rollt zurück und nimmt jede darin geschriebene Audit-Zeile mit. Die drei geforderten Ablehnungen des Core-Roundtrips lebten deshalb nur in stdout und in handgeschriebenem Markdown — beides weg, sobald der Container weg ist (Befund `G-018`).

Migration `005_bus_denial_audit` schließt das mit `workforce.bus_denials`: append-only, geschrieben von der API **nach** dem Fehlschlag auf einer frischen Verbindung — der einzigen Stelle, an der es überhaupt möglich ist.

Was dort landen darf, ist eng: Identitäten, Bezeichner, stabiler Fehlercode, HTTP-Status. Kein Betreff, kein Nachrichtentext, keine Notiz, kein Token. Das erzwingen `CHECK`-Bedingungen — ein Nachrichtentext ist weder ein gültiger Fehlercode noch eine gültige Operation. `postgres-tests/005_bus_denial_audit_acceptance.sql` versucht genau das und verlangt, dass es scheitert.

`core_audit.sql` weist seither zwei Hälften getrennt aus:

| Hälfte | Quelle | Was geprüft wird |
|---|---|---|
| Positiv | `bus_events` | elf Schritte, jeder an die exakte Datensatz-Id, den Akteur, Sender/Empfänger und die Task-Referenz gebunden — plus die **vollständige** Reihenfolge, nicht zwei Stichproben |
| Negativ | `bus_denials` | die drei geforderten Ablehnungen mit Akteur, Fehlercode und HTTP-Status |

Fehlt die Migration, bricht das Negativ-Audit ab, statt eine leere Menge als Bestehen zu melden.

**Noch nicht ausgeführt.** Migration, API-Änderung (`v8`) und die neue Audit-Abfrage sind auf diesem Mac nicht gegen ein echtes PostgreSQL gelaufen — hier gibt es weder `psql` noch Docker. Das braucht einen Lauf auf der NAS mit Freigabe.

## Vor einem echten Lauf

Nicht ausführen, bevor das nicht steht:

1. **Bus-Identität und Credential** — `agent_identity_create.sql` legt `AGENT-ENG-001` an, und `agent_prepare.sql` setzt voraus, dass es die Identität gibt. **Ob sie auf der NAS existiert, ist nicht belegt.** Eine frühere Fassung dieser Zeile behauptete „erledigt"; der Trockenlauf lief nachweislich unter `AI-ENG-001`, und `HANDOVER.md` führt `agent_identity_create.sql` als nicht ausgeführt. Vor dem nächsten Lauf gegen die Registry nachsehen, nicht gegen die Dokumentation (Befund `G-019`).
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
