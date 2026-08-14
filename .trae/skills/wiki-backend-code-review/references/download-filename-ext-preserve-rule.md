# Download Filename Extension Preserve Rule（下载文件名扩展名保留）

## 触发关键词

下载, download, 扩展名, 扩展名丢失, extname, basename, 文件名, .md, .png,
Content-Type, BINARY_EXTENSIONS, TEXT_CONTENT_TYPES, 无后缀, 预览失败

## 规则

### BR-101-1（major）：下载响应须保留文件原始扩展名，禁止静默丢失

下载功能曾因后端 basename 推导或 Content-Type 映射缺失，导致保存文件丢失扩展名
（`.md` → 无后缀、`.png` → 无法预览）。`buildAttachmentHeader` 须基于 `path.basename`
原样保留 `path.extname`；Content-Type 须按扩展名映射（二进制/文本各自的 `EXTENSIONS` 表），
未知文本回退 `text/plain; charset=utf-8`，未知二进制回退 `application/octet-stream`。

**错误示例**：

```typescript
// ❌ 中性名丢失扩展名：vault-file 无 .md/.png，下载后无法识别
const legacyName = `vault-file`; // 丢了 ext
```

**正确示例**（见项目 `buildAttachmentHeader`）：

```typescript
const baseName = path.basename(relPath);
const ext = path.extname(baseName);                       // 保留扩展名
const legacyName = (isAscii ? baseName : `vault-file${ext}`).replace(...); // 非 ASCII 也带 ext
```

### BR-101-2（standard）：二进制/文本扩展名表与 Content-Type 映射须来自配置

`BINARY_EXTENSIONS` / `BINARY_CONTENT_TYPES` / `TEXT_CONTENT_TYPES` 的扩展名与 MIME 映射
须可配置（新增格式只改配置），禁止把「支持哪些扩展名」硬编码死。

> 对应 wiki-code-dev **CODING-CONTENT-DISPOSITION-SAFE / CD-1**（文件名编码）的扩展名兜底维度；
> 与前端 **FR-094（解析保留扩展名）** 协同——后端保证输出带扩展名、前端保证解析保留扩展名。
> 扩展名/MIME 表来自 config（`download_ext_preserve.binary_extensions` / `text_content_types`）。

## 检查清单

- [ ] 下载文件名是否保留原始扩展名（无静默丢失 .md/.png 等）
- [ ] Content-Type 是否按扩展名正确映射（二进制/文本各自表）
- [ ] 未知扩展名是否有合理回退（文本→text/plain、二进制→octet-stream）
- [ ] 扩展名支持表 / MIME 映射是否来自配置（非硬编码）
