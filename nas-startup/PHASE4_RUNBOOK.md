# Phase 4 — Rollout-Runbook

**Status: vorbereitet, nicht ausgeführt.** Gerds zehnter Zielcheck (`c4abc84`)
schließt `G-042` und hält das GO allein wegen `G-043` an — vier Stellen, an
denen dieses Dokument ein Verhalten unterstellte, das es nicht gibt: Schreiben
in den gehärteten Backup-Ordner, ein Auditnachweis über einen im Fenster
geschlossenen Kanal, `DROP ROLE` ohne `DROP OWNED BY`, und zwei Skripte, die
aus dem Zielmanifest gefallen waren. Alle vier sind korrigiert; es fehlt Gerds
kurzer Nachcheck. Das Anlegen von Rollen und Secrets, das Anwenden von
Migrationen und der Austausch des v7-Containers brauchen darüber hinaus eine
CEO-Freigabe für genau ein Fenster.

Dieses Dokument ist so geschrieben, dass es im Fenster von oben nach unten
abgearbeitet wird. Jeder Schritt hat einen Befehl und ein Abbruchkriterium.
Wer abbricht, springt zu Abschnitt 8.

**Container werden nicht beim Namen genannt** (`G-042`). Ein Containername ist
eine Ableitung aus Projektordner, Dienst und Index — `startup-db-1`, nicht
`startup-postgres`. Deshalb laufen alle Befehle über `docker compose exec -T
<dienst>`, und `docker inspect` holt sich sein Ziel aus `docker compose ps -q`.
Das setzt voraus, dass jeder Befehl in `/volume1/docker/Startup` startet: ohne
das Arbeitsverzeichnis findet Compose kein Projekt. `test_runbook_targets.py`
prüft beides zusammen mit den Tabellen- und Spaltennamen gegen die
Migrationen, die dieses Fenster tatsächlich anwendet.

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

**Erledigt am 2026-09-01, nach Freigabe des CEO im Chat.** Alle drei sind auf
der NAS erzeugt worden — je 40 Zeichen aus `/dev/urandom`, ausschließlich
Buchstaben und Ziffern, direkt in die Datei geschrieben. Der Wert hat weder den
Chat noch die Shell-Historie noch das Repo berührt; `secrets/` ist über
`.gitignore` ausgeschlossen, im Index steht keine Datei daraus.

Keine Sonderzeichen, und das ist kein Versehen: Das Passwort muss in
Abschnitt 4 durch ein SQL-Stringliteral. Ein `'` darin bricht den Befehl, und
Escaping ist eine Fehlerquelle, die 40 zufällige alphanumerische Zeichen
mühelos aufwiegen — Rechenaufwand statt Zeichenvorrat.

Vor dem Fenster ist die Form zu prüfen, nicht der Wert:

```
ssh synology "cd /volume1/docker/Startup && sh check_secret_files.sh"
```

Erwartet: `RESULT: PASS`, dreimal *40 Zeichen, eine Zeile, nur Buchstaben und
Ziffern*. Das Skript gibt den Wert nie aus. Es existiert, weil am 2026-09-01
der Bot-Token mit TextEdit geschrieben wurde und als RTF-Markup in der Datei
landete — 433 Byte, die in jedem Editor wie ein Token aussahen.

**Die beiden eingehängten Secrets brauchen `640` und Gruppe `101`** (`G-044`).
Compose hängt ein `file:`-Secret als **Bind-Mount der Host-Datei** ein — am
laufenden Container gemessen, nicht angenommen; `uid`, `gid` und `mode` in der
Langform könnten daran nichts ändern. Der API-Container läuft als `uid=100
gid=101`, die Dateien gehörten `TOBKUM` mit `600`, und die API ging beim ersten
Start mit `PermissionError: /run/secrets/workforce_api_key` in einen
Neustart-Loop.

Auf dem Host ist `101` die Gruppe `administrators` — dieselbe, die bereits die
Datenbank-Dumps im Backup-Ordner liest; die Freigabe geht also nicht über die
bestehende Lage hinaus. `workforce_backup_password` wird nicht eingehängt und
bleibt auf `600`.

