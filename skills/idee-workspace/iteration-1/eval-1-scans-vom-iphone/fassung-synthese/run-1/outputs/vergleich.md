# Ideen-Vergleich, Fassung C (Synthese): Scans vom iPhone

Datum: 2026-09-08. Verfahren: `idee-synthese`. Zwei Vorschläge hinein, drei heraus.

## 1. Die Frage und das Ziel

**Frage:** Wie kommen künftig gescannte private Dokumente zu Marlene, die sie ablegt?
**Ziel:** Ein Weg herein, auf dem keine Datei verloren geht und keine halbe Datei gelesen wird.

**Die Idee, wörtlich (Tobias, 2026-09-08):**
> „Alle Scans mache ich künftig mit dem iPhone und die landen direkt in einem Ordner Eingang in iCloud, Marlene holt sie sich von da. Den Scanner am Mac schaffe ich ab."

**Bekannte Lage:**
- Heute liefern zwei Scanner in zwei Ordner; einer liegt auf der NAS, auf die Marlene nur lesend zugreift (Entscheidung 07.09.2026).
- Marlene liest lokal auf dem Mac und braucht jede Datei vollständig.
- Das Ablagekonzept vom 07.09.2026 sieht iCloud als Eingang bereits vor; die Entscheidung dazu ist **offen**.

**Annahmen (nicht gemessen):**
- Der iCloud-Ordner ist auf dem Mac als Ordner sichtbar und wird von iCloud Drive synchronisiert.
- „Optimierung des Mac-Speichers" ist aktiv, also können Dateien als Platzhalter (`.icloud`) vorliegen, bevor sie ganz da sind.
- Der Papierdurchsatz ist niedrig genug, dass Einzelblatt-Erfassung am iPhone tragbar wäre.

**Messungen — nicht gemessen.** Auszuführen wären:
```bash
# Liegen Platzhalter statt fertiger Dateien im Eingang?
find ~/Library/Mobile\ Documents/com~apple~CloudDocs/Eingang -name '*.icloud' | head
# Wie oft und wie groß kommt heute etwas herein (Durchsatz, Seitenzahl)?
ls -lT <heutiger-Scanordner-Mac>; ls -lT <NAS-Scanordner>
# Wie lange braucht eine typische Datei vom Ablegen bis "vollständig"?
brctl log --wait --shorten   # während eines Testscans
```
Alle Zahlen unten sind **Schätzungen**, keine Messwerte.

## 2. Der Gegenvorschlag (B)

Marlenes Eingang bleibt ein **lokaler Ordner auf dem Mac** und ist die einzige Schnittstelle, die sie kennt. iCloud ist dann **Transportweg, nicht Eingang**: Ein kleiner Übergabeschritt verschiebt Dateien aus dem iCloud-Ordner in den lokalen Eingang — erst, wenn sie vollständig heruntergeladen sind — und schreibt jede Übergabe in ein Protokoll. Derselbe Übergabeschritt bedient auch den NAS-Ordner. Die Frage, ob der Mac-Scanner abgeschafft wird, wird davon **getrennt** und später entschieden; bis dahin bleibt er als zweiter Quellkanal, der in denselben Eingang mündet.

Einseitig ist B an der Stelle, an der A einfach ist: B kauft Kontrolle mit einem zusätzlichen beweglichen Teil und lässt die Geräteentscheidung offen.

## 3. Die Zerlegung in zehn Bestandteile

*(beschrieben, nicht benotet)*

