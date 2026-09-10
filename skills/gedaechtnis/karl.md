# Gedächtnis Karl (SAO-001)

Was Karl weiß, ohne nachzusehen. Jeder Eintrag trägt Datum und Quelle. Eine spätere Entscheidung ersetzt eine frühere; die frühere bleibt durchgestrichen stehen. Diese Datei gehört nicht zum Skillpaket und darf Tatsachen enthalten, die im Skill nichts zu suchen haben.

## Entscheidungen des CEO

| Datum | Entscheidung | Quelle |
|---|---|---|
| 2026-09-08 | **Klasse Produktives:** Deploy `ca1bd20` über `deploy_nas.sh` freigegeben; danach `verify` und Gerds Review nach dem Lauf. Ausgeführt, Nachweis `workforce/evidence/2026-09-08_deploy_ca1bd20.md`. | Chat 2026-09-08 (`CEO-CHAT-2026-09-08/PENDING-DEC`) |
| 2026-09-08 | **Klasse Strategie:** `FILTER.md` ist das Instrument für Baustein C. Kandidaten: laut CEO „hab ich schon erklärt" — im Repo liegt keine Liste; Lesart: er hat sie mündlich oder in ChatGPT genannt, nachzureichen. **Nebentätigkeitsantrag: nein**, wird jetzt nicht gestellt. | Chat 2026-09-08 |
| 2026-09-08 | **Klasse Budget:** Tagesdecke 2,0 USD und 100 Aufrufe bestätigt; eine Messung Thorstens freigegeben. | Chat 2026-09-08 |
| 2026-09-08 | **Klasse Personal:** Der CFO heißt **Wolle**. Marlenes Probezeit wird fortgeführt. Marv ist **Mitarbeiter**, nicht Werkzeugrolle (unter Anastasia, von ihr eingetragen `911be4b`). **Karl wird COO auf Probe.** | Chat 2026-09-08 |
| ~~2026-09-08~~ | ~~**Klasse Rechte:** Marlene bleibt bis Phase 4 auf dem Kopienweg.~~ Ersetzt durch `DEC-044`: Marlene arbeitet direkt auf Google Drive und NAS. | Chat 2026-09-08, ersetzt 2026-09-10 |
| 2026-09-08 | **3-Loop angenommen:** Vorschlag A (Firma mit COO) mit den drei Auflagen aus B, C, D: Entscheidungstermin statt Chat-Freigaben unter der Woche, Phase 3 vor Phase 4, eingefroren, was keine Arbeit hat. Takt nach Wahl des COO „im Sinne der Wirtschaftlichkeit": **Montag Lage, Donnerstag Entscheidungen, Freitag bis Sonntag Wochenendbetrieb.** Organigramm gilt (`skills/ORGANIGRAMM.md`). | Chat 2026-09-08 („kannste alles so umsetzen", `PENDING-DEC`) |
| 2026-09-08 | Phase 3 gebaut: `Config.schedule`, `App.check_schedule()`, Montag/Donnerstag konfiguriert. 60 Tests, Gegenprobe bestanden. Deploy steht aus, Donnerstagsvorlage. | `workforce/evidence/2026-09-08_phase3_schedule.md` |
| 2026-09-08 | **Modell-Loop entschieden:** Schaltwort für Denken ist `!` am Anfang; die ChatGPT-Assistentin ist keine Mitarbeiterin, Export dann Archiv; Gerd legt seinen LLM-Server aus Codex ins Repo. Auflage 1 (Gedächtnis für alle sieben) umgesetzt; Auflage 2 (zwei Modelle je Identität) Meilenstein nach dem Phase-3-Deploy; Ollama wartet. | Chat 2026-09-08 („! / Export / Gerd legt ihn ins Repo") |
| 2026-09-10 | **Donnerstag 1:** P-2 Deploy Phase 3 (`35e7ae3`) und R-2 Ordnerrechte freigegeben und ausgeführt; erste Donnerstagsnachricht zugestellt (0,047 USD, Opus). S-2 in Arbeit bei Thorsten. | Chat 2026-09-10 („ja"), Nachweis `workforce/evidence/2026-09-10_deploy_phase3_und_rechte.md` |
| 2026-09-10 | **Eigener Fehler `G-114`:** Deploy gegen Gerds rotes Gate vom 2026-09-09, weil ich `REVIEW_GERD.md` vor dem Deploy nicht neu gelesen habe; Vorlage P-2 nannte `G-112`/`G-113` nicht. Regel 71: Befunddatei im Moment des Handelns lesen, Freigabesatz nennt die offenen Nummern. `G-112` bis `G-116` behoben, P-3 vorgelegt. | Gerds Review nach dem Lauf, 2026-09-10 |
| 2026-09-10 | **Antwortform:** Dem CEO ist es zu viel Text. Jede Antwort kurz, an sein Wissen angepasst, immer als Vorlage mit anschließender To-do-Liste. Keine Blümchen. | Chat 2026-09-10 |
| 2026-09-10 | **Betriebsmodus:** Alles läuft über Karl. Karl erreicht die Mitarbeiter selbst (Agenten: Gerd, Anastasia, Thorsten, Marv, Wolle), der CEO grätscht nicht dazwischen und bekommt Stück für Stück eine Vorlage. **Marlene bleibt außen vor**, der CEO spricht sie direkt an. Gerd in Codex erreicht Karl nur über die Dateien (`REVIEW_GERD.md`, `HANDOVER.md`); Gerd in Claude Code startet Karl selbst. Die fehlende Übersicht war das Problem, nicht der Wille. | Chat 2026-09-10 |
| 2026-09-10 | **DEC-038 bis DEC-045 ins Entscheidungslog eingetragen**, auf Anweisung des CEO durch Karl; Sicherung `03_DECISION_LOG.txt.vor-DEC-038.bak` daneben. Alle Chat-Freigaben seit 2026-09-03 haben damit eine Nummer. | iCloud `03_DECISION_LOG.txt` |
| 2026-09-07 | Der nächtliche Tagesprozess aus Codex mit Berichten bis 01:45 ist Archiv. Ein fehlender Claude-Bericht dort ist kein Auftrag mehr; integriert wird auf Anfrage und ~~freitags~~ montags und donnerstags (seit 2026-09-08). | bis heute in `karl/SKILL.md`, Abschnitt „Was du weißt" |

## Tatsachen zur Lage

| Stand | Tatsache | Quelle |
|---|---|---|
| 2026-09-07 | Modell des CEO: **A** Vermietung als Kern und **B** Krypto als Reserve laufen auf der Leine; **C** ist der dritte Baustein aus geistiger, KI-vervielfältigbarer Arbeit zum höchsten Ertrag je Stunde, gefunden über den Filter. | Masterplan, bis heute in `karl/SKILL.md` |
| 2026-09-07 | Phasen des Masterplans: 0 benutzen und sichern, 1 Gedächtnis, 2 Identitäten als Skills, 3 das System meldet sich (Briefing, Fristen, CFO), 4 Dokumente (Paperless, lesend) und die Entscheidung über Mac mini mit lokalem Modell, 5 Werkzeuge hinter Freigabe. | Masterplan, bis heute in `karl/SKILL.md` |
| 2026-09-09 | Gerds „LLM-Server aus Codex" ist der `OllamaProvider` in `workforce/providers.py`: seit `02acf9b` (2026-09-03) im Repo, von Gerd in `4392ab7` gehärtet (`G-092`, nur Loopback und `host.docker.internal`). Die Frage aus dem Modell-Loop ist damit erledigt. Für einen echten Lauf fehlen drei Dinge: ein laufendes Ollama (Mac mini), der Netzweg NAS → Mac mini mit Gerds Abnahme, und ein lokales Modell in der Allowlist `models.py` (dort stehen nur Echo, Haiku, Sonnet, Opus). | CEO-Hinweis 2026-09-09, `git log -- workforce/providers.py` |
| 2026-09-08 | Neue Befunde Gerd `G-096` (Deploy rollt HEAD ohne die Korrekturen aus) bis `G-099`; Invarianten 4, 7, 13, 15 nicht belegt; Filter aus `FILTER.md` nie gelaufen (Thorsten); CFO hat keine Zahlen zu Linie A und B; sieben Identitäten seit `058329a` als eigene Agenten. | Gesamtreview 2026-09-08, Berichte der sechs |
| 2026-09-07 | Rangfolge bei Widerspruch zwischen Quellen: Decision Log, dann Masterplan und Invarianten, dann Übergabe, Chatnachrichten zuletzt. | bis heute in `karl/SKILL.md` |

## Offene Vorgänge

| Seit | Vorgang | Stand |
|---|---|---|
| 2026-09-07 | Import der ChatGPT-Verläufe mit Karl in dieses Gedächtnis | wartet auf Export durch den CEO; am 2026-09-08 erneut zugesagt |
| 2026-09-08 | 3-Loop über das gesamte Projekt und Organigramm-Vorschlag, vom CEO verlangt | angenommen und umgesetzt; offen: Phase 3 als nächster Meilenstein, `G-107`/`G-108` als Donnerstagsvorlagen, Marv misst Karl nach der Skilländerung nach |
| 2026-09-08 | Gesamtreview über alle sechs Identitäten, angeordnet vom CEO im Chat 00:01 (`CEO-CHAT-2026-09-08/PENDING-DEC`), ausgeführt 04:00 | geschrieben nach `workforce/reviews/2026-09-08_gesamtreview_karl.md`; Prozess ITERATE, Fortschritt PASS; STOP Deploy bis `G-092`–`G-095` committet (Gerd `G-096`); fünf Vorlagen offen (S, P, B, PE, R); Kontrolle beim nächsten Kontakt: `git status` leer, `G-097` bestätigt, C-Kandidaten und Krypto-Bestand da, DEC-Nummern |

## Herkunft

Angelegt am 2026-09-07 durch Marv. Der Abschnitt „Was du weißt, ohne nachzusehen" wurde aus `karl/SKILL.md` hierher verschoben, weil Tatsachen veralten und eine Skilldatei die Stelle beschreibt, nicht die Lage. Die Regeln dieses Abschnitts (Vorrat statt Auftrag, Klasse Externes, wahrscheinlichste Lesart, `NO_REPORT` nur für Personen) sind im Skill geblieben.
