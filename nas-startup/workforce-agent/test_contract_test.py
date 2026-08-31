"""Local tests for the contract test. No network.

The contract test exists to catch a divergence between bus_rules.py and the
real bus. So the property that matters here is that it *would* catch one: a
fake that grants something the table denies has to be reported.
"""

from __future__ import annotations

import unittest

import contract_test
from test_core_roundtrip import KARL, FakeBus, build_clients, build_world


class ContractTestTest(unittest.TestCase):
    def test_a_faithful_bus_produces_no_divergence(self):
        world = build_world()
        result = contract_test.run_contract_test(build_clients(world), run_id="C1")
        self.assertEqual([], result["divergences"])
        self.assertEqual("PASS", result["result"])
        self.assertGreater(result["checks_total"], 40,
                           "the denial matrix should be substantial")

    def test_the_task_ends_in_a_clean_state(self):
        # A test that litters is a test nobody runs twice. The bus refuses to
        # cancel anything past PENDING, so the walk has to end at DONE.
        world = build_world()
        contract_test.run_contract_test(build_clients(world), run_id="C2")
        self.assertEqual("DONE", world["tasks"]["ENG-CONTRACT-C2"]["task_status"])
        self.assertEqual("ACCEPTED", world["handoffs"]["HO-CONTRACT-C2"]["handoff_status"])

    def test_only_two_records_are_created(self):
        world = build_world()
        contract_test.run_contract_test(build_clients(world), run_id="C3")
        self.assertEqual(1, len(world["tasks"]))
        self.assertEqual(1, len(world["handoffs"]))

    def test_a_permissive_bus_is_reported_as_divergence(self):
        # The whole point: if the real bus allowed something the table denies,
        # this test has to say so rather than pass quietly.
        world = build_world()
        clients = build_clients(world)

        class TooPermissive(FakeBus):
            def transition_task(self, task_id, *, new_status, request_id,
                                completion_evidence=None):
                task = self.world["tasks"][task_id]
                task["task_status"] = new_status
                return task

        clients["anastasia"] = TooPermissive(world, "PEO-001")
        result = contract_test.run_contract_test(clients, run_id="C4")
        self.assertEqual("FAIL", result["result"])
        self.assertTrue(any(d["identity"] == "PEO-001" for d in result["divergences"]))

    def test_a_divergence_names_what_diverged(self):
        world = build_world()
        clients = build_clients(world)

        class TooPermissive(FakeBus):
            def transition_handoff(self, handoff_id, *, new_status, request_id,
                                   response_note=None):
                handoff = self.world["handoffs"][handoff_id]
                handoff["handoff_status"] = new_status
                return handoff

        clients["karl"] = TooPermissive(world, KARL)
        result = contract_test.run_contract_test(clients, run_id="C5")
        divergence = result["divergences"][0]
        for field in ("kind", "identity", "from", "to", "predicted", "observed"):
            self.assertIn(field, divergence)
        self.assertEqual("DENY", divergence["predicted"])
        self.assertEqual("ALLOW", divergence["observed"])

    def test_closed_channel_blocks(self):
        world = build_world(channel_status="DISABLED")
        result = contract_test.run_contract_test(build_clients(world), run_id="C6")
        self.assertEqual("BLOCKED", result["result"])
        self.assertEqual({}, world["tasks"])


if __name__ == "__main__":
    unittest.main()
