# 限流韧性审查规则（BR-063）

> 复盘来源：SEA / 多机部署与代理转发场景下，限流逻辑出现三类问题——(1) 反向代理注入 X-Forwarded-For 后，服务用 `request.ip`（trustProxy 默认 false）取到的是代理自身 IP，导致限流对所有用户共享一个桶、或针对错误 IP；(2) 用无界 `Map` 累积每个 IP 的命中时间戳，长时间运行内存泄漏；(3) 校验令牌用可变时间比较，存在时序侧信道。测试中还发现固定窗口在 60s 边界跨过时会偶发触发 429（flake），故测试必须时钟无关。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"限流韧性审查参数（rate_limit_resilience）"章节读取，禁止在本规则文件硬编码阈值或窗口值。

## Trigger Keywords

X-Forwarded-For, trustProxy, app.set('trust proxy', request.ip, rateLimit, sliding window, bounded window, sweep, Map, constant-time, timing attack, clock-independent, 60s boundary, fixed window, token bucket, client IP, verify, timeSafeEqual

## Rules

### BR-063-1：反向代理下须从 X-Forwarded-For 还原真实客户端 IP（trustProxy off）

- **Severity**: critical
- **Description**: 当服务部署在反向代理 / SEA 之后，`trustProxy` 默认 `false` 时 `request.ip` 取到的可能是代理节点 IP。限流须用 `X-Forwarded-For` 的最左非信任 IP（或配置的可信跳数）作为限流键，避免"所有用户共享一个限流桶"或"针对代理 IP 限流"的误判。评审时确认：限流键提取函数优先读取 `X-Forwarded-For` 头部并用 `config.rate_limit_resilience.trusted_proxy_hop` 剔除可信跳数；未显式开启 `trust proxy` 时禁止直接用 `request.ip` 作限流键。

  **双维度键（已鉴权端点）**：对已通过鉴权的端点，限流键建议组合「真实客户端 IP + 用户名」双维度（`rate_limit_resilience.dual_dimension_key` 默认为 `true`）。仅按 IP 限流时，(a) 同一 NAT/代理出口下的多用户会互相牵连（一个用户打满共享 IP 桶，其余被误限）；(b) 单一已认证用户可耗尽整个共享 IP 桶影响同网段他人。组合 `ip + username` 后，桶粒度精确到"某用户从某 IP"，既隔离不同用户、又防止单用户滥用共享 IP 配额。匿名端点（无用户名）仍仅按 IP 限流。
- **Suggested fix**:

```typescript
// 错误：信任链默认关闭，request.ip 实为代理 IP，限流键错误
const key = request.ip; // ❌ 代理场景下取到 127.0.0.1 / 代理 IP

// 正确：从 X-Forwarded-For 还原真实客户端 IP
function clientKey(req: FastifyRequest): string {
  const xff = req.headers['x-forwarded-for'];
  if (typeof xff === 'string' && xff.length > 0) {
    const hops = xff.split(',').map(s => s.trim());
    const trusted = config.rate_limit_resilience.trusted_proxy_hop; // 剔除最右 trusted 跳数
    return hops.slice(0, Math.max(1, hops.length - trusted))[0] ?? req.ip;
  }
  return req.ip;
}
```

### BR-063-2：滑动/有界窗口 + 定时 sweep，禁止无界 Map

- **Severity**: critical
- **Description**: 为每个 IP 累积命中时间戳的 `Map` 若从不清空会随运行时间无限增长（内存泄漏）。必须使用有界滑动窗口：每个桶只保留窗口内的时间戳、由定时 `sweep` 任务删除过期桶，且 `Map` 大小受 `max_buckets` 上限保护（超限用 LRU 淘汰最旧桶）。评审时确认：限流实现含周期性 sweep（或惰性剔除过期条目），且无"无界 Map 永久累积"的代码路径。
- **Suggested fix**:

```typescript
// 错误：无界 Map，运行越久内存越大
const hits = new Map<string, number[]>();
function hit(ip: string) {
  const arr = hits.get(ip) ?? [];
  arr.push(Date.now());
  hits.set(ip, arr); // ❌ 永不清理
}

// 正确：滑动窗口 + 惰性剔除 + 有界桶数
const WINDOW = config.rate_limit_resilience.window_ms;
const hits = new Map<string, number[]>();
function hit(ip: string): boolean {
  const now = Date.now();
  const arr = (hits.get(ip) ?? []).filter(t => now - t < WINDOW); // 惰性剔除过期
  if (arr.length >= config.rate_limit_resilience.max_per_window) return false;
  arr.push(now);
  hits.set(ip, arr);
  if (hits.size > config.rate_limit_resilience.max_buckets) {
    hits.delete(hits.keys().next().value!); // LRU 兜底
  }
  return true;
}
```

### BR-063-3：令牌/密钥校验须常量时间，禁止可变时间比较

- **Severity**: critical
- **Description**: 限流令牌、CSRF 令牌或共享密钥的比较若用 `===` / `String.localeCompare` 等可变时间实现，会暴露时序侧信道，攻击者可逐字节推断令牌。必须用常量时间比较（Node 用 `crypto.timingSafeEqual`，且比较前做长度归一化避免长度泄漏）。评审时确认：任何安全令牌比较路径都使用 `timingSafeEqual`，而非普通 `===`。
- **Suggested fix**:

```typescript
// 错误：普通 === 比较，时间随前缀匹配长度变化
if (providedToken === expectedToken) { /* ❌ 时序侧信道 */ }

// 正确：常量时间比较
import { timingSafeEqual } from 'crypto';
function safeEqual(a: string, b: string): boolean {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ab.length !== bb.length) return false; // 长度不等直接 false，但仍走 timingSafeEqual
  return timingSafeEqual(ab, bb);
}
```

### BR-063-4：限流相关测试须时钟无关，避免 60s 边界 flake

- **Severity**: suggestion
- **Description**: 固定窗口限流跨越整分钟 / 60s 边界时会偶发把两次本应同窗口的命中判为不同窗口，导致 CI 偶发 429（flake）。测试必须用注入的假时钟（如 `vi.useFakeTimers` / `sinon.useFakeTimers` 或显式 `now` 参数），不依赖真实 `Date.now()` 与墙钟边界。评审时确认：限流单测不依赖真实时间、不假设"两次调用落在同一自然分钟"。
- **Suggested fix**:

```typescript
// 错误：依赖真实时间，跨 60s 边界偶发 flake
it('limits to 5/min', async () => {
  for (let i = 0; i < 6; i++) await hit(ip); // ❌ 若跨分钟边界，第6次可能不触发
  expect(blocked).toBe(true);
});

// 正确：注入假时钟，确定性
it('limits to 5/min', () => {
  vi.useFakeTimers();
  const now = 1_000_000;
  vi.setSystemTime(now);
  for (let i = 0; i < 6; i++) hit(ip, now + i * 1000); // 显式 now 参数
  expect(blocked).toBe(true);
  vi.useRealTimers();
});
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `rate_limit_resilience.enabled` | `true` | 是否启用本组规则（BR-063） |
| `rate_limit_resilience.severity_br063_1` | `critical` | BR-063-1 限流键错误违规级别 |
| `rate_limit_resilience.severity_br063_2` | `critical` | BR-063-2 无界 Map 违规级别 |
| `rate_limit_resilience.severity_br063_3` | `critical` | BR-063-3 可变时间比较违规级别 |
| `rate_limit_resilience.severity_br063_4` | `suggestion` | BR-063-4 时钟无关测试违规级别 |
| `rate_limit_resilience.trusted_proxy_hop` | `1` | 可信代理跳数（从右剔除） |
| `rate_limit_resilience.dual_dimension_key` | `true` | 已鉴权端点限流键是否组合「真实 IP + 用户名」双维度 |
| `rate_limit_resilience.window_ms` | `60000` | 滑动窗口长度 |
| `rate_limit_resilience.max_per_window` | `60` | 每窗口最大命中数 |
| `rate_limit_resilience.max_buckets` | `10000` | 桶数上限（LRU 兜底） |
| `rate_limit_resilience.timing_safe_equal_required` | `true` | 令牌比较须常量时间 |

## 检查方式

1. **限流键检查**：Grep `request.ip` 与 `X-Forwarded-For`，确认限流键提取优先用 `X-Forwarded-For` 且按 `trusted_proxy_hop` 剔除；未开 `trust proxy` 时直接用 `request.ip` → **BR-063-1 违规**。对已鉴权端点，确认限流键组合「真实 IP + 用户名」双维度（`dual_dimension_key` 为 `true`）；仅按 IP 限流导致同网段用户互相牵连 / 单用户耗尽共享 IP 桶 → **BR-063-1 双维度违规**。
2. **无界 Map 检查**：Grep 限流实现中的 `new Map`，确认有周期性 sweep / 惰性剔除过期条目 + `max_buckets` LRU 兜底；纯累积无清理 → **BR-063-2 违规**。
3. **常量时间检查**：Grep 安全令牌比较处的 `===`，确认改用 `timingSafeEqual`；可变时间比较 → **BR-063-3 违规**。
4. **测试时钟检查**：Grep 限流测试中的 `Date.now()` / `useFakeTimers`，确认用注入假时钟；依赖真实墙钟边界 → **BR-063-4 违规**（suggestion）。

## 与其他规则的关系

- 与 BR-057（长/短任务架构分离）联动：破坏性端点限流值从 config 读取，不得硬编码。
- 与 BR-034（配置化参数检测）联动：限流阈值 / 窗口 / 可信跳数均须 config 化。
- 与 BR-067（严格路径穿越）同为安全类规则，限流是纵深防御的一环。
- 与 CODING-RATE-LIMIT-RESILIENCE（限流韧性 / 多机部署）对应：本规则是 CODING-RATE-LIMIT-RESILIENCE 的后端审查视角。
