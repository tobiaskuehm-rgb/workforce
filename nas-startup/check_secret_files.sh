#!/bin/sh
set -u

# Checks the secret files without ever printing their contents.
#
# Why this exists: on 2026-09-01 the Telegram bot token was written with
# TextEdit, which saves RTF by default. The file held 433 bytes of markup and
# the run failed with an error that pointed at Telegram, not at the file. The
# value looked fine in every editor. Nothing in the chain looked at its shape.
#
# So: shape only. Length, line count, character class, and the markup
# signatures that mean "this is a document, not a secret". Never the value -
# not to stdout, not to a log, not to an exit message.
#
#   sh check_secret_files.sh [verzeichnis]
#
# Exit 0 only when every file is usable.

dir="${1:-secrets}"
problems=0

# Alphanumeric keeps the value out of every escaping question there is: the
# SQL string literal that creates the role, the shell that gets it there, and
# the compose file. A password nobody types has no reason to contain anything
# that needs quoting.
erwartet_zeichen='^[A-Za-z0-9]+$'
min_laenge=24

pruefe() {
    name="$1"
    pfad="$dir/$name"

    if [ ! -f "$pfad" ]; then
        echo "  $name: FEHLT"
        problems=$((problems + 1))
        return
    fi

    bytes=$(wc -c < "$pfad" | tr -d ' ')
    if [ "$bytes" -eq 0 ]; then
        echo "  $name: LEER - noch nichts eingetragen"
        problems=$((problems + 1))
        return
    fi

    # Read once, strip surrounding whitespace exactly like app.py does with
    # .strip(), so this check sees what the application will see.
    wert=$(tr -d '\r' < "$pfad" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    laenge=${#wert}
    zeilen=$(wc -l < "$pfad" | tr -d ' ')

    # The signatures of a document that was saved instead of a secret. RTF is
    # the one that actually happened; the others cost nothing to rule out.
    case "$wert" in
        '{\rtf'*|'{\*'*)  echo "  $name: RTF statt Klartext - in TextEdit Format > In reines Textformat umwandeln"
                          problems=$((problems + 1)); return ;;
        '<?xml'*|'<html'*|'%PDF'*|'PK'*)
                          echo "  $name: kein Klartext (Dokumentformat erkannt)"
                          problems=$((problems + 1)); return ;;
    esac

    if [ "$laenge" -lt "$min_laenge" ]; then
        echo "  $name: nur $laenge Zeichen, erwartet mindestens $min_laenge"
        problems=$((problems + 1))
        return
    fi

    # More than one non-empty line means something other than a bare secret -
    # a comment, a label, a pasted block. app.py would take the whole thing.
    inhaltszeilen=$(grep -c '[^[:space:]]' "$pfad" 2>/dev/null || echo 0)
    if [ "$inhaltszeilen" -gt 1 ]; then
        echo "  $name: $inhaltszeilen Zeilen mit Inhalt, erwartet genau eine"
        problems=$((problems + 1))
        return
    fi

    if ! echo "$wert" | grep -Eq "$erwartet_zeichen"; then
        echo "  $name: enthaelt Zeichen ausserhalb A-Z a-z 0-9"
        echo "         (nutzbar, aber jedes Sonderzeichen muss beim Anlegen der"
        echo "          Rolle escaped werden - vermeidbares Risiko)"
        problems=$((problems + 1))
        return
    fi

    echo "  $name: OK - $laenge Zeichen, eine Zeile, nur Buchstaben und Ziffern"
}

echo "--- Secret-Dateien in $dir/ ---"
pruefe workforce_api_db_password
pruefe workforce_api_key
pruefe workforce_backup_password

echo
if [ "$problems" -eq 0 ]; then
    echo "RESULT: PASS"
    exit 0
fi
echo "RESULT: FAIL ($problems)"
exit 1
