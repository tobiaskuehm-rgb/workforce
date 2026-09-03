"""Migration 010 ist der benannte Rueckbau zu 009 - und dieser Test haelt beide zusammen.

Vertretungsreview 2026-09-03, `SV-2026-09-03-04`: Der Kopf von `009` versprach
einen Rueckbau, den es nicht gab. Die Korrektur ist nicht, den Satz zu
streichen, sondern die Datei zu schreiben - und den Verweis darauf so
abzulegen, dass er nicht wieder unbemerkt falsch werden kann.

Deshalb steht er **maschinenlesbar** in beiden Dateien:

    009: -- RUECKBAU: 010_bus_function_owner_rollback.sql
    010: -- ROLLBACK-FUER: 009_bus_function_owner.sql

Ein Sprachvergleich taugt hier nicht (`G-054`): Der alte Absatz sagte
"Rueckbau ... gibt es nicht", der neue sagt "Rueckbau ist eine Datei" - beide
enthalten dasselbe Wort und meinen das Gegenteil. Die Prosa darf formulieren,
die Zusicherung steht daneben und wird aufgeloest.

Der Rest dieses Tests prueft, dass `010` wirklich zuruecknimmt, was `009`
gibt - abgeleitet aus `009`, nicht abgeschrieben.
"""

from __future__ import annotations

import pathlib
import re
import unittest

