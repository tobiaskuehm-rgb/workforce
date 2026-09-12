"""Jede Registeridentitaet kennt die gemeinsame Antwortform.

ANTWORTFORM.md gilt fuer alle; ein Skill, der sie nicht nennt, faellt niemandem auf, weil
er fuer sich gelesen vollstaendig aussieht. Jede Zusicherung ist eine reine Funktion ueber
ihren Eingaben, mit Gegenprobe, die genau einen Verstoss verlangt (Regel 47).
python3 3.9, ohne Netz.
"""

import pathlib
import re
import unittest

SKILLS = pathlib.Path(__file__).resolve().parent
REGISTER = SKILLS / "README.md"
FORM = SKILLS / "ANTWORTFORM.md"


def ordner_im_register(text):
    """Die Ordnerspalte des Registers: `karl/` -> karl."""
    kopf = text.index("## Register")
    return sorted(set(re.findall(r"^\| [^|]+ \| `([\w-]+)/` \|", text[kopf:], re.MULTILINE)))


def skilltexte(ordner):
    """{ordner: text} — ein fehlender Skill ist ein leerer Text, kein Absturz."""
    paare = {}
    for o in ordner:
        p = SKILLS / o / "SKILL.md"
        paare[o] = p.read_text() if p.exists() else ""
    return paare


# --- Zusicherungen ---------------------------------------------------------

def ohne_verweis(texte):
    """Ordner, deren Skilltext ANTWORTFORM.md nicht nennt."""
    return sorted(o for o, t in texte.items() if "ANTWORTFORM.md" not in t)


def ohne_optionenregel(texte):
    """Ein Verweis ohne die Sache ist ein Link; genannt sein muss die Tippentscheidung."""
    verletzt = []
    for o, t in texte.items():
        if "ANTWORTFORM.md" not in t:
            continue
        if not re.search(r"`ja`/`nein`|`a`/`b`/`c`", t):
            verletzt.append(o)
    return sorted(verletzt)


def fehlende_skills(texte):
    return sorted(o for o, t in texte.items() if not t)


def form_vollstaendig(text):
    """Die gemeinsame Datei traegt ihre Herkunft und den Stand der Lesart.

    Der Stand ist entweder offen oder bestaetigt - aber er steht da. Eine Lesart ohne Stand
    liest sich wie eine Anweisung des CEO, und genau das war sie am 2026-09-12 noch nicht.
    """
    fehlt = [p for p in ("2026-09-10", "2026-09-12", "Karl", "antippen") if p not in text]
    if "noch nicht bestätigt" not in text and "bestätigt am" not in text:
        fehlt.append("Stand der Lesart")
    return fehlt


# --- Tests -----------------------------------------------------------------

class AntwortformTest(unittest.TestCase):
    def setUp(self):
        self.ordner = ordner_im_register(REGISTER.read_text())
        self.texte = skilltexte(self.ordner)

    def test_es_gibt_ueberhaupt_identitaeten(self):
        self.assertGreaterEqual(len(self.ordner), 5)

    def test_die_gemeinsame_datei_existiert(self):
        self.assertTrue(FORM.exists())

    def test_jeder_skill_existiert(self):
        self.assertEqual([], fehlende_skills(self.texte))

    def test_jede_identitaet_verweist_auf_die_antwortform(self):
        self.assertEqual([], ohne_verweis(self.texte))

    def test_jeder_verweis_nennt_die_optionenregel(self):
        self.assertEqual([], ohne_optionenregel(self.texte))

    def test_die_antwortform_nennt_herkunft_und_lesart(self):
        self.assertEqual([], form_vollstaendig(FORM.read_text()))

    def test_eine_lesart_ohne_stand_faellt_auf(self):
        ohne = "Regel. Herkunft: Chat 2026-09-10 und 2026-09-12, Lesart von Karl."
        self.assertEqual(["Stand der Lesart"], form_vollstaendig(ohne))
        self.assertEqual([], form_vollstaendig(ohne + " bestätigt am 2026-09-12."))
        self.assertEqual([], form_vollstaendig(ohne + " noch nicht bestätigt."))

    # Gegenproben: jede Zusicherung muss rot werden koennen.
    def test_ein_fehlender_verweis_faellt_auf(self):
        self.assertEqual(["cfo"], ohne_verweis({"karl": "siehe ANTWORTFORM.md", "cfo": "Zahlen zuerst."}))

    def test_ein_verweis_ohne_optionenregel_faellt_auf(self):
        self.assertEqual(
            ["cfo"],
            ohne_optionenregel({
                "karl": "ANTWORTFORM.md: `a`/`b`/`c`",
                "cfo": "siehe ANTWORTFORM.md",
            }),
        )

    def test_ein_fehlender_skill_faellt_auf(self):
        self.assertEqual(["geist"], fehlende_skills({"karl": "x", "geist": ""}))

    def test_eine_fehlende_herkunft_faellt_auf(self):
        self.assertEqual(
            ["2026-09-12", "Stand der Lesart"],
            form_vollstaendig("Chat 2026-09-10, Lesart von Karl."),
        )


if __name__ == "__main__":
    unittest.main()
