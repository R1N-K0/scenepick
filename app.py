import json
import os

from flask import Flask, abort, jsonify, render_template, request, send_file

import settings

DATA_ROOT = settings.data_root()
THUMB = settings.ROOT / "cache" / "thumb"
SELECTION = settings.selection_path()


def find_images(root):
    found = {}
    for path in sorted(root.rglob("*")):
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


RGB_ROOT = settings.rgb_root()
IMAGES = find_images(RGB_ROOT)
if not IMAGES:
    raise SystemExit(f"no .jpg or .png under {RGB_ROOT}")
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
    at = ORDER.index(image_id)
    return render_template(
        "detail.html",
        image_id=image_id,
        status=read_selection().get(image_id, "unjudged"),
        box=BOXES.get(image_id),
        prev=ORDER[at - 1] if at else None,
        next=ORDER[at + 1] if at + 1 < len(ORDER) else None,
        position=f"{at + 1} / {len(ORDER)}",
    )


def serve(path):
    if not path.is_file():
        abort(404)
    return send_file(path, max_age=3600)


@app.get("/rgb/<image_id>")
def rgb(image_id):
    if image_id not in IMAGES:
        abort(404)
    return serve(IMAGES[image_id])


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
    return jsonify({"image_id": image_id, "status": status})


ensure_selection()
print(
    f"{len(IMAGES)} images"
    f", {sum(1 for i in IMAGES if not (THUMB / f'{i}.jpg').is_file())} without a thumbnail"
    f", {sum(1 for i in read_selection() if i not in IMAGES)} judgments without an image",
    flush=True,
)

if __name__ == "__main__":
    app.run(debug=True, port=settings.port())
