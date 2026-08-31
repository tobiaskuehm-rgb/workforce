"""Local tests for the contract test. No network.

The contract test exists to catch a divergence between bus_rules.py and the
real bus, so the property that matters is that it *would* catch one. Since
review finding G-014 there are three ways to diverge, and each needs its own
test:

  * the bus permits something the table denies
  * the bus refuses, but for the wrong reason - the failure mode that made the
    old version score a 401 or a 500 as a correct refusal
  * the bus refuses something the table permits

Plus a fourth, which is not a divergence but a hole: an allowed rule that the
run never exercised at all. A denial matrix alone cannot see it.
"""

from __future__ import annotations

import unittest
from unittest import mock

import bus_client
import bus_rules
import contract_test
from test_core_roundtrip import KARL, FakeBus, build_clients, build_world


class FaithfulBusTest(unittest.TestCase):
    def test_a_faithful_bus_produces_no_divergence(self):
        world = build_world()
        result = contract_test.run_contract_test(build_clients(world), run_id="C1")
        self.assertEqual([], result["divergences"])
        self.assertEqual("PASS", result["result"])
        self.assertGreater(result["deny"]["checked"], 100,
                           "the denial matrix should be substantial")

    def test_every_allowed_rule_is_exercised_positively(self):
        # The heart of G-014: 107 refusals proved the bus says no. Nothing in
        # that number said it says yes where it must.
        world = build_world()
        result = contract_test.run_contract_test(build_clients(world), run_id="C2")
        self.assertEqual({}, result["uncovered_allow"])
        self.assertEqual("17/17", result["allow"]["pairs_covered"]["TASK"])
        self.assertEqual("5/5", result["allow"]["pairs_covered"]["HANDOFF"])
        self.assertEqual(result["allow"]["checked"], result["allow"]["matched"])

    def test_the_two_halves_are_reported_apart(self):
        world = build_world()
        result = contract_test.run_contract_test(build_clients(world), run_id="C3")
        for half in ("deny", "allow"):
            self.assertIn("checked", result[half])
            self.assertIn("matched", result[half])
        self.assertIn("wrong_reason", result["deny"])
        self.assertIn("wrongly_allowed", result["deny"])

    def test_every_record_ends_in_a_final_state(self):
        # A test that litters is a test nobody runs twice, and the bus refuses
        # to cancel anything past PENDING - litter could not be cleared later.
        world = build_world()
        contract_test.run_contract_test(build_clients(world), run_id="C4")
        self.assertEqual(
            {"DONE", "CANCELLED"},
            {t["task_status"] for t in world["tasks"].values()},
        )
        self.assertEqual(
            {"ACCEPTED", "REJECTED", "CANCELLED"},
            {h["handoff_status"] for h in world["handoffs"].values()},
        )

    def test_the_footprint_is_the_documented_one(self):
        world = build_world()
        contract_test.run_contract_test(build_clients(world), run_id="C5")
        self.assertEqual(len(contract_test.TASK_PLANS), len(world["tasks"]))
        self.assertEqual(len(contract_test.HANDOFF_PLANS), len(world["handoffs"]))


