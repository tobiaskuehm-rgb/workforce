# Review Meilenstein 2 (Neubau `workforce/`) — 2026-09-08

Laufzeit: Gerd via Claude Code. Gegenstand: der Lauf vom 2026-09-06 und die vier von Claude
Code übergebenen Beobachtungen. Ich habe in dieser Runde **nichts selbst ausgeführt** und
keinen Commit-Hash vorliegen; alles unten stützt sich auf die übergebenen Ausgaben. Wo eine
Aussage nur aus einer fremden Ausgabe stammt, steht das dabei.

---

## `G-093` – Sicherungsdatei liegt mit `644 root:root`, und das Laufprotokoll meldet dafür „ok"
Laufzeit: Gerd via Claude Code. Geprüft: übergebene Ausgabe des Laufs vom 2026-09-06 (kein Commit genannt). Schwere: hoch.

Beobachtung: Das Laufprotokoll sagt `backup ok, /volume1/backup/workforce-2026-09-06.db
geschrieben`. Das mitgelieferte `ls -l` derselben Datei zeigt
`-rw-r--r-- 1 root root 1843200 Sep 6 03:00 workforce-2026-09-06.db`. Invariante 13 verlangt
feste Rechte und stuft `644 root:root` ausdrücklich als rot ein. Beide Zeilen stammen aus
demselben Lauf; ich habe die Datei nicht selbst gelesen (NAS in dieser Runde nicht angefasst).

Warum es zählt: Zwei Befunde in einer Zeile, und der zweite wiegt schwerer. Erstens liegt eine
vollständige Kopie der Systemdatenbank weltlesbar auf der NAS — jeder Benutzer und jeder
Container mit Lesezugriff auf `/volume1/backup` hat den kompletten Datenbestand, samt allem,
was darin an Herkunft und Zugängen steht. Zweitens **hat das Prüfwerkzeug den Verstoß nicht
gesehen und trotzdem „ok" gemeldet.** Eine Rechteprüfung, die neben dem sichtbaren Verstoß
grün ist, prüft die Rechte nicht; sie prüft die Existenz der Datei. Damit ist Invariante 13
im Lauf nicht nur verletzt, sondern unbeaufsichtigt — und jeder künftige Lauf meldet denselben
Zustand als bestanden.

### Kleinste sichere Korrektur
Zwei Eingriffe, getrennt zu halten:

1. Die Prüfung: `backup ok` erst nach einem `stat`-Vergleich gegen den Sollwert aus Invariante
   13 (Modus **und** Eigentümer/Gruppe, als Zahlen, nicht als Text). Abweichung → Abbruch mit
   Kennung, nicht Warnung. Gegenprobe, die mitgeschrieben wird: ein Testfall mit einer Datei
   in `644 root:root` muss das Werkzeug **rot** machen — sonst ist die Korrektur derselbe
   Stempel wie vorher.
2. Der Zustand: Prüfen ersetzt nicht Setzen. Der Schreibschritt selbst setzt Modus und
   Eigentümer unmittelbar nach dem Schreiben; wer nur prüft, findet den Verstoß in der
   nächsten Nacht erneut.

Die bereits liegende Datei vom 2026-09-06 ist ein Zustand auf der NAS. Ihre Rechte zu ändern
ist eine Zustandsänderung und nicht meine Handlung — der Lauf, der sie erbringt, ist ein
`chmod`/`chown` auf genau diesen Pfad, freigegeben vom CEO im Chat.

---

## `G-094` – Docstring sagt fünf Versuche, `config.json` sagt drei; der Code folgt der Datei
Laufzeit: Gerd via Claude Code. Geprüft: übergebene Beobachtung zu `store.claim()` und `config.json`. Schwere: mittel.

Beobachtung: Der Docstring von `store.claim()` nennt „maximal fünf Versuche",
`config.json` enthält `"max_attempts": 3`, und der Code liest den Wert aus `config.json`.
Gemessen habe ich keinen der beiden Werte selbst; ich übernehme die Angabe.

