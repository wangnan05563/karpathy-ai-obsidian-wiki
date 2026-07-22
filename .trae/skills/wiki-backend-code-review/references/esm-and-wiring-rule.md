# ESM 与模块接线审查规则

> 所有参数从 `config/review-config.md` 的"ESM 与模块接线审查参数"章节读取，禁止在规则文件中硬编码。

## 适用范围
审查涉及 ESM 全局变量、模块接线、静态分析建议应用、路由注册的代码变更。

## 复盘背景
后端代码迁移到 ESM 模式后，出现 4 类回归问题：
1. `__dirname` 在 ESM 下抛 ReferenceError
2. 新增 routes 模块未在入口文件接线，导致 API 404
3. 盲目采纳 SonarQube S6606 建议（`__dirname ?? fallback`），引入运行时错误
4. 新增 route 端点未在入口注册，curl 返回 404

## 触发关键词
`ESM`、`__dirname`、`__filename`、`import.meta.url`、`fileURLToPath`、`registerRoute`、`registerTunnelRoute`、`SonarQube`、`S6606`、`ESLint`、`404`、`ReferenceError`、`routes/*.ts`、`index.ts`、`接线`、`wiring`

## 规则清单

| 规则编号 | 名称 | 严重级别 |
|---|---|---|
| BR-ESM-01 | ESM 全局变量禁用审查 | 🔴 严重（critical） |
| BR-ESM-02 | 模块接线完整性审查 | 🔴 严重（critical） |
| BR-ESM-03 | 静态分析建议人工验证审查 | 🔴 严重（critical） |
| BR-ESM-04 | 路由注册端点可达性审查 | 🔴 严重（critical） |

---

## BR-ESM-01：ESM 全局变量禁用审查

**严重级别**：🔴 严重（critical）

**规则描述**：所有 `.ts` 文件禁止使用 `<来自 config.esm_forbidden_globals>` 中的全局变量，必须用 `import.meta.url` 派生路径。

**为什么（根因）**：
- CommonJS 模式下 `__dirname` / `__filename` 是运行时注入的全局变量
- ESM 模式下这两个全局变量不存在，访问会抛 `ReferenceError`
- 项目 `package.json` 中 `"type": "module"` 启用 ESM 后，所有 `.ts` 文件按 ESM 编译执行
- 错误往往在运行时才暴露，单测可能漏检

**检查方法**：
```powershell
# 查找禁用的全局变量
grep -rn "__dirname|__filename" api/src

# 确认 import.meta.url 派生模式存在
grep -rn "import.meta.url" api/src
```

**正确示例**：
```typescript
// 正确：ESM 模式下用 import.meta.url 派生
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// 必需 import：<来自 config.esm_required_imports>
const dirname = path.dirname(fileURLToPath(import.meta.url));
// 派生模式：<来自 config.esm_dirname_derive_pattern>
```

**错误示例**：
```typescript
// 错误：ESM 下抛 ReferenceError
// 禁用全局变量：<来自 config.esm_forbidden_globals>
const dbPath = path.join(__dirname, 'data.db');

// 错误：typeof 守卫无法拯救——访问瞬间即抛错
const dirname = typeof __dirname !== 'undefined' ? __dirname : fallback;
```

---

## BR-ESM-02：模块接线完整性审查

**严重级别**：🔴 严重（critical）

**规则描述**：新增 `routes/*.ts` 或 `workflows/*.ts` 模块时，必须在入口文件 `<来自 config.wiring_entry_file>` 中完成接线三步骤：`<来自 config.wiring_required_steps>`。

**为什么（根因）**：
- 入口文件负责组装所有模块依赖关系
- 遗漏任何一步都会导致模块不可达：
  - 缺 import → 编译错误或运行时 ReferenceError
  - 缺实例化 → 模块状态未初始化
  - 缺 registerRoute 调用 → 端点 404
- 新增模块时容易只关注自身实现，忘记入口接线

**检查方法**：
```powershell
# 1. 列出 routes 目录所有模块
ls api/src/routes

# 2. 在入口文件中检查每个模块是否完成三步骤
# 接线必需步骤：<来自 config.wiring_required_steps>
# 入口文件：<来自 config.wiring_entry_file>
grep -n "^import" api/src/index.ts
grep -n "new .*Route|register.*Route" api/src/index.ts

# 3. 对比 routes 文件与入口 import，发现遗漏
```

