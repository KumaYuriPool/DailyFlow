# Daliy

面向 OctoSense 的个人记账工具。

初步想法：通过对话输入消费或收入信息，自动记账并分类。

## 当前状态

2026-10-01：仅创建项目骨架，尚未开发任何页面、记账、分类或 AI 功能。

- 项目名称：**Daliy**，保留用户指定拼写，不改成 Daily。
- 计划应用 ID：`daliy`，尚未生成应用 manifest。
- 开发环境：Windows / PowerShell，使用工作区已有 OctoSense 工具链。
- `bundle/`：预留应用包目录，目前只有目录占位文件，不可运行或发布。
- 需求记录：[BRIEF.md](BRIEF.md)。
- 模型接手入口：[AGENTS.md](AGENTS.md)。

工作区已有的 `../my-notes` 是独立的参考 Demo，其功能未复制到本项目。
完整环境、Windows 运行时修复和历史验证见工作区的 `../agent.md`。

开始开发前，需要进一步确定首版范围、对话输入方式、自动记账确认规则和分类方式。
