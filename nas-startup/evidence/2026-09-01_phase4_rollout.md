# Phase-4-Rollout: v7 → v8, Migrationen 005–007

**Datum:** 2026-09-01, Fenster 22:18–22:36 (NAS-Zeit)
**Ausgeführt von:** Claude Code
**Freigaben:** CEO im Chat (ausdrücklich, für genau dieses Fenster) und Gerds
elfter Zielcheck auf `0966cbb` („`G-043` ist geschlossen. Technisches GO für
das bereits freigegebene Phase-4-Fenster.")
**Ausgerollter Stand:** siehe `production_state.txt`

## Was das Fenster geändert hat

| | vorher | nachher |
|---|---|---|
| API | `startup-workforce-api:v7` | `startup-workforce-api:v8` |
| Migrationen | `001`–`003` | `001`–`003`, `005`, `006`, `007` |
| Rollen | nur `workforce_app` | zusätzlich `workforce_api`, `workforce_backup` |
| DB-Container | mit `/docker-entrypoint-initdb.d` | ohne (`G-041` im laufenden System) |
| API-Zugangsdaten | `startup.env` | eigene Secret-Dateien |

**Nicht geändert:** Kanal bleibt `DISABLED`, 0 aktive Credentials, Knowledge
`004` und `008` nicht angewendet, kein Telegram, kein Modellaufruf.

## Sicherung (Abschnitt 3)

Zeitstempel für alle Dateien: `2026-09-01_22-18-42`.

```
im Container gezaehlt: 357575       (pg_dump)
im Container gezaehlt: 681          (pg_dumpall --globals-only)

-rw-r----- 1 root administrators      681 Sep  1 22:19 preflight-2026-09-01_22-18-42.globals.sql
-rw-r----- 1 root administrators   357575 Sep  1 22:19 preflight-2026-09-01_22-18-42.sql
-rw-r----- 1 root administrators 75059200 Sep  1 22:19 rollback-workforce-api-v7-2026-09-01_22-18-42.tar.gz
-rw-r----- 1 root administrators     4685 Sep  1 22:22 compose-v7-2026-09-01_22-18-42.yaml

--- Kopf des Rollen-Dumps ---
--
-- PostgreSQL database cluster dump
--
```

Größen innen und außen identisch. Die `compose.yaml`-Sicherung ist mit `cmp`
gegen das Original geprüft: `identisch`.

## Rollen (Abschnitt 4)

```
Zeilen in rollen.sql: 2
CREATE ROLE
CREATE ROLE

workforce_api|f|f
workforce_app|t|t
workforce_backup|f|f
```

Keine der neuen Rollen ist Superuser oder darf Datenbanken anlegen.
`workforce_app` behält `SUPERUSER` — `G-025`, ausdrücklich nicht Teil dieses
Fensters.

## Manifest (Abschnitt 5)

```
DEPLOY_MANIFEST.txt: commit 83867bf654721d014617a94b1f7c317c6e606917, dirty=no, 22 Pfad(e), 151 versionierte Datei(en)

manifestiert: 151 Datei(en); fehlend, abweichend oder unerwartet: 0
RESULT: PASS   (Exit 0)
```

## Gates und Start (Abschnitt 6)

Der DB-Container wurde zuerst neu erzeugt. Der gefährliche Mount ist danach
**am Container** nachgemessen, nicht in der Datei:

```
/var/lib/postgresql/data /opt/startup/tests
```

Kein `/docker-entrypoint-initdb.d`. Damit ist `G-041` auch im laufenden System
geschlossen.

Die Gates wurden für genau einen Aufruf geöffnet, der versionierte Stand blieb
fail-closed:

```
Least-privilege roles applied; workforce_app keeps SUPERUSER until a separate step removes it.
Knowledge API grants NOT applied: gate closed (APPLY_MIGRATION_008_KNOWLEDGE_GRANTS is not true).

001_employee_registry
002_workforce_bus
003_workforce_bus_trigger_fix
005_bus_denial_audit
006_legacy_registry_tables
007_least_privilege_roles
```

Beim anschließenden `up --build workforce-api` lief der Gate-Runner erneut, mit
geschlossenen Gates aus der Datei:

```
Knowledge & Capability migration NOT applied: gate closed (APPLY_MIGRATION_004_KNOWLEDGE is not true).
Workforce Bus denial audit already applied.
Legacy registry tables already applied.
Least-privilege roles already applied.
Knowledge API grants NOT applied: gate closed (APPLY_MIGRATION_008_KNOWLEDGE_GRANTS is not true).
```

Das ist der Beleg, dass nichts zurückgesetzt werden muss: Die Datei war nie
offen.

## Zwischenfall: die API kam nicht hoch

Der erste Start von v8 lief in einen Neustart-Loop:

```
File "/app/app.py", line 51, in <module>
    API_KEY = _api_key()
PermissionError: [Errno 13] Permission denied: '/run/secrets/workforce_api_key'
```

Ursache, gemessen statt vermutet:

```
bind /volume1/docker/Startup/secrets/workforce_api_key -> /run/secrets/workforce_api_key
uid=100(app) gid=101(app) groups=101(app)
-rw------- 1 1026 100 41 Sep  1 15:28 workforce_api_key
```

Compose hängt ein `file:`-Secret als Bind-Mount der Host-Datei ein — `uid`,
`gid` und `mode` in der Langform hätten daran nichts geändert. Behoben durch
Gruppe `101` und Modus `640` auf den beiden eingehängten Dateien;
`workforce_backup_password` wird nicht eingehängt und blieb auf `600`:

```
-rw-r----- 1 1026 101 41 Sep  1 15:28 workforce_api_db_password
-rw-r----- 1 1026 101 41 Sep  1 15:28 workforce_api_key
-rw------- 1 1026 100 41 Sep  1 15:28 workforce_backup_password
```

Danach: `Up 32 seconds (healthy)`, `{"status":"ok"}`.

Als Befund `G-044` festgehalten. Die Angabe im Runbook („auf `0400`/`root` im
Fenster") hätte den Fehler nicht behoben, sondern festgeschrieben.

## Nachweise (Abschnitt 7)

**1 — Health und Version**

```
{"status":"ok"}
startup-workforce-api-1 | startup-workforce-api:v8 | Up 49 seconds (healthy)
startup-db-1 | postgres:17-alpine | Up 6 minutes (healthy)
{"api_version": "v8", "channel_status": "DISABLED", ... "project_id": "START-UP"}

 Migrationen             | 001_employee_registry, 002_workforce_bus, 003_workforce_bus_trigger_fix, 005_bus_denial_audit, 006_legacy_registry_tables, 007_least_privilege_roles
 Kanal                   | DISABLED
 aktive Credentials      | 0
 Knowledge 004           | nicht angewendet
 Ablehnungs-Audit 005    | angewendet
 Rolle workforce_api     | vorhanden
 Rolle workforce_backup  | vorhanden
```

**2 — Neustart**

```
{"status":"ok"}
Up 12 seconds (health: starting)
```

**3 — Fußabdruck des API-Containers**

```
0
sauber: 0 Treffer
```

Das Eigentümerpasswort erreicht den Container nicht (`G-035`).

**4 — Rechte-Negativtest**

Der erste Versuch war **wirkungslos** und ist Teil des Nachweises:

```
ERROR:  function workforce.bus_send_message(unknown, unknown, unknown, unknown, unknown) does not exist
```

Fünf Argumente statt dreizehn. Diese Meldung wäre auch bei wirkungslosem `007`
gekommen — der Nachweis prüfte nichts. Mit der echten Signatur:

```
ERROR:  permission denied for function bus_send_message
```

Aufräumen, in eigenen Befehlen:

```
DROP OWNED
DROP ROLE
0
```

**5 — Ablehnungs-Audit**

```
1
UNKNOWN|MESSAGE_SEND|BUS_AUTH_FAILED|401|2026-09-01 20:33:36.51631+00
```

Gegenprobe, dass dieselbe Rolle nicht lesen darf:

```
ERROR:  permission denied for table bus_denials
```

Die Probezeile bleibt stehen; `bus_denials` ist append-only.

**6 — Realer `pg_dump` als `workforce_backup`**

```
Exit: 0
Bytes: 380952
--- stderr ---
```

Kein `permission denied`, keine Zeile auf stderr.

## Endzustand

```
RESULT: PASS   (nas_status.sh, Exit 0)
Manifest       RESULT: PASS
Backup-Rechte  RESULT: PASS
Rueckfallpunkte:
  neuester Preflight-Dump: preflight-2026-09-01_22-18-42.sql
  zugehoeriger Rollen-Dump: preflight-2026-09-01_22-18-42.globals.sql
  neuestes Rollback-Image: rollback-workforce-api-v7-2026-09-01_22-18-42.tar.gz
```

## Was dieser Lauf nicht belegt

- **Keine Laufzeitkette.** Kein Telegram, kein Modellaufruf, kein Agentenlauf.
  `G-030` bleibt offen.
- **Kein Urteil über Knowledge.** `004` und `008` sind Dateien auf der NAS und
  nicht angewendet; der Lauf hat sie nicht ausgeübt (`G-015`).
- **`workforce_app` ist weiterhin `SUPERUSER`** (`G-025`). Der Rückbau ist ein
  eigener Schritt.
- **Der Rückfallpfad wurde nicht geübt.** Er war nicht nötig; dass er
  funktioniert, ist damit nicht belegt.
