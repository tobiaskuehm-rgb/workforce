"""Die Noten im Ideen-Battle sind auf einen Bewerter und einen Regelstand rueckfuehrbar.

Grundlage: DEC-046 (CEO, 2026-09-11), Verfahren in thorsten/references/blinde-bewertung.md.
Drei Zusicherungen ueber skills/gedaechtnis/thorsten.md: kein Bewerter gleich Erzeuger, kein
Regelstand juenger als die Note, keine Haeufung der Spitzenwerte in einem Feld. Jede ist eine
reine Funktion ueber ihren Eingaben mit Gegenprobe, die genau einen Verstoss verlangt (Regel 47).

Die Spalten gibt es im Gedaechtnis heute noch nicht. Zeilen ohne sie werden LAUT uebersprungen
und gezaehlt; dieser Waechter meldet nie Gruen fuer etwas, das er nicht gelesen hat.
python3 3.9, ohne Netz.
"""

import pathlib
import re
import sys
import unittest

SKILLS = pathlib.Path(__file__).resolve().parent
GEDAECHTNIS = SKILLS / "gedaechtnis" / "thorsten.md"

PFLICHTSPALTEN = ("Datum", "Kandidat", "Feld", "Erzeuger", "Bewerter", "Regelstand", "Summe")
SPITZE = 10  # so viele hoechste Summen werden auf Haeufung geprueft


# --- Lesen -----------------------------------------------------------------

def _zellen(zeile):
    return [z.strip() for z in zeile.strip().strip("|").split("|")]


def tabellenzeilen(text, ueberschrift="## Frühere Urteile"):
    """[(kopf, [zellen]), ...] der Tabelle unter der Ueberschrift; leer, wenn es sie nicht gibt."""
    if ueberschrift not in text:
        return None, []
    rest = text[text.index(ueberschrift):]
    ende = rest.find("\n## ", 1)
    block = rest[:ende if ende > 0 else len(rest)]
    roh = [z for z in block.splitlines() if z.strip().startswith("|")]
    if not roh:
        return None, []
    kopf = _zellen(roh[0])
    daten = [_zellen(z) for z in roh[1:] if not set(z.replace("|", "").strip()) <= set("- ")]
    return kopf, daten


def noten(kopf, daten):
    """Nur die Zeilen, die alle Pflichtspalten gefuellt haben, als dict je Zeile."""
    if not kopf or any(s not in kopf for s in PFLICHTSPALTEN):
        return []
    idx = {s: kopf.index(s) for s in PFLICHTSPALTEN}
    fertig = []
    for zellen in daten:
        if len(zellen) < len(kopf):
            continue
        werte = {s: zellen[i] for s, i in idx.items()}
        if all(werte[s] for s in PFLICHTSPALTEN):
            fertig.append(werte)
    return fertig


def unvollstaendig(kopf, daten):
    """Zahl der Tabellenzeilen, die der Waechter NICHT beurteilen kann."""
    return len(daten) - len(noten(kopf, daten))


# --- Zusicherungen (reine Funktionen) --------------------------------------

def _tag(wert):
    """Das erste JJJJ-MM-TT in einem Feld; None, wenn keines drinsteht."""
    m = re.search(r"\d{4}-\d{2}-\d{2}", wert or "")
    return m.group(0) if m else None


def _zahl(wert):
    m = re.search(r"\d+", wert or "")
    return int(m.group(0)) if m else None


def bewerter_gleich_erzeuger(zeilen):
    return sorted(
        "%s: %s benotet sich selbst" % (z["Kandidat"], z["Erzeuger"])
        for z in zeilen
        if z["Bewerter"].strip().lower() == z["Erzeuger"].strip().lower()
    )


def regelstand_juenger_als_note(zeilen):
    """Der Filterstand darf nicht nach der Benotung entstanden sein (nie messen und regeln im selben Lauf)."""
    treffer = []
    for z in zeilen:
        note, regel = _tag(z["Datum"]), _tag(z["Regelstand"])
        if note is None or regel is None:
            treffer.append("%s: Datum oder Regelstand ohne Tag" % z["Kandidat"])
        elif regel > note:
            treffer.append("%s: Regelstand %s juenger als Note %s" % (z["Kandidat"], regel, note))
    return sorted(treffer)


def haeufung(zeilen, spitze=SPITZE):
    """Rot, wenn mehr als die Haelfte der hoechsten Summen in einem Feld liegt."""
    bewertet = [z for z in zeilen if _zahl(z["Summe"]) is not None]
    if len(bewertet) < spitze:
        return []  # zu wenig Material; die Zahl meldet der Bericht, nicht diese Funktion
    beste = sorted(bewertet, key=lambda z: _zahl(z["Summe"]), reverse=True)[:spitze]
    felder = [z["Feld"].strip() for z in beste]
    return sorted(
        "%s: %d von %d der hoechsten Summen" % (f, felder.count(f), spitze)
        for f in set(felder)
        if felder.count(f) * 2 > spitze
    )


# --- Tests -----------------------------------------------------------------

class BattleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = GEDAECHTNIS.read_text(encoding="utf-8")
        cls.kopf, cls.daten = tabellenzeilen(text)
        cls.zeilen = noten(cls.kopf, cls.daten)
        cls.offen = unvollstaendig(cls.kopf, cls.daten)
        # Laut, nicht still: dieser Waechter sagt immer, wie viel er gelesen hat.
        sys.stderr.write(
            "\n[test_battle] %d Tabellenzeilen, davon %d mit Bewerter/Regelstand/Feld pruefbar, "
            "%d uebersprungen.\n" % (len(cls.daten), len(cls.zeilen), cls.offen)
        )

    def _verlangt_zeilen(self):
        if not self.zeilen:
            self.skipTest(
                "UEBERSPRUNGEN: keine der %d Zeilen in %s hat die Spalten %s. "
                "Das ist kein Gruen — bis zum ersten Durchgang nach DEC-046 ist nichts geprueft."
                % (len(self.daten), GEDAECHTNIS.name, ", ".join(PFLICHTSPALTEN))
            )

    def test_die_tabelle_ist_ueberhaupt_lesbar(self):
        self.assertIsNotNone(self.kopf, "Abschnitt '## Frühere Urteile' nicht gefunden")
        self.assertGreaterEqual(len(self.daten), 1)

    def test_kein_bewerter_ist_sein_eigener_erzeuger(self):
        self._verlangt_zeilen()
        self.assertEqual([], bewerter_gleich_erzeuger(self.zeilen))

    def test_kein_regelstand_ist_juenger_als_seine_note(self):
        self._verlangt_zeilen()
        self.assertEqual([], regelstand_juenger_als_note(self.zeilen))

    def test_keine_haeufung_in_einem_feld(self):
        self._verlangt_zeilen()
        self.assertEqual([], haeufung(self.zeilen))

    # --- Gegenproben: jede Zusicherung muss rot werden koennen ---

    def test_selbstbenotung_faellt_auf(self):
        self.assertEqual(
            ["G: Thorsten benotet sich selbst"],
            bewerter_gleich_erzeuger([
                {"Kandidat": "G", "Erzeuger": "Thorsten", "Bewerter": "thorsten"},
                {"Kandidat": "H", "Erzeuger": "Thorsten", "Bewerter": "Marv"},
            ]),
        )

    def test_ein_juengerer_regelstand_faellt_auf(self):
        self.assertEqual(
            ["G: Regelstand 2026-09-11 juenger als Note 2026-09-10"],
            regelstand_juenger_als_note([
                {"Kandidat": "G", "Datum": "2026-09-10", "Regelstand": "abc1234 2026-09-11"},
                {"Kandidat": "H", "Datum": "2026-09-10", "Regelstand": "37ed946 2026-09-10"},
            ]),
        )

    def test_ein_regelstand_ohne_tag_faellt_auf(self):
        self.assertEqual(
            ["G: Datum oder Regelstand ohne Tag"],
            regelstand_juenger_als_note([{"Kandidat": "G", "Datum": "2026-09-10", "Regelstand": "abc1234"}]),
        )

    def test_haeufung_faellt_auf(self):
        zeilen = [{"Kandidat": str(i), "Feld": "Brandschutz" if i < 6 else "Vermietung",
                   "Summe": str(60 - i)} for i in range(10)]
        self.assertEqual(["Brandschutz: 6 von 10 der hoechsten Summen"], haeufung(zeilen))

    def test_genau_die_haelfte_ist_noch_keine_haeufung(self):
        zeilen = [{"Kandidat": str(i), "Feld": "Brandschutz" if i < 5 else "Vermietung",
                   "Summe": str(60 - i)} for i in range(10)]
        self.assertEqual([], haeufung(zeilen))

    def test_nur_die_hoechsten_summen_zaehlen(self):
        # Elf Zeilen, die elfte ist die schlechteste und kippt die Haeufung nicht mehr.
        zeilen = [{"Kandidat": str(i), "Feld": "Brandschutz" if i < 6 else "Vermietung",
                   "Summe": str(60 - i)} for i in range(11)]
        self.assertEqual(["Brandschutz: 6 von 10 der hoechsten Summen"], haeufung(zeilen))

    def test_eine_zeile_ohne_pflichtspalten_wird_nicht_gezaehlt(self):
        kopf = list(PFLICHTSPALTEN)
        voll = ["2026-09-10", "G", "Brandschutz", "Thorsten", "Marv", "37ed946 2026-09-10", "56"]
        luecke = ["2026-09-10", "H", "Brandschutz", "Thorsten", "", "37ed946 2026-09-10", "49"]
        self.assertEqual(1, len(noten(kopf, [voll, luecke])))
        self.assertEqual(1, unvollstaendig(kopf, [voll, luecke]))

    def test_eine_tabelle_ohne_neue_spalten_liefert_keine_note(self):
        self.assertEqual([], noten(["Datum", "Kandidat", "Status", "Quelle"], [["2026-09-10", "G", "TEST", "Lauf"]]))


if __name__ == "__main__":
    unittest.main()
