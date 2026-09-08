# Gesamtreview Workforce — 2026-09-08, Karl (SAO-001)

**Auftrag:** CEO im Chat, 2026-09-08 00:01, „komplettes Review über alles, alle abfragen, Vorschläge, zusammenfassen". Freigabe erfasst als `CEO-CHAT-2026-09-08/PENDING-DEC`. Ausgeführt 04:00 bis 04:20. Nur lesend: kein NAS-Befehl, kein Commit, keine Löschung. Diese Datei ist die einzige Schreibwirkung neben dem Gedächtniseintrag.

## Berücksichtigte Berichte

| Identität | Bericht | Stand |
|---|---|---|
| Gerd (AI-ENG-001) | System, Neubau gegen `INVARIANTEN.md`, Testlauf, neue Befunde `G-096` bis `G-099` | vorliegend |
| Anastasia (PEO-001) | Register, Probezeiten, Agentenwechsel `058329a` | vorliegend |
| CFO (ohne Namen) | Zahlenlage je Linie, Modellkosten, Budgetdecke | vorliegend |
| Thorsten (RAS-001) | Ideenlage, Filter, Baustein C | vorliegend |
| Marlene (POA-001) | Verwaltungsstand, erster Vorgang, Werkzeuge | vorliegend |
| Marv (Skillbauer) | Skillreife, Evals, ungecommittete Änderungen | vorliegend |

**Fehlende Berichte:** keine. `NO_REPORT` gibt es nicht; jede Identität hat geliefert. **Nicht verifiziert** von allen sechs gleichermaßen: der Zustand der NAS (Container, Kanal, ausgerollter Stand), der iCloud-Quellensatz mit dem Decision Log, Google Drive mit Marlenes Registern, die ChatGPT-Verläufe.

## Gesamturteil

**Prozess: ITERATE.** Die Verfahren tragen: Invariantenseite als Maßstab, Befunde mit Nummer, Skills nach Messverfahren, Probezeit mit Evidenz. Aber die Sicherung hinkt der Arbeit hinterher. Gerds Korrekturen `G-092` bis `G-095`, sein Review und vier abgeschlossene Skillbündel liegen ungecommittet im Arbeitsbaum, und der Deploy rollt seit `de8818b` den committeten Baum aus. Der geprüfte Stand ist damit nicht der auslieferbare (Gerds `G-096`, hoch). Dazu fehlen für drei Identitäten Prüffälle, und kein Entscheidungsgate seit dem 2026-09-03 hat eine DEC-Nummer; `DEC-037` ist weiter der jüngste Eintrag.

**Fortschritt: PASS.** Der Neubau hat in fünf Tagen das geliefert, was der Prototyp in vier Tagen nie gab: Modellantwort über Telegram, Hash-Kette, Zustellabgleich, Sicherung nach dem Mac, 30 grüne Tests unter Python 3.9. Sieben Identitäten laufen als eigene Läufe, Karl ist gemessen (43/43), Marlene hat einen echten Vorgang mit Probezeit-Evidenz. Elf von sechzehn Invarianten sind mit Test belegt.

## Bewertung je Bereich, nur aus den Berichten

**System (Gerd).** Fakt: 30/30 Tests; belegt Invarianten 1, 2, 3, 5 teilweise, 6, 8, 9, 10, 12, 14, 16; nicht belegt 4, 7, 13, 15. Vier neue Befunde: `G-096` hoch, Deploy liefert Stand vor `G-092`/`G-094`; `G-097` hoch, bei erschöpftem Budget wird der Claim zurückgegeben, aber keine Runde nimmt `RECEIVED` wieder auf, die Nachricht ist still verloren; `G-098` mittel, `compose.yaml` mountet den Anthropic-Schlüssel auch für Echo; `G-099` mittel, `deploy_nas.sh` und `backup_pull.sh` ohne Test. Gerds Urteil, zitiert: „bis dahin kein Deploy". Annahme Gerd: die NAS fährt den Stand vor `G-092`, nicht gemessen.

**Rollen (Anastasia).** Fakt: sieben Identitäten im Register, fünf im Bot, Gerd und Marv bewusst nicht. Seit `058329a` alle als eigene Agenten; das Register nennt das noch nicht, ihr eigenes Versäumnis. Probezeit-Evidenz nur für Marlene; Karl, Gerd, Thorsten, CFO haben Messungen, aber kein People-Review echter Arbeit. CFO ohne Namen.

