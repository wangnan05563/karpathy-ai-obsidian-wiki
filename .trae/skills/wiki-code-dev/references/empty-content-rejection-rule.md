# CODING-EMPTY-CONTENT-REJECTION — 归档/持久化端点拒绝空内容

> 来源：归档路由在 `question` 与 `answer` 同时缺失时仍会创建空 `qa-*.md` 节点（无内容、无价值、污染检索）。属"静默 no-op + 脏数据"。
> 对应审查规则：后端 BR-085（Critical）。

## 触发关键词

`archive` / `writeFile` / `question` / `answer` / 空内容 / 空归档 / 400 / 必填字段 / 节点创建

## 严重级别

🔴 Critical（创建空知识节点 / 静默 no-op 脏数据）

## 规则

- **ECR-1**：归档/持久化端点须拒绝空 payload：所有必填内容字段（如 `question` 与 `answer`）同时缺失/为空时，返回 `config.empty_content.reject_status`（默认 400）+ 明确错误文案，禁止创建空节点。
- **ECR-2**：空内容判定须覆盖"字段存在但为空串/纯空白"与"字段完全缺失"两类——禁止仅判 `!question && !answer`（undefined）而漏掉空串。
- **ECR-3**：拒绝须发生在写入 vault **之前**（短路），不得先写再回滚 / 先写再删。
- **ECR-4**：必填内容字段清单从 config（`empty_content.required_fields`）读取，不硬编码字段名。

## 正 / 误示例

```ts
// ❌ 误：空内容仍写 vault，生成空 qa 节点
if (!question && !answer) { /* 没拦，直接写 */ }

// ✅ 正：写入前短路拒绝（覆盖空串/纯空白/缺失）
const hasContent = [question, answer].some((v) => typeof v === 'string' && v.trim().length > 0);
if (!hasContent) {
  return reply.code(config.empty_content.reject_status)
    .send({ error: '归档内容为空（question 与 answer 均缺失）' });
}
```

## 检查清单

- [ ] 归档/持久化入口是否对空内容短路 400？
- [ ] 空判定是否覆盖"空串/纯空白"与"缺失"两类？
- [ ] 拒绝是否发生在写入 vault 之前（非先写后删）？
