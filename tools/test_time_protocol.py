"""Real Splash tests for three registered pseudo Apps; synthetic data only."""
import argparse,json,shutil
from pathlib import Path
import business_test_driver as d
from test_event_flow import apply,data
ROOT=Path(__file__).resolve().parents[1]
def timeline(**kw):return dict(name='dailyflow.timeline_query',args=kw)
def run(out,binary):
 d.configure(ROOT/'bundle',out,binary);state=out/'state';checks=[];calls=0
 def batch(name,*ops):
  nonlocal calls
  calls+=len(ops);raw=d.run(name,list(ops),state);return [data(raw,i) for i in range(len(ops))]
 expense,plan=batch('existing',apply('expense',kind='expense',title='午餐',date='2026-10-02',amount='35'),apply('plan',kind='event',title='下次洗护',date='2026-12-01',time='15:00',status='planned'))
 assert expense['ok'] and plan['ok']
 req=apply('period',kind='period_entry',date='2026-09-29',end_date='2026-10-03')
 created,replay=batch('period',req,req);assert created['ok'] and replay['replayed'];pid=created['record_id']
 q,day=batch('all',timeline(),timeline(date_from='2026-10-01',date_to='2026-10-01'))
 assert q['total']==3 and day['total']==1
 period=next(e for e in q['events'] if e['source_module']=='period');revision=period['source_revision']
 future=next(e for e in q['events'] if e['source_module']=='calendar')
 assert future['occurred_at']=='' and future['scheduled_at']=='2026-12-01T15:00:00+08:00'
 assert period['occurred_at']=='' and period['end_date']=='2026-10-03' and period['created_at']>0 and period['recorded_at']==period['created_at']
 assert all(e['event_id'] and e['source_revision'] and e['entry']['record_id']==e['source_record_id'] for e in q['events'])
 assert not d.latest(state)['flows']
 checks+=['three registered sources','inclusive range across month','day precision has no invented midnight','scheduled vs occurred vs recorded','no automatic Flow','durable period replay']
 first,=batch('page1',timeline(limit=1));second,=batch('page2',timeline(limit=1,offset=first['next_offset'],snapshot_revision=first['snapshot_revision']))
 assert first['has_more'] and first['events'][0]['event_id']!=second['events'][0]['event_id']
 missing,=batch('missing-revision',timeline(offset=1));assert not missing['ok']
 old=d.latest(state)
 for index,args in enumerate([dict(date='2026-10-03',end_date='2026-10-02'),dict(date='2026-12-01'),dict(date='2026-10-01',end_date='2026-10-02'),dict(date='bad'),dict(date='2026-09-01',end_date=17),dict(date='2026-09-01',subject='团子')]):
  result,=batch('invalid'+str(index),apply('bad'+str(index),kind='period_entry',**args));assert not result['ok'];assert d.latest(state)==old
 fixed,stale=batch('correct',apply('correct',kind='period_entry',record_id=pid,expected_revision=revision,date='2026-09-28',end_date='2026-09-30'),apply('stale',kind='period_entry',record_id=pid,expected_revision=revision,date='2026-09-27'))
 assert fixed['ok'] and not stale['ok']
 gone,oldpage=batch('moved',timeline(date_from='2026-10-01',date_to='2026-10-01'),timeline(offset=1,snapshot_revision=first['snapshot_revision']))
 assert gone['total']==0 and not oldpage['ok']
 checks+=['same-ID correction removes old dates','optimistic revision rejection','snapshot pagination rejects concurrent changes','overlap/future/invalid range rejection without writes']
 openrec,=batch('open',apply('ongoing',kind='period_entry',date='2026-10-04'))
 assert openrec['ok']
 present,futureday=batch('open-range',timeline(source_module='period',date_from=d.DAY,date_to=d.DAY),timeline(source_module='period',date_from=d.FUTURE_DAY,date_to=d.FUTURE_DAY))
 assert present['total']==1 and present['events'][0]['open_end'] and futureday['total']==0
 before=d.latest(state)
 history,=batch('history',dict(name='dailyflow.module_query',args={'queries':[{'capability':'period.history','date_from':'2026-09-01','date_to':d.DAY}]}))
 assert history['ok'] and history['results'][0]['count']==2 and d.latest(state)==before
 restored,=batch('restart',timeline(source_module='period'));assert restored['total']==2 and d.latest(state)==before
 finalrev=next(e['source_revision'] for e in restored['events'] if e['source_record_id']==pid)
 removed,=batch('delete',apply('delete',operation='delete',record_id=pid,expected_revision=finalrev));assert removed['ok']
 after,again=batch('after-delete',timeline(source_module='period'),req)
 assert after['total']==1 and again['replayed'] and len(d.latest(state)['period_entries'])==1
 assert len(d.latest(state)['records'])==1 and len(d.latest(state)['calendar_events'])==1
 checks+=['open end covers only observed days, no predictions','period history read-only','restart preserves identity','delete/replay does not resurrect','other source records intact']
 # Independent consumer + fourth fake source. Only the adapter wiring changes.
 original=(ROOT/'bundle/main.splash').read_text(encoding='utf8')
 core=(ROOT/'src/08_time_protocol.splash').read_text(encoding='utf8')
 assert 'expense' not in core and 'calendar' not in core and 'period' not in core
 storage=(ROOT/'src/00_storage.splash').read_text(encoding='utf8')
 fixture=storage+'\n'+core+'''
fn time_modules(){ return [{id: "travel"} {id: "journal"}] }
fn on_agent_tool(token,name,args_json){
    let items = [] let up = {protocol_version: 1 source_app: "dailyflow" source_module: "travel" source_record_id: "same" source_revision: 2 operation: "upsert" date: "2026-10-01"}
    let accepted = projection_accept(items,up)
    let duplicate = projection_accept(items,up)
    let old = up.to_json().parse_json() old.source_revision = 1 let stale = projection_accept(items,old)
    let other = up.to_json().parse_json() other.source_module = "journal" projection_accept(items,other)
    let unknown = up.to_json().parse_json() unknown.source_module = "unknown" let rejected = projection_accept(items,unknown)
    let tomb = {protocol_version: 1 source_app: "dailyflow" source_module: "travel" source_record_id: "same" source_revision: 3 operation: "delete"}
    projection_accept(items,tomb) let late = projection_accept(items,up)
    let malformed = up.to_json().parse_json() malformed.source_revision = 4 malformed.date = "bad" let bad = projection_accept(items,malformed)
    mod.app_tools.resolve(token,{"ok": accepted && !duplicate && !stale && !rejected && !late && !bad && items.len() == 2 && items[0].operation == "delete" && items[1].operation == "upsert"})
}
SolidView{width: Fill height: Fill Label{text: "Generic time contract"}}
'''
 (out/'bundle/main.splash').write_text(fixture,encoding='utf8')
 raw=d.run('independent-consumer',[timeline()]);calls+=1;assert data(raw,0)['ok']
 (out/'bundle/main.splash').write_text(original,encoding='utf8')
 checks+=['independent reducer without business modules/UI','fourth source via registry only','same record ID across sources is distinct','duplicate/stale/tombstone/unknown/malformed rejection']
 # Integration extension: register a fourth snapshot/project adapter in the copy.
 extra='''
fn fixture_snapshot(c){ return [{id: "fixture-record" revision: 1 title: "出行记录" date: "2026-10-01" time: "" status: "occurred" created_at: 1 updated_at: 1 flow_ids: []}] }
fn fixture_project(r){ return time_fields(r.date,"","","occurred",false) }
'''
 expanded=original.replace('fn time_modules(){ return [',extra+'\nfn time_modules(){ return [\n {id: "travel" kind: "travel_entry" name: "出行测试" snapshot: fixture_snapshot project: fixture_project}')
 assert expanded!=original
 (out/'bundle/main.splash').write_text(expanded,encoding='utf8')
 raw=d.run('fourth-adapter',[timeline(source_module='travel')],state);calls+=1
 assert data(raw,0)['events'][0]['summary']=='出行记录'
 (out/'bundle/main.splash').write_text(original,encoding='utf8')
 checks+=['fourth adapter full snapshot/query integration without core changes']
 report=dict(passed=True,tool_calls=calls,checks=checks)
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);a=p.parse_args();run(a.output.resolve(),a.binary)
