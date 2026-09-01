# Phase 4 — Rollout-Runbook

**Status: vorbereitet, nicht ausgeführt.** Gerds achter Zielcheck (`0a197b0`) gibt
technisches GO für *die Vorbereitung*. Das Anlegen von Rollen und Secrets, das
Anwenden von Migrationen und der Austausch des v7-Containers brauchen eine
gesonderte CEO-Freigabe für genau ein Fenster.

Dieses Dokument ist so geschrieben, dass es im Fenster von oben nach unten
abgearbeitet wird. Jeder Schritt hat einen Befehl und ein Abbruchkriterium.
Wer abbricht, springt zu Abschnitt 8.

## 1. Was sich ändert

| | vorher | nachher |
|---|---|---|
| API-Image | `startup-workforce-api:v7` | `startup-workforce-api:v8` |
| Migrationen | `001`–`003` | `001`–`003`, `005`, `006`, `007` |
| Datenbankrollen | nur `workforce_app` | zusätzlich `workforce_api`, `workforce_backup` |
| API-Zugangsdaten | `startup.env` (Eigentümerpasswort) | eigene Secret-Dateien |
| Manifestumfang | Quellordner ohne `compose.yaml`/`workforce-api` | zusätzlich `compose.yaml`, `postgres-init/`, `workforce-api/` |

Der Umfang ist gemessen, nicht geschätzt. Auf `ec8df2e` deckt das laufende
Manifest 130 Dateien und das Zielmanifest 144 Dateien. Das Fenster fasst genau elf davon an:

| geändert | neu |
|---|---|
| `compose.yaml` | `workforce-api/.dockerignore` |
| `workforce-api/app.py` | `workforce-api/e2e_acceptance.rb` |
| `workforce-api/Dockerfile` | `postgres-init/004_knowledge_capability.sql` |
| `workforce-api/test_app.py` | `postgres-init/005_bus_denial_audit.sql` |
| | `postgres-init/006_legacy_registry_tables.sql` |
| | `postgres-init/007_least_privilege_roles.sql` |
| | `postgres-init/008_knowledge_api_grants.sql` |

**`004` und `008` liegen danach als Dateien auf der NAS, sind aber nicht
angewendet.** Das ist kein Widerspruch: Angewendet wird eine Migration
ausschließlich durch ihr Gate, und die beiden bleiben auf `"false"`. Wer den
Zustand später prüft, prüft deshalb die Tabellen, nicht die Dateiliste —
`nas_status.sh` zeigt den angewendeten Migrationsstand.

**Ausdrücklich nicht Teil des Fensters:** Knowledge `004`, Knowledge-Grants
`008`, Telegram, Modellaufrufe, jeder externe Test. Der Kanal bleibt
`DISABLED`, der Kill Switch bleibt an.

## 2. Vorbedingungen (vor dem Fenster prüfbar)

```
ssh synology "cd /volume1/docker/Startup && sh nas_status.sh"
```

Erwartet: `RESULT: PASS`, API `v7`, Migrationen genau `001`–`003`, Kanal
`DISABLED`, 0 aktive Credentials, beide neuen Rollen **fehlen** noch.

Zusätzlich müssen im Fenster bereitliegen:

- `secrets/workforce_api_db_password` — neu erzeugtes Passwort, nicht das des Eigentümers
- `secrets/workforce_api_key` — neuer API-Schlüssel
- `secrets/workforce_backup_password` — Passwort der Backup-Rolle

Die ersten beiden sind in `compose.yaml` als Docker-Secrets deklariert und
werden in den Container gereicht. Die dritte ist **kein** Compose-Secret: sie
wird nur in Abschnitt 4 einmal gelesen, um die Rolle anzulegen, und danach vom
nächtlichen Sicherungsjob auf der NAS verwendet.

Alle drei werden **vom CEO abgelegt**, nicht von einem Assistenten erzeugt und nie
im Chat genannt. Rechte `0400`, Eigentümer `root`.

## 3. Frische Sicherung (Abbruch bei jedem Fehler)

Unmittelbar vor dem Fenster, nicht „von gestern":

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker exec startup-postgres \
  pg_dump -U workforce_app workforce > /volume1/docker/Startup-Backups/preflight-$(date +%F_%H-%M-%S).sql"
```

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker exec startup-postgres \
  pg_dumpall -U workforce_app --globals-only > /volume1/docker/Startup-Backups/preflight-$(date +%F_%H-%M-%S).globals.sql"
```

```
ssh synology "sudo /usr/local/bin/docker save startup-workforce-api:v7 \
  -o /volume1/docker/Startup-Backups/rollback-workforce-api-v7-$(date +%F_%H-%M-%S).tar.gz"
```

**Der Rollen-Dump ist nicht optional.** `pg_dump` enthält kein `CREATE ROLE`;
ein Restore ohne ihn scheitert an `role "workforce_app" does not exist` — das
ist in diesem Projekt bereits einmal passiert (`G-024`).

