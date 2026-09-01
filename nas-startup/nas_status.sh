#!/bin/sh
set -u

# One read-only look at the whole NAS state.
#
# Why this exists: the same measurements were rebuilt as a 30-line heredoc in
# every session - containers, API version, migrations, channel, credentials,
# manifest, backup permissions. Five round trips for one question, and each
# rebuild was a chance to quote something wrong. It happened.
#
# Read-only by construction: no writes, no container changes, no migration.
# The database is queried inside a throwaway container that mounts only
# startup.db.env - the three-value file, never startup.env (G-017).
#
#   ssh synology "cd /volume1/docker/Startup && sh nas_status.sh"
#
# Exits non-zero when a gate check fails, so it works as a preflight too.
# Prints identifiers and counts, never a secret and never a message body.

cd "$(dirname "$0")"
DOCKER=/usr/local/bin/docker
problems=0

echo "=== NAS-Status, $(date '+%Y-%m-%d %H:%M') ==="
echo
echo "--- Container ---"
sudo $DOCKER ps --format "{{.Names}} | {{.Image}} | {{.Status}}"

echo
echo "--- API meldet ---"
# `migration` ist ein Vorhandenseins-Flag fuer 002_workforce_bus, kein
# Migrationsstand - es steht auf 002, solange die Bus-Migration da ist, auch
# wenn 007 laengst angewendet ist. Den wirklichen Stand zeigt der Abschnitt
# Datenbank weiter unten. Der Feldname hat schon einmal in die Irre gefuehrt.
sudo $DOCKER exec startup-workforce-api-1 python -c "
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8080/bus/v1/status', timeout=5) as r:
    print(json.dumps(json.load(r), sort_keys=True))
" 2>/dev/null || echo "(API nicht erreichbar)"

echo
echo "--- Datenbank ---"
cat > /tmp/nas_status.sql <<'SQL'
SELECT 'Migrationen' AS was, string_agg(migration_id, ', ' ORDER BY migration_id) AS wert
FROM workforce.schema_migrations
UNION ALL SELECT 'Kanal', channel_status FROM workforce.bus_channels WHERE project_id = 'START-UP'
UNION ALL SELECT 'aktive Credentials', count(*)::text FROM workforce.bus_credentials
  WHERE credential_status = 'ACTIVE' AND (expires_at IS NULL OR expires_at > clock_timestamp())
UNION ALL SELECT 'Knowledge 004',
  CASE WHEN to_regclass('workforce.knowledge_systems') IS NULL THEN 'nicht angewendet' ELSE 'angewendet' END
UNION ALL SELECT 'Ablehnungs-Audit 005',
  CASE WHEN to_regclass('workforce.bus_denials') IS NULL THEN 'nicht angewendet' ELSE 'angewendet' END
UNION ALL SELECT 'Rolle workforce_api',
  CASE WHEN EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_api') THEN 'vorhanden' ELSE 'fehlt' END
UNION ALL SELECT 'Rolle workforce_backup',
  CASE WHEN EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_backup') THEN 'vorhanden' ELSE 'fehlt' END
UNION ALL SELECT 'workforce_app SUPERUSER',
  CASE WHEN EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_app' AND rolsuper) THEN 'ja - G-045: nicht per ALTER ROLE entziehbar' ELSE 'nein' END
UNION ALL SELECT 'Datenbankgroesse', pg_size_pretty(pg_database_size(current_database()));
SQL
sudo $DOCKER run --rm --network startup_backend \
  -v "$(pwd)/startup.db.env:/run/startup.db.env:ro" \
  -v /tmp/nas_status.sql:/tmp/q.sql:ro postgres:17-alpine sh -c '
    export PGHOST="${DB_HOST:-db}"
    export PGUSER="$(sed -n "s/^POSTGRES_USER=//p" /run/startup.db.env)"
    export PGDATABASE="$(sed -n "s/^POSTGRES_DB=//p" /run/startup.db.env)"
    export PGPASSWORD="$(sed -n "s/^POSTGRES_PASSWORD=//p" /run/startup.db.env)"
    psql -f /tmp/q.sql' 2>&1 | grep -vE "^\(|^$" || problems=$((problems + 1))
rm -f /tmp/nas_status.sql

# A pipeline returns the exit code of its LAST command, so `check | tail`
# reports whether `tail` worked - never whether the check passed. The first
# version of this script did exactly that and printed PASS under a failing
# manifest. Run first, capture the code, then show the tail.
run_gate() {
    label="$1"
    script="$2"
    echo
    echo "--- $label ---"
    output="$(sh "$script" 2>&1)"
    code=$?
    echo "$output" | tail -3
    [ "$code" -eq 0 ] || problems=$((problems + 1))
}

run_gate "Manifest" verify_manifest.sh
run_gate "Backup-Rechte" check_backup_permissions.sh

echo
echo "--- Rueckfallpunkte ---"
backups=../Startup-Backups
newest() {
    # `ls | head | sed` succeeds even with no input, so an empty result has to
    # be tested, not chained with ||.
    found="$(ls -1t $1 2>/dev/null | head -1)"
    if [ -n "$found" ]; then
        echo "$2: $(basename "$found")"
    else
        echo "$2: keiner gefunden"
    fi
}
# Without the exclusion the glob also matches preflight-*.globals.sql, which
# sorts later and would be reported as the database dump.
found_dump="$(ls -1t $backups/preflight-*.sql 2>/dev/null | grep -v globals | head -1)"
if [ -n "$found_dump" ]; then
    echo "neuester Preflight-Dump: $(basename "$found_dump")"
else
    echo "neuester Preflight-Dump: keiner gefunden"
fi
# "zugehoerig" was a claim, not a check: this used to report the newest
# globals dump regardless of which database dump it belonged to. A restore
# needs the pair, so the name is derived from the dump that was just named
# (G-043 - same class as guardrail 7: a text that asserts a safeguard has to
# be able to back it up).
if [ -n "$found_dump" ]; then
    mate="${found_dump%.sql}.globals.sql"
    if [ -f "$mate" ]; then
        echo "zugehoeriger Rollen-Dump: $(basename "$mate")"
    else
        echo "zugehoeriger Rollen-Dump: FEHLT zu $(basename "$found_dump")"
        problems=$((problems + 1))
    fi
else
    echo "zugehoeriger Rollen-Dump: kein Dump, also kein Paar"
fi
newest "$backups/rollback-*.tar.gz" "neuestes Rollback-Image"

echo
if [ "$problems" -eq 0 ]; then
    echo "RESULT: PASS"
else
    echo "RESULT: FAIL ($problems)"
    exit 1
fi
