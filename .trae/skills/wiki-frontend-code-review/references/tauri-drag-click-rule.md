# drag + click 冲突处理审查（FR-043）

> 复盘来源：Tauri 2.x 桌面应用的悬浮卡片标题栏同时需要拖动窗口与点击切换收起/展开状态。直接用 `data-tauri-drag-region` 属性后，原生 drag 拦截了 mousedown 事件，click 永远不触发；反之不设 drag-region 则无法拖动窗口。最终方案须用 JS 手动区分 mousedown / mousemove / mouseup，移动距离超阈值才调 `invoke('start_dragging')`，否则视作 click。
> 所有可变参数从 config/review-config.md 的 `tauri_drag_click_frontend` 字段读取。

## 规则

### FR-043-1：同时需要拖动和点击的元素禁用 data-tauri-drag-region

UI 元素若同时承担以下两种交互职责：
1. **窗口拖动**：用户按住元素移动鼠标应拖动整个桌面窗口。
2. **点击触发**：用户在元素上单击应触发业务逻辑（如展开/收起、切换状态）。

则**禁止**直接使用 `data-tauri-drag-region` 属性。`data-tauri-drag-region` 会让 Tauri 原生层在 mousedown 阶段直接拦截事件并进入拖动状态，浏览器 click 事件永不触发。

判断标准：
- 元素同时具备 drag 与 click 职责 + 直接用 `data-tauri-drag-region` → FAIL。
- 元素仅承担 drag（无 click 职责）→ 允许用 `data-tauri-drag-region`。

### FR-043-2：必须用 JS 区分 mousedown / mousemove / mouseup

同时需要拖动和点击的元素必须用以下 JS 模式实现：

1. **mousedown**：记录初始坐标 `(startX, startY)` 与时间戳，标记 `isDragging = false`。
2. **mousemove**：计算位移 `Δ = sqrt((curX-startX)² + (curY-startY)²)`；若 `Δ > move_threshold`，标记 `isDragging = true` 并调用 `invoke('start_dragging')` 启动原生拖动，且只调用一次。
3. **mouseup**：若 `isDragging === false`，触发 click 回调；若 `isDragging === true`，重置状态不触发 click。

判断标准：未实现上述三阶段处理或缺失移动阈值 → FAIL。

### FR-043-3：移动阈值必须从 config 读取

移动阈值（`move_threshold`，单位 px）通过 config 管理，默认 `5`。低于此阈值的鼠标移动视为点击抖动，不触发拖动；等于或超过此阈值视为拖动意图，调用 `start_dragging`。阈值不可硬编码到组件中。

### FR-043-4：start_dragging 命令调用一致性

调用 `invoke('start_dragging')` 须满足：
1. 命令名 `start_dragging` 与 config 中 `start_dragging_command` 字段一致。
2. 该命令由 Tauri window 插件提供，须在 `plugin_command_allowlist` 中（FR-041 配置）。
3. 调用前须确保 `isDragging` 未重复触发（即一次 mousedown 周期内只调一次）。

## 适用场景

- Tauri 2.x 桌面应用，存在同时需要拖动窗口与点击交互的 UI 元素（如悬浮卡片标题栏、可折叠工具栏、双击最大化按钮等）。
- Vue 3 + `<script setup>` 项目，用 `@mousedown` / `@mousemove` / `@mouseup` 绑定事件。

## 不适用场景

- 仅需拖动、无需点击的元素（如纯装饰性标题栏）—— 直接用 `data-tauri-drag-region` 即可。
- 仅需点击、无需拖动的元素（如普通按钮）—— 不需要 drag 处理。
- 浏览器端 Web 应用（无原生窗口拖动概念）。
- Electron 项目（拖动机制不同，用 `-webkit-app-region: drag` CSS 属性）。

## 检查流程

