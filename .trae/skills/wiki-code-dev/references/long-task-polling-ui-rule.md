# 长任务轮询 UI 模式规则（CODING-065）

> 复盘来源：v3 媒体生成工具开发中，视频生成长任务前端 UI 经历多次迭代：①初版用 SSE 流，超时中断；②改用轮询后，单次失败即终止轮询，网络抖动体验差；③轮询定时器未在组件卸载时清理，导致内存泄漏；④停止/超时/完成三态混杂在 errorMessage 中，状态机混乱。最终提炼出 5 状态机 + 容错轮询 + 三态区分 + 函数拆分 + 生命周期清理的完整模式。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `long_task` 字段读取，禁止在规则文件中硬编码轮询间隔或状态枚举。

## 规则

**前端长任务（视频生成、批量处理等）UI 交互必须遵守七项契约**：

1. **5 状态机**：长任务用 `setInterval(poll_interval_ms)` 轮询，5 状态机驱动 UI 模板切换（`idle | queued | processing | completed | failed`）
2. **容错轮询**：轮询单次失败不终止，仅更新 error 文案，容忍网络抖动（仅 completed/failed 状态终止轮询）
3. **显式停止**：完成/失败显式 `stopXxxPolling()` 停止定时器，禁止依赖垃圾回收
4. **三态区分**：用户停止/超时/正常完成三态用 `abortReason: 'user' | 'timeout' | null` 区分，避免主动取消污染 errorMessage
5. **超时用 setTimeout**：超时用 `setTimeout` 而非 `AbortSignal.timeout`（因需同步设 abortReason 标记）
6. **函数拆分**："关闭对话框"（停轮询 + 关对话框 + 重置全部）与"重置状态保持对话框"（停轮询 + 清状态，允许重新生成）拆为两个函数
7. **生命周期清理**：onBeforeUnmount 必须清理 abortController + 所有 addEventListener + setInterval timer

## 适用场景

- 前端长任务 UI（视频生成、批量处理、文件转码、模型训练等）
- 需要轮询后端任务状态的场景（创建任务 + 轮询状态 + 获取结果三阶段）
- 需要 5 状态机驱动 UI 切换的场景（idle/queued/processing/completed/failed）
- 用户可主动停止的长任务

## 不适用场景

- 秒级任务（直接用 SSE 流或单次请求，无需轮询）
- 后台任务（无需前端 UI，用任务队列 + 通知机制）
- 一次性请求（无状态机，无轮询）
- WebSocket 实时推送（无需轮询，服务端推送状态变更）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `long_task.poll_interval_ms` | `5000` | 轮询间隔（毫秒） |
| `long_task.state_machine_values` | `idle,queued,processing,completed,failed` | 5 状态机枚举 |
| `long_task.timeout_ms` | `300000` | 长任务超时（毫秒，默认 5 分钟） |
| `long_task.abort_reason_values` | `user,timeout,null` | 停止原因枚举 |
| `long_task.max_poll_failures` | `3` | 连续失败上限（超过则终止轮询） |
| `long_task.ui_dialog_selector` | `.long-task-dialog` | 长任务对话框选择器 |

## 检查方式

1. **状态机检查**：长任务 UI 必须有 5 状态机（`idle | queued | processing | completed | failed`），禁止用 boolean 或散乱状态
2. **容错轮询检查**：轮询 catch 块只更新 error 文案，不调用 `stopXxxPolling()`（除非连续失败 ≥ `max_poll_failures`）
3. **显式停止检查**：completed/failed 状态必须显式调用 `stopXxxPolling()`，禁止依赖 GC
4. **三态区分检查**：停止/超时/完成三态必须用 `abortReason` 区分，主动停止不更新 errorMessage
5. **超时实现检查**：超时用 `setTimeout` + 手动 `abortReason = 'timeout'`，禁止用 `AbortSignal.timeout`（无法同步设标记）
6. **函数拆分检查**："关闭对话框"与"重置状态保持对话框"必须拆为两个函数，禁止合并
7. **生命周期清理检查**：onBeforeUnmount 必须清理 abortController + addEventListener + setInterval

