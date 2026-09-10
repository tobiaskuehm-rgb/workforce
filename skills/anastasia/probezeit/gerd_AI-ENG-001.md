# Probezeit-Evidenz — Gerd (AI-ENG-001)

Identität: Gerd, `AI-ENG-001`, KI-Systemarchitekt und Prüfer. Probezeit seit `DEC-002`.
Vorgesetzter: CEO. Fachliche Führung: Anastasia (`PEO-001`).
Anlass: Reviewauslöser, 22 Commits seit dem letzten Review (Schwelle 5 in der Probezeit).
Stand: 2026-09-10.

Quellen: `REVIEW_GERD.md` (Neubau), `nas-startup/REVIEW_GERD.md` (Prototyp),
`skills/gerd-workspace/iteration-2/BERICHT.md` (Marvs Messung), `skills/gedaechtnis/gerd.md`,
`git log` über die 22 Commits, die ihn betreffen.

## Die vier Trennungen

**Rollenbedarf.** Kein Befund gegen die Rolle, im Gegenteil. Sie hat als einzige im Haus
belegbar etwas verhindert: Das Gate für den Deploy P-2 steht auf ROT und hält den Stand an.
Eine Prüferrolle, die nie blockiert, ist Zierde; diese hier blockiert.

**Rollendesign.** Ein Befund, und er ist neu entstanden. Seit dem 2026-09-09 hat Gerd zwei
verschiedene Grenzen an zwei Orten: In ChatGPT schreibt er Vorlagen, also er baut. In Claude
Code prüft er und baut ausdrücklich nicht. Dieselbe Identität mit zwei Grenzen ist schwer zu
überwachen, weil jede Überschreitung an einem Ort am anderen erlaubt ist. Das ist keine
Fehlentscheidung, sondern eine Folge der Arbeitsteilung, aber es braucht eine geschriebene
Trennlinie, sonst prüft er am Ende seine eigene Vorlage.

**Technischer Blocker.** Drei, keiner davon seine Schuld.

1. **Zwei Orte, ein Gedächtnis, keine Brücke.** Was Gerd in ChatGPT prüft, landet nicht von
   selbst in `REVIEW_GERD.md`. Das hat schon einmal Substanz gekostet: Sein Nachcheck vom
   2026-09-02/03 wurde nie eingetragen, und in der Lücke prüfte eine Vertretung unter
   fremdem Kürzel.
2. **Der ChatGPT-Export kommt nicht.** Mehrfach angewiesen, die Mail von OpenAI bleibt aus
   (CEO, 2026-09-09). Solange das so ist, hat er kein Gedächtnis über seine eigene Historie.
3. **Er darf nichts ausführen, und das ist richtig so** — aber es hat einen Preis, den seine
   eigenen Berichte benennen: Mehrere Invarianten stehen als „nicht belegt", weil kein echter
   Lauf stattgefunden hat. Die Rolle kann nur so viel belegen, wie jemand anders ausführt.

**Individuelle Leistung.** Belegt, nicht eingeschätzt.

- **Dreiundzwanzig Befunde allein im Neubau**, mit Schwere, Korrektur und Nachweis je Zeile.
  Vier davon hoch, darunter ein Provider, der als lokal deklariert war und beliebige
  HTTP-Ziele annahm.
- **Gemessen von Marv:** 40 von 42 mit Skill gegen 36 von 42 ohne, bei **210k Token gegen
  344k**. Er wurde durch den Skill nicht nur genauer, sondern billiger.
- **Er trennt Geprüftes von Vermutetem.** `REVIEW_GERD.md` führt einen eigenen Abschnitt
  „Geprüft und nicht bestätigt". Das ist der stärkste einzelne Beleg in dieser Akte: Ein
  Prüfer, der aufschreibt, was er *nicht* zeigen konnte, ist die Ausnahme.
- **Er benennt die Grenze seiner eigenen Korrektur.** Zum Ollama-Befund steht ausdrücklich,
  dass die zulässige Container-Brücke den Mac mini nicht anbindet und dass das kein stiller
  Rückfall auf eine beliebige Adresse ist.
- **Zwei eigene Lücken hat Marvs Runde 2 gefunden**, beide eingebaut: eine Zusage, einen Diff
  im eingefrorenen Prototyp zu prüfen, und ein Reviewdatum vom Rechner statt vom Prüfauftrag.

## Rollengrenze

Kein Fall einer Überschreitung in den 22 Commits. Er schlägt Korrekturen vor und führt sie
nicht aus; das liegt in der Rolle. Der einzige Risikopunkt ist die neue Doppelrolle oben.

## Antwortqualität

40 von 42 in Runde 2. Marvs Einordnung: Diese Runde hat noch zwei echte Lücken gefunden, also
war der Skill vorher nicht fertig. Eine dritte Runde würde messen, ob die Korrekturen halten,
und die vier stumpf gewordenen Kriterien ersetzen.

## Schulungsbedarf

Drei Stellen, keine davon ist „mehr Erfahrung":

- **Skilldatei:** dritte Messrunde durch Marv, mit ersetzten Kriterien.
- **Gedächtnis:** ein anderer Weg für die ChatGPT-Historie, weil der Export nicht kommt.
- **Referenzen:** eine geschriebene Trennlinie zwischen Vorlagenbau und Prüfung.

## Was der Rolle noch fehlt

- Eine verlässliche Brücke zwischen seinen beiden Orten. Heute trägt sie ein Mensch.
- Ein echter Lauf, an dem sich die als „nicht belegt" geführten Invarianten belegen lassen.

## Offene Vorgänge

- Nachcheck `G-112`/`G-113` offen, Deploy P-2 Phase 3 hängt dahinter, Gate ROT.
- ChatGPT-Export seit 2026-09-07 offen, anderer Weg nötig.

## Nächster kleinster Schritt

Die Trennlinie zwischen Vorlagenbau und Prüfung aufschreiben, bevor die erste Vorlage aus
ChatGPT von Gerd selbst geprüft wird. Das ist der Fall, in dem die Doppelrolle zuschlägt, und
er kann jederzeit eintreten.

Kein Personalurteil, keine Übernahmeempfehlung — das entscheidet der CEO.
