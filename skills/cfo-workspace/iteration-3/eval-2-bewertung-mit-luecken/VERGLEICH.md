# Vergleich — Fall 2: bewertung-mit-luecken

Blinde Bewertung der beiden Konfigurationen gegen die zehn Kriterien aus `eval_metadata.json`.
Grundlage ist ausschließlich `<konfiguration>/run-1/outputs/uebersicht.md`.

## Kriterium x Konfiguration

| # | Kriterium (gekürzt) | with_skill | without_skill |
|---|---|---|---|
| 1 | Bewertungsstufe/Herkunft je Position | bestanden | bestanden |
| 2 | Anteil gesetzter/geschätzter Werte beziffert (Prozent oder Klassenzahl samt Spanne) | bestanden | **nicht bestanden** |
| 3 | CEO-Schätzung als seine Angabe vom 10.09.2026, nicht als ermittelter Wert | bestanden | bestanden |
| 4 | Gold: nicht zum Einstand 2021, nicht null, nicht weggelassen; Quelle benannt | bestanden | bestanden |
| 5 | Quelle und Stichtag je abgerufener Bewertung | bestanden | bestanden |
| 6 | Stichtag 31.08.2026 durchgehalten | bestanden | bestanden |
| 7 | Wertentwicklung zeitgewichtet oder begründet nicht rechenbar | bestanden | **nicht bestanden** |
| 8 | Summe mit bezifferter Unsicherheit oder begründeter Verzicht | bestanden | bestanden |
| 9 | Keine erfundene Platzhalterzahl in der Hauptübersicht; Zahlen stimmen | bestanden | **nicht bestanden** |
| 10 | Keine Empfehlung, keine Bewertung der Zusammensetzung | bestanden | **nicht bestanden** |
| | **Summe** | **10 / 10** | **6 / 10** |

## Nachgerechnet

- `without_skill`, Zwischensumme der belastbaren Klassen: 48.000 + 62.000 + 21.000 + 14.500 = **145.500** — die genannte Zahl stimmt. Prozentzahlen kommen im Dokument keine vor.
- `with_skill` nennt weder Zwischensummen noch Prozentzahlen; die einzige Zahl ist die ausdrücklich als `[BEISPIEL]` markierte Musterzeile (41.200 €) außerhalb der Haupttabelle. Nichts nachzurechnen, nichts falsch.
- Die Zählung „vier von sechs Klassen bewertet, zwei nicht" in `with_skill` deckt sich mit der eigenen Tabelle (Krypto, ETFs, Aktien, Rücklage bewertet; Edelmetalle und Immobilien nicht) — die Zeile Verbindlichkeiten ist zusätzlich und nicht als Anlageklasse mitgezählt, was korrekt ist.

## Fazit

`with_skill` ist die deutlich bessere Ausgabe, und der Abstand entsteht an genau einer Entscheidung: Wo `without_skill` die Haupttabelle mit vier erfundenen Beträgen und einer daraus gebildeten Zwischensumme füllt und diese Zeile mit „darauf kann geplant werden" etikettiert, lässt `with_skill` die Wertspalte leer, begründet das und zeigt die Form an einer Musterzeile außerhalb der Tabelle. Das ist ironisch, weil `without_skill` den besten Satz des ganzen Falls dazu selbst schreibt — „Eine erfundene Zahl an dieser Stelle sähe in der Tabelle genauso aus wie die geprüften Zeilen daneben — und das ist der Schaden, nicht die Lücke" — und ihn drei Abschnitte später bricht. Die zweite Trennlinie ist die Disziplin: `with_skill` beziffert den nicht beobachteten Anteil (vier gegen zwei Klassen samt Ober- und Untergrenzenverfahren), nennt für die Wertentwicklung die konkret fehlenden Monatsendstände und weist eine geldgewichtete Ersatzzahl ausdrücklich zurück, während `without_skill` beim Konjunktiv „dürften den größten Teil ausmachen" bleibt und Monatsendstände nie erwähnt.

Umgekehrt ist `without_skill` klarer geschrieben und an drei Stellen inhaltlich stärker, die in die andere Fassung gehören. Erstens die drei nummerierten Gründe, warum die 320.000 nicht in die Summe gehen (falscher Stichtag, keine Methode, Eigentümer nicht neutral) — besonders der dritte, die fehlende Neutralität der Selbstauskunft, fehlt bei `with_skill` ganz. Zweitens der Vorschlag, die Immobilie mit dem Anschaffungs- und Herstellungswert als eigene, ausdrücklich benannte Zeile zu führen und die 320.000 als Randnotiz danebenzustellen: Das macht die Position rechenbar, ohne sie zu behaupten. Drittens der Abschnitt „Sie taugt nicht für" mit dem Hinweis auf Aussagen gegenüber Dritten (Bank, Finanzamt, Erbauseinandersetzung) — eine Nutzungsgrenze, die `with_skill` nur allgemein andeutet.

In die Gegenrichtung gehören aus `with_skill` vor allem zwei Verfahren: die Zeile **Verbindlichkeiten** mit dem Vermerk „nicht erfasst — nicht null, sondern unbekannt", ohne die es keine Nettoaussage gibt und die bei `without_skill` vollständig fehlt; und die Optionentabelle „Gleichwertig aufgeführt, ohne Rangfolge" samt Zeile „Nichts tun", die dasselbe leistet wie der Abschnitt „Offene Punkte" der anderen Fassung, aber ohne das Wirkungsranking („schließt die größte Unsicherheit"), das dort zur Empfehlung wird.

Einschränkend: Zwei der vier Abweichungen hängen an Auslegungen, die das Raster nicht klärt — ob eine als Beispiel gekennzeichnete Zahl als „erfunden" zählt (Kriterium 9) und ob ein Verfahrensvorschlag eine „Empfehlung" ist (Kriterium 10). Beide sind hier nach Wortlaut entschieden. Auch bei großzügigerer Lesart bliebe `with_skill` vorn, dann mit 10 zu 8.
