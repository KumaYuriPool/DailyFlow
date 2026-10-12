"""Importer for synthetic-source v1 envelopes.

Reads envelope pages emitted by `producer.py` and writes them into a
deterministic local projection under `--root`.

Invariants (hardened after independent audit 2026-10-10, F03/F04/F05):
- Path safety: source_app and source_record_id must be single path segments
  (no separators, no .., no absolute paths); the resolved target directory
  must stay inside <root>/records/<source_app>/<record_id>.
- Monotonic revisions: an envelope record older than the stored maximum is
  rejected (history preserved, tombstones never resurrected by old replays).
- Same-revision conflict: equal revision with a different content_hash is
  refused; the stored value wins and the conflict is reported.
- Tombstone gate: a tombstone applies only if its revision >= the stored
  maximum; a tombstone at an older revision is refused (no delete, no
  resurrect).

Per-record layout (under <root>/records/<source_app>/<record_id>/):
    rev-<n>.json        record content at revision n
    tombstone.json      present iff the latest applied operation was a delete
    conflicts.json      append-only log of refused same-revision conflicts

Per-source summary (<root>/sources/<source_app>.json): counts and snapshots.
"""

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

ALLOWED_SOURCES = {"dailyflow", "synthetic-climbing", "synthetic-concert", "synthetic-calendar", "synthetic-expense"}

# Single path segment: letters/digits leading, then ._- allowed; no separators.
SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ImportError_(Exception):
    pass


def _safe_segment(value, *, what):
    if not isinstance(value, str) or not SEGMENT_RE.match(value):
        raise ImportError_(f"unsafe {what}: {value!r}")
    if value in (".", "..") or "/" in value or "\\" in value:
        raise ImportError_(f"unsafe {what}: {value!r}")
    return value


def canonical_content_hash(content):
    """Single source of truth for the recomputable content hash (R4)."""
    import hashlib
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_envelope(env):
    """R4 hardening: beyond shape checks, (a) recompute content_hash over the
    canonical content body and refuse any mismatch, (b) bind each record's
    source_app to the envelope's trusted source_app — a record claiming another
    identity is refused instead of being written into a foreign directory."""
    errs = []
    if env.get("contract_version") != 1:
        errs.append("contract_version must be 1")
    src = env.get("source_app")
    if src not in ALLOWED_SOURCES:
        errs.append(f"source_app not allowed: {src}")
    for rec in env.get("records", []):
        rid = rec.get("source_record_id")
        if rec.get("source_app") != src:
            errs.append(f"record identity mismatch for {rid}: envelope {src!r} != record {rec.get('source_app')!r}")
        elif rec.get("source_app") not in ALLOWED_SOURCES:
            errs.append(f"source_app not allowed: {src}")
        if not isinstance(rec.get("source_revision"), int) or rec["source_revision"] < 1:
            errs.append(f"invalid revision for {rid}")
        ch = rec.get("content_hash")
        if not isinstance(ch, str) or len(ch) != 64:
            errs.append(f"content_hash malformed for {rid}")
        content = rec.get("content")
        if content is None:
            errs.append(f"record missing content: {rid}")
        elif isinstance(ch, str) and len(ch) == 64:
            # B4: no universal bypass — every content record's hash must
            # recompute. (Tombstones carry no content and are checked in the
            # tombstone branch instead.)
            recompute = canonical_content_hash(content)
            if recompute != ch:
                errs.append(f"content_hash mismatch for {rid}: claimed {ch[:12]}… recomputed {recompute[:12]}…")
    for tomb in env.get("tombstones", []):
        rid = tomb.get("source_record_id")
        if tomb.get("source_app") != src:
            errs.append(f"tombstone identity mismatch for {rid}: envelope {src!r} != record {tomb.get('source_app')!r}")
        elif tomb.get("source_app") not in ALLOWED_SOURCES:
            errs.append(f"source_app not allowed: {src}")
        if not tomb.get("deleted_at"):
            errs.append(f"tombstone missing deleted_at: {rid}")
    return errs


