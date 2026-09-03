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
#
# Der Container wird aufgeloest, nicht benannt (G-042, G-085): ein
# Containername ist eine Ableitung aus Projektordner, Dienst und Index. Und
# ein Fehlschlag zaehlt - die erste Fassung druckte "(API nicht erreichbar)"
# und meldete darunter PASS.
api_id="$(sudo $DOCKER compose ps -q workforce-api 2>/dev/null || true)"
if [ -z "$api_id" ]; then
    echo "FAIL: kein Container fuer den Dienst workforce-api - laeuft der Stack?"
    problems=$((problems + 1))
else
    api_out="$(sudo $DOCKER exec "$api_id" python -c "
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8080/bus/v1/status', timeout=5) as r:
    print(json.dumps(json.load(r), sort_keys=True))
" 2>&1)"
    api_code=$?
    if [ "$api_code" -eq 0 ]; then
        echo "$api_out"
    else
        echo "FAIL: API-Abfrage Exitcode $api_code"
        echo "$api_out" | tail -3
        problems=$((problems + 1))
    fi
fi

echo
echo "--- Datenbank ---"
# Unaligned mit | als Trenner, damit die Werte unten maschinell gelesen werden
# koennen; die Migrationsliste ist kommagetrennt ohne Leerzeichen, in genau
# der Form, in der production_state.txt sie fuehrt.
cat > /tmp/nas_status.sql <<'SQL'
SELECT 'Migrationen' AS was, string_agg(migration_id, ',' ORDER BY migration_id) AS wert
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
# Ausgabe und Exitcode getrennt festhalten (G-085). Die erste Fassung haengte
# ein `| grep` an und zaehlte nur bei leerer Ausgabe ein Problem: Der Status
# einer Pipeline ist der ihres letzten Befehls, und grep ist erfolgreich,
# sobald es eine Zeile ausgibt - auch die Zeile "psql: error: ...". Dieselbe
# Falle, die run_gate() unten fuer die Gates schon vermeidet.
db_out="$(sudo $DOCKER run --rm --network startup_backend \
  -v "$(pwd)/startup.db.env:/run/startup.db.env:ro" \
  -v /tmp/nas_status.sql:/tmp/q.sql:ro postgres:17-alpine sh -c '
    export PGHOST="${DB_HOST:-db}"
    export PGUSER="$(sed -n "s/^POSTGRES_USER=//p" /run/startup.db.env)"
    export PGDATABASE="$(sed -n "s/^POSTGRES_DB=//p" /run/startup.db.env)"
    export PGPASSWORD="$(sed -n "s/^POSTGRES_PASSWORD=//p" /run/startup.db.env)"
    psql -v ON_ERROR_STOP=1 -At -F "|" -f /tmp/q.sql' 2>&1)"
db_code=$?
rm -f /tmp/nas_status.sql
if [ "$db_code" -ne 0 ]; then
    echo "FAIL: Datenbankabfrage Exitcode $db_code"
    printf '%s\n' "$db_out" | tail -3
    problems=$((problems + 1))
else
    printf '%s\n' "$db_out" | awk -F'|' '{ printf "%-24s %s\n", $1, $2 }'
fi

# Sollwerte, maschinell gepruef (G-085). Das Runbook sagt "Abbruch, wenn nicht
# Kanal DISABLED, 0 aktive Credentials, Migrationen 001-003 und 005-007" - und
# ein Wert, der in der Ausgabe fehlt, ist kein Abbruch, wenn niemand ihn
# vermisst. Also werden die drei hier verglichen, nicht vom Operator gelesen.
# Die Migrationsmenge kommt aus production_state.txt, dem einen Ort, der den
# laufenden Stand nennt (G-050) - keine zweite Liste hier. Kanal und
# Credentials sind fuer ein geschlossenes Fenster fest; wer nas_status.sh
# waehrend eines offenen Fensters als Messung braucht, setzt EXPECT_CHANNEL
# ausdruecklich.
echo
echo "--- Sollwerte (Preflight) ---"
wert() { printf '%s\n' "$db_out" | sed -n "s/^$1|//p" | head -1; }
pruefe() {
    if [ -z "$2" ]; then
        echo "FAIL: $1 nicht gemessen, erwartet $3"
        problems=$((problems + 1))
    elif [ "$2" = "$3" ]; then
        echo "PASS: $1 = $3"
    else
        echo "FAIL: $1 = $2, erwartet $3"
        problems=$((problems + 1))
    fi
}
soll_migrationen="$(sed -n 's/^APPLIED_MIGRATIONS=//p' production_state.txt 2>/dev/null | head -1)"
if [ -z "$soll_migrationen" ]; then
    echo "FAIL: production_state.txt nennt keine APPLIED_MIGRATIONS"
    problems=$((problems + 1))
else
    pruefe "Migrationen" "$(wert Migrationen)" "$soll_migrationen"
fi
pruefe "Kanal" "$(wert Kanal)" "${EXPECT_CHANNEL:-DISABLED}"
pruefe "aktive Credentials" "$(wert 'aktive Credentials')" "${EXPECT_ACTIVE_CREDENTIALS:-0}"

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
# Rechte und Inhalt sind zwei Fragen. Die erste sagt, wer die Sicherung lesen
# darf; die zweite, ob sie etwas enthaelt, aus dem man wiederherstellen kann
# (G-047). Ein abgeschnittener Dump mit tadellosen Rechten besteht die erste
# und ist trotzdem wertlos.
run_gate "Backup-Inhalt" check_backup_integrity.sh
# Die Bus-Adresse ist ein abgeleiteter Name: Synology bildet ihn aus der
# LAN-Adresse, also faellt er mit dem naechsten DHCP-Wechsel um (G-051).
# Am 2026-09-02 zeigte er einen Tag lang auf ein fremdes Geraet, ohne dass
# irgendetwas es gemerkt haette - die lokalen Suiten laufen ohne Netz.
run_gate "Bus-Adresse" check_bus_address.sh
# Das Manifest prueft, was *innerhalb* der genannten Pfade liegt. Diese
# Pruefung stellt die andere Frage: was liegt daneben und wird von gar
# keiner Liste gesehen (G-060)? Ein ganzer Ordner faellt sonst durch,
# und das Manifest meldet dazu PASS.
run_gate "Unverwaltetes" check_unmanaged.sh

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
