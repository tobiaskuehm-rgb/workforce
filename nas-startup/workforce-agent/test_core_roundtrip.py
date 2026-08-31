"""Local tests for the ENG-008 core roundtrip. No network, no credentials.

The fake bus below enforces the same rules the real one does - owner-only task
transitions, recipient-only handoff decisions, evidence required for DONE. A
fake that says yes to everything would make the negative cases pass while
proving nothing, which is worse than having no test.
"""

from __future__ import annotations

import unittest

import bus_client
import core_roundtrip

KARL, GERD, ANASTASIA = "SAO-001", "AI-ENG-001", "PEO-001"


class FakeBus:
    """One instance per identity, sharing one world."""

    def __init__(self, world: dict, identity: str):
        self.world = world
        self.identity = identity

    # -- read ---------------------------------------------------------------
    def status(self):
        return {"channel_status": self.world["channel_status"]}

    def tasks(self, scope="OWNED", limit=50):
        if scope == "OWNED":
            return [t for t in self.world["tasks"].values() if t["owner_id"] == self.identity]
        if scope == "CREATED":
            return [t for t in self.world["tasks"].values() if t["creator_id"] == self.identity]
        return list(self.world["tasks"].values())

    def handoffs(self, scope="INBOX", limit=50):
        key = "recipient_id" if scope == "INBOX" else "sender_id"
        return [h for h in self.world["handoffs"].values() if h[key] == self.identity]

    # -- write --------------------------------------------------------------
    def create_task(self, *, task_id, owner_id, title, expected_output,
                    source_ref, request_id, idempotency_key, task_status="PENDING",
                    priority="MEDIUM"):
        existing = self.world["tasks"].get(task_id)
        if existing:
            return existing  # idempotent replay
        task = {
            "task_id": task_id, "creator_id": self.identity, "owner_id": owner_id,
            "task_status": "OPEN" if self.identity == KARL else task_status,
            "title": title, "completion_evidence": None,
        }
        self.world["tasks"][task_id] = task
        self.world["events"].append(
            {"type": "TASK", "key": task_id, "actor": self.identity, "request_id": request_id}
        )
        return task

    def transition_task(self, task_id, *, new_status, request_id,
                        completion_evidence=None):
        task = self.world["tasks"].get(task_id)
        if task is None:
            raise bus_client.BusError("BUS_TASK_NOT_FOUND", status=404)

        # Owner drives up to REVIEW; only the creator closes as DONE.
        allowed = task["owner_id"] if new_status != "DONE" else task["creator_id"]
        if self.identity != allowed:
            raise bus_client.BusError("BUS_TASK_TRANSITION_DENIED", status=403)
        if new_status == task["task_status"]:
            raise bus_client.BusError("BUS_TASK_TRANSITION_DENIED", status=403)
        if new_status == "DONE" and not completion_evidence:
            raise bus_client.BusError("BUS_TASK_COMPLETION_EVIDENCE_REQUIRED", status=400)

        task["task_status"] = new_status
        task["completion_evidence"] = completion_evidence
        self.world["events"].append(
            {"type": "TASK", "key": task_id, "actor": self.identity, "request_id": request_id}
        )
        return task

    def create_handoff(self, *, handoff_id, recipient_id, input_summary,
                       expected_output, source_ref, request_id, idempotency_key,
                       task_ref=None, handoff_status="PENDING",
                       risks_and_assumptions=None):
        existing = self.world["handoffs"].get(handoff_id)
        if existing:
            return existing
        handoff = {
            "handoff_id": handoff_id, "sender_id": self.identity,
            "recipient_id": recipient_id, "handoff_status": handoff_status,
            "task_ref": task_ref,
        }
        self.world["handoffs"][handoff_id] = handoff
        self.world["events"].append(
            {"type": "HANDOFF", "key": handoff_id, "actor": self.identity,
             "request_id": request_id}
        )
        return handoff

    def transition_handoff(self, handoff_id, *, new_status, request_id,
                           response_note=None):
        handoff = self.world["handoffs"].get(handoff_id)
        if handoff is None:
            raise bus_client.BusError("BUS_HANDOFF_NOT_FOUND", status=404)
        # Only the recipient decides.
        if self.identity != handoff["recipient_id"]:
            raise bus_client.BusError("BUS_HANDOFF_TRANSITION_DENIED", status=403)
        handoff["handoff_status"] = new_status
        self.world["events"].append(
            {"type": "HANDOFF", "key": handoff_id, "actor": self.identity,
             "request_id": request_id}
        )
        return handoff

    def send_message(self, *, recipient_id, subject, body, parent_message_id,
                     request_id, idempotency_key, **kwargs):
        message_id = f"MSG-{len(self.world['messages']) + 1:032d}"
        self.world["messages"][message_id] = {
            "message_id": message_id, "sender_id": self.identity,
            "recipient_id": recipient_id, "subject": subject,
        }
        self.world["events"].append(
            {"type": "MESSAGE", "key": message_id, "actor": self.identity,
             "request_id": request_id}
        )
        return self.world["messages"][message_id]


def build_world(channel_status="TESTING"):
    return {
        "channel_status": channel_status,
        "tasks": {}, "handoffs": {}, "messages": {}, "events": [],
    }


def build_clients(world):
    return {
        "karl": FakeBus(world, KARL),
        "gerd": FakeBus(world, GERD),
        "anastasia": FakeBus(world, ANASTASIA),
    }


