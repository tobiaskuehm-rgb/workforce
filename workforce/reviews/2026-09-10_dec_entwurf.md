# Entwurf für das Entscheidungslog, DEC-038 bis DEC-045

Vorlage von Karl, 2026-09-10. Ziel: `Startup_Codex/START_UP_Codex_Projektquellen_2026-08-13/03_DECISION_LOG.txt`
im iCloud-Satz, ans Ende anhängen. Form wie `DEC-036`. Der CEO schreibt, oder sagt „trag ein".

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

## DEC-044 – Klasse Rechte: Marlene bis Phase 4 auf dem Kopienweg
**Datum:** 2026-09-08
**Entscheider:** CEO
**Status:** ACTIVE

**Entscheidung:** Marlene erhält keinen eigenen Lesezugang zu Google Drive oder NAS-Inbox; Dokumente kommen als Kopie. Der lesende Zugang wird mit Phase 4 (Paperless) entschieden, mit eigener Invariantenzeile und Gerds Review vorher.

## DEC-045 – Klasse Produktives: Phase 3 und Rechte auf der NAS
**Datum:** 2026-09-10
**Entscheider:** CEO
**Status:** DONE – ZWEI DEPLOYS, GATE GRÜN BIS 2026-09-14

**Entscheidung:** Deploy `35e7ae3` (Phase 3, der Kern meldet sich: Montag Wochenlage, Donnerstag Entscheidungstermin, je 06:00 UTC an Karl) und Ordnerrechte `750`/`640`, Gruppe `10001`; danach Deploy `0ef72cb` mit den Korrekturen `G-112` bis `G-116`. Nachweise `workforce/evidence/2026-09-10_deploy_phase3_und_rechte.md` und `2026-09-10_deploy2_g112.md`. Gerd: Zeitplanbetrieb freigegeben bis einschließlich 2026-09-14; darüber hinaus nach `G-117`–`G-119`.

**Ersetzt/klärt:** `DEC-037` (Codex-Zeitpläne) ist damit historisch; die Nachtläufe aus Codex sind seit 2026-09-07 Archiv, der Takt kommt aus dem Kern.
