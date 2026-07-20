# Route Registration Rule

## 触发关键词

routes/, register, app.register, fastify.register, app.use, index.ts, 新增路由, 路由未注册, 404, router

## 规则描述

### RR-1：新增路由文件必须在入口文件同步导入与注册

**严重级别**：critical

每次新增 `routes/*.ts`（或 `routes/*.js`）文件，必须在项目入口文件（如 `index.ts` / `app.ts` / `server.ts`）中同步导入并调用注册函数，使该路由对外可访问。

**为什么**：手动注册路由的框架（Fastify / Express / Koa）不会自动扫描 `routes/` 目录。开发者新增路由文件后忘记在入口注册，编译期无任何报错，运行期前端的请求直接返回 404。这类问题在缺少端到端集成测试的项目中极易逃逸到生产环境。

## 判断逻辑

```
1. Glob '<route_directory>/*.ts' 获取所有路由文件（route_directory 默认 'routes/'，见 config）
2. Grep '<register_function_pattern>' in <entry_file> 获取入口文件中已注册的路由（默认 'register'）
3. 对比两个集合：
   - 路由文件中存在，但入口文件未匹配到对应 import 或 register 调用 → 违规
   - 入口文件中 register 了不存在的文件 → 警告（可能是清理时遗漏）
4. 提交前在 dev 环境对每个路由的代表性路径发起 OPTIONS / GET 请求，确认非 404
```

## 适用场景

- Fastify / Express / Koa 等手动注册路由的 Node.js 框架
- 路由文件按功能拆分到独立文件的中小型项目
- 任何需要"显式注册才能生效"的插件/模块加载模式

## 不适用场景

- NestJS 等装饰器自动发现路由的框架（`@Controller` 注解由框架扫描）
- Next.js / Nuxt.js 等基于文件系统路由的框架（目录即路由）
- Hapi 的插件自动加载机制（通过 manifest 配置即可）

## 配置参数

> 所有参数从 `config/coding-standards-config.md` 的 `route_registration` 段读取，规则文件不硬编码。

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `route_directory` | `routes/` | 路由文件所在目录 |
| `entry_file` | `index.ts` | 路由注册的入口文件路径 |
| `register_function_pattern` | `register` | 入口文件中识别注册调用的关键字（如 `fastify.register` / `app.use`） |
| `probe_enabled` | `false` | 是否在 CI 中对代表性路径发起真实请求验证（默认关闭，避免依赖运行时环境） |

## 示例

### 错误示例

新增 `routes/ai.ts` 与 `routes/cleanup.ts`，但入口 `index.ts` 仅注册了既有路由：

```typescript
// src/index.ts
import fastify from 'fastify';
import healthRoutes from './routes/health.js';
import userRoutes from './routes/user.js';

const app = fastify();

app.register(healthRoutes);
app.register(userRoutes);
// ❌ 缺少 aiRoutes 与 cleanupRoutes 的导入与注册
// 前端调用 /api/ai/config 与 /api/cleanup/status 全部 404
```

### 正确示例

```typescript
// src/index.ts
import fastify from 'fastify';
import healthRoutes from './routes/health.js';
import userRoutes from './routes/user.js';
import aiRoutes from './routes/ai.js';             // ✅ 同步导入
import cleanupRoutes from './routes/cleanup.js';    // ✅ 同步导入

const app = fastify();

app.register(healthRoutes);
app.register(userRoutes);
app.register(aiRoutes);                             // ✅ 同步注册
app.register(cleanupRoutes);                        // ✅ 同步注册
```

### 检测脚本片段

```powershell
# $routeDir、$entryFile、$registerPattern 由调用方从 config 读取后传入
$routeFiles = Get-ChildItem -Path $routeDir -Filter '*.ts' -ErrorAction SilentlyContinue
$entryContent = Get-Content $entryFile -Raw

foreach ($f in $routeFiles) {
  $baseName = $f.BaseName  # 如 'ai'
  # 简化匹配：入口文件是否同时包含 import 与 register 关键字
  if ($entryContent -notmatch "import.*$baseName" -or $entryContent -notmatch "$registerPattern.*$baseName") {
    Write-Warning "路由文件 $($f.Name) 未在 $entryFile 中导入或注册"
  }
}
```

## 检查清单

- [ ] 新增 `routes/*.ts` 文件后是否在入口文件导入
- [ ] 新增路由文件后是否在入口文件调用 `register` / `use`
- [ ] 删除路由文件后是否同步移除入口文件的 import 与 register
- [ ] 入口文件中所有 register 调用是否都有对应文件存在
- [ ] dev 环境是否对新增路由的代表性路径发起请求验证非 404