| # | Bestandteil | A — die Idee | B — der Gegenvorschlag |
|---|---|---|---|
| 1 | Ziel | Ein Eingang, ein Gerät, keine zweite Quelle mehr. Einfachheit als Ziel. | Ein Eingang für Marlene, beliebig viele Quellen davor. Entkopplung als Ziel. |
| 2 | Zeit bis Nutzen | Sofort: Ordner anlegen, Pfad ändern, fertig. | Erst nach Bau und Test des Übergabeschritts; dann für alle Quellen zugleich. |
| 3 | Aufwand | Eine Pfadänderung, ein Gerät wegräumen. | Skript mit Vollständigkeitsprüfung und Protokoll, dazu NAS-Anbindung. |
| 4 | Kosten | Keine neuen; ggf. iCloud-Speicher. Ein Scanner entfällt (Erlös oder Platz). | Keine neuen; laufender Pflegeaufwand für den Übergabeschritt. |
| 5 | Risiko | Marlene liest einen von außen synchronisierten Ordner: eine halb geladene Datei kann als vollständig gelesen werden. Ein Gerät heißt: fällt es aus, kommt nichts herein. | Ein zusätzliches Teil, das ausfallen kann; still ausgefallen staut sich der Eingang unbemerkt. Die Vollständigkeitsprüfung ist genau die Kontrolle, die A fehlt. |
| 6 | Rücknehmbarkeit | Die Ordneränderung in Minuten; die Abschaffung des Scanners nicht. | Jeder Teil einzeln rücknehmbar, weil nichts abgeschafft wird — dafür bleibt ein Teil mehr stehen. |
| 7 | Passung | Folgt dem Ablagekonzept, das iCloud als Eingang vorsieht — setzt damit eine **offene** Entscheidung um. | Folgt der getroffenen Entscheidung vom 07.09.2026 (Marlene liest Quellen nur) und lässt die offene iCloud-Frage offen. |
| 8 | Messbarkeit | Messbar ist nur, ob etwas ankommt; ein Sync-Fehlschlag sieht aus wie „noch nichts gescannt". | Protokoll je Datei mit Zeitpunkt, Quelle, Ergebnis; Stau und Ausfall sind zählbar. |
| 9 | Abhängigkeiten | iCloud, iPhone, die Bereitschaft, ausschließlich mobil zu scannen. | iCloud, iPhone, NAS-Zugang **und** der eigene Übergabeschritt. |
| 10 | Nebenwirkungen | Stapel und Sonderformate künftig mit der Hand am Gerät; die alte Zweiteilung verschwindet. | Die Zweiteilung der Quellen bleibt samt Pflege bestehen; Marlene sieht davon nichts. |

## 4. Je Zeile eine Wahl

**Urheber der Wahlen: eine fremde Instanz** — ein separater Lauf, dem Frage, Lage, beide Vorschläge als A und B und die zwanzig Zellen ohne Herkunftsangabe vorgelegt wurden. Er wusste nicht, welcher Vorschlag von Tobias stammt.

| # | Wahl | Begründung |
|---|---|---|
| 1 | **A** | „Einfachheit" ist konkreter und prüfbarer als „Entkopplung", solange eine Assistenz und zwei Quellen im Spiel sind. |
| 2 | **A** | Sofortiger Nutzen ohne Bau schlägt Nutzen nach Skript und Test. |
| 3 | **A** | Eine Pfadänderung ist ungleich weniger Aufwand als Skript, Prüfung, Protokoll und NAS-Anbindung. |
| 4 | **A** (Gleichstand) | Die fremde Instanz sah Gleichstand: keine neuen Kosten, entfallendes Gerät und Pflegeaufwand beide ungemessen. **Regel: Gleichstand geht an den Auftraggeber**, also an A. |
| 5 | **B** | Eine halb synchronisierte Datei als vollständig zu lesen ist ein stiller Datenfehler, ein Stau nur ein Verzug — und Marlene braucht jede Datei vollständig. |
| 6 | **B** | Nichts wird abgeschafft, jeder Teil einzeln rücknehmbar; A nimmt eine unumkehrbare Geräteentscheidung mit. |
| 7 | **B** | Folgt der bereits getroffenen Entscheidung und nimmt die offene iCloud-Entscheidung nicht vorweg. |
| 8 | **B** | „Fehlschlag sieht aus wie nichts gescannt" ist keine Messbarkeit; ein Protokoll ist eine. |
| 9 | **A** | A hängt an einer Abhängigkeit weniger, und für den eigenen Übergabeschritt steht niemand sonst ein. |
| 10 | **B** | Der Verlust von Stapelscan und Sonderformaten trifft die tägliche Arbeit unmittelbar; Pflegeaufwand einer zweiten Quelle erreicht Marlene nicht. |

Stand: A gewinnt 1, 2, 3, 4, 9 — B gewinnt 5, 6, 7, 8, 10.

## 5. Der dritte Vorschlag (C)

