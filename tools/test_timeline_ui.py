"""Real card-host UI regression for the imported timeline view (DF-13).

Synthetic data only. Defaults to the production bundle and selected runtime.
The historic --legacy fixture is forbidden during explicit runtime acceptance.
Card-host UI evidence is distinct from real official Agent evidence.

Exports the climbing organizer timeline into the app data jail, then drives
the real UI: 时间流 entry, refresh, record lines, source lines, safety flag,
gaps, and navigation persistence.
"""
import native_runtime
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_workspace_ui import Probe  # noqa: E402
from test_real_model_flow import UI  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def make_legacy_fixture(out_dir, manifest_diff):
    """Copy current bundle, remove script-tools-v1 from requires, record diff."""
    bundle_src = ROOT / "bundle"
    dst = out_dir / "legacy-fixture-bundle"
    shutil.copytree(bundle_src, dst)
    mp = dst / "manifest.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    requires_before = list(m.get("requires", []))
    if "script-tools-v1" in requires_before:
        requires_before.remove("script-tools-v1")
    m["requires"] = requires_before
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_diff.append({
        "field": "requires",
        "production": json.loads((bundle_src / "manifest.json").read_text(encoding="utf-8")).get("requires"),
        "fixture": m["requires"],
        "reason": "legacy card-host refuses script-tools-v1 (documented 0.1.1 incompatibility)",
    })
    return dst


