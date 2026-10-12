"""Agent selector: capability catalog + question -> sources/topics.

Given a user question, this module picks:
- which source_apps to read
- which tag filters / kind filters to apply
- whether clarification is required (no match)

Rule-based for offline determinism. Real DailyFlow model replaces the
matcher with model.complete output that obeys the same capability catalog
shape; the catalog schema here is what `dailyflow.capabilities` already
emits.

Run:
    python -X utf8 experiments/synthetic-source/agent_selector.py \
        --question "攀岩" --catalog experiments/synthetic-source/catalog.json \
        --output build/semifinal-202610/synthetic-source/selection.json
"""

import argparse
import json
from pathlib import Path

DEFAULT_CATALOG = {
    "contract_version": 1,
    "sources": [
        {
            "source_app": "synthetic-climbing",
            "label": "攀岩社媒",
            "modules": ["post", "image"],
            "topics": ["bouldering", "first-visit", "log", "milestone"],
            "default_window_days": 90,
            "permission": "syn (allow-list)",
        },
        {
            "source_app": "synthetic-calendar",
            "label": "日历(合成)",
            "modules": ["event_fact", "event_plan"],
            "topics": ["bouldering", "concert"],
            "default_window_days": 180,
            "permission": "syn (allow-list)",
        },
        {
            "source_app": "synthetic-expense",
            "label": "账目(合成)",
            "modules": ["expense"],
            "topics": ["bouldering", "concert"],
            "default_window_days": 365,
            "permission": "syn (allow-list)",
        },
        {
            "source_app": "synthetic-concert",
            "label": "演出社媒",
            "modules": ["post"],
            "topics": ["concert", "after-show", "announcement"],
            "default_window_days": 60,
            "permission": "syn (allow-list)",
        },
    ],
    "cross_source_alias": {
        "攀岩": "bouldering",
        "抱石": "bouldering",
        "bouldering": "bouldering",
        "演出": "concert",
        "concert": "concert",
        "音乐会": "concert",
    },
    "clarification_triggers": ["这个", "那件事", "再买", "再约"],
}


def load_catalog(path):
    if not path or not Path(path).exists():
        return DEFAULT_CATALOG
    return json.loads(Path(path).read_text(encoding="utf-8"))


def match_topic(question, catalog):
    q = question.lower()
    for alias, topic in catalog["cross_source_alias"].items():
        if alias.lower() in q:
            return topic
    for trigger in catalog.get("clarification_triggers", []):
        if trigger.lower() in q:
            return ("clarify", trigger)
    return None


def select_sources(topic, catalog):
    selected = []
    for src in catalog["sources"]:
        if topic in src["topics"]:
            selected.append(src["source_app"])
    return selected


def render_selection(question, topic, sources, *, query_id, clarification=None):
    if clarification:
        return {
            "tool": "dailyflow.capabilities",
            "contract_version": 1,
            "status": "needs_clarification",
            "query": {"query_id": query_id, "question": question, "matched_topic": None},
            "clarification": {"trigger": clarification, "candidates": list(DEFAULT_CATALOG["cross_source_alias"].values())},
            "plan": [],
            "selected_sources": [],
        }
    return {
        "tool": "dailyflow.capabilities",
        "contract_version": 1,
        "status": "ok",
        "query": {"query_id": query_id, "question": question, "matched_topic": topic},
        "plan": [
            {
                "source_app": src,
                "kind_filter": "any",
                "topic_filter": topic,
            }
            for src in sources
        ],
        "selected_sources": sources,
        "audit": {"adoption_layer": "v1-import (route=B)", "selector": "rule-based"},
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--query-id", default="")
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    catalog = load_catalog(args.catalog)
    matched = match_topic(args.question, catalog)
    if isinstance(matched, tuple) and matched[0] == "clarify":
        sel = render_selection(args.question, None, [], query_id=args.query_id or "select-1", clarification=matched[1])
    else:
        sources = select_sources(matched, catalog) if matched else []
        sel = render_selection(args.question, matched, sources, query_id=args.query_id or "select-1")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] selection -> {out} status={sel['status']} sources={sel['selected_sources']} topic={sel['query'].get('matched_topic')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
