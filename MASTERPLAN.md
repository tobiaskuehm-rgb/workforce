# Masterplan Workforce — Stand 2026-09-03, nach dem ersten Tag im Betrieb

**Status:** Vorschlag von Claude Code aus dem CEO-Brainstorming vom 2026-09-03. Entscheidungen
darin bekommen ihre Nummer im Decision Log (`G-006`). Maßstab bleibt `INVARIANTEN.md`.

## 1. Einordnung des Brainstormings

Die zehn Stichworte sind drei Sorten Dinge:

| Sorte | Stichworte | Was es im Neubau ist |
|---|---|---|
| **Wer antwortet** | Marlene, Thorsten, Gerd, Anastasia | eine Identität: Name, Modell, Policy, Systemtext, eigenes Gedächtnis |
| **Woran gearbeitet wird** | Geschäftsideen-Suche, Krypto, Immobilien, Privatbereich, CFO | eine Domäne: gehört zu einer Identität, bringt Daten und Regeln mit |
| **Wo es läuft** | Ollama, Mac mini | Infrastruktur: entscheidet, welche Daten das Haus verlassen müssen |

Rollen laut Registry (`001_employee_registry.sql`) und HO-027:

| Identität | Rolle | Domäne, die passt | Anmerkung |
|---|---|---|---|
| **Marlene** `POA-001` | Private Office Assistant | Privatbereich | Termine, Schriftverkehr, Erinnerungen; später Paperless |
| **Thorsten** `RAS-001` | Research & Strategy Analyst | Geschäftsideen-Suche; Recherche zu Krypto und Immobilien | Analyse, Strukturierung, Gegenargumente |
| **Anastasia** `PEO-001` | People & Organization | heute keine Domäne aus der Liste | bleibt angelegt, bekommt Arbeit, wenn es Menschen zu organisieren gibt |
| **Gerd** `AI-ENG-001` | AI Engineer / Architekt | Review des Systems | bleibt der Prüfer (Codex), keine Telegram-Identität |
| **Karl** `SAO-001` | Strategy & Operations, Koordinator | nicht genannt | Kandidat für die Standardidentität statt „ASSISTENZ" |
| **CFO** | neu, ohne Namen | Finanzen, Budgets, Fristen; Krypto und Immobilien als Positionen | Name und DEC-Eintrag fehlen |

**Krypto und Immobilien sind keine Identitäten, sondern zwei Domänen mit derselben Regel:**
Das System informiert, strukturiert und rechnet vor. Es handelt nicht, es hat keine Werkzeuge,
und es gibt keine persönliche Anlageberatung — das steht im Systemtext, nicht nur im Kopf.

**Ollama und Mac mini gehören zusammen.** Auf der Synology ist ein lokales Modell zu langsam
für Antworten. Auf einem Mac mini mit Apple Silicon ist es brauchbar, und dann darf die
Datengrenze für private Daten `FULL` stehen, weil nichts das Haus verlässt. Ohne Mac mini
ist Ollama nur ein Testprovider.

## 2. Drei Varianten aus dem Brainstorming

**A — Ein Bot, viele Hüte.** Alle Identitäten im vorhandenen Bot, angesprochen mit `@MARLENE`,
`@THORSTEN`, `@CFO`; jede mit Systemtext, Policy, Budget und eigenem Gedächtnis. Karl als
Standard. Aufwand: je Identität ein Konfigurationseintrag, dazu einmal das Gedächtnis.

**B — Ein Bot je Rolle.** Marlene, Thorsten und CFO bekommen je einen eigenen Telegram-Bot und
Chat. Klarere Trennung im Telefon, aber drei Token, drei Abfrager, dreimal Konfiguration.

**C — Werkstatt zuerst.** Vor neuen Identitäten die Grundlagen: Gedächtnis, Sicherung, Paperless
für Dokumente, tägliche Zusammenfassung. Identitäten erst, wenn sie echte Daten haben.

## 3. Drei Varianten unabhängig davon

**D — Mac mini als Zentrale.** Der Kern zieht auf einen Mac mini, Ollama daneben; die NAS wird
Speicher und Sicherung. Private Domänen laufen lokal mit `FULL`, geschäftliche Recherche geht
weiter zu Claude. Einmalig rund 700 bis 1.000 Euro.

**E — Das System meldet sich.** Bisher antwortet es nur. Geplante Läufe: morgens ein Briefing,
freitags die Finanzübersicht aus dem, was du unter der Woche geschickt hast, Erinnerungen an
Fristen. Technisch ein Zeitplan im Kern und Nachrichten ohne vorherige Frage.

**F — Werkzeuge hinter Freigabe.** Lesende Zugriffe — Kalender, Dokumentensuche, Kurse — als
getrennte Abrufer, deren Ergebnis als Daten durch die Grenze geht, und jede Aktion nur nach
einem Ja im Chat. Der größte Nutzen und das größte Risiko: Es rührt an die Invariante
„werkzeugloser Agent" und braucht eine eigene Zeile auf der Seite und Gerds Review vorher.

## 4. Bewertung in drei Perspektiven

Noten 1 bis 5, 5 ist am besten.

