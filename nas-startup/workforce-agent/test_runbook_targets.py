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


def runbooks() -> list[pathlib.Path]:
    """Every runbook in the folder, found rather than listed.

    The first version of this file named PHASE4_RUNBOOK.md and nothing else.
    A second runbook would then have been written, reviewed and executed
    without a single one of these checks ever looking at it - the same failure
    as a checked-documents list nobody updates, except that a runbook's lines
    get pasted into a production shell.

    Discovery has no list to forget. Both runbooks present on 2026-09-02 pass
    all checks unchanged, so no exemption was needed to make this work.
    """
    return sorted(NAS.glob("*RUNBOOK*.md"))
COMPOSE = NAS / "compose.yaml"
MIGRATIONS = NAS / "postgres-init"

PROJECT_DIR = "/volume1/docker/Startup"

# The window opens 005, 006 and 007 only. An object from 004, 008 or 009 would
# exist in the source tree and still be missing on the running database, which
# is the exact mistake the gates are there to prevent. 009 sits here since
# G-071: es hat sein eigenes Gate in compose.yaml und ist nicht angewendet.
CLOSED_GATES = ("004", "008", "009")

# Subcommands that address a container. `save`, `load`, `build` and `pull`
# address images and are none of this scan's business.
CONTAINER_SUBCOMMANDS = ("exec", "cp", "restart", "stop", "start", "kill",
                         "logs", "port", "top", "pause", "unpause", "rm")


def all_commands(text: str) -> list[str]:
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
    return joined


def commands(text: str) -> list[str]:
    """Die Teilmenge, die Container oder Datenbankobjekte adressiert.

    Der Filter ist aelter als `all_commands()` und bleibt, weil die
    Namensaufloesungen unten nur fuer diese Befehle etwas zu sagen haben. Ein
    Waechter, der jedes `sudo` prueft, darf sich darauf aber nicht stuetzen:
    dass `sudo sh /volume1/docker/Startup/backup_task.sh` bisher durch den
    Filter kam, lag allein am `docker` im Pfad.
    """
    return [c for c in all_commands(text) if "docker" in c or "workforce." in c]


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


# Flags and inline environment assignments sit between the subcommand and the
# service name: `run --rm -T -e CORE_RUN_ID=x prepare`. Both have to be
# skipped, or the assignment is read as the service.
_VORSPANN = r"(?:-\S+\s+|\S+=\S+\s+)*"

# `-f <datei>` steht **vor** dem Unterbefehl: `docker compose -f x.yaml up`.
# Das Muster ohne diesen Teil traf genau die Aufrufe nicht, um die es geht -
# jeden Aufruf einer Paketdatei.
_GLOBAL = r"(?:-f\s+\S+\s+|--env-file\s+\S+\s+|--\S+\s+)*"

SERVICE_PATTERNS = (
    rf"docker compose\s+{_GLOBAL}exec\s+{_VORSPANN}([A-Za-z0-9_][A-Za-z0-9_-]*)",
    rf"docker compose\s+{_GLOBAL}cp\s+\S+\s+([A-Za-z0-9_][A-Za-z0-9_-]*):",
    rf"docker compose\s+{_GLOBAL}(?:restart|start|stop|logs|build|kill|rm)\s+{_VORSPANN}([A-Za-z0-9_][A-Za-z0-9_-]*)",
    rf"docker compose\s+{_GLOBAL}ps\s+{_VORSPANN}([A-Za-z0-9_][A-Za-z0-9_-]*)",
    rf"docker compose\s+{_GLOBAL}up\s+{_VORSPANN}([A-Za-z0-9_][A-Za-z0-9_-]*)",
    rf"docker compose\s+{_GLOBAL}run\s+{_VORSPANN}([A-Za-z0-9_][A-Za-z0-9_-]*)",
)


def compose_file_of(command: str) -> pathlib.Path:
    """Which compose file a command addresses.

    Without `-f` that is the production compose.yaml. With `-f` it is a
    package file, resolved relative to the directory the command changes into
    - `cd /volume1/docker/Startup/workforce-agent` means the file lives in
    `workforce-agent/`.
    """
    treffer = re.search(r"-f\s+(\S+\.ya?ml)", command)
    if not treffer:
        return COMPOSE
    verzeichnis = re.search(
        r"cd\s+" + re.escape(PROJECT_DIR) + r"(/[A-Za-z0-9_.-]+)?", command)
    unter = (verzeichnis.group(1) or "").strip("/") if verzeichnis else ""
    return (NAS / unter / treffer.group(1)) if unter else (NAS / treffer.group(1))


