# Third-Party Error Guard Rule

## 触发关键词
mermaid, 第三方库, error-icon, Syntax error, suppressErrorRendering, parse, 预校验, 库级配置

## 规则

### TP-1：第三方库输出 HTML/SVG 时必须三层错误防护
**严重级别**：critical

当第三方库（如 mermaid.js、KaTeX、Prism.js）直接输出 HTML/SVG 到 DOM 时，必须采用三层错误防护，防止库内部错误渲染机制注入错误元素（如 "Syntax error in text" 图标）污染页面。

**三层防护**：
1. **库级配置**：启用库提供的错误抑制配置（如 mermaid 的 `suppressErrorRendering: true`）
2. **预校验**：渲染前用库的 parse/validate 方法验证输入，失败时跳过渲染并清空容器
3. **CSS 兜底**：用 CSS 隐藏库可能注入的错误元素类（如 `.error-icon` / `.error-text`）

**为什么三层**：库级配置可能因版本变化失效；预校验可能遗漏边界情况；CSS 兜底是最后一道防线。三层叠加才能确保万无一失。

**实现模式**（以 mermaid.js 为例；选择器与方法名从 `config/coding-standards-config.md` 的 `third_party_error_guard` 段读取，禁止在源码硬编码）：
```typescript
// 第 1 层：库级配置（suppress_config_keys 参数）
import { config } from './config';
const suppressKey = config.third_party_error_guard.suppress_config_keys.split(',')[0]; // 默认 suppressErrorRendering
mermaid.initialize({
  startOnLoad: false,
  [suppressKey]: true, // 抑制库内部错误渲染
});

// 第 2 层：预校验（parse_method_names 参数）
async function renderMindmap(content: string, container: HTMLElement) {
  container[config.third_party_error_guard.container_clear_methods.split(',')[0]] = ''; // 渲染前清空容器
  try {
    await mermaid[config.third_party_error_guard.parse_method_names.split(',')[0]](content); // 预校验语法（默认 parse）
    const { svg } = await mermaid.render(id, content);
    container.innerHTML = svg;
  } catch {
    // 校验失败时容器已清空，不渲染错误 SVG；展示用户可读提示（fallback_message 参数）
    container.innerHTML = `<div class="render-fallback">${config.third_party_error_guard.fallback_message}</div>`;
  }
}

// 第 3 层：CSS 兜底（error_css_classes 参数）
/* 隐藏库可能注入的错误元素，选择器来自 config.third_party_error_guard.error_css_classes */
const errorClasses = config.third_party_error_guard.error_css_classes; // 默认 .error-icon,.error-text,.mermaid-error
// 在全局 CSS 中：${errorClasses} { display: none !important; }
```

### TP-2：渲染前必须清空容器
**严重级别**：critical

调用第三方库渲染方法前，必须先清空目标容器（`container.innerHTML = ''`），防止上次渲染的错误 SVG 残留。

**为什么**：库的 `render()` 方法在解析失败时会自动注入错误 SVG，如果不清空容器，错误 SVG 会累积。

### TP-3：库版本升级必须重新验证错误防护
**严重级别**：suggestion

第三方库版本升级后，必须重新验证三层防护是否仍然有效：
1. 库级配置 API 是否变更（如 `suppressErrorRendering` 是否仍存在）
2. parse/validate 方法签名是否变更
3. CSS 错误元素类名是否变更

### TP-4：错误降级必须有用户可读的提示
**严重级别**：suggestion

第三方库渲染失败降级时，必须给用户一个可读的提示（如"图表语法错误，请检查内容"），禁止静默失败显示空白。

### TP-5：LLM 生成内容渲染第三方库前必须预校验
**严重级别**：critical

LLM 生成的内容（如 mermaid mindmap 语法、KaTeX 公式）在交给第三方库渲染前必须预校验。LLM 输出不可信，可能包含语法错误。

**为什么**：历史问题：LLM 生成的 mindmap 内容存在 Mermaid 语法错误，mermaid.render() 解析失败后自动注入 "Syntax error in text" 错误 SVG，用户看到页面底部出现错误图标。

## 适用场景
- 第三方库直接输出 HTML/SVG 到 DOM（mermaid、KaTeX、Prism、chart.js）
- LLM 生成内容交给第三方库渲染
- 库有内部错误渲染机制（可能注入错误元素）

## 不适用场景
- 库输出纯数据（无 DOM 操作）→ 无需 CSS 兜底
- 库错误处理已完备（有明确的 onError 回调）→ 可能无需三层
- 静态内容（非 LLM 生成）→ 预校验可选

## 检查清单
- [ ] 第三方库输出 HTML/SVG 是否三层防护（库级配置 + 预校验 + CSS 兜底）
- [ ] 渲染前是否清空容器
- [ ] 库版本升级后是否重新验证防护
- [ ] 错误降级是否有用户可读提示
- [ ] LLM 生成内容是否预校验后再渲染
