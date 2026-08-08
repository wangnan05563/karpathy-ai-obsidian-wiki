# SPA 部署完整性（前端视角）

> 后端实时部署解析规则（wiki-code-dev `spa-live-deploy-rule.md` / 后端 BR-071）的前端对应规则。
> 关注点：前端构建产物如何落盘、部署脚本如何写目录、产物完整性如何被后端门禁识别。**前端不得假设"构建结束即可服务"**，且构建配置不得硬编码触发 safe-delete 钩子 / 残留旧产物的原地覆盖。
> 所有参数见 [config/review-config.md](../config/review-config.md) 的 `spa_live_deploy_frontend.*` 段。

## 触发场景

- 评审 `vite.config.ts` 的 `build.outDir` / `emptyOutDir` 配置
- 评审部署脚本（`_deploy_live*.mjs` / `build*.ps1` / `build*.sh`）是否写全新时间戳目录、是否产出完整性标记
- 评审前端验证链（FR-061 / 第三轮）构建后是否校验产物完整

## 规则

### FR-068-1：构建输出目录须可被部署流程参数化为「全新时间戳目录」（建议级）

`vite.config.ts` 的 `build.outDir` 不应硬编码为固定 `../api/public` 并依赖 `emptyOutDir: true` 原地清空覆盖——该模式会：① 触发 WorkBuddy safe-delete 钩子的 overwrite 拦截导致构建失败；② 清空正在服务的目录造成瞬时 404；③ 残留旧 hash 产物（若清空不彻底）。部署脚本应把构建产物写入**全新 `public_live_<ts>` 目录**，整目录 create + write。

```typescript
// 合规示例：outDir 由部署脚本注入（环境变量 / CLI 参数），不写死固定路径
import { defineConfig } from 'vite';
export default defineConfig({
  build: {
    outDir: process.env.BUILD_OUT_DIR ?? '../api/public', // 部署时注入 public_live_<ts>
    emptyOutDir: true, // 仅对新目录生效，不触碰在服目录
  },
});
```

**违规示例**：`build.outDir` 固定 `../api/public` 且部署直接覆盖该目录——与后端 BR-071-4 / safe-delete 约束冲突。

### FR-068-2：部署须产出「最后写入」的完整性标记（Critical）

部署脚本写完构建产物后，须**最后**写入完整性标记（如 `.deploy-complete`），供后端 `isDeployComplete` 门禁（`index.html` + 标记）识别产物完整。前端 / 部署脚本不得假设"vite build 进程退出即产物完整可服务"——hash bundle 可能晚于 `index.html` 落地。

### FR-068-3：前端验证链构建后须校验产物完整（建议级）

沿用第三轮前端验证链（清 stale `.js` → vue-tsc → vite build）：构建后除类型检查通过外，须校验产物目录存在 `index.html` + 关键 JS bundle（`build_artifact_check` 思路），避免"类型检查通过但产物残缺"被误判为成功。

## 检测方法

1. 扫描 `vite.config.ts`，确认 `build.outDir` 可被部署注入 / 不为固定原地覆盖路径。
2. 扫描部署脚本，确认写入**全新时间戳目录**、不覆盖已存在目录、写完写 `.deploy-complete` 标记。
3. 确认前端验证链构建后校验产物完整性（index.html + bundle），而非仅 vue-tsc。

## 配置参数

所有参数见 [config/review-config.md](../config/review-config.md) 的 `spa_live_deploy_frontend.*` 段（enabled / out_dir_env_key / live_dir_pattern / complete_marker / require_fresh_dir / require_marker）。

## 适配说明

- 固定单目录部署（无时间戳切换）：FR-068-1 放宽，但仍须 `emptyOutDir` + 不残留旧产物（对应后端 SH-3）。
- 多端口 / nginx / CDN 托管前端：本规则不适用（部署由外部设施处理）。
- SSR 应用：不适用（无静态 bundle 目录）。
