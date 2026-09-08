# Befundnummern ohne Doppelvergabe — Ideen-Vergleich, Fassung C (Synthese)

Datum: 2026-09-08. Verfahren: `idee`, Fassung C. Zwei Vorschläge hinein, drei heraus.

## 1. Die Frage und das Ziel

**Frage:** Wie werden Gerds fortlaufende Befundnummern vergeben, damit Codex und Claude Code im selben Repo nie dieselbe Nummer für zwei verschiedene Befunde benutzen?

**Die Idee, wörtlich:**

> „Gerd soll seine Befundnummern nicht mehr aus der Datei ablesen, sondern es gibt eine kleine Sperrdatei NAECHSTE_NUMMER.txt im Repo. Wer eine Nummer braucht, liest sie, erhöht sie, committet sofort. Dann gibt es keine Doppelvergabe zwischen Codex und Claude mehr."

**Annahmen daneben** (nicht gemessen, aus der mitgegebenen Lage übernommen):

- Gerds Skill (Stand 08.09.2026) reserviert eine Nummer, indem die Kopfzeile in `REVIEW_GERD.md` zuerst geschrieben wird; bei Kollision behält der frühere Commit die Nummer.
- Codex und Claude Code arbeiten überwiegend nacheinander, gelegentlich parallel, gegen ein gemeinsames Git-Remote auf der NAS.
- Eine Befundnummer wird nach der Vergabe an vielen Stellen zitiert (`CLAUDE.md`, `AGENTS.md`, Nachweise, Tests) und ist damit faktisch unveränderlich.

**Messung.** Es wurde **nichts gemessen.** Der Auftrag verbietet den Zugriff auf Dateien außerhalb des Skill- und Ausgabeordners, also konnte weder die Häufigkeit der Vergabe noch die Zahl der Zitatstellen noch eine tatsächliche Kollision im Log nachgesehen werden. Was hier über Aufwand, Häufigkeit und Fehlerpfade steht, ist **geschätzt.** Die zwei Befehle, die das messbar machen würden, stehen unter Punkt 6.

## 2. Der Gegenvorschlag (B)

**Kein gemeinsamer Zähler.** Jeder Befund bekommt beim Anlegen eine dauerhafte, lokal erzeugbare Kennung, die keine Abstimmung braucht: Datum plus kurzer Hash-Anteil, `G-20260908-A3F`. Diese Kennung ist die endgültige und wird überall zitiert. Eine fortlaufende Nummer existiert nur noch als Anzeigereihenfolge in einem **erzeugten** Register und wird nirgends zitiert. Ein Test prüft zwei Eigenschaften: keine Kennung kommt doppelt vor, und jede zitierte Kennung existiert.

B ist an einer anderen Stelle einseitig als A: A optimiert die Ordnung (lückenlose, aussprechbare Zahlen) und zahlt mit Koordination; B optimiert die Koordinationsfreiheit und zahlt mit hässlichen, unsortierten Kennungen.

## 3. Die Zerlegung in zehn Bestandteile

Beschrieben, nicht benotet. Gewählt wird erst danach.

