/**
 * Pinia Store 模板（setup 语法 + SSE 事件处理）
 * 
 * 关键约束：
 * - 必须使用 setup 语法（composition API）
 * - SSE 事件处理须拆分为独立 action
 * - 状态变更须通过 action 而非直接赋值
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { SSEEvent, CompileState } from '@/types';
import { consumeSSEStream } from '@/api/wiki';

export const useCompileStore = defineStore('compile', () => {
  // ===== 状态定义（ref）=====
  const state = ref<CompileState>({
    status: 'idle', // idle | compiling | done | error
    events: [] as SSEEvent[],
    currentVaultId: '',
    currentTopic: '',
    lastError: null as string | null
  });

  // ===== 计算属性 =====
  const isCompiling = computed(() => state.value.status === 'compiling');
  const eventCount = computed(() => state.value.events.length);
  const progressEvents = computed(() =>
    state.value.events.filter(e => e.type === 'progress')
  );

  // ===== SSE 事件处理拆分 =====
  function handleProgressEvent(data: unknown) {
    // 进度事件：更新编译进度
    state.value.status = 'compiling';
    console.log('[compile-store] progress:', data);
  }

  function handleDoneEvent(data: unknown) {
    // 完成事件：重置状态
    state.value.status = 'done';
    state.value.lastError = null;
    console.log('[compile-store] done:', data);
  }

  function handleErrorMessage(data: { message: string }) {
    // 错误事件：记录错误信息
    state.value.status = 'error';
    state.value.lastError = data.message;
    console.error('[compile-store] error:', data.message);
  }

  // ===== Action：消费 SSE 流 =====
  async function startCompile(vaultId: string, topic?: string) {
    // 重置状态
    state.value = {
      status: 'compiling',
      events: [],
      currentVaultId: vaultId,
      currentTopic: topic || '',
      lastError: null
    };

    let abortController: AbortController | null = null;

    try {
      abortController = new AbortController();

      await consumeSSEStream('/api/wiki/compile', { vaultId, topic }, {
        signal: abortController.signal,
        onEvent: (event: SSEEvent) => {
          // 累积事件日志
          state.value.events.push(event);

          // 根据事件类型分发到独立处理器
          switch (event.type) {
            case 'progress':
              handleProgressEvent(event.data);
              break;
            case 'done':
              handleDoneEvent(event.data);
              break;
            case 'error':
              handleErrorMessage(event.data as { message: string });
              break;
          }
        },
        onError: (err: Error) => {
          state.value.status = 'error';
          state.value.lastError = err.message;
        },
        onEnd: () => {
          abortController = null;
        }
      });
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        state.value.status = 'error';
        state.value.lastError = err.message;
      }
    }
  }

  // ===== Action：取消编译 =====
  function cancelCompile() {
    // 注意：实际取消需要外部 AbortController 引用
    state.value.status = 'idle';
    console.log('[compile-store] cancelled');
  }

  // ===== Action：清除状态 =====
  function clearState() {
    state.value = {
      status: 'idle',
      events: [],
      currentVaultId: '',
      currentTopic: '',
      lastError: null
    };
  }

  return {
    // 状态
    state,
    isCompiling,
    eventCount,
    progressEvents,
    // Actions
    startCompile,
    cancelCompile,
    clearState
  };
});
