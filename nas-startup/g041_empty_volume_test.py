#!/usr/bin/env python3
"""G-041: what does a *fresh* database end up with, per gate setting?

Review finding G-041 was that ./postgres-init sat at /docker-entrypoint-initdb.d
in the db service. The postgres entrypoint auto-runs every *.sql there when the
data directory is empty, before registry-migrate exists, so the
APPLY_MIGRATION_* gates could not apply. Removing the mount is a one-line
change; proving the consequence is gone needs an actually empty database.

This builds the test stack from the real compose.yaml - the registry-migrate
command is extracted, never retyped, because a copy tests the copy (a mock
built from memory has cost this project four attempts before).

Three scenarios:

  zu       all gates false        -> exactly 001, 002, 003
  phase4   005, 006, 007 true     -> exactly 001, 002, 003, 005, 006, 007
  falle    the removed mount, back -> proves the test would have caught it

The third is the point. Without it, two green scenarios would only show that
this script cannot tell the difference.

Safety: the test database keeps its data in tmpfs and dies with the container.
Nothing here creates, names or removes a docker volume, so no cleanup command
can reach the production volume. Containers are removed by exact name
(G-038: never prune).

  python3 g041_empty_volume_test.py            # needs ssh access to the NAS
"""

import pathlib
import re
import subprocess
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parent
HOST = "synology"
DOCKER = "sudo /usr/local/bin/docker"
REMOTE = "/tmp/g041"

SCENARIOS = {
    "zu": ({}, {"001_employee_registry", "002_workforce_bus",
                "003_workforce_bus_trigger_fix"}),
    "phase4": ({"APPLY_MIGRATION_005_BUS_DENIAL_AUDIT": "true",
                "APPLY_MIGRATION_006_LEGACY_TABLES": "true",
                "APPLY_MIGRATION_007_LEAST_PRIVILEGE": "true"},
               {"001_employee_registry", "002_workforce_bus",
                "003_workforce_bus_trigger_fix", "005_bus_denial_audit",
                "006_legacy_registry_tables", "007_least_privilege_roles"}),
}

FORBIDDEN = {"004_knowledge_capability", "008_knowledge_api_grants"}


def registry_migrate_command() -> str:
    """The gate runner's script, taken from compose.yaml as it stands."""
    text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    block = re.search(
        r"^  registry-migrate:.*?^    command:\n      - \|\n(.*?)(?=^    volumes:|^  \w)",
        text, re.S | re.M)
    if not block:
        sys.exit("registry-migrate command not found in compose.yaml")
    body = block.group(1)
    # Strip the compose indentation; keep the script's own.
    lines = [line[8:] if line.startswith(" " * 8) else line
             for line in body.splitlines()]
    script = "\n".join(lines)
    # Compose escapes $ as $$ so the shell inside the container sees one.
    return script.replace("$$", "$")


def ssh(command: str, check: bool = True) -> str:
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=600", HOST, command],
        capture_output=True, text=True)
    if check and result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"remote command failed: {command[:80]}")
    return result.stdout


