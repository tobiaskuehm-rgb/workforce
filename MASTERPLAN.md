# Masterplan Workforce — Stand 2026-09-03, nach dem ersten Tag im Betrieb

**Status:** Vorschlag von Claude Code aus dem CEO-Brainstorming vom 2026-09-03. Entscheidungen
darin bekommen ihre Nummer im Decision Log (`G-006`). Maßstab bleibt `INVARIANTEN.md`.

## 1. Einordnung des Brainstormings

Die zehn Stichworte sind drei Sorten Dinge:

| Sorte | Stichworte | Was es im Neubau ist |
|---|---|---|
| **Wer antwortet** | Marlene, Thorsten, Gerd, Anastasia | eine Identität: Name, Modell, Policy, Systemtext, eigenes Gedächtnis |
| **Woran gearbeitet wird** | Geschäftsideen-Suche, Krypto, Immobilien, Privatbereich, CFO | eine Domäne: gehört zu einer Identität, bringt Daten und Regeln mit |
| **Wo es läuft** | Ollama, Mac mini | Infrastruktur: entscheidet, welche Daten das Haus verlassen müssen |

Rollen laut Registry (`001_employee_registry.sql`) und HO-027:

| Identität | Rolle | Domäne, die passt | Anmerkung |
|---|---|---|---|
| **Marlene** `POA-001` | Private Office Assistant | Privatbereich | Termine, Schriftverkehr, Erinnerungen; später Paperless |
| **Thorsten** `RAS-001` | Research & Strategy Analyst | Geschäftsideen-Suche; Recherche zu Krypto und Immobilien | Analyse, Strukturierung, Gegenargumente |
| **Anastasia** `PEO-001` | People & Organization | heute keine Domäne aus der Liste | bleibt angelegt, bekommt Arbeit, wenn es Menschen zu organisieren gibt |
| **Gerd** `AI-ENG-001` | AI Engineer / Architekt | Review des Systems | bleibt der Prüfer (Codex), keine Telegram-Identität |
| **Karl** `SAO-001` | Strategy & Operations, Koordinator | nicht genannt | Kandidat für die Standardidentität statt „ASSISTENZ" |
| **CFO** | neu, ohne Namen | Finanzen, Budgets, Fristen; Krypto und Immobilien als Positionen | Name und DEC-Eintrag fehlen |

**Krypto und Immobilien sind keine Identitäten, sondern zwei Domänen mit derselben Regel:**
Das System informiert, strukturiert und rechnet vor. Es handelt nicht, es hat keine Werkzeuge,
und es gibt keine persönliche Anlageberatung — das steht im Systemtext, nicht nur im Kopf.

**Ollama und Mac mini gehören zusammen.** Auf der Synology ist ein lokales Modell zu langsam
für Antworten. Auf einem Mac mini mit Apple Silicon ist es brauchbar, und dann darf die
Datengrenze für private Daten `FULL` stehen, weil nichts das Haus verlässt. Ohne Mac mini
ist Ollama nur ein Testprovider.

## 2. Drei Varianten aus dem Brainstorming

**A — Ein Bot, viele Hüte.** Alle Identitäten im vorhandenen Bot, angesprochen mit `@MARLENE`,
`@THORSTEN`, `@CFO`; jede mit Systemtext, Policy, Budget und eigenem Gedächtnis. Karl als
Standard. Aufwand: je Identität ein Konfigurationseintrag, dazu einmal das Gedächtnis.

**B — Ein Bot je Rolle.** Marlene, Thorsten und CFO bekommen je einen eigenen Telegram-Bot und
Chat. Klarere Trennung im Telefon, aber drei Token, drei Abfrager, dreimal Konfiguration.

**C — Werkstatt zuerst.** Vor neuen Identitäten die Grundlagen: Gedächtnis, Sicherung, Paperless
für Dokumente, tägliche Zusammenfassung. Identitäten erst, wenn sie echte Daten haben.

## 3. Drei Varianten unabhängig davon

