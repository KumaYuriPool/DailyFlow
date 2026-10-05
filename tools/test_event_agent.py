"""Injected model replies, real Splash coordinator and persistence; NOT Provider QA."""
import argparse,json
from pathlib import Path
import business_test_driver as d
from test_event_flow import data
ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''
let captured_payload = nil
fn test_model_request(route,payload,callback){ captured_payload = payload return nil }
fn event_timeout_test(token){
    let before = db.revision chat_reset() chat_text = "等待超时" send_model() let serial = request_serial
    start_timeout(0.3,|| {
        let expired = !busy && request_serial != serial && chat_state == "error"
        let o = {intent: "create" question: "" kind: "expense" title: "迟到" date: today() amount: "9" time: "" status: "occurred" subject: "" topic: "" flow_id: "" event_title: "" plan_title: "" plan_date: "" plan_time: "" related_event_id: "" match_title: "" match_date: "" match_amount: ""}
        chat_receive(serial,{is_ok: true data: {output: o}})
        mod.app_tools.resolve(token,{"ok": expired && db.revision == before})
    })
}
fn event_agent_tests(){
    let checks = []
    let good = {intent: "create" question: "" kind: "expense" title: "洗护费" date: today() amount: "120" time: "" status: "occurred" subject: "团子" topic: "护理" flow_id: "" event_title: "洗护" plan_title: "" plan_date: "" plan_time: "" related_event_id: "" match_title: "" match_date: "" match_amount: ""}
    chat_text = "今天给团子洗护120元" send_model() let serial = request_serial
    chat_receive(serial,{is_ok: true data: {output: good}})
    checks.push({name: "compound" pass: chat_state == "saved" && expense_snapshot(db).len() == 1 && calendar_snapshot(db).len() == 1})
    let rev = db.revision send_model() checks.push({name: "duplicate-send" pass: db.revision == rev && !busy})
    chat_text = "给团子买用品35元" send_model()
    let supplies = good.to_json().parse_json() supplies.title = "护理用品" supplies.amount = "35" supplies.event_title = "" supplies.related_event_id = calendar_snapshot(db)[0].id
    chat_receive(request_serial,{is_ok: true data: {output: supplies}})
    checks.push({name: "associate" pass: flow_catalog(db).len() == 1 && flow_query(active_flow).amount_minor == 15500})
    let correct = good.to_json().parse_json() correct.intent = "correct" correct.match_title = "洗护" correct.match_amount = "120" correct.amount = "110" correct.date = "" correct.event_title = ""
    chat_text = "洗护费改110" send_model() chat_receive(request_serial,{is_ok: true data: {output: correct}})
    checks.push({name: "unique-correction" pass: expense_snapshot(db).len() == 2 && flow_query(active_flow).amount_minor == 14500})
    rev = db.revision let query = good.to_json().parse_json() query.intent = "query"
    chat_text = "这次多少" send_model() chat_receive(request_serial,{is_ok: true data: {output: query}})
    checks.push({name: "read-only-query" pass: db.revision == rev && chat_result.split("145.00").len() > 1})
    let ask = good.to_json().parse_json() ask.intent = "clarify" ask.question = "准确多少元？"
    chat_text = "一百多" send_model() chat_receive(request_serial,{is_ok: true data: {output: ask}})
    checks.push({name: "clarify-no-write" pass: db.revision == rev && chat_state == "clarify"})
    chat_text = "130元" send_model() checks.push({name: "clarification-context" pass: chat_turns.len() == 3})
    serial = request_serial chat_reset() chat_receive(serial,{is_ok: true data: {output: good}})
    checks.push({name: "cancel-late-callback" pass: db.revision == rev && !busy})
    chat_text = "新消费" send_model() serial = request_serial chat_edit("更改输入") chat_receive(serial,{is_ok: true data: {output: good}})
    checks.push({name: "edit-invalidates-callback" pass: db.revision == rev && !busy})
    chat_text = "待超时" send_model() serial = request_serial request_serial += 1 busy = false chat_receive(serial,{is_ok: true data: {output: good}})
    checks.push({name: "timeout-generation-invalidates" pass: db.revision == rev})
    // Two same-subject but competing topics cannot be resolved without a topic.
    business_save({request_id: "compete" kind: "event" title: "体检" date: today() status: "occurred" subject: "团子" topic: "体检"})
    rev = db.revision let unclear = good.to_json().parse_json() unclear.topic = "" unclear.flow_id = "" unclear.title = "用品" unclear.amount = "5"
    chat_text = "团子的用品" send_model() chat_receive(request_serial,{is_ok: true data: {output: unclear}})
    checks.push({name: "competing-flow-clarifies" pass: db.revision == rev && chat_state == "clarify"})
    // Two expense matches cannot be chosen just by amount proximity.
    business_save({request_id: "secondwash" kind: "expense" title: "洗护费第二笔" date: today() amount: "50" flow_id: active_flow})
    rev = db.revision correct.match_amount = "" correct.topic = "护理" correct.amount = "40"
    chat_text = "洗护费改40" send_model() chat_receive(request_serial,{is_ok: true data: {output: correct}})
    checks.push({name: "competing-expense-clarifies" pass: db.revision == rev && chat_state == "clarify"})
    // An unrelated plain purchase must not inherit the last active Flow.
    let unrelated = good.to_json().parse_json() unrelated.title = "公交" unrelated.amount = "2" unrelated.subject = "" unrelated.topic = "" unrelated.event_title = ""
    chat_reset() chat_text = "今天公交2元" send_model() chat_receive(request_serial,{is_ok: true data: {output: unrelated}})
    checks.push({name: "unrelated-remains-ungrouped" pass: expense_get(last_saved).flow_ids.len() == 0})
    let plan = good.to_json().parse_json() plan.kind = "event" plan.title = "明确后续" plan.status = "planned" plan.amount = "" plan.date = "2026-10-11" plan.event_title = ""
    chat_text = "下次再护理" send_model() chat_receive(request_serial,{is_ok: true data: {output: plan}})
    let edge_found = false for edge in flow_relations(db) { if edge.type == "follow_up" && edge.to_node == last_saved { edge_found = true } }
    checks.push({name: "omitted-followup-ID-resolves-only-unique-fact" pass: chat_state == "saved" && edge_found})
    business_save({request_id: "secondfact" kind: "event" title: "另一次事项" date: today() status: "occurred" flow_id: active_flow})
    rev = db.revision chat_text = "之后再安排一次" send_model() chat_receive(request_serial,{is_ok: true data: {output: plan}})
    checks.push({name: "omitted-followup-ID-multiple-facts-clarifies" pass: chat_state == "clarify" && db.revision == rev})
    return {"ok": true checks: checks}
}
fn event_context_tests(){
    let checks = [] let good = {} let serial = 0
    business_save({request_id: "context-flow" kind: "expense" title: "护理费" amount: "10" date: today() subject: "团子" topic: "护理" event_title: "护理"})
    let rev = db.revision
    new_conversation() yy = 2026 mm = 10 pick_day(3)
    chat_text = "没有说日期的消费" send_model()
    checks.push({name: "browsing-keeps-model-input-date" pass: captured_payload.input.displayed_date == today()})
    serial = request_serial rev = db.revision backfill_here()
    chat_receive(serial,{is_ok: true data: {output: good}})
    checks.push({name: "backfill-cancels-old-model-reply" pass: db.revision == rev && !busy && context_date == "2026-10-03"})
    chat_text = "补记午餐" send_model()
    checks.push({name: "backfill-reaches-model-payload" pass: captured_payload.input.displayed_date == "2026-10-03" && captured_payload.input.actual_today == today()})
    let chosen = flow_catalog(db)[0].id choose_flow(chosen)
    chat_text = "这件事花了多少" send_model()
    checks.push({name: "selected-flow-reaches-model-payload" pass: captured_payload.input.current_flow == chosen && captured_payload.input.displayed_date == "2026-10-03"})
    serial = request_serial new_conversation() chat_receive(serial,{is_ok: true data: {output: good}})
    checks.push({name: "new-conversation-cancels-and-resets" pass: db.revision == rev && !busy && active_flow == "" && context_date == today() && chat_text == "" && last_saved == ""})
    return {"ok": true checks: checks}
}
'''
def run(out):
    d.configure(ROOT/'bundle',out,ROOT.parent/'OctoSense-App-Hub/target/release/card-host.exe')
    p=out/'bundle/main.splash';s=p.read_text(encoding='utf8').replace('host.request("model.complete",','test_model_request("model.complete",')
    s=s.replace('start_timeout(45,','start_timeout(0.1,')
    s=s.replace('if name == "dailyflow.query" { tools.resolve(token,business_query(a)) return }','if name == "dailyflow.query" { if business_optional(a,"record_id","") == "timeout-test" { event_timeout_test(token) return } if business_optional(a,"record_id","") == "context-test" { tools.resolve(token,event_context_tests()) return } tools.resolve(token,event_agent_tests()) return }')
    s=s.replace('start_timeout(0.08,|| boot())',HARNESS+'\nstart_timeout(0.08,|| boot())');p.write_text(s,encoding='utf8')
    # Independent isolates keep each bounded scenario inside normal host budgets.
    r=d.run('agent-injected',[d.query()]);report=data(r,0)
    context=d.run('context-injected',[d.query(record_id='context-test')]);report['checks'].extend(data(context,0)['checks'])
    timeout=d.run('timer-injected',[d.query(record_id='timeout-test')]);assert data(timeout,0)['ok'],timeout
    report['real_timer_timeout_with_shortened_test_delay']=True
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    assert all(c['pass'] for c in report['checks']),report
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output.resolve())
