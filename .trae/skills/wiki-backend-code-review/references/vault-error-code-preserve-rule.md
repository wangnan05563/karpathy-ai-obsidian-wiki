# Vault Error Code Preserve Rule（下游错误码透传，禁止统一吞成 500）

## 触发关键词

错误码, error code, ENOENT, EISDIR, EACCES, EPERM, EOUTSIDE, mapVaultReadError,
catch, 500, 404, 403, 400, 透传, 吞错, 状态码映射, 适配器, vault, fs 错误

## 规则

### BR-099-1（major）：下游/适配器结构化错误码须映射为语义正确的 HTTP 状态，禁统一吞 500

经封装适配器（vault / LLM / 第三方）访问外部系统时，`catch` 必须按 `err.code` 分流：
`EISDIR`→400（下的是目录）、`EACCES|EPERM`→403、`ENOENT`→404（真不存在）、
`EOUTSIDE`→400（路径越界），未知错误才回落 500。统一 `return 500` 会丢失语义信号。

### BR-099-2（standard）：仅未知错误才回落 500，且保留原始 message

只有 `code` 不在白名单（或根本无 `code`，如磁盘故障）才 500；message 应保留 `err.message`
（脱敏后）而非笼统「服务器错误」，便于定位。

> 对应 wiki-code-dev **CODING-VAULT-ERRCODE-PRESERVE / VE-1~VE-2**；
> 与 **BR-076（关键写不得静默吞错）** 互补——同为「禁止静默吞错」家族，本规则针对读错误码透传。
> `code → http` 映射表来自 config（`errcode_map.*`）。

## 检查清单

- [ ] 访问 vault/LLM/第三方适配器的 catch 是否按 `err.code` 分流为语义正确状态
- [ ] 是否无「统一 catch 返回 500」而丢失 ENOENT/EISDIR/EACCES/EOUTSIDE 语义
- [ ] 仅未知错误才回落 500，且保留原始 message（非笼统「服务器错误」）
- [ ] 错误码 → HTTP 状态映射表是否来自 config（非硬编码）