**D — Mac mini als Zentrale.** Der Kern zieht auf einen Mac mini, Ollama daneben; die NAS wird
Speicher und Sicherung. Private Domänen laufen lokal mit `FULL`, geschäftliche Recherche geht
weiter zu Claude. Einmalig rund 700 bis 1.000 Euro.

**E — Das System meldet sich.** Bisher antwortet es nur. Geplante Läufe: morgens ein Briefing,
freitags die Finanzübersicht aus dem, was du unter der Woche geschickt hast, Erinnerungen an
Fristen. Technisch ein Zeitplan im Kern und Nachrichten ohne vorherige Frage.

**F — Werkzeuge hinter Freigabe.** Lesende Zugriffe — Kalender, Dokumentensuche, Kurse — als
getrennte Abrufer, deren Ergebnis als Daten durch die Grenze geht, und jede Aktion nur nach
einem Ja im Chat. Der größte Nutzen und das größte Risiko: Es rührt an die Invariante
„werkzeugloser Agent" und braucht eine eigene Zeile auf der Seite und Gerds Review vorher.

## 4. Bewertung in drei Perspektiven

Noten 1 bis 5, 5 ist am besten.

| Variante | Nutzen im Alltag | Sicherheit und Kosten | Aufwand bis es läuft | Summe |
|---|---|---|---|---|
| A Ein Bot, viele Hüte | 4 | 5 — nichts ändert sich am Modell | 5 — Tage | **14** |
| B Ein Bot je Rolle | 3 | 4 | 2 — dreifacher Betrieb | 9 |
| C Werkstatt zuerst | 2 kurzfristig, 4 später | 5 | 3 — Wochen ohne sichtbaren Gewinn | 10 |
| D Mac mini | 3 | 5 — private Daten bleiben lokal | 2 — Kauf, Umzug, Ollama | 10 |
| E Meldet sich | 5 — das ist, was eine Assistenz ausmacht | 4 — Kosten planbar, Budget deckelt | 4 — ein Zeitplan im Kern | **13** |
| F Werkzeuge | 5 | 2 — bricht die Grundannahme | 2 — Isolation, Freigabe, Review | 9 |

## 5. Fazit

A und E zusammen sind der Weg: Identitäten als Konfiguration im einen Bot, und ein System,
das sich meldet. C ist kein Gegenmodell, sondern die Reihenfolge innerhalb von A: Gedächtnis
und Sicherung kommen vor der dritten Identität. D wird eine Entscheidung, sobald private
Daten regelmäßig an ein fremdes Modell gehen würden — vorher ist es ein Kauf ohne Anlass. F
kommt zuletzt oder gar nicht, und nur mit eigener Invariante. B nicht.

## 6. Masterplan

Jede Phase endet mit einem echten Lauf. Gerd prüft danach gegen die Invariantenseite. Kosten
für Modelle bei heutiger Nutzung: einstellige Euro im Monat, gedeckelt durch die
Konfiguration.

### Phase 0 — Diese Woche: benutzen und absichern
- Täglich benutzen, Störungen notieren. Nichts vorher bauen.
- **Sicherung weg von der NAS:** nächtlich `workforce backup` per DSM-Aufgabe, Kopie zieht
  der Mac per ssh. Test: Wiederherstellung in leeren Container, `verify` PASS (Invariante 13).
- DEC-Eintrag für den Neubau und für diesen Plan durch den CEO.
- Ergebnis: das System überlebt einen Plattenausfall und einen Neustart.

### Phase 1 — Woche 2: Gedächtnis und Karl
- **Gedächtnis je Identität:** die letzten Wechsel aus der Datei gehen als `context` mit,
  begrenzt auf die Datengrenze; Policy je Identität entscheidet, ob überhaupt.
- Standardidentität wird **Karl**, Systemtext aus der Registry-Rolle.
- Test: „und weiter?" versteht den Bezug; ein Wechsel zu `@MARLENE` sieht Karls Kontext nicht.
- Ergebnis: ein Gespräch statt einzelner Fragen.

