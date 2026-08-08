# 关键数据文件损坏防护（BR-077）

> 复盘来源：`user-store.ts` 的 `loadUsers` 用 `try/catch` 包 `readFile + JSON.parse`，但 catch 分支未区分"文件不存在"与"JSON 损坏"，又未告警/备份——损坏文件被静默当作空数据，下次 `saveUsers` 直接覆盖，原始用户记录永久丢失。对应 wiki-code-dev CODING-FILE-CORRUPTION-GUARD。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"file_corruption_guard"章节读取，禁止在本规则文件硬编码文件名。

## Trigger Keywords
loadUsers, readFile, JSON.parse, ENOENT, catch, corrupted, backup, 损坏, 默认初始化, .bak

## Rules

### BR-077-1: 区分 not-found 与 corrupt

- **Severity**: critical
- **Description**: 读取关键文件：① 文件不存在（`ENOENT`）→ 返回默认数据并初始化；② 内容损坏（`JSON.parse` 抛错 / 结构校验失败）→ `log.error` 告警、把坏文件备份为 `<name>.corrupt-<ts>.bak`（避免被下次写覆盖），回退默认或最近好备份；二者都不得让异常冒泡导致崩溃或静默清零。
- **Suggested fix**:
```typescript
export async function loadUsers(): Promise<Users> {
  try {
    const raw = await fs.readFile(path, 'utf-8')
    return JSON.parse(raw) as Users
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
      return defaultUsers()                       // 不存在：默认初始化
    }
    request?.log?.error({ err }, 'users.json corrupted, backing up')
    await backupCorrupt(path)                     // 损坏：备份，防被覆盖
    return defaultUsers()                         // 回退默认，绝不静默清零
  }
}
```

### BR-077-2: 损坏文件须备份而非覆盖

- **Severity**: critical
- **Description**: 损坏文件在下次写之前必须被重命名备份（`<name>.corrupt-<ts>.bak`），不得原地删除（丢失取证）或放任被 `saveUsers` 直接覆盖（原始数据不可恢复）。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `file_corruption_guard.enabled` | `true` | 是否启用本规则 |
| `file_corruption_guard.critical_files` | `users.json,config.json` | 关键 JSON 文件清单 |
| `file_corruption_guard.backup_on_corruption` | `true` | 损坏时备份为 `.corrupt-<ts>.bak` |
| `file_corruption_guard.backup_suffix` | `.corrupt` | 坏文件备份名标记 |
| `file_corruption_guard.severity` | `critical` | 损坏当 not-found 静默清零违规级别 |

## 检查方式

1. Grep 检索 `file_corruption_guard.critical_files` 的读取逻辑（`readFile` + `JSON.parse`）。
2. 若 catch 分支未区分 `ENOENT` 与 parse error，或未对 corrupt 做 `log.error` + 备份 → BR-077-1 违规。
3. 若 corrupt 路径直接覆盖（无备份）或让异常冒泡 → BR-077-2 违规。

## 适配新项目

- **DB 存储**：等价规则为"查询失败区分'无记录'与'记录损坏'"，损坏行须标记/归档而非静默删除。
- **配置热更新**：watch 配置变更时同样须损坏防护，避免坏配置让服务起不来。
