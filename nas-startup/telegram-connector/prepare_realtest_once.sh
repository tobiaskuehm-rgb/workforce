#!/bin/sh
set -eu

: "${POSTGRES_USER:?startup.env lacks POSTGRES_USER}"
: "${POSTGRES_DB:?startup.env lacks POSTGRES_DB}"
: "${POSTGRES_PASSWORD:?startup.env lacks POSTGRES_PASSWORD}"

token_file="${WORKFORCE_BUS_TOKEN_FILE:-/run/secrets/workforce_bus_token}"
if [ ! -e "$token_file" ] && [ "${GENERATE_WORKFORCE_BUS_TOKEN_IF_MISSING:-false}" = "true" ]; then
    token_dir="$(dirname "$token_file")"
    mkdir -p "$token_dir"
    umask 077
    temporary_token_file="${token_file}.tmp.$$"
    head -c 48 /dev/urandom | base64 | tr -d '\r\n' > "$temporary_token_file"
    mv "$temporary_token_file" "$token_file"
    echo "PASS: short-lived workforce token created in the local secret directory."
fi

if [ ! -r "$token_file" ]; then
    echo "BLOCKED: workforce bus token file is not readable." >&2
    exit 2
fi

raw_token="$(tr -d '\r\n' < "$token_file")"
token_length="${#raw_token}"
if [ "$token_length" -lt 32 ] || [ "$token_length" -gt 512 ]; then
    echo "BLOCKED: workforce bus token length is invalid." >&2
    exit 2
fi

token_hash="$(printf '%s' "$raw_token" | sha256sum | cut -d ' ' -f 1)"
unset raw_token

export PGHOST="${DB_HOST:-db}"
export PGUSER="$POSTGRES_USER"
export PGDATABASE="$POSTGRES_DB"
export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
    -v ON_ERROR_STOP=1 \
    -v workforce_token_hash="$token_hash" \
    -f /opt/startup-telegram/realtest_prepare.sql

unset token_hash PGPASSWORD
