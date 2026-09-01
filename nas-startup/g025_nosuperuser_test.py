#!/usr/bin/env python3
"""G-025: what stops working when `workforce_app` loses SUPERUSER?

Migration 007 separated the API's runtime account from the owner of
everything, but deliberately left the last step out (see its header): the
owner is still SUPERUSER, CREATEROLE, CREATEDB and BYPASSRLS. Taking that
away is not additive and locks the API out if anything below it is wrong, so
it belongs in its own window - after somebody has actually tried it.

This is that try, and it runs against **today's real backup** rather than a
synthetic schema. That has two payoffs: the rehearsal is faithful, and it
exercises the restore path, which the Phase 4 evidence had to record as
untested.

Sequence:

  A. restore today's backup                     - exercises the rollback path
  B. load the live state, run every check       - baseline, still SUPERUSER
     then ALTER ROLE ... NOSUPERUSER, run again - verdict
  C. repeat B's ALTER against a database whose bootstrap superuser IS
     workforce_app, the way production is built

A check that fails in the baseline says the rehearsal is wrong, not the
change. That distinction is the whole reason for the baseline.

**Phase C is the one that decided the matter** (review finding G-045).
Phase B demotes a workforce_app that the globals dump created next to the
bootstrap superuser `postgres`, and there the ALTER goes through. Production
is built the other way round: POSTGRES_USER=workforce_app, so workforce_app
*is* the bootstrap superuser at OID 10, and PostgreSQL refuses:

    ERROR:  permission denied to alter role
    DETAIL:  The bootstrap superuser must have the SUPERUSER attribute.

A rehearsal that only ran Phase B would have reported a green result for a
change that cannot happen.

Safety: the database lives in tmpfs and dies with the container. Nothing here
creates, names or removes a docker volume, so no cleanup command can reach the
production volume (G-038: never prune). The container is removed by exact name.
The dump never leaves the NAS.

  python3 g025_nosuperuser_test.py          # needs ssh access to the NAS
"""

from __future__ import annotations

import subprocess
import sys

HOST = "synology"
DOCKER = "sudo /usr/local/bin/docker"
NAME = "g025probe"
BACKUPS = "/volume1/docker/Startup-Backups"
IMAGE = "postgres:17-alpine"


def ssh(command: str, check: bool = True) -> str:
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=600", HOST, command],
        capture_output=True, text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"{command}\n{result.stdout}\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


def psql(user: str, sql: str, database: str = "workforce") -> str:
    escaped = sql.replace("'", "'\\''")
    return ssh(f"{DOCKER} exec {NAME} psql -U {user} -d {database} -Atc '{escaped}' 2>&1",
               check=False)


def newest_backup(pattern: str) -> str:
    # `preflight-*.sql` also matches `preflight-*.globals.sql`, which is
    # written a second later and therefore sorts first. nas_status.sh carries
    # the same exclusion for the same reason.
    found = ssh(f"ls -1t {BACKUPS}/{pattern} 2>/dev/null | grep -v globals | head -1",
                check=False)
    if not found:
        raise RuntimeError(f"keine Sicherung fuer {pattern} gefunden")
    return found


