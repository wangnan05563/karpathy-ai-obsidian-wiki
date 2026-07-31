# 第三方重库动态加载规则（CODING-067）

> 复盘来源：v3 媒体生成工具开发中，MultimodalOutputCard.vue 引入 mermaid（~600KB）渲染思维导图、marpit 渲染 PPT、monaco 编辑器等体积大的第三方库。初版用静态 import，导致首屏 bundle 膨胀 1.2MB+；且 mermaid 11.x 在解析失败时注入 error SVG 元素（.error-icon / .error-text），污染 UI。最终方案：动态 import + 模块级加载标志 + 实例缓存 + CJS 命名导出兼容 + 五层错误防护 + 渲染失败降级显示原始内容。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `heavy_library` 字段读取，禁止在规则文件中硬编码体积阈值或选择器。

## 规则

**前端引入体积大的第三方库（mermaid / marpit / monaco 等）必须遵守七项契约**：

1. **动态 import 加载**：体积大的库必须动态 `import()` 加载，避免首屏 bundle 膨胀（阈值 `heavy_library.dynamic_import_threshold_kb`，默认 200KB）
2. **模块级加载标志**：模块级 `xxxLoaded` 标志避免重复加载，已加载的直接返回缓存
3. **实例缓存复用**：实例（如 marpInstance）缓存复用，避免重建
4. **CJS 命名导出兼容**：CJS 模块经 Vite 预构建后命名导出位置不确定，统一用 `mod.X ?? mod.default?.X` 兼容访问，缺失时显式抛错
5. **五层错误防护**：第三方库错误行为不可控时（如 mermaid 11.x 错误 SVG 注入）用多层防护兜底：
   - 第一层：库选项抑制（如 `suppressErrorRendering: true`）
   - 第二层：渲染前 `parse()` 预解析验证
   - 第三层：渲染后清空容器再注入
   - 第四层：catch 中清空容器避免残留
   - 第五层：CSS 全局隐藏库内置错误元素（`heavy_library.error_suppress_selectors`）
6. **降级显示原始内容**：渲染失败时降级显示原始内容（`<pre>{{ raw }}</pre>`），让用户排查 LLM 输出
7. **动态 import + watch 回调中 await nextTick**：动态 import + watch 回调中必须 `await nextTick()` 等 DOM 更新后容器 ref 才可用

## 适用场景

- 前端引入体积大的第三方库（mermaid / marpit / monaco / codemirror / three.js / d3 等）
- LLM 输出渲染场景（mermaid 思维导图 / marp PPT / monaco 代码编辑器）
- 需要五层错误防护的不可控第三方库（库错误行为无法通过 API 抑制）
- CJS 模块经 Vite 预构建后命名导出不确定的场景

## 不适用场景

- 体积小的工具库（如 lodash-es，< 50KB，可静态 import）
- 首屏必需的库（如 Vue / React 框架本身，必须静态 import）
- 仅 SSR 使用的库（无需动态加载，Node.js 直接 require）
- 类型定义文件（.d.ts，仅编译时使用，不影响 bundle）
- 已被框架封装的库（如 Nuxt 的 @nuxt/js modules，框架自动管理加载）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `heavy_library.enabled` | `true` | 是否启用重库动态加载守卫 |
| `heavy_library.severity` | `error` | 违规严重级别 |
| `heavy_library.dynamic_import_threshold_kb` | `200` | 动态加载体积阈值（KB，超过必须动态 import） |
| `heavy_library.error_suppress_selectors` | `.error-icon,.error-text` | 库内置错误元素 CSS 选择器（用 display:none 隐藏） |
| `heavy_library.suppress_option_key` | `suppressErrorRendering` | 库选项抑制键名（mermaid 用 suppressErrorRendering） |
| `heavy_library.fallback_display_tag` | `pre` | 渲染失败降级显示的 HTML 标签 |
| `heavy_library.cache_instance` | `true` | 是否缓存库实例复用 |

## 检查方式

