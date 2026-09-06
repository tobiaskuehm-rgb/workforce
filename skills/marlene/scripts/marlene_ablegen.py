#!/usr/bin/env python3
"""Marlenes Verschiebe-Werkzeug. Standardbibliothek, Python 3.9.

Plan (JSON): {"quelle_wurzel": ..., "ablage_wurzel": ..., "quarantaene_wurzel": ..., "eintraege": [
   {"sha": "...", "quelle": "rel/pfad", "aktion": "ablegen|kopie|quarantaene", "ziel": "rel/ordner", "name": "neuer.name", "grund": "..."}]}
Regeln: Pruefsumme vor und nach jeder Kopie, keine Kollision, nie ueberschreiben, nie loeschen ohne verifizierte Kopie.
Jede Bewegung eine Zeile im Protokoll (jsonl). `undo <protokoll>` nimmt einen Lauf zurueck.
"""
import sys, json, hashlib, shutil, pathlib, datetime, os

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

REIHENFOLGE = {"kopie": 0, "ablegen": 1, "quarantaene": 2}   # Kopien zuerst: danach ist die Quelle weg

def sortiert(plan):
    return sorted(plan["eintraege"], key=lambda e: REIHENFOLGE[e["aktion"]])

def pruefen(plan):
    fehler = []; ziele = set()
    q = pathlib.Path(plan["quelle_wurzel"]).expanduser()
    a = pathlib.Path(plan["ablage_wurzel"]).expanduser()
    for e in plan["eintraege"]:
        if e["aktion"] in ("ablegen", "kopie") and not e.get("neu"):
            zd = a / e["ziel"]
            if not zd.is_dir(): fehler.append(f"Zielordner fehlt (nicht als neu markiert): {e['ziel']}")
    for e in plan["eintraege"]:
        src = q / e["quelle"]
        if not src.is_file(): fehler.append(f"fehlt: {e['quelle']}"); continue
        if not sha(src).startswith(e["sha"]): fehler.append(f"Pruefsumme weicht ab: {e['quelle']}"); continue
        if e["aktion"] in ("ablegen", "kopie"):
            z = pathlib.Path(plan["ablage_wurzel"]).expanduser() / e["ziel"] / e["name"]
        else:
            z = pathlib.Path(plan["quarantaene_wurzel"]).expanduser() / e["quelle"]
        if z.exists(): fehler.append(f"Ziel existiert schon: {z}")
        if str(z) in ziele: fehler.append(f"Zielkollision im Plan: {z}")
        ziele.add(str(z))
        if any(k in e.get("name", "").lower() for k in ("token", "secret")): fehler.append(f"Geheimnis im Plan: {e['quelle']}")
    return fehler

def ausfuehren(plan, protokoll, trocken):
    q = pathlib.Path(plan["quelle_wurzel"]).expanduser()
    a = pathlib.Path(plan["ablage_wurzel"]).expanduser()
    qu = pathlib.Path(plan["quarantaene_wurzel"]).expanduser()
    zaehler = {"ablegen": 0, "kopie": 0, "quarantaene": 0}
    liste = []
    with open(protokoll, "a", encoding="utf-8") as log:
        for e in sortiert(plan):
            src = q / e["quelle"]
            if e["aktion"] in ("ablegen", "kopie"): dst = a / e["ziel"] / e["name"]
            else: dst = qu / e["quelle"]
            zeile = {"zeit": datetime.datetime.now().isoformat(timespec="seconds"), "aktion": e["aktion"], "quelle": str(src), "ziel": str(dst), "sha": e["sha"], "grund": e.get("grund", ""), "trocken": trocken}
            if not trocken:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists(): raise SystemExit(f"ABBRUCH, Ziel existiert: {dst}")
                shutil.copy2(src, dst)
                if sha(dst) != sha(src): dst.unlink(); raise SystemExit(f"ABBRUCH, Kopie weicht ab: {dst}")
                if e["aktion"] != "kopie": os.remove(src)
            log.write(json.dumps(zeile, ensure_ascii=False) + "\n")
            zaehler[e["aktion"]] += 1
            if e["aktion"] == "quarantaene": liste.append(f"| {e['quelle']} | {e.get('grund','')} |")
    if liste and not trocken:
        l = qu / "LISTE.md"; l.parent.mkdir(parents=True, exist_ok=True)
        with open(l, "a", encoding="utf-8") as f:
            f.write(f"# Aussortiert {datetime.date.today().isoformat()}\n\nNichts gelöscht. Verschoben aus {q}.\n\n| Datei | Grund |\n|---|---|\n" + "\n".join(liste) + "\n")
    return zaehler

def undo(protokoll):
    n = 0
    for line in reversed(open(protokoll, encoding="utf-8").read().splitlines()):
        z = json.loads(line)
        if z.get("trocken"): continue
        src, dst = pathlib.Path(z["quelle"]), pathlib.Path(z["ziel"])
        if z["aktion"] == "kopie":
            if dst.exists() and sha(dst) == sha(dst): dst.unlink(); n += 1
            continue
        if dst.exists() and not src.exists():
            src.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(dst, src)
            if sha(src) != sha(dst): src.unlink(); raise SystemExit(f"ABBRUCH beim Zuruecknehmen: {src}")
            dst.unlink(); n += 1
    return n

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "undo":
        print("zurueckgenommen:", undo(sys.argv[2])); sys.exit()
    plan = json.load(open(sys.argv[2], encoding="utf-8"))
    fehler = pruefen(plan)
    if fehler:
        print("PLAN NICHT AUSFUEHRBAR:"); [print(" -", f) for f in fehler]; sys.exit(1)
    if cmd == "check": print("Plan geprueft:", len(plan["eintraege"]), "Eintraege, keine Fehler"); sys.exit()
    trocken = "--dry-run" in sys.argv
    print(("TROCKENLAUF " if trocken else "AUSGEFUEHRT ") + json.dumps(ausfuehren(plan, sys.argv[3], trocken)))
