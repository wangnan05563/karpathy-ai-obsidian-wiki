# Rule Catalog - Update Check Backend (Cache & Offline Mode)

## Scope
- Covers: 后端"检查更新"接口的缓存实现、离线模式降级、响应字段规范化、外部 API 调用频率控制。
- Does NOT cover: 前端状态机与定时器清理（属于前端审查范畴）、PWA Service Worker 缓存、CDN 缓存策略。

> 所有可配置参数（缓存 TTL、离线模式开关、响应字段、外部 API 超时等）集中定义在 [config/review-config.md](../config/review-config.md) 的"检查更新后端审查参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### UCB-1: 检查更新接口必须实现后端缓存

IsUrgent: True
Category: Update Check Backend

### Description

`/api/about/check-update` 类接口必须实现后端内存缓存，缓存 TTL 由 `check_update.cache_ttl_ms` 配置（默认 5 分钟）。每次外部 GitHub API 调用结果缓存到内存，TTL 内的请求直接返回缓存值。

无缓存的危害：
- 前端每次轮询都触发后端向 GitHub API 真实请求，触发 GitHub 限流（未认证 60 次/小时/IP）
- 高并发下外部 API 调用堆积，增加后端响应延迟
- 网络抖动时频繁失败，前端状态机频繁切换 error/latest

### Judgment Logic

1. 在目标路由文件（如 `routes/about.ts`）中搜索 `check-update` / `checkUpdate` / `has_update` 关键词。
2. 检查是否存在模块级缓存变量（如 `let updateCache: { data: UpdateResult; expiresAt: number } | null = null`）。
3. 验证缓存命中逻辑：`if (updateCache && Date.now() < updateCache.expiresAt) return updateCache.data`。
4. 验证缓存写入逻辑：外部 API 调用成功后 `updateCache = { data, expiresAt: Date.now() + cache_ttl_ms }`。
5. 验证缓存失效逻辑：外部 API 调用失败时不刷新缓存（保持旧值供降级），仅在缓存过期或首次调用时才发起真实请求。

### UCB-2: 离线模式必须固定返回 has_update: false

IsUrgent: True
Category: Update Check Backend

### Description

当 `check_update.offline_mode: true`（项目无外网通道或无 GitHub Release 通道）时，后端必须固定返回 `{ has_update: false, source: 'local' }`，禁止发起任何外部 API 调用。

离线模式适用场景：
- 内网部署项目（无公网出口）
- 项目无 GitHub Release 通道（如私有仓库）
- 演示/教学环境（避免外部依赖）

### Judgment Logic

1. 读取 `config/review-config.md` 中 `check_update.offline_mode` 配置值。
2. 在 `routes/about.ts` 中检查 `check-update` 接口实现。
3. 若 `offline_mode: true`，验证接口直接返回 `{ has_update: false, source: 'local', current_version: <package.json version> }`，不发起 fetch/axios 调用。
4. 若 `offline_mode: false`，验证接口实现真实 GitHub API 调用（`https://api.github.com/repos/{owner}/{repo}/releases/latest`）。

### UCB-3: 响应字段必须规范化

IsUrgent: False
Category: Update Check Backend

### Description

`/api/about/check-update` 接口响应必须包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `has_update` | `boolean` | 是否有新版本 |
| `current_version` | `string` | 当前版本号（从 `package.json` 读取） |
| `latest_version` | `string \| null` | 最新版本号（离线模式为 null） |
| `release_url` | `string \| null` | release 详情页 URL（离线模式为 null） |
| `source` | `'github' \| 'local'` | 数据来源：GitHub API 或本地降级 |
| `checked_at` | `number` | 检查时间戳（毫秒） |

字段缺失会导致前端状态机无法正确切换（如缺 `release_url` 则"发现新版本"按钮无法跳转）。

### Judgment Logic

1. 在 `routes/about.ts` 中检查 `check-update` 接口返回对象。
2. 验证上述 6 个字段全部存在且类型正确。
3. 验证 `current_version` 从 `package.json` 的 `version` 字段读取（而非硬编码）。
4. 验证离线模式下 `latest_version` 与 `release_url` 为 `null`（而非空串或 undefined）。

### UCB-4: 外部 API 调用必须有超时与降级

IsUrgent: True
Category: Update Check Backend

### Description

当 `check_update.offline_mode: false` 时，外部 GitHub API 调用必须：
- 设置超时（由 `check_update.external_api_timeout_ms` 配置，默认 10 秒）
- 超时或失败时降级返回 `{ has_update: false, source: 'local', error: 'fetch_failed' }`
- 不向上游抛错（避免 5xx 响应导致前端状态机卡在 error）

### Judgment Logic

1. 在 `routes/about.ts` 中检查外部 API 调用代码。
2. 验证使用 `AbortController` 或 `Promise.race` 实现超时控制。
3. 验证 try-catch 包裹外部调用，catch 分支返回降级响应而非 `reply.code(500).send(...)`。
4. 验证降级响应 `source: 'local'`，让前端知道这是降级结果而非真实检查。

