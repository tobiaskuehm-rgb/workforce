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
# Review finding G-020: the file list comes from **git**, not from `find`.
# `find` took every regular file under the given paths, so a locally present
# secrets/ folder or a stray *.env would have landed in the manifest and, via
# the directory-wide tar, on the NAS. Git's index is the definition of "the
# versioned source state", and everything the project treats as a secret is
# gitignored - so the exclusion is structural rather than a list to maintain.
#
# Run on the Mac, in nas-startup/, with the paths you are about to deploy:
#
#   sh deploy_manifest.sh workforce-agent postgres-init
#   tar czf - DEPLOY_MANIFEST.txt $(git ls-files -- workforce-agent postgres-init) \
#     | ssh synology "cd /volume1/docker/Startup && tar xzf - && find . -name '._*' -delete"
#   ssh synology "cd /volume1/docker/Startup && sh verify_manifest.sh"
#
# Note the tar argument list: versioned files, not whole directories. A
# directory-wide archive would carry the same unversioned files the manifest
# now excludes, which would defeat the point (G-020).

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

# Untracked but not ignored: a file somebody forgot to commit. It would be
# absent from the manifest and then flagged as unexpected on the NAS, which is
# a confusing way to learn about it. Say so here instead.
untracked="$(git ls-files --others --exclude-standard -- "$@")"
if [ -n "$untracked" ]; then
    echo "BLOCKED: unversionierte, nicht ignorierte Dateien in den Deploy-Pfaden:" >&2
    echo "$untracked" >&2
    echo "         committen oder ignorieren, dann erneut." >&2
    exit 2
fi

files="$(git ls-files -- "$@")"
if [ -z "$files" ]; then
    echo "BLOCKED: git kennt keine Dateien unter: $*" >&2
    exit 2
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

echo "$files" | while IFS= read -r file; do
    [ -f "$file" ] || continue
    printf '%s  %s\n' "$(sha256 "$file")" "$file"
done >> "$manifest"

count="$(grep -c '^[0-9a-f]\{64\}  ' "$manifest" || true)"
echo "$manifest: commit $commit, dirty=$dirty, $# Pfad(e), $count versionierte Datei(en)"

if [ "$dirty" = yes ]; then
    echo "WARNUNG: nicht committete Aenderungen im Baum - der Commit allein" >&2
    echo "         beschreibt diesen Stand nicht. Vor einem Nachweislauf committen." >&2
fi
