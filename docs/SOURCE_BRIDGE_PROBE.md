# 独立来源桥接预验证

2026-10-10。范围：只读核对官方固定源码、准备两个最小候选 App、运行离线独立消费者契约验证。未改 DailyFlow 生产源码、工具权限、bundle、宿主、运行时选择器或个人数据；未安装/运行候选 App、调用模型、提交或发布。

## 当前结论

**保留独立来源路线，但先按四天计划的备用技术证据推进。** 可复用的事件身份、修订与墓碑有现有代码和历史 Splash 验证基础；跨第三方 App 的工具归属以及外部数据进入生产协议仍各有一处明确边界。不能把离线消费者通过计为桥接完成。

| 层次 | 本次结果 | 证据性质 |
| --- | --- | --- |
| 官方 RC2 跨 App owner/grant | 固定源码将非内置 namespace 映射 `os.<ns>` | 源码核对；尚无正式宿主实际调用失败日志 |
| DailyFlow 生产协议 | `time_event_valid` 限定来源为 dailyflow；`protocol_envelope` 也产生该来源 | 当前代码边界，不是本次新故障 |
| 两个独立候选包 | manifest/工具声明/RC2回调和合成场景已准备 | 候选材料，未编译、准入、安装或执行 |
| 独立消费者 | 17项测试通过，包含真实历史三来源导出回放 | 离线 Python；不运行生产 Splash 或官方 Agent |
| 生产桥接与 UI | 未实施 | 不宣称跨App同步、持久化或用户验收通过 |

## 一 官方归属解析的准确边界

固定版本：`desktop-v0.1.0-rc.2`，提交 `4ccf8e068399b1da139771a9ed94cef05fa6ae60`。本次不推断日后 main 或新发行版保持相同行为。

