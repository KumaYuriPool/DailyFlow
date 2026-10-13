# 整夜冲刺最终交付总结（2026-10-13 22:30，I 集成负责人）

唯一候选：`DailyFlow/build/overnight-20261013/integration-r1/candidate-r2`（三线 U/S/H 交付合并 + 冻结后 P1 修复）。本文件为 NF-20 内部交付材料；公开发布、推送、比赛提交仍需用户具体外发授权，未执行。

## 1. 候选与运行时身份（哈希）

**DailyFlow 应用**
- main.splash SHA256 `46a7c6d38d3e1da0f03b31032d153df83774eb17653cff74655670adda09f7d3`（含 P1 修复 `nf_external_recover`）
- manifest SHA256 `bf06008d7e89cc4cf511fe69e3cb03108b0df0ca7bc1281e2d8a7b4079b48633`，hub stamp digest `fef627a257d6fad0341b68feec54f4ca5529247b35ec419b84d477430a1183ee`，hub check PASSED（两条 destructive 工具警告为设计内：每次调用等宿主批准）
- 独立账本 DailyFlowLedger bundle 未再变更（S 交付身份，集成时已重 stamp 校验）

**运行时（runtime-final-r1.json，18 点冻结构建）**
| 组件 | 源码 revision | exe SHA256 |
| --- | --- | --- |
| Shell octosense.exe | ffd5e488 | `0476df1f3aadf33f28104e69f99240f1693bac7b751f0b25b19b878da3ac6de0` |
| Kernel octos.exe | d7a2e3a0 | `4e72bc7de800da497b644becb4f7945325ce2027e00f7feb925bc6d33fe170de` |
| card-host.exe | app-hub 38635915 | `0e92683e08c714e4947bfb59ea2c6c425e3eaa42157f76a4520ea5c55a3e4898` |
| hub.exe | app-hub 38635915 | `6eaeb6664d2e34627b2a3e715547c7bba02e56032acf78bef944b28d8f193930` |

本地补丁与 D3D11 修复保持（见 runtime-final-r1.json sources 段完整补丁哈希）；本地修补 Windows 运行时，非官方发行组合。

## 2. 最终证据索引（全部在上述候选+运行时上）

| 类别 | 目录 | 结果 |
| --- | --- | --- |
| 原生生产者（业务） | `producer-contract-r7`、`producer-trace-final-r5`、`producer-storage-final-r6` | 契约 14 项 + trace 126 标记 + storage 29 标记，全过 |
| 注入消费者 | `consumer-final-r2` | 全过（含坏hash/错主/取消/撤权失败保留等对抗） |
| 外部请求注入 | `external-final-r3` | 39/39 |
| 真实双 App 同步 | `bridge-final-r1..r4` | 拉取/更正 200/重复幂等/删除不复活 |
| 真实撤权 | `bridge-final-r5`（驱动 `run_revocation_final.py`） | 记录隐藏、来源 revoked，宿主 live 复查路径 |
| 只读审计 | `bridgeprobe-final-r1/read-only-audit.json` | 写工具 READ_ONLY_REQUIRED、错主 NOT_GRANTED（真实宿主拒绝） |
| 宽屏 UI | `ui-wide-final-r4` | 41/41 |
| 窄屏账本 UI | `ledger-ui-narrow-final-r1` | 通过 |
| 设置/范围 | `settings-probe-r1`、`scope-final-r1` | 通过 |
| 旧工作台 | `workbench-final-r1` | 8/8，无数据迁移 |
| **系统 Assistant 冷启动 E2E** | `live-cold-final-r2`（e2e-checks.json 全绿） | 全链路：系统 turn→委派→真实模型→同步→整理→保存→**自动打开回执** |
| **系统 Assistant 热窗口 E2E** | `live-warm-final-r2`（e2e-checks.json 全绿） | 已完成 peer 接新任务；模型两次 invalid_args 被拒后自我修正 |
| 视觉终审 | `docs/NIGHT_SPRINT_VISUAL_REVIEW.md` | 无阻断缺陷（限制见文内） |

（相对路径均以 `candidate-r2/DailyFlow/build/` 为根；live 两次运行的本地复核截图在同目录 `screen-*.png`。）

## 3. 冻结后 P1 修复（已披露、已回归）

