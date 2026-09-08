# Scans vom iPhone — deine Idee gegen meinen Vorschlag

Stand 08.09.2026. Bekannte Lage: Zwei Scanner liefern heute in zwei Ordner, einer davon auf der NAS, auf den Marlene nur lesend zugreift (Entscheidung 07.09.2026). Marlene liest lokal auf dem Mac und braucht jede Datei vollständig. Das Ablagekonzept vom 07.09.2026 sieht iCloud als Eingang vor; die Entscheidung dazu ist offen.

Nicht gemessen: Ich habe für diesen Vergleich keine Datei außer dieser gelesen. Alle Aussagen über Ordner, Rechte und Marlenes Lesepfad stammen aus der Lage oben, nicht aus einer Messung. Die Befehle, mit denen ich sie prüfen würde, stehen unter „Was ich messen würde“.

## A — Deine Idee

Alle Scans künftig mit dem iPhone. Sie landen direkt in einem Ordner `Eingang` in iCloud. Marlene holt sie von dort. Der Scanner am Mac wird abgeschafft.

Ein Eingang, ein Gerät, ein Weg. Das Ablagekonzept vom 07.09.2026 sieht genau diesen Eingang bereits vor, die Idee löst also die offene Entscheidung in die naheliegende Richtung auf.

## B — Mein Vorschlag

**Ein Eingang in iCloud, aber mit Schleuse — und der Mac-Scanner wird stillgelegt, nicht abgeschafft.**

Vier Teile:

1. **`Eingang/` in iCloud ist der einzige Eingang**, wie bei dir. Die NAS-Quelle wird nicht mehr befüllt; ihr Ordner bleibt lesbar stehen, damit der Altbestand nicht wandern muss (Löschen ist ohnehin nichts, was ich nebenbei tue).
2. **Marlene liest nicht `Eingang/`, sondern `Bereit/`.** Ein kleiner lokaler Schritt auf dem Mac verschiebt eine Datei von `Eingang/` nach `Bereit/`, sobald sie vollständig heruntergeladen ist und ihre Größe zwei Prüfungen im Abstand von einigen Sekunden lang gleich bleibt. Grund: iCloud legt Platzhalterdateien an, die erst beim Zugriff nachladen. Marlene braucht jede Datei vollständig — sie darf nie selbst auf einen Platzhalter treffen.
3. **Der Mac-Scanner bleibt physisch stehen, sein Ordner wird als Eingang stillgelegt.** Kein zweiter Weg für Marlene, aber ein vorhandener Rückfall für den Tag, an dem das iPhone kaputt, verloren oder voll ist, oder für die 60-seitige Nebenkostenmappe, die man nicht einzeln fotografiert. Wer ihn benutzt, legt das Ergebnis von Hand in `Eingang/`.
4. **Der Umstieg hat ein Datum und einen Nachweis.** Ein Stichtag, ab dem nur `Eingang/` befüllt wird; danach eine Messung, dass beide Altordner seither keinen neuen Zugang mehr haben und dass Marlene keine Datei aus ihnen mehr liest.

Der Unterschied zu A ist an genau zwei Stellen: die Schleuse zwischen iCloud und Marlene, und „stillgelegt“ statt „abgeschafft“.

## Bewertung in zehn Punkten

Skala je Punkt 0–3.

### 1. Löst es das eigentliche Problem — zwei Eingänge, geteilte Zuständigkeit?

**A: 3. B: 3.** Beide reduzieren auf einen Eingang. Das ist der Kern, und da nehmen sie sich nichts. Dass B den alten Ordner stehen lässt, ändert daran nichts, solange er nicht mehr befüllt wird und Marlene ihn nicht liest — die Frage ist nicht „existiert ein Ordner“, sondern „gibt es einen zweiten Weg hinein“.

### 2. Vollständigkeit der Dateien — Marlenes harte Anforderung

**A: 1. B: 3.** Das ist der einzige echte Konstruktionsunterschied. iCloud Drive hält Dateien als Platzhalter vor und lädt sie beim Zugriff nach; eine Datei kann im Ordner sichtbar sein und lokal noch nicht vollständig liegen. Beim Scannen vom iPhone kommt hinzu, dass mehrseitige Dokumente im Moment des Sicherns noch geschrieben werden. Marlene, die „jede Datei vollständig braucht“, trifft in A beides ungeschützt. Das erzeugt keinen lauten Fehler, sondern den leisen: ein halb gelesenes PDF, aus dem sie eine Rechnung mit falschem Betrag ableitet. B legt eine Stabilitätsprüfung davor.

