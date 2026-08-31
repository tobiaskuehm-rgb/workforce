#!/bin/sh
set -eu

# Writes DEPLOY_MANIFEST.txt: which commit is being deployed, whether the tree
# was clean, and a SHA-256 for every file in the deployed paths.
#
# Review finding G-019: the ENG-008 run was documented as "commit 3686c76 plus
# three corrections". That is not a state anyone can reproduce. A deployment
# has to name exactly one thing, and a later reader has to be able to check
# that the NAS still holds it.
#
# Run on the Mac, in nas-startup/, with the paths you are about to deploy:
#
#   sh deploy_manifest.sh workforce-agent postgres-init
#   tar czf - DEPLOY_MANIFEST.txt workforce-agent postgres-init \
#     | ssh synology "cd /volume1/docker/Startup && tar xzf - && find . -name '._*' -delete"
#   ssh synology "cd /volume1/docker/Startup && sh verify_manifest.sh"
#
# The manifest travels with the files, so what is on the NAS always carries its
# own provenance - including after everyone has forgotten which window it was.

if [ "$#" -eq 0 ]; then
    echo "usage: sh deploy_manifest.sh <path> [<path> ...]" >&2
    exit 2
fi

if command -v sha256sum >/dev/null 2>&1; then
    sha256() { sha256sum "$1" | cut -d' ' -f1; }
elif command -v shasum >/dev/null 2>&1; then
    sha256() { shasum -a 256 "$1" | cut -d' ' -f1; }
else
    echo "no sha256sum and no shasum available" >&2
    exit 1
fi

commit="$(git rev-parse HEAD)"
if [ -n "$(git status --porcelain)" ]; then
    dirty=yes
else
    dirty=no
fi

manifest=DEPLOY_MANIFEST.txt
{
    echo "# Start UP deployment manifest"
    echo "commit=$commit"
    # A dirty tree is not forbidden - sometimes a run has to happen. It has to
    # be visible, which is the part that was missing.
    echo "dirty=$dirty"
    echo "created=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    echo "paths=$*"
    echo "#"
} > "$manifest"

count=0
for path in "$@"; do
    # -type f only: directories carry no content, symlinks are not used here.
    find "$path" -type f ! -name '._*' ! -name '.DS_Store' | sort | while read -r file; do
        printf '%s  %s\n' "$(sha256 "$file")" "$file"
    done >> "$manifest"
    count=$((count + 1))
done

files="$(grep -c '^[0-9a-f]\{64\}  ' "$manifest" || true)"
echo "$manifest: commit $commit, dirty=$dirty, $count Pfad(e), $files Datei(en)"

if [ "$dirty" = yes ]; then
    echo "WARNUNG: nicht committete Aenderungen im Baum - der Commit allein" >&2
    echo "         beschreibt diesen Stand nicht. Vor einem Nachweislauf committen." >&2
fi
