# G-041 — Gegatete Migrationen umgingen den Gate-Runner

**Datum:** 2026-09-01
**Befund von:** Gerd (Ergänzungscheck zu den drei Phase-4-Entscheidungen)
**Status:** bestätigt, korrigiert, mit Nachweis belegt
**Einstufung des Nachweises:** direkte Beobachtung an einer echten PostgreSQL-Instanz, keine Attrappe

## Der Befund

`compose.yaml` mountete im DB-Dienst `./postgres-init` nach
`/docker-entrypoint-initdb.d`. Das offizielle Postgres-Entrypoint führt bei
**leerem Datenverzeichnis** alle `*.sql` dieses Ordners alphabetisch aus —
bevor `registry-migrate` überhaupt startet und ohne jede Kenntnis von dessen
`APPLY_MIGRATION_*`-Gates.

Solange der Ordner nur `001`–`003` enthielt, war die Wirkung unsichtbar: Ein
Volume-Reset spielte genau das nach, was ohnehin angewendet war. **Phase 4
legt `004`–`008` in denselben Ordner.** Ab diesem Moment ist die Falle scharf.

## Der Nachweis

Isolierte Instanz auf der NAS, `tmpfs` als Datenverzeichnis, kein Volume
angelegt, kein Produktivobjekt berührt. Der Ordner wurde absichtlich wie vor
der Korrektur gemountet.

```
sudo docker run -d --name g041probe \
  --tmpfs /var/lib/postgresql/data:rw,size=512m \
  -e POSTGRES_USER=workforce_app -e POSTGRES_PASSWORD=testonly \
  -e POSTGRES_DB=workforce -e PGDATA=/var/lib/postgresql/data/pg \
  -v /tmp/g041probe/postgres-init:/docker-entrypoint-initdb.d:ro \
  postgres:17-alpine
```

Auszug aus `docker logs g041probe`, unverändert:

```
running bootstrap script ... ok
docker-entrypoint.sh: running /docker-entrypoint-initdb.d/001_employee_registry.sql
docker-entrypoint.sh: running /docker-entrypoint-initdb.d/002_workforce_bus.sql
docker-entrypoint.sh: running /docker-entrypoint-initdb.d/003_workforce_bus_trigger_fix.sql
docker-entrypoint.sh: running /docker-entrypoint-initdb.d/004_knowledge_capability.sql
 MIG-004-KNOWLEDGE-CAPABILITY
docker-entrypoint.sh: running /docker-entrypoint-initdb.d/005_bus_denial_audit.sql
docker-entrypoint.sh: running /docker-entrypoint-initdb.d/006_legacy_registry_tables.sql
docker-entrypoint.sh: running /docker-entrypoint-initdb.d/007_least_privilege_roles.sql
ERROR:  MIGRATION_007_ROLE_MISSING: workforce_api. Vorher anlegen: CREATE ROLE workforce_api LOGIN PASSWORD '<aus dem Secret-Store>';
```

Zustand danach: `Exited (3)`.

**Zwei Folgen, nicht eine.** Gerd nennt die erste; die zweite kam beim
Nachmessen dazu:

1. **`004` wurde angewendet.** Der Marker `MIG-004-KNOWLEDGE-CAPABILITY` steht
   im Log. Knowledge wäre als Nebenwirkung aktiv gewesen — gegen die
   ausdrückliche Auflage des CEO, dass das nicht als Nebenwirkung des
   Core-Rollouts passieren darf.
2. **Die Initialisierung brach ab.** `007` verweigerte sich korrekt, weil die
   Rollen fehlten; das Entrypoint bricht beim ersten fehlschlagenden Skript ab
   und der Container endet mit Code 3. Eine Wiederherstellung hätte also
   Knowledge angewendet **und** eine unbrauchbare Datenbank hinterlassen.

Dass `007` sich weigert, ist kein Fehler, sondern die eingebaute
Fail-closed-Regel. Sie hat hier verhindert, dass eine stillschweigend
durchgelaufene Rechtemigration den Schaden vergrößert.