# Each check is a (label, callable) that returns a short one-line result. They
# are written so the answer is a fact, not a judgement - the comparison
# between baseline and verdict is what carries the meaning.
def checks() -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []

    dump = ssh(f"{DOCKER} exec {NAME} sh -c "
               f"'pg_dump -U workforce_app workforce > /tmp/o.sql 2>/tmp/o.err; "
               f"echo \"exit=$? bytes=$(wc -c < /tmp/o.sql)\"; head -1 /tmp/o.err'",
               check=False)
    results.append(("pg_dump als workforce_app", dump))

    globals_dump = ssh(f"{DOCKER} exec {NAME} sh -c "
                       f"'pg_dumpall -U workforce_app --globals-only > /tmp/g.sql 2>/tmp/g.err; "
                       f"echo \"exit=$? bytes=$(wc -c < /tmp/g.sql)\"; head -1 /tmp/g.err'",
                       check=False)
    results.append(("pg_dumpall --globals-only", globals_dump))

    no_pw = ssh(f"{DOCKER} exec {NAME} sh -c "
                f"'pg_dumpall -U workforce_app --globals-only --no-role-passwords "
                f"> /tmp/n.sql 2>/tmp/n.err; echo \"exit=$? bytes=$(wc -c < /tmp/n.sql)\"; "
                f"head -1 /tmp/n.err'", check=False)
    results.append(("dito, --no-role-passwords", no_pw))

    # What a future migration does, in one transaction that is rolled back:
    # DDL in its own schema, a SECURITY DEFINER function, a trigger, a grant,
    # default privileges, and the marker row the gate runner counts.
    ddl = psql("workforce_app", """
BEGIN;
SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-G025-PROBE', true);
CREATE TABLE workforce.g025_probe (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, note text);
CREATE FUNCTION workforce.g025_probe_fn() RETURNS integer LANGUAGE sql SECURITY DEFINER AS 'SELECT 1';
CREATE TRIGGER g025_probe_guard BEFORE UPDATE ON workforce.g025_probe
  FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();
GRANT EXECUTE ON FUNCTION workforce.g025_probe_fn() TO workforce_api;
ALTER DEFAULT PRIVILEGES FOR ROLE workforce_app IN SCHEMA workforce GRANT SELECT ON TABLES TO workforce_backup;
INSERT INTO workforce.schema_migrations (migration_id, description) VALUES ('999_probe', 'probe');
ROLLBACK;
SELECT 'DDL-Probe durchgelaufen';""".strip())
    results.append(("Migrations-DDL (zurueckgerollt)", ddl.replace("\n", " | ")[:160]))

    backup = ssh(f"{DOCKER} exec {NAME} sh -c "
                 f"'pg_dump -U workforce_backup workforce > /tmp/b.sql 2>/tmp/b.err; "
                 f"echo \"exit=$? bytes=$(wc -c < /tmp/b.sql)\"; head -1 /tmp/b.err'",
                 check=False)
    results.append(("pg_dump als workforce_backup", backup))

    denial = psql("workforce_api",
                  "SELECT workforce.bus_record_denial('START-UP', repeat('0',64), "
                  "'G025-PROBE', 'MESSAGE_SEND', 'MESSAGE', 'PROBE', 'BUS_AUTH_FAILED', 401)")
    results.append(("bus_record_denial als workforce_api", denial.replace("\n", " ")[:120]))

    read = psql("workforce_api", "SELECT count(*) FROM workforce.bus_denials")
    results.append(("workforce_api liest bus_denials", read.replace("\n", " ")[:120]))

    # The security argument behind G-025 is that a superuser can switch the
    # append-only triggers off. Whether NOSUPERUSER actually closes that is a
    # question with an answer, so it gets asked rather than assumed.
    off = psql("workforce_app", "ALTER TABLE workforce.bus_events DISABLE TRIGGER USER")
    if "ERROR" not in off:
        psql("workforce_app", "ALTER TABLE workforce.bus_events ENABLE TRIGGER USER")
        off = "erlaubt (Trigger wieder eingeschaltet)"
    results.append(("Audit-Trigger abschalten (workforce_app)", off.replace("\n", " ")[:120]))

    all_off = psql("workforce_app", "ALTER TABLE workforce.bus_events DISABLE TRIGGER ALL")
    if "ERROR" not in all_off:
        psql("workforce_app", "ALTER TABLE workforce.bus_events ENABLE TRIGGER ALL")
        all_off = "erlaubt (Trigger wieder eingeschaltet)"
    results.append(("dito, DISABLE TRIGGER ALL", all_off.replace("\n", " ")[:120]))

    other = psql("workforce_app", "SELECT count(*) FROM pg_authid", database="postgres")
    results.append(("pg_authid lesen", other.replace("\n", " ")[:120]))

    return results


def show(title: str, results: list[tuple[str, str]]) -> None:
    print(f"\n--- {title} ---")
    for label, value in results:
        print(f"  {label:42s} {value}")


