# Rule Catalog — 持久化与缓存刷新

## Scope

- Covers: 配置文件路径解析锚点、写盘后缓存刷新、HTTP 参数防路径穿越、跨 origin 持久化边界、降级策略日志、落盘目录与 `.gitignore` 同步。
- 适用对象：所有 `services/api/` 下涉及配置持久化、文件落盘、内存缓存、HTTP 路由参数到文件系统映射的代码。
- Does NOT cover: 通用路径遍历防护（见 [security-rule.md](security-rule.md)）、配置类路由生命周期（见 [config-management-rule.md](config-management-rule.md)）、会话状态缓存失效（见 [session-state-rule.md](session-state-rule.md)）。

> 所有具体路径、正则、函数名、目录约定均从 [config/review-config.md](../config/review-config.md) 的"持久化与缓存刷新审查参数"节读取，本规则文件只描述通用模式，不硬编码任何具体值。

## Rules

### PC-1 配置文件路径解析禁止以 CWD 为唯一锚点

- Category: persistence-cache
- Severity: critical
- Description: `process.cwd()` 受启动方式影响（开发模式、打包模式、工具链切换、IDE 集成），作为唯一路径锚点会导致配置文件找不到或写到错误位置，表现为"配置丢失"或"写了但下次启动读不到"。ESM 环境下必须以 `import.meta.url` 为主锚点（与当前源文件位置绑定），打包模式退回 CWD，并辅以 `fsSync.accessSync` 探测兜底。
- Suggested fix: 实现 `getConfigPath()` 三级策略：开发模式用 `path.dirname(fileURLToPath(import.meta.url))` 推导；打包模式（`process.pkg` 存在）用 `path.resolve(process.cwd(), CONFIG_FILENAME)`；最后用候选路径数组 + `accessSync` 探测返回首个存在路径。
- Example:
  - Bad:
    ```typescript
    // CWD 漂移：从 IDE 根目录启动时读到错误位置的 config.json
    import fs from 'node:fs';
    const configPath = path.resolve(process.cwd(), 'config.json');
    const data = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    ```
  - Good:
    ```typescript
    import { fileURLToPath } from 'node:url';
    import fsSync from 'node:fs';

    // 与当前源文件位置绑定，不受启动 CWD 影响
    const API_SRC_DIR = path.dirname(fileURLToPath(import.meta.url));
    const API_CONFIG_PATH = path.resolve(API_SRC_DIR, '..', CONFIG_FILENAME);

    function getConfigPath(): string {
      const candidates: string[] = [];
      const isPackaged = !!(process as NodeJS.Process & { pkg?: unknown }).pkg;
      // 打包模式无源文件路径，退回 CWD
      if (isPackaged) candidates.push(path.resolve(process.cwd(), CONFIG_FILENAME));
      // 开发模式主锚点
      candidates.push(API_CONFIG_PATH);
      for (const p of candidates) {
        try { fsSync.accessSync(p); return p; } catch {}
      }
      return API_CONFIG_PATH;
    }
    ```

### PC-2 写盘函数必须立即刷新内存缓存（写后即刷）

- Category: persistence-cache
- Severity: critical
- Description: 配置类写盘函数（如 `saveAiConfig` / `resetAiConfig`）若只写文件不同步刷新内存缓存，下一次 `GET /config` 在缓存 TTL 窗口期内会返回旧值，表现为"保存了但页面刷新后还是旧配置"。TTL 不替代显式刷新——TTL 是兜底机制，写盘后必须立即同步缓存。
- Suggested fix: 提供统一的 `refreshConfigCache(data)` 函数，同步更新 `configCache.data` / `.path` / `.loadedAt`。所有写盘函数在 `await fs.writeFile(...)` 成功后、`return reply` 之前调用它。`writeFile` 抛错时不得刷新缓存（保持旧值供降级读取）。
- Example:
  - Bad:
    ```typescript
    async function saveAiConfig(patch: Partial<AIConfig>): Promise<void> {
      const data = { ...configCache.data, ai: { ...configCache.data.ai, ...patch } };
      await fs.writeFile(getConfigPath(), JSON.stringify(data, null, 2));
      // 缺失：未刷新 configCache，30s TTL 窗口期内 GET 返回旧值
    }
    ```
  - Good:
    ```typescript
    function refreshConfigCache(data: AppConfig): void {
      configCache.data = data;
      configCache.path = getConfigPath();
      configCache.loadedAt = Date.now();
    }

    async function saveAiConfig(patch: Partial<AIConfig>): Promise<void> {
      const data = { ...configCache.data, ai: { ...configCache.data.ai, ...patch } };
      await fs.writeFile(getConfigPath(), JSON.stringify(data, null, 2));
      // 写盘成功后立即刷新缓存，关闭 TTL 窗口期
      refreshConfigCache(data);
    }
    ```

### PC-3 HTTP 请求参数作文件名/路径段必须正则白名单校验

