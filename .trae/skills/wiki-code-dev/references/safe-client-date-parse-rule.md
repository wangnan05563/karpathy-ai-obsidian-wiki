# CODING-SAFE-CLIENT-DATE-PARSE — 客户端日期字符串安全解析

> 来源：归档路由接收前端下发的 `ts` 字段直接 `new Date(ts).toISOString()`。当 `ts` 为非法/空字符串时 `new Date('x').toISOString()` 抛 `RangeError` → 未捕获即 500。
> 对应审查规则：后端 BR-082。

## 触发关键词

`new Date(` / `toISOString(` / `ts` / 客户端时间戳 / 归档日期 / ISO 字符串 / 日期解析 / `RangeError`

## 严重级别

🔴 Critical（非法输入 → 500，且属可预防的运行时异常）

## 规则

- **SCD-1**：禁止直接 `new Date(clientString).toISOString()`——非法/空字符串经 `new Date()` 得到 `Invalid Date`，其 `.toISOString()` 抛 `RangeError`。
- **SCD-2**：须用安全解析函数（如 `toArchiveDateStr`）：仅当 `typeof input === 'string' && input.trim()` 非空时 `new Date(input)`；`!Number.isNaN(d.getTime())` 则返回 `d.toISOString().slice(0,10)`；否则返回 `config.safe_date_parse.default_value`（如今天 ISO 日期 `YYYY-MM-DD`）。
- **SCD-3**：安全解析函数须覆盖四类输入：null / undefined / 非字符串 / 无效日期，统一回退默认值；回退值从 config 读取，禁止硬编码"今天"。
- **SCD-4**：解析结果仅用于派生展示/分组（如归档日期目录），不得用于必须精确的时序比较；若需精确时间以服务端 `Date.now()` 为准。

## 正 / 误示例

```ts
// ❌ 误：ts 非法 → RangeError → 500
const dateStr = new Date(body.ts).toISOString().slice(0, 10);

// ✅ 正：安全解析，非法/缺失回退默认
function toArchiveDateStr(input: unknown): string {
  if (typeof input === 'string' && input.trim()) {
    const d = new Date(input);
    if (!Number.isNaN(d.getTime())) return d.toISOString().slice(0, 10);
  }
  return new Date().toISOString().slice(0, 10); // config.safe_date_parse.default_value
}
```

## 检查清单

- [ ] 所有客户端 `ts` / 日期字段入参是否经安全解析（覆盖空串/非法/非字符串）？
- [ ] 解析失败是否回退 config 默认值，而非抛异常或静默用 `Invalid Date`？
- [ ] 安全解析函数是否为模块级复用（避免内联散落）？
