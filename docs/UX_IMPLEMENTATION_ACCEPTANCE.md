# DailyFlow 经历界面实施与验收

> 本页保留 UX-00—05 的历史包验收。2026-10-12 随后完成的 UX-06/07 以 [官方回传与关联验收](UX_AGENT_ACCEPTANCE.md) 为准；下文“尚未完成”的两项已被新证据更新，其余边界保留。

2026-10-12。先回归旧路线，再执行 [UX-00—05](UX_ROADMAP.md)。生产 Splash 已加入经历首页和真实模型计划入口；并非把 HTML 演示直接当成生产实现。旧 roadmap、账本及证据完整保留在 [历史快照](history/pre-ux-20261012/PRODUCT_ROADMAP.md) 和原路径。

## 已实现

- 首页：经历目录、搜索、新建草稿、临时回顾保存、日期分组、详情与返回。来源和导入说明集中到设置；旧业务在“我的空间”。
- Agent：自然语言 → 宿主真实 `model.complete` → 主题、日期和最少来源计划 → 程序验证 → 读取当前导入文件 → 结果及逐来源读取计数。来源正文没有作为指令执行。保存经历不新增原始账目。
- 决策：本机 `experiences-v1.json`，独立经历 ID；完整 app/module/record 身份；移除、已排除列表、恢复、撤销；费用逐条确认，币种分开，金额/币种缺失不纳入统计。
- 来源变化：正式 producer/import/query/export 同步链更新后，界面重新读取；更正同一记录，删除使打开的详情失效。费用修订改变后重新待核对；重复刷新不重复生成原始记录。
- 任务隔离：请求序号和经历身份约束；停止、切换后的旧回调丢弃。来源开关仅控制本应用读取与上下文，不伪装宿主授权。损坏经历文件进入只读保护，原文件保留。

## 版本与证据

交付 `bundle/main.splash` SHA256：`9a1e41932ecc3ecc80d6a5b936c79d6a27fb6ee675f99f9b130979383ec84f28`。

交付 bundle BLAKE3：`f8338cd6d212ebd433b078fca07832adf48a683edb8a1c93639eb190e12448bf`，本地 unsigned/dev 候选；版本仍为 0.1.1，未发布。准入见 [hub check](../build/ux-hub-check.json)。

| 验证 | 结果及证据 | 边界 |
| --- | --- | --- |
| 修改前旧路线回归 | [13 套全部通过](../build/ux-20261012-baseline/report.json)，[基线准入](../build/ux-20261012-baseline/hub-check.json) | 基线 main 550f18f7；包含真实 UI、核心业务、resync、B1—B4 |
| 集成后旧路线 | [13 套全部通过](../build/ux-20261012-integrated/report.json) | 在经历界面首次集成版本上执行；随后修改仅限新经历模块的缺失金额和损坏存储保护 |
| 交付宽屏 UI | [15 项](../build/ux-delivery-wide/report.json) | 生产 bundle、真实点击、实际同步修订/墓碑、重启 |
| 紧凑 UI | [15 项](../build/ux-final-compact/report.json) | 412 宽度；后续仅损坏存储校验变更，不影响布局 |
| 费用 UI | [10 项](../build/ux-final-expenses/report.json) | CNY/USD、同 ID 两来源、金额更正、确认/排除分离、重启 |
| 协调层故障注入 | [18 项](../build/ux-final-contracts-r3/report.json) | 使用生产函数的标记测试副本；不作为真实 Provider、物理取消或授权证据 |
| 交付真实模型 | [两场景及零业务写入](../build/ux-delivery-model/report.json) | 相同生产 main.splash，宿主 Provider；[调用账本](../build/ux-delivery-model/apps/.host/model/ledger.json)及[配置保护/退出](../build/ux-delivery-model/cleanup.json) |
| 重复导入 | [投影幂等与墓碑保留](../build/ux-idempotence/report.json) | 独立输出目录 |
| 历史证据包 | [31 项](../build/ux-package-old-audit/repro-report.json) | 旧 ZIP 可追溯，未改成新版本；不是新 UI 安装发布证明 |

真实模型和宽屏测试后仅更新 listing 文案与两张实际截图，并重做 stamp/check；生产 main 字节未变。