def service_offenders(text: str) -> list[str]:
    """Every service name checked against the file the command really names.

    The first version resolved every name against the production
    compose.yaml, and had no pattern for `docker compose run` at all. So a
    package file's services were invisible twice over: wrong file, wrong
    subcommand. Four invented service names in the first draft of
    PHASE5_RUNBOOK.md passed it without a word - the same class as G-042, in
    the same kind of document.
    """
    offenders = []
    for command in commands(text):
        if "docker compose" not in command:
            continue
        datei = compose_file_of(command)
        if not datei.is_file():
            offenders.append(f"{datei.name}: Datei fehlt")
            continue
        vorhanden = set(compose_scan.scan(datei))
        for pattern in SERVICE_PATTERNS:
            for name in re.findall(pattern, command):
                if name not in vorhanden:
                    offenders.append(f"{datei.name}: {name}")
    return sorted(set(offenders))


def used_services(text: str) -> set[str]:
    """Service names a text mentions, without judging them."""
    found: set[str] = set()
    for command in commands(text):
        for pattern in SERVICE_PATTERNS:
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


def cross_reference_offenders(text: str) -> list[str]:
    """Every "Abschnitt N" has to be a section this runbook actually has.

    Klingt nach Kosmetik und ist es im Fenster nicht: Der Verweis auf den
    Rueckbau steht in dem Satz, der den Netzweg oeffnet, und wer ihn im
    Abbruchfall liest, hat es eilig. Mein erster Entwurf schickte ihn nach
    Abschnitt 9 - dem Abbruch - statt nach 8, dem Rueckbau.
    """
    ueberschriften = set(re.findall(r"^##\s+(\d+)\.", text, re.M))
    genannt = re.findall(r"Abschnitt\s+(\d+)", text)
    return sorted({n for n in genannt if n not in ueberschriften}, key=int)


# Wo die Pakete ihre Tokendateien wirklich benennen. Bewusst ohne .md: Ein
# Runbook darf hier nicht seine eigene Quelle sein.
TOKEN_QUELLEN = ("workforce-agent", "chain-test", "bus-realtest", "telegram-connector")
# Bewusst grosszuegig: Es faengt auch Shell- und SQL-Variablen wie
# `karl_token_hash` mit ein. Das schadet nicht - die Vollstaendigkeits-
# pruefung laeuft nur ueber Praefixe, die ein Runbook wirklich loescht,
# und dort stehen ausschliesslich echte Dateinamen. Das Signal ist der
# umgekehrte Fall: ein Name, den **keine** Quelle kennt.
TOKEN_MUSTER = re.compile(r"\b([a-z][a-z_]*_token(?:_[a-z]+)?)\b")


def known_tokens() -> set[str]:
    """Jeder Tokendateiname, den irgendein Paketskript oder Compose anlegt."""
    gefunden: set[str] = set()
    for paket in TOKEN_QUELLEN:
        ordner = NAS / paket
        if not ordner.is_dir():
            continue
        for datei in sorted(ordner.iterdir()):
            if datei.suffix not in (".sh", ".yaml", ".yml", ".sql", ".example"):
                continue
            gefunden.update(TOKEN_MUSTER.findall(datei.read_text(encoding="utf-8")))
    # `core_token_` ohne Namen ist der Praefix aus einer Schleife, keine Datei.
    return {n for n in gefunden if not n.endswith("_token_")}


