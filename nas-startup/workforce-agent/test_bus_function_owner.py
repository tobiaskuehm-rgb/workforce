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


def funktionen(text: str) -> list[tuple[str, list[str], bool, str]]:
    """(Name, Parametertypen, ist SECURITY DEFINER, Rumpf) je Funktion."""
    gefunden = []
    for treffer in FUNKTION.finditer(text):
        name, args, kopf, rumpf = treffer.groups()
        args = " ".join(args.split())
        typen = []
        for parameter in (split_top_level(args) if args else []):
            # Ein DEFAULT gehoert nicht zur Identitaet einer Funktion, der
            # Parametername auch nicht - beides faellt weg.
            ohne_default = re.sub(r"\s+DEFAULT\s+.*$", "", parameter, flags=re.IGNORECASE)
            typen.append(ohne_default.split(" ", 1)[1].strip())
        gefunden.append((name, typen, "SECURITY DEFINER" in kopf.upper(), rumpf))
    return gefunden


def signatur(name: str, typen: list[str]) -> str:
    """Die Schreibweise, in der 009 pinnt: schemaqualifiziert, Typen der Quelle.

    Nicht die kanonische Katalogschreibweise - `to_regprocedure()` normalisiert
    `timestamptz` selbst zu `timestamp with time zone`. Einen Typnamen von Hand
    umzuschreiben waere genau die Gedaechtnisleistung, die `G-044` verboten hat.
    """
    return f"workforce.{name}({', '.join(typen)})"


def security_definer(text: str) -> set[str]:
    """Vollstaendige Identitaetssignatur je SECURITY-DEFINER-Funktion.

    Bis `G-075` stand hier `name:stelligkeit`. Das unterscheidet keine zwei
    Funktionen gleichen Namens und gleicher Argumentzahl mit anderen
    Parametertypen - und genau die waere die gefaehrliche.
    """
    return {signatur(name, typen) for name, typen, secdef, _ in funktionen(text) if secdef}