## 正确示例

```vue
<!-- frontend/src/views/Query.vue -->
<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue';
import { config } from '../config';

const lt = config.long_task;

// ✅ 5 状态机
type TaskState = 'idle' | 'queued' | 'processing' | 'completed' | 'failed';
const taskState = ref<TaskState>('idle');
const errorMessage = ref('');
const videoUrl = ref('');
const abortReason = ref<'user' | 'timeout' | null>(null);

let abortController: AbortController | null = null;
let pollingTimer: ReturnType<typeof setInterval> | null = null;
let timeoutTimer: ReturnType<typeof setTimeout> | null = null;
let consecutiveFailures = 0;

/**
 * 启动视频生成长任务
 */
async function startVideoGeneration(prompt: string) {
  // 重置状态
  taskState.value = 'queued';
  errorMessage.value = '';
  videoUrl.value = '';
  abortReason.value = null;
  consecutiveFailures = 0;

  abortController = new AbortController();

  // ✅ 超时用 setTimeout，同步设 abortReason
  timeoutTimer = setTimeout(() => {
    abortReason.value = 'timeout';
    abortController?.abort();
    stopPolling();
    taskState.value = 'failed';
    errorMessage.value = '生成超时，请重试';
  }, lt.timeout_ms);

  try {
    // 创建任务
    const createRes = await fetch('/api/media/video', {
      method: 'POST',
      signal: abortController.signal,
      body: JSON.stringify({ prompt }),
    });
    const { taskId } = await createRes.json();

    // ✅ 启动轮询
    startPolling(taskId);
  } catch (err) {
    if (abortReason.value === 'user' || abortReason.value === 'timeout') return;
    taskState.value = 'failed';
    errorMessage.value = err instanceof Error ? err.message : String(err);
  }
}

/**
 * 启动轮询——容错轮询，单次失败不终止
 */
function startPolling(taskId: string) {
  // ✅ 轮询间隔从 config 读取
  pollingTimer = setInterval(async () => {
    try {
      const res = await fetch(`/api/media/video/${taskId}`);
      const data = await res.json();

      // ✅ 单次成功重置失败计数
      consecutiveFailures = 0;

      if (data.status === 'completed') {
        videoUrl.value = data.url;
        taskState.value = 'completed';
        // ✅ 显式停止轮询
        stopPolling();
      } else if (data.status === 'failed') {
        errorMessage.value = data.error || '生成失败';
        taskState.value = 'failed';
        stopPolling();
      } else {
        // queued / processing 更新状态
        taskState.value = data.status as TaskState;
      }
    } catch (err) {
      // ✅ 容错轮询：单次失败不终止，仅更新 error 文案
      consecutiveFailures++;
      errorMessage.value = `轮询失败 (${consecutiveFailures}/${lt.max_poll_failures}): ${err}`;

      // 连续失败超上限才终止
      if (consecutiveFailures >= lt.max_poll_failures) {
        taskState.value = 'failed';
        stopPolling();
      }
    }
  }, lt.poll_interval_ms);
}

/**
 * 停止轮询——清理定时器
 */
function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
  if (timeoutTimer) {
    clearTimeout(timeoutTimer);
    timeoutTimer = null;
  }
}

/**
 * 用户主动停止
 */
function stopGeneration() {
  // ✅ 三态区分：标记 user
  abortReason.value = 'user';
  abortController?.abort();
  stopPolling();
  taskState.value = 'idle';
}

/**
 * 关闭对话框——停轮询 + 关对话框 + 重置全部
 */
function closeDialog() {
  stopGeneration();
  taskState.value = 'idle';
  errorMessage.value = '';
  videoUrl.value = '';
}

/**
 * 重置状态保持对话框——停轮询 + 清状态，允许重新生成
 */
function resetKeepDialog() {
  stopPolling();
  abortReason.value = null;
  taskState.value = 'idle';
  errorMessage.value = '';
  videoUrl.value = '';
  // 对话框保持打开，用户可重新输入 prompt 生成
}

// ✅ 生命周期清理：卸载时清理所有资源
onBeforeUnmount(() => {
  stopPolling();
  abortController?.abort();
});
</script>

<template>
  <div :class="lt.ui_dialog_selector">
    <!-- 5 状态机驱动 UI 切换 -->
    <div v-if="taskState === 'idle'">请输入 prompt 生成视频</div>
    <div v-else-if="taskState === 'queued'">排队中...</div>
    <div v-else-if="taskState === 'processing'">生成中...</div>
    <div v-else-if="taskState === 'completed'">
      <video :src="videoUrl" controls></video>
      <button @click="resetKeepDialog">重新生成</button>
      <button @click="closeDialog">关闭</button>
    </div>
    <div v-else-if="taskState === 'failed'">
      <p>{{ errorMessage }}</p>
      <button @click="resetKeepDialog">重试</button>
      <button @click="closeDialog">关闭</button>
    </div>
    <button v-if="taskState === 'queued' || taskState === 'processing'" @click="stopGeneration">停止</button>
  </div>
</template>
```

