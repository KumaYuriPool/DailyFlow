# DailyFlow 源码与构建映射

本页对应评审要求的 src 到 build_event_app.py 映射。核对基线为 e7d4cdba95675c4e9ef56f9a334c2a8444780005，当前比赛开发继续在此基础上进行。构建模块与入口以源码为准；本页不代表官方宿主调用已经验收通过。

## 从入口追踪一次请求

构建入口为 [tools/build_event_app.py](../tools/build_event_app.py)。在仓库根目录运行：

```powershell
python -X utf8 tools/build_event_app.py
```

脚本按 FILES 列表读取15个 Splash 文件，拼接为 [bundle/main.splash](../bundle/main.splash)。它不是把15个文件编译成15个独立 App；输出仍是一个脚本应用。只编辑 src，不手改生成的 main.splash。

启动时，[60_ui.splash](../src/60_ui.splash) 注册延迟 boot；[00_storage.splash](../src/00_storage.splash) 读取并校验双槽状态，选择有效且较新的修订，再执行已知旧关系修复和日历投影重建。损坏状态进入写保护。

应用内对话路径：60_ui 的发送动作 → 50_agent.send_model（简单总额可走本地查询）→ 宿主 model.complete → chat_receive / agent_apply → 查询路由或40_coordinator → 源模块 → persist读回校验 → UI显示结果和来源。模型不从最多12条摘要估算全量统计。

官方应用Agent工具路径：宿主发现及授权 → [bundle/tools.json](../bundle/tools.json) 声明的 dailyflow.* → 40_coordinator.app_tool(name,call_id) → business_dispatch_official_tool检查active并读取request → business_dispatch_tool_using → 同一业务查询/写入层 → complete/fail返回宿主。0.1.1候选保留on_agent_tool与resolve/reject作为旧本地运行时和回归入口，两条入口复用业务派发。桥接源码适配不等于新版官方宿主授权实测通过；应用内模型成功不能替代这条链路。

## 活跃模块的准确顺序

| 顺序 | 源文件 | 职责与定位入口 |
| --- | --- | --- |
| 1 | [00_storage](../src/00_storage.splash) | 共享状态、日期金额基础校验、boot、双槽persist、备份恢复；启动与落盘边界 |
| 2 | [05_subjects](../src/05_subjects.splash) | subject_catalog / subject_resolve_query；主体身份与歧义校验 |
| 3 | [08_time_protocol](../src/08_time_protocol.splash) | protocol_envelope、source_snapshot、projection_accept、timeline_query；公共时间协议、来源分发及修订投影 |
| 4 | [10_expense](../src/10_expense.splash) | expense_snapshot / write / remove / summary_query；权威账目及整数分统计 |
| 5 | [15_period](../src/15_period.splash) | period_snapshot / write / remove / history_query；独立日期区间，未知结束保持未知 |
| 6 | [20_calendar](../src/20_calendar.splash) | calendar_snapshot / write / next_query；事项源；calendar_rebuild消费公共协议投影 |
| 7 | [30_flow](../src/30_flow.splash) | flow_catalog / relation_add / flow_query；主体范围与明确关系，不按同日猜关联 |
| 8 | [32_recall](../src/32_recall.splash) | recall_query；关键词/主体和已有关系组织临时时间线、修订分页 |
| 9 | [35_query_router](../src/35_query_router.splash) | module_capabilities / module_query；查询条件校验、白名单回调和来源引用 |
| 10 | [38_modules](../src/38_modules.splash) | time_modules / query_capabilities；三个来源适配器和三个对话查询能力的组合入口 |
| 11 | [39_relation_repair](../src/39_relation_repair.splash) | recover_compound_relations / repair_source_relations；只恢复严格匹配的历史漏边，备份失败不提交 |
| 12 | [40_coordinator](../src/40_coordinator.splash) | coordinator_apply / business_save / business_query / business_dispatch_tool；业务事务、收据幂等、工具派发 |
| 13 | [50_agent](../src/50_agent.splash) | send_model / chat_receive / agent_apply；受约束意图、超时/迟到拒绝、澄清和来源展示 |
| 14 | [55_help](../src/55_help.splash) | open_help / help_select；只读帮助导航，正文由构建脚本注入 |
| 15 | [60_ui](../src/60_ui.splash) | 唯一活跃Widget树；导航、对话、日历/账本、查找、源详情、手工写入和帮助 |

构建脚本还读取 [src/user_guide.json](../src/user_guide.json)，把正文嵌入55_help，并生成 [docs/USER_GUIDE.md](USER_GUIDE.md)。帮助正文只改JSON源。ButtonFlat/TextInput样式替换只作用于60_ui，不能据生成文件搜索结果推断所有模块都被改写。

src/61_app_rail.splash、62_flow_rail.splash、63_main_col.splash、64_workspace.splash 是未纳入 FILES 的旧布局实验。它们不参与当前产物，也不是额外四个应用。

## 工具到执行函数的映射

| tools.json名称 | 派发目标 | 重要边界 |
| --- | --- | --- |
| dailyflow.query | business_query | 费用与事项源；不作为经期通用读取接口 |
| dailyflow.flow_query | flow_query | 范围与关系视图 |
| dailyflow.capabilities | module_capabilities + subject_catalog | 返回实际注册能力与主体目录，包含私人信息 |
| dailyflow.module_query | module_query | expense.summary、calendar.next、period.history |
| dailyflow.timeline_query | timeline_query | 日期区间、来源筛选及修订分页；shareable:false |
| dailyflow.recall | recall_query | 按需回顾；shareable:false |
| dailyflow.save_record / dailyflow.apply | business_save → coordinator_apply | 支持删除，声明destructive与confirm:host；应用另验修订与重复请求 |

工具输出都应按私人数据处理。共享声明不是调用授权，也不证明跨App owner解析已经可用。官方宿主审批与应用内对话的明确事实自动保存是不同入口，材料不得混称为所有写入都经过同一审批UI。

## 修改与验证边界

新增参考来源通常需要源模块、38_modules注册、FILES顺序和对应契约测试；公共时间逻辑不应堆积每个来源的业务分支。当前来源仍是同包适配器，独立来源要另外验证通信、授权及结果入投影。

已有测试入口包括 [test_business_flow.py](../tools/test_business_flow.py)、[test_time_protocol.py](../tools/test_time_protocol.py)。它们的实际调用证据、模型注入证据、真实Provider、官方Agent、UI、包检查应分开登记。构建映射静态核对通过不能替代上述运行验收。
