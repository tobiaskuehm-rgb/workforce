"""The model allowlist, and the four ways around it that are now closed.

CEO addition to Phase 5, point 5. Before this, `AGENT_MODEL` was any string:
`build_provider()` handed it to the SDK unchecked and `Budget` priced an
unknown name from a fallback tariff. So a typo produced a real call at a
guessed price, and adopting a new, more expensive model required no decision.

Four controls, each with a test that removes it and demands the removal shows:

  unknown model      refused before anything is built
  task class         a model may only serve work it is listed for
  data ceiling       measured on what actually goes into the call
  no switching       the model that answers must be the one configured, and
                     an answer from a different one is **discarded**

The last one is the least obvious and the most important. An SDK alias that
resolves to a larger model, a server-side upgrade, a fallback after an error -
all arrive as a different name in the reply. Logging that and using the answer
anyway would mean the data ceiling and the price were chosen for one model
while another saw the payload.
"""

from __future__ import annotations

import dataclasses
import pathlib
import unittest
import unittest.mock

import agent_worker
import budget as budget_module
import data_boundary
import model_allowlist
import providers
from test_agent_worker import FakeBus, ScriptedProvider, message


class TheListIsClosedTest(unittest.TestCase):
    def test_a_known_model_resolves(self) -> None:
        modell = model_allowlist.for_task("echo-v1", task_class="BUS_REPLY")
        self.assertEqual("echo-v1", modell.name)
        self.assertFalse(modell.is_paid)

    def test_an_unknown_model_is_refused(self) -> None:
        with self.assertRaises(model_allowlist.ModelNotAllowed) as caught:
            model_allowlist.for_task("claude-opus-6", task_class="BUS_REPLY")
        self.assertIn("AGENT_MODEL_NOT_ALLOWED", str(caught.exception))

    def test_an_empty_model_is_refused_rather_than_defaulted(self) -> None:
        # Same shape as G-029, where an unset provider used to fall back to
        # the paid one: an incomplete configuration must decide nothing.
        with self.assertRaises(model_allowlist.ModelNotAllowed) as caught:
            model_allowlist.for_task("", task_class="BUS_REPLY")
        self.assertIn("AGENT_MODEL_NOT_CONFIGURED", str(caught.exception))

    def test_an_unknown_task_class_is_refused(self) -> None:
        with self.assertRaises(model_allowlist.ModelNotAllowed) as caught:
            model_allowlist.for_task("echo-v1", task_class="FINANCE_ADVICE")
        self.assertIn("AGENT_TASK_CLASS_UNKNOWN", str(caught.exception))

    def test_the_provider_binding_is_checked_where_the_provider_is_chosen(self) -> None:
        model_allowlist.resolve("echo-v1", provider="echo", task_class="BUS_REPLY")
        with self.assertRaises(model_allowlist.ModelNotAllowed) as caught:
            model_allowlist.resolve("claude-opus-5", provider="echo", task_class="BUS_REPLY")
        self.assertIn("AGENT_MODEL_PROVIDER_MISMATCH", str(caught.exception))

    def test_the_data_ceiling_is_a_refusal_and_not_a_truncation(self) -> None:
        modell = model_allowlist.for_task("echo-v1", task_class="BUS_REPLY")
        model_allowlist.assert_within_data_ceiling(modell, modell.max_input_chars)
        with self.assertRaises(model_allowlist.ModelNotAllowed) as caught:
            model_allowlist.assert_within_data_ceiling(modell, modell.max_input_chars + 1)
        self.assertIn("AGENT_MODEL_INPUT_TOO_LARGE", str(caught.exception))

    def test_a_switch_is_an_error(self) -> None:
        modell = model_allowlist.for_task("echo-v1", task_class="BUS_REPLY")
        model_allowlist.assert_no_switch(modell, "echo-v1")
        for anders in ("claude-opus-5", "", "echo-v2"):
            with self.subTest(geantwortet=anders):
                with self.assertRaises(model_allowlist.ModelNotAllowed) as caught:
                    model_allowlist.assert_no_switch(modell, anders)
                self.assertIn("AGENT_MODEL_SWITCHED", str(caught.exception))

    def test_the_output_ceiling_is_the_models_own(self) -> None:
        """G-057: das Feld war deklariert und wurde nie gelesen.

        `ClaudeProvider` gab `MAX_REPLY_TOKENS` an die API weiter, ein Modul-
        konstante. Die Angabe im Eintrag behauptete damit eine Grenze, die
        niemand anwandte - und eine Zusicherung, die sich nicht pruefen laesst,
        haelt den naechsten Leser vom Nachsehen ab (Leitplanke 7).
        """
        quelle = pathlib.Path(providers.__file__).read_text(encoding="utf-8")
        self.assertIn("max_tokens=self._max_output_tokens", quelle)
        self.assertNotIn("max_tokens=MAX_REPLY_TOKENS", quelle)

    def test_the_call_cost_ceiling_is_checked_before_the_call(self) -> None:
        klein = model_allowlist.ALLOWLIST["claude-haiku-4-5"]
        model_allowlist.assert_within_call_cost(klein, klein.max_input_chars)
        teuer = dataclasses.replace(klein, max_cost_usd_per_call=0.001)
        with self.assertRaises(model_allowlist.ModelNotAllowed) as caught:
            model_allowlist.assert_within_call_cost(teuer, 100)
        self.assertIn("AGENT_MODEL_CALL_TOO_EXPENSIVE", str(caught.exception))

    def test_the_worst_case_is_an_upper_bound_and_not_a_guess(self) -> None:
        # Eingabe geschaetzt, Ausgabe durch die Decke begrenzt, die der
        # Provider der API mitgibt - deshalb ist das Produkt eine echte
        # Obergrenze und ein Vorabtest ueberhaupt moeglich.
        m = model_allowlist.ALLOWLIST["claude-opus-5"]
        wenig = model_allowlist.worst_case_cost(m, 100)
        viel = model_allowlist.worst_case_cost(m, m.max_input_chars)
        self.assertLess(wenig, viel)
        self.assertGreater(wenig, m.estimated_cost(25, 0),
                           "die Ausgabe muss mitgerechnet sein")

    def test_every_listed_model_stays_under_its_own_call_ceiling(self) -> None:
        # Eine Decke, die schon der Normalfall reisst, waere keine Kontrolle,
        # sondern eine Abschaltung.
        for name, m in model_allowlist.ALLOWLIST.items():
            with self.subTest(modell=name):
                model_allowlist.assert_within_call_cost(m, m.max_input_chars)

    def test_every_entry_is_complete(self) -> None:
        # A ceiling of zero would read as "unlimited" to a careless caller.
        for name, m in model_allowlist.ALLOWLIST.items():
            with self.subTest(modell=name):
                self.assertEqual(name, m.name, "Schluessel und Name muessen gleich sein")
                self.assertGreater(m.max_input_chars, 0)
                self.assertGreater(m.max_output_tokens, 0)
                self.assertTrue(m.task_classes)
                self.assertTrue(set(m.task_classes) <= set(model_allowlist.TASK_CLASSES))
                if m.is_paid:
                    self.assertGreater(m.price_input_per_million, 0)
                    self.assertGreater(m.max_cost_usd_per_call, 0)
                else:
                    self.assertEqual(0.0, m.price_input_per_million)


