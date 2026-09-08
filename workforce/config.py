"""One configuration file, validated at start. Missing means refuse, never guess.

Everything the process needs to decide is in one JSON file: identities, routes,
policies, budgets, paths. Secrets are *not* in it - they live as files in
`secrets_dir` and are read by `read_secret()`, which checks mode and form.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import pathlib
import stat
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from urllib.parse import urlsplit

POLICIES = ("METADATA_ONLY", "BODY", "FULL")
PROVIDERS = ("echo", "ollama", "claude")
HUMAN = "CEO"  # the one human identity: the allowed Telegram chat


class ConfigError(ValueError):
    """Stable identifier, never free text."""


@dataclass(frozen=True)
class Identity:
    name: str
    provider: str
    model: str
    policy: str
    system_prompt: str


@dataclass(frozen=True)
class ScheduleItem:
    """A message the core sends itself, weekly (Phase 3 - the system speaks up). `weekday`
    is ISO (1 Monday .. 7 Sunday), `hour` is UTC - the same UTC the rest of the core already
    uses for `today()` and the budget day, so no second time source is introduced."""
    id: str
    weekday: int
    hour: int
    identity: str
    prompt: str


@dataclass(frozen=True)
class Config:
    db_path: str
    secrets_dir: str
    allowed_chat_id: int
    default_identity: str
    identities: Dict[str, Identity]
    routes: Tuple[Tuple[str, str], ...]
    max_calls_per_day: int
    max_usd_per_day: float
    ollama_url: str
    poll_timeout_seconds: int
    lease_seconds: int
    max_attempts: int
    telegram_base_url: str
    anthropic_workspace_id: str = ""
    schedule: Tuple[ScheduleItem, ...] = ()
    digest: str = ""  # sha256 of the file as loaded (G-107); "" when parsed from a dict

    def route_allowed(self, sender: str, recipient: str) -> bool:
        return (sender, recipient) in self.routes


def _require(values: Dict[str, Any], key: str, kind: type) -> Any:
    if key not in values:
        raise ConfigError(f"CONFIG_MISSING:{key}")
    value = values[key]
    if kind is float and isinstance(value, int) and not isinstance(value, bool):
        value = float(value)
    if not isinstance(value, kind) or isinstance(value, bool) and kind is not bool:
        raise ConfigError(f"CONFIG_TYPE:{key}")
    return value


def read_prompt_file(path: str) -> str:
    """A SKILL.md doubles as the system prompt: the YAML front matter is for Claude Code, the
    body is the role. One file, two readers - the text cannot drift between them."""
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"CONFIG_PROMPT_FILE_MISSING:{path}") from exc
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end == -1:
            raise ConfigError(f"CONFIG_PROMPT_FILE_FRONTMATTER:{path}")
        text = text[end + 5:]
    body = text.strip()
    if not body:
        raise ConfigError(f"CONFIG_PROMPT_FILE_EMPTY:{path}")
    return body


def parse(values: Dict[str, Any], *, base_dir: str = ".") -> Config:
    identities: Dict[str, Identity] = {}
    raw_identities = _require(values, "identities", dict)
    if not raw_identities:
        raise ConfigError("CONFIG_NO_IDENTITIES")
    for name, raw in raw_identities.items():
        if not isinstance(raw, dict):
            raise ConfigError(f"CONFIG_TYPE:identities.{name}")
        provider = _require(raw, "provider", str)
        policy = _require(raw, "policy", str)
        if provider not in PROVIDERS:
            raise ConfigError(f"CONFIG_PROVIDER_UNKNOWN:{provider}")
        if policy not in POLICIES:
            raise ConfigError(f"CONFIG_POLICY_UNKNOWN:{policy}")
        if name == HUMAN:
            raise ConfigError("CONFIG_IDENTITY_RESERVED:CEO")
        if ("system_prompt" in raw) == ("system_prompt_file" in raw):
            raise ConfigError(f"CONFIG_PROMPT_ONE_OF:{name}")
        if "system_prompt_file" in raw:
            file_path = os.path.join(base_dir, _require(raw, "system_prompt_file", str))
            prompt = read_prompt_file(file_path)
        else:
            prompt = _require(raw, "system_prompt", str)
        identities[name] = Identity(
            name=name, provider=provider, model=_require(raw, "model", str),
            policy=policy, system_prompt=prompt)

    default = _require(values, "default_identity", str)
    if default not in identities:
        raise ConfigError(f"CONFIG_DEFAULT_IDENTITY_UNKNOWN:{default}")

    routes = []
    for pair in _require(values, "routes", list):
        if not (isinstance(pair, list) and len(pair) == 2 and all(isinstance(p, str) for p in pair)):
            raise ConfigError("CONFIG_ROUTE_FORM")
        for end in pair:
            if end != HUMAN and end not in identities:
                raise ConfigError(f"CONFIG_ROUTE_UNKNOWN_IDENTITY:{end}")
        if pair[0] == pair[1]:
            raise ConfigError("CONFIG_ROUTE_SELF")
        routes.append((pair[0], pair[1]))

    schedule = _parse_schedule(values.get("schedule", []), identities=identities, routes=routes)

    poll = int(values.get("poll_timeout_seconds", 25))
    if not 1 <= poll <= 50:
        raise ConfigError("CONFIG_POLL_TIMEOUT_RANGE")
    lease = _bounded_int(values, "lease_seconds", default=300, minimum=1, maximum=3600)
    attempts = _bounded_int(values, "max_attempts", default=3, minimum=1, maximum=10)
    calls = _bounded_int(values, "max_calls_per_day", minimum=1, maximum=10_000)
    max_usd = _require(values, "max_usd_per_day", float)
    if max_usd < 0:
        raise ConfigError("CONFIG_BUDGET_NEGATIVE")
    base = str(values.get("telegram_base_url", "https://api.telegram.org"))
    if not _exact_base_url(base, scheme="https", hosts=("api.telegram.org",)):
        raise ConfigError("CONFIG_TELEGRAM_NOT_HTTPS")
    ollama = str(values.get("ollama_url", "http://127.0.0.1:11434"))
    if not _exact_base_url(
        ollama,
        scheme="http",
        hosts=("127.0.0.1", "localhost", "::1", "host.docker.internal"),
    ):
        raise ConfigError("CONFIG_OLLAMA_NOT_LOCAL")

    return Config(
        db_path=_require(values, "db_path", str),
        secrets_dir=_require(values, "secrets_dir", str),
        allowed_chat_id=_require(values, "allowed_chat_id", int),
        default_identity=default,
        identities=identities,
        routes=tuple(routes),
        max_calls_per_day=calls,
        max_usd_per_day=max_usd,
        ollama_url=ollama,
        poll_timeout_seconds=poll,
        lease_seconds=lease,
        max_attempts=attempts,
        telegram_base_url=base,
        anthropic_workspace_id=str(values.get("anthropic_workspace_id", "")).strip(),
        schedule=schedule,
    )


def _parse_schedule(raw: Any, *, identities: Dict[str, "Identity"],
                    routes: List[Tuple[str, str]]) -> Tuple["ScheduleItem", ...]:
    if not isinstance(raw, list):
        raise ConfigError("CONFIG_SCHEDULE_FORM")
    items = []
    seen_ids = set()
    for entry in raw:
        if not isinstance(entry, dict):
            raise ConfigError("CONFIG_SCHEDULE_FORM")
        item_id = _require(entry, "id", str)
        if not item_id:
            raise ConfigError("CONFIG_SCHEDULE_ID_EMPTY")
        if item_id in seen_ids:
            raise ConfigError(f"CONFIG_SCHEDULE_DUPLICATE_ID:{item_id}")
        seen_ids.add(item_id)
        weekday = entry.get("weekday")
        if not isinstance(weekday, int) or isinstance(weekday, bool) or not 1 <= weekday <= 7:
            raise ConfigError(f"CONFIG_SCHEDULE_WEEKDAY:{item_id}")
        hour = entry.get("hour")
        if not isinstance(hour, int) or isinstance(hour, bool) or not 0 <= hour <= 23:
            raise ConfigError(f"CONFIG_SCHEDULE_HOUR:{item_id}")
        identity = _require(entry, "identity", str)
        if identity not in identities:
            raise ConfigError(f"CONFIG_SCHEDULE_IDENTITY_UNKNOWN:{item_id}")
        prompt = _require(entry, "prompt", str)
        if not prompt.strip():
            raise ConfigError(f"CONFIG_SCHEDULE_PROMPT_EMPTY:{item_id}")
        # Even a scheduled message is CEO-to-identity traffic (invariant 3): the route must
        # already be an explicit allow, never created implicitly by the schedule entry.
        if (HUMAN, identity) not in routes:
            raise ConfigError(f"CONFIG_SCHEDULE_ROUTE_MISSING:{item_id}")
        items.append(ScheduleItem(id=item_id, weekday=weekday, hour=hour, identity=identity, prompt=prompt))
    return tuple(items)


def _bounded_int(values: Dict[str, Any], key: str, *, minimum: int, maximum: int,
                 default: Any = None) -> int:
    value = values.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"CONFIG_TYPE:{key}")
    if not minimum <= value <= maximum:
        raise ConfigError(f"CONFIG_RANGE:{key}")
    return value


def _exact_base_url(value: str, *, scheme: str, hosts: Tuple[str, ...]) -> bool:
    """Accept one origin, not prefix lookalikes, credentials or hidden paths."""
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == scheme
        and parsed.hostname in hosts
        and parsed.username is None
        and parsed.password is None
        and parsed.path in ("", "/")
        and not parsed.query
        and not parsed.fragment
        and (port is None or 1 <= port <= 65535)
    )


def load(path: str) -> Config:
    """The running configuration is not versioned (it carries the chat id), so the process
    names it by digest (G-107): the same digest the deploy printed, in the audit at start."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
        values = json.loads(raw.decode("utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"CONFIG_FILE_MISSING:{path}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ConfigError("CONFIG_NOT_JSON") from exc
    if not isinstance(values, dict):
        raise ConfigError("CONFIG_NOT_OBJECT")
    cfg = parse(values, base_dir=os.path.dirname(os.path.abspath(path)))
    return dataclasses.replace(cfg, digest=hashlib.sha256(raw).hexdigest())


def read_secret(secrets_dir: str, name: str) -> str:
    """A secret is a file: fixed rights, plain single-line text, never from the environment.

    Mode: no bits for "others" - 600 or 640 (a group share for a non-root
    container user is fine). Form: one line, no RTF header, no NUL - a file
    written with TextEdit is RTF and looked like a token once.
    """
    path = os.path.join(secrets_dir, name)
    try:
        info = os.stat(path)
    except FileNotFoundError as exc:
        raise ConfigError(f"SECRET_MISSING:{name}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise ConfigError(f"SECRET_NOT_A_FILE:{name}")
    mode = stat.S_IMODE(info.st_mode)
    if mode not in (0o600, 0o640):
        raise ConfigError(f"SECRET_MODE_TOO_OPEN:{name}")
    with open(path, "rb") as handle:
        raw = handle.read(4097)
    if len(raw) > 4096:
        raise ConfigError(f"SECRET_TOO_LARGE:{name}")
    if raw.startswith(b"{\\rtf") or b"\x00" in raw:
        raise ConfigError(f"SECRET_NOT_PLAIN_TEXT:{name}")
    value = raw.decode("utf-8", errors="strict").strip()
    if not value or "\n" in value or "\r" in value:
        raise ConfigError(f"SECRET_FORM:{name}")
    return value
