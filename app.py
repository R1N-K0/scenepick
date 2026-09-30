import io
import json
import os
import threading
import time
from collections import deque

from flask import Flask, abort, jsonify, render_template, request, send_file
from PIL import Image

import settings

# Before anything is read or written: a second copy on a taken port must not touch the files.
if __name__ == "__main__":
    settings.refuse_taken_port()

DATA_ROOT = settings.data_root()
THUMB = settings.ROOT / "cache" / "thumb"
SELECTION = settings.selection_path()


def find_images(roots):
    found = {}
    for path in sorted(p for root in roots for p in root.rglob("*")):
        if path.suffix.lower() not in (".jpg", ".png"):
            continue
        if path.stem in found:
            raise SystemExit(
                f"two files claim the image_id {path.stem}: {found[path.stem]} and {path}"
            )
        found[path.stem] = path
    # Ordered by image_id, not by path: capture order is in the filename, not in the
    # directory names, which the app knows nothing about.
    return dict(sorted(found.items()))


UNGROUPED = "ungrouped"

# group.json names a group by its number alone. The word is the one thing the app assumes
# about what a group is, and this is the only place it is written.
GROUP_LABEL = "scene"


def read_groups(images):
    """image_id -> group name, in the order the grid shows them. None without a group.json.

    A group may name a shot that has not been converted yet, and two groups may name the same
    shot. Neither is worth stopping for. The first group to name a shot keeps it, so the grid
    shows every image exactly once and the counts stay a count over the images.
    """
    path = DATA_ROOT / "group.json"
    if not path.is_file():
        return None

    placed = {}
    unknown = 0
    for group in json.loads(path.read_text(encoding="utf-8")):
        for image_id in sorted(group["image_ids"]):
            if image_id not in images:
                unknown += 1
            elif image_id not in placed:
                placed[image_id] = f"{GROUP_LABEL} {group['name']}"

    # Whatever no group claimed goes last, still in image_id order.
    loose = [i for i in images if i not in placed]
    for image_id in loose:
        placed[image_id] = UNGROUPED
    print(
        f"{path}: {len(placed) - len(loose)} grouped, {len(loose)} {UNGROUPED}"
        f", {unknown} ids with no image",
        flush=True,
    )
    return placed


def read_calibration(images):
    """image_id -> [x0, y0, x1, y1], drawn over the shot and nothing more. {} without one."""
    path = DATA_ROOT / "calibration.json"
    if not path.is_file():
        return {}

    boxes = json.loads(path.read_text(encoding="utf-8"))
    for image_id, box in boxes.items():
        if not (
            len(box) == 4
            and all(type(v) is int for v in box)
            and 0 <= box[0] < box[2]
            and 0 <= box[1] < box[3]
        ):
            raise SystemExit(f"{path}: {image_id} is not [x0, y0, x1, y1]: {box}")
    print(
        f"{path}: {sum(1 for i in images if i in boxes)} boxes"
        f", {sum(1 for i in boxes if i not in images)} ids with no image",
        flush=True,
    )
    return boxes


RGB_ROOTS = settings.rgb_roots()
IMAGES = find_images(RGB_ROOTS)
if not IMAGES:
    raise SystemExit(f"no .jpg or .png under {', '.join(map(str, RGB_ROOTS))}")
GROUPS = read_groups(IMAGES)
BOXES = read_calibration(IMAGES)
ORDER = list(GROUPS or IMAGES)

app = Flask(__name__)


def read_selection():
    return json.loads(SELECTION.read_text(encoding="utf-8")) if SELECTION.exists() else {}


def write_selection(selection):
    SELECTION.parent.mkdir(parents=True, exist_ok=True)
    tmp = SELECTION.with_name("selection.tmp")
    tmp.write_text(json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, SELECTION)


# Shots read ahead of the reviewer and held in memory. On the NAS one picture takes longer to
# read than to judge, so the next ones are read while the current one is looked at, and the
# wait at the start (shown on the grid) buys a run with none.
AHEAD = settings.prefetch()
HELD = {}  # image_id -> (bytes, mimetype)
RECENT = deque(maxlen=5)  # shots just seen, kept so stepping back to one is not a read again
SPENT = []  # seconds each shot took to read and convert, for the estimate on the grid
FAILED = set()
CURSOR = 0  # where the reviewer is in ORDER
WAKE = threading.Event()
GUARD = threading.Lock()


def upcoming():
    """The next AHEAD shots to judge from where the reviewer is: unjudged, and in a scene.

    Ungrouped shots are left out: they are not judged until they are in a scene (README).
    """
    selection = read_selection()
    ids = []
    for image_id in ORDER[CURSOR:]:
        if selection.get(image_id, "unjudged") != "unjudged" or image_id in FAILED:
            continue
        if GROUPS and GROUPS[image_id] == UNGROUPED:
            continue
        ids.append(image_id)
        if len(ids) == AHEAD:
            break
    return ids


