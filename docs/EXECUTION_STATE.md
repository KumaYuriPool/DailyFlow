# DailyFlow 执行状态与接手入口

不同IDE接力入口：[分工交付约定](agent-prompts/COMMON.md)。四份prompt位于docs/agent-prompts/；先运行集成负责人阶段A，再三线独立副本开发，最后阶段B合流。当前只建立prompt与流程，NF卡状态未改变。

2026-10-12 夜间计划更新：用户取消额度15%停止线，今晚全时段可用；内部交付目标改为13日21:00，18:00冻结，比赛硬截止仍为13日24:00。新增[夜间冲刺路线图 NF-00—21](OVERNIGHT_ROADMAP_20261013.md)，包含优先级、三线并行/共享资源串行、里程碑和逐卡接力门槛。旧DF/UX记录保留且已快照；新任务均未开始，唯一状态见execution-state.json。以下旧排期与停止规则仅是历史。

## 当前交接 2026-10-12

UX-00—07 已实施并验收，active_task=null。见 [新里程碑](UX_ROADMAP.md)、[官方回传与关联验收](UX_AGENT_ACCEPTANCE.md)及保留的[首轮界面验收](UX_IMPLEMENTATION_ACCEPTANCE.md)。旧 DF 卡及证据保持不变，新建前快照在 history/pre-ux-20261012。下方旧候选包摘要是历史记录，当前候选取 JSON 的 current_candidate；旧 ZIP 不含新界面，发布材料尚需重建。

更新：2026-10-12。本文件是阅读入口，[execution-state.json](execution-state.json)是唯一任务调度状态；任务定义在[路线图](PRODUCT_ROADMAP.md)。不要把本页叙述复制成第二份会漂移的任务表。

## 本轮交付与授权

2026-10-12 更正：以下"只恢复文档工作、新增任务尚未执行"的叙述已过时。实现已在 2026-10-10/11 恢复并完成大半：以 JSON 账本为准（DF-00–DF-18、DF-20/21/24/26 passed，route=B，DF-23 passed_local，DF-19 deferred，DF-27 not_taken）。DF-22/DF-25 为 ready_for_user_review，需要用户具体授权，不得自动推送/发布/提交。Goal 工具保持既有状态；本文不改变 Goal 状态、不新建重复 Goal。后续接手先核对 JSON 的 active_task/next_action，不把写文档当发布授权。

2026-10-12 回归（DF-17 r5/r6）修复了测试隔离泄漏导致的 canonical 样本投影污染，并补齐 DF-07 缺失的 validate 证据；详见 build/semifinal-202610/steps/DF-17/regression-20261012-r5 与 r6 交接。

## 接手顺序

1. `../../agent.md`与`../AGENTS.md`：读取最新段，保留历史失败证据。
2. PRODUCT_SPEC：理解Agent选源、多来源过程、模拟社媒、图文UI与实现边界。
3. execution-state.json：检查active_task、owner、route、capabilities及依赖。
4. PRODUCT_ROADMAP：只读所领取卡及依赖；按STEP_HANDOFF_TEMPLATE落地交接。
5. SEMIFINAL_PLAN：先核对北京时间和剩余实际工时，再决定能否领取新开发卡。

建议下一卡以 JSON 的 active_task/next_action 为准（当前无活跃开发卡，下一步先刷新发布材料）；勿按旧叙述从 DF-01 重领已通过的卡。接入、图片、应用内官方Agent路径的当前能力状态见 JSON capabilities，不凭本页旧叙述假设。

## 实际基线

| 对象 | 当前已知状态 | 接手核对方式 |
| --- | --- | --- |
| DailyFlow | HEAD e7d4cdba95675c4e9ef56f9a334c2a8444780005，大量未提交候选/文档；0.1.1未发布 | git status/diff及bundle摘要，不能只看HEAD |
| OctoSense本地源码 | 40ca21da68cc05ae930931adcfcf6d382d49ec26 | 读取实际HEAD；与官方RC2二进制分开 |
| App Hub本地源码 | 7b36c8afc2e4bad9dfa5d77692b6fd453f0b9785 | 读取实际HEAD/锁文件；不回退外部更新 |
| 验收宿主 | 官方desktop-v0.1.0-rc.2，源码4ccf8e0；kernel b0759a5 | extracted receipt与既有来源哈希 |
| 实际新版Hub工具 | build/semifinal-202610/release-preflight/hub-build/app-hub/target/release/hub.exe，构建自655114c | 不是当前Hub源码自动编译结果；分别记录 |
| 既有候选包 | bundle_blake3 2df8d5f1e42c1c73824297c76ad55f843211290d618242c45df02910579f024d | 代码改变后必须重新生成/验收，不能复用旧摘要 |

路径相对DailyFlow，宿主解包位于工作区`../build/semifinal-202610/rc2/extracted`。可能活跃窗口的数据根`.local-state/semifinal-rc2-agent-r2`；仅从process.json读取当时PID/端口，先确认真实存活，不复用历史PID操作。不要打印其中core/profiles凭据。

`run-dailyflow-acceptance.cmd`只恢复这台机器现有隔离环境，依赖本机build；不是发布启动器。默认旧CMD可能选旧Hub并拒绝script-tools-v1，不能因此删掉requires。

## 已验证证据，不重复制造

本地证据根`build/semifinal-202610/official-host/real-agent-r1/`：

- read-tool-audit.json：官方自有只读工具实际调用。
- denied-write.json：人拒绝，not_called，零业务写入。
- approved-write.json：r2/12000分真实写入与读回。
- corrected-write.json：同r2改10000分、record revision3、expense总数1。
- restart-readback.json：整宿主重启后严格ID与expense查询一致。
- restart-query-mismatch.json：此前一次空查询，原始参数未捕获，不能删掉或臆断根因。
- system-delegation-pending.json：系统助手引用旧黑板，未证明新委派。

桥接/模型注入与17项独立消费者契约另有证据，不属于官方跨App实测。详见OFFICIAL_HOST_ACCEPTANCE与SOURCE_BRIDGE_PROBE。

## 阻塞和切换规则

应用内官方Agent回传已验证；跨App实时接入、图片等仍按各自门槛先探针后实现。探针产出否定结论可以passed，但capability必须unavailable，后续能力门槛仍阻塞。困难任务到时写handoff，另一个Agent可继续调查或领取无共享文件冲突的独立卡。

写入状态时记录owner/更新时间/运行目录；交接后释放owner，明确下一步。没有运行中的任务就active_task=null；不能遗留“in_progress但无人负责”。通过证据失效时标blocked/version_changed并列重验范围，不抹去原证据。

route=A/B/C及变更由集成负责人写明证据、预算和取舍；C不等于新产品完成。DF-20依赖采用JSON条件规则，不能机械忽略失败任务。对外发布/提交仍需具体内容审核。
