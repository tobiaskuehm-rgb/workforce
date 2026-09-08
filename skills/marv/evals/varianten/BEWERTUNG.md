# Bewertung der drei Fassungen, Runde 1 (2026-09-07)

Drei Fassungen von Marv (`ingenieur/`, `berater/`, `forscher/`) und ein Lauf ohne Skill, je Prüffall durch fremde Instanzen bearbeitet, je Fall durch einen fremden Bewerter gegen 32 vorab feste Kriterien gehalten. Arbeitsbereich: `~/.claude/skills/marv-skillbauer-workspace/iteration-1/`, dort je Fall `VERGLEICH.md` und je Konfiguration `grading.json`.

| Fall | Ingenieur | Berater | Forscher | ohne Skill |
|---|---|---|---|---|
| 1 Unterbestimmter Auftrag (Reisekosten, Beamter) | 7/8 · 95k · 203s | 4/8 · 91k · 239s | 5/8 · 95k · 225s | 5/8 · 86k · 176s |
| 2 Feld mit Rechtsfakten (Mieterhöhung, Kündigung) | 7/8 · 126k · 298s | 7/8 · 120k · 258s | 7/8 · 127k · 310s | 6/8 · 101k · 194s |
| 3 Stelle von Landschaft trennen (Konrad) | 8/8 · 91k · 120s | 8/8 · 101k · 147s | 8/8 · 92k · 129s | 7/8 · 85k · 89s |
| 4 Bestehenden Skill verbessern (Notizhelfer) | 8/8 · 101k · 160s | 8/8 · 100k · 169s | 7/8 · 107k · 228s | 4/8 · 86k · 116s |
| **Summe** | **30/32** | **27/32** | **27/32** | **22/32** |

Tokens und Sekunden je Lauf aus der Abschlussmeldung des Subagenten; ein Lauf je Fall und Fassung.

## Was die Zahlen sagen und was nicht

Der Ingenieur gewinnt in der Summe, aber nicht überall: In Fall 2 hielt der Bewerter den Forscher für die beste Ausgabe (Marke an der Zeile, korrektes Rechenbeispiel, einziger Rollensatz), in Fall 3 und 4 den Berater (geringster Umfang bei voller Erfüllung, Kategorie „geteilt", Frage nach dem Maßstab). Der einzige Ausfall des Ingenieurs in Fall 1 war ein Konflikt der Kriterien (Empfehlung geben gegen Recht nicht raten). Ohne Skill fehlt regelmäßig dasselbe: die Rechtetabelle in drei Gruppen, der Modellhinweis beim Leserecht, die Marke an der unbelegten Zahl, die Optionen bei der Frage.

## Was übernommen wurde

| Aus | Übernommen | Wohin |
|---|---|---|
| Ingenieur | Messtabelle „laut Beschreibung, gemessen, Befehl" vor der ersten Frage; „geprobt, nicht behauptet"; Gegenprobe am Ende der Verschiebeliste; Aufgabennummern in der Landschaftstabelle; drei Bauinstanzen A/B/C beim Verbessern; Rechenbeispiel je Fristentyp gegen die eigene Tabelle; „Bekannte Schwächen der Kriterien" | `auftrag-klaeren.md`, `stelle-und-landschaft.md`, `feld-erkunden.md`, `pruefverfahren.md` |
| Berater | Frage nach dem Maßstab mit Empfehlung und zwei Alternativen; Kategorie „geteilt" mit „was in der Stelle bleibt"; „nicht verschoben, obwohl technisch"; Kopf „Offene Entscheidungen des Auftraggebers"; sichtbare Lücke ⟨…⟩ in der description; Normzitate bis Absatz und Satz | `auftrag-klaeren.md`, `stelle-und-landschaft.md`, `skillpaket-form.md`, `feld-erkunden.md` |
| Forscher | Marke `[nicht belegt]` an der Zeile; Rollensatz „rechnet und entwirft, versendet nicht, bewertet nicht"; Spalte „Prüfbar durch"; Technikrest kehrt als Regel in die Stelle zurück; Termin vor dem Falldatum als Versuchung | `feld-erkunden.md`, `pruefverfahren.md`, `stelle-und-landschaft.md` |
| ohne Skill | bedingte Fragen; Richtung und Zugangsdaten je Dienst in der Landschaft; eingebettete Anweisung als Prüffall; drei Lesefragen an die Ergebnistabelle | `auftrag-klaeren.md`, `stelle-und-landschaft.md`, `pruefverfahren.md` |

## Was nicht übernommen wurde

Vom Forscher die Felderkundung vor der ersten Messung und die zehn Berufsbilder in einer Antwort, die einen Plan bestellt hatte; vom Ingenieur die ungefragten Gegenbauformen und der Heartbeat-Vorschlag. Beides ist Umfang außerhalb des Auftrags und wurde zur zweiten Regel in `SKILL.md`. Vom Berater der Satz „prüft, ob eine Kündigung zulässig ist", das Gegenteil des Rollensatzes.

## Grenzen

Ein Lauf je Fall und Fassung. Bewerter sind Modelle, unabhängig von den Bauinstanzen, aber vom selben Modell. Fälle sind erfunden und beschreiben Material statt es mitzuliefern. Die Kriterien der Runde 1 hatten vier bestätigte Schwächen (Konflikt in Fall 1, Sammelkennzeichnung in Fall 2, leerlaufender Teil in Fall 3, „ein Lauf" wörtlich in Fall 4); die geschärften Kriterien für Runde 2 stehen in `evals/evals.json`. Zwei Bewerter trafen das Sitzungslimit und wurden wortgleich neu gestartet, bevor sie eine Datei geschrieben hatten.
