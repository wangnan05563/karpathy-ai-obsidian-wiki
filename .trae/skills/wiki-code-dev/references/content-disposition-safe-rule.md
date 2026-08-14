# Content-Disposition Safe Rule（RFC 5987 文件名编码 + 头注入清洗）

## 触发关键词

Content-Disposition, filename*, filename, RFC 5987, 中文文件名, 非 ASCII,
头注入, header injection, CRLF, attachment, 下载文件名, 编码, percent-encode

## 规则

### CD-1：进入响应头的文件名须 RFC 5987 `filename*` 编码 + legacy `filename` 兜庈

**严重级别**：critical

vault 文件名常含中文（如「上海票据交易所.md」）。直接把原始字节塞进 `filename` 会被截断/乱码。
须同时输出：
- `filename*=UTF-8''<percent-encoded>`（RFC 5987，现代浏览器优先）；
- `filename="<ascii-or-neutral>"`（旧浏览器兜底，仅当全 ASCII 时直接用原名，否则用中性名 + 扩展名兜底）。

**正确示例**（见项目 `buildAttachmentHeader`）：

```typescript
function buildAttachmentHeader(relPath: string): string {
  const baseName = path.basename(relPath);
  const ext = path.extname(baseName);
  const isAscii = /^[\x20-\x7e]*$/.test(baseName);
  // 非 ASCII 时用中性名 + 扩展名兜底，避免 legacy filename 乱码
  const legacyName = (isAscii ? baseName : `vault-file${ext}`)
    .replace(/["\\\x00-\x1f\x7f]/g, '_');           // CD-2 清洗
  const encodedName = encodeURIComponent(baseName)
    .replace(/'/g, '%27').replace(/\(/g, '%28')
    .replace(/\)/g, '%29').replace(/\*/g, '%2A');    // RFC 5987 attr-char 不含 '()*，须转义
  return `attachment; filename="${legacyName}"; filename*=UTF-8''${encodedName}`;
}
```

### CD-2：清洗可破坏响应头结构的字符（CRLF / 引号 / 反斜杠 / 控制字符）

**严重级别**：critical

文件名若含 `\r` `\n` `"` `\` 或控制字符（`\x00-\x1f` `\x7f`），会**注入/截断 HTTP 响应头**
（响应头分裂攻击，CWE-113），或破坏 `filename="..."` 引号结构。必须在编码前用白名单/黑名单清洗。

**为什么**：下载功能最初直接 `attachment; filename="${baseName}"`，当文件名含换行或引号时，
攻击者可借文件名注入额外响应头、或让浏览器解析出错误文件名。这是生产级头注入隐患。

**错误示例**：

```typescript
// ❌ 原始文件名直接拼接进响应头：含 CRLF/引号即头注入或结构破坏
reply.header('Content-Disposition', `attachment; filename="${baseName}"`);
```

**正确示例**：见 CD-1 的 `legacyName` 正则清洗 + `encodedName` 的 `encodeURIComponent` 转义。
清洗字符集（控制字符范围、`"`、`\`）须来自配置（见 wiki-backend-code-review **BR-098** 的 `header_injection.control_chars_regex`）。

### CD-3：非 ASCII 文件名禁止直接塞 legacy `filename`

**严重级别**：major

`filename`（不带 `*`）只接受 ASCII。若文件名含非 ASCII 字符，不得直接写入 `filename`，
须走 CD-1 的中性名 + `filename*` 编码方案，否则旧浏览器下载会得到乱码/截断名。

> 与 wiki-backend-code-review **BR-098**、前端 **FR-094（Content-Disposition 文件名解析）** 协同：
> 后端负责「安全编码输出」，前端负责「安全解码还原」（RFC 5987 反向解析 + 扩展名保留 + 注入字符清洗）。

## 检查清单

- [ ] 下载响应是否同时输出 `filename*`（RFC 5987 UTF-8 百分号编码）与 legacy `filename` 兜底
- [ ] 进入响应头的文件名是否清洗了 CRLF / 引号 / 反斜杠 / 控制字符（头注入防护）
- [ ] `filename*` 是否对 `' ( ) *` 做了百分号转义（RFC 5987 attr-char 约束）
- [ ] 非 ASCII 文件名是否未被直接写入 legacy `filename`（改用中性名 + 扩展名兜底）
- [ ] 清洗字符集 / 编码细节是否来自 config（非硬编码）
