"""Static check that the Phase 4 runbook names objects that really exist.

Review finding G-042: the runbook told the operator to run
`docker exec startup-postgres ...` and to read `workforce.bus_denial_audit`.
Neither exists. The containers are called `startup-db-1` and
`startup-workforce-api-1`, and migration 005 creates `workforce.bus_denials`
with an `occurred_at` column.

The defect class is worth a guard because nothing else could catch it. A
runbook is prose to every test in this repo, but its lines are meant to be
pasted into a production shell during a rollout window - the one moment where
a typo costs the most and there is least time to think. The consistency
scanner checks that documents do not contradict each other; it has no idea
whether a name refers to something that exists.

So this scan resolves the runbook's targets against their sources:

  * container-scoped docker subcommands must go through `docker compose`,
    because a container name is derived (project + service + index) and not
    a stable identifier
  * every compose command must run in the project directory, or compose
    resolves no project at all
  * every service name must exist in compose.yaml
  * every `workforce.<object>` must be created by a migration this window
    actually applies - 004 and 008 stay gated shut, so an object of theirs
    would pass a naive existence check and fail in the window
  * every column named in a query must exist in the table it selects from
"""

from __future__ import annotations

import pathlib
import re
import unittest

import compose_scan

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
RUNBOOK = NAS / "PHASE4_RUNBOOK.md"
COMPOSE = NAS / "compose.yaml"
MIGRATIONS = NAS / "postgres-init"

PROJECT_DIR = "/volume1/docker/Startup"

# The window opens 005, 006 and 007 only. An object from 004 or 008 would
# exist in the source tree and still be missing on the running database, which
# is the exact mistake the gates are there to prevent.
CLOSED_GATES = ("004", "008")

# Subcommands that address a container. `save`, `load`, `build` and `pull`
# address images and are none of this scan's business.
CONTAINER_SUBCOMMANDS = ("exec", "cp", "restart", "stop", "start", "kill",
                         "logs", "port", "top", "pause", "unpause", "rm")


def commands(text: str) -> list[str]:
    """Shell commands from the runbook, backslash continuations joined.

    Two decisions matter here. Only fenced blocks count - prose about a
    command is not a command, and this scan flagged its own explanation of
    `G-042` before that was true. And a command is judged as the shell sees
    it, not as the page prints it: the `cd` that makes compose work sits on
    the first line of a block whose compose call is three lines further down.
    """
    fenced: list[str] = []
    inside = False
    for raw in text.split("\n"):
        if raw.strip().startswith("```"):
            inside = not inside
            continue
        if inside:
            fenced.append(raw)

    joined: list[str] = []
    buffer: list[str] = []
    for line in fenced:
        stripped = line.strip()
        buffer.append(stripped[:-1].strip() if stripped.endswith("\\") else stripped)
        if not stripped.endswith("\\"):
            candidate = " ".join(buffer).strip()
            if candidate:
                joined.append(candidate)
            buffer = []
    if buffer:
        joined.append(" ".join(buffer).strip())
    return [c for c in joined if "docker" in c or "workforce." in c]


def container_name_offenders(text: str) -> list[str]:
    offenders = []
    for command in commands(text):
        for match in re.finditer(r"docker\s+(?!compose\b)([a-z]+)", command):
            if match.group(1) in CONTAINER_SUBCOMMANDS:
                offenders.append(command)
                break
        else:
            # `docker inspect` has no compose equivalent, so it may name a
            # container - but the name has to come from compose, not from the
            # author's memory.
            if re.search(r"docker\s+inspect\b", command) and "compose ps -q" not in command:
                offenders.append(command)
    return offenders


def project_directory_offenders(text: str) -> list[str]:
    return [c for c in commands(text)
            if "docker compose" in c and f"cd {PROJECT_DIR}" not in c]


def used_services(text: str) -> set[str]:
    patterns = (
        r"docker compose exec\s+(?:-\S+\s+)*([A-Za-z0-9_-]+)",
        r"docker compose cp\s+\S+\s+([A-Za-z0-9_-]+):",
        r"docker compose (?:restart|start|stop|logs|build|kill|rm)\s+(?:-\S+\s+)*([A-Za-z0-9_-]+)",
        r"docker compose ps\s+(?:-\S+\s+)*([A-Za-z0-9_-]+)",
        r"docker compose up\s+(?:-\S+\s+)*([A-Za-z0-9_-]+)",
    )
    found: set[str] = set()
    for command in commands(text):
        for pattern in patterns:
            found.update(re.findall(pattern, command))
    return found


