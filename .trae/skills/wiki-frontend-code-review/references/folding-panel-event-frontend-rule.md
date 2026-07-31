# 折叠面板事件冲突防护（FR-047）

> 复盘来源：自定义 click outside 指令未排除 `teleport-to-body` 的 `el-dropdown-menu` 组件，导致点击下拉菜单选项时折叠面板被误关闭；`el-dropdown` 默认 `hide-on-click=true` 使选项点击后面板与下拉同时关闭，破坏多步操作流程。修复方式：click outside 监听器显式排除面板内控件与 teleport 组件选择器；`el-dropdown` 设置 `:hide-on-click="false"`；`el-dropdown-menu` 与面板根元素绑定 `@click.stop` / `@mousedown.stop` 阻止冒泡。
> 所有可变参数从 config/review-config.md 的 `folding_panel_event_frontend` 字段读取，禁止在规则文件中硬编码选择器列表或事件修饰符。

## 规则

### FR-047-1：click outside 必须排除面板内控件与 teleport 组件

实现折叠面板的 click outside 关闭逻辑时，必须显式排除以下两类元素的点击事件：

1. **面板内控件**：位于面板根元素 DOM 子树内的所有可交互元素（由 `folding_panel_event_frontend.click_outside_exclude_selectors` 列出，默认 `.folding-panel, .folding-panel *`）
2. **teleport-to-body 组件**：通过 Vue `<Teleport to="body">` 挂载到 body 的浮动组件（由 `folding_panel_event_frontend.teleport_selectors` 列出，默认 `.el-dropdown-menu, .el-popover, .el-select-dropdown, .el-picker-panel, .el-cascader-panel`）

**判定标准**：click outside 监听器的 `event.target.closest(...)` 检查未覆盖上述两类选择器，即视为违规——点击下拉菜单 / 弹层 / 日期选择器等 teleport 组件时，事件 target 在 body 而非面板内，click outside 误判面板失去焦点而关闭。修复方式：在 click outside 回调中，对 `event.target` 调用 `closest(click_outside_exclude_selectors + teleport_selectors)`，命中任一即跳过关闭。

### FR-047-2：el-dropdown 必须 :hide-on-click="false"

折叠面板内使用的 `<el-dropdown>` 必须显式设置 `folding_panel_event_frontend.required_dropdown_props`（默认 `hide-on-click: false`）中列出的属性。原因：

- `el-dropdown` 默认 `hide-on-click=true`，点击下拉项后菜单立即关闭
- 若折叠面板与下拉菜单有联动操作（如选择下拉项后需面板保持展开），默认行为会破坏操作流程
- 用户需多次点击展开下拉 → 选项 → 再展开面板，体验割裂

**判定标准**：折叠面板内的 `<el-dropdown>` 未设置 `:hide-on-click="false"`，即视为违规。修复方式：添加 `:hide-on-click="false"` 属性，由业务逻辑控制菜单关闭时机（如 `@command` 回调中手动关闭）。

### FR-047-3：el-dropdown-menu 必须 @click.stop

`<el-dropdown-menu>` 及其内部的 `<el-dropdown-item>` 必须绑定 `folding_panel_event_frontend.required_event_modifiers`（默认 `@click.stop, @mousedown.stop`）中列出的事件修饰符。原因：

- 点击下拉项的 click 事件会冒泡到 body，触发 click outside 误判
- mousedown 事件同样会冒泡，部分 click outside 实现监听 mousedown 而非 click
- 即使设置了 `:hide-on-click="false"`，事件冒泡仍会导致面板关闭

**判定标准**：`<el-dropdown-menu>` 或其内部 `<el-dropdown-item>` 未绑定 `@click.stop`（与 `@mousedown.stop`），即视为违规。修复方式：在 `<el-dropdown-menu>` 根元素绑定 `@click.stop` + `@mousedown.stop`，统一拦截整层冒泡（推荐），或逐个 `<el-dropdown-item>` 绑定。

### FR-047-4：面板根元素必须 @mousedown.stop

折叠面板根元素（`.folding-panel` / `.el-collapse` / 自定义 panel 容器）必须绑定 `@mousedown.stop` 修饰符。原因：

