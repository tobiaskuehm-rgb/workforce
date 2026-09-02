"""The runtime images must contain every local module their entrypoint imports.

G-061 was invisible to the unit suite because tests import from the host tree,
while Docker copies an explicit subset. This test reconstructs that subset in
a temporary directory and imports the real entrypoint there. It needs neither
Docker nor a network and fails with the same ModuleNotFoundError as the image.
"""

from __future__ import annotations

import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent
RUNBOOK = ROOT.parent / "PHASE5_RUNBOOK.md"


def copied_python_files(dockerfile: pathlib.Path) -> list[str]:
    text = dockerfile.read_text(encoding="utf-8").replace("\\\n", " ")
    files: list[str] = []
    for line in text.splitlines():
        if not line.startswith("COPY "):
            continue
        parts = shlex.split(line)
        sources = [part for part in parts[1:-1] if not part.startswith("--")]
        files.extend(part for part in sources if part.endswith(".py"))
    return files


def command_module(dockerfile: pathlib.Path) -> str:
    text = dockerfile.read_text(encoding="utf-8")
    match = re.search(r'^CMD \["python", "/app/([a-z0-9_]+)\.py"\]$', text, re.M)
    if not match:
        raise AssertionError(f"no Python CMD in {dockerfile.name}")
    return match.group(1)


class RuntimeImageImportTest(unittest.TestCase):
    def assert_runtime_imports(self, dockerfile_name: str) -> None:
        dockerfile = ROOT / dockerfile_name
        copied = copied_python_files(dockerfile)
        self.assertTrue(copied, f"{dockerfile_name} copies no Python files")

        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory)
            for relative in copied:
                shutil.copy2(ROOT / relative, target / pathlib.Path(relative).name)
            result = subprocess.run(
                [sys.executable, "-c", f"import {command_module(dockerfile)}"],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_agent_image_entrypoint_imports_from_its_copy_set(self) -> None:
        self.assert_runtime_imports("Dockerfile")

    def test_worker_core_entrypoint_imports_from_its_copy_set(self) -> None:
        self.assert_runtime_imports("Dockerfile.workercore")

    def test_runbook_builds_both_real_images_before_opening_the_window(self) -> None:
        runbook = RUNBOOK.read_text(encoding="utf-8")
        builds = runbook.index("### 4.1 Beide Agent-Images bauen")
        opens = runbook.index("## 5. Netzweg öffnen")
        self.assertLess(builds, opens)
        self.assertIn("-f Dockerfile .", runbook[builds:opens])
        self.assertIn("-f Dockerfile.workercore .", runbook[builds:opens])
        self.assertIn("-c 'import agent_worker'", runbook[builds:opens])
        self.assertIn("-c 'import worker_core_test'", runbook[builds:opens])
        self.assertIn("docker image rm", runbook[builds:opens])


if __name__ == "__main__":
    unittest.main()
