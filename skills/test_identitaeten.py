"""Eine Identitaet steht an drei Stellen; dieser Waechter haelt sie zusammen.

Skill, Agent und Bot koennen unbemerkt auseinanderlaufen: Ein Skill verweist auf ein
Gedaechtnis, das niemand angelegt hat; ein Agent nennt ein Modell, das die Allowlist des
Bots nicht kennt; das Register nennt eine Identitaet, deren Ordner es nicht gibt. Keiner
dieser Faelle meldet sich von selbst.

Jede Zusicherung ist eine reine Funktion ueber ihren Eingaben, damit die Gegenprobe Daten
einspeisen und genau einen Verstoss verlangen kann (Regel 47: ein Waechter, der nie rot
werden kann, ist keiner). Laeuft auf python3 3.9 des Projektrechners, ohne Netz.
"""

import json
import pathlib
import re
import unittest

SKILLS = pathlib.Path(__file__).resolve().parent
WURZEL = SKILLS.parent
AGENTEN = WURZEL / ".claude" / "agents"
GEDAECHTNIS = SKILLS / "gedaechtnis"

# --- Lesen ------------------------------------------------------------------

def skillordner():
    return sorted(p.name for p in SKILLS.iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


def agentendateien():
    return sorted(p.name[:-3] for p in AGENTEN.glob("*.md"))


def kopf(text):
    """Frontmatter als flaches dict; Werte bleiben Text."""
    treffer = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not treffer:
        return {}
    felder = {}
    for zeile in treffer.group(1).splitlines():
        if ":" in zeile and not zeile.startswith(" "):
            schluessel, wert = zeile.split(":", 1)
            felder[schluessel.strip()] = wert.strip()
    return felder


# config.json und config.nas.json tragen Chat-Id und Workspace-Id und sind deshalb
# ignoriert (workforce/.gitignore). Auf einem frischen Klon fehlen sie: Der Waechter
# ueberspringt dann laut, statt falsch rot oder falsch gruen zu werden.
def botkonfiguration(name):
    p = WURZEL / "workforce" / name
    return json.loads(p.read_text()) if p.is_file() else None


def botmodelle(cfg):
    return {k: v["model"] for k, v in cfg["identities"].items()}


def erlaubte_modelle():
    quelle = (WURZEL / "workforce" / "models.py").read_text()
    return set(re.findall(r'^\s*"([\w.:-]+)": Model\(', quelle, re.MULTILINE))


# --- Zusicherungen als reine Funktionen -------------------------------------

def gedaechtnis_ohne_datei(verweise, vorhanden):
    """Ein Skill verweist auf ../gedaechtnis/X.md, das es nicht gibt."""
    return sorted("%s -> %s" % (skill, ziel)
                  for skill, ziel in verweise if ziel not in vorhanden)


# Claude Code kennt genau diese Kurznamen im Agentenkopf; eine volle Modell-Id wie
# "claude-opus-5" gehoert in den Bot, nicht hierher. Quelle: code.claude.com/docs/en/sub-agents
AGENTENMODELLE = {"opus", "sonnet", "haiku", "inherit"}


def agent_ohne_modell(koepfe):
    return sorted(name for name, k in koepfe.items() if not k.get("model"))


def agent_mit_unbekanntem_modell(koepfe, erlaubt):
    return sorted("%s=%s" % (n, k["model"]) for n, k in koepfe.items()
                  if k.get("model") and k["model"] not in erlaubt)


def agent_ohne_beschreibung(koepfe):
    return sorted(n for n, k in koepfe.items() if not k.get("description"))


def kopfname_weicht_ab(koepfe):
    return sorted("%s != %s" % (n, k.get("name")) for n, k in koepfe.items()
                  if k.get("name") != n)


def agent_ohne_skill(agenten, skills):
    return sorted(set(agenten) - set(skills))


def botmodell_nicht_erlaubt(zuordnung, allowlist):
    return sorted("%s=%s" % (i, m) for i, m in zuordnung.items() if m not in allowlist)


def ohne_gedaechtnis(register_ordner, vorhanden):
    """Eine Identitaet des Registers hat keine Gedaechtnisdatei. Was dort nicht steht, weiss
    sie nicht, egal wo sie laeuft (3-Loop Modell, Ort, Gedaechtnis, 2026-09-08)."""
    return sorted(name for name in register_ordner if name + ".md" not in vorhanden)


def ordner_im_register(text):
    kopf = text.index("## Register")
    return sorted(set(re.findall(r"^\| [^|]+ \| `([\w-]+)/` \|", text[kopf:], re.MULTILINE)))


def fehlt_im_register(register, identitaeten):
    return sorted(name for name in identitaeten
                  if not re.search(r"`%s/`" % re.escape(name), register))


# --- Tests ------------------------------------------------------------------

class GedaechtnisTest(unittest.TestCase):
    def verweise(self):
        paare = []
        for name in skillordner():
            text = (SKILLS / name / "SKILL.md").read_text()
            for ziel in re.findall(r"\.\./gedaechtnis/([\w-]+\.md)", text):
                paare.append((name, ziel))
        return paare

    def test_jeder_verweis_hat_seine_datei(self):
        vorhanden = {p.name for p in GEDAECHTNIS.glob("*.md")}
        self.assertEqual([], gedaechtnis_ohne_datei(self.verweise(), vorhanden))

    def test_es_gibt_ueberhaupt_verweise(self):
        # Sonst prueft der Test darueber eine leere Menge und ist immer gruen.
        self.assertGreaterEqual(len(self.verweise()), 4)

    def test_ein_fehlendes_gedaechtnis_faellt_auf(self):
        luecke = gedaechtnis_ohne_datei([("karl", "karl.md"), ("x", "fehlt.md")], {"karl.md"})
        self.assertEqual(["x -> fehlt.md"], luecke)

    def test_jede_registeridentitaet_hat_ein_gedaechtnis(self):
        register = ordner_im_register((SKILLS / "README.md").read_text())
        vorhanden = {p.name for p in GEDAECHTNIS.glob("*.md")}
        self.assertGreaterEqual(len(register), 5)
        self.assertEqual([], ohne_gedaechtnis(register, vorhanden))

    def test_eine_identitaet_ohne_gedaechtnis_faellt_auf(self):
        self.assertEqual(["marlene"], ohne_gedaechtnis(["karl", "marlene"], {"karl.md"}))

    def test_der_relative_pfad_loest_wirklich_auf(self):
        for skill, ziel in self.verweise():
            pfad = SKILLS / skill / ".." / "gedaechtnis" / ziel
            self.assertTrue(pfad.is_file(), "%s: %s loest nicht auf" % (skill, ziel))


class AgentenTest(unittest.TestCase):
    def koepfe(self):
        return {n: kopf((AGENTEN / (n + ".md")).read_text()) for n in agentendateien()}

    def test_jeder_agent_nennt_ein_modell(self):
        self.assertEqual([], agent_ohne_modell(self.koepfe()))

    def test_jedes_agentenmodell_ist_ein_bekannter_kurzname(self):
        self.assertEqual([], agent_mit_unbekanntem_modell(self.koepfe(), AGENTENMODELLE))

    def test_eine_volle_modell_id_faellt_auf(self):
        # Der haeufigste Fehlgriff: die Schreibweise des Bots in den Agentenkopf tragen.
        self.assertEqual(["karl=claude-opus-5"],
                         agent_mit_unbekanntem_modell({"karl": {"model": "claude-opus-5"}},
                                                      AGENTENMODELLE))

    def test_jeder_agent_hat_eine_beschreibung(self):
        self.assertEqual([], agent_ohne_beschreibung(self.koepfe()))

    def test_eine_fehlende_beschreibung_faellt_auf(self):
        self.assertEqual(["stumm"], agent_ohne_beschreibung({"stumm": {"model": "opus"}}))

    def test_der_name_im_kopf_ist_der_dateiname(self):
        # Aufgerufen wird der Kopfname; heisst die Datei anders, sucht man den Agenten
        # unter einem Namen, den es nicht gibt.
        self.assertEqual([], kopfname_weicht_ab(self.koepfe()))

    def test_ein_abweichender_kopfname_faellt_auf(self):
        self.assertEqual(["karl != Karl"], kopfname_weicht_ab({"karl": {"name": "Karl"}}))

    def test_ein_agent_ohne_modell_faellt_auf(self):
        self.assertEqual(["stumm"], agent_ohne_modell({"karl": {"model": "opus"}, "stumm": {}}))

    def test_jeder_agent_hat_seinen_skill(self):
        self.assertEqual([], agent_ohne_skill(agentendateien(), skillordner()))

    def test_ein_agent_ohne_skill_faellt_auf(self):
        self.assertEqual(["geist"], agent_ohne_skill(["karl", "geist"], ["karl"]))

    def test_jeder_agent_liest_seinen_skill_und_nennt_die_wurzel(self):
        for name in agentendateien():
            text = (AGENTEN / (name + ".md")).read_text()
            self.assertIn("skills/%s/SKILL.md" % name, text, name)
            self.assertIn("workorce claude", text, "%s nennt das Projektwurzelverzeichnis nicht" % name)

    def test_es_gibt_ueberhaupt_agenten(self):
        self.assertGreaterEqual(len(agentendateien()), 5)


class BotTest(unittest.TestCase):
    def lade(self, name):
        cfg = botkonfiguration(name)
        if cfg is None:
            self.skipTest("%s ist nicht versioniert und hier nicht vorhanden" % name)
        return cfg

    def test_eine_fehlende_konfiguration_ergibt_none_statt_eines_absturzes(self):
        # Gegenprobe zum Skip-Pfad: Auf einem frischen Klon geht der Waechter hier durch.
        self.assertIsNone(botkonfiguration("config.gibtesnicht.json"))
        self.assertIsNotNone(botkonfiguration("config.example.json"))

    def test_jedes_botmodell_steht_in_der_allowlist(self):
        zuordnung = botmodelle(self.lade("config.json"))
        self.assertEqual([], botmodell_nicht_erlaubt(zuordnung, erlaubte_modelle()))

    def test_ein_erfundenes_modell_faellt_auf(self):
        self.assertEqual(["KARL=claude-phantom-9"],
                         botmodell_nicht_erlaubt({"KARL": "claude-phantom-9"}, {"claude-opus-5"}))

    def test_die_allowlist_wurde_wirklich_gelesen(self):
        self.assertIn("claude-opus-5", erlaubte_modelle())

    def test_die_vorlage_ist_ladbar_und_nennt_ein_erlaubtes_modell(self):
        # Die Vorlage ist versioniert und wird kopiert; ein Modell, das die Allowlist
        # nicht kennt, faellt sonst erst beim ersten Start des Kopierten auf (Regel 56).
        vorlage = json.loads((WURZEL / "workforce" / "config.example.json").read_text())
        self.assertEqual([], botmodell_nicht_erlaubt(botmodelle(vorlage), erlaubte_modelle()))

    def test_jede_botidentitaet_hat_ihre_skilldatei(self):
        cfg = self.lade("config.json")
        for ident, eintrag in cfg["identities"].items():
            if "system_prompt_file" not in eintrag:
                continue
            pfad = (WURZEL / "workforce" / eintrag["system_prompt_file"]).resolve()
            self.assertTrue(pfad.is_file(), "%s: %s fehlt" % (ident, pfad))

    def test_mac_und_nas_haben_dieselben_modelle(self):
        # Die beiden Konfigurationen duerfen sich in Pfaden unterscheiden, nie im Modell:
        # deploy_nas.sh kopiert config.nas.json auf die NAS, config.json bleibt hier.
        self.assertEqual(botmodelle(self.lade("config.json")),
                         botmodelle(self.lade("config.nas.json")))


def fehlt_im_kommando(text, agenten):
    # Der Ueberblick nennt jeden Mitarbeiter fett; ein achter Agent, den niemand
    # eintraegt, fehlt sonst still in genau der Liste, die den Ueberblick geben soll.
    return sorted(n for n in agenten if ("**%s**" % n.capitalize()) not in text
                  and ("**%s**" % n.upper()) not in text)


class KommandoTest(unittest.TestCase):
    def kommando(self):
        return (WURZEL / ".claude" / "commands" / "mitarbeiter.md").read_text()

    def test_jeder_agent_steht_im_ueberblick(self):
        self.assertEqual([], fehlt_im_kommando(self.kommando(), agentendateien()))

    def test_ein_fehlender_mitarbeiter_faellt_auf(self):
        self.assertEqual(["neu"], fehlt_im_kommando("| **Karl** |", ["karl", "neu"]))

    def test_das_kommando_liest_die_modelle_statt_sie_zu_nennen(self):
        # Eine abgeschriebene Modellspalte waere beim naechsten Umstufen falsch.
        text = self.kommando()
        self.assertIn("grep", text)
        for veraltbar in ("| opus |", "| sonnet |", "| haiku |"):
            self.assertNotIn(veraltbar, text)


class RegisterTest(unittest.TestCase):
    def test_jede_identitaet_steht_im_register(self):
        register = (SKILLS / "README.md").read_text()
        self.assertEqual([], fehlt_im_register(register, skillordner()))

    def test_eine_fehlende_zeile_faellt_auf(self):
        self.assertEqual(["neu"], fehlt_im_register("| Karl | `karl/` |", ["karl", "neu"]))


if __name__ == "__main__":
    unittest.main()
