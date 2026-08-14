# Download Reentry Guard Rule（下载重入守卫，防并发重复下载）

## 触发关键词

下载, download, 重入, reentry, in-flight, 防重复点击, 并发, 重复下载,
downloading, 按钮禁用, downloadVaultFile, 状态竞态

## 规则

### FR-093-1（standard）：下载须有重入守卫（in-flight 锁），禁止并发重复下载

用户快速重复点击「下载」会触发多个并发请求，造成状态竞态、重复写入、UI 抖动。
须用 `in-flight` 布尔 / `Set` 锁住进行中的下载，重复触发直接忽略或禁用按钮。

**错误示例**：

```typescript
// ❌ 无重入守卫：连点触发并发下载
async function onDownload(p: string) { await downloadVaultFile(p); }
```

**正确示例**：

```typescript
let downloading = false;
async function onDownload(p: string) {
  if (downloading) return;            // 重入守卫
  downloading = true;
  try { await downloadVaultFile(p); }
  finally { downloading = false; }    // 无论成败都释放（与 FR-083 loading 复位同理）
}
```

### FR-093-2（suggestion）：重入锁释放必须置于 `finally`，避免永久锁死

锁的释放必须在 `finally` 中执行——任何异常路径都不能让锁残留，否则一次失败会导致后续下载全部被拦。

> 对应 wiki-code-dev **CODING-FE-DOWNLOAD-ROBUST / FR-DL-2**；
> 与 **FR-083（异步操作 loading 复位）**、**FR-082（认证请求超时兜底）** 同属「异步状态必须可靠复位」家族。

## 检查清单

- [ ] 下载是否设重入守卫（in-flight 布尔 / Set），防连点并发
- [ ] 锁释放是否置于 `finally`（异常路径不残留）
- [ ] 进行中是否禁用下载按钮或忽略重复触发（非叠加请求）
- [ ] 移动端与桌面端是否共用同一重入逻辑
