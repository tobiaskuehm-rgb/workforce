"""One configuration file, validated at start. Missing means refuse, never guess.

Everything the process needs to decide is in one JSON file: identities, routes,
policies, budgets, paths. Secrets are *not* in it - they live as files in
`secrets_dir` and are read by `read_secret()`, which checks mode and form.
"""

from __future__ import annotations

import json
import os
import pathlib
import stat
from dataclasses import dataclass
from typing import Any, Dict, Tuple

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

    poll = int(values.get("poll_timeout_seconds", 25))
    if not 1 <= poll <= 50:
        raise ConfigError("CONFIG_POLL_TIMEOUT_RANGE")
    max_usd = _require(values, "max_usd_per_day", float)
    if max_usd < 0:
        raise ConfigError("CONFIG_BUDGET_NEGATIVE")
    base = str(values.get("telegram_base_url", "https://api.telegram.org"))
    if not base.startswith("https://"):
        raise ConfigError("CONFIG_TELEGRAM_NOT_HTTPS")

    return Config(
        db_path=_require(values, "db_path", str),
        secrets_dir=_require(values, "secrets_dir", str),
        allowed_chat_id=_require(values, "allowed_chat_id", int),
        default_identity=default,
        identities=identities,
        routes=tuple(routes),
        max_calls_per_day=_require(values, "max_calls_per_day", int),
        max_usd_per_day=max_usd,
        ollama_url=str(values.get("ollama_url", "http://127.0.0.1:11434")),
        poll_timeout_seconds=poll,
        lease_seconds=int(values.get("lease_seconds", 300)),
        max_attempts=int(values.get("max_attempts", 3)),
        telegram_base_url=base,
        anthropic_workspace_id=str(values.get("anthropic_workspace_id", "")).strip(),
    )


def load(path: str) -> Config:
    try:
        with open(path, encoding="utf-8") as handle:
            values = json.load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(f"CONFIG_FILE_MISSING:{path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError("CONFIG_NOT_JSON") from exc
    if not isinstance(values, dict):
        raise ConfigError("CONFIG_NOT_OBJECT")
    return parse(values, base_dir=os.path.dirname(os.path.abspath(path)))


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
    if info.st_mode & 0o007:
        raise ConfigError(f"SECRET_MODE_TOO_OPEN:{name}")
    with open(path, "rb") as handle:
        raw = handle.read(4096)
    if raw.startswith(b"{\\rtf") or b"\x00" in raw:
        raise ConfigError(f"SECRET_NOT_PLAIN_TEXT:{name}")
    value = raw.decode("utf-8", errors="strict").strip()
    if not value or "\n" in value or "\r" in value:
        raise ConfigError(f"SECRET_FORM:{name}")
    return value
