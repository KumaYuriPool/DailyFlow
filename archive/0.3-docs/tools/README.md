# 开发验收工具

## 0.3.0 当前入口

应用业务只运行在 Splash 中。Python 用于本地桌面启动和隔离验收，不负责解析、记账或写业务状态。正常用户使用 `run-dailyflow-ai.cmd`；独立 `run-dailyflow.cmd` 是无模型的手工入口。模型测试仅发送脚本列明的虚构测试语句。

以下测试必须使用不存在的新输出目录；脚本复制 bundle，不向个人数据写入：

```powershell
python -X utf8 tools/test_business_flow.py --output build/check-business-new
python -X utf8 tools/test_chat_integration.py --output build/check-chat-new
# 需要现有 Python 已提供 cryptography（AI 启动脚本也会自动定位可用运行时）
python -X utf8 tools/test_real_model_flow.py --output build/check-model-new --core-dir "$env:USERPROFILE/.octosense/octos-home/.octos"
```

- `test_business_flow.py` / `business_test_driver.py`：真实 card-host 工具调用、存储失败、隐私过滤、幂等重放和修订检查；不经过 Shell Agent 或模型。
- `test_chat_integration.py`：注入明确标识的模拟模型回复，验证真实 Splash 对话状态、业务保存及重启恢复；不证明 Provider 可用。
- `test_real_model_flow.py`：现有桌面真实 `model.complete`，三次请求验证自动记账、Flow 复用、含糊金额追问及图形结果。使用 `desktop_flow_probe.py` 的隔离数据与仅内存保存的本地临时签名，不发布到商店、不复制 Provider 配置或密钥。
- `launch_desktop_flow.py`：本地开发启动器，与测试共用 bundle 准备逻辑；正常启动不开放测试远程端口。依赖现有 `hub.exe`、`octosense.exe` 和 Python `cryptography`。

这三类结果需分别报告。测试失败会保留证据；退出只关闭自己创建的进程。

## 0.2.0 历史脚本

以下脚本对应旧版 UI 的按钮文本；不得直接当作 0.3.0 已通过的验收。它们保留用于维护旧证据和后续迁移。

这些 Python 文件向本机 card-host 的公开测试桥发点击、输入和截图请求，读取隔离测试文件作断言。

`bridge_test.py` 先读 `/snap`，按真实控件文本或 ID 定位，过滤 Splash 源码节点。`acceptance_cases.py` 驱动完整业务流程；`final_cases.py` 验证真实运行时定时器及模块删除；`edge_cases.py` 在专用 mvp-failure 目录注入写入失败和损坏文件；`legacy_cases.py` 在 mvp-legacy 中操作旧数据副本。不要把故障测试指向个人数据。

复跑主流程需要一个新的空目录，保留已有证据目录：

```powershell
$env:DAILYFLOW_TEST_DATA = 'mvp-rerun-unique'
./run-dailyflow.ps1 -Hidden -Detach -Port 8171 -AppData "$PWD/build/$env:DAILYFLOW_TEST_DATA"
python -X utf8 tools/bridge_test.py
python -X utf8 tools/acceptance_cases.py
# Phase 1 创建真实未来任务并关闭 App。等 restart-due.json 的时间真正过去后：
./run-dailyflow.ps1 -Hidden -Detach -Port 8171 -AppData "$PWD/build/$env:DAILYFLOW_TEST_DATA"
python -X utf8 tools/acceptance_cases.py phase2
python -X utf8 tools/final_cases.py
# 等 timer-due.json 的到期时间加 20 秒真正过去，保持 App 运行：
python -X utf8 tools/final_cases.py verify
Invoke-RestMethod http://127.0.0.1:8171/quit
```

退出响应偶尔断连时，验证对应端口释放。不要关闭并非本轮启动的实例。故障/旧数据脚本面向本轮固定隔离目录，重复运行前需另存证据并准备全新副本，不提供清空真实数据的快捷命令。