def bootstrap_phase() -> None:
    """Phase C: the same ALTER, against production's actual role layout.

    initdb makes POSTGRES_USER the bootstrap superuser. On the NAS that is
    workforce_app, and PostgreSQL will not let the bootstrap superuser give
    up SUPERUSER - so the step migration 007 documents in its header cannot
    run there at all.
    """
    name = f"{NAME}boot"
    data = "/var/lib/postgresql/data"
    ssh(f"{DOCKER} rm -f {name} >/dev/null 2>&1 || true", check=False)
    try:
        ssh(f"{DOCKER} run -d --name {name} --tmpfs {data} --entrypoint sh {IMAGE} "
            f"-c 'sleep 900' >/dev/null")
        ssh(f"{DOCKER} exec {name} sh -c 'chown postgres:postgres {data} && "
            f"su postgres -c \"initdb -D {data} -U workforce_app --auth=trust\"' "
            f">/dev/null 2>&1", check=False)
        ssh(f"{DOCKER} exec {name} su postgres -c 'pg_ctl -D {data} -l /tmp/l start' "
            f">/dev/null 2>&1", check=False)
        ssh("sleep 3", check=False)

        def ask(sql: str) -> str:
            return ssh(f"{DOCKER} exec {name} psql -U workforce_app -d postgres -Atc "
                       f"'{sql}' 2>&1", check=False)

        print("\n--- Phase C: workforce_app ist der Bootstrap-Superuser, wie produktiv ---")
        print(f"  Ausgangslage                               {ask('SELECT oid, rolname, rolsuper FROM pg_roles WHERE rolsuper')}")
        versuch = ask("ALTER ROLE workforce_app NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS")
        print(f"  Befehl aus dem Kopf von 007                {versuch.replace(chr(10), ' | ')[:120]}")
        print(f"  Zustand danach                             {ask('SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles WHERE oid = 10')}")
        einzeln = ask("ALTER ROLE workforce_app NOCREATEROLE NOCREATEDB NOBYPASSRLS")
        print(f"  Nur die drei anderen Attribute             {einzeln.replace(chr(10), ' | ')[:80]}")
        print(f"  Zustand danach                             {ask('SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles WHERE oid = 10')}")
        print("  Ergebnis: SUPERUSER laesst sich hier nicht entziehen; die drei anderen")
        print("            Attribute schon - wirkungslos, solange SUPERUSER sie ueberschreibt.")
    finally:
        ssh(f"{DOCKER} rm -f {name} >/dev/null 2>&1 || true", check=False)


