# 第三方库错误防护三层法（FR-046）

> 复盘来源：Mermaid 渲染含非法语法的流程图时抛出 `Parse error` 未被捕获，整个页面白屏；KaTeX 渲染 LLM 返回的残缺 LaTeX 公式时输出乱码 DOM 节点；Prism 高亮超长代码时性能卡顿无降级。修复方式：库级配置（mermaid `suppressErrorRendering: true` / katex `throwOnError: false` / prism `logErrors: false`）+ 渲染前预校验内容合法性 + CSS 兜底样式（隐藏 `.error` 类 / 容器 `min-height` 占位）三层防护，确保任一层失效仍有兜底。
> 所有可变参数从 config/review-config.md 的 `third_party_error_guard_frontend` 字段读取，禁止在规则文件中硬编码库名、配置键或 CSS 类名。

## 规则

### FR-046-1：库输出 HTML/SVG 必须三层防护

使用 `third_party_error_guard_frontend.libraries`（默认 `mermaid, katex, prism`）中列出的第三方库渲染 HTML/SVG 输出时，必须同时具备以下三层防护：

1. **库级配置层**：库初始化时必须设置 `third_party_error_guard_frontend.suppress_config_keys` 中对应的抑制配置键（如 Mermaid 的 `suppressErrorRendering: true`、KaTeX 的 `throwOnError: false`、Prism 的 `logErrors: false`），禁止使用库的默认抛错行为。
2. **预校验层**：渲染前必须对输入内容做合法性预校验（如正则匹配语法关键字、长度截断、空内容跳过），校验失败直接降级显示原始文本或错误提示，不进入库渲染流程。
3. **CSS 兜底层**：必须为库输出的容器定义 `third_party_error_guard_frontend.error_css_classes`（默认 `.mermaid-error, .katex-error, .prism-error`）中的错误类样式，确保即使库抛错导致 DOM 残缺，也能用 CSS 隐藏错误节点并保留容器占位。

**判定标准**：三层任一缺失即视为违规。修复方式：补齐缺失层；若库本身不支持某层（如 Prism 无 `suppressErrorRendering`），则在 `suppress_config_keys` 中标注 `n/a` 并强化另外两层。

### FR-046-2：渲染前必须清空容器

调用第三方库渲染前，必须清空目标容器的现有内容（`container.innerHTML = ''` 或 `container.replaceChildren()`），禁止在已有 DOM 上追加渲染。原因：

- 库内部维护渲染状态（如 Mermaid 的 `id` 计数器），未清空会导致重复渲染冲突
- 旧内容的 SVG/Canvas 节点会残留，新渲染叠加显示
- LLM 流式输出场景下，每次增量更新必须先清空再渲染，否则 DOM 节点指数级增长

**判定标准**：检索库渲染调用（如 `mermaid.render(...)` / `katex.render(...)` / `Prism.highlightElement(...)`），若其目标容器在调用前未执行清空操作，即视为违规。修复方式：在渲染调用前插入 `container.innerHTML = ''`，或封装统一的 `safeRender(lib, container, content)` 工具函数。

### FR-046-3：库版本升级必须重新验证防护

`package.json` 中 `third_party_error_guard_frontend.libraries` 列出的库版本号变更（major / minor 升级）时，必须重新验证三层防护仍生效：

- 库级配置键名是否变更（如 Mermaid 10.x 将 `suppressErrorRendering` 改为 `suppressErrors`）
- 预校验规则是否仍匹配新版本语法（如 KaTeX 0.16 新增的 `\input` 命令）
- CSS 错误类名是否仍被库输出（如 Prism 1.29 将 `.token.error` 改为 `.error-line`）

**判定标准**：若 PR 的 `package.json` / `pnpm-lock.yaml` 中第三方库版本号变更，且 PR 描述中未贴出三层防护的重新验证截图/日志，即视为违规。修复方式：在 PR 描述中补充"版本升级验证"段，列出三层各自的验证结果。

### FR-046-4：错误降级必须有用户可读提示

当三层防护中任一层触发（库抛错被捕获 / 预校验失败 / CSS 兜底命中），必须向用户提供可读的错误提示，至少满足以下其一：

