"""The deployment manifest has to see three kinds of trouble, not two.

Review finding G-020: the first version listed files with `find` and verified
only the entries it had listed. So a locally present secrets/ folder could be
swept into the manifest and shipped, while a stale source file already on the
NAS was ignored - "keine Abweichung" then said less than it sounded like.

These tests drive the two shell scripts for real, in a throwaway git
repository, and demand a failure for each case. A guard that has never been
shown to fail is not a guard.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1]
DEPLOY = SCRIPTS / "deploy_manifest.sh"
VERIFY = SCRIPTS / "verify_manifest.sh"


def sh(script: pathlib.Path, *args: str, cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sh", str(script), *args],
        cwd=cwd, capture_output=True, text=True, check=False,
    )


def git(*args: str, cwd: pathlib.Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True)


class DeployManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._temp.name)
        git("init", "-q", cwd=self.root)
        git("config", "user.email", "test@example.invalid", cwd=self.root)
        git("config", "user.name", "Test", cwd=self.root)
        (self.root / ".gitignore").write_text("secrets/\n*.env\n!*.env.example\n")
        package = self.root / "paket"
        package.mkdir()
        (package / "code.py").write_text("print('echt')\n")
        (package / "compose.yaml").write_text("name: t\n")
        git("add", "-A", cwd=self.root)
        git("commit", "-qm", "start", cwd=self.root)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def make(self, *paths: str, environment: dict[str, str] | None = None
             ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env.update(environment or {})
        return subprocess.run(
            ["sh", str(DEPLOY), *paths],
            cwd=self.root, capture_output=True, text=True, check=False,
            env=env,
        )

    def check(self) -> subprocess.CompletedProcess:
        return sh(VERIFY, cwd=self.root)

    # -- the good case -----------------------------------------------------
    def test_a_clean_tree_produces_a_passing_manifest(self) -> None:
        self.assertEqual(0, self.make("paket").returncode)
        result = self.check()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("RESULT: PASS", result.stdout)

    # -- G-020, first half: secrets must not reach the manifest ------------
    def test_a_local_secrets_folder_never_enters_the_manifest(self) -> None:
        secrets = self.root / "paket" / "secrets"
        secrets.mkdir()
        (secrets / "telegram_bot_token").write_text("123:GEHEIM\n")
        (self.root / "paket" / "laufzeit.env").write_text("A=B\n")

        self.assertEqual(0, self.make("paket").returncode)
        manifest = (self.root / "DEPLOY_MANIFEST.txt").read_text()
        self.assertNotIn("telegram_bot_token", manifest)
        self.assertNotIn("laufzeit.env", manifest)
        # And they are allowed to sit there without failing the check.
        self.assertIn("RESULT: PASS", self.check().stdout)

    # -- G-020, second half: stale files must be seen ----------------------
    def test_a_stale_source_file_is_reported(self) -> None:
        self.assertEqual(0, self.make("paket").returncode)
        (self.root / "paket" / "alt_von_frueher.py").write_text("print('alt')\n")
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn("UNERWARTET", result.stdout)
        self.assertIn("alt_von_frueher.py", result.stdout)
        self.assertIn("RESULT: FAIL", result.stdout)

    def test_a_stale_compose_file_is_reported(self) -> None:
        # The dangerous one: a leftover compose file is not dead weight, it can
        # be started.
        self.assertEqual(0, self.make("paket").returncode)
        (self.root / "paket" / "compose.alt.yaml").write_text("name: alt\n")
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn("compose.alt.yaml", result.stdout)

    def test_a_changed_file_is_still_reported(self) -> None:
        self.assertEqual(0, self.make("paket").returncode)
        (self.root / "paket" / "code.py").write_text("print('veraendert')\n")
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn("ABWEICHUNG", result.stdout)

    def test_a_missing_file_is_still_reported(self) -> None:
        self.assertEqual(0, self.make("paket").returncode)
        (self.root / "paket" / "code.py").unlink()
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn("FEHLT", result.stdout)

    # -- something forgotten is caught before it travels -------------------
    def test_an_uncommitted_file_blocks_the_manifest(self) -> None:
        (self.root / "paket" / "neu.py").write_text("print('vergessen')\n")
        result = self.make("paket")
        self.assertEqual(2, result.returncode)
        self.assertIn("neu.py", result.stderr)

    def test_a_dirty_tree_is_named_in_the_manifest(self) -> None:
        (self.root / "paket" / "code.py").write_text("print('geaendert')\n")
        self.assertEqual(0, self.make("paket").returncode)
        self.assertIn("dirty=yes", (self.root / "DEPLOY_MANIFEST.txt").read_text())

    def test_a_rollout_can_require_a_clean_tree(self) -> None:
        (self.root / "paket" / "code.py").write_text("print('geaendert')\n")
        result = self.make("paket", environment={"REQUIRE_CLEAN": "1"})
        self.assertEqual(2, result.returncode)
        self.assertIn("sauberen Git-Baum", result.stderr)
        self.assertFalse((self.root / "DEPLOY_MANIFEST.txt").exists())

    def test_transfer_list_is_the_same_versioned_set_plus_manifest(self) -> None:
        transfer = self.root / "transfer.txt"
        result = self.make(
            "paket",
            environment={
                "REQUIRE_CLEAN": "1",
                "DEPLOY_FILE_LIST_OUT": str(transfer),
            },
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            {"paket/code.py", "paket/compose.yaml", "DEPLOY_MANIFEST.txt"},
            set(transfer.read_text(encoding="utf-8").splitlines()),
        )


if __name__ == "__main__":
    unittest.main()
