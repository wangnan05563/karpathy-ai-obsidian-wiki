# Rule Catalog — 用户库初始化完整性 (CODING-USER-STORE-INIT)

通用后端编码规范：用户存储（`users.json` 等）在首次运行 / 加载时必须**保证产出合法非空的结构**（如 `{}` 或 `{ users: [] }`），禁止让文件落成 0 字节空壳或非法 JSON。加载时须区分「文件不存在（ENOENT → 初始化默认）」与「文件损坏（JSON.parse 抛错 → 备份原文件 + 回退默认）」，损坏回退须有告警，**禁止静默清零**。本规则是后端审查条目 `wiki-backend-code-review` BR-092 的上位规范，与 `CODING-CRITICAL-WRITE-NO-SWALLOW`（BR-076）/ `CODING-FILE-CORRUPTION-GUARD`（BR-077）互补——前者管"写不得吞错"，本规则管"初始化不得落成空壳 / 损坏须兜底"。

> 复盘来源：某次运行 `data/users.json` 被写成 0 字节空壳，登录时 `loadUsers` 读取空串 → `JSON.parse('')` 抛错 → 落入未兜底分支 → 登录失败且无明确告警。修正：`loadUsers` 对空串 / 0 字节 / 损坏 JSON 统一回退默认结构并备份原文件、`log.warn`；初始化写盘必须写合法非空 JSON。

## Scope

- Covers: 任何"加载即解析 JSON"的关键数据文件（用户库、配置、状态），尤其首次运行未落盘 / 落盘中断产生的空壳。
- Does NOT cover: 纯追加日志（损坏不影响主流程）；明确为缓存、可整体丢弃的临时文件。

## Rules

### CODING-USER-STORE-INIT-1: 加载须区分 not-found 与 corrupt 并兜底

IsUrgent: True（严重）
Category: 后端 / 持久化

#### Description

`loadUsers`（`loadConfig` 等）读取文件：ENOENT → 返回合法默认结构；内容为空串 / 0 字节 / `JSON.parse` 抛错 → 备份原文件（如 `users.json.corrupt-<ts>`）+ 回退默认 + `log.warn`，**禁止抛错中断登录 / 禁止静默清零**。

#### Suggested Fix

```ts
// ✅ 空壳/损坏统一兜底默认
export function loadUsers(file: string): Users {
  if (!fs.existsSync(file)) return { users: [] } // not-found → 默认
  const raw = fs.readFileSync(file, 'utf-8')
  if (!raw.trim()) { // 0 字节空壳
    fs.renameSync(file, `${file}.corrupt-${Date.now()}`)
    log.warn({ file }, 'users.json empty-shell, fallback to default')
    return { users: [] }
  }
  try {
    return JSON.parse(raw)
  } catch {
    fs.renameSync(file, `${file}.corrupt-${Date.now()}`)
    log.warn({ file }, 'users.json corrupt, fallback to default')
    return { users: [] }
  }
}
```

### CODING-USER-STORE-INIT-2: 初始化写盘须合法非空

IsUrgent: False
Category: 后端 / 持久化

#### Description

任何初始化 / 修复写盘必须写出合法非空 JSON（`JSON.stringify(default, null, 2)`），不得写出空串 / 半截内容；结合 `CODING-CRITICAL-WRITE-NO-SWALLOW` 失败须传播。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `user_store_init.enabled` | `true` | 启用用户库初始化完整性审查 |
| `user_store_init.critical_files` | `users.json,config.json` | 须保证非空默认的关键数据文件 |
| `user_store_init.backup_on_corrupt` | `true` | 损坏/空壳文件须先备份再回退 |
| `user_store_init.severity` | `critical` | 空壳/损坏未兜底导致登录失败的违规级别 |