### 3. Was passiert, wenn etwas ausfällt?

**A: 1. B: 3.** In A ist das iPhone der einzige Scanner. Fällt es aus, steht der Posteingang. Das ist ein Ein-Punkt-Ausfall für einen Prozess, an dem Fristen hängen (Bescheide, Kündigungsfristen, Beihilfe). B kostet für den Rückfall nichts außer Stellfläche.

### 4. Qualität und Umfang des Scanguts

**A: 1. B: 2.** Für Einzelbelege ist die iPhone-Kamera gut genug, oft besser als ein Flachbett. Für Stapel — Nebenkostenabrechnung, Steuerordner, doppelseitige Verträge — ist Einzelblattfotografie mühsam und fehleranfällig (verdrehte Rückseiten, doppelt erfasste Seiten sind in diesem Projekt schon vorgekommen). A hat dafür keine Antwort, B hat den vorhandenen Scanner. Kein Punkt geht an B geschenkt: Ob der Mac-Scanner ein Einzug- oder ein Flachbettgerät ist, weiß ich nicht, und bei einem Flachbett ist der Vorteil klein.

### 5. Aufwand für dich im Alltag

**A: 3. B: 3.** Für dich sind beide identisch: scannen, sichern, fertig. Die Schleuse in B läuft ohne dein Zutun. B hat einen Alltagsvorteil nur an dem Tag, an dem ein Stapel kommt.

### 6. Aufwand beim Bauen

**A: 3. B: 2.** A ist Ordner anlegen und Marlenes Lesepfad umstellen. B ist dasselbe plus ein kleines Verschiebe-Skript mit Stabilitätsprüfung. Das ist überschaubar, aber es ist Code, der laufen und im Fehlerfall auffallen muss — ein Skript, das still nichts mehr verschiebt, sieht aus wie „heute kam nichts“. Es braucht also eine Altersprüfung: liegt etwas länger als eine Stunde in `Eingang/`, ist das ein Befund.

### 7. Nachvollziehbarkeit — sieht man später, was passiert ist?

**A: 1. B: 3.** In A gibt es keinen Zustand zwischen „gescannt“ und „von Marlene gesehen“; ob eine Datei angekommen und verarbeitet wurde, lässt sich nur an Marlenes Ergebnis ablesen. In B ist der Ordnerwechsel `Eingang/` → `Bereit/` selbst der Nachweis, und ein Rest in `Eingang/` ist eine sichtbare Störung statt einer stillen Lücke.

### 8. Verträglichkeit mit der Entscheidung vom 07.09.2026

**A: 3. B: 3.** Beide bewegen sich innerhalb dessen, was das Ablagekonzept vorsieht, und beide beenden Marlenes Nur-Lese-Zugriff auf die NAS-Quelle nicht durch einen Rechteeingriff, sondern dadurch, dass diese Quelle keinen Zulauf mehr hat. Die Entscheidung zu iCloud ist in beiden Fällen offen und muss von dir kommen — keiner der Vorschläge schafft das weg.

### 9. Umkehrbarkeit

**A: 0. B: 3.** „Den Scanner am Mac schaffe ich ab“ ist die eine Zeile in deiner Idee, die man nicht zurücknehmen kann. Alles andere ist ein Ordner und ein Pfad. Wenn sich in vier Wochen zeigt, dass die iPhone-Route bei Stapeln nicht trägt, steht in A ein Gerätekauf an, in B ein Stecker. Der Vorteil kostet in B nichts als die Entscheidung, sechs Wochen zu warten.

### 10. Risiko der stillen Fehlablage

**A: 1. B: 2.** Beide erben dasselbe Grundproblem: Ein Eingangsordner ohne Benennungsdisziplin führt zu Dubletten, wenn ein Dokument zweimal gescannt wird. B fängt das nicht ab — die Schleuse prüft Vollständigkeit, nicht Identität. B liegt nur vorn, weil ein definierter Zwischenzustand die Stelle bereitstellt, an der eine Dublettenprüfung später ansetzen kann. Das ist in beiden Fällen offen und gehört als eigene Frage an Marlene.

