"""Joins selection.json onto DATA_ROOT/data.json and writes data/meta_data.json.

The app never opens data.json. This is the one place the two files meet, and it writes
inside the app, never into DATA_ROOT.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import settings  # noqa: E402

FIELD = "status"


def load(path):
    if not path.is_file():
        raise SystemExit(f"not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    source = settings.data_root() / "data.json"
    records = load(source)
    selection = load(settings.ROOT / "data" / "selection.json")

    counts = {"unjudged": 0, "keep": 0, "reject": 0}
    for record in records:
        status = selection.get(record["image_id"], "unjudged")
        record[FIELD] = status
        counts[status] += 1

    out = settings.ROOT / "data" / "meta_data.json"
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    tally = ", ".join(f"{k} {v}" for k, v in counts.items())
    print(f"{out}: {len(records)} records, {tally}")

    ids = {r["image_id"] for r in records}
    orphans = [i for i in selection if i not in ids]
    if orphans:
        print(f"{len(orphans)} judgments match no record in {source}: {orphans[:5]}")


if __name__ == "__main__":
    main()