def eight_bit(path):
    """The picture as the browser would show it, a third of the bytes of the 16-bit PNG.

    A browser draws a 16-bit PNG at 8 bits anyway. Pillow opens one keeping the high byte of
    each channel; level 1 takes a third of the default's time for under 10% more bytes.
    Anything but a PNG is held as it is.
    """
    if path.suffix.lower() != ".png":
        return path.read_bytes(), "image/jpeg"
    buffer = io.BytesIO()
    with Image.open(path) as picture:
        picture.save(buffer, "PNG", compress_level=1)
    return buffer.getvalue(), "image/png"


def read_ahead():
    """Runs for as long as the app does: fill up to what upcoming() names, drop the rest."""
    while True:
        WAKE.clear()  # before looking, so a step taken meanwhile is not missed
        want = upcoming()
        with GUARD:
            for image_id in [i for i in HELD if i not in want and i not in RECENT]:
                del HELD[image_id]
            todo = next((i for i in want if i not in HELD), None)
        if todo is None:
            WAKE.wait()
            continue
        started = time.monotonic()
        try:
            kept = eight_bit(IMAGES[todo])
        except OSError as problem:
            print(f"not read ahead: {IMAGES[todo]}: {problem}", flush=True)
            FAILED.add(todo)
            continue
        SPENT.append(time.monotonic() - started)
        with GUARD:
            HELD[todo] = kept


def ensure_selection():
    selection = read_selection()
    if all(i in selection for i in IMAGES):
        return
    ordered = {i: selection.pop(i, "unjudged") for i in IMAGES}
    ordered.update(selection)  # ids whose image is gone keep their judgment
    write_selection(ordered)


@app.get("/")
def home():
    return render_template("home.html")


@app.get("/shot/<image_id>")
def detail(image_id):
    if image_id not in IMAGES:
        abort(404)
    global CURSOR
    CURSOR = ORDER.index(image_id)
    RECENT.append(image_id)
    WAKE.set()
    # The whole order goes to the page, not just the two neighbours: with "unjudged only" on,
    # the neighbours are picked in the browser, which holds what that filter was set to.
    return render_template(
        "detail.html",
        image_id=image_id,
        status=read_selection().get(image_id, "unjudged"),
        box=BOXES.get(image_id),
        group=GROUPS[image_id] if GROUPS else None,
        order=ORDER,
    )


def serve(path):
    if not path.is_file():
        abort(404)
    return send_file(path, max_age=3600)


@app.get("/rgb/<image_id>")
def rgb(image_id):
    if image_id not in IMAGES:
        abort(404)
    with GUARD:
        kept = HELD.get(image_id)
    if kept:
        return send_file(io.BytesIO(kept[0]), mimetype=kept[1], max_age=3600)
    return serve(IMAGES[image_id])


@app.get("/api/ahead")
def api_ahead():
    """How far the reading ahead has got, for the grid to say how long to wait."""
    want = upcoming()
    with GUARD:
        have = sum(1 for i in want if i in HELD)
    last = SPENT[-10:]
    left = round(sum(last) / len(last) * (len(want) - have)) if last else None
    return jsonify({"have": have, "want": len(want), "seconds_left": left})


@app.get("/thumb/<image_id>")
def thumb(image_id):
    if image_id not in IMAGES:
        abort(404)
    return serve(THUMB / f"{image_id}.jpg")


@app.get("/api/images")
def api_images():
    selection = read_selection()
    rows = [{"image_id": i, "status": selection.get(i, "unjudged")} for i in ORDER]
    if GROUPS:
        for row in rows:
            row["group"] = GROUPS[row["image_id"]]
    return jsonify(rows)


@app.post("/api/status")
def api_status():
    body = request.get_json(silent=True) or {}
    image_id, status = body.get("image_id"), body.get("status")
    if status not in ("unjudged", "keep", "reject"):
        abort(400)
    if image_id not in IMAGES:
        abort(404)

    selection = read_selection()
    selection[image_id] = status
    write_selection(selection)
    WAKE.set()  # a judged shot leaves what is read ahead, and the next one comes in
    return jsonify({"image_id": image_id, "status": status})


ensure_selection()
print(
    f"{len(IMAGES)} images"
    f", {sum(1 for i in IMAGES if not (THUMB / f'{i}.jpg').is_file())} without a thumbnail"
    f", {sum(1 for i in read_selection() if i not in IMAGES)} judgments without an image",
    flush=True,
)

if __name__ == "__main__":
    # The reloader runs this file twice, and only its child serves: reading ahead in the
    # parent too would read every shot twice and hold it twice.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=read_ahead, daemon=True).start()
    app.run(debug=True, port=settings.port())
