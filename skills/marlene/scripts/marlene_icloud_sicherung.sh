#!/bin/bash
# marlene_icloud_sicherung.sh - iCloud Drive dieses Macs auf die NAS spiegeln.
#
# Warum vom Mac aus und nicht von der NAS aus: Synology Cloud Sync (wie jedes NAS)
# kann iCloud Drive nicht als Quelle ansprechen, das liegt an Apple und nicht am
# Geraet (Befund 2026-09-10, https://www.synology-forum.de/threads/cloud-sync-mit-icloud-drive.113248/).
# Der Mac hat die Dateien ohnehin lokal (bei ausgeschaltetem "Speicher optimieren"),
# also schiebt er sie stattdessen selbst rueber.
#
# Kein --delete: was hier geloescht wird, bleibt auf der NAS stehen. Das ist Absicht,
# dieselbe Regel wie bei A66 fuer den bestehenden Google-Spiegel - ein Sync ist keine
# Versionierung, aber wenigstens nimmt ein Fehlgriff auf dem Mac nichts auf der NAS mit.
#
# Aufruf:
#   marlene_icloud_sicherung.sh            Trockenlauf, schreibt nichts, zeigt nur was waere
#   marlene_icloud_sicherung.sh --real     schreibt wirklich

set -euo pipefail

QUELLE="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
ZIEL_HOST="synology"
ZIEL_PFAD="/volume1/iCloud-Sicherung"
PROTOKOLL="$HOME/Library/CloudStorage/GoogleDrive-Tobias.kuehm@icloud.com/Meine Ablage/01_Ablage_Eingang/_Marlene/protokoll/icloud_sicherung.log"

TROCKEN="--dry-run"
if [ "${1:-}" = "--real" ]; then
  TROCKEN=""
fi

if ! ssh -o ConnectTimeout=8 "$ZIEL_HOST" true 2>/dev/null; then
  echo "ABBRUCH: NAS ($ZIEL_HOST) nicht erreichbar. Nichts geschrieben." >&2
  exit 1
fi

ssh "$ZIEL_HOST" "mkdir -p '$ZIEL_PFAD'"

ZEIT=$(date +%FT%T)
ERGEBNIS=$(rsync -av $TROCKEN \
  --exclude ".DS_Store" \
  --exclude "Desktop" \
  --exclude "Documents" \
  -e ssh \
  "$QUELLE/" "$ZIEL_HOST:$ZIEL_PFAD/iCloud-Drive/")

ERGEBNIS2=$(rsync -av $TROCKEN \
  --exclude ".DS_Store" \
  -e ssh \
  "$HOME/Desktop/" "$ZIEL_HOST:$ZIEL_PFAD/Desktop/")

ERGEBNIS3=$(rsync -av $TROCKEN \
  --exclude ".DS_Store" \
  --exclude "Codex" --exclude "ChatGPT" --exclude "curseforge" \
  -e ssh \
  "$HOME/Documents/" "$ZIEL_HOST:$ZIEL_PFAD/Documents/")

ZEILEN1=$(echo "$ERGEBNIS" | grep -c '^>' || true)
ZEILEN2=$(echo "$ERGEBNIS2" | grep -c '^>' || true)
ZEILEN3=$(echo "$ERGEBNIS3" | grep -c '^>' || true)

MODUS="TROCKENLAUF"; [ -z "$TROCKEN" ] && MODUS="ECHT"
mkdir -p "$(dirname "$PROTOKOLL")"
echo "$ZEIT $MODUS iCloud-Drive=$ZEILEN1 Desktop=$ZEILEN2 Documents=$ZEILEN3" >> "$PROTOKOLL"
echo "$MODUS: iCloud-Drive $ZEILEN1, Desktop $ZEILEN2, Documents $ZEILEN3 Dateien uebertragen (oder wuerden es im Trockenlauf)"
