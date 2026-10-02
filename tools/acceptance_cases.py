"""Real click/input acceptance cases, using isolated mvp-test data only."""
from bridge_test import *
from datetime import datetime, timedelta, timezone
TZ=timezone(timedelta(hours=8))
TODAY=datetime.now(TZ).strftime('%Y-%m-%d')
def record_row(kind,title):
    return next(w['t'] for w in widgets() if w['ty']=='Button' and f'{kind} · {title}' in w.get('t',''))
def count(kind): return len([r for r in state()['records'] if r['kind']==kind])
def add(kind,title,date=TODAY,value=None,source=None,at=None):
    click('记录'); click('+ '+kind); fill('record_date',date); fill('record_title',title)
    if value is not None: fill('record_amount',value)
    if source is not None: fill('record_source',source)
    if at is not None: fill('record_time',at)
    click('保存记录')
def phase1():
    click('记录'); click('+ 经期'); assert '主动启用' in status()
    assert count('period')==0
    click('经期模块：关闭（点击切换）'); click('敏感记录：隐藏（点击切换）')
    add('经期','经期开始'); assert count('period')==1,status()
    add('经期','经期开始'); assert count('period')==1 and '未重复保存' in status(),status()
    evidence('05-period-duplicate')
    click('记录'); click(record_row('经期','经期开始')); fill('record_end',TODAY); click('保存记录')
    assert [r for r in state()['records'] if r['kind']=='period'][0]['end_date']==TODAY
    click('设置'); fill('budget_input','60.00'); click('保存月预算')
    assert not any(a['key'].startswith('budget-') for a in state()['alerts'])
    add('记账','零食',value='5.00'); assert count('expense')==2
    assert not any(a['key'].startswith('budget-') for a in state()['alerts'])
    fill('record_amount','20.00'); click('保存记录')
    assert len([a for a in state()['alerts'] if a['key'].startswith('budget-')])==1
    fill('record_amount','21.00'); click('保存记录')
    assert len([a for a in state()['alerts'] if a['key'].startswith('budget-')])==1
    click('提醒'); evidence('06-budget-first-cross')
    click('已读'); click('立即检查'); assert not any(a['active'] for a in state()['alerts'])
    add('任务','给猫洗澡',at='00:00'); assert count('task')==1,status()
    task=[r for r in state()['records'] if r['kind']=='task'][0]
    assert task['reminded_due']==task['due_at']
    click('延期一天'); updated=[r for r in state()['records'] if r['kind']=='task'][0]
    assert updated['due_at']==task['due_at']+86400
    assert not any(a['active'] and a['record_id']==task['id'] for a in state()['alerts'])
    evidence('07-task-postponed')
    click('完成'); updated=[r for r in state()['records'] if r['kind']=='task'][0]
    assert updated['status']=='done' and updated['completed_at']>0
    evidence('08-task-done')
    click('Flow'); click('宠物照护'); click('删除 Flow'); click('删除 Flow')
    assert len(state()['flows'])==1 and count('expense')==2
    assert len(next(r for r in state()['records'] if r['title']=='猫粮')['flow_ids'])==1
    evidence('09-flow-deleted-source-kept')
    fill('flow_input','新闻观察（测试材料）'); click('创建 Flow'); click('导入新闻节点')
    fill('record_title','测试进展一'); fill('record_source','人工验收材料 A，第 1 页（非真实新闻）'); click('保存记录')
    assert count('news')==1
    click('Flow'); click('导入新闻节点'); fill('record_title','测试进展一'); fill('record_source','人工验收材料 A，第 1 页（非真实新闻）'); click('保存记录')
    assert count('news')==1 and '未重复保存' in status()
    fill('record_title','测试进展二'); fill('record_source','人工验收材料 A，第 2 页（非真实新闻）'); click('保存记录')
    assert count('news')==2
    click('Flow'); evidence('10-news-timeline'); click(record_row('新闻','测试进展一')); evidence('11-news-source')
    click('对话'); fill('chat_input','今天午饭花了32元'); before=count('expense'); click('请求真实模型')
    assert count('expense')==before
    assert any('no service answers' in w.get('t','') for w in widgets())
    assert find(ident='chat_input')['t']=='今天午饭花了32元'
    evidence('12-model-unavailable')
    click('记一笔实际支出'); fill('record_title','保留输入'); fill('record_amount','1.234'); click('保存记录')
    assert '最多两位' in status() and count('expense')==before
    fill('record_date','2027-02-29'); fill('record_amount','1'); click('保存记录'); assert '日期无效' in status()
    evidence('13-validation')
    click('日历')
    for date,days,weekday in [('2024-02-29',29,3),('2025-02-01',28,5),('2100-02-01',28,0),('2000-02-01',29,1),('2026-04-01',30,2)]:
        fill('date_jump',date); click('跳转日期')
        nums=[w for w in widgets() if w['ty']=='Button' and w.get('t','').replace('·','').isdigit()]
        assert len(nums)==days,(date,len(nums))
        first=next(w for w in nums if w['t'].replace('·','')=='1')
        assert round((first['r'][0]-14)/55)==weekday,(date,first['r'])
        evidence('14-calendar-'+date)
    fill('date_jump','2026-12-31'); click('跳转日期'); click('下月 ›')
    assert find(ident='date_jump')['t']=='2027-01-01'
    click('‹ 上月'); assert find(ident='date_jump')['t']=='2026-12-01'
    evidence('15-calendar-year-boundary'); click('今天')
    click('设置'); click('导出备份'); backup=json.loads((OUT/'dailyflow/backup.json').read_text())
    add('记账','恢复时移除的测试账目',value='2.00'); assert count('expense')==before+1
    click('设置'); click('恢复 backup.json'); click('恢复 backup.json')
    restored=state(); assert restored['records']==backup['records'] and restored['flows']==backup['flows'] and restored['alerts']==backup['alerts']
    evidence('16-backup-restored')
    # Schedule a real future task, then close before due time. Phase2 reopens after due.
    due=datetime.now(TZ).replace(second=0,microsecond=0)+timedelta(minutes=2)
    add('任务','重启补偿测试',date=due.strftime('%Y-%m-%d'),at=due.strftime('%H:%M'))
    r=next(r for r in state()['records'] if r['title']=='重启补偿测试')
    assert r['reminded_due']==0 and r['due_at']>time.time()
    evidence('17-before-restart')
    (OUT/'restart-due.json').write_text(json.dumps({'due_at':r['due_at'],'id':r['id']}))
    (OUT/'phase1-result.txt').write_text('PASS: period, budget, task, flows, news, model failure, validation, calendar, backup\n')
    print('PHASE1 PASS; future task due',due.isoformat(),flush=True)
    try: req('quit')
    except OSError: pass
    import socket
    time.sleep(.3)
    with socket.socket() as sock: assert sock.connect_ex(('127.0.0.1',PORT))!=0
def phase2():
    expected=json.loads((OUT/'restart-due.json').read_text()); assert time.time()>expected['due_at']
    r=next(r for r in state()['records'] if r['id']==expected['id'])
    assert r['reminded_due']==r['due_at'],r
    alerts=[a for a in state()['alerts'] if a['record_id']==r['id']]
    assert len(alerts)==1 and alerts[0]['active']
    click('提醒'); click('立即检查'); assert len([a for a in state()['alerts'] if a['record_id']==r['id']])==1
    evidence('18-restart-compensation')
    click('打开'); click('取消任务'); assert not any(a['active'] and a['record_id']==r['id'] for a in state()['alerts'])
    click('删除源记录'); click('删除源记录'); assert not any(x['id']==r['id'] for x in state()['records'])
    evidence('19-source-deleted')
    (OUT/'phase2-result.txt').write_text('PASS: restart readback, due compensation, repeated check deduplication, cancel, source delete\n')
    print('PHASE2 PASS')
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='phase2': phase2()
    else: phase1()


