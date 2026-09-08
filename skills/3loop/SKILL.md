---
name: 3loop
description: Der 3-Loop, ein Entscheidungsverfahren von Marv Skillbauer. Ein Vorschlag, drei Gegenvorschläge, drei Bewertungen aus benannten Sichten, ein Fazit. Verwenden, wenn Tobias eine Entscheidung mit Alternativen will ("mach daraus einen 3loop", "/3loop", "drei Gegenvorschläge", "bewerte das aus meiner, deiner und Gerds Sicht", "welche Variante", "Konzept mit Alternativen") oder wenn ein Vorschlag da ist und niemand ihn bisher angegriffen hat. Gilt für Konzepte, Architektur, Code und Verfahren gleich. Nicht verwenden für Aufträge ohne Wahl (eine Datei ablegen, einen Fehler beheben).
---

# Der 3-Loop

Ein Vorschlag, der nie einen Gegenvorschlag gesehen hat, ist eine Meinung mit Vorsprung. Der 3-Loop zwingt drei Alternativen an denselben Tisch, bewertet alle vier mit denselben Fragen aus drei Sichten und endet mit genau einem Fazit. Er stammt aus dem Bau von Marlene und Marv: Dort hießen die Gegenvorschläge Fassungen, die Sichten Gerd, Anastasia und Tobias, und das Fazit die Synthese. Das Verfahren ist dasselbe; hier ist es auf eine Seite gebracht, damit es für jede Entscheidung taugt.

## Die sieben Teile, in dieser Reihenfolge

1. **Die Frage in einem Satz.** Was wird entschieden, wer entscheidet, bis wann. Steht sie nicht in einem Satz, sind es zwei Loops.
2. **Gemessen, nicht gemeint.** Bevor der erste Vorschlag steht: Was gibt der Rechner, der Ordner, das Repo, der Bestand her? Zahlen mit Befehl. Was nicht messbar war, heißt „nicht gemessen".
3. **Drei Sichten und ihre Fragen, jetzt festgelegt.** Je Sicht eine Person oder Rolle mit einem Interesse, das die anderen nicht vertreten: bei Tobias meist der Alltag (findet er es, kostet es ihn Zeit), die Fachstelle (Marlene: hält es das Verfahren aus) und der Prüfer (Gerd: was passiert bei Ausfall, Verlust, Fehler; ist es nachweisbar). Je Sicht drei bis fünf Fragen. Sichten und Fragen stehen fest, **bevor** der erste Vorschlag ausformuliert ist, damit die Bewertung nicht dem Lieblingsvorschlag folgt. Und sie sind simulierte Sichten: Eine vom selben Modell geschriebene „Sicht von Gerd" ist nicht Gerds Urteil, sie heißt so und wird so gekennzeichnet; Gerd kann sie im Review kippen.
4. **Der Vorschlag (A).** Meist der des Auftraggebers. Wörtlich übernommen, dann in ganze Sätze gebracht, nie stillschweigend verbessert. Was A voraussetzt und nicht sagt, steht als Annahme daneben.
5. **Drei Gegenvorschläge (B, C, D).** Jeder einseitig, keiner ein Kompromiss: Einer stellt A an einer anderen Stelle auf den Kopf. Gute Gegenvorschläge lauten „das Gegenteil an der teuersten Stelle", „dasselbe Ziel mit dem, was schon da ist", „die einfachste Form, die noch alles erfüllt". Alle vier auf demselben Raster (Ort, Ablauf, Kosten, Aufwand, Risiko), sonst vergleicht man Äpfel mit Absätzen.
6. **Die Matrix.** Jede Sicht bewertet alle vier Vorschläge mit ihren Fragen, Note 1 bis 5, je Note ein Satz mit Grund. Vorschläge als Spalten, Fragen als Zeilen, Summe unten. Die Summe ist eine Sortierhilfe, keine Entscheidung; das Fazit darf ihr widersprechen und sagt dann warum. Die Matrix darf so lang sein, wie sie ist (vier Vorschläge mal neun bis fünfzehn Fragen sind 36 bis 60 begründete Noten); gekürzt wird nicht an den Begründungen.
7. **Ein Fazit.** Eine Empfehlung, mit den Auflagen aus den unterlegenen Vorschlägen, die sie besser machen. Dann die offenen Fragen, die nur der Auftraggeber beantworten kann, mit Empfehlung und zwei bis drei Optionen. Und die eine Sache, die am ehesten noch falsch ist.

## Verwandt

Braucht die Frage nur einen Gegenvorschlag, ist `/idee` das kleinere Verfahren: zwei Vorschläge, zehn feste Punkte, blinde Bewertung durch eine fremde Instanz. Der 3-Loop ist für Fragen mit mehr als einer sinnvollen Alternative.

## Für Code

Der Loop gilt für Code vollständig, mit drei Zusätzen:

- **Gegenvorschläge sind Skizzen mit Schnittstelle**, nicht Prosa: die zentrale Datenstruktur, der Aufruf, das eine Beispiel. Zehn Zeilen je Vorschlag reichen; ein fertiger Bau ist keine Alternative mehr, sondern ein Vorsprung.
- **Eine Sicht ist immer die Messung.** Testbarkeit, Laufzeit gegen echte Daten, Wiederherstellung nach Absturz. Wo sich etwas in fünf Minuten probieren lässt (ein Aufruf, ein Import, ein Zeitwert), wird es probiert und die Zahl steht in der Matrix.
- **Das Fazit nennt den Test, der die Entscheidung hält.** Wer den gewählten Vorschlag später bricht, soll an einem Test scheitern, nicht an einer Erinnerung.

## Regeln

1. Vier Vorschläge, nicht drei und nicht fünf; drei Sichten, vorher benannt.
2. Der Vorschlag des Auftraggebers wird nicht verbessert, bevor er bewertet ist.
3. Jede Note trägt einen Satz mit Grund; eine Note ohne Grund ist eine Stimmung.
4. Gemessenes und Geschätztes stehen getrennt; eine Zahl ohne Befehl oder Quelle ist geschätzt.
5. Das Fazit ist eine Empfehlung mit Auflagen, keine Zusammenfassung; es endet mit den Fragen an den Auftraggeber.
6. Was der Auftraggeber schon entschieden hat, wird als Randbedingung geführt, nicht neu verhandelt; widerspricht der neue Vorschlag einer alten Entscheidung, steht das im ersten Absatz.
7. Die **Vorlage** ist eine Seite: Frage, Messung in einer Tabelle, die vier Vorschläge in je fünf Zeilen, Fazit mit Fragen. Die Matrix mit ihren Begründungen hängt daran und darf länger sein. Wird die Vorlage selbst länger als eine Seite, ist die Frage zu groß.

## Form der Ausgabe

Eine Datei oder Seite mit den sieben Teilen als Überschriften, die Matrix als Tabelle, das Fazit zuletzt. Auf Deutsch. Für den Auftraggeber als Artefakt oder Datei, nie nur im Chat.

## Herkunft

Verfahren aus dem Bau von Marlene (drei Fassungen, drei Sichten, Synthese, 2026-09-04) und Marv (drei Fassungen gegen vier Prüffälle, 2026-09-07). Als eigener Skill angelegt am 2026-09-07 auf Anregung von Tobias („ein Vorschlag, drei Gegenvorschläge, drei Bewertungen, ein Fazit"). Erster Anwendungsfall: das Ablagekonzept ohne Google Drive.
