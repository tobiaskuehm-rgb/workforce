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
                     "APPLY_MIGRATION_006_LEGACY_TABLES",
                     "APPLY_MIGRATION_007_LEAST_PRIVILEGE"):
            with self.subTest(gate=gate):
                self.assertIn(f'{gate}: "false"', self.compose)

    def test_each_migration_checks_its_own_gate(self) -> None:
        # A shared gate would couple exactly the two things the finding
        # separated.
        for gate, migration in (
            ("APPLY_MIGRATION_004_KNOWLEDGE", "004_knowledge_capability.sql"),
            ("APPLY_MIGRATION_005_BUS_DENIAL_AUDIT", "005_bus_denial_audit.sql"),
            ("APPLY_MIGRATION_006_LEGACY_TABLES", "006_legacy_registry_tables.sql"),
            ("APPLY_MIGRATION_007_LEAST_PRIVILEGE", "007_least_privilege_roles.sql"),
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


class LeastPrivilegeMigrationTest(unittest.TestCase):
    """G-025: the runtime account was superuser and owner of everything."""

    def setUp(self) -> None:
        self.sql = (ROOT / "postgres-init" / "007_least_privilege_roles.sql").read_text()

    def test_it_refuses_to_run_without_the_roles(self) -> None:
        # A login role means a password, and a password does not belong in a
        # versioned file. So the migration checks instead of creating.
        self.assertIn("MIGRATION_007_ROLE_MISSING", self.sql)
        self.assertIn("workforce_api", self.sql)
        self.assertIn("workforce_backup", self.sql)

    def test_it_refuses_a_privileged_runtime_account(self) -> None:
        # Granting narrowly to an account that is itself superuser would be
        # decoration.
        self.assertIn("MIGRATION_007_ROLE_TOO_PRIVILEGED", self.sql)
        for attribute in ("rolsuper", "rolcreaterole", "rolcreatedb", "rolbypassrls"):
            self.assertIn(attribute, self.sql)

    def test_the_api_gets_no_table_rights_in_the_bus_schema(self) -> None:
        # Everything goes through SECURITY DEFINER functions. Direct table
        # access would let the API around the append-only triggers.
        self.assertIn("REVOKE ALL ON ALL TABLES IN SCHEMA workforce FROM workforce_api",
                      self.sql)

    def test_the_grants_survive_a_closed_migration_gate(self) -> None:
        # The API calls functions from 002, 004 and 005. A static GRANT list
        # would chain this migration to exactly the gates G-031 separated.
        self.assertIn("FOREACH", self.sql)
        self.assertNotIn("GRANT EXECUTE ON FUNCTION\n", self.sql)

    def test_it_does_not_strip_superuser_silently(self) -> None:
        # Taking SUPERUSER away locks the API out if anything else is wrong.
        # It is documented as a separate step, not executed here.
        self.assertNotIn("ALTER ROLE workforce_app NOSUPERUSER;", self.sql)
        self.assertIn("NOSUPERUSER", self.sql, "der naechste Schritt muss benannt sein")

    def test_public_loses_execute_not_just_the_api_role(self) -> None:
        """G-035: the first version of this migration limited nothing.

        PostgreSQL grants EXECUTE on every function to PUBLIC by default, so
        granting it to workforce_api added nothing - measured in a restored
        copy, a role with no grant at all reached BUS_AUTH_FAILED, which means
        the function ran. Revoking from workforce_api was a no-op; the revoke
        has to hit PUBLIC.
        """
        self.assertIn("REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA workforce FROM PUBLIC",
                      self.sql)
        self.assertIn("REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC",
                      self.sql)

    def test_functions_from_later_migrations_do_not_reopen_the_hole(self) -> None:
        # 004 and 005 are behind closed gates. When one opens, its new
        # functions must not arrive with the PUBLIC default - and this
        # migration will not run again to fix that.
        self.assertIn("ALTER DEFAULT PRIVILEGES", self.sql)
        self.assertIn("REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC", self.sql)

    def test_the_backup_account_can_actually_run_pg_dump(self) -> None:
        # pg_dump reads last_value from every sequence. Table rights alone
        # produce a zero-byte dump and an error - that is what the first
        # version did, measured against a restored copy.
        self.assertIn("GRANT SELECT ON ALL SEQUENCES IN SCHEMA workforce TO workforce_backup",
                      self.sql)
        self.assertIn("GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO workforce_backup",
                      self.sql)

    def test_the_backup_account_cannot_write(self) -> None:
        self.assertIn("GRANT SELECT ON ALL TABLES IN SCHEMA workforce TO workforce_backup",
                      self.sql)
        for verb in ("INSERT", "UPDATE", "DELETE"):
            self.assertNotIn(f"GRANT {verb}", self.sql.split("workforce_backup")[-1])


class ApiUsesItsOwnRoleTest(unittest.TestCase):
    """G-035: the role existed and the stack went on using the owner."""

    def setUp(self) -> None:
        self.app = (ROOT / "workforce-api" / "app.py").read_text(encoding="utf-8")
        self.compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")

    def test_the_api_never_falls_back_to_the_owner(self) -> None:
        # A missing variable used to mean "connect as workforce_app", which
        # owns the schema, every table and every function.
        self.assertIn("WORKFORCE_DB_USER_REQUIRED", self.app)
        self.assertNotIn('user=os.environ["POSTGRES_USER"]', self.app)
        self.assertNotIn('os.environ.get("POSTGRES_USER"', self.app)

    def test_the_password_comes_from_a_file(self) -> None:
        # Project rule: secrets only in files. An environment variable is
        # readable in `docker inspect`.
        self.assertIn("WORKFORCE_DB_PASSWORD_FILE", self.app)
        self.assertNotIn('os.environ["POSTGRES_PASSWORD"]', self.app)

    def test_the_stack_actually_wires_it(self) -> None:
        self.assertIn("WORKFORCE_DB_USER: workforce_api", self.compose)
        self.assertIn("WORKFORCE_DB_PASSWORD_FILE: /run/secrets/workforce_api_db_password",
                      self.compose)
        self.assertIn("workforce_api_db_password:", self.compose)


class ApiContainerFootprintTest(unittest.TestCase):
    """G-035: what the API container is handed, not what the code reads.

    The API service used to load the whole startup.env. That `app.py` no
    longer reads POSTGRES_USER is no protection - a compromised process reads
    its own environment and connects as the owner, around every grant in
    migration 007. So the check is on the footprint, not on the source.
    """

    def setUp(self) -> None:
        import compose_scan

        self.service = compose_scan.scan(ROOT / "compose.yaml")["workforce-api"]

    def test_the_owner_secret_never_enters_the_container(self) -> None:
        self.assertEqual([], self.service.env_files,
                         "startup.env traegt POSTGRES_USER und das Eigentuemer-Passwort")
        for forbidden in ("POSTGRES_USER", "POSTGRES_PASSWORD", "WORKFORCE_API_KEY"):
            with self.subTest(key=forbidden):
                self.assertNotIn(forbidden, self.service.environment)

    def test_startup_env_is_not_mounted_either(self) -> None:
        # Removing env_file and mounting the same file would be the same hole
        # with extra steps.
        for source in self.service.volume_sources:
            self.assertNotIn("startup.env", source)

    def test_it_still_gets_what_it_needs(self) -> None:
        # Fail-closed must not mean unusable.
        for required in ("POSTGRES_DB", "WORKFORCE_DB_USER",
                         "WORKFORCE_DB_PASSWORD_FILE", "WORKFORCE_API_KEY_FILE"):
            with self.subTest(key=required):
                self.assertIn(required, self.service.environment)
        self.assertIn("workforce_api_db_password", self.service.secrets)
        self.assertIn("workforce_api_key", self.service.secrets)

    def test_the_migration_runner_still_gets_the_owner(self) -> None:
        # It legitimately needs it - migrations are DDL on the owner's schema.
        # The separation is about the API, not about everything.
        import compose_scan

        runner = compose_scan.scan(ROOT / "compose.yaml")["registry-migrate"]
        self.assertIn("startup.env", runner.env_files)


class FunctionAllowlistIsRealTest(unittest.TestCase):
    """G-035: a blanket default grant is not an allowlist."""

    def setUp(self) -> None:
        self.seven = (ROOT / "postgres-init" / "007_least_privilege_roles.sql").read_text()
        self.five = (ROOT / "postgres-init" / "005_bus_denial_audit.sql").read_text()
        self.eight = (ROOT / "postgres-init" / "008_knowledge_api_grants.sql").read_text()

    def test_no_blanket_default_grant_to_the_api(self) -> None:
        # It used to hand the API execute rights on every function a later
        # migration created - including a future administrative
        # SECURITY DEFINER function nobody decided to expose.
        self.assertNotIn("GRANT EXECUTE ON FUNCTIONS TO workforce_api", self.seven)

    def test_public_stays_revoked_by_default(self) -> None:
        # The revoke half must stay: it is what keeps a new function from
        # arriving executable by everyone.
        self.assertIn("REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC", self.seven)

    def test_each_later_migration_grants_its_own_functions(self) -> None:
        self.assertIn("GRANT EXECUTE ON FUNCTION workforce.bus_record_denial", self.five)
        self.assertIn("knowledge_create_candidate", self.eight)
        self.assertIn("GRANT EXECUTE ON FUNCTION", self.eight)

    def test_those_grants_survive_a_different_gate_order(self) -> None:
        # 005 may run before 007 has created the role. It must not fail for
        # that, and 007 grants what already exists.
        self.assertIn("IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_api')",
                      self.five)
        self.assertIn("MIGRATION_008_ROLE_MISSING", self.eight)
        self.assertIn("MIGRATION_008_REQUIRES_004", self.eight)


class ModelFallbackIsOffTest(unittest.TestCase):
    """G-036: SDK retries were off, the server-side fallback was not."""

    def setUp(self) -> None:
        self.source = (ROOT / "workforce-agent" / "providers.py").read_text(encoding="utf-8")

    def test_no_server_side_fallback_is_requested(self) -> None:
        # A policy decline used to be re-run on a second model inside the same
        # call. The worker reserves one provider call against the budget; a
        # second model run inside it is neither reservable nor blockable.
        code = "\n".join(
            line for line in self.source.splitlines()
            if not line.lstrip().startswith("#")
        )
        self.assertNotIn("fallbacks=", code)
        self.assertNotIn("server-side-fallback", code)
        self.assertNotIn("betas=", code)

    def test_a_refusal_is_still_handled_as_a_result(self) -> None:
        # Removing the fallback must not turn a refusal into a crash - the
        # worker has to be able to write an explaining answer to the bus.
        self.assertIn('stop_reason", None) == "refusal"', self.source)


class ProductionStateIsNamedTest(unittest.TestCase):
    """G-023: the running state had no reference anyone could reconstruct."""

    def setUp(self) -> None:
        self.text = (ROOT / "production_state.txt").read_text(encoding="utf-8")
        self.commit = next(
            line.split("=", 1)[1].strip()
            for line in self.text.splitlines()
            if line.startswith("PRODUCTION_COMMIT=")
        )
        self.files = [
            line.split("=", 1)[1].strip()
            for line in self.text.splitlines()
            if line.startswith("FILE=")
        ]

    def test_the_named_commit_exists(self) -> None:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{self.commit}^{{commit}}"],
            cwd=ROOT.parent, capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode,
                         f"PRODUCTION_COMMIT {self.commit} existiert nicht")

    def test_every_named_file_exists_in_that_commit(self) -> None:
        # A file listed here but absent from the commit would make the check
        # pass on a state it never verified.
        import subprocess

        self.assertTrue(self.files)
        for name in self.files:
            with self.subTest(file=name):
                result = subprocess.run(
                    ["git", "cat-file", "-e", f"{self.commit}:nas-startup/{name}"],
                    cwd=ROOT.parent, capture_output=True,
                )
                self.assertEqual(0, result.returncode, name)

    def test_the_tag_points_at_the_named_commit(self) -> None:
        import subprocess

        result = subprocess.run(
            ["git", "rev-list", "-n", "1", "produktiv-v7"],
            cwd=ROOT.parent, capture_output=True, text=True,
        )
        if result.returncode != 0:
            self.skipTest("Tag produktiv-v7 nicht vorhanden")
        tagged = result.stdout.strip()
        expected = subprocess.run(
            ["git", "rev-parse", self.commit],
            cwd=ROOT.parent, capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(expected, tagged)

    def test_the_migrations_named_here_match_the_files(self) -> None:
        # The applied migrations and the deployed migration files have to be
        # the same set, or the reference describes two different systems.
        applied = next(
            line.split("=", 1)[1].strip()
            for line in self.text.splitlines()
            if line.startswith("APPLIED_MIGRATIONS=")
        ).split(",")
        from_files = [
            name.split("/")[-1].removesuffix(".sql")
            for name in self.files if name.startswith("postgres-init/")
        ]
        self.assertEqual(sorted(applied), sorted(from_files))


if __name__ == "__main__":
    unittest.main()
