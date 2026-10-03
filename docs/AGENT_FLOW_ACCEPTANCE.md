# DailyFlow 0.3.0 Agent Flow 验收

日期：2026-10-03。生产业务保持单 Splash App。本轮没有修改 Shell/Rust/运行时、用户真实账本或 Provider 配置，没有提交、推送或发布。此前通用桥接的本地平台改动不是本轮产品开发，也不代表当前旧 Shell 已包含该桥接。

## 已打通的实际流程

在完整桌面中使用既有 Provider，实际执行 **3 次模型请求**：

1. “猫粮 45 元，归到宠物照护”自动保存源记录并创建 Flow；重复发送没有新增记录。
2. 猫砂金额不清楚时真实模型提出追问，此时不保存。
3. 补充 26 元后自动保存第二条记录，复用“宠物照护”。最终 2 条记录、1 个 Flow、7100 分，图中实际合计 71 元。

这条通过的路径是 **应用内 model.complete → 结构化输出校验 → business_save → 持久化 → Flow 图**。真实结果见 [report.json](../build/agent-flow-r1/real-model2/report.json)，截图和控件见 [首笔](../build/agent-flow-r1/real-model2/01-real-expense.json)、[追问](../build/agent-flow-r1/real-model2/03-real-clarification.json)、[补充](../build/agent-flow-r1/real-model2/04-real-followup.json)、[最终 Flow](../build/agent-flow-r1/real-model2/05-real-flow-complete.json)。[清理记录](../build/agent-flow-r1/real-model2/cleanup.json) 确认测试进程退出且 Provider profile 未改变。

## 分层验收

| 层次 | 真实执行内容 | 结论与证据 |
| --- | --- | --- |
| 业务工具 | 32 次真实 card-host 工具调用，使用正式bundle的隔离副本 | 通过：[业务报告](../build/agent-flow-r1/final-business3/acceptance-final/report.json)；包括原子写入、Flow复用、同进程/重启幂等、修改payload拒绝、内容去重、旧修订拒绝、多Flow单源、字段校验、旧状态兼容、隐私过滤 |
| 存储失败 | 真实目录阻止下一状态槽写入，解除后使用同一请求重试；损坏两个状态槽 | 无孤立Flow/记录/成功收据；解除后可保存；损坏后只读。见同目录 failure/retry/corrupt 的 results.json、状态与日志 |
| 收据边界 | 128条收据满额与真实手工UI操作 | 新自动写入拒绝，手工创建、更正仍成功；[UI证据](../build/agent-flow-r1/business/integration-retest/acceptance/receipt-limit/ui-evidence.json)。128条长字段收据重启查询也通过，见 max-receipt-query/results.json |
| 对话状态机 | 注入模型输出，执行真实业务与真实存储 | 12项集成断言和1项重启断言通过；取消/改输入拦截旧回调、追问补充、重复发送、新事项清除旧上下文等见 [正式集成断言](../build/agent-flow-r1/final-chat/state/dailyflow/integration-tests.json)与[重启断言](../build/agent-flow-r1/final-chat/state/dailyflow/restart-tests.json)。**这些模型输出是注入值，不是真实Provider** |
| 真实 Provider | 完整桌面中的3次实际模型请求 | 上述45元+26元闭环通过，独立于注入测试 |
| Flow UI | 真正的节点点击、详情返回、管理折叠、长标题与空状态 | 通过；[合并UI报告](../build/agent-flow-r1/visual-final/REPORT.md)：只读复制真实模型产生的45+26元数据到隔离环境，查看71元→更正45为46→回图72元→重启仍72元→二次确认删Flow但保留两条源。该次没有调用模型；早期视觉夹具也不充当模型证据 |
| Shell Agent 工具链路 | 系统/App Agent 经授权调用新脚本工具桥接 | **未验收**：旧Shell程序不含新增桥接，未配置测试kernel。card-host --tool-call绕过模型与Shell调用者审批层，不能代替该链路 |
| AI启动入口 | 实际PowerShell入口隐藏启动、UI保存12.34元、关闭后再次启动 | 账目保留，同目录重复实例被拒绝，Provider profile未变；[启动器报告](../build/agent-flow-r1/conversation/launcher-test-output-3/report.json)。该轮没有额外模型请求 |

正式bundle的 `hub check --allow-unsigned` 通过0.3.0，仅有未正式签名warning。生成的review packet尚未经过外部审查；检查通过不代表发布。listing展示的Flow截图为真实模型数据在窄屏card-host的回读，模型保存/追问截图来自完整桌面真实测试，均保留原图。

早期 probe1/probe2/probe3、real-model1、final-business/final-business2 等开发日志保留历史，不替代上述最终通过证据。图形展示不代表任意画布编辑器，也不代表跨App自动工作流。

## 复测业务工具

在 DailyFlow 根目录运行，output 必须是一个尚不存在的新目录：

```powershell
python -X utf8 tools/test_business_flow.py --bundle bundle --output build/business-flow-check --binary ../OctoSense-App-Hub/target/release/card-host.exe
```

脚本把 bundle 复制到隔离输出后才 stamp，使用独立状态与临时端口，并关闭自己创建的进程。日期按北京时间动态生成；不接触个人数据或调用模型。需要本地含脚本工具桥接的 card-host。本轮正式通过记录位于 `build/agent-flow-r1/final-business3/acceptance-final/report.json`。输出 `acceptance-final/report.json` 的 passed=true、tool_calls=32；每个场景另有 results.json、runtime.log、snapshot.json、cleanup.json。输出目录已存在时应换新名称，脚本不会覆盖旧证据。

## 运行入口与边界

- `run-dailyflow-ai.cmd`：完整桌面与既有Provider，持久数据位于 `.local-state/desktop/`。
- `run-dailyflow.cmd` / `.ps1`：独立card-host，无模型服务，数据位于 `.local-state/dailyflow/`。两个入口不自动迁移数据。
- durable receipts上限128，新自动请求满额后拒绝，旧收据不驱逐，手工操作仍可用。格式上的800条记录/80个Flow不构成极限性能保证。
- 对话草稿和追问上下文只在内存中；关闭后不恢复。已保存源记录、Flow、关联和收据会跨重启。
- 恢复旧备份会回退收据；恢复后不要重放备份之后结果未知的旧请求。相同收据重放只描述历史操作，不复活后来删除的记录。
- 仍为单设备单实例双槽存储，不承诺断电零丢失或跨进程事务。隐藏经期只影响可见性与查询，备份仍含敏感原文。
- AppCard/glance、跨App工具完整链路、关闭后唤醒、手机真机/其他平台、连续7天真实试用及发布未完成。当前真实模型验收是具体样例，不保证所有语义和模型组合都正确。
