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
for s in telegram_bot_token anthropic_api_key; do
  ssh -o BatchMode=yes "$host" "umask 027 && cat > '$root/secrets/$s'" < "workforce/secrets/$s"
done
ssh -o BatchMode=yes "$host" "cd '$root' \
  && $docker run --rm -v '$root/secrets:/s' alpine sh -c 'chgrp 10001 /s/* && chmod 640 /s/*' \
  && $docker compose build -q && $docker compose up -d --force-recreate && $docker compose ps" < /dev/null
rm -f "$archiv"
echo "RESULT: deployed $(git rev-parse --short HEAD)"
