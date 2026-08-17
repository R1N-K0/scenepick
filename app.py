import json
import os

from flask import Flask, abort, jsonify, render_template, request, send_file

import settings

DATA_ROOT = settings.data_root()
THUMB = settings.ROOT / "cache" / "thumb"
SELECTION = settings.ROOT / "data" / "selection.json"

IMAGES = {p.stem: p for p in sorted(DATA_ROOT.glob("*")) if p.suffix.lower() in (".jpg", ".png")}
if not IMAGES:
    raise SystemExit(f"no .jpg or .png in {DATA_ROOT}")
ORDER = list(IMAGES)

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
    return jsonify([{"image_id": i, "status": selection.get(i, "unjudged")} for i in ORDER])


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
    app.run(debug=True)
