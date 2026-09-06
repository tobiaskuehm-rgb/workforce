#!/usr/bin/env python3
"""Arbeitsbereich fuer Pruefrunden anlegen und auswerten. Standardbibliothek, Python 3.9.

  eval_workspace.py init <skill-dir> <workspace/iteration-N>            Ordner und eval_metadata.json je Fall aus evals/evals.json
  eval_workspace.py timing <run-dir> <tokens> <ms>                       timing.json schreiben (Werte aus der Abschlussmeldung des Subagenten)
  eval_workspace.py summary <workspace/iteration-N>                      eigene Summen je Fall und Fassung
  eval_workspace.py fix-metrics <workspace/iteration-N>                  execution_metrics null -> {} (Aggregator stuerzt sonst ab)
Layout: eval-<id>-<name>/{with_skill,without_skill}/run-1/{outputs/,grading.json,timing.json}
"""
import sys, json, pathlib

def init(skill, ws):
    ev = json.load(open(pathlib.Path(skill) / "evals/evals.json", encoding="utf-8"))
    for e in ev["evals"]:
        d = pathlib.Path(ws) / f"eval-{e['id']}-{e.get('name', 'fall')}"
        for c in ("with_skill", "without_skill"):
            (d / c / "run-1/outputs").mkdir(parents=True, exist_ok=True)
        json.dump({"eval_id": e["id"], "eval_name": e.get("name", ""), "prompt": e["prompt"], "assertions": e.get("assertions", [])},
                  open(d / "eval_metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(d.name)

def timing(run, tokens, ms):
    json.dump({"total_tokens": int(tokens), "duration_ms": int(ms), "total_duration_seconds": round(int(ms) / 1000, 1)},
              open(pathlib.Path(run) / "timing.json", "w"), indent=2); print("timing.json:", run)

def summary(ws):
    tot = {"with_skill": [0, 0, 0, 0], "without_skill": [0, 0, 0, 0]}
    for d in sorted(pathlib.Path(ws).glob("eval-*")):
        row = d.name
        for c in tot:
            g = d / c / "run-1/grading.json"; t = d / c / "run-1/timing.json"
            if not g.exists(): row += f"  {c[:4]} --"; continue
            gj = json.load(open(g)); tj = json.load(open(t)) if t.exists() else {"total_tokens": 0, "duration_ms": 0}
            p, n = gj["summary"]["passed"], gj["summary"]["total"]; row += f"  {c[:4]} {p}/{n}"
            tot[c][0] += p; tot[c][1] += n; tot[c][2] += tj["total_tokens"]; tot[c][3] += tj["duration_ms"]
        print(row)
    for c, (p, n, tok, ms) in tot.items():
        if n: print(f"{c:14s} {p}/{n} = {p / n:.2f}  Tokens {tok:,}  Sekunden {ms / 1000:.0f}")

def fix_metrics(ws):
    n = 0
    for p in pathlib.Path(ws).glob("eval-*/*/run-1/grading.json"):
        g = json.load(open(p))
        if g.get("execution_metrics") is None:
            g["execution_metrics"] = {}; json.dump(g, open(p, "w"), ensure_ascii=False, indent=2); n += 1
    print("repariert:", n)

if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    {"init": init, "timing": timing, "summary": summary, "fix-metrics": fix_metrics}[cmd](*args)
