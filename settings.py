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


def rgb_roots():
    """The directories RGB_ROOT names when .env sets it, else [DATA_ROOT].

    On the NAS the pictures sit where RGB conversion writes them, which this app only reads;
    group.json and calibration.json sit in DATA_ROOT beside the other working files.

    RGB_ROOT may hold a `*`. Each batch holds the same shots three times -- rgb/ for the
    dataset, rgb_sat/ for this app (saturated pixels show red), rgb_view/ for annotating --
    so reading a whole batch finds every image_id three times. .../cvpr_dataset/*/rgb_sat
    reads this app's version from every batch, and a new batch needs no new setting.
    """
    value = _read_env().get("RGB_ROOT", "")
    if not value:
        return [data_root()]
    parts = Path(value).parts
    at = next((i for i, part in enumerate(parts) if "*" in part), None)
    if at is None:
        roots = [Path(value)] if Path(value).is_dir() else []
    else:
        roots = sorted(p for p in Path(*parts[:at]).glob("/".join(parts[at:])) if p.is_dir())
    if not roots:
        raise SystemExit(f"RGB_ROOT names no directory: {value}")
    return roots


def selection_path():
    """SELECTION when .env sets it, else data/selection.json in this repository.

    On the NAS the verdicts are written where the ledger side reads them, so nobody has to
    send the file on. It stays a file of its own: maskeditor rewrites its own selection.json
    whole on every reject, and two apps writing one file would drop each other's saves.
    """
    value = _read_env().get("SELECTION", "")
    return Path(value) if value else ROOT / "data" / "selection.json"


def port():
    """PORT from .env, else Flask's 5000.

    The reviewer and the mask correctors work on one Windows machine over remote desktop,
    and their sessions share one network stack: two apps on 5000 and the second will not start.
    """
    return int(_read_env().get("PORT", "") or 5000)