### Phase 2 — Woche 3: Marlene und Thorsten
- **Marlene**, Policy `BODY`, Systemtext aus dem HO-027-Skillpaket, Domäne Privatbereich.
- **Thorsten**, Domäne Geschäftsideen: strukturiert, bewertet, nennt Gegenargumente; dazu
  Recherche-Aufträge zu Krypto und Immobilien als Wissensfragen, nie als Empfehlung.
- Budget je Identität statt nur je Tag.
- Ergebnis: drei Ansprechpartner in einem Chat.

### Phase 3 — Woche 4 bis 5: Das System meldet sich
- Zeitplan im Kern: Morgenbriefing, Freitagsübersicht, Fristen. Jede geplante Nachricht ist
  ein normaler Ausgang mit Audit, Budget und Kill Switch.
- **CFO** als Identität, Name durch den CEO: führt eine einfache Übersicht aus dem, was du
  schickst — Einnahmen, Ausgaben, Positionen in Krypto und Immobilien — und rechnet vor.
- Ergebnis: eine Assistenz, die nicht nur antwortet.

### Phase 4 — Monat 2: Dokumente
- Paperless-ngx auf der NAS, Marlene und CFO lesen daraus über einen Abrufer, dessen Ergebnis
  als Daten durch die Grenze geht. Erste Form von F, lesend, ohne Aktion.
- Entscheidungspunkt **Mac mini**: Gehen jetzt regelmäßig private Dokumente an ein fremdes
  Modell? Wenn ja, D — Kern und Ollama auf den Mac mini, private Identitäten lokal mit `FULL`.
- Ergebnis: das System kennt deine Unterlagen, und du weißt, wo sie hingehen.

### Phase 5 — Monat 3, optional: Werkzeuge hinter Freigabe
- Nur mit neuer Zeile auf der Invariantenseite und Gerds Review vorher. Jede Aktion nach
  einem Ja im Chat, jeder Abrufer isoliert, Ergebnis nur als Daten.

### Was in jeder Phase gilt
- Eine Phase, ein Lauf, dann Review. Ein Befund ohne dauerhaften Schaden wird ein Test.
- Kein Handel, keine Anlageberatung, keine Werkzeuge ohne Phase 5.
- Jede Identität hat Policy, Budget und Gedächtnis für sich. Was Marlene weiß, weiß Thorsten
  nicht.
- Der Prototyp bleibt Orakel; Anastasia und Gerd bleiben angelegt, ohne Arbeit, bis es sie gibt.

## 7. Unternehmenskontext (CEO, 2026-09-03) und zehn Konzepte

**Lage:** Haupterwerb Beamter im feuerwehrtechnischen Dienst. Daneben private Vermietung,
Kryptoanlagen, Nebentätigkeit im Bau. Ziel: ein Unternehmen mit kleiner Belegschaft, und die
Belegschaft sind die KI-Identitäten.

**Zwei Rahmen, die jedes Konzept prägen.** Erstens das Nebentätigkeitsrecht: Jede gewerbliche
Tätigkeit braucht die Genehmigung des Dienstherrn und hat Zeit- und Einkommensgrenzen; die
Verwaltung eigenen Vermögens ist in der Regel frei. Was davon im Einzelfall gilt, klärt der
Dienstherr, nicht dieses Dokument. Zweitens ist die Zeit die knappe Größe, nicht das Kapital:
Das Beamteneinkommen ist die Basis, die KI-Belegschaft soll Kapazität ohne eigene Stunden
liefern — also alles, was Verwaltung, Recherche, Rechnen und Schreiben ist.

**Zehn Konzepte**, kurz; Bewertung und Reihenfolge in der Chat-Antwort vom 2026-09-03:

1. **Vermietung als Kern.** Bestand professionell verwalten, alle zwei bis drei Jahre ein Objekt
   dazu; Marlene Verwaltung, CFO Rücklagen und Cashflow, Thorsten Objektanalyse.
2. **Bau: von der Hand zur Aufsicht.** Baubegleitung, Angebotsprüfung, Mängelverfolgung,
   Bautagebuch; das System dokumentiert, er entscheidet vor Ort.
