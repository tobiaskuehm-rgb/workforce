# 3-Loop: Reviewabstand und Rollengrenze

Vorgelegt von Anastasia (`PEO-001`) am 2026-09-08. Entscheider: der CEO.

## 1. Die Frage

In welchem Abstand und in welcher Form wird jede Identität geprüft, einschließlich der
Frage, ob sie ihre Rollengrenze eingehalten hat?

Randbedingungen, schon entschieden und hier nicht neu verhandelt: Marv ist Mitarbeiter und
Anastasia unterstellt (Chat 2026-09-08). Der CFO wird erst im Oktober gebraucht. Die
Kontrolle über Anastasia ist der CEO selbst. Rollenüberschreitung zu überwachen ist Teil von
Anastasias Auftrag.

## 2. Gemessen, nicht gemeint

Befehl: `git log` je Skillordner, Zählung der Prüffälle aus `evals.json`, Stand 2026-09-08.

| Identität | angelegt | Alter | Commits am Skill | Commits mit ihrem Namen | Prüffälle |
|---|---|---|---|---|---|
| Karl | 2026-09-06 | 2 Tage | 6 | 6 | 6 |
| Marlene | 2026-09-06 | 2 Tage | 13 | 9 | 6 |
| Thorsten | 2026-09-06 | 2 Tage | 4 | 1 | 4 |
| Anastasia | 2026-09-06 | 2 Tage | 5 | 8 | 4 |
| CFO (Wolle) | 2026-09-06 | 2 Tage | 4 | 0 | 0 |
| Marv | 2026-09-06 | 2 Tage | 7 | 2 | 4 |
| Gerd | 2026-09-06 | 2 Tage | 4 | 20 | 4 |

Drei Ablesungen, die die Frage prägen:

- **Alle sieben sind gleich alt.** Ein Kalenderabstand ab Anlage lässt alle am selben Tag
  fällig werden. Sieben Reviews an einem Tag wird niemand machen.
- **Die Nutzung ist extrem ungleich.** Gerd erscheint in zwanzig Commits, der CFO in keinem.
  Ein fester Abstand prüft den, der noch nie gearbeitet hat, und verpasst den, der täglich
  arbeitet.
- **Nur Marlene hat eine Probezeitakte.** Prüffälle haben inzwischen sechs von sieben;
  gemessen im Sinne eines Vorher-Nachher-Vergleichs sind bisher nur Karl und Marv.

Nicht gemessen: die Zahl der tatsächlichen Aufrufe je Identität. Es gibt keinen Zähler.
Commits sind ein Ersatzmaß und zählen nur, was Spuren im Repo hinterlässt.

## 3. Die drei Sichten, vorher festgelegt

Simulierte Sichten. Gerd und Marv können ihre im eigenen Lauf kippen.

**Sicht Tobias (Alltag).** T1 Wie viel Zeit kostet ihn ein Zyklus? T2 Muss er den Termin
selbst im Kopf haben? T3 Erfährt er etwas, das er nicht schon weiß? T4 Was passiert, wenn er
zwei Wochen nicht reagiert?

**Sicht Anastasia (Fachstelle).** A1 Trägt es bei sieben Identitäten und wächst es mit? A2
Liegt am Ende ein Nachweis vor oder ein Eindruck? A3 Entdeckt es eine Rollenüberschreitung?
A4 Behandelt es fehlendes Werkzeug getrennt von fehlender Leistung?

**Sicht Gerd (Prüfer).** G1 Gibt es einen Zustand, in dem dieses Verfahren rot wird? G2 Was
passiert, wenn es einmal ausfällt? G3 Ist die Auslösung beobachtbar oder Erinnerungssache?
G4 Wer prüft den Prüfer?

## 4. Vorschlag A: fester Abstand

Der Vorschlag des Auftraggebers, aus der Frage „Abstand x Tage" ausformuliert.

- **Ort:** ein Termin je Identität, geführt von Anastasia.
- **Ablauf:** alle 30 Tage ein Review je Identität, mit Nachweisen aus dem Zeitraum.
- **Kosten:** sieben Reviews je Monat, bei Wachstum linear mehr.
- **Aufwand CEO:** liest sieben Berichte, entscheidet, was offen ist.
- **Risiko:** Termine ohne Stoff. Wer im Zeitraum nicht gearbeitet hat, wird trotzdem geprüft.

