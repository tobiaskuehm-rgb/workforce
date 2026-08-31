#!/bin/sh
set -eu

: "${POSTGRES_USER:?startup.env lacks POSTGRES_USER}"
: "${POSTGRES_DB:?startup.env lacks POSTGRES_DB}"
: "${POSTGRES_PASSWORD:?startup.env lacks POSTGRES_PASSWORD}"
: "${BUS_REALTEST_RUN_SUFFIX:?set BUS_REALTEST_RUN_SUFFIX to the same value the prepare step used}"

export PGHOST="${DB_HOST:-db}"
export PGUSER="$POSTGRES_USER"
export PGDATABASE="$POSTGRES_DB"
export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
    -v ON_ERROR_STOP=1 \
    -v run_suffix="$BUS_REALTEST_RUN_SUFFIX" \
    -f /opt/startup-bus-realtest/bus_realtest_cleanup.sql

unset PGPASSWORD

echo "Reminder: delete the local token files under ./secrets/ by hand now that the credentials are revoked."
