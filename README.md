# DailyFlow

以日历为入口，串联记录、进展与行动。

DailyFlow 面向 OctoSense，目标是通过统一事件协议把生活记录、任务和持续新闻组织为时间 Flow。专业模块保留自己的业务能力，对话与卡片提供记录、查询和操作入口，遵循“明确内容自动记，含糊再问”。

## 当前状态

2026-10-02：用户确认全面更名为 **DailyFlow**。本地仓库、文档、应用与数据统一位于 `D:\Life\AgenticApp\DailyFlow`。

| 路径 | 用途与状态 |
| --- | --- |
| `docs/` | 产品规划、路线图和接手资料 |
| `apps/dailyflow-calendar/bundle/` | 日历原型，真实月份切换仍待完善 |
| `apps/dailyflow-expense/bundle/` | 记账占位应用 |
| `apps/dailyflow-diary/bundle/` | 日记占位应用 |
| `apps/dailyflow-period/bundle/` | 经期占位应用 |
| `bundle/` | 历史单 bundle 原型，ID 为 `dailyflow` |
| `.local-state/`、各 App 的 `.local-state/` | 本地运行数据，不进入 Git |
| `build/`、各 App 的 `build/` | 截图、日志与更名验证证据，不进入 Git |

目前仍为四个独立 App；单 App 协议验证是下一阶段建议，尚未实施功能合并。AI、宿主卡片和后台提醒均不能视为已完成。

## 文档入口

- [产品愿景与路线图](docs/PRODUCT_VISION_ROADMAP.md)
- [项目交接](docs/HANDOFF.md)
- [需求摘要](BRIEF.md)
- [原产品策划案](docs/PRODUCT_PLAN.md)
- [更名记录](docs/RENAMING.md)
- [Agent 接手规则](AGENTS.md)

工作区中的 `my-notes` 是独立 Demo。Windows 运行时修复和历史验证见 [工作区交接记录](../agent.md)。本地更名不包含提交、推送或发布。