1. **动态 import 检查**：体积 > `dynamic_import_threshold_kb` 的库必须用 `await import('xxx')` 动态加载，禁止静态 `import xxx from 'xxx'`
2. **加载标志检查**：模块级必须有 `xxxLoaded` 标志，已加载时直接返回缓存，避免重复 import
3. **实例缓存检查**：库实例（如 marpInstance）必须缓存复用，禁止每次渲染都 new
4. **CJS 兼容检查**：访问 CJS 模块导出必须用 `mod.X ?? mod.default?.X`，缺失时显式抛错（不用 `mod.X || mod.default.X`，避免 falsy 值误判）
5. **五层防护检查**：不可控库必须实现五层防护（库选项抑制 + parse 预验证 + 渲染前清空 + catch 清空 + CSS 隐藏错误元素）
6. **降级显示检查**：渲染失败必须降级显示原始内容，禁止空白或错误图标
7. **nextTick 检查**：动态 import + watch 回调中必须 `await nextTick()` 后再访问容器 ref

## 正确示例

```typescript
// frontend/src/services/heavy-libraries.ts
import { nextTick } from 'vue';
import { config } from '../config';

const hl = config.heavy_library;

// ✅ 模块级加载标志
let mermaidLoaded: any = null;
let marpLoaded: any = null;
// ✅ 实例缓存
let marpInstance: any = null;

/**
 * 动态加载 mermaid——模块级标志避免重复加载
 * 为什么用模块级标志：动态 import() 返回 Promise，多次调用会重复加载
 * （虽然浏览器有模块缓存，但 Promise 链重复执行初始化逻辑）。
 */
export async function loadMermaid(): Promise<any> {
  if (mermaidLoaded) return mermaidLoaded;

  // ✅ 动态 import
  const mod = await import('mermaid');
  // ✅ CJS 命名导出兼容：mod.X ?? mod.default?.X
  const mermaid = mod.default ?? mod;
  if (!mermaid) {
    throw new Error('mermaid 模块导出缺失：mod.default 与 mod 均为空');
  }

  // ✅ 第一层：库选项抑制错误渲染
  mermaid.initialize({
    startOnLoad: false,
    [hl.suppress_option_key]: true, // suppressErrorRendering: true
  });

  mermaidLoaded = mermaid;
  return mermaid;
}

/**
 * 动态加载 marpit + 实例缓存
 */
export async function loadMarp(): Promise<any> {
  if (marpInstance) return marpInstance;

  const mod = await import('@marp-team/marp-core');
  // ✅ CJS 命名导出兼容
  const Marp = mod.Marp ?? mod.default?.Marp;
  if (!Marp) {
    throw new Error('@marp-team/marp-core 导出缺失：mod.Marp 与 mod.default?.Marp 均为空');
  }

  // ✅ 实例缓存复用
  marpInstance = new Marp();
  return marpInstance;
}
```

```vue
<!-- frontend/src/components/MermaidRenderer.vue -->
<script setup lang="ts">
import { ref, watch, onBeforeUnmount, nextTick } from 'vue';
import { loadMermaid } from '../services/heavy-libraries';
import { config } from '../config';

const hl = config.heavy_library;

const props = defineProps<{ content: string }>();
const containerRef = ref<HTMLDivElement | null>(null);
const renderError = ref(false);

// ✅ 第三层：渲染前清空容器
async function renderMermaid(content: string) {
  if (!containerRef.value) return;

  try {
    const mermaid = await loadMermaid();

    // ✅ 第二层：parse() 预解析验证
    await mermaid.parse(content);

    // ✅ 第三层：渲染前清空容器（避免上一次残留）
    containerRef.value.innerHTML = '';

    // 渲染
    const { svg } = await mermaid.render('mermaid-' + Date.now(), content);
    containerRef.value.innerHTML = svg;
    renderError.value = false;
  } catch (err) {
    // ✅ 第四层：catch 中清空容器避免残留
    if (containerRef.value) {
      containerRef.value.innerHTML = '';
    }
    renderError.value = true;
    console.warn('[mermaid] 渲染失败，降级显示原始内容:', err);
  }
}

// ✅ 动态 import + watch 回调中必须 await nextTick()
watch(() => props.content, async (newContent) => {
  if (!newContent) return;
  // ✅ 等 DOM 更新后容器 ref 才可用
  await nextTick();
  await renderMermaid(newContent);
}, { immediate: true });

onBeforeUnmount(() => {
  // 清空容器避免残留
  if (containerRef.value) {
    containerRef.value.innerHTML = '';
  }
});
</script>

<template>
  <div>
    <!-- ✅ 第五层：CSS 全局隐藏库内置错误元素（在 style 中） -->
    <div ref="containerRef" class="mermaid-container"></div>
    <!-- ✅ 第六层：降级显示原始内容 -->
    <pre v-if="renderError">{{ content }}</pre>
  </div>
</template>

<style>
/* ✅ 第五层：CSS 全局隐藏 mermaid 错误元素 */
/* 用 heavy_library.error_suppress_selectors 配置 */
.error-icon,
.error-text {
  display: none !important;
}
</style>
```

