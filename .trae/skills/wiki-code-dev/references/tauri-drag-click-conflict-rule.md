# Tauri drag-region 与 click 冲突处理规则（CODING-052）

> 复盘来源：Tauri 悬浮窗标题栏用 `data-tauri-drag-region` 实现拖动，但同时需要点击关闭按钮，结果点击事件被 drag-region 吞掉，关闭按钮无法响应。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `tauri_drag_click_conflict` 字段读取，禁止在规则文件中硬编码阈值或选择器。

## 触发场景

- Tauri 2.x 自定义标题栏使用 `data-tauri-drag-region` 实现窗口拖动
- 标题栏内的按钮（关闭/最小化/最大化/设置）无法响应 click 事件
- 同一元素需要同时支持拖动与点击
- 自定义窗口装饰（`decorations: false`）的标题栏实现
- Code Review 自定义标题栏代码时

## 不适用场景

- 原生窗口装饰（`decorations: true`，由 OS 处理拖动与点击）
- 仅拖动不需点击的元素（纯 drag-region，无冲突）
- Web 页面的拖动（用 `draggable` 属性，非 Tauri 机制）
- Electron 的 `-webkit-app-region: drag`（CSS 机制，规则不同）

## 规则

### 规则 1：`data-tauri-drag-region` 会吞掉 click 事件

`data-tauri-drag-region` 是 Tauri 提供的 HTML 属性，标记元素为窗口拖动区域。Tauri runtime 在该元素上拦截 `mousedown` 事件触发原生拖动，导致后续 `click` 事件无法触发。

### 规则 2：用 JS 区分拖动与点击

需要同时支持拖动与点击的元素，必须用 JS 手动区分两种行为：
- `mousedown` 记录初始位置与时间戳
- `mousemove` 超过阈值（默认 5px）→ 判定为拖动，调用 Rust 端 `start_dragging` 命令
- `mouseup` 未超过阈值 → 判定为点击，触发 click 逻辑

### 规则 3：配合 Rust 端 `start_dragging` 命令

Rust 端必须暴露 `start_dragging` 命令（通过 `window.start_dragging()` 调用 Tauri 原生拖动 API），前端通过 `invoke('start_dragging')` 触发。

### 为什么

- **drag-region 行为**：Tauri 在 `mousedown` 阶段调用 `start_dragging`，原生窗口进入拖动状态后，浏览器的 `click` 事件序列（mousedown → mouseup → click）被中断，click 永远不会触发
- **JS 区分可靠性**：基于位移阈值（5px）区分拖动与点击是 GUI 通用模式（Windows / macOS 原生标题栏同样用此机制），用户感知自然
- **阈值选择**：5px 是 Windows 与 macOS 的默认系统阈值，小于此值用户感知为"点击"，大于此值感知为"拖动"

## 判断逻辑

```
元素需要同时支持拖动与点击:
  IF 用 data-tauri-drag-region + @click:
      ❌ click 事件被吞，按钮无响应
  ELSE IF 用 JS 区分拖动与点击:
      ✅ mousedown 记录位置 → mousemove 超 5px 触发 start_dragging → mouseup 未超阈值视为 click

实现要点:
  STEP 1: 元素移除 data-tauri-drag-region 属性
  STEP 2: 绑定 mousedown 记录 clientX/clientY
  STEP 3: 绑定 mousemove，超 drag_threshold_px 触发 invoke('start_dragging')
  STEP 4: 绑定 mouseup，未超阈值时执行 click 逻辑
  STEP 5: Rust 端暴露 start_dragging 命令（调用 window.start_dragging()）
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_drag_click_conflict.enabled` | `true` | 是否启用 drag-click 冲突守卫 |
| `tauri_drag_click_conflict.severity` | `error` | 违规严重级别 |
| `tauri_drag_click_conflict.drag_attribute` | `data-tauri-drag-region` | Tauri 拖动属性名 |
| `tauri_drag_click_conflict.drag_threshold_px` | `5` | 拖动判定位移阈值（像素） |
| `tauri_drag_click_conflict.drag_threshold_ms` | `300` | 拖动判定时间阈值（毫秒，超过此时长仍未移动视为点击） |
| `tauri_drag_click_conflict.rust_command_name` | `start_dragging` | Rust 端拖动命令名（需在 ACL 三层声明，见 CODING-047） |
| `tauri_drag_click_conflict.mouse_down_record_fields` | `clientX, clientY, timestamp` | mousedown 记录的字段（逗号分隔） |
| `tauri_drag_click_conflict.drag_state_var` | `isDragging` | 拖动状态标志变量名 |
| `tauri_drag_click_conflict.required_lifecycle_hooks` | `onMounted, onBeforeUnmount` | 必须配对管理事件监听器的生命周期钩子 |

## 正确示例

### Vue 3 自定义标题栏组件

