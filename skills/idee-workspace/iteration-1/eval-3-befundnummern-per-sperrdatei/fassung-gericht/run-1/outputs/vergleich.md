# Ideen-Vergleich: Befundnummern ohne Doppelvergabe

Fassung A (das Gericht), 08.09.2026.

## Die Frage hinter der Idee

**Frage:** Wie wird verhindert, dass Codex und Claude Code, die abwechselnd im selben Git-Repo mit Remote auf der NAS arbeiten, dieselbe Befundnummer doppelt vergeben — ohne dass die Nummernvergabe selbst zur Fehlerquelle wird?

**Die Idee, wörtlich in ganze Sätze gebracht:** Gerd soll seine Befundnummern nicht mehr aus der Datei ablesen. Stattdessen gibt es eine kleine Sperrdatei `NAECHSTE_NUMMER.txt` im Repo. Wer eine Nummer braucht, liest sie, erhöht sie und committet sofort. Damit gibt es keine Doppelvergabe zwischen Codex und Claude mehr.

**Annahmen, die die Idee voraussetzt und nicht sagt:**

- Dass „committet sofort" auch „pusht sofort" heißt — ein lokaler Commit reserviert gegenüber der anderen Seite nichts.
- Dass beide Bearbeiter online sind und das NAS-Remote im Moment der Vergabe erreichbar ist.
- Dass die Nummer vor der Befundarbeit gezogen wird, nicht danach.
- Dass eine gezogene und dann verworfene Nummer als Lücke akzeptabel ist.
- Dass Git bei zwei Änderungen derselben Zeile nicht stillschweigend zusammenführt (trifft zu, aber nur beim Push, nicht bei getrennten lokalen Ständen).

**Widerspruch zu einer bestehenden Entscheidung:** Ja, ein weicher. Das Projekt hält als Konvention „die Nachrichten-Id ist eine Ableitung, keine Sequenz" und behandelt geteilten veränderlichen Zustand als Kollisionsquelle. Die Sperrdatei führt genau eine zentrale Sequenz und geteilten Zustand ein. Das ist kein Verbot, aber es gehört in den ersten Absatz.

**Eine Frage an Tobias, mit Empfehlung:** Ist überhaupt schon einmal eine Nummer doppelt vergeben worden, oder ist das ein befürchteter Fall? Empfehlung: Wenn es noch nie passiert ist, ist die billigere der beiden Lösungen die richtige.

## Messung

| Was | Wert | Herkunft |
|---|---|---|
| Heutiges Verfahren | Nummer gilt als reserviert, sobald die Kopfzeile in `REVIEW_GERD.md` steht; bei Kollision behält der frühere Commit die Nummer | Auftragslage, Gerds Skill Stand 08.09.2026 |
| Bearbeiter | Codex und Claude Code, abwechselnd, gelegentlich parallel | Auftragslage |
| Ablageort | ein Git-Repo, Remote auf der NAS | Auftragslage |
| Zitierstellen einer Befundnummer | Regeltexte, Commit-Botschaften, Testnamen, Nachweisdateien | Auftragslage |
| Bisherige Doppelvergaben | **nicht gemessen** | — |
| Kosten beider Vorschläge | 0 € einmalig, 0 € monatlich | geschätzt, keine Anschaffung vorgesehen |
| Aufwandsangaben | eine Stunde bzw. eine halbe Stunde | **geschätzt** |

Nicht messbar in diesem Lauf: Der Auftrag verbietet den Zugriff auf das Repo. Es wurde also **nichts am lebenden Bestand nachgesehen** — weder die tatsächliche höchste Befundnummer noch die Commit-Historie auf frühere Kollisionen. Beide Vorschläge arbeiten mit denselben Tatsachen aus der Auftragslage.

## Die zehn Punkte

Standardliste des Verfahrens, unverändert übernommen, festgelegt vor dem Schreiben des Gegenvorschlags: Ziel, Zeit bis Nutzen, Aufwand, Kosten, Risiko, Rücknehmbarkeit, Passung, Messbarkeit, Abhängigkeiten, Nebenwirkungen.

## Vorschlag A — Befundnummer als Ableitung statt als Sequenz

**Ort:** Das Nummernformat selbst, dokumentiert in Gerds Skill und in der Regeldatei. Kein neuer Zustand im Repo.

**Ablauf:** Ein Befund heißt künftig `G-<JJJJMMTT>-<KÜRZEL><lfd>`, also `G-20260908-CC1` (Claude Code, erster Befund des Tages) oder `G-20260908-CX1` (Codex). Datum und Kürzel kennt jeder Bearbeiter aus sich selbst; die laufende Ziffer zählt nur die eigenen Befunde des eigenen Tages. Zwei Bearbeiter können denselben Namen nie erzeugen, weil das Kürzel verschieden ist. Alte Nummern `G-001`…`G-0xx` bleiben gültig und werden nie umgeschrieben; das neue Format gilt ab Einführungstag.

