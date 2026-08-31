"""Crash-recovery tests. Review findings G-001 (loss) and G-002 (double work)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import agent_worker
import bus_client
import state_store
from test_agent_worker import FakeBus, ScriptedProvider, message


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.now = [1000.0]
        self.store = state_store.AgentStateStore(
            Path(self.tempdir.name) / "state.sqlite3",
            max_attempts=2, lease_seconds=60, clock=lambda: self.now[0],
        )

    def tearDown(self):
        self.store.close()
        self.tempdir.cleanup()

    def test_first_claim_is_granted(self):
        claim = self.store.claim("MSG-1")
        self.assertEqual("IN_PROGRESS", claim.state)
        self.assertTrue(claim.needs_model)

    def test_a_second_worker_cannot_take_a_held_message(self):
        self.store.claim("MSG-1")
        self.assertIsNone(self.store.claim("MSG-1"), "lease still running")

    def test_an_expired_lease_can_be_taken_over(self):
        self.store.claim("MSG-1")
        self.now[0] += 61
        retry = self.store.claim("MSG-1")
        self.assertEqual("IN_PROGRESS", retry.state)
        self.assertEqual(2, retry.attempts)

    def test_finished_message_is_never_reclaimed(self):
        self.store.claim("MSG-1")
        self.store.record_done("MSG-1")
        self.assertIsNone(self.store.claim("MSG-1"))

    def test_replied_message_resumes_at_the_acknowledgement(self):
        self.store.claim("MSG-1")
        self.store.record_reply("MSG-1", "MSG-REPLY-1")
        claim = self.store.claim("MSG-1")
        self.assertEqual("REPLIED", claim.state)
        self.assertFalse(claim.needs_model, "must not pay for the model twice")
        self.assertEqual("MSG-REPLY-1", claim.reply_message_id)

    def test_attempts_run_out_instead_of_looping_forever(self):
        self.store.claim("MSG-1")
        for _ in range(5):
            self.now[0] += 61
            claim = self.store.claim("MSG-1")
            if claim is not None and claim.state == "EXHAUSTED":
                break
        self.assertEqual("EXHAUSTED", claim.state)
        # Still claimable: the final notice has not been recorded yet, and a
        # run that died before sending it must not silence the message.
        again = self.store.claim("MSG-1")
        self.assertEqual("EXHAUSTED", again.state)
        self.assertFalse(again.needs_model, "no further model calls, though")
        # Recording the notice is what ends it.
        self.store.record_reply("MSG-1", "MSG-FINAL")
        self.assertEqual("REPLIED", self.store.claim("MSG-1").state)

    def test_failure_makes_the_message_claimable_again_at_once(self):
        self.store.claim("MSG-1")
        self.store.record_failure("MSG-1", "AGENT_PROVIDER_UNREACHABLE")
        claim = self.store.claim("MSG-1")
        self.assertIsNotNone(claim, "a failed attempt must not block the retry")
        self.assertEqual(2, claim.attempts)


class CrashRecoveryTest(unittest.TestCase):
    """The behaviour G-001 was about: what a dead process leaves behind."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "state.sqlite3"

    def tearDown(self):
        self.tempdir.cleanup()

    def _store(self):
        return state_store.AgentStateStore(self.path, max_attempts=3)

    def test_acknowledgement_happens_only_after_the_reply(self):
        # The core of the fix: nothing is acknowledged until the answer is out.
        bus, provider = FakeBus(), ScriptedProvider()
        order: list[str] = []
        original_ack, original_send = bus.acknowledge, bus.send_message
        bus.acknowledge = lambda *a, **k: (order.append("ack"), original_ack(*a, **k))[1]
        bus.send_message = lambda **k: (order.append("send"), original_send(**k))[1]

        store = self._store()
        agent_worker.handle_message(bus, provider, message(), policy="BODY", state=store)
        store.close()
        self.assertEqual(["send", "ack"], order)

    def test_a_crash_before_the_reply_leaves_the_message_unacknowledged(self):
        bus = FakeBus()
        bus.fail_send_with = "BUS_ROUTE_DENIED"
        store = self._store()
        result = agent_worker.handle_message(bus, ScriptedProvider(), message(),
                                             policy="BODY", state=store)
        store.close()

        self.assertEqual("REPLY_FAILED", result["result"])
        self.assertEqual([], bus.acks,
                         "unacknowledged means the next run still sees it")

    def test_a_crash_after_the_reply_resumes_without_a_second_model_call(self):
        # First run: reply lands, acknowledgement fails, process dies.
        bus, provider = FakeBus(), ScriptedProvider()

        def failing_ack(*args, **kwargs):
            raise bus_client.BusError("AGENT_BUS_TIMEOUT")

        bus.acknowledge = failing_ack
        store = self._store()
        agent_worker.handle_message(bus, provider, message(), policy="BODY", state=store)
        store.close()
        self.assertEqual(1, len(bus.sent))
        self.assertEqual(1, len(provider.seen))

        # Second run with a working bus: acknowledges, no new model call.
        bus2, provider2 = FakeBus(), ScriptedProvider()
        store2 = self._store()
        result = agent_worker.handle_message(bus2, provider2, message(),
                                             policy="BODY", state=store2)
        store2.close()

        self.assertEqual([], provider2.seen, "the model must not be paid twice")
        self.assertEqual([], bus2.sent, "no duplicate reply")
        self.assertEqual(1, len(bus2.acks), "resumes exactly at the acknowledgement")
        self.assertEqual("ANSWERED", result["result"])

    def test_a_completed_message_is_skipped_entirely(self):
        bus, provider = FakeBus(), ScriptedProvider()
        store = self._store()
        agent_worker.handle_message(bus, provider, message(), policy="BODY", state=store)
        store.close()

        bus2, provider2 = FakeBus(), ScriptedProvider()
        store2 = self._store()
        result = agent_worker.handle_message(bus2, provider2, message(),
                                             policy="BODY", state=store2)
        store2.close()

        self.assertEqual("ALREADY_HANDLED", result["result"])
        self.assertEqual([], provider2.seen)
        self.assertEqual([], bus2.sent)

    def test_without_a_store_the_old_stateless_behaviour_still_works(self):
        bus = FakeBus()
        result = agent_worker.handle_message(bus, ScriptedProvider(), message(),
                                             policy="BODY", state=None)
        self.assertEqual("ANSWERED", result["result"])
        self.assertEqual(1, len(bus.sent))
        self.assertEqual(1, len(bus.acks))


