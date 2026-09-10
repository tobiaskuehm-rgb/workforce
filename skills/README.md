# Skills — ein Ort, eine Form

Jede Identität hat genau eine Datei `skills/NAME/SKILL.md`: Kopf mit `name` und `description`
für Claude Code, darunter die Rolle als Text. Dieselbe Datei ist der Systemtext der Identität im
Bot (`system_prompt_file` in `workforce/config.json`). Claude Code findet sie über einen
Verweis aus `~/.claude/skills/`; der Bot bekommt den Ordner nach `/etc/workforce/skills`.

Regeln: technikfrei formulieren, höchstens 150 Zeilen, weil der Text bei jedem Aufruf mitgeht.
Änderungen nur hier, nie in ChatGPT oder auf der NAS — das sind Archive. Das Register, wer
welche Rolle in welchem Status hat, führt Anastasia.

## Drei Stellen, an denen eine Identität steht

Eine Identität ist erst vollständig, wenn sie an allen dreien steht, die sie braucht. Wer nur
an einer steht, ist nicht halb da, sondern anders da — die drei können Verschiedenes.

| | wo | Modell | Kontext | wer bezahlt |
|---|---|---|---|---|
| **Skill** | `skills/<name>/SKILL.md` | das des laufenden Gesprächs | der des Gesprächs — **geteilt** | — |
| **Agent** | `.claude/agents/<name>.md` | eigenes, im Kopf der Datei | **eigener**, je Lauf | das Abo |
| **Bot** | `workforce/config.json` | eigenes, je Identität | eigener, SQLite | die API, je Aufruf |

**Skill und Agent sind nicht dasselbe.** Ein Skill ist eine Anweisung *im laufenden* Kontext:
Wer hier „Karl" aufruft, bekommt nicht Karl, sondern den laufenden Assistenten mit Karls Text —
ein Modell, ein Kontext, ein Verlauf für alle. Ein Agent ist ein **eigener Lauf** mit eigenem
Modell und eigenem Kontext; seine Arbeit landet nicht im Fenster des CEO. Modelle je Identität
gibt es deshalb nur als Agent oder im Bot, nie als Skill.

## Verfahren, die keine Identität sind

Zwei Skills beschreiben keine Rolle, sondern ein Vorgehen. Sie haben keine Kennung, keinen
Status, keinen Vorgesetzten und kein Gedächtnis, weil es niemanden gibt, der sich erinnert.

| Verfahren | Ordner | wozu | Herkunft |
|---|---|---|---|
| 3-Loop | `3loop/` | ein Vorschlag, drei Gegenvorschläge, drei Sichten, ein Fazit | Marv, 2026-09-07, aus dem Bau von Marlene und Marv |
| Ideen-Vergleich | `idee/` | eine Idee gegen einen Gegenvorschlag, blind bewertet | Marv, 2026-09-09, Endfassung aus dem Vergleich |

Sie stehen **vor** dem Register und nicht darin. Das ist keine Kosmetik: Der Wächter liest ab
`## Register` und verlangt für jeden Eintrag dort eine Gedächtnisdatei. Ein Verfahren, das im
Register stünde, würde ein Gedächtnis verlangen, das es nicht geben soll.

## Register

Ein Registereintrag beantwortet fünf Fragen: wer, welche Kennung, in welchem Status, wer führt,
und wo steht der Nachweis. Bis zum 2026-09-10 beantwortete er zwei davon. Die Ordnerspalte
bleibt die zweite, weil zwei Wächter sie dort lesen (`test_identitaeten.py`,
`test_organigramm.py`).

| Identität | Ordner | Kennung | Status | Vorgesetzter / fachliche Führung | letzter Review |
|---|---|---|---|---|---|
| Karl, Koordinator, Standard im Bot | `karl/` | `SAO-001` | Probezeit (`DEC-002`) | CEO / Anastasia | 2026-09-10, `probezeit/karl_SAO-001.md` |
| Marlene, Private Office | `marlene/` | `POA-001` | Probezeit (`DEC-036`) | CEO / Anastasia | 2026-09-10, `probezeit/marlene_POA-001_2026-09-10.md` |
| Thorsten, Research & Strategy | `thorsten/` | `RAS-001` | Probezeit (`DEC-002`) | CEO / Anastasia | noch keiner |
| Anastasia, People & Organization | `anastasia/` | `PEO-001` | Probezeit (`DEC-002`) | CEO (auch Kontrolle) / — | 2026-09-10, Selbstprüfung, `probezeit/anastasia_PEO-001.md` |
| Wolle, CFO | `cfo/` | Kennung offen | ruht bis Oktober 2026 | CEO / Anastasia | noch keiner |
| Marv, Skillbauer | `marv/` | `AI-SKE-001` | Mitarbeiter seit 2026-09-08, `DEC` offen | CEO / Anastasia | 2026-09-10, `probezeit/marv_AI-SKE-001.md` |
| Gerd, Systemarchitekt und Prüfer | `gerd/` | `AI-ENG-001` | Probezeit (`DEC-002`) | CEO / Anastasia | 2026-09-10, `probezeit/gerd_AI-ENG-001.md` |

