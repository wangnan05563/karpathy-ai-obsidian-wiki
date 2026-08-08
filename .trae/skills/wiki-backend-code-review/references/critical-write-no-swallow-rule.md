# 关键写不得静默吞错（BR-076）

> 复盘来源：`user-store.ts` 的 `saveUsers` 在 `writeFile` 外层 `try/catch` 中捕获错误却未 rethrow / 未 log，导致磁盘满 / 权限不足 / safe-delete 钩子拦截等写失败被掩盖，用户"保存成功"实为未落盘。对应 wiki-code-dev CODING-CRITICAL-WRITE-NO-SWALLOW。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"critical_write_no_swallow"章节读取，禁止在本规则文件硬编码函数名。

## Trigger Keywords
saveUsers, saveConfig, persistConversation, writeFile, fs.writeFile, try/catch, catch, ok: true, 持久化, 落盘

## Rules

### BR-076-1: 关键写失败必须传播

- **Severity**: critical
- **Description**: 关键写（用户 / 配置 / 会话）的 `try/catch` 必须 `throw` 或 `request.log.error` + `throw`，禁止空 catch 或仅 console 不抛出。调用方借此决定 UI 提示 / 重试 / 降级，而非误判成功。
- **Suggested fix**:
```typescript
export async function saveUsers(users: Users): Promise<void> {
  try {
    await fs.writeFile(path, JSON.stringify(users, null, 2), 'utf-8')
  } catch (err) {
    request?.log?.error({ err }, 'saveUsers failed')
    throw err // 关键写不得静默吞错
  }
}
```

### BR-076-2: 返回布尔成功须与真实写一致

- **Severity**: critical
- **Description**: 若写函数返回 `{ ok: boolean }`，`ok` 必须反映真实写结果——成功才 `true`，任何异常路径不得 `return { ok: true }`。优先直接 `throw` 让上层用 `try/catch` 判定。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `critical_write_no_swallow.enabled` | `true` | 是否启用本规则 |
| `critical_write_no_swallow.critical_functions` | `saveUsers,saveConfig,persistConversation` | 关键写函数清单（命中即须错误传播） |
| `critical_write_no_swallow.severity` | `critical` | 关键写静默吞错违规级别 |
| `critical_write_no_swallow.silent_catch_pattern` | `catch\s*\([^)]*\)\s*\{\s*\}` | 空 catch（无 throw/log）匹配模式 |

## 检查方式

1. Grep 检索 `critical_write_no_swallow.critical_functions` 中的写函数。
2. 对每个写调用，检查其 `try/catch`：catch 分支为空 / 仅 `console.log` 无 `throw` / 返回 `{ ok: true }` → BR-076-1 违规。
3. 若写函数返回布尔且异常路径仍返回 `ok: true` → BR-076-2 违规。

## 适配新项目

- **不同持久化层**（DB / KV）：规则同样适用——事务提交 / upsert 失败必须传播，禁止吞错。
- **best-effort 缓存写**：非关键写可降级，但须 `request.log.warn` 记录，且不在 `critical_functions` 清单中。
