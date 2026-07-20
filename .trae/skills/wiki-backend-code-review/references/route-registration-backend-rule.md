# Rule Catalog — 后端路由注册守卫

## Scope

- Covers: 后端新增 `routes/*.ts` 文件时是否在入口文件（如 `index.ts`）同步导入与注册。
- 适用对象：所有手动注册路由的框架（Fastify / Express / Koa）的入口文件与 `routes/` 目录下路由文件。
- Does NOT cover: NestJS 等基于装饰器自动发现路由的框架（路由由反射机制注册，无需手动调用）。

> 所有路径、入口文件名、注册函数名、豁免列表均从 [config/review-config.md](../config/review-config.md) 的"后端路由注册守卫参数"节读取，本规则文件不硬编码任何具体值。

## Rules

### RR-1 新增路由文件必须在入口文件同步导入与注册

- Category: correctness
- Severity: critical
- Description: 手动注册路由的框架（Fastify / Express）下，新增 `routes/*.ts` 文件若仅创建文件却忘记在入口文件（如 `index.ts`）`import` 并调用注册函数（如 `register(app)`），路由实际不会挂载，前端调用对应路径会得到 404，且无任何编译期错误提示，问题往往在联调时才暴露。评审时必须对比 `routes/` 目录下所有路由文件与入口文件中的注册调用，存在差异即视为不通过。
- Judgment logic:
  1. 用 `Glob routes/*.ts` 列出所有路由文件（去除 `exempt_files` 中登记的豁免文件）。
  2. 用 `Grep` 在 `entry_file` 中搜索 `register_function_pattern`（默认 `register`）的调用，提取已注册的路由模块。
  3. 对比两组文件名集合，未在入口文件中导入或未调用注册函数的路由文件即为缺陷。
- Applicable scenarios: Fastify / Express / Koa 等手动注册路由的框架；新增或删除路由文件时；评审 PR 中出现 `routes/*.ts` 新增项时。
- Not applicable: NestJS 等基于装饰器与反射自动发现路由的框架；单体脚本（无路由目录划分）；测试目录下的 mock 路由文件。
- Configuration parameters: 见 [config/review-config.md](../config/review-config.md) 的"后端路由注册守卫参数"节——`route_directory` / `entry_file` / `register_function_pattern` / `exempt_files`。
- Suggested fix: 在入口文件顶部 `import` 路由模块，在 `register` 阶段调用注册函数；建立"目录扫描 + 入口校验"的自动化检查，CI 阶段拦截未注册路由。
- Example:
  - Bad:
    ```typescript
    // routes/ai.ts 已新建
    export function registerAiRoutes(app: FastifyInstance): void {
      app.post('/api/ai/run', /* ... */);
    }

    // routes/cleanup.ts 已新建
    export function registerCleanupRoutes(app: FastifyInstance): void {
      app.post('/api/cleanup', /* ... */);
    }

    // index.ts —— 只注册了旧路由，新增的 ai/cleanup 忘记注册
    import { registerRunRoute } from './routes/run.js';
    registerRunRoute(app);
    // 前端调用 /api/ai/run 与 /api/cleanup 返回 404
    ```
  - Good:
    ```typescript
    // index.ts —— 新增路由文件后同步导入与注册
    import { registerRunRoute } from './routes/run.js';
    import { registerAiRoutes } from './routes/ai.js';
    import { registerCleanupRoutes } from './routes/cleanup.js';

    registerRunRoute(app);
    registerAiRoutes(app);
    registerCleanupRoutes(app);
    ```
- Checklist:
  - [ ] `routes/` 目录下所有非豁免路由文件均在入口文件中被 `import`。
  - [ ] 每个 `import` 的路由模块都在入口文件中调用了注册函数（匹配 `register_function_pattern`）。
  - [ ] 路由注册函数签名与 [route-design-rule.md](route-design-rule.md) 的统一签名约定一致。
  - [ ] 豁免文件（如 `routes/_types.ts` / `routes/_shared.ts`）在 `exempt_files` 中显式登记。
- Related rules: 路由注册函数签名统一见 [route-design-rule.md](route-design-rule.md) 的"路由注册函数签名须统一为 (app, adapter) => void"。