Annahme, die A nicht ausspricht: dass Arbeit gleichmäßig über die Zeit anfällt. Die Messung
oben widerspricht dem.

## 5. Vorschlag B: Auslöser statt Termin

Das Gegenteil an der teuersten Stelle, nämlich am Kalender.

- **Ort:** derselbe, aber ohne Datum.
- **Ablauf:** ein Review wird fällig nach dem dritten abgeschlossenen echten Vorgang einer
  Identität, oder sofort bei einem Vorfall (Fehler mit Wirkung, Rollenüberschreitung, Ablehnung
  eines Auftrags).
- **Kosten:** nur dort, wo gearbeitet wurde. Der CFO kostet bis Oktober nichts.
- **Aufwand CEO:** unregelmäßig, dafür immer mit Stoff.
- **Risiko:** Eine Identität ohne Vorgänge wird nie geprüft. Und „echter Vorgang" ist heute
  nicht gezählt.

## 6. Vorschlag C: das Review ist der Prüffalllauf

Dasselbe Ziel mit dem, was schon da ist.

- **Ort:** Marvs Prüffälle, die für sechs von sieben Identitäten bereits liegen.
- **Ablauf:** Bei jeder Änderung an einer Skilldatei laufen ihre Prüffälle, dazu eine
  Grenzprüfung gegen den Abschnitt „Grenzen". Das Ergebnis ist das Review.
- **Kosten:** ein Lauf je Änderung, kein Kalender.
- **Aufwand CEO:** liest ein Ergebnis, keinen Bericht.
- **Risiko:** Es misst den Text, nicht die Arbeit. Eine Identität, deren Skill unverändert
  bleibt und die schlecht arbeitet, fällt nicht auf.

## 7. Vorschlag D: zwei Zustände, ein Review

Die einfachste Form, die noch alles erfüllt.

- **Ort:** die Probezeitakte, die es für Marlene schon gibt.
- **Ablauf:** Jede Identität hat genau zwei Zustände, Probezeit und Regelbetrieb. Es gibt
  genau ein Review, beim Übergang, mit Nachweisen. Danach nur noch bei Vorfall.
- **Kosten:** einmalig je Identität.
- **Aufwand CEO:** sieben Entscheidungen insgesamt, dann Ruhe.
- **Risiko:** Nach dem Übergang schaut niemand mehr hin. Verschlechterung fällt erst als
  Schaden auf.

## 8. Die Matrix

Note 1 bis 5, höher ist besser. Je Note ein Grund.

| Frage | A fester Abstand | B Auslöser | C Prüffalllauf | D zwei Zustände |
|---|---|---|---|---|
| T1 Zeit je Zyklus | 2 — sieben Berichte im Monat, auch ohne Stoff | 4 — nur wo gearbeitet wurde | 5 — ein Lauf, kein Bericht | 5 — einmalig |
| T2 Termin im Kopf | 3 — Anastasia führt ihn, er nicht | 4 — kommt von selbst, wenn Arbeit anfällt | 4 — hängt an seiner Änderung | 5 — kein Termin |
| T3 Neuigkeitswert | 2 — bei Nichtarbeit steht nichts drin | 5 — es gibt immer einen Anlass | 3 — sagt etwas über den Text, nicht die Lage | 3 — einmal viel, danach nichts |
| T4 Zwei Wochen keine Reaktion | 3 — Termin verstreicht, Stau wächst | 4 — Vorgang bleibt offen, kein Stau | 4 — Lauf ist schon gemacht | 2 — Übergang hängt, Identität bleibt in Probezeit |
| A1 Trägt bei sieben und wächst | 2 — wächst linear, kippt bei zwölf | 4 — wächst mit der Arbeit, nicht der Zahl | 5 — Marv läuft ohnehin | 4 — konstant klein |
| A2 Nachweis oder Eindruck | 4 — Nachweise sind vorgeschrieben | 4 — Vorgang ist der Nachweis | 5 — Trefferquote ist eine Zahl | 4 — wie bei Marlene belegt |
| A3 Entdeckt Rollenüberschreitung | 2 — nur was im Bericht landet | 3 — nur wenn sie als Vorfall gemeldet wird | 4 — Grenzprüfung ist Teil des Laufs | 2 — nach dem Übergang nie |
| A4 Werkzeug gegen Leistung getrennt | 4 — die vier Trennungen sind vorgeschrieben | 4 — am konkreten Vorgang gut erkennbar | 2 — ein Prüffall unterscheidet das nicht | 4 — wie A |
| G1 Kann rot werden | 3 — nur wenn jemand schreibt | 3 — hängt am Melden des Vorfalls | 5 — Lauf ist rot oder grün | 2 — einmal, dann nie wieder |
| G2 Ausfall des Verfahrens | 2 — ein verpasster Termin fällt nicht auf | 3 — ein nicht gemeldeter Vorfall fällt nicht auf | 4 — ein ausgefallener Lauf fällt auf | 2 — Ausfall ist der Normalzustand |
| G3 Auslösung beobachtbar | 2 — Erinnerungssache | 2 — „dritter Vorgang" wird heute nicht gezählt | 5 — die Änderung ist im Repo sichtbar | 3 — der Übergang ist ein Ereignis |
| G4 Wer prüft den Prüfer | 3 — CEO, wie entschieden | 3 — CEO | 3 — Marv prüft, Anastasia führt, CEO liest | 3 — CEO |
| **Summe** | **32** | **43** | **49** | **39** |

