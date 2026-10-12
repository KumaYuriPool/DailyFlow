"""Real Provider -> validated experience plan -> actual imported records -> UI."""
import native_runtime
import argparse,json,subprocess,sys,time,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_timeline_model import ShellProbe
from test_real_model_flow import UI
ROOT=Path(__file__).resolve().parents[1]

def main():
    a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--core-dir',required=True);args=a.parse_args()
    out=Path(args.output).resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    p=ShellProbe(out,ROOT/'bundle',shell_exe=native_runtime.binary("shell"),hub=str(native_runtime.binary("hub")),core_dir=args.core_dir)
    checks=[]
    try:
        p.wait_ready();u=UI(p)
        subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/sync_timeline_import.py'),'--data-root',str(p.apps),'--out',str(out/'sync')],capture_output=True,check=True)
        u.click('重新读取已导入数据')
        u.click('设置');u.click('助手入口 · official');u.click('回到经历')
        for index,(question,title,needle) in enumerate([
            ('请整理我是怎么开始攀岩的，结合社媒、日历和费用。只读取已有样本，不写入原始数据。','攀岩，慢慢成为习惯','synthetic-climbing'),
            ('改为回顾那场演出的前前后后，结合社媒、日历和费用。只读取已有样本。','一场演出的前前后后','synthetic-concert')]):
            u.fill('experience_input',question)
            p.request('k',c='Return',wait=1)
            deadline=time.monotonic()+240
            while time.monotonic()<deadline:
                labels=[w.get('t','') for w in u.widgets()]
                if any('已整理 ' in t or '关联结果' in t or '关联整理暂不可用' in t or '助手暂不可用' in t or '计划超出' in t or '超时' in t for t in labels): break
                time.sleep(.5)
            u.evidence(f'{index+1}-result')
            labels=[w.get('t','') for w in u.widgets()]
            ok=title in labels and any('已整理 ' in t for t in labels)
            checks.append({'name':title,'ok':ok,'real_provider':True})
            assert ok,labels
            u.click('整理过程')
            u.evidence(f'{index+1}-events')
            labels=[w.get('t','') for w in u.widgets()]
            assert any(needle in t for t in labels),labels
            u.click('整理过程')
        assert u.state().get('records',[])==[]
        checks.append({'name':'zero-source-writes','ok':True})
    except BaseException:
        if 'u' in locals():u.evidence('failure')
        raise
    finally:
        p.stop()
        (out/'report.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS real Provider two-story experience plans and zero writes')

if __name__=='__main__': main()
