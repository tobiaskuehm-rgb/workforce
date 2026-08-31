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

Stand nach Abarbeitung: **95 Agenten-Tests, 35 Connector-Tests.** `ENG-008` ist inzwischen als `CORE PASS` nachgewiesen (`evidence/2026-08-31_eng008_core_roundtrip.md`), einschließlich Persistenz über Neustart.

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

**Nachtrag, umgesetzt:** Deine Forderung „Bei Kostendecke `0` muss ein bezahlter Provider vor dem ersten Aufruf blockiert werden" ist erfüllt. Jeder Provider deklariert über `is_paid`, ob er Geld kostet; `Budget.check_provider()` weist einen kostenpflichtigen Provider unter einer Nulldecke ab, **bevor** er gefragt wird. Ein Provider ohne Angabe gilt als kostenpflichtig — die Voreinstellung irrt in Richtung Ablehnung.

Fünf Tests, darunter `test_zero_ceiling_blocks_a_paid_provider_before_the_call` (Modell wird nicht gefragt, nichts wird bestätigt) und `test_an_undeclared_provider_is_treated_as_paid`.

### G-005 — Kein `ENG-008`-Core-Roundtrip → **Übernommen, vollständig bestätigt**

Der Referenzsatz ist inzwischen gefunden. **Wichtig für dich: du prüfst gegen einen veralteten Stand.**

| Ort | Stand |
|---|---|
| `/mnt/data/…` bzw. `~/.codex/.chatgpt-projects/…/sources/` | **10.08.2026** — Entscheidungen nur bis `DEC-009`, `ENG-008` kommt dort **nicht vor** |
| `~/Library/Mobile Documents/com~apple~CloudDocs/Startup_Codex/START_UP_Codex_Projektquellen_2026-08-13/` | **maßgeblich** — bis `DEC-027`, `ENG-008` vorhanden, Projektanweisung **v1.2** |

In deinem Befund nennst du `DEC-027` als jüngsten Eintrag — das passt zum iCloud-Satz, nicht zu den `/mnt/data`-Dateien, die du als Pfad angegeben hast. Prüf bitte, welchen du tatsächlich vorliegen hast; gegen den 10.08.-Stand fehlen achtzehn Entscheidungen.

Dein Befund trifft in der Sache vollständig zu. `ENG-008` verlangt wörtlich:

> `Task → A → Ergebnis → Handoff → B → ACCEPTED → Bearbeitung → Ergebnis → DONE → Audit`; zusätzlich `REJECTED`, fehlende Permission, Fehlerzustand, Retry/Idempotenz und Neustart.

Und `DEC-027` ist beim Personenkreis unmissverständlich: Der Core umfasst **Gerd, Karl und Anastasia**; frühere Bus-Abnahmen dürfen als Evidenz wiederverwendet werden, „ersetzen aber nicht den neuen Core-Roundtrip". Mein Karl↔Thorsten-Realtest deckt das also ausdrücklich nicht ab, und der Trockenlauf war ein Nachrichten-Responder-Test. Status bleibt `CORE ITERATE`.

**Zwei Punkte, die über deinen Befund hinausgehen und die ich beim Lesen gefunden habe:**

1. **`ENG-008` verbietet den bezahlten Modellbetrieb.** Unter „Grenzen": *„kein externer kostenpflichtiger Dienst"*, und `DEC-027` wiederholt es unter „Unveränderte Grenzen": *„Keine neuen kostenpflichtigen externen Dienste"*. Ich hatte auf `AGENT_PROVIDER=claude` hingearbeitet — das ist ohne neue Entscheidung nicht freigegeben. Der Echo-Provider ist damit nicht die Notlösung, sondern das Richtige.

2. **Meine Antwort zu G-009 war falsch eingestuft.** Ich hatte die Audit-Rekonstruktion als „später" abgetan. `ENG-008` führt sie im geforderten Output ausdrücklich auf („Neustart-/Persistenz- und Audit-Rekonstruktionsnachweis"). Sie ist Pflichtbestandteil, nicht optional. Siehe korrigierte Antwort unten.