- 面板内任何控件的 mousedown 事件会冒泡到根元素，再冒泡到 document
- 部分 click outside 实现监听 document 的 mousedown 事件（而非 click），mousedown 冒泡会触发误判
- 即使面板内控件已绑定 `@mousedown.stop`（FR-045-5），根元素仍需绑定作为兜底

**判定标准**：面板根元素未绑定 `@mousedown.stop`（或等价的 `@mousedown="onStopPropagation"`），即视为违规。修复方式：在面板根元素添加 `@mousedown.stop`，与 FR-045-5 形成双重防护。

### FR-047-5：teleport-to-body 组件必须显式排除选择器列表

click outside 实现中，必须维护一个显式的 `folding_panel_event_frontend.teleport_selectors` 选择器列表，列出所有通过 `<Teleport to="body">` 挂载到 body 的浮动组件选择器，并在 click outside 回调中对 `event.target` 调用 `closest(teleport_selectors)` 排除。原因：

- teleport 组件的 DOM 不在面板子树内，常规的 `panel.contains(event.target)` 检查返回 false
- 不同组件库的 teleport 选择器不同（Element Plus 用 `.el-dropdown-menu`，Ant Design 用 `.ant-dropdown`，Naive UI 用 `.n-dropdown-menu`）
- 新增 teleport 组件时若未更新排除列表，会引入新的事件冲突

**判定标准**：click outside 实现未维护 `teleport_selectors` 列表，或列表不完整（缺少当前项目实际使用的 teleport 组件选择器），即视为违规。修复方式：在 `folding_panel_event_frontend.teleport_selectors` 中追加缺失的选择器，并在 click outside 回调中统一检查。

## 适用场景

- Vue 3 + Element Plus 项目中使用 `el-dropdown` / `el-popover` / `el-select` / `el-date-picker` 等 teleport-to-body 组件的折叠面板。
- 自定义 click outside 指令或 composable（`useClickOutside`）实现的折叠面板关闭逻辑。
- 含多级浮层的复合交互（折叠面板内嵌下拉菜单 / 弹层 / 选择器）。
- Tauri / Electron 桌面应用前端，窗口内 click outside 逻辑与原生窗口事件冲突的场景。

## 不适用场景

- 纯 CSS `:hover` 实现的折叠面板（无 JS 事件监听）。
- React / Next.js 项目（无 `el-dropdown`，改用 Ant Design / MUI 的对应组件，参数仍从 config 读取）。
- 静态页面（无折叠面板与 teleport 组件）。
- 模态对话框（`el-dialog`）内的折叠面板——模态遮罩已隔离外部点击，无需 click outside。
## 检查流程

