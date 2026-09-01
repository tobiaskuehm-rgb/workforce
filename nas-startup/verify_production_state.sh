#!/bin/sh
set -eu

# Compares the running NAS production files against a named git commit.
#
# Review finding G-023 said the running API and compose files match no commit
# of this repository. Measured on 2026-09-01, that is **not** the case: all six
# production files match commit ff2d32a exactly. The valid half of the finding
# is the other one - no manifest covered the production paths, so a PASS on
# the deploy manifest said nothing about what is actually running.
#
# This closes that without deploying anything: it runs on the Mac, reads the
# hashes from git and compares them over ssh. Nothing is written to the NAS.
#
#   cd nas-startup && sh verify_production_state.sh
#   sh verify_production_state.sh <commit>     # against a different reference
#
# Prints file names and short hashes, never file contents.

commit="${1:-$(sed -n 's/^PRODUCTION_COMMIT=//p' production_state.txt)}"
host="${PRODUCTION_HOST:-synology}"
root="${PRODUCTION_ROOT:-/volume1/docker/Startup}"

[ -n "$commit" ] || { echo "kein Referenz-Commit angegeben" >&2; exit 2; }
git rev-parse --verify --quiet "$commit^{commit}" >/dev/null \
    || { echo "Commit $commit existiert nicht" >&2; exit 2; }

# The files that make up the running system. Deliberately explicit: a glob
# would quietly stop covering something that was added later.
files="$(sed -n 's/^FILE=//p' production_state.txt)"
[ -n "$files" ] || { echo "production_state.txt nennt keine Dateien" >&2; exit 2; }

echo "Referenz: $commit"
echo "Ziel:     $host:$root"
echo

mismatch=0
checked=0
for file in $files; do
    expected="$(git show "$commit:nas-startup/$file" 2>/dev/null | shasum -a 256 | cut -d' ' -f1 || true)"
    if [ -z "$expected" ]; then
        echo "FEHLT IM COMMIT  $file"
        mismatch=$((mismatch + 1))
        continue
    fi
    actual="$(ssh -o BatchMode=yes "$host" "sha256sum $root/$file 2>/dev/null | cut -d' ' -f1" || true)"
    checked=$((checked + 1))
    if [ -z "$actual" ]; then
        echo "FEHLT AUF NAS    $file"
        mismatch=$((mismatch + 1))
    elif [ "$actual" != "$expected" ]; then
        echo "ABWEICHUNG       $file"
        echo "                 erwartet $(echo "$expected" | cut -c1-16), gefunden $(echo "$actual" | cut -c1-16)"
        mismatch=$((mismatch + 1))
    else
        echo "OK               $file"
    fi
done

echo
echo "geprueft: $checked Datei(en), abweichend oder fehlend: $mismatch"
if [ "$mismatch" -eq 0 ]; then
    echo "RESULT: PASS - der laufende Stand ist $commit"
else
    echo "RESULT: FAIL - der laufende Stand ist nicht $commit"
    exit 1
fi
