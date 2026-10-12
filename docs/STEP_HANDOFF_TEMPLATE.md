# 单步骤接力交接模板

每次完成或中断一张卡都复制本模板到`build/semifinal-202610/steps/<DF-ID>/<run-id>/handoff.md`，在execution-state.json填写路径。run-id建议北京时间日期时间+短描述；不要覆盖旧run。新增文件是运行证据，不默认公开。

## 身份和状态

- task_id / 标题：
- owner / 接手者：
- started_at / ended_at（ISO时间及Asia/Shanghai）：
- 状态：not_started / in_progress / passed / blocked / deferred
- 当前route及能力门槛：
- next_action（准确到下一条命令或人工操作）：
- 接下来允许领取的任务ID：

## 输入与保护

- 各仓库绝对路径、HEAD、开始时dirty文件列表：
- 本次用的Shell/Hub/kernel实际路径、源码版本、二进制SHA256：
- bundle摘要、schema/fixture版本：
- 保护文件起始哈希；原有更改归属：
- 隔离数据根；备份位置；不含个人数据/凭据的确认依据：
- 前置卡证据及可读检查：

## 本次实际做了什么

| 文件绝对路径 | 原有/本次修改 | 修改目的 | 是否生成产物 |
| --- | --- | --- | --- |
| 待填 | 待填 | 待填 | 待填 |

- 具体实现/设计决定与理由：
- 尚是假设的内容（不得写成事实）：
- 未修改但发现的新问题：

## 命令与验证

| 命令/人工步骤 | cwd/工具版本 | 输入fixture | 退出码/结果 | 证据路径 |
| --- | --- | --- | --- | --- |
| 待填 | 待填 | 待填 | 待填 | 待填 |

- 对任务卡每条完成门槛逐项判断：
- 正常、错误、取消/权限、重启中实际测了哪些：
- 测试性质：静态/注入/真实VM/真实模型/官方宿主/自编译宿主/人工UI。
- 未验证的部分及原因：
- 最终准确文件/包摘要：

## 失败与恢复

- 最小复现：
- 预期/实际/原始错误：
- 已尝试办法及结果，不要让下一位重复无效尝试：
- 尚未尝试的最小下一步：
- 已耗时间/时间盒剩余；到时如何降级：
- 回退文件列表、备份及操作范围；禁止reset/clean整个仓库：
- 阻塞解除条件、需人的操作：

## 运行资源与交接

- 活跃进程：PID、可执行文件、启动用途、数据根、确认存活时间。
- 服务端口、日志、会话ID；无则明确none，不保留假PID。
- 哪些已关闭、哪些留给用户；下一位如何安全恢复/退出：
- 临时文件保留/清理说明；未清理不能默认为已清理。
- 外部动作/授权：未执行或列准确已授权范围、链接、回执。
- execution-state.json与root agent.md已更新：是/否。

## summary.json最小结构

```json
{
  "task_id": "DF-XX",
  "run_id": "replace-me",
  "status": "blocked",
  "owner": "replace-me",
  "route": "undecided",
  "input_versions": {},
  "changed_files": [],
  "checks": [],
  "evidence": [],
  "failure": null,
  "capability_updates": {},
  "active_processes": [],
  "next_action": "具体下一步",
  "next_tasks": []
}
```

状态账本只放索引，长日志放run目录。模板空白不是完成证据。禁止将Provider profile、密钥、整段私人聊天或整个业务数据库复制进公开交接；合成数据也应标明性质。
