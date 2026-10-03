#!/usr/bin/env python3
"""32 real Splash tool calls covering saves, receipts, privacy and storage failure.
Use a bridge-enabled card-host; this is not a Provider or Shell Agent test.
"""
import argparse
from pathlib import Path
import business_test_driver as driver
from business_test_driver import save,query,run,latest,FUTURE_DAY
PROJECT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="Verify real Splash business tools in fresh isolated data; no model or Shell Agent calls.")
parser.add_argument('--bundle', type=Path, default=PROJECT/'bundle')
parser.add_argument('--output', type=Path, required=True, help='New directory; existing output is refused.')
parser.add_argument('--binary', type=Path, default=PROJECT.parent/'OctoSense-App-Hub/target/release/card-host.exe')
args = parser.parse_args()
ROOT = driver.configure(args.bundle,args.output,args.binary)

import shutil,copy,json
R=ROOT/'acceptance-final';R.mkdir(exist_ok=True)
def run_case(name,calls,state=None):
 res=run('acceptance-final/'+name,calls,state)
 for i,r in res.items():assert r.get('ok') is True,(name,i,r)
 return {i:r['data'] for i,r in res.items()}
def seed(name,db):
 path=R/name/'state/dailyflow';path.mkdir(parents=True,exist_ok=True)
 (path/'state-a.json').write_text(json.dumps(db,ensure_ascii=False),encoding='utf8')
 return path.parent
state=R/'core/state'
calls=[save('core1'),save('core1'),save('core1',amount='46'),save('dup1'),save('future',date='2100-01-01'),save('invalid',amount='45.111'),save('kind',kind='oops'),save('period',kind='period',title='经期',amount='',flow_names=[]),save('task',kind='task',title='疫苗预约',date=FUTURE_DAY,amount='',time='09:00',user_tags=[]),query(flow_name='宠物照护'),save('bad-time',kind='task',title='无效时间',amount='',time='25:00'),save('empty-id',request_id=''),save('tags',title='测试标签',user_tags=['猫','猫']),save('bad-date',date='2026-02-30'),save('news',kind='news',title='新闻',amount='',source=''),query(limit=1)]
r=run_case('core',calls,state)
assert r[0]['ok'] and r[0]['flow_ids']==['f2'],r
assert r[1]['replayed'],r
for i in [2,3,4,5,6,7,10,11,12,13,14]:assert not r[i]['ok'],(i,r[i])
assert r[8]['ok'] and r[8]['flow_ids']==['f2'],r
assert r[9]['total']==2 and len(r[9]['flows'])==1,r[9]
assert r[15]['truncated'] and len(r[15]['records'])==1,r[15]
db=latest(state);assert len(db['records'])==2 and len(db['flows'])==1 and len(db['receipts'])==2,db
before=json.dumps(db,sort_keys=True)
r=run_case('restart',[save('core1'),save('core1',title='不同猫粮'),query()],state)
assert r[0]['replayed'] and not r[1]['ok'] and r[2]['total']==2,r
assert json.dumps(latest(state),sort_keys=True)==before
update=save('update1',record_id='r1',expected_revision=1,amount='46',flow_names=['家庭支出'])
r=run_case('update',[update,save('stale',record_id='r1',expected_revision=1,title='陈旧编辑'),query(record_id='r1')],state)
assert r[0]['ok'] and not r[1]['ok'],r
assert r[2]['records'][0]['cents']==4600 and len(r[2]['records'][0]['flow_ids'])==2,r
# Seed a valid historical database without additive fields and with private/hidden data.
old=copy.deepcopy(latest(state));old.pop('receipts',None)
for rec in old['records']:rec.pop('user_tags',None)
old['flows'][0]['hidden']=True
period=copy.deepcopy(old['records'][0]);period.update(id='r100',kind='period',title='私密标题',cents=0,flow_ids=[],source='',end_date='',revision=1)
old['records'].append(period);old['seq']=100;old['period_enabled']=True;old['private_hidden']=True
privacy=seed('privacy',old)
r=run_case('privacy',[query(),query(kind='period'),save('hidden',title='新猫粮',flow_names=['宠物照护']),save('legacy',title='普通支出',flow_names=['新 Flow'])],privacy)
assert r[0]['total']==2 and r[1]['total']==0 and not r[2]['ok'] and r[3]['ok'],r
assert '私密标题' not in json.dumps(r,ensure_ascii=False)
assert all(f['name']!='宠物照护' for f in r[0]['flows']),r
# Valid original state with blocked next write slot must not retain records, Flows or receipts.
failuredb=copy.deepcopy(old);failuredb['revision']=101
failure=seed('failure',failuredb);(failure/'dailyflow/state-b.json').mkdir()
nextsave=save('failed-once',title='应整体失败',flow_names=['失败空组'])
r=run_case('failure',[nextsave,query()],failure)
assert not r[0]['ok'] and r[1]['total']==2,r
assert latest(failure)==failuredb
(failure/'dailyflow/state-b.json').rmdir()
r=run_case('retry',[nextsave,query()],failure)
assert r[0]['ok'] and r[1]['total']==3,r
assert sum(f['name']=='失败空组' for f in latest(failure)['flows'])==1
# Corrupt storage cannot silently start a new ledger.
corrupt=R/'corrupt/state';(corrupt/'dailyflow').mkdir(parents=True)
for slot in ['a','b']:(corrupt/f'dailyflow/state-{slot}.json').write_text('{ broken',encoding='utf8')
r=run_case('corrupt',[save(),query()],corrupt);assert not r[0]['ok'] and not r[1]['ok'],r
report={'passed':True,'cases':['atomic save + explicit Flow','same-process replay','changed payload rejection','duplicate record rejection','future/amount/type/time/date/source validation','period opt-in','existing Flow reuse','query limit','restart replay without writes','revision update + stale rejection','multi Flow no duplicate record','old schema + private filtering','hidden same-name Flow rejection','failed persist leaves no record/Flow/receipt','retry after definite failure','corrupt state read-only'], 'tool_calls':len(calls)+3+3+4+2+2+2,'all_processes_stopped':True}
(R/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
