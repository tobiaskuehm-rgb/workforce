#!/bin/sh
set -eu

# Proves review finding G-017 closed, on the NAS, against both the environment
# and the readable file system.
#
# The local drift guard (test_compose_secrets.py) reads the compose files. That
# catches a reintroduced mount, but it cannot prove what a running container
# actually sees. This script does, and it does so without ever printing a
# secret value: it looks for the presence of the secret FILES and for the NAMES
# of environment variables, never their contents.
#
# Run in /volume1/docker/Startup/workforce-agent. Needs no firewall rule and no
# credentials - none of these containers talks to the bus or the database:
#
#   sudo sh verify_secret_isolation_once.sh
#
# Every check prints PASS or FAIL and the script exits non-zero on any FAIL.

fails=0

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; fails=$((fails + 1)); }

echo "== 1. The derived file carries three values and nothing else =="
db_env="../startup.db.env"
if [ ! -r "$db_env" ]; then
    fail "$db_env missing - run derive_db_env_once.sh first"
else
    keys="$(cut -d= -f1 "$db_env" | sort | tr '\n' ' ')"
    if [ "$keys" = "POSTGRES_DB POSTGRES_PASSWORD POSTGRES_USER " ]; then
        pass "startup.db.env holds exactly: $keys"
    else
        fail "startup.db.env holds: $keys"
    fi
fi

echo
echo "== 2. The outward-facing core runner sees no shared secret file =="
# --no-deps keeps prepare from running; the entrypoint override means the
# roundtrip itself never starts. Nothing is created, nothing is revoked.
found="$(docker compose -f compose.core.yaml run --rm --no-deps \
    --entrypoint sh run -c 'find / -xdev -name "startup*.env" 2>/dev/null' || true)"
if [ -z "$found" ]; then
    pass "no startup*.env anywhere in the run container"
else
    fail "run container can read: $found"
fi

names="$(docker compose -f compose.core.yaml run --rm --no-deps \
    --entrypoint sh run -c 'env | cut -d= -f1 | sort' || true)"
if echo "$names" | grep -qE '^(POSTGRES_USER|POSTGRES_DB|POSTGRES_PASSWORD|WORKFORCE_API_KEY|TELEGRAM_BOT_TOKEN)$'; then
    fail "run container has a secret variable set: $(echo "$names" | grep -E '^(POSTGRES|WORKFORCE_API_KEY|TELEGRAM)')"
else
    pass "run container environment holds no secret variable (only *_FILE paths)"
fi

echo
echo "== 3. A database helper sees the derived file and only that =="
found="$(docker compose -f compose.core.yaml run --rm --no-deps \
    --entrypoint sh audit -c 'find / -xdev -name "startup*.env" 2>/dev/null | sort' || true)"
if [ "$found" = "/run/startup.db.env" ]; then
    pass "audit container reads /run/startup.db.env and nothing else"
else
    fail "audit container reads: ${found:-nothing}"
fi

names="$(docker compose -f compose.core.yaml run --rm --no-deps \
    --entrypoint sh audit -c 'cut -d= -f1 /run/startup.db.env | sort | tr "\n" " "' || true)"
if [ "$names" = "POSTGRES_DB POSTGRES_PASSWORD POSTGRES_USER " ]; then
    pass "the file inside the container holds only the three database keys"
else
    fail "the file inside the container holds: $names"
fi

echo
echo "== 4. Nothing was left running =="
left="$(docker compose -f compose.core.yaml ps -q || true)"
if [ -z "$left" ]; then
    pass "no container from this project remains"
else
    fail "containers remain: $left"
fi

echo
if [ "$fails" -eq 0 ]; then
    echo "RESULT: PASS"
else
    echo "RESULT: FAIL ($fails)"
    exit 1
fi
