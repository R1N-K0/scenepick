"""Generates cache/thumb/{image_id}.jpg. A cache: deleting it and rerunning is safe."""

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import settings  # noqa: E402

WIDTH = 320


def main():
    root = settings.data_root()
    thumb = settings.ROOT / "cache" / "thumb"
    thumb.mkdir(parents=True, exist_ok=True)

    made = 0
    for src in sorted(root.rglob("*")):
        if src.suffix.lower() not in (".jpg", ".png"):
            continue
        dst = thumb / f"{src.stem}.jpg"
        if dst.exists():
            continue
        img = Image.open(src)
        img.thumbnail((WIDTH, WIDTH))
        img.convert("RGB").save(dst, quality=80)
        made += 1

    print(f"{thumb}: {made} new")


if __name__ == "__main__":
    main()
