"""Load and merge ``.semshift.yml`` project configuration.

Precedence (lowest to highest): built-in defaults < ``.semshift.yml`` < explicit CLI flags.
The config file is optional; when absent, an empty config is returned and behavior is
unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_FILENAME = ".semshift.yml"

_STRING_KEYS = {"mode", "model", "fail_on", "ref"}
_INT_KEYS = {"max_file_size", "max_chunks", "top"}
_LIST_KEYS = {"paths", "exclude_paths"}
_ALLOWED_KEYS = _STRING_KEYS | _INT_KEYS | _LIST_KEYS


class ConfigError(RuntimeError):
    """Raised when ``.semshift.yml`` is present but invalid."""


@dataclass(frozen=True)
class SemShiftConfig:
    """Parsed ``.semshift.yml`` values. ``None``/empty means 'not set'."""

    mode: str | None = None
    model: str | None = None
    fail_on: str | None = None
    ref: str | None = None
    max_file_size: int | None = None
    max_chunks: int | None = None
    top: int | None = None
    paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()


def find_config(start: str | Path | None = None) -> Path | None:
    """Find the nearest ``.semshift.yml`` walking up from ``start`` (default cwd)."""
    base = Path(start or Path.cwd()).resolve()
    for directory in (base, *base.parents):
        candidate = directory / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
    return None


def load_config(
    path: str | Path | None = None,
    *,
    start: str | Path | None = None,
) -> SemShiftConfig:
    """Load config from ``path`` (or the nearest ``.semshift.yml``); empty if none."""
    config_path = Path(path) if path else find_config(start)
    if not config_path or not config_path.is_file():
        return SemShiftConfig()
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{config_path} must contain a YAML mapping, got {type(raw).__name__}.")
    unknown = set(raw) - _ALLOWED_KEYS
    if unknown:
        raise ConfigError(
            f"Unknown key(s) in {config_path}: {', '.join(sorted(unknown))}. "
            f"Allowed: {', '.join(sorted(_ALLOWED_KEYS))}."
        )
    return SemShiftConfig(
        mode=_as_str(raw, "mode", config_path),
        model=_as_str(raw, "model", config_path),
        fail_on=_as_str(raw, "fail_on", config_path),
        ref=_as_str(raw, "ref", config_path),
        max_file_size=_as_int(raw, "max_file_size", config_path),
        max_chunks=_as_int(raw, "max_chunks", config_path),
        top=_as_int(raw, "top", config_path),
        paths=_as_list(raw, "paths", config_path),
        exclude_paths=_as_list(raw, "exclude_paths", config_path),
    )


def _as_str(raw: dict[str, object], key: str, source: Path) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError(f"{source}: '{key}' must be a string, got {type(value).__name__}.")
    return value


def _as_int(raw: dict[str, object], key: str, source: Path) -> int | None:
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{source}: '{key}' must be an integer, got {type(value).__name__}.")
    return value


def _as_list(raw: dict[str, object], key: str, source: Path) -> tuple[str, ...]:
    value = raw.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    raise ConfigError(
        f"{source}: '{key}' must be a string or list of strings, got {type(value).__name__}."
    )
