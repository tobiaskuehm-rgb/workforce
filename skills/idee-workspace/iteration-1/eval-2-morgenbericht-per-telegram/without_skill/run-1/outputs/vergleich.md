# Morgenbericht: deine Idee gegen meinen Vorschlag

Stand: 08.09.2026

## Die Frage

Wie erfährt Tobias jeden Morgen, was in der Ablage fällig ist und was Marlene
zuletzt getan hat — ohne selbst in den Ordner zu sehen?

## Vorschlag A — deine Idee: Push um 7 Uhr per Telegram

Ein Zeitplan außerhalb des Skills (Automation auf der NAS oder ein
Scheduled Task) weckt Marlene jeden Morgen um 7 Uhr. Sie liest die Ablage,
baut den Bericht — was fällig ist, was gestern erledigt wurde — und schickt
ihn als Telegram-Nachricht an Tobias. Der Ordner wird nicht mehr geöffnet.

## Vorschlag B — mein Gegenvorschlag: Datei schreiben, Telegram nur als Wecker

Der Zeitplan läuft genauso um 7 Uhr, aber die Arbeit wird geteilt:

1. Marlene schreibt den vollständigen Bericht wie beschlossen als Datei nach
   `_Berichte/YYYY-MM-DD-morgenbericht.md`. Das ist die Fassung mit allem:
   Fristen, Beträge, Aktenzeichen, offene Rückfragen.
2. Telegram bekommt nur eine **Kurzmeldung ohne Modellaufruf**: drei bis fünf
   Zeilen, aus der Datei mechanisch abgeleitet (Anzahl fälliger Posten, die
   drei nächsten Fristen mit Datum, Anzahl gestriger Erledigungen), plus
   den Dateinamen.
3. Wer mehr will, antwortet im Bot — dann liest Marlene die Berichtsdatei und
   geht ins Detail. Das ist der einzige Weg, auf dem ein bezahlter Aufruf
   entsteht, und er entsteht nur, wenn Tobias ihn auslöst.
4. Fällt der Lauf aus, steht am nächsten Morgen in der Kurzmeldung, dass der
   Vortagesbericht fehlt. Stille bedeutet nie „nichts zu tun".

Der Unterschied ist nicht der Kanal, sondern **wo der lange Text entsteht und
wer ihn bezahlt**.

## Bewertung in zehn Punkten

| # | Kriterium | A (Push per Telegram) | B (Datei + Kurzmeldung) |
|---|---|---|---|
| 1 | Erfüllt den Wunsch „nicht mehr in den Ordner gucken" | **stark** — alles steht im Chat | mittel — Kurzmeldung reicht an ruhigen Tagen, sonst ein Antippen |
| 2 | Verträgt sich mit der Entscheidung vom 04.09. (Datei zuerst, Telegram später) | schwach — nimmt sie zurück, ohne dass ein Grund dokumentiert ist | **stark** — die Datei bleibt die Fassung, Telegram kommt als Zeiger dazu |
| 3 | Kostendeckel 2 USD / 100 Aufrufe pro Tag | schwach — ein langer Sonnet-Bericht täglich ist der teuerste Einzelposten und geht vom selben Deckel ab wie deine Tagesarbeit | **stark** — der tägliche Fixposten ist ein Modellaufruf für die Datei, die Meldung selbst kostet null |
| 4 | Verhalten bei erschöpftem Deckel | schwach — der Deckel greift genau dann, wenn du am Nachmittag viel gearbeitet hast; am nächsten Morgen kommt nichts, und Stille sieht aus wie „nichts fällig" | **stark** — Kurzmeldung läuft ohne Modell weiter und sagt, dass der Bericht fehlt |
| 5 | Aufwand bis zum ersten Lauf | **stark** — ein Zeitplan, ein Prompt, ein Sendeaufruf | mittel — zusätzlich die Ableitung Datei → Kurztext |
| 6 | Nachweisbarkeit („stand das da wirklich?") | schwach — eine Chatnachricht ist flüchtig und nicht durchsuchbar | **stark** — jeder Morgen liegt als datierte Datei, rückwärts lesbar |
| 7 | Datensparsamkeit | schwach — Beträge, Aktenzeichen, Arztrechnungen wandern täglich vollständig durch Telegram | **stark** — Zahlen und Namen bleiben in der Ablage, im Chat stehen Termine |
| 8 | Verhalten bei einem Fehler in Marlenes Lauf | schwach — ein halber Bericht ist trotzdem eine Nachricht und liest sich vollständig | **stark** — eine fehlende oder unvollständige Datei ist ein prüfbarer Zustand vor dem Senden |
| 9 | Zeitplan liegt außerhalb des Skills | gleich — beide brauchen ihn, beide erben dieselbe Bruchstelle | gleich, aber B merkt den Ausfall am Folgetag selbst |
| 10 | Reversibilität | mittel — Abschalten ist leicht, aber die Gewöhnung an den Push nicht | **stark** — der Push ist eine Schicht über der Datei und kann ohne Verlust weg |

Zählung: A gewinnt 1 und 5, B gewinnt 2, 3, 4, 6, 7, 8 und 10, Punkt 9 geht
unentschieden aus.

## Fazit

**B gewinnt.** Der entscheidende Punkt ist 4, nicht 3: Ein Bericht, der bei
erschöpftem Budget einfach ausbleibt, ist schlimmer als kein Bericht, weil
Stille sich wie „nichts fällig" liest — und genau an dem Tag, an dem viel los
war. B trennt deshalb die teure Arbeit (Bericht bauen) von der billigen
Zustellung (drei Zeilen senden) und macht die Zustellung unabhängig vom Modell.

**Aus A kommt das Beste mit:** Der Anstoß muss von außen kommen, du sollst
nichts abholen müssen. Genau das leistet die Kurzmeldung um 7 Uhr — sie ist
Push, nur ohne den Preis eines Berichts pro Tag.

**Was noch offen ist:** Die Entscheidung vom 04.09. hat Telegram vertagt; B
verletzt sie nicht, geht aber darüber hinaus. Bevor irgendetwas eingerichtet
wird, gehört das als kurze Vorlage vor dich — und der Zeitplan selbst ist
Arbeit außerhalb des Skills, die niemand nebenbei anlegt.

*Hier ist nichts eingerichtet und keine Datei außer dieser angefasst worden.*
