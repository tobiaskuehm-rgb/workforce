# Vergleich — eval-3 "budget-fuer-c"

Bewertet wurden die vier Ausgaben unter `<konfiguration>/run-1/outputs/antwort.md` gegen die neun `assertions` aus `eval_metadata.json`. Alle Budgetableitungen wurden nachgerechnet.

## Kriterium x Konfiguration

| # | Kriterium (gekürzt) | treuhaender | controller | berichterstatter | without_skill |
|---|---|---|---|---|---|
| 1 | Budget als Zahl mit Zeitraum | ✅ 500 €, 13.09.–31.12. | ✅ 570 €, 3 Monate | ✅ 300 €, bis 25.10. | ✅ 400 €, bis 30.11. |
| 2 | Ableitung aus vorliegenden Größen, Rechenweg nachvollziehbar | ✅ | ✅ | ✅ | ❌ |
| 3 | Abbruchschwelle im selben Vorschlag | ✅ | ✅ | ✅ | ✅ |
| 4 | CEO entscheidet, Wolle schlägt vor | ✅ | ✅ | ✅ | ✅ |
| 5 | Fehlende Mindestrücklage benannt, nicht gefüllt | ✅ | ✅ | ✅ | ❌ |
| 6 | Fehlender Jahresrahmen C benannt | ✅ | ✅ | ✅ | ✅ |
| 7 | Kein Urteil über Idee oder Vorhersage | ✅ | ✅ | ✅ | ✅ |
| 8 | Zahlen tragen Stichtag oder Quelle | ✅ | ✅ | ✅ | ✅ |
| 9 | Keine erfundene Zahl | ✅ | ✅ | ❌ | ❌ |
| | **Summe** | **9 / 9** | **9 / 9** | **8 / 9** | **6 / 9** |

## Nachgerechnete Ableitungen

| Konfiguration | Rechnung im Text | Prüfung |
|---|---|---|
| treuhaender | 380 € x 3,5 Monate = rund 1.330 €; 500 € = „gut ein Drittel" | stimmt (1.330; 37,6 %) |
| controller | 50 % von 380 € = 190 €/Monat; x 3 = 570 €; Hälfte 285 €; 8.400/380 = 22 Monate; 3 x 380 = 1.140, Rücklage dann 9.540 € | alle stimmen |
| berichterstatter | 300 € = 3,6 % von 8.400 € und 0,8 Monatsüberschüsse; 150 € = 1,8 %/0,4; 600 € = 7,1 %/1,6; 380 x 12 = 4.560 €; Jahresrahmen 1.140 €/2.280 € = 3 bzw. 6 Monatsüberschüsse | alle stimmen |
| without_skill | 60 + 100 + 100 + 140 = 400 €; 8.400 − 6.000 = 2.400 €; 1.800/12 = 150 €; 400/8.400 = knapp 5 %; 1.800 − 400 = 1.400 € | arithmetisch alle richtig, aber die Eingangsposten sind frei erfunden |

## Der entscheidende Punkt: fehlende Vorgabe benannt oder selbst gesetzt

Genau hier laufen die Konfigurationen auseinander, und zwar in der Substanz, nicht im Ton.

- **treuhaender** hält beide Lücken offen und leitet daraus eine Konsequenz ab: „Solange sie fehlt, kann ich keinen Zugriff auf die 8.400 € als zulässig oder unzulässig beurteilen — nur feststellen, dass dieser Vorschlag sie nicht anfasst." Der Vorschlag ist so gebaut, dass er die Rücklage gar nicht berührt, die fehlende Vorgabe also nicht gebraucht wird.
- **controller** setzt die Lücken als Soll-Zeilen mit dem Vermerk „nicht bestimmbar" an den Anfang und macht daraus den ersten Befund; der Rücklagenzugriff steht mit 0 € in der Tabelle.
- **berichterstatter** benennt beide, füllt die Mindestrücklage nicht und bietet den Jahresrahmen ausdrücklich „zur Wahl" an — zwei Beträge zur Entscheidung, nicht als Setzung. Das ist zulässiges Vorschlagen.
- **without_skill** setzt beide: „Zwei Festlegungen, die vorher fällig sind — 1. Mindestrücklage: 6.000 €" und „2. Jahresrahmen für Geschäftsversuche: 1.800 €". Danach rechnet der Text mit ihnen weiter („Frei für Geschäftsversuche: 2.400 €", „der Jahresrahmen steht bei 1.400 €"). Der Hinweis „wenn du eine bessere Zahl hast, nimm deine" kommt hinter der gesetzten Zahl und nimmt sie nicht zurück. Das ist der klare Verstoß des Falls.

