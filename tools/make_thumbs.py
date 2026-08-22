"""Generates cache/thumb/{image_id}.jpg. A cache: deleting it and rerunning is safe."""

import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import settings  # noqa: E402

WIDTH = 320


def duration(seconds):
    seconds = int(seconds)
    return f"{seconds // 60}m{seconds % 60:02d}s" if seconds >= 60 else f"{seconds}s"


def main():
    root = settings.data_root()
    thumb = settings.ROOT / "cache" / "thumb"
    thumb.mkdir(parents=True, exist_ok=True)

    sources = [p for p in sorted(root.rglob("*")) if p.suffix.lower() in (".jpg", ".png")]
    todo = [p for p in sources if not (thumb / f"{p.stem}.jpg").exists()]
    print(f"{len(sources)} images, {len(todo)} without a thumbnail")

    started = time.monotonic()
    for at, src in enumerate(todo, 1):
        img = Image.open(src)
        img.thumbnail((WIDTH, WIDTH))
        img.convert("RGB").save(thumb / f"{src.stem}.jpg", quality=80)
        # One line, rewritten in place. 3700 shots take minutes, and a run with no sign of
        # life is indistinguishable from a hung one.
        spent = time.monotonic() - started
        print(f"\r{at} / {len(todo)}   {duration(spent / at * (len(todo) - at))} left   ",
              end="", flush=True)

    if todo:
        print()
    print(f"{thumb}: {len(todo)} new in {duration(time.monotonic() - started)}")


if __name__ == "__main__":
    main()
