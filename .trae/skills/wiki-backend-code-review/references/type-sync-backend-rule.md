# Rule Catalog — 类型同步守卫

## Scope

- Covers: 后端 `types.ts` 新增/修改 `export interface` 时，前端 `types.ts` 必须同步对应类型，保持字段名与类型一致。
- 适用对象：全栈 TypeScript 项目中后端 `src/types.ts` 与前端 `src/types.ts`（或对应路径）的 `export interface` 定义。
- Does NOT cover: 后端独立运行无前端的项目；GraphQL 自动生成类型的项目（类型由 schema 生成，无需手动同步）；前端独有的 UI 类型（如组件 Props）。

> 所有后端/前端 types 文件路径、需同步的接口名列表均从 [config/review-config.md](../config/review-config.md) 的"类型同步守卫参数"节读取，本规则文件不硬编码任何具体值。

## Rules

### TS-1 后端 types.ts 新增 interface 必须在前端 types.ts 同步

- Category: maintainability
- Severity: critical
- Description: 全栈 TypeScript 项目中，后端 `types.ts` 定义 API 请求/响应的契约，前端 `types.ts` 引用相同类型进行编译期校验。若后端新增 interface 或修改字段而前端未同步，前端编译不会报错（因类型独立解析），但运行时调用 API 会因字段不匹配而出现 `undefined` 字段、类型断言失败、表单提交缺字段等问题，且难以定位。评审时必须对比两侧 `export interface` 列表与字段定义，差异即视为不通过。
- Judgment logic:
  1. 用 `Read` 读取 `backend_types_path`（默认 `src/types.ts`）的 `export interface` 列表与字段定义。
  2. 用 `Read` 读取 `frontend_types_path`（默认 `../../frontend/src/types.ts`）的 `export interface` 列表与字段定义。
  3. 若 `sync_interfaces` 配置非空，仅校验该列表中的接口；否则校验全部 `export interface`。
  4. 对比字段名与类型签名——后端新增 interface 前端缺失、字段名不一致、可选性不一致（`?` 缺失）、类型不一致（`string` vs `string | null`）均视为缺陷。
  5. 建议但非强制：前端可仅同步"请求/响应契约"接口，内部辅助类型可不同步——若 `sync_interfaces` 已显式列出需同步接口则按列表，否则全部校验。
- Applicable scenarios: 全栈 TypeScript 项目（后端 Node + 前端 React/Vue）；API 契约由 `types.ts` 单向定义（后端定义、前端引用）；新增接口或修改字段时；评审 PR 中出现 `types.ts` 改动时。
- Not applicable: 后端独立运行无前端的项目；GraphQL 自动生成类型（由 schema 生成器保证一致）；前端独有的 UI 类型（组件 Props、样式类型）；后端内部接口（不暴露给前端）。
- Configuration parameters: 见 [config/review-config.md](../config/review-config.md) 的"类型同步守卫参数"节——`backend_types_path` / `frontend_types_path` / `sync_interfaces`。
- Suggested fix: 在 PR 模板中加"前后端 types.ts 是否同步"检查项；建立 `npm run check:types-sync` 脚本对比两侧 interface；考虑用 `import type` 直接从前端引用后端类型（若构建工具支持跨包引用）。
- Example:
  - Bad:
    ```typescript
    // api/src/types.ts —— 后端新增 ConversationMeta
    export interface ConversationMeta {
      id: string;
      title: string;
      updatedAt: string;
      tokenCount: number; // 新增字段
    }

    // frontend/src/types.ts —— 前端未同步，tokenCount 缺失
    export interface ConversationMeta {
      id: string;
      title: string;
      updatedAt: string;
      // 前端编译不报错，但访问 meta.tokenCount 得到 undefined
    }
    ```
  - Good:
    ```typescript
    // api/src/types.ts —— 后端新增字段
    export interface ConversationMeta {
      id: string;
      title: string;
      updatedAt: string;
      tokenCount: number;
    }

    // frontend/src/types.ts —— 前端同步新增字段
    export interface ConversationMeta {
      id: string;
      title: string;
      updatedAt: string;
      tokenCount: number; // 与后端字段名/类型一致
    }
    ```
- Checklist:
  - [ ] 后端 `types.ts` 的所有 `export interface`（或 `sync_interfaces` 列表中的接口）在前端 `types.ts` 中存在。
  - [ ] 字段名、类型签名、可选性（`?`）两侧一致。
  - [ ] 后端新增字段时，前端在 PR 中同步修改，无遗漏。
  - [ ] 若使用 monorepo，前端 `import type` 直接引用后端类型可豁免本规则（单源定义）。
- Related rules: 路由参数校验见 [route-design-rule.md](route-design-rule.md) 的"路由参数须校验类型/必填/格式"。