def schema_objects() -> set[str]:
    """Every `workforce.<name>` created by a migration this window applies."""
    objects: set[str] = set()
    for path in sorted(MIGRATIONS.glob("*.sql")):
        if path.name[:3] in CLOSED_GATES:
            continue
        body = path.read_text(encoding="utf-8")
        objects.update(re.findall(r"CREATE\s+(?:[A-Z ]+\s+)?(?:TABLE|VIEW|FUNCTION|INDEX)"
                                  r"(?:\s+IF\s+NOT\s+EXISTS)?\s+workforce\.([a-z_]+)",
                                  body, re.IGNORECASE))
        objects.update(re.findall(r"ON\s+workforce\.([a-z_]+)", body, re.IGNORECASE))
    return objects


def table_columns() -> dict[str, set[str]]:
    columns: dict[str, set[str]] = {}
    for path in sorted(MIGRATIONS.glob("*.sql")):
        if path.name[:3] in CLOSED_GATES:
            continue
        body = path.read_text(encoding="utf-8")
        for match in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?workforce\.([a-z_]+)\s*\((.*?)\n\);",
                                 body, re.DOTALL | re.IGNORECASE):
            table, block = match.group(1), match.group(2)
            names = set()
            for line in block.split("\n"):
                head = line.strip()
                if not head or head.startswith(("CONSTRAINT", "PRIMARY", "FOREIGN",
                                                "UNIQUE", "CHECK", "--")):
                    continue
                first = head.split()[0]
                if re.fullmatch(r"[a-z_]+", first):
                    names.add(first)
            columns.setdefault(table, set()).update(names)
    return columns


def referenced_objects(text: str) -> set[str]:
    found: set[str] = set()
    for command in commands(text):
        # `/volume1/docker/git/workforce.git` is a path, not a schema.
        found.update(re.findall(r"(?<![/\w])workforce\.([a-z_]+)", command))
    return found


def column_offenders(text: str) -> list[str]:
    """Columns named against a workforce table, from three places.

    The aggregate form alone was not enough: when the audit proof stopped
    using `max(occurred_at)` the check had nothing left to look at and would
    have passed on any column name at all.
    """
    known = table_columns()
    offenders = []
    for command in commands(text):
        for select_list, table in re.findall(
                r"SELECT\s+(.*?)\s+FROM\s+workforce\.([a-z_]+)",
                command, re.IGNORECASE | re.DOTALL):
            if table not in known:
                continue
            for item in select_list.split(","):
                bare = item.strip()
                if re.fullmatch(r"[a-z_]+", bare) and bare not in known[table]:
                    offenders.append(f"{table}.{bare}")
        for table in re.findall(r"FROM\s+workforce\.([a-z_]+)", command, re.IGNORECASE):
            if table not in known:
                continue
            for used in re.findall(r"\b(?:max|min|avg|sum)\s*\(\s*([a-z_]+)\s*\)",
                                   command, re.IGNORECASE):
                if used not in known[table]:
                    offenders.append(f"{table}.{used}")
            for used in re.findall(r"WHERE\s+([a-z_]+)\s*=", command, re.IGNORECASE):
                if used not in known[table]:
                    offenders.append(f"{table}.{used}")
    return offenders


BACKUP_DIR = "/volume1/docker/Startup-Backups"


def backup_write_offenders(text: str) -> list[str]:
    """Writes into the hardened backup folder that the SSH user cannot make.

    Review finding G-043: `pg_dump ... > /volume1/docker/Startup-Backups/...`
    is executed by the remote shell as TOBKUM, and the folder is root-only
    since G-022. Docker is the one privileged writer available without a
    password, so a redirect or a `cp` into that path is always wrong and a
    `docker run -v .../Startup-Backups:/backup` or `docker save -o` is right.
    """
    target = re.escape(BACKUP_DIR)
    offenders = []
    for command in commands(text):
        # Only the shell's own writes are the problem. `docker save -o <path>`
        # is written by the CLI, which runs as root under sudo - measured -
        # and matches neither pattern, so it needs no exemption. An exemption
        # would have been a hole: it would also have hidden a second, real
        # write in the same command.
        redirect = re.search(r">>?\s*" + target, command)
        # `docker compose cp` addresses a container, not the host folder.
        copy = re.search(r"(?<!compose )\bcp\b[^;|]*?" + target, command)
        if redirect or copy:
            offenders.append(command)
    return offenders


def api_routes() -> list[str]:
    body = (NAS / "workforce-api" / "app.py").read_text(encoding="utf-8")
    return re.findall(r"@app\.(?:get|post|put|patch|delete)\(\s*[\"']([^\"']+)", body)


def api_route_offenders(text: str) -> list[str]:
    patterns = [re.compile("^" + re.sub(r"\\\{[a-z_]+\\\}", "[^/]+", re.escape(route)) + "$")
                for route in api_routes()]
    offenders = []
    for command in commands(text):
        for path in re.findall(r"localhost:8080(/[A-Za-z0-9_/{}.-]*)", command):
            if not any(pattern.match(path) for pattern in patterns):
                offenders.append(path)
    return offenders