class TheTariffHasOneSourceTest(unittest.TestCase):
    def test_budget_prices_come_from_the_allowlist(self) -> None:
        self.assertEqual(model_allowlist.prices(), budget_module.DEFAULT_PRICES)

    def test_no_listed_model_falls_through_to_the_fallback(self) -> None:
        for name in model_allowlist.ALLOWLIST:
            with self.subTest(modell=name):
                self.assertIn(name, budget_module.DEFAULT_PRICES)

    def test_the_fallback_is_not_cheaper_than_any_listed_model(self) -> None:
        # The second line must not be weaker than the first. If it were, an
        # unlisted model would be *cheaper* to the ceiling than a listed one.
        ein, aus = budget_module.FALLBACK_PRICE
        for name, (p_in, p_out) in budget_module.DEFAULT_PRICES.items():
            with self.subTest(modell=name):
                self.assertGreaterEqual(ein, p_in)
                self.assertGreaterEqual(aus, p_out)


class TheProviderFactoryRefusesTest(unittest.TestCase):
    def test_echo_still_builds_without_configuration(self) -> None:
        provider = providers.build_provider({"AGENT_PROVIDER": "echo"})
        self.assertEqual("echo-v1", provider.model)

    def test_an_unknown_model_is_refused_at_build_time(self) -> None:
        with self.assertRaises(providers.ProviderError) as caught:
            providers.build_provider(
                {"AGENT_PROVIDER": "echo", "AGENT_MODEL": "echo-v99"})
        self.assertIn("AGENT_MODEL_NOT_ALLOWED", str(caught.exception))

    def test_a_model_from_another_provider_is_refused(self) -> None:
        # The control that only makes sense here: echo must not serve a
        # Claude model, whatever the environment says.
        with self.assertRaises(providers.ProviderError) as caught:
            providers.build_provider(
                {"AGENT_PROVIDER": "echo", "AGENT_MODEL": "claude-opus-5"})
        self.assertIn("AGENT_MODEL_PROVIDER_MISMATCH", str(caught.exception))


