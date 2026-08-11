# Rule Catalog — 响应/序列化钩子安全 (BR-090)

后端审查条目，对应通用编码规范 `CODING-RESPONSE-HOOK-SAFE`（wiki-code-dev references/response-hook-safe-rule.md）。Fastify 的 `onSend` / `onResponse` / 自定义序列化（`contentTypeParser` / `serializer`）等响应生命周期钩子**不得阻塞、不得抛出未处理异常、不得对全量响应做有副作用的重计算**。这类钩子在**每一条**响应路径上执行，一旦在其中 `await` 阻塞或抛错，会使**所有 API 请求**挂起或 500，而非单端点故障。与 BR-091（压缩默认关闭）互补。

> 复盘来源：`compression.ts` 的 `onSend` 钩子对响应体做同步压缩且未对异常做 fail-open 包裹，某次响应体形态触发钩子内部异常 / 阻塞，导致**所有** API 请求（不止压缩端点）全部挂死。修正：钩子内部全程 `try/catch` fail-open（异常时原样返回），不 `await` 重计算，且压缩等可选能力默认关闭（见 BR-091）。

## Scope

- Covers: 全局注册的 `onSend` / `onResponse` / `setSerializer` / 自定义 `contentTypeParser`；任何"每响应必执行"的插件钩子。
- Does NOT cover: 路由级局部 `onSend`（仅作用于单路由）；纯同步、确定性的轻量头处理（仍建议 fail-open）。

## Rules

### BR-090-1: 钩子必须 fail-open

Category: 后端 / 响应生命周期
Severity: critical

#### Description

`onSend` / `onResponse` 等全局钩子内部必须 `try/catch` 包裹，**异常时原样放行**（返回原始 `payload` / `done()`），不得让单条响应异常中断整条连接或冒泡为全量 500。

#### Suggested Fix

```ts
// ✅ 钩子 fail-open，异常原样放行
fastify.addHook('onSend', async (req, reply, payload) => {
  try {
    if (shouldCompress(reply, payload)) return compress(payload)
    return payload
  } catch (err) {
    req.log?.warn({ err }, 'onSend transform skipped (fail-open)')
    return payload // 异常原样返回，不影响其他请求
  }
})
```

### BR-090-2: 钩子不得阻塞重计算

Category: 后端 / 性能
Severity: suggestion

#### Description

全局 `onSend` 内禁止对大响应体做 `await` 重压缩 / 重序列化等昂贵阻塞操作；如确需，须在受控范围内（阈值配置化）且不阻塞关键路径。

## Configuration Parameters

> 全部参数从 [config/review-config.md](../config/review-config.md) 的"响应钩子安全审查参数（BR-090）"节读取，本规则文件不硬编码任何值。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `response_hook_safe.enabled` | `true` | 启用响应钩子安全审查 |
| `response_hook_safe.hook_names` | `onSend,onResponse,setSerializer,contentTypeParser` | 视为全局响应钩子的注册点 |
| `response_hook_safe.require_fail_open` | `true` | 钩子主体须被 try/catch 包裹且异常放行 |
| `response_hook_safe.severity` | `critical` | 钩子挂死全量 API 的违规级别 |
