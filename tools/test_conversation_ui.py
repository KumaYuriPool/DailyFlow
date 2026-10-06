"""Real card-host UI regression; synthetic data, no real Provider claims."""
import argparse, json, time
from pathlib import Path
from test_workspace_ui import Probe
from test_real_model_flow import UI


class WorkspaceUI(UI):
    def texts(self):
        return [w.get('t', '') for w in self.widgets()]

    def context(self):
        return next(t for t in self.texts() if t.startswith(('今天 · ', '补记 · ')))

    def seek(self, text):
        for _ in range(10):
            targets = [w for w in self.widgets() if w.get('t') == text and w.get('ty') == 'Button' and 155 < w['r'][1] < 718]
            if targets:
                x,y,width,height = targets[0]['r']
                self.probe.request('click', x=x+width/2, y=y+height/2, wait=1)
                time.sleep(.2)
                return
            self.probe.request('m', k='scroll', x=230, y=510, dy=250, wait=1)
            time.sleep(.15)
        raise AssertionError('Unreachable: '+text)

    def evidence(self, name):
        super().evidence(name)
        for w in self.widgets():
            x,y,width,height = w['r']
            if w.get('ty') in ('Button', 'TextInput') and 30 < y < 890:
                assert x >= 0 and x+width <= 413, (name, 'horizontal overflow', w)

    def flow_picker(self):
        self.click(next(t for t in self.texts() if t.startswith('Flow · ')))


def run(p):
    ui = WorkspaceUI(p)
    time.sleep(.5)
    initial = ui.state()
    context = ui.context()
    ui.find('今天发生了什么？')
    assert not any('记好了' in t or t == '今天给团子洗护花了120元。' for t in ui.texts())
    ui.evidence('01-home')
    ui.fill('chat_input', '尚未发送的草稿')
    ui.click('全部')
    ui.fill('picker_search', '不存在')
    ui.find('没有匹配结果')
    ui.fill('picker_search', '记账')
    assert len([w for w in ui.widgets() if w.get('t') == '账本' and w['r'][0] > 52]) == 1
    ui.evidence('02-app-search')
    ui.click('‹ 关闭选择')
    assert ui.find(ident='chat_input')['t'] == '尚未发送的草稿'
    ui.click('日历')
    ui.click('3')
    assert ui.context() == context, 'Browsing must not change input date'
    ui.click('普通日历 ▾')
    ui.fill('picker_search', '记账')
    ui.find('账本日历 · 来源：记账')
    assert '普通日历 · 来源：日历' not in ui.texts()
    ui.evidence('03-view-search')
    ui.click('账本日历 · 来源：记账')
    assert ui.find(ident='date_jump')['t'] == '2026-10-03'
    ui.find('¥275')
    assert ui.context() == context
    ui.evidence('04-ledger-calendar')
    ui.click('以这一天补记')
    assert ui.context().startswith('补记 · 2026-10-03')
    assert ui.find(ident='chat_input')['t'] == '尚未发送的草稿'
    ui.evidence('05-backfill')
    ui.flow_picker()
    ui.fill('picker_search', '团子')
    ui.find('团子 · 洗护')
    ui.evidence('06-flow-search')
    ui.click('团子 · 洗护')
    assert ui.context() == '补记 · 2026-10-03 · 团子 · 洗护'
    ui.find('团子 · 洗护 · 支出 ¥275.00 · 1 项计划')
    ui.click('日历')
    ui.find('此事件')
    ui.click('账本日历 ▾')
    ui.click('普通日历 · 来源：日历')
    ui.find('此事件')
    assert ui.find(ident='date_jump')['t'] == '2026-10-03'
    ui.click('›')
    assert ui.find(ident='date_jump')['t'] == '2026-11-03'
    ui.click('普通日历 ▾')
    ui.click('账本日历 · 来源：记账')
    assert ui.find(ident='date_jump')['t'] == '2026-11-03'
    assert ui.context() == '补记 · 2026-10-03 · 团子 · 洗护'
    ui.click('‹')
    ui.click('4')
    ui.evidence('07-scoped-calendar')
    ui.click('回到对话')
    ui.click('查看事件关系')
    ui.evidence('08-graph')
    ui.seek('记账 · 洗护费 ¥110.00')
    ui.find('¥110.00')
    assert not any(w.get('i') == 'record_amount' for w in ui.widgets())
    ui.click('修改')
    ui.fill('record_amount', '111')
    ui.fill('record_date', '2026-10-03')
    ui.click('保存记录')
    updated = ui.state()
    assert len(updated['records']) == 3
    assert next(r for r in updated['records'] if r['id'] == 'r2')['cents'] == 11100
    ui.find('¥111.00')
    ui.evidence('09-corrected-source')
    ui.click('‹ 返回')
    ui.find('记账 · 洗护费 ¥111.00')
    ui.click('回到对话')
    ui.click('+ 说件新事')
    assert ui.context() == context
    assert ui.find(ident='chat_input')['t'] == '记录、查询或更正…'
    assert '查看事件关系' not in ui.texts()
    ui.fill('chat_input', '今天买午餐35元')
    ui.click('发送')
    time.sleep(.5)
    assert ui.state() == updated
    assert any('失败' in t or '不可用' in t for t in ui.texts()), ui.texts()
    ui.evidence('10-model-unavailable')
    p.stop()
    p.start()
    time.sleep(.5)
    ui = WorkspaceUI(p)
    assert ui.state() == updated
    assert ui.context() == context
    ui.evidence('11-restarted')
    assert initial['revision'] < updated['revision']
    report = dict(passed=True, window='412x892', real_provider=False,
        checks=['no fabricated conversation/receipt', 'search applications/views/Flow and empty result',
                'draft retained on navigation', 'browse does not change input date', 'explicit backfill',
                'month/day/scope/context retained across view switches', 'Flow summary and semantic graph',
                'source read/edit separation and same-ID correction', 'new conversation resets context',
                'model unavailable produces no write', 'restart persistence', 'no horizontal control overflow'])
    assert '[E]' not in (p.output/'runtime.log').read_text(encoding='utf8')
    (p.output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=Path, required=True)
    parser.add_argument('--binary', type=Path)
    args = parser.parse_args()
    p = Probe(args.output, args.seed, binary=args.binary)
    try:
        run(p)
    except BaseException:
        UI(p).evidence('failure')
        raise
    finally:
        p.stop()
