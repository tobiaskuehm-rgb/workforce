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
| Marlene `POA-001` | `marlene/` | eingesammelt aus `~/.claude/skills`, Verweis zurückgelegt |
| Gerd `AI-ENG-001` | `gerd/` | aus seinen Prüfrunden geschrieben, 2026-09-06 |
| Karl, Thorsten, Anastasia, CFO | — | einzusammeln aus ChatGPT und NAS |
