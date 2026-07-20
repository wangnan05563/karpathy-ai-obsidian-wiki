# 更新检查缓存规则

> 防止每次访问"关于"页都发起外部 HTTP 请求查询最新版本，导致 API 限流或网络抖动。
> 本规则由历史问题复盘提炼（about.ts 的 check-update 接口需要 5 分钟缓存 + 5 秒延迟首次检查）。

## 触发关键词

- `check-update` / `latest version` / `release`
- `cache` / `TTL` / `cache_ttl_ms`
- `setTimeout` / `setInterval` / `polling`
- `GitHub API` / `release feed`

## 规则

### R-1 后端更新检查必须有缓存（critical）

`/api/about/check-update` 类接口必须实现服务端缓存，禁止每次请求都发起外部 HTTP 调用。

**缓存策略**：
- 缓存 TTL 由 config `check_update.cache_ttl_ms` 管理（默认 5 分钟）
- 缓存命中时直接返回缓存数据，附带 `source: "cache"` 标志
- 缓存失效时发起外部请求，成功后写入缓存

**为什么需要**：避免高频访问触发外部 API 限流；避免网络抖动导致每次请求都失败。

### R-2 前端首次检查延迟（suggestion）

页面加载后不应立即触发检查更新（影响首屏性能），应延迟 `check_update.first_check_delay_ms`（默认 5 秒）后首次检查。

### R-3 轮询间隔不得小于缓存 TTL（critical）

前端轮询间隔 `check_update.poll_interval_ms` 必须 ≥ 后端缓存 TTL `check_update.cache_ttl_ms`，否则每次轮询都命中缓存失效，缓存形同虚设。

### R-4 离线/无外网通道的降级（critical）

当项目无外网发布通道（如内网部署、私有 fork）时，`check-update` 接口必须返回固定值 `has_update: false, source: "local"`，禁止发起外部请求。

**判断逻辑**：config `check_update.release_feed_url` 为空或 `check_update.offline_mode` 为 true 时，跳过外部请求。

### R-5 状态机必须有 5 态（critical）

前端更新检查状态机必须覆盖以下 5 态，避免出现"卡在 loading 永不返回"：

| 状态 | 含义 | 自动转移 |
|------|------|---------|
| `idle` | 初始/可重新检查 | 用户点击或定时器触发 → loading |
| `loading` | 检查中 | 成功 → latest/newer；失败 → error |
| `latest` | 已是最新 | 3 秒后自动回 idle |
| `newer` | 有新版本 | 显示更新按钮 |
| `error` | 检查失败（network/server）| 用户可重试 |

**为什么 latest 3 秒后回 idle**：避免按钮长期显示"已是最新"占用视觉焦点。

### R-6 定时器必须在 onBeforeUnmount 清理（critical）

`setTimeout`/`setInterval` 必须在组件卸载时清理，避免内存泄漏。建议用 `idleTimer`/`pollTimer` 变量记录句柄。

## 反例

```typescript
// 反例 1：无缓存，每次请求都发外部 HTTP
app.get('/api/about/check-update', async (_req, reply) => {
  const res = await fetch('https://api.github.com/repos/.../releases/latest');
  return reply.send(await res.json()); // ❌ 无缓存
});

// 反例 2：状态卡在 loading
async function checkUpdate() {
  updateState.value = { kind: 'loading' };
  const result = await fetch('/api/about/check-update');
  // ❌ 未处理 catch，未设置 latest/error 状态
}

// 反例 3：定时器未清理
onMounted(() => {
  setInterval(checkUpdate, 5 * 60 * 1000); // ❌ 未记录句柄，无法清理
});
```

## 正例

```typescript
// 后端：5 分钟缓存
const CHECK_UPDATE_CACHE_TTL_MS = 5 * 60 * 1000; // 从 config 读取
let checkUpdateCache: { data: unknown; ts: number } | null = null;

app.get('/api/about/check-update', async (_req, reply) => {
  // 缓存命中
  if (checkUpdateCache && Date.now() - checkUpdateCache.ts < CHECK_UPDATE_CACHE_TTL_MS) {
    return reply.send({ ...checkUpdateCache.data, source: 'cache' });
  }
  // 离线模式
  if (config.check_update.offline_mode) {
    return reply.send({ current, latest: current, has_update: false, source: 'local' });
  }
  // 发起外部请求
  try {
    const res = await fetch(config.check_update.release_feed_url);
    const data = await res.json();
    checkUpdateCache = { data, ts: Date.now() };
    return reply.send({ ...data, source: 'remote' });
  } catch (err) {
    // 失败时返回缓存或降级
    return reply.send({ has_update: false, source: 'error' });
  }
});

// 前端：5 态状态机 + 定时器清理
type UpdateState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'latest' }
  | { kind: 'newer'; url: string; latest: string }
  | { kind: 'error'; reason: 'network' | 'server' };

const updateState = ref<UpdateState>({ kind: 'idle' });
let idleTimer: ReturnType<typeof setTimeout> | null = null;
let pollTimer: ReturnType<typeof setInterval> | null = null;

async function checkUpdate() {
  updateState.value = { kind: 'loading' };
  try {
    const res = await fetch('/api/about/check-update');
    const data = await res.json();
    if (data.has_update) {
      updateState.value = { kind: 'newer', url: data.url, latest: data.latest };
    } else {
      updateState.value = { kind: 'latest' };
      // 3 秒后自动回 idle
      idleTimer = setTimeout(() => {
        idleTimer = null;
        if (updateState.value.kind === 'latest') {
          updateState.value = { kind: 'idle' };
        }
      }, 3000);
    }
  } catch {
    updateState.value = { kind: 'error', reason: 'network' };
  }
}

onMounted(() => {
  // 首次检查延迟 5 秒
  setTimeout(checkUpdate, 5000);
  // 轮询间隔 5 分钟（≥ 后端缓存 TTL）
  pollTimer = setInterval(checkUpdate, 5 * 60 * 1000);
});

onBeforeUnmount(() => {
  if (idleTimer) clearTimeout(idleTimer);
  if (pollTimer) clearInterval(pollTimer);
});
```

## 适用场景

- 客户端应用有"检查更新"功能的场景
- 内网部署/私有 fork（无外网发布通道）
- 需要轮询外部 API 的功能（避免限流）

## 不适用场景

- 服务端推送更新（WebSocket / SSE）
- 一次性检查（无需缓存）
- CI/CD 流水线（由编排器触发，无用户交互）
