# Befundnummern ohne Doppelvergabe — zwei Vorschläge im Vergleich

Stand: 08.09.2026. Ausgangslage: Gerds Anweisung reserviert eine Befundnummer, indem die
Kopfzeile in `REVIEW_GERD.md` zuerst geschrieben wird; bei Kollision behält der frühere
Commit die Nummer. Codex und Claude Code arbeiten abwechselnd im selben Repo, Remote auf
der NAS.

---

## Idee A (Tobias): Sperrdatei `NAECHSTE_NUMMER.txt`

Eine kleine Datei im Repo hält die nächste freie Nummer. Wer eine braucht, liest sie,
erhöht sie und committet sofort. Der Commit ist die Reservierung.

## Idee B (mein Gegenvorschlag): Nummern werden abgeleitet, nicht vergeben

Keine geteilte Ressource. Eine Befundnummer entsteht aus Datum und Seitenkürzel:

```
G-20260908-C1   erster Befund von Claude Code am 08.09.2026
G-20260908-X1   erster Befund von Codex am selben Tag
SV-20260908-C1  Vertretung, gleiches Muster
```

Zwei Seiten können am selben Tag beliebig viele Befunde schreiben, ohne voneinander zu
wissen — die Nummernräume überschneiden sich bauartbedingt nicht. Ein Test prüft drei
Dinge: die Form (`^(G|SV)-\d{8}-[CX]\d+$`), dass jede Nummer in `REVIEW_GERD.md` genau
einmal vorkommt, und dass das Kürzel zum Autor des Commits passt. Der bestehende Bestand
(`G-001` … `G-091`) bleibt unangetastet — die alten Nummern sind Historie, das Muster
gilt ab dem Umstellungstag, und der Test kennt beide Formen.

---

## Bewertung in zehn Punkten

**1. Löst es die Doppelvergabe wirklich?**
A: nur, wenn beide Seiten *vor* der Arbeit committen und pushen. Ein Commit allein
reserviert nichts — die andere Seite sieht ihn erst nach `git fetch`. Zwei Seiten, die
denselben Stand geholt haben, lesen dieselbe Zahl und erhöhen sie auf denselben Wert.
Der Konflikt wandert von `REVIEW_GERD.md` nach `NAECHSTE_NUMMER.txt`, er verschwindet
nicht. B: die Kollision ist unmöglich, nicht unwahrscheinlich. **B**

**2. Braucht es Koordination zwischen den Seiten?**
A: ja, und zwar zum frühestmöglichen Zeitpunkt — vor dem Denken, nicht nach dem Befund.
Das ist die teuerste Stelle für einen Zwang. B: keine. **B**

**3. Verhalten bei Offline-Arbeit / verzögertem Push**
A: bricht. Wer ohne Netz prüft und drei Befunde schreibt, hat drei Nummern reserviert,
die niemand sieht. B: unverändert korrekt, weil die Nummer aus lokal bekannten Größen
entsteht. **B**