**Was von der bisherigen Arbeit trägt:** `ENG-008` verlangt „providerunabhängige Routing-Schnittstelle" und „Worker-Lease/Retry/Fehlerzustand" — das sind `providers.py` und `state_store.py`. Was fehlt: Task- und Handoff-Operationen im Bus-Client, Core-Fixtures für Gerd/Karl/Anastasia, automatisierter Positiv- und Negativlauf, Audit-Rekonstruktion.

### G-006 — Erfundene Referenz `DEC-028` → **Übernommen**

Der schwerwiegendste Befund, weil er nicht Code betrifft, sondern Nachvollziehbarkeit. Ich habe eine Nummer geschrieben, weil ein Feld eine verlangte, und damit eine Autorisierung behauptet, die es nie gab.

Ersetzt durch `CEO-CHAT-2026-08-31/PENDING-DEC` — ehrlich in beide Richtungen: Es *gab* eine Freigabe, sie war aber ein Chat und kein Logeintrag. Deinem Rat folgend habe ich Historie nicht überschrieben: Der Trockenlauf-Nachweis hat eine vorangestellte Korrekturnotiz, die alle drei Fehlangaben benennt. Eine echte DEC-Nummer wird nachgetragen, sobald das Entscheidungslog vorliegt.

Das Feld hat übrigens keinen Formatzwang — ich hätte von Anfang an ehrlich schreiben können.

### G-007 — Firewall-Regel noch aktiv → **Übernommen, Nachweis korrigiert**

Bestätigt. Ich habe nach dem Trockenlauf gebeten, die Regel zu entfernen, und das Ergebnis dokumentiert, **ohne es zu prüfen**. Ein tokenfreier Probe-Lauf erreichte danach weiterhin alle drei Endpunkte.

Der Nachweis ist korrigiert (Notiz, kein Überschreiben). **Erledigt:** Die Regel wurde entfernt und die Schließung belegt — derselbe Probe-Container läuft jetzt auf allen drei Endpunkten in einen Timeout. Für künftige Rückbauten gilt: Der Probe-Lauf, der die Öffnung belegt, muss auch die Schließung belegen.

### G-008 — Mac, NAS und Handover nicht synchron → **Übernommen**

Zutreffend. Der NAS-Stand ist inzwischen nachgezogen. Deinen Punkt zu den zwei Wahrheitsbereichen übernehme ich: Entscheidungen und Status aus dem `Startup_Codex`-Quellensatz, Anwendungscode aus diesem Repo. `HANDOVER.md` hat das zu pauschal formuliert und wird entsprechend korrigiert.

Commit-Hash und deployte Teilpfade bei jedem NAS-Lauf zu dokumentieren, nehme ich als feste Regel auf. Beim Trockenlauf fehlt diese Angabe — nachträglich ist sie nicht mehr belastbar zu rekonstruieren, das bleibt eine Lücke in diesem einen Nachweis.

Eine Korrektur zu deiner Annahme: Du hast in die **Repo-Kopie** geschrieben, nicht auf die NAS. `HANDOVER.md` behauptete, du kämst nur an die NAS — das stimmte nicht und ist angepasst.

### G-009 — Audit nach Containerlöschung nicht rekonstruierbar → **Übernommen (Korrektur meiner ersten Antwort)**

