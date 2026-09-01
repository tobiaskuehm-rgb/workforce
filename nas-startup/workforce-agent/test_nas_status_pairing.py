"""The fallback-point report has to check the pair it names.

Review finding G-043 corrected the runbook; this guards the repair that came
with it. `nas_status.sh` used to print "zugehoeriger Rollen-Dump" and then
show whichever globals dump was newest - the word asserted a relationship the
script never checked. A restore needs the pair (`G-024`: without the roles
dump it stops at `role "workforce_app" does not exist`), so a globals file
from another day is not an answer, it is a false one.

The block is extracted from the script rather than retyped, for the same
reason `g041_empty_volume_test.py` extracts its runner from compose.yaml: a
copy tests the copy. It runs against fixture directories, so no network, no
credentials, no NAS.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "nas-startup" / "nas_status.sh"

START = 'echo "--- Rueckfallpunkte ---"'
END = 'newest "$backups/rollback-*.tar.gz" "neuestes Rollback-Image"'


def fallback_block() -> str:
    text = SCRIPT.read_text(encoding="utf-8")
    start = text.index(START)
    end = text.index(END) + len(END)
    return "problems=0\n" + text[start:end] + '\necho "problems=$problems"\n'


def run_against(names: list[str]) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        (base / "Startup-Backups").mkdir()
        (base / "Startup").mkdir()
        for name in names:
            (base / "Startup-Backups" / name).touch()
        script = base / "Startup" / "block.sh"
        script.write_text(fallback_block(), encoding="utf-8")
        return subprocess.run(["sh", "block.sh"], cwd=base / "Startup",
                              capture_output=True, text=True, check=False).stdout


class FallbackPairTest(unittest.TestCase):
    def test_a_complete_pair_passes(self) -> None:
        out = run_against(["preflight-2026-09-01_10-00-00.sql",
                           "preflight-2026-09-01_10-00-00.globals.sql"])
        self.assertIn("zugehoeriger Rollen-Dump: preflight-2026-09-01_10-00-00.globals.sql", out)
        self.assertIn("problems=0", out)

    def test_a_globals_dump_from_another_run_is_not_accepted(self) -> None:
        # Exactly what the old version reported as "zugehoerig".
        out = run_against(["preflight-2026-09-01_10-00-00.sql",
                           "preflight-2026-08-30_09-00-00.globals.sql"])
        self.assertIn("FEHLT zu preflight-2026-09-01_10-00-00.sql", out)
        self.assertIn("problems=1", out)

    def test_no_dump_at_all_is_not_a_finding(self) -> None:
        # Before the first backup there is nothing to pair; that is a state,
        # not a defect, and a report that cried FAIL here would be ignored.
        out = run_against([])
        self.assertIn("kein Dump, also kein Paar", out)
        self.assertIn("problems=0", out)

    def test_the_database_dump_is_not_confused_with_the_globals_dump(self) -> None:
        # `preflight-*.sql` also matches `preflight-*.globals.sql`, and the
        # latter sorts later.
        out = run_against(["preflight-2026-09-01_10-00-00.sql",
                           "preflight-2026-09-01_10-00-00.globals.sql"])
        self.assertIn("neuester Preflight-Dump: preflight-2026-09-01_10-00-00.sql", out)


class ExtractionTest(unittest.TestCase):
    def test_the_block_is_still_where_this_test_looks(self) -> None:
        block = fallback_block()
        self.assertIn("zugehoeriger Rollen-Dump", block)
        self.assertIn("globals.sql", block)


if __name__ == "__main__":
    unittest.main()
