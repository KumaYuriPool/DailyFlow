"""Actual public octos turn -> own read tool -> validated experience UI.
Never accepts a consent dialog. The human may approve in this isolated window.
"""
import native_runtime
import argparse,json,subprocess,sys,time,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_timeline_model import ShellProbe
from test_real_model_flow import UI
ROOT=Path(__file__).resolve().parents[1]

def main():
    a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--core-dir',required=True);a.add_argument('--wait-consent',type=int,default=180);a.add_argument('--human-ready',action='store_true');a.add_argument('--consent-home');args=a.parse_args()
    out=Path(args.output).resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    p=ShellProbe(out,ROOT/'bundle',shell_exe=native_runtime.binary("shell"),hub=str(native_runtime.binary("hub")),core_dir=args.core_dir,consent_home=args.consent_home,hidden=not args.human_ready)
    checks=[]
    try:
        p.wait_ready();u=UI(p)
        subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/sync_timeline_import.py'),'--data-root',str(p.apps),'--out',str(out/'sync')],capture_output=True,check=True)
        u.click('重新读取已导入数据')
        # The root agent writes this marker only after the user's explicit reply.
        if args.human_ready:
            print('WAITING HUMAN: isolated host is ready; allow DailyFlow agent then reply.',flush=True)
            while not (out/'human-ready').exists(): time.sleep(1)
        # Consent may be displayed on launch; do not click it.
        deadline=time.monotonic()+args.wait_consent
        while time.monotonic()<deadline:
            labels=[w.get('t','') for w in u.widgets()]
            if not any('Allow'==t or '允许'==t or 'Allow agent' in t for t in labels): break
            (out/'waiting-consent.json').write_text(json.dumps({'labels':labels},ensure_ascii=False,indent=2),encoding='utf-8')
            print('WAITING HUMAN CONSENT',flush=True);time.sleep(10)
        for index,(question,title) in enumerate([
            ('请整理我是怎么开始攀岩的，结合社媒、日历和费用。只读取已有样本，不写入原始数据。','攀岩，慢慢成为习惯'),
            ('改为回顾那场演出的前前后后，结合社媒、日历和费用。只读取已有样本。','一场演出的前前后后')]):
            u.fill('experience_input',question);p.request('k',c='Return',wait=1)
            deadline=time.monotonic()+210
            while time.monotonic()<deadline:
                labels=[w.get('t','') for w in u.widgets()]
                if any('已整理 ' in t or '助手暂不可用' in t or '关联整理暂不可用' in t or '关联结果' in t or '计划超出' in t or '超时' in t for t in labels): break
                time.sleep(.6)
            u.evidence(f'{index+1}-result');labels=[w.get('t','') for w in u.widgets()]
            print(json.dumps({'result':labels},ensure_ascii=False),flush=True)
            ok=title in labels and any('已整理 ' in t for t in labels)
            checks.append({'name':title,'ok':ok,'adapter':'official'})
            assert ok,labels
            u.click('整理过程');u.evidence(f'{index+1}-events')
            labels=[w.get('t','') for w in u.widgets()]
            assert any('官方 Agent' in t for t in labels),labels
            u.click('整理过程')
        receipts=json.loads((p.apps/p.app_id/'experience-agent-receipts.json').read_text(encoding='utf-8'))
        assert len(receipts)==4 and len({x['turn_id'] for x in receipts})==4
        checks.append({'name':'four-real-new-turns-for-two-two-stage-tasks','ok':True,'receipts':receipts})
        audits=[]
        for f in (out/'core/profiles/_main/data/peers').glob('*/tool_audit.jsonl'):
            audits += [json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip()]
        (out/'tool-audit.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2),encoding='utf-8')
        assert any('dailyflow.experience_context' in json.dumps(x) for x in audits)
        assert not any('dailyflow.save_record' in json.dumps(x) for x in audits)
        checks.append({'name':'official-read-tool-audit','ok':True})
        store=p.apps/p.app_id/'experiences-v1.json'
        before=store.read_bytes()
        u.fill('experience_input','请再次重新整理演出经历，仅只读。');p.request('k',c='Return',wait=0.1)
        u.click('停止');time.sleep(4)
        assert store.read_bytes()==before
        assert any('已停止展示' in w.get('t','') for w in u.widgets())
        u.evidence('3-cancelled')
        checks.append({'name':'real-interrupt-no-late-result-or-source-write','ok':True})
        assert u.state().get('records',[])==[]
        checks.append({'name':'zero-source-writes','ok':True})
    except BaseException:
        if 'u' in locals():u.evidence('failure')
        raise
    finally:
        p.stop();(out/'report.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS official Agent two-story experience tasks and zero writes')

if __name__=='__main__':main()
