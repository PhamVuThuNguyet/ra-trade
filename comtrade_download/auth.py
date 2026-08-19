"""Load Comtrade Premium subscription keys from the environment."""

import os
from collections.abc import Mapping
from pathlib import Path

from comtrade_download.constants import (
    ENV_PATH,
    PRIMARY_KEY_NAME,
    SECONDARY_KEY_NAME,
    ComtradeDownloadError,
)


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        values[name.strip()] = value.strip().strip("'").strip('"')
    return values


def load_subscription_keys(
    env_path: Path = ENV_PATH,
    environ: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    file_values = parse_env_file(env_path)
    env_values = environ if environ is not None else os.environ
    keys: list[str] = []
    for name in (PRIMARY_KEY_NAME, SECONDARY_KEY_NAME):
        value = env_values.get(name) or file_values.get(name)
        if value and value not in keys:
            keys.append(value)
    if not keys:
        raise ComtradeDownloadError(
            f"Missing {PRIMARY_KEY_NAME} or {SECONDARY_KEY_NAME} in {env_path}"
        )
    return tuple(keys)
