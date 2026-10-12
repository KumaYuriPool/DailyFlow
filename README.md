# DailyFlow

本项目采用 [Apache License 2.0](LICENSE) 开源许可证。

DailyFlow 的产品方向是：由 Agent 理解用户的问题，把散落在不同应用里的个人经历组织成有来源、可核验、可更新的时间流，以轻量 OctoSense App 呈现。用户可查看来源、纠正关联并刷新变化。

2026-10-12 工作区已实现原生经历界面与官方应用 Agent 回传：提问后由 Agent 选择来源、读取当前导入记录，再经结构化工具提交带原文引用的概括和候选关系。界面可核对关联、确认/拒绝/撤销、保存经历；来源更正或删除后旧依据失效。费用确认与关联决定分开，旧日历、账本与经期在“我的空间”。当前仍为明确标记的导入样本，无实时跨 App 拉取、真实来源图片或云同步。见[官方回传与关联验收](docs/UX_AGENT_ACCEPTANCE.md)、[任务路线图](docs/UX_ROADMAP.md)。

首次公开版本 **0.1.0**（2026-10-06），对应此前内部开发版 0.6.4；版本号重新从 0.1.0 起算，业务能力与个人数据格式不变，App Hub 尚未入库。本版补入产品定位、核心概念与Flow的协议作用，没有新增业务能力。左下「帮助」内置离线使用说明，也可从「全部」搜索「使用说明」；正文与 [操作说明](docs/USER_GUIDE.md) 共用内容源。当前设计评估与下一阶段见 [产品路线规划](docs/PRODUCT_ROADMAP.md)，上架流程和差距见 [App Hub 提交说明](docs/APP_HUB_SUBMISSION.md)。

当前工作区准备 **0.1.1 候选版，尚未发布**：补官方 RC2 工具入口适配、随包许可证、模块对应说明及 GitHub 发布工作流。桥接的真实 Splash 注入测试通过；官方 RC2 应用 Agent 的读、拒绝/批准写、更正与宿主重启精确读回已有真实证据。系统助手委派与最终发布包仍待验收。独立来源实验位于 `experiments/source-bridge/`，不包含在生产包中，也不代表跨 App 已打通。

0.6.2修复无命名Flow的事项/费用关联，普通日历合并展示同日事项及其费用；旧复合记录按严格凭据备份后补关联，见 [源关联修复](docs/SOURCE_RELATIONS_FIX.md)。查找与时间协议继续保留，见 [按需回顾](docs/FLOW_RECALL.md) 与 [通用时间协议](docs/TIME_EVENT_PROTOCOL.md)。

首页现以经历为主；旧对话与工作区保留在“我的空间”，农历仍暂缓。历史四列界面证据见 [对话工作区验收](docs/CONVERSATION_WORKSPACE_ACCEPTANCE.md)，原业务证据见 [事件 Flow 验收](docs/EVENT_FLOW_ACCEPTANCE.md)。

## 启动

2026-10-12 当前本地开发版：双击 `run-dailyflow-latest.cmd`。它显式选择本机已验收的 Shell、RC2 kernel、新 Hub 和当前 `bundle/`；独立持久数据在 `.local-state/latest-desktop`，使用默认已有 Provider 配置，首次 Agent 授权由用户确认。启动脚本参数、语法与文件路径已检查，新入口本身尚未单独进行 GUI 验收。这是本地开发加载，不是 App Hub 安装；公开安装包尚未包含本轮更新。

0.1.1候选声明 `script-tools-v1`，需要支持该接口的完整宿主。当前已在官方RC2的隔离本地catalog中验证加载；RC2首次启动须先正常打开官方Calendar初始化Card运行器，详见[启动顺序记录](docs/RC2_CARD_STARTUP_REPRO.md)。官方应用Agent部分实测已通过；系统委派及GitHub发布包安装仍待验收。

旧 `run-dailyflow-ai.cmd` 和 `run-dailyflow.cmd` 默认仍选择10月6日本地工具链，只适用于历史版本，不能用来验收本候选；不自动替换用户运行时。开发验收可在 `run-dailyflow-ai.ps1` 分别传入 `-Binary`（RC2 Shell）、`-HubBinary`（新版Hub）、`-WarmCardRunner`、`-DataDir`（新隔离目录）和 `-CoreDir`（已配置Provider的独立core）。该入口创建临时本地legacy catalog，不是商店发布安装。只替换Binary而继续用旧Hub会在检查阶段失败；工具会给出具体原因。

