"""Tests for the transcribed bus rules.

These are not tests of the bus - the bus is the authority and cannot be
reached from here. They are tests of the *transcription*: that the table says
what the migration says, and in particular that it still says the three things
that cost four attempts at the core roundtrip on 2026-08-31.

If the migration changes, these tests keep passing while being wrong. That is
the honest limit of a transcription, and the reason each rule names its source
line. A future contract test against the real bus would close it; until then,
the rules are checked here and proven in the roundtrip evidence.
"""

from __future__ import annotations

import unittest

import bus_rules

KARL, GERD, ANASTASIA, THORSTEN = "SAO-001", "AI-ENG-001", "PEO-001", "RAS-001"


class TaskRuleTest(unittest.TestCase):
    def task_may(self, identity, current, target, creator=KARL, owner=GERD):
        return bus_rules.may_transition_task(
            identity, creator_id=creator, owner_id=owner,
            current=current, target=target,
        )

    def test_only_the_coordinator_opens_a_pending_task(self):
        # Attempt one of the roundtrip died here: the owner cannot lift his
        # own task out of PENDING.
        self.assertTrue(self.task_may(KARL, "PENDING", "OPEN"))
        self.assertFalse(self.task_may(GERD, "PENDING", "OPEN"))
        self.assertFalse(self.task_may(ANASTASIA, "PENDING", "OPEN"))

    def test_coordination_only_reaches_the_named_owners(self):
        self.assertTrue(self.task_may(KARL, "PENDING", "OPEN", owner=GERD))
        self.assertTrue(self.task_may(KARL, "PENDING", "OPEN", owner=THORSTEN))
        self.assertFalse(
            self.task_may(KARL, "PENDING", "OPEN", owner="EAC-001"),
            "the rule names three owners, not everyone",
        )

    def test_the_owner_works_up_to_review(self):
        for target in ("IN_PROGRESS", "BLOCKED", "HOLD", "REVIEW"):
            with self.subTest(target=target):
                self.assertTrue(self.task_may(GERD, "OPEN", target))
        self.assertFalse(self.task_may(GERD, "OPEN", "DONE"),
                         "the owner never closes a task")

    def test_only_the_creator_closes(self):
        self.assertTrue(self.task_may(KARL, "REVIEW", "DONE"))
        self.assertFalse(self.task_may(GERD, "REVIEW", "DONE"))
        self.assertFalse(self.task_may(ANASTASIA, "REVIEW", "DONE"))

    def test_the_creator_may_send_a_review_back(self):
        self.assertTrue(self.task_may(KARL, "REVIEW", "IN_PROGRESS"))

    def test_cancelling_is_only_possible_while_pending(self):
        # Abandoned work cannot be swept away silently - the leftover
        # IN_PROGRESS tasks from the failed roundtrip attempts are a direct
        # consequence of this rule, and the rule is right.
        self.assertTrue(self.task_may(KARL, "PENDING", "CANCELLED"))
        self.assertFalse(self.task_may(KARL, "IN_PROGRESS", "CANCELLED"))
        self.assertFalse(self.task_may(GERD, "IN_PROGRESS", "CANCELLED"))

    def test_an_outsider_may_do_nothing(self):
        for current, target in (("PENDING", "OPEN"), ("OPEN", "IN_PROGRESS"),
                                ("REVIEW", "DONE")):
            with self.subTest(current=current, target=target):
                self.assertFalse(self.task_may(THORSTEN, current, target))

    def test_one_identity_can_hold_two_roles(self):
        # Karl creating a task he owns himself is both creator and owner.
        self.assertTrue(self.task_may(KARL, "OPEN", "IN_PROGRESS",
                                      creator=KARL, owner=KARL))
        self.assertTrue(self.task_may(KARL, "REVIEW", "DONE",
                                      creator=KARL, owner=KARL))


