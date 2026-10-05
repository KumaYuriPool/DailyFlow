# DailyFlow

一个 OctoSense Splash App：支出账本、普通/账本双视图日历、事件 Flow。用“说一件事”统一记录，信息明确自动保存，归属或金额不确定先追问。宠物护理只是通用事件的验收场景。

当前本地版本 **0.5.1**（2026-10-05），未提交、未发布。对话首页、常驻输入、应用／Flow／视图搜索、浏览与补记分离已实现。事件图继续保存独立事实、费用源引用与明确计划关系。

实际交付及证据见 [对话工作区验收](docs/CONVERSATION_WORKSPACE_ACCEPTANCE.md)。采用左入口栏、顶部 Flow 选择和整页工作区；预览的四列并排、面板放大及农历暂缓。原业务证据仍见 [事件 Flow 验收](docs/EVENT_FLOW_ACCEPTANCE.md)。

## 启动

Windows 双击 `run-dailyflow-ai.cmd`，使用已有完整桌面及 Provider；数据位于 `.local-state/desktop/`。手工入口 `run-dailyflow.cmd` 使用 card-host，数据位于 `.local-state/dailyflow/`，不提供模型。这两个数据根独立，不自动合并。

升级不删除历史个人数据；首次实际写入前保存原容器备份。测试只使用 `build/event-flow-r2/` 内新隔离数据。旧多应用原型和占位已退出活跃目录，原内容与数据保留在 `archive/legacy-apps/`。

## 开发与文档

- [操作说明](docs/USER_GUIDE.md)、[协议与模块边界](docs/EVENT_FLOW_PROTOCOL.md)
- [当前验收](docs/EVENT_FLOW_ACCEPTANCE.md)、[主计划](docs/PET_CARE_FLOW_REPLAN.md)、[P0](docs/P0_EXPERIENCE_PROTOCOL.md)、[P1](docs/P1_MIGRATION.md)
- [Agent 接手](AGENTS.md)、[工作区保护与实际进度](../agent.md)
- `src/` 是应用层源码；`python -X utf8 tools/build_event_app.py` 构建 `bundle/main.splash`。
- [测试命令](tools/README.md)。旧 0.3.0 文档在 `archive/0.3-docs/`；历史验收仍保留。

没有修改 Shell/Rust/Hub/Makepad。应用内 model.complete 与真实 card-host 工具调用分别验收；Shell Agent 跨 App 调用尚未完成真实验收。收据128条、单设备双槽、草稿不跨重启等边界见协议文档。
