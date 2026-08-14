# Download Mobile Silent-Failure Guard Rule（移动端下载失败不得静默）

## 触发关键词

下载, download, 移动端, MobileBrowse, 静默失败, 错误提示, 用户提示, Toast,
毫无反应, 点了没反应, downloadVaultFile, showError, 失败兜底

## 规则

### FR-092-1（major）：移动端下载失败必须显式提示用户，禁止静默

下载失败（网络/超时/401/404/解析失败）时，移动端必须弹出明确错误（Toast / 文案），
与桌面端共用同一错误出口。真实事故：移动端分支未复用桌面端错误处理，失败被吞，
用户「点了下载毫无反应」，误以为功能损坏。

**错误示例**：

```typescript
// ❌ 移动端静默：失败无任何提示
try { await downloadVaultFile(p); } catch { /* 吞掉 */ }
```

**正确示例**（统一错误出口，桌面/移动共用）：

```typescript
try {
  await downloadVaultFile(p);
} catch (e) {
  showError(`下载失败：${(e as Error).message || '未知错误'}`);
}
```

### FR-092-2（standard）：移动端与桌面端复用同一下载工具，不各自实现错误处理

`MobileBrowse` 与 `Browse` 应复用同一个 `downloadVaultFile`（含超时/重入/错误提示/文件名解析），
而非各写一套导致行为分叉、修复只改一处漏改另一处。

> 对应 wiki-code-dev **CODING-FE-DOWNLOAD-ROBUST / FR-DL-3 / FR-DL-4**；
> 与 **FR-093（重入守卫）**、**FR-087（ObjectURL 生命周期）** 协同。

## 检查清单

- [ ] 移动端下载失败是否有显式错误提示（Toast/文案），非静默
- [ ] 移动端是否复用桌面端同一下载工具与错误出口（非各自实现）
- [ ] 是否无「catch 空块吞掉下载错误」的写法
- [ ] 401/404/超时/解析失败等分支是否都有用户可见反馈