def run_scenario(name: str, gates: dict, script: str, with_trap: bool,
                 make_roles: bool = False) -> tuple[set, str, str]:
    """Returns (applied migrations, entrypoint log, container status).

    The trap scenario cannot be judged by querying: the entrypoint aborts on
    the first failing script, so there is no database left to ask. What it
    leaves behind is a log and an exit code, and those are the evidence.
    """
    tag = f"g041-{name}-{uuid.uuid4().hex[:8]}"
    db, net = f"{tag}-db", f"{tag}-net"

    # The trap scenario restores the removed mount so the entrypoint sees the
    # migrations again - the situation as it was before this fix.
    trap = (f"-v {REMOTE}/postgres-init:/docker-entrypoint-initdb.d:ro"
            if with_trap else "")
    env = " ".join(f"-e {k}={v}" for k, v in gates.items())

    ssh(f"{DOCKER} network create {net} >/dev/null")
    try:
        ssh(f"{DOCKER} run -d --name {db} --network {net} "
            f"--tmpfs /var/lib/postgresql/data:rw,size=512m "
            f"-e POSTGRES_USER=workforce_app -e POSTGRES_PASSWORD=testonly "
            f"-e POSTGRES_DB=workforce -e PGDATA=/var/lib/postgresql/data/pg "
            f"{trap} postgres:17-alpine >/dev/null")

        # 007 refuses without its two login roles, and refusing is correct
        # (MIGRATION_007_ROLE_MISSING). The real window creates them first, in
        # section 4 of the runbook, so the scenario has to do the same or it
        # tests a situation the rollout never enters.
        roles_sql = (
            "CREATE ROLE workforce_api LOGIN PASSWORD 'testonly'; "
            "CREATE ROLE workforce_backup LOGIN PASSWORD 'testonly';"
        ) if make_roles else ""

        ready = ssh(
            f"for i in $(seq 1 {10 if with_trap else 60}); do "
            f"  {DOCKER} exec {db} pg_isready -U workforce_app -d workforce >/dev/null 2>&1 "
            f"    && echo bereit && break; sleep 2; done", check=False)
        if "bereit" not in ready and not with_trap:
            print(ssh(f"{DOCKER} logs --tail 30 {db}", check=False))
            sys.exit(f"[{name}] Datenbank wurde nicht bereit")
        # With the trap in place the database is *supposed* to die: the
        # entrypoint aborts at 007 and the container exits. Treating that as a
        # setup failure would abort the run instead of recording the finding.

        if roles_sql:
            ssh(f"{DOCKER} exec {db} psql -U workforce_app -d workforce -c "
                f"\"{roles_sql}\" >/dev/null", check=False)

        ssh(f"{DOCKER} run --rm --network {net} "
            f"-v {REMOTE}/postgres-init:/opt/startup/migrations:ro "
            f"-v {REMOTE}/runner.sh:/runner.sh:ro "
            f"-e POSTGRES_USER=workforce_app -e POSTGRES_PASSWORD=testonly "
            f"-e POSTGRES_DB=workforce {env} -e DB_HOST={db} "
            f"--entrypoint /bin/sh postgres:17-alpine /runner.sh",
            check=False)

        rows = ssh(
            f"{DOCKER} exec {db} psql -U workforce_app -d workforce -tAc "
            f"\"SELECT migration_id FROM workforce.schema_migrations ORDER BY 1\"",
            check=False)
        log = ssh(f"{DOCKER} logs {db} 2>&1 | grep initdb.d || true", check=False)
        status = ssh(f"{DOCKER} ps -a --filter name={db} --format '{{{{.Status}}}}'",
                     check=False).strip()
        applied = {line.strip() for line in rows.splitlines() if line.strip()}
        return applied, log, status
    finally:
        ssh(f"{DOCKER} rm -f {db} >/dev/null 2>&1 || true", check=False)
        ssh(f"{DOCKER} network rm {net} >/dev/null 2>&1 || true", check=False)


def main() -> int:
    script = registry_migrate_command()

    # The runner connects to a container name, not to "db".
    script = script.replace('export PGHOST="db"', 'export PGHOST="$DB_HOST"')

    ssh(f"rm -rf {REMOTE} && mkdir -p {REMOTE}")
    subprocess.run(
        f"cd '{ROOT}' && tar czf - postgres-init | "
        f"ssh -o BatchMode=yes {HOST} 'tar xzf - -C {REMOTE}'",
        shell=True, check=True)
    # The runner goes over stdin rather than through a shell argument: it is a
    # multi-line script full of quotes and $, and every layer of escaping is a
    # place for it to arrive subtly different from what compose.yaml holds.
    subprocess.run(
        ["ssh", "-o", "BatchMode=yes", HOST,
         f"cat > {REMOTE}/runner.sh && chmod +x {REMOTE}/runner.sh"],
        input=script, text=True, check=True)

    failures = []

    for name, (gates, expected) in SCENARIOS.items():
        # phase4 creates the two login roles first, exactly as the rollout
        # window does before it opens any gate.
        applied, _, status = run_scenario(
            name, gates, script, with_trap=False, make_roles=(name == "phase4"))
        leaked = applied & FORBIDDEN
        print(f"[{name}] angewendet: {sorted(applied) or 'nichts'}")
        if applied != expected:
            failures.append(f"{name}: erwartet {sorted(expected)}, "
                            f"bekommen {sorted(applied)}")
        if leaked:
            failures.append(f"{name}: Knowledge trotz geschlossenem Gate: "
                            f"{sorted(leaked)}")
        if not status.startswith("Up"):
            failures.append(f"{name}: Datenbank laeuft nicht mehr ({status})")

    # The probe that gives the two scenarios above their meaning: put the
    # removed mount back and show that the gates stop working. Judged on the
    # entrypoint log, because this run destroys the database it would be
    # queried from - which is itself part of the finding.
    _, log, status = run_scenario("falle", {}, script, with_trap=True)
    ran = sorted(line.split("/")[-1].strip()
                 for line in log.splitlines() if "running" in line)
    print(f"[falle] initdb fuehrte aus: {ran or 'nichts'}")
    print(f"[falle] Zustand der Datenbank danach: {status or 'weg'}")

    if not any("004_knowledge" in name for name in ran):
        failures.append(
            "falle: der wiederhergestellte Mount hat 004 NICHT ausgefuehrt - "
            "dann belegt dieser Test nicht, dass er den Befund erkennen wuerde")
    if status.startswith("Up"):
        failures.append(
            "falle: die Initialisierung lief durch, obwohl 007 ohne Rollen "
            "abbrechen muss - erwartet wird ein beendeter Container")

    ssh(f"rm -rf {REMOTE}", check=False)

    print()
    if failures:
        for f in failures:
            print(f"  FAIL {f}")
        print("\nRESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
