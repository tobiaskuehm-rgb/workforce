"""The two operational scripts, run against an ssh fake (Bauform-Zusage 3, G-099).

deploy_nas.sh runs in a throwaway clone of this repository so that `git archive HEAD` is real
and the working tree cannot leak; ssh is a script on PATH that records arguments and stdin.
backup_pull.sh gets HOME pointed at a temp dir, so its constant target lands there.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import sqlite3
import stat
import subprocess
import tarfile
import tempfile
import time
import unittest

from workforce.store import Store

REPO = pathlib.Path(__file__).resolve().parents[2]
FAKE_SSH = r'''#!/bin/sh
# Records one call: N.args (one arg per line) and N.stdin; replays FAKE_SSH_STDOUT if set.
n=$(cat "$FAKE_SSH_LOG/count" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$FAKE_SSH_LOG/count"
printf '%s\n' "$@" > "$FAKE_SSH_LOG/$n.args"
cat > "$FAKE_SSH_LOG/$n.stdin"
[ -n "${FAKE_SSH_STDOUT:-}" ] && cat "$FAKE_SSH_STDOUT"
exit 0
'''


def config_with(provider: str) -> dict:
    return {"db_path": "/var/lib/workforce/workforce.db", "secrets_dir": "/run/secrets", "allowed_chat_id": 1,
            "default_identity": "A", "identities": {"A": {"provider": provider, "model": "claude-sonnet-5" if provider == "claude" else "echo-v1",
                                                          "policy": "BODY", "system_prompt": "Hilf."}},
            "routes": [["CEO", "A"]], "max_calls_per_day": 1, "max_usd_per_day": 1.0}


class ScriptHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.log = self.tmp / "ssh"; self.log.mkdir()
        bindir = self.tmp / "bin"; bindir.mkdir()
        (bindir / "ssh").write_text(FAKE_SSH); (bindir / "ssh").chmod(0o755)
        self.env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}", FAKE_SSH_LOG=str(self.log))

    def calls(self):
        n = int((self.log / "count").read_text()) if (self.log / "count").exists() else 0
        return [((self.log / f"{i}.args").read_text().splitlines(), (self.log / f"{i}.stdin").read_bytes())
                for i in range(1, n + 1)]


class DeployTest(ScriptHarness):
    def clone(self, provider: str, *, model_key=True) -> pathlib.Path:
        clone = self.tmp / "clone"
        subprocess.run(["git", "clone", "-q", "--shared", str(REPO), str(clone)], check=True)
        secrets = clone / "workforce/secrets"; secrets.mkdir()
        (secrets / "telegram_bot_token").write_text("tg-token\n")
        if model_key:
            (secrets / "anthropic_api_key").write_text("sk-key\n")
        (clone / "workforce/config.nas.json").write_text(json.dumps(config_with(provider)))
        # The script under test is the working-tree one; the archive it ships is still the clone's HEAD.
        shutil.copy(REPO / "workforce/deploy_nas.sh", clone / "workforce/deploy_nas.sh")
        return clone

    def deploy(self, clone):
        return subprocess.run(["sh", "workforce/deploy_nas.sh"], cwd=clone, env=self.env, capture_output=True, text=True)

    def test_a_claude_config_ships_the_model_key_and_loads_the_overlay(self):
        clone = self.clone("claude")
        run = self.deploy(clone)
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn("RESULT: deployed", run.stdout)
        import hashlib
        digest = hashlib.sha256((clone / "workforce/config.nas.json").read_bytes()).hexdigest()[:12]
        self.assertIn(f"config {digest}", run.stdout)                  # G-107: the config travels under its digest
        calls = self.calls()
        streamed = {a[-1].split("/")[-1].rstrip("'"): s for a, s in calls if "cat > " in a[-1]}
        self.assertEqual(b"tg-token\n", streamed["telegram_bot_token"])
        self.assertEqual(b"sk-key\n", streamed["anthropic_api_key"])
        final = calls[-1][0][-1]
        self.assertIn("-f compose.yaml -f compose.claude.yaml up -d --force-recreate", final)
        self.assertIn("chgrp 10001", final)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=clone, capture_output=True, text=True).stdout.strip()
        self.assertIn(f"--build-arg WORKFORCE_COMMIT={head}", final)   # G-105: the image knows its commit

    def test_an_echo_config_ships_no_model_key_and_no_overlay(self):
        clone = self.clone("echo")
        run = self.deploy(clone)
        self.assertEqual(0, run.returncode, run.stderr)
        calls = self.calls()
        targets = [a[-1] for a, _ in calls if "cat > " in a[-1]]
        self.assertFalse(any("anthropic_api_key" in t for t in targets), targets)
        self.assertTrue(any("telegram_bot_token" in t for t in targets), targets)
        final = calls[-1][0][-1]
        self.assertIn("compose -f compose.yaml build", final)
        self.assertNotIn("compose.claude.yaml", final)

    def test_a_claude_config_without_the_key_file_aborts(self):
        clone = self.clone("claude", model_key=False)
        run = self.deploy(clone)
        self.assertNotEqual(0, run.returncode)
        self.assertNotIn("RESULT: deployed", run.stdout)

    def test_an_unreadable_config_aborts_instead_of_meaning_no_claude(self):
        # G-103: "no" and "could not tell" must not look alike.
        clone = self.clone("claude")
        (clone / "workforce/config.nas.json").write_text("{not json")
        run = self.deploy(clone)
        self.assertNotEqual(0, run.returncode)
        self.assertIn("nicht lesbar", run.stderr)
        self.assertEqual([], self.calls())                     # nothing reached the NAS

    def test_the_archive_is_the_committed_tree_without_secrets_or_state(self):
        clone = self.clone("claude")
        (clone / "workforce/leak.txt").write_text("uncommitted")          # working tree only
        run = self.deploy(clone)
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn("leak.txt", run.stderr)                              # named, not shipped
        archive = self.tmp / "a.tgz"; archive.write_bytes(self.calls()[0][1])
        names = tarfile.open(archive).getnames()
        self.assertTrue(any(n.endswith("workforce/app.py") for n in names))
        for forbidden in ("secrets/", "config.json", "config.nas.json", ".db", "leak.txt"):
            self.assertFalse(any(forbidden in n for n in names), (forbidden, names))


class ComposeTest(unittest.TestCase):
    def test_the_base_mounts_only_the_bot_token_and_the_overlay_only_the_model_key(self):
        base = (REPO / "workforce/compose.yaml").read_text()
        overlay = (REPO / "workforce/compose.claude.yaml").read_text()
        self.assertNotIn("anthropic", base)
        self.assertIn("telegram_bot_token", base)
        self.assertIn("anthropic_api_key", overlay)
        self.assertNotIn("telegram_bot_token", overlay)
        # The deploy script must be the one choosing, from the config it ships.
        deploy = (REPO / "workforce/deploy_nas.sh").read_text()
        self.assertIn("compose.claude.yaml", deploy)
        self.assertIn('== "claude"', deploy)


class BackupPullTest(ScriptHarness):
    def make_db(self, *, tamper=False) -> pathlib.Path:
        live = self.tmp / "live.db"
        store = Store(str(live), clock=lambda: 1_700_000_000.0)
        for i in range(3):
            store.audit("test", f"T-{i}", "NOTE", f"k{i}", {"i": i})
        copy = self.tmp / "copy.db"
        store.backup(str(copy)); store.close()
        if tamper:
            db = sqlite3.connect(str(copy)); db.execute("UPDATE audit SET payload = '{}' WHERE seq = 2"); db.commit(); db.close()
        return copy

    def pull(self, source):
        env = dict(self.env, HOME=str(self.tmp / "home"), FAKE_SSH_STDOUT=str(source))
        return subprocess.run(["sh", "workforce/backup_pull.sh"], cwd=REPO, env=env, capture_output=True, text=True)

    def target(self):
        return self.tmp / "home/Library/CloudStorage/GoogleDrive-Tobias.kuehm@icloud.com/Meine Ablage/09_Sicherung/workforce"

    def test_a_good_copy_lands_with_mode_600_and_passes(self):
        run = self.pull(self.make_db())
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn("RESULT: PASS", run.stdout)
        files = list(self.target().glob("workforce_*.db"))
        self.assertEqual(1, len(files))
        self.assertEqual(0o600, stat.S_IMODE(files[0].stat().st_mode))
        self.assertIn("compose exec -T workforce", self.calls()[0][0][-1])

    def test_a_tampered_copy_fails_loudly(self):
        run = self.pull(self.make_db(tamper=True))
        self.assertNotEqual(0, run.returncode)
        self.assertNotIn("RESULT: PASS", run.stdout)
        self.assertIn("BESCHAEDIGT", run.stdout)

    def test_rotation_keeps_the_newest_fourteen(self):
        self.target().mkdir(parents=True)
        for i in range(20):
            old = self.target() / f"workforce_2000-01-{i + 1:02d}_0000.db"
            old.write_bytes(b"x"); os.utime(old, (1_000_000 + i, 1_000_000 + i))
        run = self.pull(self.make_db())
        self.assertEqual(0, run.returncode, run.stderr)
        kept = sorted(p.name for p in self.target().glob("workforce_*.db"))
        self.assertEqual(14, len(kept))
        self.assertNotIn("workforce_2000-01-01_0000.db", kept)   # the oldest went
        self.assertTrue(any(not k.startswith("workforce_2000") for k in kept))  # the new one stayed


if __name__ == "__main__":
    unittest.main()
