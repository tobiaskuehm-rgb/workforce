"""Local run of the integrated worker-core test. No network, no credentials.

The bus double here is deliberately closer to the real bus than the unit-test
fakes elsewhere in this package, because the properties under test live exactly
in the places a loose fake papers over:

  * `send_message` is idempotent on (sender, idempotency key), the way the real
    bus is - it derives the message id from them. A fake that handed out a
    fresh id per call would hide the duplicate reply that a resumed run must
    not produce, which is the single most important thing this test checks.
  * `acknowledge` moves a message from DELIVERED to ACCEPTED, so `poll_once()`
    stops seeing it. A fake that only recorded acknowledgements would let a
    handled message be handled again and call that a pass.
  * The inbox is filtered by recipient and carries `delivery_status`, so "is it
    still pending in the bus?" is answered by the bus.

That is the lesson from the four failed roundtrip attempts on 2026-08-31: a
double built from what its author assumes confirms the assumption.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import bus_client
import providers
import worker_core_test

AGENT = "AGENT-ENG-001"
REQUESTER = "SAO-001"


class IntegratedFakeBus:
    """One shared world; one client instance per identity."""

    def __init__(self, world: dict, identity: str):
        self.world = world
        self.identity = identity

    def status(self):
        return {"channel_status": self.world["channel_status"]}

    def inbox(self, limit: int = 25):
        return [
            dict(m) for m in self.world["messages"].values()
            if m["recipient_id"] == self.identity
        ][:limit]

    def acknowledge(self, message_id: str, *, decision: str, note: str,
                    request_id: str):
        message = self.world["messages"].get(message_id)
        if message is None:
            raise bus_client.BusError("BUS_RECORD_NOT_FOUND", status=404)
        if message["recipient_id"] != self.identity:
            raise bus_client.BusError("BUS_ACK_DENIED", status=403)
        if message["delivery_status"] != "DELIVERED":
            # The real bus refuses a second final acknowledgement rather than
            # accepting it silently.
            raise bus_client.BusError("BUS_ACK_ALREADY_FINAL", status=409)
        message["delivery_status"] = "ACCEPTED"
        self.world["acks"].append({"message_id": message_id, "decision": decision})
        return dict(message)

    def send_message(self, *, recipient_id, subject, body, parent_message_id,
                     request_id, idempotency_key, task_ref=None, **kwargs):
        if recipient_id == self.identity:
            # The schema forbids a self-route outright, before the allowlist is
            # even consulted. A fake that allowed it would let the check that
            # proves the routing control pass without proving anything.
            raise bus_client.BusError("BUS_SELF_ROUTE_DENIED", status=403)
        key = (self.identity, idempotency_key)
        if key in self.world["by_idempotency"]:
            return dict(self.world["messages"][self.world["by_idempotency"][key]])
        message_id = f"MSG-{len(self.world['messages']) + 1:032d}"
        self.world["by_idempotency"][key] = message_id
        self.world["messages"][message_id] = {
            "message_id": message_id,
            "sender_id": self.identity,
            "recipient_id": recipient_id,
            "subject": subject,
            "body": body,
            "parent_message_id": parent_message_id,
            "task_ref": task_ref,
            "action_class": kwargs.get("action_class", "INTERNAL_COMMUNICATION"),
            "delivery_status": "DELIVERED",
        }
        return dict(self.world["messages"][message_id])


def build_world(channel_status="TESTING"):
    return {
        "channel_status": channel_status,
        "messages": {},
        "by_idempotency": {},
        "acks": [],
    }


def build_harness(world, state_path, task_ref="ENG-WORKERCORE-T1"):
    agent = IntegratedFakeBus(world, AGENT)
    requester = IntegratedFakeBus(world, REQUESTER)

    def send_request(*, subject, body, key):
        sent = requester.send_message(
            recipient_id=AGENT, subject=subject, body=body,
            parent_message_id=None, task_ref=task_ref,
            request_id=f"WORKERCORE-{key}",
            idempotency_key=f"IDEM-WORKERCORE-{key}",
        )
        return str(sent["message_id"])

    return worker_core_test.Harness(
        agent_client=agent,
        send_request=send_request,
        bus_messages=lambda: [dict(m) for m in world["messages"].values()],
        state_path=state_path,
    )


class WorkerCoreTest(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.state_path = Path(self._temp.name) / "worker_core.sqlite3"
        self.world = build_world()

    def tearDown(self):
        self._temp.cleanup()

    def run_it(self, run_id="T1"):
        return worker_core_test.run_worker_core_test(
            build_harness(self.world, self.state_path), run_id=run_id
        )

    def test_the_whole_run_passes(self):
        result = self.run_it()
        self.assertEqual([], result["divergences"],
                         f"unexpected failures: {result['divergences']}")
        self.assertEqual("PASS", result["result"])

    def test_it_really_injected_the_faults(self):
        # A run that passed because nothing went wrong would prove nothing.
        result = self.run_it()
        calls = [d["call"] for d in result["injected_faults"]]
        self.assertEqual(2, calls.count("acknowledge"), "one for C, one for E")
        self.assertEqual(2 + 4, calls.count("send_message"),
                         "two dropped replies for B, four for D")

    def test_every_request_ends_with_exactly_one_reply(self):
        self.run_it()
        by_parent: dict[str, int] = {}
        for message in self.world["messages"].values():
            parent = message.get("parent_message_id")
            if parent:
                by_parent[parent] = by_parent.get(parent, 0) + 1
        self.assertEqual(5, len(by_parent))
        self.assertEqual({1}, set(by_parent.values()),
                         "a resumed or retried message must not answer twice")

    def test_the_two_phases_work_as_separate_runs(self):
        """The split has to survive being two processes, not two function calls.

        Phase two gets nothing from phase one: it re-sends the same requests,
        gets the same message ids back through the bus's idempotency, and finds
        the unacknowledged reply in the state file. That is exactly what a
        restarted container has, and nothing more.
        """
        harness = build_harness(self.world, self.state_path)
        first = worker_core_test.run_worker_core_test(harness, run_id="P1", phase="1")
        self.assertEqual("PASS", first["result"], first["divergences"])

        # A second harness with a fresh fault injector: nothing carries over.
        harness_again = build_harness(self.world, self.state_path)
        second = worker_core_test.run_worker_core_test(
            harness_again, run_id="P1", phase="2"
        )
        self.assertEqual("PASS", second["result"], second["divergences"])
        self.assertEqual(first["message_ids"]["C"], second["message_ids"]["C"],
                         "phase two must find the same message, not send a new one")

    def test_a_phase_two_without_a_state_file_is_reported(self):
        # Running phase two on an empty volume means the restart lost the
        # state. That must not look like a pass.
        harness = build_harness(self.world, self.state_path)
        result = worker_core_test.run_worker_core_test(harness, run_id="P2", phase="2")
        self.assertEqual("FAIL", result["result"])
        self.assertIn("the_state_volume_survived_the_restart",
                      {d["check"] for d in result["divergences"]})

    def test_nothing_stays_delivered(self):
        self.run_it()
        pending = [
            m["message_id"] for m in self.world["messages"].values()
            if m["recipient_id"] == AGENT and m["delivery_status"] == "DELIVERED"
        ]
        self.assertEqual([], pending)

    def test_every_reply_carries_the_task_reference(self):
        # The return leg of the Telegram chain depends on it: without the task
        # reference the connector withholds the body (finding G-003).
        self.run_it()
        replies = [m for m in self.world["messages"].values()
                   if m.get("parent_message_id")]
        self.assertTrue(replies)
        for reply in replies:
            self.assertEqual("ENG-WORKERCORE-T1", reply["task_ref"])

    def test_every_reply_carries_the_provenance_marker(self):
        # Security review A2: a reader who only sees the text must be able to
        # tell it was machine-generated.
        self.run_it()
        replies = [m for m in self.world["messages"].values()
                   if m.get("parent_message_id")]
        for reply in replies:
            self.assertTrue(reply["body"].startswith(agent_marker()),
                            reply["body"][:80])

    def test_the_reply_goes_back_to_the_requester_only(self):
        self.run_it()
        replies = [m for m in self.world["messages"].values()
                   if m.get("parent_message_id")]
        self.assertEqual({REQUESTER}, {r["recipient_id"] for r in replies})
        self.assertEqual({AGENT}, {r["sender_id"] for r in replies})


def agent_marker() -> str:
    import agent_worker
    return agent_worker.PROVENANCE_MARKER


class WeakenedControlIsDetectedTest(unittest.TestCase):
    """The run has to fail when the property it checks is broken.

    Same idea as the other weakened-control tests in this package: a suite that
    only ever sees the good case cannot tell a working control from one that
    has quietly stopped applying.
    """

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.state_path = Path(self._temp.name) / "worker_core.sqlite3"
        self.world = build_world()

    def tearDown(self):
        self._temp.cleanup()

    def test_a_bus_without_idempotency_is_caught(self):
        """A bus that hands out a fresh id per call must fail the run.

        The first version of this test passed against exactly such a bus, and
        that was the more interesting result: with a working state file the
        worker never sends twice at all, so bus idempotency was never reached.
        Scenario E - the lost state volume - is what puts the second line of
        defence under load, and this is what proves the check has teeth.
        """
        class DuplicatingBus(IntegratedFakeBus):
            def send_message(self, **kwargs):
                kwargs["idempotency_key"] = (
                    f"{kwargs['idempotency_key']}-{len(self.world['messages'])}"
                )
                return super().send_message(**kwargs)

        world = self.world
        agent = DuplicatingBus(world, AGENT)
        requester = IntegratedFakeBus(world, REQUESTER)

        def send_request(*, subject, body, key):
            sent = requester.send_message(
                recipient_id=AGENT, subject=subject, body=body,
                parent_message_id=None, task_ref="ENG-X",
                request_id=f"WORKERCORE-{key}",
                idempotency_key=f"IDEM-WORKERCORE-{key}",
            )
            return str(sent["message_id"])

        harness = worker_core_test.Harness(
            agent_client=agent, send_request=send_request,
            bus_messages=lambda: [dict(m) for m in world["messages"].values()],
            state_path=self.state_path,
        )
        result = worker_core_test.run_worker_core_test(harness, run_id="W1")
        self.assertEqual("FAIL", result["result"])

    def test_a_state_store_that_forgets_is_caught(self):
        # Without durable state the restart re-asks the model, which is what
        # the forbidden provider is there to notice.
        import state_store

        class ForgetfulStore(state_store.AgentStateStore):
            def claim(self, message_id):
                return state_store.Claim(message_id, "IN_PROGRESS", 1)

        original = state_store.AgentStateStore
        state_store.AgentStateStore = ForgetfulStore
        try:
            result = worker_core_test.run_worker_core_test(
                build_harness(self.world, self.state_path), run_id="W2"
            )
        finally:
            state_store.AgentStateStore = original

        self.assertEqual("FAIL", result["result"])
        broken = {d["check"] for d in result["divergences"]}
        self.assertIn("restart_did_not_ask_the_model", broken)


if __name__ == "__main__":
    unittest.main()
