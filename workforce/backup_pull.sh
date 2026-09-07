#!/bin/sh
# Pull a consistent copy of the bot's state file from the NAS to this Mac (Google Drive).
# The copy is made by the container itself (`workforce backup`, SQLite backup API), then
# streamed over ssh; the NAS keeps nothing extra. Target is a constant (G-091). Verifies the
# copy with `workforce verify` locally before keeping it. Run manually or from launchd.
set -eu
host="synology"; root="/volume1/docker/workforce"; docker="sudo /usr/local/bin/docker"
ziel="$HOME/Library/CloudStorage/GoogleDrive-Tobias.kuehm@icloud.com/Meine Ablage/09_Sicherung/workforce"
mkdir -p "$ziel"
stempel="$(date +%Y-%m-%d_%H%M)"; datei="$ziel/workforce_$stempel.db"
ssh -o BatchMode=yes "$host" "cd '$root' && $docker compose exec -T workforce sh -c 'python -m workforce backup /tmp/b.db --config /etc/workforce/config.json >/dev/null && cat /tmp/b.db && rm -f /tmp/b.db'" < /dev/null > "$datei"
chmod 600 "$datei"
cd "$(dirname "$0")/.." && python3 - "$datei" <<'PY'
import sys, pathlib
sys.path.insert(0, ".")
from workforce.store import Store
s = Store(sys.argv[1]); ok, bad = s.verify_audit(); n = s._db.execute("SELECT count(*) FROM audit").fetchone()[0]
print(f"Sicherung: {pathlib.Path(sys.argv[1]).name}, {n} Auditzeilen, Kette {'intakt' if ok else 'BESCHAEDIGT ab ' + str(bad)}")
sys.exit(0 if ok else 1)
PY
ls -1t "$ziel"/workforce_*.db | tail -n +15 | xargs -I{} rm -f {}   # keep the newest 14
echo "RESULT: PASS"
