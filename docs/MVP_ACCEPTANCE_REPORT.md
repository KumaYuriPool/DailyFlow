# DailyFlow 0.2.0 单 App 实际验收

日期：2026-10-02，Asia/Shanghai。环境：Windows、现有 card-host、412×892 逻辑尺寸，截图 618×1338。应用业务全部为 `bundle/main.splash`；没有修改 Rust、Shell 或原生后台服务。

结论：**手工单 App 功能已实现并通过下述实际测试；真实 AI 自动记录闭环未完成，不能称为全部 MVP 完成。** 7 天真实个人试用未开始，AppCard/glance 和关闭应用后的唤醒未验证。未提交、推送或发布。

## 方法与证据

通过 `/snap` 读取真实 Label/Button/TextInput，再以 `/click`、`/k` 点击输入；对照两个状态文件中的最高有效修订，截图并实际打开检查。没有使用 Splash 源码字符串充当 UI 成功证据，没有向生产数据写入测试记录。

主要最终回归证据在 [build/mvp-final](../build/mvp-final/)，每张截图的同名 JSON 含真实控件和当时完整测试状态。之前的开发证据保留在 `build/mvp-test/`、`build/mvp-acceptance/`，不冒充最终版本。开发驱动器位于 `tools/`，只驱动宿主公开测试桥，不执行生产业务。

| 验收项 | 结果 | 实际观察及证据 |
| --- | --- | --- |
| 真实动态月历 | 通过 | 2024/2000 闰年二月 29 天，2025/2100 二月 28 天，2026 四月 30 天；日期列偏移与独立预期一致。[2024 二月](../build/mvp-final/14-calendar-2024-02-29.json)、[2100 二月](../build/mvp-final/14-calendar-2100-02-01.json) |
| 跨年、选择与跳转 | 通过 | 2026-12 → 2027-01 → 2026-12，今天、指定日期、月历选择工作。[跨年](../build/mvp-final/15-calendar-year-boundary.json) |
| 单账目跨两个 Flow | 通过 | 一条猫粮账目关联“宠物照护”和“生活账本”，源记录数始终为 1，两个 Flow 分别展示 45.25，全局不相加两组。[详情](../build/mvp-final/02-expense.json)、[Flow](../build/mvp-final/03-flow.json) |
| 金额更正同步 | 通过 | 32.50 → 45.25 后卡片、日历和 Flow 读取同一数据。[日历](../build/mvp-final/04-calendar-linked.json) |
| 记账输入校验 | 通过 | 拒绝三位小数、无效日期；实际消费不能保存为未来计划。输入保留。[校验](../build/mvp-final/13-validation.json)、[旧账更正](../build/mvp-legacy/26-source-expense-deleted.json) |
| 经期主动开启、重复 | 通过 | 未开启不写；开启后同日重复输入只保留 1 条；结束日可为空，后续可更正。[重复输入](../build/mvp-final/05-period-duplicate.json) |
| 经期隐私与完整 CRUD | 通过 | 新建、结束、更名、隐藏/恢复显示、源删除均经真实控件验证。[后续模块检查](../build/mvp-final/29-module-delete-sync.json) |
| Flow 创建、改名、隐藏、关联移除 | 通过 | 实际操作并检查成员引用与 hidden 状态。[旧账本场景](../build/mvp-legacy/25-legacy-idempotent.json)、驱动器 `tools/legacy_cases.py` |
| 删除 Flow 保留源记录 | 通过 | 删除宠物 Flow 后猫粮仍在，生活账本引用保留；源记录总数不变。[删除组](../build/mvp-final/09-flow-deleted-source-kept.json) |
| 预算首次越限 | 通过 | 预算 60，支出 45.25 + 5 时无提醒；改第二笔为 20 时生成 1 条，改为 21 仍为 1 条；已读后重查/重开不再刷出。[预算](../build/mvp-final/06-budget-first-cross.json) |
| 任务完成与延期 | 通过 | 到期任务延期一天后 due_at 增加 86400，旧提醒停用；完成保存真实 completed_at。[延期](../build/mvp-final/07-task-postponed.json)、[完成](../build/mvp-final/08-task-done.json) |
| 真实重开补偿 | 通过 | 最终版创建北京时间 16:56 到期任务，在到期前关闭；到期后重新启动生成 1 条提醒，重复检查不新增。[创建时](../build/mvp-final/17-before-restart.json)、[补偿](../build/mvp-final/18-restart-compensation.json) |
| 运行中定时检查 | 通过 | 创建 16:57 未来任务，留应用运行，未点击“立即检查”，由 20 秒定时回调产生提醒。[定时检查](../build/mvp-final/28-foreground-timer.json) |
| 任务取消、源删除 | 通过 | 取消和删除使对应提醒失效，源记录移除。[删除](../build/mvp-final/19-source-deleted.json) |
| 人工新闻 Flow | 通过 | 人工验收材料 A 的两个测试进展形成时间线；同标题/日期/出处重录被拦截，详情显示来源；更正与删除同步。[时间线](../build/mvp-final/10-news-timeline.json)、[来源](../build/mvp-final/11-news-source.json) |
| 手工固定卡片与详情路由 | 通过 | 对话页提供三个业务入口；保存后显示操作卡片，列表与最近记录入口实际打开同一记录。详情提供更正、删除、任务操作 |
| 真实 model.complete | **失败／平台缺口** | model 权限已授予，宿主返回 `no service answers "model" on this device`。[最小实验](../build/mvp-probe/dailyflow/model-probe.json)、[最终 UI](../build/mvp-final/12-model-unavailable.png) |
| 模型失败不伪造保存 | 通过 | 输入“今天午饭花了32元”仍保留，账目数不变；手工入口可继续使用。[控件及状态](../build/mvp-final/12-model-unavailable.json) |
| AI 明确项自动写入、歧义追问、更正撤销 | **未完成** | 当前无模型服务可验证；没有关键词解析或预设回执冒充 AI。未来宿主返回候选也只展示，不启用未经验证的自动写入 |
| 双槽写入和重启读回 | 通过（本轮样本） | 创建/更正/设置/Flow/任务数据从状态槽重开读回，提醒去重状态保留 |
| 导出与恢复 | 通过 | 备份后新增测试支出，再恢复；records、flows、alerts 与备份逐字段相等，新增支出移除，保留 before-restore。[恢复](../build/mvp-final/16-backup-restored.json) |
| 公共事件投影 | 通过 | 导出事件数与源记录数一致，source_revision、record_id 和 entry 引用一致；任务为 minute 精度。[最终导出](../build/mvp-final/30-final-export.json) |
| 保存失败与重试 | 通过 | 隔离目录中以同名空目录阻止下一状态槽写入，真实发生 write failed；界面显示未保存且输入保留，数据库未改；解除故障后重试成功。[失败](../build/mvp-failure/20-save-failure.png)、[重试](../build/mvp-failure/21-retry-saved.json) |
| 损坏备份拒绝、双槽损坏恢复 | 通过 | 无效备份不替换数据；两槽损坏启动只读保护，恢复有效 backup 后找回记录。[保护](../build/mvp-failure/23-corrupt-protection.png)、[恢复](../build/mvp-failure/24-corrupt-restored.json) |
| 旧数据兼容 | 通过 | 复制真实旧账本至隔离目录，导入 3 条合计 97.00；重复导入仍 3 条；原文件哈希未变。[导入](../build/mvp-legacy/25-legacy-idempotent.json) |
| AppCard / glance / 外部记录路由 | **未验证** | 本次为应用内卡片；不等同于宿主卡片与跨 App 工具接入 |
| 关闭后的定时唤醒、休眠、跨设备 | **未实现／未验证** | 只承诺运行中检查和重开补偿 |
| 连续 7 天个人试用 | **未验证** | 需要真实时间与用户反馈，本轮没有模拟完成 |
| 极限数据量、多实例、其他平台 | **未验证** | 不把数据格式上限当作性能保证；只验证 Windows 单实例 |

