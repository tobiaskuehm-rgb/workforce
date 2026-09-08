# Organigramm der Workforce

Stand 2026-09-08, beschlossen vom CEO im Chat („kannste alles so umsetzen", `PENDING-DEC`), aus dem
3-Loop `workforce/reviews/2026-09-08_3loop_projekt_karl.md`. Das Register (`README.md`, Anastasia)
sagt, wer es gibt und wo er steht; diese Datei sagt, wer wem berichtet und in welchem Takt.
`test_organigramm.py` hält beide zusammen: Jede Identität des Registers steht hier genau einmal
mit genau einem Vorgesetzten, und jeder Vorgesetzte ist selbst eine Identität oder der CEO.

## Berichtswege

| Identität | Ordner | Vorgesetzter | Output je Woche | Gate | Stand |
|---|---|---|---|---|---|
| Karl `SAO-001`, COO auf Probe | `karl/` | CEO | Montagsübersicht, Donnerstagsvorlagen, Reihenfolge | keine Vorlage älter als sieben Tage | aktiv |
| Gerd `AI-ENG-001`, Stab | `gerd/` | CEO | Befunde, Freigabe je Deploy | jeder Deploy hat ein Review nach dem Lauf | aktiv |
| Marlene `POA-001` | `marlene/` | Karl | Fristen und Vorgänge Linie A | Vorgang endet mit „abgelegt" | aktiv, Probezeit |
| Wolle, CFO | `cfo/` | Karl | Monatsübersicht je Linie | jede Zahl mit Quelle | ruht bis Oktober 2026 |
| Thorsten `RAS-001` | `thorsten/` | Karl | ein Filterlauf je Kandidat | Stufe-2-Urteil mit Quellen | aktiv |
| Anastasia `PEO-001` | `anastasia/` | Karl | Register aktuell, Probezeit-Evidenz | jede Identität an drei Stellen | aktiv, bis auf Weiteres nur Register und Probezeit |
| Marv Skillbauer | `marv/` | Anastasia | ein gemessener Skill je Auftrag | Prüffälle vor dem Bau | aktiv |

Gerd hängt nicht unter dem COO, sondern als Stab direkt beim CEO: Wer prüft, wird nicht von dem
gesteuert, den er prüft.

## Takt

Zwei Termine je Woche, nach Wirtschaftlichkeit gewählt: kurz, fest, ohne Freigaben dazwischen.

| Wann | Was | Wer |
|---|---|---|
| **Montag** | Wochenübersicht: Was ist seit Donnerstag passiert, was liegt an, Kontrolle der Gates. Keine Entscheidungen, nur Lage. | Karl legt vor, CEO liest |
| **Donnerstag** | Entscheidungstermin: alle Vorlagen der Klassen Strategie, Budget, Personal, Rechte, gesammelt, je mit dem Satz fürs Log. Der CEO entscheidet und trägt die Nummern am selben Tag ins Decision Log. | Karl legt vor, CEO entscheidet |
| **Freitag bis Sonntag** | Wochenendbetrieb: Der Bot antwortet, nichts wird ausgerollt, kein Review, keine Vorlage. Was anfällt, wartet auf Montag. | System |
| **sofort, jeden Tag** | Nur Produktives und Externes gehen sofort an den CEO. | Karl |

Unter der Woche entscheidet der COO allein innerhalb des bestätigten Budgets (2,0 USD und 100
Aufrufe je Tag) und der Invarianten.

## Eingefroren, bis es Arbeit gibt

Wolle bis Oktober 2026. Phase 4 (Dokumente) und Phase 5 (Werkzeuge) hinter Phase 3. Kein
Modellreview, bevor drei Skills Prüffälle haben. Aufgetaut wird, wenn Linie A vollständig im
System läuft oder ein C-Kandidat Stufe 2 bestanden hat; der Anlass steht dann hier mit Datum.
