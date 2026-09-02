"""The bus address is a derived name, and it fell over without a sound.

Review finding G-051. `BUS_BASE_URL` stood in 17 places across every runtime
package - contract test, chain test, worker core, Telegram connector, agent -
and as a fact in none of them. The hostname Synology hands out for LAN access
**encodes the address**:

    https://192-168-68-78.k30068872219.direct.quickconnect.to:8443

so it changes the moment DHCP changes the address. On 2026-09-02 the NAS came
back from a reboot on .81 while the whole repository still said .78, where
`Connection refused` was the answer. Every remaining window would have died at
the first connection.

That is the same class as G-042: a name assembled from something that moves,
mistaken for an identifier. What makes this one worse is that nothing could
see it. The local suites run without network on purpose, and a deploy manifest
compares checksums, not addresses.

The split follows from that. **Here**: all occurrences agree with the one
named source, which is offline and therefore testable everywhere. **On the
NAS**: `check_bus_address.sh` decides whether that address is still this
machine, because only the machine can answer it.

One detail is worth keeping in sight: the NAS certificate carries the wildcard
`*.k30068872219.direct.quickconnect.to`, so TLS verifies *any* address variant
of that pattern against the hostname. Measured with the same
`ssl.create_default_context()` that bus_client.py uses. Convenient - and it
means a wrong address never fails at the certificate. It fails at connect, in
the window.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
STATE = NAS / "production_state.txt"

# Evidence is a dated snapshot and stays frozen; no evidence file names the
# address anyway (checked, rather than assumed - a claim about what documents
# contain has been wrong here before).
AUSGENOMMEN = ("evidence",)

# Diese Datei selbst: sie zitiert die tote Adresse im Kopf und in der
# Gegenprobe, und beides soll sie. Sie traegt keine Konfiguration, also
# verdeckt die Ausnahme nichts - anders als bei jeder anderen Datei hier.
SELBST = pathlib.Path(__file__).name

# Zwei Sorten Datei, zwei Regeln. **Konfiguration** wird ausgefuehrt: dort
# gilt genau eine Adresse, ausnahmslos. **Markdown** erzaehlt: dort darf die
# tote Adresse vorkommen, wenn der Satz sie datiert oder die Befundnummer
# nennt - eine Erklaerung, warum sie tot ist, ist kein Rueckfall.
#
# Die Trennung ist noetig, weil sonst genau die Dokumente rot werden, die den
# Befund beschreiben, und dann wird der Waechter aufgeweicht statt gelesen.
# Sie ist zugleich eng genug: ein Runbook, dessen Zeilen ausgefuehrt werden,
# kaeme mit einer nackten alten Adresse nicht durch.
KONFIGURATION = (".yaml", ".yml", ".py", ".sh", ".example", ".txt")
ERZAEHLEND = (".md",)
SUFFIXE = KONFIGURATION + ERZAEHLEND

# Datum oder Befundnummer im selben Satz - dasselbe Mass, das dieses Projekt
# schon fuer Dateizahlen benutzt.
ANKER = re.compile(r"\b20\d\d-\d\d-\d\d\b|`?G-0\d\d`?")

# Any https URL pointing at the QuickConnect direct name, wherever it appears:
# compose environment, .env example, prose in a runbook.
URL = re.compile(r"https://[A-Za-z0-9.-]*\.direct\.quickconnect\.to:\d+")

# The label that carries the address: 192-168-68-81 -> 192.168.68.81.
EINGEBETTET = re.compile(r"^https://(\d+)-(\d+)-(\d+)-(\d+)\.")


def erwartete_url() -> str:
    for line in STATE.read_text(encoding="utf-8").splitlines():
        if line.startswith("BUS_BASE_URL="):
            return line[len("BUS_BASE_URL="):].strip()
    raise AssertionError("production_state.txt nennt kein BUS_BASE_URL")


def dateien() -> list[pathlib.Path]:
    return [p for p in sorted(NAS.rglob("*"))
            if p.is_file() and p.suffix in SUFFIXE and p.name != SELBST
            and not any(teil in AUSGENOMMEN for teil in p.relative_to(NAS).parts)]


def fundstellen(suffixe: tuple[str, ...] = SUFFIXE) -> list[tuple[pathlib.Path, str]]:
    out = []
    for p in dateien():
        if p.suffix not in suffixe:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for treffer in URL.finditer(text):
            out.append((p, treffer.group(0)))
    return out


# Wie weit vor der Fundstelle ein Anker noch zaehlt. Eine tote Adresse steht
# in diesen Dokumenten fast immer als zitierter Codeblock, und der Satz, der
# ihn einleitet, steht darueber - so liest ein Mensch es auch. Drei Zeilen
# sind genug fuer "Ueberschrift, Leerzeile, Zaunmarke" und zu wenig, um einen
# Anker aus einem anderen Abschnitt zu borgen.
ANKER_REICHWEITE = 3


def unverankerte_erwaehnungen(tot: str) -> list[str]:
    """Markdown-Stellen, die die tote Adresse nennen, ohne sie einzuordnen."""
    out = []
    for p in dateien():
        if p.suffix not in ERZAEHLEND:
            continue
        zeilen = p.read_text(encoding="utf-8").splitlines()
        for i, zeile in enumerate(zeilen):
            if tot not in zeile:
                continue
            umfeld = zeilen[max(0, i - ANKER_REICHWEITE):i + 1]
            if any(ANKER.search(z) for z in umfeld):
                continue
            out.append(f"{p.relative_to(NAS)}:{i + 1}: {zeile.strip()[:90]}")
    return out


class OneAddressEverywhereTest(unittest.TestCase):
    def setUp(self) -> None:
        self.erwartet = erwartete_url()
        self.fundstellen = fundstellen(KONFIGURATION)

    def test_the_named_source_carries_a_usable_address(self) -> None:
        self.assertTrue(self.erwartet.startswith("https://"))
        self.assertRegex(self.erwartet, r":\d+$")
        # No path, no query: validate_base_url() in bus_client.py refuses those.
        self.assertNotIn("?", self.erwartet)
        # "https://host:8443" - zwei Schraegstriche und keiner mehr.
        self.assertEqual(2, self.erwartet.count("/"), "die URL traegt einen Pfad")

    def test_every_occurrence_matches_the_named_source(self) -> None:
        abweichend = sorted({
            f"{p.relative_to(NAS)}: {url}"
            for p, url in self.fundstellen if url != self.erwartet
        })
        self.assertEqual([], abweichend,
                         "Adresse weicht von production_state.txt ab")

    def test_the_address_is_actually_used_somewhere(self) -> None:
        # A guard over zero occurrences is green and worthless. On 2026-09-02
        # there were 17; the exact number is not the point and would go stale,
        # but "more than a handful, across several packages" is.
        pakete = {p.relative_to(NAS).parts[0] for p, _ in self.fundstellen}
        self.assertGreater(len(self.fundstellen), 5)
        self.assertGreaterEqual(len(pakete), 3, f"nur in {pakete} gefunden")

    def test_the_retired_address_is_gone_from_configuration(self) -> None:
        tot = "192-168-68-78"
        drin = sorted({str(p.relative_to(NAS)) for p, url in self.fundstellen if tot in url})
        self.assertEqual([], drin, f"{tot} antwortet seit dem 2026-09-02 nicht mehr")

    def test_prose_may_name_the_dead_address_only_with_a_date_or_a_finding(self) -> None:
        self.assertEqual([], unverankerte_erwaehnungen("192-168-68-78"),
                         "alte Adresse ohne Datum und ohne Befundnummer")

    def test_that_prose_rule_actually_distinguishes(self) -> None:
        # Eine Ausnahme, die alles durchlaesst, ist keine.
        self.assertTrue(ANKER.search("Am 2026-09-02 zeigte 192-168-68-78 ins Leere."))
        self.assertTrue(ANKER.search("Die Adresse 192-168-68-78 (`G-051`) ist tot."))
        self.assertIsNone(ANKER.search("Die Adresse lautet 192-168-68-78."))

    def test_an_unanchored_block_would_still_be_caught(self) -> None:
        # Die Reichweite darf nicht so gross sein, dass irgendein Datum
        # weiter oben im Dokument alles freikauft.
        import tempfile
        tot = "192-168-68-78"
        text = ("Am 2026-09-02 war einiges los.\n\n" + "Fuelltext.\n" * 6
                + "```\nhttps://" + tot + ".example:8443\n```\n")
        with tempfile.TemporaryDirectory() as ordner:
            datei = pathlib.Path(ordner) / "probe.md"
            datei.write_text(text, encoding="utf-8")
            zeilen = text.splitlines()
            treffer = [i for i, z in enumerate(zeilen) if tot in z]
            self.assertEqual(1, len(treffer))
            i = treffer[0]
            umfeld = zeilen[max(0, i - ANKER_REICHWEITE):i + 1]
            self.assertFalse(any(ANKER.search(z) for z in umfeld),
                             "ein Anker sechs Zeilen frueher darf nicht zaehlen")

    def test_a_divergent_occurrence_would_be_caught(self) -> None:
        # The probe the real defect would have needed.
        fremd = "https://192-168-68-78.k30068872219.direct.quickconnect.to:8443"
        self.assertNotEqual(self.erwartet, fremd)
        self.assertTrue(URL.fullmatch(fremd), "das Muster erkennt die alte Form nicht")

    def test_the_pattern_does_not_swallow_unrelated_urls(self) -> None:
        for harmlos in ("https://api.telegram.org/bot123/getUpdates",
                        "https://api.anthropic.com/v1/messages",
                        "http://localhost:8080/bus/v1/status"):
            with self.subTest(url=harmlos):
                self.assertIsNone(URL.search(harmlos))


class TheAddressIsCheckedOnTheNasTest(unittest.TestCase):
    """The half that only the machine can answer."""

    def setUp(self) -> None:
        self.script = (NAS / "check_bus_address.sh").read_text(encoding="utf-8")
        self.status = (NAS / "nas_status.sh").read_text(encoding="utf-8")

    def test_it_reads_the_address_from_the_named_source(self) -> None:
        self.assertIn("BUS_BASE_URL=", self.script)
        self.assertIn("production_state.txt", self.script)

    def test_it_compares_against_the_machines_own_addresses(self) -> None:
        # `ip -4 -o addr` over all global addresses, not one hard-coded
        # interface: the question is "does this name point at me", and the NAS
        # answers on eth0 today and might not tomorrow.
        self.assertIn("ip -4 -o addr show scope global", self.script)
        self.assertNotIn("eth0", self.script)

    def test_it_never_writes(self) -> None:
        loeschend = re.compile(r"(?:^|[;&|]\s*|-exec\s+)(rm|mv|cp|tee|truncate)\b"
                               r"|>\s*[\"']?/", re.MULTILINE)
        code = "\n".join(z for z in self.script.splitlines()
                         if not z.lstrip().startswith("#"))
        # `2>/dev/null` verwirft, es schreibt nicht. Alles andere mit einem
        # absoluten Pfad hinter `>` waere ein Schreibvorgang.
        code = code.replace("2>/dev/null", "").replace(">/dev/null", "")
        self.assertIsNone(loeschend.search(code))

    def test_the_result_line_follows_the_findings(self) -> None:
        self.assertIn("problems=$((problems + 1))", self.script)
        self.assertRegex(self.script, r'if \[ "\$problems" -eq 0 \]')
        self.assertIn("exit 1", self.script)

    def test_a_weakened_result_line_would_be_noticed(self) -> None:
        broken = self.script.replace('if [ "$problems" -eq 0 ]; then', 'if true; then', 1)
        self.assertNotEqual(self.script, broken)
        self.assertNotRegex(broken, r'if \[ "\$problems" -eq 0 \]')

    def test_it_runs_as_a_gate_and_not_behind_a_pipe(self) -> None:
        # The reason run_gate exists at all: a pipeline reports the exit code
        # of its last command, which once made nas_status.sh print PASS under
        # a failing manifest.
        self.assertIn('run_gate "Bus-Adresse" check_bus_address.sh', self.status)
        self.assertNotIn("check_bus_address.sh |", self.status)

    def test_a_name_without_an_embedded_address_is_not_judged(self) -> None:
        # If the NAS ever moves behind a name that carries no address, this
        # check has nothing to say - and says so, instead of failing or,
        # worse, passing silently.
        self.assertIn("HINWEIS:", self.script)
        self.assertIn("nicht pruefbar", self.script)


if __name__ == "__main__":
    unittest.main()
