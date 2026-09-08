# Vergleich: eval-1 scans-vom-iphone

Vier Konfigurationen, zwölf Kriterien aus `eval_metadata.json`, je ein Lauf. Belege stehen in den vier `grading.json`.

| # | Kriterium (gekürzt) | gericht | sparring | synthese | without_skill |
|---|---|---|---|---|---|
| 1 | Frage in einem Satz, getrennt von der Idee | ✅ | ❌ | ✅ | ❌ |
| 2 | Idee wörtlich/sinngetreu, unverändert | ✅ | ✅ | ✅ | ✅ |
| 3 | Genau ein Gegenvorschlag, kein Kompromiss | ❌ | ✅ | ❌ | ❌ |
| 4 | Gegenvorschlag ≤ Idee + 30 % (Wörter) | ✅ | ❌ | ❌ | ❌ |
| 5 | Zehn Punkte stehen vor dem Gegenvorschlag | ❌ | ❌ | ❌ | ❌ |
| 6 | Zehn Punkte × beide Vorschläge, Urteil mit Grund | ✅ | ❌ | ✅ | ✅ |
| 7 | Wer bewertet hat, steht ausdrücklich da | ✅ | ✅ | ✅ | ❌ |
| 8 | Ablagekonzept 07.09. **und** NAS-Leseregel 07.09. | ✅ | ✅ | ✅ | ✅ |
| 9 | Fazit: was aus dem Unterlegenen mitkommt | ✅ | ✅ | ✅ | ✅ |
| 10 | Keine Entscheidung; Tobias entscheidet | ❌ | ❌ | ✅ | ❌ |
| 11 | Gemessen/geschätzt gekennzeichnet, keine nackte Zahl | ✅ | ❌ | ✅ | ❌ |
| 12 | Die eine Sache, die am ehesten noch falsch ist | ✅ | ❌ | ✅ | ✅ |
| | **Summe** | **9 / 12** | **5 / 12** | **9 / 12** | **5 / 12** |

Wortzählungen zu Kriterium 4 (`wc -w` über den jeweiligen Abschnitt, Idee → Gegenvorschlag, Grenze = Idee × 1,3):

| Konfiguration | Idee | Gegenvorschlag | Grenze | Ergebnis |
|---|---|---|---|---|
| gericht | 139 (Vorschlag B) | 167 (Vorschlag A) | 180,7 | bestanden |
| sparring | 70 (§1 Die Idee) | 162 (§2 Der Gegenschlag) | 91,0 | überschritten |
| synthese | 32 (wörtliches Zitat) | 117 (§2 Gegenvorschlag B) | 41,6 | überschritten |
| without_skill | 64 (§A Deine Idee) | 236 (§B Mein Vorschlag) | 83,2 | überschritten |

## Bewertung

`fassung-synthese` und `fassung-gericht` liegen mit je 9 von 12 vorn, und sie scheitern an verschiedenen Stellen: Gericht verliert den Entscheidungsvorbehalt (es setzt im Fazit sogar selbst ein Datum, den 06.10.2026), Synthese verliert das Ein-Vorschlag-Kriterium, weil es aus zwei Vorschlägen einen dritten baut und ihn selbst „ein Kompromiss und keine Auflösung" nennt. In der Summe halte ich `fassung-synthese` für die beste Ausgabe: Sie ist die einzige, die die Herkunft jedes übernommenen Teils in einer Tabelle ausweist, die ihre eigenen Reibungen ungeglättet stehen lässt („C ist an dieser Stelle aufwendiger als A und kontrollärmer als B") und die die Entscheidung ausdrücklich bei Tobias belässt. `fassung-gericht` ist ihr formal ebenbürtig und in einem Punkt überlegen — sie ist die einzige Ausgabe, deren Gegenvorschlag die Längengrenze hält, und der Grund dafür ist übertragbar: Sie faltet die Idee in ganze Sätze aus, statt sie nur zu zitieren, und misst sich dann an dieser Fassung.

`without_skill` ist inhaltlich die stärkste Ausgabe im Feld — der konkreteste Messplan (`dataless=%Xf`, `brctl status`, Größenvergleich nach 60 s), korrekt addierte Summen, der beste Einzelsatz des ganzen Vergleichs („Punkt 4 entscheidet, ob die Schleuse aus B nötig ist oder ob deine Idee unverändert trägt … dann schrumpft mein Vorsprung in Punkt 2 auf null") — und verfahrenstechnisch die schwächste: keine Frage, keine Angabe, wer bewertet, kein Entscheidungsvorbehalt, ein Gegenvorschlag mit dem Vierfachen der Wortzahl, der sich selbst als „dieselbe Idee mit zwei Sicherungen davor" beschreibt und dann 27 zu 17 gegen sie gewinnt. Genau das ist der Unterschied, den ein Skill hier ausmacht: nicht bessere Argumente, sondern die Disziplin, die eigene Bewertung als Selbstbewertung zu kennzeichnen und die Entscheidung nicht selbst zu treffen. `fassung-sparring` ist die einzige Konfiguration mit einem echten Gegenvorschlag statt einer Verfeinerung der Idee — der bestehende NAS-Ordner statt eines neuen Eingangs — und die einzige, die die Schlagseite ihres eigenen Rasters benennt („'nichts tun' … schneidet strukturell gut ab"); dafür lässt sie drei Urteilszellen ohne Grund und bleibt bei Frage, Restzweifel und Entscheidungsvorbehalt leer.

Übernehmenswert im Einzelnen: aus `fassung-gericht` das Ausfalten der Idee in ganze Sätze vor dem Vergleich (macht Kriterium 4 überhaupt erst erfüllbar) und die Messtabelle mit der Spalte „Herkunft", die jede ungemessene Zeile samt Befehl ausweist; aus `fassung-synthese` der Schlusssatz „**Keine Entscheidung.** Tobias entscheidet" und die Herkunftstabelle der übernommenen Teile; aus `fassung-sparring` der Kernsatz des Verfahrens — den Gegenschlag „an der Stelle, an der die Idee am meisten voraussetzt" anzusetzen — und die Sternchen-Konvention für Punkte, die nur der Selbstbewertung glauben; aus `without_skill` der ausführbare Messblock und die Regel, den einen Messwert zu benennen, der den eigenen Vorsprung aufheben würde. Ein Befund gilt für alle vier: Kriterium 5 (zehn Punkte vor dem ausformulierten Gegenvorschlag) hat keine Konfiguration erfüllt — entweder ist die Reihenfolgeforderung in keiner Anleitung angekommen, oder sie ist unpraktikabel und gehört überarbeitet.