### Applicable Scenarios

- Fastify + TypeScript 后端的"检查更新"接口实现。
- 内网部署项目（`offline_mode: true`，无外网通道）。
- 公网开源项目（`offline_mode: false`，真实 GitHub API 调用）。

### Non-Applicable Scenarios

- PWA Service Worker 缓存（属于浏览器层，不归后端管）。
- CDN 缓存策略（属于部署层）。
- Electron autoUpdater（属于主进程 IPC 通信）。
- 前端状态机与定时器清理（属于前端审查范畴）。

### Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `check_update.cache_ttl_ms` | `300000`（5 分钟） | 后端内存缓存 TTL（毫秒） |
| `check_update.offline_mode` | `true` | 离线模式开关；`true` 时固定返回 `has_update: false` |
| `check_update.update_endpoint` | `/api/about/check-update` | 后端检查更新接口路径 |
| `check_update.external_api_timeout_ms` | `10000` | 外部 GitHub API 调用超时（毫秒） |
| `check_update.github_api_url_template` | `https://api.github.com/repos/{owner}/{repo}/releases/latest` | GitHub API URL 模板 |
| `check_update.required_response_fields` | `has_update, current_version, latest_version, release_url, source, checked_at` | 必需响应字段列表（逗号分隔） |
| `check_update.fallback_source` | `local` | 降级时 `source` 字段值 |
| `check_update.cache_invalidation_on_error` | `false` | 外部 API 失败时是否刷新缓存（`false` 保持旧值供降级） |

### Example

```typescript
// ❌ Wrong: 无缓存 + 无超时 + 无降级
app.get('/api/about/check-update', async (request, reply) => {
  const res = await fetch('https://api.github.com/repos/owner/repo/releases/latest')
  const data = await res.json()
  // ❌ 无缓存，每次请求都触发 GitHub API
  // ❌ 无超时，网络抖动时一直挂起
  // ❌ 无降级，失败时返回 500
  return { has_update: data.tag_name !== currentVersion }
})

// ✅ Right: 缓存 + 超时 + 降级 + 离线模式
import pkg from '../../../package.json' assert { type: 'json' }

const CURRENT_VERSION = pkg.version
let updateCache: { data: CheckUpdateResult; expiresAt: number } | null = null

interface CheckUpdateResult {
  has_update: boolean
  current_version: string
  latest_version: string | null
  release_url: string | null
  source: 'github' | 'local'
  checked_at: number
}

app.get('/api/about/check-update', async (request, reply) => {
  // ✅ 离线模式：固定返回，不发起外部请求
  if (config.check_update.offline_mode) {
    return {
      has_update: false,
      current_version: CURRENT_VERSION,
      latest_version: null,
      release_url: null,
      source: 'local' as const,
      checked_at: Date.now(),
    } satisfies CheckUpdateResult
  }

  // ✅ 缓存命中：TTL 内直接返回
  if (updateCache && Date.now() < updateCache.expiresAt) {
    return updateCache.data
  }

  // ✅ 外部 API 调用：超时 + 降级
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), config.check_update.external_api_timeout_ms)

    const res = await fetch(config.check_update.github_api_url, {
      signal: controller.signal,
      headers: { 'User-Agent': 'karpathy-wiki' },
    })
    clearTimeout(timeout)

    if (!res.ok) throw new Error(`GitHub API ${res.status}`)
    const data = await res.json()

    const result: CheckUpdateResult = {
      has_update: data.tag_name !== CURRENT_VERSION,
      current_version: CURRENT_VERSION,
      latest_version: data.tag_name,
      release_url: data.html_url,
      source: 'github' as const,
      checked_at: Date.now(),
    }

    // ✅ 缓存写入：TTL 后过期
    updateCache = {
      data: result,
      expiresAt: Date.now() + config.check_update.cache_ttl_ms,
    }

    return result
  } catch (e) {
    request.log.error({ err: e }, 'check-update failed')

    // ✅ 降级：返回 local，不向上游抛 5xx
    return {
      has_update: false,
      current_version: CURRENT_VERSION,
      latest_version: null,
      release_url: null,
      source: 'local' as const,
      checked_at: Date.now(),
    } satisfies CheckUpdateResult
  }
})
```

### Checklist

- [ ] 接口实现模块级内存缓存（`updateCache` 变量），TTL = `check_update.cache_ttl_ms`
- [ ] 缓存命中时直接返回缓存值，不发起外部 API 调用
- [ ] 离线模式 `check_update.offline_mode: true` 时固定返回 `{ has_update: false, source: 'local' }`
- [ ] 响应包含 `check_update.required_response_fields` 全部字段
- [ ] `current_version` 从 `package.json` 读取，不硬编码
- [ ] 外部 API 调用有 `AbortController` 超时控制（默认 10 秒）
- [ ] 外部 API 失败时降级返回 `source: 'local'`，不抛 5xx
- [ ] 外部 API 失败时不刷新缓存（保持旧值供下次降级读取）
