"""Test the RC2 application hook in a real legacy Splash VM with fake RC2 APIs.

The fake API models token ownership/liveness only. This does NOT verify the
official runner, admission, approval UI, peer delegation or Provider execution.
No UI/model process is started unless --run is supplied. All builds and state
stay under a new --output directory; the production bundle is never rewritten.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import build_event_app as builder
import business_test_driver as driver

ROOT = Path(__file__).resolve().parents[1]
CASES = ("roundtrip", "cancelled", "missing-request", "unknown-tool", "replay", "stale", "query", "exception")
HOOK = 'if name == "dailyflow.query" { tools.resolve(token,business_query(a)) return }'
HARNESS = r'''
let bridge_test_requests = {}
let bridge_test_live = {}
let bridge_test_replies = []
fn bridge_test_active(token){ return bridge_test_live[token] == true }
fn bridge_test_request(token){ return bridge_test_requests[token] }
fn bridge_test_complete(token,result){
    bridge_test_replies.push({token: token transport_ok: true data: result})
    bridge_test_live[token] = false return true
}
fn bridge_test_fail(token,error){
    bridge_test_replies.push({token: token transport_ok: false error: error})
    bridge_test_live[token] = false return true
}
fn bridge_test_enqueue(token,name,args){
    bridge_test_live[token] = true
    bridge_test_requests[token] = {args: args context: {app: "dailyflow" account: "synthetic" caller: "test" call_id: token}}
    app_tool(name,token)
}
fn bridge_test_call(token,name,args){ bridge_test_enqueue(token,name,args) business_drain_tools() }
fn bridge_test_suite(which){
    let before = db.revision let checks = []
    let write = {request_id: "bridge-creation" kind: "expense" title: "合成洗护费" date: today() amount: "120" event_title: "合成洗护"}
    if which == "cancelled" {
        bridge_test_enqueue("cancel","dailyflow.apply",write)
        bridge_test_live["cancel"] = false business_drain_tools()
        checks.push({name: "cancel-before-drain-never-executes" pass: db.revision == before && bridge_test_replies.len() == 0})
    }
    if which == "missing-request" {
        bridge_test_enqueue("missing","dailyflow.apply",write)
        bridge_test_requests["missing"] = nil business_drain_tools()
        checks.push({name: "missing-host-request-fails-without-write" pass: db.revision == before && bridge_test_replies.len() == 1 && !bridge_test_replies[0].transport_ok})
    }
    if which == "unknown-tool" {
        bridge_test_call("unknown","dailyflow.not_declared",{})
        checks.push({name: "unknown-tool-transport-failure" pass: db.revision == before && bridge_test_replies.len() == 1 && !bridge_test_replies[0].transport_ok})
    }
    if which == "roundtrip" {
        bridge_test_call("write","dailyflow.apply",write)
        bridge_test_call("read","dailyflow.query",{})
        let result = bridge_test_replies[0] let query = bridge_test_replies[1]
        checks.push({name: "official-args-reach-real-transaction" pass: result.token == "write" && result.transport_ok && result.data["ok"]})
        checks.push({name: "readback-reports-real-source-data" pass: query.token == "read" && query.transport_ok && query.data.total == 2 && expense_snapshot(db)[0].amount_minor == 12000})
        checks.push({name: "one-completion-per-call" pass: bridge_test_replies.len() == 2})
    }
    if which == "replay" {
        bridge_test_call("first","dailyflow.apply",write) let saved = db.revision
        bridge_test_call("retry","dailyflow.apply",write)
        checks.push({name: "receipt-replay-remains-idempotent" pass: bridge_test_replies[1].data.replayed && db.revision == saved && expense_snapshot(db).len() == 1})
    }
    if which == "stale" {
        bridge_test_call("first","dailyflow.apply",write)
        let record = expense_snapshot(db)[0] let saved = db.revision
        bridge_test_call("stale","dailyflow.apply",{request_id: "bridge-stale" record_id: record.id expected_revision: record.revision + 1 kind: "expense" title: "不能改" date: today() amount: "999"})
        checks.push({name: "business-rejection-is-structured-not-transport-success-claim" pass: bridge_test_replies[1].transport_ok && !bridge_test_replies[1].data["ok"] && db.revision == saved})
    }
    if which == "query" {
        bridge_test_call("caps","dailyflow.capabilities",{})
        bridge_test_call("empty","dailyflow.query",{})
        checks.push({name: "read-only-capabilities-and-empty-query" pass: bridge_test_replies[0].data["ok"] && bridge_test_replies[1].data.total == 0 && db.revision == before})
    }
    if which == "exception" {
        bridge_test_call("bad","dailyflow.query",{limit: "invalid"})
        checks.push({name: "bad-input-does-not-write" pass: bridge_test_replies.len() == 1 && bridge_test_replies[0].transport_ok && !bridge_test_replies[0].data["ok"] && db.revision == before})
    }
    return {"ok": true checks: checks replies: bridge_test_replies}
}
'''


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    source_root = output / "source-build"
    shutil.copytree(ROOT / "src", source_root / "src")
    shutil.copytree(ROOT / "bundle", source_root / "bundle")
    (source_root / "docs").mkdir()
    original_root = builder.ROOT
    try:
        builder.ROOT = source_root
        builder.build()
    finally:
        builder.ROOT = original_root
    file = source_root / "bundle/main.splash"
    source = file.read_text(encoding="utf-8")
    assert source.count(HOOK) == 1, "Business dispatch test insertion point changed"
    assert source.count("fn app_tool(name,call_id)") == 1
    sha = hashlib.sha256(source.encode()).hexdigest()
    for api in ("active", "request", "complete", "fail"):
        source = source.replace(f"mod.app_tools.{api}(", f"bridge_test_{api}(")
    # The official inner query must still invoke the production query. Avoid
    # recursion: only outer fixture requests have a non-empty record_id.
    source = source.replace(HOOK,
                            'if name == "dailyflow.query" { if business_optional(a,"record_id","") != "" { tools.resolve(token,bridge_test_suite(a.record_id)) return } tools.resolve(token,business_query(a)) return }')
    anchor = "start_timeout(0.08,|| boot())"
    assert source.count(anchor) == 1
    source = source.replace(anchor, HARNESS + "\n" + anchor)
    file.write_text(source, encoding="utf-8")
    metadata = {"prepared": True, "source_sha256_before_injection": sha, "mode": "real Splash with injected RC2 API", "official_host_verified": False, "cases": CASES}
    (output / "preparation.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return source_root / "bundle"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run", action="store_true", help="Start isolated hidden legacy card-host to execute fixture")
    parser.add_argument("--binary", type=Path, default=ROOT.parent / "OctoSense-App-Hub/target/release/card-host.exe")
    args = parser.parse_args()
    output = args.output.resolve()
    bundle = prepare(output)
    if not args.run:
        print(json.dumps({"prepared": str(bundle), "executed": False}))
        return
    driver.configure(bundle, output / "execution", args.binary, legacy_vm_fixture=True)
    checks = []
    for case in CASES:
        result = driver.run(case, [driver.query(record_id=case)])[0]
        assert result["ok"], result
        report = result["data"]
        assert report["ok"] and report["checks"], report
        checks.extend(report["checks"])
        assert all(check["pass"] for check in report["checks"]), report
    report = {"passed": True, "mode": "real legacy Splash with injected RC2 API and explicit manifest fixture", "official_host_verified": False, "legacy_vm_fixture": driver.fixture_metadata(), "checks": checks}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
