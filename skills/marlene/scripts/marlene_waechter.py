#!/usr/bin/env python3
"""Drei Waechter fuer Marlenes Betrieb. Standardbibliothek, Python 3.9, nur lesend.

  marlene_waechter.py [--basis <pfad>] [--tage 7] [--markdown]

Prueft drei Dinge, die am 12.09.2026 aus sechs Tagen echter Arbeit als Luecke
gemessen wurden (skills/marlene-workspace/praxis-2026-09-12/BEWERTUNG.md):

  1 Poststelle gegen Register  Ein Schreiben ging laut Postprotokoll hinaus, und
    der Ausgang oder das Vorgangsregister fuehrt es weiter als unversendet.
  2 Liegezeit der Klaerfaelle  Ein Fall liegt laenger als die vereinbarten Tage.
  3 Freigabekennung            Ein Ausgang hat keine Freigabe in seiner Vorgangsdatei.

Dazu meldet der Waechter seinen eigenen letzten Lauf: Ein Waechter, der nicht
laeuft, meldet nichts, und nichts liest sich wie gruen (3-Loop 12.09.2026).

Exitcode 0 wenn alles gruen, 1 wenn ein Waechter rot ist, 2 bei Lesefehler.
Das Skript veraendert nichts ausser seiner eigenen Laufzeile im Protokoll.
"""
import argparse
import datetime
import json
import os
import pathlib
import sys

# The nightly run may find the filing under either root; the first that exists wins.
BASIS_KANDIDATEN = [
    pathlib.Path.home() / "Ablage" / "01_Ablage_Eingang",
    pathlib.Path.home() / "Library/CloudStorage/GoogleDrive-Tobias.kuehm@icloud.com"
    / "Meine Ablage" / "01_Ablage_Eingang",
]
LAUF_FRIST_STUNDEN = 36  # a nightly guard that has not run for this long is itself a finding


def basis_finden(vorgabe):
    if vorgabe:
        p = pathlib.Path(vorgabe).expanduser()
        if not p.is_dir():
            raise SystemExit("Basis nicht gefunden: %s" % p)
        return p
    for p in BASIS_KANDIDATEN:
        if p.is_dir():
            return p
    raise SystemExit("Keine Ablage gefunden; --basis angeben.")


def zeilen(pfad):
    """JSONL lesen und kaputte Zeilen ueberspringen, aber zaehlen."""
    gut, kaputt = [], 0
    if not pfad.exists():
        return gut, kaputt
    for zeile in pfad.read_text(encoding="utf-8", errors="replace").splitlines():
        zeile = zeile.strip()
        if not zeile:
            continue
        try:
            gut.append(json.loads(zeile))
        except ValueError:
            kaputt += 1
    return gut, kaputt


def gesendete(postprotokoll):
    """Was laut Protokoll hinausging, geschluesselt nach Freigabekennung.

    Das Postprotokoll fuehrt Empfaenger, Betreff und Freigabe, aber keine
    Entwurfskennung; die Bruecke zum Ausgang ist deshalb die Freigabe (F07, F16).
    Ein Versand ohne Freigabe im Protokoll ist selbst ein Fund, kein Schweigen.
    """
    raus = {}
    ohne_freigabe = []
    for e in postprotokoll:
        if e.get("aktion") != "senden" or e.get("ergebnis") != "gesendet":
            continue
        freigabe = str(e.get("freigabe") or "").strip()
        if not freigabe:
            ohne_freigabe.append(e.get("zeit", ""))
            continue
        raus.setdefault(freigabe, e.get("zeit", ""))
    return raus, ohne_freigabe