```
[开始] 扫描 .vue 文件中的折叠面板 + click outside + teleport 组件
  │
  ▼
[1] click outside 排除检查（FR-047-1）
  │  └─ 定位 click outside 实现（自定义指令 / useClickOutside / @click.outside）
  │       └─ 检查回调是否对 event.target 调用 closest(click_outside_exclude_selectors + teleport_selectors)
  │            └─ 未排除 → 标记违规
  │
  ▼
[2] el-dropdown 属性检查（FR-047-2）
  │  └─ 定位折叠面板内的 <el-dropdown>
  │       └─ 检查是否有 :hide-on-click="false"（required_dropdown_props）
  │            └─ 未设置 → 标记违规
  │
  ▼
[3] el-dropdown-menu 事件修饰符（FR-047-3）
  │  └─ 定位 <el-dropdown-menu> 及 <el-dropdown-item>
  │       └─ 检查是否绑定 @click.stop + @mousedown.stop（required_event_modifiers）
  │            └─ 未绑定 → 标记违规
  │
  ▼
[4] 面板根元素 mousedown.stop（FR-047-4）
  │  └─ 定位折叠面板根元素（.folding-panel / .el-collapse）
  │       └─ 检查是否绑定 @mousedown.stop
  │            └─ 未绑定 → 标记违规（与 FR-045-5 联动）
  │
  ▼
[5] teleport 选择器列表完整性（FR-047-5）
  │  └─ 扫描项目中实际使用的 teleport-to-body 组件
  │       └─ 对照 config 的 teleport_selectors 列表
  │            └─ 列表不完整 → 标记违规（建议追加缺失选择器）
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `folding_panel_event_frontend.enabled` | `true` | 是否启用折叠面板事件冲突审查 |
| `folding_panel_event_frontend.click_outside_exclude_selectors` | `.folding-panel, .folding-panel *` | click outside 排除的面板内控件选择器（逗号分隔） |
| `folding_panel_event_frontend.teleport_selectors` | `.el-dropdown-menu, .el-popover, .el-select-dropdown, .el-picker-panel, .el-cascader-panel` | teleport-to-body 组件选择器列表（逗号分隔） |
| `folding_panel_event_frontend.required_dropdown_props` | `hide-on-click: false` | 折叠面板内 el-dropdown 必须设置的属性（`属性: 值` 格式，逗号分隔） |
| `folding_panel_event_frontend.required_event_modifiers` | `@click.stop, @mousedown.stop` | 面板与下拉菜单必须绑定的事件修饰符（逗号分隔） |
| `folding_panel_event_frontend.panel_root_selectors` | `.folding-panel, .el-collapse, .el-popover` | 折叠面板根元素选择器列表（逗号分隔，与 FR-045 共用） |
| `folding_panel_event_frontend.click_outside_patterns` | `v-click-outside, useClickOutside, @click.outside, onClickOutside` | click outside 实现识别关键字（逗号分隔） |
| `folding_panel_event_frontend.teleport_to_body_patterns` | `<Teleport to="body">, teleport-to-body, ElTooltip.teleport` | teleport-to-body 组件识别关键字（逗号分隔） |

## 检查方式

1. **Grep 扫描 click outside 实现**：在 `.vue` / `.ts` 文件中检索 `click_outside_patterns` 中的关键字，定位 click outside 监听器。
2. **排除选择器核对**：对 click outside 回调函数，检查 `event.target.closest(...)` 调用是否包含 `click_outside_exclude_selectors` 与 `teleport_selectors` 中的所有选择器。
3. **el-dropdown 属性扫描**：检索折叠面板内的 `<el-dropdown`，检查是否设置 `:hide-on-click="false"`（或 `required_dropdown_props` 中列出的属性）。
4. **事件修饰符检查**：检索 `<el-dropdown-menu` 与 `<el-dropdown-item`，检查是否绑定 `required_event_modifiers` 中的事件修饰符。
5. **面板根元素 mousedown.stop**：检索 `panel_root_selectors` 命中的元素，检查是否绑定 `@mousedown.stop`。
6. **teleport 选择器完整性**：扫描项目中实际使用的 teleport 组件（`<Teleport to="body">` / `el-popover` / `el-select` 等），对照 `teleport_selectors` 列表验证完整性。
7. **跨规则联动**：FR-047-4 与 FR-045-5 同时命中时（面板根元素未绑定 `@mousedown.stop`），升为 Urgent。
## 正确示例

```vue
<!-- ✅ 折叠面板 + el-dropdown 完整事件冲突防护 -->
<template>
  <div class="input-area">
    <el-button
      :class="{ 'is-active': panelVisible }"
      :aria-expanded="panelVisible"
      @click="panelVisible = !panelVisible"
    >
      高级设置
    </el-button>

    <Transition name="panel-slide">
      <!-- ✅ 面板根元素 @mousedown.stop（FR-047-4，与 FR-045-5 联动） -->
      <div
        v-if="panelVisible"
        ref="panelRef"
        class="folding-panel"
        @mousedown.stop
      >
        <label>作用范围</label>
        <!-- ✅ el-dropdown :hide-on-click="false"（FR-047-2） -->
        <el-dropdown
          :hide-on-click="false"
          trigger="click"
          @command="onScopeChange"
        >
          <span class="scope-trigger">{{ currentScope }}</span>
          <template #dropdown>
            <!-- ✅ el-dropdown-menu @click.stop @mousedown.stop（FR-047-3） -->
            <el-dropdown-menu @click.stop @mousedown.stop>
              <el-dropdown-item command="all">全部</el-dropdown-item>
              <el-dropdown-item command="recent">最近</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const panelVisible = ref(false)
const panelRef = ref<HTMLElement>()

