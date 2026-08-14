# Content-Disposition Filename Frontend Rule（前端安全解析下载文件名）

## 触发关键词

下载, download, Content-Disposition, filename*, filename, RFC 5987, 文件名解析,
扩展名, 扩展名丢失, 中文文件名, percent-decode, blob, 头注入, 文件名清洗

## 规则

### FR-094-1（major）：前端须正确解码 `filename*`（RFC 5987），还原中文等非 ASCII 文件名

当下载经 `fetch` + `blob` + `URL.createObjectURL` 触发保存时，文件名应从响应的
`Content-Disposition` 头解析。须优先读取 `filename*=UTF-8''<encoded>` 并做 `decodeURIComponent`
反向解码；仅当无 `filename*` 时回退 `filename`（ASCII）。直接 trust 未解码的 `filename*` 会得到乱码名。

**正确示例**：

```typescript
function parseDownloadFilename(header: string | null, fallback: string): string {
  if (!header) return fallback;
  const star = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(header); // RFC 5987
  if (star) {
    try { return decodeURIComponent(star[1]); } catch { /* 落到 filename */ }
  }
  const plain = /filename\s*=\s*"?([^";]+)"?/i.exec(header);
  return plain ? plain[1].trim() : fallback;
}
```

### FR-094-2（major）：解析出的文件名须保留原始扩展名，禁止静默丢失

下载功能曾因后端 basename 推导或前端未透传导致保存文件丢失扩展名（`.md` → 无后缀、`.png` → 无法预览）。
前端拿到的文件名必须保留 `path.extname`，缺失时按 MIME/Content-Type 兜底补扩展名。

### FR-094-3（standard）：文件名须清洗头注入/路径字符后再用于保存

解析出的文件名可能含 `\r` `\n` `"` `/` `\` 等，用于 `a.download` 或写盘前应清洗（去除路径分隔符与控制字符），
避免「文件名注入」破坏保存行为或被用于路径穿越。清洗字符集来自配置。

> 对应 wiki-code-dev **CODING-CONTENT-DISPOSITION-SAFE / CD-1~CD-3**（后端安全编码输出）
> 与后端 **BR-098**；与 **BR-101（下载文件名扩展名保留）** 协同——后端保证输出带扩展名、前端保证解析保留扩展名。
> 解析/清洗用的正则与字符集须来自配置（见前端 review-config `content_disposition_frontend.*`）。

## 检查清单

- [ ] 前端是否优先解码 `filename*`（RFC 5987 UTF-8 百分号解码）还原中文名
- [ ] 无 `filename*` 时是否回退 `filename`（ASCII）且不为空
- [ ] 解析出的文件名是否保留原始扩展名（无静默丢失）
- [ ] 用于保存前是否清洗 CRLF/引号/路径分隔符等注入字符（字符集来自配置）
- [ ] 解码/解析失败是否有 fallback 文件名（非崩溃）
