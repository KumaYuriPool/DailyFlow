# 通用时间事件协议 v2 与经期伪 App（0.6.0）

2026-10-06，本地 Windows 实现。当前仍是一个 DailyFlow 安装包；“App”指有独立源数据和接口的内部模块。用户本轮明确将经期记录加入第三个接入方，覆盖旧规划中“不保留经期入口”的限制。本次不拆物理 App。

## 模块边界与接入方法

- `08_time_protocol.splash`：公共事件包装、修订投影、删除标记、来源读取和带分页的时间查询。没有 expense/calendar/period 的业务分支。
- `38_modules.splash`：组合入口。`time_modules()` 注册模块 `id/kind/name` 及 `snapshot/project/write/remove/membership` 回调；`query_capabilities()` 注册 `id/module/name/description/run/tags/keywords`。公开能力目录不会序列化内部函数。
- `10_expense`、`20_calendar`、`15_period`：分别拥有费用、事项/计划、经期源记录。每个模块通过 project 回调提供时间字段，不互读私有数组。日历在保存及重启后从已注册来源重建投影。
- `35_query_router`：按能力目录校验条件并调用回调，仍限制每次最多两项能力。加入新查询能力无需增加针对该模块的分发分支。
- `40_coordinator`：沿用候选事务、修订校验和收据；通过注册接口写/删源记录。事项与费用的复合关系仍有其业务校验。

增加一个伪 App：实现其源数据验证及上述适配器，在构建顺序与组合入口注册，接入源详情页面和需要的业务查询，再做隔离契约测试。新增数据容器的持久化验证与 UI 入口仍需显式接入，不是任意插件自动发现。源 ID 由同包全局序号分配；公共事件身份包含来源命名空间。独立 App IPC、不同宿主权限及外部事件接收不属于本次实现。

## 公共事件

| 字段 | 含义 |
| --- | --- |
| protocol_version | 新事件为 2；投影仍接受已注册来源的 v1 历史事件和删除标记 |
| event_id | `dailyflow/<module>/<record_id>`，不随日期、标题或更正变化 |
| change_id | event_id + source_revision；用于识别同一修订 |
| source_app / source_module / source_record_id | 当前同包 source_app=dailyflow；模块与源身份 |
| source_revision | 正整数；相同和更旧修订不覆盖新状态 |
| event_type / summary | 模块记录类型及标题 |
| date / end_date / open_end | 开始日、包含结束日的区间；无结束日与是否未关闭分开表达 |
| time_precision / time / timezone | day 或 minute；当前验证范围固定 Asia/Shanghai，分钟字段 HH:MM |
| occurred_at / scheduled_at | 分钟精度下分别存实际时间或计划时间，RFC3339 +08:00；日精度留空，不编造零点 |
| created_at / recorded_at / updated_at | Unix 秒；recorded_at 与初次创建时刻相同，与实际发生日分开 |
| status | occurred / planned / cancelled；日期经过不意味着计划完成 |
| flow_ids / entry | 明确关系引用；entry 带来源目标、源 ID、修订、详情/编辑/删除动作 |
| amount_minor / currency | 费用扩展；其他事件为 0 和空币种，不参与费用统计 |

删除事件为最小墓碑：身份、修订、operation=delete、deleted_at。不再把删除当天伪装成事情发生时间。投影按来源 App＋模块＋源 ID 匹配，只接受更新修订；重复、乱序、旧 upsert 不能复活已删除记录。这里只提供当前快照与墓碑，不是保存所有历史修订的事件日志。

当前不支持多时区转换、夏令时、秒级或跨午夜分钟区间；这些需要后续协议扩展和测试，不能称已完成。日期区间可跨月，经期记录用于验证这条能力。

## 时间查询

工具 `dailyflow.timeline_query` 的可选参数：`date_from/date_to/source_module/flow_id/limit/offset/snapshot_revision`。

- 日期范围包含边界，按区间重叠查询；省略来源会返回全部已注册来源，包括新经期记录。未关联 Flow 的记录也能查询。
- 默认每页 30，最大 50；返回 events、total、has_more、next_offset、snapshot_revision、read_only。
- 按开始日期升序，同日保持同一快照的来源顺序。第二页起必须携带第一页的 snapshot_revision；数据变更则拒绝旧分页，要求重新从第一页读取。
- `open_end=true` 的记录按未关闭区间覆盖开始日至今天，不投影未来；这不等于每天都被用户单独确认，也不用于预测或统计已确认持续天数。
- 查询不创建 Flow、关系、源数据或收据。实际更新仍由拥有数据的模块执行。

`dailyflow.module_query` 另外提供 `period.history`：按日期/期间重叠返回经期记录，最多展示最近20条，保留总数与 sources_truncated；完整分页使用 timeline_query。不支持标签、关键词、预测或统计推断。原 expense.summary/calendar.next 契约保持。

## 经期记录使用与数据边界

在“全部”搜索“经期”，进入“经期记录”后手工填写开始日期与可选结束日期。点击记录先看详情，再修改；删除需两次点击。普通日历对应区间的每一天能打开同一源记录，账本视图不计入任何金额。

源数据存 `period_entries`，类型 `period_entry`，最多800条。日期须已发生、结束不早于开始、同日允许；拒绝与已有经期区间重叠。开始后未填结束日期表示记录未关闭，不代表预测。新记录不自动创建 Flow，也不自动继承宠物/项目归属；详情不提供把经期加入宠物事件的快捷按钮。

旧 `records` 中的 period 数据保持归档，不自动迁移、展示或发给模型。新经期记录仅在明确查询该能力时用于回答，不加入无关对话的最近12条摘要。应用内聊天本轮支持查询经期历史；新增/更正请用经期表单。公开 apply 工具支持 kind=period_entry、date/end_date、源 ID/修订与稳定 request_id。

经期记录能力不包含周期预测、排卵、安全期或健康判断。仍沿用128条自动收据、单实例双槽及备份回退边界。

## 本轮验证

证据根目录 `build/time-protocol-r1/`，全部是隔离合成数据：

- `contracts-final2`：29次真实 Splash 工具调用，三模块共同查询、跨月区间、开放结束、修订更正、删除/重放、分页版本、无写入及重启。独立消费者测重复/乱序/墓碑/未知来源；在副本注册第四个临时出行适配器，通用快照/查询成功，核心无需添加业务判断。
- `legacy-contracts`：历史字段/收据保护、旧经期不泄露、迁移前完整备份、真实槽写入失败不提交。
- `business`：原15次事务业务回归；`module-regression`：原39次模块查询回归；`agent-final`：43项注入断言与缩短测试延时的真实超时用例。不是 Provider 验收。
- `ui-narrow2`、`ui-wide`：412×892 / 1280×900 真实点击，手工新增、读取、更正、日历区间打开源、重启、两次确认删除。截图已查看；窄屏结果在最后的表单文案简化前通过，宽屏在简化后通过。
- `real1`：完整现有宿主＋已有 Provider 一次真实请求，1703 tokens；查找人工构造的9月28–30日经期、回答正确、来源打开、数据未变，截图已查看。
- 早期 `agent` 仅因能力数断言仍写2而失败（现为3）；`ui-narrow1` 误找“跳转”而实际按钮是“定位”。失败日志保留，不能计为通过。

最终 gate、受保护文件和测试进程退出核对记录在本目录 final-gate.log / final-audit.json。本次未提交、推送或发布；未修改 Shell/Makepad/启动器/Provider/个人状态。