```
ssh synology "cd /volume1/docker/Startup/secrets && \
  chgrp 101 workforce_api_key workforce_api_db_password && \
  chmod 640 workforce_api_key workforce_api_db_password && ls -ln ."
```

Hier stand vorher „auf `0400`/`root` im Fenster". Das hätte den Fehler nicht
behoben, sondern festgeschrieben: An eine root-eigene `0400`-Datei kommt ein
Container, der nicht als Root läuft, genauso wenig heran. Damit die Zahl `101`
nicht vom Zufall der Basis-Image-Vergabe abhängt, pinnt das `Dockerfile`
`uid`/`gid` inzwischen ausdrücklich.

## 3. Frische Sicherung (Abbruch bei jedem Fehler)

Unmittelbar vor dem Fenster, nicht „von gestern".

**Der Backup-Ordner ist absichtlich nur für Root beschreibbar** (`G-022`).
Nachgemessen: `drwxr-x--- root administrators`, und eine Schreibprobe als
`TOBKUM` ergibt `Permission denied`. Eine Umleitung nach
`> /volume1/docker/Startup-Backups/…` wird von der **SSH-Sitzung** ausgeführt,
nicht von Docker, und bricht deshalb ab, bevor irgendetwas gesichert ist
(`G-043`). Die Rechte werden nicht gelockert. Geschrieben wird über den
einzigen privilegierten Weg, den diese Maschine passwortlos hergibt: einen
Wegwerf-Container unter `sudo docker`, mit dem Backup-Ordner als Bind-Mount.
Als Image dient `postgres:17-alpine` — es liegt für die Datenbank ohnehin
lokal, also holt dieser Schritt nichts aus dem Netz.

Ein Zeitstempel für alle drei Dateien, damit Dump und Rollen-Dump erkennbar
zusammengehören:

```
TS=$(date +%F_%H-%M-%S) && echo "Sicherungsstempel: $TS"
```

**Datenbank-Dump.** Erst im Container erzeugen und **dort** zählen, dann
herausschreiben und die Größe vergleichen. Eine durchgehende Pipe würde den
Rückgabewert von `pg_dump` verschlucken — dieselbe Falle, die `nas_status.sh`
schon einmal `PASS` melden ließ, während eine Teilprüfung fehlschlug:

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db \
  sh -c 'pg_dump -U workforce_app workforce > /tmp/pf.sql && wc -c < /tmp/pf.sql'"
```

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db cat /tmp/pf.sql \
  | sudo /usr/local/bin/docker run --rm -i -v /volume1/docker/Startup-Backups:/backup postgres:17-alpine \
    sh -c 'cat > /backup/preflight-$TS.sql && chown 0:101 /backup/preflight-$TS.sql && chmod 640 /backup/preflight-$TS.sql'"
```

**Rollen-Dump.** Nicht optional: `pg_dump` enthält kein `CREATE ROLE`, ein
Restore ohne ihn scheitert an `role "workforce_app" does not exist` — in
diesem Projekt bereits einmal passiert (`G-024`):

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db \
  sh -c 'pg_dumpall -U workforce_app --globals-only > /tmp/pfg.sql && wc -c < /tmp/pfg.sql'"
```

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db cat /tmp/pfg.sql \
  | sudo /usr/local/bin/docker run --rm -i -v /volume1/docker/Startup-Backups:/backup postgres:17-alpine \
    sh -c 'cat > /backup/preflight-$TS.globals.sql && chown 0:101 /backup/preflight-$TS.globals.sql && chmod 640 /backup/preflight-$TS.globals.sql'"
```

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db rm -f /tmp/pf.sql /tmp/pfg.sql"
```

**Rollback-Image.** `docker save -o` schreibt aus dem CLI heraus, und das läuft
unter `sudo` als Root — dieser Befehl scheitert also nicht. Er legt die Datei
aber `600 root:root` ab und damit als einzige im Ordner unlesbar für
`TOBKUM`; nachgemessen. Deshalb dieselbe Normalisierung wie oben:

```
ssh synology "sudo /usr/local/bin/docker save startup-workforce-api:v7 \
  -o /volume1/docker/Startup-Backups/rollback-workforce-api-v7-$TS.tar.gz && \
  sudo /usr/local/bin/docker run --rm -v /volume1/docker/Startup-Backups:/backup postgres:17-alpine \
    sh -c 'chown 0:101 /backup/rollback-workforce-api-v7-$TS.tar.gz && chmod 640 /backup/rollback-workforce-api-v7-$TS.tar.gz'"