**Das iPhone wird der Hauptscanner und liefert nach iCloud/Eingang. Marlenes Eingang ist und bleibt ein lokaler Ordner auf dem Mac; ein sehr kleiner Übergabeschritt verschiebt aus iCloud dorthin, sobald eine Datei vollständig ist, und schreibt eine Zeile ins Protokoll. Der Mac-Scanner wird nicht abgeschafft, sondern zwei Wochen lang stillgelegt; danach wird über sein Ende entschieden. Der NAS-Ordner bleibt vorerst, wie er ist.**

| Teil von C | Herkunft |
|---|---|
| iPhone als Scanner, Ziel iCloud-Ordner „Eingang" | **A** (Punkt 1, 2, 3, 9) |
| Marlene liest einen lokalen Ordner, nicht den Sync-Ordner | **B** (Punkt 5) |
| Übergabeschritt mit Vollständigkeitsprüfung | **B** (Punkt 5) |
| Protokollzeile je übernommener Datei | **B** (Punkt 8) |
| NAS-Ordner bleibt unverändert und wird **nicht** angebunden | **neu** — A wollte ihn loswerden, B wollte ihn mit anbinden; C tut keines von beiden, weil Anbinden den Aufwand aus Punkt 3 zurückholt und Abschaffen die Entscheidung vom 07.09.2026 anfasst |
| Mac-Scanner zwei Wochen stillgelegt statt abgeschafft | **neu** — A schafft ab (Punkt 1), B lässt ihn laufen (Punkt 6); C macht die Rücknahme billig und die Entscheidung datiert |
| Die offene iCloud-Entscheidung wird nach den zwei Wochen mit dem Protokoll entschieden | **B** (Punkt 7), mit den Zahlen aus **B** (Punkt 8) |

**Wo zwei gewählte Teile sich reiben, ungeglättet:** Punkt 3 (A: kein Bauaufwand) und Punkt 5/8 (B: Prüfung und Protokoll) vertragen sich nicht. C hat sich für den Bauaufwand entschieden, ihn aber auf das Minimum gedrückt — eine Datei gilt als vollständig, wenn kein `.icloud`-Platzhalter mehr existiert und ihre Größe zwei Durchläufe lang gleich bleibt; das Protokoll ist eine angehängte Textzeile, keine Datenbank. Das ist ein Kompromiss und keine Auflösung: C ist an dieser Stelle aufwendiger als A und kontrollärmer als B.

Ebenso reiben sich Punkt 9 (A: eine Abhängigkeit weniger) und der Übergabeschritt, der genau eine Abhängigkeit hinzufügt. C nimmt das in Kauf, weil die hinzugefügte Abhängigkeit im eigenen Haus liegt und die vermiedene (halbe Datei) fremd und still ist.

## 6. Was weggefallen ist

| Weggefallener Teil | aus | Grund |
|---|---|---|
| Sofortige Abschaffung des Mac-Scanners | A | Unumkehrbar, bevor gemessen ist, ob Stapel und Sonderformate am iPhone tragbar sind (Punkt 6, 10). |
| „Ein Eingang, ein Gerät" als Endzustand | A | Nur aufgeschoben: C hält ihn als Ziel, aber nach zwei Wochen Beleg. |
| Anbindung des NAS-Ordners an den Übergabeschritt | B | Holt genau den Aufwand zurück, den Punkt 3 an A vergeben hat; der Ordner tut heute niemandem weh. |
| Trennung der Geräteentscheidung „auf später ohne Datum" | B | Ein Aufschub ohne Datum ist ein Aufschub für immer; C setzt zwei Wochen. |
| Größere Protokollierung (Datenbank, Auswertung) | B | Für zwei Quellen und geringen Durchsatz nicht verhältnismäßig. |

**Die eine Sache, die an C am ehesten noch falsch ist:** Die Vollständigkeitsprüfung ist geraten, nicht gemessen. Ob ein fehlender `.icloud`-Platzhalter auf diesem Mac wirklich „ganz da" bedeutet — und ob iCloud eine wachsende Datei nicht schon vorher sichtbar macht —, weiß niemand hier; genau daran hängt aber der einzige Punkt, an dem C teurer ist als A. Bevor C gebaut wird, gehört ein Testscan mit `brctl log` daneben. Fällt der anders aus, ist A ohne Umbau die richtige Antwort und dieser ganze Vergleich hat einen Übergabeschritt zu viel produziert.

**Keine Entscheidung.** Tobias entscheidet, ob C gebaut wird, A bleibt oder B kommt.
