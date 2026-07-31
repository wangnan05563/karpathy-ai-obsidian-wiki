# 第三方重库动态加载（FR-053）

> 复盘来源：v3 媒体生成工具的 MultimodalOutputCard.vue 引入 mermaid（~600KB）、marpit 等 第三方重库，初期用顶层 `import mermaid from 'mermaid'` 静态导入，导致首屏 bundle 膨胀、加载缓慢；后改为动态 `import()` 按需加载 + 模块级 `xxxLoaded` 标志防重复加载 + 实例缓存复用。同时 mermaid 经 Vite 预构建后命名导出位置不确定（`mod.mermaid` vs `mod.default.mermaid`），统一用 `mod.X ?? mod.default?.X` 兼容访问。动态 import + watch 回调中容器 ref 初期为 null（DOM 未更新），后补 `await nextTick()` 等待。
> 所有可变参数从 config/review-config.md 的 `heavy_library_frontend` 字段读取，禁止在规则文件中硬编码库名、阈值或选择器。
> 注意：本规则与 FR-046（第三方库错误防护）互补——FR-046 关注库渲染的错误处理（库级配置 + 预校验 + CSS 兜底），FR-053 关注库的加载方式（动态 import + 标志防重复 + 实例缓存 + CJS 兼容 + nextTick）。

## 规则

### FR-053-1：体积大的库必须动态 import() 加载，禁止顶层静态导入

- **Severity**: critical
- **Description**：体积 ≥ `heavy_library_frontend.dynamic_import_threshold_kb`（默认 200KB）的第三方库必须用动态 `import()` 按需加载，禁止顶层 `import xxx from 'xxx'` 静态导入。原因：静态导入会将库打进首屏 bundle，拖慢首屏加载；动态 import 将库拆为独立 chunk，仅在用时加载，首屏 bundle 显著缩小。需在 `package.json` 的 `dependencies` 中保留库依赖（动态 import 仍需依赖声明），但不在源码顶层 import。
- **判定标准**：检索 `heavy_library_frontend.heavy_libraries`（默认 `mermaid, marpit, monaco, codemirror, chartjs, d3`）中的库，若在 `.vue` / `.ts` 文件顶层用 `import xxx from 'xxx'` 静态导入，即视为违规。修复方式：改为 `const mermaid = await import('mermaid')` 动态加载。

### FR-053-2：模块级 xxxLoaded 标志必须防重复加载，禁止每次调用都 import

- **Severity**: critical
- **Description**：动态 `import()` 加载的库必须用模块级 `xxxLoaded` 标志（或缓存变量）防止重复加载——首次调用 `import()` 后缓存模块实例，后续调用直接返回缓存。原因：虽然 Vite/Webpack 的动态 import 有内部缓存，但每次 `import()` 调用仍会创建微任务 + 模块解析开销；且库初始化（如 `mermaid.initialize()`）应仅执行一次，重复初始化可能抛错或状态错乱。
- **判定标准**：检索动态 `import()` 调用，若无模块级缓存变量（`let mermaidModule: typeof import('mermaid') | null = null`）或加载标志（`let mermaidLoaded = false`），即视为违规。修复方式：`if (!mermaidModule) { mermaidModule = await import('mermaid'); mermaidModule.default.initialize(...) }`。

### FR-053-3：库实例必须缓存复用，禁止每次渲染都重建

- **Severity**: warning
- **Description**：第三方库实例（如 `marpInstance` / `monacoEditor` / `codemirrorEditor`）创建后必须缓存复用，禁止每次渲染（watch 回调 / 事件处理）都 `new` 新实例。原因：库实例创建开销大（解析配置、初始化 DOM、注册事件），重复创建导致性能卡顿；且旧实例未销毁会内存泄漏（参见 FR-052-5）。
- **判定标准**：检索库实例创建代码（`new Marp()` / `monaco.editor.create()` / `Editor.fromTextArea()`），若在 watch 回调或事件处理中调用（无模块级缓存），即视为违规。修复方式：模块级 `let marpInstance: Marp | null = null`，首次创建后缓存，后续直接用 `marpInstance`。

