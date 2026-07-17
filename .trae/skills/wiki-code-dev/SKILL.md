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
| 不确定加载哪些 | 全部加载（约 8KB） |

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

## 开发流程

### 新功能开发
1. 加载 config + 相关规则文件
2. 识别涉及的存储边界（前端/后端/文件/缓存）
3. 设计数据流：明确权威源、缓存层、降级路径
4. 编码时对照必检清单
5. 编写端到端验证（含缓存刷新、降级、边界条件）

### Bug 修复
1. 用 systematic-debugging 流程定位根因
2. 修复前对照硬约束确认未违反
3. 修复后必做：写盘函数→刷新缓存、路径函数→检查锚点、用户输入→白名单校验
4. 编写复现脚本验证

### 重构
1. 重构前梳理数据流（权威源、缓存、降级）
2. 逐文件改造，每步保持测试通过
3. 重构后对照必检清单全量自查

## 必检清单（每次提交前）

```
□ 持久化文件路径基于 import.meta.url 或配置锚点，不依赖 CWD
□ 写盘函数同步刷新内存缓存
□ 跨边界数据有单一权威源，其他存储可降级
□ 用户输入作文件名/路径有白名单校验
□ 后端不可用时前端有降级路径
□ 所有参数在 config 文件管理，无硬编码
□ 源文件 UTF-8 无 BOM
□ 端到端验证脚本通过（含缓存刷新、降级、路径穿越）
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
