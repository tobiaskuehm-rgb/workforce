"""Local tests for the leftover cleanup. No network."""

from __future__ import annotations

import unittest

import leftover_cleanup
from test_core_roundtrip import ANASTASIA, GERD, KARL, build_clients, build_world


def seed_task(world, task_id, status, creator=KARL, owner=GERD):
    world["tasks"][task_id] = {
        "task_id": task_id, "creator_id": creator, "owner_id": owner,
        "task_status": status, "title": "Altlast", "completion_evidence": None,
    }


def seed_handoff(world, handoff_id, status, sender=GERD, recipient=ANASTASIA):
    world["handoffs"][handoff_id] = {
        "handoff_id": handoff_id, "sender_id": sender,
        "recipient_id": recipient, "handoff_status": status, "task_ref": None,
    }


class LeftoverCleanupTest(unittest.TestCase):
    def test_an_in_progress_task_is_walked_to_done_with_honest_evidence(self):
        world = build_world()
        seed_task(world, "T-A", "IN_PROGRESS")
        result = leftover_cleanup.run_cleanup(
            build_clients(world), run_id="L1",
            task_ids=("T-A",), handoff_ids=(),
        )
        self.assertEqual("PASS", result["result"])
        task = world["tasks"]["T-A"]
        self.assertEqual("DONE", task["task_status"])
        self.assertIn("Abgebrochener Testlauf", task["completion_evidence"])
        self.assertIn("Keine fachliche Arbeit", task["completion_evidence"])

    def test_a_pending_task_is_cancelled_rather_than_closed(self):
        # Cancelling is available out of PENDING and claims nothing was done -
        # the honest exit where the bus offers one.
        world = build_world()
        seed_task(world, "T-B", "PENDING")
        leftover_cleanup.run_cleanup(build_clients(world), run_id="L2",
                                     task_ids=("T-B",), handoff_ids=())
        self.assertEqual("CANCELLED", world["tasks"]["T-B"]["task_status"])
        self.assertIsNone(world["tasks"]["T-B"]["completion_evidence"])

    def test_a_pending_handoff_is_cancelled_by_its_sender(self):
        world = build_world()
        seed_handoff(world, "H-A", "PENDING")
        leftover_cleanup.run_cleanup(build_clients(world), run_id="L3",
                                     task_ids=(), handoff_ids=("H-A",))
        self.assertEqual("CANCELLED", world["handoffs"]["H-A"]["handoff_status"])

    def test_already_finished_records_are_left_alone(self):
        world = build_world()
        seed_task(world, "T-C", "DONE")
        seed_handoff(world, "H-B", "ACCEPTED")
        result = leftover_cleanup.run_cleanup(
            build_clients(world), run_id="L4",
            task_ids=("T-C",), handoff_ids=("H-B",),
        )
        self.assertEqual("PASS", result["result"])
        self.assertTrue(all(s["result"] == "SKIPPED" for s in result["steps"]))
        self.assertEqual("DONE", world["tasks"]["T-C"]["task_status"])
        self.assertEqual("ACCEPTED", world["handoffs"]["H-B"]["handoff_status"])

    def test_a_missing_record_is_skipped_not_failed(self):
        world = build_world()
        result = leftover_cleanup.run_cleanup(
            build_clients(world), run_id="L5",
            task_ids=("T-GONE",), handoff_ids=("H-GONE",),
        )
        self.assertEqual("PASS", result["result"])
        self.assertTrue(all(s["detail"] == "NOT_FOUND" for s in result["steps"]))

    def test_handoffs_are_cancelled_before_tasks_are_closed(self):
        # A handoff still hanging off a task that is already DONE would look
        # stranger than the mess we started with.
        world = build_world()
        seed_task(world, "T-D", "IN_PROGRESS")
        seed_handoff(world, "H-C", "PENDING")
        result = leftover_cleanup.run_cleanup(
            build_clients(world), run_id="L6",
            task_ids=("T-D",), handoff_ids=("H-C",),
        )
        order = [s["record"] for s in result["steps"]]
        self.assertLess(order.index("H-C"), order.index("T-D"))

    def test_closed_channel_blocks_before_anything_changes(self):
        world = build_world(channel_status="DISABLED")
        seed_task(world, "T-E", "IN_PROGRESS")
        result = leftover_cleanup.run_cleanup(
            build_clients(world), run_id="L7",
            task_ids=("T-E",), handoff_ids=(),
        )
        self.assertEqual("BLOCKED", result["result"])
        self.assertEqual("IN_PROGRESS", world["tasks"]["T-E"]["task_status"])

    def test_the_run_is_repeatable(self):
        world = build_world()
        seed_task(world, "T-F", "IN_PROGRESS")
        clients = build_clients(world)
        leftover_cleanup.run_cleanup(clients, run_id="L8",
                                     task_ids=("T-F",), handoff_ids=())
        second = leftover_cleanup.run_cleanup(clients, run_id="L8",
                                              task_ids=("T-F",), handoff_ids=())
        self.assertEqual("PASS", second["result"])
        self.assertEqual("ALREADY_DONE", second["steps"][0]["detail"])


if __name__ == "__main__":
    unittest.main()
