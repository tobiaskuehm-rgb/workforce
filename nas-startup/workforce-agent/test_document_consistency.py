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
    # Both moved out of NOT_CHECKED on 2026-09-02 (G-046). The contract had
    # claimed "in workforce-api:v6 implementiert" for four versions, and the
    # README named v6 as the active API while v9 was running. Neither carries
    # a date, so both are read as current - which is exactly the case the
    # exclusion list was never meant to cover.
    NAS / "WORKFORCE_BUS_API_CONTRACT.md",
    NAS / "README.md",
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
    "WORKFORCE_BUS_ROLLOUT.md",
    "AGENTS.md", "HANDOVER.md",
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
        # Not every dated document lives under evidence/:
        # 2026-08-13_workforce_bus_nas_deployment.md sits at the top level and
        # always has. The scan assumed otherwise, so a correct reference to it
        # read as a broken one (G-046).
        available = {p.name for p in (NAS / "evidence").glob("*.md")}
        available |= {p.name for p in NAS.glob("20*.md")}
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


class UnexercisedArtifactIsLabelledTest(unittest.TestCase):
    """An artifact that has never run must not silently back an argument.

    Review finding G-046: `/openapi.json` was left reachable-with-a-key rather
    than removed, and the reason given - in a code comment and in the review
    answer - was that `e2e_acceptance.rb` reads the path list. That script has
    never been run: no evidence file names a run, and no runbook calls it. The
    trade is still the right one, but the argument is weaker than it reads, and
    the difference has to be written down where the argument is made.

    The check is deliberately narrow. Trying to decide mechanically whether an
    artifact "is exercised" gave the wrong answer for three of four candidates
    - `check_backup_permissions.sh` runs inside `nas_status.sh`, and
    `backup_bundle.sh` runs every session - so a broad guard here would have
    produced noise and been switched off.
    """

    SCRIPT = NAS / "workforce-api" / "e2e_acceptance.rb"

    def test_the_script_says_it_has_never_run(self) -> None:
        self.assertIn("NIE AUSGEFUEHRT", self.SCRIPT.read_text(encoding="utf-8"))

    def test_the_code_comment_carries_the_qualifier(self) -> None:
        app = (NAS / "workforce-api" / "app.py").read_text(encoding="utf-8")
        self.assertIn("e2e_acceptance.rb", app)
        self.assertIn("has never been run", app)

    def test_no_evidence_file_claims_a_run(self) -> None:
        # If a run ever happens, its evidence lands here and this test fails -
        # which is the reminder to take the qualifier back out again.
        for path in sorted((NAS / "evidence").glob("*.md")):
            self.assertNotIn("e2e_acceptance", path.read_text(encoding="utf-8"),
                             f"{path.name} nennt einen Lauf - Kennzeichnung anpassen")


class RunbookStatusIsCurrentTest(unittest.TestCase):
    """The runbook's head has to describe the state the runbook is in.

    It went stale three times: after G-042 it still announced the eighth
    check, after G-043 it still announced G-042 as the open blocker, and after
    the window had actually run it still said "vorbereitet, nicht ausgefuehrt"
    (G-046). The head is the first thing an operator reads before running the
    rest of the file in a production shell, so every one of those was a
    statement about whether it is safe to start.

    A runbook has two states and the check follows them:

      pending   - the head names the newest finding from the reviewer's own
                  file, so it cannot be satisfied by editing one side
      executed  - the head says so, with a date, and points at an evidence
                  file that exists
    """

    HEAD_LINES = 16

    def head(self) -> str:
        text = (NAS / "PHASE4_RUNBOOK.md").read_text(encoding="utf-8")
        return "\n".join(text.split("\n")[: self.HEAD_LINES])

    def newest_finding(self) -> str:
        review = (NAS / "REVIEW_GERD.md").read_text(encoding="utf-8")
        numbers = sorted(int(n) for n in re.findall(r"\bG-(\d{3})\b", review))
        self.assertTrue(numbers, "REVIEW_GERD.md nennt keine Befundnummer")
        return f"G-{numbers[-1]:03d}"

    def test_the_head_describes_the_state_the_runbook_is_in(self) -> None:
        head = self.head()
        if "ausgeführt am" in head:
            self.assertRegex(head, r"ausgeführt am \d{4}-\d{2}-\d{2}")
            named = re.findall(r"`(evidence/[\w./-]+\.md)`", head)
            self.assertTrue(named, "ausgefuehrt, aber kein Nachweis genannt")
            for name in named:
                self.assertTrue((NAS / name).is_file(), f"{name} fehlt")
        else:
            self.assertIn(self.newest_finding(), head)

    def test_a_head_that_claims_a_run_without_evidence_would_be_caught(self) -> None:
        head = self.head()
        self.assertIn("ausgeführt am", head)
        broken = re.sub(r"`evidence/[\w./-]+\.md`", "`evidence/gibt-es-nicht.md`", head)
        self.assertNotEqual(head, broken)
        named = re.findall(r"`(evidence/[\w./-]+\.md)`", broken)
        self.assertTrue(named)
        self.assertFalse(any((NAS / name).is_file() for name in named))

    def test_a_pending_head_without_the_newest_finding_would_be_caught(self) -> None:
        # The other branch, exercised on a head that is not the current one -
        # otherwise the pending rule would rot the moment a runbook is run.
        pending = "**Status: vorbereitet, nicht ausgeführt.** Blocker ist G-001."
        self.assertNotIn("ausgeführt am", pending)
        self.assertNotIn(self.newest_finding(), pending)


