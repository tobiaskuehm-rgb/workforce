"""Guards the files that exist more than once in this repository.

Three documents are duplicated, and each duplicate is the copy one side of the
collaboration actually reads:

    CLAUDE.md          <-> AGENTS.md              Claude reads one, Codex the other
    AGENTS.md          <-> nas-startup/AGENTS.md  only the second reaches the NAS
    HANDOVER.md        <-> nas-startup/HANDOVER.md      likewise

On 2026-09-01 both NAS copies turned out to be stale - AGENTS.md by five
commits, HANDOVER.md by three sessions. Everything written into the rules had
never reached the reviewer, and nothing said so. A divergence here is silent by
nature: each side reads a file that looks complete.

Hence a test rather than a habit. It runs with the agent suite, which is the
one suite that always gets run.
"""

from __future__ import annotations

import hashlib
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

MIRRORS = (
    ("CLAUDE.md", "AGENTS.md"),
    ("AGENTS.md", "nas-startup/AGENTS.md"),
    ("HANDOVER.md", "nas-startup/HANDOVER.md"),
)


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MirroredFilesTest(unittest.TestCase):
    def test_every_mirror_is_identical(self) -> None:
        for left, right in MIRRORS:
            with self.subTest(mirror=f"{left} <-> {right}"):
                one, two = ROOT / left, ROOT / right
                self.assertTrue(one.exists(), f"{left} fehlt")
                self.assertTrue(two.exists(), f"{right} fehlt")
                self.assertEqual(
                    digest(one), digest(two),
                    f"{left} und {right} sind auseinandergelaufen - beide gehen "
                    f"immer gemeinsam, sonst prueft die Gegenseite gegen einen "
                    f"veralteten Stand",
                )

    def test_the_guard_would_notice_a_difference(self) -> None:
        # A guard that only ever compares identical files proves nothing about
        # its own ability to see a difference.
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            (base / "a").write_text("gleich\n")
            (base / "b").write_text("gleich\n")
            self.assertEqual(digest(base / "a"), digest(base / "b"))
            (base / "b").write_text("gleich\nund eine Zeile mehr\n")
            self.assertNotEqual(digest(base / "a"), digest(base / "b"))