## Die Korrektur

Der Mount ist aus dem DB-Dienst entfernt. Er war reine Redundanz:
`registry-migrate` mountet denselben Ordner ohnehin unter
`/opt/startup/migrations` und legt `001`–`003` selbst an, wenn die
Markertabelle fehlt. Es geht also kein Weg zu den Migrationen verloren — nur
der, der die Gates ignoriert.

**Eine Compose-Änderung wirkt erst nach `--force-recreate`.** Der laufende
Container behält seine Mounts. Das Runbook zieht die Datenbank deshalb vor die
API und prüft anschließend am Container selbst, nicht in der Datei, dass
`/docker-entrypoint-initdb.d` verschwunden ist.

## Abgrenzung

Der laufende Produktivstand war zu keinem Zeitpunkt betroffen: Das Volume ist
nicht leer, die Entrypoint-Skripte laufen dort nicht, und `postgres-init/` auf
der NAS enthält bis heute nur `001`–`003`. Der Befund ist ein Blocker für
Phase 4 und für jede Wiederherstellung, nicht für den Betrieb.

Aufgeräumt wurde gezielt mit `docker rm -f g041probe` und `rm -rf
/tmp/g041probe`, nie mit `prune` (`G-038`).

## Empty-Volume-Test — drei Szenarien, `RESULT: PASS`

`g041_empty_volume_test.py`, Lauf vom 2026-09-01. Der Gate-Runner wird aus
`compose.yaml` extrahiert, nicht abgeschrieben.

```
[zu] angewendet: ['001_employee_registry', '002_workforce_bus', '003_workforce_bus_trigger_fix']
[phase4] angewendet: ['001_employee_registry', '002_workforce_bus', '003_workforce_bus_trigger_fix', '005_bus_denial_audit', '006_legacy_registry_tables', '007_least_privilege_roles']
[falle] initdb fuehrte aus: ['001_employee_registry.sql', '002_workforce_bus.sql', '003_workforce_bus_trigger_fix.sql', '004_knowledge_capability.sql', '005_bus_denial_audit.sql', '006_legacy_registry_tables.sql', '007_least_privilege_roles.sql']
[falle] Zustand der Datenbank danach: Exited (3) 30 seconds ago

RESULT: PASS
```

- **`zu`** — alle Gates geschlossen: genau `001`–`003`. Kein `004`, kein `008`.
- **`phase4`** — `005`, `006`, `007` offen, die beiden Login-Rollen vorher
  angelegt wie in Abschnitt 4 des Runbooks: genau `001`, `002`, `003`, `005`,
  `006`, `007`. **`004` und `008` bleiben unangewendet**, obwohl ihre Dateien
  im selben Ordner liegen — das ist die Aussage, auf die es ankommt.
- **`falle`** — der entfernte Mount wieder eingesetzt: das Entrypoint führt
  `001` bis `007` aus, `004_knowledge_capability.sql` darunter, und die
  Datenbank endet mit `Exited (3)`.

Ohne das dritte Szenario belegten die ersten beiden nur, dass dieser Test
keinen Unterschied erkennt.

## Zwei Korrekturen am Testaufbau, beide vom Lauf erzwungen

1. `phase4` erwartete `007` als angewendet und bekam es nicht. `007`
   verweigert sich ohne die Rollen — richtig, und meine Erwartung war falsch.
   Das Szenario legt sie jetzt vorher an, wie das Fenster es tut.
2. `falle` wurde per Abfrage bewertet und lieferte leer, weil dieser Lauf die
   Datenbank zerstört, die man befragen will. Bewertet werden jetzt
   Entrypoint-Log und Endzustand — der Abbruch ist Teil des Befunds, nicht ein
   Hindernis beim Messen.

## Rückstände

Keine. Nach dem Lauf: keine `g041`-Container, keine `g041`-Netze, kein
`/tmp/g041`, **0 Volumes** — der Test legt bauartbedingt keins an. Entfernt
wurde gezielt mit `docker rm -f` und `docker network rm`, nie mit `prune`
(`G-038`).
