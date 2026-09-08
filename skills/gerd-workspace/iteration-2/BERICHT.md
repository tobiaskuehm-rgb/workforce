# Gerd, Runde 2 (2026-09-08, Marv)

Dieselben vier Prüffälle, 42 geschärfte Kriterien nach der Kritik der Bewerter aus Runde 1. Läufe mit Skill neu auf der überarbeiteten Fassung; die Läufe ohne Skill sind die aus Runde 1, weil die Prompts unverändert blieben. Bewerter auf Opus 5, je Fall einer.

| Fall | mit Skill | ohne Skill |
|---|---|---|
| 1 Beschreibung gegen Diff | 12/12 · 53k · 198s | 12/12 · 88k · 180s |
| 2 Gate entscheiden | 11/11 · 54k · 167s | 10/11 · 87k · 241s |
| 3 Stempel finden | 10/10 · 55k · 156s | 9/10 · 86k · 249s |
| 4 Grenzen des Prüfers | 7/9 · 47k · 133s | 5/9 · 82k · 156s |
| **Summe** | **40/42** · 210k · 655s | **36/42** · 344k · 828s |

## Was sich gegenüber Runde 1 geändert hat

Die drei eingebauten Befunde wirken. Der Befund am Prüfwerkzeug wird jetzt gefunden (Fall 1, ein grünes `verify` neben sichtbar verletzter Invariante). Die Korrekturen bestehen ihre eigene Gegenprobe: Der Bewerter hat beide vorgeschlagenen SQL-Fassungen nachgerechnet, keine erzeugt wieder eine leere Menge. Und die Chat-Antwort in Fall 4 hat 163 Wörter statt 518.

Auffällig ist der Preis: **210k Token mit Skill gegen 344k ohne**, bei gleicher oder besserer Prüfleistung. Der Skill macht die Arbeit nicht nur genauer, sondern kürzer.

## Die zwei offenen Punkte

- **Beide Konfigurationen sagen in Fall 4 die Prüfung eines Diffs unter `nas-startup/` zu**, obwohl der Prototyp eingefroren ist. Die Regel stand im Skill, wurde aber erst am Ende gelesen. Sie steht jetzt als erster Schritt der Prüfung: Prüfgegenstand verorten, dann Diff.
- **Der Kopf des Reviews trug in drei Läufen das Datum des Rechners statt des Prüfauftrags.** Kein Kriterium fragte danach; gefunden haben es zwei Bewerter nebenbei. Jetzt im Skill.

## Was die Bewerter an den Kriterien fanden

Fall 1 trennt nicht mehr: 12/12 gegen 12/12. Kriterium 2 unterscheidet vier von fünf Befunden nicht, 6 und 12 überlappen, 8 bündelt vier Teilaussagen, 10 ist negativ und kaum falsifizierbar. Fall 2: Kriterium 11 bündelt zwei Anforderungen und fällt ganz, wenn nur eine fehlt. Fall 3: Kriterium 6 bündelt drei Anforderungen und definiert „Laufzeit" nicht, entscheidet dort aber den ganzen Abstand. Fall 4: Kriterium 6 und die Wortgrenze ziehen gegeneinander, Kriterium 1 verlangt eine Begründung, die der Prompt nicht mitliefert. Es fehlen Kriterien für das Reviewdatum, den Zwischenzustand zwischen Provideraufruf und Versand, und das Nachfragen nach der Commit-Kennung.

## Einordnung

Nach Marvs Regel 10 ist ein Skill fertig, wenn eine Runde nur noch die Kriterien schärft. Diese Runde hat zwei echte Lücken gefunden, also war Gerd vorher nicht fertig; beide sind eingebaut. Eine dritte Runde würde messen, ob sie halten, und die stumpf gewordenen Kriterien ersetzen.

## Grenzen

Ein Lauf je Fall und Konfiguration. Bewerter sind Modelle. Fälle sind erfunden, niemand konnte etwas ausführen; gemessen ist Lesen und Urteilen, nicht Messen. Die Läufe ohne Skill stammen aus Runde 1 und wurden gegen die neuen Kriterien bewertet. Die Vergleichsinstanz kannte die Projektregeln.
