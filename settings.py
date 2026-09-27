"""Reads .env. DATA_ROOT, and RGB_ROOT where it is set, are the absolute paths in the project."""

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


def rgb_root():
    """RGB_ROOT when .env sets it, else DATA_ROOT.

    On the NAS the pictures sit where RGB conversion writes them, which this app only reads;
    group.json and calibration.json sit in DATA_ROOT beside the other working files.
    """
    value = _read_env().get("RGB_ROOT", "")
    if not value:
        return data_root()
    path = Path(value)
    if not path.is_dir():
        raise SystemExit(f"RGB_ROOT does not exist: {path}")
    return path


def selection_path():
    """SELECTION when .env sets it, else data/selection.json in this repository.

    On the NAS the verdicts are written where the ledger side reads them, so nobody has to
    send the file on. It stays a file of its own: maskeditor rewrites its own selection.json
    whole on every reject, and two apps writing one file would drop each other's saves.
    """
    value = _read_env().get("SELECTION", "")
    return Path(value) if value else ROOT / "data" / "selection.json"
