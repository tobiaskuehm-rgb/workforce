#!/bin/bash
# marlene_icloud_sicherung.sh - iCloud Drive dieses Macs auf die NAS spiegeln.
#
# Warum vom Mac aus und nicht von der NAS aus: Synology Cloud Sync kann iCloud
# Drive nicht als Quelle ansprechen, das liegt an Apple und gilt fuer jeden
# NAS-Hersteller (Befund 2026-09-10).
#
# Warum tar statt rsync: /usr/bin/rsync auf dieser NAS ist SUID-root, und ein
# Administrator-Konto (TOBKUM ist in der Gruppe administrators) wird dabei von
# DSM zu einer interaktiven Passwortbestaetigung gezwungen ("Permission denied,
# please try again." nach erfolgreicher SSH-Anmeldung, sudo bestaetigt "a
# password is required"). Das laesst sich nicht automatisieren und ist gewollter
# Schutz, keine Luecke, die umgangen werden sollte. tar ueber SSH braucht diese
# Rechte nicht und ist derselbe Weg, der schon beim Holen der NAS-Scans lief.
#
# Kein Loeschen auf der NAS: jeder Lauf entpackt in einen neuen, datierten
# Unterordner. Alte Staende bleiben liegen, das ist die einzige Versionierung,
# die dieses Skript ohne DSM-Snapshots bieten kann (A67 bleibt trotzdem offen).
#
# Aufruf:
#   marlene_icloud_sicherung.sh            Trockenlauf: zaehlt nur, schreibt nichts
#   marlene_icloud_sicherung.sh --real     schreibt wirklich

set -euo pipefail

QUELLEN=("$HOME/Library/Mobile Documents/com~apple~CloudDocs" "$HOME/Desktop" "$HOME/Documents")
ZIEL_HOST="synology"
ZIEL_BASIS="/volume1/Marlene/backup/iCloud"
PROTOKOLL="$HOME/Library/CloudStorage/GoogleDrive-Tobias.kuehm@icloud.com/Meine Ablage/01_Ablage_Eingang/_Marlene/protokoll/icloud_sicherung.log"
STICHTAG=$(date +%F_%H%M)

TROCKEN=1
[ "${1:-}" = "--real" ] && TROCKEN=0

if ! ssh -o ConnectTimeout=8 "$ZIEL_HOST" true 2>/dev/null; then
  echo "ABBRUCH: NAS ($ZIEL_HOST) nicht erreichbar. Nichts geschrieben." >&2
  exit 1
fi

GESAMT=0
for Q in "${QUELLEN[@]}"; do
  NAME=$(basename "$Q")
  N=$(find "$Q" -type f -not -name ".DS_Store" -not -path "*/Codex/*" -not -path "*/ChatGPT/*" -not -path "*/curseforge/*" -not -path "*/Desktop/Desktop/*" -not -path "*/Documents/Documents/*" 2>/dev/null | wc -l | tr -d ' ')
  GESAMT=$((GESAMT + N))
  echo "$NAME: $N Dateien"
  if [ "$TROCKEN" -eq 0 ]; then
    ( cd "$Q" && COPYFILE_DISABLE=1 tar cf - --exclude=".DS_Store" --exclude="Codex" --exclude="ChatGPT" --exclude="curseforge" . ) \
      | ssh "$ZIEL_HOST" "mkdir -p '$ZIEL_BASIS/$STICHTAG/$NAME' && tar xf - -C '$ZIEL_BASIS/$STICHTAG/$NAME'"
  fi
done

MODUS="TROCKENLAUF"; [ "$TROCKEN" -eq 0 ] && MODUS="ECHT"
mkdir -p "$(dirname "$PROTOKOLL")"
echo "$(date +%FT%T) $MODUS Stichtag=$STICHTAG Dateien=$GESAMT" >> "$PROTOKOLL"
echo "$MODUS: $GESAMT Dateien, Stichtag $STICHTAG"