## 错误示例

```typescript
// ❌ 错误：单次失败即终止轮询，网络抖动体验差
pollingTimer = setInterval(async () => {
  try {
    const res = await fetch(`/api/media/video/${taskId}`);
    // ...
  } catch (err) {
    stopPolling(); // ⚠️ 单次失败就终止，应容忍网络抖动
    taskState.value = 'failed';
  }
}, 5000);

// ❌ 错误：完成/失败不停止轮询，依赖 GC
if (data.status === 'completed') {
  taskState.value = 'completed';
  // ⚠️ 缺少 stopPolling()，定时器继续运行
}

// ❌ 错误：超时用 AbortSignal.timeout，无法同步设 abortReason
const signal = AbortSignal.timeout(300000);
// ⚠️ 超时触发后无法同步标记 abortReason = 'timeout'，无法区分超时与用户停止

// ❌ 错误：三态混杂在 errorMessage 中
function stopGeneration() {
  errorMessage.value = '用户已停止'; // ⚠️ 停止原因不应进 errorMessage
  abortController?.abort();
}

// ❌ 错误：关闭对话框与重置状态合并为一个函数
function closeDialog() {
  stopPolling();
  taskState.value = 'idle';
  // ⚠️ 缺少"重置状态保持对话框"场景，用户无法重新生成
}

// ❌ 错误：onBeforeUnmount 未清理定时器
// ⚠️ 组件卸载后轮询定时器仍在运行，内存泄漏
```

## 适配新项目

- 适配 React：用 `useRef<ReturnType<typeof setInterval>>` 替代模块级变量，useEffect cleanup 中清理
- 适配 WebSocket 推送：用 WebSocket 替代轮询，状态机不变，停止用 `websocket.close()` 替代 `clearInterval`
- 适配任务队列 UI：5 状态机扩展为 7 状态（追加 `cancelled` / `paused`），适配更复杂的任务生命周期
- 适配 PWA：轮询在 service worker 中进行，主线程通过 postMessage 接收状态更新
- 适配移动端：轮询间隔调大（10s+），减少电量消耗；网络切换时自动重试

## 与其他规则的关系

- 与 CODING-059（长/短任务架构分离）联动：本规则是长任务的前端 UI 部分，后端走独立 JSON 端点 + 轮询
- 与 CODING-064（SSE 流消费错误处理）联动：秒级任务走 SSE 时用 SSE 错误处理，长任务走轮询时用本规则的容错轮询
- 与 CODING-066（事件委托 + 生命周期清理）联动：本规则的 onBeforeUnmount 清理属于生命周期清理的一部分
- 与 CODING-057（超时分级策略）联动：长任务超时用 `long_task.timeout_ms`（默认 5 分钟），与外部 API 调用的超时分级独立
- 与 CODING-013（优雅停止）联动：组件卸载时停止轮询 + abort 请求，避免内存泄漏
