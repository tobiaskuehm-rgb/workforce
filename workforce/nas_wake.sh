#!/bin/sh
# Weckt die NAS per Wake-on-LAN und wartet, bis sie per ssh antwortet.
#
# Warum ueberhaupt: Ein einzelner ssh-Aufruf laeuft in den Timeout, waehrend die NAS bootet
# (Synology braucht rund ein bis drei Minuten). Dieses Skript schickt das Magic Packet und
# fragt danach in Abstaenden nach, statt einmal zu klopfen und aufzugeben.
#
# Grenzen, beide gemessen und nicht verhandelbar:
#   - Es wirkt nur im selben Netz. Das Paket ist ein Broadcast und wird nicht geroutet; ist
#     der Mac unterwegs, loest schon der Name nicht auf ("naskuehm.local nodename nor
#     servname"). Dann hilft WOL nicht, sondern nur, jemanden vor Ort zu bitten.
#   - Die NAS muss im Soft-Aus stehen, nicht am Schalter getrennt. Ihre Netzkarte hoert nur
#     dann mit (`support_wol="yes"`, `eth0_wol_options="g"`, gemessen 2026-09-13).
#
# Ziel ist eine Konstante (G-091); die MAC gehoert zur Maschine, nicht zur Umgebung.
set -eu
mac="90:09:d0:25:20:95"          # eth0 der NAS, gemessen 2026-09-13
host="synology"
wartezeit="${1:-180}"            # Sekunden, bis aufgegeben wird

if [ -n "${NAS_WAKE_MAC:-}${NAS_WAKE_HOST:-}" ]; then
  echo "FAIL: Ziel ist eine Konstante, keine Umgebungsvariable (G-091)" >&2; exit 1
fi

python3 - "$mac" <<'PY'
import socket, sys
mac = sys.argv[1].replace(":", "").replace("-", "")
if len(mac) != 12 or not all(c in "0123456789abcdefABCDEF" for c in mac):
    print(f"FAIL: MAC unbrauchbar: {sys.argv[1]}", file=sys.stderr); sys.exit(2)
# Magic Packet: sechs Byte 0xFF, dann die MAC sechzehnmal.
paket = b"\xff" * 6 + bytes.fromhex(mac) * 16
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
for port in (7, 9):               # beide ueblichen Ports, kostet nichts
    s.sendto(paket, ("255.255.255.255", port))
s.close()
print(f"Weckruf gesendet ({len(paket)} Byte, Ports 7 und 9)")
PY

echo "Warte bis zu ${wartezeit}s auf Antwort von $host ..."
ende=$(( $(date +%s) + wartezeit ))
versuch=0
while [ "$(date +%s)" -lt "$ende" ]; do
  versuch=$((versuch + 1))
  if ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "$host" true 2>/dev/null; then
    echo "RESULT: erreichbar nach ${versuch} Versuchen"
    exit 0
  fi
  sleep 10
done
# Nicht erreichbar heisst nicht erreichbar - kein "vielleicht laeuft sie ja doch" (Regel 74).
echo "FAIL: $host antwortet nach ${wartezeit}s nicht. Moeglich: Mac nicht im Heimnetz, NAS am Schalter getrennt, oder WOL kam nicht an." >&2
exit 1
