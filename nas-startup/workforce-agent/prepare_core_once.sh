#!/bin/sh
set -eu

# Only the three database values are needed. If they are not in the
# environment, read them from the mounted startup.db.env, which is derived
# from startup.env and contains nothing else (derive_db_env_once.sh). The
# mount keeps every secret off `docker inspect`; the derived file is what
# keeps WORKFORCE_API_KEY out of the container's file system
# (review findings G-010, G-017).
db_env="${DB_ENV_FILE:-/run/startup.db.env}"
if [ -r "$db_env" ]; then
    POSTGRES_USER="${POSTGRES_USER:-$(sed -n 's/^POSTGRES_USER=//p' "$db_env")}"
    POSTGRES_DB="${POSTGRES_DB:-$(sed -n 's/^POSTGRES_DB=//p' "$db_env")}"
    POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(sed -n 's/^POSTGRES_PASSWORD=//p' "$db_env")}"
fi

: "${POSTGRES_USER:?startup.db.env lacks POSTGRES_USER}"
: "${POSTGRES_DB:?startup.db.env lacks POSTGRES_DB}"
: "${POSTGRES_PASSWORD:?startup.db.env lacks POSTGRES_PASSWORD}"
: "${CORE_SOURCE_REF:?set CORE_SOURCE_REF}"
: "${CORE_RUN_SUFFIX:?set CORE_RUN_SUFFIX (credential ids must be unique per run)}"

secret_dir="${CORE_SECRET_DIR:-/run/startup-core-secrets}"
mkdir -p "$secret_dir"

# Three tokens, one per core member. Generated here so the raw values never
# leave this host; only the hashes go into the database.
for who in karl gerd anastasia; do
    token_file="$secret_dir/core_token_$who"
    if [ ! -e "$token_file" ]; then
        umask 077
        temporary="${token_file}.tmp.$$"
        head -c 48 /dev/urandom | base64 | tr -d '\r\n' > "$temporary"
        mv "$temporary" "$token_file"
        # umask alone is not enough on the DSM share: its default ACL re-opens
        # the mode on creation.
        chmod 600 "$token_file"
        echo "PASS: token created for $who (mode 600)."
    fi
done

hash_of() {
    raw="$(tr -d '\r\n' < "$1")"
    length="${#raw}"
    if [ "$length" -lt 32 ] || [ "$length" -gt 512 ]; then
        echo "BLOCKED: token length in $1 is invalid." >&2
        exit 2
    fi
    printf '%s' "$raw" | sha256sum | cut -d ' ' -f 1
    unset raw
}

karl_hash="$(hash_of "$secret_dir/core_token_karl")"
gerd_hash="$(hash_of "$secret_dir/core_token_gerd")"
anastasia_hash="$(hash_of "$secret_dir/core_token_anastasia")"

# Hand the files to UID 10001 only after hashing: this container runs as root
# but with cap_drop ALL, so afterwards it can neither read them (no
# CAP_DAC_OVERRIDE) nor change their mode (no CAP_FOWNER).
for who in karl gerd anastasia; do
    if ! chown 10001:10001 "$secret_dir/core_token_$who" 2>/dev/null; then
        echo "BLOCKED: cannot hand core_token_$who to UID 10001. Needs CAP_CHOWN." >&2
        exit 2
    fi
done
echo "PASS: all three token files handed to UID 10001 (mode 600)."

export PGHOST="${DB_HOST:-db}"
export PGUSER="$POSTGRES_USER"
export PGDATABASE="$POSTGRES_DB"
export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
    -v ON_ERROR_STOP=1 \
    -v karl_token_hash="$karl_hash" \
    -v gerd_token_hash="$gerd_hash" \
    -v anastasia_token_hash="$anastasia_hash" \
    -v source_ref="$CORE_SOURCE_REF" \
    -v run_suffix="$CORE_RUN_SUFFIX" \
    -f /opt/startup-core/core_prepare.sql

unset karl_hash gerd_hash anastasia_hash PGPASSWORD
echo "Raw tokens remain only in $secret_dir. Delete them after the cleanup."
