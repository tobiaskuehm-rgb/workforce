# Feld: Vermögensverwaltung, Vermögensführung, Vermögenscontrolling

Erkundung für den Bau eines Skills. Gegenstand ist eine Rolle, die ein privates Vermögen
über sechs Anlageklassen und das Kapital dreier Geschäftslinien **führt, rechnet, analysiert
und gegen selbstgesetzte Regeln prüft** — und die **nie eine Anlage empfiehlt**.

Stand der Erkundung: 2026-09-12. Jede Zahl, jede Frist und jeder Fachbegriff unten hat eine
abgerufene Quelle; die Adressen stehen am Ende. Was ich nicht belegen konnte, steht
ausdrücklich als **nicht belegt** da.

Ein Vorbehalt vorweg, der für die ganze Datei gilt: Fast alle belastbaren Verfahren stammen aus
**beaufsichtigten** Berufen (Banken, Kapitalverwaltungsgesellschaften, Betreuer, Gutachter).
Ihre Pflichten gelten für unsere Rolle **nicht rechtlich**. Übertragbar ist die *Form* des
Verfahrens, nicht seine Verbindlichkeit. Wo ich eine Form übernehme, ist das eine
Konstruktionsentscheidung, kein Rechtssatz.

---

## Kurzfassung: was ich mitnehmen würde

| Aus welchem Beruf | Was genau | Warum für uns |
|---|---|---|
| GIPS / Asset Owner | Fünfstufige Bewertungshierarchie (22.B.6) + Pflicht, den Anteil aus der untersten Stufe auszuweisen (24.A.2) | Beantwortet Stichtagsbewertung **und** Kennzeichnung in einem |
| GIPS / Asset Owner | TWR als Regel, MWR nur daneben (21.A.25) | Entscheidet, welche Renditezahl man beim Sparplan überhaupt nennen darf |
| Betreuungsrecht | Vermögensverzeichnis (§ 1835 BGB) + jährliche Rechnungslegung (§ 1865 BGB) | Die einzige belegte *gesetzliche Mindestform* einer privaten Vermögensaufstellung |
| BGB-Auftragsrecht | „geordnete Zusammenstellung der Einnahmen oder Ausgaben" (§ 259), „Verzeichnis des Bestands" (§ 260) | Zwei Register, nicht eins: Bestand und Bewegung |
| Fondsbewertung | Aufbauorganisatorische Trennung Bewertung ↔ Portfolioverwaltung (§ 26 Abs. 2 KARBV), Plausibilisierung fremder Wertansätze (Abs. 1) | Die Rolle, die bewertet, ist nicht die, die disponiert |
| MaRisk | Limitsystem mit definiertem Überschreitungsverfahren (BTR 2.1/2.2), Risikocontrolling getrennt von Positionsverantwortung (AT 4.4.1) | Genau unser „Abweichung von selbstgesetzten Regeln melden" |
| MiFID-Portfolioverwaltung | 10-%-Schwelle, Meldung **bis Ende des Geschäftstags** (Art. 62 Abs. 1 DelVO 2017/565) | Eine fertige, datierte Eskalationsregel zum Abschreiben |
| Immobilienbewertung | Verfahrenswahl **ist zu begründen** (§ 6 ImmoWertV); Wertermittlungsstichtag ≠ Qualitätsstichtag | Zwei Stichtage statt einem — direkt auf Krypto und Beteiligungen übertragbar |
| Beteiligungscontrolling | Soll-Ist-Abweichungsanalyse, Beteiligungsbericht | Die drei Geschäftslinien |

---

## 1. Family Office (Single Family Office)

**Name des Feldes / Kernaufgabe.** In der Berufssprache: *consolidated reporting* bzw.
*Vermögensberichterstattung*. Kernaufgabe ist, verstreute Positionen über Depots, Banken,
Gesellschaften und Sachwerte hinweg zu **einer** Sicht zusammenzuführen und daraus
Vermögensstand, Wertentwicklung, Liquidität und Verpflichtungen darzustellen.

Wichtiger als die Marktliteratur ist hier ein formaler Fund: **Ein Family Office fällt in den
GIPS-Standards unter „Asset Owner"** — für diese Gruppe gibt es seit 2020 ein eigenes
vollständiges Regelwerk, die *Global Investment Performance Standards (GIPS) for Asset Owners*
(CFA Institute, 2019 veröffentlicht, Ausgabe 2020). Das ist die einzige *benannte*, öffentlich
nachlesbare Norm für Vermögensberichterstattung eines Eigentümers, die ich gefunden habe.

**Übertragbares Verfahren.** Der **GIPS Asset Owner Report** — ein Bericht mit fest
vorgeschriebenem Inhalt. Belegte Einzelheiten:

- Es gibt zwei Berichtsformen: *Total Fund and Composite Time-Weighted Return Report*
  (Abschnitt 24) und *Additional Composite Money-Weighted Return Report* (Abschnitt 25).
- **Empfehlung 21.B.2: Der Bericht soll vierteljährlich aktualisiert werden.**
- Pflicht 24.A.3: Es ist **klar zu kennzeichnen**, welche Zeiträume dargestellt sind und ob
  Renditen *gross-of-fees*, *net-of-external-costs-only* oder *net-of-fees* sind.
- Pflicht 24.A.1 j): Zu jedem Jahresende die **dreijährige annualisierte Ex-post-Standard-
  abweichung** auf Monatsrenditen — für das Portfolio *und* die Benchmark.
- Pflicht 24.C.25: Gibt es keine passende Benchmark, ist **zu begründen**, warum keine
  dargestellt wird.

Das letzte ist für uns das interessanteste Muster: Die Norm erlaubt das Fehlen einer Angabe,
verlangt aber an ihrer Stelle eine begründete Leerstelle. Genau die Form, die unsere Rolle für
schwer bewertbare Positionen braucht.

**Grenze, die dieser Beruf hält.** 21.A.20: Stützt sich der Asset Owner auf Aufzeichnungen
Dritter, muss er sicherstellen, dass **auch diese** den Anforderungen genügen — ein fremder
Depotauszug entbindet nicht. Und 21.A.22: **Organisationsänderungen dürfen historische
Performance nicht verändern.** Die Historie ist gegen Umbauten der eigenen Struktur immun.

