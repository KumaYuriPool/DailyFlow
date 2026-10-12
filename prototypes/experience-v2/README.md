# DailyFlow 经历界面 · 可交互原型

直接用现代浏览器打开 `index.html`。无需安装、账号、网络或构建；请保持 assets 目录与 HTML 的相对位置。

## 可操作内容

- 左侧搜索、切换、新建经历；三组内置故事。
- 点击来源记录，在右侧查看原文、时间和关联理由；关闭详情。
- 确认关联、重新判断、排除、即时撤销、管理已排除记录并恢复。
- 设置中的来源开关；关闭来源会隐藏对应样本。
- “更新来源”模拟首笔费用减少20元；重复更新不重复修改。
- 底部提问演示费用汇总和经历回顾；支持取消；费用从当前可见样本计算。
- 操作保存于当前浏览器localStorage；刷新可保留；设置中可重置演示。
- 小屏折叠目录与详情。

## 真实性边界

这是独立 HTML 交互原型，不是 DailyFlow 生产应用或 OctoSense 插件。没有模型请求、真实工具调用、真实数据接入、账号、云端、上传或文件解析。页面上的 Agent 过程明确是定时的演示流程；问题匹配是本地关键词规则。文件导入入口仅载入内置样本。个人空间不代表账号已实现。

原型状态键为 `dailyflow-experience-prototype-v2`，与真实应用数据隔离。file:// 本地存储能力依浏览器而异；受限时会提示仅在本次页面保留。

## 配图

`assets/climbing.png` 由内置 image_gen 生成，为模拟来源配图。生成提示：

> Generate a photorealistic editorial lifestyle photograph for a warm minimalist personal journal app. Landscape 3:2 composition. Indoor bouldering gym with a warm off-white textured climbing wall, sparse sage green, terracotta, ochre and grey climbing holds, one young adult woman seen from behind in plain dark sage sportswear climbing a beginner route at low height, thick safety mat below, soft natural afternoon light. Calm candid authentic feeling, no posed model, no commercial logos, no text, no UI, no border. High photographic quality, subtle film grain, natural skin, realistic climbing holds and body proportions. This is illustrative simulated app data.

## 验证

`verify.cjs` 为本工作区使用 Playwright + Edge 的独立交互检查，依赖路径为本机运行时路径；用户浏览原型无需运行它。结果见 verification.json，截图见 preview-*.png。