def token_cleanup_offenders(text: str) -> list[str]:
    """Loescht das Runbook genau die Tokendateien, die es auch geben kann?

    Review finding G-068. Der Kernfenster-Rueckbau loeschte
    `core_token_connector` und `core_token_thorsten` - beide legt kein Skript
    je an - und liess `core_token_gerd` und `core_token_anastasia` liegen, die
    `prepare_core_once.sh` wirklich erzeugt. `rm -f` auf einen Namen, den es
    nie gab, meldet Erfolg; zwei gueltige Bus-Tokens blieben unbemerkt auf der
    NAS, und der Schritt las sich wie ein sauberer Abschluss.

    Drei Fragen, alle drei noetig:
      * ist jeder geloeschte Name ueberhaupt ein Tokendateiname des Projekts
      * wird zu jedem Praefix die **vollstaendige** Menge geloescht
      * steht hinter jedem Loeschen ein Abwesenheitsnachweis
    """
    bekannt = known_tokens()
    offenders: list[str] = []
    geloescht: set[str] = set()
    for command in commands(text):
        # `rm` steht seit G-072 hinter einem Anfuehrungszeichen, weil geloescht
        # wird, was ein Wegwerf-Container loeschen darf: `sh -c 'rm -f ...'`.
        # Die vorige Fassung suchte " rm -f " mit fuehrendem Leerzeichen und
        # ueberging diese Form vollstaendig - sie meldete nichts, weil sie
        # nichts ansah, und das liest sich wie ein bestandener Test.
        if not re.search(r"""(?:^|[\s'"])rm\s+-f\b""", command):
            continue
        for name in re.findall(r"secrets/([a-z_]+)", command):
            if "_token" not in name:
                continue
            geloescht.add(name)
            if name not in bekannt:
                offenders.append(f"{name}: kein Paket legt diese Datei an")
            # Der Abwesenheitsnachweis darf denselben Pfad tragen wie das
            # Loeschen - im Container `/secrets/...`, ueber SSH `secrets/...`.
            elif not re.search(rf"test ! -e \S*secrets/{name}(?![a-z_])", command):
                offenders.append(f"{name}: kein Abwesenheitsnachweis")

    # Vollstaendigkeit je Praefix - nur fuer Praefixe, die das Runbook anfasst.
    for praefix in {n.rsplit("_", 1)[0] for n in geloescht if n.count("_") >= 2}:
        erwartet = {n for n in bekannt if n.startswith(praefix + "_")}
        fehlend = sorted(erwartet - geloescht)
        if fehlend:
            offenders.append(f"{praefix}: nicht geloescht: {', '.join(fehlend)}")
    return sorted(set(offenders))


# Der einzige Befehl, den diese NAS passwortlos unter sudo zulaesst. Die Regel
# steht in /etc/sudoers.d/tobkum-docker und lautet auf genau diesen Pfad -
# nicht auf `docker`, das in einer nicht-interaktiven SSH-Sitzung ohnehin
# nicht im PATH liegt.
SUDO_ERLAUBT = "/usr/local/bin/docker"


def privileged_command_offenders(text: str) -> list[str]:
    """Jedes `sudo` im Runbook muss eines sein, das die NAS auch ausfuehrt.

    Review finding G-072. Das Runbook verlangte
    `sudo sh /volume1/docker/Startup/backup_task.sh` und zweimal `sudo rm -f`
    fuer die Tokendateien. Beides ist von der passwortlosen Regel nicht
    gedeckt: `sudo` fragt dann nach dem Passwort und scheitert in einer
    nicht-interaktiven Sitzung. Beim Backup heisst das, das Fenster beginnt
    ohne Sicherung; beim Rueckbau heisst es, gueltige Bus-Tokens bleiben auf
    der NAS liegen - derselbe Ausgang wie `G-068`, nur ueber den Fehlerpfad.

    `HANDOVER.md` haelt das seit dem Phase-4-Fenster ausdruecklich fest
    ("`sudo sh ...` geht gar nicht"). Die bisherigen Waechter prueften
    Bezeichner und Abwesenheitsnachweise - ob der privilegierte Befehl auf
    dieser Maschine ueberhaupt erlaubt ist, prueft keiner. Das ist dieselbe
    Klasse wie `G-043`: nicht ein erfundener Name, sondern erfundenes
    Verhalten.

    Gelesen wird ueber `all_commands()`, nicht ueber `commands()`. Der Filter
    dort laesst nur durch, was "docker" oder "workforce." enthaelt - dass die
    Backup-Zeile geprueft worden waere, haette allein am `docker` im Pfad
    gelegen.
    """
    offenders: set[str] = set()
    for command in all_commands(text):
        for treffer in re.finditer(r"""(?:^|[\s;&|("'])sudo\s+(\S+)""", command):
            aufruf = treffer.group(1)
            if aufruf != SUDO_ERLAUBT:
                offenders.add(f"sudo {aufruf}")
    return sorted(offenders)


def deployed_paths() -> str:
    """The versioned deploy list, as one blob to search.

    Since G-052 this is where the deployed paths live. Before that they
    existed only as arguments on a command line, which is why the check below
    used to look inside the runbook's own manifest commands - and why a
    runbook that simply calls `sh deploy_manifest.sh` with no arguments, the
    correct form today, would have failed it.
    """
    datei = NAS / "deploy_paths.txt"
    return datei.read_text(encoding="utf-8") if datei.is_file() else ""