**正确示例**：
```typescript
// 入口文件：<来自 config.wiring_entry_file>
// 步骤 1：import
import { TunnelRoute } from './routes/tunnel.js';
// 步骤 2：实例化
const tunnelRoute = new TunnelRoute(deps);
// 步骤 3：注册（命名模式：<来自 config.route_register_pattern>）
tunnelRoute.registerRoute(app);
```

**错误示例**：
```typescript
// 错误：新增 routes/tunnel.ts 但入口未接线
// routes/tunnel.ts 存在 registerTunnelRoute，但 index.ts 中：
// ❌ 缺 import
// ❌ 缺实例化
// ❌ 缺 registerRoute 调用
// 结果：curl /api/tunnel/status → 404
```

---

## BR-ESM-03：静态分析建议人工验证审查

**严重级别**：🔴 严重（critical）

**规则描述**：`<来自 config.static_analysis_tools>` 等静态分析工具的修复建议必须人工验证运行时语义，验证清单：`<来自 config.static_analysis_verify_checklist>`。

**为什么（根因）**：
- 静态分析工具基于语法树推断，不理解运行时语义
- 典型反例：SonarQube S6606 建议 `typeof x !== 'undefined' ? x : fallback` 简化为 `x ?? fallback`
  - 语法等价，但 ESM 下访问 `__dirname` 直接抛 ReferenceError，`??` 无法拯救
  - `typeof` 守卫原意是"不存在则 fallback"，`??` 改成"为 null/undefined 则 fallback"
  - 后者在访问瞬间就抛错，语义被破坏
- 盲目采纳建议会引入运行时回归

**检查方法**：
```powershell
# 查找最近采纳静态分析建议的改动
git log --oneline --all | head -20
git diff HEAD~5 -- api/src

# 验证清单（必须逐项确认）：
# <来自 config.static_analysis_verify_checklist>
#   operand_throws_on_reference：操作数访问是否抛 ReferenceError
#   type_guard_bypassed：typeof 守卫是否被绕过
#   side_effect_changed：副作用是否改变
```

**正确示例**：
```typescript
// 正确：先验证运行时语义，再决定是否采纳
// SonarQube S6606 建议：__dirname ?? fallback
// 人工验证：ESM 下 __dirname 访问抛 ReferenceError，?? 无法拯救
// 结论：拒绝采纳，改用 import.meta.url 派生
const dirname = path.dirname(fileURLToPath(import.meta.url));
```

**错误示例**：
```typescript
// 错误：盲目采纳 SonarQube S6606 建议
// 原：typeof __dirname !== 'undefined' ? __dirname : fallback
// 改：__dirname ?? fallback  // ❌ ESM 下访问瞬间抛 ReferenceError
```

---

## BR-ESM-04：路由注册端点可达性审查

**严重级别**：🔴 严重（critical）

**规则描述**：所有 `routes/*.ts` 文件中暴露的端点必须在入口文件 `<来自 config.wiring_entry_file>` 中可达（即入口文件调用了对应的注册函数，命名模式 `<来自 config.route_register_pattern>`）。

**为什么（根因）**：
- 端点可达 = HTTP 请求能路由到处理函数
- 不可达的端点对用户表现为 404
- 端点定义在 routes 文件中，但路由树由入口文件组装
- 仅在 routes 文件内定义 `fastify.get(...)` 不足以暴露端点，必须被入口调用注册

**检查方法**：
```powershell
# 1. 提取 routes 文件中所有端点路径
grep -rn "fastify\.\(get\|post\|put\|delete\|patch\)" api/src/routes

# 2. 在入口文件中确认注册函数被调用
# 注册模式：<来自 config.route_register_pattern>
grep -n "register.*Route" api/src/index.ts

# 3. 运行时验证端点可达性
# 验证命令：<来自 config.endpoint_reachability_check>
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/tunnel/status
# 期望 200，若 404 则接线遗漏
```

**正确示例**：
```typescript
// routes/tunnel.ts
export function registerTunnelRoute(app: FastifyInstance) {
  app.get('/api/tunnel/status', handler);
}

// index.ts（入口文件：<来自 config.wiring_entry_file>）
import { registerTunnelRoute } from './routes/tunnel.js';
registerTunnelRoute(app);  // 命名模式：<来自 config.route_register_pattern>
```

**错误示例**：
```typescript
// routes/tunnel.ts 定义了端点
export function registerTunnelRoute(app: FastifyInstance) {
  app.get('/api/tunnel/status', handler);
}

// index.ts 未调用 registerTunnelRoute
// 结果：curl /api/tunnel/status → 404
```

---

## 检测流程