### FR-053-4：CJS 模块经 Vite 预构建后命名导出必须用 mod.X ?? mod.default?.X 兼容访问

- **Severity**: critical
- **Description**：第三方库（尤其 CJS 模块）经 Vite 预构建（`optimizeDeps`）后，命名导出的位置可能不确定——有时在 `mod.X`（具名导出），有时在 `mod.default.X`（默认导出的属性），有时在 `mod.default.default.X`（双重包装）。必须用 `mod.X ?? mod.default?.X` 兼容访问，缺失时显式抛错。原因：Vite 预构建对 CJS 模块的转换策略随版本变化，硬编码 `mod.X` 在某版本可能失效。
- **判定标准**：检索动态 `import()` 后的属性访问，若直接用 `mod.X`（无 `?? mod.default?.X` fallback），即视为违规。修复方式：`const mermaid = mod.mermaid ?? mod.default?.mermaid ?? mod.default; if (!mermaid) throw new Error('mermaid 模块加载失败')`。

### FR-053-5：动态 import + watch 回调中必须 await nextTick() 等 DOM 更新后容器 ref 才可用

- **Severity**: critical
- **Description**：动态 `import()` 加载库后，若在 `watch` 回调中用容器 `ref` 渲染，必须 `await nextTick()` 等待 Vue 完成 DOM 更新后再访问 `ref.value`。原因：watch 回调触发时，依赖变化已发生但 DOM 尚未更新，`ref.value` 可能为 null（v-if/v-show 控制的元素未渲染）；直接访问 `ref.value.innerHTML` 会抛 "Cannot read property of null" 错。
- **判定标准**：检索动态 `import()` + `watch` 组合代码，若 watch 回调中直接访问 `containerRef.value`（无 `await nextTick()`），即视为违规。修复方式：`watch(content, async () => { await import('mermaid'); await nextTick(); const container = containerRef.value; if (!container) return; ... })`。

### FR-053-6：渲染失败必须降级显示原始内容，禁止空白或乱码

- **Severity**: warning
- **Description**：第三方库渲染失败（库抛错 / 内容非法 / 容器缺失）时，必须降级显示原始内容（`<pre>{{ raw }}</pre>` 或纯文本），让用户排查 LLM 输出。禁止留空白容器或乱码 DOM——用户无法判断是渲染失败还是内容为空。与 FR-046-4 互补：FR-046-4 要求错误降级有可读提示，FR-053-6 细化为降级显示原始内容。
- **判定标准**：检索库渲染的 catch 块，若容器清空后无原始内容回填（`container.innerHTML = ''` 后无 `<pre>` 包裹原始文本），即视为违规。修复方式：`catch (e) { container.innerHTML = `<pre>${escapeHtml(raw)}</pre>` }`。

## 适用场景

- Vue 3 / React 项目引入体积大的第三方库（mermaid ~600KB / marpit / monaco editor / codemirror / chartjs / d3 等）。
- LLM 流式输出场景，渲染内容含图表/公式/代码高亮等需重库处理。
- Vite / Webpack 构建的项目，需优化首屏 bundle 体积。
- CJS 模块经构建工具预构建后命名导出位置不确定的场景。

## 不适用场景

- 体积小的库（< 200KB，如 lodash-es / dayjs），静态导入更简洁。
- 首屏必需的库（如 Vue / React / Pinia / 路由库），必须静态导入。
- SSR 场景（服务端无动态 import 需求，库在服务端静态导入）。
- 单元测试中的库导入（测试本身验证库行为，静态导入更直接）。

## 检查流程