3. **Brandschutz-Beratung.** Fachwissen aus dem Hauptberuf für Vermieter und Kleinbetriebe;
   Vorlagen und Schulungsunterlagen aus dem System. Genehmigung und Interessenkollision zuerst klären.
4. **Sanieren mit Eigenleistung.** Kaufen, mit Bau-Können herrichten, vermieten; CFO rechnet,
   Thorsten sucht Förderung. Beim Verkauf die Grenze zum gewerblichen Grundstückshandel beachten.
5. **Krypto als Reserve mit Regeln.** Kein Handel durch das System; schriftliche Allokation,
   Rebalancing-Termine, Steuerdokumentation. CFO führt, der Mensch handelt.
6. **Verwaltung für andere Kleinvermieter.** Marlene als Produkt, zwei bis fünf Kunden in der
   Region; Gewerbe, also Genehmigung.
7. **Möblierte oder Ferienvermietung.** Höhere Rendite, mehr Kommunikation, die das System
   übernimmt; örtliche Regeln zur Zweckentfremdung prüfen.
8. **Lager- und Werkstattflächen für Handwerker.** Netzwerk aus dem Bau, Nachfrage im ländlichen
   Raum; Thorsten Markt, Marlene Mieter.
9. **Das System selbst als Produkt.** KI-Büro für Nebenerwerber und Kleinvermieter; Kern offen,
   Einrichtung bezahlt. Technisch nah, Markt unbekannt.
10. **Die Klammer: Firma mit KI-Belegschaft.** Ein Dach über Vermietung, Bau und Beratung, CFO
    konsolidiert; Rechtsform und Steuern mit dem Steuerberater. Schritt drei bis fünf Jahre.

### Bewertung der Konzepte (2026-09-03, vier Gesichtspunkte)

Vier Gesichtspunkte, Noten 1 bis 5: **Ertrag und Skalierung** (was es einbringt und ob es ohne
mehr Stunden wächst), **Recht und Risiko** (Nebentätigkeitsrecht, Kapitalbindung, Haftung,
Schwankung), **Zeit und Passung** (wie viele Stunden es vom CEO braucht und wie viel davon die
KI-Belegschaft trägt) und **Körperliche Arbeit** (5 = keine, 1 = überwiegend körperlich; der
Hauptberuf ist selbst körperlich, und Verletzung oder Erschöpfung trifft das Grundeinkommen).
Konzept 0 ist das Ursprungskonzept des CEO: jetzt ein Unternehmen mit kleiner KI-Belegschaft
als Dach über den drei bestehenden Linien.

| # | Konzept | Ertrag | Recht/Risiko | Zeit/Passung | Körperlich | Summe | Rang |
|---|---|---|---|---|---|---|---|
| 1 | Vermietung als Kern | 4 | 5 | 5 | 4 | **18** | 1 |
| 5 | Krypto als Reserve mit Regeln | 2 | 4 | 5 | 5 | **16** | 2 |
| 10 | Die Klammer, in drei bis fünf Jahren | 3 | 3 | 4 | 5 | 15 | 3 |
| 0 | Ursprungskonzept: die Firma jetzt | 3 | 2 | 4 | 5 | 14 | 4 |
| 6 | Verwaltung für andere Kleinvermieter | 3 | 3 | 4 | 4 | 14 | 4 |
| 3 | Brandschutz-Beratung | 4 | 2 | 3 | 4 | 13 | 6 |
| 8 | Lager- und Werkstattflächen | 3 | 3 | 4 | 3 | 13 | 6 |
| 2 | Bau: von der Hand zur Aufsicht | 3 | 3 | 3 | 3 | 12 | 8 |
| 9 | Das System als Produkt | 2 | 4 | 1 | 5 | 12 | 8 |
| 7 | Möblierte oder Ferienvermietung | 3 | 3 | 3 | 2 | 11 | 10 |
| 4 | Sanieren mit Eigenleistung | 4 | 2 | 2 | 1 | 9 | 11 |

