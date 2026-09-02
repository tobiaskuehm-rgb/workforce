"""G-063: one fresh parameter source must drive the whole chain window."""

from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_chain_run_config.sh"


class ChainRunConfigTest(unittest.TestCase):
    def validate(self, body: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as raw:
            path = pathlib.Path(raw) / "chain-run.env"
            path.write_text(body, encoding="utf-8")
            return subprocess.run(
                ["sh", str(VALIDATOR), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )

    def test_one_matching_fresh_pair_passes(self) -> None:
        result = self.validate(
            "CHAIN_RUN_SUFFIX=PHASE5-20260902-A\n"
            "CHAIN_TASK_ID=ENG-CHAIN-PHASE5-20260902-A\n"
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_old_suffix_is_refused(self) -> None:
        result = self.validate(
            "CHAIN_RUN_SUFFIX=CHAIN20260901\n"
            "CHAIN_TASK_ID=ENG-CHAIN-CHAIN20260901\n"
        )
        self.assertEqual(2, result.returncode)

    def test_mismatched_task_is_refused(self) -> None:
        result = self.validate(
            "CHAIN_RUN_SUFFIX=PHASE5-20260902-A\n"
            "CHAIN_TASK_ID=ENG-CHAIN-ANDERER-LAUF\n"
        )
        self.assertEqual(2, result.returncode)

    def test_extra_shell_content_is_refused_before_the_file_is_sourced(self) -> None:
        result = self.validate(
            "CHAIN_RUN_SUFFIX=PHASE5-20260902-A\n"
            "CHAIN_TASK_ID=ENG-CHAIN-PHASE5-20260902-A\n"
            "UNEXPECTED=$(dangerous-command)\n"
        )
        self.assertEqual(2, result.returncode)

    def test_compose_files_have_no_reusable_suffix_or_task(self) -> None:
        sources = "\n".join(
            (HERE / name).read_text(encoding="utf-8")
            for name in (
                "compose.chain-prepare.yaml",
                "compose.chain-run.yaml",
                "compose.chain-cleanup.yaml",
                "chain.env.example",
            )
        )
        self.assertNotIn("CHAIN20260901", sources)
        self.assertNotIn("ENG-CHAIN-20260901", sources)
        self.assertIn("${CHAIN_RUN_SUFFIX:?", sources)
        self.assertIn("${CHAIN_TASK_ID:?", sources)


if __name__ == "__main__":
    unittest.main()
