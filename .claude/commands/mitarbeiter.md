---
description: Wer da ist, was er kann, was er kostet - und einen direkt beauftragen
argument-hint: [name] [auftrag]
---

Argumente: $ARGUMENTS

## Ohne Argumente: den Überblick geben

Lies die Modellzeilen mit **einem** Aufruf:

```
grep -H "^model:" .claude/agents/*.md
```

Gib danach diese Tabelle aus, die Modellspalte aus dem Messergebnis. Nichts dazu
erfinden, nichts weglassen, keine Einleitung davor:

| Mitarbeiter | Modell | wofür |
|---|---|---|
| **Karl** `SAO-001` | … | Stand, Prioritäten, Reihenfolge, „ordne das ein". Die Standardidentität. |
| **Marlene** `POA-001` | … | Private Ablage: Belege, Rechnungen, Fristen, Verträge, Rockhausen. |
| **Gerd** `AI-ENG-001` | … | Prüft Code, Commits, Läufe. Schreibt Befunde, baut nichts. |
| **Thorsten** `RAS-001` | … | Geschäftsideen gegen den Filter, Gegenargumente, Ideen-Battle. |
| **Anastasia** `PEO-001` | … | Rollen, Register, Probezeit, „wer macht was". |
| **CFO** (Name offen) | … | Zahlen mit Quelle: Linien, Budget, Steuerfristen, Szenarien. |
| **Marv** | … | Baut und misst Skills. |

Darunter genau diese zwei Sätze, unverändert:

**Ruf einen mit Namen** („Karl, ordne das ein" / „Lass Gerd das prüfen") — dann läuft er
als eigener Prozess, und nur seine Antwort landet hier.
**Für eine kurze Frage im Fluss reicht der Skill** — billiger, bleibt aber im Fenster.

Dann aufhören. Keine Empfehlung, kein nächster Schritt, keine Rückfrage.

## Mit Argumenten: beauftragen

Das erste Wort ist der Name, der Rest der Auftrag. Starte diesen Mitarbeiter über das
Agent-Werkzeug mit dem Auftrag als Prompt. Kennst du den Namen nicht, nenne die sieben
und frage nach — starte nichts auf Verdacht.

Ist der Auftrag leer, frage in einem Satz, was er tun soll.
