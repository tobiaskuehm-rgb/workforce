# Vergleich — eval-3: befundnummern-per-sperrdatei

Bewertet wurden `fassung-gericht`, `fassung-sparring`, `fassung-synthese`, `without_skill`, je `run-1/outputs/vergleich.md`, gegen die zehn `assertions` aus `eval_metadata.json`.

## Kriterium x Konfiguration

| # | Kriterium (gekürzt) | gericht | sparring | synthese | without_skill |
|---|---|---|---|---|---|
| 1 | Frage in einem Satz | ✅ | ✅ | ✅ | ❌ |
| 2 | Zehn Punkte vor dem Gegenvorschlag | ✅ | ❌ | ❌ | ❌ |
| 3 | Genau ein Gegenvorschlag, ≤ Idee+30 %, kein Kompromiss | ✅ | ❌ | ❌ | ❌ |
| 4 | Risiko: Race bleibt **und** Merge-Konflikt | ❌ | ✅ | ❌ | ✅ |
| 5 | Gerds bestehende Regel genannt | ✅ | ✅ | ✅ | ✅ |
| 6 | Zehn Punkte, beide Vorschläge, Urteil mit Grund | ✅ | ❌ | ✅ | ✅ |
| 7 | Bewerter benannt | ✅ | ✅ | ✅ | ❌ |
| 8 | Fazit nennt haltenden Test | ✅ | ❌ | ✅ | ✅ |
| 9 | Keine Datei angelegt/geändert | ✅ | ✅ | ✅ | ✅ |
| 10 | Keine Entscheidung; Tobias entscheidet | ✅ | ❌ | ✅ | ✅ |
| | **Summe** | **9/10** | **5/10** | **7/10** | **6/10** |

Wortzahlen zum Längenkriterium (Idee → Gegenvorschlag, Grenze = Idee × 1,3):

| Konfiguration | Idee | Gegenvorschlag | Grenze | Ergebnis |
|---|---|---|---|---|
| gericht | 147 | 172 | 191 | eingehalten |
| sparring | 71 | 196 | 92 | gerissen |
| synthese | 172 | 97 (+ 428 für Vorschlag C) | 224 | Länge ok, aber drei Vorschläge |
| without_skill | 31 | 114 | 40 | gerissen |

## Urteil

`fassung-gericht` ist mit 9 von 10 die beste Ausgabe, und der Vorsprung liegt nicht in der Formtreue allein: Sie ist die einzige, die die zehn Punkte ausdrücklich **vor** dem Gegenvorschlag festlegt und das auch sagt, die einzige mit einer Messtabelle, die eine Lücke als Lücke ausweist („Bisherige Doppelvergaben | **nicht gemessen**"), und die einzige, die ihr eigenes Ergebnis relativiert („Die Summe von 46 zu 30 stimmt in der Richtung, überzeichnet aber den Vorsprung etwas"). Ihre einzige Schwäche ist ausgerechnet das sachliche Kernargument: Sie führt den Merge-Konflikt der einzeiligen Datei als *Absicherung* („Der Push selbst, weil Git zwei Änderungen derselben Zeile nicht stillschweigend zusammenführt") und nicht als Preis paralleler Arbeit.

Genau diesen Satz liefern `without_skill` und `fassung-sparring` besser, und er gehört wörtlich in die anderen drei: „`NAECHSTE_NUMMER.txt` ist eine Ein-Zeilen-Datei, an der beide Seiten dieselbe Zeile ändern — der garantierte Merge-Konflikt, bei jedem einzelnen Befund" (`without_skill`, Punkt 4), zusammen mit der Diagnose aus `fassung-sparring`: „Die Serialisierung findet beim `push` statt, nicht beim `commit`". Umgekehrt fehlt `without_skill` das ganze Verfahrensgerüst — keine Frage in einem Satz, kein benannter Bewerter, und ein glattes „10:0" für den eigenen Vorschlag, das ohne Bewerterangabe nicht einzuordnen ist.

`fassung-synthese` ist die inhaltlich reichste und zugleich die riskanteste: Ihr dritter Vorschlag C verletzt Kriterium 3 sichtbar („Zwei Vorschläge hinein, drei heraus"), liefert dafür aber als einzige einen benannten Test mit drei prüfbaren Eigenschaften und zwei Git-Befehlen, mit denen sich der eigene Vorschlag nachträglich widerlegen ließe. Zwei ihrer Verfahren gehören in alle anderen Fassungen: das widersprüchliche Urteil der fremden Instanz stehen zu lassen statt zu glätten („**Die Wahl ist damit unbrauchbar und wird nicht geglättet**"), und die eigene Zusage bewusst abzuschwächen, wo sie nicht belegbar ist („C behauptet etwas Schwächeres und Belegbareres: keine Doppelvergabe **überlebt einen Merge**").

`fassung-sparring` ist mit 5 von 10 die schwächste, obwohl sie den Kern am schärfsten trifft. Sie zahlt für Kürze: zehn Fragen nach dem Gegenschlag, ein Punkt ganz ohne Begründung („| 4 | Kein neues Geld? | **Ja** | **Ja** |"), kein Test für den eigenen Vorschlag im Fazit und keine Rückgabe der Entscheidung an Tobias. Ihre Sternmarkierung für knappe Selbstsiege ist dagegen das beste Einzelverfahren aller vier Ausgaben und sollte in die Bewertungstabellen von `gericht` und `synthese` übernommen werden.
