#!/bin/sh
set -eu

# Only the three database values are needed. If they are not in the
# environment, read them from the mounted startup.db.env, which is derived
# from startup.env and contains nothing else (workforce-agent/
# derive_db_env_once.sh). See review findings G-010 and G-017.
db_env="${DB_ENV_FILE:-/run/startup.db.env}"
if [ -r "$db_env" ]; then
    POSTGRES_USER="${POSTGRES_USER:-$(sed -n 's/^POSTGRES_USER=//p' "$db_env")}"
    POSTGRES_DB="${POSTGRES_DB:-$(sed -n 's/^POSTGRES_DB=//p' "$db_env")}"
    POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(sed -n 's/^POSTGRES_PASSWORD=//p' "$db_env")}"
fi

: "${POSTGRES_USER:?startup.db.env lacks POSTGRES_USER}"
: "${POSTGRES_DB:?startup.db.env lacks POSTGRES_DB}"
: "${POSTGRES_PASSWORD:?startup.db.env lacks POSTGRES_PASSWORD}"
: "${CHAIN_SOURCE_REF:?set CHAIN_SOURCE_REF}"
: "${CHAIN_RUN_SUFFIX:?set CHAIN_RUN_SUFFIX (identity and credential ids must be unique per run)}"

secret_dir="${CHAIN_SECRET_DIR:-/run/startup-chain-secrets}"
mkdir -p "$secret_dir"

# Two bus tokens: one for the connector identity this run creates, one for the
# agent. Generated here so the raw values never leave this host; only the
# hashes go into the database.
#
# The Telegram bot token is NOT generated here - it comes from BotFather and
# has to be placed in ./secrets/telegram_bot_token by hand before the run.
for who in connector agent; do
    token_file="$secret_dir/chain_token_$who"
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

connector_hash="$(hash_of "$secret_dir/chain_token_connector")"
agent_hash="$(hash_of "$secret_dir/chain_token_agent")"

# Hand the files to UID 10001 only after hashing: this container runs as root
# but with cap_drop ALL, so afterwards it can neither read them (no
# CAP_DAC_OVERRIDE) nor change their mode (no CAP_FOWNER).
for who in connector agent; do
    if ! chown 10001:10001 "$secret_dir/chain_token_$who" 2>/dev/null; then
        echo "BLOCKED: cannot hand chain_token_$who to UID 10001. Needs CAP_CHOWN." >&2
        exit 2
    fi
done
echo "PASS: both token files handed to UID 10001 (mode 600)."

export PGHOST="${DB_HOST:-db}"
export PGUSER="$POSTGRES_USER"
export PGDATABASE="$POSTGRES_DB"
export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
    -v ON_ERROR_STOP=1 \
    -v connector_token_hash="$connector_hash" \
    -v agent_token_hash="$agent_hash" \
    -v source_ref="$CHAIN_SOURCE_REF" \
    -v run_suffix="$CHAIN_RUN_SUFFIX" \
    -f /opt/startup-chain/chain_prepare.sql

unset connector_hash agent_hash PGPASSWORD
echo "Raw tokens remain only in $secret_dir. Delete them after the cleanup."
echo "Reminder: ./secrets/telegram_bot_token must be placed there by hand."
