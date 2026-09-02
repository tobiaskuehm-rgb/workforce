#!/bin/sh
set -eu

# Was liegt im Produktionsordner, das keine Pruefung sehen kann?
#
# Review finding G-060. `verify_manifest.sh` meldet zuverlaessig, was *innerhalb*
# der genannten Pfade fehlt, abweicht oder unerwartet ist - und schweigt ueber
# alles daneben. Ein ganzer Ordner, der in keiner Pfadliste steht, ist damit
# nicht "nicht abgedeckt", sondern unsichtbar; das Manifest meldet `PASS`.
#
# Was das gekostet hat, war am 2026-09-02 messbar: `bus-realtest/` stand in
# keiner Liste, und fuenf seiner Dateien wichen ab. Zwei davon trugen die
# Verengung aus `G-017` nicht - die Hilfscontainer haetten auf der NAS
# weiterhin `startup.env` bekommen, also `WORKFORCE_API_KEY` und den
# Telegram-Token. Der Befund war im Repo behoben und in der Produktion nicht.
#
# Diese Pruefung stellt die andere Frage: **Kann die Pruefung ueberhaupt
# sehen, was dort liegt?** Sie vergleicht die oberste Ebene des
# Produktionsordners gegen `deploy_paths.txt` und gegen eine kurze,
# begruendete Liste von Dingen, die absichtlich nicht versioniert sind.
#
# Liest nur. Nennt Namen, nie Inhalte.
#
#   ssh synology "cd /volume1/docker/Startup && sh check_unmanaged.sh"

liste="${DEPLOY_PATHS:-deploy_paths.txt}"

[ -f "$liste" ] || { echo "FAIL: $liste fehlt"; exit 1; }

# Absichtlich nicht versioniert, je mit Grund. Wer hier etwas ergaenzt, trifft
# eine Entscheidung - und eine Liste ohne Gruende waere ein Abstellgleis.
#
#   DEPLOY_MANIFEST.txt      Bauartefakt, entsteht bei jedem Deploy
#   Versionen                abgeloeste Dateien, datiert abgelegt (Leitplanke 2)
#   secrets startup.env      Geheimnisse, gehoeren bauartbedingt nicht ins Git
#   startup.db.env           abgeleitete Datenbankwerte, dito
#   REVIEW_GERD.before-*     Momentaufnahmen des Pruefers, von ihm angelegt
#   NAS_*.zip .tar .tar.gz   Auslieferungsarchive aus der Zeit vor dem Git-Deploy
erlaubt_muster='^(DEPLOY_MANIFEST\.txt|Versionen|secrets|startup\.env|startup\.db\.env|REVIEW_GERD\.before-.*|NAS_.*\.(zip|tar|tar\.gz))$'

# Die Pfadliste, Kommentare und Leerzeilen heraus.
pfade="$(sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$liste")"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
find . -mindepth 1 -maxdepth 1 -print | sed 's#^\./##' | sort > "$work/eintraege"

problems=0
: > "$work/unbekannt"

# No `for x in $(ls)`: it splits a single name containing whitespace into
# several fictitious entries and can hide the real unmanaged path.
while IFS= read -r eintrag; do
    if echo "$eintrag" | grep -Eq "$erlaubt_muster"; then
        continue
    fi
    # Deckt die Liste diesen Namen ab? Ein Pfad deckt sich selbst und alles
    # darunter; auf oberster Ebene genuegt der erste Abschnitt.
    if echo "$pfade" | sed 's#/.*##' | grep -qx "$eintrag"; then
        continue
    fi
    printf '%s\n' "$eintrag" >> "$work/unbekannt"
    problems=$((problems + 1))
done < "$work/eintraege"

echo "geprueft: $(wc -l < "$work/eintraege" | tr -d ' ') Eintraege auf oberster Ebene"

if [ "$problems" -eq 0 ]; then
    echo "PASS: jeder Eintrag ist entweder im Deploy oder begruendet ausgenommen"
    echo
    echo "RESULT: PASS"
else
    echo "FAIL: von keiner Pfadliste erfasst:"
    sed 's/^/      /' "$work/unbekannt"
    echo "      Ein Manifest meldet darueber PASS, weil es nicht hinsieht (G-060)."
    echo
    echo "RESULT: FAIL ($problems)"
    exit 1
fi
