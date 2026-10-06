"""Exercise DailyFlow's actual model service with synthetic data and an existing Provider.

Requires a full desktop binary and a Python environment with cryptography.
Never copies credentials or uses personal business state. Makes three real requests.
"""
import argparse
import json
import time
from pathlib import Path

from desktop_flow_probe import DesktopProbe, ROOT
from test_real_model_flow import UI


def run(probe):
    probe.wait_ready()
    ui = UI(probe)
    calls = []

    def send(text, name):
        ui.fill('chat_input', text)
        started = time.monotonic()
        ui.click('发送')
        while time.monotonic() - started < 55:
            if not any(w.get('t') in ('正在理解…', '正在处理…') for w in ui.widgets()):
                break
            time.sleep(.4)
        ui.evidence(name)
        labels = [w.get('t', '') for w in ui.widgets() if w.get('ty') == 'Label']
        errors = [t for t in labels if '模型请求失败' in t or '模型超时' in t or '模型返回' in t]
        assert not errors, errors
        assert not any(w.get('t') == '补充并继续' for w in ui.widgets()), labels
        timing = {'scenario': name, 'seconds': round(time.monotonic()-started, 2)}
        metric_file = probe.apps/probe.app_id/'test-model-metrics.json'
        if metric_file.exists():
            timing['app_metrics'] = json.loads(metric_file.read_text(encoding='utf8'))
        calls.append(timing)
        print(name+' completed', flush=True)

    send('今天给小白买猫粮花了35元，记到小白的宠物照护事件。', '01-create')
    first = ui.state()
    assert len(first['records']) == 1 and first['records'][0]['cents'] == 3500, first
    assert len(first['flows']) == 1 and first['records'][0]['flow_ids'] == [first['flows'][0]['id']], first
    record_id = first['records'][0]['id']
    send('刚才给小白买猫粮不是35元，是32元。', '02-correct')
    corrected = ui.state()
    assert len(corrected['records']) == 1
    assert corrected['records'][0]['id'] == record_id and corrected['records'][0]['cents'] == 3200
    send('小白的宠物照护事件目前一共支出了多少？', '03-query')
    assert ui.state() == corrected, 'A query must not write or duplicate data'
    assert any('32.00' in w.get('t', '') for w in ui.widgets())
    ledger = json.loads((probe.apps/'.host/model/ledger.json').read_text(encoding='utf8'))
    usage = ledger['apps']['dailyflow']
    assert usage['calls'] == 3 and usage['tokens'] > 0
    report = {'passed': True, 'real_provider': True, 'requests': calls,
              'same_record_id': record_id, 'total_minor': 3200, 'query_did_not_write': True,
              'host_ledger_calls': usage['calls'], 'host_ledger_tokens': usage['tokens']}
    (probe.output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--core-dir', required=True, type=Path)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--bundle', type=Path, default=ROOT/'bundle')
    args = parser.parse_args()
    probe = DesktopProbe(args.bundle, args.output, core_dir=args.core_dir, binary=args.binary)
    try:
        run(probe)
    finally:
        probe.stop()
