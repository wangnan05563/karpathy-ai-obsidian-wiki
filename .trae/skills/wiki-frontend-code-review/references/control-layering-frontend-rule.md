# 控件分层原则（FR-045）

> 复盘来源：工具栏控件数量增长到 6+ 时仍扁平堆叠在 button-bar 内，导致折叠面板与按钮挤占同一行，视觉混乱且交互误触；折叠面板放在 button-bar 内导致布局抖动、面板展开后挤压主操作按钮宽度。修复方式：当工具栏控件数超过阈值（默认 5）时强制分层——主操作按钮留在 button-bar，次要控件与折叠面板移到 button-bar 外、input-area 内的独立分层容器，并用 Vue `<Transition>` 渐入渐出。
> 所有可变参数从 config/review-config.md 的 `control_layering_frontend` 字段读取，禁止在规则文件中硬编码阈值、选择器或动画前缀。

## 规则

### FR-045-1：工具栏控件数超过阈值必须分层

工具栏（button-bar）内可见的主操作控件数量若超过 `control_layering_frontend.threshold`（默认 `5`），必须将次要控件迁移到分层容器中，仅保留高频主操作在 button-bar 内。统计范围包括但不限于：`<button>` / `<el-button>` / `<el-dropdown>` / `<el-tooltip>` 包裹的按钮 / `<el-input>` 内联搜索框 / `<el-switch>` 切换器。

**判定标准**：若 button-bar 直接子级控件数 > `threshold`，即视为违规。修复方式：将低频控件归入折叠面板（FR-045-2），主操作按使用频次排序保留在前 `threshold` 个位置。当 button-bar 同时承担"主操作 + 配置入口"双职责时，配置类控件必须分层。

### FR-045-2：折叠面板 HTML 位置必须在 button-bar 外、input-area 内

折叠面板（含 `el-collapse` / `el-popover` / 自定义 panel）的根 DOM 节点必须挂在 `control_layering_frontend.input_area_selector`（默认 `.input-area`）下、且不在 `control_layering_frontend.button_bar_selector`（默认 `.button-bar`）内。即 DOM 层级须满足：

```
.input-area
  ├── .button-bar          ← 主操作按钮（FR-045-1 阈值内）
  └── .folding-panel       ← 折叠面板（与 button-bar 平级）
```

**判定标准**：若折叠面板根元素是 button-bar 的直接或间接子节点（DOM `contains` 关系成立），即视为违规——折叠面板展开时会撑大 button-bar 高度或挤占按钮宽度。修复方式：将折叠面板移到 button-bar 同级兄弟节点，用绝对定位或 flex 布局独立排布。
### FR-045-3：展开/收起必须有 Vue Transition 动画

折叠面板的展开与收起必须用 Vue 内置 `<Transition>` 组件包裹，`name` 属性必须以 `control_layering_frontend.transition_name_prefix`（默认 `panel-`）为前缀，确保动画样式可被全局 CSS 命中。禁止依赖 CSS `display: none` 硬切换或 `v-if` 无动画直接挂载/卸载。

**判定标准**：折叠面板的 `v-if` / `v-show` 控制块未被 `<Transition>` 包裹，或 `name` 属性缺失 / 不以前缀开头，即视为违规。修复方式：用 `<Transition :name="transitionName">` 包裹面板根节点，并在全局样式中定义 `.panel-enter-active` / `.panel-leave-active` 等过渡类。

### FR-045-4：触发按钮必须有激活状态视觉反馈

控制折叠面板显隐的触发按钮（trigger button）必须在面板展开状态下提供激活态视觉反馈，至少满足以下其一：

- `aria-expanded` 属性同步绑定到面板显隐状态（无障碍 + CSS 属性选择器双用）
- 激活态 class（如 `.is-active` / `.panel-open`）动态绑定
- 激活态样式（背景色加深 / 边框高亮 / 图标旋转）通过 CSS 选择器覆盖

**判定标准**：触发按钮既无 `aria-expanded` 也无激活态 class / 样式，即视为违规——用户无法从视觉上判断面板当前是否展开。修复方式：`:aria-expanded="panelVisible"` + `:class="{ 'is-active': panelVisible }"` 双绑定。

### FR-045-5：面板内控件必须 @mousedown.stop 阻止冒泡

折叠面板内的所有可交互控件（input / button / select / dropdown 等）必须绑定 `@mousedown.stop` 修饰符，阻止 mousedown 事件冒泡到面板根元素或外部 click outside 监听器。否则面板内点击会触发外部 click outside 误判（与 [FR-047](folding-panel-event-frontend-rule.md) 联动），导致面板意外关闭。

**判定标准**：面板内可交互控件未绑定 `@mousedown.stop`（或等价的 `@mousedown="onStopPropagation"`），即视为违规。修复方式：在控件上添加 `@mousedown.stop`，或在面板根元素统一绑定 `@mousedown.stop` 拦截整层冒泡（推荐后者，避免逐控件添加）。

## 适用场景

