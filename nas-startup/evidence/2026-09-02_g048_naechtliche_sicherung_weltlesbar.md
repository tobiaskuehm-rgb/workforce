# `G-048`: Der nächtliche Sicherungsjob legt weltlesbare Dateien ab

**Datum:** 2026-09-02
**Gefunden von:** `check_backup_permissions.sh`, beim Routinestatus nach einem NAS-Neustart
**Freigabe für die Korrektur:** CEO im Chat
**Produktivänderung:** Rechte an zwei Dateien. Sonst nichts.

## Befund

`nas_status.sh` meldete zum ersten Mal `RESULT: FAIL`, Exit 1:

```
FAIL: 2 Datei(en) mit Welt-Leserecht:
/volume1/docker/Startup-Backups/workforce-2026-09-02_02-05-01.sql
/volume1/docker/Startup-Backups/config-2026-09-02_02-05-01.tar.gz
PASS: keine Datei mit Welt-Schreibrecht
PASS: kein everyone-Eintrag in der ACL
RESULT: FAIL (1)
```

Im Vergleich zum Vortag:

```
heute 02:05    -rw-r--r-- 1 root root            380952  workforce-2026-09-02_02-05-01.sql
heute 02:05    -rw-r--r-- 1 root root             27718  config-2026-09-02_02-05-01.tar.gz
gestern 02:05  -rw-r----- 1 root administrators  330502  workforce-2026-09-01_02-05-01.sql
```

## Warum das kein Neustartfolgeschaden ist

Der nächtliche DSM-Job schreibt mit der Umask des Auftrags, also `644 root:root`
— und hat das immer getan. Am 2026-09-01 wurden beim Schließen von `G-022` die
**vorhandenen** Dateien von Hand nachgezogen und die Synology-ACL entfernt; der
Job selbst blieb unverändert. In der ersten Nacht danach entstanden wieder
weltlesbare Dateien.

Der Wächter hat genau das vorhergesagt. Aus seinem eigenen Kopf:

> **Warum dieses Skript existiert und keine einmalige Prüfung:** Der nächtliche
> Sicherungsjob läuft als Root um 02:05 und erzeugt neue Dateien. Welche Rechte
> er ihnen gibt, wird nicht von hier gesteuert. Eine einmalige Verschärfung kann
> deshalb über Nacht erodieren, still, und nichts würde es sagen.

Betroffen war ein vollständiger Datenbank-Dump und ein Konfigurationsarchiv,
das `startup.env` enthält — also das Passwort des Eigentümerkontos. Lesbar für
jedes Konto auf der NAS.

## Korrektur

Über einen Wegwerf-Container unter `sudo docker`, weil die Dateien Root gehören
und die SSH-Sitzung als `TOBKUM` läuft (`G-043`):

```
-rw-r----- 1 root administrators  27718 Sep  2 02:05 config-2026-09-02_02-05-01.tar.gz
-rw-r----- 1 root administrators 380952 Sep  2 02:05 workforce-2026-09-02_02-05-01.sql
```

Danach:

```
PASS: keine Datei mit Welt-Leserecht
PASS: keine Datei mit Welt-Schreibrecht
PASS: kein everyone-Eintrag in der ACL
geprueft: 64 Datei(en)
RESULT: PASS

nas_status Exit: 0
```

## Dauerhaft

Die Korrektur von Hand hält bis morgen früh 02:05. `harden_backup_permissions.sh`
setzt den Zustand statt ihn zu finden und ist dafür gebaut, **von derselben
DSM-Aufgabe** aufgerufen zu werden, die die Sicherung schreibt:

```
sh /volume1/docker/Startup/harden_backup_permissions.sh
```

Diese Zeile muss der CEO in der DSM-Aufgabe hinter den Sicherungsbefehl setzen
— an den Aufgabenplaner komme ich nicht heran. **Bis das geschehen ist, ist der
Befund nur behoben, nicht geschlossen.**

Im Wegwerf-Container geprobt, mit einer absichtlich weltlesbaren Datei neben
einer korrekten:

```
vorher:
-rw-r-----    1 root     101     0  ok.sql
-rw-r--r--    1 root     root    0  weltlesbar.sql

zu weit offen, wird korrigiert: 1 Datei(en)
/probe/weltlesbar.sql
geprueft: 2 Datei(en)
RESULT: PASS
Exit: 0

nachher:
-rw-r-----    1 root     101     0  ok.sql
-rw-r-----    1 root     101     0  weltlesbar.sql

zweiter Lauf (muss idempotent sein):
geprueft: 2 Datei(en)
RESULT: PASS
```

Ohne Root verweigert es den Dienst mit Exit 1 und verweist auf den Weg über
einen Root-Container.

## Was dieser Eintrag nicht belegt

- **Die DSM-Aufgabe ist unverändert.** Der dauerhafte Teil steht aus.
- **Wie lange die Dateien offen standen**, lässt sich nicht mehr feststellen —
  sie entstanden um 02:05 und wurden gegen 07:40 korrigiert. Ob in dieser Zeit
  jemand darauf zugegriffen hat, sagt kein Protokoll, das ich gelesen habe.
- **Ältere Sicherungen** waren nicht betroffen; die Prüfung deckt alle 64
  Dateien im Ordner ab und meldet jetzt `PASS`.