```
[开始] 扫描 .vue / .ts 文件中的第三方重库导入
  │
  ▼
[1] 动态 import 检查（FR-053-1）
  │  └─ 检索 heavy_libraries 列表中的库名
  │       └─ 顶层 import xxx from 'xxx' → 标记违规
  │       └─ 动态 import('xxx') → 合规
  │
  ▼
[2] 防重复加载检查（FR-053-2）
  │  └─ 检索动态 import() 调用
  │       └─ 无模块级缓存变量 / 加载标志 → 标记违规
  │
  ▼
[3] 实例缓存检查（FR-053-3）
  │  └─ 检索库实例创建（new Marp / monaco.editor.create）
  │       └─ 在 watch/事件处理中创建且无缓存 → 标记违规
  │
  ▼
[4] CJS 兼容访问检查（FR-053-4）
  │  └─ 检索动态 import() 后的属性访问
  │       └─ 直接 mod.X（无 ?? mod.default?.X）→ 标记违规
  │
  ▼
[5] nextTick 检查（FR-053-5）
  │  └─ 检索动态 import() + watch 组合
  │       └─ watch 回调中直接访问 ref.value（无 await nextTick）→ 标记违规
  │
  ▼
[6] 渲染失败降级检查（FR-053-6）
  │  └─ 检索库渲染的 catch 块
  │       └─ 容器清空后无原始内容回填 → 标记违规
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `heavy_library_frontend.enabled` | `true` | 是否启用重库动态加载审查 |
| `heavy_library_frontend.dynamic_import_threshold_kb` | `200` | 库体积阈值（KB），≥ 此值必须动态 import |
| `heavy_library_frontend.heavy_libraries` | `mermaid, marpit, monaco, codemirror, chartjs, d3, pdfjs, videojs` | 重库清单（逗号分隔，强制动态 import） |
| `heavy_library_frontend.library_module_paths` | `mermaid=mermaid, marpit=@marp-team marp-core, monaco=monaco-editor, codemirror=codemirror, chartjs=chart.js, d3=d3` | 库名 → npm 包名映射（`库名=包名` 格式，逗号分隔） |
| `heavy_library_frontend.require_loaded_flag` | `true` | 是否强制模块级 loaded 标志防重复加载 |
| `heavy_library_frontend.require_instance_cache` | `true` | 是否强制库实例缓存复用 |
| `heavy_library_frontend.cjs_compat_pattern` | `mod.X ?? mod.default?.X` | CJS 模块命名导出兼容访问模式 |
| `heavy_library_frontend.require_next_tick_in_watch` | `true` | watch 回调中是否强制 await nextTick() |
| `heavy_library_frontend.fallback_to_raw_content` | `true` | 渲染失败是否强制降级显示原始内容 |
| `heavy_library_frontend.fallback_tag` | `pre` | 降级显示原始内容的 HTML 标签 |
| `heavy_library_frontend.error_suppress_selectors` | `.error-icon, .error-text` | 库内置错误元素的 CSS 选择器（与 FR-046 共用，全局隐藏） |

## 检查方式

1. **重库导入扫描**：在 `.vue` / `.ts` 文件中检索 `heavy_libraries` 中的库名，定位导入点。
2. **导入方式判定**：对每个导入点，检查是顶层 `import xxx from`（违规）还是 `import('xxx')`（合规）。
3. **防重复加载检查**：检索动态 `import()` 调用，验证是否有模块级缓存变量或 loaded 标志。
4. **实例缓存检查**：检索库实例创建代码（`new Marp()` / `monaco.editor.create()`），验证是否在模块级缓存变量中复用。
5. **CJS 兼容检查**：检索动态 `import()` 后的属性访问，验证是否用 `mod.X ?? mod.default?.X` 模式。
6. **nextTick 检查**：检索动态 `import()` + `watch` 组合，验证 watch 回调中是否有 `await nextTick()`。
7. **降级显示检查**：检索库渲染的 catch 块，验证是否回填原始内容（`<pre>` 包裹）。

## 正确示例

```ts
// ✅ mermaid 动态加载 + 标志防重复 + 实例缓存（FR-053-1/2/3）
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'

// ✅ 模块级缓存变量 + loaded 标志（FR-053-2）
let mermaidModule: typeof import('mermaid') | null = null
let mermaidLoaded = false

