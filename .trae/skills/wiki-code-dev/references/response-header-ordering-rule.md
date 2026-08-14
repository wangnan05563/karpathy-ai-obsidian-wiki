# Response Header Ordering Rule（响应头时序：成功读取后再设置）

## 触发关键词

Content-Disposition, Content-Type, reply.header, 下载, download, 流式, 附件,
响应头, 头时序, 半截响应, 错误路径, 成功路径, 文件流出

## 规则

### RH-1：Content-Disposition / Content-Type 等响应头须在「成功读取内容后、发送体前」设置

**严重级别**：major

凡是「先读文件/资源、再发二进制/附件响应」的 handler，`reply.header('Content-Disposition', ...)`
等响应头必须放在**成功读取之后**、`reply.send(...)` 之前。读取失败的分支不得提前设置这些头。

**为什么**：早期实现在 `try` 之前或读取前就 `reply.header('Content-Disposition', ...)`，
一旦后续 `vault.readFile` 抛错进入 `catch`，响应已带上 `attachment` 头却回的是错误 JSON——
客户端（尤其移动端）会把它当成一个「损坏的下载文件」而非「错误提示」，造成
「明明报错却弹出保存框」的误导，且难以排查。

**正确示例**：

```typescript
try {
  const buffer = await vault.readFileBuffer(query.path);
  reply.header('Content-Type', BINARY_CONTENT_TYPES[ext] || 'application/octet-stream');
  reply.header('Content-Disposition', buildAttachmentHeader(query.path)); // ✅ 读取成功后才设头
  return void reply.send(buffer);
} catch (err) {
  const { status, message } = mapVaultReadError(err);
  return void reply.code(status).send({ error: message }); // ✅ 错误路径只置状态码，无 Content-Disposition
}
```

**错误示例**：

```typescript
// ❌ 读取前就设头：读取失败仍带 attachment 头，误导客户端
reply.header('Content-Disposition', buildAttachmentHeader(query.path));
const buffer = await vault.readFileBuffer(query.path);
return void reply.send(buffer);
```

### RH-2：错误路径只置状态码与错误体，绝不携带 Content-Disposition

**严重级别**：major

`catch` 分支只应 `reply.code(status).send({ error })`，不设置 `Content-Disposition` /
`Content-Type`（除必要错误 JSON 的 `application/json`）。响应语义必须「要么完整附件、要么纯错误」，
不允许「错误响应却带附件头」的中间态。

> 与 wiki-backend-code-review **BR-100** 一致；与 **CODING-DOWNLOAD-AUTH / DA-1**、
> **CODING-VAULT-ERRCODE-PRESERVE / VE-1** 协同（错误路径同时要保证正确状态码）。

## 检查清单

- [ ] 响应头（Content-Disposition / Content-Type）是否在成功读取之后、send 之前设置
- [ ] 错误（catch）分支是否只置状态码 + 错误体，不携带 Content-Disposition
- [ ] 是否不存在「先 set 头、后可能抛错」的半截响应路径
- [ ] 二进制与文本分支是否都遵循同一头时序约定
