# DailyFlow 更名记录

日期：2026-10-02。用户明确要求全面更名；本轮完成本地项目、应用标识和数据目录迁移，未提交、推送或发布。

## 名称与目录映射

| 更名前 | 更名后 |
| --- | --- |
| 产品 Daily | DailyFlow |
| 工作区 Daliy 仓库 | DailyFlow 仓库，保留 .git 和既有修改 |
| 工作区 Daily/apps | DailyFlow/apps |
| 应用 ID daily | dailyflow |
| daily-calendar | dailyflow-calendar |
| daily-expense | dailyflow-expense |
| daily-diary | dailyflow-diary |
| daily-period | dailyflow-period |
| .local-state/daily | .local-state/dailyflow |
| 各 App 的 .local-state/daily-* | 各 App 的 .local-state/dailyflow-* |

四个独立 App 的结构保留。目录统一不等于合并为一个功能 App。文档正文、可执行命令、manifest、listing 与 Splash 中的产品引用已更新；历史截图、日志和失败源码备份保持原样，因此其中仍可出现旧名称。

## 数据与 Git

迁移前后旧原型 `expenses.json` 的 SHA256 均为 `6509489D906991F6EEBF551822DC0B4378CF4F2EA124C7A445F9C73AB5E9E48C`，文件内容未改变。

初次 Windows Move-Item 返回权限错误但已移动部分根文件和 Git 内容。检查后通过提升权限移动剩余目录，最后仅移除已经确认无内容的旧目录，没有覆盖目标或重置仓库。Git 的既有未提交修改继续保留。

远端仍为 `https://github.com/KumaYuriPool/Daliy.git`。本机没有 gh 命令，本轮浏览器访问 GitHub 超时，未完成远端仓库更名；为了保持 remote 有效，没有改成未经确认的新地址。远端仓库名称是尚未完成的更名项，不代表本地更名失败。

## 验证结果

- 五个 bundle 均已重新 stamp，并通过准入检查：dailyflow、dailyflow-calendar、dailyflow-expense、dailyflow-diary、dailyflow-period。
- 五个 bundle 均以新 ID 启动并截图。三张占位页的真实 Label 均为 `DailyFlow placeholder`。
- 三个占位 App 与旧单 bundle 的截图已更新到对应包内，原截图保存在 `build/rename-dailyflow/`。
- 日历独立 App 仍触发 `proto_field ui target is not an object (got nil)`。旧日志也有同类错误；本轮记录但未扩展为功能修复，不能称为全部运行验收通过。日历截图保存在证据目录，原 listing 截图未替换。
- 旧原型 bundle 中的 `main.splash.v0.3-broken.bak` 会导致 gate 拒绝，已原样移至 `build/main.splash.v0.3-broken.bak` 后重新检查通过。
- 测试使用独立数据目录，未对真实账目执行增删改；端口 8156–8160 均已关闭。
- 未修改 App Hub Cargo.lock 和 Makepad Windows 渲染补丁。listing 中发布者占位信息和未签名警告仍存在，尚不能直接发布。

证据：`build/rename-dailyflow/results.json`、各 App 的 `*-check.log`、`*-snapshot.json`、PNG 与运行日志。

## 后续事项

远端仓库更名为 DailyFlow 后，再更新 origin 并验证访问。修复日历既有错误、实施协议 MVP、签名和发布是后续独立工作。