## 运行检查与视觉检查

`octo doctor` 中 Python、App Hub、hub、card-host、cargo 均为 `[ok]`。最终准入输出原文见 [check-output.txt](../build/mvp-final/check-output.txt)：

```text
dailyflow 0.2.0 — PASSED
  [warning] publisher-signature: unsigned: accountability rests on the hub alone
  grants: capabilities {"model", "storage"}, hosts {}, storage 16777216 bytes, agent none
```

工具另提示 listing 中 publisher/support/privacy 仍为历史占位资料，发布前须由真实发布者填写。平台声明已从模板 Android 改为本轮实际测试的 Windows。`hub scan` 生成了 [review.json](../build/mvp-final/review.json) 和开发者 [七项答复](../build/mvp-final/REVIEW-ANSWERS.md)，不是人工审核批准。

最终正常流程日志未发现 `[E]`、`on_render closure failed`、`callback error`；未复现独立日历旧 `ui target nil`。日志保留 Windows GPU 等待性能提示，不能称为无任何日志或性能问题。故障测试早期日志包含真实注入的 write failed 和损坏 JSON 读取错误；这促成了 `try/catch` 以及初始化前禁止定时写入的修复。

真实截图已打开查看，修复了控件默认白字在浅色背景上难读的问题。包内三张截图均来自最终真实 App 状态并已查看：日历、新闻 Flow、模型失败保留输入；没有生成或拼接替代截图。

## 数据保护、进程与边界

修改前备份源码与 `.local-state` 至 `build/mvp-baseline-20261002/`。本轮测试只使用 `build/mvp-*` 隔离目录。下列 SHA256 开发前后相同：

| 文件 | SHA256 |
| --- | --- |
| 真实 expenses.json | `6509489D906991F6EEBF551822DC0B4378CF4F2EA124C7A445F9C73AB5E9E48C` |
| App Hub Cargo.lock | `647462C851D540AA56C23813AC04EFD1BCEADDA6E46392B0B790DF3BF901FB46` |
| Makepad Windows d3d11.rs | `4C8247B37730481F0DE52D40A4F0F940926C46FC721F1C41ED11DE73628FE509` |

所有本轮启动的测试进程均通过各自端口 `/quit` 结束；关闭检查见 `build/mvp-final/cleanup.json`。Windows 有时先退出再发完 HTTP 响应，判断依据为端口和本轮进程是否仍在，不误杀其他应用。

已交付程序、Windows 启动脚本、[操作说明](USER_GUIDE.md) 和 [协议说明](DATA_PROTOCOL.md)。下一步可以开始真实个人试用；AI 需要目标宿主提供可用且授权的 model 服务后，另行验证结构化输出、业务校验与自动保存闭环，不通过新增原生服务绕开限制。
