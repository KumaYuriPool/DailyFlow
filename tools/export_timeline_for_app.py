"""Export one or more organizer timeline JSON files into the app-read format.

Merged output lets the model pick an exact topic id from `topics`; records
carry their `topic` so the Splash view can filter read-only.

Run:
    python -X utf8 tools/export_timeline_for_app.py \
        --timeline build/.../timeline-climbing.json \
        --timeline build/.../timeline-concert.json \
        --output <app-data-dir>/timeline-imported.json
"""

import argparse
import datetime as _dt
import json
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", action="append", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    today = _dt.date.today()
    topics, records, gaps = [], [], []
    for path in args.timeline:
        timeline = json.loads(Path(path).read_text(encoding="utf-8"))
        topic = timeline.get("topic", "")
        if topic and topic not in topics:
            topics.append(topic)
        for r in timeline.get("records", []):
            occurred = (r.get("occurred_at") or "")[:10]
            try:
                future = _dt.date.fromisoformat(occurred) > today
            except ValueError:
                future = False
            records.append({
                "topic": topic,
                "date": occurred,
                "title": r.get("title", ""),
                "body": r.get("body", ""),
                "source_app": r.get("source_app", ""),
                "source_module": r.get("source_module", "external"),
                "currency": r.get("currency", ""),
                "kind": r.get("kind", ""),
                "amount_minor": r.get("amount_minor", -1),
                "revision": r.get("source_revision", 0),
                "record_id": r.get("source_record_id", ""),
                "citation": r.get("citation", ""),
                "tags": r.get("tags", []),
                "suspicious": bool(r.get("suspicious_instruction")),
                "future": future,
                # R2: user exclusions from the applied timeline survive the
                # export; the app hides them and counts them in the summary.
                "excluded": bool(r.get("_excluded")),
            })
        for g in timeline.get("gaps", []):
            gaps.append({"topic": topic, "kind": g.get("kind", ""), "detail": g.get("detail", "")})

    # Source status bar data (PRODUCT_SPEC §3): which sources are in scope and
    # how many records each carries; the UI pairs this with generated_at and
    # an explicit "file import, not live-connected" label (DF-26 gate).
    source_counts = {}
    for r in records:
        source_counts[r["source_app"]] = source_counts.get(r["source_app"], 0) + 1

    out = {
        "topic": ",".join(topics),
        "topics": topics,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "adoption_layer": "v1-import (route=B)",
        "sources": [{"source_app": k, "records": source_counts[k]} for k in sorted(source_counts)],
        "records": records,
        "gaps": gaps,
    }
    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] topics={topics} {len(records)} records -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
