# Lehren aus Marlene

Jede Zeile hier war ein Fehler oder eine Beinahe. Lies sie vor dem nächsten Skill.

1. **Zwei Dinge in einem Kopf.** Stelle und Landschaft wurden gemischt, bis der Auftraggeber es sagte. Regel: Schritt 2 vor allem anderen.
2. **Die Nummer aus dem anderen Quellensatz.** Eine vorbereitete Migration hieß 005; im Repo war 005 längst belegt. Nummern, Kennungen, Namen werden dort vergeben, wo der Code liegt, nie übernommen.
3. **Der Compiler, der nicht kompiliert.** Vier Minuten Bauzeit für ein Werkzeug, das an einer SDK-Diskrepanz scheiterte. Vorher messen, ob das Werkzeug überhaupt läuft; die Bordmittel (JXA) taten in einer Sekunde, was der Compiler nicht tat.
4. **Die Frist aus dem Gedächtnis.** Bekanntgabefiktion drei statt vier Tage, seit 2025 geändert. Ein fremder Bewerter fand es; die Regel „abrufen, nicht erinnern" galt schon und wurde einmal gebrochen.
5. **Der Prüffall im laufenden Jahr.** „Abrechnung 2026 fertig machen" im September 2026. Beide Instanzen, mit und ohne Skill, fanden den Fehler des Falls. Fälle brauchen ein Datum und eine Plausibilitätsprüfung.
6. **Der Rechtsbehelf mit falschem Namen.** Gegen die Familienkasse gibt es Einspruch, nicht Widerspruch; mein Kriterium hatte es falsch, die Instanz ohne Skill hatte es richtig. Kriterien sind Behauptungen und können falsch sein; ein Bewerter, der widerspricht, hat vielleicht recht.
7. **Platzhalter sind Behauptungen.** „[beschädigte Teile werden aufbewahrt, bestätigen]" unterstellt die Tatsache. Regel: keine eckigen Klammern in Entwürfen, Fehlendes weglassen und fragen. Brauchte zwei Runden.
8. **Der Satz mit Semikolons.** Die Kernaussage war fünfzig Wörter mit drei Gliedern. Regel: ein Satz, 25 Wörter, kein Semikolon.
9. **Die Kopie nach dem Verschieben.** Der Plan kopierte Steuerbelege, nachdem die Quelle schon verschoben war. Der Selbsttest fand es; das Skript erzwingt jetzt die Reihenfolge.
10. **Das unsichtbare Zeichen.** Drei Zielordner trugen U+F028 am Namensende. Blind abgelegt gäbe es zwei gleich aussehende Ordner. Die Zielordner-Prüfung im Skript fand es; vorher hatte kein Auge es gesehen.
11. **Zwölf parallele Läufe** treffen das Sitzungslimit; sechs Läufe brachen ab, drei mit halben Ausgaben. Zwei Wellen, Abgebrochenes beiseite, nie bewerten.
12. **Der Aggregator, der Nullen zeigt.** Er erwartet `run-1/`-Unterordner und stürzt bei `execution_metrics: null` ab. Layout vorher prüfen, eigene Summen daneben rechnen.
13. **„Zehnmal besser" ist nicht messbar.** Messbar sind Kriterien, die vorher feststehen, und Läufe ohne Skill. Das steht in jeder Übergabe.
14. **Die Bewerter, die die Kriterien kritisieren,** waren die beste Quelle für die nächste Runde. Ihr `eval_feedback` wird gelesen, nicht nur ihre Pass-Rate.
15. **Der Auftraggeber antwortet in Sprachnachrichten-Deutsch,** mitten im Lauf. „Unwichtig" heißt Quarantäne, „ja ja" heißt ja. Verstehen wie ein Kollege, festhalten in ganzen Sätzen.
16. **Der Praxistest an echten Kopien** fand in einer Stunde, was drei Prüfrunden nicht fanden: die zu strenge Datumsregel, den Rückstand statt Eingang, die Fassungen im Drive. Kein Skill ist fertig, bevor er echte Kopien gesehen hat.

## Aus dem Bau von Marv, Runde 1 (2026-09-07)

