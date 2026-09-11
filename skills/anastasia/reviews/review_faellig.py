#!/usr/bin/env python3
"""Zaehlt je Identitaet die Commits seit ihrem letzten Review und meldet, wer faellig ist.

Aufruf:
    python3 skills/anastasia/reviews/review_faellig.py            # Tabelle, Exitcode 1 wenn jemand faellig ist
    python3 skills/anastasia/reviews/review_faellig.py --kurz     # nur die Faelligen, eine Zeile je Identitaet
    python3 skills/anastasia/reviews/review_faellig.py --gemacht <name> [<sha>]

Ein Commit "betrifft" eine Identitaet, wenn er ihren Skillordner beruehrt oder ihren
Anzeigenamen im Betreff traegt. Beides zusammen, weil Arbeit an einer Identitaet und Arbeit
durch eine Identitaet verschiedene Spuren hinterlassen.
"""
import json
import pathlib
import datetime
import subprocess
import sys
from typing import List, Optional, Set

HIER = pathlib.Path(__file__).resolve().parent
STAND = HIER / "stand.json"
WURZEL = HIER.parents[2]


def git(*args: str) -> str:
    fertig = subprocess.run(
        ["git", "-C", str(WURZEL), *args],
        capture_output=True, text=True, check=False,
    )
    if fertig.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {fertig.stderr.strip()}")
    return fertig.stdout


def lade() -> dict:
    return json.loads(STAND.read_text(encoding="utf-8"))


def schwelle(stand: dict, eintrag: dict) -> int:
    # Eigene Schwelle schlaegt den Zustandswert; Probezeit wird enger geprueft als Regelbetrieb.
    if eintrag.get("schwelle") is not None:
        return int(eintrag["schwelle"])
    if eintrag.get("zustand") == "probezeit":
        return int(stand["schwelle_probezeit"])
    return int(stand["schwelle_standard"])


def spuren_ausserhalb(eintrag, seit_datum):
    """Zaehlt Arbeitsspuren einer Identitaet ausserhalb des Repos.

    Wer im Drive oder in einem Vorgangsregister arbeitet, hinterlaesst dort Dateien und
    keinen Commit. Ohne diesen Weg zaehlt der Ausloeser fuer solche Identitaeten null,
    waehrend die Commits *ueber* sie mitgezaehlt werden — das Mass zeigte dann fremde
    Arbeit als ihre an (Einwand des CEO, 2026-09-10).
    """
    ort = eintrag.get("arbeitsort")
    if not ort:
        return None
    wurzel = pathlib.Path(ort).expanduser()
    if not wurzel.is_dir():
        return None
    grenze = datetime.datetime.strptime(seit_datum, "%Y-%m-%d").timestamp() if seit_datum else 0
    gezaehlt = 0
    for pfad in wurzel.rglob("*"):
        if pfad.is_file() and not pfad.name.startswith("."):
            try:
                if pfad.stat().st_mtime >= grenze:
                    gezaehlt += 1
            except OSError:
                continue
    return gezaehlt


def commits_seit(name, anzeige, seit, pfade):
    """Kurzhashes der Commits, die diese Identitaet betreffen, seit dem letzten Review.

    Rueckgabe: List[str]. Ohne Typannotation in der Signatur, weil der Mac dieses
    Projekts Python 3.9 fahrt und `str | None` dort ein TypeError ist (Regel G-011).
    """
    spanne = [f"{seit}..HEAD"] if seit else []
    treffer = set()  # type: Set[str]

    # Weg 1: Commits, die einen ihrer Pfade beruehren. Der Arbeitsbereich zaehlt mit:
    # `skills/<name>` als Pfadangabe trifft `skills/<name>-workspace` NICHT, und damit fielen
    # bis zum 2026-09-10 saemtliche Messrunden aus der Zaehlung — bei Karl drei, bei Thorsten
    # die einzige. Zusaetzliche Pfade stehen je Identitaet in `stand.json` unter `pfade`.
    for pfad in pfade:
        for zeile in git("log", "--format=%h", *spanne, "--", pfad).splitlines():
            if zeile.strip():
                treffer.add(zeile.strip())

    # Weg 2: Commits, deren Betreff mit ihrem Namen beginnt ("Marlene: ...").
    rufname = anzeige.split(" (")[0]
    for zeile in git("log", "--format=%h\t%s", *spanne).splitlines():
        if "\t" not in zeile:
            continue
        kurz, betreff = zeile.split("\t", 1)
        if betreff.lower().startswith(rufname.lower()):
            treffer.add(kurz)

    return sorted(treffer)