**Absicherung:** Ein Test läuft über Regeldatei und Reviewdatei, sammelt alle Befundkennungen und schlägt fehl, wenn eine zweimal mit verschiedenem Inhalt vorkommt oder dem Muster nicht entspricht — mit Gegenprobe an einer künstlich doppelten Kennung.

**Kosten:** keine. **Aufwand:** einmalig geschätzt eine Stunde, laufend null.

**Risiko:** Die Kennung wird länger und ist im Gespräch unhandlich. Zwei Formate stehen nebeneinander. Ein verwechseltes Kürzel erzeugt eine falsche, aber keine doppelte Kennung.

**Rücknahme:** Format zurückstellen, Test entfernen; vergebene Kennungen bleiben gültig, weil sie ohnehin eindeutig sind.

## Vorschlag B — Sperrdatei `NAECHSTE_NUMMER.txt` im Repo

**Ort:** Eine kleine versionierte Datei im Repo-Wurzelverzeichnis.

**Ablauf:** Wer eine Befundnummer braucht, zieht den aktuellen Stand vom Remote, liest die Zahl, erhöht sie um eins, schreibt sie zurück und committet und pusht diesen Einzeiler sofort — vor der eigentlichen Befundarbeit. Wessen Push zuerst durchgeht, hat die Nummer; der andere bekommt eine Ablehnung, zieht neu, liest die erhöhte Zahl und wiederholt.

**Absicherung:** Der Push selbst, weil Git zwei Änderungen derselben Zeile nicht stillschweigend zusammenführt.

**Kosten:** keine. **Aufwand:** einmalig geschätzt eine halbe Stunde, laufend ein zusätzlicher Commit und Push je Befund.

**Risiko:** Der Ablauf greift nur bei sofortigem Push; wer offline oder in einem längeren Block ohne Push arbeitet, hat nicht reserviert. Das Repo bekommt eine Kette kurzer Commits ohne Inhalt. Eine gezogene und verworfene Nummer hinterlässt eine Lücke.

**Rücknahme:** Datei stehen lassen oder entfernen, Ablauf aus den Skilltexten streichen; Minuten.

## Bewertung

**Bewertet von einer fremden Instanz** — einem eigenen Lauf, der nur Frage, Messung, beide Vorschläge als A und B und die zehn Punkte bekam, ohne Herkunftsangabe und ohne Zugriff auf diese Datei.

| # | Punkt | A | Grund | B | Grund |
|---|---|---|---|---|---|
| 1 | Ziel | 5 | Die Kollision ist strukturell ausgeschlossen, weil das Bearbeiterkürzel im Namen steckt und niemand den Namensraum eines anderen betreten kann. | 3 | Die Sperre wirkt nur, wenn jeder Bearbeiter sie diszipliniert und sofort bedient — genau die Disziplin, die dieses Projekt anderswo als schwächste Absicherung einstuft. |
| 2 | Zeit bis Nutzen | 5 | Wirkt mit dem ersten Befund nach Einführungstag, ohne Vorlauf oder Migration. | 4 | Wirkt ebenfalls sofort, aber erst nachdem beide Skilltexte geändert und von beiden Seiten gelesen sind. |
| 3 | Aufwand | 4 | Eine Stunde einmalig inklusive Test und Gegenprobe, laufend nichts. | 3 | Eine halbe Stunde einmalig, dafür laufend ein Zieh-Commit-Push je Befund — der Aufwand wandert in den Dauerbetrieb. |
| 4 | Kosten | 5 | Kein Geld, weder einmalig noch monatlich. | 5 | Kein Geld, weder einmalig noch monatlich. |
| 5 | Risiko | 4 | Schlimmster Fall ist ein falsches Kürzel — eine falsche, aber eindeutige Kennung, billig zu korrigieren. | 2 | Der Fehlerfall ist genau der, den die Frage ausschließen will: wer offline oder in einem langen Block arbeitet, hat nicht reserviert und kollidiert trotzdem — die Nummernvergabe wird selbst zur Fehlerquelle. |
| 6 | Rücknehmbarkeit | 5 | Format zurückstellen, Test entfernen; vergebene Kennungen bleiben gültig, weil sie ohnehin eindeutig sind. | 4 | Ablauf aus den Skilltexten streichen in Minuten, die Datei bleibt als versionierter Rest mit ihren Lückenzahlen stehen. |
| 7 | Passung | 5 | Trifft die Hausregel „Ableitung statt Sequenz" wörtlich und ist rein additiv, alte Nummern werden nie umgeschrieben. | 2 | Führt eine zentrale Sequenz plus gemeinsamen Zustand ein — das Gegenteil der Idempotenzkonvention — und der Push als „Absicherung" hat keinen Test, der ihn prüfen kann. |
| 8 | Messbarkeit | 5 | Der Test über Regel- und Reviewdatei mit Gegenprobe sagt in vier Wochen mechanisch, ob eine Kennung doppelt oder formwidrig ist. | 2 | Messbar wäre nur eine Lückenstatistik der Datei; ob jemand die Nummer ohne Ziehen vergeben hat, sieht man nirgends. |
| 9 | Abhängigkeiten | 5 | Braucht nur Datum und eigenes Kürzel, beides kennt jeder Bearbeiter aus sich selbst — kein Netz, kein Remote, kein Zustand. | 2 | Setzt erreichbares NAS-Remote, sofortiges Pushen und die Mitwirkung beider Seiten bei jedem einzelnen Befund voraus. |
| 10 | Nebenwirkungen | 3 | Zwei Nummernformate nebeneinander und längere, im Gespräch unhandliche Kennungen. | 3 | Eine Kette inhaltsloser Commits verrauscht die Historie, und Lücken in der Folge laden zu Fehldeutungen ein. |
| | **Summe** | **46** | | **30** | |

