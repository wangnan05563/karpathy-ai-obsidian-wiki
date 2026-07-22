<template>
  <div class="wiki-compile-view">
    <el-card header="Wiki 编译">
      <el-form :model="form" label-width="100px">
        <el-form-item label="Vault ID">
          <el-input v-model="form.vaultId" placeholder="输入 vault UUID" />
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="form.topic" placeholder="可选主题" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startCompile" :loading="compiling">
            开始编译
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 编译进度 -->
      <div v-if="status" class="compile-status">
        <el-alert
          :title="status.title"
          :type="status.type"
          :closable="false"
          show-icon
        />
        <pre v-if="status.output" class="output">{{ status.output }}</pre>
      </div>

      <!-- SSE 事件日志 -->
      <el-collapse v-if="events.length">
        <el-collapse-item title="事件日志">
          <div v-for="(evt, idx) in events" :key="idx" class="event-log">
            <span class="event-type" :class="evt.type">{{ evt.type }}</span>
            <span class="event-time">{{ formatTime(evt.timestamp) }}</span>
            <pre class="event-data">{{ JSON.stringify(evt.data, null, 2) }}</pre>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue';
import { ElMessage } from 'element-plus';
import type { SSEEvent } from '@/types';
import { consumeSSEStream } from '@/api/wiki';

// ===== 状态定义 =====
const form = reactive({
  vaultId: '',
  topic: ''
});

const compiling = ref(false);
const status = ref<{ title: string; type: 'success' | 'warning' | 'error'; output: string } | null>(null);
const events = ref<SSEEvent[]>([]);

let abortController: AbortController | null = null;

// ===== SSE 事件消费 =====
async function startCompile() {
  if (!form.vaultId) {
    ElMessage.warning('请输入 Vault ID');
    return;
  }

  compiling.value = true;
  events.value = [];
  status.value = null;

  // AbortController 用于取消 SSE 连接
  abortController = new AbortController();

  try {
    await consumeSSEStream('/api/wiki/compile', {
      vaultId: form.vaultId,
      topic: form.topic || undefined
    }, {
      signal: abortController.signal,
      onEvent: (event: SSEEvent) => {
        events.value.push(event);

        // 根据事件类型更新状态显示
        switch (event.type) {
          case 'progress':
            status.value = {
              title: '编译中...',
              type: 'info',
              output: JSON.stringify(event.data, null, 2)
            };
            break;
          case 'done':
            status.value = {
              title: '编译完成',
              type: 'success',
              output: JSON.stringify(event.data, null, 2)
            };
            ElMessage.success('编译完成');
            break;
          case 'error':
            status.value = {
              title: '编译失败',
              type: 'error',
              output: JSON.stringify(event.data, null, 2)
            };
            ElMessage.error(event.data.message || '编译出错');
            break;
        }
      },
      onError: (err: Error) => {
        ElMessage.error(`SSE 连接失败: ${err.message}`);
        status.value = {
          title: '连接失败',
          type: 'error',
          output: err.message
        };
      },
      onEnd: () => {
        compiling.value = false;
        abortController = null;
      }
    });
  } catch (err) {
    if (err instanceof Error && err.name !== 'AbortError') {
      ElMessage.error(`编译失败: ${err.message}`);
    }
  }
}

// ===== 生命周期管理 =====
onBeforeUnmount(() => {
  // 组件卸载时关闭 SSE 连接
  if (abortController) {
    abortController.abort();
    abortController = null;
  }
});

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString();
}
</script>

<style scoped>
.compile-status {
  margin-top: 20px;
}
.output {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  font-size: 12px;
}
.event-log {
  margin: 8px 0;
  padding: 8px;
  border-left: 3px solid #409eff;
  background: #fafafa;
}
.event-type {
  font-weight: bold;
  margin-right: 8px;
}
.event-type.progress { color: #409eff; }
.event-type.done { color: #67c23a; }
.event-type.error { color: #f56c6c; }
.event-time {
  color: #909399;
  font-size: 12px;
}
.event-data {
  margin: 4px 0 0 0;
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
