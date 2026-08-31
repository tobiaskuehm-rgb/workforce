#!/bin/sh
set -eu

# Derives startup.db.env from startup.env: the three database values and
# nothing else.
#
# Why this exists (review finding G-017): mounting the full startup.env into
# the one-shot helper containers kept WORKFORCE_API_KEY out of `docker
# inspect`, but not out of the container. A mount restricts the environment,
# not the file system - anything running in that container could read the file.
# Least privilege needs a smaller file, not a quieter one.
#
# Run on the NAS, in /volume1/docker/Startup, whenever startup.env changes:
#
#   sudo sh workforce-agent/derive_db_env_once.sh
#
# Ownership root:users with mode 660 mirrors startup.env deliberately. The
# helper containers run as root without CAP_DAC_OVERRIDE, so they can only
# read a file they own; TOBKUM reads it through the group; nobody else at all.
# A 600 file owned by TOBKUM would fail exactly the way startup.env did on
# 2026-08-31 (see evidence/2026-08-31_contract_test_und_aufraeumen.md).

src="${STARTUP_ENV:-./startup.env}"
dst="${STARTUP_DB_ENV:-./startup.db.env}"

[ -r "$src" ] || { echo "cannot read $src - run this from /volume1/docker/Startup" >&2; exit 1; }

tmp="$dst.tmp.$$"
umask 077
: > "$tmp"

for key in POSTGRES_USER POSTGRES_DB POSTGRES_PASSWORD; do
    value="$(sed -n "s/^$key=//p" "$src" | head -n 1)"
    [ -n "$value" ] || { rm -f "$tmp"; echo "$src lacks $key" >&2; exit 1; }
    printf '%s=%s\n' "$key" "$value" >> "$tmp"
done

# Fails loudly rather than shipping a file that carries more than it should.
if [ "$(wc -l < "$tmp")" -ne 3 ]; then
    rm -f "$tmp"
    echo "refusing to write $dst: expected exactly three lines" >&2
    exit 1
fi

# Overridable only so the script can be exercised off the NAS; on the NAS
# the default is the point. No silent fallback: if the ownership cannot be
# set, the file is not written.
owner="${DB_ENV_OWNER:-root:users}"
chown "$owner" "$tmp"
chmod 660 "$tmp"
mv "$tmp" "$dst"

echo "wrote $dst (3 values, $owner 660)"
echo "keys: $(cut -d= -f1 "$dst" | tr '\n' ' ')"
