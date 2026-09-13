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
# What landed is measured, not assumed (G-116): every shipped file's sha256 against the
# committed tree, checked on the NAS inside a throwaway container. Any deviation aborts.
# The manifest covers what the deploy ships: the package flat, plus skills/ as it lands
# (G-118). Both are mounted into the container, so both decide behaviour.
manifest="$(mktemp)"; unpack="$(mktemp -d)"
git archive --format=tar HEAD workforce skills | tar -xf - -C "$unpack"
# The package lands flat at the root, skills/ keeps its folder - the manifest names the paths
# as they are on the NAS, so `sha256sum -c` can be run from there.
(cd "$unpack/workforce" && find . -type f | sed 's|^\./||' | sort | while read -r f; do shasum -a 256 "$f"; done) > "$manifest"
(cd "$unpack" && find skills -type f | sort | while read -r f; do shasum -a 256 "$f"; done) >> "$manifest"
ssh -o BatchMode=yes "$host" "cd '$root' && $docker run --rm -i -v '$root:/w' -w /w alpine sha256sum -c -" < "$manifest" \
  || { echo "FAIL: ausgerollte Dateien weichen von $(git rev-parse --short HEAD) ab" >&2; rm -rf "$unpack" "$manifest" "$archiv"; exit 1; }
# A deploy adds and never removes (G-047): a file that left the tree stays on the NAS and is
# reported as unexpected. config.json and secrets/ are deliberately not versioned.
erlaubt="$(mktemp)"
{ cut -c 67- "$manifest"; printf 'config.json\n'; } | sort > "$erlaubt"
gefunden="$(ssh -o BatchMode=yes "$host" "cd '$root' && $docker run --rm -v '$root:/w' -w /w alpine find . -type f -not -path './secrets/*' | sed 's|^\./||' | sort" < /dev/null)" \
  || { echo "FAIL: Dateiliste der NAS nicht lesbar" >&2; rm -rf "$unpack" "$manifest" "$erlaubt" "$archiv"; exit 1; }
# Nach einem Deploy liegen dort Dateien. Eine leere Liste heisst nicht "nichts Unerwartetes",
# sondern "nicht gemessen" - und ein Waechter, der bei einem Fehlschlag gruen meldet, ist keiner.
[ -n "$gefunden" ] || { echo "FAIL: Dateiliste der NAS ist leer - Pruefung nicht gelaufen" >&2; rm -rf "$unpack" "$manifest" "$erlaubt" "$archiv"; exit 1; }
unerwartet="$(printf '%s\n' "$gefunden" | grep -Fxv -f "$erlaubt" || true)"
rm -f "$erlaubt"
[ -z "$unerwartet" ] || { echo "FAIL: unerwartete Dateien auf der NAS: $(printf '%s' "$unerwartet" | tr '\n' ' ')" >&2; rm -rf "$unpack" "$manifest" "$archiv"; exit 1; }
rm -rf "$unpack" "$manifest"
# Rights are set by the script, not by hand (G-115, G-108): directories 750, files 640, the
# script 750, group 10001 so the container user reads by number (G-044). Then read back.
ssh -o BatchMode=yes "$host" "cd '$root' \
  && $docker run --rm -v '$root:/w' alpine sh -c 'chgrp -R 10001 /w && find /w -type d -exec chmod 750 {} + && find /w -type f -exec chmod 640 {} + && chmod 750 /w/deploy_nas.sh'" < /dev/null
# Every secret this deploy shipped is read back, not just the first (G-117); the expectation
# is generated from $secrets, so adding a secret cannot silently skip its check.
pfade="/w /w/skills /w/secrets /w/config.json"; erwartet="750 10001 /w|750 10001 /w/skills|750 10001 /w/secrets|640 10001 /w/config.json"
for s in $secrets; do pfade="$pfade /w/secrets/$s"; erwartet="$erwartet|640 10001 /w/secrets/$s"; done
rechte="$(ssh -o BatchMode=yes "$host" "cd '$root' && $docker run --rm -v '$root:/w' alpine stat -c '%a %g %n' $pfade" < /dev/null | tr '\n' '|' | sed 's/|$//')"
[ "$rechte" = "$erwartet" ] || { echo "FAIL: Rechte auf der NAS: $rechte" >&2; rm -f "$archiv"; exit 1; }
# A mode of 750 says nothing while a DSM ACL grants more (G-117). synoacltool runs on the NAS
# itself, not in a container; "no archive" means the path carries no ACL beyond the mode.
# Die Antwort traegt eine Marke je Pfad, damit "keine ACL" von "nicht gemessen" unterscheidbar
# ist: fehlt synoacltool oder scheitert der Aufruf, kommt keine Marke und der Deploy bricht ab.
# Zwei Dinge sind am 2026-09-13 auf der NAS gemessen worden, beide nicht selbstverstaendlich:
# synoacltool liegt nicht im PATH einer nicht-interaktiven Sitzung (voller Pfad noetig, wie bei
# docker), und seine ACL-Zeilen beginnen mit einem Tabulator - ein Muster mit " *" findet sie
# nicht und meldet 0, wo 8 stehen. Gegen /volume1/docker gemessen: 8 Eintraege, gegen unsere
# eigenen Pfade 0.
rc=0
acl="$(ssh -o BatchMode=yes "$host" "[ -x /usr/syno/bin/synoacltool ] || exit 9; for p in '$root' '$root/secrets' '$root/config.json'; do n=\$(/usr/syno/bin/synoacltool -get \"\$p\" 2>/dev/null | grep -c '^[[:space:]]*\[[0-9]' || true); printf 'ACL:%s ' \"\$n\"; done" < /dev/null)" || rc=$?
case "$rc:$acl" in
  "0:ACL:0 ACL:0 ACL:0 ") : ;;
  "9:"*) echo "FAIL: /usr/syno/bin/synoacltool fehlt auf der NAS - ACL nicht pruefbar" >&2; rm -f "$archiv"; exit 1 ;;
  *) echo "FAIL: ACL auf der NAS nicht wie erwartet (Exit $rc): $acl" >&2; rm -f "$archiv"; exit 1 ;;
esac
ssh -o BatchMode=yes "$host" "cd '$root' \
  && $docker compose $compose build -q --build-arg WORKFORCE_COMMIT=$(git rev-parse HEAD) \
  && $docker compose $compose up -d --force-recreate && $docker compose $compose ps" < /dev/null
rm -f "$archiv"
# The config is not versioned (G-107); its digest is the name it travels under - the same
# digest the container writes into its STARTUP audit row.
echo "RESULT: deployed $(git rev-parse --short HEAD) config $(shasum -a 256 workforce/config.nas.json | cut -c1-12)"