def deployed_relative_paths(liste: str) -> set[str]:
    """Jeder Pfad, den die Liste abdeckt - NAS-relativ und einzeln aufgeloest.

    Ein Verzeichnis in `deploy_paths.txt` deckt alles darunter ab. Die erste
    Fassung suchte den Skriptnamen woertlich in der Liste und verlangte
    deshalb einen Einzeleintrag je Skript - und genau so ein Einzeleintrag
    neben seinem Ordner hat als `G-069` das Manifest dauerhaft rot gemacht.
    Die beiden Fehler bedingen einander: Der zu enge Waechter erzeugte den
    Eintrag, der das Gate brach.
    """
    pfade: set[str] = set()
    for zeile in liste.splitlines():
        eintrag = zeile.split("#", 1)[0].strip()
        if not eintrag:
            continue
        ziel = NAS / eintrag
        if ziel.is_dir():
            pfade.update(str(datei.relative_to(NAS))
                         for datei in ziel.rglob("*") if datei.is_file())
        elif ziel.is_file():
            pfade.add(eintrag)
    return pfade


def deployed_file_names(liste: str) -> set[str]:
    """Nur die Basenamen - die schwaechere Aussage, fuer Aufrufe ohne Pfad."""
    return {pfad.rsplit("/", 1)[-1] for pfad in deployed_relative_paths(liste)}


def script_target(command: str, prefix: str, name: str) -> str | None:
    """NAS-relativer Pfad des aufgerufenen Skripts, oder None.

    None heisst nicht "in Ordnung", sondern "aus diesem Befehl nicht
    bestimmbar" - dann bleibt nur der Basename. Auf dem Mac ausgefuehrte
    Befehle fallen hierunter; ihr Arbeitsverzeichnis ist das Repo, und dessen
    Wurzel entspricht der NAS-Wurzel.
    """
    if prefix.startswith(PROJECT_DIR + "/"):
        return prefix[len(PROJECT_DIR) + 1:] + name
    if prefix in ("", "./"):
        # Das letzte `cd` in den Projektbaum gewinnt, wie in der Shell auch.
        verzeichnis = None
        for treffer in re.finditer(r"cd\s+" + re.escape(PROJECT_DIR) + r"(/[A-Za-z0-9_.-]+)?",
                                   command):
            unter = treffer.group(1)
            verzeichnis = unter[1:] + "/" if unter else ""
        if verzeichnis is not None:
            return verzeichnis + name
    return None


def helper_script_offenders(text: str,
                            deploy_paths_file: str | None = None) -> list[str]:
    """Every script the runbook runs has to be one the rollout also ships.

    Review finding G-043: `check_secret_files.sh` was executed by section 2
    and missing from both path lists in section 5, so the target manifest
    would have stopped covering a file the window depends on - and an
    uncovered path is not reported as missing, it is simply out of scope.

    Gemessen wird gegen **deploy_paths.txt** und sonst nichts. Die erste
    Fassung sah in den Manifest-Befehlen des Runbooks selbst nach, weil die
    Pfadliste damals nur dort existierte; seit G-052 ist sie eine versionierte
    Datei, und gegen die zu pruefen ist die staerkere Aussage - sie sagt, was
    wirklich ausgerollt wird, statt was eine Befehlszeile behauptet.

    Verglichen wird gegen eine **Menge exakter Pfade**, nicht gegen einen
    zusammengesetzten Text (`G-073`). Die vorige Fassung haengte Pfadliste und
    Dateinamen zu einem Block zusammen und fragte `name not in block` - eine
    Teilstringpruefung, unter der ein fehlendes `status.sh` als abgedeckt galt,
    sobald irgendwo `nas_status.sh` stand. Wo der Befehl einen Pfad hergibt,
    wird der ganze Pfad gebunden: Derselbe Basename in einem anderen Paket ist
    ein anderes Skript.
    """
    liste = deploy_paths_file if deploy_paths_file is not None else deployed_paths()
    abgedeckt = deployed_relative_paths(liste)
    namen = deployed_file_names(liste)
    offenders: set[str] = set()
    for command in all_commands(text):
        # Auch pfadqualifiziert: `sh /volume1/docker/Startup/backup_task.sh`
        # ist derselbe Aufruf und braucht dieselbe Abdeckung. Ohne den
        # Pfadteil fiel genau diese Form still aus der Pruefung.
        for prefix, name in re.findall(
                r"(?:^|\s)sh\s+(\S*/)?([A-Za-z0-9_-]+\.sh)", command):
            ziel = script_target(command, prefix, name)
            if ziel is not None:
                if ziel not in abgedeckt:
                    offenders.add(ziel)
            elif name not in namen:
                offenders.add(name)
    return sorted(offenders)


