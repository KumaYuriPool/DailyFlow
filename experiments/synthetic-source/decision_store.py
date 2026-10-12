"""Persistent decision store for relation confirm/exclude (DF-15).

User decisions survive refresh: the store file lives next to the projection,
keyed by (topic, left_record_id, right_record_id). On re-organize,
apply_relations re-applies stored decisions automatically.

Store format (<root>/relation-decisions.json):
{
  "schema": 1,
  "decisions": {
    "bouldering|climb-post-001|exp-climb-001": {
      "decision": "confirm", "user_note": "...", "decided_at": "ISO"
    }
  }
}

Rules:
- Same key rewrite overwrites (user changed their mind).
- Entries are never deleted (audit trail); "exclude" later "confirm" simply wins.
- Topic changes do not lose decisions: keys are per-topic.
- The store is human-readable JSON; users may edit it externally.
"""

import datetime as _dt
import json
from pathlib import Path


def store_path(root):
    return Path(root) / "relation-decisions.json"


def load_store(root):
    p = store_path(root)
    if not p.exists():
        return {"schema": 1, "decisions": {}}
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError(f"unsupported decision store schema: {data.get('schema')}")
    return data


def save_store(root, store):
    p = store_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def _key(topic, left_id, right_id):
    a, b = sorted([left_id, right_id])
    return f"{topic}|{a}|{b}"


def record_decision(root, topic, left_id, right_id, decision, note=""):
    if decision not in ("confirm", "exclude", "needs_user"):
        raise ValueError(f"invalid decision: {decision}")
    store = load_store(root)
    store["decisions"][_key(topic, left_id, right_id)] = {
        "decision": decision,
        "user_note": note,
        "decided_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }
    save_store(root, store)
    return _key(topic, left_id, right_id)


def get_decision(store, topic, left_id, right_id, default="needs_user"):
    return store.get("decisions", {}).get(_key(topic, left_id, right_id), {}).get("decision", default)


def apply_stored_to_candidates(candidates, store, topic):
    """Overlay stored decisions onto a fresh candidate list (refresh path)."""
    for pair in candidates.get("pairs", []):
        stored = get_decision(store, topic, pair["left"]["source_record_id"], pair["right"]["source_record_id"])
        if stored != "needs_user":
            pair["decision"] = stored
            pair["decision_source"] = "persisted_store"
    return candidates
