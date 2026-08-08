# CODING-INTEGER-INDEX-VALIDATION — 客户端序号/数组下标整数校验

> 来源：归档路由用 `body.messageIndex` 经 `getSession(threadId).messages[messageIndex]` 取内容。当 `messageIndex` 为非整数（小数/字符串/缺失）时得到 `undefined` → 后续 `record.xxx` 抛错 → 500；也错失了"参数非法应 400"的契约。
> 对应审查规则：后端 BR-083。

## 触发关键词

`messageIndex` / `messages[` / 数组下标 / 客户端序号 / `index` 参数 / `Number.isInteger` / 请求体下标 / 缺失字段

## 严重级别

🔴 Critical（非法输入 → 500 或 undefined 访问）

## 规则

- **IIV-1**：客户端下发的数组下标 / 序号参数（如 `messageIndex`）必须用 `Number.isInteger` 校验；非整数（小数 / 字符串 / 缺失）直接返回 `config.integer_index.reject_status`（默认 400），禁止直接用作数组下标。
- **IIV-2**：校验顺序：先判空（存在性）→ 再 `Number.isInteger` → 再范围检查（如 ≥ 0）。任一不满足即拒绝，错误文案从 config 读取。
- **IIV-3**：服务端取数（`getSession` 等）失败得到 `undefined record` 时，若走"请求体内容"分支则不应再依赖 `record` 变量，避免 `record is not defined` 类 ReferenceError。
- **IIV-4**：校验须发生在任何数组访问之前（短路），不得在访问后靠 `?.` 掩盖非法输入。

## 正 / 误示例

```ts
// ❌ 误：小数/字符串下标 → messages[1.5] = undefined → 下游 500
const record = store.getSession(threadId)?.messages[body.messageIndex];

// ✅ 正：先整数校验，非法即 400
if (typeof body?.messageIndex !== 'number' || !Number.isInteger(body.messageIndex)) {
  return reply.code(config.integer_index.reject_status).send({ error: 'messageIndex 必须为整数' });
}
```

## 检查清单

- [ ] 所有 `body.xxxIndex` / 客户端序号用于数组访问前是否 `Number.isInteger` 校验？
- [ ] 校验失败是否返回 400（而非 undefined 访问 → 500）？
- [ ] 是否覆盖"缺失 / 小数 / 字符串 / 负数"四类非法？