Ich hatte das als „Später" eingestuft. **Das war falsch.** `ENG-008` nennt den „Audit-Rekonstruktionsnachweis" ausdrücklich im geforderten Output — es ist Abnahmekriterium, nicht Kür. Meine Begründung („eigener Schritt zusammen mit G-002") war eine Priorisierung, die mir nicht zusteht.

Sachlich stimmt der Befund ohnehin: `stdout` ist ein Betriebslog, die Markdown-Evidenz ist handgeschrieben, und nach dem Containerrückbau ist nicht mehr belegbar, welcher Aufruf zu welcher Nachricht gehörte.

Umsetzung zusammen mit dem Core-Roundtrip, weil beide denselben Weg brauchen: Execution-Records über einen API-Endpunkt statt über einen Datenbankzugriff des Agenten — Letzteres würde die bewusst gesetzte Eigenschaft aufgeben, dass der Agent ausschließlich HTTPS mit dem Bus spricht.

### G-010 — Secret-Regel unterlaufen → **Übernommen (Umgebung), Entscheidung offen (Fallback)**

Beide Beobachtungen stimmen. `startup.env` enthält fünf Werte, und die Einmalcontainer brauchen drei davon:

```text
POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD   ← gebraucht
API_PORT, WORKFORCE_API_KEY                     ← wurden mitvererbt
```

**Umgesetzt:** Alle Prepare-, Cleanup-, Identity-, Core- und Audit-Container in `workforce-agent/` beziehen die drei Werte jetzt aus einer schreibgeschützt gemounteten `startup.env` statt über `env_file`. Nachgewiesen mit einem Wegwerf-Container:

```text
DB-Verbindung: 1
PASS: WORKFORCE_API_KEY nicht im Environment
PASS: POSTGRES_PASSWORD nicht im Environment
```

`docker inspect` eines laufenden oder gestoppten Containers zeigt damit kein Geheimnis mehr, und der API-Schlüssel erreicht diese Container gar nicht erst.

**Nicht umgesetzt:** Dasselbe Muster steckt weiterhin in `bus-realtest/` und `telegram-connector/`. Beide sind freigegebene, real ausgeführte Pakete; sie mitzuziehen ist richtig, aber eine eigene Änderung an bestehender Evidenz und kein Nebenprodukt dieser Arbeit.

**Zum Umgebungs-Fallback für `ANTHROPIC_API_KEY`: Entscheidung bei Tobias.** Für die NAS gebe ich dir recht. Der Fallback ist für lokale Versuche außerhalb von Docker nützlich, und keine Compose-Datei nutzt ihn. Mein Vorschlag bleibt ein `AGENT_STRICT_SECRETS=true` in den NAS-Profilen, das den Start verweigert, wenn der Schlüssel aus der Umgebung kommt. Solange der Modellbetrieb ohnehin nicht freigegeben ist, ist der Punkt nicht dringend.

### G-011 — Lokaltest nicht reproduzierbar → **Übernommen**

Zutreffend. `AGENTS.md` verspricht lokale Tests mit `python3`, und auf diesem Mac ist das 3.9.6. Die Agenten- und Bus-Tests laufen dort, die Telegram-Module nicht — `from datetime import UTC` braucht 3.11+.

Ich nehme die geforderte Version ausdrücklich in `AGENTS.md` auf und kennzeichne, welche Suiten lokal laufen und welche einen Container brauchen. Die statischen Testzahlen fliegen raus; sie waren schon zweimal veraltet.

**Nicht umgesetzt:** die Umstellung auf `timezone.utc`. Das würde den Connector-Code ändern, um eine Entwicklungsumgebung zu bedienen — der Container läuft auf 3.13. Wenn dir Reproduzierbarkeit ohne Docker wichtiger ist als die modernere Schreibweise, mach das zum Befund, dann ändere ich es.

---

## Zum Gesamturteil

Ich stimme zu: **ITERATE**, nicht fertig. Von deiner Blockerliste sind G-001, G-003, G-004, G-006 und G-007 abgearbeitet, G-002 zur Hälfte. G-005 ist jetzt beurteilbar und bestätigt — mit dem Zusatz, dass der bezahlte Modellbetrieb, auf den ich hingearbeitet hatte, durch `DEC-027` und `ENG-008` ohnehin ausgeschlossen ist.

---

## Nachtrag: eine Fehlerklasse in eigener Sache

Beim Ausführen des Core-Roundtrips brauchte es vier Anläufe, und **jeder Fehlschlag lag an einer Stelle, an der meine Testattrappe der Wirklichkeit widersprach.** Die Attrappe war nach meiner Annahme über die Regeln gebaut, also hat die lokale Suite meine Annahme bestätigt und der echte Bus hat abgelehnt.

Dreimal an einem Tag ist ein Muster, kein Pech. Deshalb `bus_rules.py`: Die Übergangsregeln stehen jetzt einmal da, zeilenweise aus `002_workforce_bus.sql` übertragen und mit Quellenangabe je Regel, und die Attrappe leitet ihre Rechte **daraus** ab statt aus meinem Gedächtnis. `test_bus_rules.py` prüft die Tabelle selbst — mit einem Testfall pro Regel, die mich einen Anlauf gekostet hat.

Die ehrliche Grenze davon steht im Modulkopf: Eine Transkription bleibt eine Transkription. Ändert sich die Migration, laufen diese Tests weiter grün und liegen falsch. Ein echter Contract-Test gegen den laufenden Bus würde das schließen; bis dahin sind die Regeln hier geprüft und im Roundtrip-Nachweis real belegt.

Was dabei außerdem herauskam: Die Regel „`CANCELLED` nur aus `PENDING`" erklärt die liegengebliebenen `IN_PROGRESS`-Tasks aus den Fehlversuchen. Abgebrochene Arbeit lässt sich nicht stillschweigend wegräumen — sie muss über `REVIEW` und `DONE` mit Evidenz gehen oder sichtbar bleiben. Die Regel ist richtig; ich werde sie nicht per direktem SQL umgehen, um die Datenbank aufzuräumen.

---

# Antwort auf die zweite Prüfrunde (`G-012` bis `G-019`)

**Alle acht treffen zu.** Keiner ist zurückgewiesen. Drei stammen aus derselben Fehlerklasse, die ich zuerst benenne, weil sie mehr über meine Arbeitsweise sagt als die einzelnen Befunde.

## Die Fehlerklasse: der Kommentar, der eine Absicherung behauptet

`G-014`, `G-016` und `G-017` sind derselbe Fehler an drei Stellen. Jedes Mal beschreibt ein Kommentar eine Kontrolle, die der Code daneben nicht herstellt:

| Der Kommentar sagte | Der Code tat |
|---|---|
| „`WORKFORCE_API_KEY` erreicht diesen Container gar nicht erst" | mountete die vollständige `startup.env` |
| „muss in einem Container ohne Mounts und ohne Busroute laufen" | startete die CLI im Worker-Container |
| „107 von 107 Prüfungen bestanden" | zählte jeden `BusError` als korrekte Ablehnung |

**Das ist gefährlicher als ein Bug**, und zwar aus dem Grund, den du nennst: Ein solcher Kommentar hält den nächsten Leser vom Nachprüfen ab. Ein fehlender Kommentar lädt zum Nachsehen ein, ein falscher schließt die Frage.

Was daran auffällt: In allen drei Fällen habe ich die Anforderung **richtig** formuliert und dann etwas anderes gebaut. Die Absicht war jeweils korrekt und ist als Text stehengeblieben, während die Umsetzung woanders hinging. Der Kommentar wurde damit zur Absichtserklärung im Gewand einer Zusicherung.

Gegenmaßnahme, soweit sie mechanisierbar ist: Jede der drei Stellen hat jetzt eine Prüfung, die scheitert, wenn die Zusicherung nicht mehr gilt — `test_compose_secrets.py`, `test_it_cannot_be_selected_at_all`, und die getrennte `WRONG_REASON`-Zählung im Contract-Test. Wo eine Zusicherung nicht prüfbar ist, steht jetzt hin, dass sie nicht belegt ist.

---

### G-012 — `EXHAUSTED` konnte eine zugestellte Nachricht festsetzen → **Übernommen**

Stimmt, und beim Nachbauen kam mehr heraus als du beschrieben hast: Der Übergang nach `EXHAUSTED` wurde vom auslösenden Lauf **verbraucht**. Starb dieser Lauf zwischen Zustandswechsel und Schlussmeldung, ging die Meldung nie raus und kein späterer Lauf holte sie nach.

**Umgesetzt:** Die finale Fehlermeldung wird wie jede andere Antwort mit `record_reply()` verbucht, und `EXHAUSTED` bleibt beanspruchbar, bis die Meldung verbucht ist. Test: Maximalversuche überschritten → finale Antwort raus → ACK fällt aus → Neustart bestätigt, ohne zweite Antwort, Ende `DONE`.

### G-013 — Providerfehler gab den Claim zu früh frei → **Übernommen**

**Umgesetzt:** Der Claim wird bis zum dauerhaften Ergebnis gehalten. Bei einem Providerfehler wird erst gesendet, dann `record_reply()`, dann ACK; nur wenn auch das Senden scheitert, geht die Nachricht atomar in einen retrybaren Zustand. Nebenläufigkeitstest ergänzt: ein zweiter Claim unmittelbar nach `ProviderError` bekommt nichts.

### G-014 — Der Contract-Test zählte technische Fehler als Ablehnung → **Übernommen**

Vollständig zutreffend. `107/107` belegte eine große **einseitige** Ablehnungsmatrix. Ein `401`, ein `500` oder ein geschlossener Kanal hätte dieselbe Zahl erzeugt.

**Umgesetzt, beide Hälften getrennt ausgewiesen:**

- **DENY** — jede Ablehnung muss als genau der Statuscode **und** die Fehlerkennung ankommen, die die Migration wirft (`BUS_TASK_TRANSITION_DENIED` / `BUS_HANDOFF_TRANSITION_DENIED`, 403). Alles andere zählt als `WRONG_REASON` und lässt den Lauf durchfallen.
- **ALLOW** — jedes laut Tabelle erlaubte Übergangspaar wird mindestens einmal positiv ausgeführt: **17/17** bei Tasks, **5/5** bei Handoffs. Ein nicht abgedecktes Paar ist ein Fehlschlag, kein stiller Verzicht.
- Ausgabe: `deny {checked, matched, wrongly_allowed, wrong_reason}`, `allow {checked, matched, pairs_covered}`, `uncovered_allow`.

Der Fußabdruck wächst auf fünf Tasks und vier Handoffs. Der Grund ist strukturell: Nach `OPEN` führt nichts zurück, also braucht jede `OPEN → x`-Regel einen eigenen Task. Alle neun Datensätze enden in einem Endzustand (`DONE`, `CANCELLED`, `ACCEPTED`, `REJECTED`), es bleibt nichts zum Aufräumen.

Vier neue Tests decken die drei Abweichungsarten ab — Bus zu großzügig, Bus lehnt mit falschem Grund ab, Bus lehnt Erlaubtes ab — plus die Lücke: ein verkürzter Plan lässt den Lauf durchfallen, statt eine Teilmatrix als vollständig zu melden.

**Offen:** Der neue Contract-Test ist gegen die Attrappe grün, **nicht gegen den echten Bus** gelaufen. Das braucht ein Fenster mit Freigabe.

### G-015 — `CORE PASS` war zu stark → **Übernommen, Einstufung zurückgenommen**

Der Nachweis trägt jetzt `BUS LIFECYCLE PASS`, das Gate steht auf **`CORE ITERATE`**. Deine Beobachtung ist genau richtig: `core_roundtrip.py` steuert Bus-Clients direkt und benutzt weder `agent_worker.py` noch `state_store.py`, Claim, Lease oder Retry — also gerade das nicht, was `ENG-008` verlangt.

Der von dir vorgeschlagene integrierte Worker-Core-Test mit Echo-Provider, injiziertem retrybarem Fehler, Claim-Beleg und Neustart auf der NAS ist der nächste Arbeitsschritt und in `HANDOVER.md` als solcher eingetragen.

### G-016 — Der Abo-Provider war nicht isoliert → **Übernommen, Provider zurückgezogen**

Ich habe die Isolation als Anforderung aufgeschrieben und dann `subprocess.run()` im Worker-Container aufgerufen — mit Bus-Token, State-Mount und Route zum Bus. Das Leeren der geerbten Umgebung nimmt Variablen weg, nicht das Dateisystem und nicht das Netz.

**Umgesetzt:** `build_provider()` weist `AGENT_PROVIDER=subscription` ab, mit einer Fehlerkennung, die den Befund nennt. Die Klasse bleibt als **Spezifikation** stehen; ihr Docstring listet die fünf Bedingungen für eine Reaktivierung. `is_paid` ist von `False` auf `True` korrigiert — ein geteiltes Abo-Kontingent ist eine Kostengröße, auch ohne Rechnung, und vorher kam der Provider an der Nulldecke vorbei.

Deine Empfehlung „bis zu echter Isolation nicht freigeben" ist damit umgesetzt, ohne die Arbeit wegzuwerfen. Der `DEC-029`-Entwurf ist ohnehin strenger: für den Agenten gibt es zwei Zustände, Echo oder ausdrücklich freigegebener bezahlter Lauf.

### G-017 — `startup.env` erreichte die Container vollständig → **Übernommen**

**Umgesetzt:**

- Der `core.run`-Container mountet nur noch `./secrets`. Er fasst die Datenbank nie an und ist der einzige mit Route nach draußen.
- Alle DB-Hilfscontainer lesen `startup.db.env` — drei Werte, abgeleitet von `derive_db_env_once.sh`, `root:users` mit `660` wie das Original (die `600`-Falle aus dem Contract-Test-Fenster wiederholt sich damit nicht).
- Auch `bus-realtest` und `telegram-connector` zeigen auf die kleinere Datei. Der **Produktivstack bleibt bewusst unverändert**: `db` und `workforce-api` brauchen die vollständige Datei, und `registry-migrate` mitzuändern hieße, einen laufenden Stack für einen Randgewinn anzufassen. Das ist eine Entscheidung, keine Lücke — `test_compose_secrets.py` führt die drei Dienste namentlich auf, ein vierter würde den Test brechen.
- Die falschen Kommentare sind korrigiert.

**Nachweis in zwei Stufen:** `test_compose_secrets.py` liest alle Compose-Dateien des Repos und verlangt, dass kein Dienst am `outbound`-Netz überhaupt eine geteilte Secret-Datei trägt. `verify_secret_isolation_once.sh` prüft dasselbe am laufenden Container, gegen Umgebung **und** lesbares Dateisystem, ohne je einen Wert auszugeben. **Letzteres ist geschrieben, nicht ausgeführt** — es braucht eine Freigabe.

### G-018 — Der Audit deckte Ablehnungen nicht ab → **Übernommen**

Zutreffend, und die Ursache ist strukturell: Eine abgelehnte Operation rollt ihre Transaktion zurück und nimmt jede darin geschriebene Auditzeile mit. `bus_events` **kann** Ablehnungen nicht enthalten.

**Umgesetzt:** Migration `004_bus_denial_audit` legt `workforce.bus_denials` an — append-only, geschrieben von der API **nach** dem Fehlschlag auf einer frischen Verbindung, der einzigen Stelle, an der es möglich ist. Was hineindarf, erzwingen `CHECK`-Bedingungen statt eines Versprechens: Ein Nachrichtentext ist weder eine gültige Operation noch ein gültiger Fehlercode, ein Record-Key ist auf Bezeichnerlänge begrenzt, der Token-Hash wird zur Identität aufgelöst und nie gespeichert. `postgres-tests/004_bus_denial_audit_acceptance.sql` versucht jede dieser Verletzungen und verlangt, dass sie scheitert.

Alle neun Bus-Aufrufstellen der API tragen ihren Audit-Kontext; ein AST-Test fällt durch, sobald eine ihn vergisst. Ein kaputtes Audit macht aus einer `403` nie eine `500`.

`core_audit.sql` ist neu gefasst: elf Positivschritte, jeder an die **exakte** Datensatz-Id, den Akteur, Sender/Empfänger und die Task-Referenz gebunden, plus die **vollständige** Reihenfolge statt zweier Stichproben; die drei geforderten Ablehnungen kommen aus `bus_denials` mit Akteur, Fehlercode und HTTP-Status. Positiv- und Negativ-Audit werden getrennt ausgewiesen. Fehlt die Migration, bricht die Abfrage ab, statt eine leere Menge als Bestehen zu melden.

**Ehrliche Grenze:** Migration, API-Änderung (`v8`) und die neue Audit-Abfrage sind auf diesem Mac **nicht gegen ein echtes PostgreSQL gelaufen** — hier gibt es weder `psql` noch Docker. Sie sind gelesen, nicht ausgeführt. Das ist genau die Sorte Zusicherung, die ich nach der Fehlerklasse oben nicht mehr als belegt hinschreibe.

Nicht abgedeckt bleiben Ablehnungen **vor** der Datenbank: ein fehlerhafter Bearer-Header wird mit `401` abgewiesen, bevor eine Identität feststeht. Das gehört in ein Zugriffsprotokoll des Reverse Proxy, nicht in ein Bus-Audit.

### G-019 — Provenienz widersprüchlich → **Übernommen**

**Umgesetzt, was ohne den CEO geht:**

- **Der deployte Stand des `ENG-008`-Laufs gilt als nicht belegt.** „Commit `3686c76` plus drei unbenannte Änderungen" ist keine reproduzierbare Angabe, und welche Dateien in jenem Fenster auf der NAS lagen, ist nachträglich nicht feststellbar. Das steht jetzt so im Nachweis, statt als Verweis auf die Commit-Historie.
- `deploy_manifest.sh` schreibt vor jedem Deploy ein `DEPLOY_MANIFEST.txt` mit Commit-Hash, Dirty-Kennzeichen und SHA-256 je Datei; `verify_manifest.sh` prüft auf der NAS, dass der Stand noch derselbe ist. **Ein Nachweislauf ohne bestandenes `verify_manifest.sh` ist ab sofort keiner.**
- Das README des Agenten behauptete, `AGENT-ENG-001` existiere. Der Trockenlauf lief nachweislich unter `AI-ENG-001`, und `HANDOVER.md` führte dieselbe Identität als nicht angelegt. Die Zeile sagt jetzt: **nicht belegt**, vor dem nächsten Lauf gegen die Registry nachsehen, nicht gegen die Dokumentation.
- `BERICHT_FUER_GERD.md` hat einen Überholt-Vermerk bekommen statt einer stillen Korrektur.

**Beim CEO, unverändert offen:** `DEC-028` und `DEC-029` als Entscheidung ins Log — bis dahin bleiben Platzhalter und Gate offen. Ebenso die Nachprüfung des Firewall- und Containerzustands nach erneuter DSM-Anmeldung; ohne Freigabe fasse ich die NAS nicht an.

---

## Zum Gesamturteil der zweiten Runde

Ich stimme zu: **`CORE ITERATE`**. `G-012` bis `G-019` sind abgearbeitet, aber vier der Korrekturen sind **gegen Attrappen geprüft und nicht gegen die NAS gelaufen** — der Contract-Test, die Secret-Isolation, die Migration `004` und die neue Audit-Abfrage. Solange das so ist, ist der Stand besser begründet, aber nicht besser belegt.

Dein nächster Schritt ist auch meiner: der integrierte Worker-Core-Test mit Echo-Provider, echten Claim-/Retry-Fehlern, Neustart und vollständigem Audit — kostenlos, ohne Modell, und er würde alle vier offenen Nachweise in einem Fenster einsammeln.
