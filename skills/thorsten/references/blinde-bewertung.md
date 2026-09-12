# Blinde Bewertung — wie ein Kandidat eine Note bekommt, die nicht von seinem Erzeuger stammt

Grundlage: `DEC-046` (CEO, 2026-09-11) auf den 3-Loop
`workforce/reviews/2026-09-11_3loop_battle_karl.md`. Gebaut von Marv am 2026-09-11.

**Der Zweck in einem Satz:** „Thorsten ist besser geworden" soll sich von „Thorsten benotet sich
besser" unterscheiden lassen — und das geht nur, wenn Erzeuger und Bewerter zwei sind.

**Was diese Datei nicht behauptet:** dass eine fremde Instanz unabhängig ist. Sie kann dasselbe
Modell mit denselben Kriterien sein und dieselben Neigungen haben. Die Note ist deshalb eine
Sortierhilfe; den Beleg liefert erst die Probe. Das ist keine Floskel, sondern die Auflage, die
den 3-Loop entschieden hat.

## Die drei Stellen

| Stelle | Wer | Ausgang |
|---|---|---|
| Erzeugen | Thorsten (drei montags), CEO (drei montags) | Kandidatenblatt, ohne Note |
| Bewerten | Marv, als fremde Instanz, blind | Note je Kriterium, Summe, Feld |
| Regeln | Thorsten schlägt vor, Karl gibt frei | Änderung an `FILTER.md`, ab nächstem Durchgang |

Niemand hat zwei dieser Stellen im selben Durchgang.

## Was Marv bekommt

Ein **Kandidatenblatt** je Kandidat, eine Datei, und sonst nichts:

1. **Kennung** — Buchstabe oder Zahl des Durchgangs, ohne Herkunft im Namen.
2. **Der Kandidat** in höchstens 200 Wörtern: was verkauft wird, an wen, wofür.
3. **Die Tatsachen mit Quelle und Datum**, so wie Thorsten sie erhoben hat — Preise,
   Bestandsanbieter, Rechtslage. Ohne Quelle gilt eine Angabe als `UNKNOWN`, nicht als Tatsache.
4. **Die Kriterien**: die sieben Kriterien und Gewichte aus `FILTER.md`, Stufe 2, wörtlich
   mitgeliefert — Marv schlägt sie nicht selbst nach, sonst benotet er einen anderen Stand.
5. **Der Regelstand**: der Commit-Hash von `FILTER.md` und sein Datum, z. B. `37ed946 2026-09-10`.
   Ermittelt mit `git log -1 --format='%h %ad' --date=short -- FILTER.md`.
6. **Das Feld**, in das der Kandidat gehört (Brandschutz, Vermietung, IT-Dienstleistung, …) —
   eine Angabe, keine Wertung, und sie ist nötig, weil der Wächter die Häufung darüber zählt.

**Was nicht mitgeht:** wer den Kandidaten erzeugt hat; frühere Noten desselben Kandidaten;
Thorstens Gedächtnis; die Kennungen der Mitbewerber in einer Reihenfolge, die die Herkunft
verrät. Die Blätter eines Durchgangs werden vor der Übergabe gemischt.

**Wenn ein Blatt die Herkunft doch verrät** — ein Satz wie „mein Montagskandidat" —, benotet Marv
nicht, sondern gibt das Blatt zurück. Eine Note auf einem verbrannten Blatt heißt „nach
einheitlichem Raster bewertet", nicht „blind", und wird auch so eingetragen.

## Was Marv zurückgibt

Je Kandidat ein Block, in genau dieser Form:

```
Kennung:     G
Feld:        Brandschutz
Bewerter:    Marv
Regelstand:  37ed946 2026-09-10
Ertrag je Stunde        3 ×3 = 9    <ein Satz, warum; Quelle oder UNKNOWN>
Systemanteil            5 ×3 = 15   <ein Satz>
Recht                   5 ×2 = 10   <ein Satz>
Wiederkehr              5 ×2 = 10   <ein Satz>
Zeit bis zum ersten Euro 3 ×1 = 3   <ein Satz>
Kapital einmalig        4 ×1 = 4    <ein Satz>
Ausstieg aus der Stunde 5 ×1 = 5    <ein Satz>
Summe:       56 von 65
```