class SwitchingProvider(ScriptedProvider):
    """Answers as something other than it was configured as."""

    name = "scripted"
    model = "echo-v1"

    def complete(self, *, system, content):
        return providers.Reply(text="Antwort aus dem falschen Modell.",
                               provider=self.name, model="claude-opus-5")


class SmallModelProvider(ScriptedProvider):
    """Configured for the cheap model, which has the smaller data ceiling."""

    name = "scripted"
    model = "claude-haiku-4-5"


class TheWorkerRefusesTest(unittest.TestCase):
    """The controls where they actually run."""

    def test_a_switched_answer_is_discarded_not_used(self) -> None:
        bus = FakeBus()
        result = agent_worker.handle_message(
            bus, SwitchingProvider(), message(), policy="BODY")
        self.assertEqual("REFUSED", result["result"])
        gesendet = " ".join(str(eintrag) for eintrag in bus.sent)
        self.assertNotIn("Antwort aus dem falschen Modell", gesendet,
                         "die Modellausgabe darf nicht verwendet werden")
        self.assertIn("AGENT_MODEL_SWITCHED", gesendet)

    def test_a_payload_over_the_model_ceiling_is_refused_before_the_call(self) -> None:
        # Gross genug fuer die Datengrenze, zu gross fuer dieses Modell -
        # genau das Fenster, in dem die Modellobergrenze etwas entscheidet.
        provider = SmallModelProvider()
        ceiling = model_allowlist.ALLOWLIST["claude-haiku-4-5"].max_input_chars
        self.assertLess(ceiling, data_boundary.MAX_OUTBOUND_CHARS)
        bus = FakeBus()
        result = agent_worker.handle_message(
            bus, provider, message(body="x" * (ceiling + 500)), policy="BODY")
        self.assertEqual("REFUSED", result["result"])
        self.assertEqual([], provider.seen, "das Modell darf gar nicht gefragt werden")
        self.assertIn("AGENT_MODEL_INPUT_TOO_LARGE",
                      " ".join(str(eintrag) for eintrag in bus.sent))

    def test_the_same_payload_reaches_a_model_that_is_allowed_it(self) -> None:
        # Die Gegenprobe: ohne sie wuerde der Test oben auch bestehen, wenn
        # die Nachricht aus einem ganz anderen Grund abgelehnt wuerde.
        gross = ScriptedProvider()          # echo-v1, Obergrenze GROSS
        ceiling = model_allowlist.ALLOWLIST["claude-haiku-4-5"].max_input_chars
        result = agent_worker.handle_message(
            FakeBus(), gross, message(body="x" * (ceiling + 500)), policy="BODY")
        self.assertEqual("ANSWERED", result["result"])
        self.assertEqual(1, len(gross.seen))

    def test_no_model_ceiling_exceeds_the_data_boundary(self) -> None:
        # Eine Obergrenze oberhalb der Datengrenze koennte nie greifen und
        # waere Zierrat - genau der Zustand, in dem dieser Test entstand.
        for name, m in model_allowlist.ALLOWLIST.items():
            with self.subTest(modell=name):
                self.assertLessEqual(m.max_input_chars,
                                     data_boundary.MAX_OUTBOUND_CHARS)

    def test_an_over_budget_call_is_refused_before_the_provider_is_asked(self) -> None:
        # Der Punkt der Vorabpruefung: Die laufweite Kostendecke koennte hier
        # nichts ausrichten, weil Kosten erst nach dem Aufruf bekannt sind.
        teuer = dataclasses.replace(model_allowlist.ALLOWLIST["echo-v1"],
                                    price_output_per_million=1000.0,
                                    max_cost_usd_per_call=0.0)
        provider = ScriptedProvider()
        bus = FakeBus()
        with unittest.mock.patch.dict(model_allowlist.ALLOWLIST,
                                      {"echo-v1": teuer}):
            result = agent_worker.handle_message(bus, provider, message(),
                                                 policy="BODY")
        self.assertEqual("REFUSED", result["result"])
        self.assertEqual([], provider.seen, "das Modell darf gar nicht gefragt werden")
        self.assertIn("AGENT_MODEL_CALL_TOO_EXPENSIVE",
                      " ".join(str(eintrag) for eintrag in bus.sent))

    def test_a_normal_message_still_gets_through(self) -> None:
        # Ohne diesen Fall waere jede Verschaerfung oben "erfolgreich".
        bus = FakeBus()
        result = agent_worker.handle_message(
            bus, ScriptedProvider(), message(), policy="BODY")
        self.assertEqual("ANSWERED", result["result"])

    def test_a_provider_without_a_model_is_refused(self) -> None:
        class Namenlos(ScriptedProvider):
            model = ""

        bus = FakeBus()
        result = agent_worker.handle_message(bus, Namenlos(), message(), policy="BODY")
        self.assertEqual("REFUSED", result["result"])


if __name__ == "__main__":
    unittest.main()
