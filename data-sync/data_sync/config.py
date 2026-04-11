from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping


@dataclass(frozen=True)
class SourceDBConfig:
    host: str
    port: int
    user: str
    password: str
    charset: str = "utf8mb4"
    connect_timeout_seconds: int = 10
    read_timeout_seconds: int = 60
    write_timeout_seconds: int = 60


def _read_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _resolve_value(env: Mapping[str, str], *keys: str) -> str:
    for key in keys:
        val = str(env.get(key, "")).strip()
        if val:
            return val
    return ""


def resolve_source_db_config(
    project_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> SourceDBConfig:
    root = project_root or Path(__file__).resolve().parents[3]

    merged: Dict[str, str] = {}
    merged.update(_read_env_file(root / ".env"))
    merged.update(_read_env_file(root / "dataenv.txt"))

    runtime_env = dict(environ or os.environ)
    merged.update({k: v for k, v in runtime_env.items() if isinstance(v, str)})

    host = _resolve_value(merged, "SOURCE_DB_HOST", "BT_DB_HOST")
    port_raw = _resolve_value(merged, "SOURCE_DB_PORT", "BT_DB_PORT")
    user = _resolve_value(merged, "SOURCE_DB_USER", "BT_DB_USER")
    password = _resolve_value(merged, "SOURCE_DB_PASSWORD", "BT_DB_PASSWORD")
    charset = _resolve_value(merged, "SOURCE_DB_CHARSET", "BT_DB_CHARSET") or "utf8mb4"

    missing = []
    if not host:
        missing.append("SOURCE_DB_HOST/BT_DB_HOST")
    if not port_raw:
        missing.append("SOURCE_DB_PORT/BT_DB_PORT")
    if not user:
        missing.append("SOURCE_DB_USER/BT_DB_USER")
    if not password:
        missing.append("SOURCE_DB_PASSWORD/BT_DB_PASSWORD")
    if missing:
        raise RuntimeError(
            "Missing source DB config keys: "
            + ", ".join(missing)
            + ". Configure env vars or .env/dataenv.txt."
        )

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid DB port: {port_raw}") from exc

    return SourceDBConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        charset=charset,
    )

