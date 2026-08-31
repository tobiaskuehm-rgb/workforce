# Entwürfe für das Entscheidungslog

**Zweck:** Zwei Einträge zum Nachtragen in `03_DECISION_LOG.txt` (iCloud, `Startup_Codex/START_UP_Codex_Projektquellen_2026-08-13/`). Der letzte echte Eintrag dort ist `DEC-027`.

**Status:** Entwurf. Nichts davon gilt, bevor du es geprüft und ins Log übernommen hast. Ich habe die Einträge **nicht** selbst dorthin geschrieben — das Log ist deine autoritative Quelle, und ein Assistent, der sich seine eigenen Freigaben einträgt, wäre genau das Muster, das `DEC-028` unten korrigiert.

Zwei Einträge statt einem, weil sie unterschiedliche Klassen sind: Der eine dokumentiert nach und erlaubt kostenlose Tests, der andere erlaubt erstmals einen kostenpflichtigen externen Dienst. Sie zu vermischen würde die zweite Entscheidung in der ersten verstecken.

---

## DEC-028 – Workforce-Agent: Identität, Testläufe und stehende Testfreigabe

**Datum:** 2026-08-31
**Entscheider:** CEO
**Status:** ACTIVE

**Anlass:** Am 2026-08-31 wurden am Workforce Core Arbeiten ausgeführt, die im Entscheidungslog fehlen. Sie waren per Chat freigegeben, aber nicht als Entscheidung erfasst. Zwischenzeitlich trugen Konfiguration und Evidenz die erfundene Referenz `DEC-028/ENG-008`; diese wurde durch den ehrlichen Platzhalter `CEO-CHAT-2026-08-31/PENDING-DEC` ersetzt und wird mit dieser Entscheidung aufgelöst.

**Nachträglich erfasst:**

1. **Technische Agentenidentität `AGENT-ENG-001`** wurde dauerhaft im Register angelegt: `role_code = SYSTEM_AGENT`, Titel „Automated agent – not an employee, answers are machine generated", `read_scope = PARTICIPANT`, `task_authority = PROPOSE`, kein Handoff-Recht, acht `MESSAGE`-Routen exakt gespiegelt von `AI-ENG-001`. Grund: Der Agent lief zuvor unter Gerds Zugang, einer Person in der Probezeit — maschinelle Antworten erschienen als Nachrichten eines Menschen.
2. **Vier Testläufe** mit Kanalöffnung auf `TESTING` und kurzlebigen `ACCEPTANCE`-Zugängen: Bus-Realtest Karl ↔ Thorsten mit 20 Negativtests, Telegram-Realtest 2 nach `DEC-026`, Agenten-Trockenlauf mit Echo-Provider, `ENG-008`-Core-Roundtrip mit Gerd, Karl und Anastasia.
3. **Aufräumen** der Datensätze aus abgebrochenen Testläufen, geschlossen über die Regeln des Busses statt per direktem SQL.

Alle Läufe endeten mit vollständigem Rückbau: Zugänge widerrufen, Kanal `DISABLED`, Token-Dateien gelöscht, temporäre Firewallregeln entfernt. Nachweise liegen in `evidence/`.

**Stehende Freigabe für kostenlose Testläufe:** Gerd darf innerhalb des Core-Scopes Testläufe gegen die NAS ausführen, ohne dafür jeweils eine neue Entscheidung zu benötigen, unter allen folgenden Bedingungen:

- **Kein externer kostenpflichtiger Dienst.** Diese Freigabe ändert nichts an der Grenze aus `DEC-027`.
- Kanal höchstens `TESTING`, niemals `ACTIVE`; `ACCEPTANCE`-Zugänge mit höchstens 30 Minuten Gültigkeit.
- Vollständiger Rückbau nach jedem Lauf: Zugänge `REVOKED`, Kanal `DISABLED`, Token-Dateien gelöscht.
- **Firewallfreigaben bleiben Einzelentscheidung des CEO.** Sie werden weiterhin von Hand gesetzt und nach jedem Lauf entfernt und geprüft.
- Frisches Datenbank-Backup vorhanden, produktives Volume und `startup.env` unangetastet.
- Jeder Lauf hinterlässt einen Nachweis in `evidence/` mit Ergebnis und Rückbau.

**Unveränderte Grenzen:** Alle Grenzen aus `DEC-027` bleiben in Kraft, insbesondere keine kostenpflichtigen externen Dienste, keine produktive externe Kommunikation, keine Übermittlung sensibler Daten, keine Abschwächung von Security oder Permissions, keine produktive Rechteaktivierung. Credentials bleiben außerhalb von Chat, Quellen und Git.

**Ersetzt/klärt:** Löst den Platzhalter `CEO-CHAT-2026-08-31/PENDING-DEC` in Konfiguration und Evidenz auf. Ändert `DEC-027` nicht, sondern arbeitet innerhalb dessen operativer Freigabe.

---

## DEC-029 – Einmaliger Modelllauf des Workforce-Agenten

**Datum:** 2026-08-31
**Entscheider:** CEO
**Status:** FREIGEGEBEN FÜR GENAU EINEN LAUF

**Entscheidung:** Abweichend von `DEC-027` und `ENG-008` wird **ein einziger** Lauf des Workforce-Agenten mit einem externen kostenpflichtigen Modelldienst freigegeben. Zweck ist ausschließlich der Nachweis, dass die gebaute Kette mit einem echten Modell trägt.