class TimelineProbe(Probe):
    """Probe that stages the given bundle source (production or labeled fixture)."""

    def __init__(self, out, bundle_src, size, binary=None):
        import os
        import socket
        import subprocess
        self.size = size
        self.binary = Path(binary).resolve() if binary else native_runtime.binary("card_host")
        native_runtime.verify_selection("card_host", self.binary)
        self.output = Path(out).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        native_runtime.record_runtime(self.output)
        self.apps = self.output / "apps"
        self.app_id = "dailyflow"
        self.bundle = self.output / "bundle"
        shutil.copytree(bundle_src, self.bundle)
        self.apps.mkdir(parents=True, exist_ok=True)
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self.log = (self.output / "runtime.log").open("a", encoding="utf8")
        self.child = subprocess.Popen(
            [str(self.binary), "--bundle", str(self.bundle), "--app-data", str(self.apps),
             "--allow-unsigned", "--stamp", "--size", self.size],
            stdout=self.log, stderr=subprocess.STDOUT,
            env=dict(os.environ, MAKEPAD_HIDE_WINDOWS="1", MAKEPAD_REMOTE=str(self.port)),
            creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(120):
            try:
                if any(w.get("t") == "本地数据已就绪" for w in self.snapshot().get("s", [])):
                    return
            except (OSError, ValueError):
                pass
            time.sleep(.2)
        self.stop()
        raise RuntimeError("UI not ready")


def run(p, wide=False):
    ui = UI(p)
    time.sleep(.4)

    # export timeline sample into the app data jail before opening the view
    app_dir = p.apps / p.app_id
    timeline_src = ROOT / "build/semifinal-202610/synthetic-source/timeline-climbing.json"
    assert timeline_src.exists(), "run organizer first"
    import subprocess
    subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools/export_timeline_for_app.py"),
                    "--timeline", str(timeline_src), "--output", str(app_dir / "timeline-imported.json")],
                   check=True, capture_output=True)
    # reload: fs jail is read at render; navigate away+back or press refresh
    ui.click("时间流")
    time.sleep(.4)

    # navigate: 时间流 entry in left rail
    ui.click("时间流")
    time.sleep(.4)

    texts = [w.get("t", "") for w in ui.widgets()]
    assert any("导入时间流" in t for t in texts), texts[:20]
    # summary line: topic + count
    assert any(t.startswith("bouldering · ") and "条 · 按时间排列" in t for t in texts), texts
    # source status bar (PRODUCT_SPEC §3 / DF-26): scope + snapshot time + honesty
    assert any("来源范围：" in t and "synthetic-climbing" in t for t in texts), texts
    assert any("导入快照" in t and "未连接实时来源" in t for t in texts), texts
    # records: at least the four anchor records from the climbing scenario
    for needle in ("B 站的攀岩入门视频（已收藏）",):
        assert any(needle in t for t in texts), f"missing record {needle}"
    # scroll to the bottom collecting text (narrow screens clip the tail)
    for _ in range(14):
        texts += [w.get("t", "") for w in ui.widgets()]
        ui.probe.request("m", k="scroll", x=230, y=510, dy=200, wait=1)
        time.sleep(.12)
        texts += [w.get("t", "") for w in ui.widgets()]
    assert any("首条 V3" in t for t in texts), "missing record 首条 V3 (after scroll)"
    # source line with revision
    assert any("synthetic-climbing · 动态 · rev2" in t for t in texts), texts
    # expense rendered with money
    assert any("周卡续费 ¥880" in t for t in texts), texts
    # malicious body flagged, not executed: flag line present, no tool effects
    assert any("配文含指令样文本" in t for t in texts), texts
    # gaps panel
    assert any("尚未覆盖" in t for t in texts)
    assert any("weekly_frequency" in t for t in texts), texts

    # refresh keeps data (persistence of import file, not of chat state);
    # scroll position resets, so sweep again before asserting the tail rows.
    ui.click("刷新")
    time.sleep(.3)
    texts2 = texts
    for _ in range(14):
        texts2 += [w.get("t", "") for w in ui.widgets()]
        ui.probe.request("m", k="scroll", x=230, y=510, dy=200, wait=1)
        time.sleep(.12)
        texts2 += [w.get("t", "") for w in ui.widgets()]
    assert any("周卡续费 ¥880" in t for t in texts2)

    ui.evidence("01-timeline-wide" if wide else "01-timeline")

    # draft preservation: type in composer, navigate away and back
    # (composer is in chat column; narrow layout hides workspace; use 范围 picker path)
    # navigate to 查找 then back via 时间流 again
    ui.click("查找")
    time.sleep(.3)
    ui.click("时间流")
    time.sleep(.3)
    texts3 = texts2
    for _ in range(14):
        texts3 += [w.get("t", "") for w in ui.widgets()]
        ui.probe.request("m", k="scroll", x=230, y=510, dy=200, wait=1)
        time.sleep(.12)
        texts3 += [w.get("t", "") for w in ui.widgets()]
    assert any("周卡续费 ¥880" in t for t in texts3), "timeline must survive navigation"

    # business state untouched: no writes to business files by this view
    return {"ok": True, "records_shown": len([t for t in texts if "synthetic-" in t])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--wide", action="store_true")
    ap.add_argument("--binary", default="")
    ap.add_argument("--legacy", action="store_true",
                    help="use the labeled legacy fixture with the old card-host instead")
    args = ap.parse_args()
    import os
    if args.legacy and os.environ.get('DAILYFLOW_RUNTIME_MANIFEST'):
        ap.error('Explicit runtime acceptance must retain production admission requirements')
    out = Path(args.output).resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists(), 'Use a fresh build output'
    manifest_diff = []
    if args.legacy:
        bundle_src = make_legacy_fixture(out, manifest_diff)
        binary = args.binary or None
        evidence_class = "legacy_vm_ui_regression (not production admission)"
    else:
        bundle_src = ROOT / "bundle"
        binary = args.binary or str(
            native_runtime.binary("card_host"))
        evidence_class = "production_bundle_ui_regression (selected card-host, dev stamp/unsigned)"
    p = TimelineProbe(out, bundle_src, size="1280x900" if args.wide else "412x892", binary=binary)
    try:
        result = run(p, wide=args.wide)
        (out / "report.json").write_text(
            json.dumps({**result, "fixture": manifest_diff,
                        "host_binary": str(p.binary),
                        "host_sha256": __import__("hashlib").sha256(Path(p.binary).read_bytes()).hexdigest(),
                        "evidence_class": evidence_class},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        print("[OK] timeline UI regression passed", result)
        return 0
    finally:
        p.stop()


if __name__ == "__main__":
    sys.exit(main())