历史AI入口数据位于 `.local-state/desktop/`，手工card-host入口数据位于 `.local-state/dailyflow/`；两个数据根独立，不自动合并。官方card-host不提供本候选要求的宿主工具API；旧补丁card-host的业务/注入测试也不能替代完整宿主。

升级不删除历史个人数据；首次实际写入前保存原容器备份。测试使用 build 下的新隔离目录。旧多应用原型和占位已退出活跃目录，原内容与数据保留在 `archive/legacy-apps/`；旧经期记录不会自动混入新的 period_entries。

## 开发与文档

- [经历界面与 Agent 交互设计](docs/UX_AGENT_INTERACTION_DESIGN.md)：基于第二版HTML原型的目标导航、任务状态、模型与工具接入、关联纠正和验收门槛；设计不代表实现完成。
- [产品说明](docs/PRODUCT_SPEC.md)：轻量事件流界面、时间事件核心、参考来源与官方 Agent 分工。
- [可接力路线图](docs/PRODUCT_ROADMAP.md)：28张任务卡、依赖、验收、失败分支与下一步。
- [执行状态](docs/EXECUTION_STATE.md)与[任务账本](docs/execution-state.json)：接手入口及唯一调度状态。
- [步骤交接模板](docs/STEP_HANDOFF_TEMPLATE.md)：每步版本、修改、证据、阻塞及进程交接。
- [复赛四天执行计划](docs/SEMIFINAL_PLAN.md)：北京时间 10 月 13 日 24:00 整截止；12 日中午功能冻结，13 日中午完成提交。
- [复赛执行进度](docs/SEMIFINAL_PROGRESS.md)：本轮通过项、阻塞与下一步，区分候选版和已发布版。
- [OctoSense RC2 更新核对](docs/OCTOSENSE_RC2_REVIEW.md)：官方更新与源码核对；实际进度见[官方宿主验收](docs/OFFICIAL_HOST_ACCEPTANCE.md)。
- [模块映射](docs/MODULE_MAP.md)：15个源码模块、构建顺序与工具派发。
- [独立来源实验](docs/SOURCE_BRIDGE_PROBE.md)：17项消费者契约验证及尚未通过的跨 App 边界。
- [GitHub 发布预检](docs/GITHUB_RELEASE_PREFLIGHT.md)与[复赛提交草稿](docs/SEMIFINAL_SUBMISSION_DRAFT.md)：候选发布材料，尚未对外提交。

- [首次提交正文](docs/APP_HUB_ISSUE_0.1.0.md)：产品介绍、展望、架构与审核信息。

- [模型执行链路与核心架构](docs/AGENT_EXECUTION_ARCHITECTURE.md)：流程图、Prompt与上下文、模块执行边界；修改Agent链路前先读。
- [操作说明](docs/USER_GUIDE.md)、[协议与模块边界](docs/EVENT_FLOW_PROTOCOL.md)
- [事件 Flow 历史验收](docs/EVENT_FLOW_ACCEPTANCE.md)、[旧收敛计划](docs/PET_CARE_FLOW_REPLAN.md)、[历史 P0](docs/P0_EXPERIENCE_PROTOCOL.md)、[历史 P1](docs/P1_MIGRATION.md)
- [Agent 接手](AGENTS.md)、[工作区保护与实际进度](../agent.md)
- `src/` 是应用层源码；`python -X utf8 tools/build_event_app.py` 构建 `bundle/main.splash`。
- 使用说明编辑 `src/user_guide.json`，构建时同步应用内正文与 `docs/USER_GUIDE.md`，不要分别维护两份文案。
- [测试命令](tools/README.md)。旧 0.3.0 文档在 `archive/0.3-docs/`；历史验收仍保留。

没有修改 Shell/Rust/Hub/Makepad。应用内 model.complete 与真实 card-host 工具调用分别验收；Shell Agent 跨 App 调用尚未完成真实验收。收据128条、单设备双槽、草稿不跨重启等边界见协议文档。
