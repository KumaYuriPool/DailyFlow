"""Source relations without a Flow, calendar composition and receipt-only repair."""
import argparse,json,copy
from pathlib import Path
import business_test_driver as d
from test_event_flow import apply,data

def run(out,binary):
 d.configure(Path('bundle'),out,binary);state=out/'state';calls=0
 main=out/'bundle/main.splash';original=main.read_text(encoding='utf8')
 hook='''if name == "dailyflow.flow_query" && a.flow_id == "__calendar_probe" {
 let ordinary = calendar_query(today(),"","","ordinary") let ledger = calendar_query(today(),"","","ledger") let labels = []
 for e in ordinary { labels.push(calendar_item_label(e)) }
 tools.resolve(token,{"ok": true ordinary: ordinary ledger: ledger labels: labels total: calendar_sum(today(),"","") valid: valid_db(db)}) return
 }
 '''
 main.write_text(original.replace('let a = args_json.parse_json()', 'let a = args_json.parse_json()\n'+hook),encoding='utf8')
 def batch(name,*ops,root=None):
  nonlocal calls
  calls+=len(ops);raw=d.run(name,list(ops),root or state);return [data(raw,i) for i in range(len(ops))]
 probe=dict(name='dailyflow.flow_query',args={'flow_id':'__calendar_probe'})
 req=apply('spa',kind='expense',title='SPA花费',date=d.DAY,amount='350',event_title='做SPA')
 created,replay=batch('create',req,req);assert created['ok'] and replay['replayed']
 q,=batch('calendar',probe);assert q['valid'] and len(q['ordinary'])==len(q['ledger'])==1 and q['total']==35000 and q['labels']==['已发生 · 做SPA · ¥350.00']
 before=d.latest(state);assert not before['flows'] and len(before['relations'])==1
 pristine=copy.deepcopy(before);expense=before['records'][0];event=before['calendar_events'][0]
 recall,=batch('recall',dict(name='dailyflow.recall',args={'text':'做SPA'}));assert recall['total']==2
 corrected,=batch('correct',apply('correct',kind='expense',record_id=expense['id'],expected_revision=expense['revision'],title='SPA花费',date=d.DAY,amount='320'));assert corrected['ok']
 q,=batch('corrected',probe);assert q['labels']==['已发生 · 做SPA · ¥320.00'] and q['total']==32000
 moved,=batch('move',apply('move',kind='expense',record_id=expense['id'],expected_revision=2,title='SPA花费',date='2026-09-30',amount='320'));assert moved['ok']
 q,=batch('cross-day',probe);assert q['labels']==['已发生 · 做SPA'] and q['total']==0
 undone,=batch('cancel',apply('cancel',kind='event',record_id=event['id'],expected_revision=event['revision'],title='做SPA',date=d.DAY,status='cancelled'));assert undone['ok']
 assert not d.latest(state)['relations']
 # Global follow-up and fulfills must remain source relations without creating containers.
 compound,=batch('followup',apply('activity',kind='expense',title='按摩费',event_title='按摩',date=d.DAY,amount='50',plan_title='下次按摩',plan_date=d.FUTURE_DAY));assert compound['ok']
 current=d.latest(state);plan=next(e for e in current['calendar_events'] if e['status']=='planned')
 fulfilled,=batch('fulfilled',apply('done',kind='event',title='提前按摩',date=d.DAY,status='occurred',fulfills_id=plan['id']));assert fulfilled['ok'] and not d.latest(state)['flows']
 # Synthetic pre-fix save: remove precisely the edge the old version omitted.
 legacy=copy.deepcopy(pristine);legacy['relations']=[]
 def seed(name,value):
  dest=out/name;folder=dest/'dailyflow';folder.mkdir(parents=True);(folder/'state-a.json').write_text(json.dumps(value,ensure_ascii=False),encoding='utf8');return dest
 repair=seed('legacy',legacy)
 fixed,=batch('repair',probe,root=repair);assert fixed['labels']==['已发生 · 做SPA · ¥350.00']
 after=d.latest(repair);assert after['revision']==legacy['revision']+1 and after['source_relations_version']==1 and len(after['relations'])==1
 for key in ['records','calendar_events','flows','receipts','seq']:assert after[key]==legacy[key]
 backup=repair/'dailyflow'/f"pre-source-relations-v1-{legacy['revision']}.json";assert json.loads(backup.read_text(encoding='utf8'))==legacy
 batch('repair-restart',probe,root=repair);assert d.latest(repair)==after
 # Near matches, edited sources, missing receipts and conflicting relations are not evidence.
 for name,edit in [('no-receipt',lambda s:s.update(receipts=[])),('changed',lambda s:s['records'][0].update(revision=2)),('distant',lambda s:s['calendar_events'][0].update(created_at=s['records'][0]['created_at']+20,updated_at=s['records'][0]['created_at']+20)),('wrong-id',lambda s:s['calendar_events'][0].update(id='evt999')),('existing-edge',lambda s:s.update(relations=copy.deepcopy(pristine['relations'])))]:
  sample=copy.deepcopy(legacy);edit(sample);dest=seed(name,sample);batch('check-'+name,probe,root=dest);assert d.latest(dest)==sample
 failed=seed('backup-blocked',legacy);(failed/'dailyflow'/backup.name).mkdir();batch('backup-fault',probe,root=failed);assert d.latest(failed)==legacy
 failed=seed('write-blocked',legacy);(failed/'dailyflow'/'state-b.json').mkdir();batch('write-fault',probe,root=failed);assert d.latest(failed)==legacy
 # Deleting the event restores its standalone expense instead of losing the money.
 delete_state=seed('delete-state',pristine)
 deleted,=batch('delete-event',apply('delete-event',operation='delete',record_id=event['id'],expected_revision=event['revision']),root=delete_state);assert deleted['ok']
 q,=batch('after-delete',probe,root=delete_state);assert q['labels']==['SPA花费  ¥350.00'] and q['total']==35000
 assert not d.latest(delete_state)['relations']
 report=dict(passed=True,tool_calls=calls,real_provider=False,checks=['ungrouped compound relation','single ordinary item with amount / ledger counted once','same-ID correction','cross-day expense preserved','withdraw/delete lifecycle','global follow-up/fulfillment','receipt-only repair','backup and source/receipt identity preserved','restart idempotent','near matches not repaired','backup/write failures preserve state'])
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);a=p.parse_args();run(a.output,a.binary)