Regeln für den Bewerter, kurz:

- **Je Kriterium ein Satz.** Ohne Satz keine Note.
- **Ohne Quelle keine Note**, sondern `UNKNOWN` an der Zeile; ein `UNKNOWN` zählt als 0 und wird
  in der Summe sichtbar gemacht, nicht weggemittelt.
- **Keine Statusvergabe.** `KILL`, `PARK`, `TEST` entscheidet Thorsten, nicht der Bewerter; der
  Bewerter liefert Zahlen und Sätze.
- **Kein Vorschlag zur Änderung des Filters.** Fällt dem Bewerter etwas am Raster auf, schreibt
  er es unter den Block als Bemerkung — sie geht an Thorsten und wird nicht Teil der Note.

## Wie es ins Gedächtnis kommt

Die Note wandert in die Tabelle **Frühere Urteile** in `skills/gedaechtnis/thorsten.md`. Die
Tabelle bekommt dafür diesen Kopf; alte Zeilen bleiben stehen, wie sie sind:

```
| Datum | Kandidat | Feld | Erzeuger | Bewerter | Regelstand | Summe | Status | Quelle |
```

| Spalte | Was hineingehört |
|---|---|
| `Datum` | Tag der Benotung, `JJJJ-MM-TT` |
| `Kandidat` | Kennung und Kurztitel |
| `Feld` | wie auf dem Blatt |
| `Erzeuger` | `Thorsten`, `CEO` oder wer sonst den Kandidaten gebracht hat |
| `Bewerter` | wer benotet hat, hier `Marv`; **nie derselbe wie der Erzeuger** |
| `Regelstand` | Hash und Datum des `FILTER.md`-Commits, der beim Benoten galt |
| `Summe` | Zahl von 0 bis 65 |
| `Status` | Thorstens Entscheidung, danach vergeben |
| `Quelle` | Durchgang, Datum, Datei des Bewertungsblocks |

**Eine Fassung ersetzt ihre Zeile.** Wird ein Kandidat überarbeitet, wird seine Zeile ersetzt und
das alte Datum durchgestrichen — keine zweite Zeile für denselben Gedanken.

**Erzeuger ist eine eigene Spalte**, obwohl `DEC-046` nur Bewerter, Regelstand und Feld nennt:
Die Zusicherung „kein Bewerter gleich Erzeuger" lässt sich ohne sie nicht prüfen, und aus der
Quellenspalte zu raten wäre eine Textsuche, kein Vergleich. Dasselbe gilt für `Summe`, ohne die
der Wächter die zehn höchsten Werte nicht finden kann. Karl kann beides streichen; dann fallen
die zugehörigen Prüfungen mit.

## Der Wächter

`skills/test_battle.py` liest diese Tabelle und prüft drei Dinge, jedes mit Gegenprobe:

1. **Kein Bewerter gleich Erzeuger.**
2. **Kein Regelstand jünger als die Note** — ein am 2026-09-10 benoteter Kandidat darf keinen
   Filterstand vom 2026-09-11 tragen; sonst wäre im selben Lauf gemessen und geregelt worden.
3. **Häufung unter der Schwelle** — liegen mehr als die Hälfte der zehn höchsten Summen in
   einem Feld, wird die Zeile rot und Karl legt sie donnerstags vor.

Zeilen ohne die neuen Spalten kann er nicht prüfen. Er **überspringt sie laut** und meldet, wie
viele Zeilen vollständig sind; er meldet nie Grün für etwas, das er nicht gelesen hat.

## Was offen ist

- Die Zeilen im Gedächtnis haben die Spalten heute noch nicht. Der Wächter läuft, misst aber
  null Zeilen, bis der erste Durchgang nach diesem Verfahren gelaufen ist.
- Ob Marv als Bewerter genug Abstand hat, ist **nicht gemessen**. Die erste Gegenprobe wäre,
  einen bereits benoteten Kandidaten blind erneut vorzulegen und die Abweichung zu messen.
