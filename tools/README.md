# 当前事件 Flow 构建与验收工具

0.6.3新增：`test_help_ui.py --output build/<new-dir> --binary <active-card-host>`（可加 `--wide`）。使用新隔离空数据，实际点击内置指南七节、滚动、搜索入口及返回，检查对话/表单草稿保留和业务只读；不请求模型。编辑指南正文用 `src/user_guide.json`，运行 `build_event_app.py` 同步包与 USER_GUIDE.md。

0.6.2新增：`test_source_relations.py`（无Flow关系/日历合并/严格备份修复与故障），`test_source_relations_ui.py`（合成旧数据恢复后的宽窄屏点击，--seed仅合成目录），`test_source_relations_model.py`（完整宿主＋已有Provider一条合成SPA输入）。契约/UI传--output新目录及--binary活跃card-host；真实模型用已有带cryptography的Python，仅传--output。见docs/SOURCE_RELATIONS_FIX.md。

0.6.1新增 `test_recall.py`（真实只读搜索/关系/分页工具契约）、`test_recall_ui.py`（实际点击）。后者 `--seed` 只接合成测试目录，可加 `--wide`；两者传 `--output build/<new-dir> --binary <active-card-host>`。不得用个人目录作seed。当前验收见 docs/FLOW_RECALL.md。

0.6.0新增：`test_time_protocol.py` 验证注册式时间协议和第三/第四来源；`test_period_ui.py` 验证经期手工区间CRUD及日历来源（可加 `--wide`）；`test_period_model.py` 用已有Provider查询合成经期数据。前两者传 `--output build/<new-dir> --binary <active-card-host>`；真实模型测试传 `--output build/<new-dir> --seed-state <synthetic-state-folder>`，使用已有含cryptography的Python。不得传个人数据作为seed。

生产只运行 Splash；Python 工具用于构建、启动或隔离测试，不承载业务。运行目录为 DailyFlow，输出必须是新目录。

```powershell
python -X utf8 tools/build_event_app.py
python -X utf8 tools/test_event_flow.py --output build/<new-business>
python -X utf8 tools/test_event_contracts.py --output build/<new-contracts>
python -X utf8 tools/test_event_agent.py --output build/<new-injected>
python -X utf8 tools/test_event_lifecycle.py --output build/<new-lifecycle>
```

`test_event_lifecycle.py` 需要本轮保存的 `build/event-flow-r2/baseline/bundle`，用真正旧代码产生兼容收据。协议夹具测试使用只有 reducer 的最小 Splash，不加载记账界面。

真实 Provider 和 UI 测试使用现有包含 cryptography 的 Python（启动器可自动选择），不安装依赖、不复制 Provider。`test_event_real.py --output build/<new-real>` 执行七条真实黄金场景；默认测试源码与正式源码一致。`--capture-proposal` 仅用于人工构造场景的开发诊断，不能用于真实个人数据。

`test_event_real_edges.py --output build/<new-edges> --seed build/event-flow-r2/real3/apps/dailyflow` 验证两项歧义。`test_event_ui.py --output build/<new-ui> --seed build/event-flow-r2/real3/apps/dailyflow` 使用既有合成模型数据做412×892点击、截图、编辑、删除和重启。seed 只允许合成测试状态，不能使用个人数据目录。

每个 harness 只关闭自己启动的进程并记录 cleanup。已有 test_business_flow/test_chat_integration/test_real_model_flow 等是0.3.0历史工具，不能作为0.4.0通过依据；UI类和桌面隔离启动器被当前测试复用。
