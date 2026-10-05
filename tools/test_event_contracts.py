"""Protocol-only Splash fixture + migration/fault contracts; no real Provider."""
import argparse,json,re,shutil
from pathlib import Path
import business_test_driver as d
from test_event_flow import apply,data
ROOT=Path(__file__).resolve().parents[1]

def run(out):
    d.configure(ROOT/'bundle',out,ROOT.parent/'OctoSense-App-Hub/target/release/card-host.exe')
    # A real minimal Splash app loads only the projection reducer, no expense UI/store.
    main=(ROOT/'src/20_calendar.splash').read_text(encoding='utf8')
    reducer=main[main.index('fn projection_accept'):main.index('fn calendar_rebuild')]
    fixture='''
fn on_agent_tool(token,name,args_json){
    let items = [] let up = {protocol_version: 1 source_app: "dailyflow" source_module: "expense" source_record_id: "x" source_revision: 2 operation: "upsert" amount_minor: 11000 date: "2026-10-04"}
    projection_accept(items,up) projection_accept(items,up)
    let old = up.to_json().parse_json() old.source_revision = 1 old.amount_minor = 12000 projection_accept(items,old)
    let good = items.len() == 1 && items[0].amount_minor == 11000
    let tomb = {protocol_version: 1 source_app: "dailyflow" source_module: "expense" source_record_id: "x" source_revision: 3 operation: "delete"}
    projection_accept(items,tomb) projection_accept(items,tomb) projection_accept(items,up)
    mod.app_tools.resolve(token,{"ok": good && items.len() == 1 && items[0].operation == "delete" count: items.len() revision: items[0].source_revision})
}
SolidView{width: Fill height: Fill Label{text: "Protocol fixture"}}
'''
    (out/'bundle/main.splash').write_text(reducer+fixture,encoding='utf8')
    r=d.run('protocol-only',[d.query()]);assert data(r,0)['ok'],r
    # Restore production code into this isolated copy; never touch formal bundle.
    shutil.copyfile(ROOT/'bundle/main.splash',out/'bundle/main.splash')
    state=out/'migration-state';folder=state/'dailyflow';folder.mkdir(parents=True)
    legacy=dict(schema_version=1,revision=10,seq=10,records=[],flows=[dict(id='old-hidden',name='PRIVATE_ARCHIVE',hidden=False,created_at=0)],alerts=[],budget_cents=0,budget_month='',budget_notified=False,period_enabled=True,private_hidden=False,receipts=[])
    def old_record(id,kind,title,fids):return dict(id=id,kind=kind,title=title,date=d.DAY,revision=1,end_date='',source='',cents=100 if kind=='expense' else 0,due_at=0,completed_at=0,reminded_due=0,status='recorded',created_at=0,updated_at=0,flow_ids=fids)
    legacy['records']=[old_record('old-e','expense','旧支出',[]),old_record('old-p','period','PRIVATE_RECORD',['old-hidden'])]
    (folder/'state-a.json').write_text(json.dumps(legacy,ensure_ascii=False),encoding='utf8')
    r=d.run('migration',[d.query(),apply('new',kind='expense',title='新支出',date=d.DAY,amount='2'),d.query()],state)
    assert data(r,0)['total']==1 and not data(r,0)['flows'],r
    assert 'PRIVATE_' not in json.dumps(r,ensure_ascii=False),r
    assert data(r,1)['ok'];assert d.latest(state)['records'][1]==legacy['records'][1]
    assert json.loads((folder/'pre-event-flow-v1.json').read_text(encoding='utf8'))==legacy
    # Storage failure: next dual slot is a directory, so write/readback fails.
    failed=out/'failed-state';f=failed/'dailyflow';f.mkdir(parents=True)
    failed_legacy=dict(legacy,revision=1);(f/'state-a.json').write_text(json.dumps(failed_legacy,ensure_ascii=False),encoding='utf8');(f/'state-b.json').mkdir()
    r=d.run('storage-fault',[apply('blocked',kind='expense',title='不应保存',date=d.DAY,amount='9'),d.query()],failed)
    assert not data(r,0)['ok'];assert data(r,1)['total']==1;assert json.loads((f/'state-a.json').read_text(encoding='utf8'))==failed_legacy
    report={'passed':True,'protocol_fixture_without_expense_ui':True,'checks':['duplicate revision idempotent','stale revision ignored','delete tombstone prevents resurrection','historical source bytes preserved semantically','unsupported records/Flow names excluded','pre-migration complete backup','actual slot write failure leaves prior state unchanged']}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output.resolve())