| Variante | Nutzen im Alltag | Sicherheit und Kosten | Aufwand bis es läuft | Summe |
|---|---|---|---|---|
| A Ein Bot, viele Hüte | 4 | 5 — nichts ändert sich am Modell | 5 — Tage | **14** |
| B Ein Bot je Rolle | 3 | 4 | 2 — dreifacher Betrieb | 9 |
| C Werkstatt zuerst | 2 kurzfristig, 4 später | 5 | 3 — Wochen ohne sichtbaren Gewinn | 10 |
| D Mac mini | 3 | 5 — private Daten bleiben lokal | 2 — Kauf, Umzug, Ollama | 10 |
| E Meldet sich | 5 — das ist, was eine Assistenz ausmacht | 4 — Kosten planbar, Budget deckelt | 4 — ein Zeitplan im Kern | **13** |
| F Werkzeuge | 5 | 2 — bricht die Grundannahme | 2 — Isolation, Freigabe, Review | 9 |

## 5. Fazit

A und E zusammen sind der Weg: Identitäten als Konfiguration im einen Bot, und ein System,
das sich meldet. C ist kein Gegenmodell, sondern die Reihenfolge innerhalb von A: Gedächtnis
und Sicherung kommen vor der dritten Identität. D wird eine Entscheidung, sobald private
Daten regelmäßig an ein fremdes Modell gehen würden — vorher ist es ein Kauf ohne Anlass. F
kommt zuletzt oder gar nicht, und nur mit eigener Invariante. B nicht.

## 6. Masterplan

Jede Phase endet mit einem echten Lauf. Gerd prüft danach gegen die Invariantenseite. Kosten
für Modelle bei heutiger Nutzung: einstellige Euro im Monat, gedeckelt durch die
Konfiguration.

### Phase 0 — Diese Woche: benutzen und absichern
- Täglich benutzen, Störungen notieren. Nichts vorher bauen.
- **Sicherung weg von der NAS:** nächtlich `workforce backup` per DSM-Aufgabe, Kopie zieht
  der Mac per ssh. Test: Wiederherstellung in leeren Container, `verify` PASS (Invariante 13).
- DEC-Eintrag für den Neubau und für diesen Plan durch den CEO.
- Ergebnis: das System überlebt einen Plattenausfall und einen Neustart.

### Phase 1 — Woche 2: Gedächtnis und Karl
- **Gedächtnis je Identität:** die letzten Wechsel aus der Datei gehen als `context` mit,
  begrenzt auf die Datengrenze; Policy je Identität entscheidet, ob überhaupt.
- Standardidentität wird **Karl**, Systemtext aus der Registry-Rolle.
- Test: „und weiter?" versteht den Bezug; ein Wechsel zu `@MARLENE` sieht Karls Kontext nicht.
- Ergebnis: ein Gespräch statt einzelner Fragen.

### Phase 2 — Woche 3: Marlene und Thorsten
- **Marlene**, Policy `BODY`, Systemtext aus dem HO-027-Skillpaket, Domäne Privatbereich.
- **Thorsten**, Domäne Geschäftsideen: strukturiert, bewertet, nennt Gegenargumente; dazu
  Recherche-Aufträge zu Krypto und Immobilien als Wissensfragen, nie als Empfehlung.
- Budget je Identität statt nur je Tag.
- Ergebnis: drei Ansprechpartner in einem Chat.

### Phase 3 — Woche 4 bis 5: Das System meldet sich
- Zeitplan im Kern: Morgenbriefing, Freitagsübersicht, Fristen. Jede geplante Nachricht ist
  ein normaler Ausgang mit Audit, Budget und Kill Switch.
- **CFO** als Identität, Name durch den CEO: führt eine einfache Übersicht aus dem, was du
  schickst — Einnahmen, Ausgaben, Positionen in Krypto und Immobilien — und rechnet vor.
- Ergebnis: eine Assistenz, die nicht nur antwortet.

### Phase 4 — Monat 2: Dokumente
- Paperless-ngx auf der NAS, Marlene und CFO lesen daraus über einen Abrufer, dessen Ergebnis
  als Daten durch die Grenze geht. Erste Form von F, lesend, ohne Aktion.
- Entscheidungspunkt **Mac mini**: Gehen jetzt regelmäßig private Dokumente an ein fremdes
  Modell? Wenn ja, D — Kern und Ollama auf den Mac mini, private Identitäten lokal mit `FULL`.
- Ergebnis: das System kennt deine Unterlagen, und du weißt, wo sie hingehen.

### Phase 5 — Monat 3, optional: Werkzeuge hinter Freigabe
- Nur mit neuer Zeile auf der Invariantenseite und Gerds Review vorher. Jede Aktion nach
  einem Ja im Chat, jeder Abrufer isoliert, Ergebnis nur als Daten.

### Was in jeder Phase gilt
- Eine Phase, ein Lauf, dann Review. Ein Befund ohne dauerhaften Schaden wird ein Test.
- Kein Handel, keine Anlageberatung, keine Werkzeuge ohne Phase 5.
- Jede Identität hat Policy, Budget und Gedächtnis für sich. Was Marlene weiß, weiß Thorsten
  nicht.
- Der Prototyp bleibt Orakel; Anastasia und Gerd bleiben angelegt, ohne Arbeit, bis es sie gibt.
