# Data Repair / Migration Script Safety Rule（数据迁移 / 修复脚本安全）

## 触发关键词

migrate, migration, 迁移, 修复, 重写, recover, source:, replace, 批量重命名,
recover-title, dry-run, --apply, 历史数据, 脏数据, 文件名修复

## 规则

### MS-1：迁移/修复脚本默认 dry-run，显式 `--apply` 才写盘

**严重级别**：critical

脚本默认只扫描并报告"将做什么"，绝不修改任何文件。只有在显式传入 `--apply` 时才执行写操作。
这样任何误操作都可在不破坏数据的前提下先预览。

**为什么**：生产 vault 历史数据量巨大，一次误改会污染大量 Markdown 的 `source:` 引用与文件名。
dry-run 默认是从"事故"降级为"可回放操作"的关键设计。

**正确示例**：

```javascript
const APPLY = process.argv.includes('--apply');
if (!APPLY) {
  console.log('[dry-run] 未发现需要迁移 / 以下将被修改（加 --apply 执行）:');
  // 仅打印，不写
}
// APPLY 为真时才 rename / rewrite
```

### MS-2：迁移须幂等且可恢复——不删原文件、冲突用后缀而非覆盖

**严重级别**：critical

- **幂等**：重复运行同一迁移，结果一致（已迁移项被识别为"已完成"跳过）。
- **可恢复**：原文件在确认新文件落盘成功前不得删除（或先备份到独立目录）。
- **冲突命名**：目标名已存在时用 `-2` / `-3` 递增后缀，禁止静默覆盖。

**为什么**：迁移改写 `source:` 与文件名，一旦覆盖且引用错乱，难以还原。冲突后缀 + 不删原文件让
任何步骤都可人工比对回退。

### MS-3：引用改写须用函数式替换，禁止字符串拼接 `$1`

**严重级别**：critical

用 `String.replace(regex, replacement)` 改写引用（如 frontmatter `source: raw/<old>` → `raw/<new>`）
时，若 `replacement` 用字符串 `"$1" + newName`，当 `newName` 本身含 `$` 时，`$1` 会被当作捕获组
引用，污染目标路径（例如得到 `raw/raw/evil`）。

**正确示例**（函数式替换，把捕获组作为字符串拼接，绝不被 reinterpret）：

```javascript
// ❌ 危险：newName 含 $ 时 '$1' 被当捕获组
content = content.replace(re, "$1" + newName);

// ✅ 安全：函数返回值按字面拼接，newName 中的 $ 不会被 reinterpret
content = content.replace(re, (_, g1) => `${g1}${newName}`);
```

### MS-4：对同一引用页重复读取须用缓存 Map（pageCache）

**严重级别**：best-practice

迁移需从多个编译页反查引用（如用页面 title 做 `recover-title`）。对同一文件多次 `readFile` 既慢
又易错——先建 `Map<path, content>` 预读所有相关页，refs 收集 / 文件名推导 / `source:` 改写三处复用，
避免重复 IO。

### MS-5：两阶段执行——先全量扫描，再批量改写

**严重级别**：best-practice

迁移禁止"边读边写"：必须先扫描全部待处理项并构建映射（旧名→新名、引用页→待改字段），确认无误后
再统一改写。边读边写会导致同一文件被重复处理或中途崩溃留下半完成状态。

**正确示例骨架**：

```javascript
// 阶段 1：扫描（只读）
const plan = [];
for (const f of dirtyFiles) {
  const target = deriveTargetName(f);          // 含 stripInternalPrefix + CJK 保留
  const refs = findReferencingPages(f, pageCache); // 复用缓存
  plan.push({ from: f, to: target, refs });
}
if (!APPLY) { report(plan); process.exit(0); }
// 阶段 2：改写（先改名、再更新引用、最后删旧名——顺序可逆）
for (const item of plan) { rename(item); rewriteRefs(item); }
```

## 检查清单

- [ ] 脚本是否 dry-run 默认、显式 `--apply` 才写盘
- [ ] 迁移是否幂等（重复运行结果一致）+ 可恢复（不删原文件 / 先备份）
- [ ] 冲突文件名是否用 `-2/-3` 后缀而非覆盖
- [ ] 引用改写是否函数式替换（`(_, g1) => g1 + newName`），无 `$1` 字符串拼接
- [ ] 重复读取是否用 pageCache / 预读 Map
- [ ] 是否两阶段（先全量扫描再批量改写），禁止边读边写
