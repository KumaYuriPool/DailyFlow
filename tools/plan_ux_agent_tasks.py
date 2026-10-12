"""Append the authorized UX-06/07 work without changing historical cards."""
import json, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
hist=R/'docs/history/pre-agent-ux-20261012'
hist.mkdir(exist_ok=True)
for name in ['UX_ROADMAP.md','execution-state.json','EXECUTION_STATE.md']:
    p=R/'docs'/name
    if not (hist/name).exists(): (hist/name).write_bytes(p.read_bytes())
(hist/'hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in hist.iterdir() if p.name!='hashes.json'},indent=2),encoding='utf-8')
cards=[
('UX-06A','核实官方公开接口与真实回执','UX-05','核对 octos.turn.start/interrupt；记录官方回执形状、同一 peer 新轮及授权边界。'),
('UX-06B','只读上下文工具和任务隔离','UX-06A','新增绑定 request/phase 的只读工具；限制已开放目录或当前记录，拒绝迟到、取消、串经历工具请求。'),
('UX-06C','官方运行适配与界面状态','UX-06B','用真实 octos.turn.start→工具→最终结构化回执；公开取消与故障，不伪造流式事件；模型路径可显式切换。'),
('UX-06D','官方运行端到端与反例','UX-06C','真实授权宿主两次新轮、工具审计与 UI 读回；取消/失败/旧结果不污染；零源记录写入。'),
('UX-07A','有引用的概括和候选边契约','UX-04','限量许可记录、完整 identity/revision、原文摘录；校验不存在/越权/旧修订/异常数据。'),
('UX-07B','第二阶段关联推理和持久化','UX-07A','读取后调用助手，验证输出后保存概括和候选边；不改原文、不推算账目总额。'),
('UX-07C','候选关系核对界面','UX-07B','明确两端及证据，逐边确认/拒绝/撤销；费用与成员排除独立；可点开原始记录。'),
('UX-07D','来源变化与重启回归','UX-07C','更正/删除/撤权/排除使引用失效，禁止旧确认复活；两故事真实推理，持久化与旧业务回归。')]
p=R/'docs/execution-state.json';d=json.loads(p.read_text(encoding='utf-8'))
d['scope']='UX-06/07 authorized 2026-10-12; UX-00—05 and DF history retained'
d['active_task']='UX-06A'; d['next_action']='实施 UX-06A—D 与 UX-07A—D；真实宿主授权由用户处理。'
for t in d['tasks']:
    if t['id'] in ['UX-06','UX-07']: t.update(status='in_progress',resume_condition=None)
for id,title,dep,accept in cards:
    if not any(t['id']==id for t in d['tasks']):
        d['tasks'].append(dict(id=id,title=title,dependencies=[dep],status='in_progress' if id in ['UX-06A','UX-07A'] else 'planned',owner=None,run_id='ux-agent-20261012',evidence=[],acceptance=accept,blocker=None,resume_condition=None))
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=R/'docs/UX_ROADMAP.md';s=p.read_text(encoding='utf-8')
s+='\n## 2026-10-12 追加：官方回传与关联推理\n\n用户已授权执行 UX-06/07 至完成。旧完成卡和证据不改写；本轮开始前快照在 history/pre-agent-ux-20261012。以下小卡均在唯一 JSON 账本追踪。\n\n'
for id,title,dep,accept in cards:
    s+=f'### {id} {title}\n\n- 前置：{dep}。\n- 执行与验收：{accept}\n- 交接：新增文件、实际命令、隔离 build 证据、当前失败与下一操作。真实 Provider 与注入契约证据分别记录；不得以 check 代替宿主或 UI 证据。\n\n'
s+='退出门槛：两项实现均有实际证据再标 passed；授权待用户处理时继续不依赖它的工作。UX-08—10 和外发不纳入本轮。账户剩余≤15%时遵照用户指令总结并停止。\n'
p.write_text(s,encoding='utf-8')
