# 官方 Agent 回传与关联推理验收

2026-10-12，UX-06A—D / UX-07A—D。最终状态以 execution-state.json 为准。本页区分真实宿主、模型调用、已录制结果的界面回放与注入契约；不能互相替代。

## 实现契约

默认入口为官方应用 Agent。每阶段调用宿主公开 `octos.turn.start`，由宿主管理应用身份、会话、Provider 与授权；没有使用 `peer_send_input` 给 done peer 续任务，也没有修改 Shell/Rust。

1. Agent 调用 `dailyflow.experience_context(request_id)`，取得本阶段限定的来源目录或记录。
2. 通过 `dailyflow.experience_result` 提交 `plan` 或 `organization`，宿主校验工具参数，应用再核对身份、修订、日期及引用原文。仅保存待采用的建议，不确认关联、费用或写回来源。
3. 宿主本轮完成回执的 `turn_id` 到达后，应用将本轮已通过校验的对象交给经历界面。自由文本、旧黑板和仅聊天中的 JSON 均不是结果。

每轮绑定 request、experience、query revision 与阶段 ticket。未读取/未提交只补一次只读新轮，仍受原 180 秒期限约束；授权拒绝、传输错误、取消不自动重试。每阶段最多两次提交校验，成功提交幂等。停止调用 `octos.turn.interrupt`，同时清理待采用对象，迟到结果丢弃。界面过程来自应用提交、实际工具处理和完成回执，不冒充宿主逐 token 推送。

设置保留显式 `model.complete` 备用入口，两阶段共用计划及来源引用验证。该接口没有物理取消接线，停止后拒收结果；不称官方 Agent 路径。两阶段各有独立超时，第一阶段计时器不会中断第二阶段。

## 关联与界面

第二阶段最多提供 36 条当前可见记录，总序列化长度限制 48,000；过长正文/标题省略并带标志。给定完整 app/module/id/revision、原文、日期、种类及 suspicious/future 标志。模型提出有引用的概括和 `same_experience`、`sequence`、`supports` 候选，不把同日同名自动确认为关系。

程序拒绝未知身份、模块混淆、旧修订、无依据/改写的摘录、自环、重复边、逆序或同日的 sequence。每条概括最多四个来源，最多六条概括和十二条候选；提示优先生成四条概括和六条有用关系。语义仍是模型建议，引用核验不证明因果。

经历界面分“原始时间流”“经历概括”“核对关联”。可点引用看原文；每条关系可确认、不相关、重新核对或撤销。成员排除、关联决定、费用确认相互独立。费用仍按币种由程序计算。保存经历迁移临时组织结果及决定；重启不丢失。来源更正/删除/停止读取或成员排除后，相应概括隐藏，旧关系只显示通用失效提示，不泄露旧标题/理由/摘录；新修订候选需重新确认。

## 实际证据与版本

最终证据汇总见 `build/ux-agent-delivery-summary.json`；UX-06/07 及八张小卡全部通过。每份报告对应自己的生产 main 摘要；源码调整后的证据不冒称旧包已测。

- 初次真实官方完整两阶段：`build/ux-official-r3`，两故事四个不同 turn_id，实际 context 工具审计，原业务零写入；这是自由文本适配的历史成功，最终结构化工具另验。
- 显式备用入口：`build/ux-reasoning-model-r4`，真实 Provider 两故事、每故事两阶段、源记录零写入。
- 界面回放：`build/ux-relations-ui-wide-r1` 13/13、`build/ux-relations-ui-compact-r2` 14/14。读取上述真实官方已录制结果，显式迁移为保存经历；更正/删除测试仅注入私有导入投影，不称真实外部 App 拉取。含真实点击、重启及截图。
- 旧路径回归：`build/ux-agent-final-regression` 13 套全过，含来源同步、对抗反例、两种宽度和原业务。随后仅官方结果接口进一步收紧，需看对应新契约和真实宿主证据。

运行链：本机编译 OctoSense Shell 40ca21da、官方 RC2 kernel b0759a5、本地 655114c Hub/Card-host 与已记录的 first-card 修复。不是宣称未修改的公开发行包在其他设备也已通过。新业务目录全在 build 内；复用用户原隔离配置已有的 DailyFlow 允许状态，不复制/修改授权。测试核对原 Provider 与 consent 文件不变。

## 发现并修复的问题

- 第一阶段超时误停第二阶段；日期字符串不能按数值比较，改为 epoch_day。
- 默认服务在未允许应用 Agent 时正确拒绝；保留 r1 证据，复用用户此前已有允许状态后验收。
- 自由文本结果存在逗号改写、重复 JSON 字段或未读本轮上下文等错误；均拒收。r4—r6 失败不删除，最终改为专用结构化工具回传。
- 部分旧 helper 测试意外启动第二阶段，独立 stub transport 后只测试对应协调层；真实第二阶段另有证据。
- 窄屏测试曾错误要求详情与关系列表同时显示；改为实际返回导航后验收。

## 边界与交接

仍是标记清楚的导入样本。系统 Agent 跨应用委派、实时 App 数据拉取、图片、云账号不属于本轮完成项。模型推理可失败或无足够依据，应用不伪造候选。来源开关不撤销宿主权限，也不删除 Provider/宿主已有会话。

`experience-agent-receipts.json` 只保存本次进程的成功阶段回执，不是跨重启完整审计；真实工具审计由宿主保留。完整聊天亦可能由宿主保存。

所有发布动作仍独立：0.1.1 未发布，旧 ZIP 不包含本轮代码，发布前重建 DF-21 材料、刷新 screenshots 并另按 DF-22/25 外发。Goal 状态未改。

## 最终收口

最终生产 main SHA256：`d497f4efe2759540a8b256f82ce625b255b47215809ea173a9a2f3170e767859`；bundle BLAKE3：`79f5eed0c4f5eb9363df375767d46e85ceba3b2a1cbee995620fb7edbbd42a48`。最终官方与交付宽屏、第一轮结构化契约使用同一验收main；其后只调整一处取消提示，使模型备用入口不误称已物理中断，控制流无变化。精确差异证明在 build/ux-agent-post-test-delta.json；交付main重新通过46项结构化契约。另增加能力披露、listing和截图并stamp/check。

- official：6 项/套通过，`build/ux-official-r7/report.json`。
- peer_contracts：46 项/套通过，`build/ux-agent-structured-peer-contracts/report.json`。
- experience_contracts：20 项/套通过，`build/ux-agent-final-contracts-r2/report.json`。
- reasoning_contracts：32 项/套通过，`build/ux-agent-final-reasoning/report.json`。
- legacy_regression：13 项/套通过，`build/ux-agent-final-regression/report.json`。
- delivery_ui：14 项/套通过，`build/ux-agent-delivery-ui/report.json`。
- compact_ui：14 项/套通过，`build/ux-relations-ui-compact-r2/report.json`。
- model_fallback：3 项/套通过，`build/ux-reasoning-model-r4/report.json`。

官方最终结构化路径是 ux-official-r7：4次读取、结构化提交（含一次引用拒收后的更正）及4个不同turn_id；随后真实点击停止，观察窗口内未采用迟到结果，源数据零写。更长时间的迟到/切换通过注入契约覆盖，不称无限时长观察。最终UI为14项、含原文、候选核对、撤销、重启和来源失效。所有本轮测试宿主已退出。当前不是发行版包，未推送或提交。

交付main最后契约：`build/ux-agent-delivery-peer-contracts/report.json`，46/46；Windows文本差异检查以cr-at-eol规则通过。
