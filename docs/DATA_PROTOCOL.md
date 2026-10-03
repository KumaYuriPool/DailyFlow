# DailyFlow 数据与内部入口协议 v1

## 0.3.0 应用工具与自动记录补充（2026-10-03，优先于历史说明）

数据库版本仍为 `schema_version=1`，增加可选 `records[].user_tags` 和 `receipts`，旧有效 v1 状态可读取。没有复制第二份账本；Flow、日历和详情仍引用源记录。旧版下文“无对外 Agent API”“AI 尚未跑通”仅描述 0.2.0，不再代表本版。

`business_save(args)` 为自动记录和工具调用的公共入口，手工表单复用同一业务提交函数但不创建请求收据。入参为 `request_id, record_id, expected_revision, kind, title, date, amount, time, end_date, source, flow_names, user_tags`；除整数修订号与两个字符串数组外均为字符串。新建使用空 record_id 和修订号 0；更新必须提供现有 ID/修订号，不能改变业务类型。金额仍用十进制字符串转整数分，禁止用模型原文充当成功回执。

返回 `{ok, record_id, flow_ids, message, replayed}`。成功只在候选数据库写入并读回通过后返回；异常可能无法确认结果，调用方必须核对原请求，不能自动重试新请求。记录、按精确去首尾空格名称复用或创建的 Flow、关联以及收据在同一候选数据库一次 persist。空 flow_names 不自动选中页面当前组，更新时保留原关联；隐藏同名 Flow 拒绝自动关联。

`request_id` 为 1–128 位 ASCII 字母、数字、短横线或下划线。规范化后的同 ID/同参数请求可在重启后重放，返回历史结果且不再写入；同 ID/不同参数拒绝。收据最多 128 条，不驱逐；满额时只拒绝新的自动写入，手工路径可继续。重放不复活后来删除的记录，也不保证原记录此刻仍未变化。恢复旧备份会回退收据，恢复后不可盲目重投备份之后的未知请求。

标签归业务模块与用户：kind 标识业务类型，user_tags 保存明确自定义标签（最多12个、每个40字以内）；无全局预设标签词表。flow_names 单次最多8个、每个60字以内。旧记录仅在实际更新时增补标签字段。收据保留规范化参数，可能包含敏感信息；与记录一样留在本地数据和备份中，不作为宽泛查询或模型上下文导出。

工具文件声明 `dailyflow.query` 与 `dailyflow.save_record`，由 app 实现；risk 分别为 read/act，声明 private_data=true。query 默认50条、最多100条，返回匹配 total 与 truncated；过滤禁用/隐藏的经期记录、隐藏 Flow 名称和成员 ID，不返回收据。保存经期仍要求主动启用。工具不提供删除、恢复、设置或直接文件操作。Agent 工作区访问声明为 none，要求通过应用工具操作。

应用内 `model.complete` 使用结构化输出：明确事实通过业务校验后保存，歧义先追问；旧回调在取消或改写输入后失效。会话草稿和追问上下文不跨重启。模型输入只含当前对话、当前日期和少量可见 Flow 名称，不包含整个记录库。

完整桌面启动入口使用 `.local-state/desktop/`；旧独立 card-host 使用 `.local-state/dailyflow/`，两者不自动迁移。独立工具传输、应用内真实模型与 Shell Agent 工具链路是不同验收层；最后一项仍未通过真实验收。详见 [AGENT_FLOW_ACCEPTANCE](AGENT_FLOW_ACCEPTANCE.md)。

## 0.2.0 原协议记录（保留历史）

实现入口为 `bundle/main.splash`，生产业务仅由 Splash 执行。开发测试脚本不参与应用的数据处理。

## 权威数据与投影

数据库包含 `schema_version=1`、整体 `revision`、单调 `seq`、`records`、`flows`、`alerts` 与设置。记录包含 `id`、模块 `kind`、记录修订 `revision`、`title`、发生日期 `date`、可空的 `end_date`、`created_at`、`updated_at`、`flow_ids`。

