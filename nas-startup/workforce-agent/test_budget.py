"""Tests for the run budget. No network, no cost."""

from __future__ import annotations

import unittest

import agent_worker
import budget as budget_module
from test_agent_worker import FakeBus, ScriptedProvider, message


class BudgetTest(unittest.TestCase):
    def test_message_ceiling_stops_the_run(self):
        b = budget_module.Budget(max_messages=2)
        b.record_message()
        b.check_message()
        b.record_message()
        with self.assertRaises(budget_module.BudgetExhausted) as caught:
            b.check_message()
        self.assertEqual("messages", caught.exception.limit_name)

    def test_provider_call_ceiling_stops_the_run(self):
        b = budget_module.Budget(max_provider_calls=1)
        b.record_provider_call(model="claude-opus-5", input_tokens=10, output_tokens=10)
        with self.assertRaises(budget_module.BudgetExhausted) as caught:
            b.check_message()
        self.assertEqual("provider_calls", caught.exception.limit_name)

    def test_token_ceiling_stops_the_run(self):
        b = budget_module.Budget(max_tokens=100)
        b.record_provider_call(model="claude-opus-5", input_tokens=60, output_tokens=60)
        with self.assertRaises(budget_module.BudgetExhausted) as caught:
            b.check_message()
        self.assertEqual("tokens", caught.exception.limit_name)

    def test_cost_ceiling_stops_the_run(self):
        b = budget_module.Budget(max_cost_usd=0.01, max_tokens=10_000_000)
        # 1M input tokens at $5/1M = $5.00, well past a one-cent ceiling.
        b.record_provider_call(model="claude-opus-5", input_tokens=1_000_000, output_tokens=0)
        with self.assertRaises(budget_module.BudgetExhausted) as caught:
            b.check_message()
        self.assertEqual("cost_usd", caught.exception.limit_name)

    def test_cost_is_computed_from_the_price_table(self):
        b = budget_module.Budget()
        b.record_provider_call(model="claude-opus-5", input_tokens=1_000_000, output_tokens=1_000_000)
        self.assertAlmostEqual(30.00, b.cost_usd, places=4)  # 5 + 25

    def test_unknown_model_uses_the_fallback_price_instead_of_zero(self):
        # A model missing from the table must not silently cost nothing -
        # that would make the ceiling unreachable.
        b = budget_module.Budget()
        b.record_provider_call(model="some-future-model", input_tokens=1_000_000, output_tokens=0)
        self.assertAlmostEqual(5.00, b.cost_usd, places=4)

    def test_missing_usage_counts_as_zero_tokens_but_still_counts_the_call(self):
        b = budget_module.Budget()
        b.record_provider_call(model="claude-opus-5", input_tokens=None, output_tokens=None)
        self.assertEqual(1, b.provider_calls)
        self.assertEqual(0, b.total_tokens)

    def test_zero_cost_ceiling_still_allows_a_free_provider(self):
        # A ceiling of 0.00 means "this run must not cost anything", not
        # "this run may not happen". The echo provider spends nothing, so a
        # dry run under a zero ceiling has to work.
        b = budget_module.Budget(max_cost_usd=0.0)
        b.check_message()
        b.record_provider_call(model="echo-v1", input_tokens=None, output_tokens=None)
        b.check_message()

    def test_zero_cost_ceiling_trips_on_the_first_paid_call(self):
        b = budget_module.Budget(max_cost_usd=0.0)
        b.record_provider_call(model="claude-opus-5", input_tokens=1000, output_tokens=100)
        with self.assertRaises(budget_module.BudgetExhausted) as caught:
            b.check_message()
        self.assertEqual("cost_usd", caught.exception.limit_name)

    def test_log_record_reports_use_against_every_ceiling(self):
        record = budget_module.Budget().as_log_record()
        for key in ("messages_max", "provider_calls_max", "tokens_max", "cost_usd_max"):
            self.assertIn(key, record)

    def test_negative_ceiling_is_refused(self):
        with self.assertRaises(ValueError):
            budget_module.Budget(max_messages=-1)

    def test_build_budget_reads_the_environment(self):
        b = budget_module.build_budget({
            "AGENT_MAX_MESSAGES": "3",
            "AGENT_MAX_PROVIDER_CALLS": "4",
            "AGENT_MAX_TOKENS": "5000",
            "AGENT_MAX_COST_USD": "0.25",
        })
        self.assertEqual((3, 4, 5000, 0.25),
                         (b.max_messages, b.max_provider_calls, b.max_tokens, b.max_cost_usd))

    def test_build_budget_refuses_nonsense(self):
        with self.assertRaises(ValueError):
            budget_module.build_budget({"AGENT_MAX_MESSAGES": "viele"})
        with self.assertRaises(ValueError):
            budget_module.build_budget({"AGENT_MAX_COST_USD": "-1"})


class BudgetInWorkerTest(unittest.TestCase):
    def test_exhausted_budget_leaves_the_message_untouched(self):
        # The property that matters: no acknowledgement, no reply, nothing
        # swallowed. The message must still be there for a later run.
        bus, provider = FakeBus(), ScriptedProvider()
        spent = budget_module.Budget(max_messages=0)

        with self.assertRaises(budget_module.BudgetExhausted):
            agent_worker.handle_message(bus, provider, message(),
                                        policy="BODY", budget=spent)

        self.assertEqual([], bus.acks, "must not acknowledge")
        self.assertEqual([], bus.sent, "must not reply")
        self.assertEqual([], provider.seen, "must not reach the provider")

    def test_poll_stops_early_and_leaves_the_rest_pending(self):
        messages = [message(message_id=f"MSG-{i:032d}") for i in range(4)]
        bus = FakeBus(messages=messages)
        results = agent_worker.poll_once(
            bus, ScriptedProvider(), policy="BODY",
            budget=budget_module.Budget(max_messages=2),
        )
        self.assertEqual(2, len(results))
        self.assertEqual(2, len(bus.acks), "only the handled ones are acknowledged")

    def test_run_stops_once_the_budget_is_spent(self):
        bus = FakeBus(messages=[message()])
        slept: list[int] = []
        handled = agent_worker.run(
            bus, ScriptedProvider(), poll_seconds=99, max_cycles=10,
            policy="BODY", budget=budget_module.Budget(max_messages=1),
            sleep=slept.append,
        )
        self.assertEqual(1, handled)
        self.assertEqual([], slept, "must not keep polling on a spent budget")

    def test_without_a_budget_nothing_changes(self):
        bus = FakeBus()
        result = agent_worker.handle_message(bus, ScriptedProvider(), message(),
                                             policy="BODY", budget=None)
        self.assertEqual("ANSWERED", result["result"])


if __name__ == "__main__":
    unittest.main()