- Vue 3 + Element Plus 项目中含工具栏（button-bar）+ 折叠面板的复合交互区域。
- 工具栏控件数随业务增长逐步膨胀，需要分层管理的页面（如仪表盘、配置页、富文本编辑器工具栏）。
- SPA 手动路由项目中，单视图内含多个折叠面板（搜索过滤面板 / 高级设置面板 / 历史记录面板）的场景。
- Tauri / Electron 桌面应用前端，工具栏受窗口宽度限制需要分层折叠的场景。

## 不适用场景

- 工具栏控件数 ≤ `threshold`（默认 5）的简单页面（无需分层）。
- React / Next.js 项目（无 `<Transition>` 内置组件，改用 `framer-motion` / `react-transition-group`，参数仍从 config 读取）。
- 纯静态页面（无折叠交互）。
- 移动端底部 Tab Bar（属于导航栏规则，参见 `icon_navigation` 配置段）。
## 检查流程

```
[开始] 扫描 .vue 文件 <template> 段
  │
  ▼
[1] 工具栏控件数统计（FR-045-1）
  │  └─ 定位 button-bar 选择器（从 config 读取 button_bar_selector）
  │       └─ 统计直接子级 <button> / <el-button> / <el-dropdown> / <el-input> / <el-switch> 数量
  │            └─ 数量 > threshold（默认 5）→ 标记违规（建议分层）
  │
  ▼
[2] 折叠面板 DOM 位置核对（FR-045-2）
  │  └─ 定位折叠面板根元素（el-collapse / el-popover / .folding-panel）
  │       └─ 检查 DOM 父级链是否包含 button-bar
  │            └─ 包含 → 标记违规（移到 button-bar 同级）
  │       └─ 检查 DOM 父级链是否包含 input-area
  │            └─ 不包含 → 标记违规（移到 input-area 下）
  │
  ▼
[3] Vue Transition 动画检查（FR-045-3）
  │  └─ 折叠面板的 v-if / v-show 控制块
  │       └─ 未被 <Transition> 包裹 → 标记违规
  │       └─ <Transition> 缺少 name 或 name 不以 transition_name_prefix 开头 → 标记违规
  │
  ▼
[4] 触发按钮激活态反馈（FR-045-4）
  │  └─ 控制面板显隐的触发按钮
  │       └─ 无 aria-expanded 且无 :class 激活态绑定 → 标记违规
  │
  ▼
[5] 面板内控件冒泡阻止（FR-045-5）
  │  └─ 扫描面板根元素及内部可交互控件
  │       └─ 根元素未绑定 @mousedown.stop 且内部控件未逐个绑定 → 标记违规
  │       └─ 与 FR-047 click outside 联动检查
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `control_layering_frontend.enabled` | `true` | 是否启用控件分层审查 |
| `control_layering_frontend.threshold` | `5` | 工具栏控件数分层阈值，超过即必须分层 |
| `control_layering_frontend.frequent_threshold` | `3` | 高频主操作保留数量阈值（用于排序分层） |
| `control_layering_frontend.button_bar_selector` | `.button-bar` | 工具栏容器 CSS 选择器 |
| `control_layering_frontend.input_area_selector` | `.input-area` | 输入区容器 CSS 选择器（折叠面板须挂在此下） |
| `control_layering_frontend.transition_name_prefix` | `panel-` | Vue `<Transition>` name 属性前缀 |
| `control_layering_frontend.panel_root_selectors` | `.folding-panel, .el-collapse, .el-popover` | 折叠面板根元素选择器列表（逗号分隔） |
| `control_layering_frontend.trigger_active_class` | `is-active` | 触发按钮激活态 class 名 |
| `control_layering_frontend.require_aria_expanded` | `true` | 是否强制触发按钮绑定 aria-expanded |

## 检查方式

1. **Grep 扫描 button-bar**：在 `.vue` 文件中检索 `control_layering_frontend.button_bar_selector`（默认 `.button-bar`），定位工具栏容器。
2. **统计控件数**：对 button-bar 容器直接子级节点，统计 `<button` / `<el-button` / `<el-dropdown` / `<el-input` / `<el-switch` 出现次数，与 `threshold` 比对。
3. **DOM 层级核对**：对折叠面板根元素（`panel_root_selectors` 命中），用 AST 或正则解析其父级链，检查是否在 `button_bar_selector` 内、是否在 `input_area_selector` 内。
4. **Transition 包裹检查**：检索 `<Transition` 标签，检查其是否包裹折叠面板的 `v-if` / `v-show` 控制块；`name` 属性是否以 `transition_name_prefix` 开头。
5. **触发按钮激活态**：检索控制 `panelVisible` / `collapseVisible` 等响应式变量的按钮，检查 `:aria-expanded` 与 `:class` 绑定。
6. **冒泡阻止扫描**：检索面板根元素及内部控件的 `@mousedown` 绑定，验证是否带 `.stop` 修饰符。
## 正确示例

```vue
<!-- ✅ 工具栏控件数 = 3（≤ threshold），主操作 + 折叠面板分层布局 -->
<template>
  <div class="input-area">
    <!-- ✅ button-bar 内仅保留主操作按钮（FR-045-1） -->
    <div class="button-bar">
      <el-button @click="onSend">发送</el-button>
      <el-button @click="onClear">清空</el-button>
      <el-button @click="onExport">导出</el-button>
    </div>

    <!-- ✅ 折叠面板在 button-bar 外、input-area 内（FR-045-2） -->
    <!-- ✅ 触发按钮有激活态 class + aria-expanded（FR-045-4） -->
    <el-button
      :class="{ 'is-active': panelVisible }"
      :aria-expanded="panelVisible"
      @click="panelVisible = !panelVisible"
    >
      高级设置
    </el-button>

    <!-- ✅ Vue Transition 包裹，name 以前缀开头（FR-045-3） -->
    <Transition name="panel-slide">
      <div
        v-if="panelVisible"
        class="folding-panel"
        @mousedown.stop
      >
        <el-input v-model="config.keyword" placeholder="关键词" />
        <el-select v-model="config.scope">
          <el-option label="全部" value="all" />
        </el-select>
      </div>
    </Transition>
  </div>