**Fazit.** Das Ursprungskonzept ist als Ziel richtig und als erster Schritt falsch: Eine Firma
ohne laufendes Geschäft darunter ist Struktur, die Genehmigung, Kosten und Zeit bindet, bevor
sie etwas trägt. Die Firma entsteht aus Konzept 1 mit dem KI-Backoffice, Konzept 5 als Reserve,
und einer genehmigten zweiten Linie aus 2 oder 3. Konzept 10 ist dann kein Projekt mehr,
sondern ein Name für das, was schon läuft.

### Lernbedarf und Investitionsbedarf je Konzept (2026-09-03)

Zahlen sind grobe Spannen aus dem Gedächtnis, keine Angebote; Zulassungsfragen sind mit
„prüfen" markiert und gehören zu Dienstherr, IHK oder Steuerberater. In der Reihenfolge des
Rankings.

| # | Konzept | Lernbedarf, Ausbildung | Investition einmalig | Laufend je Jahr |
|---|---|---|---|---|
| 1 | Vermietung als Kern | Mietrecht und Nebenkostenabrechnung in Grundzügen (VHS/IHK-Kurs, Haus & Grund); Anlage V. Kein Abschluss nötig. | Nächstes Objekt: 20–30 % Eigenkapital plus Kaufnebenkosten 8–12 % (Grunderwerbsteuer Thüringen 5 %, prüfen; Notar und Grundbuch ~2 %; Makler bis 3,57 %) | Rücklage 1–1,5 % des Gebäudewerts, Verwaltung im System ~50 € Modellkosten |
| 5 | Krypto als Reserve | Steuerliche Behandlung (Haltefrist ein Jahr, Freigrenze, prüfen), Verwahrung. Kein Kurs, ein Wochenende Lesen. | Hardware-Wallet 80–150 € | Tracking-Werkzeug 0–150 € |
| 10 | Die Klammer, später | Buchführung und Steuern in Grundzügen; Rechtsformwahl mit Steuerberater. | UG ab 1 € Kapital, Gründung 500–1.000 €; GmbH 25.000 € Stammkapital, halb einzuzahlen | Steuerberater 1.500–3.000 €, IHK-Beitrag, Nebentätigkeitsgenehmigung |
| 0 | Ursprungskonzept jetzt | wie 10, nur früher | wie 10 | wie 10, ohne Geschäft darunter |
| 6 | Verwaltung für andere | Erlaubnis nach § 34c GewO für Wohnimmobilienverwalter mit Weiterbildungspflicht (prüfen); für WEG zusätzlich zertifizierter Verwalter (IHK). Kurs 1.500–3.000 €. | Erlaubnis und Gewerbeanmeldung 300–1.000 € | Vermögensschadenhaftpflicht 300–600 €, Weiterbildung |
| 3 | Brandschutz-Beratung | Brandschutzbeauftragter nach vfdb 12-09 (1.500–2.500 €, Teile davon durch den Dienst ggf. anerkannt, prüfen); für Brandschutznachweise die Nachweisberechtigung nach Landesbauordnung (prüfen); Fachplaner Brandschutz 5.000–8.000 €, Monate. | Ausbildung 2.000–8.000 € | Berufshaftpflicht 500–1.500 €, Nebentätigkeitsgenehmigung |
| 8 | Lager- und Werkstattflächen | Baurecht und Bauantrag, Gewerbemietrecht. | Grundstück plus Systemhalle grob 100.000–250.000 €, oder Lagercontainer 3.000–5.000 € je Stück als Einstieg | Grundsteuer, Versicherung, Instandhaltung |
| 2 | Bau als Aufsicht | VOB/B, Mängelrecht, Bauleitung (IHK-Kurs 2.000–4.000 €); ob eine Bauleiterrolle nach Landesbauordnung eine bestimmte Qualifikation verlangt, hängt vom Umfang ab (prüfen). | Tablet, Software unter 1.500 € | Haftpflicht 500–1.000 €, Nebentätigkeitsgenehmigung |
| 9 | System als Produkt | Vertrieb, Support, Datenschutz mit Auftragsverarbeitung. | fast nichts | deine Zeit, die einzige Größe, die zählt |
| 7 | Möblierte Vermietung | Umsatzsteuer bei Kurzzeitvermietung, Meldepflichten, Zweckentfremdung (prüfen). | Möblierung 10.000–25.000 € je Einheit | Reinigung, Plattformgebühren, höherer Verschleiß |
| 4 | Sanieren mit Eigenleistung | Förderprogramme (KfW, BAFA, Energieberater als Voraussetzung), Kalkulation, Baurecht. | Kaufpreis plus 300–1.000 € je m² Sanierung, Werkzeug | Zinsen; beim Verkauf Steuerberater wegen Grundstückshandel |

