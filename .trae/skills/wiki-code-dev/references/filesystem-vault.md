# 文件系统/Vault 操作规范

本文档记录 Karpathy Wiki 项目对文件系统（Vault）的操作标准。

## 路径白名单机制

所有文件写入操作必须经过白名单校验：

```typescript
const ALLOWED_PATHS = ['pages/', 'assets/', 'config/'];

function isPathAllowed(vaultId: string, filePath: string): boolean {
  const resolved = resolve(VAULT_ROOT, vaultId, filePath);
  return ALLOWED_PATHS.some(allowed => resolved.startsWith(resolve(VAULT_ROOT, vaultId, allowed)));
}
```

## 路径遍历防护

### UUID 正则校验

Vault ID 必须符合 UUID 格式：

```typescript
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

if (!UUID_REGEX.test(vaultId)) {
  throw new Error(`Invalid vault ID: ${vaultId}`);
}
```

### 禁止 .. 路径穿越

```typescript
if (filePath.includes('..') || filePath.includes('\\')) {
  throw new Error('Path traversal detected');
}
```

## 并发文件追加串行化

多个编译任务可能同时写入同一文件，必须串行化：

```typescript
let compileLock = Promise.resolve<void>();

function withCompileLock<T>(fn: () => Promise<T>): Promise<T> {
  const promise = compileLock.then(fn, fn);
  compileLock = promise.catch(() => {});
  return promise;
}

// 使用
await withCompileLock(async () => {
  await appendToFile(path, content);
});
```

## 部分失败不回滚

编译过程中单个页面失败时，不回滚已完成的页面，而是标记为 draft：

```typescript
try {
  await writeFile(vaultId, pagePath, content);
} catch (err) {
  // 保存为 draft，不中断整体流程
  await writeFile(`${pagePath}.draft`, content);
  yield { type: 'error', data: { page: pagePath, reason: 'draft_saved' } };
}
```

## 临时文件规范

临时文件必须使用 `os.tmpdir()` + 唯一前缀：

```typescript
import os from 'os';
import { randomUUID } from 'crypto';

const tempDir = os.tmpdir();
const tempPrefix = `wiki-${randomUUID()}`;
const tempFile = join(tempDir, `${tempPrefix}.tmp`);

// 使用后必须清理
finally {
  await unlink(tempFile).catch(() => {});
}
```

## 文件操作优先级

| 优先级 | 操作 | 说明 |
|---|---|---|
| 1 | `fs/promises` 异步 API | 首选，非阻塞 |
| 2 | `mkdir -p` 递归创建 | 幂等操作 |
| 3 | `access` 检查存在 | 写入前检查 |
| 4 | `rename` 原子替换 | 更新文件时使用 |
