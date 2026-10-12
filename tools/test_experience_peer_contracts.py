"""Native Splash peer-adapter fault probes, NOT official Agent/Provider evidence.

Copies the current production bundle and injects assertions. Only octos.turn.start
and interrupt are replaced by a local transport recorder; all adapter/context/
callback validation is the production implementation. Uses private app data.
"""
import native_runtime
import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_timeline_ui import TimelineProbe

ROOT = Path(__file__).resolve().parents[1]
BINARY = native_runtime.binary("card_host")

PROBE = r'''
let pc_checks = []
let pc_calls = 0
let pc_result = nil
let pc_requests = []
let pc_stops = 0
fn pc_check(name,value){
    pc_checks.push({name: name "passed": value})
    fs.write("experience-peer-contract-report.json",pc_checks.to_json())
}
fn pc_callback(r){ pc_calls += 1 pc_result = r }
fn pc_start(args,callback){ pc_requests.push(args) }
fn pc_interrupt(args,callback){ pc_stops += 1 }
fn pc_setup(ticket){
    ex_id = "peer-test" ex_query_revision = 3 ex_serial = 30 ex_busy = true
    ex_request = ticket ex_peer_ticket = ticket ex_peer_owner = ex_context()
    ex_peer_serial = ex_serial ex_peer_pending = true ex_peer_read = false
    ex_peer_attempt = 0 ex_peer_prompt = "contract probe"
    ex_peer_output = nil ex_peer_submissions = 0
    ex_peer_input = {catalog: ["allowed-source"] marker: ticket}
    pc_calls = 0 pc_result = nil ex_events = []
}
fn pc_reply(turn,text){ return {is_ok: true data: {turn_id: turn text: text} error: ""} }
fn pc_plan(){ return {intent: "query" topic: "bouldering" start: "" end: "" sources: ["allowed-source"] question: ""} }
fn pc_submit(){ return ex_peer_result({request_id: ex_peer_ticket plan: pc_plan()}) }
fn pc_finish(r){ ex_peer_finish(ex_peer_ticket,ex_serial,ex_context(),r,|v| pc_callback(v)) }
fn pc_broken(r,name){
    pc_setup("broken-envelope") ex_peer_context({request_id: "broken-envelope"})
    pc_submit()
    pc_finish(r)
    pc_check(name,pc_calls == 1 && !pc_result.is_ok)
}
fn pc_probe(){
    let before = db.to_json()
    timeline_data = PC_RECORDS.parse_json() timeline_error = ""
    ex_store = "{\"version\":1,\"seq\":0,\"items\":[],\"decisions\":[],\"disabled\":[]}".parse_json()
    ex_topic = "bouldering" ex_start = "" ex_end = "" ex_sources = []
    ex_reason_snapshot = []
    for item in ex_visible() { ex_reason_snapshot.push({ref: ex_reason_ref(item) title: item.title body: item.body}) }
    ex_adapter = "official" ex_peer_turns = []
    pc_setup("a")
    let r = ex_peer_context({request_id: "expired"})
    pc_check("expired-ticket-tool-denied",!r["ok"] && !ex_peer_read)
    ex_peer_serial = 29 r = ex_peer_context({request_id: "a"})
    pc_check("mismatched-serial-tool-denied",!r["ok"] && !ex_peer_read)
    ex_peer_serial = 30 ex_peer_owner = "different"
    r = ex_peer_context({request_id: "a"})
    pc_check("mismatched-owner-tool-denied",!r["ok"] && !ex_peer_read)
    ex_peer_owner = ex_context() ex_busy = false
    r = ex_peer_context({request_id: "a"})
    pc_check("inactive-task-tool-denied",!r["ok"] && !ex_peer_read)
    ex_busy = true ex_peer_pending = false r = ex_peer_context({request_id: "a"})
    pc_check("ended-task-tool-denied",!r["ok"] && !ex_peer_read)
    pc_setup("a") r = ex_peer_context({request_id: "a"})
    pc_check("current-task-only-bounded-context",r["ok"] && ex_peer_read && r.context.marker == "a" && r.query_revision == 3 && r.experience_id == "peer-test")
    ex_peer_finish("expired",30,"peer-test",nil,|v| pc_callback(v))
    pc_check("expired-finish-ignored",pc_calls == 0 && ex_peer_pending)
    ex_peer_finish("a",29,"peer-test",nil,|v| pc_callback(v))
    pc_check("old-serial-finish-ignored",pc_calls == 0 && ex_peer_pending)
    ex_peer_finish("a",30,"other",nil,|v| pc_callback(v))
    pc_check("other-owner-finish-ignored",pc_calls == 0 && ex_peer_pending)
    ex_cancel()
    ex_peer_finish("a",30,"peer-test",nil,|v| pc_callback(v))
    pc_check("cancel-clears-context-and-late-result",!ex_peer_pending && !ex_busy && ex_peer_input == nil && pc_calls == 0 && pc_stops == 1)
    r = ex_peer_context({request_id: "a"})
    pc_check("cancelled-context-not-readable",!r["ok"])
    r = ex_peer_result({request_id: "a" plan: pc_plan()})
    pc_check("cancelled-result-not-submitted",!r["ok"] && ex_peer_output == nil)
    pc_setup("submit-guards")
    r = pc_submit()
    pc_check("submission-requires-context-read",!r["ok"] && ex_peer_output == nil)
    ex_peer_context({request_id: "submit-guards"})
    r = ex_peer_result({request_id: "expired" plan: pc_plan()})
    pc_check("expired-result-tool-denied",!r["ok"] && ex_peer_output == nil)
    ex_peer_serial = 29 r = pc_submit()
    pc_check("result-mismatched-serial-denied",!r["ok"] && ex_peer_output == nil)
    ex_peer_serial = 30 ex_peer_owner = "other" r = pc_submit()
    pc_check("result-mismatched-owner-denied",!r["ok"] && ex_peer_output == nil)
    pc_setup("no-tool")
    ex_peer_attempt = 1
    pc_finish(pc_reply("turn-no-tool","{\"intent\":\"query\"}"))
    pc_check("unread-context-cannot-succeed",pc_calls == 1 && !pc_result.is_ok && ex_peer_turns.len() == 0)
    pc_setup("repair-read")
    pc_finish(pc_reply("turn-unread-1","{\"intent\":\"query\"}"))
    pc_check("missing-read-repairs-once-with-new-turn",pc_calls == 0 && pc_requests.len() == 1 && ex_peer_attempt == 1 && ex_peer_pending && ex_peer_input.marker == "repair-read" && ex_peer_ticket == "repair-read")
    pc_finish(pc_reply("turn-unread-2","{\"intent\":\"query\"}"))
    pc_check("second-missing-read-terminates-without-third-turn",pc_calls == 1 && !pc_result.is_ok && pc_requests.len() == 1 && !ex_peer_pending && ex_peer_input == nil && ex_peer_turns.len() == 0)
    pc_requests = []
    for malformed in ["{bad" "{\"intent\":\"query\"}" "[]" "42" "\"string\""] {
        pc_setup("malformed") ex_peer_context({request_id: "malformed"})
        ex_peer_attempt = 1
        pc_finish(pc_reply("turn-malformed",malformed))
        pc_check("free-text-cannot-replace-result-tool: " + malformed,pc_calls == 1 && !pc_result.is_ok)
    }
    pc_setup("missing-turn") ex_peer_context({request_id: "missing-turn"})
    pc_submit()
    pc_finish(pc_reply("","{\"intent\":\"query\"}"))
    pc_check("missing-turn-id-rejected",pc_calls == 1 && !pc_result.is_ok)
    pc_setup("failed")
    pc_finish({is_ok: false error: "transport failure"})
    pc_check("host-failure-forwarded-without-retry",pc_calls == 1 && !pc_result.is_ok && pc_result.error == "transport failure" && pc_requests.len() == 0)
    pc_broken(nil,"nil-host-envelope-fails-cleanly")
    pc_broken({},"empty-host-envelope-fails-cleanly")
    pc_broken({is_ok: true},"missing-data-envelope-fails-cleanly")
    pc_broken({is_ok: true data: {turn_id: 42 text: "{}"}},"nonstring-turn-envelope-fails-cleanly")
    pc_setup("success") ex_peer_context({request_id: "success"})
    r = pc_submit()
    pc_check("valid-plan-submit-waits-for-host-completion",r["ok"] && pc_calls == 0 && ex_peer_pending && ex_peer_output.topic == "bouldering")
    r = ex_peer_result({request_id: "success" plan: {intent: "clarify" question: "replace accepted"}})
    pc_check("duplicate-result-is-idempotent-no-overwrite",r["ok"] && ex_peer_output.intent == "query" && ex_peer_submissions == 1)
    pc_finish(pc_reply("turn-1","This is ordinary final text, deliberately not JSON."))
    pc_check("actual-host-envelope-adapted",pc_calls == 1 && pc_result.is_ok && pc_result.data.output.topic == "bouldering" && !ex_peer_pending && ex_peer_input == nil)
    let receipts = ex_peer_turns.len()
    pc_finish(pc_reply("turn-1","{\"intent\":\"query\"}"))
    pc_check("duplicate-completion-ignored",pc_calls == 1 && ex_peer_turns.len() == receipts)
    pc_setup("bad-source") ex_peer_context({request_id: "bad-source"})
    let badplan = pc_plan() badplan.sources = ["not-authorized"]
    r = ex_peer_result({request_id: "bad-source" plan: badplan})
    pc_check("unauthorized-plan-source-rejected",!r["ok"] && ex_peer_output == nil)
    r = ex_peer_result({request_id: "bad-source" plan: badplan})
    let third = pc_submit()
    pc_check("two-invalid-submissions-cap-even-valid-third",!r["ok"] && !third["ok"] && ex_peer_output == nil)
    pc_finish(pc_reply("turn-invalid-limit","done"))
    pc_check("invalid-submission-limit-does-not-trigger-repair",pc_calls == 1 && !pc_result.is_ok && pc_requests.len() == 0)
    let org = PC_ORGANIZATION.parse_json()
    pc_setup("organization") ex_peer_input.phase = "organize" ex_peer_context({request_id: "organization"})
    r = ex_peer_result({request_id: "organization" organization: org})
    pc_check("valid-organization-submission-awaits-finish",r["ok"] && pc_calls == 0 && ex_peer_output.edges.len() == 1)
    pc_finish(pc_reply("turn-org","整理完成"))
    pc_check("organization-returned-only-after-host-completes",pc_calls == 1 && pc_result.is_ok && pc_result.data.output.edges.len() == 1)
    pc_setup("stale-revision") ex_peer_input.phase = "organize" ex_peer_context({request_id: "stale-revision"})
    let badorg = org.to_json().parse_json() badorg.edges[0].from.revision = 90
    r = ex_peer_result({request_id: "stale-revision" organization: badorg})
    pc_check("organization-wrong-source-revision-rejected",!r["ok"] && ex_peer_output == nil)
    badorg = org.to_json().parse_json() badorg.edges[0].from.quote = "invented citation"
    r = ex_peer_result({request_id: "stale-revision" organization: badorg})
    pc_check("organization-invented-citation-rejected",!r["ok"] && ex_peer_output == nil)
    pc_setup("new-request") ex_peer_pending = false
    ex_run_assistant("test",{marker: "new"},{type: "object"},30,"peer-test",|v| pc_callback(v))
    let ticket1 = ex_peer_ticket
    ex_peer_context({request_id: ticket1})
    pc_submit()
    pc_finish(pc_reply("turn-2","{\"intent\":\"query\"}"))
    ex_run_assistant("another",{marker: "another"},{type: "object"},30,"peer-test",|v| pc_callback(v))
    let ticket2 = ex_peer_ticket
    pc_check("every-new-task-dispatches-new-turn",pc_requests.len() == 2 && ticket1 != ticket2 && pc_requests[0].trigger == "person" && pc_requests[1].trigger == "person")
    ex_peer_context({request_id: ticket2})
    pc_submit()
    pc_finish(pc_reply("turn-3","{\"intent\":\"query\"}"))
    pc_check("different-turns-recorded",ex_peer_turns[ex_peer_turns.len()-2].turn_id == "turn-2" && ex_peer_turns[ex_peer_turns.len()-1].turn_id == "turn-3")
    let large = "abcdefghij" while large.len() <= 180000 { large = large + large }
    pc_setup("large-input") ex_peer_pending = false
    ex_run_assistant("test",{data: large},{type: "object"},30,"peer-test",|v| pc_callback(v))
    pc_check("oversized-context-not-dispatched",pc_calls == 1 && !pc_result.is_ok && !ex_peer_pending && pc_requests.len() == 2)
    pc_setup("large-prompt") ex_peer_pending = false
    ex_run_assistant(large,{}, {type: "object"},30,"peer-test",|v| pc_callback(v))
    pc_check("oversized-prompt-clears-context-not-dispatched",pc_calls == 1 && !pc_result.is_ok && !ex_peer_pending && ex_peer_input == nil && pc_requests.len() == 2)
    pc_check("original-business-state-unchanged",db.to_json() == before)
    fs.write("experience-peer-contract-complete.json",{checks: pc_checks.len()}.to_json())
}
start_timeout(1.0,|| pc_probe())
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = Path(args.output).resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists(), 'Use a fresh build directory'
    out.mkdir(parents=True)
    fixture = out / 'helper-fixture'
    shutil.copytree(ROOT / 'bundle', fixture)
    main_file = fixture / 'main.splash'
    source = main_file.read_text(encoding='utf-8')
    production_sha = hashlib.sha256(main_file.read_bytes()).hexdigest()
    start = 'host.request("octos.turn.start",'
    interrupt = 'host.request("octos.turn.interrupt",{},'
    assert source.count(start) == 2 and source.count(interrupt) == 1
    assert source.count('start_timeout(0.08,|| boot())') == 1
    record = dict(topic='bouldering', date='2026-10-01', source_app='allowed-source', source_module='post', record_id='first', revision=1,
                  kind='post', amount_minor=0, currency='', excluded=False, future=False,
                  title='第一次攀岩', body='计划继续练习。', citation='fixture', tags=[], suspicious=False)
    records = [record, {**record, 'record_id': 'second', 'title': '第二次攀岩', 'date': '2026-10-02'}]
    def ref(row):
        return {k: row[k] for k in ('source_app', 'source_module', 'record_id', 'revision')} | {'quote': row['title']}
    organization = dict(claims=[dict(text='记录描述了两次攀岩。', evidence=[ref(records[0]), ref(records[1])])],
                        edges=[dict(kind='same_experience', title='攀岩练习', reason='两次攀岩记录，是否相关待本人核对。',
                                    **{'from': ref(records[0]), 'to': ref(records[1])})])
    probe = PROBE.replace('PC_RECORDS', json.dumps(json.dumps({'records': records, 'sources': [], 'gaps': []}), ensure_ascii=False))
    probe = probe.replace('PC_ORGANIZATION', json.dumps(json.dumps(organization), ensure_ascii=False))
    injected = source.replace(start, 'pc_start(').replace(interrupt, 'pc_interrupt({},')
    injected = injected.replace('start_timeout(0.08,|| boot())', probe + '\nstart_timeout(0.08,|| boot())')
    main_file.write_text(injected, encoding='utf-8')
    provenance = {
        'evidence_class': 'injected Splash helper faults with transport recorder; NOT real official Agent/Provider/consent evidence',
        'production_main_sha256': production_sha,
        'injected_main_sha256': hashlib.sha256(main_file.read_bytes()).hexdigest(),
        'binary_sha256': hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        'fixture_changes': ['inject contract probe', 'replace octos.turn.start and interrupt transport calls with recorder'],
    }
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    p = TimelineProbe(out / 'runtime', fixture, '1280x900', binary=BINARY)
    try:
        folder = p.apps / p.app_id
        report_file = folder / 'experience-peer-contract-report.json'
        complete = folder / 'experience-peer-contract-complete.json'
        for _ in range(65):
            if complete.exists():
                break
            time.sleep(.2)
        checks = json.loads(report_file.read_text(encoding='utf-8')) if report_file.exists() else []
        result = dict(provenance, completed=complete.exists(), checks=checks)
        (out / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False))
        assert complete.exists(), 'Injected probe did not finish; inspect runtime log and partial report'
        assert checks and all(c['passed'] for c in checks)
    finally:
        p.stop()


if __name__ == '__main__':
    main()
