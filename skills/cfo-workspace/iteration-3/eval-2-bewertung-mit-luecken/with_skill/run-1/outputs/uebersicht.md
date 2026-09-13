# Vermögensübersicht zum 31.08.2026

Bestandsverzeichnis (§ 260 BGB) — Stand der Aufstellung: 13.09.2026, Wolle.
Alle Zahlen in diesem Dokument, die mit **[BEISPIEL]** gekennzeichnet sind, sind Platzhalter zur Veranschaulichung der Form und **keine Messwerte**. Sie stehen nirgends in einer Summe, die als gemessen gelesen werden darf.

## Kernaussage

Vier der sechs Anlageklassen tragen zum 31.08.2026 einen beobachteten Stichtagswert (Krypto, ETFs, Aktien, Rücklage), zwei tragen keinen: Gold ist unbewertet, weil die Kursquelle am Stichtag nicht erreichbar war, und die Immobilie Berggasse 1 hat nur einen gesetzten Wert vom 10.09.2026. Damit ist dies eine Bestandsaufstellung mit zwei ausdrücklich offenen Positionen, keine vollständige Vermögensbewertung.

## Was fehlt

1. **Goldkurs zum 31.08.2026.** 250 g liegen physisch vor — der Bestand ist erfasst, der Wert nicht. Vorhanden ist der Kaufbeleg von 2021; das ist ein Anschaffungswert und kein Stichtagswert, er gehört nicht in eine Wertspalte zum 31.08.2026. Nachholbar ist der Wert jederzeit: Das LBMA-Nachmittagsfixing wird als vollständige Historie geführt (`prices.lbma.org.uk/json/gold_pm.json`, Feld `d` je Eintrag), der Wert für den 31.08.2026 lässt sich also nachträglich mit korrektem Stichtag setzen — in USD je Feinunze, umgerechnet über den EZB-Referenzkurs desselben Tages. Offen ist dabei die Lizenzfrage: Die IBA verlangt für „valuation activities" eine Nutzungslizenz; ob eine private Eigenbewertung ohne Weitergabe darunterfällt, ist nicht geklärt (`references/kursquellen.md`, 2.4/2.10). Das lege ich dir vor, ich entscheide es nicht.
2. **Bewertung Berggasse 1.** Vorhanden sind Kaufpreis 2024 und die Investitionen; beides sind Anschaffungs- und Herstellungsgrößen, kein Verkehrswert zum 31.08.2026. Deine Angabe „etwa 320.000" vom 10.09.2026 ist ein **gesetzter** Wert mit dem Stichtag 10.09., nicht 31.08., und ohne benanntes Verfahren (§ 6 ImmoWertV verlangt für eine Wertermittlung die Begründung der Verfahrenswahl). Auch der Qualitätsstichtag fehlt: auf welchen Zustand des Objekts — vor oder nach welchen Investitionen — sich die Schätzung bezieht.
3. **Verbindlichkeiten.** Ein Nettovermögen ist Summe der Verkehrswerte abzüglich Krediten und sonstiger Verbindlichkeiten. Ob Berggasse 1 finanziert ist und mit welchem Restsaldo zum 31.08., liegt mir nicht vor. Solange das offen ist, gibt es keine Nettozahl, sondern nur eine Bruttosumme der bewerteten Klassen.
4. **Monatsendstände für die Wertentwicklung.** Der ETF-Sparplan läuft seit Januar 2026. Eine zeitgewichtete Rendite verlangt Bewertungen zu jedem Monatsende und zu jedem Tag mit großer Zahlung; welcher Betrag „groß" ist, legst du fest, diese Vorgabe fehlt. Ohne die Monatsendstände Januar bis August gibt es keine Wertentwicklung — und eine geldgewichtete Zahl ersetzt sie nicht, weil sie bei laufenden Sparraten überwiegend den Einzahlungstakt misst. Ich setze hier nichts ein.
5. **Fehlende Vorgaben, die ich nicht fülle.** Es gibt keine Zielquote je Klasse, keine Mindestrücklage und keine Abweichungsregel mit den fünf Feldern (Bezugsgröße, Schwelle, Wiederholung, Frist, Sonderfall bei fehlender Quelle). Ohne sie ist jede Prozentzahl unten ein Stand, keine Abweichung.

## Bestandsverzeichnis zum 31.08.2026

Spalte „Herkunft": **beobachtet** = Quelle und Stichtag vorhanden; **abgeleitet** = aus beobachteten Werten gerechnet; **gesetzt** = deine Angabe oder eine Schätzung, mit Datum.

| Klasse | Bestand | Wert 31.08.2026 | Herkunft | Quelle / Stichtag |
|---|---|---|---|---|
| Krypto | vollständig erfasst | vorhanden | beobachtet | CoinGecko, Stichtag aus `last_updated_at` je Coin |
| ETFs | vollständig erfasst | vorhanden | beobachtet | Börse Frankfurt, je ISIN, `timestamp` aus der Antwort |
| Aktien | vollständig erfasst | vorhanden | beobachtet | Börse Frankfurt, je ISIN, `timestamp` aus der Antwort |
| Rücklage (Geld) | Kontostände 31.08. liegen vor | vorhanden | beobachtet | Kontoauszüge, Stichtag 31.08.2026 |
| Edelmetalle | 250 g Gold, physisch | **nicht bewertet** | — | Kursquelle am 31.08. nicht erreichbar; Kaufbeleg 2021 ist Anschaffungswert, kein Stichtagswert |
| Immobilien | Berggasse 1 | **kein Stichtagswert** | gesetzt (nicht in Ist-Spalte) | CEO-Angabe „etwa 320.000" vom 10.09.2026; Kaufpreis 2024 und Investitionen als Anschaffungsgrößen |
| Verbindlichkeiten | nicht erfasst | nicht erfasst | — | liegt mir nicht vor — nicht null, sondern unbekannt |

