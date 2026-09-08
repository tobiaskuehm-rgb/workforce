#!/usr/bin/env python3
"""Arbeitsbereich fuer Pruefrunden anlegen und auswerten. Standardbibliothek, Python 3.9.

  eval_workspace.py init <skill-dir> <workspace/iteration-N> [konfig,...]   Ordner, eval_metadata.json je Fall aus evals/evals.json, BEWERTER_ANLEITUNG.md
                                                                         Konfigurationen: Standard with_skill,without_skill
  eval_workspace.py timing <run-dir> <tokens> <ms>                       timing.json schreiben (Werte aus der Abschlussmeldung des Subagenten)
  eval_workspace.py summary <workspace/iteration-N>                      eigene Summen je Fall und Fassung
  eval_workspace.py fix-metrics <workspace/iteration-N>                  execution_metrics null -> {} (Aggregator stuerzt sonst ab)
Layout: eval-<id>-<name>/<konfiguration>/run-1/{outputs/,grading.json,timing.json}
"""
import sys, json, pathlib

GRADER = """# Anleitung fuer Bewerter

Du bewertest die Konfigurationen {konfigs} desselben Prueffalls. Du weisst nicht, welche Konfiguration welche Anleitung hatte; bewerte nur die Ausgaben in `<konfiguration>/run-1/outputs/`.

Massstab: die Kriterien (`assertions`) in `eval_metadata.json` des Falls. Fuer jedes Kriterium und jede Konfiguration entscheidest du `passed: true|false` und belegst mit einem Zitat aus der Ausgabe (`evidence`: Datei plus woertliche Stelle). Beweislast beim Kriterium: Ohne Zitat nicht bestanden. Ein Kriterium mit mehreren Teilen ist nur bestanden, wenn alle Teile belegt sind. Rechenbeispiele rechnest du nach; Anzahlen zaehlst du gegen die Liste, die sie zaehlen.

Schreibe je Konfiguration `<konfiguration>/run-1/grading.json`:

{{
  "expectations": [ {{"text": "<Kriterium woertlich>", "passed": true, "evidence": "<Datei: Zitat>"}} ],
  "summary": "<zwei bis vier Saetze: Staerken, Schwaechen, auffaellige Fehler>",
  "execution_metrics": {{}},
  "timing": null,
  "claims": [],
  "user_notes_summary": "",
  "eval_feedback": "<Kritik an den Kriterien: unscharf, doppelt, unpruefbar, widerspruechlich, fehlend>"
}}

Zum Schluss `<fall>/VERGLEICH.md`: Tabelle Kriterium x Konfiguration, Summen, und drei bis fuenf Saetze, welche Ausgabe warum am besten war und welche konkreten Saetze oder Verfahren aus einer Konfiguration in die anderen gehoeren. Antworte auf Deutsch. Lies nichts ausserhalb des Fallordners.
"""

def init(skill, ws, konfigs=("with_skill", "without_skill")):
    ev = json.load(open(pathlib.Path(skill) / "evals/evals.json", encoding="utf-8"))
    for e in ev["evals"]:
        d = pathlib.Path(ws) / f"eval-{e['id']}-{e.get('name', 'fall')}"
        for c in konfigs:
            (d / c / "run-1/outputs").mkdir(parents=True, exist_ok=True)
        json.dump({"eval_id": e["id"], "eval_name": e.get("name", ""), "prompt": e["prompt"], "assertions": e.get("assertions", [])},
                  open(d / "eval_metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(d.name)
    (pathlib.Path(ws) / "BEWERTER_ANLEITUNG.md").write_text(GRADER.format(konfigs=", ".join(konfigs)), encoding="utf-8")
    print("BEWERTER_ANLEITUNG.md")

def timing(run, tokens, ms):
    json.dump({"total_tokens": int(tokens), "duration_ms": int(ms), "total_duration_seconds": round(int(ms) / 1000, 1)},
              open(pathlib.Path(run) / "timing.json", "w"), indent=2); print("timing.json:", run)

def summary(ws):
    # Configurations are discovered from the folders, so three variants plus baseline work as well as with/without.
    cases = sorted(pathlib.Path(ws).glob("eval-*"))
    konfigs = sorted({c.name for d in cases for c in d.iterdir() if (c / "run-1").is_dir()})
    tot = {c: [0, 0, 0, 0] for c in konfigs}
    print("| Fall | " + " | ".join(konfigs) + " |"); print("|---|" + "---|" * len(konfigs))
    for d in cases:
        row = []
        for c in konfigs:
            g = d / c / "run-1/grading.json"; t = d / c / "run-1/timing.json"
            if not g.exists(): row.append("--"); continue
            gj = json.load(open(g)); tj = json.load(open(t)) if t.exists() else {"total_tokens": 0, "duration_ms": 0}
            ex = gj.get("expectations", []); p = sum(1 for x in ex if x.get("passed")); n = len(ex)
            tot[c][0] += p; tot[c][1] += n; tot[c][2] += tj["total_tokens"]; tot[c][3] += tj["duration_ms"]
            row.append(f"{p}/{n} · {tj['total_tokens'] // 1000}k · {tj['duration_ms'] // 1000}s")
        print(f"| {d.name} | " + " | ".join(row) + " |")
    print("| **Summe** | " + " | ".join(f"**{p}/{n}** · {tok // 1000}k · {ms // 1000}s" for p, n, tok, ms in tot.values()) + " |")

def fix_metrics(ws):
    n = 0
    for p in pathlib.Path(ws).glob("eval-*/*/run-1/grading.json"):
        g = json.load(open(p))
        if g.get("execution_metrics") is None:
            g["execution_metrics"] = {}; json.dump(g, open(p, "w"), ensure_ascii=False, indent=2); n += 1
    print("repariert:", n)

if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "init" and len(args) == 3: args = [args[0], args[1], tuple(args[2].split(","))]
    {"init": init, "timing": timing, "summary": summary, "fix-metrics": fix_metrics}[cmd](*args)
