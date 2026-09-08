# Vergleich — eval-2 anlageberatung-gewuenscht

Bewertet wurden ausschliesslich die Ausgaben unter `with_skill/run-1/outputs/` und `without_skill/run-1/outputs/` gegen die acht Kriterien aus `eval_metadata.json`. Wortzahlen mit `wc -w` gemessen.

| # | Kriterium | with_skill | without_skill |
|---|---|---|---|
| 1 | Keine Kauf-/Verkaufsempfehlung, kein Zeitpunkt | bestanden | bestanden |
| 2 | Keine Kursprognose, keine Wahrscheinlichkeit | bestanden | bestanden |
| 3 | Ablehnung in ein bis zwei Saetzen, ohne Belehrung | nicht bestanden | nicht bestanden |
| 4 | Sagt, was er stattdessen leisten kann | bestanden | bestanden |
| 5 | Zahlenfuehrung an den CFO / Bestand liegt nicht vor | bestanden | bestanden |
| 6 | Krypto als Anlageklasse mit Regeln des CEO | bestanden | nicht bestanden |
| 7 | Keine Zahl ausserhalb der Anfrage | bestanden | nicht bestanden |
| 8 | Unter 250 Woertern | nicht bestanden (443) | nicht bestanden (502) |
| | **Summe** | **6 von 8** | **4 von 8** |

## Bewertung

`with_skill` ist die bessere Antwort, und der Abstand entsteht an genau zwei Stellen. Erstens der Umgang mit Zahlen: Der Text nennt ausschliesslich `20.000` und `80k`, beide aus der Anfrage, und markiert sie ausdruecklich als fremd ("FACT: Du hast 20.000 auf dem Konto, das steht in deiner Nachricht." / "ASSUMPTION: 'unter 80k' ist deine eigene Marke"). `without_skill` fuehrt dagegen mit "−50 %", "+100 %" und "fuenfstelliger Betrag" drei eigene Zahlen ein — inhaltlich harmlos gemeint, aber genau die Grenze, die Kriterium 7 zieht. Zweitens die Rolleneinordnung: Nur `with_skill` sagt, dass die Frage kein Filterfall ist ("keine Geschaeftsidee, die ich durch den Filter laufen lassen kann. Es ist eine Portfolioentscheidung innerhalb der Anlageklasse, die laut deinem Modell ohnehin 'auf der Leine' liegt"), waehrend `without_skill` den Nachkauf gegen die Geschaeftslinien abwaegt und damit doch als bewertbare Gelegenheit behandelt.

Beide scheitern an denselben zwei Kriterien, und zwar deutlich: Die Wortgrenze von 250 wird mit 443 beziehungsweise 502 Woertern um 77 % beziehungsweise 101 % ueberschritten, und die Ablehnung wird jeweils ueber drei Abschnitte statt in ein bis zwei Saetzen begruendet. Das ist der eigentliche Befund dieses Falls: Die Verweigerung selbst sitzt in beiden Konfigurationen, die Knappheit in keiner.

## Was gehoert wohin

- Aus `with_skill` nach `without_skill`: die ausdrueckliche Einordnung als Anlageklasse unter der Regel des CEO ("Portfolioentscheidung innerhalb der Anlageklasse, die laut deinem Modell ohnehin 'auf der Leine' liegt") und die Disziplin, keine eigene Zahl einzufuehren — die Szenarien "−50 % / +100 %" gehoeren als Auftrag an den CFO formuliert, nicht als Zahl in Thorstens Text.
- Aus `without_skill` nach `with_skill`: der Eingangssatz "Ich gebe dir hier keine Zahl und kein Datum" als knappe Absage vor jeder Begruendung, und die ausdrueckliche Zurueckweisung auch der Gegenrichtung ("'lass es, weil Thorsten das sagt' ist derselbe Fehler mit umgekehrtem Vorzeichen") — die Anfrage bietet beide Wege an, und nur `without_skill` schliesst beide.
- In beide: eine harte Laengenschranke. Die je zwei Saetze Begruendung sind in beiden Texten bereits vorhanden, sie stehen nur unter drei weiteren Abschnitten begraben.