def role_cleanup_offenders(text: str) -> list[str]:
    """A role the runbook creates has to be gone again when it is done.

    `DROP ROLE` alone fails once the role holds a privilege - measured in a
    throwaway container: `cannot be dropped because some objects depend on
    it`. So the cleanup needs DROP OWNED BY, and it needs to sit in its own
    command: in an `&&` chain a failing negative test skips it.
    """
    joined = "\n".join(commands(text))
    offenders = []
    for role in set(re.findall(r"CREATE ROLE\s+([a-z_]+)", joined)):
        if role in {"workforce_api", "workforce_backup"}:  # the window keeps these
            continue
        if f"DROP OWNED BY {role}" not in joined:
            offenders.append(f"{role}: DROP OWNED BY fehlt")
        if f"DROP ROLE {role}" not in joined:
            offenders.append(f"{role}: DROP ROLE fehlt")
    return offenders


def helper_script_offenders(text: str) -> list[str]:
    """Every script the runbook runs has to be one the rollout also ships.

    Review finding G-043: `check_secret_files.sh` was executed by section 2
    and missing from both path lists in section 5, so the target manifest
    would have stopped covering a file the window depends on - and an
    uncovered path is not reported as missing, it is simply out of scope.
    """
    executed = set()
    manifest_commands = []
    for command in commands(text):
        if "deploy_manifest.sh" in command or "git ls-files" in command:
            manifest_commands.append(command)
        executed.update(re.findall(r"(?:^|\s)sh\s+([A-Za-z0-9_-]+\.sh)", command))
    lists = " ".join(manifest_commands)
    return sorted(name for name in executed if name not in lists)


class RunbookTargetsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = RUNBOOK.read_text(encoding="utf-8")

    def test_no_command_addresses_a_container_by_name(self) -> None:
        self.assertEqual([], container_name_offenders(self.text))

    def test_every_compose_command_runs_in_the_project_directory(self) -> None:
        self.assertEqual([], project_directory_offenders(self.text))

    def test_every_service_exists_in_compose(self) -> None:
        defined = set(compose_scan.scan(COMPOSE))
        self.assertTrue(defined, "compose.yaml lieferte keine Dienste")
        self.assertEqual(set(), used_services(self.text) - defined)

    def test_every_schema_object_is_created_by_an_applied_migration(self) -> None:
        self.assertEqual(set(), referenced_objects(self.text) - schema_objects())

    def test_every_column_in_a_query_exists(self) -> None:
        self.assertEqual([], column_offenders(self.text))

    def test_no_write_into_the_backup_folder_bypasses_docker(self) -> None:
        self.assertEqual([], backup_write_offenders(self.text))

    def test_every_api_path_exists(self) -> None:
        self.assertEqual([], api_route_offenders(self.text))

    def test_every_created_role_is_dropped_again(self) -> None:
        self.assertEqual([], role_cleanup_offenders(self.text))

    def test_every_executed_helper_script_is_in_the_target_manifest(self) -> None:
        self.assertEqual([], helper_script_offenders(self.text))

    def test_an_image_reference_is_not_mistaken_for_a_container(self) -> None:
        # `docker save startup-workforce-api:v7` is correct and must stay.
        self.assertIn("docker save startup-workforce-api:v7", self.text)
        self.assertEqual([], container_name_offenders(self.text))


