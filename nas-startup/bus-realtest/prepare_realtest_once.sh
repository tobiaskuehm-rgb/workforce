#!/bin/sh
set -eu

: "${POSTGRES_USER:?startup.env lacks POSTGRES_USER}"
: "${POSTGRES_DB:?startup.env lacks POSTGRES_DB}"
: "${POSTGRES_PASSWORD:?startup.env lacks POSTGRES_PASSWORD}"
: "${BUS_REALTEST_SOURCE_REF:?set BUS_REALTEST_SOURCE_REF (e.g. a DEC-.../ENG-003 reference) before running}"

karl_token_file="${KARL_BUS_TOKEN_FILE:-/run/startup-bus-secrets/bus_token_karl}"
thorsten_token_file="${THORSTEN_BUS_TOKEN_FILE:-/run/startup-bus-secrets/bus_token_thorsten}"

generate_token_if_missing() {
    token_file="$1"
    if [ ! -e "$token_file" ] && [ "${GENERATE_BUS_TOKENS_IF_MISSING:-false}" = "true" ]; then
        token_dir="$(dirname "$token_file")"
        mkdir -p "$token_dir"
        umask 077
        temporary_token_file="${token_file}.tmp.$$"
        head -c 48 /dev/urandom | base64 | tr -d '\r\n' > "$temporary_token_file"
        mv "$temporary_token_file" "$token_file"
        # umask alone is not enough here: the DSM share carries a default ACL
        # that re-opens the mode on creation, so the 2026-08-31 realtest wrote
        # both token files as rwxrwxrwx despite the umask above.
        #
        # 600 alone would lock out the run and negtest containers, which read
        # these files as UID 10001. This step runs as root, so hand the file to
        # that UID instead of widening the mode.
        chown 10001:10001 "$token_file" 2>/dev/null || true
        chmod 600 "$token_file"
        echo "PASS: short-lived token created at $token_file (mode 600, owner 10001)."
    fi
}

hash_token() {
    token_file="$1"
    if [ ! -r "$token_file" ]; then
        echo "BLOCKED: token file $token_file is not readable." >&2
        exit 2
    fi
    raw_token="$(tr -d '\r\n' < "$token_file")"
    token_length="${#raw_token}"
    if [ "$token_length" -lt 32 ] || [ "$token_length" -gt 512 ]; then
        echo "BLOCKED: token length in $token_file is invalid." >&2
        exit 2
    fi
    printf '%s' "$raw_token" | sha256sum | cut -d ' ' -f 1
    unset raw_token
}

generate_token_if_missing "$karl_token_file"
generate_token_if_missing "$thorsten_token_file"

karl_hash="$(hash_token "$karl_token_file")"
thorsten_hash="$(hash_token "$thorsten_token_file")"

export PGHOST="${DB_HOST:-db}"
export PGUSER="$POSTGRES_USER"
export PGDATABASE="$POSTGRES_DB"
export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
    -v ON_ERROR_STOP=1 \
    -v karl_token_hash="$karl_hash" \
    -v thorsten_token_hash="$thorsten_hash" \
    -v source_ref="$BUS_REALTEST_SOURCE_REF" \
    -f /opt/startup-bus-realtest/bus_realtest_prepare.sql

unset karl_hash thorsten_hash PGPASSWORD

echo "Raw tokens remain only in $karl_token_file and $thorsten_token_file on this host."
echo "Copy each one out manually for the run step, then treat these files as secrets."
