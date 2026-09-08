# Sparring: Befundnummern per Sperrdatei

*Ideen-Vergleich, Fassung B (Sparring). 2026-09-08. Eine Viertelstunde, eine Seite.*

## 1. Die Idee, zurückgespiegelt

Tobias: „Gerd soll seine Befundnummern nicht mehr aus der Datei ablesen, sondern es gibt eine kleine Sperrdatei `NAECHSTE_NUMMER.txt` im Repo. Wer eine Nummer braucht, liest sie, erhöht sie, committet sofort. Dann gibt es keine Doppelvergabe zwischen Codex und Claude mehr."

Ziel dahinter: zwei Instanzen, die abwechselnd im selben Repo arbeiten, dürfen nie dieselbe Befundnummer vergeben — heute hängt das daran, dass wer zuerst die Kopfzeile in `REVIEW_GERD.md` schreibt, die Nummer behält.

## 2. Der Gegenschlag

Das Gegenteil an der Stelle, an der die Idee am meisten voraussetzt: Sie setzt voraus, dass es **eine** fortlaufende Zahl geben muss, die alle teilen. Der Gegenschlag streicht den geteilten Zähler ersatzlos.

**Was:** Die Befundkennung trägt Herkunft und Datum statt einer globalen Zahl — `G-2026-09-08-01`, `C-2026-09-08-01`. Vergeber ist der Präfix (Gerd/Codex/Claude/Vertretung), Datum ist der Tag, die letzte Ziffer zählt nur **innerhalb** des eigenen Laufs an diesem Tag.

**Wo:** Nur in der Namenskonventionstabelle von `CLAUDE.md`/`AGENTS.md` und in Gerds Skill. Keine neue Datei, kein neuer Ordner, kein Skript.

**Was es kostet:** Ein Absatz in zwei gespiegelten Dateien, ein Absatz im Skill. Die bestehenden `G-001`–`G-091` bleiben stehen und werden nie umnummeriert; die Reihe endet einfach, wie `SV-2026-09-03-01` sie schon einmal verlassen hat — das Muster existiert im Bestand also bereits und ist nicht erfunden.

**Was es riskiert:** Man kann nicht mehr auf einen Blick sagen, wie viele Befunde es insgesamt gibt (die Zahl war ohnehin nie die Aussage). Zwei Läufe derselben Instanz am selben Tag müssen ihre eigene laufende Ziffer kennen — das ist aber eine Datei, die ein Lauf selbst schreibt, kein geteilter Zustand. Und alte Verweise und neue Kennungen sehen unterschiedlich aus, dauerhaft.

*Gemessen wurde nichts: Ich durfte für diesen Lauf keine Repo-Datei öffnen. Alles unten stützt sich auf die im Auftrag genannte Lage und auf die Regeln, die ich aus dem Projektkontext kenne. Wo etwas geschätzt ist, steht es dabei.*

## 3. Zehn Fragen

**Selbstbewertung durch den Verfasser des Gegenschlags; wo ich mir selbst geglaubt habe, steht ein Stern.**

