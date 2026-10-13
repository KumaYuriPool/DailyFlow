# NF-18 原型对照视觉与交互验收（集成候选终审）

检查时间：2026-10-13 21:50—22:10（北京时间）。集成人：I。
验收对象：`build/overnight-20261013/integration-r1/candidate-r2`（三线合并 + P1 修复后候选，main.splash SHA256 `46a7c6d38d3e1da0f03b31032d153df83774eb17653cff74655670adda09f7d3`）。

## 验收方法与证据分层（如实说明）

1. **U 线逐张视觉评审（像素级）**：U 在其交付中对 18 张原生截图（1280x900 与 412x892 各半）逐张打开查看，覆盖统一时间线、滚动、详情、设置、空间、原文、变化、已排除、旧工作台，结论见 `.parallel/night-20261013/U/delivery/U/visual-review.md`。该评审针对 U 合流前候选（main SHA `faf22c19…`）；本轮集成候选的 UI 模块即 U 交付模块经三方合并而来。
2. **集成候选全套控件树断言（终审重跑）**：在最新整套运行时（runtime-final-r1：Shell `0476df1f…`、kernel `4e72bc7d…`、card-host `0e92683e…`、hub `6eaeb666…`）上重跑：
   - `ui-wide-final-r4`：41/41 通过（统一元信息行、诚实来源条、金额行、内联关系、关系决定持久化/清除、设置弹层滚动保持、详情身份/关联理由/跨源、原文遮罩、排除/恢复、空间弹层无点穿、旧工作台入口往返、范围开关隐藏/恢复、第二故事同渲染器、重启存储形状）
   - `ledger-ui-narrow-final-r1`：通过（412 窄屏独立账本表单/更正详情/删除）
   - `settings-probe-r1`、`scope-final-r1`：通过
   - `workbench-final-r1`：8/8 通过（旧工作台真实点击：记 220→改 200 同 ID、重启保持、双击删除、无独立账本数据迁移、返回新 UI）
3. **物理捕获结构检查（I 执行）**：12 张关键截图全为有效渲染帧（无全黑/全白帧；尺寸为物理分辨率捕获：1920x1350=1280x900@1.5x DPI、618x1338=412x892@1.5x、live 2100x1350=1400x900 窗口@1.5x）。窄屏高比例均匀行为表单留白，非渲染破损。
4. **live 端到端截图**：`live-cold-final-r1/screen-405.png`（真实系统 Assistant 全链路后的经历详情：攀岩/2026-10-01/1 来源/1 记录/CNY 待核对 200.00/来源状态行），已通过 Read 呈现在集成会话中供用户查看。

**限制（如实）**：I 的会话环境中 Read 图片仅返回 CDN URL、外部视觉模型无法访问本机 URL，I 本轮无法亲自做像素级查看；像素级逐张查看依据为 U 线评审（同 UI 代码血缘、合并后断言全绿），最终人工像素复核建议由用户对本文件所列截图执行一次确认。

## 逐项对照结论（原型 experience-v2 ↔ 集成候选）

| 原型目标 | 终审结论 | 依据 |
| --- | --- | --- |
| 我的空间弹层 | 符合 | U 逐张查看 + ui-wide `space-overlay`、`space-overlay-no-point-through` |
| 独立旧工作台入口 | 符合 | workbench-final-r1 真实点击 8/8；无数据迁移 |
| 设置/连接与授权弹层 | 符合（诚实标注） | settings-probe 全文核对：导入样本明确"无需宿主授权"，不冒充已授权；`settings-no-fake-grant` |
| 顶部概括与统一时间流 | 符合 | `unified-meta-line`、`top-summary-claim`、`honest-source-strip`、滚动定位 |
| 有依据的事件分组 | 符合（保守降级为日期组+候选关联） | `inline-relation-sequence/same-experience/supports` + 关联理由可读 |
| 详情与就地操作 | 符合 | `detail-identity/relation-reason/jump-other-end/cross-source-detail` |
| 排除/恢复/移除视图 | 符合 | `exclude-in-detail`、`removed-view-shows-twin`、`restored` |
| 遮罩与滚动保持 | 符合 | `original-overlay`、`original-close-keeps-detail`、`scroll-preserved-after-overlay` |
| Esc 关闭 | 已知限制（披露非缺陷遮蔽） | `escape-disclosed`：Esc 不支持关闭，关闭按钮与遮罩点击可用 |
| 原型装饰（照片/连线/动画） | 有意不做 | P2 赛后；来源/模拟标识清晰可见 |
| 窄屏 412 | 符合 | ledger-ui-narrow 3 张 + U 窄屏 45 项 |
| 来源状态真实接线（NF-12） | 符合 | `settings-ledger-real-adapter`、scope 开关、bridge 真实状态（连接/授权/范围分离显示） |
| 撤权后内容不可见 | 符合 | bridge-final-r5：撤权后 records=0、状态 revoked、正文/金额不可见 |
| 自动打开定位的视觉呈现 | 符合（附 P1 修复说明） | live-cold screen-405 显示经历详情+问题+整理面板；自动打开的持久回执经 P1 修复（`nf_external_recover` 2s/8s 重试）后由 live 重跑验证 |

## 截图索引（供用户最终像素复核）

- 宽屏：`candidate-r2/DailyFlow/build/ui-wide-final-r4/{01-unified,02-detail,03-space,04-settings-import,05-concert,08-restarted}.png`
- 窄屏：`candidate-r2/DailyFlow/build/ledger-ui-narrow-final-r1/{01-form,02-corrected-detail,03-deleted}.png`
- 旧工作台：`candidate-r2/DailyFlow/build/workbench-final-r1/{old-workbench-corrected,old-workbench-restarted,back-to-experiences}.png`
- 真实系统链路：`candidate-r2/DailyFlow/build/live-cold-final-r1/screen-405.png`（及 15s 间隔全序列）
- 撤权/只读审计回执：`bridge-final-r5/`、`bridgeprobe-final-r1/`

## 结论

无阻断视觉缺陷。两个已披露限制：Esc 不关闭弹层（有替代关闭路径）、装饰性原型元素未实现（P2）。无截断性裁切（滚动区裁剪属正常）；来源与模拟标识均可见。P1 修复（自动打开重试）后的 live 重跑证据见 NF-17 记录。