if __name__ == "__main__":
    unittest.main()


class ClaimLifecycleTest(unittest.TestCase):
    """Findings G-012 and G-013: the claim must outlive the work, not the try."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "state.sqlite3"

    def tearDown(self):
        self.tempdir.cleanup()

    def _store(self, **kwargs):
        return state_store.AgentStateStore(self.path, **kwargs)

    def test_an_exhausted_message_is_not_lost_when_the_ack_fails(self):
        # G-012, exactly the case Gerd asked for: attempts exceeded, final
        # reply lands, acknowledgement fails, restart must acknowledge without
        # a second reply and end DONE.
        store = self._store(max_attempts=1, lease_seconds=0)
        store.claim("MSG-X")               # first attempt
        store.claim("MSG-X")               # second → EXHAUSTED
        store.close()

        bus, provider = FakeBus(), ScriptedProvider()

        def failing_ack(*args, **kwargs):
            raise bus_client.BusError("AGENT_BUS_TIMEOUT")

        bus.acknowledge = failing_ack
        store = self._store(max_attempts=1, lease_seconds=0)
        agent_worker.handle_message(bus, provider, message(message_id="MSG-X"),
                                    policy="BODY", state=store)
        store.close()
        self.assertEqual(1, len(bus.sent), "the final failure notice goes out")

        # Restart with a working bus.
        bus2, provider2 = FakeBus(), ScriptedProvider()
        store = self._store(max_attempts=1, lease_seconds=0)
        result = agent_worker.handle_message(bus2, provider2,
                                             message(message_id="MSG-X"),
                                             policy="BODY", state=store)
        store.close()

        self.assertEqual([], bus2.sent, "no second reply")
        self.assertEqual([], provider2.seen, "no second model call")
        self.assertEqual(1, len(bus2.acks), "the message is acknowledged at last")
        self.assertEqual("ANSWERED", result["result"])

    def test_a_provider_error_keeps_the_claim_until_the_reply_is_out(self):
        # G-013: a second worker sharing the store must not be able to take the
        # message while the first is still writing its failure reply.
        store = self._store()
        bus = FakeBus()
        provider = ScriptedProvider(error="AGENT_PROVIDER_UNREACHABLE")

        second = self._store()
        stolen: list[object] = []
        original_send = bus.send_message

        def send_and_probe(**kwargs):
            # At this moment the provider has already failed. A competing
            # worker must still be locked out.
            stolen.append(second.claim("MSG-" + "A" * 32))
            return original_send(**kwargs)

        bus.send_message = send_and_probe
        agent_worker.handle_message(bus, provider, message(), policy="BODY",
                                    state=store)
        store.close()
        second.close()

        self.assertEqual([None], stolen,
                         "the claim must still be held while the reply is written")

    def test_a_failed_reply_does_hand_the_message_back(self):
        # The one case where releasing early is right: nothing durable exists.
        store = self._store()
        bus = FakeBus()
        bus.fail_send_with = "AGENT_BUS_UNREACHABLE"
        agent_worker.handle_message(bus, ScriptedProvider(), message(),
                                    policy="BODY", state=store)
        store.close()

        retry = self._store()
        claim = retry.claim("MSG-" + "A" * 32)
        retry.close()
        self.assertIsNotNone(claim, "a run that produced nothing must be retryable")
        self.assertEqual("IN_PROGRESS", claim.state)