- 容器内显示错误文案（如 "图表渲染失败，请检查语法" / "公式解析错误"）
- 容器旁显示原始内容（`<pre>` 包裹原始文本，让用户自行判断）
- 触发全局通知（`ElMessage.error` / toast），但必须指明失败的具体库与内容片段

**判定标准**：错误降级后容器为空或仅显示乱码 DOM，即视为违规——用户无法判断是渲染失败还是内容为空。修复方式：在 `catch` 块或预校验失败分支中，向容器写入 `error_css_classes` 对应的错误类节点 + 错误文案。

### FR-046-5：LLM 生成内容渲染前必须预校验

当第三方库渲染的内容来源为 LLM 流式输出（如 ChatGPT/Claude 返回的 Markdown 含 Mermaid 代码块 / LaTeX 公式）时，必须在渲染前调用 `third_party_error_guard_frontend.parse_method_names`（默认 `parseMermaid, parseKatex, parsePrism`）中的预校验方法，对内容做语法合法性检查：

- 检查代码块是否闭合（``` 配对）
- 检查关键语法字符是否成对（如 Mermaid 的 `-->` / KaTeX 的 `$...$`）
- 检查内容长度是否超出阈值（防止超长输入导致库性能崩溃）
- 检查是否含已知非法语法（如 Mermaid 的 `sequenceDiagram` 拼写错误）

**判定标准**：LLM 流式输出直接进入第三方库渲染（无中间预校验步骤），即视为违规——LLM 输出不可控，残缺/非法语法会直接触发库抛错。修复方式：在流式输出接收端与库渲染端之间插入预校验层，校验失败降级为纯文本显示。

## 适用场景

- Vue 3 / React 项目中使用 Mermaid / KaTeX / Prism / Chart.js / D3 等输出 HTML/SVG 的第三方库。
- LLM 流式输出场景（ChatGPT/Claude API 集成），LLM 返回内容含图表/公式/代码高亮。
- 富文本编辑器集成第三方渲染插件（如 Markdown 编辑器 + Mermaid 预览）。
- 知识库 / 文档系统批量渲染用户上传的含图表内容。

## 不适用场景

- 纯文本渲染（无 HTML/SVG 输出的库，如 lodash / dayjs）。
- 服务端渲染（SSR）场景——库错误在服务端捕获，不涉及前端 DOM。
- 静态内容渲染（内容在构建时确定，无运行时风险）。
- 单元测试中的库调用（测试本身即验证库行为，无需三层防护）。
## 检查流程

```
[开始] 扫描 .vue / .ts 文件中的第三方库渲染调用
  │
  ▼
[1] 三层防护完整性检查（FR-046-1）
  │  └─ 检索 libraries 列表中的库导入与调用（mermaid.render / katex.render / Prism.highlight）
  │       └─ 检查 suppress_config_keys 对应配置键是否设置
  │            └─ 未设置 → 标记违规（库级配置层缺失）
  │       └─ 检查渲染前是否有预校验调用（parse_method_names 命中）
  │            └─ 无预校验 → 标记违规（预校验层缺失）
  │       └─ 检查 error_css_classes 是否在全局样式中定义
  │            └─ 未定义 → 标记违规（CSS 兜底层缺失）
  │
  ▼
[2] 容器清空检查（FR-046-2）
  │  └─ 定位库渲染调用的目标容器
  │       └─ 渲染调用前是否有 innerHTML = '' / replaceChildren() / empty()
  │            └─ 未清空 → 标记违规
  │
  ▼
[3] 版本升级验证（FR-046-3）
  │  └─ git diff 中 package.json / pnpm-lock.yaml 的库版本号变更
  │       └─ PR 描述中是否有"版本升级验证"段
  │            └─ 无验证段 → 标记违规
  │
  ▼
[4] 错误降级提示（FR-046-4）
  │  └─ 检查 catch 块与预校验失败分支
  │       └─ 容器是否写入错误文案或 error_css_classes 节点
  │            └─ 无可读提示 → 标记违规
  │
  ▼
