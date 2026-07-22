# E2E 测试前置服务检查（FR-030）

> 复盘来源：CI 与本地执行 E2E 测试时未先校验前端 dev server / 后端 API 是否已启动，Playwright 直接对未监听端口发起请求，整套测试在第一个用例即以 `ERR_CONNECTION_REFUSED` 失败，浪费 10+ 分钟的浏览器启动开销；且因测试报告无"服务未启动"显式提示，开发者误以为是测试选择器失效。
> 所有可变参数从 config/review-config.md 的 `e2e_precheck_frontend` 字段读取。

## 规则

### FR-030-1：运行 E2E 测试前必须执行前置服务就绪检查

E2E 测试套件（Playwright / Cypress / Selenium 等）在执行任何业务用例前，必须先执行"服务就绪检查"（service preflight check），且检查必须满足：

1. **端口监听检查**：对 `e2e_precheck_frontend.required_ports` 列出的每个端口（如前端 5173、后端 8000），用 `netstat` / `lsof` / `Get-NetTCPConnection` 等检测端口处于 LISTEN 状态。
2. **健康检查接口**：对 `e2e_precheck_frontend.health_endpoints` 列出的每个端点（如 `http://localhost:5173/`、`http://localhost:8000/health`）发起 HTTP GET，要求返回 2xx 状态码且响应时间 < `e2e_precheck_frontend.health_timeout_ms`。
3. **重试与超时**：若检查失败，按 `e2e_precheck_frontend.retry_count` 重试，每次间隔 `e2e_precheck_frontend.retry_interval_ms`。
4. **失败即中止**：所有重试均失败后，必须立即中止测试套件，并在报告中显式输出"服务未就绪"诊断信息（区分前端未起 / 后端未起 / 健康检查超时三种情况），禁止继续执行后续用例。

### FR-030-2：测试报告必须区分"服务异常"与"用例失败"

Playwright / 测试运行器的报告须包含一个独立的 preflight 阶段输出，明确告知：

- 检查的服务列表与状态（pass/fail）。
- 失败服务对应的 `ERR_CONNECTION_REFUSED` 错误码（或等价信息）。
- 建议操作（如 `请先执行 pnpm dev 启动前端开发服务器`）。

禁止把"服务未就绪"导致的失败混入业务用例失败统计——否则用例成功率指标失真，掩盖真实业务问题。

## 适用场景

- 项目使用 Playwright / Cypress / Selenium / Puppeteer 运行 E2E 测试。
- 测试目标为前后端分离项目，前端 dev server 与后端 API 服务为独立进程。
- CI 流水线中先启动服务、再跑测试的工作流。
- 本地开发者运行 `pnpm test:e2e` 前的预检查。

## 不适用场景

- 单元测试 / 组件测试（Vitest / Jest）—— 无外部服务依赖，无需 preflight。
- 测试运行器内置服务启动逻辑（如 Playwright `webServer` 配置 + `url` + `timeout`，本身已含就绪检查 —— 此时只需保证 config 完整，本规则自动满足）。
- Mock 全部后端接口的纯前端 E2E（无需后端服务）。

## 检查流程

```
[开始] 执行 E2E 测试套件
  │
  ▼
[1] preflight: 遍历 required_ports 检查 LISTEN 状态
  │  └─ 任意端口未监听 → 重试 retry_count 次
  │       └─ 仍失败 → [中止测试 + 输出诊断]（FR-030-1）
  │
  ▼ 全部 LISTEN
[2] 遍历 health_endpoints 发起 HTTP GET
  │  └─ 任意端点非 2xx / 超时 → 重试 retry_count 次
  │       └─ 仍失败 → [中止测试 + 输出诊断]（FR-030-1）
  │
  ▼ 全部 2xx
[3] 在报告中输出 preflight pass 段（FR-030-2）
  │
  ▼
[4] 执行业务 E2E 用例
  │
  ▼
[结束]
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `e2e_precheck_frontend.required_ports` | `5173, 8000` | 必须监听的端口列表（逗号分隔，前端 dev + 后端 API） |
| `e2e_precheck_frontend.health_endpoints` | `http://localhost:5173/, http://localhost:8000/health` | 健康检查端点列表（逗号分隔） |
| `e2e_precheck_frontend.health_timeout_ms` | `3000` | 单次健康检查请求超时（毫秒） |
| `e2e_precheck_frontend.retry_count` | `5` | 服务就绪检查失败重试次数 |
| `e2e_precheck_frontend.retry_interval_ms` | `1000` | 重试间隔（毫秒） |
| `e2e_precheck_frontend.abort_on_failure` | `true` | 服务未就绪时是否中止测试 |
| `e2e_precheck_frontend.distinct_report_section` | `true` | 测试报告中是否独立 preflight 段 |
| `e2e_precheck_frontend.connection_refused_indicator` | `ERR_CONNECTION_REFUSED, ECONNREFUSED` | 标识"服务未起"的错误码关键字 |

## 检查方式

1. 在 E2E 测试入口文件（如 `playwright.config.ts`、`e2e/setup.ts`、`conftest.py`）中检索是否存在 preflight 检查代码。
2. 核对检查的端口列表是否覆盖 `required_ports`（前端 + 后端）。
3. 核对健康检查端点是否覆盖 `health_endpoints`，且 HTTP 状态码判断为 2xx（而非仅判断"返回响应"）。
4. 模拟服务未起场景（杀掉 dev server），验证测试在 preflight 阶段即中止而非业务用例阶段失败。
5. 检查测试报告是否含独立 preflight 段，且在失败时输出 `connection_refused_indicator` 关键字与建议操作。

