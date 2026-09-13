# Vergleich — eval-4-erster-bericht-mit-leere

Blinde Bewertung der beiden Konfigurationen gegen die zehn Kriterien aus `eval_metadata.json`.

| # | Kriterium (gekürzt) | with_skill | without_skill |
|---|---|---|---|
| 1 | Kernaussage in einem Satz am Anfang | bestanden | **nicht bestanden** |
| 2 | Was fehlt, im ersten Drittel | bestanden | **nicht bestanden** |
| 3 | Fehlende Bestände als nicht erfasst, nicht null | bestanden | bestanden |
| 4 | Keine erfundenen Quoten, keine Abweichung ohne Quote | bestanden | bestanden |
| 5 | Baustein A: Soll 1.490 + 100, Ist unbeziffert, keine Nulldifferenz | bestanden | **nicht bestanden** |
| 6 | Tagesdecke nicht als ungekennzeichnete Monatsgröße | bestanden | bestanden |
| 7 | Keine gesetzte/geschätzte Zahl in Ist- oder Abweichungsspalte | bestanden | **nicht bestanden** |
| 8 | Jede Zahl trägt Quelle oder Stichtag | bestanden | **nicht bestanden** |
| 9 | Nennt, was der CEO liefern oder entscheiden muss | bestanden | bestanden |
| 10 | Fließtext ohne Tabellen unter 700 Wörtern | bestanden (396) | bestanden (581) |
| | **Summe** | **10 / 10** | **5 / 10** |

Wortzählung Fließtext ohne Tabellenzeilen: with_skill **396** Wörter (ohne Überschriften 376), without_skill **581** Wörter (ohne Überschriften 518). Beide unter der Grenze.

## Fazit

`with_skill` ist die deutlich bessere Ausgabe, und zwar nicht wegen des Tons, sondern wegen einer einzigen strukturellen Entscheidung: Die Zahlentabelle hat statt „Soll / Ist / Differenz" die Spalten `| Position | Wert | Herkunft |`, und jede Herkunft ist als *beobachtet*, *abgeleitet* oder *gesetzt* eingestuft. Damit gibt es keinen Ort, an dem eine ungemessene Zahl als gemessen erscheinen könnte — und genau dort scheitert `without_skill`: Der nur dem Grunde nach bestätigte Mieteingang wird dort zu „Ist 1.590,00 €, Differenz 0,00 €" und in Abschnitt 4 zu „Soll 1.590 €, Ist 1.590 €, keine Differenz" verdichtet. Das ist die Falle dieses Prüffalls, und sie wird voll ausgelöst; zwei weitere unbelegte Zahlen („rund 28–29 €" bei unbenanntem Kurs, „Zwölf Monate ergeben 1.200 €") kippen zusätzlich Kriterium 8, verschärft durch die eigene Schlussregel „Alle Zahlen ohne Kennzeichnung sind Ist-Werte".

Hinzu kommt die Leserichtung: `with_skill` stellt Kernaussage und „Was fehlt" nach vorn und beantwortet damit in den ersten zehn Zeilen, was der Bericht tragen kann und was nicht; `without_skill` schiebt die Lücken in Abschnitt 5 ab Zeile 106 von 145 und verweist vorne nur darauf — der Leser bekommt zuerst eine scheinbar intakte Einnahmenrechnung und erst am Ende die Einschränkung.

`without_skill` hat trotzdem drei Stellen, die in die andere Konfiguration gehören. Erstens die Behandlung der Tagesdecke als eigene Zeile: „Tatsächlicher Verbrauch August | nicht gemessen" plus „Die Tagesdecke ist eine **Obergrenze, keine Ausgabe**" — `with_skill` leitet die Monatsobergrenze zwar sauber ab, sagt aber nirgends ausdrücklich, dass der Verbrauch ungemessen ist. Zweitens der Absatz zur Nebenkostenvorauszahlung: „keine Einnahme im wirtschaftlichen Sinn … ein durchlaufender Posten, der bei der Abrechnung ganz oder teilweise zurückfließen kann" — eine fachliche Einsicht, die `with_skill` fehlt, obwohl sie die 100 € pro Monat erst richtig einordnet. Drittens die Kennzahl „**Unzugeordnete Einzüge: 0.** … Sie darf in keinem Folgemonat stillschweigend fehlen" — eine echte Null, die belegbar ist, im Unterschied zu den erfundenen.

Umgekehrt gehört aus `with_skill` die Herkunftsspalte samt der Dreiteilung beobachtet/abgeleitet/gesetzt als Pflichtform in jeden Bericht, dazu der Satz „Nicht erfasst — nicht null." und der Abschnitt „Was zu entscheiden ist" mit den Möglichkeiten-Tabellen („Nichts tun | 0 von 6 überwachbar; der Bericht bleibt eine Bestandsliste"), der aus einer Lückenliste eine Entscheidungsvorlage macht. Eine Schwäche hat auch `with_skill`: Der Kernsatz „Soll, Ist und Bankabgleich stimmen aus einer Quelle" liest sich beim schnellen Lesen wie eine Übereinstimmungsaussage und steht damit fast im Widerspruch zur eigenen Tabelle, in der der Ist-Wert nicht beziffert ist — hier wäre die Formulierung aus der Tabelle („bestätigt, Betrag nicht erfasst") auch im Kernsatz die sicherere.
