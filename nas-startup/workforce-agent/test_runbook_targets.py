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
    known = table_columns()
    offenders = []
    for command in commands(text):
        tables = re.findall(r"FROM\s+workforce\.([a-z_]+)", command, re.IGNORECASE)
        for table in tables:
            if table not in known:
                continue
            for used in re.findall(r"\b(?:max|min|avg|sum|count)\s*\(\s*([a-z_]+)\s*\)",
                                   command, re.IGNORECASE):
                if used not in known[table]:
                    offenders.append(f"{table}.{used}")
    return offenders


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
        broken = self.text.replace("max(occurred_at)", "max(created_at)", 1)
        self.assertNotEqual(self.text, broken)
        self.assertTrue(column_offenders(broken))

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
