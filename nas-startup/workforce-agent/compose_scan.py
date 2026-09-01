"""Minimal reader for the compose files in this repository.

Not a YAML parser. It understands exactly the shapes these files use and is
deliberately narrow: per service it extracts the `env_file` list, the source
side of every `volumes:` entry, and the network names. Everything else is
ignored.

A real parser would be better, but PyYAML is not in the standard library and
the agent suite has to run without dependencies (see CLAUDE.md). The scan is
used by test_compose_secrets.py to keep a security property from eroding, so
it fails loudly on anything it cannot read rather than reporting an empty
service - a silent empty result would turn the guard into a rubber stamp.
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field


@dataclass
class Service:
    name: str
    env_files: list[str] = field(default_factory=list)
    volume_sources: list[str] = field(default_factory=list)
    # The full "source:destination:mode" spec. Where a directory is mounted is
    # a security property of its own: postgres-init under /opt/startup is a
    # file store the gate runner reads, the same folder under
    # /docker-entrypoint-initdb.d is an auto-executed script directory
    # (review finding G-041).
    volume_mounts: list[str] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)
    # Environment keys only, never values. What a container is handed is a
    # security property (review finding G-035); what the values are is not
    # this scanner's business.
    environment: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def scan(path: pathlib.Path) -> dict[str, Service]:
    """Return the services of one compose file, keyed by name."""
    services: dict[str, Service] = {}
    in_services = False
    current: Service | None = None
    current_key: str | None = None

    text = path.read_text()
    # YAML anchors and merge keys would make a service look empty here, and an
    # empty service passes every check in test_compose_secrets.py. Refuse to
    # read what this parser cannot resolve rather than reporting a service with
    # no mounts and no networks - that would turn the guard into a rubber
    # stamp, which is the exact failure mode it exists to prevent.
    for marker in ("<<:", "&", "*"):
        for number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if marker == "&" and re.search(r":\s+&\w", line):
                raise ValueError(
                    f"{path}:{number}: YAML anchor - this scanner cannot resolve "
                    "anchors; write the service out in full"
                )
            if marker == "*" and re.search(r":\s+\*\w", line):
                raise ValueError(
                    f"{path}:{number}: YAML alias - this scanner cannot resolve "
                    "aliases; write the service out in full"
                )
            if marker == "<<:" and stripped.startswith("<<:"):
                raise ValueError(
                    f"{path}:{number}: YAML merge key - this scanner cannot "
                    "resolve merges; write the service out in full"
                )

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = _indent(line)
        stripped = line.strip()

        # Top-level key: `services:`, `networks:`, `volumes:`, `secrets:`, ...
        if indent == 0:
            in_services = stripped == "services:"
            current = None
            current_key = None
            continue

        if not in_services:
            continue

        # Service name, two spaces in.
        if indent == 2 and stripped.endswith(":"):
            current = Service(name=stripped[:-1])
            services[current.name] = current
            current_key = None
            continue

        if current is None:
            continue

        # Key inside a service, four spaces in.
        if indent == 4:
            if stripped.endswith(":"):
                current_key = stripped[:-1]
            elif ":" in stripped:
                key, _, value = stripped.partition(":")
                current_key = None
                # Inline list form, e.g. `env_file: [../startup.env]`.
                value = value.strip()
                if key == "env_file" and value.startswith("["):
                    current.env_files.extend(
                        v.strip().strip("'\"")
                        for v in value[1:-1].split(",")
                        if v.strip()
                    )
            continue

        # List item or nested mapping below a service key.
        if indent >= 6 and current_key is not None:
            if current_key == "env_file" and stripped.startswith("- "):
                current.env_files.append(stripped[2:].strip().strip("'\""))
            elif current_key == "volumes" and stripped.startswith("- "):
                current.volume_sources.append(stripped[2:].split(":")[0].strip())
                current.volume_mounts.append(stripped[2:].strip())
            elif current_key == "environment":
                if stripped.startswith("- "):
                    current.environment.append(stripped[2:].split("=")[0].strip())
                elif ":" in stripped:
                    current.environment.append(stripped.split(":", 1)[0].strip())
            elif current_key == "secrets" and stripped.startswith("- "):
                current.secrets.append(stripped[2:].strip())
            elif current_key == "networks":
                if stripped.startswith("- "):
                    current.networks.append(stripped[2:].strip())
                elif indent == 6 and stripped.endswith(":"):
                    # Mapping form: `outbound:` with settings below it.
                    current.networks.append(stripped[:-1])

    if not services:
        raise ValueError(f"{path}: no services found - scan is out of step with the file")
    return services


def scan_tree(root: pathlib.Path) -> dict[pathlib.Path, dict[str, Service]]:
    """Every compose file under root, deepest name first for stable output."""
    found = sorted(root.glob("*/compose*.y*ml")) + sorted(root.glob("compose*.y*ml"))
    if not found:
        raise ValueError(f"{root}: no compose files found")
    return {p.relative_to(root): scan(p) for p in found}