// ✅ click outside 排除面板内控件 + teleport 组件（FR-047-1 / FR-047-5）
function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!panelRef.value) return
  // ✅ 排除面板内控件（click_outside_exclude_selectors，从 config 读取）
  if (panelRef.value.contains(target)) return
  // ✅ 排除 teleport-to-body 组件（teleport_selectors，从 config 读取）
  const teleportSelectors = [
    '.el-dropdown-menu', '.el-popover', '.el-select-dropdown',
    '.el-picker-panel', '.el-cascader-panel'
  ]
  if (teleportSelectors.some(s => target.closest(s))) return
  panelVisible.value = false
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // ✅ 监听 mousedown 而非仅 click，防止 mousedown 冒泡触发误判
  document.addEventListener('mousedown', handleClickOutside)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('mousedown', handleClickOutside)
})

function onScopeChange(cmd: string) {
  // 业务逻辑控制菜单关闭时机
}
</script>
```

## 错误示例

```vue
<!-- ❌ click outside 未排除 teleport 组件（FR-047-1 / FR-047-5 违规） -->
<template>
  <div class="folding-panel" ref="panelRef">
    <el-dropdown trigger="click">
      <span>作用范围</span>
      <template #dropdown>
        <!-- ❌ el-dropdown-menu 无 @click.stop（FR-047-3 违规） -->
        <el-dropdown-menu>
          <el-dropdown-item command="all">全部</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
// ❌ click outside 仅检查 panel.contains(target)，未排除 teleport 组件
// 点击下拉菜单时，target 在 body 的 .el-dropdown-menu，contains 返回 false
// → 面板被误关闭
function handleClickOutside(e) {
  if (panelRef.value && !panelRef.value.contains(e.target)) {
    panelVisible.value = false  // ❌ 误关闭
  }
}
</script>
```

```vue
<!-- ❌ el-dropdown 未设 :hide-on-click="false"（FR-047-2 违规） + 面板根元素无 @mousedown.stop（FR-047-4 违规） -->
<template>
  <!-- ❌ 面板根元素无 @mousedown.stop -->
  <div class="folding-panel" ref="panelRef">
    <!-- ❌ el-dropdown 默认 hide-on-click=true，点击选项后菜单关闭 -->
    <el-dropdown trigger="click" @command="onScopeChange">
      <span>作用范围</span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="all">全部</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>
```

## 与其他规则的关系

- **FR-045（控件分层原则）**：FR-045-5 要求面板内控件 `@mousedown.stop`，FR-047-4 要求面板根元素 `@mousedown.stop`，两者形成"控件层 + 根元素层"双重冒泡拦截。同时命中即升为 Urgent。
- **FR-046（第三方库错误防护）**：第三方库输出的 SVG/Canvas 节点可能捕获鼠标事件，FR-047-1 的 `click_outside_exclude_selectors` 须包含库输出容器选择器（如 `.mermaid-output`）。
- **Element Plus 规则（E1-E6）**：FR-047-2 的 `:hide-on-click="false"` 是 Element Plus `el-dropdown` 的专属属性，与 E 系列规则共同约束 Element Plus 组件用法。
- **AR-3（定时器清理）**：FR-047 的 `addEventListener` 必须在 `onBeforeUnmount` 中 `removeEventListener`，与 AR-3 的定时器清理规则同理。

## 适配新项目

- **Ant Design Vue**：`teleport_selectors` 改为 `.ant-dropdown-menu, .ant-popover, .ant-select-dropdown, .ant-picker-dropdown`；`el-dropdown` 改为 `<a-dropdown>`，`hide-on-click` 属性名不变。
- **Naive UI**：`teleport_selectors` 改为 `.n-dropdown-menu, .n-popover, .n-select-menu, .n-date-panel`；`el-dropdown` 改为 `<n-dropdown>`，属性改为 `:show-arrow="false"` + `:render-label`。
- **React / Next.js**：用 `react-click-outside-hook` 或 `useClickOutside` 自定义 hook；`@mousedown.stop` 改为 `onMouseDown={(e) => e.stopPropagation()}`；`teleport_selectors` 仍从 config 读取。
- **Vue 2**：`@mousedown.stop` 修饰符兼容；`<Transition>` 仍可用；`addEventListener` 在 `mounted` / `beforeDestroy` 钩子配对管理。
- **纯 JavaScript（无框架）**：用 `element.addEventListener('mousedown', e => e.stopPropagation())`；click outside 用 `document.addEventListener('click', handler)` + `closest()` 检查；其余规则不变。