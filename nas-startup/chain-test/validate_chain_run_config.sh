#!/bin/sh
set -eu

datei="${1:-chain-run.env}"
if [ ! -r "$datei" ]; then
    echo "BLOCKED: $datei fehlt oder ist nicht lesbar." >&2
    exit 2
fi

unexpected="$(sed -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' \
    -e '/^CHAIN_RUN_SUFFIX=/d' -e '/^CHAIN_TASK_ID=/d' "$datei" | wc -l | tr -d ' ')"
if [ "$unexpected" -ne 0 ]; then
    echo "BLOCKED: $datei enthaelt unbekannte oder nicht sichere Zeilen." >&2
    exit 2
fi

wert() {
    name="$1"
    count="$(sed -n "/^${name}=/p" "$datei" | wc -l | tr -d ' ')"
    if [ "$count" -ne 1 ]; then
        echo "BLOCKED: $name muss genau einmal in $datei stehen." >&2
        exit 2
    fi
    sed -n "s/^${name}=//p" "$datei"
}

suffix="$(wert CHAIN_RUN_SUFFIX)"
task_id="$(wert CHAIN_TASK_ID)"

case "$suffix" in
    SET-*|CHAIN20260901|*[!A-Z0-9-]*|"")
        echo "BLOCKED: CHAIN_RUN_SUFFIX ist Platzhalter, bereits benutzt oder ungueltig." >&2
        exit 2
        ;;
esac

if [ "${#suffix}" -lt 6 ] || [ "${#suffix}" -gt 48 ]; then
    echo "BLOCKED: CHAIN_RUN_SUFFIX muss 6 bis 48 Zeichen lang sein." >&2
    exit 2
fi

if [ "$task_id" != "ENG-CHAIN-$suffix" ]; then
    echo "BLOCKED: CHAIN_TASK_ID muss exakt ENG-CHAIN-$suffix sein." >&2
    exit 2
fi

echo "PASS: chain-run.env ist konsistent ($suffix)."