def function_arity() -> dict[str, int]:
    """Parameter count per workforce function, from the migrations."""
    arity: dict[str, int] = {}
    for path in sorted(MIGRATIONS.glob("*.sql")):
        if path.name[:3] in CLOSED_GATES:
            continue
        body = path.read_text(encoding="utf-8")
        for match in re.finditer(
                r"CREATE (?:OR REPLACE )?FUNCTION workforce\.([a-z_]+)\s*\((.*?)\)\s*\n?\s*RETURNS",
                body, re.DOTALL | re.IGNORECASE):
            params = match.group(2).strip()
            arity[match.group(1)] = len(split_top_level(params)) if params else 0
    return arity


def split_top_level(argument_list: str) -> list[str]:
    """Split on commas that are not inside parentheses or quotes."""
    parts, depth, quoted, current = [], 0, False, ""
    for char in argument_list:
        if char == "'":
            quoted = not quoted
        if not quoted:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(current.strip())
                current = ""
                continue
        current += char
    if current.strip():
        parts.append(current.strip())
    return parts


def call_arity_offenders(text: str) -> list[str]:
    """Calls whose argument count does not match the function definition.

    Review finding G-044: the privilege negative test called
    `bus_send_message` with five arguments. It takes thirteen, so PostgreSQL
    answered `function ... does not exist` - the same answer it would give if
    007 had never run. The proof proved nothing, and it had looked green.
    """
    known = function_arity()
    offenders = []
    for command in commands(text):
        for name, args in re.findall(r"workforce\.([a-z_]+)\s*\((.*?)\)\s*(?:\\?\"|'|$|\s*2>)",
                                     command, re.DOTALL):
            if name not in known:
                continue
            used = len(split_top_level(args)) if args.strip() else 0
            if used != known[name]:
                offenders.append(f"{name}: {used} statt {known[name]}")
    return offenders