</template>
```

```css
/* ✅ Transition 过渡类名以前缀开头（从 config 读取 transition_name_prefix） */
.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.panel-slide-enter-from,
.panel-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
```

## 错误示例

```vue
<!-- ❌ 工具栏控件数 = 7（> threshold=5），未分层（FR-045-1 违规） -->
<template>
  <div class="button-bar">
    <el-button>发送</el-button>
    <el-button>清空</el-button>
    <el-button>导出</el-button>
    <el-button>高级设置</el-button>
    <el-button>历史记录</el-button>
    <el-button>主题切换</el-button>
    <el-button>关于</el-button>
    <!-- ❌ 7 个控件全堆在 button-bar 内，视觉混乱 -->
  </div>
</template>
```

```vue
<!-- ❌ 折叠面板放在 button-bar 内（FR-045-2 违规） -->
<template>
  <div class="button-bar">
    <el-button>发送</el-button>
    <!-- ❌ 折叠面板是 button-bar 的子节点，展开会撑大 button-bar -->
    <el-collapse v-model="activeNames">
      <el-collapse-item title="高级设置" name="advanced">
        <el-input v-model="config.keyword" />
      </el-collapse-item>
    </el-collapse>
  </div>
</template>
```

```vue
<!-- ❌ 折叠面板无 Transition 动画（FR-045-3 违规） + 触发按钮无激活态（FR-045-4 违规） + 面板内控件无 @mousedown.stop（FR-045-5 违规） -->
<template>
  <div class="input-area">
    <el-button @click="panelVisible = !panelVisible">高级设置</el-button>
    <!-- ❌ v-if 直接挂载，无 <Transition> 包裹 -->
    <div v-if="panelVisible" class="folding-panel">
      <!-- ❌ 无 @mousedown.stop，点击会冒泡触发外部 click outside -->
      <el-input v-model="config.keyword" />
    </div>
  </div>
</template>
```

## 与其他规则的关系

- **FR-047（折叠面板事件冲突防护）**：FR-045-5 与 FR-047 形成"DOM 结构 + 事件冒泡"双向联动。FR-045-5 要求面板根元素 `@mousedown.stop`；FR-047 要求外部 click outside 监听器排除面板与 teleport 组件。两者同时命中触发 Urgent。
- **FR-046（第三方库错误防护）**：当折叠面板内嵌入 Mermaid / KaTeX 等第三方库渲染区域时，FR-046 的"渲染前清空容器"规则与 FR-045-2 的"面板位置"规则共同约束 DOM 结构。
- **IN-1 / IN-3（图标与导航栏）**：工具栏控件数与导航栏菜单项数统计独立，但分层逻辑一致——超过阈值即分层折叠。
- **DA-8（破坏性按钮防护）**：分层后保留在 button-bar 内的主操作若属于破坏性按钮（启动/停止/删除），仍须满足 `required_guards` 至少其一。

## 适配新项目

- **React / Next.js**：`<Transition>` 改为 `framer-motion` 的 `<AnimatePresence>` 或 `react-transition-group` 的 `<CSSTransition>`；`name` 属性改为 `classNames` 参数；其余规则不变。
- **Vue 2**：`<Transition>` 仍可用；`aria-expanded` 与 `:class` 绑定方式不变；`@mousedown.stop` 修饰符兼容。
- **纯 JavaScript（无框架）**：用 CSS `transition` + class 切换实现动画；`aria-expanded` 属性手动 `setAttribute`；事件冒泡用 `event.stopPropagation()`。
- **移动端**：`threshold` 可降至 `3`（屏幕宽度受限）；折叠面板改为底部抽屉（Bottom Sheet）模式，DOM 层级约束不变。
- **桌面端 Tauri / Electron**：`threshold` 可升至 `7`（窗口宽度充裕）；折叠面板可用 Popover 浮层，仍须满足 `input_area_selector` 内的 DOM 约束。