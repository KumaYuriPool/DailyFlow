# Splash 语言限制与坑（实战总结）

**日期**：2026-10-02
**来源**：DailyFlow v0.1 → v0.5 迭代期间的实战经验
**适用**：所有 Splash App 开发者

---

## 0. 核心结论（先看）

Splash 看起来简单，但**有 8 个明确的坑**——这些坑如果不避开，整个 App 静默失败（**不报错，body 不渲染**）。

每条坑都有"症状 + 原因 + 解决"三段说明。

---

## 坑 1：`on_render` 在嵌套 SolidView > Label 内不触发

**症状**：Label 用 `on_render: || set_text(...)` 设置动态文本，**在 widget tree 里 widget 不出现**。

**原因**（实测）：
- `Label{on_render: || set_text(...)}` 直接放在 GestureView/SolidView 内 **有时不触发**
- 单独放在 ScrollYView 内（my-notes 模板用法）**工作**

**解决方案**：
- ❌ 不用 on_render，改用 widget id + `set_text`：
  ```splash
  foo := Label{text: ""}  // 给个 id
  // 在 fn 里：
  ui.foo.set_text("新文本")
  ```
- ✅ 用 `text: variable` 在构造时确定（但变量后续修改不传播）

**优先级**：**别相信 on_render + 嵌套**。

---

## 坑 2：widget 数量超限静默失败

**症状**：app 启动后 widget tree 里大部分 widget 不见，但**无任何 `[E]` 错误**。

**原因**（实测）：
- v0.3 试过 130 widget（每个日历 cell 3 层嵌套），Splash body 评估为 `nothing`
- v0.5 优化到 80 widget（每个 cell 只 1 层）就稳定

**实测阈值**：
| widget 数 | 结果 |
|----------|------|
| ~30 | ✅ 稳定 |
| ~80 | ✅ 稳定（v0.5 dailyflow-calendar） |
| ~130 | ❌ 静默失败 |

**解决方案**：
- 每个 cell 用**最少的嵌套层数**
- 避免 `GestureView > SolidView > Label` 三层（用 `GestureView > Label` 两层）
- 复杂功能拆 bundle 而非塞单 splash

---

## 坑 3：`text: variable` 字段只读取一次

**症状**：创建 Label 时 `text: my_var`，后续修改 `my_var = "new"` **Label 不更新**。

**原因**：Splash widget 属性在构造时求值。

**解决方案**：
```splash
// 错：
Label{text: my_var}
my_var = "new"  // Label 不会变

// 对：
Label{id := Label{text: my_var}}  // 给个 id
my_var = "new"
ui.id.set_text("new")  // 必须用 set_text
```

---

## 坑 4：嵌套 SolidView 宽度被父级 `width: Fill` 吃掉

**症状**：嵌套的 SolidView `width: 320` 实际显示为 ~65px。

**原因**：父级 `View{width: Fill}` 时，SolidView 子节点无法正确计算 fill width。

**解决方案**：
- 避免设置面板这种"居中固定宽"布局
- 改用底部 tab 或全宽设计
- 或者把 inner SolidView 改为 View

---

## 坑 5：`Label{text: array[i].field}` 不解析对象字段

**症状**：`text: expenses[i].amount` 显示空白或 `[Error:WrongValue]`。

**原因**：Splash 的 text 字段可能不支持 `.field` 访问语法。

**解决方案**：
- 用 `my-notes` 模板：`text: array[i]`（数组元素本身）
- 对象数组要先展平为字符串数组：
  ```splash
  let r0 = ""  // 全局字符串变量
  // 然后 r0 = "¥" + expenses[0].amount + " " + expenses[0].note
  Label{text: r0}  // text 字段读 r0
  ```

---

## 坑 6：GestureView 单行语法被错误嵌套

**症状**：把多个 `GestureView{...}}` 写在一行（每个独立），结果后一个被嵌入到前一个内。

**原因**：Splash 解析器对 `GestureView{...}}` 单行结尾的 `}` 闭合判断不严格。

**解决方案**：**每个 GestureView 独立多行**：
```splash
// 错（一行一个）：
GestureView{...}}
GestureView{...}}

// 对（每个独立多行）：
GestureView{
    ...
}
GestureView{
    ...
}
```

---

## 坑 7：`visible: false` 的 widget 不触发 `on_render`

**症状**：`visible: false` 的 SolidView/View 内的 on_render 永远不调用。

**原因**：widget 不可见时不参与渲染。

**解决方案**：
- 默认 visible=true，切换用 `set_visible(true/false)`
- 或者**不要依赖 on_render**，改用 widget id + set_text

---

## 坑 8：`text: "abc"[0]` 字符串索引报错

**症状**：`text: "abc"[0]` 触发 `[Error:WrongValue]`。

**原因**：Splash 不支持字符串下标。

**解决方案**：
- 用预定义数组 `["一", "二", "三"]`
- 用 `split()` 后取元素

---

## 调试流程（标准）

```bash
# 1. octo check
python -X utf8 tools/octo check D:/path/to/bundle

# 2. 启动
python -X utf8 tools/octo run D:/path/to/bundle --port 8143 --hidden --detach
sleep 3

# 3. 检查错误
cat .local-state/card-host.log | grep "\[E\]"

# 4. 看 widget tree（找 widget id 名字）
curl -s 127.0.0.1:8143/snap | python -c "
import json,sys
d=json.loads(sys.stdin.read())
for w in d['s']:
    t = w.get('t','')[:30]
    i = w.get('i','-')
    if w['ty'] in ('SolidView','Label','GestureView','Button','TextInput'):
        print(f'{w[\"ty\"]:12} i={i:8}  r={w[\"r\"]}  t={repr(t)}')
"

# 5. 截图
python -X utf8 tools/octo shot 8143 build/iter.png

# 6. 关掉
curl -s -m 2 127.0.0.1:8143/quit
```

---

## 远程桥路由（与 Splash 无关但相关）

| 路由 | 用途 |
|------|------|
| `GET /snap` | widget tree JSON（id/ty/r/t） |
| `GET /k?t=TEXT` | 输入文字（**不是 `/type`**） |
| `POST /click -d '{x,y}'` | 模拟点击 |
| `GET /quit` | 关 App |

获取坐标脚本：
```python
import json, urllib.request
d = json.loads(urllib.request.urlopen("http://127.0.0.1:8143/snap").read())
for w in d['s']:
    if w['ty'] == 'Button':
        print(w['t'], w['r'])
```

---

## 工具函数（v0.5 已验证）

```splash
// 这些函数模式经过验证可用

fn select_day(d){
    selected_day = d
    refresh()  // 调用 refresh 刷新 UI
}

fn refresh(){
    // 用 ui.<id> 直接更新
    ui.status.set_text("新文本")
    ui.cell1.draw_bg.color: 1 == selected_day ? blue_light : card
}
```

---

## 已知陷阱总结

| 行为 | 工作 | 不工作 |
|------|------|--------|
| 设置文本 | `ui.<id>.set_text(...)` | `text: variable`（只读一次） |
| 改背景色 | `ui.<id>.draw_bg.color: ...` | widget 内 on_render 改 draw_bg |
| 切换 view | `ui.view1.set_visible(false)` | `set_visible` 在 widget 销毁后调用 |
| 点击响应 | `ButtonFlat.on_click` `GestureView.on_tap` | on_click 闭包内访问未命名 widget |
| 嵌套 widget | 2 层稳定 | 3 层 + on_render 不稳定 |

---

## 一句话总结

> Splash 简单但**暗坑多**。每条规则都用过血泪验证。要么避开，要么接受 widget 数量 ≤ 80 的限制。
