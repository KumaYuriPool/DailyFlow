# DailyFlow

一个 OctoSense Splash App，帮助你随手记录生活中的事，想起时找回来，并回到原记录继续处理。以对话输入、统一时间协议和后台 Flow 组织为基础，日历按天看，查找围绕事情回看。当前用支出账本、日历事项和经期记录验证；宠物护理只是通用场景。

当前本地版本 **0.6.4**（2026-10-06），未发布。本版补入产品定位、核心概念与Flow的协议作用，没有新增业务能力。左下「帮助」内置离线使用说明，也可从「全部」搜索「使用说明」；正文与 [操作说明](docs/USER_GUIDE.md) 共用内容源。当前设计评估与下一阶段见 [产品路线规划](docs/PRODUCT_ROADMAP.md)，上架流程和差距见 [App Hub 提交说明](docs/APP_HUB_SUBMISSION.md)。

0.6.2修复无命名Flow的事项/费用关联，普通日历合并展示同日事项及其费用；旧复合记录按严格凭据备份后补关联，见 [源关联修复](docs/SOURCE_RELATIONS_FIX.md)。查找与时间协议继续保留，见 [按需回顾](docs/FLOW_RECALL.md) 与 [通用时间协议](docs/TIME_EVENT_PROTOCOL.md)。

当前为 App 导航、对话与按需工作区，面板可放大，窄屏分层，农历仍暂缓。历史四列界面证据见 [对话工作区验收](docs/CONVERSATION_WORKSPACE_ACCEPTANCE.md)，原业务证据见 [事件 Flow 验收](docs/EVENT_FLOW_ACCEPTANCE.md)。

## 启动

Windows 双击 `run-dailyflow-ai.cmd`，使用已有完整桌面及 Provider；数据位于 `.local-state/desktop/`。手工入口 `run-dailyflow.cmd` 使用 card-host，数据位于 `.local-state/dailyflow/`，不提供模型。这两个数据根独立，不自动合并。

升级不删除历史个人数据；首次实际写入前保存原容器备份。测试使用 build 下的新隔离目录。旧多应用原型和占位已退出活跃目录，原内容与数据保留在 `archive/legacy-apps/`；旧经期记录不会自动混入新的 period_entries。

## 开发与文档

- [模型执行链路与核心架构](docs/AGENT_EXECUTION_ARCHITECTURE.md)：流程图、Prompt与上下文、模块执行边界；修改Agent链路前先读。
- [操作说明](docs/USER_GUIDE.md)、[协议与模块边界](docs/EVENT_FLOW_PROTOCOL.md)
- [当前验收](docs/EVENT_FLOW_ACCEPTANCE.md)、[主计划](docs/PET_CARE_FLOW_REPLAN.md)、[P0](docs/P0_EXPERIENCE_PROTOCOL.md)、[P1](docs/P1_MIGRATION.md)
- [Agent 接手](AGENTS.md)、[工作区保护与实际进度](../agent.md)
- `src/` 是应用层源码；`python -X utf8 tools/build_event_app.py` 构建 `bundle/main.splash`。
- 使用说明编辑 `src/user_guide.json`，构建时同步应用内正文与 `docs/USER_GUIDE.md`，不要分别维护两份文案。
- [测试命令](tools/README.md)。旧 0.3.0 文档在 `archive/0.3-docs/`；历史验收仍保留。

没有修改 Shell/Rust/Hub/Makepad。应用内 model.complete 与真实 card-host 工具调用分别验收；Shell Agent 跨 App 调用尚未完成真实验收。收据128条、单设备双槽、草稿不跨重启等边界见协议文档。