class WeakenedControlIsDetectedTest(unittest.TestCase):
    """Each check is shown a defect it must not miss.

    A scan that only ever sees a clean runbook cannot tell a working guard
    from a broken regex.
    """

    def setUp(self) -> None:
        self.text = RUNBOOK.read_text(encoding="utf-8")

    def test_the_original_container_name_would_be_caught(self) -> None:
        broken = self.text.replace(
            "cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db",
            "sudo /usr/local/bin/docker exec startup-postgres", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(container_name_offenders(broken))

    def test_a_bare_docker_inspect_would_be_caught(self) -> None:
        broken = self.text.replace(
            "sudo /usr/local/bin/docker inspect \\$(sudo /usr/local/bin/docker compose ps -q db)",
            "sudo /usr/local/bin/docker inspect startup-db-1", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(container_name_offenders(broken))

    def test_a_compose_command_outside_the_project_would_be_caught(self) -> None:
        broken = self.text.replace(
            "ssh synology \"cd /volume1/docker/Startup && sudo /usr/local/bin/docker compose exec -T db",
            "ssh synology \"sudo /usr/local/bin/docker compose exec -T db", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(project_directory_offenders(broken))

    def test_an_unknown_service_would_be_caught(self) -> None:
        broken = self.text.replace("docker compose exec -T db", "docker compose exec -T postgres", 1)
        defined = set(compose_scan.scan(COMPOSE))
        self.assertTrue(used_services(broken) - defined)

    def test_the_original_table_name_would_be_caught(self) -> None:
        broken = self.text.replace("workforce.bus_denials", "workforce.bus_denial_audit", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(referenced_objects(broken) - schema_objects())

    def test_the_original_column_name_would_be_caught(self) -> None:
        broken = self.text.replace("occurred_at FROM workforce.bus_denials",
                                   "created_at FROM workforce.bus_denials", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(column_offenders(broken))

    def test_a_wrong_column_in_a_where_clause_would_be_caught(self) -> None:
        broken = self.text.replace("WHERE request_id = 'PHASE4-AUDIT-PROBE'",
                                   "WHERE anfrage_id = 'PHASE4-AUDIT-PROBE'", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(column_offenders(broken))

    def test_a_redirect_into_the_backup_folder_would_be_caught(self) -> None:
        # The exact command G-043 found.
        broken = self.text.replace(
            "sh -c 'pg_dump -U workforce_app workforce > /tmp/pf.sql && wc -c < /tmp/pf.sql'",
            "pg_dump -U workforce_app workforce > /volume1/docker/Startup-Backups/preflight-x.sql", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(backup_write_offenders(broken))

    def test_a_cp_into_the_backup_folder_would_be_caught(self) -> None:
        broken = self.text.replace(
            "cat compose.yaml",
            "cp -p compose.yaml /volume1/docker/Startup-Backups/compose-v7.yaml #", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(backup_write_offenders(broken))

    def test_docker_save_into_the_backup_folder_stays_allowed(self) -> None:
        # It is written by the CLI as root. A guard that flagged it would be
        # turned off rather than obeyed.
        self.assertIn("docker save startup-workforce-api:v7", self.text)
        self.assertEqual([], backup_write_offenders(self.text))

    def test_the_original_api_path_would_be_caught(self) -> None:
        broken = self.text.replace("curl -sS localhost:8080/health",
                                   "curl -sS -X POST localhost:8080/bus/messages", 1)
        self.assertNotEqual(self.text, broken)
        self.assertIn("/bus/messages", api_route_offenders(broken))

    def test_a_bare_drop_role_would_be_caught(self) -> None:
        broken = self.text.replace("'DROP OWNED BY niemand; DROP ROLE niemand;'",
                                   "'DROP ROLE niemand'", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(role_cleanup_offenders(broken))

    def test_a_script_missing_from_the_manifest_would_be_caught(self) -> None:
        broken = self.text.replace("check_secret_files.sh verify_production_state.sh",
                                   "verify_production_state.sh")
        self.assertNotEqual(self.text, broken)
        self.assertIn("check_secret_files.sh", helper_script_offenders(broken))

    def test_a_knowledge_object_would_be_caught_although_it_exists(self) -> None:
        # The point of the gate: `knowledge_objects` is real in the tree and
        # absent from the database this window produces.
        broken = self.text.replace("workforce.bus_denials", "workforce.knowledge_objects", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(referenced_objects(broken) - schema_objects())


class ScanSourcesTest(unittest.TestCase):
    """The scan is only as good as what it reads."""

    def test_the_runbook_still_closes_the_gates_this_scan_assumes(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        self.assertIn("`004` und `008` bleiben geschlossen", text)

    def test_the_scan_actually_reads_the_runbook(self) -> None:
        # Every check above compares against an empty set when the parser
        # stops matching. `compose_scan.py` refuses files it cannot read for
        # the same reason: a guard that looks at nothing reports PASS.
        text = RUNBOOK.read_text(encoding="utf-8")
        self.assertGreater(len(commands(text)), 15)
        self.assertIn("db", used_services(text))
        self.assertIn("workforce-api", used_services(text))
        self.assertIn("bus_denials", referenced_objects(text))
        self.assertIn("CREATE ROLE niemand", "\n".join(commands(text)))
        self.assertIn("check_secret_files.sh", text)

    def test_the_route_scan_finds_the_routes_it_needs(self) -> None:
        routes = api_routes()
        self.assertIn("/health", routes)
        self.assertIn("/bus/v1/messages", routes)
        self.assertNotIn("/bus/messages", routes)

    def test_the_migration_scan_finds_the_objects_it_needs(self) -> None:
        objects = schema_objects()
        self.assertIn("bus_denials", objects)
        self.assertIn("bus_send_message", objects)
        self.assertNotIn("knowledge_objects", objects)

    def test_the_column_scan_finds_the_columns_it_needs(self) -> None:
        columns = table_columns()
        self.assertIn("occurred_at", columns["bus_denials"])
        self.assertNotIn("created_at", columns["bus_denials"])


if __name__ == "__main__":
    unittest.main()