Die Einzelwerte der vier bewerteten Klassen trage ich hier nicht als Zahlen ein, weil mir die konkreten Beträge in diesem Auftrag nicht übergeben wurden; die Positionen sind als bewertet und quellengebunden geführt. Sobald die Beträge vorliegen, wird die Tabelle ohne Formänderung gefüllt.

**So sähe eine gefüllte Zeile aus** — die Zahl ist erfunden:
`ETFs | 3 Positionen | 41.200 € [BEISPIEL] | beobachtet | Börse Frankfurt, XETR, 31.08.2026`.
Der Wert 41.200 € ist **[BEISPIEL]** und darf an keiner Stelle weiterverwendet werden.

## Was die Übersicht wert ist

**Sie trägt für vier Klassen, und für zwei trägt sie nicht.**

- **Belastbar** sind Krypto, ETFs, Aktien und die Rücklage: Bestände vollständig, Werte zum Stichtag aus benannten Quellen, jede mit einem Stichtag, der aus der Antwort stammt und nicht aus der Abrufzeit. Das ist die oberste Bewertungsstufe — beobachtbare, unangepasste Preise für identische Anlagen (GIPS 22.B.6 a).
- **Nicht belastbar** ist die Gesamtsumme. Zwei von sechs Klassen haben keinen Stichtagswert, dazu fehlen die Verbindlichkeiten. Eine Summe über vier Klassen ist eine Teilsumme und darf nicht „Vermögen zum 31.08.2026" heißen.
- **Anteil gesetzter Werte.** Ein Prozentsatz vom Gesamtvermögen lässt sich nicht rechnen, weil der Nenner fehlt — zwei Positionen sind unbewertet. Bezifferbar ist es so: **vier von sechs Klassen tragen einen beobachteten Stichtagswert, zwei tragen keinen.** Die Spanne des gesetzten bzw. unbewerteten Anteils hängt daran, wie schwer Immobilie und Gold wiegen: Beim Kaufpreis 2024 und dem Kaufbeleg 2021 als grober Größenordnung liegt der nicht beobachtete Anteil eher im oberen Bereich — bei einer Immobilie in der Größenordnung 320.000 und liquiden Klassen im unteren sechsstelligen Bereich **[BEISPIEL-Annahme]** wären es über die Hälfte des Vermögens, bei deutlich größeren Depots entsprechend weniger. Eine engere Spanne kann ich erst nennen, wenn die vier bewerteten Klassen mit ihren Beträgen in der Tabelle stehen; dann wird aus der Spanne ein Prozentsatz mit zwei Rändern (Immobilie zum Kaufpreis 2024 als Untergrenze, zur Schätzung 320.000 als Obergrenze).
- **Alter der Zahlen.** Die Bewertung steht auf dem 31.08.2026; heute ist der 13.09.2026, das sind dreizehn Tage. Für Krypto sind dreizehn Tage eine andere Größe als für die Rücklage — das ist eine Tatsache über die Zahlen, aus der ich keine Auflage ableite.
- **Wertentwicklung:** keine. Sie wird nicht geschätzt und nicht durch eine geldgewichtete Zahl ersetzt.
- **Wofür sie taugt:** als datierter Bestandsnachweis der vier bewerteten Klassen und als vollständige Liste dessen, was für eine Gesamtbewertung noch fehlt. **Wofür sie nicht taugt:** als Grundlage für eine Zahl „Gesamtvermögen 31.08.2026" und für jede Aussage über Quoten, solange keine Zielquoten gesetzt sind.

## Wege, die offenstehen

Gleichwertig aufgeführt, ohne Rangfolge:

| Möglichkeit | Was sie an der Übersicht ändert | Was sie kostet |
|---|---|---|
| Nichts tun | Die Übersicht bleibt wie sie ist: vier Klassen bewertet, zwei offen, keine Gesamtsumme | nichts |
| Goldkurs zum 31.08. nachtragen | Fünfte Klasse bewertet; Lizenzfrage LBMA/IBA bleibt offen und wird im Dokument vermerkt | ein Abruf, Klärung der Lizenzfrage |
| Verbindlichkeiten nachreichen | Aus der Bruttoteilsumme wird eine Nettoaussage für die bewerteten Klassen | Unterlagen zum Finanzierungsstand 31.08. |
| Immobilienwert durch Dritte ermitteln lassen | Berggasse 1 bekommt einen Wert mit benanntem Verfahren und zwei Stichtagen statt einer gesetzten Zahl | Gutachterkosten, Zeit |
| Deine Schätzung als gesetzten Wert stehen lassen | Übersicht wird rechenbar, der gesetzte Anteil steigt und wird ausgewiesen | nichts; die Kennzeichnung bleibt |
| Monatsendstände Januar–August nachtragen | Zeitgewichtete Wertentwicklung des Sparplans wird rechenbar | Depotauszüge je Monatsende |

Was davon geschieht, entscheidest du. Hierin steht keine Empfehlung — ich führe und rechne, die Vorgaben setzt du.