def _record_dir(root, source_app, record_id):
    """Path-checked record directory; refuses escape from the projection."""
    src = _safe_segment(source_app, what="source_app")
    rid = _safe_segment(record_id, what="source_record_id")
    base = (root / "records").resolve()
    target = (base / src / rid).resolve()
    if base != target and base not in target.parents:
        raise ImportError_(f"path escapes projection: {source_app}/{record_id}")
    return target


def _stored_max_revision(record_dir):
    """Numeric max over stored rev files (audit F04: never string-sort)."""
    if not record_dir.exists():
        return 0, None
    best = 0
    best_path = None
    for p in record_dir.glob("rev-*.json"):
        m = re.fullmatch(r"rev-(\d+)\.json", p.name)
        if not m:
            continue
        n = int(m.group(1))
        if n > best:
            best, best_path = n, p
    return best, best_path


def _tombstone_revision(record_dir):
    """Revision of the stored tombstone, if any (audit R1)."""
    t = record_dir / "tombstone.json" if record_dir.exists() else None
    if t and t.exists():
        try:
            data = json.loads(t.read_text(encoding="utf-8"))
            rev = data.get("source_revision")
            if isinstance(rev, int) and rev >= 1:
                return rev
        except (ValueError, OSError):
            pass
    return 0


def _unified_max_revision(record_dir):
    """R1: deletions participate in the revision race. The effective ceiling
    is the max of content revisions AND the tombstone revision — a late
    content replay below a tombstone's revision can never resurrect the
    record, and a late tombstone below stored content can never roll the
    deletion back."""
    content_rev, best_path = _stored_max_revision(record_dir)
    tomb_rev = _tombstone_revision(record_dir)
    return max(content_rev, tomb_rev), content_rev, tomb_rev, best_path


def _log_conflict(record_dir, entry):
    record_dir.mkdir(parents=True, exist_ok=True)
    log_path = record_dir / "conflicts.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    log.append(entry)
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def _apply_record(root, rec, fetched_at):
    """Monotonic upsert against the UNIFIED ceiling (R1): content and
    tombstone revisions race in one ordering.

    Same-revision delete/content collision rule: first write wins; the loser
    is logged into conflicts.json and refused — no silent overwrite, no
    implicit resurrection either way.
    """
    record_dir = _record_dir(root, rec["source_app"], rec["source_record_id"])
    max_rev, content_rev, tomb_rev, _ = _unified_max_revision(record_dir)
    rev = rec["source_revision"]
    tomb = record_dir / "tombstone.json"

    if rev < max_rev:
        # Late/old replay: never write, never resurrect, never delete.
        return (False, True, False, f"stale revision {rev} < unified max {max_rev}")
    if rev == max_rev:
        if rev == content_rev and tomb_rev != rev:
            current = json.loads((record_dir / f"rev-{rev}.json").read_text(encoding="utf-8"))
            if current.get("content_hash") == rec.get("content_hash"):
                return (False, True, False, "idempotent replay")
            _log_conflict(record_dir, {
                "revision": rev, "kind": "content-conflict",
                "refused_hash": rec.get("content_hash"),
                "kept_hash": current.get("content_hash"), "at": fetched_at,
            })
            return (False, False, True, f"same-revision content conflict at rev {rev}; stored value kept")
        if rev == tomb_rev:
            # Same revision already claimed by a delete. Content may not
            # silently replace a tombstone at the same revision.
            _log_conflict(record_dir, {
                "revision": rev, "kind": "delete-vs-content",
                "refused_hash": rec.get("content_hash"), "at": fetched_at,
            })
            return (False, False, True, f"revision {rev} already deleted; content refused")
    # rev > max_rev: strictly newer content re-creates the record.
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / f"rev-{rev}.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    if tomb.exists():
        tomb.unlink()  # strictly newer content revision re-creates the record
    return (True, False, False, f"applied rev {rev}")


