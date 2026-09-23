"""Stand in for the capture side until real data arrives.

Writes data.json, group.json, calibration.json, and one RGB image per shot, all directly in
DATA_ROOT. Every shot has the white board and its two markers in frame.
Raise SETS to 37 for the real scale of about 185 scenes.
"""

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import settings  # noqa: E402

SETS = 1
SCENES_PER_SET = 3
START = datetime(2026, 8, 10, 9, 0, 0)
INTERVAL = timedelta(seconds=20)
WEATHER = ["sunny", "cloudy", "overcast"]

SIZE = (1280, 960)
BLUR_RATE = 0.15
BLOWN_RATE = 0.08


def build():
    random.seed(0)
    shots = []
    groups = []
    scene_no = 0
    for set_no in range(1, SETS + 1):
        t = START + timedelta(days=set_no - 1)
        for _ in range(SCENES_PER_SET):
            scene_no += 1
            scene_id = str(scene_no)
            weather = random.choice(WEATHER)
            gain = random.choice([0, 10, 20, 30])
            image_ids = []

            for _ in range(random.randint(12, 20)):
                image_ids.append(f"{t:%Y%m%d_%H%M%S}_01")
                shots.append(shot(image_ids[-1], scene_id, t, gain, weather))
                t += INTERVAL

            groups.append({"name": scene_id, "image_ids": image_ids})
            t += timedelta(minutes=6)
    return shots, groups


def shot(image_id, scene_id, t, gain, weather):
    return {
        "image_id": image_id,
        "scene_id": scene_id,
        "metadata": {
            "datetime": t.isoformat(),
            "exposure_time_ms": round(random.uniform(3.0, 20.0), 2),
            "gain": gain,
            "weather": weather,
        },
    }


def font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def capture(seed):
    rng = random.Random(seed)
    img = Image.new("RGB", SIZE, tuple(rng.randrange(60, 140) for _ in range(3)))
    d = ImageDraw.Draw(img)
    for _ in range(rng.randint(3, 6)):
        x, y = rng.randrange(0, SIZE[0] - 200), rng.randrange(0, SIZE[1] - 200)
        side = rng.randrange(120, 320)
        color = tuple(rng.randrange(80, 256) for _ in range(3))
        if rng.random() < 0.5:
            d.ellipse((x, y, x + side, y + side), fill=color)
        else:
            d.rectangle((x, y, x + side, y + side), fill=color)
    box = board(d, rng)
    if rng.random() < BLUR_RATE:
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(4, 9)))
    if rng.random() < BLOWN_RATE:
        img = Image.blend(img, Image.new("RGB", SIZE, (255, 255, 255)), 0.65)
    return img, box


def board(d, rng):
    """The white board with a marker under each bottom corner. Returns its [x0, y0, x1, y1]."""
    x0, y0 = rng.randrange(760, 840), rng.randrange(480, 560)
    x1, y1 = x0 + 360, y0 + 240
    # PIL fills x1 and y1 themselves; calibration.json's x1 and y1 are exclusive.
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(244, 244, 242))
    for x in (x0, x1 - 60):
        d.rectangle((x, y1 + 40, x + 59, y1 + 99), fill=(0, 0, 0))
        d.rectangle((x + 15, y1 + 55, x + 29, y1 + 69), fill=(255, 255, 255))
    return [x0, y0, x1, y1]


def render(record):
    img, box = capture(record["image_id"])
    d = ImageDraw.Draw(img)
    d.text((40, 32), record["image_id"], fill=(0, 0, 0), font=font(44))
    d.text((40, 88), f"scene {record['scene_id']}", fill=(0, 0, 0), font=font(36))
    return img, box


def write_json(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def main():
    root = settings.data_root()
    shots, groups = build()
    write_json(root / "data.json", shots)
    write_json(root / "group.json", groups)

    boxes = {}
    for record in shots:
        img, boxes[record["image_id"]] = render(record)
        img.save(root / f"{record['image_id']}.jpg", quality=88)
    write_json(root / "calibration.json", boxes)

    print(f"{root}: {len(shots)} images, {len(groups)} groups")


if __name__ == "__main__":
    main()