def section(path: pathlib.Path, heading: str) -> str:
    """The body under one Markdown heading, up to the next of same or higher level."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if heading not in lines:
        raise LookupError(heading)
    level = len(heading) - len(heading.lstrip("#"))
    out = []
    for line in lines[lines.index(heading) + 1:]:
        if line.startswith("#") and (len(line) - len(line.lstrip("#"))) <= level:
            break
        out.append(line)
    return "\n".join(out)


class StatusSectionsNameNoVersionTest(unittest.TestCase):
    """G-050: three documents named a running API version that was two behind.

    CLAUDE.md's layer table said the API is `v7` and HANDOVER.md said the NAS
    runs on `v8`, while `v9` had been running since 2026-09-01. CLAUDE.md is
    the first file every assistant reads and HANDOVER.md is the only thing the
    two sides know about each other, so both were wrong in the place where it
    costs the most - and 35 tests in this file were green.

    The fix is not a cleverer scanner. `production_state.txt` already is the
    one place that names the running state, and HANDOVER.md already says so in
    words: "Der laufende Stand ist production_state.txt, nicht dieses
    Dokument." A second statement of the same fact is a copy, and copies go
    stale. So the status sections state no version at all - they point at the
    source. A version that is never written down cannot rot.

    Deliberately narrow: everywhere else a version number is part of a story
    ("v7 -> v8 im Fenster", the rollback tag, a `docker save` command) and
    those stay true. Only sections that describe the system **now** are held
    to this.
    """

    # Sections whose subject is the current state of the system.
    SECTIONS = (
        (ROOT / "CLAUDE.md", "## Worum es geht"),
        (ROOT / "HANDOVER.md", "### Fertig und nachgewiesen"),
        (ROOT / "HANDOVER.md", "### Systemzustand"),
    )

    # The two files that answer "what is running": the named source state and
    # the single read command that measures it.
    QUELLEN = ("production_state.txt", "nas_status.sh")

    # A version token in the API sense. `/bus/v1/messages`, `echo-v1` and
    # `Projektanweisung v1.2` are excluded by shape rather than by a list -
    # a list of exceptions is the thing that stops being maintained.
    VERSION = re.compile(r"(?<![/\w-])v(\d+)\b(?![\d.])")

    def test_no_status_section_states_a_version(self) -> None:
        offenders = []
        for path, heading in self.SECTIONS:
            treffer = sorted({m.group(0) for m in self.VERSION.finditer(section(path, heading))})
            if treffer:
                offenders.append(f"{path.name} :: {heading} -> {treffer}")
        self.assertEqual([], offenders,
                         "eine Versionsnummer im Statusabschnitt veraltet still - "
                         "auf production_state.txt verweisen statt sie zu nennen")

    def test_every_status_section_points_at_the_source(self) -> None:
        # Removing the number is only half of it. Without the pointer the
        # reader is left with no way to find out, and writes one back in.
        for path, heading in self.SECTIONS:
            with self.subTest(abschnitt=heading):
                body = section(path, heading)
                self.assertTrue(any(q in body for q in self.QUELLEN),
                                f"{path.name} :: {heading} nennt keine Quelle")

    def test_every_named_section_exists(self) -> None:
        # A renamed heading would silently switch this guard off - the same
        # failure as a checked-documents list nobody updates.
        for path, heading in self.SECTIONS:
            with self.subTest(abschnitt=heading):
                section(path, heading)

    def test_it_would_catch_the_lines_that_were_actually_wrong(self) -> None:
        for zeile in (
            "| Workforce-API (FastAPI, `v7`) | `nas-startup/workforce-api/` | laeuft |",
            "Die NAS laeuft auf **v8** mit Migrationen `001`-`003`.",
            "| Workforce-API `v7` (FastAPI) | laeuft, gesund | - |",
        ):
            with self.subTest(zeile=zeile[:40]):
                self.assertTrue(self.VERSION.search(zeile))

    def test_the_pattern_does_not_fire_on_paths_or_suffixes(self) -> None:
        # A guard that also flags `/bus/v1/messages` would be turned off within
        # a day, because every second sentence in this project names a route.
        for harmlos in (
            "Die Route `/bus/v1/messages` nimmt den Text entgegen.",
            "Sieben `/knowledge/v1`-Endpunkte liegen in `004`.",
            "Der Echo-Provider meldet sich als `echo-v1`.",
            "Projektanweisung v1.2 ist der gueltige Stand.",
            "Der Tag `produktiv-v8` bleibt als Rueckfallmarke stehen.",
        ):
            with self.subTest(satz=harmlos[:40]):
                self.assertIsNone(self.VERSION.search(harmlos))

    def test_the_section_reader_stops_at_the_next_heading(self) -> None:
        # If it read to the end of the file, every section would contain every
        # version in the document and the guard would be permanently red -
        # which is the same as switched off.
        body = section(ROOT / "HANDOVER.md", "### Systemzustand")
        self.assertIn("nas_status.sh", body)
        self.assertNotIn("### Technisch offen", body)
        self.assertLess(len(body), len((ROOT / "HANDOVER.md").read_text(encoding="utf-8")) / 2)


class TheAgentReadmeMatchesTheCodeTest(unittest.TestCase):
    """G-054: zwei sicherheitsrelevante Aussagen im Agenten-README waren falsch.

    Die Policy-Tabelle nannte den Betreff unter `METADATA_ONLY` - den Code hat
    `G-029` genau davon befreit, weil Menschen die eigentliche Anfrage in den
    Betreff schreiben. Und "Server-seitige Fallbacks sind aktiviert" stand da
    noch, obwohl `G-036` sie abgeschaltet hat.

    Beide Aussagen beschreiben Verhalten, das jemand beim Lesen fuer wahr
    haelt. Die erste haette einen Leser, der Code und Dokument angleicht, in
    die falsche Richtung geschickt: zurueck zu `G-029`.

    Die Abhilfe trennt Prosa von Zusicherung. Das README darf beschreiben, wie
    es will; die **maschinenlesbare Liste** darin ist die Aussage, und die
    wird hier gegen `data_boundary.py` gehalten. Ein Sprachvergleich waere
    hier untauglich - der korrigierte Satz lautet "Weder Text noch Betreff",
    nennt das Wort also und meint das Gegenteil.
    """

    README = NAS / "workforce-agent" / "README.md"

    def allowlist_from_code(self) -> dict[str, tuple[str, ...]]:
        quelle = (NAS / "workforce-agent" / "data_boundary.py").read_text(encoding="utf-8")
        block = quelle[quelle.index("_ALLOWED_FIELDS"):quelle.index("class DataBoundaryError")]
        out = {}
        for policy in ("METADATA_ONLY", "BODY", "FULL"):
            muster = re.compile(rf'"{policy}":\s*\(([^)]*)\)', re.S)
            treffer = muster.search(block)
            self.assertIsNotNone(treffer, f"{policy} nicht in data_boundary.py gefunden")
            felder = re.findall(r'"([a-z_]+)"', treffer.group(1))
            out[policy] = tuple(felder)
        return out

    def allowlist_from_readme(self) -> dict[str, tuple[str, ...]]:
        text = self.README.read_text(encoding="utf-8")
        out = {}
        for zeile in text.splitlines():
            teile = zeile.split(None, 1)
            if len(teile) == 2 and teile[0] in ("METADATA_ONLY", "BODY", "FULL"):
                out[teile[0]] = tuple(f.strip() for f in teile[1].split(","))
        return out

    def test_the_readme_names_all_three_policies(self) -> None:
        # Ohne das waere der Vergleich unten gruen ueber einer leeren Liste.
        self.assertEqual({"METADATA_ONLY", "BODY", "FULL"},
                         set(self.allowlist_from_readme()))

    def test_the_readme_list_matches_the_code(self) -> None:
        self.assertEqual(self.allowlist_from_code(), self.allowlist_from_readme())

    def test_the_subject_is_not_metadata(self) -> None:
        # Die Aussage, um die es bei G-029 ging, als eigener Test - damit sie
        # nicht in einem Gesamtvergleich untergeht.
        self.assertNotIn("subject", self.allowlist_from_code()["METADATA_ONLY"])

    def test_a_readme_that_drifted_would_be_caught(self) -> None:
        falsch = dict(self.allowlist_from_code())
        falsch["METADATA_ONLY"] = falsch["METADATA_ONLY"] + ("subject",)
        self.assertNotEqual(falsch, self.allowlist_from_readme())


class NoDocumentClaimsAWithdrawnFeatureTest(unittest.TestCase):
    """G-036 schaltete serverseitige Fallbacks ab; ein README sagte weiter ja."""

    def test_the_code_really_has_them_off(self) -> None:
        quelle = (NAS / "workforce-agent" / "providers.py").read_text(encoding="utf-8")
        self.assertIn("No server-side fallback", quelle)
        self.assertIn("max_retries: int = 0", quelle)

    BEHAUPTUNG = re.compile(
        r"Fallbacks?\s+(?:sind|ist)\s+aktivier|"
        r"aktivierte[rn]?\s+(?:server[- ]?seitige[rn]?\s+)?Fallback",
        re.IGNORECASE)

    # Ein Dokument, das den Befund beschreibt, muss den falschen Satz zitieren
    # duerfen - sonst ist die Regel, die daraus wurde, nicht aufschreibbar.
    # Zugelassen ist er nur mit Befundnummer oder Datum in unmittelbarer
    # Naehe, dasselbe Mass wie bei den Dateizahlen und bei der Bus-Adresse.
    ANKER = re.compile(r"`?G-0\d\d`?|\b20\d\d-\d\d-\d\d\b")
    REICHWEITE = 160

    def unverankert(self, text: str) -> bool:
        for treffer in self.BEHAUPTUNG.finditer(text):
            umfeld = text[max(0, treffer.start() - self.REICHWEITE):
                          treffer.end() + self.REICHWEITE]
            if not self.ANKER.search(umfeld):
                return True
        return False

    def test_no_document_says_they_are_on(self) -> None:
        offenders = [path.name for path, text in documents() if self.unverankert(text)]
        self.assertEqual([], offenders,
                         "G-036 hat serverseitige Fallbacks abgeschaltet")

    def test_a_bare_claim_is_still_caught(self) -> None:
        # Die Ausnahme darf nicht alles freikaufen.
        self.assertTrue(self.unverankert(
            "Server-seitige Fallbacks sind aktiviert, damit nichts liegen bleibt."))
        self.assertFalse(self.unverankert(
            "Frueher hiess es „Fallbacks sind aktiviert\u201c; `G-036` hat sie abgeschaltet."))

    def test_that_check_would_have_caught_the_real_sentence(self) -> None:
        # Der Satz, der bis zum 2026-09-02 im Agenten-README stand.
        echt = ("Server-seitige Fallbacks sind aktiviert, damit ein Grenzfall "
                "nicht stumm im Bus liegen bleibt.")
        behauptungen = re.compile(
            r"Fallbacks?\s+(?:sind|ist)\s+aktivier", re.IGNORECASE)
        self.assertTrue(behauptungen.search(echt))
        # Und die Verneinung darf durchkommen, sonst ist die Korrektur unschreibbar.
        self.assertIsNone(behauptungen.search("Server-seitige Fallbacks sind aus."))


if __name__ == "__main__":
    unittest.main()
