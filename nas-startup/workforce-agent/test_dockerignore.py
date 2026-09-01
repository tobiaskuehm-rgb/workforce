"""Every build context must refuse the files that must not travel.

Review finding G-026: Docker sends the whole context directory to the daemon
before it reads the Dockerfile. A secret the Dockerfile never COPYs still
reaches the builder and the cache. Four contexts had no `.dockerignore` at all.

These tests do not read the files as text - they apply the patterns the way
Docker does, against names that have actually shown up in this project.
"""

from __future__ import annotations

import fnmatch
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTEXTS = ("workforce-api", "workforce-agent", "telegram-connector", "chain-test")

# Names taken from what really exists here, not invented for the test.
MUST_BE_IGNORED = (
    "secrets/telegram_bot_token",
    "secrets/chain_token_agent",
    "secrets/agent_bus_token",
    "chain.env",
    "agent.chain.env",
    "telegram-realtest.env",
    "state.sqlite3",
    "worker_core.sqlite3",
    "__pycache__/app.cpython-313.pyc",
    "DEPLOY_MANIFEST.txt",
    "workforce.bundle",
    "anthropic_api_key",
    ".DS_Store",
)

# These have to survive, or the image is empty.
MUST_SURVIVE = (
    "app.py", "agent_worker.py", "telegram_connector.py", "bus_client.py",
    "Dockerfile", "compose.yaml", "chain.env.example",
)


def ignored(patterns: list[str], name: str) -> bool:
    """Docker's rules, reduced to what these files use: globs and ! negation."""
    decision = False
    for pattern in patterns:
        negated = pattern.startswith("!")
        candidate = pattern[1:] if negated else pattern
        directory = candidate.endswith("/")
        candidate = candidate.rstrip("/")
        hit = (
            fnmatch.fnmatch(name, candidate)
            or fnmatch.fnmatch(pathlib.PurePath(name).name, candidate)
            or (directory and name.startswith(candidate + "/"))
        )
        if hit:
            decision = not negated
    return decision


def patterns_of(context: str) -> list[str]:
    path = ROOT / context / ".dockerignore"
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


class DockerignoreTest(unittest.TestCase):
    def test_every_build_context_has_one(self) -> None:
        for context in CONTEXTS:
            with self.subTest(context=context):
                self.assertTrue((ROOT / context / ".dockerignore").is_file())

    def test_secrets_state_and_environment_never_travel(self) -> None:
        for context in CONTEXTS:
            patterns = patterns_of(context)
            for name in MUST_BE_IGNORED:
                with self.subTest(context=context, file=name):
                    self.assertTrue(
                        ignored(patterns, name),
                        f"{name} wuerde in den Buildkontext von {context} gelangen",
                    )

    def test_the_source_still_gets_through(self) -> None:
        # A .dockerignore that excludes everything would pass the test above
        # and produce an unusable image.
        for context in CONTEXTS:
            patterns = patterns_of(context)
            for name in MUST_SURVIVE:
                with self.subTest(context=context, file=name):
                    self.assertFalse(ignored(patterns, name))

    def test_example_files_are_explicitly_kept(self) -> None:
        # *.env is excluded, *.env.example must not be - the examples are the
        # only documentation of what a runtime file has to contain.
        for context in CONTEXTS:
            with self.subTest(context=context):
                self.assertFalse(ignored(patterns_of(context), "workforce-agent.env.example"))
