# Rule Catalog - Update Check State Machine (Frontend Async Flow)

## Scope
- Covers: 前端"检查更新"功能的状态机审查、轮询定时器生命周期管理、缓存与轮询节奏对齐、离线模式降级。
- Does NOT cover: 后端缓存实现（属于后端审查）、PWA Service Worker 更新（属于构建/Service Worker 范畴）、Electron 自动更新（属于桌面端范畴）。

> 所有可配置参数（缓存 TTL、轮询间隔、首次延迟、状态机必需状态等）集中定义在 [config/review-config.md](../config/review-config.md) 的"检查更新审查参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### UC-1: 检查更新状态机必须覆盖全部必需状态

IsUrgent: True
Category: Update Check

### Description

"检查更新"功能必须实现完整的状态机，覆盖 `check_update.required_states`（默认 `idle, loading, latest, newer, error`）五个状态：

- `idle`：初始态/重置态，按钮可点击
- `loading`：请求中，按钮禁用并显示 loading 图标
- `latest`：已是最新版，3 秒后自动回 `idle`
- `newer`：发现新版本，显示更新按钮（链接到下载/详情页）
- `error`：请求失败，显示重试按钮

任一状态缺失会导致 UI 卡在某个不可恢复的中间态（如永远 loading、永远 error 无重试）。

### UC-2: 轮询定时器必须在 onBeforeUnmount 中清理

IsUrgent: True
Category: Update Check

### Description

轮询检查更新使用 `setInterval` 时，必须在 `onBeforeUnmount` 中 `clearInterval`。否则组件卸载后定时器仍在执行，引发：
- 内存泄漏（闭包持有已卸载组件的 ref）
- 状态更新警告（Vue 警告"组件已卸载仍更新状态"）
- 重复请求（每次进入组件都新建一个定时器，老的没清理）

### UC-3: 轮询间隔必须大于后端缓存 TTL

IsUrgent: True
Category: Update Check

### Description

前端轮询间隔 `check_update.poll_interval_ms` 必须 ≥ 后端缓存 TTL `check_update.cache_ttl_ms`。

若轮询间隔 < 缓存 TTL，每次轮询都命中缓存，相当于无意义的额外请求（虽不增加后端负担但浪费网络往返）。若轮询间隔 > 缓存 TTL，每次轮询都会触发后端真实请求，可能触发外部 API 限流。

推荐：轮询间隔 = 缓存 TTL（默认均为 5 分钟），保证每次轮询都恰好触发后端一次真实检查。

### UC-4: 离线模式必须返回固定值

IsUrgent: False
Category: Update Check

### Description

当 `check_update.offline_mode: true`（项目无外网通道或无 GitHub Release 通道）时，后端 `/api/about/check-update` 必须固定返回 `{ has_update: false, source: 'local' }`，避免：
- 前端每次轮询都触发真实 GitHub API 调用（增加延迟）
- 网络错误时前端误报"有新版本"（因 fallback 处理不当）
- 用户困惑（看到"有更新"但点击后无法跳转下载）

### Judgment Logic

1. 在目标 `.vue` 文件 `<script setup>` 段搜索 `checkUpdate` / `check_update` / `setInterval` / `updateState` 等关键词。
2. 验证 `updateState` 的类型是否为联合类型 `idle | loading | latest | newer | error`，且每个状态都有对应的 UI 分支（`v-if` / `v-else-if`）。
3. 检查 `setInterval` 调用是否在 `onMounted` 中，且 `clearInterval` 在 `onBeforeUnmount` 中配对。
4. 若配置 `check_update.offline_mode: true`，验证后端接口返回固定值（前端不发起真实外部请求）。
5. 若配置 `check_update.first_check_delay_ms > 0`，验证首次检查是 `setTimeout` 延迟触发，而非立即触发。

### Applicable Scenarios

- Vue 3 + `<script setup>` 的"关于"页面或"设置"面板的检查更新功能。
- 内网部署项目（无 GitHub Release 通道，需离线模式降级）。
- 任何使用轮询定时的异步状态机场景。

### Non-Applicable Scenarios

- PWA Service Worker 更新（属于 Service Worker 生命周期，不归前端组件管）。
- Electron autoUpdater（属于主进程，IPC 通信由框架管理）。
- 一次性检查（无轮询需求，可省略 UC-2 / UC-3）。
- 公网开源项目（`offline_mode: false`，需真实 GitHub API 调用，UC-4 不适用）。

### Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `check_update.cache_ttl_ms` | `300000`（5 分钟） | 后端缓存 TTL（毫秒） |
| `check_update.poll_interval_ms` | `300000`（5 分钟） | 前端轮询间隔（毫秒），必须 ≥ `cache_ttl_ms` |
| `check_update.first_check_delay_ms` | `5000` | 首次检查延迟（毫秒），避免与首屏渲染竞争 |
| `check_update.latest_to_idle_ms` | `3000` | `latest` 状态自动回 `idle` 的延迟 |
| `check_update.offline_mode` | `true` | 离线模式开关；`true` 时后端固定返回 `has_update: false` |
| `check_update.required_states` | `idle, loading, latest, newer, error` | 必需状态列表（逗号分隔） |
| `check_update.update_endpoint` | `/api/about/check-update` | 后端检查更新接口路径 |
| `check_update.cleanup_hook` | `onBeforeUnmount` | 定时器清理生命周期钩子名 |

### Example

```vue
<!-- ❌ Wrong: 状态机不完整 + 定时器未清理 -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'

const updateState = ref<'loading' | 'latest' | 'newer'>('loading')

async function checkUpdate() {
  updateState.value = 'loading'
  const res = await fetch('/api/about/check-update')
  // ❌ 无 error 状态处理
  // ❌ 无 idle 初始态
  updateState.value = res.has_update ? 'newer' : 'latest'
}

onMounted(() => {
  checkUpdate()
  // ❌ setInterval 未在 onBeforeUnmount 清理
  setInterval(checkUpdate, 300000)
})
</script>

<!-- ✅ Right: 完整状态机 + 定时器清理 -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

// ✅ 五态联合类型，与 config.check_update.required_states 一致
type UpdateState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'latest'; checkedAt: number }
  | { kind: 'newer'; version: string; url: string }
  | { kind: 'error'; message: string }

const updateState = ref<UpdateState>({ kind: 'idle' })
let pollTimer: ReturnType<typeof setInterval> | null = null
let firstCheckTimer: ReturnType<typeof setTimeout> | null = null

async function checkUpdate() {
  updateState.value = { kind: 'loading' }
  try {
    const res = await fetch('/api/about/check-update')
    const data = await res.json()
    if (data.has_update) {
      updateState.value = { kind: 'newer', version: data.version, url: data.url }
    } else {
      updateState.value = { kind: 'latest', checkedAt: Date.now() }
      // latest 3 秒后自动回 idle
      setTimeout(() => {
        if (updateState.value.kind === 'latest') {
          updateState.value = { kind: 'idle' }
        }
      }, 3000)  // 与 config.check_update.latest_to_idle_ms 一致
    }
  } catch (e) {
    updateState.value = { kind: 'error', message: (e as Error).message }
  }
}

onMounted(() => {
  // ✅ 首次检查延迟 5 秒，避免与首屏渲染竞争
  firstCheckTimer = setTimeout(checkUpdate, 5000)
  // ✅ 轮询间隔 = 缓存 TTL（5 分钟），保证每次恰好触发一次后端真实检查
  pollTimer = setInterval(checkUpdate, 300000)
})

// ✅ 必须在 onBeforeUnmount 配对清理
onBeforeUnmount(() => {
  if (firstCheckTimer) clearTimeout(firstCheckTimer)
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <!-- ✅ 五态各有对应 UI 分支 -->
  <el-button v-if="updateState.kind === 'idle'" @click="checkUpdate">检查更新</el-button>
  <el-button v-else-if="updateState.kind === 'loading'" loading disabled>检查中</el-button>
  <el-tag v-else-if="updateState.kind === 'latest'" type="success">已是最新版</el-tag>
  <el-button v-else-if="updateState.kind === 'newer'" type="primary" @click="openReleaseUrl(updateState.url)">
    发现新版本 {{ updateState.version }}
  </el-button>
  <el-button v-else-if="updateState.kind === 'error'" type="danger" @click="checkUpdate">检查失败，重试</el-button>
</template>
```

### Checklist

- [ ] 状态机覆盖 `check_update.required_states` 全部状态（默认 5 态）
- [ ] 每个状态有对应的 UI 分支（`v-if` / `v-else-if`）
- [ ] `setInterval` 在 `onMounted` 启动，`clearInterval` 在 `onBeforeUnmount` 配对清理
- [ ] 轮询间隔 ≥ 后端缓存 TTL（默认均为 5 分钟）
- [ ] 首次检查用 `setTimeout` 延迟触发（默认 5 秒）
- [ ] `latest` 状态 3 秒后自动回 `idle`
- [ ] 离线模式 `offline_mode: true` 时后端固定返回 `{ has_update: false }`
