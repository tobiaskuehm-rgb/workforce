"""Cross-document contradiction scan.

Review finding G-033: documentation and manifest overstated single pieces of
evidence, and a stale command survived in a script header. The class of defect
is older than that finding - `CORE PASS` outlived its retraction in one file,
a migration number outlived its rename in three, and both mirrors of the rules
were months apart from each other.

None of that is a code bug, and no test suite was looking. This one is. It
checks the invariants that have actually broken here, not a general idea of
tidiness:

  * every file a document points at exists
  * every migration mentioned by number exists under that number
  * the API version is the same everywhere it is stated
  * no document claims a gate the evidence has retracted
  * no document states a test count (they went stale twice)

A finding here is a documentation defect, which in this project has twice been
the thing that misled the reviewer.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"

# Documents that make claims about the system. Reviews are excluded on
# purpose: REVIEW_GERD.md is written by the reviewer and quotes states that
# were true when he wrote them.
DOCUMENTS = (
    ROOT / "CLAUDE.md",
    ROOT / "AGENTS.md",
    ROOT / "HANDOVER.md",
    NAS / "workforce-agent" / "README.md",
    NAS / "chain-test" / "README.md",
    NAS / "PHASE4_RUNBOOK.md",
)

# Documents deliberately outside the checks above. Reviews belong to the
# reviewer; evidence is a dated snapshot and its numbers are supposed to stay
# frozen. Everything else that lives at the top of nas-startup/ makes claims
# about the running system and has to be in DOCUMENTS - see the test below,
# which is what turns "somebody forgot to add it" into a failing run rather
# than silent loss of coverage.
NOT_CHECKED = {
    "REVIEW_GERD.md", "REVIEW_ANTWORTEN.md", "GESAMTREVIEW_GERD_2026-09-01.md",
    "NACHREVIEW_GERD_2026-09-01_C625B8C.md", "BERICHT_FUER_GERD.md",
    "DEC_ENTWUERFE_2026-08-31.md", "2026-08-13_workforce_bus_nas_deployment.md",
    "ACCEPTANCE_CHECKLIST.md", "BUS_PACKAGE_MANIFEST.md",
    "BUS_REALTEST_KARL_THORSTEN_RUNBOOK.md", "NEXT_STEPS_KARL_THORSTEN.md",
    "WORKFORCE_BUS_API_CONTRACT.md", "WORKFORCE_BUS_ROLLOUT.md",
    "README.md", "AGENTS.md", "HANDOVER.md",
}


def documents() -> list[tuple[pathlib.Path, str]]:
    return [(p, p.read_text(encoding="utf-8")) for p in DOCUMENTS if p.is_file()]


def is_placeholder(name: str) -> bool:
    """`NNN_<name>.sql` in the conventions is a pattern, not a reference."""
    return "<" in name or "NNN" in name or name.startswith("JJJJ")


class ReferencedFilesExistTest(unittest.TestCase):
    def test_every_migration_mentioned_by_name_exists(self) -> None:
        available = {p.name for p in (NAS / "postgres-init").glob("*.sql")}
        missing = []
        for path, text in documents():
            for name in re.findall(r"\b(\d{3}_[a-z_]+)\.sql\b", text):
                # Acceptance tests live in postgres-tests/ and carry their own
                # numbering; they have their own check below.
                if name.endswith("_acceptance") or is_placeholder(name):
                    continue
                if f"{name}.sql" not in available:
                    missing.append(f"{path.name}: {name}.sql")
        self.assertEqual([], missing, f"vorhanden: {sorted(available)}")

    def test_every_acceptance_test_mentioned_by_name_exists(self) -> None:
        available = {p.name for p in (NAS / "postgres-tests").glob("*.sql")}
        missing = [
            f"{path.name}: {name}"
            for path, text in documents()
            for name in re.findall(r"postgres-tests/(\S+?\.sql)", text)
            if name not in available and not is_placeholder(name)
        ]
        self.assertEqual([], missing, f"vorhanden: {sorted(available)}")

    def test_every_evidence_document_mentioned_exists(self) -> None:
        available = {p.name for p in (NAS / "evidence").glob("*.md")}
        missing = [
            f"{path.name}: {name}"
            for path, text in documents()
            for name in re.findall(r"(20\d\d-\d\d-\d\d_[a-z0-9_]+\.md)", text)
            if name not in available
        ]
        self.assertEqual([], missing)


class VersionsAgreeTest(unittest.TestCase):
    def test_the_api_version_is_stated_the_same_everywhere(self) -> None:
        app = (NAS / "workforce-api" / "app.py").read_text(encoding="utf-8")
        in_code = set(re.findall(r'"api_version": "(v\d+)"', app))
        self.assertEqual(1, len(in_code), f"app.py nennt mehrere Versionen: {in_code}")
        version = in_code.pop()

        dockerfile = (NAS / "workforce-api" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(f'version="{version}"', dockerfile)

        compose = (NAS / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn(f"startup-workforce-api:{version}", compose)

    def test_the_production_reference_names_the_running_version(self) -> None:
        # production_state.txt describes what runs on the NAS - which is the
        # older image, deliberately. It must not silently drift to the version
        # in the repository.
        state = (NAS / "production_state.txt").read_text(encoding="utf-8")
        self.assertRegex(state, r"API_IMAGE=startup-workforce-api:v\d+")
        self.assertRegex(state, r"PRODUCTION_COMMIT=[0-9a-f]{7,40}")


class NoRetractedClaimSurvivesTest(unittest.TestCase):
    def test_no_document_still_claims_core_pass(self) -> None:
        # The gate was downgraded to CORE ITERATE on 2026-08-31 (G-015) and
        # has stayed there. A surviving CORE PASS would be the exact defect
        # G-019 described: two documents, two truths.
        offenders = [
            path.name for path, text in documents()
            if re.search(r"(?<!~~)\bCORE PASS\b(?!~~)", text)
            and "CORE ITERATE" not in text
        ]
        self.assertEqual([], offenders)

    def test_no_document_states_a_test_count(self) -> None:
        # Convention in CLAUDE.md: test numbers went stale twice before
        # anybody read them.
        offenders = []
        for path, text in documents():
            for match in re.findall(r"\b\d{2,4} Tests?\b", text):
                offenders.append(f"{path.name}: {match}")
        self.assertEqual([], offenders)


class MigrationsAreNamedCorrectlyTest(unittest.TestCase):
    """G-037: 004 and 005 were confused in five places and the scan passed.

    The old scan checked that a referenced file exists. It never checked that
    the *number* a document attaches to a *topic* is the right one. After the
    G-021 merge the denial audit moved from 004 to 005, and the documents kept
    saying 004 - which points readers at the knowledge migration instead.
    """

    # Words that show the sentence is drawing a distinction rather than
    # making a claim: "damals 004, heute 005", "ohne Knowledge 004". A guard
    # that flags correct text gets switched off, so it has to read these.
    CONTRAST = ("ohne", "damals", "heute", "statt", "nicht", "umnummeriert",
                "frueher", "früher", "vorher")

    def disambiguated(self, line: str) -> bool:
        lowered = line.lower()
        return any(word in lowered for word in self.CONTRAST)

    # Topic -> the migration number that owns it, taken from the files
    # themselves rather than from a second list.
    def topic_of(self, number: str) -> str:
        for path in (NAS / "postgres-init").glob(f"{number}_*.sql"):
            return path.stem.split("_", 1)[1]
        return ""

    def test_the_denial_audit_is_not_called_004(self) -> None:
        self.assertEqual("bus_denial_audit", self.topic_of("005"))
        offenders = []
        for path, text in documents():
            for line_number, line in enumerate(text.splitlines(), start=1):
                if self.disambiguated(line):
                    continue
                if re.search(r"`004`[^\n]{0,60}(Ablehnung|denial|bus_denials)", line, re.I) \
                   or re.search(r"(Ablehnung|denial|bus_denials)[^\n]{0,40}`004`", line, re.I):
                    offenders.append(f"{path.name}:{line_number}")
        self.assertEqual([], offenders,
                         "das Ablehnungs-Audit ist Migration 005, nicht 004")

    def test_knowledge_is_not_called_005(self) -> None:
        self.assertEqual("knowledge_capability", self.topic_of("004"))
        offenders = [
            f"{path.name}:{number}"
            for path, text in documents()
            for number, line in enumerate(text.splitlines(), start=1)
            if not self.disambiguated(line)
            and re.search(r"`005`[^\n]{0,60}Knowledge", line, re.I)
        ]
        self.assertEqual([], offenders)


class TheGuardHasTeethTest(unittest.TestCase):
    """A scan that only ever passes proves nothing about its own reach.

    G-037 was exactly that: the first version of this file passed while five
    documents named the wrong migration. These cases pin what it can see and
    what it deliberately lets through.
    """

    def setUp(self) -> None:
        self.checker = MigrationsAreNamedCorrectlyTest("test_the_denial_audit_is_not_called_004")

    def test_it_would_catch_the_line_that_was_actually_wrong(self) -> None:
        wrong = "| `G-018` | Migration `004`: append-only `bus_denials` |"
        self.assertFalse(self.checker.disambiguated(wrong))
        self.assertTrue(
            re.search(r"`004`[^\n]{0,60}(Ablehnung|denial|bus_denials)", wrong, re.I)
        )

    def test_it_lets_a_sentence_that_draws_the_distinction_through(self) -> None:
        # "damals 004, heute 005" is correct text and must not be flagged -
        # a guard that cries wolf gets switched off.
        for correct in (
            "die Migration für das Ablehnungs-Audit - damals `004`, heute `005`",
            "Migrationen `005`-`007` - ohne Knowledge `004`",
        ):
            with self.subTest(text=correct):
                self.assertTrue(self.checker.disambiguated(correct))

    def test_the_topic_mapping_comes_from_the_files(self) -> None:
        # Not from a second list somebody has to keep in sync - that is the
        # failure mode this whole scan exists for.
        self.assertEqual("bus_denial_audit", self.checker.topic_of("005"))
        self.assertEqual("knowledge_capability", self.checker.topic_of("004"))


class ClaimsMatchTheCodeTest(unittest.TestCase):
    """G-037: comments outlived the behaviour they described."""

    def test_the_data_policy_comment_matches_the_allowlist(self) -> None:
        # The example file said METADATA_ONLY carries the subject long after
        # the subject had been removed from it (G-029, then G-037).
        import data_boundary

        example = (NAS / "workforce-agent" / "workforce-agent.env.example").read_text(
            encoding="utf-8"
        )
        line = next(
            (l for l in example.splitlines() if "METADATA_ONLY" in l and l.lstrip().startswith("#")),
            "",
        )
        carries_subject = "subject" in data_boundary._ALLOWED_FIELDS["METADATA_ONLY"]
        claims_subject = re.search(r"^#\s+METADATA_ONLY\s+subject", line) is not None
        self.assertEqual(carries_subject, claims_subject,
                         f"Kommentar und Feldliste widersprechen sich: {line!r}")

    def test_no_document_claims_a_model_fallback(self) -> None:
        # G-036 removed the server-side fallback. A document still promising
        # it would send the next reader looking for a feature that is gone.
        providers = (NAS / "workforce-agent" / "providers.py").read_text(encoding="utf-8")
        code = "\n".join(
            l for l in providers.splitlines() if not l.lstrip().startswith("#")
        )
        self.assertNotIn("fallbacks=", code)
        offenders = [
            path.name for path, text in documents()
            if re.search(r"Fallback-?Modell|server-side-fallback", text, re.I)
        ]
        self.assertEqual([], offenders)

    def test_no_document_states_a_commit_count(self) -> None:
        # Same class as the test counts: true when written, wrong one commit
        # later.
        offenders = [
            f"{path.name}: {match}"
            for path, text in documents()
            for match in re.findall(r"\b\d{2,5} Commits?\b", text)
        ]
        self.assertEqual([], offenders)

    def test_nothing_claims_all_gates_are_closed_while_they_are_open(self) -> None:
        # HANDOVER said "Nichts mehr offen beim Nutzer" while four migration
        # gates and a CEO decision were open.
        offenders = [
            path.name for path, text in documents()
            if "Nichts mehr offen" in text
        ]
        self.assertEqual([], offenders)


class GatedMigrationsAreNotDescribedAsAutomaticTest(unittest.TestCase):
    """G-037: a document said a gated migration applies on the next `up`.

    Every migration with an APPLY_ gate is fail-closed - a plain
    `docker compose up` applies none of them. A document promising the
    opposite sends somebody into a rollout window expecting work that will
    not happen, or worse, not expecting work that will.
    """

    def gated_migrations(self) -> set[str]:
        compose = (NAS / "compose.yaml").read_text(encoding="utf-8")
        return {
            name for name in re.findall(r"migrations/(\d{3})_[a-z_]+\.sql", compose)
            if re.search(rf"APPLY_MIGRATION_{name}_[A-Z_]+:-false", compose)
        }

    def test_at_least_one_migration_is_gated(self) -> None:
        # If this ever returns nothing the test below becomes vacuous.
        self.assertNotEqual(set(), self.gated_migrations())

    def test_no_document_calls_a_gated_migration_automatic(self) -> None:
        gated = self.gated_migrations()
        automatic = re.compile(
            r"(zieht (sie|beide|diese)?\s*beim naechsten|zieht .{0,20}beim nächsten|"
            r"automatisch angewendet|wendet .{0,20}automatisch an)", re.I
        )
        offenders = []
        for path, text in documents():
            for number, line in enumerate(text.splitlines(), start=1):
                if not automatic.search(line):
                    continue
                if any(re.search(rf"`?{g}[_`]", line) for g in gated):
                    offenders.append(f"{path.name}:{number}")
        self.assertEqual([], offenders,
                         f"gegatete Migrationen: {sorted(gated)} - ein up wendet keine an")


class NoHardcodedCountsTest(unittest.TestCase):
    """G-037: a manifest file count went stale between two deployments."""

    # A number is allowed when the line anchors it to a moment - a commit or
    # a date. "99 Dateien auf f59e757" stays true forever; "56 Dateien" in a
    # status table is stale by the next nightly backup.
    ANCHOR = re.compile(r"`[0-9a-f]{7,40}`|\b20\d\d-\d\d-\d\d\b")

    COUNT = re.compile(r"\b\d{2,4}\s+(?:Manifest)?[Dd]ateien\b")

    def test_no_document_states_an_unanchored_file_count(self) -> None:
        """The unit is the sentence, not the source line.

        The first version scanned line by line. Markdown prose wraps, so a
        paragraph reading "das Manifest deckt 130\nDateien" split the number
        from the word and slipped through - which is exactly how the count in
        PHASE4_RUNBOOK.md survived a run of this test. Joining wrapped lines
        closes that. The anchor now has to sit in the same sentence as the
        number, because a date three sentences away does not keep this
        particular number true.
        """
        offenders = []
        for path, text in documents():
            for start, paragraph in self.paragraphs(text):
                for sentence in re.split(r"(?<=[.:;])\s+", paragraph):
                    if not self.COUNT.search(sentence):
                        continue
                    if self.ANCHOR.search(sentence):
                        continue
                    offenders.append(f"{path.name}:{start}")
        self.assertEqual([], sorted(set(offenders)),
                         "eine Dateizahl ohne Commit oder Datum veraltet still")

    @staticmethod
    def paragraphs(text: str) -> list[tuple[int, str]]:
        """Wrapped prose lines joined; blank lines and list/table rows split.

        Table rows must stay separate: joining them would let an anchor in one
        row excuse a bare count in the next.
        """
        out, buf, start = [], [], 0
        def flush():
            if buf:
                out.append((start, " ".join(buf)))
                buf.clear()
        for number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            structural = (not stripped or stripped.startswith(("|", "-", "*", "#", ">", "```"))
                          or re.match(r"^\d+\.", stripped))
            if structural:
                flush()
                if stripped:
                    out.append((number, stripped))
                continue
            if not buf:
                start = number
            buf.append(stripped)
        flush()
        return out

    def test_every_operational_document_is_actually_checked(self) -> None:
        """A checked-documents list nobody updates stops being a check.

        PHASE4_RUNBOOK.md was written, reviewed and nearly committed while
        being invisible to every scanner in this file - including the one that
        catches unanchored file counts, which it tripped. It is also the most
        dangerous document in the repository, because its lines are meant to be
        executed. So: any new top-level document either joins DOCUMENTS or is
        named in NOT_CHECKED, and forgetting both fails here.
        """
        checked = {p.name for p in DOCUMENTS}
        forgotten = sorted(
            p.name for p in NAS.glob("*.md")
            if p.name not in checked and p.name not in NOT_CHECKED
        )
        self.assertEqual([], forgotten,
                         "neues Dokument: in DOCUMENTS aufnehmen oder in "
                         "NOT_CHECKED begruenden")

    def test_a_wrapped_count_is_still_caught(self) -> None:
        """The escape this guard was blind to, kept as a standing probe."""
        wrapped = "das laufende Manifest deckt 130\nDateien und faellt damit auf."
        joined = self.paragraphs(wrapped)
        self.assertEqual(1, len(joined), "Zeilen wurden nicht zusammengefuegt")
        self.assertTrue(self.COUNT.search(joined[0][1]))
        self.assertFalse(self.ANCHOR.search(joined[0][1]))

    def test_a_table_row_cannot_borrow_the_anchor_of_its_neighbour(self) -> None:
        rows = "| Lauf | `ec8df2e` |\n| Manifest | 126 Dateien |"
        joined = self.paragraphs(rows)
        self.assertEqual(2, len(joined), "Tabellenzeilen wurden verschmolzen")
        self.assertFalse(self.ANCHOR.search(joined[1][1]))

    def test_the_anchor_rule_actually_distinguishes(self) -> None:
        # A guard whose exemption swallows everything is not a guard.
        self.assertTrue(self.ANCHOR.search("Der Lauf begann auf `f59e757`, 99 Dateien"))
        self.assertFalse(self.ANCHOR.search("| Manifest | 126 Dateien, nichts unerwartet |"))


class SecretsAreDescribedWhereTheyLiveTest(unittest.TestCase):
    """G-037: a document told the operator to put a secret in startup.env.

    The compose file had just stopped handing startup.env to the API, exactly
    so the owner password would leave the container. A document pointing the
    new secret back into that file would undo the fix by instruction.
    """

    def api_service(self):
        import compose_scan

        return compose_scan.scan(NAS / "compose.yaml")["workforce-api"]

    def test_the_api_service_really_has_no_env_file(self) -> None:
        self.assertEqual([], self.api_service().env_files)

    def test_no_document_claims_the_api_still_holds_the_owner_secret(self) -> None:
        """The line that got away.

        After startup.env was removed from the API service, HANDOVER still
        said "der API-Container sieht ueber env_file weiterhin
        POSTGRES_PASSWORD". True when written, wrong one commit later - and
        none of the other checks in this file looked at it. A stale open point
        is worse than a stale closed one: it sends somebody to fix what is
        already fixed, and it makes the real open points look less credible.
        """
        if self.api_service().env_files:
            self.skipTest("API-Service laedt wieder eine env_file - dann stimmt die Aussage")
        offenders = []
        for path, text in documents():
            for number, line in enumerate(text.splitlines(), start=1):
                if not re.search(r"POSTGRES_PASSWORD|Eigentuemer-Passwort|Eigentümer-Passwort", line):
                    continue
                # Only lines that claim the API *has* it, in the present tense.
                if re.search(r"(API-Container|API-Service|api).{0,80}(sieht|erhaelt|erhält|bekommt|traegt|trägt).{0,40}"
                             r"(POSTGRES_PASSWORD|Eigentuemer-Passwort|Eigentümer-Passwort)", line, re.I) \
                   or re.search(r"(POSTGRES_PASSWORD|Eigentuemer-Passwort|Eigentümer-Passwort).{0,60}"
                                r"(im API-Container|erreicht den API)", line, re.I):
                    if not re.search(r"erledigt|nicht mehr|behoben|entfernt|frueher|früher|war\b", line, re.I):
                        offenders.append(f"{path.name}:{number}")
        self.assertEqual([], offenders,
                         "startup.env erreicht den API-Service nicht mehr")

    def test_that_check_would_have_caught_the_real_line(self) -> None:
        # The sentence exactly as it stood, so the guard is shown to have
        # teeth rather than asserted to.
        stale = ("**Offen und benannt:** `workforce_app` behaelt `SUPERUSER`, und der "
                 "API-Container sieht ueber `env_file` weiterhin `POSTGRES_PASSWORD`.")
        self.assertTrue(
            re.search(r"(API-Container|API-Service|api).{0,80}(sieht|erhaelt|bekommt).{0,40}"
                      r"(POSTGRES_PASSWORD|Eigentuemer-Passwort)", stale, re.I)
        )
        self.assertFalse(re.search(r"erledigt|nicht mehr|behoben|entfernt", stale, re.I))

    def test_no_document_puts_an_api_secret_into_startup_env(self) -> None:
        # Only checked while the service has no env_file - if that ever comes
        # back, this test is not the right guard any more and says so.
        if self.api_service().env_files:
            self.skipTest("API-Service laedt wieder eine env_file - erst das pruefen")
        offenders = []
        for path, text in documents():
            for number, line in enumerate(text.splitlines(), start=1):
                if "startup.env" not in line:
                    continue
                if re.search(r"(workforce_api|API-Schl|API_KEY).{0,60}startup\.env", line, re.I) \
                   or re.search(r"startup\.env.{0,60}(workforce_api|API-Schl|API_KEY)", line, re.I):
                    if not re.search(r"nicht|kein|ohne|erreicht .{0,20}nicht", line, re.I):
                        offenders.append(f"{path.name}:{number}")
        self.assertEqual([], offenders)


class MigrationNumbersAreUniqueTest(unittest.TestCase):
    def test_no_two_migrations_share_a_number(self) -> None:
        names = sorted(p.name for p in (NAS / "postgres-init").glob("*.sql"))
        numbers = [n.split("_", 1)[0] for n in names]
        self.assertEqual(len(numbers), len(set(numbers)), names)

    def test_no_two_acceptance_tests_share_a_number(self) -> None:
        names = sorted(p.name for p in (NAS / "postgres-tests").glob("*.sql"))
        numbers = [n.split("_", 1)[0] for n in names]
        self.assertEqual(len(numbers), len(set(numbers)), names)


if __name__ == "__main__":
    unittest.main()
