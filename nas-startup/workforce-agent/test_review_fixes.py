"""Tests for the fifth-round findings that were fixed outside the API.

Each fix here changed one line or one default. That is exactly the kind of
change that gets reverted by a later edit without anybody noticing, so each
one gets a test that states the property rather than the line.
"""

from __future__ import annotations

import pathlib
import unittest

import data_boundary
import providers

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ProviderIsFailClosedTest(unittest.TestCase):
    """G-029: an unset provider used to select the paid one."""

    def test_no_provider_configured_refuses_to_start(self) -> None:
        with self.assertRaises(providers.ProviderError) as caught:
            providers.build_provider({})
        self.assertEqual("AGENT_PROVIDER_NOT_CONFIGURED", str(caught.exception))

    def test_an_empty_value_is_not_a_choice_either(self) -> None:
        for value in ("", "   ", "\t"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(providers.ProviderError):
                    providers.build_provider({"AGENT_PROVIDER": value})

    def test_echo_still_works_without_anything_else(self) -> None:
        # Fail-closed must not mean unusable: the free provider needs no key,
        # no file and no network.
        provider = providers.build_provider({"AGENT_PROVIDER": "echo"})
        self.assertEqual("echo", provider.name)
        self.assertFalse(provider.is_paid)

    def test_the_example_file_does_not_hand_out_the_widest_policy(self) -> None:
        example = (ROOT / "workforce-agent" / "workforce-agent.env.example").read_text()
        self.assertIn("AGENT_DATA_POLICY=METADATA_ONLY", example)
        self.assertNotIn("AGENT_DATA_POLICY=FULL", example)


class SubjectIsContentTest(unittest.TestCase):
    """G-029: the subject used to travel under the narrowest policy."""

    def test_metadata_only_keeps_the_subject_on_the_nas(self) -> None:
        self.assertNotIn("subject", data_boundary._ALLOWED_FIELDS["METADATA_ONLY"])

    def test_the_wider_policies_still_carry_it(self) -> None:
        # Removing it everywhere would make BODY useless for a model.
        for policy in ("BODY", "FULL"):
            with self.subTest(policy=policy):
                self.assertIn("subject", data_boundary._ALLOWED_FIELDS[policy])

    def test_each_policy_is_a_superset_of_the_narrower_one(self) -> None:
        # The policies are a ladder. If a wider one ever lost a field, a run
        # could disclose less than configured - or, worse, the ladder could
        # develop a rung that discloses something the next one does not.
        metadata = set(data_boundary._ALLOWED_FIELDS["METADATA_ONLY"])
        body = set(data_boundary._ALLOWED_FIELDS["BODY"])
        full = set(data_boundary._ALLOWED_FIELDS["FULL"])
        self.assertTrue(metadata < body < full)


class ProviderCallsAreNotMultipliedTest(unittest.TestCase):
    """G-034: one reserved call must mean one external attempt."""

    def test_the_sdk_does_not_retry_behind_the_budget(self) -> None:
        import inspect

        signature = inspect.signature(providers.ClaudeProvider.__init__)
        self.assertEqual(0, signature.parameters["max_retries"].default,
                         "ein SDK-Retry macht aus einem reservierten Aufruf mehrere")


class MigrationsAreSeparatelyGatedTest(unittest.TestCase):
    """G-031: a core window must not migrate knowledge as a side effect."""

    def setUp(self) -> None:
        self.compose = (ROOT / "compose.yaml").read_text()

    def test_both_gates_default_to_closed(self) -> None:
        for gate in ("APPLY_MIGRATION_004_KNOWLEDGE",
                     "APPLY_MIGRATION_005_BUS_DENIAL_AUDIT",
                     "APPLY_MIGRATION_006_LEGACY_TABLES"):
            with self.subTest(gate=gate):
                self.assertIn(f'{gate}: "false"', self.compose)

    def test_each_migration_checks_its_own_gate(self) -> None:
        # A shared gate would couple exactly the two things the finding
        # separated.
        for gate, migration in (
            ("APPLY_MIGRATION_004_KNOWLEDGE", "004_knowledge_capability.sql"),
            ("APPLY_MIGRATION_005_BUS_DENIAL_AUDIT", "005_bus_denial_audit.sql"),
            ("APPLY_MIGRATION_006_LEGACY_TABLES", "006_legacy_registry_tables.sql"),
        ):
            with self.subTest(migration=migration):
                self.assertIn(f'"$${{{gate}:-false}}" != "true"', self.compose)
                self.assertIn(migration, self.compose)

    def test_the_three_applied_migrations_stay_automatic(self) -> None:
        # 001-003 are long applied on the NAS; gating them would turn a
        # restart into a manual step for no gain.
        for migration in ("001_employee_registry", "002_workforce_bus",
                          "003_workforce_bus_trigger_fix"):
            with self.subTest(migration=migration):
                self.assertNotIn(f"APPLY_MIGRATION_{migration.upper()}", self.compose)

    def test_migrations_run_in_ascending_order(self) -> None:
        import re

        numbers = [int(n) for n in re.findall(r"migrations/0*(\d+)_", self.compose)]
        self.assertEqual(sorted(numbers), numbers, numbers)

    def test_knowledge_and_bus_audit_are_different_numbers(self) -> None:
        # The whole of G-021: two migrations under one number are two
        # competing truths.
        migrations = sorted(p.name for p in (ROOT / "postgres-init").glob("*.sql"))
        prefixes = [name.split("_", 1)[0] for name in migrations]
        self.assertEqual(len(prefixes), len(set(prefixes)), migrations)


if __name__ == "__main__":
    unittest.main()