**4. Merge-Verhalten**
A: `NAECHSTE_NUMMER.txt` ist eine Ein-Zeilen-Datei, an der beide Seiten dieselbe Zeile
ändern — der garantierte Merge-Konflikt, bei jedem einzelnen Befund. Automatisch lösbar
ist er nicht (Git kann nicht wissen, dass „73 gegen 73" zwei verschiedene Befunde sind).
B: beide Seiten hängen in verschiedene Zeilen an; ein Konflikt ist selten und trivial.
**B**

**5. Aufwand pro Befund**
A: lesen, erhöhen, committen, pushen, dann erst arbeiten — vier Schritte vor dem ersten
Satz. B: Nummer hinschreiben. **B**

**6. Nachvollziehbarkeit im Nachhinein**
A: die Nummernfolge ist dicht und sagt die Reihenfolge der Reservierung — hübsch, aber
die Reservierungsreihenfolge ist nicht die Befundreihenfolge, und `NAECHSTE_NUMMER.txt`
hat eine Historie, die niemand liest. B: die Nummer trägt Datum und Urheber, ohne dass
man irgendwo nachschlägt. Für ein Projekt, dessen Regeln „ein Name behauptet etwas, das
der Inhalt einlösen muss" heißen, ist das der bessere Handel. **B**

**7. Prüfbarkeit — gibt es einen Zustand, in dem der Wächter rot wird?**
A: schwer. Eine verlorene Reservierung (Nummer gezogen, Befund nie geschrieben) sieht
aus wie eine Lücke, und eine Lücke ist kein Fehler — der Test kann nicht unterscheiden.
B: die Form ist regulär prüfbar, Doppelvergabe ist ein exakter Duplikat-Test, und die
Zuordnung Kürzel↔Autor ist gegen den Commit messbar. Alle drei haben eine Gegenprobe.
**B**

**8. Abhängigkeit von Disziplin**
A: hängt vollständig daran, dass niemand „schnell mal" eine Nummer nimmt, ohne zu
committen. Das Projekt hat für genau diese Klasse schon einen Satz: Disziplin ist die
schwächste Absicherung (`test_mirrors.py`). B: es gibt nichts, woran Disziplin scheitern
könnte, außer der Form — und die ist getestet. **B**

**9. Verträglichkeit mit dem Bestand**
A: fügt eine neue geteilte Datei hinzu, die ins Manifest, in `deploy_paths.txt` und in
die Überlegungen zu `check_unmanaged.sh` müsste — eine Datei, die den Zustand *ist* statt
ihn zu beschreiben. Sie ist damit dieselbe Klasse wie ein hartkodierter Zählerstand
(Regel 24: Bestandszahlen altern). B: fügt nichts hinzu; ändert eine Konvention und einen
Test. Nachteil: der bestehende Nummernstand ist nicht mehr fortlaufend, und Verweise wie
„`G-071`" in `CLAUDE.md` stehen neben Verweisen neuer Form — zwei Muster nebeneinander,
das ist der reale Preis von B. **B, mit einem Abzug**

**10. Was passiert im Fehlerfall?**
A: bei einer Kollision behält — wie bisher — der frühere Commit die Nummer, die spätere
Seite muss ihren Befund umnummerieren, samt aller Querverweise, die sie schon geschrieben
hat. Genau der Ausgang, den die Idee vermeiden wollte, nur eine Datei weiter. B: der
Fehlerfall ist eine falsch geformte Nummer, und die fällt beim Test auf, bevor sie
irgendwo zitiert wird. **B**

---

## Fazit

**B gewinnt, 10:0 in der Richtung, 9,5:0,5 der Sache nach** (Punkt 9 geht mit Abzug
durch). Der Grund ist ein einziger und er ist nicht Geschmack: **Idee A verschiebt den
Konflikt, sie beseitigt ihn nicht.** Eine Sperrdatei ist nur dann eine Sperre, wenn es
eine Instanz gibt, die die Reihenfolge entscheidet, bevor beide Seiten gelesen haben — bei
Git ist das der Push, und der passiert nach dem Lesen. Alles, was A gewinnt, gewinnt sie
über Disziplin; alles, was B gewinnt, gewinnt sie über die Bauart.

**Was aus A mitkommt, und es ist der wertvollste Teil der Idee:** der Wunsch, dass die
Nummernvergabe eine *überprüfbare Handlung* ist statt einer Gewohnheit. Den nimmt B auf,
nur an einer anderen Stelle — nicht durch eine Datei, die reserviert, sondern durch einen
Test, der eine Doppelvergabe unmöglich stehen lässt. Ohne diesen Test wäre B nur eine
weitere Konvention, und Konventionen halten in diesem Repo bekanntlich genau so lange,
bis es eilig wird.

**Ein Vorbehalt, der zu B gehört:** Der Umstieg macht den Nummernraum uneinheitlich. Wenn
Tobias das nicht will, ist der brauchbare Kompromiss nicht A, sondern B mit dichter
Nummer und Seitenkürzel — `G-092-C`, `G-092-X` fallen weg, weil sie wieder eine geteilte
Zahl brauchen; also `G-C-001` und `G-X-001` als zwei fortlaufende Reihen. Kollisionsfrei,
kompakt, aber ohne Datum. Das wäre die einzige Variante, über die ich noch reden würde.

**Entscheidung liegt bei Tobias.** Nichts angelegt, nichts im Repo geändert.