def bericht(nur_faellige=False):
    stand = lade()
    zeilen = []  # type: List[tuple]
    faellig = []  # type: List[tuple]
    for name, eintrag in stand["identitaeten"].items():
        if eintrag.get("zustand") == "ruht":
            zeilen.append((eintrag["anzeige"], "ruht", "", "-", ""))
            continue
        pfade = [f"skills/{name}", f"skills/{name}-workspace"] + eintrag.get("pfade", [])
        gezaehlt = commits_seit(name, eintrag["anzeige"], eintrag.get("letztes_review"), pfade)
        grenze = schwelle(stand, eintrag)
        seit_datum = eintrag.get("letztes_review_datum")
        aussen = spuren_ausserhalb(eintrag, seit_datum)
        # Der Ausloeser nimmt den groesseren der beiden Wege. Wer im Repo arbeitet, wird
        # ueber Commits faellig; wer draussen arbeitet, ueber seine Dateien.
        # Fuenf Commits sind ein Arbeitsabschnitt, fuenf geaenderte Dateien eine Stunde.
        # Beide Wege brauchen deshalb ihre eigene Schwelle, sonst wird eine Identitaet mit
        # externem Arbeitsort am Tag nach ihrem Review wieder faellig (gemessen 2026-09-10).
        grenze_aussen = int(stand.get("schwelle_arbeitsort", 40))
        # Ein Takt in Tagen schlaegt beide Zaehlwege: Wer produktiv nach aussen arbeitet, wird
        # nach Zeit geprueft und nicht nach Menge (CEO, 2026-09-11, fuer Marlene).
        takt = eintrag.get("takt_tage")
        faellig_nach_zeit = False
        if takt and seit_datum:
            heute = datetime.date.today()
            alter = (heute - datetime.date.fromisoformat(seit_datum)).days
            faellig_nach_zeit = alter >= int(takt)
            # Ein Wochentag verankert den Bericht: faellig ab diesem Tag, sobald seit dem
            # letzten Bericht ein neuer angebrochen ist (CEO, 2026-09-11: montags).
            tag = eintrag.get("takt_wochentag")
            if tag is not None:
                letzter = datetime.date.fromisoformat(seit_datum)
                faellig_nach_zeit = heute.weekday() >= int(tag) and (heute - letzter).days >= 1 and heute.isocalendar()[1] != letzter.isocalendar()[1]
        elif takt:
            faellig_nach_zeit = True
        # Ein Takt ERSETZT die Mengenschwellen, er ergaenzt sie nicht. Sonst stuende eine
        # produktive Identitaet dauerhaft auf faellig, und ein Waechter, der immer rot ist,
        # wird abgeschaltet statt gelesen (gemessen 2026-09-11: Marlene 64 von 40).
        if takt:
            ist_faellig = faellig_nach_zeit
        else:
            ist_faellig = len(gezaehlt) >= grenze or (aussen or 0) >= grenze_aussen
        wirksam = len(gezaehlt) if len(gezaehlt) >= grenze else (aussen or 0)
        if ist_faellig:
            faellig.append((name, eintrag["anzeige"], wirksam, grenze))
        zeilen.append((
            eintrag["anzeige"],
            eintrag.get("zustand", ""),
            f"{len(gezaehlt)}/{grenze}",
            "-" if aussen is None else "%d/%d" % (aussen, int(stand.get("schwelle_arbeitsort", 40))),
            "FAELLIG" if ist_faellig else "",
        ))

    if nur_faellige:
        for name, anzeige, anzahl, grenze in faellig:
            print(f"Review faellig: {anzeige} — {anzahl} Arbeitseinheiten seit dem letzten Review (Schwelle {grenze})")
    else:
        breite = max(len(z[0]) for z in zeilen)
        print(f"{'Identitaet'.ljust(breite)}  Zustand      Commits  Dateien  ")
        for anzeige, zustand, zaehler, aussen, marke in zeilen:
            print(f"{anzeige.ljust(breite)}  {zustand.ljust(11)}  {zaehler.ljust(7)}  {aussen.ljust(7)}  {marke}")
        print()
        print(f"{len(faellig)} von {len(stand['identitaeten'])} faellig." if faellig else "Niemand faellig.")

    # Exitcode 1 heisst: es liegt etwas an. Damit taugt der Aufruf als Gate.
    return 1 if faellig else 0


def gemacht(name, sha):
    stand = lade()
    if name not in stand["identitaeten"]:
        print(f"Unbekannte Identitaet: {name}", file=sys.stderr)
        return 2
    voll = git("rev-parse", sha or "HEAD").strip()
    stand["identitaeten"][name]["letztes_review"] = voll
    stand["identitaeten"][name]["letztes_review_datum"] = datetime.date.today().isoformat()
    STAND.write_text(json.dumps(stand, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{stand['identitaeten'][name]['anzeige']}: Review vermerkt auf {voll[:8]}.")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--gemacht":
        sys.exit(gemacht(args[1], args[2] if len(args) > 2 else None))
    sys.exit(bericht(nur_faellige=bool(args and args[0] == "--kurz")))
