# 0.1.1候选包扫描答复

2026-10-10，本地自审草稿，不是App Hub审核结论。使用官方Hub固定源码655114c编译的CLI，执行 `hub scan bundle --packet build/semifinal-202610/release-preflight/candidate-scan.json`，生成8个问题；未指定外部reviewer、未发布。

## 1. 名称、描述与实现

当前提供同包账目、事项/计划、经期来源及时间线查询。实现入口为src/10_expense、15_period、20_calendar、08_time_protocol、32_recall和38_modules，构建对应见[模块映射](MODULE_MAP.md)。listing明确独立App、后台提醒、云同步未提供，对话尚不能直接发起完整时间线查找。保存主题、日记、新闻不写入已实现清单。

## 2. 平台与类别

listing仅声明Windows、productivity。已用官方RC2 Windows发行二进制在隔离本地catalog加载，尚未从GitHub公开发布物安装；首次Card初始化的前提见[复现记录](RC2_CARD_STARTUP_REPRO.md)。其他平台未声明通过。

## 3. 权限和主机

manifest仅声明storage和model，没有应用network.hosts。storage用于双槽状态、备份和收据；model用于应用内结构化理解。模型提供商由宿主配置，不能把空应用网络主机列表说成模型请求离线。官方应用Agent的模型会话另由宿主管理，隐私说明已分别解释。没有文件夹通读权限，agent_workspace为none。

## 4. 界面是否欺骗

DailyFlow自己的界面为记录、日历、账本、查找、帮助与数据操作，不模仿付款、登录或系统授权界面。真正的Agent同意/工具审批由官方宿主显示，不能用应用绘制的按钮冒充。当前截图仍需在最终发布版人工核对。

## 5. 非Agent文件中的指令文本

src/50_agent含发送给应用内模型的任务约束与结构化输出提示，这是实现的一部分，不能回答为“所有指令均只在AGENT.md”。src/user_guide.json为用户说明；业务来源内容不授予工具权限，返回数据应作为数据处理。最终公开材料不包含测试core、Provider或整个build目录。

## 6. 攻击性内容

当前文案及合成样例未发现攻击私人个体的内容。此为本轮源码范围的作者检查，不代表第三方全面内容审查。

## 7. Agent边界与工具风险

bundle/AGENT.md要求使用已声明应用工具、修改前查ID/修订、结果未知先读回、不重放删除、不根据同日或同主体猜关联；不要求其他助手忽略规则或获取未声明权限。新入口读取宿主request.args，保持宿主审批。

save_record/apply支持删除，因此标destructive且confirm:host；当前没有confirm:app工具。所有工具结果标private_data。recall/timeline_query为shareable:false；其他六个工具仍shareable:true，可能返回私人信息，必须在宿主具体授权下使用，不能视为公开数据。第三方跨App路径尚未验收，不因声明shareable而声称可用或越过授权。

## 8. 建议路线

**human-review，待补证据。** 新Hub静态检查通过，旧收据兼容修复及业务/注入验证通过，但官方Agent批准/拒绝、真实工具结果、系统委派、最终GitHub封装包安装与截图验收尚未完成。RC2启动前提已记录，需要评审知悉。取得证据后更新此草稿，不能将生成扫描问题或作者答复说成官方审核通过。

当前版本进度见[执行进度](SEMIFINAL_PROGRESS.md)，最终提交字段见[提交草稿](SEMIFINAL_SUBMISSION_DRAFT.md)。