```vue
<!-- packages/web/src/components/TitleBar.vue -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { invoke } from '@tauri-apps/api/core';

const props = defineProps<{
  title: string;
}>();

const emit = defineEmits<{
  close: [];
  minimize: [];
}>();

// 拖动状态：区分点击与拖动的关键
// 用 ref 而非 data-tauri-drag-region，避免 click 被吞
const isDragging = ref(false);
const dragStartPos = ref<{ x: number; y: number; t: number } | null>(null);

const DRAG_THRESHOLD_PX = 5; // 从 config 读取

function onMouseDown(e: MouseEvent) {
  // 记录 mousedown 起始位置与时间，作为拖动/点击判定的基准
  dragStartPos.value = { x: e.clientX, y: e.clientY, t: Date.now() };
  isDragging.value = false;
}

function onMouseMove(e: MouseEvent) {
  if (!dragStartPos.value) return;
  const dx = e.clientX - dragStartPos.value.x;
  const dy = e.clientY - dragStartPos.value.y;
  // 位移超过阈值才触发拖动，避免微小抖动误判
  if (Math.sqrt(dx * dx + dy * dy) > DRAG_THRESHOLD_PX && !isDragging.value) {
    isDragging.value = true;
    invoke('start_dragging').catch(console.error);
  }
}

function onMouseUp(e: MouseEvent) {
  if (!dragStartPos.value) return;
  if (!isDragging.value) {
    // 未触发拖动 → 视为点击，但标题栏本身无点击逻辑
    // 子按钮（关闭/最小化）的 click 事件独立处理，不受影响
  }
  dragStartPos.value = null;
  isDragging.value = false;
}

function onClose() {
  emit('close');
}

function onMinimize() {
  emit('minimize');
}

// 事件监听器必须在 onMounted/onBeforeUnmount 配对管理，避免内存泄漏
onMounted(() => {
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
});

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove);
  window.removeEventListener('mouseup', onMouseUp);
});
</script>

<template>
  <!-- 注意：标题栏元素不加 data-tauri-drag-region，改用 @mousedown 手动处理 -->
  <div class="title-bar" @mousedown="onMouseDown">
    <span class="title">{{ title }}</span>
    <div class="buttons">
      <!-- 子按钮的 click 不受拖动逻辑影响，正常响应 -->
      <button class="btn-minimize" @click="onMinimize">—</button>
      <button class="btn-close" @click="onClose">×</button>
    </div>
  </div>
</template>

<style scoped>
.title-bar {
  display: flex;
  align-items: center;
  height: 32px;
  padding: 0 12px;
  user-select: none;
  cursor: default;
}
.buttons {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
</style>
```

### Rust 端 `start_dragging` 命令

```rust
// src/lib.rs
#[tauri::command]
async fn start_dragging(window: tauri::WebviewWindow) -> Result<(), String> {
    // 调用 Tauri 原生拖动 API，进入窗口拖动状态
    // 命令必须在 ACL 三层声明（CODING-047）
    window.start_dragging().map_err(|e| e.to_string())
}

pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![start_dragging])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### build.rs ACL 声明（配合 CODING-047）

```rust
// build.rs
tauri_build::build_attributes! {
    tauri_build::AppManifest {
        commands: &["start_dragging"],
        ..Default::default()
    }
}
```

```json
// capabilities/default.json
{
  "permissions": ["core:default", "allow-start-dragging"]
}
```

## 错误示例

### 错误 1：同时用 `data-tauri-drag-region` 与 `@click`

```vue
<!-- ❌ data-tauri-drag-region 吞掉 click，按钮无响应 -->
<div data-tauri-drag-region @click="onTitleClick">
  <button @click="onClose">×</button>
</div>
```

### 错误 2：仅靠 `click` 事件区分

```vue
<!-- ❌ 拖动后仍触发 click，用户体验混乱 -->
<div @click="onTitleClick" @mousedown="startDrag">
  <!-- startDrag 调用 start_dragging 后，click 仍会触发 -->
</div>
```

### 错误 3：未清理事件监听器

```vue
<!-- ❌ window 级监听器未在 onBeforeUnmount 移除，组件销毁后仍触发 -->
<script setup>
onMounted(() => {
  window.addEventListener('mousemove', onMouseMove);
  // 缺少 onBeforeUnmount 清理
});
</script>
```

### 错误 4：阈值过小

```typescript
// ❌ 阈值 1px，用户轻微抖动即触发拖动，点击难以触发
const DRAG_THRESHOLD = 1;
```

## 错误诊断速查表

| 现象 | 根因 | 修复动作 |
|------|------|---------|
| 标题栏按钮点击无响应 | `data-tauri-drag-region` 吞掉 click | 移除属性，用 JS 区分拖动与点击 |
| 拖动后仍触发 click | 未用 `isDragging` 标志拦截 | mouseup 时检查 `isDragging`，true 则不触发 click |
| 拖动不流畅 | `start_dragging` 调用时机过晚 | mousemove 超 5px 立即调用，不等 mouseup |
| 组件销毁后报错 | window 监听器未清理 | onBeforeUnmount 中 `removeEventListener` |
| 微小抖动误判拖动 | 阈值过小（<5px） | 阈值设为 5px（系统默认值） |
| `start_dragging` 调用报错 | Rust 命令未在 ACL 三层声明 | 按 CODING-047 补齐 build.rs / capabilities / lib.rs |

## 适用场景

- Tauri 2.x 自定义窗口装饰（`decorations: false`）的标题栏
- 悬浮窗 / 工具栏同时需要拖动与点击
- 任何"同一元素既拖动又点击"的 Tauri UI 场景
- macOS / Windows / Linux 跨平台标题栏实现

## 适配新项目

- **React 项目**：`required_lifecycle_hooks` 改为 `useEffect mount, useEffect cleanup`
- **Svelte 项目**：用 `onMount` / `onDestroy` 替代 Vue 钩子
- **原生 JS 项目**：在 DOM Ready 时 addEventListener，unload 时 remove
- **触屏设备**：追加 `touchstart` / `touchmove` / `touchend` 处理，阈值适当放大（如 10px）
- **不同阈值偏好**：根据用户群体调整 `drag_threshold_px`（精确操作场景用 3px，粗放场景用 8px）
- **Electron 项目**：规则不适用，Electron 用 `-webkit-app-region: drag` + `-webkit-app-region: no-drag` 区分