17. **Die beste Fassung verlor an einem Kriterienkonflikt.** „Jede Frage mit Empfehlung" gegen „das Recht nicht raten": Der Ingenieur ließ die Empfehlung weg und fiel durch. Kriterien werden vor der Runde gegeneinander gelesen; die Auflösung ist „Empfehlung = bestätige den Messbefund".
18. **Der Sammelhinweis am Ende rettet keine Tabelle.** Ohne Skill standen Zahlen aus nicht abgerufenen Paragraphen unmarkiert in Tabellen, und `antwort.md` behauptete, jede Stelle sei markiert. Marke an der Zeile.
19. **Der Rechenfehler, den keine Regel findet.** Sieben statt sechs Monate im Kündigungsbeispiel, gegen die eigene Tabelle. Nur Nachrechnen findet das; jedes Beispiel wird nachgerechnet, jede Anzahl gegen ihre Liste gezählt.
20. **Der Satz, der das Gegenteil sagt.** „Prüft, ob eine Kündigung zulässig ist" in der Rollenbeschreibung einer sonst guten Fassung. Der Rollensatz steht fest und wird abgeschrieben, nicht neu formuliert.
21. **Reichtum außerhalb des Auftrags kostet Punkte.** Zehn Berufsbilder und drei Fassungen, wo ein Plan bestellt war; Gegenbauformen und Heartbeat, wo eine Trennung bestellt war. Der Umfang ist der Auftrag.
22. **Vier Konfigurationen je Fall sind vier Bewerter,** und zwei davon trafen das Sitzungslimit, ohne eine Datei geschrieben zu haben. Bewerter erst nach den Läufen starten, nicht parallel zu ihnen, und die Anleitung als Datei, damit ein Neustart wortgleich ist.

## Aus Runde 2 (2026-09-07)

23. **Die behauptete Messung.** Eine Ausgabe trug Werte in der Spalte „Gemessen" und schrieb zwei Absätze später, der Ordner sei nie geöffnet worden. Kein Kriterium fragte das ab; gefunden hat es der Bewerter. Was nicht gemessen wurde, heißt „nicht gemessen", auch wenn die Zahl aus der Aufgabenbeschreibung plausibel wäre.
24. **Die Gegenprobe, die niemand nachzählt.** Eine Ausgabe behauptete Trefferzahlen ihrer eigenen Suche falsch. Eine Gegenprobe ist erst ein Nachweis, wenn ihr Ergebnis stimmt; der Bewerter zählt sie nach.
25. **Der falsche Wochentag.** Ein Kündigungsbeispiel datierte einen Donnerstag als Mittwoch, im selben Satz mit einer unbelegten Behauptung über Werktage. Datumsangaben in Beispielen werden gegen den Kalender geprüft, nicht nur gegen die eigene Tabelle.
26. **Das Guthaben endet mitten in der Runde.** Drei Bewerter starben an aufgebrauchten Credits, nachdem die Läufe schon bezahlt waren. Läufe zuerst sichern (`timing.json` sofort), Bewerter danach; ein Modellwechsel mitten in einer Runde ist zulässig, gehört aber als Einschränkung in den Bericht.
27. **Der Bewerter, der Vorbefunde vorfindet.** Ein abgebrochener Bewerter hinterließ Dateien, die der nächste „bestätigte". Vor einem Neustart wird der Fallordner von Bewertungsresten befreit, sonst ist die zweite Bewertung nicht unabhängig.

## Aus dem Bau von Gerd, Runde 1 (2026-09-08)

28. **Die Baseline kennt das Projekt.** Eine Instanz ohne Skill, gestartet aus dem Projektordner, liest CLAUDE.md und zitiert alte Befunde. „Ohne Skill" heißt dann „mit Projektregeln, ohne Rolle"; das steht im Bericht, sonst ist der Abstand falsch gelesen.
29. **Kriterien, die Hausvokabular messen, messen die Rolle nicht.** „ROT", „Nicht blockierendes Backlog", „hoch/mittel/niedrig" trennten die Konfigurationen, ohne dass der Prompt sie vorgab. Entweder die Form in den Prompt oder das Kriterium inhaltlich formulieren.
30. **Die Korrektur braucht dieselbe Gegenprobe wie der Befund.** Ein Vorschlag mit Skill wiederholte den Fehler, den er behob, und kein Kriterium sah hin. Wer einen Test verlangt, der rot werden kann, verlangt es auch für den Test, den er vorschlägt.
31. **Ein Skill, der eine Datei nennt, wird gegen die Platte geprüft.** Gerds Skill führte eine Review-Datei weiter, die es im Repo nicht gab. Jeder Pfad in einem Skill wird beim Bau einmal aufgelöst.
