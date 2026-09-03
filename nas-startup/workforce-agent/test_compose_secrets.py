"""Guards the secret footprint of every compose file in the repository.

Review finding G-017: switching the helper containers from `env_file` to a
read-only mount took the values out of `docker inspect`, but the container
could still read the whole startup.env - five secrets where three were needed,
and the externally networked core runner got them too although it never talks
to the database.

The fix is a smaller file, not a quieter mount. These tests hold that line.
They are cheap and they are the only thing standing between the property and a
future compose file that reintroduces the mount by copy-and-paste.
"""

from __future__ import annotations

import pathlib
import unittest

import compose_scan

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The full startup.env holds five values, among them the owner role and its
# superuser password. Two services may see it:
#
#   db                the database itself is initialised from it
#   registry-migrate  migrations are DDL on the owner's schema
#
# **workforce-api was removed from this list on 2026-09-01** (review finding
# G-035). It used to load the whole file, so the owner credentials sat in the
# API container - and "app.py does not read them" is no protection when a
# compromised process can read its own environment and connect as the owner.
# It now gets the database name plus two secret files and nothing else.
#
# This test compares as an equality on purpose: it failed the moment the API
# stopped reading the file, which is how the improvement got recorded instead
# of drifting past unnoticed.
PRODUCTIVE_STACK = pathlib.Path("compose.yaml")
STACK_SERVICES_ALLOWED_FULL_ENV = {"db", "registry-migrate"}

FULL_ENV = "startup.env"
DB_ENV = "startup.db.env"

# Anything reachable from outside gets no shared secret file at all.
OUTBOUND_NETWORK = "outbound"


def _basename(reference: str) -> str:
    return reference.rsplit("/", 1)[-1]


def _secret_refs(service: compose_scan.Service) -> list[str]:
    """Shared secret files this service can read, by base name."""
    refs = [_basename(e) for e in service.env_files]
    refs += [_basename(v) for v in service.volume_sources]
    return [r for r in refs if r in (FULL_ENV, DB_ENV)]


def full_env_offenders(tree) -> list[str]:
    """Services outside the productive stack that can read the full file."""
    return [
        f"{path}:{name}"
        for path, services in tree.items()
        for name, service in services.items()
        if FULL_ENV in _secret_refs(service)
        and not (path == PRODUCTIVE_STACK and name in STACK_SERVICES_ALLOWED_FULL_ENV)
    ]


def outbound_offenders(tree) -> list[str]:
    """Services with a route outside that carry a shared secret file."""
    return [
        f"{path}:{name} -> {_secret_refs(service)}"
        for path, services in tree.items()
        for name, service in services.items()
        if OUTBOUND_NETWORK in service.networks and _secret_refs(service)
    ]


class ComposeSecretFootprintTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = compose_scan.scan_tree(ROOT)

    def test_scan_sees_the_whole_tree(self) -> None:
        # A parser that quietly reads nothing would make every other test
        # below pass. Pin the shape instead of trusting it.
        self.assertIn(PRODUCTIVE_STACK, self.tree)
        self.assertIn(pathlib.Path("workforce-agent/compose.core.yaml"), self.tree)
        self.assertGreaterEqual(len(self.tree), 20)

    def test_only_the_productive_stack_touches_the_full_startup_env(self) -> None:
        offenders = full_env_offenders(self.tree)
        self.assertEqual(
            [], offenders,
            "these services read the full startup.env; they need startup.db.env "
            "(workforce-agent/derive_db_env_once.sh)",
        )

    def test_the_productive_stack_gained_no_further_readers(self) -> None:
        stack = self.tree[PRODUCTIVE_STACK]
        readers = {n for n, s in stack.items() if FULL_ENV in _secret_refs(s)}
        self.assertEqual(STACK_SERVICES_ALLOWED_FULL_ENV, readers)

    def test_no_outbound_service_reads_a_shared_secret_file(self) -> None:
        # The heart of G-017: the core runner sat on the outbound network with
        # the database password and the API key mounted, and used neither.
        offenders = outbound_offenders(self.tree)
        self.assertEqual(
            [], offenders,
            "a service with a route to the outside must carry no shared secret "
            "file - short-lived tokens under ./secrets only",
        )

    def test_the_core_runner_mounts_nothing_but_its_tokens(self) -> None:
        run = self.tree[pathlib.Path("workforce-agent/compose.core.yaml")]["run"]
        self.assertEqual(["./secrets"], run.volume_sources)
        self.assertEqual([], run.env_files)

    def test_database_helpers_use_the_derived_file(self) -> None:
        # Every helper on the backend network that needs credentials at all
        # must take them from the three-value file.
        helpers = [
            (path, name, refs)
            for path, services in self.tree.items()
            for name, service in services.items()
            if path != PRODUCTIVE_STACK and (refs := _secret_refs(service))
        ]
        self.assertNotEqual([], helpers, "no helper found - the scan lost the tree")
        for path, name, refs in helpers:
            self.assertEqual([DB_ENV], refs, f"{path}:{name}")


# --- G-089: Echo und bezahlter Provider haben getrennte Secret-Mounts --------
#
# compose.agent.yaml listed the Anthropic key as a secret without condition,
# so an echo dry run could not start without a key file and, once it had one,
# mounted a paid credential into a container that never reads it (G-017
# class). The provider is now pinned per file, and the secret footprint has
# to match the provider that is pinned.

AGENT_FILES = (pathlib.Path("workforce-agent/compose.agent.yaml"),
               pathlib.Path("workforce-agent/compose.agent-echo.yaml"))