```
[开始] 扫描前端代码
  │
  ▼
[1] 识别同时承担 drag + click 职责的元素
  │  ├─ 元素含 data-tauri-drag-region 且绑定了 @click / @dblclick → FAIL（FR-043-1）
  │  └─ 元素含 @mousedown 且代码中调用了 start_dragging + 含 @click → 标记为待审查元素
  │
  ▼
[2] 对待审查元素核对三阶段处理
  │  ├─ @mousedown：记录 startX/startY + isDragging=false → 缺失则 FAIL（FR-043-2）
  │  ├─ @mousemove：计算位移，超阈值调 invoke('start_dragging') 一次 → 缺失则 FAIL
  │  └─ @mouseup：根据 isDragging 决定是否触发 click → 缺失则 FAIL
  │
  ▼
[3] 移动阈值来源检查
  │  └─ 阈值硬编码（如 if (delta > 5)）而非从 config 读取 → FAIL（FR-043-3）
  │
  ▼
[4] start_dragging 调用一致性检查
  │  ├─ 命令名与 config 中 start_dragging_command 不一致 → FAIL（FR-043-4）
  │  └─ 一次 mousedown 周期内重复调用 start_dragging → FAIL
  │
  ▼
[5] 全部通过 → PASS
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_drag_click_frontend.move_threshold_px` | `5` | 鼠标移动阈值（像素），超过此值视为拖动意图 |
| `tauri_drag_click_frontend.start_dragging_command` | `start_dragging` | 调用 Rust 端启动原生拖动的 invoke 命令名 |
| `tauri_drag_click_frontend.drag_region_attribute` | `data-tauri-drag-region` | Tauri 原生 drag 属性名（用于识别误用） |
| `tauri_drag_click_frontend.required_mouse_events` | `mousedown, mousemove, mouseup` | drag+click 元素必须绑定的鼠标事件列表（逗号分隔） |
| `tauri_drag_click_frontend.click_max_move_px` | `5` | 视为 click 的最大移动距离（与 move_threshold_px 通常一致） |
| `tauri_drag_click_frontend.dblclick_timeout_ms` | `300` | 双击间隔（毫秒），若元素还含 @dblclick 须额外检查时序 |
| `tauri_drag_click_frontend.allow_data_tauri_drag_region` | `true` | 是否允许在纯 drag 元素上使用 `data-tauri-drag-region`（默认允许） |

## 检查方式

1. Grep 前端 `.vue` / `.ts` 文件中的 `data-tauri-drag-region` 属性，对命中元素检查是否同时绑定 `@click` / `@dblclick` / `v-on:click` —— 若有则 FAIL。
2. Grep `invoke('start_dragging')` 或 `invoke("{start_dragging_command}")` 调用位置，反查其所在组件是否实现三阶段 mousedown/mousemove/mouseup 处理。
3. 核对 `move_threshold_px` 是否从 config 读取，而非硬编码字面量。
4. 检查 `start_dragging` 命令名是否与 config 一致，且 `isDragging` 标志确保单次 mousedown 周期内只调用一次。
5. 若元素还含 `@dblclick`，核对 `dblclick_timeout_ms` 时序逻辑（避免 drag 误触发 dblclick）。

## 正确示例

```vue
<!-- ✅ FloatingCard.vue — 三阶段 drag+click 处理 -->
<script setup lang="ts">
import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'

// 阈值从 config 读取（项目通常封装为 useConfig composable）
const MOVE_THRESHOLD_PX = 5  // 实际项目从 config.tauri_drag_click_frontend.move_threshold_px 读取

const isDragging = ref(false)
let startX = 0
let startY = 0
let dragStarted = false  // 防止单次 mousedown 周期内重复调 start_dragging

function onMouseDown(e: MouseEvent) {
  // 记录起点，标记尚未拖动
  startX = e.clientX
  startY = e.clientY
  isDragging.value = false
  dragStarted = false
}

function onMouseMove(e: MouseEvent) {
  // 计算位移，超阈值才启动原生拖动，且只调一次
  const dx = e.clientX - startX
  const dy = e.clientY - startY
  const delta = Math.sqrt(dx * dx + dy * dy)
  if (!dragStarted && delta > MOVE_THRESHOLD_PX) {
    isDragging.value = true
    dragStarted = true
    // ✅ 调用 Rust 端 start_dragging（由 Tauri window 插件提供）
    invoke('start_dragging').catch(err => console.error('drag failed:', err))
  }
}

function onMouseUp() {
  // 未拖动则视为 click，触发业务逻辑
  if (!isDragging.value) {
    toggleCollapse()
  }
  isDragging.value = false
  dragStarted = false
}

function toggleCollapse() {
  // 业务逻辑：切换卡片收起/展开
  collapsed.value = !collapsed.value
}

const collapsed = ref(false)
</script>

<template>
  <!-- ✅ 不用 data-tauri-drag-region，改用三阶段事件处理 -->
  <div
    class="card-header"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
  >
    <span class="title">悬浮卡片</span>
  </div>
</template>
```

```vue
<!-- ✅ 纯拖动元素（无 click 职责）仍可用 data-tauri-drag-region -->
<template>
  <!-- 标题栏装饰区域，仅用于拖动窗口，无点击交互 -->
  <div class="title-bar-decoration" data-tauri-drag-region></div>
</template>
```

## 错误示例

