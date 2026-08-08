# Rule Catalog — 关键写不得静默吞错 (CODING-CRITICAL-WRITE-NO-SWALLOW)

通用编码规范：涉及用户数据 / 配置 / 状态的"关键写"操作（保存用户、落盘配置、持久化会话），一旦写失败必须**显式传播错误**（抛出或记录后抛出），禁止在 `try/catch` 中静默吞掉、返回 `ok: true` 假成功。静默吞错会让上层以为保存成功，实则数据丢失且无任何告警。本规则是后端审查条目 `wiki-backend-code-review` BR-076 的上位规范。

> 复盘来源：`user-store.ts` 的 `saveUsers` 在 `writeFile` 外层 `try/catch` 中捕获错误却未 rethrow / 未 log，导致磁盘满 / 权限不足 / safe-delete 钩子拦截等写失败被掩盖，用户"保存成功"实为未落盘。修正：关键写失败须 `throw` 或 `log + throw`，由调用方决定是否降级。

## Scope

- Covers: 任何持久化关键数据的写操作（`saveUsers` / `saveConfig` / `persistConversation` / 配置回写 / 会话落盘）。
- Does NOT cover: 纯日志写出（可降级到 stdout）；明确标注为 best-effort 的非关键缓存写（仍建议记录）。

## Rules

### CODING-CRITICAL-WRITE-NO-SWALLOW-1: 关键写失败必须传播

IsUrgent: True（严重）
Category: 持久化 / 错误处理

#### Description

关键写（用户 / 配置 / 会话）的 `try/catch` 必须 `throw` 或 `request.log.error` + `throw`，禁止空 catch 或仅 console 不抛出。调用方借此决定 UI 提示 / 重试 / 降级，而非误判成功。

#### Suggested Fix

```ts
// ✅ 失败显式传播
export async function saveUsers(users: Users): Promise<void> {
  try {
    await fs.writeFile(path, JSON.stringify(users, null, 2), 'utf-8')
  } catch (err) {
    request?.log?.error({ err }, 'saveUsers failed')
    throw err // 关键写不得静默吞错
  }
}
```

### CODING-CRITICAL-WRITE-NO-SWALLOW-2: 返回布尔成功须与真实写一致

IsUrgent: True（严重）
Category: 持久化 / 错误处理

#### Description

若写函数返回 `{ ok: boolean }`，`ok` 必须反映真实写结果——成功才 `true`，任何异常路径不得 `return { ok: true }`。优先直接 `throw` 让上层用 `try/catch` 判定。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `critical_write_no_swallow.enabled` | `true` | 启用本组规则（CODING-CRITICAL-WRITE-NO-SWALLOW） |
| `critical_write_no_swallow.critical_functions` | `saveUsers,saveConfig,persistConversation` | 关键写函数清单（命中即须错误传播） |
| `critical_write_no_swallow.severity` | `critical` | 关键写静默吞错违规级别 |
| `critical_write_no_swallow.silent_catch_pattern` | `catch\s*\([^)]*\)\s*\{\s*\}` | 空 catch（无 throw / log）匹配模式 |