**Gesamturteil der fremden Instanz:** A gewinnt deutlich, und der Abstand liegt nicht in der Bequemlichkeit, sondern in den Punkten 5, 7, 8 und 9: A macht die Doppelvergabe strukturell unmöglich und prüfbar, B macht sie nur unwahrscheinlich und öffnet dafür einen neuen Fehlerweg — genau das, was die Frage im Nebensatz verbietet. Die Summe täuscht nicht, sie untertreibt eher. Aus B gehört ein Gedanke in A: dass die Vergabe im Repo sichtbare Spuren hinterlassen soll — der Test sollte deshalb auch prüfen, dass jedes Kürzel zu einem bekannten Bearbeiter gehört. Die unhandliche Länge von A lässt sich entschärfen, indem im Gespräch der Kurzteil genügt und nur der Schriftverkehr die volle Kennung führt.

## Fazit

**Auflösung:** **B war Tobias' Idee** (die Sperrdatei), **A der Gegenvorschlag** (die abgeleitete Kennung).

Der Gegenvorschlag gewinnt, und zwar an der Stelle, an der die Idee ihr eigenes Versprechen nicht ganz einlöst: Die Sperrdatei verhindert die Doppelvergabe nur, solange sofort gepusht wird — sie ersetzt eine Kollisionsquelle durch eine Disziplinbedingung, während die abgeleitete Kennung die Kollision unmöglich macht, ohne dass jemand etwas tun muss. Der zweite Abstand ist die Prüfbarkeit: Die Sperrdatei hat keinen Test, der ihr Versagen bemerken würde, die Kennung hat einen mit Gegenprobe. Die Summe von 46 zu 30 stimmt in der Richtung, überzeichnet aber den Vorsprung etwas, weil vier der zehn Punkte (Kosten, Zeit, Rücknahme, Nebenwirkungen) beide Vorschläge kaum unterscheiden.

**Was aus der Idee mitkommt:** Ihr Kern ist richtig und bleibt — die Nummer wird **vor** der Arbeit festgelegt und nicht nachträglich aus dem Bestand abgelesen; genau das ist der Fehler des heutigen Verfahrens. Zweitens ihr Anspruch, dass die Vergabe eine sichtbare Spur im Repo hinterlässt: Das erledigt beim Gegenvorschlag der Test, der jedes Kürzel gegen die Liste der bekannten Bearbeiter hält, damit ein vertauschtes Kürzel auffällt statt still durchzugehen. Drittens die Beobachtung, die die Idee überhaupt ausgelöst hat: dass „wer zuerst committet, behält die Nummer" eine Regel für den Konfliktfall ist und keine Vermeidung.

**Was daran am ehesten noch falsch ist:** Dass das Problem die Mühe lohnt. Es ist nicht gemessen, ob je eine Nummer doppelt vergeben wurde — und wenn nicht, ist auch der Gegenvorschlag eine Stunde Arbeit gegen einen Fall, den es nicht gibt. Der zweite Zweifel: Zwei Nummernformate nebeneinander sind dauerhaft, und ein Regelwerk, das seine eigenen Befunde in zwei Sprachen zitiert, ist schlechter lesbar — das könnte teurer sein, als es in Punkt 10 aussieht.

Keine Entscheidung; die trifft Tobias.
