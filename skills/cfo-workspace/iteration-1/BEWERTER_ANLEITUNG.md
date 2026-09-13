# Anleitung fuer Bewerter

Du bewertest die Konfigurationen fassung-treuhaender, fassung-controller, fassung-berichterstatter, without_skill desselben Prueffalls. Du weisst nicht, welche Konfiguration welche Anleitung hatte; bewerte nur die Ausgaben in `<konfiguration>/run-1/outputs/`.

Massstab: die Kriterien (`assertions`) in `eval_metadata.json` des Falls. Fuer jedes Kriterium und jede Konfiguration entscheidest du `passed: true|false` und belegst mit einem Zitat aus der Ausgabe (`evidence`: Datei plus woertliche Stelle). Beweislast beim Kriterium: Ohne Zitat nicht bestanden. Ein Kriterium mit mehreren Teilen ist nur bestanden, wenn alle Teile belegt sind. Rechenbeispiele rechnest du nach; Anzahlen zaehlst du gegen die Liste, die sie zaehlen.

Schreibe je Konfiguration `<konfiguration>/run-1/grading.json`:

{
  "expectations": [ {"text": "<Kriterium woertlich>", "passed": true, "evidence": "<Datei: Zitat>"} ],
  "summary": "<zwei bis vier Saetze: Staerken, Schwaechen, auffaellige Fehler>",
  "execution_metrics": {},
  "timing": null,
  "claims": [],
  "user_notes_summary": "",
  "eval_feedback": "<Kritik an den Kriterien: unscharf, doppelt, unpruefbar, widerspruechlich, fehlend>"
}

Zum Schluss `<fall>/VERGLEICH.md`: Tabelle Kriterium x Konfiguration, Summen, und drei bis fuenf Saetze, welche Ausgabe warum am besten war und welche konkreten Saetze oder Verfahren aus einer Konfiguration in die anderen gehoeren. Antworte auf Deutsch. Lies nichts ausserhalb des Fallordners.
