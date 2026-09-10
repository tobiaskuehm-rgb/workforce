# 3-Loop: Soll `FILTER.md` ein Wettbewerbskriterium bekommen?

Erstellt von Thorsten (RAS-001) am 2026-09-10. Die drei Sichten sind **simuliert** und tragen
die Namen der Rollen, die sie vertreten; sie sind nicht deren Urteil.

---

## 1. Die Frage

Bekommt `FILTER.md` ein achtes Kriterium für Wettbewerb, und wenn ja mit welchem Gewicht —
entschieden vom CEO, vor dem nächsten Filterlauf.

**Randbedingung, nicht neu verhandelt:** Der CEO hat am 2026-09-10 festgestellt, dass acht
Wochenstunden Nebentätigkeit genehmigungsfähig sind. Die Rechtsnote steht damit bei allen
Kandidaten auf 5.

**Widerspruch zu einer früheren Regel, gleich im ersten Absatz:** Der Thorsten-Skill verlangt,
dass eine Filteränderung nur mit Bezug auf ein Probenergebnis vorgeschlagen wird. Ein solches
gibt es nicht. Der CEO hat diese Regel am 2026-09-10 ausdrücklich gelockert („du wolltest
deinen Filter anpassen damit du besser wirst") und zugleich vor dem Gegenteil gewarnt: zu
starkes Kleben am Filter.

---

## 2. Gemessen, nicht gemeint

Gerechnet mit `sens.py` und `sens2.py` über die sieben benoteten Kandidaten.

| Messung | Ergebnis |
|---|---|
| Gewichtssumme heute | 13, Höchstwert 65, Schwelle 50 = 77 % |
| Spanne der vier Besten | **5 Punkte** (56 bis 51), also 8 % der Skala |
| Einzelne Notenänderungen, die Platz 1 kippen | 12 von 112 = **11 %** |
| Notenänderungen um **eine** Stufe, die Platz 1 kippen | **keine** |
| Wettbewerb ×1 | Rangfolge unverändert, Abstände schrumpfen auf 1 Punkt |
| Wettbewerb ×2 | **G fällt von Platz 1 auf 2**, Kernel-System führt |
| Wettbewerb ×3 | G fällt auf Platz 4 |
| Schwelle bei ×2 | müsste von 50 auf **58** steigen, sonst lockert sie sich still |

**Zwei Befunde daraus.** Erstens ist der erste Platz von G robust: Kein einzelner Notenschritt
kippt ihn. Die Rangfolge ist also kein Rauschen. Zweitens kippt ein neues Kriterium ihn sehr
wohl, weil es einen systematischen Abstand von zwei Stufen einführt (G hat 1, die anderen 3).
Die Frage ist damit echt.

**Nicht gemessen:** ob meine Wettbewerbsnoten selbst stimmen. Sie stammen aus der Zahl der
gefundenen Anbieter, nicht aus deren Marktanteil.

---

## 3. Die drei Sichten und ihre Fragen

Festgelegt **vor** den Vorschlägen.

**Sicht CEO (Alltag).** 1. Bringt es mich schneller zu einem zahlenden Kunden? 2. Kostet es mich
zusätzliche Zeit? 3. Verstehe ich das Ergebnis ohne Thorsten? 4. Kann ich damit heute
entscheiden?

**Sicht Verfahren (simuliert Karl).** 1. Bleibt der Filter in einer Sitzung anwendbar?
2. Käme jemand anders zum selben Ergebnis? 3. Lässt sich das Kriterium missbrauchen, um einen
Lieblingskandidaten zu retten? 4. Bleibt die Schwelle ehrlich?

**Sicht Prüfer (simuliert Gerd).** 1. Ist die Änderung belegt oder Meinung? 2. Entwertet sie
frühere Urteile? 3. Ist sie rückbaubar? 4. Deckt sie die Lücke wirklich, oder verschiebt sie
sie?

---

## 4. Vorschlag A — achtes Kriterium „Wettbewerb", Gewicht ×2

Vom CEO angeregt. Neue Zeile in Stufe 2: *Wettbewerb ×2 — wie besetzt ist der Markt und wie
stark ist die Marke des Anbieters Teil des Produkts. 5 = leer oder zersplittert, 1 = von
Markenanbietern besetzt.* Höchstwert steigt auf 75, Schwelle auf 58.

| | |
|---|---|
| Ort | `FILTER.md`, Stufe 2, achte Zeile |
| Ablauf | jeder Kandidat bekommt eine achte Note; alle sieben bisherigen werden nachbenotet |
| Kosten | keine |
| Aufwand | einmalig sieben Nachbenotungen, danach eine Note je Kandidat mehr |
| Risiko | Höchstwert und Schwelle müssen mitwandern, sonst lockert sich der Filter still |

**Annahme, die A nicht ausspricht:** dass Wettbewerb unabhängig vom Ertrag ist. Ist er nicht —
ein besetzter Markt drückt den erzielbaren Preis, und der steckt schon in der Ertragsnote.

## 5. Vorschlag B — Wettbewerb als Ausschluss in Stufe 1

Das Gegenteil an der teuersten Stelle. Keine Note, sondern eine sechste Ausschlussfrage:
*Ist der Markt von Markenanbietern besetzt, deren Marke Teil des Produkts ist? Raus.*

| | |
|---|---|
| Ort | `FILTER.md`, Stufe 1, sechste Frage |
| Ablauf | beendet die Prüfung sofort, wie die anderen fünf |
| Kosten | keine |
| Aufwand | am geringsten von allen vier |
| Risiko | **G und E fallen sofort raus**, 1 ebenfalls; drei Kandidaten weg ohne Probe |

## 6. Vorschlag C — kein neues Kriterium, sondern eine Regel zur Ertragsnote

Dasselbe Ziel mit dem, was schon da ist. `FILTER.md` sagt bei Ertrag bereits „echte Preise aus
Angeboten, Portalen, Gesprächen; nie geschätzt ohne Quelle". Ergänzt wird ein Satz: *Der Ertrag
ist der **erzielbare**, nicht der Marktpreis. Wo Bestandsanbieter mit Marke den Preis setzen,
ist der erzielbare Preis deren Untergrenze, und die Note richtet sich danach.*

| | |
|---|---|
| Ort | `FILTER.md`, Stufe 2, Zeile Ertrag, Spalte Quelle |
| Ablauf | keine neue Note, aber eine strengere Begründungspflicht für die vorhandene |
| Kosten | keine |
| Aufwand | Nachbenotung nur dort, wo Bestandsanbieter belegt sind |
| Risiko | Wettbewerb bleibt unsichtbar, er steckt in einer Zahl, die auch anderes trägt |

Wirkung gemessen: G fiele bei Ertrag von 3 auf 2 (6,97 € je Mitarbeiter ist die Untergrenze),
Summe **53** statt 56 — Gleichstand mit dem Kernel-System, ohne neues Kriterium.

## 7. Vorschlag D — nichts ändern, Stufe 3 vorziehen

Die einfachste Form, die noch alles erfüllt. Der Filter hat seine Arbeit getan: aus zehn
Kandidaten sind vier über 50. `FILTER.md` sagt selbst, ein Kandidat ist C *„nicht, weil die
Tabelle es sagt, sondern weil jemand bezahlt hat"*. Also wird nicht weiter sortiert, sondern
geprobt. Wettbewerb misst die Probe von allein: Wer bei besetztem Markt kein Angebot
unterbekommt, fällt in Stufe 3 durch.

| | |
|---|---|
| Ort | nirgends, `FILTER.md` bleibt unverändert |
| Ablauf | alle vier über 50 gehen sofort in Stufe 3, keine Rangfolge unter ihnen |
| Kosten | die Proben selbst; drei davon kosten nur Zeit |
| Aufwand | null am Filter, dafür vier Proben beim CEO |
| Risiko | vier Proben parallel könnten mehr sein, als acht Wochenstunden tragen |

---

## 8. Die Matrix

Note 1 bis 5, je Note ein Grund.

### Sicht CEO (Alltag)

| Frage | A ×2 | B Ausschluss | C Ertragsregel | D proben |
|---|---|---|---|---|
| Schneller zum zahlenden Kunden? | 2 — sortiert um, bringt aber keinen Kunden näher | 3 — räumt drei Kandidaten weg, das spart Zeit | 2 — dasselbe, eine Note ändert nichts am Markt | **5** — die Probe ist der Kunde |
| Kostet zusätzliche Zeit? | 3 — sieben Nachbenotungen | **5** — kostet nichts | 4 — wenige Nachbenotungen | 2 — vier Proben sind echte Arbeit |
| Verstehe ich es ohne Thorsten? | 4 — eine Zeile mehr, lesbar | **5** — eine Frage, ja oder nein | 3 — versteckt Wettbewerb in einer fremden Zahl | **5** — Kunde zahlt oder nicht |
| Kann ich heute entscheiden? | 3 — erst nach Nachbenotung | 4 — sofort | 4 — sofort | **5** — sofort, und es passiert etwas |
| **Summe** | **12** | **17** | **13** | **17** |

### Sicht Verfahren (simuliert Karl)

| Frage | A ×2 | B Ausschluss | C Ertragsregel | D proben |
|---|---|---|---|---|
| In einer Sitzung anwendbar? | 4 — acht Noten statt sieben | **5** — eine Frage | 4 — unverändert lang | **5** — unverändert |
| Käme jemand anders zum selben Ergebnis? | 2 — „wie besetzt ist der Markt" ist Ermessen | 2 — „Marke Teil des Produkts" ebenso | 3 — an einen belegten Preis gebunden, das hilft | 4 — eine Probe hat ein Ergebnis, keine Note |
| Missbrauchbar, um einen Liebling zu retten? | 2 — achte Note ist der bequemste Hebel | 4 — Ausschluss lässt sich schlecht schönreden | **5** — Preisquelle ist nachprüfbar | **5** — nichts zu drehen |
| Bleibt die Schwelle ehrlich? | 2 — nur wenn 50 auf 58 mitwandert, leicht zu vergessen | **5** — Schwelle unberührt | **5** — unberührt | **5** — unberührt |
| **Summe** | **10** | **16** | **17** | **19** |

### Sicht Prüfer (simuliert Gerd)

| Frage | A ×2 | B Ausschluss | C Ertragsregel | D proben |
|---|---|---|---|---|
| Belegt oder Meinung? | 2 — kein Probenergebnis, genau was die Regel verbietet | 1 — dieselbe Schwäche, härtere Wirkung | 4 — stützt sich auf belegte Preise | **5** — die Probe ist der Beleg |
| Entwertet frühere Urteile? | 3 — alle sieben müssen nachbenotet werden | 1 — **löscht drei Kandidaten ohne Probe** | 4 — ändert nur belegbare Fälle | **5** — ändert keins |
| Rückbaubar? | 4 — Zeile entfernen, Schwelle zurück | 2 — weggeworfene Kandidaten kommen nicht wieder | **5** — Satz entfernen | **5** — nichts getan |
| Deckt die Lücke wirklich? | 3 — misst Wettbewerb, aber doppelt zum Ertrag | 3 — nur den Extremfall | 4 — genau dort, wo er wirkt: am Preis | 4 — misst ihn erst nachträglich |
| **Summe** | **12** | **7** | **17** | **19** |

### Gesamt

| | A ×2 | B Ausschluss | C Ertragsregel | D proben |
|---|---|---|---|---|
| CEO | 12 | 17 | 13 | 17 |
| Verfahren | 10 | 16 | 17 | 19 |
| Prüfer | 12 | 7 | 17 | 19 |
| **Summe** | **34** | **40** | **47** | **55** |

---

## 9. Fazit

**Empfehlung: D, mit der Auflage aus C.**

`FILTER.md` bekommt kein achtes Kriterium. Die vier Kandidaten über 50 gehen in Stufe 3, ohne
weitere Rangfolge unter ihnen. Das ist zugleich die Antwort auf die Warnung des CEO: Die
Gefahr war nicht, dass der Filter ein Kriterium zu wenig hat, sondern dass ich ihn weiter
verfeinere, statt ihn zu verlassen. Der Filter selbst sagt, dass jemand bezahlen muss.

**Die Auflage aus C wird trotzdem übernommen**, weil sie in zwei von drei Sichten die beste
Einzelbewertung hat und nichts kostet: Der Ertrag ist der erzielbare Preis, nicht der
Marktpreis. Das ist ein Satz in einer Spalte, die es schon gibt, er ist an eine belegbare
Quelle gebunden und jederzeit rückbaubar. Er senkt G auf 53 und stellt damit von selbst her,
was A mit einem ganzen Kriterium erreichen wollte.

**Was aus den unterlegenen Vorschlägen mitkommt.** Von B die Erkenntnis, dass „Marke ist Teil
des Produkts" eine echte Kategorie ist — sie wird als Warnsatz bei der Ertragsnote vermerkt,
nicht als Ausschluss. Von A die Mahnung, dass eine neue Zeile immer auch die Schwelle
verschiebt.

**Die Reihenfolge der Proben löst das Mengenproblem aus D.** Vier Proben parallel sprengen acht
Wochenstunden. Drei der vier kosten nur Gespräche, eine kostet Bauzeit. Reihenfolge: erst der
Nebentätigkeitsantrag, dann die drei Gesprächsproben nebeneinander, die Bauprobe zuletzt.

### Fragen an den CEO

1. **Wird D so gefahren?** Empfehlung ja. Alternativen: nur C übernehmen und weiter sortieren;
   oder A trotz allem, wenn dir die Rangfolge wichtiger ist als die Proben.
2. **Welche der vier Proben zuerst?** Empfehlung: der Nebentätigkeitsantrag, weil er alle vier
   freischaltet. Alternativen: Kandidat 5 zuerst, weil er am schnellsten Geld bringt; oder
   Kandidat 6, weil das System ohnehin gebaut wird.
3. **Darf Thorsten weiterhin aus deinen Vorschlägen ableiten?** Du hast es erlaubt. Ich möchte
   es in einer Form festhalten, die nicht zur Schönfärberei einlädt: Eine Abwandlung wird als
   eigener Kandidat mit eigener Nummer geführt und nennt den Ursprung. G stammt so aus meinem
   eigenen B, I aus meinem A — beide sind gekennzeichnet.

### Die eine Sache, die am ehesten noch falsch ist

Meine Wettbewerbsnoten. Ich habe sie aus der **Zahl der gefundenen Anbieter** gebildet, nicht
aus deren Marktanteil. Ein Markt mit sechs sichtbaren Anbietern kann zersplittert und leicht
angreifbar sein; ein Markt mit zwei kann geschlossen sein. Wäre G in Wahrheit eine 3 statt
einer 1, hielte es Platz 1 auch unter Vorschlag A — und dann hätte ich den ganzen Loop über
eine Lücke geführt, die keine ist.
