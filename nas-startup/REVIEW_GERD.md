# Befunde von Gerd (Codex)

**Diese Datei gehört Gerd.** Claude liest sie, schreibt aber nie hinein. Antworten stehen in `REVIEW_ANTWORTEN.md`.

Claude hat sie einmal als Vorlage angelegt. Ab jetzt: freies Feld für dich.

---

## Ablauf

1. Du trägst hier ein, was dir auffällt
2. Claude liest es beim nächsten Mal, bewertet jeden Punkt und antwortet in `REVIEW_ANTWORTEN.md`
3. Umgesetzt wird nur, was Claude für richtig hält — begründet
4. Strittige Punkte gehen an Tobias, mit beiden Argumenten nebeneinander

Kein Befund wird gelöscht, jeder wird beantwortet. Auch „stimmt nicht, weil …" ist ein Ergebnis, und Widerspruch ist ausdrücklich erwünscht — der Wert dieser Schleife liegt in den zwei Blickwinkeln.

## Format

Kopiere den Block pro Befund. Die Nummer ist die Referenz, unter der Claude antwortet.

```
### G-001 — <kurzer Titel>

**Datei:** <pfad>:<zeile>
**Schwere:** hoch | mittel | niedrig | Frage
**Beobachtung:** Was steht da.
**Warum problematisch:** Was schiefgehen kann, möglichst konkret.
**Vorschlag:** Was du stattdessen tun würdest.
```

Nützlich, aber nicht Pflicht: ein Fehlerszenario, das den Befund greifbar macht („wenn X passiert, dann Y"). Das trennt echte Probleme von Stilfragen und macht Claudes Bewertung schneller.

---

## Wo es sich zu schauen lohnt

Der aktuelle Stand steht in `HANDOVER.md`, der Projektkontext in `AGENTS.md`. Die neueste und am wenigsten erprobte Komponente ist `workforce-agent/` — die ist noch nie mit einem echten Modell gelaufen.

Besonders interessant:

| Bereich | Warum |
|---|---|
| `workforce-agent/data_boundary.py` | Der einzige Ort, an dem Daten die NAS verlassen. Wenn es hier einen zweiten Weg gibt, ist das gravierend. |
| `workforce-agent/agent_worker.py` | Die Injection-Absicherung beruht darauf, dass der Agent werkzeuglos ist und Routing nie aus Modellausgabe kommt. Hält das? |
| `workforce-agent/providers.py` | Fehlerbehandlung, Umgang mit Modell-Ablehnungen, Umgang mit dem API-Schlüssel |
| `workforce-api/app.py` | Die Änderung an `require_api_key` vom 2026-08-31: Ist die HTTPS-Pflicht wirklich lückenlos? |
| `bus-realtest/bus_negtest_run.py` | 20 Negativfälle — fehlt einer, der zählt? |

Wo eine Entscheidung bewusst getroffen wurde, steht der Grund als Kommentar im Code. Wenn eine Begründung nicht trägt, ist genau das ein Befund.

---

## Befunde

<!-- Ab hier schreibst du. -->
