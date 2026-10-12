"""Actual fresh-home consent boundary; never clicks or writes an approval."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

import native_runtime
from test_timeline_model import ShellProbe
from test_real_model_flow import UI

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', required=True)
    ap.add_argument('--core-dir', required=True)
    args = ap.parse_args()
    out = Path(args.output).resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    p = ShellProbe(out, ROOT/'bundle', shell_exe=native_runtime.binary('shell'),
                   hub=str(native_runtime.binary('hub')), core_dir=args.core_dir)
    checks = []
    try:
        p.wait_ready()
        u = UI(p)
        subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/'tools/sync_timeline_import.py'),
                        '--data-root', str(p.apps), '--out', str(out/'sync')],
                       capture_output=True, check=True)
        u.click('重新读取已导入数据')
        u.fill('experience_input', '请整理我是怎么开始攀岩的，只读取已有样本。')
        p.request('k', c='Return', wait=1)
        deadline = time.monotonic()+45
        labels = []
        while time.monotonic() < deadline:
            labels = [w.get('t', '') for w in u.widgets()]
            if any('Waiting for the person to allow' in t for t in labels):
                break
            time.sleep(.5)
        u.evidence('no-consent')
        checks.append({'name': 'explicit-host-consent-refusal',
                       'ok': any('Waiting for the person to allow' in t for t in labels)})
        audits = list((out/'core').rglob('tool_audit.jsonl'))
        checks.append({'name': 'no-tools-executed',
                       'ok': all(not f.read_text(encoding='utf-8').strip() for f in audits)})
        receipts = p.apps/p.app_id/'experience-agent-receipts.json'
        checks.append({'name': 'no-completed-turn-receipts',
                       'ok': not receipts.exists() or json.loads(receipts.read_text(encoding='utf-8')) == []})
        checks.append({'name': 'zero-business-writes', 'ok': u.state().get('records', []) == []})
        consent = out/'home/approvals/consent.json'
        granted = consent.exists() and json.loads(consent.read_text(encoding='utf-8')).get('apps', {}).get('dailyflow', {}).get('allowed') is True
        checks.append({'name': 'no-consent-granted', 'ok': not granted})
        assert all(x['ok'] for x in checks), checks
    finally:
        p.stop()
        (out/'report.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS fresh-home host consent boundary')


if __name__ == '__main__':
    main()