```

Danach die Sicherung *lesen*, nicht nur ihre Existenz prüfen:

```
ssh synology "ls -l /volume1/docker/Startup-Backups/preflight-$TS.sql \
  /volume1/docker/Startup-Backups/preflight-$TS.globals.sql \
  /volume1/docker/Startup-Backups/rollback-workforce-api-v7-$TS.tar.gz && \
  head -3 /volume1/docker/Startup-Backups/preflight-$TS.globals.sql"
```

Erwartet: drei Dateien, jede `-rw-r----- root administrators`, jede größer als
0 Byte, die Größe der beiden Dumps gleich der oben im Container gezählten, und
der Rollen-Dump beginnt mit dem `pg_dumpall`-Kopf. **Lesbar zu sein ist Teil
des Nachweises** — eine Sicherung, die im Rückfall niemand öffnen kann, ist
keine. Abbruch bei jeder Abweichung.

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
  sudo /usr/local/bin/docker compose cp /tmp/rollen.sql db:/tmp/rollen.sql && \
  sudo /usr/local/bin/docker compose exec -T db psql -U workforce_app -d workforce -f /tmp/rollen.sql && \
  sudo /usr/local/bin/docker compose exec -T db rm /tmp/rollen.sql && rm /tmp/rollen.sql"
```

Prüfen, dass beide existieren und **keine** davon Superuser ist:

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db psql -U workforce_app -d workforce -Atc \
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
  check_backup_permissions.sh check_secret_files.sh verify_production_state.sh nas_status.sh \
  g041_empty_volume_test.py production_state.txt
```

**Vorher die laufende `compose.yaml` sichern.** Sie wird gleich ersetzt, und
der Rückfall in Abschnitt 8 braucht die Fassung, unter der der Stack heute
läuft:

Auch hier gilt Abschnitt 3: `cp` liefe als `TOBKUM` und käme nicht in den
Ordner (`G-043`). Derselbe privilegierte Weg, derselbe Zeitstempel:

```
ssh synology "cd /volume1/docker/Startup && cat compose.yaml \
  | sudo /usr/local/bin/docker run --rm -i -v /volume1/docker/Startup-Backups:/backup postgres:17-alpine \
    sh -c 'cat > /backup/compose-v7-$TS.yaml && chown 0:101 /backup/compose-v7-$TS.yaml && chmod 640 /backup/compose-v7-$TS.yaml'"
```

```
ssh synology "ls -l /volume1/docker/Startup-Backups/compose-v7-$TS.yaml && \
  cmp -s /volume1/docker/Startup-Backups/compose-v7-$TS.yaml /volume1/docker/Startup/compose.yaml \
  && echo 'identisch' || echo 'ABWEICHUNG - Abbruch'"
```

Übertragen wird die Dateiliste, nie ein Verzeichnis (`G-020`), und über `-T`,
nie über `$(...)` — zsh trennt unquotierte Variablen nicht in Wörter (`G-033`):

```
cd nas-startup && git ls-files -- chain-test telegram-connector workforce-agent evidence \
  compose.yaml postgres-init workforce-api HANDOVER.md AGENTS.md REVIEW_GERD.md \
  REVIEW_ANTWORTEN.md NACHREVIEW_GERD_2026-09-01_C625B8C.md PHASE4_RUNBOOK.md \
  deploy_manifest.sh verify_manifest.sh backup_bundle.sh check_backup_permissions.sh \
  check_secret_files.sh verify_production_state.sh nas_status.sh g041_empty_volume_test.py \
  production_state.txt > /tmp/liste.txt && \
  echo DEPLOY_MANIFEST.txt >> /tmp/liste.txt && \
  tar czf - -T /tmp/liste.txt | ssh synology "cd /volume1/docker/Startup && tar xzf - && find . -name '._*' -delete"
