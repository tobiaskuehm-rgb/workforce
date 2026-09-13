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

## Aus Gerd Runde 2 und Anastasia Runde 1 (2026-09-08)

32. **Ein Skill wird kürzer, nicht länger.** Gerds Fassung mit Skill brauchte 210k Token gegen 344k ohne, bei gleicher Prüfleistung. Wer eine Regel hat, sucht nicht mehr; das ist neben der Genauigkeit der zweite Ertrag und gehört in den Bericht.
33. **Eine Regel am Ende der Datei wird zuletzt gelesen.** Gerds Einfrierungsregel stand unter „Regeln, die nicht verhandelbar sind" und wurde in beiden Läufen übergangen. Was am Anfang jedes Auftrags gilt, gehört in den ersten Schritt des Verfahrens, nicht in die Liste am Schluss.
34. **Der Kopf trägt das Datum des Auftrags.** Drei Läufe datierten ihr Ergebnis auf den Rechner statt auf den Prüftag. Kein Kriterium fragte danach; zwei Bewerter fanden es nebenbei. Wo ein Prüffall ein Datum setzt, gehört ein Kriterium dazu.
35. **Ein Kriterium, das nicht mehr trennt, ist verbraucht.** Fall 1 bei Gerd stand nach der zweiten Runde 12/12 gegen 12/12. Das heißt nicht, dass der Fall gut ist, sondern dass er seine Arbeit getan hat; er wird für die nächste Runde ersetzt oder verschärft.
36. **Die Baseline in Alltagssprache ist die ehrlichere.** Bei Anastasia bekam der Lauf ohne Skill dieselbe Aufgabe ohne Rollenvokabular. Er fand dasselbe wie der Skill, wo gesunder Menschenverstand reicht, und brach genau dort ein, wo Verfahren zählt (3/9 statt 9/9). Ein Abstand, der nur aus Hausvokabular besteht, misst nichts.
37. **Der Abstand misst, wie viel Selbstbeschränkung die Rolle braucht.** Thorsten hatte in Runde 1 den größten gemessenen Abstand (34/36 gegen 15/36), weil seine Rolle fast nur aus Nichttun besteht: keine Ideen erfinden, keine Zahl setzen, keine Empfehlung geben. Wo eine Rolle vor allem etwas unterlässt, trägt der Skill am meisten — und ein kleiner Abstand heißt umgekehrt nicht, dass der Skill schwach ist, sondern dass die Rolle näher am Naheliegenden liegt.
38. **Eine Verweigerung, die dreimal begründet wird, ist halb geliefert.** Beide Konfigurationen lehnten die Anlageberatung ab und schrieben dann 443 und 502 Wörter, eine davon mit selbst gerechneten Szenarien. Wer eine Prognose verweigert und daneben rechnet, hat sie gegeben. Zu jeder Absageregel gehört eine Längengrenze.

## Aus dem Review der Skilltexte (2026-09-08, von außen)

39. **Ein Review ohne die Referenzen findet die Widersprüche in der Skilldatei selbst,** und die sind die teuersten, weil sie bei jedem Aufruf mitgehen. Elf Punkte, neun angenommen: Frist zuerst stand in Schritt 4 hinter der Rechnungsprüfung in Schritt 3; die Sichten des 3-Loops standen hinter den Vorschlägen, obwohl der Text „vorher benannt" verlangte. Vor jeder Übergabe liest jemand nur die Skilldatei, ohne Referenzen, und sucht Sätze, die einander widersprechen.
40. **Ein Wort, das im Skill eine Handlung verbietet, braucht im Skill seine Bedeutung.** „Ein Konto anfassen" neben „Bankabgleich", „hochladen" neben „ablegen", „Lauf" neben „stoppt": Jedes war in der Referenz oder im Kopf des Autors eindeutig und in der Datei nicht. Die Bedeutung steht in der Klammer daneben, nicht drei Dateien weiter.
41. **Nicht jeder Befund von außen ist einer.** „Lesenden Bankzugriff unterscheiden" klang vernünftig und hätte eine Datengrenze aufgehoben, die Absicht ist; „Prüfvermerk auf Arbeitskopie" hätte die Dublette erzeugt, die der Skill verhindert. Zurückgewiesen mit Grund, wie Regel 8 es verlangt.

## Aus dem Bau von /idee (2026-09-08)

42. **Eine Reihenfolge, die der Text verlangt, wird als Gliederung der Ausgabe geschrieben, nicht als Regel.** Drei Fassungen verlangten „zehn Punkte vor dem Gegenvorschlag"; in Fall 1 hielt es keine. Als nummerierte Abschnitte der Ausgabe hielt es das Gericht in zwei von drei Fällen als einzige. Ein Modell folgt der Form, die es schreiben soll, eher als einer Regel, die es sich merken soll.
43. **„Idee plus Sicherungen" ist kein Gegenvorschlag.** Drei von vier Fassungen bauten die Alternative als Verbesserung der Idee und ließen sie dann gewinnen. Ein Gegenvorschlag ist das Gegenteil an der Stelle, an der die Idee am meisten voraussetzt; sonst vergleicht man eine Idee mit ihrer eigenen zweiten Fassung.
44. **Der Verfahrens-Skill braucht dieselbe Messung wie der Rollen-Skill.** /idee hatte am Vormittag einen Entwurf, am Nachmittag drei Fassungen und 32 Kriterien, und der Entwurf war die beste Fassung — aber erst die Messung sagte, was ihm fehlte, und das kam aus den unterlegenen.

