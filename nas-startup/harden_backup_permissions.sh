#!/bin/sh
set -eu

# Puts every file in the backup folder back to root:administrators / 640.
#
# Review finding G-048: the nightly DSM task writes its dump and its config
# archive with the job's umask, which is `644 root:root`. On 2026-09-01 the
# existing files were tightened by hand while closing G-022; the job itself was
# never changed. The first night after that, 2026-09-02 at 02:05, it produced
# two world-readable files again - a full database dump and a config archive
# containing startup.env, and with it the owner's password.
#
# check_backup_permissions.sh found it, which is what it was written for
# ("a single tightening can erode overnight, silently, and nothing would say
# so"). Finding it every morning is not the same as preventing it, so this
# script exists to be called by the same scheduled task that writes the files:
#
#   sh /volume1/docker/Startup/harden_backup_permissions.sh
#
# Von Hand, falls die Aufgabe nicht als root laeuft - ueber einen
# Wegwerf-Container, weil die Dateien root gehoeren:
#
#   sudo /usr/local/bin/docker run --rm -v /volume1/docker/Startup-Backups:/backup \
#     postgres:17-alpine sh -c 'chown -R 0:101 /backup && chmod -R u=rw,g=r,o= /backup'
#
# Append that line to the DSM task *after* the backup command. It has to run as
# root, because the files belong to root - and the DSM scheduler runs its tasks
# as root, so there is nothing extra to arrange.
#
# Idempotent by construction: it sets a state, it does not toggle one. Running
# it twice changes nothing the second time.
#
# It prints file names and counts, never contents. It does not delete anything
# and does not create anything - guardrail 2, and a backup folder is the last
# place to make an exception.

backups="${BACKUP_DIR:-/volume1/docker/Startup-Backups}"
[ -d "$backups" ] || { echo "$backups fehlt" >&2; exit 1; }

# Group 101 is `administrators` on this NAS. The number rather than the name,
# for the same reason the Docker secrets are handed over by number (G-044):
# inside a container the name may not exist, and this script is meant to be
# usable from one.
group="${BACKUP_GROUP:-101}"

if [ "$(id -u)" -ne 0 ]; then
    echo "FAIL: laeuft nicht als root - chown auf root-eigene Dateien schlaegt fehl" >&2
    echo "      Der DSM-Aufgabenplaner fuehrt Aufgaben als root aus. Fuer den Weg" >&2
    echo "      von Hand ueber einen Root-Container siehe den Kopf dieser Datei." >&2
    exit 1
fi

vorher="$(find "$backups" -type f \( -perm -o=r -o -perm -o=w \) | wc -l | tr -d ' ')"

if [ "$vorher" -ne 0 ]; then
    echo "zu weit offen, wird korrigiert: $vorher Datei(en)"
    find "$backups" -type f \( -perm -o=r -o -perm -o=w \) -print | head -20
fi

# u=rw,g=r,o= is 640 written so it cannot be misread, and it never touches the
# execute bit of a directory.
find "$backups" -type f -exec chown "0:$group" {} +
find "$backups" -type f -exec chmod u=rw,g=r,o= {} +
chown "0:$group" "$backups"
chmod u=rwx,g=rx,o= "$backups"

nachher="$(find "$backups" -type f \( -perm -o=r -o -perm -o=w \) | wc -l | tr -d ' ')"
echo "geprueft: $(find "$backups" -type f | wc -l | tr -d ' ') Datei(en)"

if [ "$nachher" -eq 0 ]; then
    echo "RESULT: PASS"
else
    echo "RESULT: FAIL ($nachher Datei(en) weiterhin zu offen)"
    exit 1
fi