**Zahlen (CFO).** Fakt: erste Modellantwort 0,0017 USD bei 296/112 Token (HANDOVER); Tagesdecke 2,0 USD und 100 Aufrufe in `config.example.json`. Fehlend, als `unbekannt` benannt: Rockhausen Miete, Nebenkosten, Gebäudewert; Krypto-Bestand; Linie-C-Ist; Systemkosten; Steuerfristen. Ableitung CFO: die Decke trüge rechnerisch rund 1.170 Antworten des gemessenen Typs, ein Datenpunkt, keine Prognose. Der CFO kann Linie A und B derzeit nicht führen, weil ihm niemand Zahlen übergeben hat.

**Ideen (Thorsten).** Fakt: `FILTER.md` ist nie auf einen Kandidaten angewandt worden; die Rangliste in `MASTERPLAN.md` Abschnitt 7 ist ein anderes Instrument mit anderer Skala und nicht als vorläufig gekennzeichnet. Rang 1 und 2 dort sind Baustein A und B, nicht C. Kein Battle-Protokoll, keine Recherchefrage, Gedächtnis leer. Annahme Thorsten: der CEO versteht die zehn Konzepte als C-Kandidatenliste, unbelegt. Er warnt vor dem Anker der fünf Tage alten Rangliste.

**Verwaltung (Marlene).** Fakt: ein Vorgang abgeschlossen (zwei Entlassungsberichte, 2026-09-07), ein Vorgang offen (`MED-KLINIK-2026-05`, Seite 7 fehlt, Anweisung fertig), vier Kopien im Inbox-Ordner liegen noch; zwei Werkzeuge im Lauf gebaut. Fristenliste, Rechnungsjournal, Vertragsregister liegen außerhalb ihres Zugriffs. Annahme Marlene: Rockhausen und Verträge ruhen, nicht bestätigt.

**Skills (Marv).** Fakt: Karl 43/43, Marv 40/40, Gerd 37/38 gemessen; Thorsten, Anastasia, CFO nie gemessen, keine Prüffälle; `3loop` liegt nur auf diesem Rechner, nicht im Repo. Vier Bündel in `skills/` sind fertig und ungesichert; die Belegberichte liegen unversioniert in `~/.claude`. Annahme Marv: Karl nach der Gedächtnis-Auslagerung nicht nachgemessen.

## Widersprüche und Auflösung

- **Filter gegen Rangliste.** Thorstens Urteil: der Filter ist nie gelaufen, die Masterplan-Rangliste ist die faktische Entscheidungsgrundlage und das schwächere Instrument. Der Masterplan (Claude Code, 2026-09-03/06) hält das Modell A/B/C für bestätigt. Auflösung: der CEO übergibt drei bis fünf C-Kandidaten und erklärt, welches Instrument gilt; Owner Tobias, Vorlage S-2 unten.
- **Gerd gegen den Betrieb.** Gerd sagt „kein Deploy bis Commit". Auf der NAS läuft laut HANDOVER Stand `de8818b` oder jünger; ob das Modell dort produktiv antwortet, ist nicht verifiziert. Auflösung: Commit der vier Dateien, dann ein gemessener Deploy mit `verify`; Owner Claude Code, Gate Gerds Nachcheck des Diffs.

## Roadmap