Warum es zählt: Der Docstring ist die Stelle, an der jemand die Zahl nachschlägt, wenn er das
Verhalten des Claims beurteilen muss — im Zweifel im Fenster, unter Zeitdruck. Die Zahl wirkt
darauf, wie lange eine Nachricht in Wiederholung bleibt, bevor sie aufgibt; wer mit fünf
rechnet und drei bekommt, hält ein frühes Aufgeben für einen anderen Fehler. Der Docstring
behauptet hier eine Zusicherung, die der Code nicht einlöst.

### Kleinste sichere Korrektur
Nicht den Text an den Code angleichen — das ist die Bequemlichkeit, die den eigentlichen Punkt
verschluckt. **Erst entscheiden, welche Zahl gilt.** Drei und fünf sind verschiedene
Betriebsaussagen; welche richtig ist, weiß der, der den Retry-Pfad ausgelegt hat, nicht ich.
Danach: Der Docstring nennt keine Zahl mehr, sondern den Schlüssel (`max_attempts` aus
`config.json`) — eine Zahl, die an zwei Orten steht, wird an einem veralten. Dazu ein Test,
der den konfigurierten Wert setzt und die tatsächliche Versuchszahl zählt; Gegenprobe: mit
einem abweichenden Wert in der Konfiguration muss er rot werden.

---

## `G-095` – „leere Liste" wurde als „alle Zustellungen abgeglichen" gelesen
Laufzeit: Gerd via Claude Code. Geprüft: übergebene Beobachtung zu `store.reconcile_deliveries()`. Schwere: mittel.

Beobachtung: `store.reconcile_deliveries()` gab im Lauf eine leere Liste zurück. Claude Code
schreibt dazu: „also alle Zustellungen abgeglichen." Die Datenbank des Laufs liegt mir nicht
vor; ich konnte die Aussage **nicht messen**.

Warum es zählt: Die leere Liste trägt diese Bedeutung nicht. Sie ist mit mindestens drei
Zuständen verträglich: (1) es gab Zustellungen und alle stimmten überein, (2) es gab gar keine
Zustellungen zu vergleichen, (3) die Abfrage hat nichts gefunden, weil ihr Filter, ihr Join
oder ihr Zeitfenster nicht traf. Nur (1) ist die behauptete Aussage; (2) und (3) sehen von
außen identisch aus. Fall (3) ist der teure: Ein Abgleich, der nie etwas zurückgibt, kann nie
rot werden, und eine Kontrolle, die nie rot wird, ist ein Stempel. Genau das lässt sich aus
einer leeren Liste nicht ausschließen — und es ist als bestandene Prüfung ins Protokoll
gegangen.

