"""Real production clicks for currency totals, revision and membership decisions."""
import native_runtime
import argparse,json,sys,time,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_timeline_ui import TimelineProbe
from test_real_model_flow import UI
ROOT=Path(__file__).resolve().parents[1]

def main():
    a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args()
    out=Path(args.output).resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    p=TimelineProbe(out,ROOT/'bundle','1280x900',binary=native_runtime.binary("card_host"))
    checks=[]
    try:
        u=UI(p);u.click('布局');path=p.apps/p.app_id/'timeline-imported.json'
        base={'topic':'核验','date':'2026-10-01','title':'核验费用','body':'原始金额','source_app':'a','source_module':'expense','record_id':'same','revision':1,'kind':'expense','amount_minor':1200,'currency':'CNY','excluded':False,'suspicious':False,'future':False,'citation':'fixture','tags':[]}
        data={'records':[base,{**base,'source_app':'b','title':'另一来源费用','amount_minor':500,'currency':'USD'}],'sources':[{'source_app':'a','records':1},{'source_app':'b','records':1}],'gaps':[],'topics':['核验'],'topic':'核验','adoption_layer':'isolated-ui-fixture','generated_at':'2026-10-12T00:00:00Z'}
        def write():path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        write();u.click('重新读取已导入数据');u.click('浏览 · 核验');u.click('保存为经历')
        def ck(name,needle):
            ok=any(needle in w.get('t','') for w in u.widgets());checks.append({'name':name,'ok':ok});assert ok,name
        ck('pending-cny','CNY 已确认 0.00 / 待核对 12.00');ck('pending-usd','USD 已确认 0.00 / 待核对 5.00')
        u.click('确认计入这段经历')
        ck('confirm-cny-only','CNY 已确认 12.00 / 待核对 0.00');ck('usd-independent','USD 已确认 0.00 / 待核对 5.00')
        u.evidence('01-confirmed')
        data['records'][0]['revision']=2;data['records'][0]['amount_minor']=1000;write();u.click('重新读取')
        ck('revision-invalidates-confirmation','CNY 已确认 0.00 / 待核对 10.00');ck('revision-feedback','来源已更正，请重新核对费用。')
        u.click('确认计入这段经历');u.click('从这段经历移除')
        ck('other-source-same-id-survives','USD 已确认 0.00 / 待核对 5.00')
        u.click('已排除');u.click('恢复到这段经历');u.click('返回时间流')
        ck('restore-keeps-fee-decision','CNY 已确认 10.00 / 待核对 0.00')
        p.stop();p.start();u=UI(p);u.click('核验')
        ck('restart-keeps-confirmation','CNY 已确认 10.00 / 待核对 0.00')
        u.evidence('02-restarted')
        assert u.state().get('records',[])==[]
        checks.append({'name':'no-business-writes','ok':True})
    except BaseException:
        u.evidence('failure');raise
    finally:
        p.stop();(out/'report.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS',len(checks),'expense UI checks')

if __name__=='__main__':main()
