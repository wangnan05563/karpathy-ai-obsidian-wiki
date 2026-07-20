---
name: wiki-code-dev
description: "Karpathy-Wiki 项目编码规范与开发准则。在新功能开发、Bug 修复、代码重构前加载，提供持久化、缓存、路径解析、存储边界、输入校验等通用规则。所有规则与具体业务解耦，可适配不同模块。"
---

# Wiki Code Dev

Karpathy-Wiki 项目的通用编码规范与开发准则。规则与具体业务解耦，抽象为可跨模块复用的判断逻辑。

## 触发条件

- 新功能开发前加载规则
- Bug 修复前对照必检清单
- 代码重构前确认未违反硬约束
- Code Review 时作为规则源
- 不确定某写法是否合规时查询

## 加载策略

按需加载以节省 context token：

### 1. 基线（必读）
- [SKILL.md](SKILL.md) — 本文件
- [config/coding-standards-config.md](config/coding-standards-config.md) — 项目参数（路径锚点、缓存 TTL、白名单正则、降级策略）

### 2. 规则路由（按需）
根据任务类型选择性加载：

| 任务类型 | 加载规则文件 |
|---------|------------|
| 涉及文件读写/持久化 | [references/persistence-rule.md](references/persistence-rule.md) |
| 涉及内存缓存/写后读 | [references/cache-rule.md](references/cache-rule.md) |
| 涉及路径解析 | [references/path-resolution-rule.md](references/path-resolution-rule.md) |
| 涉及前端存储(localStorage/IndexedDB) | [references/storage-boundary-rule.md](references/storage-boundary-rule.md) |
| 涉及多源数据同步 | [references/single-source-rule.md](references/single-source-rule.md) |
| 涉及用户输入作文件名/路径 | [references/input-validation-rule.md](references/input-validation-rule.md) |
| 涉及错误处理/降级 | [references/fallback-rule.md](references/fallback-rule.md) |
| 涉及文件编辑/编码/中文/构建门禁 | [references/encoding-guard-rule.md](references/encoding-guard-rule.md) |
| 涉及 PowerShell/服务管理/端口 | [references/powershell-constraints-rule.md](references/powershell-constraints-rule.md) |
| 涉及新增路由/接口注册 | [references/route-registration-rule.md](references/route-registration-rule.md) |
| 涉及子进程/外部资源/异步赋值字段 | [references/null-guard-rule.md](references/null-guard-rule.md) |
| 涉及子进程/定时器/长连接/服务退出 | [references/graceful-shutdown-rule.md](references/graceful-shutdown-rule.md) |
| 涉及敏感字段/API Key/密码/GET 配置接口 | [references/sensitive-field-masking-rule.md](references/sensitive-field-masking-rule.md) |
| 涉及后端/前端 types.ts 同步 | [references/type-sync-rule.md](references/type-sync-rule.md) |
| 涉及 flex 布局/滚动容器/内容裁切 | [references/scroll-container-rule.md](references/scroll-container-rule.md) |
| 涉及 SPA 内部跳转/视图切换/CustomEvent | [references/spa-navigation-rule.md](references/spa-navigation-rule.md) |
| 涉及检查更新/版本对比/缓存轮询 | [references/update-check-rule.md](references/update-check-rule.md) |
| 需要参考历史复盘/工作流模板 | [references/development-workflow.md](references/development-workflow.md) |
| 不确定加载哪些 | 全部加载（约 40KB） |

### 3. 示例按需
仅当生成修复代码时加载 `references/examples/<rule>-examples.md`。

## 硬约束（不可违反）