def pinned_provider(path: pathlib.Path, service: str) -> str | None:
    """`AGENT_PROVIDER: <x>` from the raw environment block of one service.

    compose_scan records environment *keys* only - values are none of its
    business for secrets. For this one key the value is the property, so it is
    read from the text, narrowly.
    """
    import re
    text = (ROOT / path).read_text(encoding="utf-8")
    block = text.split(f"\n  {service}:\n", 1)
    if len(block) < 2:
        return None
    body = re.split(r"\n  \S", block[1], maxsplit=1)[0]
    treffer = re.search(r"^\s+AGENT_PROVIDER:\s*(\S+)", body, re.MULTILINE)
    return treffer.group(1).strip("'\"") if treffer else None


def model_key_offenders(tree) -> list[str]:
    """Services pinned to echo that still mount a model key."""
    return [
        f"{path}:{name} -> {sorted(service.secrets)}"
        for path, services in tree.items()
        for name, service in services.items()
        if pinned_provider(path, name) == "echo"
        and any("api_key" in s for s in service.secrets)
    ]


class ProviderSecretFootprintTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = compose_scan.scan_tree(ROOT)

    def test_both_agent_files_pin_their_provider(self) -> None:
        self.assertEqual("claude", pinned_provider(AGENT_FILES[0], "workforce-agent"))
        self.assertEqual("echo", pinned_provider(AGENT_FILES[1], "workforce-agent-echo"))

    def test_the_echo_run_mounts_only_the_bus_token(self) -> None:
        echo = self.tree[AGENT_FILES[1]]["workforce-agent-echo"]
        self.assertEqual(["agent_bus_token"], echo.secrets)

    def test_the_paid_run_mounts_the_key_it_uses(self) -> None:
        paid = self.tree[AGENT_FILES[0]]["workforce-agent"]
        self.assertEqual(["agent_bus_token", "anthropic_api_key"], sorted(paid.secrets))

    def test_no_echo_service_anywhere_mounts_a_model_key(self) -> None:
        self.assertEqual([], model_key_offenders(self.tree))

    def test_the_scan_sees_the_secrets_at_all(self) -> None:
        self.assertTrue(any(s.secrets for services in self.tree.values() for s in services.values()),
                        "kein Dienst mit secrets - Scan kaputt")

    def test_a_key_on_an_echo_service_would_be_caught(self) -> None:
        tree = {AGENT_FILES[1]: {"workforce-agent-echo": compose_scan.Service(
            name="workforce-agent-echo", secrets=["agent_bus_token", "anthropic_api_key"])}}
        self.assertEqual(1, len(model_key_offenders(tree)))


class WeakenedControlIsDetectedTest(unittest.TestCase):
    """The guard has to notice when the property is broken again.

    Same idea as test_weakened_control_is_detected in the worker suite: a test
    that only ever sees the good case cannot tell a working control from a
    control that has quietly stopped applying.
    """

    def test_a_reintroduced_full_env_mount_is_reported(self) -> None:
        tree = {
            pathlib.Path("workforce-agent/compose.core.yaml"): {
                "run": compose_scan.Service(
                    name="run",
                    volume_sources=["../startup.env", "./secrets"],
                    networks=[OUTBOUND_NETWORK],
                )
            }
        }
        self.assertEqual(
            ["workforce-agent/compose.core.yaml:run"], full_env_offenders(tree)
        )
        self.assertEqual(1, len(outbound_offenders(tree)))

    def test_the_smaller_file_on_an_outbound_service_is_still_reported(self) -> None:
        # Swapping the file for the smaller one is not enough on its own: a
        # container with a route outside has no business holding either.
        tree = {
            pathlib.Path("workforce-agent/compose.core.yaml"): {
                "run": compose_scan.Service(
                    name="run",
                    volume_sources=["../startup.db.env"],
                    networks=[OUTBOUND_NETWORK],
                )
            }
        }
        self.assertEqual([], full_env_offenders(tree))
        self.assertEqual(
            ["workforce-agent/compose.core.yaml:run -> ['startup.db.env']"],
            outbound_offenders(tree),
        )

    def test_a_compose_file_the_scanner_cannot_read_is_refused(self) -> None:
        # A service assembled through a YAML anchor would come back empty, and
        # an empty service passes every check above. The scanner has to refuse
        # the file instead - a guard that cannot see is worse than none,
        # because it reports PASS.
        import pathlib as _pathlib
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = _pathlib.Path(directory) / "compose.anchored.yaml"
            path.write_text(
                "name: t\n"
                "x-base: &base\n"
                "  image: x\n"
                "services:\n"
                "  a:\n"
                "    <<: *base\n"
                "    volumes:\n"
                "      - ../startup.env:/run/startup.env:ro\n"
            )
            with self.assertRaises(ValueError):
                compose_scan.scan(path)

    def test_the_guard_says_nothing_about_a_clean_tree(self) -> None:
        tree = {
            pathlib.Path("workforce-agent/compose.core.yaml"): {
                "run": compose_scan.Service(
                    name="run", volume_sources=["./secrets"], networks=[OUTBOUND_NETWORK]
                ),
                "audit": compose_scan.Service(
                    name="audit",
                    volume_sources=["../startup.db.env"],
                    networks=["startup_backend"],
                ),
            }
        }
        self.assertEqual([], full_env_offenders(tree))
        self.assertEqual([], outbound_offenders(tree))


if __name__ == "__main__":
    unittest.main()