Danach die Sicherung *lesen*, nicht nur ihre Existenz prüfen:

```
ssh synology "ls -l /volume1/docker/Startup-Backups/ | tail -4 && \
  head -3 /volume1/docker/Startup-Backups/preflight-*.globals.sql | head -5"
```

Abbruch, wenn eine Datei 0 Byte hat oder der Dump eine Fehlermeldung enthält.

## 4. Rollen anlegen

Passwörter kommen aus den Secret-Dateien, nie aus der Kommandozeile und nie
aus einem Heredoc mit `$` darin — eine `$`-Ersetzung hat hier schon einmal die
Prozess-ID als Passwort gesetzt. Deshalb: SQL in eine Datei schreiben, Datei
ausführen.

```
ssh synology "cd /volume1/docker/Startup && \
  printf 'CREATE ROLE workforce_api LOGIN PASSWORD %s;\n' \
    \"\$(sed -e \"s/'/''/g\" -e \"s/^/'/\" -e \"s/\$/'/\" secrets/workforce_api_db_password)\" \
    > /tmp/rollen.sql && \
  printf 'CREATE ROLE workforce_backup LOGIN PASSWORD %s;\n' \
    \"\$(sed -e \"s/'/''/g\" -e \"s/^/'/\" -e \"s/\$/'/\" secrets/workforce_backup_password)\" \
    >> /tmp/rollen.sql && \
  sudo /usr/local/bin/docker cp /tmp/rollen.sql startup-postgres:/tmp/rollen.sql && \
  sudo /usr/local/bin/docker exec startup-postgres psql -U workforce_app -d workforce -f /tmp/rollen.sql && \
  sudo /usr/local/bin/docker exec startup-postgres rm /tmp/rollen.sql && rm /tmp/rollen.sql"
```

Prüfen, dass beide existieren und **keine** davon Superuser ist:

```
ssh synology "sudo /usr/local/bin/docker exec startup-postgres psql -U workforce_app -d workforce -Atc \
  \"SELECT rolname, rolsuper, rolcreatedb FROM pg_roles WHERE rolname LIKE 'workforce%' ORDER BY 1\""
```

Abbruch, wenn `workforce_api` oder `workforce_backup` `t` bei `rolsuper` zeigt.

## 5. Zielmanifest erzeugen und ausrollen

Auf dem Mac, mit sauberem Baum:

```
cd nas-startup && MANIFEST_OUT=DEPLOY_MANIFEST.txt sh deploy_manifest.sh \
  chain-test telegram-connector workforce-agent evidence compose.yaml postgres-init workforce-api \
  HANDOVER.md AGENTS.md REVIEW_GERD.md REVIEW_ANTWORTEN.md NACHREVIEW_GERD_2026-09-01_C625B8C.md \
  PHASE4_RUNBOOK.md deploy_manifest.sh verify_manifest.sh backup_bundle.sh \
  check_backup_permissions.sh verify_production_state.sh nas_status.sh production_state.txt
```

Übertragen wird die Dateiliste, nie ein Verzeichnis (`G-020`), und über `-T`,
nie über `$(...)` — zsh trennt unquotierte Variablen nicht in Wörter (`G-033`):

```
cd nas-startup && git ls-files -- chain-test telegram-connector workforce-agent evidence \
  compose.yaml postgres-init workforce-api HANDOVER.md AGENTS.md REVIEW_GERD.md \
  REVIEW_ANTWORTEN.md NACHREVIEW_GERD_2026-09-01_C625B8C.md PHASE4_RUNBOOK.md \
  deploy_manifest.sh verify_manifest.sh backup_bundle.sh check_backup_permissions.sh \
  verify_production_state.sh nas_status.sh production_state.txt > /tmp/liste.txt && \
  echo DEPLOY_MANIFEST.txt >> /tmp/liste.txt && \
  tar czf - -T /tmp/liste.txt | ssh synology "cd /volume1/docker/Startup && tar xzf - && find . -name '._*' -delete"
```

```
ssh synology "cd /volume1/docker/Startup && sh verify_manifest.sh"
```

Abbruch bei jedem `fehlend`, `abweichend` oder `unerwartet`.

## 6. Gates öffnen und starten

Genau drei Gates gehen auf. `004` und `008` bleiben geschlossen — das ist die
Zeile, an der ein Flüchtigkeitsfehler Knowledge ungewollt aktivieren würde:

```
ssh synology "cd /volume1/docker/Startup && grep -n APPLY_MIGRATION compose.yaml"
```

