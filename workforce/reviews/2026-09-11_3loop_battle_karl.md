# 3-Loop: Wie das Ideen-Battle gebaut wird, damit „besser" messbar ist

Karl, 2026-09-11, auf `/3loop` des CEO zur Vorlage vom selben Tag. Die Sichten sind simuliert
und so gekennzeichnet; Anastasia und Gerd können sie im Review kippen.

## 1. Die Frage in einem Satz

Wie werden beim Ideen-Battle Erzeugen, Bewerten und Regelgeben verteilt, damit sich „Thorsten
ist besser geworden" von „Thorsten benotet sich besser" unterscheiden lässt; entscheidet der
CEO bis Donnerstag, 2026-09-17.

**Randbedingungen, schon entschieden:** `FILTER.md` ist das Instrument (2026-09-08). Takt
Montag Lage, Donnerstag Entscheidungen (2026-09-08). Erzeugen bleibt offen, eine Fassung ersetzt
ihre Zeile (Anastasia, vom CEO korrigiert, 2026-09-11). Kein Handel, keine Anlageberatung.
Anastasias Entscheidung vom 2026-09-11, Thorsten verantworte den Filter selbst, wird hier
**nicht** als Randbedingung geführt, sondern ist Gegenstand: Filteränderungen sind Klasse
Strategie, also CEO.

## 2. Gemessen, nicht gemeint

| Was | Wert | Befehl oder Quelle |
|---|---|---|
| Einträge in Thorstens Gedächtnis seit 2026-09-08 | 52 Zeilen | `grep -c "^\| 2026-09" skills/gedaechtnis/thorsten.md` |
| Kandidaten am 2026-09-10 in eigenen Läufen | 7 | Anastasias Review |
| Nennungen Brandschutz/Unterweisung | 10 | `grep -ci` |
| Filteränderungen | 2 (2026-09-06 Anlage, 2026-09-10 Ertragsregel) | `git log -- FILTER.md` |
| Battle-Läufe nach Skill (drei und drei) | 0 vollständige; 2 Erwähnungen | Gedächtnis, Anastasia |
| Vorhersagen vor einer Probe | 3 formuliert | `grep -ci vorhersage` |
| Proben mit Ergebnis | 0 | Gedächtnis |
| Fremde Bewerter je Kandidat | 0; alle Noten von Thorsten selbst | Anastasias Review |
| Kosten einer blinden Fremdbewertung | nicht gemessen; Marvs Messungen kosten einstellige Cent bis Euro je Lauf | Marvs Berichte |

**Nicht gemessen:** ob die Brandschutz-Kandidaten gut sind; wie viel Zeit der CEO für eigene
Noten hätte; ob Thorstens Vorhersagen treffen, weil keine Probe abgeschlossen ist.

## 3. Drei Sichten, jetzt festgelegt

**Tobias, Alltag:** Kostet es mich Zeit je Woche? Bekomme ich montags drei Ideen, die ich
nicht selbst hatte? Weiß ich nach vier Wochen, ob der Filter etwas taugt? Kann ich es liegen
lassen, ohne dass es kippt?

**Anastasia, Organisation (simuliert):** Sind Erzeuger, Bewerter, Regelgeber getrennt? Hat
jede Rolle Owner, Output, Gate? Ist Thorstens Probezeit daran messbar? Verträgt es Zuwachs,
ohne umgebaut zu werden?

**Gerd, Nachweis (simuliert):** Ist jede Note auf einen Bewerter und einen Regelstand
rückführbar? Gibt es einen Zustand, in dem der Wächter rot wird? Was passiert, wenn der
Bewerter ausfällt? Kann jemand die Noten nachträglich verschieben, ohne dass es auffällt?

## 4. Der Vorschlag (A): drei Rollen an drei Stellen

