# DailyFlow 提交 App Hub：当前流程与差距

> 2026-10-06：首次公开版本已按用户决定改为 0.1.0，署名毛茸茸战队，unsigned，暂不附视频。唯一正文见 [0.1.0 Issue 草稿](APP_HUB_ISSUE_0.1.0.md)。用户已授权创建并推送版本标签，尚未要求发送 Issue；以下 0.6.4 为内部开发期历史。

2026-10-06 待审更新：用户指定署名“毛茸茸战队”，确认原KumaYuriPool/Daliy仓库；GitHub返回现名KumaYuriPool/DailyFlow，仍为同一公开仓库。当前已在本地替换占位listing、准备PRIVACY.md、当前合成截图与check/scan材料，见 [0.6.4待审材料](SUBMISSION_REVIEW_0.6.4.md)。用户明确要求审核后才提交，视频由用户自己录；未提交/推送/tag/签名/发Issue/发布。下文“占位资料”记录准备前检查，不代表新的本地草稿仍有同样占位；隐私URL和版本tag仍需审核后实际发布并验证。

核对日期：2026-10-06。已读取上游 main 的最新 [OctoSense README](https://github.com/OctoSense-org/OctoSense/blob/main/README.zh-CN.md)、[App Hub 发布说明](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/main/docs/PUBLISHING.md#submitting) 和 [Design Flow 发布说明](https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/docs/PUBLISHING.md)。线上文档是流程依据，本地旧文档仅作对照。

## 官方接受的路径

1. 应用源码和 bundle 放在自己的公开仓库；完善 listing、图标和至少一张真实 PNG 截图。截图更新后重新 stamp。
2. 在最终包上运行 `hub stamp bundle`、`hub check bundle --allow-unsigned` 和 `hub scan bundle --packet build/review.json`，回答 scan 的审核问题。
3. 正式签名使用仓库外保管的发布者私钥，先 stamp、再 `hub sign-manifest`，然后用公钥运行 `hub check --publisher-key`。首次允许 unsigned；一旦发布者密钥被登记，后续更新必须保持签名连续性。
4. 将最终包提交、推送到公开仓库，并为确切提交打版本标签。
5. 在 [App Hub Issues](https://github.com/OctoSense-org/OctoSense-App-Hub/issues) 新建 `Submit dailyflow <version>`，附仓库地址、tag、完整 SHA、bundle 路径、发布者 ID/公钥（或首次 unsigned）、该提交的完整 check 输出和 scan 答案。
6. 维护者检查同一提交，审核后执行 publish 并更新签名目录。提交者不修改 Hub 的 catalog/index/artifacts；目前没有独立 index 仓库或 publish-app Action。

签名后只要包内容有变，就必须重新 stamp、签名和检查。review.json 留在 build，不放进 bundle。以上是操作说明，本轮没有执行签名、提交、推送、tag、Issue 或发布。

## DailyFlow 还缺什么

- 当前 origin 是 `https://github.com/KumaYuriPool/Daliy.git`，bundle 在 `bundle/`。未核验该远端可见性，也没有将本地 0.6.3 推送过去；现有 HEAD 不代表当前工作区包。
- `listing.json` 发布者仍为 `Replace with your publisher name`，支持和隐私地址仍是 example.com。需要真实发布者信息、可访问的支持渠道，以及覆盖本地记录与模型摘要发送行为的隐私说明。
- 商店 release_notes 仍描述 0.4.0；已查看的 `03-event-flow.png` 仍是旧蓝色日历/事件图界面。需要按准备提交的版本重新整理商店说明并拍摄截图，不能将历史图当作当前界面。
- 当前包未签名，尚未运行本次正式发布 scan、准备审核答复或确认 publisher identity。不能把 unsigned check 通过视为已可入库。
- DailyFlow 自己的对话通过宿主模型服务工作。上游 README 明确区分 Shell Agent 的工具执行器；本地应用内对话验收不能证明商店 Shell Agent 已能调用应用工具，也不能证明所有用户环境都兼容。正式提交前需要使用目标发行版做安装与使用验收。
- 当前声明 Windows；其他平台、长期容量和独立 App 通信仍未完成验收。保持这些限制在商店介绍和内置说明中可见。

## 本轮内置说明验收

0.6.3 新增左下「帮助」和「全部」搜索「使用说明」。七节内容来自 `src/user_guide.json`，构建时嵌入 main.splash 并同步生成 USER_GUIDE.md；运行时无需网络或模型。新增 55_help，当前共15个编译模块。只改说明和导航，不改业务协议/存储。

`build/help-guide-r1/ui-narrow2`（412×892）和 `ui-wide1`（1280×900）均通过真实控件操作：七节正文、滚动到底、搜索入口、返回手工表单、保留对话和表单草稿、业务状态不变。已检查宽窄屏截图。首轮 ui-narrow1 在搜索入口误点同名 TextInput，补上 Button 选择器后通过；失败证据保留。无真实 Provider 请求，不声称本轮重新验证模型功能。

最终 `hub stamp/check --allow-unsigned` 通过；证据见 final-gate.log 和 final-audit.json。个人数据和原生保护文件哈希不变，测试宿主均退出，用户窗口未关闭。正常退出并重开已有 AI 启动器后可读新说明。