Erwartet: `004` und `008` auf `"false"`, `005`, `006`, `007` auf `"true"`.
Stimmt das nicht, wird die Datei korrigiert und Abschnitt 5 wiederholt — nicht
auf der NAS editiert (Regel 1).

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose up -d --build workforce-api"
```

## 7. Nachweise (alle sechs, sonst Rückfall)

1. **Health und Version**
   ```
   ssh synology "curl -sS localhost:8080/health && echo && cd /volume1/docker/Startup && sh nas_status.sh"
   ```
   Erwartet `v8`, Migrationen `001`–`003`,`005`,`006`,`007`, Kanal `DISABLED`.

2. **Neustart übersteht den Zustand**
   ```
   ssh synology "sudo /usr/local/bin/docker restart startup-workforce-api && sleep 10 && curl -sS localhost:8080/health"
   ```

3. **Fußabdruck des API-Containers** — das Eigentümerpasswort darf ihn nicht erreichen:
   ```
   ssh synology "sudo /usr/local/bin/docker exec startup-workforce-api env | grep -ci 'POSTGRES_PASSWORD\|startup.env' || echo 'sauber: 0 Treffer'"
   ```
   Erwartet: 0 Treffer. Jeder Treffer ist ein Abbruch (`G-035`).

4. **Rechte-Negativtest** — eine Rolle mit bloßem `USAGE` darf nichts können:
   ```
   ssh synology "sudo /usr/local/bin/docker exec startup-postgres psql -U workforce_app -d workforce -Atc \
     \"CREATE ROLE niemand LOGIN PASSWORD 'x'; GRANT USAGE ON SCHEMA workforce TO niemand;\" && \
     sudo /usr/local/bin/docker exec startup-postgres psql -U niemand -d workforce -Atc \
     \"SELECT workforce.bus_send_message('x','x','x','x','x')\" 2>&1 | head -2; \
     sudo /usr/local/bin/docker exec startup-postgres psql -U workforce_app -d workforce -Atc 'DROP ROLE niemand'"
   ```
   Erwartet: `permission denied for function`. Erreicht die Rolle stattdessen
   `BUS_AUTH_FAILED`, ist `007` wirkungslos — das war genau der Befund `G-035`,
   weil PostgreSQL `EXECUTE` standardmäßig an `PUBLIC` vergibt.

5. **Ablehnungs-Audit schreibt wirklich** (`005`):
   ```
   ssh synology "curl -sS -X POST localhost:8080/bus/messages -H 'X-API-Key: falsch' -d '{}' >/dev/null; \
     sudo /usr/local/bin/docker exec startup-postgres psql -U workforce_app -d workforce -Atc \
     'SELECT count(*), max(created_at) FROM workforce.bus_denial_audit'"
   ```
   Erwartet: Zähler > 0 mit frischem Zeitstempel.

6. **Realer `pg_dump` als `workforce_backup`** — nicht simuliert:
   ```
   ssh synology "sudo /usr/local/bin/docker exec startup-postgres \
     pg_dump -U workforce_backup workforce > /tmp/backup_probe.sql; echo \"Exit: \$?\"; \
     wc -c < /tmp/backup_probe.sql; rm -f /tmp/backup_probe.sql"
   ```
   Erwartet: Exit 0, Größe > 300 KB, keine `permission denied`-Zeile. Der Lauf
   ist beim ersten Versuch an `permission denied for sequence` gescheitert;
   `007` vergibt die Sequenzrechte deshalb ausdrücklich mit.

## 8. Rückfall

Auslöser: jedes Abbruchkriterium oben. Reihenfolge:

```
ssh synology "sudo /usr/local/bin/docker load -i /volume1/docker/Startup-Backups/rollback-workforce-api-v7-<Zeitstempel>.tar.gz"
```

```
ssh synology "cd /volume1/docker/Startup && git -C /volume1/docker/git/workforce.git log --oneline -1"
```

Produktivdateien auf den vorherigen Commit zurückspielen (Abschnitt 5 mit dem
alten Commit), dann Container mit v7 starten. Nur wenn die Datenbank
tatsächlich beschädigt ist:

```
ssh synology "sudo /usr/local/bin/docker exec -i startup-postgres psql -U workforce_app -d postgres \
  -f - < /volume1/docker/Startup-Backups/preflight-<Zeitstempel>.globals.sql"
```

**Erst der Rollen-Dump, dann der Datenbank-Dump.** Umgekehrt scheitert er.

Nach jedem Rückfall: `nas_status.sh` muss wieder `RESULT: PASS` mit `v7` und
Migrationen `001`–`003` zeigen, sonst ist das Fenster nicht sauber geschlossen.

## 9. Nach dem Fenster

- Evidenzdatei unter `evidence/` mit allen sechs Nachweisen im Rohtext
- `production_state.txt` auf den neuen Commit setzen
- `HANDOVER.md` fortschreiben
- Offen bleibt danach: `workforce_app` verliert `SUPERUSER` (eigener Schritt,
  nicht in diesem Fenster), `G-030` Laufzeitkette, `G-040` `/openapi.json`
