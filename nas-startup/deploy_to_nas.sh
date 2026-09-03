#!/bin/sh
set -eu

# Deploys the versioned files to the NAS - the three documented steps from
# HANDOVER.md in one place, so the procedure lives in the repo instead of a
# code block that has to be pasted by hand (G-047: what fills production
# belongs in the repo; G-052: a list that exists only in a terminal is not
# versioned).
#
#   sh deploy_to_nas.sh          # from anywhere; the script cds to its folder
#
# Fails closed at every step: a dirty tree produces no manifest and therefore
# no transfer (G-064); a failed transfer skips the verification; a failed
# verification exits 1. The list of files comes from deploy_manifest.sh, so
# transfer and manifest cover exactly the same set - never a whole directory
# (G-020).
#
# It never deletes anything on the NAS (guardrail 22): a renamed or removed
# file stays there and verify_manifest.sh reports it as UNERWARTET. That
# report is the signal, not a failure of this script.

cd "$(dirname "$0")"
host="${PRODUCTION_HOST:-synology}"
root="${PRODUCTION_ROOT:-/volume1/docker/Startup}"

liste="$(mktemp)"
trap 'rm -f "$liste"' EXIT

echo "== 1/3 Manifest (verlangt sauberen Arbeitsbaum)"
REQUIRE_CLEAN=1 DEPLOY_FILE_LIST_OUT="$liste" sh deploy_manifest.sh

echo "== 2/3 Transfer nach $host:$root"
# COPYFILE_DISABLE keeps macOS resource forks out of the archive; the find
# removes any ._* file that slipped through. The list goes in via -T, never
# via $(...): zsh would hand the whole list over as one argument.
COPYFILE_DISABLE=1 tar czf - -T "$liste" \
  | ssh -o BatchMode=yes "$host" "cd '$root' && tar xzf - && find . -name '._*' -delete"

echo "== 3/3 Pruefung auf der NAS"
ssh -o BatchMode=yes "$host" \
  "cd '$root' && grep -qx 'dirty=no' DEPLOY_MANIFEST.txt && sh verify_manifest.sh && sh check_unmanaged.sh"