class CoreRoundtripTest(unittest.TestCase):
    def test_full_roundtrip_passes(self):
        world = build_world()
        result = core_roundtrip.run_core_roundtrip(build_clients(world), run_id="T1")

        failed = [s for s in result["transcript"] if s["result"] == "FAIL"]
        self.assertEqual([], failed, f"unexpected failures: {failed}")
        self.assertEqual("PASS", result["result"])

    def test_the_dec_027_sequence_is_actually_walked(self):
        world = build_world()
        result = core_roundtrip.run_core_roundtrip(build_clients(world), run_id="T2")
        steps = [s["step"] for s in result["transcript"]]

        for required in [
            "karl_creates_task",           # Task
            "gerd_sees_task",              # → Mitarbeiter A
            "gerd_reports_result",         # → Ergebnis
            "gerd_creates_handoff",        # → Handoff
            "anastasia_sees_handoff",      # → Mitarbeiter B
            "anastasia_accepts_handoff",   # → ACCEPTED
            "anastasia_reports_result",    # → Bearbeitung, Ergebnis
            "gerd_moves_task_review",
            "karl_closes_task",            # → DONE
        ]:
            self.assertIn(required, steps)

        # Order matters: the handoff cannot precede the task.
        self.assertLess(steps.index("karl_creates_task"), steps.index("gerd_creates_handoff"))
        self.assertLess(steps.index("anastasia_accepts_handoff"), steps.index("karl_closes_task"))

    def test_task_ends_as_done_with_evidence(self):
        world = build_world()
        core_roundtrip.run_core_roundtrip(build_clients(world), run_id="T3")
        task = world["tasks"]["ENG-CORE-T3"]
        self.assertEqual("DONE", task["task_status"])
        self.assertIn("Core-Roundtrip T3", task["completion_evidence"])

    def test_rejected_path_is_exercised(self):
        world = build_world()
        core_roundtrip.run_core_roundtrip(build_clients(world), run_id="T4")
        self.assertEqual("REJECTED", world["handoffs"]["HO-CORE-T4-REJ"]["handoff_status"])

    def test_missing_permission_cases_are_refused(self):
        world = build_world()
        result = core_roundtrip.run_core_roundtrip(build_clients(world), run_id="T5")
        steps = {s["step"]: s for s in result["transcript"]}

        for step in ("third_party_cannot_decide_handoff",
                     "non_owner_cannot_transition_task",
                     "done_without_evidence_refused"):
            self.assertEqual("PASS", steps[step]["result"], step)

    def test_a_permissive_bus_makes_the_negative_cases_fail(self):
        # The property that makes the negative cases worth anything: if the bus
        # stopped enforcing, the run has to notice.
        world = build_world()
        clients = build_clients(world)

        class Permissive(FakeBus):
            def transition_handoff(self, handoff_id, *, new_status, request_id,
                                   response_note=None):
                handoff = self.world["handoffs"][handoff_id]
                handoff["handoff_status"] = new_status
                return handoff

        clients["karl"] = Permissive(world, KARL)
        result = core_roundtrip.run_core_roundtrip(clients, run_id="T6")
        failed = {s["step"] for s in result["transcript"] if s["result"] == "FAIL"}
        self.assertIn("third_party_cannot_decide_handoff", failed)
        self.assertEqual("FAIL", result["result"])

    def test_replay_of_the_task_is_idempotent(self):
        world = build_world()
        result = core_roundtrip.run_core_roundtrip(build_clients(world), run_id="T7")
        steps = {s["step"]: s for s in result["transcript"]}
        self.assertEqual("PASS", steps["task_replay_is_idempotent"]["result"])
        self.assertEqual(1, len(world["tasks"]), "replay must not create a second task")

    def test_closed_channel_blocks_before_anything_is_written(self):
        world = build_world(channel_status="DISABLED")
        result = core_roundtrip.run_core_roundtrip(build_clients(world), run_id="T8")
        self.assertEqual("BLOCKED", result["result"])
        self.assertEqual({}, world["tasks"])
        self.assertEqual({}, world["handoffs"])

    def test_a_failing_step_stops_the_run_and_is_reported(self):
        world = build_world()
        clients = build_clients(world)

        def refuse(**kwargs):
            raise bus_client.BusError("BUS_TASK_ROUTE_DENIED", status=403)

        clients["karl"].create_task = refuse
        result = core_roundtrip.run_core_roundtrip(clients, run_id="T9")
        self.assertEqual("FAIL", result["result"])
        self.assertEqual("karl_creates_task", result["transcript"][-1]["step"])

    def test_every_step_reaches_the_audit_trail(self):
        world = build_world()
        core_roundtrip.run_core_roundtrip(build_clients(world), run_id="TA")
        request_ids = {e["request_id"] for e in world["events"]}
        # Each write carries its own request id, which is what makes the run
        # reconstructable from the audit afterwards.
        self.assertTrue(all(r.startswith("CORE-TA-") for r in request_ids))
        self.assertGreaterEqual(len(request_ids), 8)


class ExpectRefusalTest(unittest.TestCase):
    def test_a_refusal_for_the_wrong_reason_counts_as_failure(self):
        transcript = core_roundtrip.Transcript()

        def wrong_reason():
            raise bus_client.BusError("BUS_ROUTE_DENIED", status=403)

        core_roundtrip.expect_refusal(
            transcript, "case", wrong_reason,
            expected_status=403, expected_details=("BUS_ACK_DENIED",),
        )
        self.assertEqual("FAIL", transcript.steps[0]["result"])

    def test_an_action_that_succeeds_counts_as_failure(self):
        transcript = core_roundtrip.Transcript()
        core_roundtrip.expect_refusal(
            transcript, "case", lambda: {"ok": True}, expected_status=403,
        )
        self.assertEqual("FAIL", transcript.steps[0]["result"])
        self.assertEqual("NOT_REFUSED", transcript.steps[0]["detail"])


if __name__ == "__main__":
    unittest.main()
