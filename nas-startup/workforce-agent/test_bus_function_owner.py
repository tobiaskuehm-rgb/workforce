"""Migration 009 darf nur die zwoelf Busfunktionen anfassen - und genau die.

Review finding G-071. Der erste Entwurf sprach im Kommentar von den zwoelf
SECURITY-DEFINER-Busfunktionen und waehlte im Code dynamisch **jede**
SECURITY-DEFINER-Funktion im Schema `workforce`. Heute waere das dasselbe;
nach einer Anwendung der gegateten `004` waeren es neunzehn, und die sieben
Knowledge-Funktionen waeren als Nebenwirkung in den Bus-Eigentuemerkontext
gewandert. Dazu kam ein `GRANT SELECT, INSERT, UPDATE ON ALL TABLES` in zwei
Schemata, das denselben Weg genommen haette.

Das ist Leitplanke 7 in ihrer teuersten Form: Die Anforderung stand richtig im
Kommentar, gebaut war etwas anderes, und der Kommentar blieb als Zusicherung
stehen.

Die Migration pinnt jetzt Namen und Stelligkeit und bricht ab, wenn der
Katalog etwas anderes enthaelt. Diese Datei ist die zweite Haelfte davon: Sie
leitet dieselben Mengen erneut aus `002` und `005` ab und haelt sie gegen die
Listen in `009` und im Abnahmetest. Aendert eine Migration die Busfunktionen
oder ihre Tabellenzugriffe, wird diese Datei rot - dieselbe Aufgabe, die
`bus_rules.py` fuer die Uebergangsregeln erfuellt.

Warum Name und Stelligkeit und nicht der Typ: Der Katalog schreibt Typen
anders als die Quelle (`timestamptz` wird `timestamp with time zone`). Eine
abgeschriebene Typliste waere genau die Gedaechtnisleistung, die `G-044`
verboten hat.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
MIGRATIONS = NAS / "postgres-init"
MIGRATION = MIGRATIONS / "009_bus_function_owner.sql"
ACCEPTANCE = NAS / "postgres-tests" / "009_bus_function_owner_acceptance.sql"

# Die Migrationen, die das Fenster wirklich anwendet. 004 und 008 sind gegatet;
# ihre Objekte existieren in der Quelle und fehlen in der Datenbank.
ANGEWENDET = ("001_employee_registry.sql", "002_workforce_bus.sql",
              "003_workforce_bus_trigger_fix.sql", "005_bus_denial_audit.sql",
              "006_legacy_registry_tables.sql", "007_least_privilege_roles.sql")

FUNKTION = re.compile(
    r"CREATE (?:OR REPLACE )?FUNCTION\s+workforce\.(\w+)\s*\((.*?)\)\s*"
    r"RETURNS(.*?)AS \$\$(.*?)\$\$;", re.DOTALL | re.IGNORECASE)
TRIGGER = re.compile(
    r"CREATE TRIGGER\s+\w+\s+[^;]*?\sON\s+workforce\.(\w+)[^;]*?"
    r"EXECUTE FUNCTION\s+workforce\.(\w+)\s*\(", re.DOTALL | re.IGNORECASE)


def split_top_level(argument_list: str) -> list[str]:
    """Argumente trennen, ohne an einem Komma in Klammern zu zerbrechen."""
    teile: list[str] = []
    tiefe = 0
    aktuell = ""
    for zeichen in argument_list:
        if zeichen == "(":
            tiefe += 1
        elif zeichen == ")":
            tiefe -= 1
        if zeichen == "," and tiefe == 0:
            teile.append(aktuell.strip())
            aktuell = ""
        else:
            aktuell += zeichen
    if aktuell.strip():
        teile.append(aktuell.strip())
    return teile


def quelltext(dateien: tuple[str, ...] = ANGEWENDET) -> str:
    return "\n".join((MIGRATIONS / name).read_text(encoding="utf-8")
                     for name in dateien if (MIGRATIONS / name).is_file())


def funktionen(text: str) -> list[tuple[str, int, bool, str]]:
    """(Name, Stelligkeit, ist SECURITY DEFINER, Rumpf) je Funktion."""
    gefunden = []
    for treffer in FUNKTION.finditer(text):
        name, args, kopf, rumpf = treffer.groups()
        args = " ".join(args.split())
        gefunden.append((name, len(split_top_level(args)) if args else 0,
                         "SECURITY DEFINER" in kopf.upper(), rumpf))
    return gefunden


def security_definer(text: str) -> set[str]:
    """`name:stelligkeit` je SECURITY-DEFINER-Funktion, wie 009 sie pinnt."""
    return {f"{name}:{arity}" for name, arity, secdef, _ in funktionen(text) if secdef}


def tabellenzugriffe(rumpf: str) -> dict[str, set[str]]:
    zugriff: dict[str, set[str]] = {}
    for muster, recht in ((r"\bFROM\s+workforce\.(\w+)", "SELECT"),
                          (r"\bJOIN\s+workforce\.(\w+)", "SELECT"),
                          (r"\bINSERT\s+INTO\s+workforce\.(\w+)", "INSERT"),
                          (r"\bUPDATE\s+workforce\.(\w+)", "UPDATE"),
                          (r"\bDELETE\s+FROM\s+workforce\.(\w+)", "DELETE")):
        for tabelle in re.findall(muster, rumpf, re.IGNORECASE):
            zugriff.setdefault(tabelle, set()).add(recht)
    return zugriff


def benoetigte_rechte(text: str) -> dict[str, set[str]]:
    """Was `workforce_owner` mindestens braucht, aus den Quellen abgeleitet.

    Zwei Ebenen, und die zweite ist die, die man vergisst: Die Trigger auf den
    Tabellen, in die die zwoelf schreiben, sind **nicht** SECURITY DEFINER.
    Sie laufen im Aufruf als `workforce_owner`, und `bus_record_change` fuegt
    dabei in `bus_events` ein. Ohne dieses INSERT stuende die Auditspur still -
    der teuerste Ausgang einer zu engen Allowlist.
    """
    alle = funktionen(text)
    rumpf_von = {name: rumpf for name, _, _, rumpf in alle}

    noetig: dict[str, set[str]] = {}
    geschrieben: set[str] = set()
    for name, _, secdef, rumpf in alle:
        if not secdef:
            continue
        for tabelle, rechte in tabellenzugriffe(rumpf).items():
            noetig.setdefault(tabelle, set()).update(rechte)
            if rechte & {"INSERT", "UPDATE", "DELETE"}:
                geschrieben.add(tabelle)

    for tabelle, funktion in TRIGGER.findall(text):
        if tabelle not in geschrieben or funktion not in rumpf_von:
            continue
        for ziel, rechte in tabellenzugriffe(rumpf_von[funktion]).items():
            noetig.setdefault(ziel, set()).update(rechte)
    return noetig


def gepinnte_funktionen(datei: pathlib.Path) -> set[str]:
    """Die `name:stelligkeit`-Eintraege, die eine SQL-Datei auffuehrt."""
    return set(re.findall(r"'([a-z_]+:\d+)'", datei.read_text(encoding="utf-8")))


def erteilte_rechte(datei: pathlib.Path) -> dict[str, set[str]]:
    """Die GRANT-Bloecke der Migration, nach Tabelle aufgeloest."""
    text = datei.read_text(encoding="utf-8")
    # Kommentarzeilen raus, sonst zaehlt ein Beispiel in der Prosa mit.
    text = "\n".join(z for z in text.splitlines() if not z.lstrip().startswith("--"))
    erteilt: dict[str, set[str]] = {}
    for rechte, ziele in re.findall(
            r"GRANT\s+([A-Z, ]+?)\s+ON\s+((?:\s*workforce\.\w+,?)+)\s*TO\s+workforce_owner",
            text, re.IGNORECASE):
        gesetzt = {r.strip().upper() for r in rechte.split(",") if r.strip()}
        for tabelle in re.findall(r"workforce\.(\w+)", ziele):
            erteilt.setdefault(tabelle, set()).update(gesetzt)
    return erteilt


def erwartete_rechte_im_abnahmetest() -> dict[str, set[str]]:
    """Die `tabelle=RECHTE`-Liste, gegen die der Abnahmetest den Katalog haelt."""
    erwartet: dict[str, set[str]] = {}
    for zeile in re.findall(r"'(\w+=[A-Z,]+)'",
                            ACCEPTANCE.read_text(encoding="utf-8")):
        tabelle, rechte = zeile.split("=", 1)
        erwartet[tabelle] = set(rechte.split(","))
    return erwartet


class PinnedFunctionsTest(unittest.TestCase):
    def test_the_migration_pins_exactly_the_security_definer_functions(self) -> None:
        self.assertEqual(security_definer(quelltext()), gepinnte_funktionen(MIGRATION))

    def test_the_acceptance_test_pins_the_same_set(self) -> None:
        self.assertEqual(gepinnte_funktionen(MIGRATION), gepinnte_funktionen(ACCEPTANCE))

    def test_there_are_twelve_of_them(self) -> None:
        # Die Zahl steht im Kopf beider Dateien und im Nachweis. Sie hier zu
        # binden ist zulaessig, weil sie das ist, was diese Migration selbst
        # erzeugt, und nicht eine gewachsene Population (`G-049`).
        self.assertEqual(12, len(gepinnte_funktionen(MIGRATION)))

    def test_no_knowledge_function_is_pinned(self) -> None:
        """Die Grenze, um die es in `G-071` geht.

        `004` bringt sieben eigene SECURITY-DEFINER-Funktionen mit. Keine
        davon darf in 009 stehen - und die Gegenprobe darunter belegt, dass es
        sie ueberhaupt gibt, sonst prueft der Test eine leere Menge.
        """
        knowledge = security_definer(
            (MIGRATIONS / "004_knowledge_capability.sql").read_text(encoding="utf-8"))
        self.assertEqual(7, len(knowledge))
        self.assertEqual(set(), knowledge & gepinnte_funktionen(MIGRATION))

    def test_an_added_security_definer_function_would_be_caught(self) -> None:
        erfunden = security_definer(quelltext()) | {"bus_erfunden:3"}
        self.assertNotEqual(erfunden, gepinnte_funktionen(MIGRATION))

    def test_a_changed_arity_would_be_caught(self) -> None:
        # Genau der Fall aus `G-044`: derselbe Name, andere Stelligkeit.
        self.assertIn("bus_send_message:13", gepinnte_funktionen(MIGRATION))
        self.assertNotIn("bus_send_message:5", gepinnte_funktionen(MIGRATION))


class GrantAllowlistTest(unittest.TestCase):
    def test_the_migration_grants_exactly_what_the_functions_need(self) -> None:
        self.assertEqual(benoetigte_rechte(quelltext()), erteilte_rechte(MIGRATION))

    def test_the_audit_insert_is_part_of_it(self) -> None:
        """Ohne `bus_events` waere die Allowlist zu eng statt zu breit.

        Der Zugriff steht in keinem der zwoelf Rumpfe - er kommt aus dem
        Trigger `bus_record_change`, der als Aufrufer laeuft. Genau diese
        Ebene uebersieht man, wenn man eine Allowlist aus den Funktionen
        allein ableitet.
        """
        self.assertEqual({"INSERT"}, erteilte_rechte(MIGRATION).get("bus_events"))

    def test_nothing_may_be_deleted(self) -> None:
        for tabelle, rechte in erteilte_rechte(MIGRATION).items():
            with self.subTest(tabelle=tabelle):
                self.assertNotIn("DELETE", rechte)

    def test_no_blanket_grant_survives(self) -> None:
        text = MIGRATION.read_text(encoding="utf-8")
        aktiv = "\n".join(z for z in text.splitlines() if not z.lstrip().startswith("--"))
        self.assertNotIn("GRANT SELECT, INSERT, UPDATE ON ALL TABLES", aktiv)
        self.assertNotIn("IN SCHEMA public TO workforce_owner", aktiv)
        # Die Gegenprobe: Ein REVOKE auf ALL TABLES ist erlaubt und muss da
        # sein, sonst haengt der Endzustand an der Vorgeschichte der Rolle.
        self.assertIn("REVOKE ALL ON ALL TABLES IN SCHEMA workforce", aktiv)

    def test_no_knowledge_table_is_granted(self) -> None:
        self.assertEqual([], sorted(t for t in erteilte_rechte(MIGRATION)
                                    if t.startswith("knowledge_")))

    def test_the_acceptance_test_expects_the_same_allowlist(self) -> None:
        """Sonst haetten Migration und Abnahmetest zwei Wahrheiten.

        Der Abnahmetest vergleicht den Katalog gegen seine eigene Liste. Waere
        die breiter als die Migration, bestuende er ueber einem zu weit
        geoeffneten Zustand - und das ist genau der Fall, den `G-071` an der
        ersten Fassung gefunden hat.
        """
        self.assertEqual(benoetigte_rechte(quelltext()),
                         erwartete_rechte_im_abnahmetest())

    def test_a_missing_grant_would_be_caught(self) -> None:
        gekuerzt = dict(erteilte_rechte(MIGRATION))
        gekuerzt.pop("bus_events")
        self.assertNotEqual(benoetigte_rechte(quelltext()), gekuerzt)

    def test_a_broader_grant_would_be_caught(self) -> None:
        erweitert = {t: set(r) for t, r in erteilte_rechte(MIGRATION).items()}
        erweitert["bus_credentials"].add("UPDATE")
        self.assertNotEqual(benoetigte_rechte(quelltext()), erweitert)


class DerivationIsNotEmptyTest(unittest.TestCase):
    """Jede Aussage oben vergleicht zwei abgeleitete Mengen.

    Waeren die Regexe kaputt, waeren beide leer und alles bestuende - genau
    der Fehler, den `compose_scan.py` als Regel hinterlassen hat: ein
    Waechter, der nicht hinsieht, meldet PASS.
    """

    def test_the_source_scan_finds_functions(self) -> None:
        alle = funktionen(quelltext())
        self.assertGreater(len(alle), 20)
        self.assertEqual(12, sum(1 for _, _, secdef, _ in alle if secdef))

    def test_the_trigger_scan_finds_triggers(self) -> None:
        self.assertGreater(len(TRIGGER.findall(quelltext())), 30)

    def test_the_grant_scan_finds_grants(self) -> None:
        self.assertGreater(len(erteilte_rechte(MIGRATION)), 10)


if __name__ == "__main__":
    unittest.main()