def _apply_tombstone(root, tomb, fetched_at):
    record_dir = _record_dir(root, tomb["source_app"], tomb["source_record_id"])
    max_rev, content_rev, tomb_rev, _ = _unified_max_revision(record_dir)
    rev = tomb["source_revision"]
    tomb_path = record_dir / "tombstone.json"
    if rev < max_rev:
        return (False, True, False, f"stale tombstone {rev} < unified max {max_rev}; record kept")
    if rev == max_rev:
        if rev == tomb_rev:
            current = json.loads(tomb_path.read_text(encoding="utf-8"))
            if current.get("deleted_at") == tomb.get("deleted_at"):
                return (False, True, False, "idempotent tombstone")
            _log_conflict(record_dir, {
                "revision": rev, "kind": "tombstone-conflict", "at": fetched_at,
            })
            return (False, False, True, f"tombstone conflict at rev {rev}; existing kept")
        if rev == content_rev:
            # Same revision already claimed by content; delete may not win.
            _log_conflict(record_dir, {
                "revision": rev, "kind": "content-vs-delete", "at": fetched_at,
            })
            return (False, False, True, f"revision {rev} already has content; tombstone refused")
    record_dir.mkdir(parents=True, exist_ok=True)
    tomb_path.write_text(json.dumps(tomb, ensure_ascii=False, indent=2), encoding="utf-8")
    return (True, False, False, f"tombstone applied at rev {rev}")


def import_envelope(env, root, summary, run_report=None):
    src = env["source_app"]
    snap = env.get("snapshot_revision", 1)
    fetched_at = env.get("fetched_at", _dt.datetime.now(_dt.timezone.utc).isoformat())

    src_summary = summary.setdefault(src, {
        "source_app": src,
        "first_seen": fetched_at,
        "last_seen": fetched_at,
        "record_count": 0,
        "snapshot_revisions": [],
    })
    src_summary["last_seen"] = fetched_at
    if snap not in src_summary["snapshot_revisions"]:
        src_summary["snapshot_revisions"].append(snap)

    run_src = (run_report if run_report is not None else {}).setdefault(
        src, {"applied": 0, "skipped": 0, "conflicts": 0, "statuses": []})

    def _tally(applied, skipped, conflict, status, record):
        run_src["applied"] += int(applied)
        run_src["skipped"] += int(skipped)
        run_src["conflicts"] += int(conflict)
        run_src["statuses"].append({"record": record, "status": status})

    for rec in env.get("records", []):
        _tally(*_apply_record(root, rec, fetched_at), rec["source_record_id"])

    for tomb in env.get("tombstones", []):
        _tally(*_apply_tombstone(root, tomb, fetched_at), tomb["source_record_id"])

    rec_root = root / "records" / src
    src_summary["record_count"] = len(list(rec_root.iterdir())) if rec_root.exists() else 0


def import_scenario(envelopes_dir, root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    summary = {}
    run_report = {}
    envelope_files = sorted(Path(envelopes_dir).glob("page-*.json"))
    if not envelope_files:
        return False, f"no envelope files in {envelopes_dir}", summary

    errs_all = []
    for f in envelope_files:
        env = json.loads(f.read_text(encoding="utf-8"))
        errs = validate_envelope(env)
        if errs:
            errs_all.extend([f"{f.name}: {e}" for e in errs])
            continue
        import_envelope(env, root, summary, run_report)

    # sources.json holds only stable facts; per-run tallies live separately so
    # re-importing the same envelopes leaves the projection byte-identical.
    (root / "sources.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "last-import-report.json").write_text(
        json.dumps(run_report, ensure_ascii=False, indent=2), encoding="utf-8")
    return (not errs_all), errs_all, summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--envelopes", required=True)
    ap.add_argument("--root", required=True)
    args = ap.parse_args(argv)

    ok, errs, summary = import_scenario(args.envelopes, args.root)
    if not ok:
        print(f"[FAIL] {args.scenario}: {errs}")
        return 2
    sources_summary_path = Path(args.root) / "sources.json"
    print(f"[OK] scenario={args.scenario} sources={len(summary)} records_root={args.root}/records summary={sources_summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