| # | Frage | Idee (Sperrdatei) | Gegenschlag (Präfix+Datum) |
|---|---|---|---|
| 1 | Löst er die Frage ganz? | **Nein** — er verschiebt die Kollision von der Kopfzeile auf eine Ein-Zeilen-Datei; zwei lokale Commits `92→93` kollidieren beim Push, und eine Ein-Zeilen-Datei kann Git nicht mergen | **Ja** — zwei Vergeber können bauartbedingt nicht dieselbe Kennung erzeugen |
| 2 | Merkt Tobias in zwei Wochen etwas davon? | **Ja** — jeder Befund kostet einen Extra-Commit | **Ja** — die Kennungen sehen anders aus |
| 3 | Unter einer Stunde Arbeit? | **Nein** — Datei, Format, Skillanpassung, Konfliktregel für den Push, dazu ein Wächter, sonst ist es Disziplin (Leitplanke: „Disziplin ist die schwächste Absicherung") | **Ja** — drei Absätze, davon zwei gespiegelt |
| 4 | Kein neues Geld? | **Ja** | **Ja** |
| 5 | In einer Stunde rückgängig? | **Ja** — Datei entfernen, alte Regel zurück | **Ja*** — zurück geht schnell, aber vergebene Kennungen bleiben in Nachweisen stehen (knapp, deshalb Stern) |
| 6 | Widerspricht keiner bestehenden Entscheidung? | **Nein** — ein zweiter Ort, der dieselbe Tatsache nennt wie `REVIEW_GERD.md`; genau die Klasse, gegen die `G-050` steht („eine Zahl, die nirgends steht, kann nicht veralten") | **Ja*** — `SV-2026-09-03-01` zeigt das Muster im Bestand; ob eine Umstellung der Kennungen eine `DEC`-Nummer braucht, ist offen (Stern) |
| 7 | Braucht nichts, was noch nicht da ist? | **Nein** — braucht eine Konfliktregel für den NAS-Remote und einen Test, der sie hält | **Ja** — braucht nur Git und ein Datum |
| 8 | In vier Wochen erkennbar, ob es funktioniert hat? | **Ja** — eine Doppelvergabe fällt auf | **Ja** — dito, und eine Doppelvergabe wäre hier ein Fehler *im* Lauf, nicht zwischen zweien |
| 9 | Ändert nichts, das nicht gefragt war? | **Nein** — der Commit-Rhythmus jedes Befunds ändert sich („committet sofort" heißt: ein Commit ohne Inhalt, gegen Leitplanke 5, die im Rumpf ein Warum verlangt) | **Ja** |
| 10 | Ginge das ohne Befund durch Gerd? | **Nein** — er würde mindestens fragen, wo der Wächter ist, der die Sperrdatei gegen `REVIEW_GERD.md` hält, und was beim Push-Konflikt gilt | **Ja*** — er würde die Umstellung selbst wohl durchgehen lassen, aber nach dem Umgang mit den Altnummern fragen (knapp, deshalb Stern) |

**Stand: Idee 4 Ja — Gegenschlag 10 Ja.** Der Gegenschlag führt. Drei seiner Siege tragen einen Stern.

## 4. Fazit

**Wo die Idee hält:** Die Diagnose stimmt vollständig — „wer zuerst die Kopfzeile schreibt, behält die Nummer" ist ein Wettlauf und keine Regel, und bei zwei abwechselnd arbeitenden Instanzen mit gemeinsamem Remote ist die Doppelvergabe eine Frage der Zeit, nicht der Wahrscheinlichkeit. Dass das geregelt gehört, ist unbestritten.

**Wo sie wackelt:** Ein Zähler in Git löst keinen Wettlauf, er benennt ihn nur um. Die Serialisierung findet beim `push` statt, nicht beim `commit`, und eine einzeilige Datei ist der ungünstigste denkbare Merge-Gegenstand — sie erzeugt einen Konflikt genau dann, wenn zwei Seiten gleichzeitig arbeiten, also im einzigen Fall, für den sie gebaut wurde. Dazu ist sie ein zweiter Ort für dieselbe Tatsache (`G-050`) und braucht damit sofort einen Wächter, sonst ist sie eine Zusicherung ohne Deckung (Leitplanke 7).

**Was die Idee vom Gegenschlag nehmen sollte:** Den Verzicht auf den geteilten Zustand. Wenn die fortlaufende Zahl bleiben soll, dann wenigstens mit Vergeber-Präfix — `G-092`, `C-001` — damit die Datei zwar noch existiert, ein Konflikt aber nie mehr zwei Befunde denselben Namen gibt, sondern höchstens eine Lücke in einer Reihe hinterlässt. Eine Lücke ist ein kosmetischer Schaden, ein Namensdoppel ein Nachweisschaden.
