# Rule Catalog — 超时/阈值可配置化（禁止硬编码） (CODING-CONFIG-TIMEOUT)

通用编码规范：任何超时（网络请求、子进程、SSE、轮询）、重试次数、批量大小等"魔法数字"都须从配置读取（config / 环境变量），禁止在代码里写死字面量（如 `30000`、`30_000`）。硬编码超时在不同网络 / 代理环境下要么过早断开、要么永久挂起，且无法在不改代码的情况下调优。本规则是后端审查条目 `wiki-backend-code-review` BR-079 与 BR-034（配置化边界）的泛化上位规范。

> 复盘来源：`edgeTtsClient.ts` 把合成超时硬编码为 `30000` 毫秒。在弱网 / 代理环境偶发合成超过 30s 被中断；调优须改代码重发。修正：超时改为从配置读取 `EDGE_TTS_TIMEOUT_MS`（默认 30s，可配），与既有 `BR-053` 超时链式 / `BR-055` 超时分级一致。

## Scope

- Covers: 任何 timeout / retry / batch-size / poll-interval / threshold 等数值参数。
- Does NOT cover: 编译期常量（如数组长度上限的安全兜底）、与运行时环境无关的物理常量。

## Rules

### CODING-CONFIG-TIMEOUT-1: 超时须从配置读取，禁硬编码字面量

IsUrgent: True（严重）
Category: 配置化 / 可靠性

#### Description

所有超时 / 阈值须引用配置键（如 `config.edgeTtsTimeoutMs`），禁止在调用处写死 `30000` / `30_000` / `setTimeout(fn, 30000)`。配置键默认值与注释须说明单位与适用场景。

#### Suggested Fix

```ts
// ❌ 硬编码
const res = await fetch(url, { signal: AbortSignal.timeout(30000) })
// ✅ 配置驱动
const res = await fetch(url, { signal: AbortSignal.timeout(config.edgeTtsTimeoutMs) })
```

### CODING-CONFIG-TIMEOUT-2: 多层级超时须自下而上递增

IsUrgent: False（建议级）
Category: 配置化 / 可靠性

#### Description

涉及多层调用（前端 → 后端 → 外部 API）时，各层超时从同一份配置读取且上层 ≥ 下层 × 1.5（与 `BR-053` 一致），禁止各层独立硬编码导致上层先断。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_timeout.enabled` | `true` | 启用本组规则（CODING-CONFIG-TIMEOUT） |
| `config_timeout.timeout_keys` | `edgeTtsTimeoutMs` | 须配置化的超时键清单（可扩展） |
| `config_timeout.default_ms` | `30000` | 超时默认毫秒 |
| `config_timeout.forbidden_literal_ms` | `30000,30_000,60000` | 禁止在代码中直接出现的硬编码毫秒字面量（审查告警） |
| `config_timeout.margin_multiplier` | `1.5` | 多层超时递增倍数（与 BR-053 对齐） |