**Was nur dieser Beruf kann.** Die *Konsolidierung über Rechtsträger und Anlageklassen hinweg*
bei gleichzeitiger Trennung nach Strategien („Composites", Abschnitt 23). Kein anderer der hier
betrachteten Berufe sieht Depot, Immobilie, Beteiligung und Rücklage zugleich.

**Nicht belegt:** einen *Standard* für die Gliederung einer Family-Office-Vermögensaufstellung
(welche Positionen, welche Mindestangaben je Position). Die Marktliteratur nennt wiederkehrend
Bausteine — NAV mit Periodenveränderung, Allokation gegen Ziel mit Drift, Konzentration,
Liquiditätssicht mit Verpflichtungen —, aber das sind Anbieterbeiträge, keine Norm. Ich behandle
sie unten als *Hinweis*, nicht als Beleg. Das Citi-Papier „Consolidated Reporting in Family
Offices" habe ich abgerufen, konnte es aber technisch nicht auswerten (Bild-PDF) — also **nicht
belegt**.

---

## 2. Vermögensverwaltung / Portfolioverwaltung (MiFID-Welt)

**Name / Kernaufgabe.** *Finanzportfolioverwaltung*. Für uns relevant ist nicht die
Dispositionsseite (die unsere Rolle gerade nicht hat), sondern die **Berichts- und
Warnpflicht** gegenüber dem Eigentümer.

**Übertragbares Verfahren — und der beste Einzelfund dieser Erkundung.**
Artikel 62 Abs. 1 der Delegierten Verordnung (EU) 2017/565:

> Der Kunde ist zu unterrichten, wenn der Gesamtwert des Portfolios, wie zu Beginn des jeweiligen
> Berichtszeitraums bewertet, **um 10 % fällt**, und anschließend **bei jedem Wertverlust in
> 10-%-Schritten** — **spätestens am Ende des Geschäftstags**, an dem der Schwellenwert
> überschritten wird, oder, wenn an einem geschäftsfreien Tag, **am Ende des folgenden
> Geschäftstags**.

Das ist eine vollständige Abweichungsregel in einem Satz: **Bezugsgröße** (Wert zu Beginn des
Berichtszeitraums), **Schwelle** (10 %), **Wiederholung** (jede weiteren 10 %), **Frist**
(Geschäftstagsende), **Sonderfall** (geschäftsfreier Tag). Genau diese fünf Felder braucht jede
Regel, die unsere Rolle überwachen soll — egal ob sie eine Krypto-Quote, ein Linienbudget oder
die Rücklagenhöhe betrifft.

Artikel 62 Abs. 2 macht dasselbe für gehebelte Instrumente, dort aber **je Instrument** statt auf
Portfolioebene. Auch das ist übertragbar: Manche Regeln gelten aufs Ganze, manche je Position.

**Grenze.** Die Meldung hängt an einem **fixierten Anfangswert je Berichtszeitraum**, nicht am
gleitenden Höchststand. Wer die Bezugsgröße mitziehen lässt, meldet nie. Die Bezugsgröße gehört
deshalb festgeschrieben und datiert.

**Was nur dieser Beruf kann.** Er verbindet Bericht und Frist: nicht „im nächsten Monatsbericht",
sondern noch am selben Tag. Kein anderer hier betrachteter Beruf kennt eine Tagesfrist für eine
Abweichungsmeldung an den Eigentümer.

**Nicht belegt:** der Inhalt des periodischen Berichts nach Art. 60 DelVO 2017/565 (Turnus,
Pflichtangaben). Der Abruf ist fehlgeschlagen; ich führe ihn als offene Quelle.

---

## 3. Treuhänder und Vermögenstreuhand (BGB) — plus Betreuungsrecht

Das ist der Beruf, der unserer Rolle rechtlich am nächsten kommt: jemand verwaltet **fremdes**
Vermögen, empfiehlt nichts, und schuldet vor allem **Rechenschaft**.

**Verfahren 1 — das Zweiregister-Prinzip.**
- **§ 259 Abs. 1 BGB:** Wer über Einnahmen oder Ausgaben Rechenschaft schuldet, hat *„eine die
  geordnete Zusammenstellung der Einnahmen oder der Ausgaben enthaltende Rechnung"* zu erteilen
  — samt Belegen, soweit üblich.
- **§ 260 Abs. 1 BGB:** Wer über den **Bestand eines Inbegriffs von Gegenständen** Auskunft
  schuldet, hat ein **Verzeichnis des Bestands** vorzulegen.

Zwei Paragraphen, zwei Register: **Bestandsverzeichnis** (was ist da, zum Stichtag) und
**Rechnung** (was ist geflossen, im Zeitraum). Das ist die begriffliche Grundlage für die
Trennung von Vermögensaufstellung und Kapitalflussrechnung — und sie ist älter und klarer als
jede Reporting-Software-Broschüre.

Beide Paragraphen kennen zusätzlich die **eidesstattliche Versicherung** bei Zweifeln an
Vollständigkeit (§ 259 Abs. 2, § 260 Abs. 2) und beide nehmen **Angelegenheiten von geringer
Bedeutung** aus (§ 259 Abs. 3, § 260 Abs. 3). Auch das ist eine Konstruktionsidee: eine
Wesentlichkeitsschwelle gehört in die Regel, nicht in die Laune des Berichtenden.

**Verfahren 2 — Vermögensverzeichnis und Jahresrechnung im Betreuungsrecht.**
Hier wird das Abstrakte konkret, und zwar als **gesetzlich vorgeschriebene private
Vermögensaufstellung**:

- **§ 1835 BGB (Vermögensverzeichnis):** Der Betreuer erstellt bei Amtsantritt ein Verzeichnis
  des Vermögens und reicht es beim Betreuungsgericht ein. Es enthält **auch Angaben zu den
  regelmäßigen Einnahmen und Ausgaben**. Die Angaben sind *„in geeigneter Weise zu belegen"*.
  Bei Bedarf und Verhältnismäßigkeit dürfen Behörde, Notar oder Sachverständiger hinzugezogen
  werden; bei Unzulänglichkeit kann das Gericht die Erstellung anordnen.
- **§ 1865 BGB (Rechnungslegung):** *„Die Rechnung ist jährlich zu legen."* Das Rechnungsjahr
  bestimmt **das Gericht**. Die Rechnung muss **eine geordnete Zusammenstellung der Einnahmen und
  Ausgaben** enthalten **und den Vermögensstand darstellen** — also nicht nur Flüsse, sondern
  auch, *wie sich das verwaltete Vermögen entwickelt hat*. Führt der Betreute ein kaufmännisches
  Unternehmen, genügt *„ein aus den Büchern gezogener Jahresabschluss"*.

Der letzte Satz ist für uns bemerkenswert: Das Gesetz akzeptiert für den **unternehmerischen
Teil** ein anderes Format als für den privaten — genau die Zweiteilung, die unsere Rolle
zwischen sechs Anlageklassen und drei Geschäftslinien ohnehin hat.

**Grenze.** Der Verwalter **legt vor**, ein Dritter **nimmt ab** (Gericht, Berechtigter). Die
prüfende Instanz ist nie der Verwalter. Übertragen: Unsere Rolle erzeugt die Aufstellung, der
Eigentümer nimmt sie ab — und die Rolle kennzeichnet, was sie selbst nicht belegen konnte,
statt es glattzuziehen.

**Was nur dieser Beruf kann.** Er hat den **Erstbestand**. § 1835 verlangt ein Verzeichnis *bei
Amtsantritt* — einen datierten Nullpunkt, gegen den alles Spätere gemessen wird. Kein anderer
Beruf hier schreibt einen Anfangsbestand vor.

---

## 4. Fondsbuchhaltung und Fondsadministration

**Name / Kernaufgabe.** *Fondsbuchhaltung*, *Anteilpreisermittlung*, *NAV calculation*. Kernaufgabe
ist die **periodische Wertermittlung eines Sondervermögens** und die dazugehörige Rechnungslegung.

**Übertragbares Verfahren — der Nettoinventarwert (§ 168 KAGB).**
Der Wert des Investmentvermögens wird ermittelt als **Verkehrswerte der Vermögensgegenstände
abzüglich aufgenommener Kredite und sonstiger Verbindlichkeiten**, geteilt durch die Zahl der
Anteile. Für börsengehandelte Gegenstände gilt **der Kurswert**, sofern dieser eine verlässliche
Bewertung gewährleistet; liegt kein handelbarer Kurs vor, sind **angemessene Bewertungsmodelle**
anzuwenden, die aktuelle Marktgegebenheiten und kaufmännische Sorgfalt berücksichtigen.

Für uns: Die Formel *Summe Verkehrswerte − Verbindlichkeiten* ist die saubere Definition von
„Nettovermögen" — Immobilienkredite gehören auf dieselbe Seite der Rechnung wie das
Kryptodepot, nicht in eine Fußnote.

**Grenze — und das ist die schärfste Trennung, die ich gefunden habe.**
**§ 26 Abs. 2 KARBV:** Die Bewertung bzw. die Mitwirkung daran muss durch einen Bereich erfolgen,
der **aufbauorganisatorisch von dem für die Portfolioverwaltung zuständigen Bereich getrennt**
ist — *„auch auf der Ebene der Geschäftsleitung"*.
**§ 26 Abs. 1 KARBV:** Die Gesellschaft muss die **von der Verwahrstelle ermittelten Wertansätze
in geeigneter Weise auf Plausibilität prüfen** und Unregelmäßigkeiten aufklären; die Mitwirkung
ist **nachvollziehbar zu dokumentieren**.
**§ 26 Abs. 4 KARBV:** Die **Interne Revision** prüft die Einhaltung regelmäßig.

Drei Sätze, drei Prinzipien: *Wer bewertet, disponiert nicht.* *Fremde Werte werden
plausibilisiert, nicht übernommen.* *Die Einhaltung wird von einer dritten Stelle nachgeprüft.*
Alle drei sind für unsere Rolle direkt formulierbar — die Rolle bewertet und empfiehlt nicht,
sie prüft Depotwerte gegen eine zweite Quelle, und sie hält fest, wann sie das getan hat.

Dazu die **Verwahrstelle** als zweites Augenpaar: § 76 Abs. 1 KAGB verpflichtet sie
sicherzustellen, dass Ausgabe/Rücknahme von Anteilen den Regeln entsprechen, dass bei Geschäften
**der Gegenwert innerhalb der üblichen Fristen** überwiesen wird, dass Erträge regelkonform
verwendet werden und dass Sicherheiten *„rechtswirksam bestellt und jederzeit vorhanden"* sind.

**Was nur dieser Beruf kann.** Die **tägliche, wiederholbare, prüfbare Wertermittlung nach
schriftlich fixierter Bewertungsrichtlinie**, verbunden mit einer institutionellen
Doppelbesetzung (KVG *und* Verwahrstelle). Kein anderer Beruf hier ermittelt Werte in dieser
Taktung gegen ein festes Regelwerk.

---

## 5. Risikocontrolling (MaRisk)

**Name / Kernaufgabe.** *Risikocontrolling-Funktion*. Kernaufgabe: wesentliche Risiken
**identifizieren, beurteilen, steuern, überwachen und berichten** (AT 4.3.2 Tz. 1 MaRisk).

**Übertragbares Verfahren — das Limitsystem.**
- **BTR 2.1 Tz. 1:** *„Auf der Grundlage der Risikotragfähigkeit ist ein System von Limiten zur
  Begrenzung der Marktpreisrisiken einzurichten."* Risikokonzentrationen sind zu berücksichtigen.
- **BTR 2.1 Tz. 2:** *„Ohne Marktpreisrisikolimit darf kein mit Marktpreisrisiken behaftetes
  Geschäft abgeschlossen werden."* — Fail-closed: keine Regel, kein Geschäft.
- **AT 4.3.2 Tz. 8 (sinngemäß, belegt im Regelungstext):** Es muss ein **konsistentes Verfahren
  zur Behandlung von Limitüberschreitungen** eingerichtet sein.
- **BTR 2.2 Tz. 1:** Geschäfte sind **unverzüglich** auf die Limite anzurechnen; der
  Positionsverantwortliche muss über Limite und **aktuelle Ausnutzung zeitnah informiert** sein;
  bei Überschreitung sind geeignete Maßnahmen zu treffen, gegebenenfalls ein
  **Eskalationsverfahren** einzuleiten.
- **BTR 2.2 Tz. 2 / BTR 2.3 Tz. 1 — zwei Taktungen:** Positionen des **Handelsbuches** sind
  **täglich** zu bewerten und täglich zu einer Gesamtrisikoposition zusammenzufassen; Positionen
  des **Anlagebuches** **mindestens vierteljährlich**.
- **BTR 2.1 Tz. 3:** Für *„länger anhaltende Fälle fehlender, veralteter oder verzerrter
  Marktpreise"* sind für wesentliche Positionen **alternative Bewertungsmethoden festzulegen** —
  vorher, nicht im Ereignisfall.
- **BTR 2.1 Tz. 4:** Die im **Rechnungswesen und Risikocontrolling** ermittelten Ergebnisse sind
  **regelmäßig zu plausibilisieren** — also zwei Rechenwege gegeneinander.

Die Zwei-Taktungen-Regel ist für uns unmittelbar brauchbar: Krypto ist unser „Handelsbuch",
Immobilien und Beteiligungen sind das „Anlagebuch". Unterschiedliche Bewertungsfrequenz ist
keine Nachlässigkeit, sondern Methode.

**Grenze — Funktionstrennung.**
- **AT 4.3.1 Tz. 1:** *„Die Aufbau- und Ablauforganisation muss sicherstellen, dass miteinander
  unvereinbare Tätigkeiten von verschiedenen Mitarbeitern ausgeführt werden."* Prozesse, Aufgaben,
  Kompetenzen, Verantwortlichkeiten und Kommunikationswege sind klar zu definieren. Auch bei
  Arbeitsplatzwechseln sind Interessenkonflikte zu vermeiden; beim Wechsel aus Handels- oder
  Marktbereichen in Kontrollbereiche sind **angemessene Übergangsfristen** vorzusehen.
- **AT 4.4.1 Tz. 1:** Die Risikocontrolling-Funktion muss **organisatorisch bis einschließlich der
  Ebene der Geschäftsleitung** von den Bereichen getrennt sein, **die Geschäfte initiieren bzw.
  abschließen**. Zu diesen zählen ausdrücklich auch Bereiche **mit Positionsverantwortung (z. B.
  Treasury)**.
- Als *nachgelagerte Bereiche und Kontrollbereiche* nennt MaRisk namentlich:
  **Risikocontrolling-Funktion, Compliance-Funktion, Marktfolge, Abwicklung und Kontrolle**.
- **AT 4.4.1 Tz. 3:** Die Mitarbeiter des Risikocontrollings müssen **uneingeschränkten Zugang**
  zu allen relevanten Informationen haben.
- Kleine Institute dürfen **alternative Kontrollmechanismen** einrichten (AT 4.3.1) bzw. die
  Trennung erst unterhalb der Geschäftsleitung ziehen (AT 4.4.1 Tz. 1).

Die letzte Klausel ist die wichtigste für ein Ein-Personen-Vermögen: Die Norm kennt selbst den
Fall, dass die Trennung personell nicht darstellbar ist, und verlangt dann **kompensierende
Kontrollen** statt Verzicht. Unsere Rolle ist genau so ein alternativer Kontrollmechanismus: Der
Eigentümer entscheidet und handelt, die Rolle misst und meldet — aber sie disponiert nie.

**Was nur dieser Beruf kann.** Er **begrenzt vorab** statt hinterher zu berichten. Limit,
Auslastung, Überschreitung, Eskalation — das ist der einzige hier gefundene Beruf, dessen
Kernprodukt eine *Schwelle* ist und nicht ein *Bericht*.

---

## 6. Immobilienbestandsverwaltung / Real Estate Asset Management

**Name / Kernaufgabe.** *Immobilien-Asset-Management* (objektbezogene Wertsteuerung, abgegrenzt
vom operativen *Property Management*). Für die Bewertungsseite: *Verkehrswertermittlung*.

**Verfahren 1 — Verkehrswert und Verfahrenswahl.**
**§ 194 BauGB** definiert den Verkehrswert (Marktwert) über den Preis, der **in dem Zeitpunkt, auf
den sich die Ermittlung bezieht**, im gewöhnlichen Geschäftsverkehr nach rechtlichen Gegebenheiten
und tatsächlichen Eigenschaften, sonstiger Beschaffenheit und Lage zu erzielen wäre — **ohne
Rücksicht auf ungewöhnliche oder persönliche Verhältnisse**.

**§ 6 ImmoWertV (Wertermittlungsverfahren; Ermittlung des Verkehrswerts):**
> „Grundsätzlich sind zur Wertermittlung das Vergleichswertverfahren, das Ertragswertverfahren,
> das Sachwertverfahren oder mehrere dieser Verfahren heranzuziehen. Die Verfahren sind nach der
> Art des Wertermittlungsobjekts … insbesondere der Eignung der zur Verfügung stehenden Daten, zu
> wählen; **die Wahl ist zu begründen**."

Die Verfahren selbst: Vergleichswert §§ 24–26, Ertragswert §§ 27–34, Sachwert §§ 35–39 ImmoWertV.

**Verfahren 2 — zwei Stichtage statt einem. Das ist der eigentliche Fund.**
- **Wertermittlungsstichtag** (§ 2 ImmoWertV): *„der Zeitpunkt, auf den sich die Wertermittlung
  bezieht und der für die Ermittlung der allgemeinen Wertverhältnisse maßgeblich ist."*
- **Qualitätsstichtag** (§ 4 Abs. 1 ImmoWertV): *„der Zeitpunkt, auf den sich der für die
  Wertermittlung maßgebliche Grundstückszustand bezieht. Er entspricht dem Wertermittlungs-
  stichtag, es sei denn, dass aus rechtlichen oder sonstigen Gründen der Zustand des Grundstücks
  zu einem anderen Zeitpunkt maßgebend ist."*

Also: **Wann galt der Markt** und **wann galt der Zustand der Sache** sind zwei verschiedene
Fragen. Übertragen auf unser Feld ist das direkt anwendbar und heute vermutlich der häufigste
stille Fehler: Ein Beteiligungswert vom 31.12. wird mit einem Bestandsstand vom 30.09. kombiniert
und als eine Zahl ausgewiesen. Die Rolle sollte **je Position beide Daten führen**.

**Verfahren 3 — Kennzahlen.** Die *gif Gesellschaft für Immobilienwirtschaftliche Forschung e. V.*
gibt einen **Kennzahlenkatalog Immobilienmanagement** heraus (Produktnummer EP-011-2011, Stand
März 2011), der nach eigener Beschreibung **rund 100 Kennzahlen** von der reinen
Objektbewirtschaftung bis zu Investmentkennzahlen systematisch ordnet; Bezug für
Nicht-Mitglieder 49,00 € inkl. 7 % MwSt.
**Nicht belegt:** die Definitionen einzelner Kennzahlen (Leerstandsquote, WALT, Mietrendite) nach
gif — die Produktseite nennt weder Formeln noch die Gliederung, und den Katalog selbst habe ich
nicht abgerufen. Die in der Websuche kursierenden Definitionen stammen aus Maklerlexika und sind
als Beleg untauglich.

**Grenze.** Die **Begründungspflicht für die Methode** (§ 6 ImmoWertV). Nicht der Wert allein ist
das Produkt, sondern Wert *plus* Begründung, warum dieser Weg zu ihm führte. Und: Der Verkehrswert
ignoriert **ungewöhnliche und persönliche Verhältnisse** (§ 194 BauGB) — was der Eigentümer
persönlich an einem Objekt hängt, ist kein Wertbestandteil.

**Was nur dieser Beruf kann.** Er bewertet **Einzelstücke ohne Markt**. Für eine Immobilie, eine
Beteiligung oder ein Sammlerstück gibt es keinen Kurs; dieser Beruf hat als einziger ein
ausformuliertes, nachvollziehbares Verfahren für genau diesen Fall — und zwingt es zur
Begründung.

---

## 7. Rechnungswesen für Kapitalanlagen / Vermögensaufstellung im Steuerrecht

**Name / Kernaufgabe.** Bewertung und Ausweis von Vermögensgegenständen zu einem **Stichtag** nach
einem festen Regelwerk.

**Übertragbares Verfahren — die Stichtagsregel des Bewertungsgesetzes.**
**§ 11 Abs. 1 BewG:** Wertpapiere, die am Stichtag im regulierten Markt an einer deutschen Börse
gehandelt werden, sind **mit dem niedrigsten am Stichtag notierten Kurs** anzusetzen. **Liegt am
Stichtag keine Notierung vor, gilt der letzte Kurs innerhalb der vorangegangenen 30 Tage.**
**§ 11 Abs. 2 BewG:** Für nicht notierte Anteile an Kapitalgesellschaften ist der gemeine Wert
anzusetzen; fehlen Verkäufe unter fremden Dritten **innerhalb eines Jahres**, ist er unter
Berücksichtigung der **Ertragsaussichten** oder einer anderen anerkannten, auch im gewöhnlichen
Geschäftsverkehr für nichtsteuerliche Zwecke üblichen Methode zu ermitteln — mit dem
**Substanzwert als Mindestwert**.

Drei übertragbare Bausteine: (a) eine **Rückfallregel mit benannter Frist** (30 Tage), wenn am
Stichtag kein Kurs vorliegt; (b) eine **Geltungsdauer für Transaktionspreise** (ein Jahr); (c) eine
**Untergrenze** (Substanzwert), damit eine Ertragsschätzung nicht beliebig nach unten läuft.

**§ 151 Abs. 1 BewG** (gesonderte Feststellung) ordnet die Vermögensarten, die für Erbschaft- und
Schenkungsteuer je einzeln festgestellt werden: **Grundbesitzwerte**, **Werte des
Betriebsvermögens oder des Anteils daran**, **Anteile an Kapitalgesellschaften nach § 11 Abs. 2**
und **Anteile an anderem Vermögen und Schulden, die mehreren Personen zustehen**. Im
Feststellungsbescheid sind außerdem Angaben **zur Zurechnung der wirtschaftlichen Einheit** und,
bei mehreren Beteiligten, **zur Höhe des Anteils** zu machen.

Das ist damit die einzige **amtliche Gliederung einer Vermögensaufstellung**, die ich belegen
konnte — und sie ist für uns brauchbar, weil sie nach **Bewertungsweg** ordnet (Grundbesitz,
Betriebsvermögen, Anteile, sonstiges Miteigentum), nicht nach Anlagegefühl.
**Nicht belegt:** eine Norm, die für jede Einzelposition einer privaten Vermögensaufstellung
Pflichtangaben festlegt (Menge, Anschaffungsdatum, Anschaffungskosten, Verwahrort …). Die
nächstliegende Annäherung bleibt § 1835 BGB („belegen … in geeigneter Weise") plus § 151 Abs. 1
BewG (Zurechnung und Anteilshöhe).

**Verfahren 2 — Kapitalflussrechnung.** **DRS 21** verlangt die Kapitalflussrechnung in
**Staffelform** (DRS 21.12) mit drei Bereichen: **laufende Geschäftstätigkeit**,
**Investitionstätigkeit**, **Finanzierungstätigkeit**; Ausgangspunkt ist der **Finanzmittelfonds**
am Periodenanfang. Für unsere Rolle ist das die Gliederung, in der sich „Sparplan",
„Immobilienkauf" und „Kapitaleinlage in eine Linie" sauber trennen lassen — und genau diese
Trennung braucht die Renditemessung weiter unten.
**Einschränkung:** Diese Angaben stammen aus Fachbeiträgen zu DRS 21 (Haufe u. a.), nicht aus dem
Standardtext selbst, den ich nicht abgerufen habe. Die **Ziffernangabe 21.12** gilt daher als
**schwach belegt**.

**Grenze.** Der **Stichtag** selbst: gebucht wird der Wert des Tages, nicht der Wert, der besser
passt. Und der **Stetigkeitsgedanke** — dieselbe Methode über die Zeit, sonst ist der Vergleich
wertlos.

**Was nur dieser Beruf kann.** Er löst den Fall „**Stichtag da, Preis nicht da**" mit einer festen
Frist statt mit Ermessen.

---

## 8. Beteiligungscontrolling

**Name / Kernaufgabe.** *Beteiligungscontrolling*. Kernaufgabe: die Beteiligungen auf das
Gesamtzielsystem des Eigentümers ausrichten, Ziele und Maßnahmen zwischen Eigentümer und
Gesellschaft abstimmen, und über die Entwicklung berichten.

**Übertragbare Verfahren.**
- **Soll-Ist-Analyse mit Abweichungsanalyse:** Zu den Kennzahlen werden **Erwartungen,
  Zielvorgaben und Soll-Werte vorab festgelegt**; positive **und** negative Abweichungen lösen
  eine Abweichungsanalyse aus, **negative sollen früh erkannt werden**, um Gegenmaßnahmen zu
  ermöglichen.
- **Beteiligungsbericht:** bündelt die von den Gesellschaften gelieferten Informationen und macht
  **Umfang und Entwicklung** der wirtschaftlichen Betätigungen transparent. Im kommunalen Bereich
  ist das ein eingeführtes, regelmäßig erscheinendes Dokument.
- **Portfolioanalyse** des Beteiligungsportfolios.

Für unsere drei Geschäftslinien ist der Beteiligungsbericht die naheliegende Form: **je Linie ein
Abschnitt mit Soll, Ist, Abweichung und Kommentar**, alle Linien in einem Dokument, damit sie
vergleichbar werden.

**Grenze.** Die **Trennung von Eigentümersicht und Geschäftsführungssicht**. Das
Beteiligungscontrolling steuert nicht das operative Geschäft der Tochter; es misst gegen die
Ziele, die der Eigentümer gesetzt hat. Exakt die Grenze, die unsere Rolle braucht: Sie sagt einer
Linie nicht, was sie tun soll — sie sagt dem Eigentümer, wo die Linie von seiner Vorgabe abweicht.

**Was nur dieser Beruf kann.** Er behandelt **unternehmerisches Kapital als Portfolioposition**,
ohne es wie ein Wertpapier zu bewerten. Für „Budget und Kontrolle einer neuen Linie" ist das der
einzige passende Beruf.

**Einschränkung zur Quellenlage:** Die Belege sind Fachportale (business-wissen.de, otris,
Controlling-Wiki der HSLU), keine Norm. Ein *verbindlicher* Standard für Beteiligungscontrolling
im Privatvermögen ist **nicht belegt**. Für kommunale Beteiligungsberichte gibt es
landesrechtliche Pflichten — deren Fundstellen habe ich **nicht** abgerufen und führe sie daher
nicht an.

---

# Die drei Querschnittsfragen

## A. Wie wird ein Vermögen richtig aufgestellt?

**Kurz: Es gibt keine einzelne anerkannte Gliederung für eine private Vermögensaufstellung. Es
gibt drei Quellen, die zusammen eine tragfähige ergeben.**

**1. Der gesetzliche Mindestinhalt (Betreuungsrecht).** § 1835 BGB: ein **Vermögensverzeichnis**
zum Amtsantritt, **einschließlich Angaben zu den regelmäßigen Einnahmen und Ausgaben**, mit
Angaben, die *„in geeigneter Weise zu belegen"* sind. § 1865 BGB: **jährlich** eine Rechnung, die
**eine geordnete Zusammenstellung der Einnahmen und Ausgaben enthält und den Vermögensstand
darstellt**; für einen kaufmännischen Betrieb des Betreuten genügt **ein aus den Büchern gezogener
Jahresabschluss**.

Daraus folgt eine Dreiteilung, die ich als Grundgerüst empfehlen würde:
**(i) Bestand zum Stichtag — (ii) regelmäßige Einnahmen und Ausgaben — (iii) Entwicklung seit der
letzten Rechnung.** Und für den unternehmerischen Teil ein **eigenes Format**.

**2. Die Ordnung nach Bewertungsweg (Steuerrecht).** § 151 Abs. 1 BewG gliedert nach
**Grundbesitz / Betriebsvermögen / Anteile an Kapitalgesellschaften / Anteile an sonstigem
Vermögen und Schulden** und verlangt je Einheit **Zurechnung** und, bei mehreren Beteiligten,
**Anteilshöhe**. Für uns heißt das: Eine Position braucht mindestens **Was, Wem zugerechnet, Zu
welchem Anteil** — und die Klasse, nach der sie bewertet wird.

**3. Die Trennung Bestand ↔ Bewegung (BGB).** § 260 verlangt ein **Verzeichnis des Bestands**,
§ 259 eine **geordnete Zusammenstellung der Einnahmen oder Ausgaben**. Zwei Register. Wer beides
in eine Tabelle schreibt, verliert genau die Trennung, die Frage B braucht.

**4. Die Nettogröße (Fondsrecht).** § 168 KAGB: **Verkehrswerte abzüglich Kredite und sonstiger
Verbindlichkeiten**. Schulden gehören in dieselbe Aufstellung, nicht daneben.

**Ergänzend, aber nicht als Beleg:** Die Family-Office-Marktliteratur nennt wiederkehrend als
Bausteine eines konsolidierten Berichts NAV mit Periodenveränderung, Allokation gegen Ziel mit
Drift-Analyse, Konzentration nach Manager oder Sektor sowie eine Liquiditätssicht einschließlich
zugesagter und anstehender Verpflichtungen. Das deckt sich mit dem Obigen und ergänzt es um die
**Liquiditäts- und Verpflichtungssicht** — für unsere Rolle wichtig, weil die Rücklage in Geld
eine der sechs Klassen ist. Als *Hinweis* brauchbar, als *Standard* **nicht belegt**.

## B. Wie misst man Wertentwicklung ehrlich?

**Der Unterschied.**
- **Zeitgewichtete Rendite (TWR)** ist laut GIPS-Glossar *„a method of calculating period-by-period
  returns that reflects the change in value and negates the effects of external cash flows"* — sie
  neutralisiert Ein- und Auszahlungen. Sie misst, **wie gut die Anlage war**.
- **Geldgewichtete Rendite (MWR)** gewichtet die Perioden nach dem eingesetzten Kapital. Sie misst,
  **wie gut der Eigentümer gefahren ist** — Zeitpunkt und Höhe der Einzahlungen wirken mit.

**Die Regel, die daraus folgt — und sie ist belegt, nicht gemeint.**
**GIPS for Asset Owners 21.A.25:** *Der Asset Owner **muss** zeitgewichtete Renditen für alle Total
Funds darstellen; geldgewichtete Renditen **dürfen zusätzlich** dargestellt werden.*
Für die Firmen-Fassung gilt sinngemäß: MWR statt TWR nur, wenn die Firma **die externen
Zahlungsströme kontrolliert** und das Vehikel *closed-end*, *fixed life*, *fixed commitment* ist
oder illiquide Anlagen einen wesentlichen Teil der Strategie ausmachen.

**Warum das beim Sparplan entscheidet, welche Zahl man nennen darf.**
Bei einem Sparplan **bestimmt der Eigentümer die Zahlungsströme**, nicht die verwaltende Stelle.
Genau das ist der Fall, für den TWR gebaut ist: Die Zahl soll nicht dadurch besser werden, dass
zufällig kurz vor einem Anstieg eingezahlt wurde. Wer bei laufenden Einzahlungen eine MWR als
„Rendite des Portfolios" nennt, nennt eine Größe, die überwiegend vom **Einzahlungstakt** getrieben
ist. Beides ist zulässig — aber **die Reihenfolge liegt fest**: TWR ist die Pflichtzahl, MWR die
Zusatzzahl. Für unsere Rolle ist daraus eine Ausgaberegel formulierbar: *Nenne TWR; nenne MWR nur
mit Etikett und nur zusätzlich.*

**Die handwerklichen Vorschriften dazu (GIPS AO, Abschnitt 22) — hier liegt die eigentliche
Arbeit:**

| Was | TWR | MWR |
|---|---|---|
| Bewertungsfrequenz | **mindestens monatlich** (22.A.20 a) | **mindestens jährlich** und zum Periodenende (22.A.22) |
| Bewertungstermin | **Kalendermonatsende oder letzter Geschäftstag** (22.A.20 b) | Periodenende |
| Sonderbewertung | **am Tag jedes „large cash flow"**; der Asset Owner **muss definieren**, was ein *large cash flow* ist (22.A.20 c) | — |
| Berechnung | mindestens monatlich (22.A.21 a); Teilperioden bei großen Zahlungsströmen, falls keine Tagesrenditen (22.A.21 c); für nicht-große Zahlungsströme **tagesgewichtete Anpassung** (22.A.21 d); Perioden **geometrisch verketten** (22.A.21 f) | **annualisierte Since-Inception-MWR** bzw. für den längsten belegbaren Zeitraum (22.A.23 a); **auf Basis täglicher externer Zahlungsströme** (22.A.23 b, verpflichtend seit **1. Januar 2020**) |
| Private-Market-Anlagen | Bewertung **mindestens quartalsweise**, zum Quartalsende (22.A.30) | — |
| Jahresstichtage | Anfangs- und Endbewertungstermine müssen **konsistent** sein; sofern kein abweichendes Geschäftsjahr, **zum Kalenderjahresende oder letzten Geschäftstag** (22.A.19, verpflichtend für Perioden ab **1. Januar 2006**) | dito |

Zwei Punkte davon sind für unsere Rolle die eigentliche Nachricht:

1. **„Large cash flow" muss definiert werden** (22.A.20 c). Die Norm sagt nicht, *wie groß*. Sie
   sagt: Lege es fest, schreib es auf, wende es konsistent an. Das ist exakt das Muster
   „selbstgesetzte Regel, gegen die gemessen wird" — die Schwelle stammt vom Eigentümer, die
   Einhaltung von der Rolle.
2. **Kostenetikett ist Pflicht** (24.A.3 b): jede Rendite ist als *gross-of-fees*,
   *net-of-external-costs-only* oder *net-of-fees* zu kennzeichnen. Eine Renditezahl ohne dieses
   Etikett ist nach dieser Norm unvollständig. Was bei „net" abzuziehen ist, steht in 22.A.24:
   **Transaktionskosten**, **alle Gebühren und Kosten extern verwalteter Pooled Funds**,
   **Verwaltungsgebühren extern verwalteter Einzelmandate** und **Investment-Management-Kosten**.

**Weitere belegte Pflichten mit Datum:** Wechselt der Berichtstyp (z. B. von geldgewichtet auf
zeitgewichtet oder umgekehrt), ist das darzustellen/offenzulegen (24.C.…/25.C.… — die
Übergangsregel ist im Text belegt, die exakte Ziffer habe ich nicht isoliert: **Ziffer nicht
belegt**).

## C. Wie bewertet man zum Stichtag?

**Die Bewertungshierarchie.** Es gibt zwei, und sie sagen dasselbe in unterschiedlicher Tiefe.

**IFRS 13 — drei Stufen (die geläufige Fassung):**
- **Stufe 1:** unangepasste notierte Preise auf **aktiven Märkten** für **identische** Vermögens-
  werte, zu denen der Bilanzierende am Bewertungsstichtag Zugang hat. Verlässlichste Eingangsgröße.
- **Stufe 2:** andere **beobachtbare** Eingangsgrößen, direkt oder indirekt — Preise für
  **ähnliche** Werte, Preise auf **inaktiven** Märkten, Zinssätze, Zinsstrukturkurven, implizite
  Volatilitäten, Kreditaufschläge.
- **Stufe 3:** **nicht beobachtbare** Eingangsgrößen; sie müssen die Annahmen abbilden, die
  Marktteilnehmer zugrunde legen würden.
- **Das Einstufungsprinzip:** Die **gesamte** Bewertung wird nach der **niedrigsten Stufe**
  eingeordnet, die für die Bewertung **insgesamt wesentlich** ist. Je niedriger die Stufe, desto
  mehr Erläuterung ist nötig.

**GIPS 22.B.6 — fünf Stufen (die für uns brauchbarere, weil feiner):**
a. objektive, beobachtbare, **unangepasste** Marktpreise für **identische** Anlagen auf **aktiven**
   Märkten am Bewertungsstichtag; sonst
b. objektive, beobachtbare Marktpreise für **ähnliche** Anlagen auf **aktiven** Märkten; sonst
c. notierte Preise für identische oder ähnliche Anlagen auf **nicht aktiven** Märkten — ausdrücklich
   definiert als Märkte *„in which there are few transactions …, the prices are not current, or
   price quotations vary substantially over time and/or between market makers"*; sonst
d. **marktbasierte Eingangsgrößen außer Preisen**, die für die Anlage beobachtbar sind; sonst
e. **subjektive, nicht beobachtbare** Eingangsgrößen. Diese dürfen **nur** verwendet werden, wenn
   beobachtbare nicht verfügbar oder nicht sachgerecht sind, und sind **auf Basis der besten
   verfügbaren Information** zu entwickeln.

**Wie gekennzeichnet wird, welche Stufe verwendet wurde — und das ist die Antwort auf die
eigentliche Frage:**

1. **Anteilsausweis.** GIPS **24.A.2**: Der Asset Owner **muss den Prozentsatz des Gesamtwerts
   ausweisen, der mit subjektiven, nicht beobachtbaren Eingangsgrößen bewertet wurde** — zum
   jüngsten Jahresende, sofern diese Anlagen einen **wesentlichen** Betrag ausmachen. (Dieselbe
   Pflicht für Composites: 25.A.2.)
2. **Abweichungsanzeige.** GIPS **24.C.24**: Weicht die eigene Bewertungshierarchie **wesentlich**
   von der empfohlenen ab, **ist das offenzulegen** (verpflichtend für Perioden ab **1. Januar
   2011**). Entsprechend 25.C.24 für Composites.
3. **Vorläufige Werte.** GIPS **22.A.18**: Wird der letzte verfügbare historische Preis oder ein
   vorläufiger Schätzwert als Fair Value verwendet, muss er (a) als **beste Annäherung an den
   aktuellen Fair Value** gelten und (b) die **Differenz zum endgültigen Wert und deren Wirkung**
   auf Vermögen und Performance **beurteilt** und **bei Erhalt des endgültigen Werts angepasst**
   werden. Ergänzend **24.B.9/25.B.5**: die Verwendung vorläufiger Schätzwerte *soll* angegeben
   werden.
4. **Externe Bewertung.** GIPS **22.B.2**: Bewertungen *sollen* von einem **qualifizierten
   unabhängigen Dritten** stammen. **22.B.8**: Private-Market-Anlagen *sollen* **mindestens alle
   12 Monate** extern bewertet werden. „External valuation" ist im Glossar definiert als
   *„an assessment of value performed by an independent third party"*.
5. **Verfahrensbegründung (Sachwerte).** § 6 ImmoWertV: **die Wahl des Verfahrens ist zu
   begründen.**

**Die Stichtagsmechanik.**
- **Zwei Stichtage:** Wertermittlungsstichtag (Marktverhältnisse, § 2 ImmoWertV) und
  Qualitätsstichtag (Zustand der Sache, § 4 ImmoWertV) — sie fallen zusammen, **es sei denn**, der
  Zustand ist zu einem anderen Zeitpunkt maßgebend.
- **Kein Preis am Stichtag:** § 11 Abs. 1 BewG greift auf den **letzten Kurs der vorangegangenen
  30 Tage** zurück. MaRisk BTR 2.1 Tz. 3 verlangt, **vorab alternative Bewertungsmethoden
  festzulegen** für länger anhaltende Fälle fehlender, veralteter oder verzerrter Marktpreise.
- **Kein Markt überhaupt:** § 11 Abs. 2 BewG — Ertragsaussichten oder andere anerkannte Methode,
  **Substanzwert als Untergrenze**. § 168 Abs. 3 KAGB — **angemessene Bewertungsmodelle** unter
  Berücksichtigung aktueller Marktgegebenheiten.
- **Bewertungsfrequenz nach Klasse:** MaRisk — Handelsbuch **täglich**, Anlagebuch **mindestens
  vierteljährlich**. GIPS — Portfolios **mindestens monatlich**, Private-Market-Anlagen
  **mindestens quartalsweise**.
- **Trennung der Funktion:** § 26 Abs. 2 KARBV — wer bewertet, ist **aufbauorganisatorisch von der
  Portfolioverwaltung getrennt**, bis in die Geschäftsleitung. § 26 Abs. 1 KARBV — fremde
  Wertansätze werden **plausibilisiert und dokumentiert**, nicht übernommen.

**Vorschlag für unsere Rolle, direkt aus diesem Material:** Jede Position trägt vier Zusatzfelder —
**Bewertungsstufe (a–e nach GIPS 22.B.6)**, **Wertermittlungsstichtag**, **Qualitätsstichtag**,
**Quelle**. Und die Vermögensaufstellung weist in einer Zeile aus, **welcher Prozentsatz des
Gesamtvermögens auf Stufe e beruht** (nach dem Muster 24.A.2). Das ist die ehrlichste verfügbare
Einzelkennzahl über die Belastbarkeit einer Vermögensaufstellung.

---

# Was ich nicht belegen konnte

Ausdrücklich als offene Punkte, nicht als Tatsachen:

- Ein **Standard für die Gliederung einer Family-Office-Vermögensaufstellung** (welche Positionen
  in welcher Reihenfolge, welche Mindestangaben je Position). Existiert möglicherweise; gefunden
  habe ich nur Anbieterliteratur.
- Der Inhalt des **Citi-Papiers „Consolidated Reporting in Family Offices"** — abgerufen, technisch
  nicht auswertbar (Bild-PDF).
- **CFA Institute, „Elements of an Investment Policy Statement for Individual Investors"** —
  abgerufen, nicht auswertbar. Damit sind auch die **Bestandteile eines IPS** (Duties and
  Responsibilities, Rebalancing, Review-Turnus) und alle **konkreten Toleranzbänder**
  (z. B. „50 % Ziel, Band 40–60 %") **nicht belegt**; sie stammen aus Sekundärtexten und
  Praxisblogs.
- **Artikel 60 DelVO 2017/565** (Inhalt und Turnus des periodischen Berichts bei
  Portfolioverwaltung) — Abruf fehlgeschlagen.
- **DRS 21 im Wortlaut**; die Angabe „Staffelform, DRS 21.12" stammt aus Fachbeiträgen.
- **gif-Kennzahlendefinitionen** (Leerstandsquote, WALT, Mietrendite) — Katalog nicht abgerufen,
  nur Produktbeschreibung.
- Eine **Norm für Beteiligungscontrolling im Privatvermögen**; die Belege sind Fachportale.
- Die exakte GIPS-Ziffer für die Offenlegung eines **Wechsels des Renditetyps** (TWR ↔ MWR); im
  Text vorhanden, Ziffer nicht isoliert.
- Ob und wie ein Family Office **Krypto** in die Bewertungshierarchie einordnet — keine Quelle
  gefunden, die das benennt.

---

# Quellen

Alle im Rahmen dieser Erkundung am 2026-09-12 abgerufen.

**Performancemessung und Vermögensberichterstattung**
1. CFA Institute: *Global Investment Performance Standards (GIPS®) for Asset Owners*, Ausgabe 2020
   (© 2019 CFA Institute). Volltext-PDF, ausgewertet.
   https://www.gipsstandards.org/wp-content/uploads/2021/02/2020_gips_standards_asset_owners.pdf
   — Provisions 21.A.20–21.A.28, 21.B.2, 22.A.16–22.A.32, 22.B.2/22.B.6/22.B.8, 23.A.1–23.A.8,
   24.A.1–24.A.3, 24.B.9, 24.C.22–24.C.25, 25.A.2, 25.B.5, 25.C.24, Glossar (fair value,
   external valuation, time-weighted return).
2. GIPS Standards: *Guidance Statement on Calculation Methodology* (2011).
   https://www.gipsstandards.org/wp-content/uploads/2021/03/calculation_methodology_gs_2011.pdf
   — als Fundstelle notiert, **nicht** im Volltext ausgewertet.
3. CFA Institute: *Overview of the Global Investment Performance Standards* (Refresher Reading).
   https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/overview-of-the-global-investment-performance-standards

**Bewertung**
4. IFRS Foundation: *IFRS 13 Fair Value Measurement*.
   https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2022/issued/part-a/ifrs-13-fair-value-measurement.pdf
   — Stufenhierarchie; ausgewertet über Suchergebnisdarstellung, **nicht** im Volltext.
5. § 168 KAGB (Bewertung, Nettoinventarwert). https://www.gesetze-im-internet.de/kagb/__168.html
6. § 76 KAGB (Kontrollfunktion der Verwahrstelle). https://www.gesetze-im-internet.de/kagb/__76.html
7. § 26 KARBV (Allgemeine Bewertungsgrundsätze, Funktionstrennung).
   https://www.gesetze-im-internet.de/karbv/__26.html
8. § 194 BauGB (Verkehrswert). https://www.gesetze-im-internet.de/bbaug/__194.html
9. ImmoWertV (Fassung 2021, in Kraft seit 1.1.2022), §§ 2, 4, 6, 24–26, 27–34, 35–39.
   https://www.gesetze-im-internet.de/immowertv_2022/BJNR280500021.html
   § 4 im Wortlaut zusätzlich: https://lxgesetze.de/immowertv/4
10. § 11 BewG (Wertpapiere und Anteile). https://www.gesetze-im-internet.de/bewg/__11.html
11. § 151 BewG (Gesonderte Feststellungen). https://www.gesetze-im-internet.de/bewg/__151.html

**Rechenschaft und Vermögensverzeichnis**
12. § 259 BGB (Umfang der Rechenschaftspflicht). https://www.gesetze-im-internet.de/bgb/__259.html
13. § 260 BGB (Pflichten bei Herausgabe oder Auskunft über Inbegriff von Gegenständen).
    https://www.gesetze-im-internet.de/bgb/__260.html
14. § 1835 BGB (Vermögensverzeichnis). https://www.gesetze-im-internet.de/bgb/__1835.html
15. § 1865 BGB (Rechnungslegung). https://www.gesetze-im-internet.de/bgb/__1865.html

**Risikocontrolling und Limitsystem**
16. BaFin: *Mindestanforderungen an das Risikomanagement — MaRisk*, Rundschreiben, Fassung vom
    30.06.2026 (BA 54). Volltext-PDF, ausgewertet.
    https://www.bundesbank.de/resource/blob/825336/866a68577eb35afee82fbe60c39a4f87/472B63F073F071307366337C94F8C870/2026-06-30-rundschreiben-data.pdf
    — AT 4.3.1 Tz. 1 (mit Erläuterung „Nachgelagerte Bereiche und Kontrollbereiche"),
    AT 4.3.2 Tz. 1 und Tz. 8, AT 4.4.1 Tz. 1–3, BTR 2.1 Tz. 1–4, BTR 2.2 Tz. 1–3, BTR 2.3 Tz. 1.
17. BaFin: Rundschreiben 06/2024 (BA) MaRisk.
    https://www.bafin.de/SharedDocs/Downloads/DE/Rundschreiben/dl_rs_06_2024_MaRisk_pdf_BA.pdf

**Berichts- und Warnpflichten der Portfolioverwaltung**
18. Delegierte Verordnung (EU) 2017/565, Artikel 62 (Zusätzliche Berichtspflichten bei der
    Portfolioverwaltung und bei Geschäften mit Eventualverbindlichkeiten).
    https://freirecht.de/g/EU2017VO565:62
    Konsolidierter Amtstext: https://eur-lex.europa.eu/legal-content/DE/TXT/PDF/?uri=CELEX%3A02017R0565-20220802

**Beteiligungscontrolling**
19. business-wissen.de: *Beteiligungscontrolling — Kennzahlen zur Überwachung und Analyse*.
    https://www.business-wissen.de/hb/beteiligungscontrolling-kennzahlen-zur-ueberwachung-und-analyse/
20. otris: *Beteiligungscontrolling — Definition & Aufgaben*.
    https://www.otris.de/wiki/beteiligungscontrolling/
21. Controlling-Wiki der Hochschule Luzern: *Beteiligungscontrolling*.
    https://wiki.hslu.ch/controlling/Beteiligungscontrolling

**Immobilien-Kennzahlen**
22. gif Gesellschaft für Immobilienwirtschaftliche Forschung e. V.: *Kennzahlenkatalog
    Immobilienmanagement*, EP-011-2011, Stand März 2011 (Produktseite; Katalog selbst nicht
    abgerufen). https://gif-ev.com/produkt/kennzahlenkatalog-immobilienmanagement/

**Kapitalflussrechnung**
23. Haufe: *Gliederung der Kapitalflussrechnung* (zu DRS 21).
    https://www.haufe.de/finance/jahresabschluss-bilanzierung/neuer-drs-21-zur-kapitalflussrechnung/gliederung-der-kapitalflussrechnung_188_233092.html
24. DRSC: *DRS 21 Kapitalflussrechnung* (Projektseite; Standardtext nicht abgerufen).
    https://www.drsc.de/projekte/kapitalflussrechnung-drs-21/

**Abgerufen, aber nicht auswertbar (als offene Quellen geführt)**
25. Citi Private Bank: *Consolidated Reporting in Family Offices*.
    https://www.privatebank.citibank.com/ivc/docs/Consolidated-reporting-in-family-Offices.pdf
26. CFA Institute: *Elements of an Investment Policy Statement for Individual Investors*.
    https://rpc.cfainstitute.org/sites/default/files/-/media/documents/article/position-paper/investment-policy-statement-individual-investors.pdf
27. Artikel 60 DelVO 2017/565 (periodische Berichte).
    https://lexparency.de/eu/32017R0565/ART_60/

---

*Diese Datei beschreibt Berufsverfahren. Sie enthält keine Anlageempfehlung, keine Bewertung einer
Anlageklasse und keine Aussage über künftige Kursverläufe.*