```vue
<!-- ❌ 同时承担 drag + click 但直接用 data-tauri-drag-region -->
<template>
  <!-- data-tauri-drag-region 会拦截 mousedown，click 永远不触发 -->
  <div
    class="card-header"
    data-tauri-drag-region
    @click="toggleCollapse"
  >
    <span class="title">悬浮卡片</span>
  </div>
</template>
```

```vue
<!-- ❌ 实现了 mousedown/mousemove/mouseup 但阈值硬编码 -->
<script setup lang="ts">
function onMouseMove(e: MouseEvent) {
  const dx = e.clientX - startX
  const dy = e.clientY - startY
  // ❌ 5px 阈值硬编码，未从 config 读取
  if (Math.sqrt(dx * dx + dy * dy) > 5) {
    invoke('start_dragging')
  }
}
</script>
```

```vue
<!-- ❌ 缺失 mouseup 处理，无法区分点击与拖动 -->
<script setup lang="ts">
function onMouseDown(e: MouseEvent) {
  startX = e.clientX
  startY = e.clientY
}
function onMouseMove(e: MouseEvent) {
  const dx = e.clientX - startX
  if (Math.abs(dx) > MOVE_THRESHOLD_PX) {
    invoke('start_dragging')
  }
}
// ❌ 无 onMouseUp，isDragging 标志不会重置，click 触发条件永远不正确
</script>
```

```vue
<!-- ❌ 一次 mousedown 周期内重复调用 start_dragging -->
<script setup lang="ts">
function onMouseMove(e: MouseEvent) {
  const delta = Math.sqrt(
    (e.clientX - startX) ** 2 + (e.clientY - startY) ** 2
  )
  if (delta > MOVE_THRESHOLD_PX) {
    // ❌ 每次 mousemove 都调用，导致 start_dragging 被调用 N 次
    invoke('start_dragging')
  }
}
</script>
```

```vue
<!-- ❌ 命令名与 config 中 start_dragging_command 不一致 -->
<script setup lang="ts">
// config 配置 start_dragging_command = 'start_dragging'
// 但代码写成了 'startDrag' → FAIL
function onMouseMove(e: MouseEvent) {
  if (delta > MOVE_THRESHOLD_PX) {
    invoke('startDrag')  // ❌ 命令名不一致
  }
}
</script>
```

## 适配新项目

- **React / Next.js 项目**：把 `@mousedown` 替换为 `onMouseDown` props，逻辑一致。
- **Svelte / Solid 项目**：用 `on:mousedown` / `onMouseDown`，阈值仍从 config 读取。
- **移动端项目**：把 mousedown/mousemove/mouseup 替换为 touchstart/touchmove/touchend，阈值通常放大到 `10`（手指接触面大于鼠标）。
- **多 drag 区域项目**：若项目有多个 drag+click 元素（如多个悬浮卡片），把三阶段处理抽成 `useDragClick` composable，参数从 config 注入。
- **含双击场景**：若元素还含 `@dblclick`（如双击最大化），须额外核对 `dblclick_timeout_ms` 时序，避免 drag 误触发 dblclick。

## 输出格式

```
FAIL — drag+click 元素误用 data-tauri-drag-region
  FilePath: frontend/src/components/FloatingCard.vue line 12
  元素同时绑定 data-tauri-drag-region 与 @click，click 事件永不触发

  <div
    class="card-header"
    data-tauri-drag-region
    @click="toggleCollapse"
  >

修复建议：
  1. 移除 data-tauri-drag-region 属性
  2. 实现 @mousedown / @mousemove / @mouseup 三阶段处理
  3. mousemove 中位移超过 move_threshold_px (5px) 时调 invoke('start_dragging')
  4. mouseup 中根据 isDragging 标志决定是否触发 click 回调
```

```
FAIL — 移动阈值硬编码
  FilePath: frontend/src/components/FloatingCard.vue line 28
  if (delta > 5) 中阈值 5 未从 config 读取

修复建议：
  从 config.tauri_drag_click_frontend.move_threshold_px 读取阈值
  const MOVE_THRESHOLD_PX = config.tauri_drag_click_frontend.move_threshold_px
```

```
FAIL — start_dragging 调用未防重复
  FilePath: frontend/src/components/FloatingCard.vue line 35
  onMouseMove 中每次移动都调用 invoke('start_dragging')，导致单次 mousedown 周期内调用 N 次

修复建议：
  增加 dragStarted 标志，确保单次 mousedown 周期内只调一次：
  if (!dragStarted && delta > MOVE_THRESHOLD_PX) {
    dragStarted = true
    invoke('start_dragging')
  }
```
