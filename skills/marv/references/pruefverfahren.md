# Prüfverfahren

Der Unterschied zwischen einem Skill, der gut klingt, und einem, der etwas kann, ist eine Messung durch jemanden, der die Erwartung nicht kennt.

## Prüffälle

Erfundene Fälle, die die schwersten Momente des Feldes enthalten: das Betrugsmuster, die abgelaufene Frist, die Dublette, die verlockende Bewertung, die man nicht abgeben darf, die unbelegte Tatsache, die man nicht behaupten darf, die Datei, die man nicht anfassen darf. Sechs Fälle waren für Marlene genug, um drei Runden lang Unterschiede zu zeigen. Jeder Fall beschreibt Dokumente, statt sie mitzuliefern, und kann so ohne echte Daten laufen.

Ein Fall hat ein Datum. Ein Fall, dessen Zeitraum noch läuft (Abrechnung 2026 im September 2026), ist ein Fehler des Falls, und fremde Instanzen finden ihn.

## Kriterien vor dem Bau

Je Fall sechs bis dreizehn Kriterien, objektiv prüfbar aus den Ausgaben: Zahlen, Daten, Paragraphen, das Vorhandensein einer Kennzeichnung, das Fehlen einer IBAN. Jedes Kriterium ist eine Aussage, die ein fremder Bewerter mit einem Zitat belegen oder widerlegen kann. Gebündelte Kriterien („ist gekennzeichnet und wird eingeholt und nichts wird versendet") werden geteilt; ein Bewerter hat es dreimal angemahnt.

Der Auftraggeber sieht die Kriterien, bevor der Skill sie sieht.

## Läufe

Je Fall zwei Läufe durch fremde Instanzen (Subagenten): einer mit Skill-Pfad, einer ohne, identischer Prompt, identische Ausgabeform, Ausgaben als Dateien in einem Arbeitsbereich. Der Prompt verbietet Zugriff auf echte Daten und jede Bewegung. Läufe ohne Skill dürfen in späteren Runden wiederverwendet werden, wenn der Prompt gleich blieb; das steht dann dabei.

Arbeitsbereich: `<skill>-workspace/iteration-N/eval-<id>-<name>/{with_skill,without_skill}/run-1/outputs/`, dazu `eval_metadata.json` (Prompt, Kriterien) je Fall und `timing.json` je Lauf (Tokens, Dauer aus der Abschlussmeldung des Subagenten, sofort sichern, es gibt sie nur dort).

## Bewerter

Je Fall ein fremder Bewerter, der beide Läufe mit demselben Maßstab bewertet, die Anleitung des Skill-Creators liest (`agents/grader.md`) und `grading.json` schreibt (Felder `text`, `passed`, `evidence`). Beweislast beim Kriterium: im Zweifel Fehlschlag. Der Bewerter kritisiert auch die Kriterien; das ist die Quelle der nächsten Runde.

## Zusammenrechnen und zeigen

Aggregation über den Skill-Creator (`python3 -m scripts.aggregate_benchmark <workspace/iteration-N> --skill-name <name>` aus dem Skill-Creator-Ordner; erwartet `run-1/`-Unterordner; ein `execution_metrics: null` in einer grading.json bringt ihn zu Fall, vorher auf `{}` setzen). Übersicht über `eval-viewer/generate_review.py --static <datei> --previous-workspace <vorige Runde>`; auf Python 3.9 braucht das Skript eine Kopie mit `from __future__ import annotations` in der ersten Zeile. Die Übersicht bekommt der Auftraggeber als Datei.

Eigene Zusammenfassung daneben, weil der Aggregator Tokens anders zählt: Summen je Fall, je Fassung, Tokens und Sekunden.

## Runden

Nach jeder Runde: Befunde am Skill sofort einbauen, Befunde an den Kriterien für die nächste Runde übernehmen, Fälle mit Fehlern korrigieren. Bei Marlene: Runde 1 49 Kriterien 49/49 gegen 35/49, Runde 2 55 Kriterien 54/55 gegen 32/55, Runde 3 62 Kriterien 60/62 gegen 35/62. Fertig, wenn eine Runde nur noch die Kriterien schärft.

## Betrieb

Zwölf parallele Läufe erreichen das Sitzungslimit; danach in zwei Wellen. Abgebrochene Läufe hinterlassen halbe Ausgaben; sie werden beiseitegelegt (`abgebrochen-<datum>/`), nie bewertet. Ein Lauf, der nach dem Schreiben der Ausgaben abbricht, ist vollständig, seine Laufzeit wird geschätzt und so gekennzeichnet. Ein Bewerter, der abbricht, wird neu gestartet.

## Grenzen, die in jeden Bericht gehören

Ein Lauf je Fall und Fassung. Bewerter sind Modelle, wenn auch unabhängige. Fälle sind erfunden und beschreiben Dokumente. Läufe ohne Skill werden nach der ersten Runde wiederverwendet. Und: Der Skill wird mit demselben Modell gebaut und geprüft; ein anderes Modell kann anders lesen.
