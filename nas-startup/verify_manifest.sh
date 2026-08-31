#!/bin/sh
set -eu

# Checks that the files on this machine still match DEPLOY_MANIFEST.txt.
#
# Review finding G-019: a run that becomes evidence has to name the exact
# source state it ran on. The manifest names it; this checks the claim is
# still true.
#
# Run on the NAS after deploying, and again before any run that is going to
# become evidence:
#
#   cd /volume1/docker/Startup && sh verify_manifest.sh
#
# Exits non-zero on any difference. Prints file names, never file contents.

manifest="${1:-DEPLOY_MANIFEST.txt}"
[ -r "$manifest" ] || { echo "$manifest fehlt" >&2; exit 1; }

if command -v sha256sum >/dev/null 2>&1; then
    sha256() { sha256sum "$1" | cut -d' ' -f1; }
elif command -v shasum >/dev/null 2>&1; then
    sha256() { shasum -a 256 "$1" | cut -d' ' -f1; }
else
    echo "no sha256sum and no shasum available" >&2
    exit 1
fi

sed -n 's/^commit=/commit:   /p;s/^dirty=/dirty:    /p;s/^created=/erstellt: /p;s/^paths=/pfade:    /p' "$manifest"

# The check loop runs in a pipeline, so its variables live in a subshell. The
# findings go to a file rather than to variables that would not survive.
findings="$(mktemp)"
trap 'rm -f "$findings"' EXIT

grep '^[0-9a-f]\{64\}  ' "$manifest" | while IFS= read -r line; do
    expected="${line%%  *}"
    file="${line#*  }"
    if [ ! -f "$file" ]; then
        echo "FEHLT      $file" >> "$findings"
    elif [ "$(sha256 "$file")" != "$expected" ]; then
        echo "ABWEICHUNG $file" >> "$findings"
    fi
done

total="$(grep -c '^[0-9a-f]\{64\}  ' "$manifest")"
differing="$(wc -l < "$findings" | tr -d ' ')"

[ "$differing" -eq 0 ] || cat "$findings"
echo "geprueft: $total Datei(en), abweichend oder fehlend: $differing"

# A file present on the NAS but absent from the manifest is not an error here -
# the manifest covers the deployed paths, and secrets and state deliberately
# stay out of it.

if [ "$differing" -eq 0 ]; then
    echo "RESULT: PASS"
else
    echo "RESULT: FAIL"
    exit 1
fi
