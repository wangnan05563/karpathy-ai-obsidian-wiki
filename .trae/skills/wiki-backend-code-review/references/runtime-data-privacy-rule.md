# 运行时数据隐私审查规则（BR-065）

> 复盘来源：新增运行时落盘数据目录（如 SEA 多机场景下的 `data/`、会话缓存、索引缓存）未被加入 `.gitignore`，导致运行期含用户内容的文件被 `git add` 入库，造成隐私泄露。另一面：会话默认被持久化到服务端，违反"服务端默认不存会话"的最小化原则，且多机部署下服务端会话无法共享。本规则扩展 BR-030~037 的持久化/目录分离审查。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"运行时数据隐私审查参数（runtime_data_privacy）"章节读取，禁止在本规则文件硬编码目录名或策略。

## Trigger Keywords

.gitignore, gitignore, runtime data dir, data/, persistent data, sessions, 服务端会话, server-side session, localStorage default, IndexedDB, 隐私, 泄露, privacy leak, 运行期写入, 入库, git add, tracked, 目录分离, 最小化

## Rules

### BR-065-1：每个新增的运行时落盘目录必须与既有兄弟目录一并 gitignore

- **Severity**: critical
- **Description**: 任何新增的"运行期才产生、含用户内容"的目录（如 `data/`、`data/conversations/`、`cache/`、`index/`、SEA 多机下的 `userData/`）都必须同步加入 `.gitignore`，且若已有同类兄弟目录被忽略，新目录须在同一处追加（保持规则集中）。漏加会导致运行期文件被提交入库，泄露用户对话 / 索引内容。评审时确认：新增落盘目录的 PR 同时修改了 `.gitignore`（或与既有 ignore 规则同组），并用 `git check-ignore -v <path>` 验证该路径确实被忽略。
- **Suggested fix**:

```text
# 错误：新增 data/conversations/ 落盘，但未加入 .gitignore
// api/src/routes/conversations.ts
const DIR = path.join(getStateDir(), 'conversations'); // ❌ 运行期文件会被 git add

# 正确：.gitignore 与既有兄弟目录同组追加
# --- runtime data (never commit) ---
data/
data/conversations/
cache/
index/
userData/
```

### BR-065-2：持久化默认保守——会话默认不服务端存储，仅显式开启

- **Severity**: critical
- **Description**: 会话 / 临时交互状态默认不得持久化到服务端（多机部署下服务端会话无法共享，且扩大泄露面）。默认策略：会话留在客户端（localStorage / IndexedDB 降级缓存，见 BR-037），服务端仅作权威源存储"用户显式保存的对话"。任何"默认服务端存会话"的代码路径必须改回默认关闭，且仅当用户显式开启 `persistSessions` 配置才启用。评审时确认：会话写入服务端的代码受 `config.runtime_data_privacy.server_side_sessions` 显式开关保护，且默认值为 `false`。
- **Suggested fix**:

```typescript
// 错误：无条件把每次交互写服务端会话存储
await sessionStore.set(userId, session); // ❌ 默认服务端存会话，扩大泄露面

// 正确：受配置开关保护，默认 false
if (config.runtime_data_privacy.server_side_sessions) {
  await sessionStore.set(userId, session); // ✅ 仅用户显式开启
}
// 默认：会话留在客户端 IndexedDB 降级缓存（BR-037 跨 origin 边界）
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `runtime_data_privacy.enabled` | `true` | 是否启用本组规则（BR-065） |
| `runtime_data_privacy.severity_br065_1` | `critical` | BR-065-1 新目录未 gitignore 违规级别 |
| `runtime_data_privacy.severity_br065_2` | `critical` | BR-065-2 默认服务端存会话违规级别 |
| `runtime_data_privacy.runtime_data_dirs` | `data/,cache/,index/,userData/` | 运行期数据目录清单（须被 gitignore） |
| `runtime_data_privacy.gitignore_file_path` | `.gitignore` | gitignore 路径 |
| `runtime_data_privacy.verification_command` | `git check-ignore -v <path>` | 验证命令 |
| `runtime_data_privacy.server_side_sessions` | `false` | 服务端存会话默认开关 |
| `runtime_data_privacy.server_side_sessions_config_field` | `persistSessions` | 显式开关字段名 |

## 检查方式

1. **gitignore 同步检查**：Grep 新增落盘目录常量（如 `getStateDir()` / `path.join(..., 'conversations')`），确认 PR 同时修改 `.gitignore` 追加该目录；并运行 `git check-ignore -v <path>` 验证被忽略。漏加 → **BR-065-1 违规**。
2. **会话默认检查**：Grep 会话写入服务端代码，确认受 `server_side_sessions` 开关保护且默认 `false`；无条件写入 → **BR-065-2 违规**。

## 与其他规则的关系

- 与 BR-030~033（目录结构分离）联动：本规则是其隐私维度的强化（新增运行期目录必须 gitignore）。
- 与 BR-037（跨 origin 持久化边界）联动：会话默认留客户端、服务端仅权威源。
- 与 BR-066（可移植配置默认）联动：多机部署下数据目录须可重派生，配合本规则防泄露。
- 与 CODING-RUNTIME-DATA-PRIVACY（运行时数据隐私）对应：本规则是 CODING-RUNTIME-DATA-PRIVACY 的后端审查视角。
