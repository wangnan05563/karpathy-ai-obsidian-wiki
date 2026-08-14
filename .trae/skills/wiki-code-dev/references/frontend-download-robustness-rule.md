# Frontend Download Robustness Rule（前端下载健壮性：超时 / 重入 / 错误提示 / 移动端共享）

## 触发关键词

下载, download, fetch, blob, AbortSignal.timeout, 超时, 重入, reentry, in-flight,
移动端, 静默失败, 错误提示, 用户提示, downloadVaultFile, createObjectURL, 防重复点击

## 规则

### FR-DL-1：前端 fetch 下载须带可配置超时（`AbortSignal.timeout`）

**严重级别**：major

下载二进制/大文件时若后端卡死或网络中断，未设超时的请求会**永久挂起**，用户无任何反馈。
每个下载 `fetch` 必须传入 `signal: AbortSignal.timeout(<阈值>)`，阈值来自配置（禁止硬编码 `30000` 之类）。

**正确示例**：

```typescript
const timeoutMs = downloadConfig.timeout_ms ?? 30000; // 来自配置
const resp = await fetch(url, {
  headers: { Authorization: `Bearer ${token}` },
  signal: AbortSignal.timeout(timeoutMs),
});
```

> 超时阈值键名与默认值见 wiki-auto-testing / 前端 review-config 的 `download_frontend.timeout_ms`；
> 与 **CODING-CONFIG-TIMEOUT**（超时阈值可配置化）协同。

### FR-DL-2：下载须有重入守卫（in-flight 锁），禁止并发重复下载

**严重级别**：standard

用户快速重复点击「下载」会触发多个并发请求，造成状态竞态、重复写入、UI 抖动。
须用 `in-flight` 布尔 / `Set` 锁住进行中的下载，重复触发直接忽略或禁用按钮。

**正确示例**：

```typescript
let downloading = false; // 或按 path 维度的 Set<string>
async function downloadVaultFile(path: string) {
  if (downloading) return;          // 重入守卫
  downloading = true;
  try { /* fetch + blob + 保存 */ }
  finally { downloading = false; }   // 无论成败都释放（与 CODING-AUTH-LOADING-RESET 同理）
}
```

### FR-DL-3：下载错误必须显式提示用户，禁止静默失败（移动端/桌面端一致）

**严重级别**：major

下载失败时（网络/超时/401/404/解析失败）必须向用户弹出明确错误（Toast / 文案），
**不得**让移动端「毫无反应」而桌面端有提示——这是真实事故：移动端分支未复用桌面端错误处理，
失败被吞，用户以为「点了没反应」。

**正确示例**（统一错误出口）：

```typescript
try {
  await downloadVaultFile(p);
} catch (e) {
  // 桌面端 + 移动端共用同一错误提示路径
  showError(`下载失败：${(e as Error).message || '未知错误'}`);
}
```

### FR-DL-4：移动端与桌面端复用同一下载逻辑，不各自实现

**严重级别**：standard

移动端（`MobileBrowse`）与桌面端（`Browse`）应复用同一个 `downloadVaultFile`
服务/工具（含超时、重入、错误提示、文件名解析），而非各写一套导致行为分叉、修复只改一处。

> 对应 wiki-frontend-code-review **FR-091 / FR-092 / FR-093**（分别覆盖超时、移动端静默失败、重入守卫）；
> 与 **CODING-MEDIA-OBJECT-URL / FR-087**（blob/ObjectURL 生命周期）协同——下载用 `URL.createObjectURL`
> 后须 `revokeObjectURL`。

## 检查清单

- [ ] 下载 fetch 是否带 `AbortSignal.timeout`（阈值来自配置，非硬编码）
- [ ] 是否有重入守卫（in-flight 锁 / 按钮禁用），防重复点击并发
- [ ] 下载失败是否在移动端与桌面端都显式提示用户（无静默失败）
- [ ] 移动端是否复用同一下载工具（超时/重入/错误提示/文件名解析不各自实现）
- [ ] 下载产生的 ObjectURL 是否在保存后 `revokeObjectURL`（无内存泄漏）
