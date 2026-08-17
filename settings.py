"""Reads .env. DATA_ROOT is the only absolute path in the project."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"


def _read_env():
    if not ENV.exists():
        raise SystemExit(f"{ENV} not found. Copy .env.example and set DATA_ROOT.")
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def data_root():
    value = _read_env().get("DATA_ROOT", "")
    if not value:
        raise SystemExit(f"DATA_ROOT is not set in {ENV}.")
    path = Path(value)
    if not path.is_dir():
        raise SystemExit(f"DATA_ROOT does not exist: {path}")
    return path
