#!/bin/sh
# Deploy the workforce core to the NAS. Versioned files travel as an archive built from
# `git ls-files` (never a directory: G-020), config and secrets by scp, and the secrets get
# their group via a throwaway container because the ssh user cannot chgrp to 10001.
# Target is a constant (G-091). Nothing is deleted on the NAS.
set -eu
host="synology"
root="/volume1/docker/workforce"
docker="sudo /usr/local/bin/docker"
cd "$(dirname "$0")/.."
[ -z "$(git status --porcelain -- workforce)" ] || { echo "FAIL: workforce/ hat unversionierte Aenderungen" >&2; exit 1; }
[ -f workforce/config.nas.json ] || { echo "FAIL: workforce/config.nas.json fehlt" >&2; exit 1; }
archiv="$(mktemp)"; liste="$(mktemp)"
git ls-files workforce > "$liste"
COPYFILE_DISABLE=1 tar czf "$archiv" -T "$liste"
ssh -o BatchMode=yes "$host" "mkdir -p '$root/secrets' && cd '$root' && tar xzf - --strip-components=1" < "$archiv"
scp -q workforce/config.nas.json "$host:$root/config.json"
scp -q workforce/secrets/telegram_bot_token workforce/secrets/anthropic_api_key "$host:$root/secrets/"
ssh -o BatchMode=yes "$host" "cd '$root' \
  && $docker run --rm -v '$root/secrets:/s' alpine sh -c 'chgrp 10001 /s/* && chmod 640 /s/*' \
  && $docker compose build -q && $docker compose up -d && $docker compose ps" < /dev/null
rm -f "$archiv" "$liste"
echo "RESULT: deployed $(git rev-parse --short HEAD)"
