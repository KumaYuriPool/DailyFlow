# DailyFlow v0.1 → v0.5 验证迭代日志

**日期**：2026-10-02
**目的**：记录每次迭代的真实结果（截图 + widget tree + 错误日志），方便其他 agent 理解我们走了哪些弯路

---

## 0. 验证方法（每次迭代都做这 5 件事）

```bash
# 1. check（确认 bundle 通过门控）
python -X utf8 tools/octo check D:/path/to/bundle

# 2. 启动
python -X utf8 tools/octo run D:/path/to/bundle --port 8143 --hidden --detach
sleep 3

# 3. 截图
python -X utf8 tools/octo shot 8143 build/iter.png

# 4. 检查 [E] 错误
cat .local-state/card-host.log | grep "\[E\]"

# 5. 查看 widget tree（实际渲染了哪些）
curl -s 127.0.0.1:8143/snap | python -c "..."
```

**注意**：截图"看起来对"≠ 功能对。每次必须看 widget tree + 实际点击验证。

---

## v0.1 (2026-10-01)

**目标**：从 my-notes 模板复制，做"能跑通的最简日历"
**结果**：✅ PASSED，但 UI 简陋
**截图**：`my-notes/build/01-empty.png`

### 关键发现
- 模板里的 `GestureView > SolidView > Label` 三层嵌套
- on_click 真实工作
- set_text 在 on_click 内真实工作
- 但当时误以为 `[E]=0` 就是成功（实际只代表解析器通过）

---

## v0.2 (2026-10-01)

**目标**：加记账 CRUD + 状态栏 + 月份导航
**结果**：✅ 全部功能闭环
**截图**：`my-notes/build/v9-03-del1.png`

### 验证清单
| 功能 | 结果 | 证据 |
|------|------|------|
| 添加记账 | ✅ | 状态栏更新 |
| 删除记账 | ✅ | expenses.json 实际减少 |
| 月份切换 | ✅ | 状态栏 ¥32→¥15→¥0 |
| 列表显示 | ⚠️ 部分 | row2/row3 显示残留（旧 bug） |

### 已知问题（诚实记录）
- 月份标题中间空白（on_render 失效）
- 选中态视觉对比度弱
- 删除后 row2/row3 显示残留

---

## v0.3 (2026-10-01) ← **失败**

**目标**：iOS 极简风改进 + 增强日历交互
**结果**：❌ 130 widget 触发静默 body 不渲染
**截图**：`DailyFlow/build/v0.3-cal2.png`（只剩顶部 + 星期表头）

### 失败原因
- 每个日历 cell 用了 3 层嵌套（GestureView > SolidView > Label）
- 35 个 cell × 3 层 + 其他 widget = 130 个 widget
- Splash body 评估为 nothing（无 `[E]` 错误）

### 教训
- `[E]=0` ≠ 成功——可能是 Splash 静默丢弃整个 body
- widget 数量是硬性限制（实测 ~130 爆炸）

---

## v0.4 stable (2026-10-01)

**目标**：退回最简日历，能跑通
**结果**：✅ 78 widget，完整月历显示
**截图**：`DailyFlow/build/v0.4-stable.png`

### 关键修复
- 每个 cell 只 1 层 GestureView 包 Label（不是 3 层）
- 31 cell + 表头 + 标题 + 状态栏 = ~78 widget
- 选中态用 `==` 三元运算符在 SolidView draw_bg 上做
- 没有用 on_render（避免坑 1）

### 局限
- 月份标题中间空白（on_render 在这个上下文失效）
- 状态栏硬编码"选中 2026-10-15"
- 选中态视觉上不明显

---

## v0.5 (2026-10-01)

**目标**：状态栏动态更新 + 选中态文字动态化
**结果**：✅ 31 个 cXX widget 全部构造成功
**截图**：`DailyFlow/apps/dailyflow-calendar/build/03c-launch.png`

### 关键修复
- 给 31 个 cell 命名 c1..c31
- `select_day(d)` 调用 `refresh()`
- `refresh()` 用 `ui.<id>.set_text` + `ui.<id>.draw_bg.color: ...` 直接更新
- 状态栏 widget id `status` 用 `set_text` 实时更新