- Category: persistence-cache
- Severity: critical
- Description: 来自 `request.params.id` / `request.body.filename` 的值直接拼接到文件系统路径会形成路径穿越漏洞（`../` 跳出根目录）或文件名注入（null byte、换行符）。资源 ID 必须用 UUID 正则校验，通用文件名段必须用文件名白名单正则校验。正则本身视为配置项，禁止在代码内联硬编码字面量。
- Suggested fix: 从 config 读取 UUID 正则与文件名正则，提供 `assertSafeId(id)` / `assertSafeFilename(name)` 校验函数。所有路由参数用作文件名前必须先过校验，校验失败返回 400。
- Example:
  - Bad:
    ```typescript
    app.get('/api/conversations/:id', async (request, reply) => {
      // 直接拼路径，../../../etc/passwd 可穿越
      const file = path.join(dataDir, `${request.params.id}.json`);
      const content = await fs.readFile(file, 'utf-8');
      return reply.send(JSON.parse(content));
    });
    ```
  - Good:
    ```typescript
    import { UUID_RE, FILENAME_RE } from '../config/regex.js';

    function assertSafeId(id: string): void {
      if (!UUID_RE.test(id)) {
        throw new Error(`非法资源 ID: ${id}`);
      }
    }

    app.get('/api/conversations/:id', async (request, reply) => {
      const id = (request.params as { id: string }).id;
      assertSafeId(id);
      const file = path.join(dataDir, `${id}.json`);
      const content = await fs.readFile(file, 'utf-8');
      return reply.send(JSON.parse(content));
    });
    ```

### PC-4 跨 origin 共享数据必须以后端为权威源

- Category: persistence-cache
- Severity: critical
- Description: 浏览器存储（IndexedDB / localStorage）按 origin（协议+域名+端口）隔离，开发模式（5173）与生产模式（3000）会形成两份独立数据，表现为"开发环境有的会话在生产环境看不到"。跨 origin 共享的数据必须以后端文件系统为权威源，浏览器存储仅作降级缓存。敏感数据（apiKey、authtoken）禁止 localStorage 明文存储。
- Suggested fix: 按 config 的"跨 origin 持久化边界"表识别权威源。后端提供完整 CRUD 路由，前端 store 优先调用后端 API，失败时降级到本地缓存。提供一次性幂等迁移函数，在应用启动时检测本地缓存有数据但后端为空，自动迁移到后端。
- Example:
  - Bad:
    ```typescript
    // 仅存 IndexedDB，开发/生产两份数据，且 apiKey 明文存 localStorage
    async function saveConversation(conv: Conversation): Promise<void> {
      await indexedDb.put('conversations', conv);
      localStorage.setItem('apiKey', conv.apiKey); // 敏感数据明文
    }
    ```
  - Good:
    ```typescript
    // 后端为权威源，IndexedDB 仅作降级缓存
    async function saveConversation(conv: Conversation): Promise<void> {
      try {
        await fetch('/api/conversations/' + conv.id, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(conv),
        });
      } catch (err) {
        // 后端不可用降级到本地缓存，但须记录降级事件
        console.warn('后端不可用，降级到 IndexedDB 缓存', err);
        await indexedDb.put('conversations', conv);
      }
    }

    // 一次性幂等迁移：启动时检测本地有数据但后端为空
    async function migrateIndexedDbToBackend(): Promise<void> {
      const local = await indexedDb.getAll('conversations');
      if (local.length === 0) return;
      for (const conv of local) {
        await fetch('/api/conversations/' + conv.id, { method: 'PUT', /* ... */ });
      }
    }
    ```

### PC-5 降级到本地缓存必须记录 warn 日志，禁止静默失败

- Category: persistence-cache
- Severity: suggestion
- Description: 后端不可用时前端降级到本地缓存是合理容错，但若静默降级（无日志），用户会误以为数据已持久化到后端，实际只在本地，下次换设备/浏览器即丢失。降级必须 `console.warn` 记录事件类型、错误摘要、降级目标，便于排查。
- Suggested fix: 所有降级分支统一 `console.warn('[降级] <操作> 失败，降级到 <缓存层>:', err)`。降级日志级别由 config 的"降级策略参数"表管理（默认 `warn`）。
- Example:
  - Bad:
    ```typescript
    try {
      await fetch('/api/conversations').then(r => r.json());
    } catch {
      // 静默降级，用户无感知
      return await indexedDb.getAll('conversations');
    }
    ```
  - Good:
    ```typescript
    try {
      return await fetch('/api/conversations').then(r => r.json());
    } catch (err) {
      console.warn('[降级] 加载历史会话失败，降级到 IndexedDB 缓存:', err);
      return await indexedDb.getAll('conversations');
    }
    ```

### PC-6 新建落盘目录须同步登记 .gitignore 排除规则

- Category: persistence-cache
- Severity: suggestion
- Description: 后端新建落盘目录（如 `data/conversations/`、`test_screenshots/`）若未在 `.gitignore` 登记排除规则，运行期写入的会话数据、截图、凭证文件会误提交到 git 仓库，泄露敏感信息。落盘目录约定与 `.gitignore` 必须双向同步。
- Suggested fix: 按 config 的"落盘目录约定"表新增目录时，同步在 `.gitignore` 添加排除规则（目录名 + 末尾 `/`）。评审时确认目录约定表与 `.gitignore` 内容一致。
- Example:
  - Bad:
    ```typescript
    // 新增 data/conversations/ 落盘目录，但 .gitignore 未更新
    const dir = path.resolve(dataDir, 'conversations');
    await fs.mkdir(dir, { recursive: true });
    ```
  - Good:
    ```text
    # .gitignore 同步登记
    data/conversations/
    test_screenshots/
    ```
    ```typescript
    // 代码与 .gitignore 双向同步
    const dir = path.resolve(dataDir, 'conversations'); // 已在 config 落盘目录约定表登记
    await fs.mkdir(dir, { recursive: true });
    ```
