# Skills — ein Ort, eine Form

Jede Identität hat genau eine Datei `skills/NAME/SKILL.md`: Kopf mit `name` und `description`
für Claude Code, darunter die Rolle als Text. Dieselbe Datei ist der Systemtext der Identität im
Bot (`system_prompt_file` in `workforce/config.json`). Claude Code findet sie über einen
Verweis aus `~/.claude/skills/`; der Bot bekommt den Ordner nach `/etc/workforce/skills`.

Regeln: technikfrei formulieren, höchstens 150 Zeilen, weil der Text bei jedem Aufruf mitgeht.
Änderungen nur hier, nie in ChatGPT oder auf der NAS — das sind Archive. Das Register, wer
welche Rolle in welchem Status hat, führt Anastasia.

| Identität | Ordner | Stand |
|---|---|---|
| Karl `SAO-001`, Standard | `karl/` | aus Company State, Regel 5 und Review-Vorlage des Quellensatzes, 2026-09-06 |
| Marlene `POA-001` | `marlene/` | eingesammelt aus `~/.claude/skills`, Verweis zurückgelegt |
| Thorsten `RAS-001` | `thorsten/` | aus Opportunity-Filter v0.2 des Quellensatzes und `FILTER.md`, 2026-09-06 |
| Anastasia `PEO-001` | `anastasia/` | aus Company State, Regel 4 und ihrer Organisationsbestandsaufnahme, 2026-09-06 |
| CFO, Name offen | `cfo/` | neu, 2026-09-06; Name und `DEC`-Eintrag durch den CEO |
| Marv Skillbauer, Kennung offen, fachliche Führung Anastasia | `marv/` | hat sich selbst gebaut, eingesammelt aus `~/.claude/skills` am 2026-09-06; Werkzeugrolle, kein Bot-Skill |
| Gerd `AI-ENG-001` | `gerd/` | aus seinen Prüfrunden, 2026-09-06; kein Bot-Skill, lebt in Claude Code und Codex |

Quelle der Rollen: `00_COMPANY_STATE.txt` und `interim-bus/rules/` im iCloud-Quellensatz
`Startup_Codex`, einmalig geholt am 2026-09-06. Ab jetzt gilt nur diese Ablage.
