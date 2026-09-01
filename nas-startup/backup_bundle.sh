#!/bin/sh
set -eu

# Copies the complete git history to the NAS as a single file.
#
# Why this exists: the repository has no remote and lived on exactly one Mac.
# The NAS held only deployed files - no history, no commit messages, no
# reasoning. A lost or replaced machine would have taken all of it. That is a
# bigger risk than any single finding in the review log.
#
# A bundle rather than a real remote, because the NAS has no git: it cannot run
# git-receive-pack, so `git push` is impossible. A bundle needs nothing on the
# far side but storage.
#
# Run from nas-startup/ after committing:
#
#   sh backup_bundle.sh
#
# Restore on another machine (needs only ssh access to the NAS):
#
#   ssh synology "cat /volume1/docker/git/workforce.bundle" > workforce.bundle
#   git clone workforce.bundle "workorce claude"
#
# The bundle carries only what git tracks, so gitignored secrets stay out by
# construction - the same argument that makes the deploy manifest safe (G-020).
#
# Once the DSM package "Git Server" is installed this becomes unnecessary:
# a real remote over ssh replaces it, and `git push` keeps itself current.

target="${BUNDLE_TARGET:-/volume1/docker/git/workforce.bundle}"
host="${BUNDLE_HOST:-synology}"
local_bundle="$(mktemp -t workforce-bundle)"
trap 'rm -f "$local_bundle"' EXIT

git bundle create "$local_bundle" --all >/dev/null 2>&1
git bundle verify "$local_bundle" >/dev/null

if command -v sha256sum >/dev/null 2>&1; then
    sha256() { sha256sum "$1" | cut -d' ' -f1; }
else
    sha256() { shasum -a 256 "$1" | cut -d' ' -f1; }
fi
here="$(sha256 "$local_bundle")"

ssh "$host" "mkdir -p $(dirname "$target") && cat > $target" < "$local_bundle"
there="$(ssh "$host" "sha256sum $target | cut -d' ' -f1")"

if [ "$here" != "$there" ]; then
    echo "FAIL: Pruefsumme weicht ab - lokal $here, NAS $there" >&2
    exit 1
fi

echo "PASS: $target"
echo "  Commit:     $(git rev-parse --short HEAD)"
echo "  Groesse:    $(wc -c < "$local_bundle" | tr -d ' ') Bytes"
echo "  Pruefsumme: $here"