class DivergenceIsReportedTest(unittest.TestCase):
    def test_a_permissive_bus_is_reported(self):
        world = build_world()
        clients = build_clients(world)

        class TooPermissive(FakeBus):
            def transition_task(self, task_id, *, new_status, request_id,
                                completion_evidence=None):
                task = self.world["tasks"][task_id]
                task["task_status"] = new_status
                return task

        clients["anastasia"] = TooPermissive(world, "PEO-001")
        result = contract_test.run_contract_test(clients, run_id="D1")
        self.assertEqual("FAIL", result["result"])
        self.assertGreater(result["deny"]["wrongly_allowed"], 0)
        self.assertTrue(any(d.get("identity") == "PEO-001" for d in result["divergences"]))

    def test_a_refusal_for_the_wrong_reason_is_not_a_pass(self):
        # This is the G-014 case exactly. The old version asked only whether a
        # BusError came back, so a bus that had fallen over answered every
        # denied transition with 500 and scored a clean sweep.
        world = build_world()
        clients = build_clients(world)

        class Broken(FakeBus):
            def transition_task(self, task_id, *, new_status, request_id,
                                completion_evidence=None):
                raise bus_client.BusError("BUS_DATABASE_UNAVAILABLE", status=503)

        clients["anastasia"] = Broken(world, "PEO-001")
        result = contract_test.run_contract_test(clients, run_id="D2")
        self.assertEqual("FAIL", result["result"])
        self.assertGreater(result["deny"]["wrong_reason"], 0)
        self.assertEqual(0, result["deny"]["wrongly_allowed"])
        wrong = [d for d in result["divergences"] if d["observed"] == "WRONG_REASON"]
        self.assertEqual(503, wrong[0]["status"])
        self.assertEqual("BUS_DATABASE_UNAVAILABLE", wrong[0]["detail"])

    def test_an_expired_credential_is_not_a_pass_either(self):
        world = build_world()
        clients = build_clients(world)

        class Unauthorised(FakeBus):
            def transition_handoff(self, handoff_id, *, new_status, request_id,
                                   response_note=None):
                raise bus_client.BusError("BUS_AUTH_FAILED", status=401)

        clients["karl"] = Unauthorised(world, KARL)
        result = contract_test.run_contract_test(clients, run_id="D3")
        self.assertEqual("FAIL", result["result"])
        self.assertGreater(result["deny"]["wrong_reason"], 0)

    def test_the_right_identifier_with_the_wrong_status_is_not_a_pass(self):
        # Both halves of the expectation matter. A 200-shaped refusal or a
        # denial arriving as 400 would mean the API mapping changed.
        world = build_world()
        clients = build_clients(world)

        class WrongStatus(FakeBus):
            def transition_task(self, task_id, *, new_status, request_id,
                                completion_evidence=None):
                raise bus_client.BusError("BUS_TASK_TRANSITION_DENIED", status=400)

        clients["anastasia"] = WrongStatus(world, "PEO-001")
        result = contract_test.run_contract_test(clients, run_id="D4")
        self.assertGreater(result["deny"]["wrong_reason"], 0)

    def test_a_bus_that_refuses_an_allowed_transition_is_reported(self):
        world = build_world()
        clients = build_clients(world)

        class TooStrict(FakeBus):
            def transition_task(self, task_id, *, new_status, request_id,
                                completion_evidence=None):
                if new_status == "HOLD":
                    raise bus_client.BusError("BUS_TASK_TRANSITION_DENIED", status=403)
                return super().transition_task(
                    task_id, new_status=new_status, request_id=request_id,
                    completion_evidence=completion_evidence)

        clients["gerd"] = TooStrict(world, "AI-ENG-001")
        result = contract_test.run_contract_test(clients, run_id="D5")
        self.assertEqual("FAIL", result["result"])
        refused = [d for d in result["divergences"]
                   if d["predicted"] == "ALLOW" and d["observed"] == "DENY"]
        self.assertTrue(refused)
        self.assertNotEqual({}, result["uncovered_allow"])


class CoverageGapIsReportedTest(unittest.TestCase):
    def test_a_shortened_plan_leaves_the_run_failing(self):
        # Not a bus defect but a test defect: if a future edit drops a walk,
        # the run must not report PASS on a partial matrix. That silent
        # narrowing is how "107/107" came to sound complete.
        world = build_world()
        short = (contract_test.TASK_PLANS[0],)
        with mock.patch.object(contract_test, "TASK_PLANS", short):
            result = contract_test.run_contract_test(build_clients(world), run_id="G1")
        self.assertEqual("FAIL", result["result"])
        self.assertIn("TASK", result["uncovered_allow"])
        self.assertIn(["PENDING", "CANCELLED"], result["uncovered_allow"]["TASK"])

    def test_the_plans_agree_with_the_table(self):
        # A plan step the table calls denied would be scored as a divergence
        # of the bus, when it is really a defect in this file. Catch it here,
        # locally, rather than on the NAS with live credentials.
        world = build_world()
        result = contract_test.run_contract_test(build_clients(world), run_id="G2")
        self.assertFalse([d for d in result["divergences"]
                          if d.get("detail") == "PLAN_CONTRADICTS_TABLE"])

    def test_the_expected_denial_matches_the_transcription(self):
        # The expectation is hard-coded; if the migration ever raises another
        # identifier, this pins where to look.
        self.assertEqual(("BUS_TASK_TRANSITION_DENIED", 403),
                         contract_test.DENIAL_EXPECTED["TASK"])
        self.assertEqual(("BUS_HANDOFF_TRANSITION_DENIED", 403),
                         contract_test.DENIAL_EXPECTED["HANDOFF"])
        self.assertIn("DONE", bus_rules.TASK_STATUSES)
        self.assertIn("REJECTED", bus_rules.HANDOFF_STATUSES)


class ChannelGateTest(unittest.TestCase):
    def test_closed_channel_blocks(self):
        world = build_world(channel_status="DISABLED")
        result = contract_test.run_contract_test(build_clients(world), run_id="C6")
        self.assertEqual("BLOCKED", result["result"])
        self.assertEqual({}, world["tasks"])


if __name__ == "__main__":
    unittest.main()
