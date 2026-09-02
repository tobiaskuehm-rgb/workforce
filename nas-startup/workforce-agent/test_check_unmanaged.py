"""G-060: top-level paths outside the deployment scope are visible."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile
import unittest

NAS = pathlib.Path(__file__).resolve().parents[1]
CHECK = NAS / "check_unmanaged.sh"


class CheckUnmanagedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        shutil.copy2(CHECK, self.root / "check_unmanaged.sh")
        (self.root / "deploy_paths.txt").write_text(
            "check_unmanaged.sh\ndeploy_paths.txt\nknown-package\n",
            encoding="utf-8",
        )
        (self.root / "known-package").mkdir()
        (self.root / "Versionen").mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", "check_unmanaged.sh"], cwd=self.root,
            text=True, capture_output=True, check=False,
        )

    def test_known_and_explained_paths_pass(self) -> None:
        result = self.run_check()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("RESULT: PASS", result.stdout)

    def test_unknown_name_with_spaces_is_one_visible_failure(self) -> None:
        (self.root / "alter code ordner").mkdir()
        result = self.run_check()
        self.assertEqual(1, result.returncode)
        self.assertIn("alter code ordner", result.stdout)
        self.assertIn("RESULT: FAIL (1)", result.stdout)


if __name__ == "__main__":
    unittest.main()