class RunbookTargetsTest(unittest.TestCase):
    """Every check runs against every runbook, one subTest per document."""

    def setUp(self) -> None:
        self.runbooks = [(p.name, p.read_text(encoding="utf-8")) for p in runbooks()]
        self.assertTrue(self.runbooks, "kein Runbook gefunden - Glob kaputt?")
        # The single-document form the older probes below still use.
        self.text = RUNBOOK.read_text(encoding="utf-8")

    def check_each(self, pruefung) -> None:
        for name, text in self.runbooks:
            with self.subTest(runbook=name):
                pruefung(text)

    def test_every_runbook_is_covered(self) -> None:
        # Names the documents out loud, so a glob that silently stops matching
        # shows up as a failure here instead of as a green run over nothing.
        gefunden = {name for name, _ in self.runbooks}
        self.assertIn("PHASE4_RUNBOOK.md", gefunden)
        self.assertEqual(
            gefunden,
            {p.name for p in NAS.glob("*.md") if "RUNBOOK" in p.name},
            "ein Runbook faellt aus der Abdeckung")

    def test_no_command_addresses_a_container_by_name(self) -> None:
        self.check_each(lambda t: self.assertEqual([], container_name_offenders(t)))

    def test_every_compose_command_runs_in_the_project_directory(self) -> None:
        self.check_each(lambda t: self.assertEqual([], project_directory_offenders(t)))

    def test_every_service_exists_in_the_file_the_command_names(self) -> None:
        self.assertTrue(set(compose_scan.scan(COMPOSE)),
                        "compose.yaml lieferte keine Dienste")
        self.check_each(lambda t: self.assertEqual([], service_offenders(t)))

    def test_an_invented_service_would_be_caught(self) -> None:
        erfunden = ('```bash\nssh synology "cd /volume1/docker/Startup/workforce-agent '
                    '&& sudo /usr/local/bin/docker compose -f compose.core.yaml '
                    'up --abort-on-container-exit gibt-es-nicht"\n```\n')
        self.assertEqual(["compose.core.yaml: gibt-es-nicht"],
                         service_offenders(erfunden))

    def test_a_real_service_in_a_package_file_passes(self) -> None:
        # Ohne diese Gegenprobe waere der Test darueber auch mit einer
        # Pruefung gruen, die grundsaetzlich alles ablehnt.
        echt = ('```bash\nssh synology "cd /volume1/docker/Startup/workforce-agent '
                '&& sudo /usr/local/bin/docker compose -f compose.core.yaml '
                'up --abort-on-container-exit prepare"\n```\n')
        self.assertEqual([], service_offenders(echt))

    def test_an_inline_environment_assignment_is_not_a_service(self) -> None:
        mit_env = ('```bash\nssh synology "cd /volume1/docker/Startup/workforce-agent '
                   '&& sudo /usr/local/bin/docker compose -f compose.core.yaml '
                   'run --rm -T -e CORE_RUN_ID=x prepare"\n```\n')
        self.assertEqual([], service_offenders(mit_env))

    def test_a_bare_flag_is_not_read_as_a_service(self) -> None:
        # `up --abort-on-container-exit` nennt gar keinen Dienst. Das erste
        # Muster las das Flag als Namen und meldete drei Verstoesse, die
        # keine waren - ein Waechter mit Fehlalarmen wird entschaerft.
        ohne = ('```bash\nssh synology "cd /volume1/docker/Startup/chain-test '
                '&& sudo /usr/local/bin/docker compose -f compose.chain-prepare.yaml '
                'up --abort-on-container-exit"\n```\n')
        self.assertEqual([], service_offenders(ohne))
        self.assertEqual(set(), used_services(ohne))

    def test_a_compose_file_that_does_not_exist_is_reported(self) -> None:
        fehlt = ('```bash\nssh synology "cd /volume1/docker/Startup '
                 '&& sudo /usr/local/bin/docker compose -f compose.erfunden.yaml up"\n```\n')
        self.assertEqual(["compose.erfunden.yaml: Datei fehlt"], service_offenders(fehlt))

    def test_every_schema_object_is_created_by_an_applied_migration(self) -> None:
        bekannt = schema_objects()
        self.check_each(lambda t: self.assertEqual(set(), referenced_objects(t) - bekannt))

    def test_every_column_in_a_query_exists(self) -> None:
        self.check_each(lambda t: self.assertEqual([], column_offenders(t)))

    def test_no_write_into_the_backup_folder_bypasses_docker(self) -> None:
        self.check_each(lambda t: self.assertEqual([], backup_write_offenders(t)))

    def test_every_api_path_exists(self) -> None:
        self.check_each(lambda t: self.assertEqual([], api_route_offenders(t)))

    def test_every_created_role_is_dropped_again(self) -> None:
        self.check_each(lambda t: self.assertEqual([], role_cleanup_offenders(t)))

    def test_every_privileged_command_is_one_the_nas_allows(self) -> None:
        self.check_each(lambda t: self.assertEqual([], privileged_command_offenders(t)))

    def test_every_executed_helper_script_is_in_the_target_manifest(self) -> None:
        self.check_each(lambda t: self.assertEqual([], helper_script_offenders(t)))

    def test_every_deleted_token_exists_and_is_proven_gone(self) -> None:
        self.check_each(lambda t: self.assertEqual([], token_cleanup_offenders(t)))

    def test_the_token_sources_are_actually_found(self) -> None:
        # Ohne das waere die Pruefung oben gruen ueber einer leeren Menge.
        bekannt = known_tokens()
        for name in ("core_token_karl", "core_token_gerd", "core_token_anastasia",
                     "chain_token_agent", "chain_token_connector"):
            with self.subTest(token=name):
                self.assertIn(name, bekannt)

    def test_an_invented_token_name_would_be_caught(self) -> None:
        erfunden = ('```bash\nssh synology "cd /volume1/docker/Startup/workforce-agent '
                    '&& sudo rm -f secrets/core_token_thorsten"\n```\n')
        self.assertIn("core_token_thorsten: kein Paket legt diese Datei an",
                      token_cleanup_offenders(erfunden))

    def test_an_incomplete_cleanup_would_be_caught(self) -> None:
        # Genau der Fall aus G-068: karl geloescht, gerd und anastasia nicht.
        halb = ('```bash\nssh synology "cd /volume1/docker/Startup/workforce-agent '
                '&& sudo rm -f secrets/core_token_karl '
                '&& test ! -e secrets/core_token_karl"\n```\n')
        befunde = token_cleanup_offenders(halb)
        self.assertTrue(any("nicht geloescht" in b for b in befunde), befunde)

    def test_a_deletion_without_proof_would_be_caught(self) -> None:
        ohne = ('```bash\nssh synology "cd /volume1/docker/Startup/workforce-agent '
                '&& sudo rm -f secrets/core_token_karl secrets/core_token_gerd '
                'secrets/core_token_anastasia"\n```\n')
        self.assertIn("core_token_karl: kein Abwesenheitsnachweis",
                      token_cleanup_offenders(ohne))

    def test_every_section_reference_points_somewhere(self) -> None:
        self.check_each(lambda t: self.assertEqual([], cross_reference_offenders(t)))

    def test_a_reference_to_a_missing_section_would_be_caught(self) -> None:
        erfunden = "## 1. Eins\n\nWeiter in Abschnitt 4.\n"
        self.assertEqual(["4"], cross_reference_offenders(erfunden))
        self.assertEqual([], cross_reference_offenders("## 4. Vier\n\nSiehe Abschnitt 4.\n"))

    def test_every_function_call_has_the_right_number_of_arguments(self) -> None:
        self.check_each(lambda t: self.assertEqual([], call_arity_offenders(t)))

    def test_the_deploy_list_is_actually_read(self) -> None:
        # Ohne das waere die Erweiterung oben ein Freibrief: eine leere Liste
        # deckt nichts ab, und der Test daneben wuerde es nicht merken.
        self.assertIn("nas_status.sh", deployed_paths())
        self.assertIn("check_secret_files.sh", deployed_paths())

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

    def test_the_original_five_argument_call_would_be_caught(self) -> None:
        broken = self.text.replace(
            "'x','x','x','x','x','x','x','x','x','x','x','x','x'", "'x','x','x','x','x'", 1)
        self.assertNotEqual(self.text, broken)
        self.assertIn("bus_send_message: 5 statt 13", call_arity_offenders(broken))

    def test_a_wrong_arity_on_the_audit_call_would_be_caught(self) -> None:
        # The second call in the runbook, so the check is not looking at one
        # command and calling it a day.
        broken = self.text.replace("'BUS_AUTH_FAILED', 401)", "'BUS_AUTH_FAILED')", 1)
        self.assertNotEqual(self.text, broken)
        self.assertIn("bus_record_denial: 7 statt 8", call_arity_offenders(broken))

    def test_a_script_missing_from_the_deploy_list_would_be_caught(self) -> None:
        """Die Gegenprobe wandert mit der Quelle mit.

        Sie strich frueher einen Pfad aus dem Runbook, weil die Liste dort
        stand. Seit G-052 steht sie in deploy_paths.txt, also wird jetzt dort
        gestrichen - sonst prueft die Gegenprobe eine Stelle, an der die
        Entscheidung nicht mehr faellt.
        """
        vollstaendig = deployed_paths()
        self.assertIn("check_secret_files.sh", vollstaendig)
        ohne = vollstaendig.replace("check_secret_files.sh", "")
        self.assertIn("check_secret_files.sh",
                      helper_script_offenders(self.text, deploy_paths_file=ohne))
        self.assertEqual([], helper_script_offenders(self.text,
                                                     deploy_paths_file=vollstaendig))

    def test_a_path_qualified_script_is_checked_too(self) -> None:
        pfad = ('```bash\nssh synology "sudo sh '
                '/volume1/docker/Startup/gibt_es_nicht.sh"\n```\n')
        self.assertEqual(["gibt_es_nicht.sh"], helper_script_offenders(pfad))
        echt = ('```bash\nssh synology "sudo sh '
                '/volume1/docker/Startup/backup_task.sh"\n```\n')
        self.assertEqual([], helper_script_offenders(echt))

    def test_a_script_nobody_deploys_would_be_caught(self) -> None:
        erfunden = "```bash\nssh synology \"cd /volume1/docker/Startup && sh gibt_es_nicht.sh\"\n```\n"
        self.assertNotIn("gibt_es_nicht.sh", deployed_paths())
        self.assertEqual(["gibt_es_nicht.sh"], helper_script_offenders(erfunden))

    def test_an_unauthorised_sudo_would_be_caught(self) -> None:
        """Genau die drei Formen aus `G-072`, jede fuer sich.

        Die Gegenprobe darunter ist die wichtigere Haelfte: Der erlaubte
        Aufruf muss durchgehen, sonst waere der Waechter nur eine Sperre
        gegen `sudo` und keine gegen das falsche `sudo`.
        """
        for zeile, erwartet in (
                ('ssh synology "sudo sh /volume1/docker/Startup/backup_task.sh"', "sudo sh"),
                ('ssh synology "cd /volume1/docker/Startup && sudo rm -f secrets/x"', "sudo rm"),
                ('ssh synology "sudo docker ps"', "sudo docker"),
        ):
            with self.subTest(zeile=zeile):
                self.assertEqual([erwartet],
                                 privileged_command_offenders(f"```bash\n{zeile}\n```\n"))
        erlaubt = 'ssh synology "sudo /usr/local/bin/docker compose ps"'
        self.assertEqual([], privileged_command_offenders(f"```bash\n{erlaubt}\n```\n"))

    def test_the_sudo_guard_does_not_depend_on_the_docker_filter(self) -> None:
        """Ohne `all_commands()` waere der Waechter zufaellig wirksam.

        `commands()` laesst nur durch, was "docker" oder "workforce." enthaelt.
        Ein `sudo sh` in einem Befehl ohne beides - und den gibt es, sobald
        jemand ein Skript ausserhalb von /volume1/docker aufruft - waere sonst
        unsichtbar.
        """
        ohne = 'ssh synology "sudo sh /volume1/tmp/etwas.sh"'
        block = f"```bash\n{ohne}\n```\n"
        self.assertEqual([], commands(block))
        self.assertEqual(["sudo sh"], privileged_command_offenders(block))

    def test_a_containerised_deletion_is_still_checked(self) -> None:
        """Der Tokenwaechter darf an der neuen Loeschform nicht vorbeisehen.

        Seit `G-072` steht das `rm` hinter einem Anfuehrungszeichen. Die
        vorige Fassung suchte " rm -f " mit fuehrendem Leerzeichen, uebersprang
        die Form vollstaendig und meldete nichts - ein Waechter, der nicht
        hinsieht, meldet PASS (`G-058`).
        """
        loeschen = ("sudo /usr/local/bin/docker run --rm "
                    "-v /volume1/docker/Startup/workforce-agent/secrets:/secrets "
                    "postgres:17-alpine sh -c 'rm -f /secrets/core_token_karl "
                    "/secrets/core_token_gerd /secrets/core_token_anastasia%s'")
        vorlage = "```bash\nssh synology \"" + loeschen + "\"\n```\n"
        nachweis = (" && test ! -e /secrets/core_token_karl"
                    " && test ! -e /secrets/core_token_gerd"
                    " && test ! -e /secrets/core_token_anastasia")
        self.assertEqual([], token_cleanup_offenders(vorlage % nachweis))
        ohne = nachweis.replace(" && test ! -e /secrets/core_token_gerd", "")
        self.assertEqual(["core_token_gerd: kein Abwesenheitsnachweis"],
                         token_cleanup_offenders(vorlage % ohne))

    def test_a_substring_of_a_deployed_name_is_not_coverage(self) -> None:
        """Genau der Fall aus `G-073`.

        Die vorige Fassung baute aus Pfadliste und Dateinamen einen Textblock
        und fragte `name not in block`. `status.sh` ist ein Teilstring von
        `nas_status.sh`, also galt ein Skript, das niemand ausrollt, als
        abgedeckt. Der Wert der Pruefung haengt daran, dass sie hier genau
        einen Verstoss meldet - nicht keinen und nicht zwei.
        """
        liste = "nas_status.sh\n"
        fehlend = '```bash\nssh synology "cd /volume1/docker/Startup && sh status.sh"\n```\n'
        self.assertEqual(["status.sh"],
                         helper_script_offenders(fehlend, deploy_paths_file=liste))
        echt = '```bash\nssh synology "cd /volume1/docker/Startup && sh nas_status.sh"\n```\n'
        self.assertEqual([], helper_script_offenders(echt, deploy_paths_file=liste))

    def test_the_same_basename_in_another_package_is_another_script(self) -> None:
        """Ein Basename ist kein Bezeichner, solange der Befehl einen Pfad nennt.

        `chain-test/validate_chain_run_config.sh` wird ausgerollt. Derselbe
        Name unter `telegram-connector/` waere eine andere Datei, die niemand
        ausrollt - und unter einem reinen Namensvergleich unsichtbar.
        """
        liste = "chain-test\n"
        echt = ('```bash\nssh synology "cd /volume1/docker/Startup/chain-test '
                '&& sh validate_chain_run_config.sh chain-run.env"\n```\n')
        self.assertEqual([], helper_script_offenders(echt, deploy_paths_file=liste))
        fremd = ('```bash\nssh synology "cd /volume1/docker/Startup/telegram-connector '
                 '&& sh validate_chain_run_config.sh chain-run.env"\n```\n')
        self.assertEqual(["telegram-connector/validate_chain_run_config.sh"],
                         helper_script_offenders(fremd, deploy_paths_file=liste))

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
        # Section 6 was rewritten when G-044 moved the gate out of the
        # versioned file; the invariant this scan depends on is that the two
        # stay shut, so anchor on the abort criterion rather than on prose.
        self.assertIn("Steht `004` oder `008` dabei,", text)
        self.assertIn("die beiden bleiben auf `\"false\"`", text)

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

    def test_the_signature_scan_finds_the_functions_it_needs(self) -> None:
        arity = function_arity()
        self.assertEqual(13, arity["bus_send_message"])
        self.assertEqual(8, arity["bus_record_denial"])

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
