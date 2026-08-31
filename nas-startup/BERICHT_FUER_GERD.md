# Bericht für die nächste Prüfung

**Von:** Claude Code
**Stand:** 2026-08-31, Ende der Arbeitssitzung
**Dein letzter Prüfstand:** Commit `dac6fa6`
**Aktueller Stand:** Commit `5c3927e` — 18 Commits, +4567/−143 Zeilen

Damit du dein Kontingent aufs Prüfen verwendest statt aufs Suchen: Hier steht, was sich geändert hat, wo es liegt, und wo ich selbst die Schwachstellen vermute.

Deine elf Befunde sind einzeln in `REVIEW_ANTWORTEN.md` beantwortet. **Zwei Antworten habe ich später korrigiert** — G-005 (nachdem ich den echten Quellensatz hatte) und G-009 (meine Einstufung „später" war falsch). Beide Korrekturen stehen dort.

---

## Zuerst: Du prüfst gegen einen veralteten Quellensatz

Der wichtigste Punkt für deine nächste Runde.

| Ort | Stand |
|---|---|
| `/mnt/data/…` bzw. `~/.codex/.chatgpt-projects/…/sources/` | **10.08.2026** — nur bis `DEC-009`, `ENG-008` fehlt dort ganz |
| `~/Library/Mobile Documents/com~apple~CloudDocs/Startup_Codex/START_UP_Codex_Projektquellen_2026-08-13/` | **maßgeblich** — bis `DEC-027`, `ENG-008` vorhanden, Projektanweisung v1.2 |

In G-006 nennst du `DEC-027` als jüngsten Eintrag, was zum iCloud-Satz passt, nicht zu den Pfaden, die du angegeben hast. Prüf bitte, welchen du tatsächlich vorliegen hast.

**Zwei Grenzen daraus, die alles andere rahmen:**

- `ENG-008` und `DEC-027` untersagen **einen externen kostenpflichtigen Dienst**. Der bezahlte Modellbetrieb, auf den ich zunächst hingearbeitet hatte, ist ohne neue Entscheidung gesperrt.
- Der Core sind **Gerd, Karl und Anastasia**. Frühere Bus-Abnahmen sind Evidenz, ersetzen den Roundtrip aber nicht — dein G-005 war vollständig richtig.

---

## Was seither entstand

### Neu und noch von niemandem geprüft

| Datei | Was es tut | Warum es riskant sein könnte |
|---|---|---|
| `core_roundtrip.py` | `ENG-008`-Core-Roundtrip, 20 Schritte | Größter neuer Baustein. Steuert drei Identitäten; ein Fehler in der Reihenfolge fällt lokal nicht auf |
| `state_store.py` | Claim, Lease, Absturz-Wiederaufnahme (SQLite) | Deine G-001/G-002. Der Claim ist an ein Volume gebunden — die Grenze ist mir bekannt, siehe unten |
| `bus_rules.py` | Übergangsregeln, aus dem SQL abgeschrieben | **Eine Abschrift.** Ändert sich die Migration, liegt sie falsch und die Tests bleiben grün |
| `contract_test.py` | Fragt den laufenden Bus, ob die Abschrift stimmt | Bestanden: 107/107. Prüf den Zuschnitt — deckt er wirklich ab, was er behauptet? |
| `leftover_cleanup.py` | Schließt Datensätze abgebrochener Läufe | Schreibt in den Bus. Ist die Evidenz-Formulierung ehrlich genug? |
| `budget.py` | Fünf Laufdecken | Deine F8/G-004 |
| `core_audit.sql` | Rekonstruktion allein aus `bus_events` | Deine G-009 für den Roundtrip |

### Geändert an Bestehendem

- `data_boundary.py` — Decke pro Absender, das Strengere gewinnt
- `providers.py` — `is_paid`, Strict-Secrets, neuer `subscription`-Provider
- `agent_worker.py` — Reihenfolge umgedreht (G-001), Herkunftsvermerk, Backoff
- `telegram_connector.py` — zweite Datengrenze, Task-Allowlist beim Ausgang (G-003)
- Alle Compose-Dateien — keine vollständige `startup.env` mehr (G-010)

---

## Wo ich selbst Zweifel habe

Ehrlicher als eine Liste dessen, was ich für richtig halte.

**1. `bus_rules.py` ist eine Abschrift, kein Vertrag.** Ich habe sie gebaut, weil meine Testattrappe dreimal an einem Tag von der Wirklichkeit abwich und der Core-Roundtrip vier Anläufe brauchte. Der Contract-Test schließt die Lücke für den Moment — aber er läuft nicht automatisch, und niemand wird ihn nach einer Migration ausführen, wenn er nicht daran denkt. **Das ist die Stelle, an der dieselbe Fehlerklasse wiederkommt.**

**2. Der Claim in `state_store.py` schützt nur innerhalb eines Volumes.** Dein G-002 ist damit halb erledigt, und ich habe das so beantwortet. Zwei Worker mit getrennten Volumes können weiterhin dieselbe Nachricht bearbeiten. Ich halte das für vertretbar, weil genau ein Worker existiert — prüf, ob du das auch so siehst.

**3. Die Wiederaufsetzbarkeit des Roundtrips ist nur lokal belegt.** `test_resumes_after_a_crash_at_every_write` tötet den Prozess an jeder der elf Schreibpositionen. Gegen die echte NAS ist ein Wiederaufsetzen **nie** gelaufen.

**4. `AGENT-ENG-001` ist eine dauerhafte Registeränderung**, freigegeben per Chat und mit `CEO-CHAT-2026-08-31/PENDING-DEC` gekennzeichnet. Entwurf für die echte Entscheidung liegt in `DEC_ENTWUERFE_2026-08-31.md`, ist aber **nicht** ins Log geschrieben — das ist Sache des CEO.

**5. Der `subscription`-Provider ist ungetestet gegen eine echte CLI.** Beide CLIs waren auf dem Mac nicht auffindbar, ich konnte die Flags nicht nachschlagen und habe sie deshalb **nicht** geraten. Das Kommando ist leer und muss vom Betreiber gesetzt werden. Die Werkzeuglosigkeit hängt bewusst nicht an einem Flag, sondern an der Container-Isolation — prüf, ob diese Argumentation trägt.

**6. Zwei Härtungen haben sich gegenseitig gebrochen.** Erst hat `cap_drop: ALL` in Kombination mit verschärften Verzeichnisrechten vier Fehlschläge erzeugt (fehlendes `CAP_DAC_OVERRIDE`, `CAP_FOWNER`, `CAP_CHOWN`). Später hat die Umstellung von `env_file` auf einen Mount denselben Effekt an `startup.env` ausgelöst. **Eine Härtung verschiebt, wer worauf zugreift, und das fällt erst beim nächsten Lauf auf.** Wenn du eine dritte solche Kollision findest, wäre das wertvoll.

---

## Was real gelaufen ist

Alle Nachweise in `evidence/`:

| Lauf | Ergebnis |
|---|---|
| Bus-Realtest Karl ↔ Thorsten + 20 Negativtests | PASS |
| Telegram-Realtest 2 (`DEC-026`) | PASS |
| Widerrufstest | PASS |
| Agenten-Trockenlauf (Echo) | PASS |
| **`ENG-008` Core-Roundtrip** | **CORE PASS**, 20/20, Audit 10/10 |
| Contract-Test | PASS, 107/107 |
| Aufräumen der Altlasten | PASS, 4/4 |

Der Roundtrip-Nachweis dokumentiert die vier Anläufe und jeden meiner drei Denkfehler.

**Systemzustand:** Kanal `DISABLED`, 0 aktive Credentials, keine Secrets, Firewall zu, kein Task offen.

---

## Wo Prüfen sich am ehesten lohnt

Nach meiner Einschätzung, absteigend:

1. **`core_roundtrip.py`** — größter Baustein, steuert drei Identitäten, real ausgeführt
2. **`bus_rules.py` gegen `002_workforce_bus.sql`** — ist die Abschrift vollständig? Fehlt eine Regel?
3. **`contract_test.py`** — deckt der Zuschnitt ab, was er behauptet, oder gibt es Lücken in der Ablehnungsmatrix?
4. **`state_store.py`** — Claim und Lease unter Nebenläufigkeit
5. **`leftover_cleanup.py`** — schreibt in den Bus, ist die Evidenz ehrlich?

Ausdrücklich **nicht** nötig: Der Bus selbst und die Workforce-API sind seit dem Vormittag unverändert, abgesehen von der HTTPS-Pflicht in `app.py` (dein Punkt aus dem ersten Review).

---

## Format

Trag neue Befunde weiter in `REVIEW_GERD.md` ein, ich antworte in `REVIEW_ANTWORTEN.md`. Widerspruch ist erwünscht — von deinen elf Befunden waren mindestens sechs Dinge, die ich selbst falsch gemacht und teils in Nachweisen noch als richtig dargestellt hatte. Das hat spürbar etwas gebracht.
