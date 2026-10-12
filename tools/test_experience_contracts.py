"""Fault injection into actual Splash helpers; NOT real model/consent evidence."""
import native_runtime
import argparse,json,shutil,sys,time,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_timeline_ui import TimelineProbe
ROOT=Path(__file__).resolve().parents[1]

def main():
    a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args()
    out=Path(args.output).resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True);fixture=out/'helper-fixture';shutil.copytree(ROOT/'bundle',fixture)
    record={'topic':'t','date':'2026-10-01','source_app':'a','source_module':'post','record_id':'same','revision':1,'kind':'expense','amount_minor':1200,'currency':'CNY','excluded':False,'future':False,'title':'test','body':'untrusted','citation':'fixture','tags':[],'suspicious':False}
    records=[record,{**record,'source_app':'b'},{**record,'source_module':'other'}]
    injected='''
fn ex_contract_probe(){
    let checks = []
    timeline_data = PAYLOAD.parse_json()
    ex_store = "{\\"version\\":1,\\"seq\\":0,\\"items\\":[],\\"decisions\\":[],\\"disabled\\":[]}".parse_json()
    ex_topic = "t" ex_id = "test-1" ex_start = "" ex_end = "" ex_sources = []
    let r = timeline_data.records[0]
    ex_decide(r,"membership","exclude")
    checks.push({name: "full-source-identity" ok: ex_visible().len() == 2})
    ex_id = "test-2"
    checks.push({name: "experience-isolation" ok: ex_visible().len() == 3})
    ex_id = "test-1" ex_undo()
    checks.push({name: "undo-membership" ok: ex_visible().len() == 3})
    ex_decide(r,"expense","confirm")
    checks.push({name: "confirm-exact-expense" ok: ex_confirmed(r) && !ex_confirmed(timeline_data.records[1]) && !ex_confirmed(timeline_data.records[2])})
    r.revision = 2
    checks.push({name: "changed-revision-needs-confirmation" ok: !ex_confirmed(r)})
    ex_state = "idle" ex_serial = 9 ex_busy = true
    ex_receive(8,"test-1",nil)
    checks.push({name: "late-request-rejected" ok: ex_state == "idle" && ex_busy})
    ex_receive(9,"other-owner",nil)
    checks.push({name: "switched-experience-rejected" ok: ex_state == "idle" && ex_busy})
    ex_cancel() ex_receive(9,"test-1",nil)
    checks.push({name: "cancelled-callback-rejected" ok: ex_state == "cancelled" && !ex_busy})
    let plan = {topic: "t" start: "" end: "" sources: ["evil-source"]}
    checks.push({name: "source-whitelist" ok: !ex_plan_valid(plan)})
    plan.sources = ["a"] plan.start = "2026-02-31"
    checks.push({name: "invalid-date-rejected" ok: !ex_plan_valid(plan)})
    ex_detail = ex_key(r) ex_store.disabled = ["a"]
    checks.push({name: "disabled-source-hidden" ok: ex_visible().len() == 1 && ex_detail_record() == nil})
    ex_store.disabled = [] ex_id = "" ex_query_revision = 42
    ex_decide(r,"expense","confirm") ex_save()
    checks.push({name: "save-retains-temporary-decisions" ok: ex_id != "" && ex_confirmed(r)})
    fs.write("timeline-imported.json",timeline_data.to_json())
    ex_serial = 11 ex_busy = true
    let reply = "{\\"is_ok\\":true,\\"data\\":{\\"output\\":{\\"intent\\":\\"query\\",\\"topic\\":\\"t\\",\\"start\\":\\"\\",\\"end\\":\\"\\",\\"sources\\":[\\"a\\"],\\"question\\":\\"\\"}}}".parse_json()
    ex_receive(11,ex_context(),reply)
    checks.push({name: "actual-host-envelope-decoded" ok: ex_topic == "t" && ex_snapshot.len() == 2})
    ex_start = "2026-10-02"
    checks.push({name: "date-range-filters-records" ok: ex_records().len() == 0})
    ex_start = "2026-10-01" ex_end = "2026-10-01"
    checks.push({name: "date-range-inclusive-both-ends" ok: ex_records().len() == 2})
    let reversed = {topic: "t" start: "2026-10-02" end: "2026-10-01" sources: ["a"]}
    checks.push({name: "reversed-date-range-rejected" ok: !ex_plan_valid(reversed)})
    ex_end = ""
    ex_start = "" timeline_data.records[0].currency = ""
    checks.push({name: "unknown-currency-not-added" ok: ex_money_line().search("缺少币种或金额") >= 0})
    fs.write("experiences-v1.json","{bad") ex_store = nil ex_load()
    checks.push({name: "corrupt-store-readonly" ok: ex_store_error && !ex_commit(ex_store) && fs.read("experiences-v1.json") == "{bad"})
    for corrupt in ["{\\"version\\":1}" "{\\"version\\":1,\\"seq\\":0,\\"items\\":\\"bad\\",\\"decisions\\":[],\\"disabled\\":[]}"] {
        fs.write("experiences-v1.json",corrupt) ex_store = nil ex_store_error = false ex_load()
        checks.push({name: "invalid-store-fields-readonly" ok: ex_store_error && !ex_commit(ex_store) && fs.read("experiences-v1.json") == corrupt})
    }
    fs.write("experience-contract-report.json",checks.to_json())
}
start_timeout(1.0,|| ex_contract_probe())
'''.replace(' ok:', ' "passed":').replace('PAYLOAD',json.dumps(json.dumps({'records':records,'sources':[],'gaps':[]}),ensure_ascii=False))
    path=fixture/'main.splash'
    source=path.read_text(encoding='utf-8')
    # This suite checks coordinator helpers, never starts a Provider/peer.
    source=source.replace('fn ex_run_assistant(', 'fn ex_contract_unused_transport(')
    injected='fn ex_run_assistant(task,input,schema,serial,owner,callback){}\n'+injected
    path.write_text(source.replace('start_timeout(0.08,|| boot())',injected+'\nstart_timeout(0.08,|| boot())'),encoding='utf-8')
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    p=TimelineProbe(out/'runtime',fixture,'1280x900',binary=native_runtime.binary("card_host"))
    try:
        report=p.apps/p.app_id/'experience-contract-report.json'
        for _ in range(50):
            if report.exists():break
            time.sleep(.2)
        checks=json.loads(report.read_text(encoding='utf-8'))
        (out/'report.json').write_text(json.dumps({'evidence_class':'injected helper faults, not Provider calls','checks':checks},indent=2),encoding='utf-8')
        print(json.dumps(checks,ensure_ascii=False))
        assert all(c['passed'] for c in checks)
    finally:p.stop()

if __name__=='__main__':main()
