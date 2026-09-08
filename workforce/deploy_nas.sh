#!/bin/sh
# Deploy the workforce core to the NAS. What travels is the committed tree via `git archive`
# (never a directory, never the working tree: G-020), config and secrets by scp, and the secrets get
# their group via a throwaway container because the ssh user cannot chgrp to 10001.
# Target is a constant (G-091). Nothing is deleted on the NAS.
set -eu
host="synology"
root="/volume1/docker/workforce"
docker="sudo /usr/local/bin/docker"
cd "$(dirname "$0")/.."
[ -f workforce/config.nas.json ] || { echo "FAIL: workforce/config.nas.json fehlt" >&2; exit 1; }
# Decided before anything leaves this machine (G-103). A container gets only the secret it
# uses (G-098): the model key travels, and the overlay that mounts it loads, only when the
# shipped config names a `claude` identity. Read from the config, never guessed from secrets/.
secrets="telegram_bot_token"; compose="-f compose.yaml"
# Exit 0 means claude, 1 means no claude; anything else (broken JSON, no python3) is not an
# answer and aborts (G-103) - "no" and "could not tell" must not look alike.
rc=0
python3 -c '
import json, sys
try:
    c = json.load(open(sys.argv[1]))
    claude = any(i.get("provider") == "claude" for i in c["identities"].values())
except Exception:
    sys.exit(2)   # an uncaught error would exit 1 and read as "no claude"
sys.exit(0 if claude else 1)' workforce/config.nas.json 2>/dev/null || rc=$?
case "$rc" in
  0) secrets="$secrets anthropic_api_key"; compose="$compose -f compose.claude.yaml" ;;
  1) ;;
  *) echo "FAIL: workforce/config.nas.json nicht lesbar (Exit $rc)" >&2; exit 1 ;;
esac
# What ships is the committed tree (git archive), never the working tree: another session's
# uncommitted edits under skills/ or workforce/ cannot reach the NAS by accident. Say so.
if [ -n "$(git status --porcelain -- workforce skills)" ]; then
  echo "HINWEIS: unversionierte Aenderungen unter workforce/ oder skills/ werden nicht ausgerollt:" >&2
  git status --porcelain -- workforce skills >&2
fi
archiv="$(mktemp)"
git archive --format=tar.gz -o "$archiv" HEAD workforce
ssh -o BatchMode=yes "$host" "mkdir -p '$root/secrets' && cd '$root' && tar xzf - --strip-components=1" < "$archiv"
# The skills are company assets outside the package; they land beside it as $root/skills.
git archive --format=tar.gz -o "$archiv" HEAD skills
ssh -o BatchMode=yes "$host" "cd '$root' && tar xzf -" < "$archiv"
# scp needs the SFTP subsystem, which this NAS does not offer ("Connection closed"); a file
# over ssh stdin does not. umask 027 so a secret is never world-readable, not even briefly.
ssh -o BatchMode=yes "$host" "umask 027 && cat > '$root/config.json'" < workforce/config.nas.json
for s in $secrets; do
  ssh -o BatchMode=yes "$host" "umask 027 && cat > '$root/secrets/$s'" < "workforce/secrets/$s"
done
ssh -o BatchMode=yes "$host" "cd '$root' \
  && $docker run --rm -v '$root/secrets:/s' alpine sh -c 'chgrp 10001 /s/* && chmod 640 /s/*' \
  && $docker compose $compose build -q --build-arg WORKFORCE_COMMIT=$(git rev-parse HEAD) \
  && $docker compose $compose up -d --force-recreate && $docker compose $compose ps" < /dev/null
rm -f "$archiv"
echo "RESULT: deployed $(git rev-parse --short HEAD)"