1. [Catalog::owner_of](https://github.com/OctoSense-org/OctoSense/blob/4ccf8e068399b1da139771a9ed94cef05fa6ae60/crates/shell/src/host_tools/relay.rs#L336) 取工具名第一段，toolbox/workflow 指向 toolbox，内置 native namespace 指向原应用，其他指向 `os.<namespace>`。
2. [script_apps::install](https://github.com/OctoSense-org/OctoSense/blob/4ccf8e068399b1da139771a9ed94cef05fa6ae60/crates/shell/src/host_tools/script_apps.rs#L157) 按真实 app id 声明自有工具；读取 `agent.tools` 时，使用上述规则确定被授予工具的 owner。
3. [Catalog::may_call](https://github.com/OctoSense-org/OctoSense/blob/4ccf8e068399b1da139771a9ed94cef05fa6ae60/crates/shell/src/host_tools/relay.rs#L357) 跨应用调用要求目标工具 shareable 且精确匹配 `(owner, tool)` 授权。

候选来源 `dev.dailyflow.probeledger` 提供 `probeledger.events`，候选调用方 `dev.dailyflow.probeconsumer` 请求该工具。源码预期授权 owner 为 `os.probeledger`，与实际来源身份不符。**预期现象是调用方未获得正确来源的工具，具体错误或不可发现状态必须由实机记录，不能预填。** 这是固定版本的设计限制/接入缺口证据，不称为上游已确认 bug，也不通过扫描谁先声明工具来绕过身份保护。

原始摘录保存在 [upstream-owner-excerpts.json](../experiments/source-bridge/fixtures/upstream-owner-excerpts.json)。候选回调形式参照[官方 RC2 示例](https://github.com/OctoSense-org/OctoSense/blob/4ccf8e068399b1da139771a9ed94cef05fa6ae60/tools/fixtures/host-api-lab/bundle/main.splash)。此材料未在上游发 Issue。

## 二 生产协议的另一边界

[08_time_protocol.splash](../src/08_time_protocol.splash) 的 `time_event_valid` 只接受 `source_app == "dailyflow"` 和已注册模块，`protocol_envelope` 固定产生同包来源身份。因此宿主成功返回第三方记录，也不能直接证明生产投影接受了它。

未来需显式配置来源身份绑定、适配与准入规则，保存权威源身份，定义传输的分页、墓碑、失败、撤权与迟到响应策略；不宜简单删掉来源检查，也不能将全部外部来源改名 dailyflow，造成身份碰撞或信任边界消失。当前 timeline_query 只返回活跃事件，不是面向外部消费者的完整墓碑同步端点。

本次消费者在实验目录使用外部身份，验证设计行为；未放宽生产验证。资金统计仍由来源业务程序计算，不让模型重写金额成为同步数据。

## 三 已完成的独立消费者证据

执行：`python -X utf8 tools/test_source_bridge_contract.py --output build/semifinal-202610/source-bridge/contracts-r2`。r1为首轮通过记录；r2新增输出逐步变化轨迹并复跑通过。

结果：17项通过，详细结果见 [report.json](../build/semifinal-202610/source-bridge/contracts-r2/report.json)、[tests.log](../build/semifinal-202610/source-bridge/contracts-r2/tests.log) 和 [变化轨迹](../build/semifinal-202610/source-bridge/contracts-r2/synthetic-change-trace.json)。候选包另通过 JSON 解析、元数据、链接与空白检查，见 [static-audit.json](../build/semifinal-202610/source-bridge/static-audit.json)，不代表包 schema 检查或 Splash 编译通过。build为本地证据目录；对外材料应附选定报告，不把链接存在误写为已公开。

覆盖：历史 Splash 三模块输出可被独立程序读取；来源+记录身份不随更正变化；重复读取只留一条；旧修订不覆盖新值；墓碑阻止迟到旧值复活；部分/空结果不误删；同ID跨来源不碰撞；拒绝/不可用隐藏缓存；来源伪造拒绝；同修订冲突拒绝；不合法页原子拒绝；分页版本/偏移检查；结果与输入对象互不污染。

历史导出为合成数据，保留源文件字节与 SHA256，来源见[实验说明](../experiments/source-bridge/README.md)。在其字段结构上构造的独立来源样本明确标为合成输入；不称之为记账 App 实际返回。数据校验比旧同包协议更严格的地方属于实验消费者约束，不能推断生产已加固。

可展示的确定对照：同一笔120元重复两次，简单追加输入有两条，消费者仍一条；更正100元后重放旧120元，当前仍100元；删除后重放旧修订，当前无可见记录。对照用于展示算法效果，不声称旧 DailyFlow 发布版曾出现这些错误，亦不计算未经测量的效率提升百分比。

## 四 后续正式宿主探针（最多两小时）

仅在 P0 官方自有工具通路可用后，由主 Agent 独占宿主执行。使用新的隔离安装和数据目录；保持开发者模式关闭，来源和调用方均为非 `os.*` 身份；准入要求按官方实际流程执行。若无法合法安装候选包，标“准入未验证”，不要将该问题误归因为 owner。

| 步骤 | 需要保留的证据 | 判定 |
| --- | --- | --- |
| 来源自身工具 | 同一候选包被允许启用后，自己的 Agent 调用 `probeledger.events` 返回原始结构化记录 | 先排除回调/准入/来源运行失败 |
| 调用方发现和调用 | 用户允许调用方 Agent 后，工具目录、实际 owner、请求/返回或拒绝原文 | 判断跨App授权目标是否正确 |
| 拒绝/关闭 | 拒绝启用、关闭来源后的真实状态 | 不返回编造的空成功，不绕权限 |
| 更正/删除/重拉 | UI阶段推进后两次读回，比较源ID、修订与金额/墓碑 | 只能称工具传输；仍需另验证确定性导入 |

只需一条合成记录。候选来源内存状态重启会重置，不能用于持久化或旧修订复活验收。候选调用方没有导入器；禁止把 Agent 复述/复制记录到提示词算成程序桥接。

若目标解析或准入仍阻塞，在时间上限内保存最小证据并停止接入，选择四天计划路线B。无需为赶比赛修改 Shell、增加全局授权或正式拆出账本。若官方版本更新解决目标解析，仍需生产来源绑定与结构化投影接入，再判断是否能在剩余时间完成。

## 五 比赛材料措辞

可说：“已实现同包三来源的公共时间事件协议，并提供离线独立消费者及17项一致性契约验证；正在验证官方第三方应用接入边界。”

不可说：“四个独立App已经互通”“官方Agent完成跨App账本同步”“Python通过等于Splash/正式发布通过”“已完成官方Octos协议悬赏”。本成果属于自选的复用与验证证据，仍需运行中的 DailyFlow 用户任务支撑 Agentic 评价。