// ✅ 库实例缓存复用（FR-053-3，mermaid 无实例但有配置状态）
let mermaidInitialized = false

async function loadMermaid() {
  // ✅ 防重复加载（FR-053-2）
  if (!mermaidLoaded) {
    // ✅ 动态 import（FR-053-1）
    const mod = await import('mermaid')
    // ✅ CJS 兼容访问（FR-053-4）
    const mermaid = mod.mermaid ?? mod.default?.mermaid ?? mod.default
    if (!mermaid) throw new Error('mermaid 模块加载失败')
    mermaidModule = mermaid
    mermaidLoaded = true

    // ✅ 初始化仅执行一次（FR-053-3）
    if (!mermaidInitialized) {
      mermaid.initialize({
        startOnLoad: false,
        suppressErrorRendering: true  // 与 FR-046 共用错误防护
      })
      mermaidInitialized = true
    }
  }
  return mermaidModule!
}
```

```ts
// ✅ marpit 动态加载 + 实例缓存 + CJS 兼容（FR-053-1/3/4）
let marpModule: typeof import('@marp-team/marp-core') | null = null
let marpInstance: any = null  // 缓存实例

async function loadMarp() {
  if (!marpModule) {
    const mod = await import('@marp-team/marp-core')
    // ✅ CJS 兼容：Marp 可能在 mod.Marp / mod.default.Marp / mod.default
    const Marp = mod.Marp ?? mod.default?.Marp ?? mod.default
    if (!Marp) throw new Error('Marp 模块加载失败')
    marpModule = mod

    // ✅ 实例缓存复用（FR-053-3），禁止每次渲染都 new Marp()
    if (!marpInstance) {
      marpInstance = new Marp()
    }
  }
  return marpInstance
}
```

```ts
// ✅ watch 回调中 await nextTick() + 降级显示（FR-053-5/6）
const renderedContent = ref('')
const containerRef = ref<HTMLElement>()
const rawContent = ref('')  // 保存原始内容用于降级

watch(renderedContent, async (newContent) => {
  if (!newContent) return

  // ✅ 动态加载库（FR-053-1）
  const mermaid = await loadMermaid()

  // ✅ await nextTick() 等 DOM 更新后容器 ref 才可用（FR-053-5）
  await nextTick()
  const container = containerRef.value
  if (!container) return  // 容器仍为 null 则跳过

  // 保存原始内容用于降级（FR-053-6）
  rawContent.value = newContent

  try {
    // 渲染前清空容器（与 FR-046-2 共用）
    container.innerHTML = ''
    const { svg } = await mermaid.render(`m-${Date.now()}`, newContent)
    container.innerHTML = svg
  } catch (e) {
    // ✅ 渲染失败降级显示原始内容（FR-053-6）
    container.innerHTML = `<pre>${escapeHtml(rawContent.value)}</pre>`
  }
})

// ✅ onBeforeUnmount 清理库实例（与 FR-052-5 共用）
onBeforeUnmount(() => {
  if (containerRef.value) {
    containerRef.value.innerHTML = ''  // 释放 DOM 引用
  }
})

function escapeHtml(str: string): string {
  return str.replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[c]!)
}
```

## 错误示例

```ts
// ❌ 顶层静态导入重库（FR-053-1 违规）
import mermaid from 'mermaid'  // ❌ 600KB 打进首屏 bundle
import Marp from '@marp-team/marp-core'  // ❌ 重库静态导入

// ❌ 每次调用都 import 无缓存（FR-053-2 违规）
async function renderMermaid(content: string, container: HTMLElement) {
  // ❌ 每次都 import()，虽 Vite 有内部缓存但重复初始化
  const mermaid = await import('mermaid')
  mermaid.default.initialize({ startOnLoad: false })  // ❌ 重复初始化可能抛错
  const { svg } = await mermaid.default.render('m-1', content)
  container.innerHTML = svg
}