[5] LLM 内容预校验（FR-046-5）
  │  └─ 检索 LLM 流式输出（EventSource / fetch stream）与库渲染调用的数据流
  │       └─ 中间是否有 parse_method_names 预校验
  │            └─ 无预校验 → 标记违规（LLM 输出直入库渲染）
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `third_party_error_guard_frontend.enabled` | `true` | 是否启用第三方库错误防护审查 |
| `third_party_error_guard_frontend.libraries` | `mermaid, katex, prism` | 纳入审查的第三方库列表（逗号分隔） |
| `third_party_error_guard_frontend.suppress_config_keys` | `mermaid=suppressErrorRendering:true, katex=throwOnError:false, prism=logErrors:false` | 各库的抑制配置键（`库=键:值` 格式，逗号分隔） |
| `third_party_error_guard_frontend.parse_method_names` | `parseMermaid, parseKatex, parsePrism` | 预校验方法名列表（逗号分隔） |
| `third_party_error_guard_frontend.error_css_classes` | `.mermaid-error, .katex-error, .prism-error` | 错误降级 CSS 类名列表（逗号分隔） |
| `third_party_error_guard_frontend.require_container_clear` | `true` | 是否强制渲染前清空容器 |
| `third_party_error_guard_frontend.container_clear_methods` | `innerHTML='', replaceChildren(), empty()` | 允许的容器清空方式（逗号分隔） |
| `third_party_error_guard_frontend.llm_source_patterns` | `EventSource, fetch(stream), consumeSSEStream, OpenAI, Claude, LLM` | LLM 流式输出源识别关键字（逗号分隔） |
| `third_party_error_guard_frontend.max_content_length` | `10000` | 预校验时内容长度上限（字符数），超过即降级 |
| `third_party_error_guard_frontend.fallback_message` | `渲染失败，请检查内容语法` | 错误降级时的默认用户可读提示文案 |

## 检查方式

1. **Grep 扫描库调用**：在 `.vue` / `.ts` 文件中检索 `libraries` 列表中的库名（`mermaid` / `katex` / `Prism`），定位渲染调用点。
2. **库级配置核对**：检索库初始化代码（`mermaid.initialize(...)` / `katex.render(..., options)` / `Prism.manual = true`），对照 `suppress_config_keys` 验证配置键是否设置。
3. **预校验调用检查**：检索 `parse_method_names` 中的方法名是否在渲染调用前被调用。
4. **CSS 兜底扫描**：在全局样式文件（`*.css` / `*.scss` / `.vue <style>`）中检索 `error_css_classes` 是否定义。
5. **容器清空检查**：对每个库渲染调用，向上回溯 5 行代码，检查是否有 `container_clear_methods` 中的清空操作。
6. **版本变更检测**：对 `git diff` 中的 `package.json` / `pnpm-lock.yaml`，比对 `libraries` 列表中库的版本号变更，要求 PR 描述含验证段。
7. **LLM 源识别**：检索 `llm_source_patterns` 关键字，若命中且数据流向 `libraries` 渲染，强制要求 `parse_method_names` 预校验。
## 正确示例

```ts
// ✅ Mermaid 三层防护 + 容器清空 + LLM 预校验
import mermaid from 'mermaid'
import { parseMermaid } from '@/utils/mermaid-validator'

// ✅ 库级配置层：抑制错误渲染（suppress_config_keys 从 config 读取）
mermaid.initialize({
  startOnLoad: false,
  suppressErrorRendering: true,  // 从 config.third_party_error_guard_frontend.suppress_config_keys
  suppressErrors: true,
})

async function renderMermaid(container: HTMLElement, code: string) {
  // ✅ 渲染前清空容器（FR-046-2）
  container.innerHTML = ''

  // ✅ 预校验层：LLM 内容必须先校验（FR-046-5）
  const validation = parseMermaid(code)
  if (!validation.valid) {
    // ✅ 错误降级有可读提示（FR-046-4）
    container.innerHTML = `<div class="mermaid-error">${validation.message}</div>`
    return
  }

  try {
    const { svg } = await mermaid.render(`m-${Date.now()}`, code)
    container.innerHTML = svg
  } catch (e) {
    // ✅ 错误降级：捕获库抛错，写入 error_css_classes 节点
    container.innerHTML = `<div class="mermaid-error">渲染失败，请检查语法</div>`
  }
}
```

