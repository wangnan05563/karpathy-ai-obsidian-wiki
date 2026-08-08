# Rule Catalog — TS/JS Shadowing (Vite)

前端 `.js` 遮蔽 `.ts` 审查规则：确保 `src/` 下不存在已编译的 `.js` / `.map`，Vite 的 `resolve.extensions` 优先解析 `.ts`，避免 `.ts` 修改静默不生效。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

> 复盘来源：Vite 默认 `resolve.extensions` 中 `.js` 排在 `.ts` 之前。当 `src/` 下残留编译产物 `.js`（及 `.js.map`）时，导入 `./foo` 会先命中 `foo.js` 而非 `foo.ts`，导致开发者修改 `.ts` 后构建/运行仍用旧 `.js`，出现"改了代码不生效"的幽灵现象。须从源头禁止 `.js` 进入 `src/` 并用 vue-tsc + vite build 验证。

## Scope
- Covers: `frontend/src/**/*.js`、`frontend/src/**/*.js.map`、`vite.config.ts` 的 `resolve.extensions`、构建/类型检查验证步骤。
- Does NOT cover: 第三方依赖 `node_modules/` 下的 `.js`、构建产物 `dist/` 下的 `.js`（这些由 gitignore 处理）。

## Rules

### FR-061-1: src/ 下禁止存在已编译的 .js / .map（.ts 优先解析）

IsUrgent: True
Category: TS/JS Shadowing

#### Description

Vite 解析模块时按 `resolve.extensions` 顺序尝试扩展名。默认 `.js` 在 `.ts` 之前，因此 `src/` 下若同时存在 `foo.ts` 与 `foo.js`，`import './foo'` 会加载 `foo.js`。一旦编译产物残留，`.ts` 的修改永远不会被使用，问题极难排查。必须在评审中确认：`src/` 下无 `.js` / `.js.map`（除非是合法的、被显式引用的库入口）；如有，须清理并加入清理清单（`*.tsbuildinfo, node_modules/.vite, src/**/*.js`，见 FR-026）。

#### Suggested Fix

- 在 `frontend/` 根 `tsconfig.json` 设 `"noEmit": true` 或仅用 vue-tsc 做类型检查，不在 `src/` 内产出 `.js`。
- 在 pre-commit / CI 增加检查：`git ls-files 'frontend/src/**/*.js' 'frontend/src/**/*.js.map'` 必须为空。
- 清理命令：`Remove-Item frontend/src/**/*.js, frontend/src/**/*.js.map -Force`（Windows）或 `find frontend/src -name '*.js' -delete`。

> **示例代码**: 见 typecheck-cache-frontend-rule.md 的 `cache_cleanup_targets`（FR-026）与 type-safety-rule.md 的 vue-tsc 幽灵错误段。

### FR-061-2: vite.config 的 resolve.extensions 须将 .ts 置于 .js 之前

IsUrgent: True
Category: TS/JS Shadowing

#### Description

即便 `src/` 已无 `.js`，仍应在 `vite.config.ts` 显式配置 `resolve.extensions`，把 `'.ts'` / `'.tsx'` 放在 `'.js'` / `'.jsx'` 之前（或仅保留 TS 扩展名），从配置层面杜绝 `.js` 优先。评审时确认：`vite.config.ts` 中存在 `resolve.extensions` 且 TS 扩展名排序在 JS 之前；未配置则视为潜在隐患。

#### Suggested Fix

```ts
// vite.config.ts
export default defineConfig({
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'] // ✅ .ts 在 .js 之前
  }
})
```

> **示例代码**: 见 type-safety-rule.md 类型检查相关段。

### FR-061-3: 修改后以 vue-tsc + vite build 验证 .ts 真实生效

IsUrgent: False
Category: TS/JS Shadowing

#### Description

仅靠编辑器提示无法确认 `.ts` 修改被真正使用。评审建议（suggestion 级）：变更涉及 `src/` 下 TS 文件时，运行 `vue-tsc --noEmit` 做类型检查 + `vite build` 做真实构建，确认无"修改未生效"类幽灵问题；若 CI 已含这两步则视为满足。作用同 FR-026 的"清缓存后重跑验证"。

#### Suggested Fix

```bash
# 验证 .ts 修改真实生效
npx vue-tsc --noEmit && npx vite build
```

> **示例代码**: 见 typecheck-cache-frontend-rule.md（FR-026）recheck_after_clean 段。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ts_js_shadowing_frontend.enabled` | `true` | 启用本组规则（FR-061） |
| `ts_js_shadowing_frontend.severity_br061_1` | `critical` | FR-061-1 src/ 残留 .js/.map 违规级别 |
| `ts_js_shadowing_frontend.severity_br061_2` | `critical` | FR-061-2 resolve.extensions 顺序违规级别 |
| `ts_js_shadowing_frontend.severity_br061_3` | `suggestion` | FR-061-3 验证步骤违规级别 |
| `ts_js_shadowing_frontend.src_glob` | `frontend/src/**` | 受管控源码目录 |
| `ts_js_shadowing_frontend.forbidden_extensions` | `*.js,*.js.map` | 禁止出现在 src/ 的扩展名 |
| `ts_js_shadowing_frontend.typecheck_command` | `vue-tsc --noEmit` | 类型检查命令 |
| `ts_js_shadowing_frontend.build_command` | `vite build` | 构建命令 |
