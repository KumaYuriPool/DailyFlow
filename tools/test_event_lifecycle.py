"""Actual legacy-receipt compatibility, multi-Flow totals and plan lifecycle."""
import argparse,json,shutil
from pathlib import Path
import business_test_driver as d
from test_event_flow import apply,data
ROOT=Path(__file__).resolve().parents[1]
def run(out):
    d.configure(ROOT/'build/event-flow-r2/baseline/bundle',out,ROOT.parent/'OctoSense-App-Hub/target/release/card-host.exe')
    state=out/'state';old=d.save('old-receipt',title='历史费用',amount='10',flow_names=['旧事件'])
    r=d.run('old-runtime',[old],state);assert data(r,0)['ok']
    before=d.latest(state)
    for name in ['main.splash','tools.json','manifest.json','AGENT.md']:shutil.copyfile(ROOT/'bundle'/name,out/'bundle'/name)
    r=d.run('new-runtime',[old,d.query(),apply('multi',kind='expense',title='共用费用',date=d.DAY,amount='100',flow_names=['事件A','事件B']),d.query()],state)
    assert data(r,0)['replayed'],r
    assert data(r,1)['records'][0]['id']==before['records'][0]['id']
    q=data(r,3);a=next(f['id'] for f in q['flows'] if f['name']=='事件A');b=next(f['id'] for f in q['flows'] if f['name']=='事件B')
    graph=lambda fid:{'name':'dailyflow.flow_query','args':dict(flow_id=fid)}
    r=d.run('multi-plan',[graph(a),graph(b),graph(''),apply('plan',kind='event',title='明确计划',date='2026-10-01',status='planned',flow_id=a),d.query(kind='event')],state)
    assert data(r,0)['amount_minor']==10000 and data(r,1)['amount_minor']==10000 and data(r,2)['amount_minor']==11000
    plan=data(r,4)['records'][0];assert plan['status']=='planned'
    r=d.run('fulfill',[apply('done',kind='event',title='明确完成',date=d.DAY,status='occurred',flow_id=a,fulfills_id=plan['id']),graph(a),d.query(kind='event')],state)
    assert data(r,0)['ok'],r
    assert data(r,1)['plans']==0 and any(e['type']=='fulfills' for e in data(r,1)['relations'])
    done=next(e for e in data(r,2)['records'] if e['id']!=plan['id'])
    r=d.run('cancel',[apply('cancel',kind='event',title=done['title'],date=done['date'],status='cancelled',record_id=done['id'],expected_revision=done['revision']),graph(a),apply('dropA',operation='delete_flow',flow_id=a),graph(b),d.query()],state)
    assert data(r,0)['ok'] and data(r,1)['plans']==1
    assert data(r,2)['ok'] and data(r,3)['amount_minor']==10000
    assert len([r for r in data(r,4)['records'] if r['kind']=='expense'])==2
    latest=d.latest(state);assert latest['receipts'][0]==before['receipts'][0]
    report=dict(passed=True,checks=['actual 0.3.0 receipt replays under 0.4.0','legacy ID/revision retained','historical receipt byte content retained','two Flows one global expense','overdue plan remains planned','explicit fulfills relation','withdraw completion restores pending plan without expenses','delete one Flow keeps other membership and sources'])
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output.resolve())