## 正确示例

```ts
// ✅ playwright.config.ts — 使用内置 webServer 配置自动执行就绪检查
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  retries: process.env.CI ? 2 : 0,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report' }],
  ],
  webServer: [
    {
      command: 'pnpm dev',
      port: 5173,                                  // ✅ 端口监听检查
      url: 'http://localhost:5173/',                // ✅ 健康检查端点
      timeout: 30_000,                              // ✅ 启动超时
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'pnpm --filter backend dev',
      port: 8000,
      url: 'http://localhost:8000/health',         // ✅ 后端健康检查
      timeout: 30_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
})
```

```ts
// ✅ 自定义 preflight 脚本（独立于 Playwright）
// e2e/preflight.ts
import net from 'node:net'

const CFG = {
  requiredPorts: [5173, 8000],
  healthEndpoints: ['http://localhost:5173/', 'http://localhost:8000/health'],
  timeoutMs: 3000,
  retryCount: 5,
  retryIntervalMs: 1000,
}

async function checkPort(port: number): Promise<boolean> {
  return new Promise(resolve => {
    const sock = net.connect({ port, host: '127.0.0.1' })
    sock.setTimeout(CFG.timeoutMs)
    sock.on('connect', () => { sock.end(); resolve(true) })
    sock.on('error', () => resolve(false))
    sock.on('timeout', () => { sock.destroy(); resolve(false) })
  })
}

async function checkHealth(url: string): Promise<boolean> {
  try {
    const ctrl = new AbortController()
    const t = setTimeout(() => ctrl.abort(), CFG.timeoutMs)
    const res = await fetch(url, { signal: ctrl.signal })
    clearTimeout(t)
    return res.ok
  } catch {
    return false
  }
}

export async function preflight(): Promise<void> {
  for (let attempt = 1; attempt <= CFG.retryCount; attempt++) {
    const portsOk = await Promise.all(CFG.requiredPorts.map(checkPort))
    const healthOk = await Promise.all(CFG.healthEndpoints.map(checkHealth))

    if (portsOk.every(Boolean) && healthOk.every(Boolean)) {
      console.log(`[preflight] pass on attempt ${attempt}`)
      return
    }

    const failed: string[] = []
    CFG.requiredPorts.forEach((p, i) => {
      if (!portsOk[i]) failed.push(`port ${p} not listening (ERR_CONNECTION_REFUSED)`)
    })
    CFG.healthEndpoints.forEach((u, i) => {
      if (!healthOk[i]) failed.push(`health ${u} did not return 2xx`)
    })

    if (attempt === CFG.retryCount) {
      // ✅ 输出独立 preflight 段，区分服务异常与用例失败
      console.error('[preflight] FAILED — services not ready:')
      failed.forEach(f => console.error('  -', f))
      console.error('  建议操作：pnpm dev 启动前端开发服务器，pnpm --filter backend dev 启动后端 API')
      process.exit(1)  // ✅ 立即中止，不进入业务用例
    }

    console.warn(`[preflight] attempt ${attempt} failed, retrying in ${CFG.retryIntervalMs}ms`)
    await new Promise(r => setTimeout(r, CFG.retryIntervalMs))
  }
}
```

## 错误示例

```ts
// ❌ 未做 preflight，直接执行业务用例
import { test, expect } from '@playwright/test'

test('home page renders', async ({ page }) => {
  // dev server 未起时 → ERR_CONNECTION_REFUSED
  // Playwright 报"page.goto timeout"，开发者误以为是选择器失效
  await page.goto('/')
  await expect(page.locator('h1')).toHaveText('Home')
})
```

```ts
// ❌ 仅检查端口，未做健康检查
import net from 'node:net'

test.beforeAll(async () => {
  // 端口 LISTEN 但服务可能还在启动（如 Vite 优化阶段）
  // ❌ 缺失 health_endpoints 检查
  const ok = await new Promise<boolean>(resolve => {
    const s = net.connect({ port: 5173 })
    s.on('connect', () => { s.end(); resolve(true) })
    s.on('error', () => resolve(false))
  })
  if (!ok) throw new Error('frontend not started')
  // ❌ 缺失重试逻辑：偶发慢启动时直接 fail
})
```

```ts
// ❌ 把"服务未就绪"错误混入业务用例报告
test('home page renders', async ({ page }) => {
  try {
    await page.goto('/')
  } catch (err) {
    // ❌ 静默吞错 ERR_CONNECTION_REFUSED，标记用例"失败"而非"服务未就绪"
    throw new Error('test failed')
  }
})
```

## 适配新项目

- **React / Next.js**：端口改为 `3000`（Next dev）或 `4173`（Vite preview）；其余流程不变。
- **Vue 2**：dev server 端口默认 `8080`（vue-cli）或 `5173`（迁移到 Vite 后），调整 `required_ports` 即可。
- **纯 JavaScript（无框架）**：本规则仍适用，端口与端点按项目实际填写；Cypress 用 `cy.request()` 实现 health 检查。
- **Docker Compose 启动**：`required_ports` 列出容器暴露端口，`health_endpoints` 通过 `host.docker.internal` 或 service 名称访问；可借助 `docker compose up --wait` 内置健康检查。
- **CI 流水线**：建议把 preflight 与业务测试拆为独立 step（GitHub Actions / GitLab CI），preflight 失败时跳过业务测试 step 以节省运行时间。
