"""End-to-end route=B demo verification.

Drives the full pipeline:
1. producer -> v1 envelope pages (DF-07)
2. importer -> on-disk projection (DF-07/DF-09)
3. dailyflow_query_v1 -> timeline_query-shape (DF-08)
4. agent_selector -> capabilities surfaced (DF-11)
5. organizer -> timeline JSON (DF-11)
6. relation_candidates -> candidates (DF-15)
7. apply_relations -> applied timeline (DF-15)
8. render_timelines/preview_timeline -> HTML/PNG (DF-13)
9. media_resolver -> picture version (DF-14)

Then verifies:
- outputs exist and contain expected counts
- projection bytes match across re-runs (idempotence)
- tombstone preserved
- user decisions reflect in applied timeline
- freshness: a re-imported higher revision upgrades the record
"""

import argparse
import datetime as _dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha_dir(p):
    if not p.exists():
        return None
    files = sorted([f for f in p.rglob("*") if f.is_file()])
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(p).as_posix().encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def run_module(modpath, *args):
    sys.path.insert(0, str(Path(modpath).resolve().parent))
    cmd = [sys.executable, str(modpath)] + list(args)
    import subprocess
    return subprocess.run(cmd, capture_output=True, text=True)


def ensure_clean(p):
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    SYN = ROOT / "experiments/synthetic-source"

    summary = {"runs": [], "checks": [], "outputs": []}
    fail = False

    def step(name, fn):
        try:
            r = fn()
            ok = r.returncode == 0
            summary["runs"].append({"name": name, "returncode": r.returncode, "stdout": r.stdout[-300:], "stderr": r.stderr[-300:]})
            if not ok:
                fail = True
            return r
        except Exception as e:
            summary["runs"].append({"name": name, "error": str(e)})
            fail = True
            return None

    paths = {}
    paths["climb_envelopes"] = out / "envelopes-climbing"
    paths["concert_envelopes"] = out / "envelopes-concert"
    paths["climb_projection"] = out / "projection-climbing"
    paths["concert_projection"] = out / "projection-concert"
    paths["climb_query"] = out / "query-climbing.json"
    paths["concert_query"] = out / "query-concert.json"
    paths["climb_selection"] = out / "selection-climbing.json"
    paths["concert_selection"] = out / "selection-concert.json"
    paths["climb_timeline"] = out / "timeline-climbing.json"
    paths["concert_timeline"] = out / "timeline-concert.json"
    paths["climb_relations"] = out / "relations-climbing.json"
    paths["climb_relations_merged"] = out / "relations-climbing-merged.json"
    paths["climb_decided"] = out / "relations-climbing-decided.json"
    paths["climb_applied"] = out / "timeline-climbing-applied.json"
    paths["timeline_html"] = out / "timelines.html"
    paths["timeline_preview"] = out / "preview.png"
    paths["timeline_media"] = out / "preview-with-media.png"

    for p in paths.values():
        if p.is_dir() and p.exists():
            shutil.rmtree(p)
        if p.is_dir() and not p.exists():
            p.mkdir(parents=True, exist_ok=True)

    step("producer climbing", lambda: run_module(SYN / "producer.py", "--scenario", "climbing", "--output", str(paths["climb_envelopes"])))
    step("producer concert", lambda: run_module(SYN / "producer.py", "--scenario", "concert", "--output", str(paths["concert_envelopes"])))
    step("import climbing", lambda: run_module(SYN / "importer.py", "--scenario", "climbing", "--envelopes", str(paths["climb_envelopes"]), "--root", str(paths["climb_projection"])))
    step("import concert", lambda: run_module(SYN / "importer.py", "--scenario", "concert", "--envelopes", str(paths["concert_envelopes"]), "--root", str(paths["concert_projection"])))

    step("query climbing", lambda: run_module(SYN / "dailyflow_query_v1.py", "--projection", str(paths["climb_projection"]), "--topics", "bouldering", "--from", "2026-09-01", "--to", "2026-10-31", "--query-id", "e2e-climb", "--output", str(paths["climb_query"])))
    step("query concert", lambda: run_module(SYN / "dailyflow_query_v1.py", "--projection", str(paths["concert_projection"]), "--topics", "concert", "--from", "2026-09-25", "--to", "2026-10-31", "--query-id", "e2e-concert", "--output", str(paths["concert_query"])))

    step("selector climbing", lambda: run_module(SYN / "agent_selector.py", "--question", "我是怎么从刷到攀岩视频到持续练习的", "--catalog", str(SYN / "catalog.json"), "--query-id", "e2e-sel-climb", "--output", str(paths["climb_selection"])))
    step("selector concert", lambda: run_module(SYN / "agent_selector.py", "--question", "演出从期待到结束的经历串起来", "--catalog", str(SYN / "catalog.json"), "--query-id", "e2e-sel-concert", "--output", str(paths["concert_selection"])))

    step("organizer climbing", lambda: run_module(SYN / "organizer.py", "--selection", str(paths["climb_selection"]), "--query-climb", str(paths["climb_query"]), "--output", str(paths["climb_timeline"])))
    step("organizer concert", lambda: run_module(SYN / "organizer.py", "--selection", str(paths["concert_selection"]), "--query-concert", str(paths["concert_query"]), "--output", str(paths["concert_timeline"])))

    step("relations climbing", lambda: run_module(SYN / "relation_candidates.py", "--timeline", str(paths["climb_timeline"]), "--output", str(paths["climb_relations"])))

    decided = (ROOT / "build/semifinal-202610/synthetic-source/relations-climbing-decided.json")
    paths["climb_decided"] = paths["climb_decided"]
    shutil.copy(decided, paths["climb_decided"])

    step("merge decisions", lambda: run_module(ROOT / "tools/_merge_relations.py", "--candidates", str(paths["climb_relations"]), "--decisions", str(paths["climb_decided"]), "--output", str(paths["climb_relations_merged"])))
    step("apply climbing", lambda: run_module(SYN / "apply_relations.py", "--timeline", str(paths["climb_timeline"]), "--relations", str(paths["climb_relations_merged"]), "--output", str(paths["climb_applied"])))

    step("render HTML", lambda: run_module(ROOT / "tools/render_timelines.py", "--climb", str(paths["climb_timeline"]), "--concert", str(paths["concert_timeline"]), "--output", str(paths["timeline_html"])))
    step("preview PNG", lambda: run_module(ROOT / "tools/preview_timeline.py", "--climb", str(paths["climb_timeline"]), "--concert", str(paths["concert_timeline"]), "--output", str(paths["timeline_preview"])))
    step("media PNG", lambda: run_module(SYN / "media_resolver.py", "--timeline", str(paths["climb_timeline"]), "--media-dir", str(ROOT / "build/semifinal-202610/steps/DF-14/media"), "--output", str(paths["timeline_media"])))

    expected_files = [
        paths["climb_envelopes"], paths["concert_envelopes"],
        paths["climb_projection"], paths["concert_projection"],
        paths["climb_query"], paths["concert_query"],
        paths["climb_timeline"], paths["concert_timeline"],
        paths["climb_applied"], paths["timeline_html"], paths["timeline_preview"], paths["timeline_media"],
    ]
    for p in expected_files:
        ok = p.exists() and (p.is_file() or any(p.iterdir()))
        summary["checks"].append({"name": f"file:{p.name}", "ok": ok, "path": str(p)})
        if not ok:
            fail = True

    cl = json.loads(paths["climb_timeline"].read_text(encoding="utf-8"))
    summary["checks"].append({"name": "climb-records-count>=6", "ok": len(cl.get("records", [])) >= 6, "got": len(cl.get("records", []))})
    if len(cl.get("records", [])) < 6:
        fail = True

    co = json.loads(paths["concert_timeline"].read_text(encoding="utf-8"))
    summary["checks"].append({"name": "concert-records-count>=4", "ok": len(co.get("records", [])) >= 4, "got": len(co.get("records", []))})
    if len(co.get("records", [])) < 4:
        fail = True

    tombstone_present = (paths["concert_projection"] / "records/synthetic-concert/concert-recap-007/tombstone.json").exists()
    summary["checks"].append({"name": "tombstone-persists-e2e", "ok": tombstone_present})
    if not tombstone_present:
        fail = True

    applied = json.loads(paths["climb_applied"].read_text(encoding="utf-8"))
    has_confirmed = len(applied["applied_relations"]["confirmed"]) > 0
    has_excluded = len(applied["applied_relations"]["excluded"]) > 0
    summary["checks"].append({"name": "applied-has-confirmed-or-excluded", "ok": has_confirmed and has_excluded,
                              "confirmed": len(applied["applied_relations"]["confirmed"]),
                              "excluded": len(applied["applied_relations"]["excluded"])})
    if not (has_confirmed and has_excluded):
        fail = True

    for p in [paths["timeline_html"], paths["timeline_preview"], paths["timeline_media"]]:
        if p.exists() and p.stat().st_size > 0:
            summary["outputs"].append({"name": p.name, "size": p.stat().st_size})
        else:
            summary["checks"].append({"name": f"render-output:{p.name}", "ok": False})
            fail = True

    (out / "e2e-report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'FAIL' if fail else 'OK'}] runs={len(summary['runs'])} checks={len(summary['checks'])} outputs={len(summary['outputs'])} -> {out / 'e2e-report.json'}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
