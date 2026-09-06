# Ablage und Benennung

## Vier Eigenschaften, die jede abgelegte Unterlage behalten muss

ISO 15489, der Standard für Schriftgutverwaltung, verlangt von einer Unterlage vier Dinge: **authentisch** (sie ist, was sie zu sein behauptet), **verlässlich** (ihr Inhalt ist vertrauenswürdig), **unversehrt** (sie ist vollständig und unverändert) und **benutzbar** (sie lässt sich finden, abrufen, darstellen und verstehen). Daraus folgen Marlenes Regeln 4 und 5: Originale bleiben unverändert, jede Bewegung ist mit Prüfsumme protokolliert, und die Ablage muss ohne sie lesbar bleiben.

## Namensschema

`JJJJ-MM-TT_Absender_Betreff.erweiterung`

- **Datum zuerst, ISO 8601.** Dann ist alphabetische Reihenfolge gleich zeitliche Reihenfolge, in jedem Programm, auf jedem System. Das Datum ist das Dokumentdatum. Steht bei Vorlagen, Verträgen, Listen und Exposés kein Datum im Text, gilt das Dateidatum als Dokumentdatum, ohne Kennzeichnung (Entscheidung Tobias, 2026-09-06, Praxistest A7); bei Rechnungen, Bescheiden und Briefen bleibt das Datum im Text Pflicht.
- **Nur Buchstaben, Ziffern, Bindestrich, Unterstrich.** Keine Leerzeichen, keine Umlaute, keine Sonderzeichen; sie brechen, sobald ein Name in eine Adresse, ein Skript, eine Sicherung oder eine Cloud-Synchronisation gerät. `Knöll` wird `Knoell`, `Straße` wird `Strasse`.
- **Bindestrich innerhalb eines Feldes, Unterstrich zwischen Feldern.** `Holzbau-Knoell` ist ein Absender, `_` trennt ihn vom Betreff.
- **Dokumentnummer in den Betreff,** wenn es eine gibt: `Rechnung-RG-25-007`.
- **Unter 70 Zeichen.** Der Name beschreibt den Inhalt, nicht den Ablageweg.
- **Die Person steckt im Ordner, nicht im Namen.**

Beispiele:

| kommt an als | wird zu |
|---|---|
| `Scan__20250915_091237.pdf`, Rechnung eines Holzbaubetriebs vom 15.09.2025 | `2025-09-15_Holzbau-Knoell_Rechnung-RG-25-007.pdf` |
| Foto einer Schornsteinfegerrechnung vom 04.03.2026 | `2026-03-04_Schornsteinfeger_Rechnung-Rockhausen.jpg` |
| Bescheid der Tierseuchenkasse vom 20.01.2026 | `2026-01-20_Tierseuchenkasse_Bescheid.pdf` |
| Arztrechnung mit Diagnose im Text | `2026-02-11_Praxis-Name_Rechnung.pdf`, ohne Diagnose im Namen |

## Warum die Ablage nummeriert ist und so bleibt

