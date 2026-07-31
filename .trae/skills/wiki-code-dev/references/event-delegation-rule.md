# 事件委托 + 生命周期清理规则（CODING-066）

> 复盘来源：v3 媒体生成工具开发中，MultimodalOutputCard.vue 用 v-html 渲染 LLM 生成的 Markdown（含 mermaid / marp），需为渲染后的 DOM 元素绑定点击事件（如折叠/展开代码块、复制代码）。直接在 v-html 内容中绑定 Vue 事件无效（Vue 无法解析 v-html 内的指令），改用父容器 addEventListener 事件委托。同时发现组件卸载时未清理 addEventListener 与第三方库实例，导致内存泄漏。
> 本规则为行为规则，无可变参数，所有逻辑为运行时约定。

## 规则

**Vue 3 中 v-html 渲染内容的事件绑定 + 组件卸载清理必须遵守五项契约**：

1. **事件委托**：v-html 渲染的 DOM 无法绑定 Vue 事件，统一用父容器 `addEventListener` 事件委托
2. **命中目标元素**：按 `target.tagName` / `target.closest(selector)` 命中目标元素，避免每个子元素单独绑定
3. **保存函数引用**：onBeforeUnmount 必须移除所有 `addEventListener` 注册的监听器，函数引用需保存（禁止用匿名函数）
4. **全局事件配对移除**：全局事件（`globalThis.addEventListener`）必须配对 `globalThis.removeEventListener`
5. **第三方库实例销毁**：第三方库实例（mermaid/marp）必须在 onBeforeUnmount 调用其 destroy/dispose 方法（若存在）

## 适用场景

- Vue 3 中 v-html 渲染内容的事件绑定（Markdown / 富文本 / LLM 输出）
- 用 addEventListener 注册事件的组件（需在卸载时清理）
- 使用第三方库实例的组件（mermaid/marp/monaco/codemirror 等）
- 注册全局事件的组件（resize/scroll/keydown 等）

## 不适用场景

- Vue 模板中的原生事件绑定（用 @click 等指令，Vue 自动清理）
- React 组件（用 useEffect cleanup，无需手动 removeEventListener）
- 一次性事件监听（`{ once: true }`，自动移除）
- 纯展示组件（无事件绑定，无第三方库实例）

## 关键参数

本规则为行为规则，无可变参数。所有逻辑为运行时约定：
- 事件委托：父容器 `addEventListener` + `target.closest(selector)`
- 函数引用保存：`const handleClick = (...) => {}` + `addEventListener('click', handleClick)` + `removeEventListener('click', handleClick)`
- 全局事件配对：`globalThis.addEventListener` 与 `globalThis.removeEventListener` 必须用同一函数引用
- 第三方库销毁：`if (instance.destroy) instance.destroy()` 或 `if (instance.dispose) instance.dispose()`

## 检查方式

1. **事件委托检查**：v-html 渲染内容的点击/键盘事件必须用父容器 `addEventListener` 委托，禁止尝试在 v-html 内容中绑定 Vue 事件
2. **命中目标检查**：事件处理函数必须用 `target.closest(selector)` 命中目标元素，禁止遍历子元素逐个绑定
3. **函数引用检查**：addEventListener 与 removeEventListener 必须用同一函数引用，禁止匿名函数
4. **全局事件配对检查**：`globalThis.addEventListener` 必须在 onBeforeUnmount 配对 `globalThis.removeEventListener`
5. **第三方库销毁检查**：第三方库实例必须在 onBeforeUnmount 调用 destroy/dispose，且检查方法存在

## 正确示例

