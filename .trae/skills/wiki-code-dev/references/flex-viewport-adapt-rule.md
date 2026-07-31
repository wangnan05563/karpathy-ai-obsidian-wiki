# flex 容器高度自适应规则（CODING-057）

> 复盘来源：顶部导航栏与页脚删除后，Browse/Graph/Users 页面原 `calc(100vh - 240px)` 高度计算失效，导致底部留白或视野未最大化。改造为 `flex: 1 + min-height: 0` 自适应后，内容区自动填满剩余空间。
> 所有可变参数从 `config/coding-standards-config.md` 的 `flex_viewport_adapt` 字段读取，禁止在规则文件中硬编码像素值或 CSS 属性。

## 触发场景

- 页面布局结构调整（删除顶部导航、页脚、侧栏等固定元素）
- 视口高度计算依赖的固定元素被移除或高度变化
- 卡片式布局需要填满剩余空间
- 侧栏布局改造后内容区需自适应

## 规则

### FVA-1：禁止使用 calc(100vh - Xpx) 硬编码高度

当容器高度需要填满视口剩余空间时，**禁止使用** `calc(100vh - Xpx)` 硬编码计算，必须用 flex 布局自适应：

```css
/* 禁止 */
.browse-card {
  height: calc(100vh - 240px);
}

/* 必须 */
.browse-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.browse-card {
  flex: 1;
  min-height: 0;
}
```

### FVA-2：父容器必须建立 flex 上下文

使用 `flex: 1` 的子元素，其父容器必须同时满足：
- `display: flex`（建立 flex 上下文）
- `flex-direction: column`（垂直排列时）
- `height: 100%` 或明确的高度值（否则 flex 子项无参考高度）

### FVA-3：flex 子项必须 min-height: 0

`flex: 1` 的子项必须加 `min-height: 0`，否则内容超出时不会收缩，导致溢出父容器而非触发内部滚动。

### FVA-4：布局结构变更后必须审计所有 calc(100vh) 引用

当删除/移除页面固定元素（导航栏、页脚、标题栏）后，必须用 Grep 搜索所有 `calc(100vh` 引用，评估是否需要改为 flex 自适应：

```bash
grep -rn "calc(100vh" frontend/src/views/
```

## 设计流程

```
布局结构调整（删除固定元素）
   ↓
1. Grep 搜索所有 calc(100vh - Xpx) 引用
   ↓
2. 评估每个引用的 Xpx 是否包含已删除元素的高度
   ↓
   是 → 改为 flex: 1 + min-height: 0
   否 → 保留（可能是独立模态框等）
   ↓
3. 父容器建立 flex 上下文（display:flex + height:100%）
   ↓
4. vue-tsc 验证无类型错误
   ↓
5. 浏览器验证：窗口缩放时内容区自适应
   ↓
6. E2E 响应式测试通过
```

## 适用场景

- 侧栏布局改造（顶部导航→左侧侧栏，内容区高度变化）
- 删除页脚 / 顶部栏后视口重算
- 卡片式布局需要填满剩余空间
- 任何 `calc(100vh - Xpx)` 中 X 值依赖的元素被移除的场景
- 多视图共享同一 flex 上下文（如 Browse/Graph/Users 共享 .content 区域）

## 不适用场景

- 固定高度模态框 / 弹窗（需明确像素高度）
- 绝对定位元素（position: absolute/fixed）
- 打印布局（@media print 有独立的高度计算）
- Canvas / SVG 固定宽高比容器
- 移动端 App（有独立的视口设计规范）

## 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `flex_viewport_adapt.forbidden_height_pattern` | `calc\(100vh` | 禁止的高度计算模式正则 |
| `flex_viewport_adapt.required_parent_props` | `["display: flex", "height: 100%"]` | 父容器必须建立的 CSS 属性 |
| `flex_viewport_adapt.required_child_props` | `["flex: 1", "min-height: 0"]` | 子项必须的 CSS 属性 |
| `flex_viewport_adapt.audit_on_layout_change` | `true` | 布局变更时是否自动审计 calc 引用 |
| `flex_viewport_adapt.view_file_patterns` | `["**/views/*.vue"]` | 需审计的视图文件 glob |
