"""check_secret_files.sh: does the shape check actually reject bad shapes?

On 2026-09-01 the Telegram bot token was written with TextEdit, which saves
RTF by default. 433 bytes of markup went in as a token and the run failed with
an error naming Telegram. The file looked correct in every editor, and nothing
in the chain ever looked at its shape.

The script exists so that never repeats. These tests exist so the script does
not quietly stop working - a checker that passes everything is worse than none,
because it is believed.
"""

import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "check_secret_files.sh"
NAMES = ("workforce_api_db_password", "workforce_api_key",
         "workforce_backup_password")
GOOD = "K7mQp2XvR9tLbN4wZ8cF6yHj3sD5gA1eU0iO"


class SecretShapeCheckTest(unittest.TestCase):

    def run_check(self, files: dict[str, bytes]) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            secrets = pathlib.Path(tmp) / "secrets"
            secrets.mkdir()
            for name, content in files.items():
                (secrets / name).write_bytes(content)
            return subprocess.run(
                ["sh", str(SCRIPT), str(secrets)],
                capture_output=True, text=True,
            )

    def all_good(self) -> dict[str, bytes]:
        return {name: (GOOD + "\n").encode() for name in NAMES}

    def test_three_well_formed_files_pass(self) -> None:
        result = self.run_check(self.all_good())
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("RESULT: PASS", result.stdout)

    def test_a_trailing_newline_is_tolerated(self) -> None:
        # app.py strips, so the check has to strip too - otherwise it would
        # reject files that work and send someone hunting for nothing.
        files = self.all_good()
        files[NAMES[0]] = (GOOD + "\r\n").encode()
        self.assertEqual(0, self.run_check(files).returncode)

    def test_rtf_is_rejected(self) -> None:
        """The failure that actually happened, kept as a standing probe."""
        files = self.all_good()
        files[NAMES[0]] = rb"{\rtf1\ansi\ansicpg1252\cocoartf2761 \cf0 Passwort}"
        result = self.run_check(files)
        self.assertEqual(1, result.returncode)
        self.assertIn("RTF", result.stdout)

    def test_an_empty_file_is_rejected(self) -> None:
        files = self.all_good()
        files[NAMES[1]] = b""
        self.assertEqual(1, self.run_check(files).returncode)

    def test_a_missing_file_is_rejected(self) -> None:
        files = self.all_good()
        del files[NAMES[2]]
        result = self.run_check(files)
        self.assertEqual(1, result.returncode)
        self.assertIn("FEHLT", result.stdout)

    def test_a_short_password_is_rejected(self) -> None:
        files = self.all_good()
        files[NAMES[0]] = b"kurz123\n"
        self.assertEqual(1, self.run_check(files).returncode)

    def test_a_label_line_next_to_the_value_is_rejected(self) -> None:
        # "Passwort: xyz" or a comment above the value would be read whole.
        files = self.all_good()
        files[NAMES[1]] = ("# API-Schluessel\n" + GOOD + "\n").encode()
        self.assertEqual(1, self.run_check(files).returncode)

    def test_special_characters_are_reported(self) -> None:
        # Usable, but every one of them has to survive an SQL string literal
        # on the way into CREATE ROLE. Avoiding the class beats escaping it.
        files = self.all_good()
        files[NAMES[0]] = ("abc'def\"ghi$jkl;mno pqr stuvwxyz012345\n").encode()
        self.assertEqual(1, self.run_check(files).returncode)

    def test_the_check_never_prints_the_value(self) -> None:
        """The whole point: a shape report that leaks the shape's content."""
        result = self.run_check(self.all_good())
        self.assertNotIn(GOOD, result.stdout)
        self.assertNotIn(GOOD, result.stderr)

    def test_a_weakened_check_would_be_noticed(self) -> None:
        """If every case above passed, these tests would prove nothing."""
        bad = self.all_good()
        bad[NAMES[0]] = rb"{\rtf1 Passwort}"
        self.assertNotEqual(
            self.run_check(self.all_good()).returncode,
            self.run_check(bad).returncode,
            "der Pruefer unterscheidet gute und kaputte Dateien nicht mehr",
        )


if __name__ == "__main__":
    unittest.main()
