# CODING-GENERATED-FILENAME-UNIQUENESS — 服务端生成文件名唯一性（防碰撞静默覆盖）

> 来源：归档路由 `POST /api/query/archive` 复盘。原实现 `relPath = queries/qa-${dateStr}-${shortId}.md`（shortId = 线程 UUID 前 8 位）→ 同线程同日归档多条消息文件名相同、后者**静默覆盖**前者，造成不可见数据丢失。
> 对应审查规则：后端 BR-081。

## 触发关键词

`writeFile` / `writeFileSync` / vault 落盘 / 文件名组合 / `qa-${date}-${shortId}` / `randomUUID` / 碰撞 / 覆盖 / `path.join(vaultRoot, ...)` / 派生分组键

## 严重级别

🔴 Critical（静默数据丢失，无报错、难发现）

## 规则

- **GFU-1**：当服务端用"**派生分组键**"（日期 + 线程 UUID 前 N 位 / 用户 ID 前缀等**非全局唯一**标识）拼接落盘路径时，必须追加**随机/唯一后缀**，保证同一分组键多次写入不互相覆盖。后缀熵长度从 `config.generated_filename.collision_suffix_len`（默认 4 位 hex）读取。
- **GFU-2**：分组前缀（date / shortId）保留以便人工按时间/线程浏览；唯一后缀保证写入**安全幂等**（同输入可重复写入得到不同文件，而非覆盖既有文件）。
- **GFU-3**：禁止用客户端可控且非唯一的字段直接作为唯一文件名（如仅用 `threadId` 前 8 位）。若必须，须叠加 GFU-1 后缀。
- **GFU-4**：文件名其余分段仍须满足 Vault 写入白名单（见 `filesystem-vault-rule.md` / BR-058）——仅追加随机后缀不改变既有白名单约束。

## 正 / 误示例

```ts
// ❌ 误：同线程同日多条归档 → 后者覆盖前者（静默丢数据）
const shortId = threadId.slice(0, 8);
const relPath = `queries/qa-${dateStr}-${shortId}.md`;

// ✅ 正：分组前缀保留 + 4 位随机后缀保证唯一
const shortId = threadId.slice(0, 8);
const uniq = randomUUID().slice(0, config.generated_filename.collision_suffix_len);
const relPath = `queries/qa-${dateStr}-${shortId}-${uniq}.md`;
```

## 检查清单

- [ ] 所有 `writeFile` / `writeFileSync` 的 `relPath` 构造是否含"非全局唯一"的分组键？
- [ ] 若是 → 是否叠加了随机/唯一后缀（长度从 config 读取）？
- [ ] 同一分组键重复写入是否会产生不同文件名（而非覆盖）？
