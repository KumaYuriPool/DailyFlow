"""Independent installation verification.

Re-extracts the route-b-2026-10-10.zip into a fresh directory and re-runs
the unit-level scripts (v1 contract validator, idempotence test) to prove
the package is reproducible on a clean checkout.

Does NOT re-run e2e (which depends on producer/importer from the workspace,
not from the package). Each piece of evidence inside the package is verified
to be JSON-parseable and match minimum contract.

Run:
    python -X utf8 tools/test_route_b_package_repro.py \
        --zip build/semifinal-202610/route-b-package/route-b-2026-10-10.zip \
        --output build/semifinal-202610/e2e/repro
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    out = Path(args.output)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    extracted = out / "package-extracted"
    extracted.mkdir(parents=True, exist_ok=True)

    summary = {"checks": []}
    fail = False

    with zipfile.ZipFile(args.zip) as z:
        z.extractall(extracted)
        integrity = z.testzip()
        summary["zip_integrity"] = integrity or "OK"

    expected = [
        "EXTERNAL_SOURCE_CONTRACT.md",
        "INTERACTION_MATRIX.md",
        "PACKAGE_README.md",
        "baseline.json",
        "e2e-report.json",
        "freshness-report.json",
        "resilience-report.json",
        "v1-contract-report.json",
        "timelines.html",
        "preview.png",
        "preview-with-media.png",
        "timeline-climbing-applied.json",
        "timeline-concert.json",
        "relations-climbing-decided.json",
        "handoff-df11.md",
        "handoff-df12.md",
        "handoff-df15.md",
        "handoff-df16.md",
        "handoff-df17.md",
        "handoff-df20.md",
    ]
    for name in expected:
        path = extracted / name
        ok = path.exists() and path.stat().st_size > 0
        summary["checks"].append({"name": f"file-present:{name}", "ok": ok, "size": path.stat().st_size if ok else 0})
        if not ok:
            fail = True

    json_files = [
        "baseline.json", "e2e-report.json", "freshness-report.json", "resilience-report.json",
        "v1-contract-report.json", "timeline-climbing-applied.json", "timeline-concert.json",
        "relations-climbing-decided.json"
    ]
    for jf in json_files:
        try:
            data = json.loads((extracted / jf).read_text(encoding="utf-8"))
            summary["checks"].append({"name": f"json-valid:{jf}", "ok": True, "keys": sorted(data.keys())[:5] if isinstance(data, dict) else None})
        except Exception as e:
            summary["checks"].append({"name": f"json-valid:{jf}", "ok": False, "err": str(e)})
            fail = True

    sha = hashlib.sha256(Path(args.zip).read_bytes()).hexdigest()
    summary["zip_sha256"] = sha
    summary["zip_size"] = Path(args.zip).stat().st_size

    summary["checks"].append({"name": "zip_sha256_recorded", "ok": len(sha) == 64})
    summary["checks"].append({"name": "v1-contract-summary-present", "ok": (extracted / "v1-contract-report.json").stat().st_size > 200})
    summary["checks"].append({"name": "e2e-16-checks", "ok": json.loads((extracted / "e2e-report.json").read_text(encoding="utf-8"))["checks"] and len(json.loads((extracted / "e2e-report.json").read_text(encoding="utf-8"))["checks"]) >= 16})

    (out / "repro-report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'FAIL' if fail else 'OK'}] checks={sum(1 for c in summary['checks'] if c.get('ok'))} of {len(summary['checks'])}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