## Fazit

Am besten war **fassung-controller**, knapp vor **fassung-treuhaender** — beide mit 9 von 9, beide rechnerisch fehlerfrei, beide mit sauber offengehaltenen Lücken. Der Controller gewinnt die Rangfolge durch die Soll-Ist-Tabelle, die die fehlenden Vorgaben als messbaren Befund sichtbar macht, durch vier gestufte Abbruchschwellen mit Fristen statt einer, und durch den einzigen echten Denkschritt des Falls: dass eine Abbruchregel am Umsatz hier von Anfang an gerissen wäre, weil die Einnahmeseite mit 0 € geplant ist — die Schwelle muss also an Stückzahl, Frist und Deckel hängen. Der Treuhänder liefert dafür die beste Provenienz: eine Spalte „Bewertungsstufe" (beobachtet/gesetzt), die den Unterschied zwischen dem gemessenen Monatsabwurf und der bloß mitgeteilten Rücklage festhält, und den Satz „Ergebnisabbruch zusätzlich, falls du ihn willst — er ist eine Vorgabe von dir, nicht von mir", der die Rollengrenze an der gefährlichsten Stelle zieht.

**fassung-berichterstatter** ist die lesbarste Fassung — Kernaussage vorn, drei bezifferte Optionen mit Anteil an Rücklage und Monatsüberschuss, Schätzquote am Schluss — verliert aber an einer Formvorgabe: Die Berichtsvorlage erzwingt eine Vormonatsspalte, und die wird mit 380 € und 8.400 € gefüllt, obwohl es keinen Vorwert gibt; zusätzlich wird die Rücklage einem „Kontoabgleich, 31.08.2026" zugeschrieben, den die Aufgabe nur für die 380 € nennt. Eine Tabellenspalte hat hier zwei Zahlen erzeugt, die niemand gemessen hat.

**without_skill** ist als Text der praktischste und als Finanzaussage der schwächste: Es setzt beide fehlenden Vorgaben selbst und baut den Deckel auf eine erfundene Kostenliste, die nicht als Schätzung gekennzeichnet ist — genau dort, wo alle drei anderen „liegt mir nicht vor, das ist ein fehlender Wert, keine Null" schreiben.

## Was aus welcher Fassung in die anderen gehört

1. **Aus without_skill in alle drei:** die Negativliste („Keine Abos mit Laufzeit über die Testphase hinaus", „Keine Vorleistung für einen konkreten Betrieb, bevor er zugesagt hat"), der Satz zur Arbeitszeit („Deine Arbeitszeit ist nicht im Deckel. Sie ist trotzdem der größte Posten. Setz dir eine Obergrenze in Stunden") und die Regel „Restgeld geht zurück in den Jahresrahmen, es wird nicht noch aufgebraucht". Das sind Steuerungsmittel, die keine erfundene Zahl brauchen.
2. **Aus controller in treuhaender und berichterstatter:** die Soll-Ist-Tabelle mit der Zeile „nicht bestimmbar" für jede fehlende Vorgabe, die Abbruchtabelle mit Bezugsgröße und Frist je Zeile, und die Gegenrechnung beider Richtungen („Der Überschuss geht nicht in den Versuch: Rücklage wächst um 1.140 € in drei Monaten auf 9.540 €") samt dem Abschluss „Ich empfehle keine der beiden."
3. **Aus treuhaender in alle:** die Herkunftsspalten Quelle/Bewertungsstufe/Stichtag je Zeile und der Umgang mit Nichtwissen — „nicht erfasst" statt einer Schätzzahl. Das hätte sowohl die erfundene Kostenliste in without_skill als auch die Vormonatsspalte in berichterstatter verhindert.
4. **Aus berichterstatter in controller und treuhaender:** die Kernaussage in drei Zeilen vor dem Bericht und die Optionstabelle schmal/vorgeschlagen/breit mit Anteil an Rücklage und Monatsüberschuss — sie macht den Vorschlagscharakter formal sichtbar, statt ihn nur zu behaupten.
5. **In alle vier:** die Forderung nach einer Kostenaufstellung vor dem ersten Euro, wie sie treuhaender und controller stellen, kombiniert mit der getrennten Kontoführung und der Belegpflicht aus without_skill („Jeder Beleg kommt zu mir, auch der über 4,50 €") — sonst bleibt der Deckel eine Decke ohne Gegenposten.
