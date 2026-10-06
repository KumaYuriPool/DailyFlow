"""On-demand read views using actual Splash tools and isolated synthetic sources."""
import argparse,json
from pathlib import Path
import business_test_driver as d
from test_event_flow import apply,data

def recall(**args):return dict(name='dailyflow.recall',args=args)
def run(out,binary):
 d.configure(Path('bundle'),out,binary);state=out/'state';calls=0
 def batch(name,*ops):
  nonlocal calls
  calls+=len(ops);raw=d.run(name,list(ops),state);return [data(raw,i) for i in range(len(ops))]
 created,=batch('seed',apply('care',kind='expense',title='洗护费',date='2026-10-04',amount='120',subject='团子',event_title='团子洗护',plan_title='再次护理',plan_date='2026-10-11',plan_time='15:00'))
 assert created['ok'];expense=created['record_id'];fid=created['flow_ids'][0]
 food,period=batch('others',apply('food',kind='expense',title='猫粮',date='2026-10-04',amount='50',subject='团子'),apply('period',kind='period_entry',date='2026-09-28',end_date='2026-09-30'))
 assert food['ok'] and period['ok']
 before=d.latest(state)
 q,empty=batch('search',recall(text='团子洗护'),recall())
 assert q['ok'] and q['total']==3 and q['read_only'] and empty['total']==0
 assert {e['source_module'] for e in q['events']}=={'expense','calendar'}
 assert [e['date'] for e in q['events']]==['2026-10-04','2026-10-04','2026-10-11']
 assert '猫粮' not in str(q['events']);assert len({e['event_id'] for e in q['events']})==3
 assert q['events'][-1]['status']=='planned' and q['events'][-1]['time']=='15:00'
 group,third=batch('subject',recall(text='团子'),recall(text='经期'))
 assert group['total']==4 and group['flow_id']==fid and third['total']==1 and third['events'][0]['end_date']=='2026-09-30'
 assert d.latest(state)==before
 no,invalid=batch('invalid',recall(text='不存在'),recall(flow_id='missing'));assert no['total']==0 and not invalid['ok']
 candidate,=batch('candidate',recall(text='团'));assert candidate['flow_id']=='' and candidate['candidates'][0]['label']=='团子 · 4 条 · 2026-10-04 起'
 first,=batch('page',recall(text='团子',limit=1))
 nextpage,=batch('page2',recall(text='团子',offset=1,limit=1,snapshot_revision=first['snapshot_revision']))
 assert nextpage['events'][0]['event_id']!=first['events'][0]['event_id']
 r=next(e for e in q['events'] if e['source_record_id']==expense)
 corrected,=batch('correct',apply('correct',kind='expense',record_id=expense,expected_revision=r['source_revision'],title='洗护费',date='2026-10-03',amount='110'))
 assert corrected['ok']
 moved,stale=batch('moved',recall(text='团子洗护'),recall(text='团子',offset=1,snapshot_revision=first['snapshot_revision']))
 assert moved['events'][0]['source_record_id']==expense and moved['events'][0]['date']=='2026-10-03' and not stale['ok']
 rev=moved['events'][0]['source_revision']
 deleted,=batch('delete',apply('delete',operation='delete',record_id=expense,expected_revision=rev));assert deleted['ok']
 after,=batch('after',recall(text='团子洗护'));assert after['total']==2 and expense not in str(after['events'])
 # UI seed keeps the original three-step example; tests below use their own branch.
 assert len(d.latest(state)['flows'])==1 and len(d.latest(state)['period_entries'])==1
 early,late=batch('minutes',apply('late',kind='event',title='检查',date='2026-10-02',time='18:00',status='occurred'),apply('early',kind='event',title='检查',date='2026-10-02',time='09:00',status='occurred'))
 minute,=batch('ordered',recall(text='检查'));assert [e['time'] for e in minute['events']]==['09:00','18:00']
 assert len(d.latest(state)['flows'])==1
 # A date collision and unrelated same-subject record never becomes a confirmed edge.
 snapshot=d.latest(state);again,=batch('restart-readonly',recall(text='团子洗护'));assert again['total']==2 and d.latest(state)==snapshot
 report=dict(passed=True,tool_calls=calls,real_provider=False,checks=['title plus confirmed typed relations','no same-subject/date over-expansion','dedup and time order','explicit subject view','registered third source interval','empty/unknown search','snapshot pagination','same-ID correction refresh','delete no ghost','restart read-only and no Flow creation'])
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);a=p.parse_args();run(a.output,a.binary)