**Was quer über alle Konzepte gilt:** Der Nebentätigkeitsantrag ist die eine Ausbildung, die
nichts kostet und alles freischaltet. Steuern in Grundzügen lernt man einmal für alle Linien.
Und die KI-Belegschaft senkt den Lernbedarf messbar: Thorsten bereitet Stoff auf und fragt ab,
der CFO rechnet vor, Marlene hält Fristen — was bleibt, ist das, was ein Abschluss oder eine
Erlaubnis verlangt, und das kann niemand für dich lernen.

### Gesamttabelle: Bewertung, Lernbedarf, Investition (2026-09-03)

Fasst die beiden Tabellen oben zusammen. Noten 1 bis 5, Körper 5 = keine körperliche Arbeit.
Beträge grob, Zulassungen „prüfen".

| Rang | # | Konzept | Ertrag | Recht | Zeit | Körper | Σ | Lernbedarf | Einmalig | Laufend / Jahr |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | Vermietung als Kern | 4 | 5 | 5 | 4 | **18** | Mietrecht, Nebenkosten; kein Abschluss | nächstes Objekt: 20–30 % EK + 8–12 % Nebenkosten | Rücklage 1–1,5 % Gebäudewert |
| 2 | 5 | Krypto als Reserve mit Regeln | 2 | 4 | 5 | 5 | **16** | Steuer, Haltefrist, Verwahrung; ein Wochenende | Hardware-Wallet 80–150 € | Tracking 0–150 € |
| 3 | 10 | Die Klammer, in 3–5 Jahren | 3 | 3 | 4 | 5 | 15 | Buchführung, Steuern; Rechtsform mit StB | UG ab 1 €, Gründung 500–1.000 €; GmbH 25.000 € | StB 1.500–3.000 €, IHK, Genehmigung |
| 4 | 0 | Ursprungskonzept: Firma jetzt | 3 | 2 | 4 | 5 | 14 | wie 10, nur früher | wie 10 | wie 10, ohne Geschäft darunter |
| 4 | 6 | Verwaltung für andere Kleinvermieter | 3 | 3 | 4 | 4 | 14 | § 34c GewO, Weiterbildungspflicht, WEG-Zertifikat (prüfen); Kurs 1.500–3.000 € | Erlaubnis, Gewerbe 300–1.000 € | Haftpflicht 300–600 € |
| 6 | 3 | Brandschutz-Beratung | 4 | 2 | 3 | 4 | 13 | Brandschutzbeauftragter vfdb 12-09 (1.500–2.500 €, Anerkennung prüfen); Nachweisberechtigung LBO (prüfen); Fachplaner 5.000–8.000 € | Ausbildung 2.000–8.000 € | Haftpflicht 500–1.500 €, Genehmigung |
| 6 | 8 | Lager- und Werkstattflächen | 3 | 3 | 4 | 3 | 13 | Baurecht, Bauantrag, Gewerbemietrecht | Halle 100.000–250.000 € oder Container 3.000–5.000 €/Stück | Grundsteuer, Versicherung, Instandhaltung |
| 8 | 2 | Bau als Aufsicht | 3 | 3 | 3 | 3 | 12 | VOB/B, Mängelrecht; IHK-Bauleiter 2.000–4.000 €; Qualifikation je Umfang (prüfen) | Tablet, Software < 1.500 € | Haftpflicht 500–1.000 €, Genehmigung |
| 8 | 9 | Das System als Produkt | 2 | 4 | 1 | 5 | 12 | Vertrieb, Support, Datenschutz | fast nichts | deine Zeit |
| 10 | 7 | Möblierte Vermietung | 3 | 3 | 3 | 2 | 11 | USt bei Kurzzeitvermietung, Meldepflicht, Zweckentfremdung (prüfen) | Möblierung 10.000–25.000 €/Einheit | Reinigung, Plattformen, Verschleiß |
| 11 | 4 | Sanieren mit Eigenleistung | 4 | 2 | 2 | 1 | 9 | Förderung mit Energieberater, Kalkulation, Baurecht | Kaufpreis + 300–1.000 €/m² | Zinsen; Verkauf nur mit StB |