```vue
<!-- frontend/src/components/MultimodalOutputCard.vue -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';

const containerRef = ref<HTMLDivElement | null>(null);
let mermaidInstance: any = null;

// ✅ 保存函数引用，便于 removeEventListener
const handleClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  // ✅ 用 closest 命中目标元素
  const codeBlock = target.closest('.code-block-header');
  if (codeBlock) {
    codeBlock.parentElement?.classList.toggle('collapsed');
    return;
  }
  const copyBtn = target.closest('.copy-button');
  if (copyBtn) {
    const code = copyBtn.previousElementSibling?.textContent || '';
    navigator.clipboard.writeText(code);
    return;
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    containerRef.value?.blur();
  }
};

const handleResize = () => {
  // 窗口大小变化时重新渲染 mermaid
  if (mermaidInstance) {
    renderMermaid();
  }
};

onMounted(async () => {
  await nextTick();

  // ✅ 事件委托：父容器 addEventListener
  containerRef.value?.addEventListener('click', handleClick);
  containerRef.value?.addEventListener('keydown', handleKeydown);

  // ✅ 全局事件配对 addEventListener
  globalThis.addEventListener('resize', handleResize);

  // ✅ 第三方库实例化
  const mermaid = await import('mermaid');
  mermaidInstance = mermaid.default ?? mermaid;
  mermaidInstance.initialize({ startOnLoad: false });
});

// ✅ 生命周期清理：卸载时移除所有监听器 + 销毁第三方库实例
onBeforeUnmount(() => {
  // ✅ 移除事件委托监听器（用同一函数引用）
  containerRef.value?.removeEventListener('click', handleClick);
  containerRef.value?.removeEventListener('keydown', handleKeydown);

  // ✅ 全局事件配对 removeEventListener
  globalThis.removeEventListener('resize', handleResize);

  // ✅ 第三方库实例销毁（检查方法存在）
  if (mermaidInstance) {
    if (typeof mermaidInstance.destroy === 'function') {
      mermaidInstance.destroy();
    } else if (typeof mermaidInstance.dispose === 'function') {
      mermaidInstance.dispose();
    }
    mermaidInstance = null;
  }
});

const renderedContent = ref('');
</script>

<template>
  <!-- v-html 渲染 LLM 输出，事件通过父容器委托 -->
  <div
    ref="containerRef"
    class="multimodal-output"
    v-html="renderedContent"
    tabindex="0"
  ></div>
</template>
```

## 错误示例

```vue
<!-- ❌ 错误：v-html 内容中尝试绑定 Vue 事件（无效） -->
<template>
  <div v-html="content"></div>
</template>
<!-- content 中含 <button @click="handle">点击</button> -->
<!-- ⚠️ Vue 无法解析 v-html 内的指令，@click 不生效 -->

<script setup>
// ❌ 错误：addEventListener 用匿名函数，无法 removeEventListener
onMounted(() => {
  containerRef.value?.addEventListener('click', (event) => { // ⚠️ 匿名函数
    // ...
  });
});
onBeforeUnmount(() => {
  // ⚠️ 无法移除匿名函数，内存泄漏
  containerRef.value?.removeEventListener('click', ???);
});
</script>

<script setup>
// ❌ 错误：全局事件未配对 removeEventListener
onMounted(() => {
  globalThis.addEventListener('resize', handleResize); // ⚠️ 无对应 removeEventListener
});
onBeforeUnmount(() => {
  // ⚠️ 缺少 globalThis.removeEventListener('resize', handleResize)
});
</script>

<script setup>
// ❌ 错误：第三方库实例未销毁
onMounted(async () => {
  const mermaid = await import('mermaid');
  mermaidInstance = mermaid.default ?? mermaid;
  mermaidInstance.initialize({ startOnLoad: false });
});
onBeforeUnmount(() => {
  // ⚠️ 缺少 mermaidInstance.destroy() / dispose()
});
</script>

<script setup>
// ❌ 错误：遍历子元素逐个绑定事件
onMounted(() => {
  const blocks = containerRef.value?.querySelectorAll('.code-block-header');
  blocks?.forEach(block => {
    block.addEventListener('click', () => { // ⚠️ 逐个绑定 + 匿名函数
      block.parentElement?.classList.toggle('collapsed');
    });
  });
});
// ⚠️ 子元素动态变化时需重新绑定，且无法 removeEventListener
</script>
```

## 适配新项目

- 适配 React：用 useEffect 注册事件，useEffect cleanup 函数中 removeEventListener；第三方库实例用 useRef 保存
- 适配原生 JS：用 CustomEvent + dispatchEvent 替代事件委托，组件卸载时 dispatch('unmount') 通知清理
- 适配 Shadow DOM：事件委托到 Shadow DOM 宿主元素，用 `event.composedPath()` 跨 Shadow DOM 边界
- 适配 jQuery：用 `.on('click', selector, handler)` 事件委托，`.off('click', handler)` 移除
- 适配无第三方库场景：本规则第 5 项可省略，仅保留前 4 项

## 与其他规则的关系

- 与 CODING-067（第三方重库动态加载）联动：本规则的第三方库实例销毁针对动态加载的库
- 与 CODING-065（长任务轮询 UI 模式）联动：长任务 UI 组件的 onBeforeUnmount 清理属于本规则的一部分
- 与 CODING-064（SSE 流消费错误处理）联动：SSE 流消费组件卸载时需 abort 进行中的流，属于本规则的生命周期清理
- 与 CODING-013（优雅停止）联动：组件卸载时的资源清理属于优雅停止的前端版
- 与 CODING-027（Composable API 先读后用）联动：调用第三方库的 destroy/dispose 前必须 Read 源码确认方法存在