def stelligkeitssicht(signaturen: set[str]) -> set[str]:
    """Die alte, zu schwache Sicht - nur noch fuer die Gegenprobe da."""
    sicht = set()
    for eintrag in signaturen:
        name, _, rest = eintrag.partition("(")
        argumente = rest.rstrip(")")
        sicht.add(f"{name}:{len(argumente.split(',')) if argumente else 0}")
    return sicht


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
    """Die vollstaendigen Signaturen, die eine SQL-Datei auffuehrt."""
    return {" ".join(eintrag.split())
            for eintrag in re.findall(r"'(workforce\.\w+\([^']*\))'",
                                      datei.read_text(encoding="utf-8"))}


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
    # Schemaqualifiziert seit `G-074`: Zwei gleichnamige Tabellen in zwei
    # Schemata duerfen im Mengenvergleich nicht zusammenfallen.
    for zeile in re.findall(r"'workforce\.(\w+=[A-Z,]+)'",
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
        gepinnt = gepinnte_funktionen(MIGRATION)
        self.assertIn("workforce.bus_send_message(" + ", ".join(["text"] * 13) + ")", gepinnt)
        self.assertNotIn("workforce.bus_send_message(" + ", ".join(["text"] * 5) + ")", gepinnt)

    def test_a_changed_parameter_type_at_the_same_arity_would_be_caught(self) -> None:
        """Der reproduzierbare Gegenfall aus `G-075`.

        Ein Parametertyp wird geaendert, die Argumentzahl bleibt. Unter der
        alten Sicht `name:stelligkeit` blieb `bus_send_message:13` woertlich
        gleich und der Pin-Test gruen - eine gleichnamige Funktion mit anderen
        Typen waere als die freigegebene durchgegangen. Beide Haelften stehen
        hier: dass die neue Sicht anschlaegt **und** dass die alte es nicht
        getan haette.
        """
        echt = (MIGRATIONS / "002_workforce_bus.sql").read_text(encoding="utf-8")
        original = "CREATE FUNCTION workforce.bus_send_message(\n    p_token_hash text,"
        self.assertIn(original, echt, "Ankerzeile hat sich geaendert")
        veraendert = echt.replace(original,
                                  original.replace("p_token_hash text,", "p_token_hash varchar,"), 1)

        vorher = security_definer(echt)
        nachher = security_definer(veraendert)
        self.assertNotEqual(vorher, nachher, "der Typwechsel faellt nicht auf")
        self.assertIn("workforce.bus_send_message(varchar, " + ", ".join(["text"] * 12) + ")",
                      nachher)
        # Und die Gegenprobe, die den Befund belegt: unter der alten Sicht
        # waeren beide Mengen identisch gewesen.
        self.assertEqual(stelligkeitssicht(vorher), stelligkeitssicht(nachher))

    def test_the_migration_resolves_through_the_catalog(self) -> None:
        """Aufgeloest wird ueber `to_regprocedure()`, gehandelt ueber die OID.

        Ein Namensvergleich haette dieselbe Schwaeche wie der alte Pin: Er
        trifft jede Ueberladung. `to_regprocedure` liefert NULL statt eines
        Fehlers, also ist eine veraenderte Signatur ein benannter Abbruch.
        """
        for datei in (MIGRATION, ACCEPTANCE):
            with self.subTest(datei=datei.name):
                aktiv = "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                                   if not z.lstrip().startswith("--"))
                self.assertIn("to_regprocedure(", aktiv)
                self.assertIn("SIGNATURE_NOT_FOUND", aktiv)
                # Kein Rueckfall auf den blossen Namen mehr.
                self.assertNotIn("p.proname = v_name", aktiv)
                self.assertNotIn("proname || ':' || p.pronargs", aktiv)

    def test_the_internal_helpers_are_part_of_the_twelve(self) -> None:
        # Die zehn aufrufbaren werden im Abnahmetest aus zwoelf minus zwei
        # abgeleitet. Waeren die beiden keine Teilmenge, waere die Zehn falsch.
        intern = {"workforce.bus_authenticate(text, text)",
                  "workforce.bus_identify_for_audit(text, text)"}
        gepinnt = gepinnte_funktionen(MIGRATION)
        self.assertTrue(intern <= gepinnt)
        self.assertEqual(10, len(gepinnt - intern))


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

    def test_the_schema_itself_is_reset_before_it_is_granted(self) -> None:
        """Ein `CREATE` auf `workforce` waere der Weg zurueck.

        Eine Rolle, die diese Migration bereits vorfindet, koennte `CREATE` auf
        dem Schema mitbringen. Damit legt sie eigene Relationen an, ist deren
        Eigentuemerin und kann auf ihnen Trigger abschalten - genau der Weg,
        den 009 zumachen soll. Der Eigentuemer ohne Tabelleneigentum waere
        sonst nur eine Momentaufnahme.
        """
        text = MIGRATION.read_text(encoding="utf-8")
        aktiv = "\n".join(z for z in text.splitlines() if not z.lstrip().startswith("--"))
        self.assertIn("REVOKE ALL ON SCHEMA workforce FROM workforce_owner;", aktiv)
        # Und die Reihenfolge: erst zuruecknehmen, dann erteilen.
        self.assertLess(aktiv.index("REVOKE ALL ON SCHEMA workforce"),
                        aktiv.index("GRANT USAGE ON SCHEMA workforce"))

    def test_the_acceptance_test_demands_exactly_usage_on_the_schema(self) -> None:
        # "USAGE ist vorhanden" haette ein zusaetzliches CREATE nicht bemerkt.
        aktiv = "\n".join(z for z in ACCEPTANCE.read_text(encoding="utf-8").splitlines()
                          if not z.lstrip().startswith("--"))
        self.assertIn("v_schema_rechte <> 'USAGE'", aktiv)
        self.assertIn("ACCEPTANCE_009_WORKFORCE_SCHEMA_PRIVILEGES", aktiv)

    def test_the_public_self_check_can_actually_fire(self) -> None:
        """Die Selbstpruefung war logisch leer.

        Sie verlangte `a.grantee = 0` und jointe gleichzeitig auf `pg_roles`,
        wo es zur OID 0 keine Zeile gibt: Der Join entfernte jede Zeile,
        `EXISTS` war immer falsch, der Waechter konnte nie anschlagen. Die
        beiden Tatsachen brauchen zwei getrennte Abfragen - eine ohne den Join
        (die Vorgabe existiert) und eine mit ihm (sie wird ausgeblendet).
        """
        aktiv = "\n".join(z for z in ACCEPTANCE.read_text(encoding="utf-8").splitlines()
                          if not z.lstrip().startswith("--"))
        selbst = aktiv[aktiv.index("ACCEPTANCE_009_SELF_CHECK_FAILED"):]
        widerspruch = "JOIN pg_roles r ON r.oid = a.grantee"

        # Der Block, der die Vorgabe belegt, darf den Join nicht enthalten.
        # Abgegrenzt wird an seinem eigenen `IF NOT EXISTS (` - ein fester
        # Zeichenabstand haette die vorige Pruefung mit erfasst, die den Join
        # zu Recht fuehrt.
        bis = aktiv.index("keine PUBLIC-Vorgabe auf public")
        vorgabe = aktiv[aktiv.rindex("IF NOT EXISTS (", 0, bis):bis]
        self.assertIn("a.grantee = 0", vorgabe)
        self.assertIn("privilege_type = 'USAGE'", vorgabe)
        self.assertNotIn(widerspruch, vorgabe)

        # Der Block, der das Ausblenden belegt, muss ihn enthalten.
        self.assertIn(widerspruch, selbst)
        self.assertIn("PUBLIC nicht ausgeblendet", selbst)

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

    def test_the_expectation_is_schema_qualified(self) -> None:
        """`G-074`: Zwei Schemata, ein Tabellenname - das darf nicht kollabieren.

        Die erste Fassung gruppierte nach `table_name` allein. Ein Grant auf
        `public.bus_messages` waere unter demselben Schluessel gelandet wie
        der auf `workforce.bus_messages` und im Mengenvergleich verschwunden.
        """
        text = ACCEPTANCE.read_text(encoding="utf-8")
        qualifiziert = re.findall(r"'(\w+)\.(\w+=[A-Z,]+)'", text)
        self.assertEqual(13, len(qualifiziert))
        self.assertEqual({"workforce"}, {schema for schema, _ in qualifiziert})
        # Gegenprobe: kein unqualifizierter Eintrag ist uebriggeblieben.
        self.assertEqual([], re.findall(r"'(?<![\w.])(\w+=[A-Z,]+)'", text))

    def test_the_public_schema_is_not_checked_by_effective_privilege(self) -> None:
        """`G-074`: `has_schema_privilege` beantwortet die falsche Frage.

        Es liefert das **effektive** Recht, und `USAGE` auf `public` hat jede
        Rolle ueber die Pseudorolle `PUBLIC`. Der Abnahmetest waere damit auf
        jeder frischen PostgreSQL-17-Instanz falsch rot geworden. Geprueft
        wird jetzt der direkte ACL-Eintrag im Katalog.
        """
        text = ACCEPTANCE.read_text(encoding="utf-8")
        aktiv = "\n".join(z for z in text.splitlines() if not z.lstrip().startswith("--"))
        self.assertNotIn("has_schema_privilege", aktiv)
        self.assertIn("aclexplode(n.nspacl)", aktiv)
        # Gegenprobe: der Kommentar darf das Wort nennen, ohne den Test rot zu
        # machen - ein Sprachvergleich waere sonst wieder der Waechter (G-054).
        self.assertIn("has_schema_privilege", text)

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