UI 宿主为已验收的本地 655114c card-host 加 first-card 修复；真实模型使用现有本地编译 Shell 40ca21da 和官方 RC2 b0759a5 kernel。工作区 Git 后来更新到别的 revision，不等于这些二进制已经重编。测试均用独立 app 数据目录，未修改 Cargo.lock、Makepad Windows 修复、个人记录或原 Provider 配置。

所有中间失败目录保留：`ux-ui-01/02`、`ux-ui-narrow-01/02`、`ux-model-01/debug/02`、`ux-final-contracts` 等。包括发现的目录重绘、窄屏返回、宿主 `is_ok` 回执、对象错误调用字符串方法和损坏存储保护问题；不得把这些失败日志删除后声称从未出错。

## 可以如何演示

1. 打开当前 bundle 的经历首页。说明“这里使用已导入的模拟来源，模型请求是真实的”。旧 `run-dailyflow-acceptance.cmd` 固定历史验收副本，不能用于展示新界面。
2. 提问“整理我是怎么开始攀岩的，结合社媒、日历和费用”。展开“整理过程”，核对实际选择来源与计数；读取范围以导入快照为限。
3. 保存为经历，打开一条记录，看原文和来源修订；移除无关记录再恢复。
4. 逐条确认需要计入的费用，观察已确认与待核对分开；演示费用更正后需要再次核对。
5. 独立来源更正/删除后运行正式 sync，再点“重新读取”；不要把此按钮讲成自动联网拉取。
6. 改问演出问题，沿用同一模型计划和读取机制；从“我的空间”进入原日历/账本功能。

截图：[经历首页](../build/ux-delivery-wide/01-experience.png)、[记录详情](../build/ux-delivery-wide/02-detail.png)、[紧凑详情](../build/ux-final-compact/02-detail.png)、[真实模型结果](../build/ux-delivery-model/1-result.png)。

## 后续与发布边界

UX-06—10 仍未完成：官方应用 Agent 的启动/事件/取消适配，第二阶段有引用的模型概括与具体跨事件候选边，图片与键盘焦点完善，受控 UI 文件导入和 App 到 App 拉取，账号及云同步。当前日期组只表明同日，费用确认只表示计入本经历，不能拿来宣称已实现复杂关系推理。

没有物理模型取消 API 接线；“停止”立即拒收后续结果，UI明确提示后台调用可能仍在结束。来源关闭并不撤销宿主权限。跨 App 权限拒绝、单来源网络超时、分页等外部能力仍随 UX-06/09 验证，不能用导入样本代替。

旧 DF-20/21/23 的包证据属于旧冻结版本。新 UI 要发布仍需刷新候选包与安装材料，然后按 DF-22/25 处理外发授权；本轮未 push、打标签、发布或提交比赛。接手只读 JSON 中 `active_task` 和 `next_action`，不重复建立调度账本。

## 接手文件与验证命令

生产：`src/47_experience.splash` 管任务与视图仓库；`src/65_experience_ui.splash` 管经历界面；`60_ui` 保留旧业务；`tools/build_event_app.py` 将两个 UI 树装入根容器；exporter 补齐模块和币种字段。新旧 UI 共用原业务存储，但新决定单独保存。

所有测试输出必须使用全新 build 子目录。运行 Python 需使用已配置 bundled Python；GUI 测试仅禁用 loopback HTTP 的代理。不要把 overlay envelope 写进 canonical `build/semifinal-202610/synthetic-source`。

```text
python -X utf8 tools/build_event_app.py
hub stamp bundle
hub check bundle --allow-unsigned --json
python -X utf8 tools/test_experience_ui.py --output build/<fresh-wide> --wide
python -X utf8 tools/test_experience_ui.py --output build/<fresh-compact>
python -X utf8 tools/test_experience_expenses.py --output build/<fresh-expenses>
python -X utf8 tools/test_experience_contracts.py --output build/<fresh-contracts>
python -X utf8 tools/test_experience_model.py --output build/<fresh-model> --core-dir <existing-configured-core>
python -X utf8 tools/run_ux_regression.py --output build/<fresh-regression>
```

hub 使用 `build/semifinal-202610/release-preflight/hub-build/app-hub/target/release/hub.exe`。不要向报告复制 Provider 密钥；测试自己的 core 配置副本也不应打进发布包。
