#!/bin/sh
set -eu

# Zeigt die Bus-Adresse noch auf diese NAS?
#
# Review finding G-051: `BUS_BASE_URL` stand in 17 Dateien und nirgends als
# Tatsache. Der Hostname ist ein **abgeleiteter** Name - Synology bildet ihn
# aus der LAN-Adresse, `192-168-68-81.<id>.direct.quickconnect.to` -, also
# aendert er sich, sobald DHCP die Adresse aendert. Genau dieselbe Klasse wie
# ein Containername aus Projektordner, Dienst und Index (G-042): er sieht
# stabil aus und ist es nicht.
#
# Am 2026-09-02 war er tot. Nach einem Neustart lag die NAS auf .81, im ganzen
# Repo stand .78, und dort antwortete `Connection refused`. Jedes Fenster -
# Contract-Test, Kettenlauf, Worker-Core, Telegram - waere an der ersten
# Verbindung gescheitert. Kein Test konnte das sehen: die lokalen Suiten
# laufen ohne Netz, und ein Deploy-Manifest prueft Pruefsummen, keine Adressen.
#
# Der Anschluss zum Zertifikat ist der Grund, warum der Name ueberhaupt so
# aussieht: Das NAS-Zertifikat traegt `*.<id>.direct.quickconnect.to`, damit
# verifiziert TLS **jede** Adressvariante dieses Musters gegen den Hostnamen.
# Das ist bequem und heisst zugleich, dass eine falsche Adresse nicht am
# Zertifikat auffaellt - sie faellt erst beim Verbinden auf, im Fenster.
#
# Prueft zwei Dinge und schreibt nichts:
#
#   1. die im Namen steckende Adresse gehoert dieser NAS
#   2. auf dem Port hoert jemand
#
#   ssh synology "cd /volume1/docker/Startup && sh check_bus_address.sh"

state="${PRODUCTION_STATE:-production_state.txt}"

[ -f "$state" ] || { echo "$state fehlt" >&2; exit 1; }

problems=0
fail() {
    echo "FAIL: $1"
    problems=$((problems + 1))
}

url="$(sed -n 's/^BUS_BASE_URL=//p' "$state" | head -1)"
if [ -z "$url" ]; then
    echo "FAIL: $state nennt kein BUS_BASE_URL"
    exit 1
fi
echo "Adresse laut $state: $url"

# https://<host>:<port> - ohne Pfad, so wie validate_base_url() es verlangt.
rest="${url#https://}"
host="${rest%%:*}"
port="${rest##*:}"
case "$url" in
    https://*) ;;
    *) fail "BUS_BASE_URL ist kein https"; ;;
esac
case "$port" in
    ''|*[!0-9]*) fail "kein Port in BUS_BASE_URL"; port="" ;;
esac

# Das erste Namenslabel traegt die Adresse: 192-168-68-81 -> 192.168.68.81.
# Passt es nicht auf dieses Muster, ist es ein anderer Namenstyp und diese
# Pruefung sagt nichts - sie schweigt dann, statt etwas zu behaupten.
label="${host%%.*}"
case "$label" in
    [0-9]*-[0-9]*-[0-9]*-[0-9]*)
        eingebettet="$(echo "$label" | tr '-' '.')"
        echo "im Namen steckt: $eingebettet"
        eigene="$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1)"
        if [ -z "$eigene" ]; then
            fail "eigene Adressen nicht lesbar"
        elif echo "$eigene" | grep -qx "$eingebettet"; then
            echo "PASS: die Adresse gehoert dieser NAS"
        else
            fail "die Adresse gehoert dieser NAS nicht - eigene: $(echo "$eigene" | tr '\n' ' ')"
        fi
        ;;
    *)
        echo "HINWEIS: $label ist keine eingebettete Adresse - nicht pruefbar"
        ;;
esac

if [ -n "$port" ]; then
    if netstat -tln 2>/dev/null | grep -q "[:.]$port "; then
        echo "PASS: auf Port $port hoert jemand"
    else
        fail "auf Port $port hoert niemand - Reverse Proxy aus?"
    fi
fi

echo
if [ "$problems" -eq 0 ]; then
    echo "RESULT: PASS"
else
    echo "RESULT: FAIL ($problems)"
    exit 1
fi
