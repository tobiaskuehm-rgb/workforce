# Plan für Montag, 2026-09-14

Karl, geschrieben am 2026-09-13. Reihenfolge vom CEO: **erst Gerd, dann Deploy**, auf Fable 5.1.

## 1. Gerds Nachcheck, vor allem anderen

Prüfgegenstand: alles seit `3b6cae3`. Vier Sachen, die er noch nie gesehen hat:

- **Kontextdateien** (`workforce/config.py`): Der Bot lädt Gedächtnis und Antwortform beim
  Start. Vorher hatte er nichts davon; jede `SKILL.md` versprach ein Gedächtnis, das im Bot
  unerreichbar war. Fünf Tests, Befundnummer offen, vergibt er.
- **Die drei Wächter aus dem Code-Review** (`deploy_nas.sh`, `config.py`): ACL, unerwartete
  Dateien, Lesefehler — alle drei meldeten bei einem Fehlschlag grün.
- **Die ACL-Korrektur vom 2026-09-13**: voller Pfad und Tabulator im Muster, gegen die NAS
  gemessen (`evidence/2026-09-13_acl_und_pruefsumme_gemessen.md`). Ob das `G-117` schließt,
  entscheidet er.
- **`G-119`**: Fehlerpfad gemessen, Bewertung bei ihm.

Dazu die Frage, die ich ihm ausdrücklich stelle: Reicht eine Attrappe für einen Wächter über
ein fremdes Werkzeug, oder gehört jeder solche Wächter einmal gegen die echte Maschine
gemessen? Meine beiden blinden Stellen hätte keine Attrappe gezeigt.

## 2. Deploy, nach seiner Freigabe

`sh workforce/deploy_nas.sh` aus sauberem Baum. Neu darin, alles ungetestet gegen die echte
NAS: Prüfsummen über `workforce/` **und** `skills/`, Meldung unerwarteter Dateien, Rechte für
**alle** Secrets zurückgelesen, ACL-Prüfung. Jeder dieser Schritte bricht vor `up` ab.

**Was schiefgehen kann, und was dann passiert:** Bricht ein Schritt ab, läuft der alte
Container weiter — das ist der Sinn. Der Zeitplan liefe dann Montag noch ohne Gedächtnis, und
Gerds Freigabe für den Zeitplanbetrieb endet mit dem Montagstermin. Also: Wenn der Deploy
scheitert, ist das eine Vorlage an den CEO, keine stille Reparatur.

## 3. Danach

Gerds Review nach dem Lauf, dann die Wochenlage. Höchstens eine Vorlage am Tag (`DEC-048`),
also kommt alles Weitere Donnerstag.

## Was der CEO Montag zu tun hat

Nichts, bis ich mich melde. Dann eine Entscheidung: Deploy ja oder nein, je nachdem was Gerd
sagt.
