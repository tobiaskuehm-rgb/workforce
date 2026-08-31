#!/bin/sh
set -eu

: "${POSTGRES_USER:?startup.env lacks POSTGRES_USER}"
: "${POSTGRES_DB:?startup.env lacks POSTGRES_DB}"
: "${POSTGRES_PASSWORD:?startup.env lacks POSTGRES_PASSWORD}"
: "${BUS_REALTEST_SOURCE_REF:?set BUS_REALTEST_SOURCE_REF (e.g. a DEC-.../ENG-003 reference) before running}"
: "${BUS_REALTEST_RUN_SUFFIX:?set BUS_REALTEST_RUN_SUFFIX (credential ids must be unique: a REVOKED credential can never be reactivated)}"

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
        chmod 600 "$token_file"
        echo "PASS: short-lived token created at $token_file (mode 600)."
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

# Only now hand both files to UID 10001, the user the run and negtest
# containers execute as. This has to happen after hashing: this container runs
# as root but with cap_drop ALL, so once a file belongs to 10001 it can no
# longer read it (no CAP_DAC_OVERRIDE) nor change its mode (no CAP_FOWNER).
# Widening the mode instead would put the raw tokens back within reach of every
# account on the NAS.
for token_file in "$karl_token_file" "$thorsten_token_file"; do
    if ! chown 10001:10001 "$token_file" 2>/dev/null; then
        echo "BLOCKED: cannot hand $token_file to UID 10001. The container needs CAP_CHOWN; cap_drop ALL removes it." >&2
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
    -v karl_token_hash="$karl_hash" \
    -v thorsten_token_hash="$thorsten_hash" \
    -v source_ref="$BUS_REALTEST_SOURCE_REF" \
    -v run_suffix="$BUS_REALTEST_RUN_SUFFIX" \
    -f /opt/startup-bus-realtest/bus_realtest_prepare.sql

unset karl_hash thorsten_hash PGPASSWORD

echo "Raw tokens remain only in $karl_token_file and $thorsten_token_file on this host."
echo "Copy each one out manually for the run step, then treat these files as secrets."
