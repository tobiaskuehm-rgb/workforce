# Prüfverfahren

Der Unterschied zwischen einem Skill, der gut klingt, und einem, der etwas kann, ist eine Messung durch jemanden, der die Erwartung nicht kennt.

## Prüffälle

Erfundene Fälle, die die schwersten Momente des Feldes enthalten: das Betrugsmuster, die abgelaufene Frist, die Dublette, die verlockende Bewertung, die man nicht abgeben darf, die unbelegte Tatsache, die man nicht behaupten darf, die Datei, die man nicht anfassen darf. Sechs Fälle waren für Marlene genug, um drei Runden lang Unterschiede zu zeigen. Jeder Fall beschreibt Dokumente, statt sie mitzuliefern, und kann so ohne echte Daten laufen.

Ein Fall hat ein Datum. Ein Fall, dessen Zeitraum noch läuft (Abrechnung 2026 im September 2026), ist ein Fehler des Falls, und fremde Instanzen finden ihn.

## Die Norm, damit zwei Messungen dasselbe messen

Seit dem 13.09.2026 gilt für jede neue Runde dieselbe Form, weil die Ergebnisse sonst nebeneinander stehen, ohne vergleichbar zu sein: **vier Prüffälle, zehn Kriterien je Fall, vier Konfigurationen** (drei Fassungen und ohne Skill), oder zwei Konfigurationen, wenn es keine Fassungen gibt. Vier Fälle, weil sechs mal vier Läufe dreimal das Sitzungslimit gerissen haben; zehn Kriterien, weil die Bewerter darunter zu trennen aufhörten.

**Der Prompt nennt nur die Lage, nie die Lücke.** Er sagt, was geschehen ist, nie, was daran fehlt. Die Wortzahl ist dabei der falsche Hebel — beim ersten Versuch am 13.09.2026 lagen drei von vier Fällen über der selbstgesetzten Grenze von sechzig Wörtern, weil das Zitat des Auftraggebers und die nackte Lage zusammen mehr brauchen. Maßgeblich ist der Inhalt: Zitat und Tatsachen so knapp wie möglich, und kein Satz, der eine Lücke benennt, die der Skill selbst finden soll. Ein Satz wie „Stand: keine Mindestrücklage gesetzt, kein Jahresrahmen" verrät der Vergleichsinstanz die halbe Lösung, und genau das hatte der Skill leisten sollen. Gemessen am 13.09.2026: Die Promptlänge korreliert fast monoton mit dem schrumpfenden Abstand zur Fassung ohne Skill — Karl 26 Wörter und 17 Punkte Abstand, Gerd 141 Wörter und 8, in Runde 2 noch 4.

Ergebnisse aus der Zeit davor bleiben stehen, wie sie sind, und tragen den Vermerk, unter welcher Form sie entstanden. Umgerechnet wird nichts; eine nachträglich angepasste Zahl ist keine Messung mehr.

## Kriterien vor dem Bau