## 9. Fazit

**Empfehlung: B, mit drei Auflagen aus C, A und D.** Die Summe führt C, das Fazit
widerspricht ihr, und zwar aus einem Grund: C misst den Skilltext, nicht die Arbeit. Eine
Identität, deren Datei unverändert bleibt und die schlecht arbeitet, wird von C nie geprüft.
Das ist genau der Fall, für den ein Review da ist. C ist das beste Instrument und das falsche
Verfahren.

Die drei Auflagen:

1. **Aus C:** Der Prüffalllauf ist das Instrument des Reviews, nicht sein Ersatz. Wer geprüft
   wird, wird gegen seine Prüffälle gemessen, damit am Ende eine Zahl steht und kein Eindruck.
   Die Grenzprüfung gegen den Abschnitt „Grenzen" läuft mit.
2. **Aus A:** Ein Deckel gegen das Vergessen. Wer neunzig Tage ohne Auslöser bleibt, bekommt
   ein kurzes Review trotzdem, mit dem einen Satz, dass nichts anlag. Das schließt Bs größte
   Lücke, ohne den Kalender zurückzuholen.
3. **Aus D:** Nur zwei Zustände. Probezeit und Regelbetrieb, kein drittes Etikett. Das hält
   die Akte lesbar.

**Rollengrenze.** Sie wird an drei Stellen geprüft, weil keine allein trägt: im Prüffalllauf
gegen den Grenzabschnitt, in jedem Review als eigener Punkt, und laufend durch Selbstmeldung
plus den CEO. Für die Selbstmeldung gilt die Einschränkung ausdrücklich: Wer überschreitet,
merkt es meist nicht, sonst hätte er es nicht getan. Sie ist eine Ergänzung, kein Wächter.

**Fragen an den CEO.**

1. **Wie viele abgeschlossene Vorgänge lösen ein Review aus?** Empfehlung drei. Optionen: drei
   (früh genug für eine Korrektur), fünf (weniger Aufwand, späteres Signal), oder einer für die
   erste Runde jeder neuen Identität.
2. **Gilt der Neunzig-Tage-Deckel auch in der Probezeit?** Empfehlung nein, dort dreißig Tage,
   weil eine Probezeit einen Endpunkt braucht. Optionen: dreißig, sechzig, oder gar kein Deckel
   in der Probezeit.
3. **Wer schließt eine Probezeit ab?** Empfehlung: du, auf meine Vorlage, mit einer
   Entscheidungsnummer. Optionen: du allein, du auf Vorlage, oder Karl entscheidet für alle
   außer sich selbst.

**Was am ehesten falsch ist.** Der Auslöser. „Drei abgeschlossene Vorgänge" setzt voraus, dass
irgendwo gezählt wird, was ein abgeschlossener Vorgang ist. Heute zählt das niemand. Marlene
führt ihre Vorgänge selbst, die anderen führen gar keine. Wird dieser Zähler nicht gebaut,
verfällt B still auf den Neunzig-Tage-Deckel, und dann ist es Vorschlag A mit einem längeren
Abstand. Das ist die Stelle, an der dieser Loop kippt.
