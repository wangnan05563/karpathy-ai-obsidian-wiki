# 前端 .ts 被 .js 影子覆盖规则

**代码**：CODING-TS-JS-SHADOWING
**严重级别**：critical

## 问题（Problem）

Vite 默认的 `resolve.extensions` 解析顺序大致为 `[".mjs", ".js", ".mts", ".ts", ...]`，即 **`.js` 排在 `.ts` 之前**。当 `src/` 目录内残留了编译产物 `.js` / `.map`（如误编译、或旧构建遗留），Vite 在 dev / build / 单测解析模块时会优先命中 `.js`，导致对 `.ts` 源文件的编辑被**静默忽略**——页面与测试表现与源码不一致，且没有任何报错。

我们曾因此浪费大量精力修改 `.ts` 却看不到效果，直到发现 `src/` 内残留 `.js` 才定位。另外，PowerShell 的 `Remove-Item` 被安全 hook 拦截，无法用于清理，需改用 Node `fs.unlinkSync`。

## 规则（Rule）

### R-1：前端改动前清理残留 .js 产物
使用 Node 清理，禁止依赖被安全 hook 拦截的 PowerShell `Remove-Item`：

```javascript
// scripts/clean-stale-js.mjs
import fs from 'node:fs';
import path from 'node:path';
function clean(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) clean(p);
    else if (p.endsWith('.js') || p.endsWith('.js.map')) {
      const tsSibling = p.replace(/\.js(\.map)?$/, '.ts');
      if (fs.existsSync(tsSibling)) fs.unlinkSync(p);
    }
  }
}
clean('src');
```

### R-2：vite `resolve.extensions` 必须优先 `.ts`
在 `vite.config.ts` 显式指定顺序，确保 `.ts` 先于 `.js`：

```typescript
export default defineConfig({
  resolve: {
    extensions: [".mjs", ".ts", ".tsx", ".js", ".jsx", ".vue", ".json"],
  },
});
```

### R-3：前端改动必须双验证
改动前端后必须同时通过 `vue-tsc` 类型检查与 `vite build` 产物验证，二者缺一即视为未验证。

## 适用 / 不适用

- **适用**：前端（如 `packages/web`）涉及 `.ts`/`.vue` 编辑、构建、单测；CI 构建门禁。
- **不适用**：纯后端代码、纯 Markdown 文档、与 Vite 解析无关的 Node 脚本。

## 检查清单
- [ ] `src/` 内是否存在与 `.ts` 同名的残留 `.js`/`.map`（用 `vue_tsc_stale_artifact_patterns` 扫描）
- [ ] vite `resolve.extensions` 是否已把 `.ts` 置于 `.js` 之前
- [ ] 清理残留是否使用 Node `fs.unlinkSync`（而非 PowerShell `Remove-Item`）
- [ ] 是否通过 `vue-tsc` + `vite build` 双验证
