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
| Karl `SAO-001`, Standard | `karl/` | Opus | Opus | v2 nach Marv, 2026-09-07: Feld erkundet (FwDV 100, Chief of Staff, ISO 19011, Scrum, GGO), drei Fassungen, fünf Prüfrunden, Endfassung 43/43 gegen 26/43; Arbeitsbereich `karl-workspace/` |
| Marlene `POA-001` | `marlene/` | Sonnet | Sonnet | eingesammelt aus `~/.claude/skills`, Verweis zurückgelegt |
| Thorsten `RAS-001` | `thorsten/` | Opus | Opus | aus Opportunity-Filter v0.2 des Quellensatzes und `FILTER.md`, 2026-09-06 |
| Anastasia `PEO-001` | `anastasia/` | Sonnet | Sonnet | aus Company State, Regel 4 und ihrer Organisationsbestandsaufnahme, 2026-09-06 |
| CFO, Name offen | `cfo/` | Sonnet | Sonnet | neu, 2026-09-06; Name und `DEC`-Eintrag durch den CEO |
| Marv Skillbauer, Kennung offen | `marv/` | Opus | — | hat sich selbst gebaut, 2026-09-06; Werkzeugrolle, bewusst kein Bot-Skill |
| Gerd `AI-ENG-001` | `gerd/` | Opus | — | aus seinen Prüfrunden, 2026-09-06; lebt in Claude Code und Codex, bewusst kein Bot-Skill |

Die Modellwahl folgt einer Linie: **Urteilsarbeit teuer, strukturierte Arbeit günstiger.** Karl
integriert und widerspricht, Thorsten zerlegt Annahmen, Gerd prüft, Marv baut und misst — dort
ist ein schwächeres Modell eine schlechtere Antwort, nicht nur eine langsamere. Anastasia, CFO
und Marlene arbeiten gegen eine Form, die im Skill steht; dort trägt Sonnet.

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
