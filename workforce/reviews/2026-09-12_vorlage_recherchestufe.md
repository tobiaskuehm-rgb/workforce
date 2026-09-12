# Vorlage, Klasse Strategie: Die Recherchestufe fehlt im Filter

Karl, 2026-09-12, auf Einwand des CEO: „Wir wollten grob Ideen sammeln, dann Deep Research
tagelang auf Ollama. Jetzt soll ich nach der zweiten Idee schon aktiv werden."

**Sachverhalt.** Der Einwand trägt, der Fehler ist meiner. `FILTER.md` hat drei Stufen:
Ausschluss, Ordnen mit Noten, Test mit Probe. Zwischen Noten und Probe steht nichts. In meinem
3-Loop vom 2026-09-11 habe ich „die Probe ist der Maßstab" zur Auflage gemacht — richtig gegen
Noten auf Papier, falsch als nächster Schritt. Damit landet der CEO nach zwei Ideen bei
Kaltakquise, und die teuerste Ressource des Hauses, seine Stunden, wird als erste ausgegeben.
Der ausgelassene Schritt ist der billigste: Recherche.

**Was dazwischen gehört.** Stufe 2b, Recherche, vor der Probe: Je Kandidat die Fragen, die
über ihn entscheiden (Marktgröße, wer heute bezahlt, welcher Preis erzielt wird, welche
Erlaubnis nötig ist), mit Quelle und Datum. Ergebnis ist kein Urteil, sondern Material, das
die Noten der Stufe 2 belegt oder widerlegt. Erst wenn ein Kandidat die Recherche übersteht,
kostet er eine Stunde des CEO.

**Warum lokal.** Recherche über Tage bedeutet viele lange Läufe. Bei 2,0 USD Tagesdecke ist
das mit einem bezahlten Modell nicht zu machen; ein lokales Modell kostet Strom. Genau dafür
ist der `OllamaProvider` im Kern, gehärtet mit `G-092`.

**Was dem im Weg steht, gemessen am 2026-09-12:**

| Blocker | Stand |
|---|---|
| Ollama läuft | auf diesem Mac nicht erreichbar; Mac mini M1 vorhanden, Zustand nicht gemessen |
| Netzweg NAS → Mac mini | nicht festgelegt; der Provider erlaubt nur Loopback und die Container-Brücke |
| Lokales Modell in der Allowlist | fehlt; `models.py` kennt nur Echo, Haiku, Sonnet, Opus |

**Optionen.**
(a) **Recherche auf dem Mac mini, Ollama.** Nutzen: kostenlos, tagelang, private Daten bleiben
im Haus. Risiko: Qualität eines lokalen Modells für Marktrecherche ist nicht gemessen, und es
hat kein Netz, also keine Quellen aus dem Web. Aufwand: Mac mini einrichten, Modell wählen,
Allowlist ergänzen, Gerds Abnahme des Netzwegs, ein bis zwei Tage.
(b) **Recherche mit Websuche auf dem bezahlten Modell, eng gedeckelt.** Nutzen: echte Quellen
mit Datum, das ist es, was die Noten braucht. Risiko: Kosten, und die Decke bremst. Aufwand:
gering, läuft heute.
(c) **Recherche als Fragenliste, der CEO sucht selbst.** Nutzen: null Kosten. Risiko: seine
Stunden, genau das, was vermieden werden soll. Aufwand: null.

**Empfehlung: (b) jetzt, (a) als Ziel.** Ein lokales Modell ohne Netz beantwortet keine Frage
nach Marktgröße oder erzielbarem Preis; es kann ordnen, zusammenfassen und Annahmen zerlegen,
aber die Quelle muss von außen kommen. Also: Recherche mit Quellen jetzt bezahlt und gedeckelt,
und Ollama übernimmt, sobald es steht, den Teil, der keine Quelle braucht — Ordnen, Entwürfe,
Vorlesen langer Texte.

**Satz fürs Log:** Klasse Strategie: Der CEO nimmt eine Recherchestufe zwischen Noten und Probe
in `FILTER.md` auf; keine Probe ohne Recherche, keine Note ohne Material.

**To-do CEO:** ja oder nein zur Recherchestufe, und (a), (b) oder (c).
