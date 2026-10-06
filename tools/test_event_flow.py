"""Real Splash/card-host contract tests in a fresh isolated output directory."""
import argparse,json
from pathlib import Path
import business_test_driver as d

def apply(req,**kw):return {'name':'dailyflow.apply','args':dict(request_id=req,**kw)}
def data(results,i):
    assert results[i]['ok'],results[i]
    return results[i]['data']

def run(output,binary=None):
    d.configure(Path('bundle'),output,Path(binary or '../OctoSense-App-Hub/target/release/card-host.exe'))
    state=output/'state'
    first=apply('golden',kind='expense',title='团子洗护费',date=d.DAY,amount='120',subject='团子',topic='护理',event_title='团子洗护',plan_title='再次护理',plan_date=d.FUTURE_DAY,plan_time='15:00',evidence='用户明确事项及后续安排')
    results=d.run('create',[first,first,d.query(),{'name':'dailyflow.flow_query','args':{}}],state)
    assert data(results,0)['ok'],results
    assert data(results,1)['replayed'],results
    q=data(results,2);assert len(q['records'])==3,q
    expense=next(r for r in q['records'] if r['kind']=='expense');event=next(r for r in q['records'] if r['kind']=='event' and r['status']=='occurred')
    fid=q['flows'][0]['id'];eid=expense['id']
    graph=data(results,3);assert graph['amount_minor']==12000
    results=d.run('update',[apply('correct',kind='expense',record_id=eid,expected_revision=expense['revision'],title=expense['title'],date='2026-09-30',amount='110'),apply('stale',kind='expense',record_id=eid,expected_revision=expense['revision'],title='stale',date=d.DAY,amount='999'),{'name':'dailyflow.flow_query','args':{'flow_id':fid}},d.query()],state)
    assert data(results,0)['ok'] and not data(results,1)['ok'],results
    graph=data(results,2);assert graph['amount_minor']==11000 and {e['type'] for e in graph['relations']}=={'belongs_to','expense_for','follow_up'},graph
    q=data(results,3);expense=next(r for r in q['records'] if r['id']==eid)
    # Failed compound must not leave expense, event, Flow, relation or receipt behind.
    before=d.latest(state)
    results=d.run('failure',[apply('bad',kind='expense',title='失败复合',date=d.DAY,amount='35',subject='另一主体',topic='维修',event_title='维修',plan_title='复查',plan_date='bad'),d.query()],state)
    assert not data(results,0)['ok'];assert d.latest(state)==before
    results=d.run('delete',[apply('delete',operation='delete',record_id=eid,expected_revision=expense['revision']),first,{'name':'dailyflow.flow_query','args':{'flow_id':fid}},apply('drop',operation='delete_flow',flow_id=fid),d.query()],state)
    assert data(results,0)['ok'] and data(results,1)['replayed'];assert data(results,2)['amount_minor']==0
    assert data(results,3)['ok'];assert len(data(results,4)['records'])==2
    latest=d.latest(state);assert len(latest['tombstones'])==1 and latest['relations']==[]
    assert (state/'dailyflow/pre-event-flow-v1.json').exists()
    report={'passed':True,'real_splash_calls':15,'checks':['compound independent fact/expense/plan IDs','typed semantic relations','durable replay','same-ID correction','stale revision rejected','compound failure rollback','expense delete preserves events','receipt replay does not revive deletion','Flow delete preserves source events','restart persistence','migration backup']}
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path);args=p.parse_args();run(args.output,args.binary)
