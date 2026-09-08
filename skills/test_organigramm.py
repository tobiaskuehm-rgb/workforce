"""Das Organigramm und das Register sagen dasselbe; dieser Waechter haelt sie zusammen.

Ein Organigramm, das eine Identitaet nennt, die das Register nicht kennt, oder eine, die
zwei Vorgesetzte hat, oder das eine Identitaet des Registers vergisst, meldet sich nicht von
selbst. Jede Zusicherung ist eine reine Funktion ueber ihren Eingaben, mit Gegenprobe, die
genau einen Verstoss verlangt (Regel 47). python3 3.9, ohne Netz.
"""

import pathlib
import re
import unittest

SKILLS = pathlib.Path(__file__).resolve().parent
ORGANIGRAMM = SKILLS / "ORGANIGRAMM.md"
REGISTER = SKILLS / "README.md"


def ordner_im_register(text):
    """Die Ordnerspalte des Registers: `karl/` -> karl."""
    kopf = text.index("## Register")
    return sorted(set(re.findall(r"^\| [^|]+ \| `([\w-]+)/` \|", text[kopf:], re.MULTILINE)))


def zeilen_im_organigramm(text):
    """[(ordner, vorgesetzter), ...] aus der Tabelle Berichtswege."""
    a = text.index("## Berichtswege"); b = text.index("## Takt")
    return [(o, v.strip()) for o, v in re.findall(r"^\| [^|]+ \| `([\w-]+)/` \| ([^|]+) \|", text[a:b], re.MULTILINE)]


# --- Zusicherungen ---------------------------------------------------------

def fehlt_im_organigramm(register_ordner, organigramm):
    return sorted(set(register_ordner) - {o for o, _ in organigramm})


def unbekannt_im_organigramm(register_ordner, organigramm):
    return sorted({o for o, _ in organigramm} - set(register_ordner))


def mehrfach_im_organigramm(organigramm):
    namen = [o for o, _ in organigramm]
    return sorted({o for o in namen if namen.count(o) > 1})


def vorgesetzter_unbekannt(organigramm, namen_der_identitaeten):
    """Ein Vorgesetzter ist der CEO oder der Name einer Identitaet aus der Tabelle."""
    erlaubt = {"CEO"} | set(namen_der_identitaeten)
    return sorted("%s -> %s" % (o, v) for o, v in organigramm if v not in erlaubt)


def namen(text):
    """Der Vorname am Zeilenanfang der Tabelle: 'Karl `SAO-001`, COO' -> Karl."""
    a = text.index("## Berichtswege"); b = text.index("## Takt")
    return [m.split()[0] for m in re.findall(r"^\| ([^|`]+)", text[a:b], re.MULTILINE) if m.strip() not in ("Identität", "---")]


# --- Tests -----------------------------------------------------------------

class OrganigrammTest(unittest.TestCase):
    def setUp(self):
        self.register = ordner_im_register(REGISTER.read_text())
        self.text = ORGANIGRAMM.read_text()
        self.org = zeilen_im_organigramm(self.text)

    def test_es_gibt_ueberhaupt_zeilen(self):
        self.assertGreaterEqual(len(self.org), 5)
        self.assertGreaterEqual(len(self.register), 5)

    def test_jede_identitaet_des_registers_steht_im_organigramm(self):
        self.assertEqual([], fehlt_im_organigramm(self.register, self.org))

    def test_das_organigramm_nennt_keine_fremde_identitaet(self):
        self.assertEqual([], unbekannt_im_organigramm(self.register, self.org))

    def test_jede_identitaet_hat_genau_einen_vorgesetzten(self):
        self.assertEqual([], mehrfach_im_organigramm(self.org))

    def test_jeder_vorgesetzte_ist_der_ceo_oder_eine_identitaet(self):
        self.assertEqual([], vorgesetzter_unbekannt(self.org, namen(self.text)))

    def test_der_pruefer_haengt_beim_ceo(self):
        # Wer prueft, wird nicht von dem gesteuert, den er prueft.
        self.assertIn(("gerd", "CEO"), self.org)

    # Gegenproben: jede Zusicherung muss rot werden koennen.
    def test_eine_vergessene_identitaet_faellt_auf(self):
        self.assertEqual(["wolle"], fehlt_im_organigramm(["karl", "wolle"], [("karl", "CEO")]))

    def test_eine_fremde_identitaet_faellt_auf(self):
        self.assertEqual(["geist"], unbekannt_im_organigramm(["karl"], [("karl", "CEO"), ("geist", "Karl")]))

    def test_zwei_vorgesetzte_fallen_auf(self):
        self.assertEqual(["marv"], mehrfach_im_organigramm([("marv", "Anastasia"), ("marv", "Karl")]))

    def test_ein_unbekannter_vorgesetzter_faellt_auf(self):
        self.assertEqual(["karl -> Codex"], vorgesetzter_unbekannt([("karl", "Codex")], ["Karl"]))


if __name__ == "__main__":
    unittest.main()
