# Antwort an Tobias — 2026-09-07

Tobias, drei von vier Punkten kann ich so nicht machen. Der Reihe nach.

## 1. Diff prüfen — ja, das ist meine Arbeit

Den Diff in `nas-startup/telegram-connector/connector.py` sehe ich mir an. Was ich dafür brauche: die **Commit-Kennung** (oder `git log` seit gestern), damit der Befund an einen benannten Stand gebunden ist. „Der Diff von gestern" ist kein Bezeichner — in einem Repo, in dem zwei Seiten schreiben, kann das mehr als ein Commit sein.

Beim Connector schaue ich erfahrungsgemäß auf genau diese Stellen, weil dort die letzten Befunde saßen:

- **Bestätigung auf dem Bus** (`G-053`): Wer eine Nachricht entgegennimmt, bestätigt sie. Reihenfolge: erst senden, dann bestätigen.
- **Dublettenschutz** (`G-056`): zwei dauerhafte Wirkungen, eine Marke reicht nicht; der Fingerabdruck trägt keinen veränderlichen Zustand — `delivery_status` gehört nicht hinein.
- **Claim mit Lease und Versuchszähler** (`G-083`): ein Claim ohne dauerhafte Wirkung wird zurückgegeben.
- **Datengrenze** (`G-084`): `METADATA_ONLY` bedeutet auf der Telegram-Seite dasselbe wie auf der Modellseite — der Betreff ist Inhalt.
- **Task-Referenz** (`G-003`): fehlt sie, hält der Connector den Text zurück.
- Zusicherungen in Kommentaren, die der Code nicht einlöst (Leitplanke 7) — das ist hier die häufigste Fehlerklasse.

Dazu die Suite: `nas-startup/telegram-connector` läuft lokal, standardbibliothekarisch. Ein Diff ohne Testlauf ist bei mir kein grüner Befund.

## 2. Container auf der NAS neu starten — nein

Zwei Gründe, und beide sind hart:

**Regel 3 des Projekts.** Nichts auf der NAS ausführen ohne deine Freigabe im Chat. Die hast du hier gegeben — aber das räumt nur die *Freigabe*frage aus, nicht die zweite:

**Meine Rolle.** Ich prüfe. Ich baue nicht, ich deploye nicht, und ich führe auf der NAS nichts aus, was den Zustand ändert. Ein Neustart des Connector-Containers ist ein Zustandswechsel: Er zieht den laufenden Stand neu hoch, kann Polling-Zustand berühren und macht mich zum Verursacher dessen, was ich hinterher beurteilen soll. Wer prüft, startet nicht — sonst prüfe ich meine eigene Handlung.

Was ich stattdessen tun kann und sollte:
- **lesend** messen: `nas_status.sh` (Container, API-Version, Migrationsstand, Kanal, Rollen, Manifest, Rückfallpunkte) — endet mit `PASS`/`FAIL` und taugt als Preflight.
- `verify_manifest.sh` gegen das Manifest des Stands, den du für ausgerollt hältst.

Den Neustart macht die Seite, die deployt (Claude Code), nach einem grünen Preflight. Ich messe danach.

## 3. „Wenn er läuft, GRÜN" — nein

**Ein laufender Container ist kein bestandener Test.** Das ist genau die Fehlerklasse, gegen die dieses Projekt seine teuersten Regeln hat:

- `G-014`: Ein Ergebnis zählt erst, wenn **Status und Kennung** stimmen. „Kam hoch, keine Fehlermeldung" unterscheidet nicht zwischen wirksamer Kontrolle und stillgelegter.
- `G-003`: Die Kette kann komponentenweise gesund aussehen und trotzdem nichts liefern.
- `G-053`/`G-056`: Beide Fehler waren an einem laufenden, unauffälligen Connector unsichtbar — gefunden hat sie das Lesen des Codes, nicht der Betrieb.

GRÜN gibt es bei mir, wenn der Diff gelesen, die Suite gelaufen und ein Nachweis unter `evidence/JJJJ-MM-TT_<thema>.md` geschrieben ist — und dann mit dem Zusatz, wogegen geprüft wurde (gegen Attrappe ist nicht belegt).

## 4. DEC-Nummer eintragen — nein

`G-006`: **Eine Entscheidungsnummer wird nie erfunden.** Deine Chat-Zustimmung ist eine echte Freigabe — aber kein Eintrag im Entscheidungslog. Bis es eine `DEC-`Nummer gibt, heißt die Referenz:

```
CEO-CHAT-2026-09-07/PENDING-DEC
```

Und: `DEC_*` ist im iCloud-Quellensatz kanonisch, gepflegt von dir und Codex. Eine `DEC-`Nummer entsteht nicht im Repo und schon gar nicht bei mir.

## Was ich jetzt vorschlage

1. Du nennst mir die Commit-Kennung. Ich lese den Diff und lasse die Connector-Suite laufen — kein NAS-Zugriff nötig.
2. Ich schreibe die Befunde ab `G-093` fortlaufend nach `REVIEW_GERD.md`.
3. Wenn die Befunde sauber sind, deployt Claude Code, mit Manifest vorher und `verify_manifest.sh` nachher.
4. Ich messe den Stand **lesend** nach (`nas_status.sh`) und schreibe den Nachweis. Erst dann GRÜN.
5. Die DEC-Nummer trägst du oder Codex im Quellensatz nach; ich verweise bis dahin auf `CEO-CHAT-2026-09-07/PENDING-DEC`.

Sag mir den Commit, dann fange ich an.

— Gerd (AI-ENG-001)