| 模块 | 专属字段与约束 |
| --- | --- |
| expense | `cents` 为整数分；输入最多两位小数，拒绝负值、零和未来消费 |
| period | 必须主动启用；空结束日表示未知；同日或重叠周期拒绝新增；不生成预测 |
| task | `due_at` 是计划到期 Unix 秒；`completed_at` 是实际完成秒，未完成为 0；`status` 为 pending/done/cancelled |
| news | `source` 为人工填写的出处；`date` 为事件日期，`created_at` 为收录时间，不自动抓取或生成事实 |

`event_of(record)` 生成公共事件：`event_id=event-<record_id>`、`source_app=dailyflow`、`source_record_id`、`source_revision`、`event_type`、`title`、`time_kind`、日期/结束日/到期/完成时间、`timezone=Asia/Shanghai`、时间精度、生命周期字段、`flow_ids` 和 `entry={target,record_id,action:detail}`。`events-export.json` 是导出快照，不作为第二份账本。应用内日历、Flow、详情与卡片直接读取同一源记录。

当前时间以已验证 card-host 的 UTC `local_time` 加 8 小时处理，日期支持 1970–2100，不支持自动切换时区或夏令时。日历以周一为首日，按公历闰年算法计算。

## 写入、去重与路由

`new_record/open_record/save_record` 为表单和固定卡片的共同业务入口；`open_record(id)` 实际打开该模块条目的编辑页。更新校验打开时的修订号，保存成功后才更新内存、显示回执。同一表单重复提交更新同一个 ID；重新新建时用日期、类型、标题及金额/来源/到期时间阻止相同输入。经期使用区间重叠检测。

这是单设备、单实例的本地协议，尚无跨进程锁、跨设备冲突解决或对外 Agent 写入 API。内容去重是保守规则：两笔完全相同的实际消费需用不同备注区分。AI 尚未跑通，不能把候选模型输出当作保存回执。

Flow 保存稳定 `id`、名称、`hidden` 和创建时间。成员 ID 保存在源记录 `flow_ids` 中，加入/移除不复制源记录。每次合计遍历源记录一次；全局合计不相加各组的合计。日历默认仅显示可见 Flow 的节点，日期支出摘要为当日全部账目。

删除 Flow 仅移除该组及成员引用；删除源记录移除所有展示，并停用其任务提醒。两种删除均在页面内二次点击确认。当前没有 Flow 专属自动采集规则。隐藏不删除数据，显式选中 Flow 可查看该组。

## 提醒

每次业务写入及运行中每 20 秒检查规则；启动时补偿。预算按本月所有源账目计算，每个自然月首次超过预算生成一条提醒，持续越限、已读、重启均不重复。修改预算不会重置本月已提醒标记；0 关闭预算。

任务提醒键为 `due-<id>-<due_at>`，记录 `reminded_due`。延期会停用旧提醒并清空该字段，完成、取消、删除会停用该任务的提醒。完成时保存实际时间。提醒只在应用内显示；关闭应用、休眠和关机不会由 DailyFlow 唤醒。

## 持久化与恢复

`state-a.json` 与 `state-b.json` 按数据库修订交替写入，写入返回值和全文读回都通过后才替换内存状态。启动验证结构、日期、引用与唯一 ID，取有效的最高修订；两份均损坏时停止业务写入。此方案保留上一完整修订，但不是文件系统事务，也不能保证断电时最新一次修改绝不丢失。

导出写 `backup.json` 并读回核对，同时生成公共事件快照。恢复先校验备份，二次确认后写 `before-restore.json`，再以新修订保存；不会降低已发出的 ID 序号。数据上限为 800 条源记录、80 个 Flow、1600 条提醒历史，另受宿主单文件 1 MiB 限制；上限不是性能保证，大数据压力测试尚未完成。

旧 `expenses.json` 仅在用户点击导入时读取，用 `legacy-<old id>` 幂等导入；旧文件不修改。备份含经期等敏感信息，显示隐藏不等于加密。应用不保存密钥，不请求网络或后台服务能力。

API 依据：工作区 `OctoScript-App-Design-Flow/docs/SCRIPT-API.md`、`docs/AI-SERVICES.md`；类型判断见 `makepad/platform/script/src/native.rs`。没有修改这些运行时文件。
