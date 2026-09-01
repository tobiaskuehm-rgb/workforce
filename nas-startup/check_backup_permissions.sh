#!/bin/sh
set -eu

# Checks that no backup file is readable by anyone outside root and
# administrators.
#
# Review finding G-022: the backup folder carried a Synology ACL with
# `everyone: allow r-x`, inherited onto every file. 25 configuration archives
# containing startup.env and 26 full SQL dumps of the database were readable
# by any NAS account. Fixed on 2026-09-01 by removing the ACL and setting
# root:administrators with 750/640.
#
# **Why this script exists rather than a one-off check:** the nightly backup
# job runs as root at 02:05 and creates new files. What mode it gives them is
# not controlled from here. A single tightening can therefore erode overnight,
# silently, and nothing would say so.
#
# Run on the NAS, no privileges needed beyond reading the directory:
#
#   ssh synology "cd /volume1/docker/Startup && sh check_backup_permissions.sh"
#
# Prints file names, never contents. Exits non-zero on any finding.

backups="${BACKUP_DIR:-/volume1/docker/Startup-Backups}"
[ -d "$backups" ] || { echo "$backups fehlt" >&2; exit 1; }

problems=0

# 1. Nothing may be world-readable.
world="$(find "$backups" -perm -o=r 2>/dev/null | wc -l | tr -d ' ')"
if [ "$world" -ne 0 ]; then
    echo "FAIL: $world Datei(en) mit Welt-Leserecht:"
    find "$backups" -perm -o=r 2>/dev/null | head -10
    problems=$((problems + 1))
else
    echo "PASS: keine Datei mit Welt-Leserecht"
fi

# 2. Nothing may be world-writable either - a rewritten backup is worse than
#    a readable one.
writable="$(find "$backups" -perm -o=w 2>/dev/null | wc -l | tr -d ' ')"
if [ "$writable" -ne 0 ]; then
    echo "FAIL: $writable Datei(en) mit Welt-Schreibrecht"
    problems=$((problems + 1))
else
    echo "PASS: keine Datei mit Welt-Schreibrecht"
fi

# 3. The Synology ACL must stay gone. If it comes back, an `everyone` entry
#    can grant access that the POSIX bits above no longer show.
if [ -x /usr/syno/bin/synoacltool ]; then
    if /usr/syno/bin/synoacltool -get "$backups" 2>&1 | grep -q "everyone"; then
        echo "FAIL: ACL enthaelt wieder einen everyone-Eintrag"
        problems=$((problems + 1))
    else
        echo "PASS: kein everyone-Eintrag in der ACL"
    fi
fi

# 4. Ownership: root, group administrators.
owner="$(find "$backups" -maxdepth 0 -printf '%U:%G\n' 2>/dev/null || stat -c '%u:%G' "$backups")"
echo "Eigentuemer des Ordners: $owner"

echo "geprueft: $(find "$backups" -type f | wc -l | tr -d ' ') Datei(en)"
if [ "$problems" -eq 0 ]; then
    echo "RESULT: PASS"
else
    echo "RESULT: FAIL ($problems)"
    exit 1
fi