def waechter_1(basis):
    """Gesendet laut Protokoll, aber im Ausgang nicht als versendet verbucht.

    Zwei Stufen, damit der Waechter nicht bei jedem Lauf dieselbe Zeile
    dreiundzwanzigmal meldet: Fuehrt keine einzige Vorgangsdatei einen
    Versandvermerk, ist das ein Befund ueber das Verfahren. Sobald das Feld
    gepflegt wird, wird jede Luecke einzeln gemeldet.
    """
    marlene = basis / "_Marlene"
    post, kaputt = zeilen(marlene / "protokoll" / "post.jsonl")
    if not post:
        return ["Postprotokoll fehlt oder ist leer: %s" % (marlene / "protokoll/post.jsonl")], 0
    raus, ohne_freigabe = gesendete(post)
    funde = ["Versand am %s ohne Freigabekennung im Postprotokoll" % z[:16]
             for z in ohne_freigabe]
    if not raus:
        return funde, kaputt

    vorgaenge = {}
    ordner = marlene / "ausgang"
    if ordner.is_dir():
        for datei in sorted(ordner.glob("*.vorgang.json")):
            try:
                daten = json.loads(datei.read_text(encoding="utf-8"))
            except ValueError:
                continue
            freigabe = str(daten.get("freigabe") or "").strip()
            if freigabe:
                vorgaenge[freigabe] = (datei.name.split(".")[0], daten)

    mit_vermerk = sum(1 for _, d in vorgaenge.values() if d.get("gesendet_am"))
    if vorgaenge and mit_vermerk == 0:
        funde.append("Keine der %d Vorgangsdateien fuehrt einen Versandvermerk; %d Sendungen "
                     "lassen sich nicht gegenpruefen (Feld gesendet_am fehlt durchgaengig)"
                     % (len(vorgaenge), len(raus)))
        return funde, kaputt

    register = marlene / "VORGAENGE.md"
    text = register.read_text(encoding="utf-8", errors="replace") if register.exists() else ""
    for freigabe, zeit in sorted(raus.items()):
        if freigabe not in vorgaenge:
            funde.append("Versand mit Freigabe %s am %s gehoert zu keiner Vorgangsdatei"
                         % (freigabe, zeit[:16]))
            continue
        kennung, daten = vorgaenge[freigabe]
        if not daten.get("gesendet_am"):
            funde.append("%s (Freigabe %s) ging am %s hinaus, die Vorgangsdatei fuehrt "
                         "keinen Versand" % (kennung, freigabe, zeit[:16]))
        elif text and kennung not in text:
            funde.append("%s ging am %s hinaus und kommt in VORGAENGE.md nicht vor"
                         % (kennung, zeit[:16]))
    return funde, kaputt


def fund_wenn_aelter(name, liegt_seit, tage, jetzt):
    """Reine Funktion, damit die Gegenprobe Daten einspeisen kann (CLAUDE.md, Regel 47).

    Rueckgabe: Liste mit keinem oder genau einem Fund.
    """
    offen = (jetzt - liegt_seit).days
    if offen <= tage:
        return []
    return ["%s liegt seit %d Tagen zur Klaerung (seit %s)"
            % (name, offen, liegt_seit.strftime("%d.%m."))]


def waechter_2(basis, tage):
    """Klaerfaelle, die laenger als vereinbart liegen.

    Gemessen wird st_ctime, nicht st_mtime: Das Dokumentdatum einer kopierten
    Rechnung sagt nichts darueber, seit wann sie zur Klaerung liegt; ctime
    aendert sich beim Verschieben in den Ordner.
    """
    ordner = basis / "_Klären"
    if not ordner.is_dir():
        return [], 0
    jetzt = datetime.datetime.now()
    funde = []
    for datei in sorted(ordner.iterdir()):
        if datei.name.startswith(".") or datei.is_dir():
            continue
        liegt_seit = datetime.datetime.fromtimestamp(datei.stat().st_ctime)
        funde.extend(fund_wenn_aelter(datei.name, liegt_seit, tage, jetzt))
    return funde, 0


