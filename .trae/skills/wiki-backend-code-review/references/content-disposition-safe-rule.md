# Content-Disposition Safe Rule（RFC 5987 编码 + 头注入清洗）

## 触发关键词

Content-Disposition, filename*, filename, RFC 5987, 中文文件名, 非 ASCII, 头注入,
header injection, CRLF, attachment, 下载文件名, percent-encode, encodeURIComponent

## 规则

### BR-098-1（critical）：进入响应头的文件名须 RFC 5987 `filename*` 编码 + legacy `filename` 兜底

vault 文件名常含中文。须同时输出 `filename*=UTF-8''<encoded>`（现代浏览器优先）与
`filename="<ascii>"`（旧浏览器兜底，非 ASCII 时用中性名 + 扩展名兜底）。直接塞原始字节会乱码/截断。

### BR-098-2（critical）：清洗可破坏响应头结构的字符（CRLF / 引号 / 反斜杠 / 控制字符）

文件名含 `\r` `\n` `"` `\` 或控制字符会注入/截断 HTTP 响应头（CWE-113）。
编码前须用黑名单清洗；字符集来自配置（`header_injection.control_chars_regex`），非硬编码。

### BR-098-3（major）：`filename*` 须对 `' ( ) *` 做百分号转义（RFC 5987 attr-char 约束）

`encodeURIComponent` 不覆盖 `' ( ) *`，须额外转义为 `%27 %28 %29 %2A`，否则部分浏览器解析异常。

### BR-098-4（major）：非 ASCII 文件名禁止直接写入 legacy `filename`

`filename`（不带 `*`）只接受 ASCII；非 ASCII 须走中性名 + `filename*` 方案，禁直接写入。

> 对应 wiki-code-dev **CODING-CONTENT-DISPOSITION-SAFE / CD-1~CD-3**；
> 与前端 **FR-094**（安全解码还原）协同——后端「安全编码输出」、前端「安全解码解析」。
> 编码/清洗字符集与扩展名兜底来自 config（`header_injection.*`、`download_ext_preserve.binary_extensions`）。

## 检查清单

- [ ] 下载响应是否同时输出 `filename*`（RFC 5987 UTF-8 编码）与 legacy `filename` 兜底
- [ ] 进入响应头的文件名是否清洗 CRLF/引号/反斜杠/控制字符（头注入防护）
- [ ] `filename*` 是否对 `' ( ) *` 做百分号转义
- [ ] 非 ASCII 文件名是否被直接写入 legacy `filename`（应改用中性名 + 扩展名）
- [ ] 清洗字符集 / 编码细节是否来自 config（非硬编码）
