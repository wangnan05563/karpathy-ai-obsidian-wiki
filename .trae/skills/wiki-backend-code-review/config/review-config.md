# Review Configuration — wiki-backend-code-review

> 评审参数集中管理。规则文件本身不硬编码任何具体目录名、阈值或事件名，
> 一切可配置项都从本文件读取，便于项目演进时单点维护。

## 技术栈

- Runtime: Node.js (LTS)
- Framework: Fastify 4.x
- Language: TypeScript (target ES2022, module ESNext / ESM)
- 模块系统: ESM（`"type": "module"`，import/export，禁止 require）
- 异步模型: async/await + Node Streams + AsyncIterable

## 项目目录映射

| 逻辑角色 | 目录约定（相对项目根） | 说明 |
|---------|----------------------|------|
| HTTP 路由层 | `services/api/src/routes/` | Fastify 路由注册，参数解析 + 响应格式化 |
| 工作流编排 | `services/api/src/workflows/` | 调用 engine adapter，串接 hook 与预算控制 |
| 引擎适配器 | `services/api/src/engine/` | `EngineAdapter` 接口实现，封装外部引擎调用 |
| Vault 文件系统 | `services/api/src/vault/` | 对 Obsidian Vault 的读写、追加、状态持久化 |
| Prompt 存储 | `prompts/` | prompt 模板单点存放，禁止内联到 .ts 代码 |
| 状态持久化 | `services/api/src/state/` | `FileStateStore` 实现，runId 唯一索引 |
| 共享工具 | `services/api/src/utils/` | 通用 helper（路径校验、临时文件等） |

> 评审时若发现实际路径与上述映射不符，以实际路径为准并在报告中标注差异，
> 不要因路径偏差而跳过规则匹配。

## SSE 事件格式约定

- 事件分隔符：`\n\n`（两个换行）
- 单事件行格式：
  ```
  event: <type>\n
  data: <json-string>\n
  \n
  ```
- 必备事件类型（可扩展，但以下为契约下限）：
  - `progress`：进度/心跳事件
  - `result`：单条结果产出
  - `error`：错误推送（不通过抛异常断连）
  - `done`：正常结束事件
- JSON payload 必须是单行序列化结果（`JSON.stringify`，禁止多行美化后写入）。

## 并发控制阈值

| 场景 | 阈值/策略 | 说明 |
|------|----------|------|
| index.md / log.md 追加 | 串行化（`withCompileLock`） | 防止并发追加交错导致索引损坏 |
| 单进程内 SSE 连接 | 不限硬上限，但须 finally 收尾 | 避免连接泄漏 |
| 引擎调用预算 | 由 `EngineAdapter` 配置项注入 | 耗尽时返回 `budget_exceeded`，不抛异常 |
| 文件锁等待超时 | 由 `FileStateStore` 配置项注入 | 超时后降级，不阻塞事件循环 |

> 具体数值由项目运行时配置注入，评审规则只校验"是否使用对应机制"，
> 不校验具体阈值大小。

## 路径遍历防护规则

- 用户可控输入（如 `runId`、文件名、路径段）必须正则白名单校验后才能拼接到文件系统路径。
- 推荐白名单正则（UUID 形式）：`/^[a-fA-F0-9-]{36}$/`
- 文件名白名单（仅允许字母/数字/下划线/短横线/点）：`/^[A-Za-z0-9._-]+$/`
- 禁止模式：
  - 含 `..` 的相对路径
  - 绝对路径（`/` 或盘符 `C:` 开头）
  - 含 null byte 或换行符的输入
- 拼接后的最终路径必须用 `path.resolve` 解析后，校验仍落在允许的根目录内（`startsWith` 检查）。

## Vault 写入白名单

- AI 工具仅可写入：指定工作目录、`index.md`、`log.md`、`drafts/`、`attachments/`。
- 禁止修改：`SCHEMA.md`（结构契约文件，只能由人工维护）。
- 禁止删除：已归档的内容目录（防止 AI 误删历史）。
- 部分失败策略：不回滚已写入内容，标记 `draft` 状态保留半成品，由人工或后续流程收尾。

## 临时文件策略

- 临时文件必须使用 `os.tmpdir()` 作为根目录。
- 文件名必须带唯一前缀（如 `runId + '-' + Date.now()`），避免并发冲突。
- 临时文件使用完毕后必须 `fs.promises.unlink` 清理（在 finally 中）。

## 适用 / 不适用场景

### 适用

- 评审 `services/api/` 下的 Fastify 路由、workflow、engine adapter、vault 操作、state store。
- 评审 SSE 流式输出、文件系统并发追加、引擎预算控制等后端逻辑。
- 评审 TypeScript 后端代码的安全、错误处理、可维护性。

### 不适用

- 前端代码（`.tsx` / `.jsx` / 浏览器侧 `.ts`）。
- 纯 prompt 文本（`prompts/` 下的 `.md` 内容质量评审，属另一技能职责）。
- Obsidian Vault 内容本身的语义正确性（本技能只评审"对 Vault 的操作是否安全"，不评审内容）。
- 构建配置、CI 脚本等非业务后端代码（除非涉及安全或路径校验）。