```

```
ssh synology "cd /volume1/docker/Startup && sh verify_manifest.sh"
```

Abbruch bei jedem `fehlend`, `abweichend` oder `unerwartet`.

## 6. Gates öffnen und starten

**Die Gates werden nicht im versionierten Stand geöffnet** (`G-044`). Hier
stand vorher, `005`–`007` müssten in der ausgerollten `compose.yaml` auf
`"true"` stehen. Das kollidiert mit `test_review_fixes.py`, der genau diese
Gates im versionierten Stand auf `"false"` verlangt (`G-031`) — ein Commit mit
`"true"` macht den Wächter rot und muss hinterher zurückgenommen werden, also
genau die Sorte Schritt, den man vergisst. Der Kommentar in `compose.yaml`
sagt es selbst: „Flip exactly one, for exactly one window, and set it back
afterwards."

Erst prüfen, dass die Datei geschlossen ist — **alle fünf** auf `"false"`:

```
ssh synology "cd /volume1/docker/Startup && grep -n APPLY_MIGRATION compose.yaml"
```

Geöffnet wird dann für **einen einzigen Aufruf**, und `004`/`008` kommen dabei
gar nicht erst vor:

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose run --rm -T \
  -e APPLY_MIGRATION_005_BUS_DENIAL_AUDIT=true \
  -e APPLY_MIGRATION_006_LEGACY_TABLES=true \
  -e APPLY_MIGRATION_007_LEAST_PRIVILEGE=true \
  registry-migrate"
```

Erwartet: `applied.` für `005`, `006`, `007`, `NOT applied: gate closed` für
`004` und `008`. Danach der Migrationsstand:

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db \
  psql -U workforce_app -d workforce -Atc \"SELECT migration_id FROM workforce.schema_migrations ORDER BY 1\""
```

Erwartet: genau `001`–`003`, `005`, `006`, `007`. Steht `004` oder `008` dabei,
ist das ein Abbruch.

**Der DB-Container muss mit neu erzeugt werden.** `compose.yaml` entfernt den
Mount `./postgres-init:/docker-entrypoint-initdb.d` aus dem DB-Dienst
(`G-041`). Die Datei zu ersetzen ändert nichts am **laufenden** Container: der
hält seine Mounts, bis er ersetzt wird. Solange er läuft, zeigt er weiter auf
den Ordner, in den dieses Fenster gerade `004`–`008` gelegt hat.

Deshalb erst die Datenbank, dann die API:

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose up -d --force-recreate db"
```

Nachsehen, dass der Mount wirklich weg ist — nicht in der Datei, sondern im Container:

```
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker inspect \$(sudo /usr/local/bin/docker compose ps -q db) --format '{{range .Mounts}}{{.Destination}} {{end}}'"
```

