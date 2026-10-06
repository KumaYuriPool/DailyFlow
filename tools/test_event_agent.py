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
    return {"ok": true checks: checks}
}
fn event_agent_edge_tests(){
    let checks = []
    let good = {intent: "create" question: "" kind: "expense" title: "洗护费" date: today() amount: "120" time: "" status: "occurred" subject: "团子" topic: "护理" flow_id: "" event_title: "洗护" plan_title: "" plan_date: "" plan_time: "" related_event_id: "" match_title: "" match_date: "" match_amount: ""}
    business_save({request_id: "edge-wash" kind: "expense" title: "洗护费" amount: "110" date: today() subject: "团子" event_title: "洗护"})
    active_flow = flow_catalog(db)[0].id
    business_save({request_id: "edge-supply" kind: "expense" title: "护理用品" amount: "35" date: today() flow_id: active_flow})
    let rev = db.revision let correct = good.to_json().parse_json() correct.intent = "correct" correct.match_title = "洗护" correct.match_amount = "120" correct.amount = "110" correct.date = "" correct.event_title = ""
    // Preserve legacy ambiguous containers rather than silently merging old data.
    let legacy = clone_db() legacy.flows.push({id: "legacy-topic" name: "团子 · 体检" subject: "团子" topic: "体检" hidden: false event_flow: true created_at: 0}) persist(legacy)
    rev = db.revision let unclear = good.to_json().parse_json() unclear.topic = "" unclear.flow_id = "" unclear.title = "用品" unclear.amount = "5"
    chat_text = "团子的用品" send_model() chat_receive(request_serial,{is_ok: true data: {output: unclear}})
    checks.push({name: "competing-flow-clarifies" pass: db.revision == rev && chat_state == "clarify"})
    manual_apply({operation: "delete_flow" flow_id: "legacy-topic"})
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
fn event_subject_tests(){
    let checks = []
    let o = {intent: "create" question: "" kind: "expense" title: "洗护费" date: today() amount: "120" time: "" status: "occurred" subject: "团子" topic: "洗护" flow_id: "" event_title: "洗护" plan_title: "" plan_date: "" plan_time: "" related_event_id: "" match_title: "" match_date: "" match_amount: "" user_tags: []}
    chat_text = "给团子洗护花了120元" send_model() chat_receive(request_serial,{is_ok: true data: {output: o}})
    let fid = active_flow
    checks.push({name: "subject-only-flow-name" pass: flow_name(fid) == "团子" && flow_catalog(db).len() == 1})
    o.title = "猫粮" o.topic = "猫粮" o.event_title = "" o.user_tags = ["猫粮"]
    chat_text = "给团子买猫粮花了120元" send_model() chat_receive(request_serial,{is_ok: true data: {output: o}})
    checks.push({name: "different-items-same-subject-total-240" pass: active_flow == fid && flow_catalog(db).len() == 1 && flow_query(fid).amount_minor == 24000})
    checks.push({name: "ordinary-item-does-not-add-model-inferred-tag" pass: expense_get(last_saved).user_tags.len() == 0})
    o.user_tags = ["猫粮" "模型捏造"]
    chat_text = "给团子买猫粮花了120元，加标签猫粮" send_model() chat_receive(request_serial,{is_ok: true data: {output: o}})
    checks.push({name: "explicit-tag-grounded-and-independent" pass: expense_get(last_saved).user_tags.to_json() == ["猫粮"].to_json() && active_flow == fid && flow_catalog(db).len() == 1})
    let before = db.revision o.subject = "豆包" o.flow_id = fid o.user_tags = []
    chat_text = "给豆包买猫粮花了120元" send_model() chat_receive(request_serial,{is_ok: true data: {output: o}})
    checks.push({name: "wrong-subject-flow-rejected" pass: db.revision == before && chat_state == "clarify"})
    chat_reset() o.flow_id = "" chat_text = "给豆包买猫粮花了120元" send_model() chat_receive(request_serial,{is_ok: true data: {output: o}})
    checks.push({name: "different-subject-separated" pass: flow_catalog(db).len() == 2 && active_flow != fid && flow_name(active_flow) == "豆包"})
    before = db.revision o.intent = "query" o.subject = "团子" o.topic = "宠物花费"
    chat_text = "团子一共花了多少" send_model() chat_receive(request_serial,{is_ok: true data: {output: o}})
    checks.push({name: "subject-query-across-items-read-only" pass: db.revision == before && chat_result.split("360.00").len() > 1})
    let legacy = clone_db() legacy.flows = [{id: "old" name: "旧主体 · 护理" subject: "旧主体" topic: "护理" hidden: false event_flow: true}]
    let resolved = flow_resolve(legacy,"旧主体","猫粮","")
    checks.push({name: "single-legacy-subject-flow-reused-and-displayed-without-rewriting-history" pass: resolved.flow_id == "old" && legacy.flows.len() == 1 && legacy.flows[0].name == "旧主体 · 护理" && flow_catalog(legacy)[0].name == "旧主体"})
    return {"ok": true checks: checks}
}
fn event_speed_context_tests(){
    let checks = []
    business_save({request_id: "speed-flow" kind: "expense" title: "洗护费" date: today() amount: "120" subject: "团子"})
    let fid = flow_catalog(db)[0].id active_flow = fid
    business_save({request_id: "speed-other" kind: "expense" title: "豆包费用" date: today() amount: "5" subject: "豆包"})
    let other = flow_matches(db,"豆包","")[0].id
    let c = clone_db()
    for i in 20 { let r = source_base(c,"expense") r.title = "历史猫粮" r.date = today() r.revision = 1 r.cents = 100 r.flow_ids = [fid] r.created_at = i r.updated_at = i c.records.push(r) } persist(c)
    let before = db.revision captured_payload = nil chat_reset() chat_text = "团子一共花了多少钱？" send_model()
    checks.push({name: "local-total-full-history-no-model-no-write" pass: captured_payload == nil && db.revision == before && chat_metrics.route == "local" && chat_result.split("140.00").len() > 1})
    chat_reset() captured_payload = nil chat_text = "团子今天一共花了多少钱？" send_model()
    checks.push({name: "date-qualified-query-falls-through" pass: captured_payload != nil && busy})
    chat_reset() captured_payload = nil chat_text = "团子一共花了多少钱，再记一笔50元" send_model()
    checks.push({name: "compound-query-falls-through" pass: captured_payload != nil && busy})
    chat_reset() chat_text = "给团子买猫粮花了12元" send_model()
    let compact = captured_payload.input.context let old = business_query({limit: 30 flow_id: fid})
    let compact_shape = true for r in compact.records { if business_optional(r,"created_at",nil) != nil || business_optional(r,"revision",nil) != nil || business_optional(r,"user_tags",nil) != nil { compact_shape = false } }
    checks.push({name: "compact-context-capped-and-flags-truncation" pass: compact.records.len() == 12 && compact.truncated && compact.matching_records == 21 && compact_shape})
    let old_size = old.to_json().len() let new_size = compact.to_json().len()
    checks.push({name: "context-smaller-than-full-records" pass: new_size < old_size})
    checks.push({name: "only-intent-required" pass: captured_payload.schema.required.to_json() == ["intent"].to_json()})
    chat_receive(request_serial,{is_ok: true data: {output: {intent: "create" title: "猫粮" amount: "12" subject: "团子"}}})
    checks.push({name: "sparse-valid-reply-saves-with-safe-defaults" pass: chat_state == "saved" && expense_get(last_saved).cents == 1200 && expense_get(last_saved).date == context_date})
    chat_reset() chat_text = "给豆包买猫粮花了6元" send_model()
    let rows = captured_payload.input.context.records
    checks.push({name: "explicit-other-subject-context-beats-active-flow" pass: rows.len() == 1 && rows[0].flow_ids.to_json() == [other].to_json()})
    before = db.revision chat_receive(request_serial,{is_ok: true data: {output: {title: "缺少意图" amount: "6"}}})
    checks.push({name: "missing-intent-rejected" pass: db.revision == before && chat_state == "error"})
    return {"ok": true checks: checks old_context_size: old_size compact_context_size: new_size}
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
    chat_text = "请分析这件事目前的费用" send_model()
    checks.push({name: "selected-flow-reaches-model-payload" pass: captured_payload.input.current_flow == chosen && captured_payload.input.displayed_date == "2026-10-03"})
    serial = request_serial new_conversation() chat_receive(serial,{is_ok: true data: {output: good}})
    checks.push({name: "new-conversation-cancels-and-resets" pass: db.revision == rev && !busy && active_flow == "" && context_date == today() && chat_text == "" && last_saved == ""})
    return {"ok": true checks: checks}
}
fn module_agent_tests(){
    let checks = []
    business_save({request_id: "module-exp" kind: "expense" title: "猫粮" date: today() amount: "120" subject: "团子"})
    business_save({request_id: "module-plan" kind: "event" title: "洗护" date: "2026-12-10" status: "planned" subject: "团子"})
    let fid = flow_matches(db,"团子","")[0].id let sid = subject_catalog(db)[0].id let before = db.revision
    chat_reset() chat_text = "团子本月花费和下次洗护" send_model()
    checks.push({name: "capabilities-in-model-payload" pass: captured_payload.input.capabilities.len() == 3 && captured_payload.input.capabilities[2].id == "period.history"})
    chat_receive(request_serial,{is_ok: true data: {output: {intent: "query" subject_id: sid queries: [{capability: "expense.summary" period: "this_month"} {capability: "calendar.next" keyword: "洗护"}]}}})
    checks.push({name: "compound-query-model-to-modules-no-write" pass: chat_state == "answered" && db.revision == before && chat_result.split("120.00").len() > 1 && chat_result.split("2026-12-10").len() > 1 && chat_query_sources.len() == 2})
    clear_chat() checks.push({name: "cancel-clears-query-sources" pass: chat_query_sources.len() == 0})
    let c = clone_db() c.flows.push({id: "duplicate" name: "团子旧分组" subject: "团子" topic: "旧" event_flow: true hidden: false}) persist(c)
    let result = module_query({subject: "团子" queries: [{capability: "expense.summary"}]})
    checks.push({name: "legacy-same-name-subject-query-clarifies" pass: !result["ok"]})
    result = module_query({subject_id: sid queries: [{capability: "expense.summary"}]})
    checks.push({name: "explicit-subject-ID-resolves-ambiguity" pass: result["ok"] && result.results[0].amount_minor == 12000})
    let plan = calendar_snapshot(db)[0] c = clone_db() relation_add(c,fid,"fulfills","synthetic-fact",plan.id,"fixture")
    // Test the relation view without persisting an invalid fixture source.
    let saved = db db = c result = module_query({subject_id: sid queries: [{capability: "calendar.next"}]}) db = saved
    checks.push({name: "fulfilled-plans-excluded" pass: result["ok"] && result.results[0].count == 0})
    return {"ok": true checks: checks}
}
'''
def run(out,binary=None):
    d.configure(ROOT/'bundle',out,Path(binary or ROOT.parent/'OctoSense-App-Hub/target/release/card-host.exe'))
    p=out/'bundle/main.splash';s=p.read_text(encoding='utf8').replace('host.request("model.complete",','test_model_request("model.complete",')
    s=s.replace('start_timeout(45,','start_timeout(0.1,')
    s=s.replace('if name == "dailyflow.query" { tools.resolve(token,business_query(a)) return }','if name == "dailyflow.query" { if business_optional(a,"record_id","") == "timeout-test" { event_timeout_test(token) return } if business_optional(a,"record_id","") == "speed-test" { tools.resolve(token,event_speed_context_tests()) return } if business_optional(a,"record_id","") == "edge-test" { tools.resolve(token,event_agent_edge_tests()) return } if business_optional(a,"record_id","") == "subject-test" { tools.resolve(token,event_subject_tests()) return } if business_optional(a,"record_id","") == "context-test" { tools.resolve(token,event_context_tests()) return } tools.resolve(token,event_agent_tests()) return }')
    s=s.replace('if name == "dailyflow.capabilities" {', 'if name == "dailyflow.capabilities" { tools.resolve(token,module_agent_tests()) return } if name == "test-unused-capabilities" {')
    s=s.replace('start_timeout(0.08,|| boot())',HARNESS+'\nstart_timeout(0.08,|| boot())');p.write_text(s,encoding='utf8')
    # Independent isolates keep each bounded scenario inside normal host budgets.
    r=d.run('agent-injected',[d.query()]);report=data(r,0)
    edges=d.run('edges-injected',[d.query(record_id='edge-test')]);report['checks'].extend(data(edges,0)['checks'])
    context=d.run('context-injected',[d.query(record_id='context-test')]);report['checks'].extend(data(context,0)['checks'])
    subject=d.run('subject-injected',[d.query(record_id='subject-test')]);report['checks'].extend(data(subject,0)['checks'])
    speed=d.run('speed-injected',[d.query(record_id='speed-test')]);metrics=data(speed,0);report['checks'].extend(metrics['checks']);report['context_sizes']={k:metrics[k] for k in ('old_context_size','compact_context_size')}
    timeout=d.run('timer-injected',[d.query(record_id='timeout-test')]);assert data(timeout,0)['ok'],timeout
    modules=d.run('modules-injected',[dict(name='dailyflow.capabilities',args={})]);report['checks'].extend(data(modules,0)['checks'])
    report['real_timer_timeout_with_shortened_test_delay']=True
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    assert all(c['pass'] for c in report['checks']),report
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path);args=p.parse_args();run(args.output.resolve(),args.binary)
