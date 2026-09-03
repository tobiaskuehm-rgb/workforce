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
# Fails closed at every step, and each step is its own command so that the
# exit status is the status of that step (review finding G-080): a dirty tree
# produces no manifest and therefore no archive (G-064); the archive is built
# completely in a local temp file before anything is sent, so a local tar
# error is a plain non-zero exit and never reaches ssh - no pipeline, no
# `pipefail`, which POSIX sh does not have; a failed transfer skips the
# verification; a failed verification exits 1. The list of files comes from
# deploy_manifest.sh, so transfer and manifest cover exactly the same set -
# never a whole directory (G-020).
#
# It never deletes anything on the NAS, and since G-080 that sentence is true:
# the first version ran `find . -name '._*' -delete` over the whole target
# folder after unpacking - a recursive delete whose targets did not come from
# the manifest and could have hit runtime or secret paths that are deliberately
# not deployed. COPYFILE_DISABLE=1 keeps those macOS resource forks out of the
# archive at the source, which is the only place they can be prevented. A
# renamed or removed file therefore stays on the NAS and verify_manifest.sh
# reports it as UNERWARTET (guardrail 22); that report is the signal, not a
# failure of this script, and cleaning it up is a visible maintenance step
# of its own.

cd "$(dirname "$0")"
host="${PRODUCTION_HOST:-synology}"
root="${PRODUCTION_ROOT:-/volume1/docker/Startup}"

liste="$(mktemp)"
archiv="$(mktemp)"
trap 'rm -f "$liste" "$archiv"' EXIT

echo "== 1/3 Manifest (verlangt sauberen Arbeitsbaum)"
REQUIRE_CLEAN=1 DEPLOY_FILE_LIST_OUT="$liste" sh deploy_manifest.sh

echo "== 2/3 Archiv lokal bauen, dann nach $host:$root uebertragen"
# The list goes in via -T, never via $(...): zsh would hand the whole list
# over as one argument. The archive is complete before ssh starts.
COPYFILE_DISABLE=1 tar czf "$archiv" -T "$liste"
ssh -o BatchMode=yes "$host" "cd '$root' && tar xzf -" < "$archiv"

echo "== 3/3 Pruefung auf der NAS"
ssh -o BatchMode=yes "$host" \
  "cd '$root' && grep -qx 'dirty=no' DEPLOY_MANIFEST.txt && sh verify_manifest.sh && sh check_unmanaged.sh"
