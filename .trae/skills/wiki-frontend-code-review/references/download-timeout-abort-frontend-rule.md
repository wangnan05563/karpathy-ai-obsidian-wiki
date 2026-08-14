# Download Timeout / Abort Frontend Rule（下载请求超时与可中断）

## 触发关键词

下载, download, fetch, blob, AbortSignal.timeout, 超时, 挂起, 大文件, 卡死,
downloadVaultFile, signal, 中断, 取消下载

## 规则

### FR-091-1（major）：下载 fetch 必须带可配置超时（`AbortSignal.timeout`）

前端下载二进制/大文件时若后端卡死或网络中断，未设超时的请求会永久挂起，用户无任何反馈。
每个下载 `fetch` 必须传入 `signal: AbortSignal.timeout(<阈值>)`，阈值来自配置（`download_frontend.timeout_ms`），
禁止硬编码 `30000` 之类字面量。

**错误示例**：

```typescript
// ❌ 无超时：后端卡死则请求永久挂起
const resp = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
```

**正确示例**：

```typescript
const timeoutMs = downloadFrontend.timeout_ms ?? 30000; // 来自配置
const resp = await fetch(url, {
  headers: { Authorization: `Bearer ${token}` },
  signal: AbortSignal.timeout(timeoutMs),
});
```

### FR-091-2（suggestion）：超时/中断须给用户可重试反馈

`AbortError` / 超时异常须被 `catch` 捕获并提示用户「下载超时，可重试」，不得静默吞掉或让按钮永久「下载中」。

> 对应 wiki-code-dev **CODING-FE-DOWNLOAD-ROBUST / FR-DL-1**、**CODING-CONFIG-TIMEOUT**；
> 与 **FR-082（认证请求超时兜底）** 同属「异步请求必须设超时」家族。

## 检查清单

- [ ] 下载 fetch 是否带 `AbortSignal.timeout`（阈值来自配置）
- [ ] 是否无硬编码超时字面量（`30000` 等）
- [ ] 超时/AbortError 是否提示用户并可重试（无永久「下载中」）
- [ ] 移动端与桌面端下载是否共用同一超时逻辑（非各自实现）