// ❌ 实例每次重建（FR-053-3 违规）
watch(content, async (newContent) => {
  // ❌ 每次渲染都 new Marp()，性能卡顿 + 旧实例未销毁泄漏
  const mod = await import('@marp-team/marp-core')
  const marp = new mod.Marp()
  const { html } = marp.render(newContent)
  container.value.innerHTML = html
})

// ❌ 直接 mod.X 无 CJS 兼容（FR-053-4 违规）
async function loadMermaid() {
  const mod = await import('mermaid')
  // ❌ Vite 预构建后 mermaid 可能在 mod.default.mermaid 而非 mod.mermaid
  return mod.mermaid  // ❌ 某版本可能 undefined
}

// ❌ watch 回调中未 await nextTick()（FR-053-5 违规）
watch(content, async (newContent) => {
  const mermaid = await loadMermaid()
  // ❌ 未 await nextTick()，DOM 未更新时 containerRef.value 可能为 null
  const container = containerRef.value
  // ❌ 若 container 为 null，下一行抛 "Cannot read property 'innerHTML' of null"
  container.innerHTML = ''
  const { svg } = await mermaid.render('m-1', newContent)
  container.innerHTML = svg
})

// ❌ 渲染失败留空白（FR-053-6 违规）
try {
  const { svg } = await mermaid.render('m-1', content)
  container.innerHTML = svg
} catch (e) {
  container.innerHTML = ''  // ❌ 留空白，用户无法判断是渲染失败还是内容为空
  console.error(e)
}

// ✅ 正确：降级显示原始内容
catch (e) {
  container.innerHTML = `<pre>${escapeHtml(content)}</pre>`  // ✅ 用户可排查
}
```

## 与其他规则的关系

- **FR-046（第三方库错误防护）**：FR-053 约束库的加载方式（动态 import + 标志防重复 + 实例缓存），FR-046 约束库渲染的错误防护（库级配置 + 预校验 + CSS 兜底）。两者互补：FR-053 管加载生命周期，FR-046 管渲染错误处理。共用的 `error_suppress_selectors` 配置项在两个规则中引用。
- **FR-052（事件委托 + 生命周期清理）**：FR-052-5 约束库实例的销毁（destroy/dispose），FR-053-3 约束库实例的缓存复用。两者共同覆盖第三方库实例的生命周期：FR-053-3 管创建与复用，FR-052-5 管销毁。
- **FR-050-3（finally reader.cancel）**：FR-053-1 的动态 import 与 FR-050 的 SSE 流消费都涉及异步资源管理，但分属不同资源类型（库模块 vs 流 reader）。
- **vue.cleanup_required**：Vue 通用规则要求事件监听器清理，FR-053-2 的 loaded 标志与 vue.cleanup_required 共同确保库资源不泄漏。

## 适配新项目

- **React / Next.js**：`import` 改为 `await import()`；`watch` 改为 `useEffect`；`nextTick` 改为 `flushSync` 或 `await new Promise(r => requestAnimationFrame(r))`；`onBeforeUnmount` 改为 `useEffect` cleanup；动态加载逻辑不变。
- **Vue 2**：`import` 改为 `() => import()`；`watch` 语法不变；`nextTick` 改为 `this.$nextTick`；`onBeforeUnmount` 改为 `beforeDestroy`；动态加载逻辑不变。
- **纯 JavaScript**：去掉框架生命周期，动态 import 与缓存逻辑不变；`nextTick` 改为 `requestAnimationFrame` 或 `setTimeout(0)`。
- **Webpack 项目**：动态 import 语法不变，Vite 预构建改为 Webpack 处理；CJS 兼容访问模式（`mod.X ?? mod.default?.X`）同样适用。
- **Rollup 项目**：动态 import 语法不变，CJS 模块通过 `@rollup/plugin-commonjs` 转换，兼容访问模式同样适用。
- **SSR 项目**：服务端用静态 import（无首屏 bundle 问题），客户端 hydration 后用动态 import 按需加载；`heavy_library_frontend.ssr_static_import` 配置项控制服务端导入方式。
