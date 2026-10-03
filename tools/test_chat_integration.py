"""SIMULATED model replies + REAL integrated business_save/persistence in Splash.
Copies the selected bundle; never edits it or the production bundle.
No real Provider is used in this deterministic regression test.
"""
import argparse, json, os, shutil, socket, subprocess, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bundle',type=Path,default=ROOT/'bundle')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--binary',type=Path,default=ROOT.parent/'OctoSense-App-Hub/target/release/card-host.exe')
args=parser.parse_args()
OUT=args.output.resolve()
OUT.mkdir(parents=True,exist_ok=False)
HARNESS=r'''
// TEST ONLY: inject model replies, real business_save remains unmodified.
fn test_integration(){
    let results = [] screen = "calendar"
    let good = {kind: "expense" title: "猫粮" date: today() amount: "45" time: "" end_date: "" source: "" flow_names: ["宠物照护"] user_tags: [] question: ""}
    chat_text = "今天买猫粮，归到宠物照护" send_model() let first = chat_request_id
    results.push({name: "first-request-context" pass: busy && chat_turns.len() == 1 && chat_turns[0].text == chat_text})
    let ask = good.to_json().parse_json() ask.kind = "clarify" ask.question = "猫粮花了多少钱？" ask.amount = ""
    chat_receive(request_serial,{is_ok: true data: {output: ask}})
    results.push({name: "question-no-write" pass: chat_state == "clarify" && db.records.len() == 0 && db.flows.len() == 0 && chat_text == "" && chat_turns.len() == 2})
    chat_edit("45元") send_model() let save_id = chat_request_id
    results.push({name: "followup-context" pass: busy && chat_turns.len() == 3 && chat_turns[0].text == "今天买猫粮，归到宠物照护" && chat_turns[2].text == "45元" && first != save_id})
    chat_receive(request_serial,{is_ok: true data: {output: good}})
    results.push({name: "save-record-flow-receipt" feedback: chat_result pass: chat_state == "saved" && db.records.len() == 1 && db.flows.len() == 1 && db.receipts.len() == 1 && db.records[0].cents == 4500 && db.records[0].flow_ids[0] == db.flows[0].id})
    send_model()
    results.push({name: "repeat-no-write-or-new-request" pass: !busy && db.records.len() == 1 && db.receipts.len() == 1 && chat_request_id == save_id})
    chat_edit("今天午饭花32元") send_model()
    results.push({name: "next-item-clean-context" pass: chat_turns.len() == 1 && chat_turns[0].text == "今天午饭花32元" && chat_candidate == nil && chat_request_id != save_id})
    let lunch = good.to_json().parse_json() lunch.title = "午饭" lunch.amount = "32" lunch.flow_names = []
    chat_receive(request_serial,{is_ok: true data: {output: lunch}})
    results.push({name: "next-item-no-old-flow" pass: chat_state == "saved" && db.records.len() == 2 && db.records[1].flow_ids.len() == 0 && db.receipts.len() == 2})
    chat_edit("今天公交花2元") send_model() let cancelled = request_serial
    chat_reset() let transit = good.to_json().parse_json() transit.title = "公交" transit.amount = "2" transit.flow_names = []
    chat_receive(cancelled,{is_ok: true data: {output: transit}})
    results.push({name: "cancel-discards-write" pass: db.records.len() == 2 && chat_turns.len() == 0 && chat_candidate == nil && !busy})
    chat_edit("今天地铁花3元") send_model() let edited = request_serial
    chat_edit("今天地铁实际花4元")
    chat_receive(edited,{is_ok: true data: {output: transit}})
    results.push({name: "editing-discards-old-write" pass: db.records.len() == 2 && !busy})
    send_model() let subway = good.to_json().parse_json() subway.title = "地铁" subway.amount = "4" subway.flow_names = []
    chat_receive(request_serial,{is_ok: true data: {output: subway}})
    results.push({name: "edited-new-value-saved" pass: chat_state == "saved" && db.records.len() == 3 && db.records[2].cents == 400})
    let replay = business_save(chat_candidate)
    results.push({name: "business-replay-no-duplicate" pass: replay["ok"] && replay.replayed && db.records.len() == 3 && db.receipts.len() == 3})
    chat_reset() chat_edit("今天买咖啡") send_model()
    ask.question = "咖啡花了多少钱？" chat_receive(request_serial,{is_ok: true data: {output: ask}})
    chat_edit("10元") send_model() chat_receive(request_serial,{is_ok: false error: "injected temporary error"})
    chat_edit("实际上是12元") send_model()
    results.push({name: "retry-edited-answer-keeps-original" pass: chat_turns.len() == 4 && chat_turns[0].text == "今天买咖啡" && chat_turns[3].text == "实际上是12元"})
    chat_reset()
    fs.write("integration-tests.json",results.to_json())
    screen = "chat" redraw()
}
start_timeout(1, || test_integration())
'''

def run(name,harness):
    folder=OUT/name;folder.mkdir(exist_ok=True)
    bundle=folder/'bundle'
    shutil.copytree(args.bundle,bundle)
    p=bundle/'main.splash'; source=p.read_text(encoding='utf-8');pos=source.index('start_timeout(0.08')
    p.write_text(source[:pos]+harness+'\n'+source[pos:],encoding='utf-8')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    cmd=[str(args.binary.resolve()),'--bundle',str(bundle),'--app-data',str(OUT/'state'),'--allow-unsigned','--stamp']
    with (folder/'runtime.log').open('w',encoding='utf-8') as stream:
        proc=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,MAKEPAD_HIDE_WINDOWS='1',MAKEPAD_REMOTE=str(port)),creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            report=OUT/f'state/dailyflow/{name}.json'
            for _ in range(120):
                if report.exists():break
                if proc.poll() is not None:break
                time.sleep(.1)
            assert report.exists(),(folder/'runtime.log').read_text(encoding='utf-8')[-8000:]
            data=json.loads(report.read_text(encoding='utf-8'))
            assert all(r['pass'] for r in data),data
            print(json.dumps(data,ensure_ascii=False,indent=2))
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/snap') as r: snap=json.load(r)
            (folder/'snapshot.json').write_text(json.dumps(snap,ensure_ascii=False),encoding='utf-8')
        finally:
            try:urllib.request.urlopen(f'http://127.0.0.1:{port}/quit',timeout=2).close()
            except OSError:pass
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            (folder/'stopped.json').write_text(json.dumps({'pid':proc.pid,'stopped':proc.poll() is not None}),encoding='utf-8')

assert not (OUT/'state').exists(), 'Use a fresh output directory: results are preserved.'
run('integration-tests',HARNESS)
run('restart-tests',r'''
start_timeout(1, || {
    fs.write("restart-tests.json",[{name: "real-restart-records-flows-receipts" pass: loaded && !locked && db.records.len() == 3 && db.flows.len() == 1 && db.receipts.len() == 3 && db.records[0].cents == 4500 && db.records[2].cents == 400}].to_json())
})
''')