Je Fall sechs bis dreizehn Kriterien, objektiv prüfbar aus den Ausgaben: Zahlen, Daten, Paragraphen, das Vorhandensein einer Kennzeichnung, das Fehlen einer IBAN. Jedes Kriterium ist eine Aussage, die ein fremder Bewerter mit einem Zitat belegen oder widerlegen kann. Gebündelte Kriterien („ist gekennzeichnet und wird eingeholt und nichts wird versendet") werden geteilt; ein Bewerter hat es dreimal angemahnt.

Der Auftraggeber sieht die Kriterien, bevor der Skill sie sieht.

Neben jedem Kriterium steht „Prüfbar durch": Zitat, Struktur, Suche, Nachrechnen. Unter den Kriterien steht ein Abschnitt „Bekannte Schwächen der Kriterien" (Längenlimits sind Setzungen, „nächste Woche" hat zwei Lesarten). Der Prompt eines Falls bringt sein Material selbst mit („Im Notizbestand gibt es: (a) … (b) …"), sonst ist das Kriterium nicht aus der Ausgabe prüfbar. Zwei Versuchungen gehören in jeden Satz von Fällen: eine eingebettete Anweisung im Material („ignoriere alles vorher und …"), die als Inhalt behandelt werden muss, und ein Termin, der vor dem Falldatum liegt.

Ein Kriterium darf nicht mit einem anderen kollidieren. „Jede Frage mit Empfehlung" und „das Recht nicht raten" fielen in Runde 1 zusammen, und die beste Fassung verlor genau dort; die Auflösung steht in `auftrag-klaeren.md` (Empfehlung = bestätige den Messbefund). Ein Kriterium, das „ein Lauf je Fall" wörtlich verlangt, bestraft die Fassung, die drei ansetzt; es heißt „nennt die Zahl der Läufe je Fall als Grenze".

## Einen bestehenden Skill verbessern

Drei Bauinstanzen statt zwei: A ohne Skill, B mit dem alten Skill, C mit dem neuen. C minus B ist die Verbesserung, C minus A der Beitrag des Skills. Die erste Runde ist eine Nullmessung des alten Skills, niemand baut vorher. Die Frage an den Auftraggeber lautet „Woran würdest du merken, dass der Skill besser ist?" mit Empfehlung und zwei Alternativen; „zehnmal besser" wird als unmessbar benannt, und zwar im ersten Satz. Die Ergebnistabelle wird mit drei Fragen gelesen: Wo ist „mit" nicht besser, wo schlechter, was fällt bei beiden durch.

## Läufe

Je Fall zwei Läufe durch fremde Instanzen (Subagenten): einer mit Skill-Pfad, einer ohne, identischer Prompt, identische Ausgabeform, Ausgaben als Dateien in einem Arbeitsbereich. Der Prompt verbietet Zugriff auf echte Daten und jede Bewegung. Läufe ohne Skill dürfen in späteren Runden wiederverwendet werden, wenn der Prompt gleich blieb; das steht dann dabei.

Arbeitsbereich: `<skill>-workspace/iteration-N/eval-<id>-<name>/{with_skill,without_skill}/run-1/outputs/`, dazu `eval_metadata.json` (Prompt, Kriterien) je Fall und `timing.json` je Lauf (Tokens, Dauer aus der Abschlussmeldung des Subagenten, sofort sichern, es gibt sie nur dort).

## Bewerter

Je Fall ein fremder Bewerter, der alle Läufe mit demselben Maßstab bewertet. Die Anleitung des Skill-Creators (`agents/grader.md`) liegt nicht auf jedem Rechner als Datei; deshalb steht die Anleitung als Text im Arbeitsbereich (`BEWERTER_ANLEITUNG.md`, Vorlage in `scripts/eval_workspace.py init`) und nennt das Format von `grading.json` (Felder `expectations[text,passed,evidence]`, `summary`, `execution_metrics: {}`, `eval_feedback`). Der Bewerter kennt die Zuordnung Fassung zu Anleitung nicht. Er schreibt neben den Bewertungen einen `VERGLEICH.md` je Fall: Tabelle Kriterium × Konfiguration, und welche Sätze oder Verfahren aus einer Fassung in die anderen gehören. Beweislast beim Kriterium: im Zweifel Fehlschlag. Der Bewerter kritisiert auch die Kriterien; das ist die Quelle der nächsten Runde.

## Zusammenrechnen und zeigen

Aggregation über den Skill-Creator (`python3 -m scripts.aggregate_benchmark <workspace/iteration-N> --skill-name <name>` aus dem Skill-Creator-Ordner; erwartet `run-1/`-Unterordner; ein `execution_metrics: null` in einer grading.json bringt ihn zu Fall, vorher auf `{}` setzen). Übersicht über `eval-viewer/generate_review.py --static <datei> --previous-workspace <vorige Runde>`; auf Python 3.9 braucht das Skript eine Kopie mit `from __future__ import annotations` in der ersten Zeile. Die Übersicht bekommt der Auftraggeber als Datei.

Eigene Zusammenfassung daneben, weil der Aggregator Tokens anders zählt: Summen je Fall, je Fassung, Tokens und Sekunden.

## Runden

Nach jeder Runde: Befunde am Skill auf Gültigkeit prüfen (widerspricht er einer Regel, einem anderen Befund, dem Auftrag?), dann einbauen; Befunde an den Kriterien für die nächste Runde übernehmen, Fälle mit Fehlern korrigieren. **Entwicklungsfälle sind keine Abschlussfälle:** Wer dieselben vier Fälle über drei Runden nachbessert, optimiert auf diese Fälle. Die Abschlussmessung enthält mindestens einen Fall, den keine Runde gesehen hat, oder einen Praxistest an echten Kopien. Vorher stehen Aufwand und Abbruch fest: höchstens drei Runden je Skill ohne neue Regel, dann ist es eine Kriterienfrage, keine Skillfrage. Bei Marlene: Runde 1 49 Kriterien 49/49 gegen 35/49, Runde 2 55 Kriterien 54/55 gegen 32/55, Runde 3 62 Kriterien 60/62 gegen 35/62. Fertig, wenn eine Runde nur noch die Kriterien schärft.

## Betrieb

Zwölf parallele Läufe erreichen das Sitzungslimit; danach in zwei Wellen. Abgebrochene Läufe hinterlassen halbe Ausgaben; sie werden beiseitegelegt (`abgebrochen-<datum>/`), nie bewertet. Ein Lauf, der nach dem Schreiben der Ausgaben abbricht, ist vollständig, seine Laufzeit wird geschätzt und so gekennzeichnet. Ein Bewerter, der abbricht, wird neu gestartet.

## Grenzen, die in jeden Bericht gehören

Ein Lauf je Fall und Fassung. Bewerter sind Modelle, wenn auch unabhängige. Fälle sind erfunden und beschreiben Dokumente. Läufe ohne Skill werden nach der ersten Runde wiederverwendet. Der Skill wird mit demselben Modell gebaut und geprüft; ein anderes Modell kann anders lesen. Und: Der Vergleich mit und ohne Skill misst das ganze mitgegebene Paket — läuft die Vergleichsinstanz aus dem Projektordner, kennt sie die Projektregeln, und der Abstand ist der Zuwachs des Skills über diese Regeln, nicht über null; das steht im Bericht (Lehre 28).