from test_bus_function_owner import (
    erteilte_rechte,
    gepinnte_funktionen,
    quelltext,
    security_definer,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
MIGRATIONS = NAS / "postgres-init"
NEUN = MIGRATIONS / "009_bus_function_owner.sql"
ZEHN = MIGRATIONS / "010_bus_function_owner_rollback.sql"
ABNAHME = NAS / "postgres-tests" / "010_bus_function_owner_rollback_acceptance.sql"
COMPOSE = NAS / "compose.yaml"

GATE = "APPLY_MIGRATION_010_FUNCTION_OWNER_ROLLBACK"


def marken(text: str, schluessel: str) -> list[str]:
    """Die Werte eines maschinenlesbaren Kopfeintrags `-- SCHLUESSEL: wert`."""
    return re.findall(rf"^--\s*{schluessel}:\s*(\S+)\s*$", text, re.MULTILINE)


def ohne_kommentarzeilen(datei: pathlib.Path) -> str:
    """Nur die Zeilen, die die Datenbank wirklich ausfuehrt.

    Beide Koepfe sprechen ueber `DROP ROLE` und `DROP OWNED BY` - ein Scanner
    ohne diesen Schnitt wuerde die Erklaerung fuer die Sache halten.
    """
    return "\n".join(z for z in datei.read_text(encoding="utf-8").splitlines()
                     if not z.lstrip().startswith("--"))


def beruehrte_schemata(datei: pathlib.Path) -> set[str]:
    """Jedes Schema, auf dem eine Datei `workforce_owner` etwas gibt oder nimmt."""
    text = ohne_kommentarzeilen(datei)
    schemata = set(re.findall(
        r"(?:GRANT|REVOKE)[^;]*?\bON\s+SCHEMA\s+(\w+)[^;]*?workforce_owner", text,
        re.IGNORECASE | re.DOTALL))
    # Und die Schemata, in denen Relationen benannt werden.
    for block in re.findall(r"GRANT[^;]*?TO\s+workforce_owner", text,
                            re.IGNORECASE | re.DOTALL):
        schemata.update(re.findall(r"\b(\w+)\.\w+", block))
    return schemata


def pauschale_ruecknahmen(datei: pathlib.Path) -> set[tuple[str, str]]:
    """`(art, schema)` je `REVOKE ALL ON ALL <art> IN SCHEMA <schema>`."""
    text = ohne_kommentarzeilen(datei)
    return {(art.upper(), schema) for art, schema in re.findall(
        r"REVOKE\s+ALL\s+ON\s+ALL\s+(\w+)\s+IN\s+SCHEMA\s+(\w+)\s+FROM\s+workforce_owner",
        text, re.IGNORECASE)}


def schema_ruecknahmen(datei: pathlib.Path) -> set[str]:
    text = ohne_kommentarzeilen(datei)
    return set(re.findall(
        r"REVOKE\s+ALL\s+ON\s+SCHEMA\s+(\w+)\s+FROM\s+workforce_owner",
        text, re.IGNORECASE))


def relationsschemata(datei: pathlib.Path) -> set[str]:
    """Die Schemata, in denen eine Datei `workforce_owner` Relationsrechte gibt."""
    text = ohne_kommentarzeilen(datei)
    schemata: set[str] = set()
    for block in re.findall(r"GRANT[^;]*?TO\s+workforce_owner", text,
                            re.IGNORECASE | re.DOTALL):
        if re.search(r"\bON\s+SCHEMA\b", block, re.IGNORECASE):
            continue
        schemata.update(re.findall(r"\b(\w+)\.\w+", block))
    return schemata


def fehlende_ruecknahmen(beruehrt: set[str], zurueck: set[str]) -> list[str]:
    """Rein, damit die Gegenprobe sie mit erfundenen Mengen aufrufen kann.

    Ein Vergleich, der nur mit den echten Daten laeuft, belegt nicht, dass er
    ueberhaupt anschlagen kann - dieselbe Frage wie bei jedem Waechter
    (Regel 47).
    """
    return sorted(beruehrt - zurueck)


def fehlende_pauschalen(schemata: set[str], pauschal: set[tuple[str, str]]) -> list[str]:
    """Dasselbe fuer die pauschalen Ruecknahmen je Objektart."""
    return sorted(
        f"{art} IN {schema}"
        for schema in schemata
        for art in ("TABLES", "SEQUENCES", "FUNCTIONS")
        if (art, schema) not in pauschal
    )


class CrossReferenceTest(unittest.TestCase):
    def test_009_names_its_rollback_and_the_file_is_there(self) -> None:
        namen = marken(NEUN.read_text(encoding="utf-8"), "RUECKBAU")
        self.assertEqual(1, len(namen), f"genau ein RUECKBAU-Eintrag erwartet: {namen}")
        self.assertTrue((MIGRATIONS / namen[0]).is_file(), namen[0])

    def test_010_names_what_it_rolls_back_and_the_file_is_there(self) -> None:
        namen = marken(ZEHN.read_text(encoding="utf-8"), "ROLLBACK-FUER")
        self.assertEqual(1, len(namen), f"genau ein ROLLBACK-FUER-Eintrag erwartet: {namen}")
        self.assertTrue((MIGRATIONS / namen[0]).is_file(), namen[0])

    def test_the_pair_points_at_each_other(self) -> None:
        vorwaerts = marken(NEUN.read_text(encoding="utf-8"), "RUECKBAU")[0]
        rueckwaerts = marken(ZEHN.read_text(encoding="utf-8"), "ROLLBACK-FUER")[0]
        self.assertEqual(ZEHN.name, vorwaerts)
        self.assertEqual(NEUN.name, rueckwaerts)

    def test_a_dangling_reference_would_be_caught(self) -> None:
        # Die Gegenprobe zum eigentlichen Zweck: Ein Verweis auf eine Datei,
        # die es nicht gibt, muss auffallen - genau das war `SV-2026-09-03-04`.
        erfunden = marken("-- RUECKBAU: 010_gibt_es_nicht.sql\n", "RUECKBAU")
        self.assertEqual(["010_gibt_es_nicht.sql"], erfunden)
        self.assertFalse((MIGRATIONS / erfunden[0]).is_file())

    def test_the_marker_reader_ignores_prose(self) -> None:
        # Ein Satz ueber den Rueckbau ist kein Eintrag.
        self.assertEqual([], marken("-- Der RUECKBAU: steht woanders und heisst x.sql\n",
                                    "RUECKBAU"))


class PinnedFunctionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.erwartet = security_definer(quelltext())

    def test_the_rollback_pins_exactly_the_same_functions_as_the_migration(self) -> None:
        self.assertEqual(self.erwartet, gepinnte_funktionen(ZEHN))

    def test_the_acceptance_test_pins_the_same(self) -> None:
        self.assertEqual(self.erwartet, gepinnte_funktionen(ABNAHME))

    def test_the_derivation_is_not_empty(self) -> None:
        # Ohne das waeren die beiden Vergleiche oben zwei leere Mengen.
        self.assertEqual(12, len(self.erwartet), sorted(self.erwartet))

    def test_a_changed_signature_would_be_caught(self) -> None:
        verfaelscht = {s.replace("(text, text)", "(text, integer)") for s in self.erwartet}
        self.assertNotEqual(verfaelscht, gepinnte_funktionen(ZEHN))


class OwnerIsReadNotNamedTest(unittest.TestCase):
    """Der Zieleigentuemer kommt aus dem Katalog, nicht aus dem Gedaechtnis (`G-042`)."""

    def setUp(self) -> None:
        self.aktiv = ohne_kommentarzeilen(ZEHN)

    def test_no_role_name_is_written_into_the_owner_change(self) -> None:
        treffer = re.findall(r"OWNER\s+TO\s+(\w+)", self.aktiv, re.IGNORECASE)
        self.assertEqual([], treffer,
                         f"abgeschriebener Zieleigentuemer: {treffer}")

    def test_the_target_comes_from_the_schema_owner(self) -> None:
        self.assertIn("nspowner", self.aktiv)
        self.assertRegex(self.aktiv, r"OWNER\s+TO\s+%I")

    def test_a_literal_owner_would_be_caught(self) -> None:
        beispiel = "ALTER FUNCTION workforce.f() OWNER TO workforce_app;"
        self.assertEqual(["workforce_app"],
                         re.findall(r"OWNER\s+TO\s+(\w+)", beispiel, re.IGNORECASE))

    def test_two_independent_anchors_have_to_agree(self) -> None:
        # Schemaeigentuemer und Tabelleneigentuemer. Stimmen sie nicht ueberein,
        # ist der Zustand halb migriert - und Raten die schlechteste Antwort.
        self.assertIn("MIGRATION_010_OWNER_ANCHORS_DISAGREE", self.aktiv)
        self.assertIn("bus_messages", self.aktiv)


class NothingIsDroppedTest(unittest.TestCase):
    """Leitplanke 1 und 2: der Rueckbau loescht nichts."""

    VERBOTEN = (r"DROP\s+ROLE", r"DROP\s+OWNED", r"DROP\s+TABLE", r"DROP\s+COLUMN",
                r"TRUNCATE", r"DELETE\s+FROM")

    def test_the_executed_lines_contain_no_destructive_verb(self) -> None:
        aktiv = ohne_kommentarzeilen(ZEHN)
        for muster in self.VERBOTEN:
            with self.subTest(muster=muster):
                self.assertIsNone(re.search(muster, aktiv, re.IGNORECASE))

    def test_the_head_explains_why_the_role_stays(self) -> None:
        # Die Entscheidung selbst ist keine Regex-Frage, aber sie muss
        # dastehen: eine Rolle, die uebrig bleibt, ohne dass jemand es wollte,
        # ist ein Rest und keine Entscheidung.
        kopf = ZEHN.read_text(encoding="utf-8")
        self.assertIn("DROP OWNED BY", kopf)
        self.assertIn("Die Rolle bleibt stehen", kopf)

    def test_the_scan_would_see_a_drop(self) -> None:
        self.assertIsNotNone(re.search(r"DROP\s+ROLE", "DROP ROLE workforce_owner;",
                                       re.IGNORECASE))

    def test_the_comment_stripper_does_not_blank_the_file(self) -> None:
        # Ein Scanner, der nichts liest, meldet PASS - genau die Lage, die
        # `compose_scan.py` als Regel hinterlassen hat.
        self.assertIn("REVOKE ALL ON ALL TABLES", ohne_kommentarzeilen(ZEHN))


class TakesBackWhatNineGivesTest(unittest.TestCase):
    """Abgeleitet aus 009, nicht abgeschrieben."""

    def test_every_schema_009_touches_is_revoked(self) -> None:
        fehlend = fehlende_ruecknahmen(beruehrte_schemata(NEUN), schema_ruecknahmen(ZEHN))
        self.assertEqual([], fehlend, f"010 nimmt auf diesen Schemata nichts zurueck: {fehlend}")

    def test_every_schema_with_relation_grants_is_swept(self) -> None:
        fehlend = fehlende_pauschalen(relationsschemata(NEUN), pauschale_ruecknahmen(ZEHN))
        self.assertEqual([], fehlend, f"nicht pauschal zurueckgenommen: {fehlend}")

    def test_the_derivation_sees_the_grants(self) -> None:
        # Ohne das waeren die Vergleiche oben leere Mengen gegen leere Mengen.
        self.assertEqual(13, len(erteilte_rechte(NEUN)), sorted(erteilte_rechte(NEUN)))
        self.assertEqual({"workforce", "public"}, beruehrte_schemata(NEUN))
        self.assertEqual({"workforce"}, relationsschemata(NEUN))

    def test_a_forgotten_schema_would_be_caught(self) -> None:
        # Die Gegenprobe laeuft ueber dieselbe Funktion, nur mit einem Schema,
        # das `010` nicht zurueckninmmt - genau ein Fund, nicht "irgendwas".
        self.assertEqual(
            ["knowledge"],
            fehlende_ruecknahmen(beruehrte_schemata(NEUN) | {"knowledge"},
                                 schema_ruecknahmen(ZEHN)))

    def test_a_forgotten_object_class_would_be_caught(self) -> None:
        ohne_sequenzen = {(art, schema) for art, schema in pauschale_ruecknahmen(ZEHN)
                          if art != "SEQUENCES"}
        self.assertEqual(["SEQUENCES IN workforce"],
                         fehlende_pauschalen(relationsschemata(NEUN), ohne_sequenzen))


class PreconditionsTest(unittest.TestCase):
    """Ein Rueckbau, der auch ohne etwas zurueckzubauen gelingt, ist `G-068`."""

    def setUp(self) -> None:
        self.aktiv = ohne_kommentarzeilen(ZEHN)

    def test_it_refuses_without_the_009_marker(self) -> None:
        self.assertIn("'009_bus_function_owner'", self.aktiv)
        self.assertIn("MIGRATION_010_009_NOT_APPLIED", self.aktiv)

    def test_it_refuses_without_the_role(self) -> None:
        self.assertIn("MIGRATION_010_OWNER_ROLE_MISSING", self.aktiv)

    def test_it_verifies_the_end_state_in_the_same_transaction(self) -> None:
        for kennung in ("MIGRATION_010_RELATION_PRIVILEGES_REMAIN",
                        "MIGRATION_010_FUNCTION_PRIVILEGES_REMAIN",
                        "MIGRATION_010_SCHEMA_PRIVILEGES_REMAIN",
                        "MIGRATION_010_DEFAULT_ACL_REMAINS",
                        "MIGRATION_010_OWNER_STILL_OWNS_RELATIONS",
                        "MIGRATION_010_OWNER_STILL_OWNS_FUNCTIONS"):
            with self.subTest(kennung=kennung):
                self.assertIn(kennung, self.aktiv)

    def test_the_marker_row_matches_the_file_name(self) -> None:
        self.assertIn("'010_bus_function_owner_rollback'", self.aktiv)
        self.assertIn("MIG-010-BUS-FUNCTION-OWNER-ROLLBACK", self.aktiv)


class GateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.compose = COMPOSE.read_text(encoding="utf-8")

    def test_the_gate_defaults_to_closed(self) -> None:
        self.assertIn(f'{GATE}: "false"', self.compose)

    def test_the_rollback_has_its_own_gate_and_its_own_marker_check(self) -> None:
        self.assertIn(f'"$${{{GATE}:-false}}" != "true"', self.compose)
        self.assertIn("'010_bus_function_owner_rollback'", self.compose)
        self.assertIn("migrations/010_bus_function_owner_rollback.sql", self.compose)

    def test_the_rollback_is_not_coupled_to_the_migration_gate(self) -> None:
        # Ein geteiltes Gate hiesse: wer 009 oeffnet, oeffnet den Rueckbau mit.
        # Genau die Kopplung, die `G-031` getrennt hat.
        self.assertNotEqual(GATE, "APPLY_MIGRATION_009_FUNCTION_OWNER")
        self.assertIn('APPLY_MIGRATION_009_FUNCTION_OWNER: "false"', self.compose)


if __name__ == "__main__":
    unittest.main()
