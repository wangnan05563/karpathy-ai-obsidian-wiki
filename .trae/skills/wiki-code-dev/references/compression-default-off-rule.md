# Rule Catalog — 压缩默认关闭 (CODING-COMPRESSION-DEFAULT-OFF)

通用后端编码规范：响应压缩（`@fastify/compress` 等）必须**默认关闭**，仅当配置显式 `enable: true` 时才注册；注册须为**条件式**（`if (config.compress.enable) app.register(compress, {...})`），且压缩阈值（最小字节数、压缩率）全部来自配置。禁止硬编码无条件 `app.register(compression)`。本规则是后端审查条目 `wiki-backend-code-review` BR-091 的上位规范，与 CODING-RESPONSE-HOOK-SAFE 互补（压缩是响应钩子挂死的高频来源）。

> 复盘来源：`@fastify/compress` 默认被注册且 `enable` 配置被忽略，其 `onSend` 钩子在异常时挂死**所有** API。修正：压缩改为默认关闭；通过 `WIKI_DISABLE_COMPRESS=1` / `config.compress.enable` 显式开启；阈值（min 字节数、压缩率）参数化。压测验证关闭须发 ≥100 紧请求确认无拦截生效。

## Scope

- Covers: 任何响应体压缩中间件（`@fastify/compress` / `fastify-compress` / 自定义 gzip 钩子）。
- Does NOT cover: 静态资源由反向代理（nginx）完成的传输层压缩；客户端显式协商且服务端无全局钩子的场景。

## Rules

### CODING-COMPRESSION-DEFAULT-OFF-1: 压缩默认关闭 + 条件注册

IsUrgent: True（严重）
Category: 后端 / 中间件

#### Description

压缩中间件默认不注册；仅当配置 `compress.enable === true` 时 `if (...)` 包裹注册。禁止 `app.register(compress)` 无条件写死。

#### Suggested Fix

```ts
// ✅ 默认关闭，条件注册
if (config.compress.enable) {
  await app.register(compress, {
    threshold: config.compress.threshold_bytes,
    global: true,
    zlibOptions: { level: config.compress.level },
  })
}
```

### CODING-COMPRESSION-DEFAULT-OFF-2: 阈值全部来自配置

IsUrgent: False
Category: 后端 / 配置

#### Description

压缩最小字节数、压缩率/级别、白名单 content-type 均来自 `config.compress.*`，禁止硬编码 `1024` / `0.3` / `['application/json']` 等字面量。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `compression.enabled` | `false` | 压缩默认关闭（显式开启才注册） |
| `compression.threshold_bytes` | `1024` | 小于此字节数的响应不压缩（配置化） |
| `compression.level` | `6` | zlib 压缩级别（配置化） |
| `compression.disable_env` | `WIKI_DISABLE_COMPRESS` | 全局硬关闭开关环境变量名 |
| `compression.severity` | `major` | 压缩无条件注册/硬编码阈值的违规级别 |