```
┌─────────────────────────────────────────┐
│  开始审查 .ts 文件变更                    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  BR-ESM-01：扫描 __dirname/__filename   │
│  grep -rn "__dirname|__filename"       │
└────────────────┬────────────────────────┘
                 │
         命中 ───┴─── 未命中
          │              │
          ▼              ▼
   ┌──────────┐   ┌─────────────────────┐
   │ 报告违规  │   │ BR-ESM-02：检查接线 │
   │ critical │   │ 对比 routes/ 与入口 │
   └──────────┘   └──────────┬──────────┘
                            │
                    缺步骤──┴──齐全
                      │           │
                      ▼           ▼
               ┌──────────┐  ┌─────────────────────┐
               │ 报告违规  │  │ BR-ESM-03：检查近  │
               │ critical │  │ 期静态分析采纳      │
               └──────────┘  └──────────┬──────────┘
                                       │
                              采纳──┴──未采纳
                                │           │
                                ▼           ▼
                         ┌──────────┐  ┌─────────────────────┐
                         │ 验证清单  │  │ BR-ESM-04：端点可达 │
                         │ 逐项确认  │  │ curl 验证 HTTP 码   │
                         └─────┬────┘  └──────────┬──────────┘
                               │                  │
                       语义破坏┴语义等价    404────┴──200
                         │        │          │       │
                         ▼        ▼          ▼       ▼
                  ┌──────────┐ ┌────┐  ┌──────────┐ ┌────┐
                  │ 报告违规  │ │ 通过│  │ 报告违规  │ │通过│
                  │ critical │ └────┘  │ critical │ └────┘
                  └──────────┘         └──────────┘
```

---

## 审查结果呈现形式

每条审查发现必须包含以下六要素：

| 字段 | 说明 | 示例 |
|------|------|------|
| 规则编号 | 违反的规则 ID | BR-ESM-01 |
| 文件:行号 | 违规位置 | api/src/index.ts:42 |
| 严重级别 | critical / warning / suggestion | 🔴 严重（critical） |
| 问题描述 | 简述违规内容 | 使用了 ESM 禁用全局变量 __dirname |
| 修复建议 | 具体修复步骤 | 改用 path.dirname(fileURLToPath(import.meta.url)) |
| 规范依据 | 引用的规则章节 | BR-ESM-01 § ESM 全局变量禁用审查 |

**结果示例**：

| 规则编号 | 文件:行号 | 严重级别 | 问题描述 | 修复建议 | 规范依据 |
|---|---|---|---|---|---|
| BR-ESM-01 | api/src/index.ts:42 | 🔴 严重 | 使用 `__dirname`，ESM 下抛 ReferenceError | 改用 `path.dirname(fileURLToPath(import.meta.url))` | esm-and-wiring-rule.md § BR-ESM-01 |
| BR-ESM-02 | api/src/index.ts | 🔴 严重 | 新增 routes/tunnel.ts 未在入口完成接线三步骤 | 添加 import + 实例化 + registerRoute 调用 | esm-and-wiring-rule.md § BR-ESM-02 |
| BR-ESM-03 | api/src/index.ts:42 | 🔴 严重 | 盲目采纳 SonarQube S6606 建议，破坏 typeof 守卫 | 拒绝采纳，改用 import.meta.url 派生 | esm-and-wiring-rule.md § BR-ESM-03 |
| BR-ESM-04 | api/src/routes/tunnel.ts | 🔴 严重 | 端点 /api/tunnel/status 在入口未注册，返回 404 | 入口文件调用 registerTunnelRoute(app) | esm-and-wiring-rule.md § BR-ESM-04 |

---

## 适用场景 / 不适用场景

**适用场景**：
- 项目 `package.json` 中 `"type": "module"` 或使用 ESM 导入语法
- 新增 `routes/*.ts` 或 `workflows/*.ts` 模块
- 应用静态分析工具（SonarQube、ESLint）建议
- 新增 HTTP 端点
- 涉及路径派生（`__dirname` 替换为 `import.meta.url`）

**不适用场景**：
- CommonJS 项目（`require` / `module.exports`）
- 纯前端代码（.vue / .tsx）→ 使用 wiki-frontend-code-review
- 非 TypeScript 后端代码
- 不涉及模块接线的纯函数库改动

---

## 交叉引用
- 架构分层相关：[architecture-rule.md](architecture-rule.md)
- 安全相关：[security-rule.md](security-rule.md)
- 配置读取一致性：[config-consistency-rule.md](config-consistency-rule.md)
- 热更新闭环：[hot-update-rule.md](hot-update-rule.md)