1. **路径解析禁用 CWD**：持久化文件路径必须基于 `import.meta.url` 或配置的锚点目录，禁止依赖 `process.cwd()`
2. **写后即刷**：任何写盘函数必须同步刷新对应内存缓存，禁止依赖 TTL 自然过期
3. **单一权威源**：每类数据只能有一个权威存储，其他存储仅作缓存且必须可降级
4. **存储边界明确**：跨 origin/进程/会话共享的数据必须用后端持久化，浏览器存储仅作单 origin 缓存
5. **输入白名单**：用户输入作为文件名/路径时必须用白名单正则校验，禁止直接拼接
6. **降级不阻断**：后端不可用时前端必须能降级到本地缓存，主流程不阻断
7. **配置化无硬编码**：所有参数（路径、TTL、正则、阈值）必须在 config 文件管理，规则文件仅描述模式
8. **UTF-8 无 BOM**：所有源文件与 meta 文件 UTF-8 无 BOM（Windows cmd.exe 兼容）
9. **编码守卫**：Edit/Write 含非 ASCII 字符文件前必须严格 UTF-8 解码检测；非 UTF-8 文件用 `encoding_fallback` 读写；构建前必须执行 `encoding_scan_command` 门禁
10. **PowerShell 约束**：禁用 `&&`（用 `command_separator`）、禁用只读变量赋值（`readonly_vars`）、禁用 `cmd /c`（`blocked_commands`）；工作目录通过 `cwd_param` 指定而非 `cd`
11. **路由注册守卫**：新增 `routes/*.ts` 文件必须在 `entry_file` 同步 import 与调用 `register_function_pattern`；自动发现框架（NestJS 等）可豁免
12. **空值守卫**：由 `async_assignment_keywords`（spawn/exec/connect 等）赋值的字段使用前必须 `if (!x)` 守卫并重建/抛错，禁止直接访问
13. **优雅停止**：创建子进程/定时器/长连接的模块必须注册 `shutdown_signals` 钩子，按"子进程→定时器→连接"顺序清理后 `process.exit`
14. **敏感字段脱敏**：GET 接口返回字段名匹配 `sensitive_field_patterns` 时必须脱敏 + 附 `configured` 标志；POST 空串语义为"不修改"
15. **类型同步**：后端 `backend_types_path` 与前端 `frontend_types_path` 同名 interface 字段必须对齐，提交前通过两端 `typecheck_command` 门禁
16. **滚动容器单一职责**：容器链路上 `overflow-y: auto` 层数不得超过 `scroll_container.max_overflow_layers`（默认 1）；`flex-direction: column + flex: 1` 容器内的自然高度子项必须 `flex-shrink: 0`
17. **SPA 内部跳转**：跨组件视图切换必须通过 `spa_navigation.event_name_pattern` 派发 CustomEvent，由入口组件监听切换；监听器必须在 onMounted/onBeforeUnmount 配对管理
18. **更新检查缓存**：`/api/about/check-update` 类接口必须有 `check_update.cache_ttl_ms`（默认 5 分钟）后端缓存；轮询间隔 `poll_interval_ms` 必须 ≥ `cache_ttl_ms`；离线模式 `offline_mode: true` 时固定返回 `has_update: false`

## 开发流程

### 新功能开发
1. 加载 config + 相关规则文件
2. 识别涉及的存储边界（前端/后端/文件/缓存）
3. 设计数据流：明确权威源、缓存层、降级路径
4. 编码时对照必检清单
5. 若新增路由文件 → 同步在 `entry_file` 导入与注册
6. 若涉及子进程/定时器/长连接 → 注册 `shutdown_signals` 清理钩子
7. 若新增 GET 配置接口 → 检查响应字段是否匹配敏感模式并脱敏
8. 若后端 types.ts 新增/修改 interface → 同步前端 types.ts
9. 编写端到端验证（含缓存刷新、降级、边界条件）

### Bug 修复
1. 用 systematic-debugging 流程定位根因
2. 修复前对照硬约束确认未违反
3. 修复后必做：写盘函数→刷新缓存、路径函数→检查锚点、用户输入→白名单校验
4. 修复后必做：子进程字段→空值守卫、敏感字段→脱敏、类型变更→前后端同步
5. 编写复现脚本验证

### 重构
1. 重构前梳理数据流（权威源、缓存、降级）
2. 逐文件改造，每步保持测试通过
3. 重构后对照必检清单全量自查
4. 重构后必做：路由文件与入口注册对账、信号钩子覆盖、types.ts 两端对齐

## 必检清单（每次提交前）

```
□ 持久化文件路径基于 import.meta.url 或配置锚点，不依赖 CWD
□ 写盘函数同步刷新内存缓存
□ 跨边界数据有单一权威源，其他存储可降级
□ 用户输入作文件名/路径有白名单校验
□ 后端不可用时前端有降级路径
□ 所有参数在 config 文件管理，无硬编码
□ 源文件 UTF-8 无 BOM
□ Edit 含中文文件前已检测编码，非 UTF-8 用 encoding_fallback 读写
□ 构建前已执行 encoding_scan_command 门禁
□ PowerShell 命令未用 &&、未赋值只读变量、未用 cmd /c
□ 启动服务前已停止占用端口的旧进程
□ 新增 routes/*.ts 已在 entry_file 同步导入与 register
□ 异步赋值字段（this.provider/child/connection 等）使用前有空值守卫
□ 创建子进程/定时器/长连接的模块已注册 SIGINT/SIGTERM 清理钩子
□ GET 接口返回的敏感字段已脱敏并附 configured 标志
□ POST 接口空串语义为"不修改"，未误清空敏感字段
□ 后端 types.ts 与前端 types.ts 同名 interface 字段对齐
□ 已通过后端 tsc --noEmit 与前端 vue-tsc --noEmit 门禁
□ 端到端验证脚本通过（含缓存刷新、降级、路径穿越）
□ 滚动容器链路上 overflow-y: auto 层数 ≤ 1，flex 子项需自然撑开时已加 flex-shrink: 0
□ 跨组件 SPA 跳转通过 CustomEvent 派发，监听器在 onMounted/onBeforeUnmount 配对管理
□ 检查更新类接口有后端缓存（≥ 1 分钟），轮询间隔 ≥ 缓存 TTL，离线模式返回固定值
```

## 适用场景

- 全栈项目（前端 SPA + 后端 API + 文件系统持久化）
- 有内存缓存层的服务
- 多 origin/多启动方式的应用
- 需要降级容错的本地优先应用

## 不适用场景

- 纯静态站点（无后端、无持久化）
- SSR 应用（渲染时机与持久化模式不同，需独立规范）
- 移动端 App（存储模型不同）
- 无 IO 的纯函数库