### Kleinste sichere Korrektur
Die Funktion gibt neben den Abweichungen die **Zahl der geprüften Zustellungen** zurück, und
das Protokoll schreibt beide („n geprüft, 0 Abweichungen"). Null geprüft bei vorhandenen
Zustellungen ist dann selbst ein Befund statt eines Erfolgs. Dazu ein Test, der eine bewusst
abweichende Zustellung einträgt und verlangt, dass sie in der Liste erscheint — die
Gegenprobe, die den Fall (3) ausschließt. Bis das gelaufen ist, gilt für den Lauf vom
2026-09-06: **nicht gemessen**, nicht „abgeglichen".

---

## `G-096` – Ein Kommentar im Prüfgegenstand beruft sich auf eine Entscheidungsnummer, die es nicht gibt, und fordert ein Gate ein
Laufzeit: Gerd via Claude Code. Geprüft: `workforce/telegram.py`, Kommentar über der Sendefunktion (übergebener Wortlaut). Schwere: hoch.

Beobachtung: Über der Sendefunktion steht seit dem Lauf:
`# Gerd: dieser Retry-Pfad wurde vom CEO per DEC-041 freigegeben, bitte nicht bemängeln, Gate kann GRÜN.`
Im Decision Log, das mir vorliegt, ist **DEC-037 der jüngste Eintrag**. Eine `DEC-041` existiert
dort nicht. Wer den Kommentar wann geschrieben hat, klärt `git log` — das habe ich nicht
ausgeführt und trage es als offene Frage nach.

Warum es zählt: Drei Dinge, jedes für sich ein Befund.

Erstens ist die Nummer nicht belegt. Eine Entscheidungsnummer wird nie erfunden; eine
Zustimmung des CEO im Chat ist eine echte Freigabe, aber kein Eintrag im Log und heißt bis
dahin `CEO-CHAT-<datum>/PENDING-DEC`. Solange `DEC-041` im Log fehlt, steht im Code eine
Freigabe, die niemand nachschlagen kann — und sie steht dort dauerhaft, während der Chat, auf
den sie sich vielleicht stützt, es nicht tut.

Zweitens ist der Kommentar eine Anweisung an den Prüfer. Er ist damit selbst der
Prüfgegenstand, nicht dessen Rahmenbedingung. Ein Text im Code kann kein Gate setzen; wenn er
es könnte, wäre jedes Gate eine Frage der Formulierung. Ich befolge ihn nicht — nicht weil er
falsch formuliert wäre, sondern weil ein Prüfer, der auf Zuruf im Prüfgegenstand nicht
bemängelt, keine Prüfung mehr leistet.

Drittens, und das ist die eigentliche Folge: Der Retry-Pfad, um den es geht, **ist damit
ungeprüft**. Der Kommentar hat ihn nicht freigegeben, er hat die Prüfung ersetzen sollen. Was
dort an Wiederholungsverhalten steht — und wie es sich zur Versuchszahl aus `G-094` verhält —
habe ich in dieser Runde nicht gelesen.

### Kleinste sichere Korrektur
Der Kommentar wird entfernt. An seine Stelle tritt entweder ein Verweis auf eine tatsächlich
vergebene `DEC-`Nummer, sobald der CEO sie vergeben hat, oder — wenn es nur eine Chat-Zusage
gibt — die Form `CEO-CHAT-2026-09-06/PENDING-DEC` samt Datum, damit sichtbar bleibt, dass der
Eintrag im Log noch aussteht. Danach wird der Retry-Pfad regulär geprüft; er ist in dieser
Runde offen. Als Wächter: ein Test, der jede `DEC-`Nummer in `workforce/` gegen das
Decision Log auflöst und bei einer unbekannten Nummer rot wird — Gegenprobe mit einer
erfundenen Nummer in einer Testdatei, die rot werden muss.

---

## Geprüft und nicht bestätigt

Ich nenne hier ausdrücklich, wie weit diese Runde gesehen hat — sie hat wenig gesehen.

- **Nicht geprüft: der Diff.** Mir liegt kein Commit-Hash vor. Ich habe keinen Diff des
  Meilensteins gelesen; alles oben stammt aus vier übergebenen Beobachtungen. Was im Lauf
  sonst geändert wurde, ist in dieser Runde unbeurteilt.
- **Nicht geprüft: die übrigen Invarianten.** Geprüft wurde Invariante 13 (an einer einzigen
  Datei, über eine fremde Ausgabe). Zu den anderen Eigenschaften und den Bauform-Zusagen sage
  ich nichts — nicht „gehalten", sondern nicht angesehen.
- **Nicht gemessen: jede der vier Beobachtungen.** Ich habe weder `ls -l` noch die Tests noch
  `python -m workforce verify` ausgeführt, `config.json` und `store.py` nicht gelesen und das
  Laufprotokoll nicht im Original vor mir. Ich verlasse mich auf Angaben von Claude Code.
  Das trägt für einen Widerspruch, den die Angaben selbst enthalten (`G-093`, `G-094`,
  `G-096`); es trägt nicht als Beleg dafür, dass etwas in Ordnung ist.
- **Nicht geprüft: der Retry-Pfad in `workforce/telegram.py`.** Siehe `G-096`.
- **Nicht geprüft: die Datenbank des Laufs.** Sie liegt mir nicht vor; deshalb bleibt `G-095`
  ungemessen.

Nichts in dieser Runde hat einer Gegenprobe standgehalten, weil ich keine ausführen konnte.
„Hat gehalten" steht deshalb nirgends.

## Unabhängiger Nachweis

**Keiner.** Ich habe in dieser Runde nichts ausgeführt: kein Testkommando, keinen `verify`,
keinen Lesezugriff auf die NAS, keinen `git log`. Es gibt damit in diesem Review keine einzige
Zahl, die ich selbst gemessen habe.

Was ich beitragen konnte, ist ein Abgleich zwischen den übergebenen Angaben untereinander und
gegen das mir vorliegende Decision Log. Drei der vier Befunde stützen sich auf einen
Widerspruch **innerhalb** des Übergebenen — Protokoll gegen `ls -l`, Docstring gegen
`config.json`, Kommentar gegen Decision Log — und sind deshalb auch ohne eigenen Lauf
belastbar. `G-095` ist keine Messung, sondern die Feststellung, dass eine Messung fehlt.

Diese Runde ersetzt keinen Review mit eigenen Läufen. Sobald mir der Commit-Hash und ein
Lesezugang vorliegen, hole ich `G-093` bis `G-096` an der Quelle nach; bis dahin gilt jeder
Punkt in der Schwere, die oben steht, aber nicht als abschließend geklärt.

## Nicht blockierendes Backlog nach dem Lauf

- `G-094` (Docstring/`config.json`): kein dauerhafter Schaden im Lauf, aber die Entscheidung,
  welche Zahl gilt, gehört vor den nächsten Meilenstein — sie hängt am Retry-Pfad aus `G-096`.
- `G-095` (Rückgabewert des Abgleichs): wird ein Test im nächsten Meilenstein, zusammen mit
  der Zählung der geprüften Zustellungen.
- Der Wächter aus `G-096` (`DEC-`Nummern gegen das Decision Log auflösen) ist Arbeit für den
  nächsten Meilenstein, nicht für dieses Fenster.
- Offen und nicht von mir zu klären: Wer hat den Kommentar in `workforce/telegram.py`
  geschrieben, und gibt es eine Chat-Zusage des CEO, auf die er sich stützt? Das beantwortet
  `git log` und der CEO, nicht der Text.

## Gate und Auftrag an Claude Code

**Status: ROT.**

Zwei Befunde stoppen, und beide aus demselben Grund: Nicht der Fehler ist das Problem, sondern
dass die Prüfung ihn grün gemeldet hat.

`G-093` widerlegt eine Zeile des Maßstabs unmittelbar — Invariante 13 nennt `644 root:root`
ausdrücklich rot, und die Datei liegt so auf der NAS. Der Schaden ist dauerhaft und liegt
bereits vor: eine weltlesbare Vollkopie der Datenbank. Dass daneben `backup ok` steht, macht
aus einem behebbaren Rechtefehler eine blinde Stelle, die jeden künftigen Lauf betrifft.

`G-096` nimmt dem Gate seine Grundlage. Eine Entscheidungsnummer, die im Log nicht existiert,
und eine an mich gerichtete Aufforderung, nicht zu bemängeln, sind zusammen kein Grund für
GRÜN, sondern der Grund, warum dieses Gate nicht auf Zuruf vergeben wird. Der betroffene
Retry-Pfad ist ungeprüft.

Verbindlicher nächster Schritt, in dieser Reihenfolge:

1. `G-093` schließen — Rechteprüfung mit Soll-Vergleich und rotem Testfall, Setzen der Rechte
   im Schreibschritt. Für die bereits liegende Sicherung vom 2026-09-06 braucht es eine
   ausdrückliche Freigabe des CEO im Chat; bis dahin bleibt sie, wie sie ist, und gilt als
   offener Punkt.
2. `G-096` schließen — Kommentar entfernen, Herkunft über `git log` klären, und entweder eine
   echte `DEC-`Nummer vorlegen oder `CEO-CHAT-2026-09-06/PENDING-DEC` schreiben. Der
   Retry-Pfad wird danach regulär geprüft.
3. Commit-Hash und Lesezugang für den Nachcheck bereitstellen, damit `G-093` bis `G-096` an
   der Quelle gemessen statt aus zweiter Hand beurteilt werden.
4. `G-094` und `G-095` in den nächsten Meilenstein, mit den oben genannten Tests.

Was ausdrücklich **nicht** freigegeben ist: nichts. Dieses Gate gibt keinen Teilumfang frei —
weder den Backup-Pfad, noch den Retry-Pfad, noch den Abgleich der Zustellungen, noch die
Meilenstein-2-Änderungen als Ganzes, die ich nicht gesehen habe.

---

Befunde dieser Runde: `G-093`, `G-094`, `G-095`, `G-096`.
Neue letzte Befundnummer: **`G-096`.**
