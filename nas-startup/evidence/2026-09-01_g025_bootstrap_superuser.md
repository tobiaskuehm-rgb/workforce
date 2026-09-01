# `G-025` lässt sich nicht per `ALTER ROLE` schließen — `G-045`

**Datum:** 2026-09-01
**Anlass:** CEO-Freigabe im Chat, `G-025` vorzubereiten **und auszuführen**
**Ergebnis:** Nicht ausgeführt. Der dokumentierte Schritt ist auf dieser
Datenbank nicht ausführbar. Die Produktion wurde nicht verändert.

## Was geplant war

Migration `007` nennt in ihrem Kopf den letzten Schritt wörtlich:

```sql
ALTER ROLE workforce_app NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS;
```

mit der Begründung, `workforce_app` bleibe Eigentümer und Migrationskonto,
und DDL auf dem eigenen Schema brauche keinen Superuser.

## Was die Probe ergeben hat

Der erste Teil stimmt: DDL, Dumps und der Bus laufen ohne `SUPERUSER` weiter.
Der Schritt scheitert an etwas anderem.

**`workforce_app` ist der Bootstrap-Superuser.** Produktiv nachgesehen:

```
SELECT oid, rolname, rolsuper FROM pg_roles WHERE oid = 10;
10|workforce_app|t
```

Das ist kein Zufall, sondern Bauart: `initdb` macht `POSTGRES_USER` zum
Bootstrap-Superuser, und `startup.env` setzt dort `workforce_app`. Und
PostgreSQL lässt diesen Rollen ihr Superuser-Attribut nicht nehmen:

```
ERROR:  permission denied to alter role
DETAIL:  The bootstrap superuser must have the SUPERUSER attribute.
```

Die Anweisung schlägt **als Ganzes** fehl; es ändert sich nichts. Die drei
übrigen Attribute lassen sich einzeln entfernen (`workforce_app|t|f|f|f`),
aber das ist wirkungslos: Ein Superuser überschreibt `CREATEROLE`,
`CREATEDB` und `BYPASSRLS` ohnehin.

**Es gibt keinen zweiten Superuser.** `SELECT rolname FROM pg_roles WHERE
rolsuper` liefert produktiv genau eine Zeile. Wäre der Entzug möglich
gewesen, hätte ihn niemand zurücknehmen können — der Plan enthielt eine
Einbahnstraße, die niemandem aufgefallen war.

## Zwei weitere Messergebnisse

**Der Rollen-Dump bräche.** Ohne `SUPERUSER` scheitert `pg_dumpall
--globals-only` an `permission denied for table pg_authid` (Exit 1, 229 Byte
statt 1504). Das ist genau der Dump, den `G-024` zur Pflicht gemacht hat.
`--no-role-passwords` läuft, liefert aber Rollen ohne Passwörter — ein
Restore müsste sie danach aus den Secret-Dateien setzen. Für die künftige
Eigentümertrennung vorgemerkt; heute nicht nötig, weil `workforce_app`
Superuser bleibt.

**Der Superuser-Entzug hätte die Audit-Trigger nicht geschützt.** Gemessen,
vorher wie nachher:

```
Audit-Trigger abschalten (workforce_app)   erlaubt
dito, DISABLE TRIGGER ALL                  erlaubt
```

Die Kommentare in `006` und `007` führen als Begründung an, ein Superuser
könne die Append-only-Trigger abschalten. Das stimmt — aber der **Eigentümer**
kann es auch. `NOSUPERUSER` allein hätte das Loch nicht geschlossen.

## Der Rückfallpfad ist damit erstmals geübt

Phase A der Probe hat die Sicherung `preflight-2026-09-01_22-18-42` in einen
Wegwerf-Container zurückgespielt — erst Rollen-Dump, dann Datenbank-Dump:

```
Phase A - Rueckfallprobe aus der Sicherung:
  Migrationszeilen: 3, Tabellen im Schema workforce: 15
```

Drei Migrationszeilen sind korrekt: Der Dump stammt von **vor** dem
Phase-4-Fenster. Meine erste Erwartung war 6 und damit falsch — die
Wiederherstellung war es nicht.

Der Phase-4-Nachweis musste festhalten, dass der Rückfallpfad ungeübt sei.
Das gilt nicht mehr.

## Was daraus folgt

`G-025` ist keine `ALTER ROLE`-Frage, sondern eine **Eigentümerfrage**. Wer
den Superuser aus dem Datenpfad haben will, braucht einen eigenen,
nicht-privilegierten Eigentümer für Schema, Tabellen und Funktionen. Das ist
deshalb kein Einzeiler:

- die zehn `SECURITY DEFINER`-Funktionen laufen **als ihr Eigentümer**; ein
  Wechsel ändert, mit welchen Rechten sie ausgeführt werden
- der Gate-Runner verbindet sich als `POSTGRES_USER` aus `startup.env` und
  würde neue Objekte weiter als `workforce_app` anlegen
- `REASSIGN OWNED BY` ist nicht additiv und braucht ein eigenes Fenster

Das ist eine Entwurfsarbeit mit eigener Migration, eigener Probe und eigener
Freigabe — nicht der Nachtrag, als der es im Kopf von `007` steht.

## Vollständiger Lauf

Wiederholbar mit `python3 g025_nosuperuser_test.py` (braucht SSH-Zugang zur
NAS; Testdaten in `tmpfs`, kein Volume, Container mit `docker rm -f`).

```
Sicherung: /volume1/docker/Startup-Backups/preflight-2026-09-01_23-27-46.sql
Rollen-Dump: /volume1/docker/Startup-Backups/preflight-2026-09-01_23-27-46.globals.sql

Phase A - Rueckfallprobe aus der Sicherung:
  Migrationszeilen: 6, Tabellen im Schema workforce: 16
  Rollen in der Probe: workforce_api,workforce_app,workforce_backup

Phase B - Probe gegen den laufenden Stand:
  Migrationszeilen produktiv: 6, in der Probe: 6
workforce_app rolsuper vor der Umstellung: t

--- Grundlinie: workforce_app ist noch SUPERUSER ---
  pg_dump als workforce_app                  exit=0 bytes=380952
  pg_dumpall --globals-only                  exit=0 bytes=1504
  dito, --no-role-passwords                  exit=0 bytes=924
  Migrations-DDL (zurueckgerollt)            BEGIN | SYSTEM-MIGRATION | MIG-G025-PROBE | CREATE TABLE | CREATE FUNCTION | CREATE TRIGGER | GRANT | ALTER DEFAULT PRIVILEGES | INSERT 0 1 | ROLLBACK | DDL-Pro
  pg_dump als workforce_backup               exit=0 bytes=380952
  bus_record_denial als workforce_api        2
  workforce_api liest bus_denials            ERROR:  permission denied for table bus_denials
  Audit-Trigger abschalten (workforce_app)   erlaubt (Trigger wieder eingeschaltet)
  dito, DISABLE TRIGGER ALL                  erlaubt (Trigger wieder eingeschaltet)
  pg_authid lesen                            19

workforce_app nach der Umstellung (super|createrole|createdb|bypassrls): f|f|f|f

--- Nach ALTER ROLE ... NOSUPERUSER ---
  pg_dump als workforce_app                  exit=0 bytes=381059
  pg_dumpall --globals-only                  exit=1 bytes=229
pg_dumpall: error: query failed: ERROR:  permission denied for table pg_authid
  dito, --no-role-passwords                  exit=0 bytes=932
  Migrations-DDL (zurueckgerollt)            BEGIN | SYSTEM-MIGRATION | MIG-G025-PROBE | CREATE TABLE | CREATE FUNCTION | CREATE TRIGGER | GRANT | ALTER DEFAULT PRIVILEGES | INSERT 0 1 | ROLLBACK | DDL-Pro
  pg_dump als workforce_backup               exit=0 bytes=381059
  bus_record_denial als workforce_api        3
  workforce_api liest bus_denials            ERROR:  permission denied for table bus_denials
  Audit-Trigger abschalten (workforce_app)   erlaubt (Trigger wieder eingeschaltet)
  dito, DISABLE TRIGGER ALL                  erlaubt (Trigger wieder eingeschaltet)
  pg_authid lesen                            ERROR:  permission denied for table pg_authid

--- Phase C: workforce_app ist der Bootstrap-Superuser, wie produktiv ---
  Ausgangslage                               10|workforce_app|t
  Befehl aus dem Kopf von 007                ERROR:  permission denied to alter role | DETAIL:  The bootstrap superuser must have the SUPERUSER attribute.
  Zustand danach                             workforce_app|t|t|t|t
  Nur die drei anderen Attribute             ALTER ROLE
  Zustand danach                             workforce_app|t|f|f|f
  Ergebnis: SUPERUSER laesst sich hier nicht entziehen; die drei anderen
            Attribute schon - wirkungslos, solange SUPERUSER sie ueberschreibt.

Aufgeraeumt. Reste: keine
```