### Sechs Gesichtspunkte und die Simulation „Was müsste passieren, damit X auf Platz 1 steht"

Einmalig und Laufend in Punkte umgemünzt, 5 ist am günstigsten. **Einmalig:** 5 unter 500 €,
4 bis 5.000 €, 3 bis 25.000 €, 2 bis 100.000 €, 1 darüber. **Laufend je Jahr:** 5 unter 200 €,
4 bis 1.000 €, 3 bis 3.000 €, 2 bis 10.000 €, 1 darüber. Höchstwert 30.

| Rang | # | Konzept | Ertrag | Recht | Zeit | Körper | Einmalig | Laufend | Σ |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 5 | Krypto als Reserve | 2 | 4 | 5 | 5 | 5 | 5 | **26** |
| 2 | 1 | Vermietung als Kern | 4 | 5 | 5 | 4 | 2 | 3 | **23** |
| 3 | 10 | Die Klammer, später | 3 | 3 | 4 | 5 | 4 | 3 | 22 |
| 3 | 6 | Verwaltung für andere | 3 | 3 | 4 | 4 | 4 | 4 | 22 |
| 3 | 9 | System als Produkt | 2 | 4 | 1 | 5 | 5 | 5 | 22 |
| 6 | 0 | Ursprungskonzept jetzt | 3 | 2 | 4 | 5 | 4 | 3 | 21 |
| 7 | 3 | Brandschutz-Beratung | 4 | 2 | 3 | 4 | 3 | 4 | 20 |
| 7 | 2 | Bau als Aufsicht | 3 | 3 | 3 | 3 | 4 | 4 | 20 |
| 9 | 8 | Lager- und Werkstattflächen | 3 | 3 | 4 | 3 | 1 | 3 | 17 |
| 10 | 7 | Möblierte Vermietung | 3 | 3 | 3 | 2 | 3 | 2 | 16 |
| 11 | 4 | Sanieren mit Eigenleistung | 4 | 2 | 2 | 1 | 1 | 2 | 12 |

**Vorsicht mit dieser Summe:** Zwei Kostenspalten belohnen, wenig zu tun. Deshalb steht die
Krypto-Reserve mit Ertrag 2 vorn. Zählt Ertrag doppelt, bleibt sie vorn; erst dreifach gezählt
überholt die Vermietung. Die Summe misst Aufwand, nicht Erfolg.

**Simulation.** Ziel ist Σ 26, also gleichauf mit Platz 1. Je Konzept: welche Noten sich ändern
müssten, was das in der Wirklichkeit ist, und ob es ohne Änderung des Konzepts erreichbar ist.