```css
/* ✅ CSS 兜底层：定义 error_css_classes 样式（从 config 读取） */
.mermaid-error,
.katex-error,
.prism-error {
  padding: 12px;
  border: 1px dashed var(--accent-cyan-a30);
  border-radius: 6px;
  background: var(--accent-pink-a08);
  color: var(--text-muted);
  font-family: monospace;
  font-size: 13px;
  min-height: 40px;  /* 容器占位，防止塌陷 */
}
```

## 错误示例

```ts
// ❌ 无库级配置 + 无预校验 + 无容器清空 + 无错误降级（FR-046-1/2/4/5 全违规）
import mermaid from 'mermaid'

function renderMermaid(container: HTMLElement, code: string) {
  // ❌ 未调用 mermaid.initialize 设置 suppressErrorRendering
  // ❌ 未清空容器（FR-046-2），旧 SVG 残留
  // ❌ 未预校验 LLM 内容（FR-046-5），非法语法直接进库
  mermaid.render('m-1', code).then(({ svg }) => {
    container.innerHTML = svg
  }).catch(e => {
    // ❌ catch 块未写入可读提示，容器为空（FR-046-4 违规）
    console.error(e)
  })
}
```

```ts
// ❌ 版本升级未重新验证防护（FR-046-3 违规）
// package.json: "mermaid": "10.9.0" → "11.0.0"（major 升级）
// PR 描述未含"版本升级验证"段
// 风险：mermaid 11.x 的 suppressErrorRendering 键名可能已变更
```

```vue
<!-- ❌ LLM 流式输出直接进 Mermaid 渲染（FR-046-5 违规） -->
<template>
  <div ref="container" class="mermaid-output"></div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import mermaid from 'mermaid'

const props = defineProps<{ llmStreamChunk: string }>()
const container = ref<HTMLElement>()

// ❌ watch LLM 流式 chunk 直接拼接到 mermaid 渲染，无预校验
watch(() => props.llmStreamChunk, (chunk) => {
  if (container.value) {
    // ❌ LLM 输出不可控，残缺语法直接触发 mermaid 抛错
    mermaid.render('m-stream', chunk).then(({ svg }) => {
      container.value.innerHTML = svg
    })
  }
})
</script>
```

## 与其他规则的关系

- **FR-045（控件分层）**：当第三方库渲染区域位于折叠面板内时，FR-045-2 约束面板 DOM 位置，FR-046 约束库渲染防护，两者共同确保面板内库渲染不崩溃。
- **FR-047（折叠面板事件冲突）**：第三方库输出的 SVG/Canvas 节点可能捕获鼠标事件，与 FR-047 的 click outside 监听冲突；FR-046-2 的容器清空可避免旧节点残留。
- **AR-1~AR-4（Async 可靠性）**：第三方库渲染通常为异步操作，FR-046-1 的库级配置与 AR-1 的超时控制互补——库抛错由 FR-046 捕获，库卡死由 AR-1 超时兜底。
- **ES-6（编码损坏扫描）**：第三方库输出的乱码 DOM 节点可能含 U+FFFD 字符，FR-046-4 的错误降级提示须避免输出乱码。

## 适配新项目

- **React / Next.js**：`mermaid.initialize` 在 `useEffect` 中调用；`container.innerHTML = ''` 改为 `ref.current.replaceChildren()`；`error_css_classes` 仍用全局 CSS 或 CSS-in-JS 定义。
- **Vue 2**：`mermaid.render` 在 `mounted` 钩子调用；`watch` 改为 `watch: { llmStreamChunk: { handler, immediate: true } }`；其余规则不变。
- **Chart.js / D3**：`libraries` 配置追加 `chartjs, d3`；`suppress_config_keys` 追加 `chartjs=responsive:false, d3=selection.on:null`；`parse_method_names` 追加 `parseChartConfig, parseD3Data`。
- **纯 JavaScript（无框架）**：用原生 `try/catch` 包裹库调用；`addEventListener` 监听 LLM 流式输出后调用预校验；其余规则不变。
- **SSR 场景**：服务端渲染时库抛错在服务端捕获，前端仅需 CSS 兜底层 + 错误降级提示，库级配置与预校验在服务端执行。