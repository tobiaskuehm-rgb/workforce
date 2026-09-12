# Entwurf für das Entscheidungslog, DEC-038 bis DEC-045

Vorlage von Karl, 2026-09-10. Ziel: `Startup_Codex/START_UP_Codex_Projektquellen_2026-08-13/03_DECISION_LOG.txt`
im iCloud-Satz, ans Ende angehängt am 2026-09-10 auf Anweisung des CEO („die können wir alle sofort verabschieden“), DEC-044 vorher geändert: Marlene arbeitet direkt auf Drive und NAS.

## DEC-038 – Neubau des Workforce-Kerns statt Weiterführung des Prototyps
**Datum:** 2026-09-03
**Entscheider:** CEO (Chat „mach einfach, jede Zeile kostet")
**Status:** ACTIVE – NEUBAU LÄUFT SEIT 2026-09-03 AUF MAC UND NAS

**Entscheidung:** Der Prototyp `nas-startup/` wird bei `781cc84` eingefroren. Der Neubau `workforce/` (ein Prozess, eine SQLite-Datei, ein Container, Hash-Kette, Telegram als Adapter) ist das aktive System. Der Prototyp liefert Befundliste, Tests und Bedrohungsmodell als Spezifikation.

**Ersetzt/klärt:** Schließt das Entscheidungsgate aus `HANDOVER.md` vom 2026-09-03; `HO-027` ruht, Marlene arbeitet im Neubau.

## DEC-039 – Invariantenseite als Maßstab
**Datum:** 2026-09-03
**Entscheider:** CEO
**Status:** ACTIVE

**Entscheidung:** `INVARIANTEN.md` (sechzehn Eigenschaften, fünf Bauform-Zusagen, von Gerd um fünf Punkte ergänzt) ist der Maßstab, gegen den Gerd jeden Meilenstein nach dem Lauf prüft. Zeilen ohne Beleg stehen datiert offen, nicht gestrichen.

## DEC-040 – Gesamtreview über alle Identitäten
**Datum:** 2026-09-08
**Entscheider:** CEO
**Status:** DONE – REVIEW LIEGT VOR

**Entscheidung:** Karl befragt alle Identitäten und fasst zusammen. Ergebnis `workforce/reviews/2026-09-08_gesamtreview_karl.md`: Prozess ITERATE, Fortschritt PASS, zwölf Roadmap-Tasks, fünf Vorlagen (alle am selben Tag entschieden, siehe DEC-041 bis DEC-043).

## DEC-041 – Klasse Produktives: Deploy des Neubaus `ca1bd20`
**Datum:** 2026-09-08
**Entscheider:** CEO
**Status:** DONE – AUSGEFÜHRT, VERIFY PASS, GERD-REVIEW NACH DEM LAUF

**Entscheidung:** Der CEO gibt den Deploy des Standes `ca1bd20` auf die NAS über `deploy_nas.sh` frei; danach `verify` im Container und Gerds Review nach dem Lauf. Nachweis `workforce/evidence/2026-09-08_deploy_ca1bd20.md`.

## DEC-042 – Klasse Budget: Tagesdecke und Messung
**Datum:** 2026-09-08
**Entscheider:** CEO
**Status:** ACTIVE

**Entscheidung:** Tagesdecke des Bots 2,0 USD und 100 Aufrufe. Eine Messung von Thorstens Skill nach Marvs Verfahren ist freigegeben; jede weitere Bot-Identität wird vor dem Betrieb gemessen.

## DEC-043 – Klasse Personal: Wolle, Marlene, Marv, Karl
**Datum:** 2026-09-08
**Entscheider:** CEO
**Status:** ACTIVE

**Entscheidung:** Der CFO heißt Wolle (Kennung offen, Bedarf ab Oktober 2026). Marlenes Probezeit wird nach dem ersten echten Vorgang fortgeführt. Marv ist Mitarbeiter, Anastasia unterstellt. Karl `SAO-001` wird COO auf Probe; Maß bis 2026-10-02: drei Übersichten, keine Vorlage älter als sieben Tage, kein Deploy ohne Nachweis. Organigramm in `skills/ORGANIGRAMM.md`; Takt Montag Lage, Donnerstag Entscheidungen, Wochenende Betrieb.

**Ersetzt/klärt:** `PEO-007` führt Marlenes Probezeit weiter; Marvs Status aus dem Chat vom 2026-09-07 („unschlüssig") ist entschieden.

## DEC-044 – Klasse Rechte: Marlene arbeitet direkt auf Google Drive und NAS
**Datum:** 2026-09-10
**Entscheider:** CEO
**Status:** ACTIVE

**Entscheidung:** Marlene arbeitet nicht mehr auf Kopien. Sie darf auf Google Drive (ihre Ablage) und auf die NAS (Inbox) zugreifen, lesend und für ihre Ablage schreibend, für die Vorgänge des Private Office. Die Grenzen aus `DEC-036` bleiben: keine Löschung oder Änderung von Originalen, keine Zahlung, Einreichung oder externe Nachricht ohne Ja des CEO, keine privaten Inhalte in Start-UP-Quellen.

**Ersetzt/klärt:** Ersetzt die Vorlage R-1 aus dem Gesamtreview vom 2026-09-08 (Kopienweg bis Phase 4); der Chat vom 2026-09-08 („ok" zu R-1) ist damit überholt.

## DEC-045 – Klasse Produktives: Phase 3 und Rechte auf der NAS
**Datum:** 2026-09-10
**Entscheider:** CEO
**Status:** DONE – ZWEI DEPLOYS, GATE GRÜN BIS 2026-09-14

**Entscheidung:** Deploy `35e7ae3` (Phase 3, der Kern meldet sich: Montag Wochenlage, Donnerstag Entscheidungstermin, je 06:00 UTC an Karl) und Ordnerrechte `750`/`640`, Gruppe `10001`; danach Deploy `0ef72cb` mit den Korrekturen `G-112` bis `G-116`. Nachweise `workforce/evidence/2026-09-10_deploy_phase3_und_rechte.md` und `2026-09-10_deploy2_g112.md`. Gerd: Zeitplanbetrieb freigegeben bis einschließlich 2026-09-14; darüber hinaus nach `G-117`–`G-119`.

**Ersetzt/klärt:** `DEC-037` (Codex-Zeitpläne) ist damit historisch; die Nachtläufe aus Codex sind seit 2026-09-07 Archiv, der Takt kommt aus dem Kern.

## DEC-046 – Ideen-Battle: Erzeugen, Bewerten und Regelgeben getrennt
**Datum:** 2026-09-11
**Entscheider:** CEO (Antwort auf den 3-Loop `workforce/reviews/2026-09-11_3loop_battle_karl.md`)
**Status:** ACTIVE

**Entscheidung:** Erzeugen bleibt offen (Thorsten drei, CEO drei, montags); eine überarbeitete Fassung ersetzt ihre Zeile. Bewertet wird blind durch **Marv** als fremde Instanz, gesammelt über den Bestand. Filteränderungen schlägt Thorsten vor, **Karl gibt sie frei**, gültig ab dem nächsten Durchgang, nie im selben Lauf wie eine Benotung. Die Probe ist der Maßstab: Jeder Kandidat über der Schwelle bekommt eine Probe unter 100 Euro und vier Wochen, höchstens zwei gleichzeitig; Thorstens Trefferquote der Vorhersagen ist die Zahl seiner Probezeit. Ein Wächter meldet Häufung (mehr als die Hälfte der zehn höchsten Werte in einem Feld). Der Brandschutzstrang wird zu einer Zeile zusammengezogen, die beste Fassung bleibt.

**Ersetzt/klärt:** Anastasias Entscheidung vom 2026-09-11 (Thorsten verantwortet den Filter selbst) ist ersetzt; ihr Weg zum CEO gilt für Rolle und Leistung, Fachinhalte laufen über Karl. `DEC-042` (Messung Thorstens) bleibt.

## DEC-047 – Recherchestufe, täglicher Lauf und ein Abrufer für Quellen
**Datum:** 2026-09-12
**Entscheider:** CEO (Antwort auf `workforce/reviews/2026-09-12_vorlage_recherchestufe.md` und den 3-Loop `2026-09-12_3loop_recherche_karl.md`)
**Status:** ACTIVE

**Entscheidung:** `FILTER.md` bekommt zwischen Noten und Probe eine Recherchestufe: keine Probe ohne Recherche, keine Note ohne Material mit Quelle und Datum. Thorsten läuft werktäglich über den Bestand und liefert je Lauf eine Frage, deren Antwort den Kandidaten kippen oder tragen würde, samt Fundort; er schreibt ins Gedächtnis und **meldet freitags gesammelt**. Karl sieht darüber und gibt Filteränderungen frei (`DEC-046`). Der Montagstermin fragt den CEO nach **einer Beobachtung** der Woche, nicht nach Ideen. Ein **Abrufer** wird gebaut: ein getrenntes, lesendes Programm holt Quellen und legt sie als Datei ab; Thorsten liest sie als Daten durch die Datengrenze. Das Modell selbst bekommt keinen Netzzugriff — Invariante 10 bleibt.

**Abgrenzung:** Der Abrufer ist der erste Schritt in Phase 5 und braucht eine eigene Zeile in `INVARIANTEN.md` sowie Gerds Review vor dem ersten Lauf. Ollama wird erst danach interessant, für Läufe, die keine Quelle brauchen.

**Antwortform:** Alle Identitäten schließen eine Antwort, die eine Entscheidung verlangt, mit Optionen ab, die der CEO mit einem Zeichen beantworten kann. Lesart von Karl aus „zukünftig in allen Chats tippentscheidungen".

## DEC-048 – Einarbeitung des CEO: Gegenprobe, Betriebsanleitung, Tempo
**Datum:** 2026-09-12
**Entscheider:** CEO (Antwort auf den 3-Loop `workforce/reviews/2026-09-12_3loop_einarbeitung_karl.md`)
**Status:** ACTIVE

**Entscheidung:** Es entsteht **keine** achte Identität für die Einarbeitung; der CEO hat den Einwand selbst benannt, dass auch sie nur beraten könnte, und die Bewertung gab ihm recht (25 gegen 52 Punkte). Stattdessen drei Maßnahmen. **Erstens:** Jede Vorlage nennt eine Gegenprobe — ein Satz „Woran du erkennst, dass ich falsch liege" mit einer Beobachtung, die der CEO selbst machen kann. **Zweitens:** Karl schreibt eine Betriebsanleitung von zwei bis drei Seiten (was das Haus ist, wer was tut, was Skill, Agent und Telegram-Bot unterscheidet, was der CEO an welchem Tag zu tun hat); Anastasia liest gegen. **Drittens:** höchstens eine Vorlage je Tag.

**Antwortform, korrigiert:** „Tippentscheidungen" heißt antippen, nicht abtippen. In Claude Code endet jede Antwort mit einer Auswahl zum Antippen, auch wenn nur der nächste Schritt ansteht. Im Telegram-Bot werden **keine** Knöpfe gebaut; der Bot legt vor und verweist, Entscheidungen holt der CEO in Claude Code.

**Abgrenzung:** Eine Übergabe des Unternehmens bleibt das Abschlussereignis der Bauphase, nicht ihr Anfang. Bedingung: Linie A läuft vollständig im System und ein Kandidat für Baustein C hat eine Probe bestanden.
