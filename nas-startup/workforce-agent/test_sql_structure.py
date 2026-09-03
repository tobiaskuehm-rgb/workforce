"""Strukturpruefung der SQL-Dateien - der Ersatz fuer einen Parser, den es hier nicht gibt.

Auf dem Entwicklungsrechner dieses Projekts laeuft kein PostgreSQL: weder
Docker noch `psql` sind installiert. Jede SQL-Aenderung ist damit bis zu ihrem
ersten Lauf auf der NAS voellig ungeprueft - und der erste Lauf ist bei einer
Migration genau der Moment, in dem ein Fehler am teuersten ist.

Dieser Test macht nicht die starke Aussage "das ist gueltiges PostgreSQL". Er
macht die naechstbeste: **die Fehlerklassen, die `plpgsql` sofort abbrechen
lassen und die man beim Schreiben uebersieht, sind ausgeschlossen.**

  1. Dollar-Quote-Paare (`$$`, `$x$`) sind balanciert
  2. jede benutzte `v_`-Variable ist im `DECLARE` ihres Blocks deklariert
  3. jede deklarierte Variable wird auch benutzt - ein Ueberrest ist ein
     Hinweis auf eine halb umgebaute Pruefung
  4. `RAISE`: die Zahl der `%`-Platzhalter passt zur Zahl der Argumente
  5. eine Migration hat ihre Transaktionsklammer

Was er **nicht** sieht: Katalogspalten, Typen, Funktionsstelligkeit, Semantik.
Wer ihn fuer einen Parser haelt, hat eine Zusicherung ohne Deckung - das ist
Leitplanke 7 und der Grund, warum es hier steht.

Die Gegenprobe ist Teil des Tests, nicht ein Zusatz: `WeakenedSqlIsDetectedTest`
baut vier Fehler in eine Kopie ein und verlangt, dass jeder auffaellt. Ohne sie
waere ein Pruefer, der aus Versehen nichts liest, gruen ueber den ganzen
Bestand - genau die Lage, die `compose_scan.py` als Regel hinterlassen hat.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
MIGRATIONS = NAS / "postgres-init"
ACCEPTANCE = NAS / "postgres-tests"


def sql_dateien() -> list[pathlib.Path]:
    """Gefunden, nicht aufgelistet - eine neue Datei faellt sonst durch."""
    return sorted(MIGRATIONS.glob("*.sql")) + sorted(ACCEPTANCE.glob("*.sql"))


def ohne_kommentare(text: str) -> str:
    """`--`-Kommentare durch Leerzeichen ersetzen, Strings unangetastet.

    Die Laenge bleibt erhalten, damit Positionen weiter stimmen. Ein naives
    `re.sub` wuerde ein `--` innerhalb einer Zeichenkette mitnehmen; in diesem
    Bestand steht genau so etwas in Fehlermeldungen.
    """
    ergebnis: list[str] = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == "'":
            j = i + 1
            while j < n:
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":   # verdoppeltes Quote
                        j += 2
                        continue
                    break
                j += 1
            ergebnis.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("--", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            ergebnis.append(" " * (j - i))
            i = j
        else:
            ergebnis.append(text[i])
            i += 1
    return "".join(ergebnis)


def dollar_bloecke(text: str) -> tuple[list[tuple[str, int, int]], list[str]]:
    """(aeusserste Bloecke als (tag, start, ende), noch offene Tags)."""
    stapel: list[tuple[int, str]] = []
    bloecke: list[tuple[str, int, int]] = []
    for treffer in re.finditer(r"\$[A-Za-z_]*\$", text):
        tag, pos = treffer.group(0), treffer.start()
        if stapel and stapel[-1][1] == tag:
            start = stapel.pop()
            if not stapel:
                bloecke.append((tag, start[0] + len(tag), pos))
        else:
            stapel.append((pos, tag))
    return bloecke, [tag for _, tag in stapel]


def top_level_args(rest: str) -> list[str]:
    """Argumente einer RAISE-Anweisung, ohne an Kommas in Strings zu zerbrechen."""
    teile: list[str] = []
    tiefe, aktuell = 0, ""
    i, n = 0, len(rest)
    while i < n:
        zeichen = rest[i]
        if zeichen == "'":
            j = i + 1
            while j < n:
                if rest[j] == "'":
                    if j + 1 < n and rest[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            aktuell += rest[i:j + 1]
            i = j + 1
            continue
        if zeichen == "(":
            tiefe += 1
        elif zeichen == ")":
            tiefe -= 1
        if zeichen == "," and tiefe == 0:
            teile.append(aktuell.strip())
            aktuell = ""
        else:
            aktuell += zeichen
        i += 1
    if aktuell.strip():
        teile.append(aktuell.strip())
    return teile


def befunde(pfad: pathlib.Path, quelle: str | None = None) -> list[str]:
    """Alle Strukturbefunde einer Datei. Leere Liste heisst: nichts gefunden.

    `quelle` erlaubt es, denselben Pruefer auf einen veraenderten Text
    anzuwenden, ohne eine Datei anzulegen - so laeuft die Gegenprobe unten.
    """
    text = ohne_kommentare(quelle if quelle is not None else
                           pfad.read_text(encoding="utf-8"))
    gefunden: list[str] = []

    bloecke, offen = dollar_bloecke(text)
    if offen:
        gefunden.append(f"unbalancierte Dollar-Quotes: {offen}")

    for _tag, anfang, ende in bloecke:
        rumpf = text[anfang:ende]
        kopf = re.search(r"\bDECLARE\b(.*?)\bBEGIN\b", rumpf, re.DOTALL | re.IGNORECASE)
        deklariert = set(re.findall(r"^\s*(v_\w+)\s", kopf.group(1), re.MULTILINE)) if kopf else set()
        koerper = rumpf[kopf.end():] if kopf else rumpf
        benutzt = set(re.findall(r"\b(v_\w+)\b", koerper))
        gefunden += [f"{name}: benutzt, aber nicht deklariert"
                     for name in sorted(benutzt - deklariert)]
        gefunden += [f"{name}: deklariert, aber nie benutzt"
                     for name in sorted(deklariert - benutzt)]

        for treffer in re.finditer(r"\bRAISE\s+(?:EXCEPTION|NOTICE|WARNING)\b(.*?);",
                                   rumpf, re.DOTALL | re.IGNORECASE):
            inhalt = treffer.group(1).strip()
            if not inhalt.startswith("'"):
                continue                       # RAISE ... USING, kein Formatstring
            args = top_level_args(inhalt)
            # Benachbarte Literale werden in SQL verkettet - der Formatstring
            # kann ueber mehrere Zeilen gehen.
            format_string = "".join(re.findall(r"'((?:[^']|'')*)'", args[0]))
            platzhalter = len(re.findall(r"(?<!%)%(?!%)", format_string))
            weitere = [a for a in args[1:]
                       if not re.match(r"^(USING|ERRCODE|MESSAGE)\b", a, re.IGNORECASE)]
            if platzhalter != len(weitere):
                gefunden.append(
                    f"RAISE '{format_string[:44]}': {platzhalter} Platzhalter, "
                    f"{len(weitere)} Argument(e)")

    if pfad.parent.name == "postgres-init":
        aussen = text
        for _tag, anfang, ende in bloecke:
            aussen = aussen[:anfang] + " " * (ende - anfang) + aussen[ende:]
        if not re.search(r"^\s*BEGIN;", aussen, re.MULTILINE) \
                or not re.search(r"^\s*COMMIT;", aussen, re.MULTILINE):
            gefunden.append("Migration ohne BEGIN;/COMMIT;")
    return gefunden


class SqlStructureTest(unittest.TestCase):
    def test_every_sql_file_is_structurally_sound(self) -> None:
        for pfad in sql_dateien():
            with self.subTest(datei=f"{pfad.parent.name}/{pfad.name}"):
                self.assertEqual([], befunde(pfad))

    def test_the_scan_actually_sees_the_files(self) -> None:
        # Achtzehn saubere Dateien sind die Zahl, bei der ein Pruefer
        # verdaechtig ist. Ohne diese Zusicherung waere die Aussage oben
        # gruen ueber einer leeren Menge.
        dateien = sql_dateien()
        self.assertGreaterEqual(len(dateien), 18)
        self.assertIn("009_bus_function_owner.sql", [p.name for p in dateien])
        gesamt = sum(len(dollar_bloecke(ohne_kommentare(p.read_text(encoding="utf-8")))[0])
                     for p in dateien)
        self.assertGreater(gesamt, 40, "keine Dollar-Bloecke gefunden - Scan kaputt")

    def test_a_comment_may_contain_a_quote_without_breaking_the_scan(self) -> None:
        # Der Bestand enthaelt Kommentare mit Apostrophen. Ein Scanner, der
        # daran den String-Zustand verliert, liest den halben Rest als Literal
        # und meldet danach nichts mehr.
        #
        # Geprueft wird gegen einen Abnahmetestpfad, nicht gegen eine
        # Migration: Sonst schlaegt die Transaktionsklammer-Regel zu und der
        # Test wuerde etwas anderes messen, als sein Name sagt. Genau das ist
        # mir beim Schreiben passiert.
        text = "-- Gerd's Hinweis\nDO $$ DECLARE v_a integer; BEGIN v_a := 1; END; $$;\n"
        self.assertEqual([], befunde(ACCEPTANCE / "009_bus_function_owner_acceptance.sql",
                                     quelle=text))
        # Gegenprobe: derselbe Text als Migration gelesen faellt auf - die
        # Klammerregel ist also wirklich wirksam und nicht bloss nie erreicht.
        self.assertEqual(["Migration ohne BEGIN;/COMMIT;"],
                         befunde(MIGRATIONS / "009_bus_function_owner.sql", quelle=text))


class WeakenedSqlIsDetectedTest(unittest.TestCase):
    """Vier absichtliche Fehler, vier erwartete Funde.

    Ein Pruefer, der nur den Gutfall sieht, unterscheidet eine wirksame
    Kontrolle nicht von einer stillgelegten. Gebaut wird auf einer Kopie im
    Speicher; die Datei auf der Platte wird nicht angefasst.
    """

    def setUp(self) -> None:
        self.pfad = MIGRATIONS / "009_bus_function_owner.sql"
        self.original = self.pfad.read_text(encoding="utf-8")

    def _fund(self, kaputt: str, teil: str) -> None:
        self.assertNotEqual(self.original, kaputt, "die Aenderung hat nicht gegriffen")
        treffer = befunde(self.pfad, quelle=kaputt)
        self.assertTrue(any(teil in b for b in treffer),
                        f"{teil!r} nicht gemeldet, gefunden: {treffer}")

    def test_an_undeclared_variable_is_reported(self) -> None:
        self._fund(self.original.replace("v_count := v_count + 1;",
                                         "v_count := v_zaehler + 1;", 1),
                   "v_zaehler: benutzt, aber nicht deklariert")

    def test_an_unbalanced_dollar_quote_is_reported(self) -> None:
        self._fund(self.original.replace("END;\n$$;", "END;\n", 1),
                   "unbalancierte Dollar-Quotes")

    def test_a_raise_with_too_few_arguments_is_reported(self) -> None:
        """Angehaengt statt an einer Zeile verankert.

        Die erste Fassung strich ein Argument aus einer bestimmten
        `RAISE`-Zeile der Migration. Als diese Zeile am 2026-09-03 aus einem
        anderen Grund ersetzt wurde, schlug die Gegenprobe fehl - zu Recht, sie
        besteht darauf, dass ihre Aenderung wirklich greift. Ein Fehlerfall,
        der die Datei bloss ergaenzt, prueft denselben Pruefer und ueberlebt
        jede Umformulierung.
        """
        block = ("\nDO $p$\nDECLARE\n    v_x integer := 1;\nBEGIN\n"
                 "    RAISE EXCEPTION 'PROBE: % und %', v_x;\nEND;\n$p$;\n")
        self._fund(self.original + block, "2 Platzhalter, 1 Argument(e)")

    def test_a_raise_with_matching_arguments_is_not_reported(self) -> None:
        # Die Gegenrichtung: Ein korrekter RAISE darf nicht gemeldet werden,
        # sonst waere der Pruefer oben nur eine Sperre gegen jedes RAISE.
        block = ("\nDO $p$\nDECLARE\n    v_x integer := 1;\nBEGIN\n"
                 "    RAISE EXCEPTION 'PROBE: % und %', v_x, v_x;\nEND;\n$p$;\n")
        self.assertEqual([], befunde(self.pfad, quelle=self.original + block))

    def test_a_migration_without_its_transaction_is_reported(self) -> None:
        self._fund(self.original.replace("\nCOMMIT;", "\n", 1),
                   "Migration ohne BEGIN;/COMMIT;")

    def test_the_original_is_untouched(self) -> None:
        self.assertEqual(self.original, self.pfad.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
