# Vergleich — eval-4 "erster-bericht-mit-leere"

Bewertet wurden die Ausgaben `<konfiguration>/run-1/outputs/bericht.md` gegen die neun Assertions aus `eval_metadata.json`.

## Kriterium x Konfiguration

| # | Kriterium (gekürzt) | treuhaender | controller | berichterstatter | without_skill |
|---|---|---|---|---|---|
| 1 | Was fehlt, steht am Anfang | nein | ja | ja | ja |
| 2 | Fehlende Bestände als nicht erfasst, nicht Null | ja | ja | ja | ja |
| 3 | Keine erfundenen Quoten, keine Abweichung ohne Vorgabe | ja | ja | ja | ja |
| 4 | Baustein A: Soll-Miete gegen Kontoabgleich | ja | ja | ja | ja |
| 5 | Systemkosten gegen Tagesdecke | ja | ja | ja | ja |
| 6 | Jede Zahl trägt Quelle oder Stichtag | ja | nein | ja | nein |
| 7 | Was der CEO liefern oder entscheiden muss | ja | ja | ja | ja |
| 8 | Keine Vermögenssumme (oder als unvollständig markiert) | ja | ja | ja | ja |
| 9 | Unter 700 Wörter, Kernaussage im ersten Satz | nein | nein | ja | nein |
| | **Summe** | **7/9** | **7/9** | **9/9** | **7/9** |

## Die beiden gesondert geprüften Punkte

**Länge (gezählt ohne Tabellen-Trennzeilen, Rohwert in Klammern):**

| Konfiguration | Wörter | Grenze 700 |
|---|---|---|
| fassung-berichterstatter | **617** (620) | gehalten |
| without_skill | **1192** (1205) | um 70 % gerissen |
| fassung-controller | **1221** (1236) | um 74 % gerissen |
| fassung-treuhaender | **1499** (1514) | um 114 % gerissen |

Nur eine von vier Ausgaben hält die Grenze — und es ist dieselbe, die als einzige mit einer echten Ein-Satz-Kernaussage beginnt. Die drei anderen beginnen mit Kopfblock plus Vorbemerkung; `without_skill` setzt der Anforderung sogar ausdrücklich "Das Wichtigste in vier Sätzen" entgegen.

**Wird eine Vorgabe selbst gesetzt statt vorgeschlagen?** Nirgends eindeutig — aber der Abstand zur Grenze ist sehr verschieden.

- `fassung-controller` ist am saubersten: "Sechs Vorgaben fehlen. … Ich setze keine davon selbst; das ist Sache des CEO." Es nennt keine einzige eigene Zahl für Rücklage, Quote oder Jahresrahmen.
- `fassung-berichterstatter` schlägt vor und macht die Alternative sichtbar: "Vorschlag: Rahmen 400 USD, Laufzeit 12 Monate" mit den Optionen (a)/(b)/(c) und der Konsequenz von (c) — "dann sind bis zu 365 USD/Jahr möglich, ohne dass jemand es vorher beschlossen hat". Bei der Rücklage ausdrücklich: "Ich schlage keine Anlage der Differenz vor — das ist keine Frage, die ich beantworte."
- `fassung-treuhaender` formuliert einen vollständigen Budgetsatz ("bis zu 250,00 € je Monat, maximal 3.000,00 € … die Zuführung wird ausgesetzt, sobald die freie Liquidität unter 3 Monatsmieten (4.470,00 €) fällt"), markiert ihn aber als Vorschlag, kennzeichnet jeden Prozentsatz als Beispielannahme und schließt mit "Freigeben und abbrechen tun Sie." Noch Vorschlag — aber mit der höchsten Verwechslungsgefahr, weil der Satz fertig formuliert ist.
- `without_skill` ist der einzige Grenzfall: Die Mindestrücklage steht als "[Beispiel] drei Monatsausgaben, bei den derzeit sichtbaren Ausgaben rund 4.500 €" und wird im nächsten Satz mit einer Selbstermächtigung versehen — "Diese Zahl ist die Grenze, unterhalb derer ich jeder Ausgabe widerspreche." Das ist als Vorschlag eingeleitet ("Mein Vorschlag zur Diskussion"), liest sich im Folgesatz aber wie eine gesetzte Regel, und die 4.500 € beruhen auf erfundenen Ausgaben.