Karls Vorlage vom 2026-09-11, wörtlich: Erzeugen offen (Thorsten drei, CEO drei, montags);
Bewerten durch eine fremde Instanz, blind, nach Marvs Verfahren, gesammelt über den Bestand;
Regelwerk beim CEO donnerstags auf Vorlage über Karl, gültig ab dem nächsten Durchgang;
Maßstab sind Vorhersagen vor Proben, nicht Noten.

**Annahmen, die A nicht sagt:** Eine fremde Instanz benotet anders als Thorsten, obwohl beide
dasselbe Modell sein können. Blind heißt: Sie sieht nicht, wer erzeugt hat; sie sieht aber
die Kriterien, und die stammen von Thorsten. Marvs Verfahren lässt sich auf Ideen übertragen.
Proben werden überhaupt gelaufen, bisher null.

## 5. Drei Gegenvorschläge

**B, das Gegenteil an der teuersten Stelle: keine Noten, nur Proben.** Die teuerste Stelle ist
die Bewertung, denn sie kostet Aufbau, Modellbudget und Streit. Also: Stufe 2 entfällt. Jeder
Kandidat, der Stufe 1 (Ausschluss) besteht, bekommt eine billigste Probe unter 100 Euro und
vier Wochen; der Markt benotet. Thorsten erzeugt, sagt voraus, misst. Der Filter wird nur an
Probenergebnissen geändert.

**C, dasselbe Ziel mit dem, was da ist: Anastasias Verfahren.** Thorsten behält alle drei
Rollen, aber unter Regeln, die schon in seinem Skill stehen oder von ihm stammen: Verzerrung
je Lauf benannt, Fassung ersetzt Zeile, Filteränderung angekündigt und erst ab dem nächsten
Durchgang, und Anastasia misst monatlich die Häufung. Kein neuer Bewerter.

**D, die einfachste Form: der CEO benotet.** Thorsten liefert je Kandidat nur Fakten mit Quelle
und die Ausschlussprüfung, keine Noten. Der CEO vergibt die Noten montags selbst, denn er ist
der, der die Idee kaufen muss. Filter ändert nur er. Thorsten wird Rechercheur, nicht Richter.

| | A drei Stellen | B nur Proben | C Anastasia | D CEO benotet |
|---|---|---|---|---|
| Ort | Repo plus fremde Instanz | Markt | Repo, Thorsten | Chat montags |
| Ablauf | erzeugen, blind benoten, CEO regelt, Vorhersage zählt | Stufe 1, Probe, Ergebnis | wie heute plus Selbstdisziplin und Monatsreview | Fakten von Thorsten, Noten vom CEO |
| Kosten | ein Bewertungslauf je Kandidat, Cent bis Euro | bis 100 Euro je Probe | null | null Geld, CEO-Zeit |
| Aufwand bis es läuft | Marv baut den Prüffall, eine Woche | null, sofort | null | null |
| Risiko | fremde Instanz teilt Thorstens Kriterien | zu viele Proben, Geld und Zeit | Selbstbild statt Messung bleibt möglich | CEO ist der Engpass, Ankereffekt beim CEO |

## 6. Die Matrix

