"""The chain, end to end, locally: Telegram → Connector → Bus → Agent → Bus →
Connector → Telegram.

No network, no credentials, no bot, no cost. The connector and the worker are
the real code; only Telegram and the bus are fakes, and the bus fake enforces
the route allowlist because the return leg being structurally impossible was
the defect this package was written after.

Why this exists before the NAS run: every piece of this chain is separately
proven and the pieces have never run together. The two blockers already found
by reading (no return route, no task reference on the reply) would each have
cost one window. This is where the third one should surface, not there.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import chain_adapters
import telegram_connector

import agent_worker
import providers
import state_store
from chain_world import ChainWorld

CONNECTOR = "CEO-TG-CHAIN1"
AGENT = "AGENT-ENG-001"
TASK_ID = "ENG-CHAIN-1"
CHAT_ID = 4711
USER_ID = 815


def build_settings(state_path: Path, *, outbound_policy: str = "METADATA_ONLY"):
    return telegram_connector.Settings(
        enabled=True,
        kill_switch=False,
        allowed_chat_id=CHAT_ID,
        allowed_user_id=USER_ID,
        allowed_recipient_ids=frozenset({AGENT}),
        allowed_task_ids=frozenset({TASK_ID}),
        workforce_base_url="https://example.invalid",
        state_path=state_path,
        # The connector validates source_ref as ^DEC-\\d{3}/ENG-\\d{3}$, so it
        # cannot carry the honest CEO-CHAT-…/PENDING-DEC placeholder the rest
        # of the project uses. It writes its own authorising decision instead,
        # which is true: DEC-023/ENG-007 is what permits this connector to
        # exist. See the README for why the two source refs differ.
        source_ref="DEC-023/ENG-007",
        outbound_policy=outbound_policy,
        outbound_body_chars=500,
        telegram_bot_token="test-only",
        workforce_bus_token="test-only",
    )


class ChainTest(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._temp.name)
        self.world = ChainWorld(connector_id=CONNECTOR, agent_id=AGENT)
        self.telegram = chain_adapters.FakeTelegram([
            chain_adapters.telegram_update(
                1, f"/task {AGENT} {TASK_ID} | Kurze Lagebeurteilung | Drei Saetze",
                chat_id=CHAT_ID, user_id=USER_ID,
            )
        ])

    def tearDown(self):
        self._temp.cleanup()

    def build_connector(self, *, outbound_policy="METADATA_ONLY"):
        settings = build_settings(self.tmp / "connector.sqlite3",
                                  outbound_policy=outbound_policy)
        store = telegram_connector.AuditStore(settings.state_path)
        gateway = chain_adapters.ConnectorGateway(self.world,
                                                  source_ref=settings.source_ref)
        return telegram_connector.TelegramConnector(
            settings, store, self.telegram, gateway
        )

    def run_agent(self):
        store = state_store.AgentStateStore(self.tmp / "agent.sqlite3")
        try:
            return agent_worker.poll_once(
                chain_adapters.AgentBusClient(self.world),
                providers.EchoProvider(),
                state=store,
            )
        finally:
            store.close()

    # -- the chain ---------------------------------------------------------
    def test_the_chain_closes(self):
        connector = self.build_connector(outbound_policy="BODY")

        handled = connector.poll_once()
        self.assertEqual(1, handled, "the /task command was not processed")
        self.assertIn(TASK_ID, self.world.tasks, "no task reached the bus")

        results = self.run_agent()
        self.assertEqual(1, len(results), f"the agent handled nothing: {results}")
        self.assertEqual("ANSWERED", results[0]["result"], results[0])

        sent = connector.publish_inbox_notifications()
        self.assertEqual(1, sent, "the answer never reached Telegram")

        # The end of the chain is the chat, not the bus.
        texts = [text for _, text in self.telegram.chat]
        answer = [t for t in texts if t.startswith("NACHRICHT")]
        self.assertEqual(1, len(answer), texts)
        self.assertIn(AGENT, answer[0])
        self.assertIn(TASK_ID, answer[0], "the task reference did not survive")

    def test_the_answer_text_arrives_under_body_policy(self):
        connector = self.build_connector(outbound_policy="BODY")
        connector.poll_once()
        self.run_agent()
        connector.publish_inbox_notifications()

        answer = [t for _, t in self.telegram.chat if t.startswith("NACHRICHT")][0]
        self.assertIn("Maschinell erzeugte Antwort", answer,
                      "the provenance marker must reach the reader")
        self.assertIn("Echo-Provider", answer,
                      "the echo answer itself must be visible under BODY")

    def test_metadata_only_announces_without_the_text(self):
        # The fail-closed default: the chain still closes, but the reader sees
        # that something arrived, not what it says.
        connector = self.build_connector(outbound_policy="METADATA_ONLY")
        connector.poll_once()
        self.run_agent()
        self.assertEqual(1, connector.publish_inbox_notifications())

        answer = [t for _, t in self.telegram.chat if t.startswith("NACHRICHT")][0]
        self.assertIn(TASK_ID, answer)
        self.assertNotIn("Echo-Provider", answer)

    def test_the_reply_is_acknowledged_and_nothing_stays_pending(self):
        connector = self.build_connector()
        connector.poll_once()
        self.run_agent()
        connector.publish_inbox_notifications()

        pending = [m for m in self.world.messages.values()
                   if m["recipient_id"] == AGENT and m["delivery_status"] == "DELIVERED"]
        self.assertEqual([], pending)

    def test_a_second_pass_answers_nothing_twice(self):
        connector = self.build_connector()
        connector.poll_once()
        self.run_agent()
        connector.publish_inbox_notifications()

        # Same state files, same world: a repeated run must be a no-op.
        self.assertEqual(0, len(self.run_agent()))
        self.assertEqual(0, connector.publish_inbox_notifications())
        replies = [m for m in self.world.messages.values() if m["parent_message_id"]]
        self.assertEqual(1, len(replies))


class TheChainCanBreakTest(unittest.TestCase):
    """Each of these would have cost one window on the NAS."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._temp.name)
        self.world = ChainWorld(connector_id=CONNECTOR, agent_id=AGENT)
        self.telegram = chain_adapters.FakeTelegram([
            chain_adapters.telegram_update(
                1, f"/task {AGENT} {TASK_ID} | Kurze Lagebeurteilung | Drei Saetze",
                chat_id=CHAT_ID, user_id=USER_ID,
            )
        ])

    def tearDown(self):
        self._temp.cleanup()

    def _connector(self, policy="BODY"):
        settings = build_settings(self.tmp / "c.sqlite3", outbound_policy=policy)
        return telegram_connector.TelegramConnector(
            settings, telegram_connector.AuditStore(settings.state_path),
            self.telegram,
            chain_adapters.ConnectorGateway(self.world, source_ref=settings.source_ref),
        )

    def _agent(self):
        store = state_store.AgentStateStore(self.tmp / "a.sqlite3")
        try:
            return agent_worker.poll_once(
                chain_adapters.AgentBusClient(self.world),
                providers.EchoProvider(), state=store)
        finally:
            store.close()

    def test_without_the_return_route_the_answer_never_arrives(self):
        # Blocker 1 from the README, kept as a test so it cannot come back:
        # every earlier prepare script created outbound routes only.
        self.world.routes.discard((AGENT, CONNECTOR, "MESSAGE"))
        connector = self._connector()
        connector.poll_once()
        results = self._agent()
        self.assertEqual("REPLY_FAILED", results[0]["result"])
        self.assertEqual(0, connector.publish_inbox_notifications())

    def test_without_the_task_reference_the_text_is_withheld(self):
        # Blocker 2: the connector forwards a body only for an allowlisted
        # task. An answer without the reference is announced but never shown.
        connector = self._connector(policy="BODY")
        connector.poll_once()
        self._agent()
        for message in self.world.messages.values():
            if message["parent_message_id"]:
                message["task_ref"] = None
        connector.publish_inbox_notifications()
        answer = [t for _, t in self.telegram.chat if t.startswith("NACHRICHT")][0]
        self.assertNotIn("Echo-Provider", answer)

    def test_a_task_outside_the_allowlist_never_enters_the_bus(self):
        self.telegram.pending = [chain_adapters.telegram_update(
            2, f"/task {AGENT} ENG-NOT-ALLOWED | x | y",
            chat_id=CHAT_ID, user_id=USER_ID)]
        connector = self._connector()
        connector.poll_once()
        self.assertEqual({}, self.world.tasks)
        self.assertTrue(any("FEHLER" in t for _, t in self.telegram.chat))

    def test_a_stranger_gets_nothing(self):
        self.telegram.pending = [chain_adapters.telegram_update(
            3, f"/task {AGENT} {TASK_ID} | x | y", chat_id=CHAT_ID, user_id=USER_ID + 1)]
        connector = self._connector()
        connector.poll_once()
        self.assertEqual({}, self.world.tasks)
        self.assertEqual([], self.telegram.chat)


if __name__ == "__main__":
    unittest.main()