### 验证结果
| 验证项 | 结果 |
|--------|------|
| octo check | ✅ PASSED |
| 启动 | ✅ 0 错误（需 start_timeout 延迟 refresh） |
| 日历渲染 | ✅ 1-31 全部显示 |
| 点击切换 | ✅ 状态栏更新到"选中 2026-10-18" |
| 选中态 | ✅ 验证函数正确（视觉上对比度待优化） |

---

## v0.6 (2026-10-01，未完成)

**目标**：加 prev/next_month，标题动态更新
**结果**：⏸ 部分完成

### 当前代码
- 加了 `current_month` 全局变量
- 加了 `prev_month()` / `next_month()` 函数
- 加了 `refresh()` 调用
- 标题改用 `on_render` 显示 `current_month`（**仍不可靠**）

### 已知问题
- 标题文字"2026 年 10 月"中间空白
- 月份切换后日历格子数字**不变**（hardcoded "1".."31"）
- 这是 prototype 简化

---

## v0.7 → v0.9（计划）

| 版本 | 目标 | 状态 |
|------|------|------|
| v0.7 | 当前月完整动态 + 31 天硬编码改成根据 first_weekday 计算 | 待办 |
| v0.8 | 4 bundle 拆分为单一 bundle 5 splash（但 Splash 不支持 include → 改为 1 splash 多 view） | 待办 |
| v0.9 | 集成测试 + 真实数据持久化 | 待办 |

---

## 关键截图清单

| 文件 | 内容 |
|------|------|
| `DailyFlow/build/v0.4-stable.png` | 完整月历 1-31 显示 |
| `DailyFlow/build/v0.3-cal2.png` | **失败案例**：只剩顶部 |
| `DailyFlow/apps/dailyflow-calendar/build/03c-launch.png` | v0.5 完整日历 + 状态栏 |
| `DailyFlow/apps/dailyflow-calendar/build/03d-click18.png` | 点击 18 后状态栏更新 |
| `my-notes/build/v9-03-del1.png` | v0.2 记账完整闭环 |

---

## 关键代码模式（v0.5 验证）

```splash
// 给每个 widget 命名以便后续修改
c1 := SolidView{width: Fill height: Fill draw_bg.color: card border_radius: 8.0
    GestureView{width: Fill height: Fill on_tap: |x, y| select_day(1)
        Label{width: Fill height: Fill text: "1" draw_text.color: ink draw_text.text_style.font_size: 18
            align: Align{x: 0.5, y: 0.5}}}

// 全局变量跟踪选中
let selected_day = 15

// 点击响应
fn select_day(d){
    selected_day = d
    refresh()
}

// 显式刷新（不用 on_render）
fn refresh(){
    let dd = "" + selected_day
    if selected_day < 10 { dd = "0" + dd }
    ui.status.set_text("选中 2026-10-" + dd)
    ui.c1.draw_bg.color: 1 == selected_day ? blue_light : card
    ui.c2.draw_bg.color: 2 == selected_day ? blue_light : card
    // ... 重复 31 次
}

// boot 必须延后以等 widget 构造
fn boot(){ refresh() }
start_timeout(0.1, || boot())
```

---

## 错误恢复经验

### v0.1-v0.2 的错误
- 把 "0 错误" 当成功标准 → 用户反馈后才改正

### v0.3 的错误
- widget 数量爆炸 → 静默失败 → 没意识到
- 没意识到"嵌套 widget 数量有上限"

### v0.4-v0.5 的修正
- 每个 widget 单独多行语法
- 1 层嵌套而非 3 层
- 用 widget id + set_text 替代 on_render
- 强制验证"点击 → 实际修改"

---

## 给接手 Agent 的建议

1. **永远跑通后再加新功能**——v0.3 的教训
2. **截图 + widget tree + 实际点击三重验证**
3. **每个 widget 独立多行**（splash 解析器偏好）
4. **widget 数量 ≤ 80**（实测安全阈值）
5. **Splash 内不支持的事情不要尝试**（shader、自定义 widget、include）
