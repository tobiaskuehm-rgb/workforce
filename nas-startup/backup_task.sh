#!/bin/sh
set -eu

# The nightly backup, as a versioned file instead of a field in DSM.
#
# Today the logic lives only inside the Task Scheduler's own database. It is
# not in git, not in the manifest, not reviewed, and not testable - the only
# way to read it is to open the task or to query esynoscheduler. That is the
# deeper half of review finding G-047: a folder mounted into production was
# unmanaged, and so is the script that fills it.
#
# Once this is in place the DSM task shrinks to one line:
#
#     sh /volume1/docker/Startup/backup_task.sh
#
# **This script does not replace the task by itself.** Changing the task is the
# CEO's to do; nothing here reaches the Task Scheduler.
#
# What it changes against the version that ran until 2026-09-02:
#
#   * The container is resolved through `docker compose ps -q db` instead of
#     the hard-coded `startup-db-1`. A container name is derived from project
#     directory, service and index (G-042); the name is right today and is not
#     a fact anyone promised to keep.
#
#   * It waits for the database to be healthy. The NAS powers on at 02:00 and
#     the task runs at 02:05, so the old version had five minutes of luck built
#     into it.
#
#   * A dump that did not finish is renamed to `.unvollstaendig` rather than
#     left in place. `> file` creates the file before the command runs, so a
#     failed `docker exec` leaves a truncated one that looks like a backup.
#     It is renamed, not deleted - guardrail 2 - and the suffix takes it out of
#     the `workforce-*.sql` glob, so nothing mistakes it for the newest good
#     dump and check_backup_integrity.sh sees the real age gap.
#
#   * The retention prune runs **last**, and only after the dump has been shown
#     to be complete. The old order deleted 31-day-old backups before anyone
#     had established that today's was worth keeping.
#
#   * Permissions are set at the end, so the files do not sit world-readable
#     between 02:05 and whenever somebody notices (G-048).
#
# Retention stays at 30 days, unchanged, because that is a decision the CEO
# made and not one to alter while fixing something else.

BASE_DIR="${BASE_DIR:-/volume1/docker/Startup}"
BACKUP_DIR="${BACKUP_DIR:-/volume1/docker/Startup-Backups}"
DOCKER="${DOCKER_BIN:-/usr/local/bin/docker}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
HEALTH_TRIES="${DB_HEALTH_TRIES:-60}"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"

[ -d "$BASE_DIR" ] || { echo "FAIL: $BASE_DIR fehlt"; exit 1; }
[ -d "$BACKUP_DIR" ] || { echo "FAIL: $BACKUP_DIR fehlt"; exit 1; }

cd "$BASE_DIR"

# 1. Is docker usable at all? Without this the next line's `|| true` turns
#    "the CLI could not run" into "there is no container", and the operator
#    goes looking for a stopped stack that is running fine. Found by a test
#    harness of mine that passed DOCKER_BIN as a single quoted word.
if ! "$DOCKER" version >/dev/null 2>&1; then
    echo "FAIL: $DOCKER ist nicht ausfuehrbar - laeuft die Aufgabe als root?"
    exit 1
fi

# 2. Which container is the database right now.
db_id="$("$DOCKER" compose ps -q db 2>/dev/null || true)"
if [ -z "$db_id" ]; then
    echo "FAIL: kein Container fuer den Dienst db - laeuft der Stack?"
    exit 1
fi

# 3. Healthy, not merely running. A database that is still starting answers
#    connections with a refusal, and the refusal would end up in the dump file.
state=""
tries=0
while [ "$tries" -lt "$HEALTH_TRIES" ]; do
    state="$("$DOCKER" inspect -f \
        '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
        "$db_id" 2>/dev/null || true)"
    [ "$state" = "healthy" ] && break
    tries=$((tries + 1))
    sleep 5
done
if [ "$state" != "healthy" ]; then
    echo "FAIL: db ist nach $((HEALTH_TRIES * 5))s nicht gesund (Zustand: ${state:-unbekannt})"
    exit 1
fi
echo "db gesund nach $((tries * 5))s"

dump="$BACKUP_DIR/workforce-$STAMP.sql"

# 4. The dump. `set -e` ends the run if pg_dump fails, but the redirection has
#    already created the file, so the failure path has to mark it.
if ! "$DOCKER" exec "$db_id" pg_dump -U workforce_app -d workforce > "$dump"; then
    mv "$dump" "$dump.unvollstaendig"
    echo "FAIL: pg_dump gescheitert, Datei als .unvollstaendig markiert"
    exit 1
fi

# 5. Complete, not merely present. This is the line pg_dump writes last; a dump
#    cut off in the middle does not have it. Anchored, because the phrase also
#    occurs in the header comment.
if ! grep -q '^-- PostgreSQL database dump complete$' "$dump"; then
    mv "$dump" "$dump.unvollstaendig"
    echo "FAIL: Dump ohne Abschlusszeile, als .unvollstaendig markiert"
    exit 1
fi
echo "Dump vollstaendig: $(wc -c < "$dump" | tr -d ' ') Byte"

# 6. The configuration archive. startup.env is in here, which is why the
#    permissions step below is not optional.
tar -czf "$BACKUP_DIR/config-$STAMP.tar.gz" \
    -C "$BASE_DIR" \
    compose.yaml startup.env workforce-api
echo "Archiv geschrieben: $(wc -c < "$BACKUP_DIR/config-$STAMP.tar.gz" | tr -d ' ') Byte"

# 7. Permissions, before anything else can read them (G-048).
sh "$BASE_DIR/harden_backup_permissions.sh"

# 8. Only now the retention prune. Deleting old backups is safe exactly when a
#    new good one exists, and not a step earlier.
geloescht="$(find "$BACKUP_DIR" -type f \
    \( -name 'workforce-*.sql' -o -name 'config-*.tar.gz' \) \
    -mtime "+$RETENTION_DAYS" -print | wc -l | tr -d ' ')"
find "$BACKUP_DIR" -type f \
    \( -name 'workforce-*.sql' -o -name 'config-*.tar.gz' \) \
    -mtime "+$RETENTION_DAYS" -delete
echo "aelter als $RETENTION_DAYS Tage entfernt: $geloescht Datei(en)"

echo "RESULT: PASS"