| # | Bestandteil | A — Sperrdatei `NAECHSTE_NUMMER.txt` | B — lokal erzeugte Kennung + erzeugtes Register |
|---|---|---|---|
| 1 | Ziel | Verhindert Doppelvergabe, indem die Reservierung aus der großen Datei in eine kleine, konfliktfreudige Datei wandert. Zwei Seiten kollidieren dann sichtbar am Push statt still im Text. | Macht Doppelvergabe strukturell unmöglich: zwei unabhängig erzeugte Kennungen sind nie gleich, es gibt nichts zu reservieren. |
| 2 | Zeit bis Nutzen | Wirkt, sobald die Datei liegt und beide Skills den Ablauf nennen. Jede einzelne Vergabe kostet aber einen Pull-Push-Zyklus, im Kollisionsfall zwei. | Wirkt ab der ersten Zeile; die Kennung entsteht offline, ohne Netz, ohne zweiten Commit. |
| 3 | Aufwand | Eine Datei, ein Absatz in Gerds Skill, eine Zeile in `CLAUDE.md`. Sehr klein. | Ein Generator (eine Funktion), ein Registerskript, ein Test über Eindeutigkeit und Auflösbarkeit. Klein, aber an drei Stellen. |
| 4 | Kosten | Laufend: je Befund ein zusätzlicher Commit, dessen Botschaft von nichts handelt, plus Push. | Einmalig beim Bau, danach null je Befund. |
| 5 | Risiko | Der gefährliche Pfad ist der abgekürzte: Wer liest und erhöht, aber vor dem Push abbricht oder den Schritt überspringt, vergibt still doppelt — und die Nummer ist danach unveränderlich. Der Ablauf hängt an Disziplin. | Der gefährliche Pfad ist die Migration: Bestehende `G-0NN`-Nummern sind überall zitiert, ein Umstieg schafft zwei Kennungswelten nebeneinander. |
| 6 | Rücknehmbarkeit | Vollständig: Datei löschen, alter Ablauf gilt wieder, keine vergebene Nummer sieht anders aus als vorher. | Praktisch nicht: einmal vergebene und zitierte `G-JJJJMMTT-XXX`-Kennungen bleiben im Bestand stehen, auch wenn man das Verfahren aufgibt. |
| 7 | Passung | Passt zum Bestand, weil er die vorhandene Nummernform unangetastet lässt. Passt schlecht zum Grundsatz, dass eine Zusicherung maschinell prüfbar sein muss: „wir committen sofort" ist Disziplin, und Disziplin gilt hier ausdrücklich als schwächste Absicherung. | Passt zum Grundsatz „Beleg statt Behauptung": Eindeutigkeit und Auflösbarkeit sind ein Test. Bricht dagegen mit der gewachsenen Nummernform, die in Regeltexten und Tests steht. |
| 8 | Messbarkeit | Beobachtbar ist nur der Gutfall. Eine stille Doppelvergabe fällt erst auf, wenn jemand zwei Befunde unter derselben Nummer liest. | Zwei Eigenschaften laufen jederzeit gegen den ganzen Bestand: keine Dublette, kein Zitat ins Leere. |
| 9 | Abhängigkeiten | Gemeinsames Remote erreichbar, beide Seiten online, Push-Reihenfolge trägt die Semantik. Fällt die NAS aus, fällt die Vergabe aus. | Nur die lokale Uhr und ein Zufallswert. Kein Netz, kein Remote, keine Reihenfolge. |
| 10 | Nebenwirkungen | Streut Reservierungs-Commits in die Historie, deren Beschreibung von nichts handelt — gegen die Regel, dass jeder Commit im Rumpf ein Warum trägt. Erzeugt außerdem Löcher: eine reservierte, nie benutzte Nummer bleibt für immer leer. | Verliert die Lesereihenfolge und die Aussprechbarkeit („die G-070er-Runde"). Das Register stellt beides wieder her, aber nur als Ansicht. |

## 4. Je Zeile eine Wahl

**Wer wählt:** eine fremde Instanz — ein Subagent, der Frage, Messung, beide Vorschläge als A und B und die zehn Bestandteile ohne Herkunftsangabe bekam. Er wusste nicht, welcher Vorschlag von wem stammt.

| # | Bestandteil | Wahl | Begründung der fremden Instanz (ein Satz) |
|---|---|---|---|
| 1 | Ziel | **B** | Doppelvergabe wird nicht verhindert, sondern strukturell unmöglich gemacht — das löst das Ziel vollständiger als ein Wettlauf, den man gewinnen muss. |
| 2 | Zeit bis Nutzen | **B** | Die Kennung entsteht lokal ohne Push, Pull oder zweiten Commit; A braucht im Kollisionsfall einen Wiederholungslauf. |
| 3 | Aufwand | **Gleichstand → A** | A ist eine Datei und eine Konvention, B ein Generator plus Prüftest — beides eine Sitzung, nur an verschiedenen Stellen. *(Nach Regel 4 des Verfahrens geht Gleichstand an den Auftraggeber.)* |
| 4 | Kosten | **B** | Laufende Kosten null, während A jeder Vergabe dauerhaft einen Commit und einen Push-Zyklus aufbürdet. |
| 5 | Risiko | **B** | A hat einen echten Fehlerpfad — wer liest und vor dem Push abbricht, vergibt still doppelt, und die Nummer ist danach unveränderlich; B kennt diesen Zustand nicht. |
| 6 | Rücknehmbarkeit | **A** | Eine fortlaufende Nummer bleibt lesbar und weiterführbar, wenn man das Verfahren aufgibt, während vergebene B-Kennungen überall zitiert und damit dauerhaft sind. |
| 7 | Passung | **B** | Das Projekt verlangt für jede Zusicherung einen maschinell prüfbaren Beleg, und B liefert genau den, während A seine Zusicherung an Disziplin und Reihenfolge hängt. |
| 8 | Messbarkeit | **B** | „Keine Kennung doppelt, jede zitierte existiert" läuft jederzeit gegen den ganzen Bestand; A kann nur den Gutfall beobachten. |
| 9 | Abhängigkeiten | **B** | A hängt an Remote, Push-Reihenfolge und Erreichbarkeit; B hängt an nichts außer der lokalen Uhr. |
| 10 | Nebenwirkungen | **strittig → A** | Die fremde Instanz schrieb „A", widersprach sich im selben Satz und begründete dann für B (A streue inhaltsleere Reservierungs-Commits, B verliere nur die Lesereihenfolge). **Die Wahl ist damit unbrauchbar und wird nicht geglättet**; sie zählt als Gleichstand und geht nach Regel 4 an den Auftraggeber. |

**Gesamtbild der fremden Instanz:** „B trägt. Es entfernt die Ursache statt sie zu verwalten, kennt keinen Zustand ‚still doppelt vergeben', und seine Zusicherung ist ein Test statt einer Disziplin." Mitzunehmen sei aus A, dass die Reihenfolge einen sichtbaren Ort braucht.

Stand: **B in sieben Punkten, A in drei** (davon zwei über die Gleichstandsregel). Genau die drei A-Punkte sind aber Aufwand, Rücknehmbarkeit und Nebenwirkungen — die drei, die über den *Umstieg* entscheiden, nicht über das Zielbild.

## 5. Der dritte Vorschlag (C)

**Die Nummer wird lokal vergeben und maschinell auf Eindeutigkeit geprüft; die Sperrdatei bleibt, aber sie sperrt nicht, sie zählt.**

Im Einzelnen:

1. **Die Kennung bleibt `G-NNN`.** Kein Formatwechsel, keine zwei Kennungswelten. `G-090` heißt weiter `G-090`.
2. **Vergeben wird ohne Reservierung.** Wer einen Befund anlegt, nimmt die nächste freie Nummer aus `NAECHSTE_NUMMER.txt` und **committet sie zusammen mit dem Befundtext** — ein Commit, nicht zwei. Kein vorgezogener Push, keine Reservierung, kein Zustand „Nummer gezogen, Befund fehlt".
3. **Kollisionen werden nicht verhindert, sondern erkannt und billig repariert.** Ein Test `test_befundnummern.py` prüft drei Eigenschaften über den ganzen Bestand: jede Nummer kommt genau einmal als Befundkopf vor, jede irgendwo zitierte Nummer hat einen Befundkopf, und `NAECHSTE_NUMMER.txt` ist größer als die höchste vergebene. Ein Merge, der zwei Befunde unter `G-091` zusammenführt, wird damit rot, statt still durchzugehen.
4. **Die Reparatur ist genau dann noch billig, wenn sie sofort kommt.** Weil Nummer und Text im selben Commit liegen, ist der jüngere der beiden Befunde vor dem Merge noch nirgends zitiert; er wird umnummeriert und das war es. Genau das ist die Regel aus Gerds bisherigem Skill — der frühere Commit behält die Nummer —, nur mit einem Test dahinter statt mit einem Blick.
5. **`NAECHSTE_NUMMER.txt` wird erzeugt, nicht gepflegt.** Ein Skript liest die höchste Kopfzeile und schreibt die nächste Zahl; dasselbe Skript ist der Test aus Punkt 3. Die Datei ist damit eine Ansicht auf den Bestand und keine zweite Wahrheit, die veralten kann.

| Teil von C | Herkunft |
|---|---|
| Nummernform `G-NNN` bleibt | A |
| `NAECHSTE_NUMMER.txt` als Ort der nächsten Zahl | A |
| Nummer und Befund in **einem** Commit, keine Vorabreservierung | **neu** — A und B vertragen sich hier nicht: A braucht die Reservierung, B braucht sie nicht, weil es keine Reihenfolge kennt. C behält die Reihenfolge und streicht die Reservierung, und das geht nur, indem der Konflikt in den Merge verlegt wird. |
| Test über Eindeutigkeit und Auflösbarkeit der Zitate | B |
| Vergabe braucht kein Netz und kein Remote | B |
| Die Datei wird erzeugt statt gepflegt | B |
| Bei Kollision behält der frühere Commit die Nummer | Gerds bisheriger Skill, unverändert übernommen |

**Was an C nicht glatt ist, und das bleibt so stehen:** C nimmt in Kauf, dass zwei parallel arbeitende Seiten dieselbe Nummer benutzen — es verspricht nur, dass es vor dem Zitieren auffällt. Wer A wörtlich nimmt („dann gibt es keine Doppelvergabe mehr"), bekommt das von C nicht. C behauptet etwas Schwächeres und Belegbareres: keine Doppelvergabe **überlebt einen Merge**.

## 6. Was weggefallen ist

| Weggefallen | Grund |
|---|---|
| Der vorgezogene Reservierungs-Commit aus A | Er ist die Quelle des einzigen stillen Fehlers, den A hat (gezogen, nicht gepusht), und erzeugt Commits ohne Warum sowie dauerhafte Nummernlöcher. |
| Der scheiternde Push als Kollisionssignal (A) | Er trägt nur, solange beide online sind und die Reihenfolge einhalten; ein Test trägt immer. |
| Das Kennungsformat `G-JJJJMMTT-XXX` aus B | Der Bruch mit dem Bestand kostet mehr als er einbringt: die alten Nummern stehen in Regeltexten, Nachweisen und Tests, und ein Umstieg schafft zwei Welten nebeneinander. |
| Das erzeugte Register mit Anzeigespalte aus B | Ohne Formatwechsel gibt es nichts zu registrieren — die Reihenfolge steckt schon in der Zahl. |
| Die Vollständigkeitsgarantie „keine Doppelvergabe, nie" aus A | Sie war nicht belegbar; C ersetzt sie durch eine schwächere Zusage mit Test. |

**Was an C am ehesten noch falsch ist:** die Annahme, dass ein Befund nie zwischen seinem Commit und dem Merge zitiert wird. Sie stimmt für den Normalfall — Gerd schreibt den Befund, dann folgen Korrektur und Regel —, aber genau die Reihenfolge dieses Projekts (Befund korrigieren, Regel in `CLAUDE.md` ergänzen, Antwort nach `REVIEW_ANTWORTEN.md`, **alles im selben Commit**) macht das Zitat gleichzeitig mit dem Befund. Dann ist die Umnummerierung kein Einzeiler mehr, sondern drei Dateien. Das ist prüfbar und nicht geraten worden:

```bash
git log --oneline --all -S'G-0' -- REVIEW_GERD.md | wc -l   # wie oft überhaupt vergeben
git log --format=%H --all -- REVIEW_GERD.md | while read c; do git show --stat $c | grep -c CLAUDE.md; done
```

Der erste Befehl sagt, wie oft das Verfahren je gebraucht wurde; der zweite, ob Befund und Zitat wirklich zusammen committet werden. Bei einer sehr kleinen ersten Zahl trägt A auch ohne Test, und C wäre Aufwand für ein Problem, das dreimal im Jahr auftritt.

**Keine Entscheidung.** Tobias entscheidet, ob C gebaut wird, A bleibt oder B kommt.
