# Bewertung der drei Fassungen von /idee, Runde 1 (2026-09-08)

Drei Fassungen (`gericht/`, `sparring/`, `synthese/`) und ein Lauf ohne Skill, je Prüffall durch fremde Instanzen auf Opus bearbeitet, je Fall ein fremder Bewerter gegen 32 vorab feste Kriterien. Arbeitsbereich: `~/.claude/skills/idee-workspace/iteration-1/`.

| Fall | Gericht | Sparring | Synthese | ohne Skill |
|---|---|---|---|---|
| 1 Scans vom iPhone in iCloud | 9/12 · 94k · 283s | 5/12 · 88k · 136s | 9/12 · 94k · 244s | 5/12 · 88k · 125s |
| 2 Morgenbericht per Telegram | 10/10 · 95k · 253s | 6/10 · 87k · 117s | 8/10 · 92k · 227s | 4/10 · 85k · 73s |
| 3 Befundnummern per Sperrdatei | 9/10 · 97k · 263s | 5/10 · 88k · 145s | 7/10 · 95k · 290s | 6/10 · 86k · 84s |
| **Summe** | **28/32** | **16/32** | **24/32** | **15/32** |

## Was die Zahlen sagen

Das Gericht gewinnt, weil es als einzige Fassung die zehn Punkte nachweislich vor die Vorschläge legt, die Länge hält und die Messung mit Herkunftsspalte führt. Die Synthese ist inhaltlich die reichste und verliert an einer Regel: Ihr dritter Vorschlag C ist ein Kompromiss, und C wurde nie blind bewertet. Das Sparring trifft in allen drei Fällen den Kern am schärfsten („Serialisierung beim push, nicht beim commit") und zahlt für die Kürze mit fehlenden Begründungen, fehlendem Test und fehlender Rückgabe der Entscheidung. Ohne Skill entstehen die sachlich stärksten Zerlegungen (garantierter Merge-Konflikt je Befund), aber kein Verfahren: keine Frage, kein benannter Bewerter, ein „10:0" für den eigenen Vorschlag, und das Fazit zieht die Entscheidung an sich.

## Zwei Befunde, die alle Fassungen teilen

**Keine Fassung stellte die zehn Punkte vor den Gegenvorschlag** (Fall 1: 0 von 4; Fall 2 und 3: nur das Gericht). Drei Anleitungen verlangten es. Die Antwort ist nicht eine deutlichere Bitte, sondern die Gliederung: In der Endfassung sind die Punkte Abschnitt 3 der Ausgabe, die Vorschläge Abschnitt 4 und 5.

**Drei von vier bauten den Gegenvorschlag als „Idee plus Sicherungen"** (Fall 1). Das ist eine Verbesserung, keine Alternative, und sie gewinnt dann zwangsläufig. Nur das Sparring setzte einen echten Gegenentwurf. Die Regel dazu stammt aus dem Sparring: das Gegenteil an der Stelle, an der die Idee am meisten voraussetzt.

## Was übernommen wurde

| Aus | Übernommen |
|---|---|
| Gericht | Grundgerüst; Idee in ganze Sätze ausfalten (macht das Längenkriterium erst erfüllbar); Messtabelle mit Herkunft und „nicht gemessen"-Zeilen; blinde fremde Instanz mit gewürfelter Reihenfolge; „Zustände, keine Eigenschaften" für Punkte, die eine offene Entscheidung heilt |
| Sparring | Gegenvorschlag als Gegenteil an der teuersten Voraussetzung; Stern für knappe Selbstsiege |
| Synthese | fester Schlusssatz „Keine Entscheidung. Tobias entscheidet."; Übernahmetabelle mit Herkunft; strittiges Urteil stehen lassen statt glätten; die eigene Zusage abschwächen, wo sie nicht belegbar ist |
| ohne Skill | Bruchstellenprüfung (was passiert bei stillem Ausfall, woran merkt man es); der eine Messwert, der den Vorsprung aufheben würde |

## Was nicht übernommen wurde

Der dritte Vorschlag C der Synthese, weil er die Regel „zwei hinein, zwei heraus" bricht und nie bewertet wurde; sein Nutzen steckt jetzt in der Übernahmetabelle. Die Ja-Nein-Fragen des Sparrings, weil sie in Fall 3 eine Zelle ohne Begründung ließen und „nichts tun" strukturell bevorteilen. Die Gleichstandsregel der Synthese („Gleichstand geht an den Auftraggeber"), weil sie eine Höflichkeit als Regel verkleidet; ein Gleichstand ist ein Gleichstand.

## Kritik an den Kriterien (für Runde 2)

Kriterium 4 (Länge) nennt weder Einheit noch Bezugstext; ob „die Idee" das Zitat oder die ausgefaltete Fassung ist, entscheidet über das Ergebnis. Es steht in Spannung zu Kriterium 2 (wörtlich wiedergeben). Kriterium 10 (keine Entscheidung) besteht faktisch immer, wenn nur der Ausgabeordner sichtbar ist. Kriterium 7 wertet unbenannte Selbstbewertung und blinde Fremdbewertung gleich. Fall 3 Kriterium 4 bündelt zwei Fehlerbilder (Race und Merge-Konflikt) zu einem Alles-oder-nichts-Punkt.

## Grenzen

Ein Lauf je Fall und Fassung. Bewerter sind Modelle. Fälle sind erfunden, tragen aber echte Lage. Alle Läufe hatten keinen Zugriff auf Projektdateien; die Messung war überall „nicht gemessen". Die Endfassung ist die Synthese aus dieser Runde und noch nicht selbst gemessen.
