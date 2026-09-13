# Vergleich — eval-2 "bewertung-mit-luecken"

Bewertet wurden die vier Ausgaben unter `<konfiguration>/run-1/outputs/uebersicht.md` gegen die neun `assertions` aus `eval_metadata.json`. Beweislast beim Kriterium: ohne wörtliches Zitat nicht bestanden; mehrteilige Kriterien nur bei belegten Teilen.

## Kriterium × Konfiguration

| # | Kriterium (gekürzt) | Treuhänder | Controller | Berichterstatter | without_skill |
|---|---|:--:|:--:|:--:|:--:|
| 1 | Bewertungsstufe/Herkunft je Position | ✅ | ✅ | ✅ | ✅ |
| 2 | Anteil Setzungen/Schätzungen als Zahl | ✅ | ✅ | ✅ | ✅ |
| 3 | CEO-Schätzung als seine Angabe **mit Datum** | ✅ | ❌ | ✅ | ❌ |
| 4 | Gold: kein Einstand, kein Weglassen, keine Null; Quelle benannt | ✅ | ✅ | ✅ | ✅ |
| 5 | Quelle und Stichtag je abgerufener Bewertung | ✅ | ✅ | ✅ | ✅ |
| 6 | Stichtag 31.08.2026 durchgehalten | ✅ | ✅ | ✅ | ✅ |
| 7 | Sparplan: zeitgewichtet bzw. Einzahlungstakt benannt | ✅ | ✅ | ✅ | ❌ |
| 8 | Gesamtsumme **und** Unsicherheit darin | ✅ | ❌ | ✅ | ✅ |
| 9 | Keine Empfehlung, keine Gut-Schlecht-Wertung | ✅ | ✅ | ❌ | ✅ |
| | **Summe** | **9/9** | **7/9** | **8/9** | **7/9** |

## Nachrechnung (kein Kriterium, aber Befund)

| Konfiguration | genannter Anteil | gegen die eigene Tabelle | Ergebnis |
|---|---|---|---|
| Treuhänder | 69,2 % gesetzt / 30,8 % beobachtet | 320.000 / 462.100 = 69,25 %; 142.100 / 462.100 = 30,75 % | stimmt |
| Controller | **60 % nicht belegt** | Kennzahltabelle setzt den unbelegten Block mit **334.000 €** an; die eigenen Posten ergeben 19.000 € Gold + 320.000 € Immobilie = **339.000 €** | **Abweichung 5.000 €** — die Bezugszahl ist aus der eigenen Aufstellung nicht ableitbar. Die Aussage kippt nicht (339.000/557.400 = 60,8 %), die Herleitung fehlt trotzdem. |
| Berichterstatter | 67,6 % Schätzung | 320.000 / 473.500 = 67,58 %; Zwischensumme 48.200+61.500+19.800+24.000 = 153.500 €; Sensitivität 10 % von 320.000 = 32.000 € | stimmt durchgehend |
| without_skill | "rund zwei Drittel" | (320.000 + ~18.000) / ~500.700 = 67,5 %; belegte Summe 48.000+96.500+18.200 = 162.700 € | stimmt, aber nie als Prozentsatz ausgewiesen |

Zwei weitere Rechenbefunde: **Treuhänder** schreibt "die zwölf Tage dazwischen" — zwischen 31.08. und 13.09.2026 liegen 13 Tage (der Controller zählt korrekt "13 Tage später"). **Controller** mischt zwei Grundgesamtheiten: die Quoten 28 / 62 / 10 % beziehen sich auf die belegte Summe von 218.400 €, die 60 % auf das Gesamtbild; das steht nebeneinander, ohne dass der Unterschied benannt wird.

## Fazit

Am besten ist **fassung-treuhaender**, als einzige mit 9/9 und ohne inneren Widerspruch: Die dreistufige Legende (beobachtet / abgeleitet / gesetzt) steht über der Tabelle statt in der Prosa, jede Zeile trägt Stufe *und* Quelle *und* Stichtag, die CEO-Angabe ist taggenau datiert und um den Zustandsbezug ergänzt — die einzige Ausgabe, die bemerkt, dass eine Immobilienschätzung *zwei* Stichtage braucht und beide fehlen. Ihre Summenlogik ist die sauberste: bewertete Zwischensumme ja, Gesamtvermögen "nicht abschließend bezifferbar".

**fassung-berichterstatter** liegt inhaltlich fast gleichauf und ist rechnerisch als einzige fehlerfrei; sie scheitert nur an einem selbst gesetzten Widerspruch — "Vorschlag zur Prüfung: Rate unverändert, solange die Rücklage über sechs Monatsausgaben liegt" ist eine Empfehlung mit eigener Schwelle, zwei Zeilen über dem Satz "Zu keiner dieser Anlagen gebe ich eine Empfehlung". **fassung-controller** ist analytisch die schärfste (Kennzahl vor Bestand, Soll-Ist-Abschnitt, der das Fehlen jeder Vorgabe zum ersten Befund macht), verliert aber zwei Kriterien an fehlender Datierung und an der verweigerten Gesamtsumme — und hat als einzige einen echten Rechenwiderspruch. **without_skill** liefert den fachlich wichtigsten Einzelfund des ganzen Feldes (die fehlende Restschuld der Immobilie), bleibt aber ohne Datum an der CEO-Angabe, behandelt den Sparplan nur als Doppelzählungsrisiko statt als Renditefrage und nennt unmittelbar nach dem eigenen Verbot, Kurse zu schätzen, einen Goldpreiskorridor aus dem Gedächtnis.

**Was in die jeweils anderen gehört:** Die Sensitivitätsrechnung des Berichterstatters — "verschiebt sie sich um 10 %, bewegt sich die Summe um 32.000 €" — ist die einzige Stelle im Feld, die Unsicherheit in Euro statt in Prozent ausdrückt, und gehört in alle vier. Der Satz des Controllers "Zwei Zahlen für dieselbe Immobilie, die zufällig nah beieinander liegen, sind kein gegenseitiger Beleg" schließt genau die Lücke, die der Treuhänder mit seiner Gegenprobentabelle offen lässt. Aus without_skill gehört die Restschuldfrage als feste Zeile in jede Immobilienposition ("Ein Immobilienwert ohne die zugehörige Restschuld ist kein Vermögenswert, sondern eine halbe Bilanz"), aus dem Treuhänder die Datumsdisziplin "Datum der Angabe: 13.09.2026, Zustandsbezug: unbestimmt" und die Nachtragsregel "*beobachtet, nachgetragen am ⟨Datum⟩*, nicht rückwirkend so dargestellt, als wäre sie am Stichtag erhoben worden".

**Zu den Kriterien:** Kriterium 8 ("nennt eine Gesamtsumme") arbeitet gegen Kriterium 4 — wer das Gold korrekt unbewertet lässt, kann keine vollständige Gesamtsumme nennen; der Controller fällt genau für die Vorsicht durch, die der Fall sonst belohnt. Kriterium 3 legt keine Datumsgenauigkeit fest ("2026" vs. "09/2026" vs. "13.09.2026"), Kriterium 9 vermengt zwei verschiedene Verbote, und die Kriterien 1 und 5 überlappen für alle marktbewerteten Positionen. Kein Kriterium prüft die innere Rechenkonsistenz — ohne die zusätzliche Nachrechnung wäre der Widerspruch 334.000/339.000 des Controllers unbemerkt geblieben, obwohl er die Leitzahl der ganzen Ausgabe trägt.
