# Vault Error Code Preserve Rule（下游错误码透传，禁止统一吞成 500）

## 触发关键词

错误码, error code, ENOENT, EISDIR, EACCES, EPERM, EOUTSIDE, mapVaultReadError,
catch, 500, 404, 403, 400, 透传, 吞错, 状态码映射, 下游适配器, vault, fs 错误

## 规则

### VE-1：下游/适配器返回的结构化错误码须映射为对应 HTTP 状态，禁止统一吞成 500

**严重级别**：major

经封装适配器（vault / LLM / 第三方）访问外部系统时，这些系统返回带 `code` 的
结构化错误（`ENOENT` / `EISDIR` / `EACCES` / `EOUTSIDE` 等）。handler 的 `catch`
必须**按 `code` 分流**为语义正确的 HTTP 状态，禁止统一 `return 500` 把「资源不存在」
误标成「服务器故障」，也禁止把「目录/越界」误标成「不存在」。

**为什么**：下载功能最初统一 `catch { return 500 }`，导致「文件不存在」被标成 500、
「下的是目录」「路径越界」也全是 500——前端/移动端无法区分「真的没这文件」与
「服务端炸了」，重试策略与用户提示全错。错误码是下游给的**语义信号**，吞掉即丢失。

**正确示例**（见项目 `mapVaultReadError`）：

```typescript
function mapVaultReadError(err: unknown): { status: number; message: string } {
  const e = err as (Error & { code?: string }) | null;
  const code = e?.code;
  const message = e?.message || '读取文件失败';
  if (code === 'EISDIR') return { status: 400, message };   // 下的是目录
  if (code === 'EACCES' || code === 'EPERM') return { status: 403, message };
  if (code === 'ENOENT') return { status: 404, message };   // 真·不存在
  if (code === 'EOUTSIDE') return { status: 400, message }; // 路径越界
  return { status: 500, message };                          // 未知错误才回落 500
}
```

**错误示例**：

```typescript
// ❌ 统一吞成 500：丢失 ENOENT/EISDIR/EOUTSIDE 语义
} catch (err) {
  return void reply.code(500).send({ error: '读取失败' });
}
```

### VE-2：仅「未知错误」才回落 500，且保留原始 message

**严重级别**：standard

只有 `code` 不在已知白名单（或根本无 `code`，如磁盘故障、网络中断）时才返回 500；
并且 500 的 message 应保留 `err.message`（脱敏后）而非笼统「服务器错误」，便于定位。

> 与 wiki-backend-code-review **BR-099** 一致；与 **CODING-CRITICAL-WRITE-NO-SWALLOW / BR-076**
> 互补（BR-076 针对「写失败须传播」，本规则针对「读错误码须透传」，同为「禁止静默吞错」家族）。
> 状态码映射表（`code → http`）须来自配置（见 BR-099 的 `errcode_map.*`）。

## 检查清单

- [ ] 访问 vault/LLM/第三方适配器的 catch 是否按 `err.code` 分流为语义正确的 HTTP 状态
- [ ] 是否不存在「统一 catch 返回 500」而丢失 ENOENT/EISDIR/EACCES/EOUTSIDE 语义
- [ ] 仅未知错误才回落 500，且保留了原始 message（非笼统「服务器错误」）
- [ ] 错误码 → HTTP 状态的映射表是否来自 config（非硬编码）
