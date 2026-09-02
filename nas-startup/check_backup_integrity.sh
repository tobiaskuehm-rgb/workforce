#!/bin/sh
set -eu

# Is the newest backup one you could actually restore from?
#
# The nightly task writes:
#
#   docker exec startup-db-1 pg_dump -U workforce_app -d workforce > "$BACKUP_DIR/..."
#
# The redirection is done by the task's shell. If `docker exec` fails - wrong
# container name, container not healthy yet, database not up - the file is
# created anyway, empty or truncated, and the task carries on to write the
# config archive. Nothing says a word. The gap is not theoretical here: the NAS
# powers on at 02:00 and this runs at 02:05, so the database has five minutes
# to become healthy.
#
# `check_backup_permissions.sh` answers "may the wrong people read it". This
# one answers "is there anything worth reading". Both are needed; neither
# implies the other.
#
# What makes a plain pg_dump complete is not its size. It is the trailer that
# pg_dump writes last, plus - since 17.x - a `\unrestrict` matching the
# `\restrict` it opens with. A dump cut off in the middle has neither. Checked
# against the real output of pg_dump 17.10 on this NAS, not from memory.
#
# Reads only; prints names, sizes and ages, never contents. Needs no root: the
# files are 640 root:administrators and TOBKUM is in that group.
#
#   ssh synology "cd /volume1/docker/Startup && sh check_backup_integrity.sh"

backups="${BACKUP_DIR:-/volume1/docker/Startup-Backups}"
max_age_hours="${BACKUP_MAX_AGE_HOURS:-26}"
min_ratio_percent="${BACKUP_MIN_RATIO_PERCENT:-50}"

[ -d "$backups" ] || { echo "$backups fehlt" >&2; exit 1; }

problems=0

fail() {
    echo "FAIL: $1"
    problems=$((problems + 1))
}

# `workforce-*.sql` also matches nothing else here, but the preflight dumps
# carry their own prefix on purpose - this check is about the nightly job.
newest_dump="$(ls -1t "$backups"/workforce-*.sql 2>/dev/null | head -1 || true)"
previous_dump="$(ls -1t "$backups"/workforce-*.sql 2>/dev/null | sed -n '2p' || true)"

if [ -z "$newest_dump" ]; then
    fail "kein Datenbank-Dump im Ordner"
else
    echo "neuester Dump: $(basename "$newest_dump")"

    age_seconds="$(( $(date +%s) - $(date -r "$newest_dump" +%s) ))"
    age_hours="$(( age_seconds / 3600 ))"
    if [ "$age_hours" -gt "$max_age_hours" ]; then
        fail "Dump ist ${age_hours}h alt (erlaubt: ${max_age_hours}h) - lief der Job?"
    else
        echo "PASS: Alter ${age_hours}h"
    fi

    # The trailer pg_dump writes last. Its absence is the signature of a dump
    # that was cut off - which is exactly what a failed `docker exec` leaves
    # behind, because the shell created the file before the command ran.
    if [ "$(grep -c '^-- PostgreSQL database dump complete$' "$newest_dump" || true)" -eq 1 ]; then
        echo "PASS: Abschlusszeile vorhanden"
    else
        fail "Abschlusszeile fehlt - der Dump ist abgeschnitten oder leer"
    fi

    # pg_dump 17.x wraps its output. An opening \restrict without its closing
    # counterpart means the same thing, and catches a file truncated after the
    # trailer would have been.
    opened="$(grep -c '^\\restrict ' "$newest_dump" || true)"
    closed="$(grep -c '^\\unrestrict ' "$newest_dump" || true)"
    if [ "$opened" -ne "$closed" ]; then
        fail "restrict/unrestrict unpaarig ($opened/$closed)"
    else
        echo "PASS: restrict/unrestrict paarig ($opened)"
    fi

    size="$(wc -c < "$newest_dump" | tr -d ' ')"
    echo "Groesse: $size Byte"
    if [ -n "$previous_dump" ]; then
        previous_size="$(wc -c < "$previous_dump" | tr -d ' ')"
        # A database does not usually lose half its content overnight. If it
        # does, that is worth a look even when the dump is syntactically whole.
        if [ "$previous_size" -gt 0 ] \
           && [ "$(( size * 100 / previous_size ))" -lt "$min_ratio_percent" ]; then
            fail "Dump auf $(( size * 100 / previous_size ))% des vorherigen geschrumpft"
        else
            echo "PASS: Groesse plausibel gegen $(basename "$previous_dump")"
        fi
    fi
fi

newest_config="$(ls -1t "$backups"/config-*.tar.gz 2>/dev/null | head -1 || true)"
if [ -z "$newest_config" ]; then
    fail "kein Konfigurationsarchiv im Ordner"
else
    echo "neuestes Archiv: $(basename "$newest_config")"
    # Listing is not extracting: this reads the table of contents and never
    # writes a file or prints startup.env, which is what is in there.
    if inhalt="$(tar -tzf "$newest_config" 2>/dev/null)"; then
        fehlend=""
        for erwartet in compose.yaml startup.env workforce-api; do
            printf '%s\n' "$inhalt" | grep -q "^$erwartet" || fehlend="$fehlend $erwartet"
        done
        if [ -n "$fehlend" ]; then
            fail "im Archiv fehlt:$fehlend"
        else
            echo "PASS: Archiv lesbar und vollstaendig"
        fi
    else
        fail "Archiv ist nicht lesbar - abgeschnitten oder beschaedigt"
    fi
fi

echo
if [ "$problems" -eq 0 ]; then
    echo "RESULT: PASS"
else
    echo "RESULT: FAIL ($problems)"
    exit 1
fi