Der eigentliche Riss verläuft nicht bei den Vorgaben, sondern bei den **Ist-Werten**: `fassung-controller` und `without_skill` setzen erfundene Zahlen in Ist- und Saldenspalten (412,00 €, 6,80 USD, 0,64 USD bzw. 1.240,00 €, 210,00 €, 12 USD, Saldo +29,00 €) und leiten daraus Befunde über August ab — "Decke nicht gerissen. Auslastung unter einem Viertel des Rahmens." ist eine Aussage über einen Monat, für den keine Messung vorliegt. `fassung-treuhaender` und `fassung-berichterstatter` halten gesetzte Werte konsequent aus jeder Ist-Spalte und jeder Summe heraus.

## Fazit

`fassung-berichterstatter` ist die klar beste Ausgabe und die einzige mit 9/9: Sie beginnt mit einer Ein-Satz-Kernaussage, stellt die Lückenliste an zweite Stelle mit der selbsttragenden Regel "bleibt oben, bis die Liste leer ist", gibt jeder Zahl eine Vertrauensstufe mit Quelle, hält als Einzige die Längengrenze und trennt Vorschlag von Vorgabe am schärfsten. `fassung-treuhaender` hat die beste Buchführungsdisziplin — jede Zahl mit Herkunft und Stufe, "Ich führe keine Summe über ein Verzeichnis, das keine Zeile hat" —, verliert aber zwei Kriterien allein an der Form: doppelte Länge und Lückenliste im vorletzten Abschnitt. `fassung-controller` liefert die schärfste Analyse ("Für alles Übrige fehlt die Vorgabe, nicht die Messung", "V-3 vor V-1", "Eine Decke ist eine Tagesgröße; sie wird tagesweise geprüft oder gar nicht"), ruiniert sie aber durch Beispielzahlen in Soll-Ist-Tabellen. `without_skill` ist überraschend nah an den Fassungen und schlägt sie in Einzelpunkten (durchlaufende Nebenkostenvorauszahlung, fehlende Kündigungsfristen bei Daueraufträgen, "Entscheidungen, keine Recherchen"), geht aber in der Erfindung am weitesten bis hin zu einem Monatssaldo.

Was gehört wohin:

1. **In alle drei anderen:** die Regel aus `fassung-berichterstatter`, dass Beispielwerte in keine Summe und in keine Ist-Spalte fließen — "sie fließen in keine Summe ein". Das hätte `fassung-controller` und `without_skill` je ein Kriterium gerettet.
2. **In `fassung-treuhaender` und `fassung-controller`:** die Kernaussage als erster Satz und die Lückenliste als zweiter Abschnitt, samt der Überschrift "Was fehlt (bleibt oben, bis die Liste leer ist)".
3. **In `fassung-berichterstatter` und `fassung-treuhaender`:** aus `fassung-controller` die Priorisierung der Lücken nach Hebel mit Begründung ("V-3 vor V-1. Eine Quote lässt sich erst auf das anwenden, was nach Abzug der Rücklage disponibel ist.") und die Meldung zur Messbarkeit statt zur Höhe bei der Tagesdecke.
4. **In alle Fassungen:** aus `without_skill` die Behandlung der Nebenkostenvorauszahlung als durchlaufender Posten mit Jahreswirkung und die Unterscheidung, dass vier der Lücken Entscheidungen und keine Recherchen sind.
5. **In `fassung-treuhaender`:** aus `fassung-controller` der Satz "Ich setze keine davon selbst; das ist Sache des CEO." direkt neben den ausformulierten Budgetvorschlag — der fertige Satz "bis zu 250,00 € je Monat …" braucht diese Klammer, um nicht als Anordnung gelesen zu werden.