## Aus dem Bau der drei Waechter (2026-09-12)

45. **Ein Waechter, der seine eigene Datenform nicht kennt, meldet gruen.** Meine erste Fassung suchte die Entwurfskennung im Postprotokoll; das Protokoll fuehrt aber Empfaenger, Betreff und Freigabe, keinen Entwurfspfad. Ergebnis: keine Zuordnung, keine Funde, dreimal gruen — bei zwei bekannten Verstoessen. Der erste Lauf eines Waechters geht gegen die echten Daten, und wenn er gruen ist, wo ein Verstoss bekannt ist, ist der Waechter kaputt, nicht die Lage.
46. **JSON null ist nicht leer.** `str(daten.get("freigabe", ""))` ergibt bei `null` den Text `None`, und der ist nicht leer. Die eine Vorgangsdatei ohne Freigabe kam so durch. Richtig ist `str(x or "")`; die Gegenprobe speist `null` ein, nicht nur einen fehlenden Schluessel.
47. **Ein Waechter, der immer rot ist, wird abgeschaltet.** Das Feld fuer den Versandvermerk gibt es in keiner der 23 Vorgangsdateien; je Sendung ein Fund waeren 23 gleiche Zeilen. Fehlt ein Verfahren ganz, ist das ein Befund ueber das Verfahren; sobald es gepflegt wird, wird jede Luecke einzeln gemeldet. Zwei Stufen statt einer Flut.
48. **Eine Schwelle wird an beiden Seiten geprueft.** Sieben Tage heisst: bei sieben gruen, bei acht rot. Ohne die Gegenprobe an der Grenze steht dort ein Vergleichsoperator, den niemand gelesen hat.

## Aus dem Vergleich der Messungen (2026-09-13)

49. **Zahlen aus verschiedenen Formen stehen nebeneinander, als wären sie dasselbe Maß.** Drei Fälle gegen sechs, 32 Kriterien gegen 62, 26 Wörter Prompt gegen 141 — und im Register steht das Ergebnis in einer Spalte. Der CEO hat es gesehen, ich nicht. Eine Norm je Runde, und wo sie fehlt, steht sie als Vermerk dabei.
50. **Der Prompt verrät, was der Skill leisten soll.** Je mehr Lage in der Aufgabe steht, desto kleiner der Abstand zur Fassung ohne Skill; die Reihenfolge ist fast monoton. Ein Prüffall sagt, was geschehen ist, nie, was daran fehlt — sonst misst man, wie gut man selbst die Aufgabe gestellt hat.
51. **Der Abstand ist nicht die Güte.** Sieben Punkte Vorsprung bei Wolle und fünfundzwanzig bei Marlene sagen etwas über die Aufgabe, nicht über die Rolle. Das bessere Maß ist die eigene Punktzahl gegen die eigenen Kriterien; der Abstand gehört daneben, mit der Promptlänge.

## 52. Ein Skill kann eine Falle beim Namen nennen und trotzdem hineinlaufen

Wolles Text führte die vier Formen der versteckten Empfehlung als Tabelle, samt Beispielen aus der ersten Messrunde. In Runde 2 kam der Rat trotzdem durch, in einer fünften Form, die dort nicht stand: bedingt. „Wenn du entscheidest, dann auf einem frischen Stichtag" liest sich als Sorgfalt und ist eine Auflage an die Handlung. Eine Liste verbotener Formen schützt nur vor den Formen, die auf ihr stehen; die nächste Messrunde findet die nächste. Deshalb gehört neben die Liste ein Satzmuster, das sich prüfen lässt — hier: jeder Satz, der mit „wenn du" beginnt und mit einer Anweisung endet.

## 53. Zwei richtige Antworten dürfen nicht gegeneinander stehen

Fall 2 verlangte den Anteil gesetzter Werte als Zahl und zugleich, eine unbewertete Position nicht zu bewerten. Wer das zweite richtig machte, hatte keinen Nenner für das erste. Der Lauf scheiterte an einem Kriterienfehler, nicht an einem Mangel — und das ist die teuerste Sorte Fehlmessung, weil sie wie ein Befund aussieht. Die Auflösung war keine Lockerung, sondern eine schärfere Frage: Wo der Prozentsatz nicht geht, stehen Klassenzahl und Spanne. Ein Kriterium, das zwei richtige Antworten gegeneinander stellt, misst den Skill nicht, sondern sich selbst.

## 54. Die Kritik der Bewerter am Kriterienkatalog ist der wertvollste Teil ihrer Arbeit

In Runde 2 haben die vier Bewerter sieben Kriterien angegriffen — zwei Widersprüche, zwei, die in jedem Lauf trivial bestanden wurden, zwei Geschmacksurteile ohne Maßstab, eines ohne Nähegrenze. Alle sieben ließen sich nachvollziehen und wurden geändert; zwei der drei Punkte, die Runde 3 gewann, kamen aus dieser Kritik und nicht aus dem Skilltext. Das Feld `eval_feedback` ist deshalb keine Höflichkeitszeile: Wer es leer lässt, misst in der nächsten Runde mit demselben stumpfen Werkzeug.
