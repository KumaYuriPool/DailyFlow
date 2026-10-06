"""Real Provider acceptance for subject grouping and explicit expense tags."""
import argparse
import json
import time
from pathlib import Path

from desktop_flow_probe import DesktopProbe, ROOT
from test_real_model_flow import UI


def run(probe, expected_model_calls=3):
    probe.wait_ready()
    ui = UI(probe)
    timings = []

    def send(text, name):
        ui.fill('chat_input', text)
        started = time.monotonic()
        ui.click('发送')
        end = time.monotonic() + 55
        while time.monotonic() < end:
            if not any(w.get('t') in ('正在理解…', '正在处理…') for w in ui.widgets()):
                break
            time.sleep(.4)
        ui.evidence(name)
        labels = [w.get('t', '') for w in ui.widgets() if w.get('ty') == 'Label']
        assert not any('模型请求失败' in t or '模型超时' in t or '模型返回' in t for t in labels), labels
        assert not any(w.get('t') == '补充并继续' for w in ui.widgets()), labels
        timings.append({'scenario': name, 'seconds': round(time.monotonic()-started, 3)})
        print(name + ' completed ' + str(timings[-1]['seconds']) + 's', flush=True)

    send('给团子洗护花了120元。', '01-grooming')
    first = ui.state()
    assert len(first['flows']) == 1 and first['flows'][0]['name'] == '团子', first
    fid = first['flows'][0]['id']
    assert len(first['records']) == 1 and first['records'][0]['cents'] == 12000, first
    send('给团子买猫粮花了120元。', '02-food')
    second = ui.state()
    assert len(second['flows']) == 1 and len(second['records']) == 2, second
    assert all(r['flow_ids'] == [fid] and not r['user_tags'] for r in second['records']), second
    assert sum(r['cents'] for r in second['records']) == 24000
    food = next(r for r in second['records'] if r['id'] != first['records'][0]['id'])
    assert not any(e['type'] == 'expense_for' and e['to_node'] == food['id'] for e in second['relations']), second
    send('团子一共花了多少钱？', '03-total')
    assert ui.state() == second, 'Query changed business data'
    assert any('240.00' in w.get('t', '') for w in ui.widgets())
    send('又给团子买了一袋猫粮花了55元，加标签猫粮。', '04-explicit-tag')
    final = ui.state()
    assert len(final['flows']) == 1 and len(final['records']) == 3, final
    tagged = next(r for r in final['records'] if r['cents'] == 5500)
    assert tagged['user_tags'] == ['猫粮'] and tagged['flow_ids'] == [fid], final
    assert all(not r['user_tags'] for r in final['records'] if r['id'] != tagged['id']), final
    assert any('#猫粮' in w.get('t', '') for w in ui.widgets())
    ledger = json.loads((probe.apps/'.host/model/ledger.json').read_text(encoding='utf8'))['apps']['dailyflow']
    assert ledger['calls'] == expected_model_calls and ledger['tokens'] > 0
    report = {'passed': True, 'real_provider': True, 'messages': 4, 'requests': ledger['calls'], 'usage': ledger, 'timings': timings,
              'shared_subject': '团子', 'initial_total_minor': 24000,
              'ordinary_food_has_no_tag_or_grooming_link': True, 'explicit_tag': '猫粮',
              'query_did_not_write': True, 'final_total_minor': 29500}
    (probe.output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, default=ROOT/'bundle')
    parser.add_argument('--expected-model-calls', type=int, default=3)
    parser.add_argument('--core-dir', type=Path, default=Path.home()/'.octosense/octos-home/.octos')
    args = parser.parse_args()
    probe = DesktopProbe(args.bundle, args.output, core_dir=args.core_dir)
    try:
        run(probe, args.expected_model_calls)
    finally:
        probe.stop()