class HandoffRuleTest(unittest.TestCase):
    def handoff_may(self, identity, current, target, sender=GERD, recipient=ANASTASIA):
        return bus_rules.may_transition_handoff(
            identity, sender_id=sender, recipient_id=recipient,
            current=current, target=target,
        )

    def test_the_sender_opens_a_pending_handoff(self):
        # Attempt two died here: the recipient cannot decide a PENDING handoff.
        self.assertTrue(self.handoff_may(GERD, "PENDING", "OPEN"))
        self.assertFalse(self.handoff_may(ANASTASIA, "PENDING", "OPEN"))

    def test_the_recipient_decides_an_open_handoff(self):
        self.assertTrue(self.handoff_may(ANASTASIA, "OPEN", "ACCEPTED"))
        self.assertTrue(self.handoff_may(ANASTASIA, "OPEN", "REJECTED"))
        self.assertFalse(self.handoff_may(GERD, "OPEN", "ACCEPTED"),
                         "the sender does not accept his own handoff")

    def test_a_third_party_decides_nothing(self):
        self.assertFalse(self.handoff_may(KARL, "OPEN", "ACCEPTED"))
        self.assertFalse(self.handoff_may(KARL, "OPEN", "REJECTED"))

    def test_a_decided_handoff_is_final(self):
        for current in ("ACCEPTED", "REJECTED", "CANCELLED"):
            for identity in (GERD, ANASTASIA, KARL):
                with self.subTest(current=current, identity=identity):
                    self.assertFalse(self.handoff_may(identity, current, "OPEN"))

    def test_only_the_sender_cancels(self):
        self.assertTrue(self.handoff_may(GERD, "OPEN", "CANCELLED"))
        self.assertFalse(self.handoff_may(ANASTASIA, "OPEN", "CANCELLED"))


class TranscriptionQualityTest(unittest.TestCase):
    """Guardrails on the table itself, so it stays usable as documentation."""

    def test_every_rule_names_its_source(self):
        for rule in bus_rules.TASK_RULES + bus_rules.HANDOFF_RULES:
            with self.subTest(rule=rule):
                self.assertIn("002_workforce_bus.sql", rule.source)

    def test_no_rule_is_empty(self):
        for rule in bus_rules.TASK_RULES + bus_rules.HANDOFF_RULES:
            with self.subTest(rule=rule):
                self.assertTrue(rule.from_status)
                self.assertTrue(rule.to_status)

    def test_same_status_is_a_conflict_not_a_permission_question(self):
        # Attempt three died here: a negative case asked for the status a
        # record already had and got 409 instead of the 403 it was testing for.
        self.assertTrue(bus_rules.SAME_STATUS_IS_CONFLICT)

class DriftGuardTest(unittest.TestCase):
    """The failure mode of a transcription is not being wrong from the start.

    It is quietly becoming wrong later, when someone edits the migration and
    the local suite keeps passing. These tests turn that into a loud failure.
    """

    def test_the_transcription_still_matches_the_migration(self):
        for name, expected in bus_rules.TRANSCRIBED_FROM.items():
            with self.subTest(function=name):
                actual = bus_rules.sql_function_digest(name)
                self.assertIsNotNone(
                    actual,
                    f"{name} not found in {bus_rules.SQL_SOURCE} — did the file move?",
                )
                self.assertEqual(
                    expected, actual,
                    f"\n\n  workforce.{name} in 002_workforce_bus.sql has changed since"
                    f"\n  bus_rules.py was written from it. The rules in this module may"
                    f"\n  now be wrong while every other test still passes.\n"
                    f"\n  What to do, in order:"
                    f"\n    1. Read the changed function."
                    f"\n    2. Update TASK_RULES / HANDOFF_RULES to match it."
                    f"\n    3. Run contract_test.py against a live bus."
                    f"\n    4. Only then record the new digest in TRANSCRIBED_FROM.\n"
                    f"\n  Updating the digest without step 1 turns this guard into a"
                    f"\n  rubber stamp.\n",
                )

    def test_the_guard_notices_a_changed_function(self):
        # The property that matters: if the source changes, this fails. Without
        # this test the guard could be silently broken and nobody would know.
        import tempfile
        from pathlib import Path

        original = bus_rules.sql_function_body("bus_transition_task")
        self.assertIsNotNone(original)

        with tempfile.TemporaryDirectory() as tempdir:
            altered = Path(tempdir) / "migration.sql"
            altered.write_text(
                original.replace("v_allowed :=", "v_allowed := TRUE OR"),
                encoding="utf-8",
            )
            digest = bus_rules.sql_function_digest("bus_transition_task", altered)

        self.assertIsNotNone(digest)
        self.assertNotEqual(
            bus_rules.TRANSCRIBED_FROM["bus_transition_task"], digest,
            "a changed permission condition must change the fingerprint",
        )

    def test_a_missing_source_is_reported_rather_than_passing(self):
        from pathlib import Path

        self.assertIsNone(
            bus_rules.sql_function_digest("bus_transition_task", Path("/nirgendwo.sql"))
        )

    def test_every_transcribed_function_is_actually_used(self):
        # A fingerprint for a function nothing transcribes would be noise, and
        # a transcribed function without one would be unguarded.
        sources = " ".join(
            rule.source for rule in bus_rules.TASK_RULES + bus_rules.HANDOFF_RULES
        )
        for name in bus_rules.TRANSCRIBED_FROM:
            with self.subTest(function=name):
                self.assertIn(name, sources)


if __name__ == "__main__":
    unittest.main()