| # | Konzept | Σ | Lücke | Hebel (Note von → nach) | Was das in der Wirklichkeit ist | Erreichbar |
|---|---|---|---|---|---|---|
| 5 | Krypto-Reserve | 26 | 0 | — | nichts; und bei gewichtetem Ertrag fällt es sofort | ist es, nach Zählung |
| 1 | Vermietung | 23 | 3 | Ertrag 4→5, Körper 4→5, Laufend 3→3 | Miet- und Nebenkostenoptimierung durch den CFO; Hausmeisterdienst ~1.000 €/Jahr; Objektkauf über Kredit ohne Eigenkapitaleinsatz hebt Einmalig nicht, nur die Bank | **ja, mit Phase 2–3 des Systems plus Hausmeister** |
| 10 | Klammer | 22 | 4 | Recht 3→5, Ertrag 3→4, Einmalig 4→5 | Nebentätigkeitsgenehmigung erteilt, Steuerberater bestellt, mindestens eine Linie läuft darunter, UG statt GmbH | ja, in zwei bis drei Jahren; ist der Plan |
| 6 | Verwaltung für andere | 22 | 4 | Recht 3→5, Ertrag 3→4, Körper 4→5 | § 34c-Erlaubnis, Genehmigung, Haftpflicht; fünf zahlende Kleinvermieter; keine Begehungen, alles über das System | ja, 12–18 Monate, ~3.000 € und Vertrieb |
| 9 | System als Produkt | 22 | 4 | Zeit 1→3, Ertrag 2→4 | Support automatisiert oder ein Partner, der ihn übernimmt; zahlende Kunden, die es heute nicht gibt | nur mit Partner; dann ist es dessen Geschäft |
| 0 | Ursprungskonzept jetzt | 21 | 5 | Recht 2→4, Ertrag 3→4, Laufend 3→4, Einmalig 4→5 | dieselben Schritte wie bei 10 — Genehmigung, Geschäft darunter, günstiger Steuerberater, UG | ja, aber dann **ist** es Konzept 10 |
| 3 | Brandschutz | 20 | 6 | Recht 2→5, Zeit 3→4, Einmalig 3→4, Ertrag 4→5 | Genehmigung erteilt, Zertifikat Brandschutzbeauftragter statt Fachplaner (~2.000 €), Haftpflicht; Vorlagen im System, Begehungen gebündelt; drei bis fünf Dauerkunden | **ja, in 12 Monaten — wenn der Dienstherr ja sagt**; das erreichbarste Geschäftskonzept |
| 2 | Bau als Aufsicht | 20 | 6 | Recht 3→5, Zeit 3→4, Einmalig 4→5, Laufend 4→5, Körper 3→4 | Genehmigung, Dokumentation nur aus Fotos der Bauherren, keine Präsenz | höchstens 24: ohne Baustelle ist es keine Aufsicht mehr |
| 8 | Lagerflächen | 17 | 9 | Einmalig 1→3, Körper 3→5, Ertrag 3→4, Recht 3→4, Laufend 3→4 | Container statt Halle, Verpachtung an einen Betreiber, Vollbelegung, Baugenehmigung | höchstens 24: das Kapital bleibt |
| 7 | Möblierte Vermietung | 16 | 10 | Körper 2→5, Ertrag 3→4, Recht 3→4, Einmalig 3→4 | Reinigungsdienst (senkt Laufend auf 1), Zweckentfremdung geklärt, bestehende Einheit nutzen | höchstens 21: der Reinigungsdienst frisst den Mehrertrag |
| 4 | Sanieren mit Eigenleistung | 12 | 14 | Körper 1→5, Zeit 2→4 | Handwerker statt Eigenleistung — dann fällt Ertrag auf 2, und das Kapital bleibt 1 | nein: ohne Eigenleistung ist es Konzept 1 mit Kredit |

**Was die Simulation zeigt.** Vier Konzepte kommen ohne Verbiegen nach oben: Vermietung (mit
dem System und einem Hausmeister), Brandschutz (mit der Genehmigung), Verwaltung für andere
(mit Erlaubnis und Vertrieb) und die Klammer (mit der Zeit). Bei allen vier ist derselbe Hebel
der größte: die Note **Recht**, also ein Antrag beim Dienstherrn. Die unteren vier erreichen
Platz 1 nicht, weil ihr Nachteil im Konzept steckt — Kapital oder Körper — und jede Abhilfe
das Konzept in ein anderes verwandelt.
