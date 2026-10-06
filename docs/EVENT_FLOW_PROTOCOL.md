# 事件 Flow 应用内协议（0.4.0）

0.6.2修订：expense_for/follow_up/fulfills允许空flow_id，belongs_to仍需容器；明确源关系不再依赖命名Flow。按范围消费全局边需两端均可见。普通日历同日组合与旧收据修复规则见 [SOURCE_RELATIONS_FIX](SOURCE_RELATIONS_FIX.md)。

2026-10-06 更新：公共时间包装和投影已抽离到 08_time_protocol，注册入口在 38_modules，经期为第三个伪 App。当前 v2 字段、查询与边界见 [TIME_EVENT_PROTOCOL](TIME_EVENT_PROTOCOL.md)。下文保留0.4.0业务基线；尤其 occurred_at、模块集合和文件归属以新协议为准。

2026-10-04。一个 App：`source_app=dailyflow`。协议版本 1；数据库仍为 schema_version=1，新增 event_flow_version=2。P0/P1 文档与本实现约定共同作为接手入口。

## 权威边界

| 源文件 | 权威数据与公开操作 |
| --- | --- |
| src/00_storage.splash | 验证、双槽提交、备份与恢复；完整保留历史字段 |
| src/10_expense.splash | 唯一账目容器；公开 expense_snapshot/get/write/remove/membership |
| src/20_calendar.splash | calendar_events 与 projection_accept/calendar_query/sum/rebuild |
| src/30_flow.splash | Flow 主题、源引用及 typed relations；通过模块接口修改归属 |
| src/40_coordinator.splash | 单候选复合提交、收据、修订检查、工具兼容包装 |
| src/50_agent.splash | 受约束意图、查询、更正候选与追问；不直接访问私有源账 |
| src/60_ui.splash | 两主入口、双日历、读取/编辑、图与返回状态；通过公开接口操作 |

`tools/build_event_app.py` 将模块组成单个 Splash 包，并拒绝日历/Flow/Agent/UI 对私有账目数组的访问。没有新增原生服务或跨 App 传输。源账内部保留 `cents`；公开快照同时提供 `amount_minor`、`currency=CNY`、`record_id` 兼容字段。分类由记账模块持有，用户标签另存。

## 公共信封与投影

每个源快照包含 protocol_version/change_id/operation/source_app/source_module/source_record_id/source_revision/date/occurred_at/time_precision/timezone/summary/entry。费用扩展 amount_minor/currency；事件扩展 status/time。日期精度使用 YYYY-MM-DD，分钟精度使用带 +08:00 的时间；时区为 Asia/Shanghai。

change_id 由模块、源 ID、修订组成。投影只接受较新修订；相同或更旧修订不覆盖。删除保存递增修订墓碑，重复投递或旧 upsert 不会复活。一次提交成功后，从公开来源快照和墓碑重建投影；重启执行同一路径。金额按源 ID 唯一计数，一笔费用关联多 Flow 不增加全局支出。

普通日历将同日附属费用折叠到事实节点；跨日费用仍在其实际日期可见。账本日历始终只展示实际费用，计划和撤回事件不计费。空白日期标为未记录。投影测试用最小 Splash 程序，仅加载 reducer，无记账界面或私有源账。

## 复合写入与关系

`dailyflow.apply` 支持 save/delete/link/unlink/delete_flow；save 可以包含一个源记录、一个独立发生事实和一项明确后续计划。所有源、关系、收据先在候选状态校验，然后一次持久化。任何字段/修订/写入失败都不提交候选。

- belongs_to：源 ID → Flow ID。
- expense_for：已发生事项 ID → 费用 ID；费用节点不复制金额。
- follow_up：既有事项 ID → 用户明确的后续计划 ID。
- fulfills：明确发生事项 ID → 同 Flow 的计划 ID。图中计划标为已实现，不再计入待执行计划；保留原计划时间与源身份。

没有基于相邻日期的因果连线。Agent 从主体和事项解析 Flow；多候选追问。若模型漏了明确后续安排的源 ID，仅在用户表达“再/下次/后续/之后”、已确定所属 Flow、且其中只有一个已发生事项时补齐引用；多个候选仍先问。这个保护不生成新的计划或日期，也不靠宠物关键词归组。

更正查询唯一费用候选后提交其当前 ID/修订；不新建替代费用。取消事项会撤下不再成立的费用/完成关系，但保留源账。删除 Flow 解除受支持源的引用；为保护不支持的历史记录，旧 Flow 容器身份保留为 hidden，不出现在新产品。

## 兼容、错误与限制

首次实际写入前保存 `pre-event-flow-v1.json`，失败则拒绝写入；仅启动不会迁移真实个人数据。旧记录、旧修订、历史字段、收据完整保留。旧版 source save 收据按原规范化内容核对，可跨版本重放；支持范围外的历史记录和仅关联这些记录的 Flow 不进入 UI、查询或模型上下文。

request_id 是操作级幂等键，与源修订 change_id 不同。相同键不同内容拒绝；最多 128 条自动收据，不驱逐。手工操作仍可继续。双槽是单设备单实例本地持久化，不是断电事务；恢复旧备份会回退收据。聊天草稿/追问不跨重启；超时/取消/改写使旧回调失效。未知保存结果应查询后再决定，不盲目重投新请求。

保留工具 dailyflow.query/save_record，新增 flow_query/apply。工具真实 card-host 调用与应用内真实 model.complete 分开验收；Shell Agent 跨 App 路径仍不属于本轮通过范围。
