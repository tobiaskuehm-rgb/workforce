#!/usr/bin/env python3
"""Zugriff auf Zugangsdaten, mit Schranke davor und Protokoll dahinter.

Die Zugangsdaten liegen im macOS-Schluesselbund, nie in einer Datei, nie im Repo,
nie in der Ablage. Dieses Modul holt sie und gibt sie **an den Aufrufer im
Programm** weiter; es druckt sie nie, schreibt sie nie ins Protokoll und nimmt
sie nie entgegen. Angelegt werden sie von Tobias selbst:

    security add-generic-password -a "<benutzername>" -s "marlene-swe-erfurt" -w

Vor jedem Zugriff wird geprueft:
  - steht das Konto im Register (marlene_konten.json)
  - ist die Aktion fuer dieses Konto erlaubt (marlene_schranken.aktion_erlaubt)
Beides fail closed. Danach eine Zeile ins Protokoll: Zeit, Konto, Aktion, Zweck.
Der Wert steht dort nie.

    marlene_tresor.py pruefen <konto> <aktion>     nur die Schranke, ohne Zugriff
    marlene_tresor.py status                       welche Konten sind hinterlegt
"""
import datetime, json, os, subprocess, sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import marlene_schranken as S

REGISTER = os.path.join(HIER, "marlene_konten.json")
PROTOKOLL_VORGABE = os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-Tobias.kuehm@icloud.com/Meine Ablage/"
    "01_Ablage_Eingang/_Marlene/protokoll/zugriffe.jsonl")


def register():
    r = S.laden(REGISTER)
    return {k: v for k, v in r.items() if not k.startswith("_")}


def protokollieren(konto, aktion, zweck, ergebnis, protokoll=None):
    zeile = {"zeit": datetime.datetime.now().isoformat(timespec="seconds"),
             "konto": konto, "aktion": aktion, "zweck": zweck, "ergebnis": ergebnis}
    p = protokoll or PROTOKOLL_VORGABE
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return zeile


def hinterlegt(konto, reg=None):
    """Gibt es einen Schluesselbund-Eintrag? Fragt nur nach der Existenz."""
    reg = reg if reg is not None else register()
    e = reg.get(konto)
    if not e:
        return False
    r = subprocess.run(["security", "find-generic-password", "-s", e["schluesselbund_dienst"]],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def geheimnis(konto, aktion, zweck, reg=None, protokoll=None):
    """Gibt (wert, None) oder (None, Grund). Der Wert wird nie protokolliert."""
    reg = reg if reg is not None else register()
    ok, grund = S.aktion_erlaubt(konto, aktion, reg)
    if not ok:
        protokollieren(konto, aktion, zweck, "abgelehnt: " + grund, protokoll)
        return None, grund
    dienst = reg[konto]["schluesselbund_dienst"]
    r = subprocess.run(["security", "find-generic-password", "-s", dienst, "-w"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        protokollieren(konto, aktion, zweck, "kein Eintrag im Schluesselbund", protokoll)
        return None, "kein Eintrag im Schluesselbund fuer " + dienst
    protokollieren(konto, aktion, zweck, "freigegeben", protokoll)
    return r.stdout.rstrip("\n"), None


def main(argv):
    reg = register()
    if len(argv) > 1 and argv[1] == "status":
        for k, e in sorted(reg.items()):
            print("%-14s Klasse %s  %-28s %s" % (
                k, e["klasse"], e["anbieter"][:28],
                "hinterlegt" if hinterlegt(k, reg) else "noch kein Eintrag"))
            print("               erlaubt: " + ", ".join(e["aktionen"]))
        return 0
    if len(argv) > 3 and argv[1] == "pruefen":
        ok, grund = S.aktion_erlaubt(argv[2], argv[3], reg)
        print(("ERLAUBT: " if ok else "ABGELEHNT: ") + grund)
        return 0 if ok else 1
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
