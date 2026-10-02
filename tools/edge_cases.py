"""Fault injection only in explicitly isolated development storage."""
import bridge_test as b
import socket
from pathlib import Path
b.PORT=8172
b.OUT=b.ROOT/'build'/'mvp-failure'
def quit_owned():
    try: b.req('quit')
    except (OSError, Exception): pass
    b.time.sleep(.4)
    with socket.socket() as s: assert s.connect_ex(('127.0.0.1',b.PORT))!=0
def failure():
    before=b.state()
    # Block the next alternating write with a directory, without changing real data.
    name='state-a.json' if (before['revision']+1)%2 else 'state-b.json'
    target=b.OUT/'dailyflow'/name
    assert not target.exists() or (target.is_dir() and not list(target.iterdir()))
    target.mkdir(exist_ok=True)
    b.click('记录'); b.click('+ 记账'); b.fill('record_title','写入失败输入保留'); b.fill('record_amount','12.30'); b.click('保存记录')
    assert '写入失败' in b.status(),b.status()
    assert b.find(ident='record_title')['t']=='写入失败输入保留'
    assert b.state()==before
    b.evidence('20-save-failure')
    target.rmdir() # only removes the empty fault-injection directory
    b.click('保存记录'); assert len(b.state()['records'])==1,b.status()
    b.evidence('21-retry-saved')
    b.click('设置'); b.click('导出备份')
    backup=(b.OUT/'dailyflow/backup.json').read_text()
    (b.OUT/'dailyflow/backup.json').write_text('{"schema_version":1,"records":false}')
    b.click('恢复 backup.json'); assert '无效' in b.status()
    b.evidence('22-invalid-backup')
    (b.OUT/'dailyflow/backup.json').write_text(backup)
    quit_owned()
    # Preserve good slots, then test both corrupted on restart.
    for path in (b.OUT/'dailyflow').glob('state-*.json'):
        (b.OUT/(path.name+'.good')).write_bytes(path.read_bytes())
        path.write_text('{broken')
    print('FAULT PHASE1 PASS; restart required')
def corrupt():
    assert '存储损坏' in b.status(),b.status()
    # b.evidence requires a valid state; save raw controls and screenshot instead.
    (b.OUT/'23-corrupt-protection.json').write_text(b.json.dumps(b.widgets(),ensure_ascii=False,indent=2),encoding='utf-8')
    (b.OUT/'23-corrupt-protection.png').write_bytes(b.req('g',raw=1))
    b.click('设置'); b.click('恢复 backup.json'); b.click('恢复 backup.json')
    assert len(b.state()['records'])==1 and '恢复完成' in b.status(),b.status()
    b.evidence('24-corrupt-restored')
    quit_owned(); print('FAULT PHASE2 PASS')
if __name__=='__main__':
    if len(b.sys.argv)>1: corrupt()
    else: failure()

