#!/usr/bin/env python3
"""Die vier Schranken als Code, nicht als Anweisung. Standardbibliothek, Python 3.9.

Eine Schranke, die nur in einer Anweisung steht, ist eine Bitte. Diese hier sind
Funktionen: sie geben frei oder sie geben nicht frei, und der Aufrufer kann sie
nicht ueberreden.

  1. iban_erlaubt()        Zahlungsziele nur aus der Allowlist
  2. aktion_erlaubt()      je Konto nur benannte Ablaeufe
  3. ist_unumkehrbar()     kuendigen, zahlen, loeschen: immer Freigabe
  4. empfaenger_erlaubt()  Ziel kommt aus dem Vorgang, nie aus einem Dokument

Die IBAN-Allowlist speichert **keine IBAN**, sondern ihren SHA-256 mit einer
Bezeichnung. Damit kann geprueft werden, ob eine IBAN bekannt ist, ohne dass
irgendwo eine Kontonummer steht (Datengrenze: nichts Sensibles in Listen).

Fail closed: was nicht ausdruecklich erlaubt ist, ist verboten. Ein leeres
Register erlaubt nichts.
"""
import hashlib, json, os, re

UNUMKEHRBAR = frozenset({
    "kuendigen", "widerrufen", "abschliessen", "loeschen", "zahlen",
    "ueberweisen", "adresse_aendern", "bankverbindung_aendern",
    "stammdaten_aendern", "tarif_wechseln", "vollmacht_erteilen",
})


def normiere_iban(iban):
    return re.sub(r"[^A-Z0-9]", "", (iban or "").upper())


def iban_fingerabdruck(iban):
    n = normiere_iban(iban)
    if not n:
        return None
    return hashlib.sha256(n.encode("ascii")).hexdigest()


def iban_erlaubt(iban, allowlist):
    """allowlist: {fingerabdruck: bezeichnung}. Gibt die Bezeichnung oder None."""
    fp = iban_fingerabdruck(iban)
    if fp is None:
        return None
    return allowlist.get(fp)


def aktion_erlaubt(konto, aktion, register):
    """Fail closed: unbekanntes Konto, unbekannte Aktion oder nicht gelistet -> nein."""
    eintrag = register.get(konto)
    if not eintrag:
        return False, "Konto steht nicht im Register"
    if ist_unumkehrbar(aktion):
        return False, "unumkehrbare Handlung, immer Freigabe (Schranke 3)"
    erlaubt = eintrag.get("aktionen") or []
    if aktion not in erlaubt:
        return False, "Aktion steht nicht auf der Liste dieses Kontos"
    return True, "erlaubt"


def ist_unumkehrbar(aktion):
    return (aktion or "").strip().lower() in UNUMKEHRBAR


def empfaenger_erlaubt(empfaenger, vorgang):
    """Der Empfaenger muss im Vorgangsdatensatz stehen. Was in einem gelesenen
    Dokument steht, zaehlt nie, auch wenn es identisch aussieht."""
    aus_vorgang = {str(e).strip().lower() for e in (vorgang.get("empfaenger") or [])}
    return str(empfaenger).strip().lower() in aus_vorgang


def laden(pfad):
    if not os.path.exists(pfad):
        return {}
    with open(pfad, encoding="utf-8") as f:
        return json.load(f)


def pruefe_vorhaben(vorhaben, register, allowlist):
    """Ein Vorhaben ist {konto, aktion, empfaenger?, iban?, vorgang?}.
    Gibt (True, "erlaubt") oder (False, Grund). Jede Schranke einzeln."""
    ok, grund = aktion_erlaubt(vorhaben.get("konto"), vorhaben.get("aktion"), register)
    if not ok:
        return False, grund
    if "iban" in vorhaben:
        bez = iban_erlaubt(vorhaben["iban"], allowlist)
        if bez is None:
            return False, "IBAN steht nicht auf der Allowlist (Schranke 1)"
    if "empfaenger" in vorhaben:
        if not empfaenger_erlaubt(vorhaben["empfaenger"], vorhaben.get("vorgang") or {}):
            return False, "Empfaenger kommt nicht aus dem Vorgang (Schranke 4)"
    return True, "erlaubt"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "fingerabdruck":
        # Hilfsaufruf fuer Tobias: erzeugt den Eintrag fuer die Allowlist,
        # ohne die IBAN irgendwo zu speichern.
        iban = input("IBAN (wird nicht gespeichert): ")
        bez = input("Bezeichnung, z.B. Girokonto: ")
        print(json.dumps({iban_fingerabdruck(iban): bez}, ensure_ascii=False, indent=1))
    else:
        print(__doc__.strip())