Die bestehende Struktur `01_` bis `11_` folgt dem Prinzip, das Johnny.Decimal aus der Dezimalklassifikation der Bibliotheken übernommen hat: Eine feste, kurze Liste von Bereichen mit Nummer, darunter Kategorien, darunter erst die Dateien. Die Nummer hält die Reihenfolge stabil und macht den Ort nennbar („liegt in 03, Haus Rockhausen, Strom"). Deshalb legt Marlene nie einen neuen Bereich auf oberster Ebene an: Die Liste ist der Vertrag mit allen, die ohne sie suchen.

Darunter gliedert sich alles nach **Objekt, Person oder Sparte**. Ein Haus hat Strom, Wasser, Abfall, Grundsteuer, Kredit, Versicherung, Rechnungen Dienstleister, Rechnungen Geräte. Ein Fahrzeug hat Kauf, Kredit, Versicherung, Reparatur. Ein Tier hat Versicherung und Behandlungen. Eine Person hat Arbeit, Krankenkasse, Bewerbungen, Steuer. Fehlt eine Sparte bei einem Objekt, die es bei einem anderen schon gibt, wird sie nach demselben Muster angelegt und im Bericht gemeldet.

## Zuordnungsregeln, in dieser Reihenfolge

1. **Objekt vor Person.** Eine Rechnung für das Haus geht zum Haus, auch wenn sie an Tobias adressiert ist.
2. **Sparte nach Kostenart.** Strom zu Strom, Handwerker zu Rechnungen Dienstleister, Gerätekauf zu Rechnungen Geräte.
3. **Person nach Empfänger,** wenn kein Objekt betroffen ist: Lohn, Krankenkasse, Bewerbung, Behörde.
4. **Kinder zum Kind,** Kindergeld zu Kindergeld.
5. **Urkunden zu Urkunden,** nie in einen Sachordner: Geburt, Heirat, Ausweise, Testament, Vollmachten.
6. **Rechnungen und Quittungen** ist der Ort für Kaufbelege ohne Objekt und ohne Person: die Gewährleistung braucht sie zwei Jahre.
7. **Steuerrelevantes bekommt zusätzlich eine Kopie** in `09_Kopie Steuer/JJJJ/`; das Original bleibt am Sachort.

## Dubletten und Wertloses

Liegt ein Dokument in der Drive-Ablage in anderer Fassung (gleicher Name, andere Bytes), gilt die Drive-Fassung; die Fassung aus Schreibtisch, Dokumente oder Downloads geht mit Verweis in die Quarantäne (Entscheidung Tobias, 2026-09-06, Praxistest A5).

Eine Dublette ist byteweise gleich; gleicher Name allein reicht nicht. Bei Dubletten bleibt die Fassung, die schon am richtigen Ort liegt, oder sonst die älteste; die anderen gehen mit Verweis in die Quarantäne. Webseiten-Ausdrucke erkennt man an Adresse und Druckdatum in Kopf- oder Fußzeile und am Namen, der ein Seitentitel ist; Bildschirmfotos an ihrem Namen. Beides ist Quarantäne mit Grund, kein Löschen.

## Der Notfallordner als stehende Prüfung

Verbraucherschutz und Vorsorgeberatung empfehlen einen Notfallordner, der drei Fragen beantwortet: Was besitze ich? Was ist mir wichtig? Wer soll im Ernstfall handeln? Zwölf Rubriken: persönliche Dokumente, medizinische Informationen, Vorsorgedokumente (Vorsorgevollmacht, Patientenverfügung, Betreuungsverfügung, Testament), Finanzen und Konten, Versicherungen, Immobilien, Fahrzeuge, Beruf, digitaler Nachlass, Haustiere, Notfallkontakte, persönliche Wünsche. Zweimal im Jahr aktualisieren. Für Marlene: Ein Bericht im Frühjahr und einer im Herbst prüfen, ob `07_Urkunden Familie` und die Versicherungsordner diese Rubriken abdecken, und nennen, was fehlt. Anlegen tut sie nichts davon; das ist Tobias' Entscheidung.

## Quellen

- DCC, ISO 15489 Briefing (vier Eigenschaften), https://dcc.ac.uk/guidance/briefing-papers/standards-watch-papers/iso-15489
- Harvard Medical School Data Management, File Naming Conventions, https://datamanagement.hms.harvard.edu/plan-design/file-naming-conventions
- University of Connecticut Library, File Naming and Date Formatting, https://guides.lib.uconn.edu/c.php?g=832372&p=8226285
- FilesDesk, File Naming Conventions (Zeichen, Trenner, Länge), https://filesdesk.app/blog/file-naming-conventions
- Johnny.Decimal und PARA, https://help.noteplan.co/article/155-how-to-organize-your-notes-and-folders-using-johnny-decimal-and-para
- fallswaspassiert.de, Was gehört in eine Notfallmappe (zwölf Rubriken), https://www.fallswaspassiert.de/ratgeber/was-gehoert-in-eine-notfallmappe
- ZDF, Notfallordner anlegen, https://www.zdf.de/nachrichten/ratgeber/notfallordner-patientenverfuegung-vorsorgevollmacht-testament-100.html
