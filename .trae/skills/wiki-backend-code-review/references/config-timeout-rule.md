# 超时/阈值可配置化（禁止硬编码）（BR-079）

> 复盘来源：`edgeTtsClient.ts` 把合成超时硬编码为 `30000` 毫秒，弱网/代理环境偶发超 30s 被中断，调优须改代码重发。修正：超时改为从配置读取 `edgeTtsTimeoutMs`（默认 30s，可配），与 BR-053 超时链式 / BR-055 超时分级一致。对应 wiki-code-dev CODING-CONFIG-TIMEOUT（扩展 BR-034 配置化边界）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"config_timeout"章节读取，禁止在本规则文件硬编码毫秒字面量。

## Trigger Keywords
setTimeout, AbortSignal.timeout, 30000, 30_000, 60000, timeout, fetch, execFileSync, 超时, 硬编码, config

## Rules

### BR-079-1: 超时须从配置读取，禁硬编码字面量

- **Severity**: critical
- **Description**: 所有超时 / 阈值须引用配置键（如 `config.edgeTtsTimeoutMs`），禁止在调用处写死 `30000` / `30_000` / `setTimeout(fn, 30000)`。配置键默认值与注释须说明单位与适用场景。
- **Suggested fix**:
```typescript
// ❌ 硬编码
const res = await fetch(url, { signal: AbortSignal.timeout(30000) })
// ✅ 配置驱动
const res = await fetch(url, { signal: AbortSignal.timeout(config.edgeTtsTimeoutMs) })
```

### BR-079-2: 多层级超时须自下而上递增

- **Severity**: suggestion
- **Description**: 涉及多层调用（前端 → 后端 → 外部 API）时，各层超时从同一份配置读取且上层 ≥ 下层 × `config_timeout.margin_multiplier`（1.5），禁止各层独立硬编码导致上层先断。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `config_timeout.enabled` | `true` | 是否启用本规则 |
| `config_timeout.timeout_keys` | `edgeTtsTimeoutMs` | 须配置化的超时键清单 |
| `config_timeout.default_ms` | `30000` | 超时默认毫秒 |
| `config_timeout.forbidden_literal_ms` | `30000,30_000,60000` | 禁止直接在代码出现硬编码毫秒字面量 |
| `config_timeout.margin_multiplier` | `1.5` | 多层超时递增倍数（与 BR-053 对齐） |

## 检查方式

1. Grep 检索 `setTimeout(` / `AbortSignal.timeout(` / `execFileSync(..., { timeout:` 调用点。
2. 若超时参数为 `config_timeout.forbidden_literal_ms` 中的硬编码字面量（非配置引用）→ BR-079-1 违规。
3. 多层调用各层超时若存在且上层 < 下层 × `margin_multiplier` → BR-079-2 违规。

## 适配新项目

- **不同框架**：超时 API 各异（Go `context.WithTimeout` / Python `asyncio.wait_for`），规则核心"超时从配置读取、禁硬编码"不变。
- **与 BR-053/BR-055 协同**：本规则聚焦单点超时不可硬编码，链式递增与分级策略由 BR-053 / BR-055 覆盖。
