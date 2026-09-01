#!/bin/sh
set -eu

# Checks that the deployed paths hold exactly the manifested source state.
#
# Three questions, and the third is the one review finding G-020 was about:
#
#   1. Is every manifested file present?      (fehlend)
#   2. Is every manifested file unchanged?    (abweichend)
#   3. Is anything there that does NOT belong? (unerwartet)
#
# The earlier version asked only the first two. "108 Dateien, keine Abweichung"
# then proved those 108 were intact - not that the directories held only them.
# Since the deployment untars into existing folders and never removes anything,
# a source or compose file from an older package could sit there unnoticed and
# still be picked up by a compose run.
#
# What may legitimately be there without being manifested is listed once, in
# `allowed()` below, and nowhere else. Anything outside that list fails.
#
# Run on the NAS after deploying, and again before any run that is going to
# become evidence:
#
#   cd /volume1/docker/Startup && sh verify_manifest.sh
#
# Prints file names, never file contents.

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

# The only files allowed to exist in a deployed path without being manifested.
# Deliberately short and deliberately here rather than spread out: every entry
# is something the NAS legitimately holds and git legitimately does not.
allowed() {
    case "$1" in
        secrets/*|*/secrets/*)         return 0 ;;  # tokens, placed by hand
        *.env)                         return 0 ;;  # runtime configuration
        *.rtf.bak)                     return 0 ;;  # rescued secret, deleted at cleanup
        __pycache__/*|*/__pycache__/*) return 0 ;;
        *.pyc)                         return 0 ;;
        ._*|*/._*|.DS_Store|*/.DS_Store) return 0 ;;  # AppleDouble from the share
        DEPLOY_MANIFEST.txt)           return 0 ;;
        *) return 1 ;;
    esac
}

sed -n 's/^commit=/commit:   /p;s/^dirty=/dirty:    /p;s/^created=/erstellt: /p;s/^paths=/pfade:    /p' "$manifest"

paths="$(sed -n 's/^paths=//p' "$manifest")"
[ -n "$paths" ] || { echo "$manifest nennt keine Pfade" >&2; exit 1; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

grep '^[0-9a-f]\{64\}  ' "$manifest" | sed 's/^[0-9a-f]\{64\}  //' | sort > "$work/soll"

# The loops run in pipelines, so their variables live in subshells. Findings go
# to files rather than to variables that would not survive.
grep '^[0-9a-f]\{64\}  ' "$manifest" | while IFS= read -r line; do
    expected="${line%%  *}"
    file="${line#*  }"
    if [ ! -f "$file" ]; then
        echo "FEHLT       $file" >> "$work/findings"
    elif [ "$(sha256 "$file")" != "$expected" ]; then
        echo "ABWEICHUNG  $file" >> "$work/findings"
    fi
done

# What is actually there, minus what the manifest lists, minus what is allowed.
# shellcheck disable=SC2086 - paths is a deliberate word list
find $paths -type f 2>/dev/null | sed 's|^\./||' | sort > "$work/ist"
comm -23 "$work/ist" "$work/soll" | while IFS= read -r file; do
    allowed "$file" || echo "UNERWARTET  $file" >> "$work/findings"
done

total="$(wc -l < "$work/soll" | tr -d ' ')"
touch "$work/findings"
problems="$(wc -l < "$work/findings" | tr -d ' ')"

[ "$problems" -eq 0 ] || sort "$work/findings"
echo "manifestiert: $total Datei(en); fehlend, abweichend oder unerwartet: $problems"

if [ "$problems" -eq 0 ]; then
    echo "RESULT: PASS"
else
    echo "RESULT: FAIL"
    exit 1
fi
