#!/bin/sh
set -eu

: "${POSTGRES_USER:?startup.env lacks POSTGRES_USER}"
: "${POSTGRES_DB:?startup.env lacks POSTGRES_DB}"
: "${POSTGRES_PASSWORD:?startup.env lacks POSTGRES_PASSWORD}"

export PGHOST="${DB_HOST:-db}"
export PGUSER="$POSTGRES_USER"
export PGDATABASE="$POSTGRES_DB"
export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
    -v ON_ERROR_STOP=1 \
    -f /opt/startup-telegram/realtest_cleanup.sql

unset PGPASSWORD

token_file="${WORKFORCE_BUS_TOKEN_FILE:-}"
if [ -n "$token_file" ] && [ -f "$token_file" ]; then
    rm -f -- "$token_file"
    echo "PASS: short-lived workforce token file removed."
fi
