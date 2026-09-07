# Anleitung für Bewerter (Runde 1, Karl)

Du bewertest zwei Ausgaben desselben Prüffalls, `with_skill` und `without_skill`, gegen dieselben
Kriterien. Du kennst nicht, welche Fassung „richtig" sein soll; du prüfst Aussagen gegen Text.

Für jedes Kriterium: `passed` true oder false, `evidence` ein wörtliches Zitat aus der Ausgabe,
das die Entscheidung trägt, oder „kein Beleg gefunden". Beweislast beim Kriterium: Wenn die
Ausgabe es nicht erkennbar erfüllt, ist es nicht erfüllt. Ein Kriterium, das aus deiner Sicht
falsch oder unscharf ist, bewertest du trotzdem und schreibst deinen Einwand unter
`eval_feedback`. Das ist die Quelle der nächsten Runde.

Ausgabe je Variante als JSON-Datei `grading.json` im Ordner `run-1/` der Variante:
{"eval_id": N, "variant": "with_skill" | "without_skill",
 "criteria": [{"text": "...", "passed": true, "evidence": "..."}],
 "passed_count": N, "total": N,
 "eval_feedback": "Einwände gegen Kriterien oder Fall, oder leer"}
Zusätzlich `execution_metrics: {}` als leeres Objekt.