def main() -> int:
    dump = newest_backup("preflight-*.sql")
    if "globals" in dump:
        raise RuntimeError("Glob hat den Rollen-Dump erwischt")
    globals_dump = dump[: -len(".sql")] + ".globals.sql"

    print(f"Sicherung: {dump}")
    print(f"Rollen-Dump: {globals_dump}")

    ssh(f"{DOCKER} rm -f {NAME} >/dev/null 2>&1 || true", check=False)
    try:
        ssh(f"{DOCKER} run -d --name {NAME} --tmpfs /var/lib/postgresql/data "
            f"-e POSTGRES_PASSWORD=probe -e PGDATA=/var/lib/postgresql/data {IMAGE} >/dev/null")

        ready = ""
        for _ in range(30):
            ready = ssh(f"{DOCKER} exec {NAME} pg_isready -U postgres 2>&1", check=False)
            if "accepting connections" in ready:
                break
            ssh("sleep 2", check=False)
        if "accepting connections" not in ready:
            print(ssh(f"{DOCKER} logs --tail 20 {NAME}", check=False))
            raise RuntimeError("Testdatenbank wurde nicht bereit")

        # Phase A - the rollback path, exercised for the first time. Roles
        # first, then the database, then its contents: that is the order a real
        # restore needs (G-024: without the roles dump it stops at
        # `role "workforce_app" does not exist`).
        #
        # The preflight dump predates the Phase 4 window, so it carries the
        # migration set of its own era. Comparing it against today would be
        # comparing two different systems; the check is that it restores at
        # all and lands on a coherent state.
        ssh(f"cat {globals_dump} | {DOCKER} exec -i {NAME} psql -U postgres -d postgres "
            f"-v ON_ERROR_STOP=0 >/dev/null 2>&1", check=False)
        ssh(f"{DOCKER} exec {NAME} psql -U postgres -d postgres -Atc "
            f"'CREATE DATABASE wiederherstellung OWNER workforce_app' >/dev/null 2>&1",
            check=False)
        ssh(f"cat {dump} | {DOCKER} exec -i {NAME} psql -U postgres -d wiederherstellung "
            f"-v ON_ERROR_STOP=0 >/dev/null 2>&1", check=False)
        aus_sicherung = psql("postgres", "SELECT count(*) FROM workforce.schema_migrations",
                             database="wiederherstellung")
        tabellen = psql("postgres", "SELECT count(*) FROM information_schema.tables "
                        "WHERE table_schema='workforce'", database="wiederherstellung")
        print(f"\nPhase A - Rueckfallprobe aus der Sicherung:")
        print(f"  Migrationszeilen: {aus_sicherung}, Tabellen im Schema workforce: {tabellen}")
        if not aus_sicherung.strip().isdigit() or int(aus_sicherung) < 3:
            raise RuntimeError(f"Wiederherstellung unvollstaendig: {aus_sicherung}")

        # Phase B - the rehearsal itself, against the state that is running
        # right now. Streamed container to container; nothing is written to
        # the backup folder and no dump file leaves the NAS.
        # Roles first here too: pg_dump carries no CREATE ROLE, so without the
        # globals the probe would be missing workforce_api and
        # workforce_backup - and every check that uses them would report a
        # missing role instead of a missing privilege. The first run of this
        # script did exactly that.
        ssh(f"cd /volume1/docker/Startup && {DOCKER} compose exec -T db "
            f"pg_dumpall -U workforce_app --globals-only | {DOCKER} exec -i {NAME} "
            f"psql -U postgres -d postgres -v ON_ERROR_STOP=0 >/dev/null 2>&1", check=False)
        ssh(f"{DOCKER} exec {NAME} psql -U postgres -d postgres -Atc "
            f"'CREATE DATABASE workforce OWNER workforce_app' >/dev/null 2>&1", check=False)
        ssh(f"cd /volume1/docker/Startup && {DOCKER} compose exec -T db "
            f"pg_dump -U workforce_app workforce | {DOCKER} exec -i {NAME} "
            f"psql -U postgres -d workforce -v ON_ERROR_STOP=0 >/dev/null 2>&1", check=False)

        rollen = psql("postgres", "SELECT string_agg(rolname, ',' ORDER BY rolname) "
                      "FROM pg_roles WHERE rolname LIKE 'workforce%'")
        print(f"  Rollen in der Probe: {rollen}")
        for pflicht in ("workforce_api", "workforce_app", "workforce_backup"):
            if pflicht not in rollen:
                raise RuntimeError(f"{pflicht} fehlt in der Probe")

        produktiv = ssh(f"cd /volume1/docker/Startup && {DOCKER} compose exec -T db psql "
                        f"-U workforce_app -d workforce -Atc "
                        f"'SELECT count(*) FROM workforce.schema_migrations'").strip()
        restored = psql("postgres", "SELECT count(*) FROM workforce.schema_migrations")
        print(f"\nPhase B - Probe gegen den laufenden Stand:")
        print(f"  Migrationszeilen produktiv: {produktiv}, in der Probe: {restored}")
        if restored.strip() != produktiv:
            raise RuntimeError(f"Probe weicht vom Produktivstand ab: "
                               f"{restored} statt {produktiv}")

        before = psql("postgres", "SELECT rolsuper FROM pg_roles WHERE rolname='workforce_app'")
        print(f"workforce_app rolsuper vor der Umstellung: {before}")
        if before.strip() != "t":
            raise RuntimeError("Ausgangslage stimmt nicht - workforce_app ist kein Superuser")

        show("Grundlinie: workforce_app ist noch SUPERUSER", checks())

        ssh(f"{DOCKER} exec {NAME} psql -U postgres -d workforce -Atc "
            f"'ALTER ROLE workforce_app NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS' "
            f">/dev/null")
        after = psql("postgres",
                     "SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls "
                     "FROM pg_roles WHERE rolname='workforce_app'")
        print(f"\nworkforce_app nach der Umstellung (super|createrole|createdb|bypassrls): {after}")
        if after.strip() != "f|f|f|f":
            raise RuntimeError(f"Umstellung nicht wirksam: {after}")

        show("Nach ALTER ROLE ... NOSUPERUSER", checks())

        bootstrap_phase()
        return 0
    finally:
        ssh(f"{DOCKER} rm -f {NAME} >/dev/null 2>&1 || true", check=False)
        rest = ssh(f"{DOCKER} ps -a --filter name={NAME} --format '{{{{.Names}}}}'", check=False)
        print(f"\nAufgeraeumt. Reste: {rest or 'keine'}")


if __name__ == "__main__":
    sys.exit(main())
