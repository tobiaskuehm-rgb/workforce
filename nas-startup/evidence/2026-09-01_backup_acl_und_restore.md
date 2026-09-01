# Nachweis: Backup-Rechte gehärtet und Restore erstmals bewiesen

**Datum:** 2026-09-01
**Anlass:** Prüfbefunde `G-022` (Backup-ACL) und `G-024` (Restore nie durchgeführt)
**Freigabe:** CEO im Chat, ausdrücklich für die Rechteänderung und den Restore-Test
**Ergebnis:** `G-022` **behoben und nachgemessen**, `G-024` **Restore erstmals belegt**

---

## Teil 1 — `G-022`: Die Sicherungen waren für jeden lesbar

### Befund geprüft, nicht übernommen

Gerd nannte „SQL- und Konfigurationsbackups sind über die Synology-ACL für `everyone` lesbar". Selbst gemessen:

```
[6] everyone::allow:r-x---a-R-c--:fd--   (vererbend auf Dateien und Ordner)
drwxrwxrwx+  /volume1/docker/Startup-Backups
-rwxrwxrwx+  53 Dateien darin
```

**Bestätigt, und schwerer als beschrieben.** Der Inhalt, namentlich geprüft:

- **25 Konfigurationsarchive** `config-*.tar.gz` — enthalten `compose.yaml`, die vollständige `workforce-api/` und **`startup.env`** mit Datenbankpasswort und `WORKFORCE_API_KEY`
- **26 vollständige SQL-Dumps** `workforce-*.sql`, täglich um 02:05, der neueste 330 KB — enthalten Nachrichteninhalte, Tasks, Handoffs, den Mitarbeiterregistereintrag und die Credential-Tabelle

Jeder NAS-Benutzer konnte beides lesen.

### Ein Teil des Befunds trifft nicht zu

**`startup.env` selbst war nie exponiert.** Die Datei meldet „It's Linux mode" — sie hat gar keine ACL und steht auf `rw-rw---- root:users`. Die Härtung vom 2026-08-31 hält. Betroffen war ausschließlich der Backup-Pfad, also die *Kopien* in den Archiven.

### Zwei Schritte, zwei Wirkungen

**Der CEO hat zuerst in DSM** die vier Konten mit Lesezugriff auf den `docker`-Ordner (`Drucker`, `guest`, `MaraKühm`, `Marlen`) auf „Kein Zugriff" gesetzt. Nachgemessen: Sie haben jetzt explizite `deny`-Einträge. **Der `everyone`-Eintrag blieb** — er stammt aus den POSIX-Welt-Bits, nicht aus der Benutzerliste, und ist in DSM dort nicht abschaltbar.

**Danach, nach ausdrücklicher Freigabe**, eng begrenzt auf `/volume1/docker/Startup-Backups`:

```
chown -R 0:101        # root:administrators
chmod 750 (Ordner) / 640 (Dateien)
```

Nichts am `docker`-Ordner insgesamt, nichts an `Startup/`, nichts am Backup-Job.

### Endstand, gemessen