| Sicht und Frage | A | B | C | D |
|---|---|---|---|---|
| Tobias: Zeit je Woche | 4, eine Stunde montags | 3, Proben brauchen ihn (Briefe, Anrufe) | 5, wie heute | 2, er benotet alles selbst |
| Tobias: drei Ideen, die er nicht hatte | 4, Erzeugen bleibt offen | 4 | 4 | 3, Thorsten liefert nur Fakten, weniger Antrieb |
| Tobias: weiß nach vier Wochen, ob es taugt | 5, Vorhersagen gezählt | 5, Ergebnisse gezählt | 2, wieder nur Noten | 3, seine eigenen Noten |
| Tobias: liegen lassen | 4 | 3, Proben laufen aus | 4 | 1, ohne ihn steht alles |
| Anastasia: Rollen getrennt | 5 | 4, Markt bewertet, Thorsten regelt mit | 1, alle drei bei ihm | 4, CEO bewertet und regelt, zwei bei ihm |
| Anastasia: Owner, Output, Gate | 5 | 4, Gate ist das Probenende | 3, Gate ist ein Monatsreview | 3, Gate ist die Laune des Montags |
| Anastasia: Probezeit messbar | 5, Trefferquote der Vorhersagen | 5 | 2 | 3 |
| Anastasia: verträgt Zuwachs | 4 | 2, jede Probe kostet | 4 | 1 |
| Gerd: Note rückführbar | 5, Bewerter und Regelstand je Note | 5, Ergebnis ist die Note | 3, Regelstand ja, Bewerter ist der Erzeuger | 3, Note ohne Begründungspflicht |
| Gerd: Wächter kann rot werden | 4, Häufungsprüfung und Regelstand-Abstand testbar | 3, „Probe nicht gelaufen" ist prüfbar, sonst wenig | 2, Selbstbenennung der Verzerrung ist nicht prüfbar | 2 |
| Gerd: Bewerter fällt aus | 4, zweite Instanz | 3, Probe verzögert sich | 5, nichts fällt aus | 1, alles steht |
| Gerd: Noten nachträglich verschieben | 5, Bewertung im Repo, Kette | 5 | 2, derselbe kann alles ändern | 3 |
| **Summe** | **54** | **46** | **37** | **29** |

## 7. Fazit

**Empfehlung: A, mit zwei Auflagen aus B und einer aus C.**

1. **Aus B: Die Probe ist der Maßstab, die Note nur die Reihenfolge.** Ein Kandidat gilt erst
   als gut, wenn eine Probe gelaufen ist; bisher null. Jeder Kandidat über der Schwelle bekommt
   eine Probe unter 100 Euro und vier Wochen, und Thorstens Trefferquote der Vorhersagen ist
   die Zahl in seiner Probezeit.
2. **Aus B: Höchstens zwei Proben gleichzeitig**, weil sie den CEO brauchen.
3. **Aus C: Die Verzerrung wird je Lauf benannt, und ein Wächter zählt die Häufung**: Landen
   mehr als die Hälfte der zehn höchsten Werte in einem Feld, wird die Zeile rot, und Karl
   legt es donnerstags vor.

**Der Test, der die Entscheidung hält:** ein Wächter über `skills/gedaechtnis/thorsten.md`,
der je Note Bewerter, Regelstand (Commit von `FILTER.md`) und Feld verlangt und die drei
Bedingungen prüft: kein Bewerter gleich Erzeuger, kein Regelstand jünger als die Note, Häufung
unter der Schwelle. Gegenprobe je Bedingung.

**Offene Fragen, nur der CEO:**

- **Wer ist die fremde Instanz?** Empfehlung: dasselbe Verfahren wie bei Marv, ein frischer
  Lauf ohne Thorstens Gedächtnis, auf Sonnet. Optionen: (a) frische Instanz Sonnet; (b) Marv
  selbst als Bewerter; (c) der CEO stichprobenartig, jede vierte Note.
- **Anastasias Entscheidung zur Filterhoheit:** Empfehlung: zurücknehmen, Klasse Strategie.
  Optionen: (a) zurücknehmen; (b) Thorsten ändert, CEO kann donnerstags kippen; (c) belassen.
- **Der Brandschutzstrang:** Empfehlung: die vier Fassungen zu einer Zeile zusammenziehen und
  einmal blind benoten lassen. Optionen: (a) zusammenziehen; (b) alle vier stehen lassen;
  (c) alle vier parken, bis eine Probe aus einem anderen Feld gelaufen ist.

**Die eine Sache, die am ehesten noch falsch ist:** dass eine fremde Instanz unabhängig ist.
Sie kann dasselbe Modell mit denselben Kriterien sein und dieselben Neigungen haben. Deshalb
Auflage 1: Erst die Probe macht aus einer Note einen Beleg.

Nächster Schritt: Der CEO beantwortet die drei Fragen bis Donnerstag, 2026-09-17; Owner Tobias.
