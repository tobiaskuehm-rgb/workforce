#!/usr/bin/env python3
"""Liegt die Datei wirklich hier, oder ist sie nur ein Platzhalter?

Google Drive und iCloud halten Dateien als Platzhalter: der Eintrag im Ordner
sieht vollstaendig aus, der Inhalt liegt aber in der Cloud. `ls` zeigt die volle
Groesse, `stat` zeigt null belegte Bloecke. Wer so eine Datei liest, loest einen
Download aus, der bei grossen Scans minutenlang dauert oder haengt.

Gefunden am 2026-09-08: der halbe KV-Ordner war so, und die Texterkennung lieferte
deshalb leere Seiten statt einer Fehlermeldung. Ein Werkzeug, das nichts findet und
nichts meldet, liest sich wie ein bestandener Test.

    marlene_lokal.py pruefen  <pfad> [...]        Liste: lokal, Platzhalter, fehlt
    marlene_lokal.py holen    <pfad> [--sekunden N]  Platzhalter materialisieren

`holen` liest je Datei den Anfang und wartet hoechstens N Sekunden (Vorgabe 20).
Was danach immer noch Platzhalter ist, wird als solches gemeldet, nicht stillschweigend
uebergangen. Geschrieben wird nichts.
"""
import sys, os, subprocess

def zustand(p):
    try:
        s = os.stat(p)
    except FileNotFoundError:
        return "fehlt", 0
    if not os.path.isfile(p):
        return "kein_file", 0
    if s.st_size == 0:
        return "leer", 0
    return ("platzhalter" if s.st_blocks == 0 else "lokal"), s.st_size

def dateien(pfade):
    for p in pfade:
        if os.path.isdir(p):
            for wurzel, _, namen in os.walk(p):
                for n in sorted(namen):
                    if not n.startswith("."):
                        yield os.path.join(wurzel, n)
        else:
            yield p

def holen(p, sekunden):
    """Download anstossen, indem der Anfang gelesen wird. Bricht nach der Frist ab."""
    try:
        subprocess.run(["dd", "if=" + p, "of=/dev/null", "bs=1m", "count=1"],
                       timeout=sekunden, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False
    return zustand(p)[0] == "lokal"

def main(argv):
    if len(argv) < 3:
        print(__doc__.strip()); return 2
    befehl = argv[1]
    sekunden = 20
    if "--sekunden" in argv:
        i = argv.index("--sekunden"); sekunden = int(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    pfade = argv[2:]
    zaehler = {}
    offen = []
    for f in dateien(pfade):
        z, groesse = zustand(f)
        if befehl == "holen" and z == "platzhalter":
            z = "lokal" if holen(f, sekunden) else "platzhalter"
        zaehler[z] = zaehler.get(z, 0) + 1
        if z != "lokal":
            offen.append((z, groesse, f))
    for z, groesse, f in offen:
        print("%-12s %10d  %s" % (z, groesse, f))
    print("  ".join("%s=%d" % (k, v) for k, v in sorted(zaehler.items())))
    return 1 if any(z == "platzhalter" for z, _, _ in offen) else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