18:00 冻结候选在真实冷启动 E2E 中暴露 P1：完成窗口一次 64ms Splash 墙钟预算超限（外部负载竞争）导致自动打开渲染回执丢失、UI busy 卡死。修复：`src/49_external_entry.splash` 增加完成后的 2s/8s 双延迟恢复 `nf_external_recover`（仅依据持久化状态）。补丁 `integration-r1/fix-r1-autoopen-retry.patch`；冻结快照 `freeze-1800` 未动；修复后重跑 external-final-r3（39/39）与 live 冷/热两次 E2E 全绿。

## 4. 如实披露的限制与未完成项

1. **上游漂移**：22:00 终审 29/29 来源，kernel 前进至 b81e6230（issue #2162 会话-档案绑定，与本轮带档案连接路径无交集）、matrix-rust-sdk 前进（测试重构+QR 修复）。按时间预算决定不重建，本轮不宣称"检查时全最新已构建"。详见 `upstream-drift-final.md`。
2. **live 取消探针未跑**：取消/迟到语义仅注入消费者测试覆盖（consumer-final-r2），未做真实系统会话中的现场取消演示。
3. **视觉像素级人工复核**：I 环境无法亲自查看像素（Read 仅回 CDN URL、视觉模型无法访问本机）；以 U 线 18 张逐张评审 + 集成断言全绿 + 结构检查替代，建议用户对 `NIGHT_SPRINT_VISUAL_REVIEW.md` 所列截图做一次最终确认。
4. **已知 UI 限制**：Esc 不关闭弹层（有替代关闭路径）；原型装饰元素（照片/连线/动画）P2 未做。
5. **官方发行门槛未过**：native-apps 标签规则、setup 固定 pin 两项官方发行门槛仍未通过，本组合不是官方发行包。
6. **主工作区未覆盖**：主仓库 DailyFlow 源码/bundle 仍为冲刺前状态（候选与全部证据在 candidate-r2）；主工作区提升为赛后第一步。
6b. **平台读桥的交付完整性缺口（22:40 核实）**：跨 App 读桥 `crates/shell/src/host_tools/read_bridge.rs`（app_tools.read/cancel/focus/watch_authorization）为 H 线夜间新增平台文件，**上游 ffd5e488 主线不含此文件**（git cat-file/log 已核实）；H 交付的 platform/ 目录只含被修改上游文件的 base/new 对照（installed_owner/mod/relay/script_apps），**未包含 read_bridge.rs 本体**——该文件仅存在于 `H/runtime-work/candidate/shell` 树与已构建的四 exe 中（最终构建即来自该树，产物正确）。后果：仅按 H 交付补丁重建会编译失败；上游 PR 文件集必须补入此文件。上游贡献时还应包含 OS-H-01（lib.rs 同步注册竞态）与 OS-H-06（contained.rs turn.start 60s 超时）两项修复。
7. 插桩模式（producer trace/storage、external-final-r3）在低内存时段需 `MAKEPAD_SPLASH_BUDGET_MS` 覆盖才能稳定（每标记写文件超 64ms 默认墙钟预算）；契约模式与全部生产路径在默认预算下通过。
8. 比赛材料（README/listing/隐私披露/DF-21 ZIP）尚未按本候选刷新——待用户确认候选后执行。

## 5. 复现步骤（本机）

```
cd D:/Life/AgenticApp/DailyFlow/build/overnight-20261013/integration-r1
# 回归单测（走 resource_guard，角色 I）
python -X utf8 run_check.py test_integrated_ui ui-wide-repro --wide
# 本地人工查看候选（可见窗口，H 人配置档案原地引用）
python -X utf8 run_candidate.py --app dailyflow
```
环境清单 `runtime-final-r1.json`（`DAILYFLOW_RUNTIME_MANIFEST` 强制哈希校验）；两 App 已注册于隔离 `candidate-r2/state/apps`，数据为合成验收数据，未迁移旧工作台数据。

## 6. 待用户动作

1. 审核本交付与 `NIGHT_SPRINT_VISUAL_REVIEW.md` 截图（最终像素确认）。
2. 决定是否在 24:00 前提交比赛材料（需按本候选刷新 DF-21 材料后外发，属具体外发授权范围）。
3. 赛后：主工作区提升候选、从 b81e6230 重建内核做全最新回归、live 取消探针、Esc/装饰 P2。
