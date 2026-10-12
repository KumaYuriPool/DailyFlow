"""One-command timeline re-import (audit R5): rerun the whole offline chain
from SOURCE and refresh the app's imported file, so a user (or a test) can
change a source, sync, and hit 刷新 in the app to see the new state.

Chain: producer -> importer -> query -> organizer -> export -> copy to data root.

Usage:
  python -X utf8 tools/sync_timeline_import.py --data-root <app-data-dir> [--out <workdir>]

With a running app, afterwards press 刷新 in the 时间流 view (or re-enter it);
the view reloads timeline-imported.json and the persisted exclusions from
timeline-decisions.json remain in effect (R2).
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYN = ROOT / "experiments/synthetic-source"


def run(*args):
    r = subprocess.run([sys.executable, "-X", "utf8", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{args[1]} failed: {r.stderr[-400:]}")
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True, help="app data root containing <app-id>/")
    ap.add_argument("--app-id", default="dailyflow")
    ap.add_argument("--out", default=str(ROOT / "build/semifinal-202610/synthetic-source"))
    ap.add_argument("--applied-climb", default="",
                    help="use an applied (user-decided) climbing timeline instead of the raw organizer output")
    ap.add_argument("--applied-concert", default="")
    args = ap.parse_args()
    out = Path(args.out)

    steps = []
    for scenario in ("climbing", "concert"):
        steps.append(run(str(SYN / "producer.py"), "--scenario", scenario, "--output", str(out / scenario)))
    for scenario in ("climbing", "concert"):
        steps.append(run(str(SYN / "importer.py"), "--scenario", scenario,
                         "--envelopes", str(out / scenario),
                         "--root", str(out / f"projection-{scenario}")))
    for scenario, topic, since in (("climbing", "bouldering", "2026-09-01"),
                                   ("concert", "concert", "2026-09-25")):
        steps.append(run(str(SYN / "dailyflow_query_v1.py"),
                         "--projection", str(out / f"projection-{scenario}"),
                         "--topics", topic, "--from", since, "--to", "2026-12-31",
                         "--query-id", f"sync-{scenario}",
                         "--output", str(out / f"query-{scenario}.json")))
    steps.append(run(str(SYN / "agent_selector.py"),
                     "--question", "我是怎么从刷到攀岩视频到开始练习的？",
                     "--catalog", str(SYN.parent / "experiments" / "synthetic-source" / "catalog.json")
                     if False else str(ROOT / "experiments/synthetic-source/catalog.json"),
                     "--query-id", "sync-climb", "--output", str(out / "selection-climb.json")))
    steps.append(run(str(SYN / "agent_selector.py"),
                     "--question", "把这次演出从期待到结束的经历串起来",
                     "--catalog", str(ROOT / "experiments/synthetic-source/catalog.json"),
                     "--query-id", "sync-concert", "--output", str(out / "selection-concert.json")))
    steps.append(run(str(SYN / "organizer.py"),
                     "--selection", str(out / "selection-climb.json"),
                     "--query-climb", str(out / "query-climbing.json"),
                     "--output", str(out / "timeline-climbing.json")))
    steps.append(run(str(SYN / "organizer.py"),
                     "--selection", str(out / "selection-concert.json"),
                     "--query-concert", str(out / "query-concert.json"),
                     "--output", str(out / "timeline-concert.json")))
    climb_src = args.applied_climb or str(out / "timeline-climbing.json")
    concert_src = args.applied_concert or str(out / "timeline-concert.json")
    steps.append(run(str(ROOT / "tools/export_timeline_for_app.py"),
                     "--timeline", climb_src,
                     "--timeline", concert_src,
                     "--output", str(out / "timeline-imported.json")))

    dst = Path(args.data_root).expanduser() / args.app_id / "timeline-imported.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out / "timeline-imported.json", dst)
    print(f"[OK] synced -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
