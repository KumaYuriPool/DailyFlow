"""Reads projection produced by `importer.py` and emits the same JSON shape
that DailyFlow's `dailyflow.timeline_query` would return for the same scope.

This is the bridge step (DF-08) where v1 envelope -> DailyFlow projection ->
`synthetic.*`-accepted timeline_query response. It runs offline and does NOT
modify the live DailyFlow instance.

Run:
    python -X utf8 experiments/synthetic-source/dailyflow_query_v1.py \
        --projection build/semifinal-202610/synthetic-source/projection-climbing \
        --topics climbing --from 2026-09-01 --to 2026-10-31 \
        --output build/semifinal-202610/synthetic-source/query-climbing.json
"""

import argparse
import datetime as _dt
import json
from pathlib import Path


def parse_dt(value, *, fallback):
    if not value:
        return fallback
    try:
        if "T" in value:
            return _dt.datetime.fromisoformat(value)
        return _dt.datetime.fromisoformat(value + "T00:00:00")
    except Exception:
        return fallback


def discover_records(projection_root, *, source_apps=None, topic=None, date_from=None, date_to=None):
    """Iterate records under <root>/records/<source_app>/<record_id>."""
    records_root = projection_root / "records"
    if not records_root.exists():
        return
    for source_dir in sorted(records_root.iterdir()):
        if not source_dir.is_dir():
            continue
        if source_apps and source_dir.name not in source_apps:
            continue
        for rec_dir in sorted(source_dir.iterdir()):
            if not rec_dir.is_dir():
                continue
            latest = None
            latest_rev = -1
            # audit F04: choose by numeric revision, never file-name string sort
            for rev_path in rec_dir.glob("rev-*.json"):
                try:
                    n = int(rev_path.stem.split("-")[1])
                except (IndexError, ValueError):
                    continue
                if n > latest_rev:
                    latest_rev, latest = n, rev_path
            if not latest:
                continue
            rec = json.loads(latest.read_text(encoding="utf-8"))
            tomb_path = rec_dir / "tombstone.json"
            tomb = json.loads(tomb_path.read_text(encoding="utf-8")) if tomb_path.exists() else None
            # R1 query-side gate: a tombstone hides the record outright — a
            # deleted record is never returned as data, whatever content
            # revisions remain stored as history.
            if tomb is not None:
                continue
            content = rec.get("content", {})
            occurred = content.get("occurred_at") or content.get("start")
            if not occurred:
                continue
            occurred_dt = parse_dt(occurred, fallback=_dt.datetime.min)
            if date_from:
                if occurred_dt.tzinfo is None:
                    cmp = date_from.replace(tzinfo=None) if date_from.tzinfo else date_from
                else:
                    cmp = date_from if date_from.tzinfo else date_from.replace(tzinfo=occurred_dt.tzinfo)
                if occurred_dt < cmp:
                    continue
            if date_to:
                if occurred_dt.tzinfo is None:
                    cmp = date_to.replace(tzinfo=None) if date_to.tzinfo else date_to
                else:
                    cmp = date_to if date_to.tzinfo else date_to.replace(tzinfo=occurred_dt.tzinfo)
                if occurred_dt > cmp:
                    continue
            tags = content.get("tags", [])
            if topic and topic.lower() not in [t.lower() for t in tags] and topic.lower() not in content.get("title", "").lower():
                continue
            yield {
                "source_app": rec["source_app"],
                "source_module": rec.get("source_module", "post"),
                "source_record_id": rec["source_record_id"],
                "source_revision": rec["source_revision"],
                "kind": content.get("kind"),
                "occurred_at": occurred,
                "title": content.get("title"),
                "body": content.get("body", ""),
                "tags": tags,
                "amount_minor": content.get("amount_minor", -1),
                "currency": content.get("currency", "CNY"),
                "media": content.get("media", []),
                "deleted": bool(tomb),
                "source_meta": content.get("source_meta", {}),
            }


def render_timeline_query_response(records, *, query_id, topic, from_d, to_d, source_apps):
    sorted_records = sorted(records, key=lambda r: r["occurred_at"])
    sources_seen = sorted({r["source_app"] for r in sorted_records})
    kinds_seen = sorted({r["kind"] for r in sorted_records if r["kind"]})
    return {
        "tool": "dailyflow.timeline_query",
        "contract_version": 1,
        "query": {
            "query_id": query_id,
            "topic": topic,
            "from": from_d.isoformat() if from_d else None,
            "to": to_d.isoformat() if to_d else None,
            "source_apps": sorted(source_apps) if source_apps else None,
        },
        "result": {
            "ok": True,
            "record_count": len(sorted_records),
            "sources_seen": sources_seen,
            "kinds_seen": kinds_seen,
            "sources_with_data": {s: sum(1 for r in sorted_records if r["source_app"] == s) for s in sources_seen},
            "shortfall": [],
            "records": sorted_records,
        },
        "audit": {
            "records_considered": len(sorted_records),
            "synthetic": True,
            "adoption_layer": "v1-import (route=B)",
        },
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--projection", required=True)
    ap.add_argument("--topics", default="")
    ap.add_argument("--source-apps", default="")
    ap.add_argument("--from", dest="from_d", default="")
    ap.add_argument("--to", dest="to_d", default="")
    ap.add_argument("--query-id", default="")
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    projection = Path(args.projection)
    if not projection.exists():
        print(f"[FAIL] projection not found: {projection}")
        return 2

    topics = [t.strip() for t in args.topics.split(",") if t.strip()] if args.topics else [None]
    source_apps = {s.strip() for s in args.source_apps.split(",") if s.strip()} if args.source_apps else None
    from_d = parse_dt(args.from_d, fallback=None) if args.from_d else _dt.datetime.min
    to_d = parse_dt(args.to_d, fallback=None) if args.to_d else _dt.datetime.max

    all_records = []
    for topic in topics:
        for rec in discover_records(projection, source_apps=source_apps, topic=topic, date_from=from_d, date_to=to_d):
            all_records.append(rec)

    query_id = args.query_id or f"q-{_dt.datetime.now(_dt.timezone.utc).isoformat()}"
    out = render_timeline_query_response(all_records, query_id=query_id, topic=args.topics or "<all>",
                                        from_d=from_d, to_d=to_d, source_apps=source_apps)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(all_records)} records -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
