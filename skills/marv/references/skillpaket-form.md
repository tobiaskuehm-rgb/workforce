# Die Form eines Skillpakets

```
<name>/
├── SKILL.md                 Frontmatter (name, description), unter 200 Zeilen, Verfahren, Rechte, Regeln, Selbstprüfung, Herkunft
├── references/              je Thema eine Datei, je Datei eine Quellenliste; Tabelle in SKILL.md sagt, wann welche gelesen wird
├── scripts/                 nur Standardbibliothek der vorhandenen Python-Version; jedes Skript mit Selbsttest
├── evals/
│   ├── evals.json           Prüffälle: id, prompt, expected_output, files
│   └── varianten/           die drei Fassungen und die Bewertung
```

## Frontmatter

`name` klein, mit Bindestrich. `description` in der Sprache des Auftraggebers, drängend: was der Skill tut, und alle Anlässe, bei denen er anspringen soll, mit Beispielsätzen in Anführungszeichen, auch solche, in denen das Schlüsselwort nicht fällt („räum den Schreibtisch auf", „was ist fällig"). Und wofür er nicht gilt. Modelle lösen Skills zu selten aus, nicht zu oft. Hängt eine Stelle der description von einer offenen Antwort des Auftraggebers ab, steht dort eine sichtbare Lücke ⟨…⟩ statt einer geratenen Angabe; das ist etwas anderes als der eckige Platzhalter in einem Entwurf an Dritte (Lehre 7), der dort verboten bleibt. Die Auslöseprüfung mit zehn Testsätzen gegen alte und neue Beschreibung läuft, bevor der Auftraggeber geantwortet hat.

## SKILL.md

Rolle in drei Sätzen. Dann eine Tabelle „bei diesem Auftrag lies diese Referenz". Dann das Verfahren in nummerierten Schritten. Dann Rechte in drei Spalten: allein, vorlegen, nie. Dann zehn Regeln, jede ein Satz. Dann eine Selbstprüfung mit zehn Fragen. Dann Herkunft: woher jede Regel kommt. Ein Entscheidungsbaum („was ist das?"), wenn das Feld Arten unterscheidet.

Erklären, warum, nicht befehlen. Kein ALLES GROSS. Beispiele aus dem Feld, erfunden.

## Referenzen

Eine Referenz erklärt eine Sache vollständig: Gesetz, Verfahren, Register, Beispiele, Grenzen, Quellen. Tabellen für Fristen, Spalten, Kostenarten. Am Ende „Quellen" mit Adressen. Keine privaten Namen, keine Kennnummern; das wird per Suche geprüft (Kindernamen, IBAN-Muster).

## Skripte

Nur, wenn ein Schritt deterministisch sein muss (Prüfsummen, Verschieben, Protokoll). Standardbibliothek, weil der Rechner des Auftraggebers keine Pakete hat und keinen Paketmanager. Jedes Skript hat einen Selbsttest in Wegwerfordnern und einen Trockenlauf-Schalter. Reihenfolgeabhängigkeiten (Kopie vor Verschieben) werden im Skript erzwungen, nicht im Plan erwartet.

## Prüffälle

`evals.json` mit sechs Fällen, jeder mit `expected_output` als Beschreibung, die Kriterien stehen im Arbeitsbereich. Fälle nennen ein Datum. Fälle enthalten das, was der Skill verbietet, als Versuchung.

## Was nicht ins Paket gehört

Echte Dokumente, Berichte über echte Dokumente, Konfiguration mit echten Pfaden und Namen; das liegt beim Auftraggeber (bei Marlene: `_Marlene` im Drive). Bewertungsdateien und Läufe liegen im `-workspace`-Ordner neben dem Paket, nicht darin.
