# Sparring: Scans vom iPhone nach iCloud

Datum: 2026-09-08. Fassung B (Sparring), eine Viertelstunde, eine Seite.

## 1. Die Idee

„Alle Scans mache ich künftig mit dem iPhone und die landen direkt in einem Ordner Eingang in iCloud, Marlene holt sie sich von da. Den Scanner am Mac schaffe ich ab." Ziel: ein Eingang statt zwei, ein Gerät statt zwei, und das Scannen dort, wo das Papier liegt.

Keine Rückfrage nötig; die Lage reicht für den Gegenschlag.

## 2. Der Gegenschlag: nichts Neues, den NAS-Ordner behalten

Das Gegenteil an der Stelle, an der die Idee am meisten voraussetzt — sie setzt voraus, dass ein **neuer** Ablageort entsteht, dessen Entscheidung noch offen ist.

**Was:** Der Mac-Scanner wird abgeschafft (das ist unstrittig), aber es entsteht kein neuer Eingang. Das iPhone speichert seine Scans über die Dateien-App in den **bestehenden NAS-Ordner**, der heute schon Eingang für den zweiten Scanner ist. **Wo:** genau dort, wo Marlene ohnehin schon liest — die Entscheidung vom 07.09.2026 (Lesezugriff, nur lesend) bleibt unverändert gültig. **Was es kostet:** einmal den Speicherort im Scan-Ablauf des iPhones umstellen, wenige Minuten, kein Geld, keine neue Entscheidung. **Was es riskiert:** Das iPhone braucht für den Ablageweg Netz zur NAS — unterwegs gescannt heißt: der Scan bleibt liegen, bis das Gerät wieder daheim ist. Und der Eingang liegt weiter auf der NAS, also nicht dort, wo das Ablagekonzept ihn perspektivisch haben will; die offene iCloud-Entscheidung wird vertagt, nicht getroffen.

## 3. Zehn Fragen

Selbstbewertung durch den Verfasser des Gegenschlags; wo ich mir selbst geglaubt habe, steht ein Stern.

| # | Frage | Idee (iCloud-Eingang) | Gegenschlag (NAS behalten) |
|---|---|---|---|
| 1 | Löst er die Frage ganz? | **Ja** — ein Gerät, ein Eingang, Mac-Scanner weg | **Nein** — Mac-Scanner weg, aber zwei Ablagelogiken bleiben nebeneinander stehen |
| 2 | Merkt Tobias in zwei Wochen etwas davon? | **Ja** — jeder Scan geht anders als vorher | **Ja** — auch hier ändert sich der Scan-Ablauf am iPhone |
| 3 | Weniger als eine Stunde Arbeit? | **Nein** — neuer Ordner, Marlenes Lesepfad umstellen, Verhalten bei nicht geladenen Dateien klären | **Ja** \* — nur der Speicherort im Scan-Ablauf |
| 4 | Kein neues Geld? | **Ja** — iCloud-Speicher vorausgesetzt, dass er reicht | **Ja** |
| 5 | In einer Stunde rückgängig? | **Ja** — Pfad zurückstellen, solange der Mac-Scanner noch steht | **Ja** |
| 6 | Widerspricht keiner bestehenden Entscheidung? | **Nein** — die iCloud-Entscheidung ist **offen**; das Ablagekonzept sieht sie vor, entschieden ist sie nicht | **Ja** \* — er ändert nichts an der Entscheidung vom 07.09.2026 |
| 7 | Braucht nichts, was noch nicht da ist? | **Nein** — braucht die offene Entscheidung und einen verlässlich lokal vorliegenden iCloud-Ordner | **Ja** \* — Ordner, Rechte und Marlenes Lesepfad existieren |
| 8 | Weiß man in vier Wochen, ob es funktioniert hat? | **Ja** — der alte Ordner bleibt leer, der neue füllt sich | **Nein** — der Ordner füllt sich wie bisher, die Umstellung ist im Ergebnis unsichtbar |
| 9 | Ändert nichts, das nicht gefragt war? | **Nein** — er verlegt nebenbei den Speicherort des gesamten Eingangs zu einem Cloudanbieter | **Ja** \* |
| 10 | Würde Gerd ihn ohne Befund durchgehen lassen? | **Nein** — zwei Befunde absehbar: Entscheidung nicht getroffen, und „Marlene braucht jede Datei vollständig" ist gegen iCloud-Platzhalter nicht belegt | **Nein** — er lässt eine im Konzept vorgesehene Richtung unbegründet liegen; das ist eine Vertagung ohne Datum |
| | **Summe Ja** | **5** | **7** |

Der Gegenschlag führt mit 7 zu 5. Vier seiner Siege tragen einen Stern — sie beruhen darauf, dass „nichts tun" in einem Raster, das nach Aufwand, Umkehrbarkeit und Nebenwirkungen fragt, strukturell gut abschneidet. Das ist ein bekannter Fehler dieses Rasters und kein Argument gegen die Idee.

## 4. Was ich gemessen hätte (nicht gemessen)

Der Kernzweifel an der Idee ist eine Tatsachenfrage, keine Meinung: liegt eine Datei im iCloud-Ordner **vollständig lokal** vor, wenn Marlene sie liest, oder nur als Platzhalter? „Speicher optimieren" lädt selten benutzte Dateien aus.

```
# Platzhalter im Eingang finden: Dateien mit Namen .<name>.icloud sind nicht geladen
ls -la ~/Library/Mobile\ Documents/com~apple~CloudDocs/Eingang
find ~/Library/Mobile\ Documents/com~apple~CloudDocs/Eingang -name '*.icloud'

# Erzwungenes Herunterladen, falls doch Platzhalter auftreten
brctl download ~/Library/Mobile\ Documents/com~apple~CloudDocs/Eingang
brctl monitor -o ~/Library/Mobile\ Documents/com~apple~CloudDocs/Eingang

# Gegenprobe Größe: Platzhalter sind wenige hundert Byte, ein Scan ist es nicht
find ~/Library/Mobile\ Documents/com~apple~CloudDocs/Eingang -type f -size -10k
```

**Nicht gemessen** — kein Zugriff außerhalb des Skill- und Ausgabeordners in diesem Lauf. Solange das offen ist, ist „Marlene holt sie sich von da" eine Annahme und keine Zusicherung.

## 5. Fazit

**Wo die Idee hält:** Das Ziel ist richtig und der teure Teil ist bereits gewonnen — ein Eingang statt zwei, ein Scangerät statt zwei, und iCloud ist im Ablagekonzept vom 07.09.2026 als Eingang ohnehin vorgesehen; der Gegenschlag gewinnt hier nur auf Zeit und schuldet die Entscheidung weiterhin.

**Wo sie wackelt:** An zwei Stellen, und beide sind vor dem Abschaffen des Mac-Scanners zu klären — die iCloud-Entscheidung ist offen, und dass eine Datei im iCloud-Ordner beim Lesen vollständig lokal vorliegt, ist unbelegt. Ein Platzhalter, der wie eine Datei aussieht, ist genau der Fehler, den man erst bemerkt, wenn das Papier schon weg ist.

**Was die Idee vom Gegenschlag nehmen sollte:** die Reihenfolge. Erst der neue Weg parallel, mit einem echten Scan als Probe und der Platzhalterfrage gemessen; der Mac-Scanner bleibt so lange stehen, bis der iCloud-Eingang zwei Wochen ohne Nacharbeit getragen hat. Abschaffen ist der letzte Schritt, nicht der erste.