**Warum abweichend:** `DEC-027` untersagt „neue kostenpflichtige externe Dienste", `ENG-008` untersagt „externen kostenpflichtigen Dienst". Diese Entscheidung hebt das **nicht allgemein** auf, sondern öffnet ein einzelnes, eng begrenztes Fenster.

**Scope:**

| Grenze | Wert |
|---|---|
| Anbieter, Modell | Anthropic, `claude-opus-5` |
| Nachrichten | genau **eine** |
| Modellaufrufe | höchstens **einer** |
| Kostendecke | **0,50 USD** |
| Laufzeit | höchstens 5 Minuten |
| Zyklen | 1 |
| Datengrenze | `AGENT_DATA_POLICY` — vom CEO festzulegen, siehe unten |
| Identität | `AGENT-ENG-001`, kurzlebiger `ACCEPTANCE`-Zugang |
| Kanal | höchstens `TESTING` |
| Schlüsselablage | nur Datei, `AGENT_STRICT_SECRETS=true` |

**Zur Datengrenze:** Der CEO hat `FULL` als allgemeine Einstellung gewählt. Für diesen ersten Lauf ist festzulegen, ob es dabei bleibt oder ob mit `BODY` begonnen wird — `FULL` ergänzt lediglich Task- und Handoff-Referenzen. Übertragen wird in beiden Fällen ausschließlich die eine bearbeitete Nachricht; Zugangsdaten, Employee Memory und Datenbankinhalte sind konstruktiv nicht erreichbar.

**Inhalt der Testnachricht:** Eine eigens angelegte, fachlich harmlose Anfrage. Keine realen Geschäftsinhalte, keine personenbezogenen Daten, keine Finanzdaten.

**Verpflichtender Rückbau, unmittelbar nach dem Lauf:** Zugang `REVOKED`, Kanal `DISABLED`, Token- und Schlüsseldatei gelöscht, `AGENT_PROVIDER` zurück auf `echo`, Compose-Projekte und Testnetz entfernt, Firewallregel zurückgenommen und die Sperrung nachgewiesen.

**Nicht enthalten:** Dauerbetrieb, ein zweiter Lauf, Verarbeitung realer Geschäftsinhalte, Weitergabe der Modellantwort per Telegram (`TELEGRAM_OUTBOUND_POLICY` bleibt `METADATA_ONLY`), sowie jede Ausweitung auf weitere Identitäten.

**Verbraucht sich:** Diese Freigabe ist nach einem Lauf aufgebraucht — unabhängig davon, ob er gelingt. Ein weiterer Lauf braucht eine neue Entscheidung.

**Kostengrundsatz (gilt über diesen Lauf hinaus):** Ausgaben für Modellaufrufe werden **einzeln und vorab vom CEO freigegeben**, niemals automatisch und niemals als Dauerfreigabe. Es gibt bewusst keinen Zustand, in dem der Agent von selbst Geld ausgibt: Voreinstellung ist der kostenlose Echo-Provider, und eine Kostendecke von `0` weist einen kostenpflichtigen Provider bereits vor dem ersten Aufruf ab.

Hintergrund: Wo Arbeit auch über die vorhandenen Pro-Abos möglich ist, hat das Vorrang — dort sind die Kosten bereits getragen und ein erschöpftes Limit ist eine Wartezeit, keine Rechnung. Der CEO entscheidet je Fall, ob er auf ein zurückgesetztes Limit wartet oder Kosten freigibt.

**Wichtige Abgrenzung:** Die Pro-Abos (Claude Pro, ChatGPT Pro) gelten für die Chat-Oberflächen und decken **keinen** API-Zugang. Der Workforce-Agent auf der NAS kann sie nicht nutzen; er spricht über die API und wird pro Token getrennt abgerechnet. Für ihn gibt es daher nur zwei Zustände: kostenloser Echo-Provider oder ausdrücklich freigegebener, kostenpflichtiger Lauf. Eine „erst Abo, dann API"-Abstufung existiert für den Agenten nicht.

---

## Was von dir noch fehlt

1. **Beide Einträge prüfen** und in `03_DECISION_LOG.txt` übernehmen — oder mir sagen, was zu ändern ist.
2. **Datengrenze für den Einmallauf** festlegen: `BODY` oder `FULL`.
3. **Entscheiden, ob `DEC-029` überhaupt jetzt gebraucht wird.** Der Agent ist gebaut, getestet und im Trockenlauf bewährt; was ein bezahlter Lauf zusätzlich beweist, ist ausschließlich die Antwortqualität eines echten Modells. Das ist ein echter Nachweis, aber kein dringender — der Core ist gerade erst durchs Gate, und `DEC-027` stellt die Reihenfolge `CORE → THORSTEN → FINANCE` auf. Ein Aufschub kostet nichts.
4. Nur falls `DEC-029` kommt: **einen Anthropic-API-Schlüssel** anlegen (console.anthropic.com, eigenes Guthaben — das Pro-Abo deckt das nicht) und auf der NAS ablegen. Wie beim Bot-Token: **nicht** in den Chat, sondern direkt in die Datei.

Erst danach baue ich das Runbook für den Lauf.
