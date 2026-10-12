"""Production Splash experience UI, isolated synthetic source and real clicks."""
import native_runtime
import argparse, hashlib, json, subprocess, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_timeline_ui import TimelineProbe
from test_real_model_flow import UI
ROOT = Path(__file__).resolve().parents[1]
HOST = native_runtime.binary("card_host")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    ap.add_argument('--wide', action='store_true')
    args = ap.parse_args()
    out = Path(args.output).resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    p = TimelineProbe(out,ROOT/'bundle','1280x900' if args.wide else '412x892',binary=HOST)
    checks = []
    def ck(name, ok):
        checks.append({'name':name,'ok':bool(ok)})
        (out/'report.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
        assert ok,name
        print('PASS',name,flush=True)
    try:
        u=UI(p)
        texts=lambda: [w.get('t','') for w in u.widgets()]
        if args.wide: u.click('布局')
        work=out/'sync'
        sync=lambda: subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/sync_timeline_import.py'),'--data-root',str(p.apps),'--out',str(work)],capture_output=True,check=True)
        sync()
        u.click('重新读取已导入数据')
        u.click('浏览 · 攀岩，慢慢成为习惯')
        ck('two-stories-catalog', '文件导入样本' in ' '.join(texts()))
        u.click('保存为经历')
        store=p.apps/p.app_id/'experiences-v1.json'
        ck('saved-separate-experience',json.loads(store.read_text(encoding='utf-8'))['items'][0]['id']=='experience-1')
        u.evidence('01-experience')
        u.click('查看记录')
        ck('own-detail',any('climb-post-001' in t for t in texts()))
        u.evidence('02-detail')
        u.click('‹ 返回时间流')
        u.click('从这段经历移除')
        ck('scoped-exclusion',any(d['experience']=='experience-1' and d['kind']=='membership' for d in json.loads(store.read_text(encoding='utf-8'))['decisions']))
        u.click('重新读取')
        u.click('已排除')
        ck('removed-accessible',any('B 站的攀岩入门视频' in t for t in texts()))
        u.click('恢复到这段经历')
        u.click('返回时间流')
        ck('restored',any('B 站的攀岩入门视频' in t for t in texts()))
        u.click('从这段经历移除')
        u.click('撤销上次决定')
        ck('undo',any('B 站的攀岩入门视频' in t for t in texts()))
        # Actual producer correction -> validated importer -> refreshed UI detail.
        u.click('查看记录')
        env=json.loads((work/'climbing/page-01-posts.json').read_text(encoding='utf-8'))
        rec=env['records'][0]
        rec['source_revision']=30
        rec['content']['title']='UX验收更正后的攀岩收藏'
        rec['content_hash']=hashlib.sha256(json.dumps(rec['content'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        env['records']=[rec];env['tombstones']=[];env['snapshot_revision']=30
        overlay=work/'climbing/page-06-ux.json'
        overlay.write_text(json.dumps(env,ensure_ascii=False),encoding='utf-8')
        sync();u.click('重新读取')
        detail_labels=texts()
        if not args.wide:
            for _ in range(4):
                p.request('m',k='scroll',x=270,y=500,dy=150,wait=1)
                detail_labels+=texts()
        ck('live-detail-correction',any('UX验收更正后的攀岩收藏'==t for t in detail_labels) and any('rev 30' in t for t in detail_labels))
        u.evidence('03-corrected')
        env['records']=[]
        env['tombstones']=[{'source_app':env['source_app'],'source_module':env['source_module'],'source_record_id':rec['source_record_id'],'source_revision':31,'deleted_at':'2026-10-12T02:00:00Z','content_hash':'0'*64}]
        env['snapshot_revision']=31
        overlay.write_text(json.dumps(env,ensure_ascii=False),encoding='utf-8')
        sync();u.click('重新读取')
        ck('deleted-detail-invalidated',any('旧内容已隐藏' in t for t in texts()) and not any(t=='UX验收更正后的攀岩收藏' for t in texts()))
        u.evidence('04-deleted')
        u.click('‹ 返回时间流')
        u.click('设置')
        u.click('停止读取 · synthetic-climbing')
        u.click('回到经历')
        ck('source-opt-out',not any('synthetic-climbing'==t or '动态 · synthetic-climbing'==t for t in texts()))
        u.click('设置');u.click('允许读取 · synthetic-climbing');u.click('回到经历')
        u.click('+ 新建经历')
        ck('draft-preserved',len(json.loads(store.read_text(encoding='utf-8'))['items'])==2)
        u.click('浏览 · 一场演出的前前后后')
        ck('second-story',any('一场演出的前前后后'==t for t in texts()))
        u.evidence('05-concert')
        ck('zero-source-writes',u.state().get('records',[])==[])
        p.stop();p.start();u=UI(p)
        ck('restart-directory',any('攀岩，慢慢成为习惯'==t for t in texts()))
        u.click('攀岩，慢慢成为习惯')
        ck('restart-no-resurrection',not any('UX验收更正后的攀岩收藏'==t for t in texts()))
        u.evidence('06-restarted')
    except BaseException:
        u.evidence('failure')
        raise
    finally:
        p.stop()
    return 0

if __name__=='__main__': sys.exit(main())