**Kein Status wird vorab auf `ACTIVE` gesetzt**, solange Kennung oder Entscheidungsnummer offen
sind. Zwei Einträge tragen deshalb offene Felder: Wolles Kennung und Marvs `DEC`.

**Reviewtermine gibt es nicht.** Ein Review wird über Arbeit ausgelöst, nicht über den
Kalender — siehe `anastasia/reviews/`. Der Grund steht im 3-Loop vom 2026-09-08: Alle sieben
Identitäten sind am selben Tag angelegt worden und wären am selben Tag fällig geworden.

### Modelle je Identität

| Identität | Agent | Bot | Stand des Skills |
|---|---|---|---|
| Karl | Sonnet | Opus | v2 nach Marv, 43/43 gegen 26/43 über fünf Runden |
| Marlene | Sonnet | Sonnet | drei Runden und Praxistest an 47 Dateien |
| Thorsten | Sonnet | Opus | Prüffälle liegen, **noch nicht gemessen** |
| Anastasia | Sonnet | Sonnet | Runde 1 durch Marv, 34/35 gegen 24/35 |
| Wolle | Sonnet | Sonnet | keine Prüffälle, ruht |
| Marv | Opus | — | Runde 2, 40/40 gegen 17/40; eigener Skill, kein fremder Blick |
| Gerd | Opus | — | Runde 2, 40/42 gegen 36/42 |

Die Modellwahl folgt zwei Fragen, und sie ziehen in verschiedene Richtungen: **Wie oft wird
er gerufen?** und **wie teuer ist eine schlechtere Antwort?** Gerd prüft und Marv baut — selten,
tief, und ein schwächeres Modell wäre dort nicht langsamer, sondern schlechter; sie bleiben auf
Opus. Alle übrigen laufen auf Sonnet, Karl als meistgerufene Identität ausdrücklich auch: Seine
Form steht im Skill und trägt sie.

Als Agent und im Bot darf dieselbe Identität verschieden laufen. Der Agent zahlt aus dem Abo,
das sich an vielen Läufen erschöpft; der Bot rechnet je Aufruf ab und deckelt bei
`max_usd_per_day`. Karl steht deshalb hier auf Sonnet und dort auf Opus.

Diese Zuordnung war bis 2026-09-08 Einschätzung, keine Messung. Anastasia hat an diesem Tag
freigegeben, dass Marv sie für Karl misst (Sonnet gegen Opus, dessen sechs Prüffälle aus
`karl/evals/evals.json`, Kriterium: passt heißt gleiche Trefferquote beim billigeren Modell) —
begrenzt auf Karl, wegen des schmelzenden Kontingents des CEO. Für die übrigen Identitäten
bleibt es vorerst bei der Einschätzung; eine Ausweitung braucht eine erneute Freigabe. Details
und Begründung in `skills/gedaechtnis/anastasia.md`, Abschnitt Modellzuordnung. Ergebnis folgt
hier mit Datum, sobald Marv liefert.

Der Bot deckelt bei `max_usd_per_day`; die Reservierung vor dem Aufruf wird danach gegen den
tatsächlichen Verbrauch zurückgebucht (`reconcile`), Opus ist deshalb keine Handvoll Aufrufe.

## Gedächtnis

`skills/gedaechtnis/<name>.md` — was eine Identität weiß, ohne nachzusehen: Entscheidungen des
CEO, Tatsachen zur Lage, offene Vorgänge, jeder Eintrag mit Datum und Quelle. Fünf Identitäten
verweisen im Skill darauf (`../gedaechtnis/<name>.md`); der relative Pfad löst in allen drei
Laufzeiten auf, weil das Gedächtnis **neben** den Skills liegt und der Bot den ganzen Ordner
bekommt.

Es liegt seit dem 2026-09-08 hier im Repo statt in `~/.claude/skills/`; dort steht nur noch ein
Verweis. Vorher war es unversioniert, ungesichert und im Bot nicht erreichbar. Der abgelöste
Ordner liegt als `~/.claude/gedaechtnis.abgeloest-2026-09-07/` beiseite, gelöscht ist nichts.

**Geschrieben wird es in Claude Code**, vom Agenten oder von Hand. Der Bot mountet `skills/`
schreibgeschützt, und sein Provider ist werkzeuglos — dort ist das Gedächtnis Lesestoff. Was
eine Identität im Telegram-Gespräch erfährt, landet also **nicht** von selbst im Gedächtnis.

Marlene und Marv haben keins: Sie führen laufende Vorgänge in ihren Arbeitsbereichen unter
`~/.claude/skills/<name>-workspace/`.

Quelle der Rollen: `00_COMPANY_STATE.txt` und `interim-bus/rules/` im iCloud-Quellensatz
`Startup_Codex`, einmalig geholt am 2026-09-06. Ab jetzt gilt nur diese Ablage.