| # | Task | Owner | Output | Gate |
|---|---|---|---|---|
| 1 | Gerds Korrekturen `G-092` bis `G-095` und `REVIEW_GERD.md` committen, je Befund ein Commit, gezieltes `git add` | Claude Code | Commits im Repo | `git status` in `workforce/` leer; 30/30 Tests grün; kein Deploy vorher |
| 2 | Vier Skillbündel committen (Gedächtnisverweise, Gerd v1 samt `evals/`, Marv R2, `BEWERTUNG.md`) | Claude Code mit Marv | vier Commits | `git status` in `skills/` leer außer bewusst Offenem |
| 3 | `G-097` beheben: Wiederaufnahme von `RECEIVED` und abgelaufenen Claims zu Rundenbeginn, mit Test | Claude Code | Commit plus Test | Gerd bestätigt im Nachcheck |
| 4 | `G-098`, `G-099`: Secret-Mount nach Provider, Tests für `deploy_nas.sh` und `backup_pull.sh` | Claude Code | Commits | Gerd bestätigt |
| 5 | Invarianten 4, 7, 13, 15 belegen oder auf der Seite datiert als „offen bis Meilenstein N" kennzeichnen | Claude Code, Gerd prüft | Änderung `INVARIANTEN.md` | Gerd akzeptiert die Kennzeichnung |
| 6 | Deploy des committeten Standes auf die NAS, danach `verify` | Claude Code | Manifest und `verify PASS` | CEO-Freigabe im Chat für den NAS-Lauf; Task 1 bis 4 erledigt |
| 7 | Register um Agentenlauf ergänzen; `3loop` ins Repo, Register und Agent | Anastasia, Marv | `skills/README.md`, Commit | Anastasia zeichnet |
| 8 | Karl nach Gedächtnis-Auslagerung gegen sechs Prüffälle nachmessen; Prüffälle für Thorsten, dann Anastasia, CFO | Marv | Messberichte | CEO-Entscheidung zur Messpflicht (Budget) |
| 9 | Seite 7 Klinikbericht nachscannen; Rechnungen und Beihilfe/PKV zu beiden Aufenthalten klären; vier Inbox-Kopien abschließen | Tobias scannt, Marlene führt | abgeschlossener Vorgang | Marlene meldet „abgelegt" |
| 10 | Zahlen an den CFO: Rockhausen-Ist von Marlene, Krypto-Bestand vom CEO, Modellkosten aus der Zustandsdatei über Wochen | Marlene, Tobias, Claude Code | erste Monatsübersicht | CFO meldet Linie A und B „geführt" |
| 11 | C-Kandidaten übergeben, Antrag beim Dienstherrn offen formuliert, dann ein Filterlauf je Kandidat mit Quellen | Tobias, dann Thorsten | Filterurteile | Vorlage S-1 bis S-3 entschieden |
| 12 | ChatGPT-Export in die Gedächtnisse von Karl und Thorsten | Tobias liefert, Karl trägt ein | Gedächtniseinträge | Export liegt vor |

Reihenfolge nach Schaden: 1 und 2 sichern, was fertig ist; 3 verhindert stillen Nachrichtenverlust; 6 braucht 1 bis 4 und eine Freigabe. 9 bis 12 laufen parallel, sie hängen am CEO und nicht am Code.

## STOP und HOLD

- **STOP: kein Deploy auf die NAS**, bis Task 1 bis 4 committet sind und Gerd den Diff nachgeprüft hat (`G-096`). Gerds Urteil, unverändert übernommen.
- **HOLD: kein neuer Meilenstein im Neubau** (Phase 1 Gedächtnis im Bot, Phase 3 Zeitplan), bis `G-097` behoben ist. Ein System, das sich meldet, darf keine Nachricht still verlieren.
- **HOLD: keine weiteren Evals mit Modellkosten**, bis der CEO die Messpflicht entschieden hat (Vorlage B-2).
- **HOLD: `HO-027`** ruht weiter; Marlene arbeitet im Neubau.

## CEO-Entscheidungen, als Vorlagen

**Klasse Strategie, S-1 bis S-3.** Sachverhalt: Der Filter ist nie gelaufen; die Rangliste im Masterplan ist ein anderes Instrument. Optionen: (a) drei bis fünf C-Kandidaten aus 2, 3, 6, 8, 9 benennen und den Filter darauf laufen lassen, Nutzen klare Grundlage, Risiko Aufwand von sechs Wochen, Aufwand ein Abend Auswahl plus Thorstens Läufe; (b) die Masterplan-Rangliste als Entscheidung übernehmen, Nutzen sofort, Risiko keine Quellenpflicht und kein Ausschlussschritt, Aufwand null; (c) beides parallel, Nutzen Anker sichtbar gemacht, Risiko zwei Zahlen für dieselbe Sache, Aufwand wie (a). Empfehlung: (a), und der Antrag beim Dienstherrn wird jetzt offen für das Feld „Brandschutzwissen" gestellt, weil er jeden Kandidaten gleichzeitig blockiert. Satz fürs Log: **Klasse Strategie: Der CEO benennt bis zum 2026-09-12 drei bis fünf Kandidaten für Baustein C, erklärt `FILTER.md` zum maßgeblichen Instrument und stellt den Nebentätigkeitsantrag offen für das Feld Brandschutzwissen.**

**Klasse Produktives, P-1.** Sachverhalt: `G-096`, der committete Stand ist nicht der geprüfte. Optionen: (a) Commit und gemessener Deploy nach Gerds Nachcheck, Nutzen geprüfter Stand läuft, Risiko ein Betriebsfenster, Aufwand zwei Stunden; (b) NAS bleibt auf altem Stand, Nutzen keine Änderung, Risiko `G-092` und `G-094` offen im Betrieb, Aufwand null. Empfehlung: (a). Satz: **Klasse Produktives: Der CEO gibt den Deploy des committeten Neubau-Standes auf die NAS frei, sobald Gerd den Diff `G-092` bis `G-099` nachgeprüft hat.**