def waechter_3(basis):
    """Ausgaenge ohne Freigabekennung in der Vorgangsdatei."""
    ordner = basis / "_Marlene" / "ausgang"
    if not ordner.is_dir():
        return [], 0
    funde = []
    for datei in sorted(ordner.glob("*.vorgang.json")):
        kennung = datei.name.split(".")[0]
        try:
            daten = json.loads(datei.read_text(encoding="utf-8"))
        except ValueError:
            funde.append("%s: Vorgangsdatei ist nicht lesbar" % kennung)
            continue
        if not str(daten.get("freigabe") or "").strip():  # JSON null ist keine Freigabe
            funde.append("%s hat keine Freigabekennung in der Vorgangsdatei" % kennung)
    return funde, 0


def letzter_lauf(marlene):
    eintraege, _ = zeilen(marlene / "protokoll" / "waechter.jsonl")
    if not eintraege:
        return None
    return eintraege[-1].get("zeit")


def lauf_vermerken(marlene, ergebnis):
    """Die einzige Schreiboperation: eine Zeile, damit ein ausgefallener Lauf auffaellt."""
    ziel = marlene / "protokoll" / "waechter.jsonl"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    zeile = {"zeit": datetime.datetime.now().isoformat(timespec="seconds"),
             "ergebnis": ergebnis}
    with ziel.open("a", encoding="utf-8") as f:
        f.write(json.dumps(zeile, ensure_ascii=False) + "\n")


def bericht(basis, tage, schreiben=True):
    marlene = basis / "_Marlene"
    vorher = letzter_lauf(marlene)
    pruefungen = [
        ("Poststelle gegen Register", waechter_1(basis)),
        ("Liegezeit der Klaerfaelle (%d Tage)" % tage, waechter_2(basis, tage)),
        ("Freigabekennung je Ausgang", waechter_3(basis)),
    ]
    zeilen_aus = []
    rot = False
    for name, (funde, kaputt) in pruefungen:
        if funde:
            rot = True
            zeilen_aus.append("- **ROT — %s:**" % name)
            for f in funde:
                zeilen_aus.append("  - %s" % f)
        else:
            zeilen_aus.append("- gruen — %s" % name)
        if kaputt:
            zeilen_aus.append("  - Hinweis: %d unlesbare Protokollzeilen uebersprungen" % kaputt)

    # A guard that did not run reports nothing, and nothing reads like green.
    if vorher:
        alt = datetime.datetime.now() - datetime.datetime.fromisoformat(vorher)
        stunden = alt.days * 24 + alt.seconds // 3600
        if stunden > LAUF_FRIST_STUNDEN:
            rot = True
            zeilen_aus.append("- **ROT — Waechter selbst:** letzter Lauf vor %d Stunden (%s)"
                              % (stunden, vorher[:16]))
        else:
            zeilen_aus.append("- gruen — Waechter selbst: letzter Lauf %s" % vorher[:16])
    else:
        zeilen_aus.append("- Waechter selbst: erster Lauf, keine Vorgeschichte")

    if schreiben:
        lauf_vermerken(marlene, "rot" if rot else "gruen")
    kopf = "## Waechter, %s" % datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    return kopf + "\n" + "\n".join(zeilen_aus), rot


def main():
    p = argparse.ArgumentParser(description="Drei Waechter fuer Marlenes Betrieb")
    p.add_argument("--basis", help="Pfad zu 01_Ablage_Eingang")
    p.add_argument("--tage", type=int, default=7, help="Hoechstliegezeit Klaerfaelle")
    p.add_argument("--kein-eintrag", action="store_true",
                   help="Laufzeile nicht schreiben (fuer Proben)")
    a = p.parse_args()
    try:
        basis = basis_finden(a.basis)
        text, rot = bericht(basis, a.tage, schreiben=not a.kein_eintrag)
    except OSError as fehler:
        print("Lesefehler: %s" % fehler, file=sys.stderr)
        return 2
    print(text)
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main())
