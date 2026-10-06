# 单包内模块查询协议（0.5.5）

0.6.0 更新：能力目录与分发改为 38_modules 注册回调，新增 period.history 与独立的 dailyflow.timeline_query。完整范围见 [通用时间协议](TIME_EVENT_PROTOCOL.md)；本节下方“只有两项能力”是0.5.5历史基线。仍不支持独立 App IPC 或动态插件发现。

当前只有一个 DailyFlow App。记账持有费用源记录，日历持有事件源记录并消费投影，Flow 持有归属与关系。界面的 App 入口是内部模块，未拆成独立安装包。本轮未修改 Shell、Makepad、Provider 或启动器。

`05_subjects` 提供共享主体 ID：已有主体 Flow 在读取时派生稳定 `dailyflow.subject.<flow_id>`，不因查询写盘；下一次正常业务保存时注册到 subjects 并关联 Flow。名称用于展示与匹配，ID 用于模块间引用。同名旧分组保持不同身份，要求明确选择，不自动合并。无主体的旧 Flow 可按显式 flow_id 查询。源记录仍通过 flow_ids 关联主体，不重写历史记录。删除 Flow 保留源数据；此操作不会自动把旧源记录重新归属到后来创建的 Flow。

`dailyflow.capabilities` 返回当前能力目录与可见主体；`dailyflow.module_query` 接收 subject_id／subject／flow_id 及最多两项 queries。组合条件必须相符，未知能力、重复能力、错误日期与标签类型会拒绝。所有计划先校验，再分发到选定模块。

| 能力 | 数据与条件 | 返回 |
| --- | --- | --- |
| expense.summary | 全部源支出；主体、日期、显式标签、标题关键词 | 分币整数求和、条数、最多5条来源引用 |
| calendar.next | 今天起未撤回、未完成的计划；主体、日期、标题关键词 | 日期和时间排序的最多3项计划、符合条件总数、来源引用 |

期间支持 all、today、this_month、last_month；也可给出 date_from／date_to（包含边界），不能与非 all 期间混用。calendar.next 按天判断今天及未来；今天已过钟点但未完成的事项仍包含。未定时间显示“时间未定”。筛选的是源标题，不是模型推测的类别。

每条来源携带 source_app=dailyflow、source_module、source_record_id、source_revision、subject_id 和详情入口。结果另有 modules_used、read_only、sources_truncated。来源列表截断不影响全量求和。对话中的来源按钮直接打开该条源记录。

模型收到简短能力目录、Flow／主体元数据、当前消息及澄清问答、最多12条相关近期摘要。它输出查询计划，应用用选定模块的完整源数据计算并直接展示，无需第二次模型总结。严格匹配的简单总额问题仍零模型请求，同样经过此查询入口。模型上下文不代表完整数据；更正与写入继续走原事务协调器。

后续新增伪 App 时，添加其能力描述、参数契约、模块适配器和来源详情入口；按任务选模块，不能把每个模块的全部数据加入提示词。目前目录仅有上述两项，尚未实现动态插件发现、任意组合查询、独立 App IPC 或无限量数据存储。真正拆分为独立 App 时仍需接入宿主已公开且授权的通信能力，不能把本轮模块调用称为跨 App 验证。

验收证据在 `build/module-routing-r1/`；早期失败日志保留。只使用隔离合成数据。
