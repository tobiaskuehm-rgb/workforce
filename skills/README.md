# Skills — ein Ort, eine Form

Jede Identität hat genau eine Datei `skills/NAME/SKILL.md`: Kopf mit `name` und `description`
für Claude Code, darunter die Rolle als Text. Dieselbe Datei ist der Systemtext der Identität im
Bot (`system_prompt_file` in `workforce/config.json`). Claude Code findet sie über einen
Verweis aus `~/.claude/skills/`; der Bot bekommt den Ordner nach `/etc/workforce/skills`.

Regeln: technikfrei formulieren, höchstens 150 Zeilen, weil der Text bei jedem Aufruf mitgeht.
Änderungen nur hier, nie in ChatGPT oder auf der NAS — das sind Archive. Das Register, wer
welche Rolle in welchem Status hat, führt Anastasia.

## Drei Stellen, an denen eine Identität steht

Eine Identität ist erst vollständig, wenn sie an allen dreien steht, die sie braucht. Wer nur
an einer steht, ist nicht halb da, sondern anders da — die drei können Verschiedenes.

| | wo | Modell | Kontext | wer bezahlt |
|---|---|---|---|---|
| **Skill** | `skills/<name>/SKILL.md` | das des laufenden Gesprächs | der des Gesprächs — **geteilt** | — |
| **Agent** | `.claude/agents/<name>.md` | eigenes, im Kopf der Datei | **eigener**, je Lauf | das Abo |
| **Bot** | `workforce/config.json` | eigenes, je Identität | eigener, SQLite | die API, je Aufruf |

**Skill und Agent sind nicht dasselbe.** Ein Skill ist eine Anweisung *im laufenden* Kontext:
Wer hier „Karl" aufruft, bekommt nicht Karl, sondern den laufenden Assistenten mit Karls Text —
ein Modell, ein Kontext, ein Verlauf für alle. Ein Agent ist ein **eigener Lauf** mit eigenem
Modell und eigenem Kontext; seine Arbeit landet nicht im Fenster des CEO. Modelle je Identität
gibt es deshalb nur als Agent oder im Bot, nie als Skill.

## Register

| Identität | Ordner | Agent | Bot | Stand |
|---|---|---|---|---|
| Karl `SAO-001`, Standard, **COO auf Probe** seit 2026-09-08 (Chat, `PENDING-DEC`) | `karl/` | Sonnet | Opus | v2 nach Marv, 2026-09-07: Feld erkundet (FwDV 100, Chief of Staff, ISO 19011, Scrum, GGO), drei Fassungen, fünf Prüfrunden, Endfassung 43/43 gegen 26/43; Arbeitsbereich `karl-workspace/` |
| Marlene `POA-001` | `marlene/` | Sonnet | Sonnet | eingesammelt aus `~/.claude/skills`, Verweis zurückgelegt |
| Thorsten `RAS-001` | `thorsten/` | Sonnet | Opus | aus Opportunity-Filter v0.2 des Quellensatzes und `FILTER.md`, 2026-09-06 |
| Anastasia `PEO-001` | `anastasia/` | Sonnet | Sonnet | aus Company State, Regel 4 und ihrer Organisationsbestandsaufnahme, 2026-09-06; Runde 1 durch Marv am 2026-09-08: 34/35 gegen 24/35, vier Prüffälle, fremde Bewerter; Arbeitsbereich `anastasia-workspace/` |
| Wolle, CFO, Kennung offen | `cfo/` | Sonnet | Sonnet | neu, 2026-09-06; Name Wolle vom CEO 2026-09-08 (Chat, `PENDING-DEC`), Kennung und `DEC`-Eintrag offen; Bedarf erst Oktober 2026 (Chat 2026-09-08) |
| Marv Skillbauer, Kennung offen (Vorschlag `AI-SKI-001`), unterstellt Anastasia | `marv/` | Opus | — | hat sich selbst gebaut, 2026-09-06; bewusst kein Bot-Skill; Mitarbeiter seit 2026-09-08 (Chat, `PENDING-DEC`), zwei Runden 40/40 gegen 17/40; Auftrag: Skills von Thorsten, Anastasia, Wolle überarbeiten und messen |
| Gerd `AI-ENG-001` | `gerd/` | Opus | — | aus seinen Prüfrunden, 2026-09-06; lebt in Claude Code und Codex, bewusst kein Bot-Skill; zwei Runden durch Marv am 2026-09-08: 37/38 gegen 29/38, dann 40/42 gegen 36/42; Arbeitsbereich `gerd-workspace/` |

Die Modellwahl folgt zwei Fragen, und sie ziehen in verschiedene Richtungen: **Wie oft wird
er gerufen?** und **wie teuer ist eine schlechtere Antwort?** Gerd prüft und Marv baut — selten,
tief, und ein schwächeres Modell wäre dort nicht langsamer, sondern schlechter; sie bleiben auf
Opus. Alle übrigen laufen auf Sonnet, Karl als meistgerufene Identität ausdrücklich auch: Seine
Form steht im Skill und trägt sie.

Als Agent und im Bot darf dieselbe Identität verschieden laufen. Der Agent zahlt aus dem Abo,
das sich an vielen Läufen erschöpft; der Bot rechnet je Aufruf ab und deckelt bei
`max_usd_per_day`. Karl steht deshalb hier auf Sonnet und dort auf Opus.

Der Bot deckelt bei `max_usd_per_day`; die Reservierung vor dem Aufruf wird danach gegen den
tatsächlichen Verbrauch zurückgebucht (`reconcile`), Opus ist deshalb keine Handvoll Aufrufe.

## Gedächtnis

`skills/gedaechtnis/<name>.md` — was eine Identität weiß, ohne nachzusehen: Entscheidungen des
CEO, Tatsachen zur Lage, offene Vorgänge, jeder Eintrag mit Datum und Quelle. Fünf Identitäten
verweisen im Skill darauf (`../gedaechtnis/<name>.md`); der relative Pfad löst in allen drei
Laufzeiten auf, weil das Gedächtnis **neben** den Skills liegt und der Bot den ganzen Ordner
bekommt.

Es liegt seit dem 2026-09-08 hier im Repo statt in `~/.claude/skills/`; dort steht nur noch ein
Verweis. Vorher war es unversioniert, ungesichert und im Bot nicht erreichbar. Der abgelöste
Ordner liegt als `~/.claude/gedaechtnis.abgeloest-2026-09-07/` beiseite, gelöscht ist nichts.

**Geschrieben wird es in Claude Code**, vom Agenten oder von Hand. Der Bot mountet `skills/`
schreibgeschützt, und sein Provider ist werkzeuglos — dort ist das Gedächtnis Lesestoff. Was
eine Identität im Telegram-Gespräch erfährt, landet also **nicht** von selbst im Gedächtnis.

Marlene und Marv haben keins: Sie führen laufende Vorgänge in ihren Arbeitsbereichen unter
`~/.claude/skills/<name>-workspace/`.

Quelle der Rollen: `00_COMPANY_STATE.txt` und `interim-bus/rules/` im iCloud-Quellensatz
`Startup_Codex`, einmalig geholt am 2026-09-06. Ab jetzt gilt nur diese Ablage.
