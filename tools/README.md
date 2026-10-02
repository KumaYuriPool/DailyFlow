# 开发验收工具

这些 Python 文件只向本机 card-host 的公开测试桥发点击、输入和截图请求，读取隔离测试文件作断言。生产运行只需要 bundle 和启动脚本，不依赖这些测试工具。

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