| | vorher | nachher |
|---|---|---|
| ACL | `everyone: allow r-x`, vererbend | **keine ACL** („Linux mode") |
| Ordner | `drwxrwxrwx` `TOBKUM:users` | `drwxr-x---` `root:administrators` |
| Dateien | `-rwxrwxrwx` | `-rw-r-----` |
| Dateien mit Welt-Leserecht | **53** | **0** |
| Zugriff `TOBKUM` | über `everyone` | über `administrators` — geprüft, liest weiter |
| Produktivstack | `Up (healthy)` | unverändert `Up (healthy)` |

### Was offen bleibt

**Der nächtliche Backup-Job läuft als Root und legt neue Dateien an.** Welche Rechte er ihnen gibt, ist von hier nicht gesteuert. Eine einmalige Härtung kann über Nacht erodieren, ohne dass es jemand bemerkt.

`check_backup_permissions.sh` prüft deshalb dauerhaft: keine Welt-Lese- und keine Welt-Schreibrechte, kein `everyone` in der ACL. **Nach dem nächsten Lauf um 02:05 erneut ausführen** — bis dahin ist unbekannt, ob die Härtung hält.

Die Rotation der im Archiv gelegenen Zugangsdaten ist **nicht** erfolgt und bleibt eine eigene Entscheidung: Wer die Sicherungen in den vergangenen Wochen gelesen hat, ist nicht feststellbar.

---

## Teil 2 — `G-024`: Der Restore war nie durchgeführt

### Befund bestätigt, und der erste Versuch schlug fehl

Isolierter Aufbau: eigener `postgres:17-alpine`-Container, eigenes Docker-Netz, `tmpfs` statt Volume, keine Verbindung zur Produktivdatenbank. Eingespielt wurde `workforce-2026-09-01_02-05-01.sql` (330.502 Bytes).

**Erster Versuch: sieben Fehler.**

```
ERROR:  role "workforce_app" does not exist
```

Der Dump stammt aus `pg_dump`, nicht `pg_dumpall`. Er enthält `ALTER ... OWNER TO workforce_app`, aber **kein `CREATE ROLE`**. Struktur und Daten kamen trotzdem an — alles gehörte danach `postgres`.

**Das ist kein Schönheitsfehler.** Zehn der 24 Funktionen sind `SECURITY DEFINER`; sie hätten nach einem solchen Restore als `postgres` gelaufen statt als `workforce_app`, also mit anderen Rechten als im Original.

### Zweiter Versuch: die Wiederherstellungsvorschrift

```sql
CREATE ROLE workforce_app LOGIN PASSWORD '<aus startup.env>';
psql -U postgres -d <ziel> -f workforce-JJJJ-MM-TT_HH-MM-SS.sql
```

**Fehlerzeilen: 0.** Gegengeprüft:

| | |
|---|---|
| Tabellen in `workforce` | 15, Eigentümer `workforce_app` |
| Funktionen | 24, davon 10 `SECURITY DEFINER`, Eigentümer `workforce_app` |
| Nachrichten / Tasks / Handoffs | 24 / 7 / 8 |
| Credentials | 19 |
| Audit-Ereignisse | 226 |
| Migrationen | `001_employee_registry`, `002_workforce_bus`, `003_workforce_bus_trigger_fix` |

### Der Abgleich mit der Produktion

Die Produktion zeigt mehr: 28 Nachrichten, 9 Tasks, 21 Credentials, 9 Mitarbeiter, 248 Audit-Ereignisse. **Die Differenz ist namentlich aufgeklärt** — sie besteht ausschließlich aus dem Kettenlauf, der nach der Sicherung lief:

```
CREDENTIAL  CRED-CHAIN-AGENT-CHAIN20260901       04:58
CREDENTIAL  CRED-CHAIN-CONNECTOR-CHAIN20260901   04:58
EMPLOYEE    CEO-TG-CHAIN20260901
MESSAGE     4 Stueck                             05:04 – 05:13
TASK        ENG-CHAIN-20260901, ENG-CHAIN-20260902
```

Der Dump von 02:05 ist damit **vollständig und getreu für seinen Zeitpunkt**. Der Verlust bei einem Restore wäre die Arbeit seit der letzten Nacht — die Eigenschaft einer täglichen Sicherung, kein Defekt.

### Rückbau

Container und Netz entfernt, geprüft: null Reste. Produktivdatenbank während des gesamten Tests nur **lesend** angefasst.

### Was offen bleibt

- **Die Sicherungen liegen weiterhin nur auf derselben NAS.** Ein Plattenausfall nimmt Produktion und Sicherung gemeinsam. Dagegen hilft weder die ACL noch dieser Nachweis.
- **`pg_dump` statt `pg_dumpall`:** Die Rolle muss bei jedem Restore von Hand angelegt werden. Alternativ den Backup-Job auf `pg_dumpall --globals-only` als zweite Datei erweitern — das ist eine Änderung am Backup-Job und braucht eine eigene Entscheidung.
- **Ein Restore auf fremder Hardware ist nicht geprüft.** Dieser Test lief auf derselben NAS.
