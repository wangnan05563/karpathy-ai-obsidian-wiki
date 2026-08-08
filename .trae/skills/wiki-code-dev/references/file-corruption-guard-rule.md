# Rule Catalog — 关键数据文件损坏防护 (CODING-FILE-CORRUPTION-GUARD)

通用编码规范：读取用户 / 配置等关键 JSON 文件时，必须把"文件不存在（not-found）"与"文件存在但内容损坏（parse error）"区分开：not-found 用默认数据初始化即可；损坏须**告警 + 备份坏文件 + 回退默认（或最后一次好备份）**，禁止把损坏当 not-found 直接覆盖、也禁止让 `JSON.parse` 异常冒泡导致进程崩溃 / 数据清零。本规则是后端审查条目 `wiki-backend-code-review` BR-077 的上位规范。

> 复盘来源：`user-store.ts` 的 `loadUsers` 用 `try/catch` 包 `readFile + JSON.parse`，但 catch 分支既未区分"文件不存在"与"JSON 损坏"，又未告警/备份——损坏文件被静默当作空数据，下次 `saveUsers` 直接覆盖，原始用户记录永久丢失。修正：not-found → 默认；corrupt → log.error + 备份坏文件 + 回退默认（或备份），绝不静默清零。

## Scope

- Covers: 任何从磁盘读取关键 JSON（users.json / config.json / sessions / vault 索引）并反序列化的逻辑。
- Does NOT cover: 纯日志 / 临时产物读取；明确允许丢失的缓存文件（仍建议区分）。

## Rules

### CODING-FILE-CORRUPTION-GUARD-1: 区分 not-found 与 corrupt

IsUrgent: True（严重）
Category: 持久化 / 健壮性

#### Description

读取关键文件：① 文件不存在（`ENOENT`）→ 返回默认数据并初始化；② 内容损坏（`JSON.parse` 抛错 / 结构校验失败）→ `log.error` 告警、把坏文件备份为 `<name>.corrupt-<ts>.bak`（避免被下次写覆盖），回退默认或最近好备份；二者都不得让异常冒泡导致崩溃或静默清零。

#### Suggested Fix

```ts
// ✅ 区分 not-found 与 corrupt
export async function loadUsers(): Promise<Users> {
  try {
    const raw = await fs.readFile(path, 'utf-8')
    return JSON.parse(raw) as Users
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
      return defaultUsers()            // 不存在：默认初始化
    }
    request?.log?.error({ err }, 'users.json corrupted, backing up') // 损坏：告警
    await backupCorrupt(path)          // 备份坏文件，防被覆盖
    return defaultUsers()              // 回退默认，绝不静默清零
  }
}
```

### CODING-FILE-CORRUPTION-GUARD-2: 损坏文件须备份而非覆盖

IsUrgent: True（严重）
Category: 持久化 / 健壮性

#### Description

损坏文件在下次写之前必须被重命名备份（`<name>.corrupt-<ts>.bak`），不得原地删除（丢失取证）或放任被 `saveUsers` 直接覆盖（原始数据不可恢复）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `file_corruption_guard.enabled` | `true` | 启用本组规则（CODING-FILE-CORRUPTION-GUARD） |
| `file_corruption_guard.critical_files` | `users.json,config.json` | 关键 JSON 文件清单（命中即须损坏防护） |
| `file_corruption_guard.backup_on_corruption` | `true` | 损坏时备份为 `.corrupt-<ts>.bak` |
| `file_corruption_guard.backup_suffix` | `.corrupt` | 坏文件备份名标记 |
| `file_corruption_guard.severity` | `critical` | 损坏当 not-found 静默清零违规级别 |