**Klasse Budget, B-1 und B-2.** Sachverhalt: Tagesdecke 2,0 USD und 100 Aufrufe stehen in einer Beispieldatei, nicht als Entscheidung; Evals kosten Modellbudget; drei Identitäten sind ungemessen. Optionen: (a) Decke bestätigen und Messpflicht vor Betrieb für jede Bot-Identität, Nutzen Verlässlichkeit, Risiko Kosten je Messung im einstelligen Eurobereich, Aufwand Marv je Skill ein Tag; (b) ungemessen im Betrieb lassen, Nutzen sofort nutzbar, Risiko unbekannte Qualität ohne Zahl, Aufwand null; (c) nur Thorsten messen, Nutzen der meistgenutzte zuerst, Risiko zwei bleiben offen, Aufwand ein Tag. Empfehlung: (c) jetzt, (a) als Regel ab Phase 2. Satz: **Klasse Budget: Der CEO bestätigt die Tagesdecke von 2,0 USD und 100 Aufrufen und gibt eine Messung Thorstens frei; jede weitere Bot-Identität wird vor dem Betrieb gemessen.**

**Klasse Personal, PE-1 bis PE-3.** Sachverhalt: CFO ohne Namen seit 2026-09-06; Marlene nach dem ersten Vorgang mit Evidenz ohne Urteil; Marv ohne Status als Mitarbeiter. Optionen je Punkt: entscheiden jetzt oder freitags. Empfehlung: Name jetzt, weil das Register und der Skillkopf daran hängen; Marlene weiter in Probezeit bis zum zweiten Vorgang; Marv als Werkzeugrolle ohne Botsitz führen. Satz: **Klasse Personal: Der CEO vergibt dem CFO einen Namen, führt Marlenes Probezeit bis zum zweiten echten Vorgang fort und führt Marv als Werkzeugrolle ohne Botsitz.**

**Klasse Rechte, R-1.** Sachverhalt: Marlene hat keinen Lesezugang zu ihren eigenen Registern in Google Drive und zur NAS-Inbox; sie arbeitet über Kopien, die Claude Code bereitstellt. Optionen: (a) lesender Zugang über einen Abrufer hinter der Datengrenze, Nutzen vollständiger Verwaltungsstand, Risiko rührt an Phase 4 und Invariante 10, Aufwand Gerds Review vorher; (b) Kopien wie bisher, Nutzen nichts ändert sich, Risiko Marlene bleibt blind für Fristen, Aufwand null. Empfehlung: (b) bis Phase 4, dann (a) mit eigener Invariantenzeile. Satz: **Klasse Rechte: Der CEO belässt Marlene bis Phase 4 auf dem Kopienweg und entscheidet den lesenden Zugang mit der Paperless-Phase.**

**Offen und nicht neu:** DEC-Nummern für `INVARIANTEN.md`, den Neubau (`CEO-CHAT-2026-09-03`) und dieses Review (`CEO-CHAT-2026-09-08`). Gerd hat das dreimal angemahnt; ich wiederhole es als Tatsache, nicht als Vorlage: die Nummer entsteht im iCloud-Quellensatz, Owner Tobias.

## Kontrolle

Beim nächsten Kontakt sehe ich nach: ist `git status` in `workforce/` und `skills/` leer, hat Gerd `G-097` bestätigt, liegen Kandidaten für C und der Krypto-Bestand vor, und hat das Log Nummern für die drei Chat-Freigaben.

## Nächster Schritt

Gerds Korrekturen `G-092` bis `G-095` und `REVIEW_GERD.md` committen, je Befund ein Commit, kein Deploy davor; Owner Claude Code, Gate: Gerds Nachcheck des Diffs.

## Nachtrag 2026-09-08, 07:30

Task 1 wurde um 05:50 durch `4392ab7` erledigt, in einem Commit statt je Befund; `G-096` ist damit geschlossen. Task 2 ist in fünf Commits gesichert (`d86c3a3` bis `c22ca8d`). Task 3, `G-097`, ist behoben und getestet, Gerds Nachcheck steht aus. Der STOP für den Deploy bleibt, bis der Nachcheck vorliegt und der CEO P-1 entscheidet.
