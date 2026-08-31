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
: "${AGENT_SOURCE_REF:?set AGENT_SOURCE_REF (e.g. a DEC-.../ENG-... reference) before running}"
: "${AGENT_RUN_SUFFIX:?set AGENT_RUN_SUFFIX (credential ids must be unique: a REVOKED credential can never be reactivated)}"

token_file="${AGENT_BUS_TOKEN_FILE:-/run/startup-agent-secrets/agent_bus_token}"

if [ ! -e "$token_file" ] && [ "${GENERATE_AGENT_TOKEN_IF_MISSING:-false}" = "true" ]; then
    token_dir="$(dirname "$token_file")"
    mkdir -p "$token_dir"
    umask 077
    temporary_token_file="${token_file}.tmp.$$"
    head -c 48 /dev/urandom | base64 | tr -d '\r\n' > "$temporary_token_file"
    mv "$temporary_token_file" "$token_file"
    # umask alone is not enough on the DSM share: its default ACL re-opens the
    # mode on creation, so set it explicitly while root still owns the file.
    chmod 600 "$token_file"
    echo "PASS: short-lived agent token created at $token_file (mode 600)."
fi

if [ ! -r "$token_file" ]; then
    echo "BLOCKED: agent token file $token_file is not readable." >&2
    exit 2
fi

raw_token="$(tr -d '\r\n' < "$token_file")"
token_length="${#raw_token}"
if [ "$token_length" -lt 32 ] || [ "$token_length" -gt 512 ]; then
    echo "BLOCKED: agent token length in $token_file is invalid." >&2
    exit 2
fi

token_hash="$(printf '%s' "$raw_token" | sha256sum | cut -d ' ' -f 1)"
unset raw_token

# Hand the file to UID 10001 only now. This container runs as root but with
# cap_drop ALL, so once the file belongs to 10001 it can neither read it (no
# CAP_DAC_OVERRIDE) nor change its mode (no CAP_FOWNER). Widening the mode
# instead would put the raw token within reach of every account on the NAS.
if ! chown 10001:10001 "$token_file" 2>/dev/null; then
    echo "BLOCKED: cannot hand $token_file to UID 10001. The container needs CAP_CHOWN; cap_drop ALL removes it." >&2
    exit 2
fi
echo "PASS: agent token handed to UID 10001 (mode 600)."

export PGHOST="${DB_HOST:-db}"
export PGUSER="$POSTGRES_USER"
export PGDATABASE="$POSTGRES_DB"
export PGPASSWORD="$POSTGRES_PASSWORD"

psql \
    -v ON_ERROR_STOP=1 \
    -v agent_token_hash="$token_hash" \
    -v source_ref="$AGENT_SOURCE_REF" \
    -v run_suffix="$AGENT_RUN_SUFFIX" \
    -f /opt/startup-agent/agent_prepare.sql

unset token_hash PGPASSWORD

echo "The raw token remains only in $token_file on this host. Delete it after the cleanup step."