Erwartet: **kein** `/docker-entrypoint-initdb.d`. Steht es noch da, ist die
Korrektur nicht wirksam und das Fenster wird abgebrochen.

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
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose restart workforce-api && sleep 10 && curl -sS localhost:8080/health"
   ```

3. **Fußabdruck des API-Containers** — das Eigentümerpasswort darf ihn nicht erreichen:
   ```
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T workforce-api env | grep -ci 'POSTGRES_PASSWORD\|startup.env' || echo 'sauber: 0 Treffer'"
   ```
   Erwartet: 0 Treffer. Jeder Treffer ist ein Abbruch (`G-035`).

4. **Rechte-Negativtest** — eine Rolle mit bloßem `USAGE` darf nichts können.
   Drei getrennte Befehle, nicht einer: Das Aufräumen muss auch dann laufen,
   wenn der Negativtest fehlschlägt, und in einer `&&`-Kette täte es das nicht.
   ```
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db psql -U workforce_app -d workforce -Atc \
     \"CREATE ROLE niemand LOGIN PASSWORD 'x'; GRANT USAGE ON SCHEMA workforce TO niemand;\""
   ```
   ```
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db psql -U niemand -d workforce -Atc \
     \"SELECT workforce.bus_send_message('x','x','x','x','x','x','x','x','x','x','x','x','x')\" 2>&1 | head -2"
   ```
   **Dreizehn Argumente, nicht fünf** (`G-044`). Hier standen fünf, und
   PostgreSQL antwortete darauf `function ... does not exist` — dieselbe
   Meldung, die auch bei wirkungslosem `007` gekommen wäre. Der Nachweis prüfte
   nichts. Ein Fehlschlag ist erst dann die erwartete Ablehnung, wenn die
   Kennung stimmt (`G-014`); die Signatur steht in
   `002_workforce_bus.sql` und lässt sich mit
   `pg_get_function_identity_arguments` nachsehen.

   Erwartet: `permission denied for function bus_send_message`. Erreicht die
   Rolle stattdessen `BUS_AUTH_FAILED`, ist `007` wirkungslos — das war genau
   der Befund `G-035`, weil PostgreSQL `EXECUTE` standardmäßig an `PUBLIC`
   vergibt.

   **Aufräumen, unabhängig vom Ergebnis.** `DROP ROLE` allein scheitert: das
   erteilte `USAGE` ist eine Abhängigkeit, und PostgreSQL antwortet mit
   `role "niemand" cannot be dropped because some objects depend on it —
   DETAIL: privileges for schema workforce`. Im Wegwerf-Container nachgemessen
   (`G-043`). Erst `DROP OWNED BY`, dann `DROP ROLE`:
   ```
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db psql -U workforce_app -d workforce -Atc \
     'DROP OWNED BY niemand; DROP ROLE niemand;'"
   ```
   ```
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db psql -U workforce_app -d workforce -Atc \
     \"SELECT count(*) FROM pg_roles WHERE rolname = 'niemand'\""
   ```
   Erwartet: `0`. Eine liegengebliebene Testrolle ist Müll im Produktivsystem
   und widerspricht der Regel, dass ein Testpaket nichts hinterlässt.

5. **Ablehnungs-Audit schreibt wirklich** (`005`). **Nicht über HTTP.** Der
   frühere Befehl konnte den Auditpfad nie erreichen (`G-043`), aus drei
   Gründen übereinander: `/bus/messages` gibt es nicht — die Route heißt
   `/bus/v1/messages` —, sie erwartet `Authorization: Bearer` statt
   `X-API-Key`, und `require_bus_ready()` läuft **vor** jeder Tokenprüfung und
   weist bei Kanal `DISABLED` mit `503 BUS_CHANNEL_NOT_ACTIVE` ab. Über
   `localhost:8080` käme zusätzlich `BUS_HTTPS_REQUIRED` zuerst. Der Kanal
   bleibt in diesem Fenster verbindlich `DISABLED`, also wird der Nachweis
   dort geführt, wo die Ablehnung tatsächlich verbucht wird:
   ```
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db psql -U workforce_api -d workforce -Atc \
     \"SELECT workforce.bus_record_denial('START-UP', repeat('0',64), 'PHASE4-AUDIT-PROBE', 'MESSAGE_SEND', 'MESSAGE', 'PROBE', 'BUS_AUTH_FAILED', 401)\""
   ```
   ```
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db psql -U workforce_app -d workforce -Atc \
     \"SELECT actor_id, operation, error_code, http_status, occurred_at FROM workforce.bus_denials WHERE request_id = 'PHASE4-AUDIT-PROBE'\""
   ```
   Erwartet: genau eine Zeile, `actor_id` = `UNKNOWN` (der erfundene
   Token-Hash löst auf nichts auf, und `bus_identify_for_audit` darf dafür
   nicht werfen), frischer Zeitstempel. **Die Zeile bleibt stehen** —
   `bus_denials` ist append-only, und eine Probe mit erkennbarer Request-Id ist
   ehrlicher als eine, die man hinterher wegräumt.

   Der Aufruf belegt zugleich den Grant aus `005`/`007`. Die Gegenprobe belegt
   dessen Enge — dieselbe Rolle darf den Datensatz **nicht lesen**:
   ```
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db psql -U workforce_api -d workforce -Atc \
     'SELECT count(*) FROM workforce.bus_denials' 2>&1 | head -2"
   ```
   Erwartet: `permission denied for table bus_denials`. Kommt hier eine Zahl,
   ist `007` zu weit.

6. **Realer `pg_dump` als `workforce_backup`** — nicht simuliert:
   ```
   ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db \
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
ssh synology "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db psql -U workforce_app -d postgres \
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
