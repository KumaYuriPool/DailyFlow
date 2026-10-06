"""Full-source pseudo-App routing via actual isolated Splash tool calls."""
import argparse, json
from pathlib import Path
import business_test_driver as d
from test_event_flow import apply, data
ROOT=Path(__file__).resolve().parents[1]
def query(*plans,**scope):
    return dict(name='dailyflow.module_query',args=dict(queries=list(plans),**scope))
def run(out,binary):
    d.configure(ROOT/'bundle',out,binary)
    state=out/'state'
    calls=[apply(f'exp{i}',kind='expense',title='猫粮',amount='10',date=d.DAY,subject='团子',user_tags=['猫粮'] if i<2 else []) for i in range(15)]
    calls += [apply('past',kind='expense',title='洗护',amount='20',date='2026-09-01',subject='团子'),apply('other',kind='expense',title='猫粮',amount='99',date=d.DAY,subject='豆包')]
    calls += [apply('plan'+str(i),kind='event',title='洗护'+str(i),date='2026-12-'+str(10+i),status='planned',subject='团子') for i in range(5)]
    calls += [apply('cancel',kind='event',title='洗护取消',date=d.FUTURE_DAY,status='cancelled',subject='团子'),apply('occurred',kind='event',title='洗护发生',date=d.DAY,status='occurred',subject='团子'),dict(name='dailyflow.capabilities',args={})]
    seeded={}
    for start in range(0,len(calls),2):
        part=d.run('seed'+str(start),calls[start:start+2],state)
        seeded.update({start+i:v for i,v in part.items()})
    assert all(data(seeded,i)['ok'] for i in range(len(calls)))
    catalog=data(seeded,len(calls)-1);subject=next(s for s in catalog['subjects'] if s['name']=='团子');sid=subject['id']
    before=d.latest(state)
    tests=[query({'capability':'expense.summary'},subject_id=sid),query({'capability':'expense.summary','period':'this_month'},{'capability':'calendar.next','keyword':'洗护'},subject='团子'),query({'capability':'expense.summary','tag':'猫粮'},subject_id=sid),query({'capability':'calendar.next'},subject_id=sid),query({'capability':'expense.summary'},subject_id=sid,subject='豆包')]
    tests += [query(p,subject_id=sid) for p in [{'capability':'unknown.write'},{'capability':'expense.summary','date_from':'bad'},{'capability':'expense.summary','date_from':'2026-10-05','date_to':'2026-10-01'},{'capability':'expense.summary','period':'this_month','date_from':d.DAY},{'capability':'calendar.next','tag':'猫粮'}]]
    tests += [query({'capability':'expense.summary'},{'capability':'expense.summary'},subject_id=sid),query({'capability':'expense.summary'},subject='不存在'),query({'capability':'expense.summary'})]
    r={}
    for start in range(0,len(tests),2):
        part=d.run('queries'+str(start),tests[start:start+2],state)
        r.update({start+i:v for i,v in part.items()})
    total=data(r,0);assert total['ok'] and total['modules_used']==['expense'] and total['results'][0]['amount_minor']==17000 and total['results'][0]['count']==16
    assert len(total['results'][0]['sources'])==5 and total['results'][0]['sources_truncated']
    compound=data(r,1);assert compound['ok'] and compound['modules_used']==['expense','calendar'] and compound['results'][0]['amount_minor']==15000
    plans=compound['results'][1];assert plans['count']==5 and len(plans['events'])==3 and plans['events'][0]['date']=='2026-12-10'
    assert all(s['subject_id']==sid and s['source_revision']>0 and s['entry']['record_id']==s['source_record_id'] for result in compound['results'] for s in result['sources'])
    assert data(r,2)['results'][0]['amount_minor']==2000 and data(r,3)['modules_used']==['calendar']
    assert all(not r[i]['ok'] or not r[i]['data']['ok'] for i in range(4,12))
    assert data(r,12)['results'][0]['amount_minor']==26900
    assert d.latest(state)==before
    # Registry survives restart; queries never materialize or write identities.
    again=d.run('restart',[dict(name='dailyflow.capabilities',args={})],state)
    assert data(again,0)['subjects']==catalog['subjects'] and d.latest(state)==before
    report=dict(passed=True,tool_calls=len(calls)+len(tests)+1,checks=['full-source beyond 12 records','month and exact tag filters','compound module selection','upcoming order and bounded references','cancelled and occurred excluded','stable shared subject across modules and restart','invalid plans rejected','queries read-only'],subject_id=sid)
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);a=p.parse_args();run(a.output.resolve(),a.binary)