## 错误示例

```typescript
// ❌ 错误：静态 import 重库，首屏 bundle 膨胀
import mermaid from 'mermaid'; // ⚠️ ~600KB 进入首屏 bundle
import Marp from '@marp-team/marp-core'; // ⚠️ ~200KB 进入首屏 bundle

// ❌ 错误：无加载标志，重复加载
async function renderMermaid() {
  const mermaid = await import('mermaid'); // ⚠️ 每次调用都执行 import 链
  mermaid.default.initialize({ startOnLoad: false });
  // ...
}

// ❌ 错误：无实例缓存，每次渲染都 new
async function renderMarp() {
  const mod = await import('@marp-team/marp-core');
  const marp = new mod.Marp(); // ⚠️ 每次渲染都 new，浪费内存
  // ...
}

// ❌ 错误：CJS 命名导出用 || 访问，falsy 值误判
const Marp = mod.Marp || mod.default.Marp;
// ⚠️ 若 Marp 是 0 或空字符串，|| 会取 default.Marp

// ❌ 错误：无五层防护，mermaid 错误 SVG 污染 UI
async function renderMermaid(content: string) {
  const mermaid = await loadMermaid();
  // ⚠️ 缺少 suppressErrorRendering: true
  // ⚠️ 缺少 parse() 预验证
  // ⚠️ 缺少渲染前清空容器
  // ⚠️ 缺少 catch 清空
  // ⚠️ 缺少 CSS 隐藏 .error-icon / .error-text
  const { svg } = await mermaid.render('x', content);
  containerRef.value.innerHTML = svg; // ⚠️ 解析失败时 mermaid 注入错误 SVG
}

// ❌ 错误：渲染失败不降级，UI 空白
catch (err) {
  console.error(err);
  // ⚠️ 缺少降级显示 <pre>{{ raw }}</pre>
}

// ❌ 错误：动态 import + watch 回调中未 await nextTick
watch(() => props.content, async (newContent) => {
  const mermaid = await loadMermaid();
  // ⚠️ 未 await nextTick()，containerRef.value 可能仍为 null
  containerRef.value.innerHTML = ''; // TypeError: Cannot read property 'innerHTML' of null
});
```

## 适配新项目

- 适配 React：用 `useRef` 保存加载标志与实例，`useEffect` 中动态 import，useEffect cleanup 中销毁实例
- 适配 Web Worker：重库加载到 Web Worker 中，主线程 postMessage 通信，避免主线程卡顿
- 适配 SSR：重库在 onMounted（客户端）中加载，SSR 阶段跳过（避免 window undefined）
- 适配 CDN 加载：用 `<script>` 标签从 CDN 加载，window 全局访问，避免打包
- 适配微前端：重库加载到子应用，主应用通过 props 传递实例，避免重复加载

## 与其他规则的关系

- 与 CODING-066（事件委托 + 生命周期清理）联动：本规则的第三方库实例必须在 onBeforeUnmount 销毁
- 与 CODING-063（SSE 事件对象映射分发）联动：重库渲染的 v-html 内容事件委托由 CODING-066 处理
- 与 CODING-027（Composable API 先读后用）联动：调用重库 API 前必须 Read 源码确认其错误行为与销毁方法
- 与 CODING-013（优雅停止）联动：组件卸载时销毁重库实例，避免内存泄漏
- 与项目硬约束（首屏性能）联动：重库动态加载是首屏性能优化的核心手段