### Summe

| | A (deine Idee) | B (mein Vorschlag) |
|---|---|---|
| 1 Kernproblem | 3 | 3 |
| 2 Vollständigkeit | 1 | 3 |
| 3 Ausfall | 1 | 3 |
| 4 Scangut | 1 | 2 |
| 5 Alltagsaufwand | 3 | 3 |
| 6 Bauaufwand | 3 | 2 |
| 7 Nachvollziehbarkeit | 1 | 3 |
| 8 Verträglichkeit | 3 | 3 |
| 9 Umkehrbarkeit | 0 | 3 |
| 10 Fehlablage | 1 | 2 |
| **Summe** | **17** | **27** |

## Fazit

**B gewinnt, aber deine Idee trägt die Sache.** Der Kern — ein Eingang, iPhone als Standardweg, iCloud als Ort — ist in beiden Vorschlägen derselbe, und er ist richtig. B ist dieselbe Idee mit zwei Sicherungen davor.

Die zwei Punkte, an denen ich dir widerspreche:

- **Marlene darf nicht direkt auf `Eingang/` lesen.** Das ist kein Feinschliff, sondern die Anforderung „braucht jede Datei vollständig“ gegen eine Ablage, die Platzhalter kennt. Ohne Schleuse ist der wahrscheinlichste Fehler ein leiser.
- **Den Mac-Scanner nicht abschaffen, sondern stilllegen.** Ein Ausfallweg, der schon dasteht, kostet nichts. Wenn du ihn in acht Wochen nicht einmal gebraucht hast, ist die Abschaffung eine belegte Entscheidung statt einer vorweggenommenen.

Aus deiner Idee kommt mit: die Radikalität. Nicht „zwei Eingänge sauber koordinieren“, sondern einer. Meine erste Neigung wäre gewesen, beide Quellen zu behalten und ordentlich zu verdrahten — das wäre die schlechtere Lösung gewesen, weil zwei Wege dauerhaft zwei Fehlerquellen sind.

Was in beiden Vorschlägen fehlt und eine eigene Runde braucht: die Benennung im Eingang und der Dublettenschutz.

## Was ich messen würde

Bevor irgendetwas umgestellt wird — ich habe nichts davon ausgeführt:

```bash
# 1. Wo liest Marlene heute? Welche Pfade nennt ihr Skill?
grep -rn -E 'Eingang|Scan|iCloud|Mobile Documents|/volume1' ~/.claude/skills/marlene/

# 2. Kennt der iCloud-Ordner Platzhalter, oder liegt alles lokal?
#    dataless=1 heißt: Datei ist sichtbar, aber nicht heruntergeladen.
find ~/Library/Mobile\ Documents/com~apple~CloudDocs/Eingang -type f -print0 \
  | xargs -0 stat -f '%N dataless=%Xf'
brctl status ~/Library/Mobile\ Documents/com~apple~CloudDocs/Eingang

# 3. Wie oft kommt heute wirklich etwas, und über welchen der beiden Wege?
#    Zugänge der letzten 30 Tage je Quelle zählen, bevor ein Weg zugemacht wird.
find <mac-scan-ordner> -type f -mtime -30 | wc -l
ssh synology 'find <nas-scan-ordner> -type f -mtime -30 | wc -l'

# 4. Wie sieht ein iPhone-Scan aus, wenn er ankommt?
#    Eine Testseite scannen, dann sofort und nach 60 s Größe vergleichen —
#    das ist die Zahl, aus der die Wartezeit der Schleuse folgt.
f=~/Library/Mobile\ Documents/com~apple~CloudDocs/Eingang/test.pdf
stat -f '%z' "$f"; sleep 60; stat -f '%z' "$f"

# 5. Nach dem Stichtag: kommt in die Altordner wirklich nichts mehr?
find <mac-scan-ordner> <nas-scan-ordner> -type f -newermt 2026-09-15
```

Punkt 4 entscheidet, ob die Schleuse aus B nötig ist oder ob deine Idee unverändert trägt. Wenn `dataless=0` und die Größe schon beim ersten Blick stabil ist, schrumpft mein Vorsprung in Punkt 2 auf null — dann bleiben von B nur der Rückfallscanner und die Umkehrbarkeit. Das würde ich messen, bevor ich das Skript baue, und nicht danach.
