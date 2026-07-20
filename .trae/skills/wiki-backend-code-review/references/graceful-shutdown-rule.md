# Rule Catalog — 优雅停止

## Scope

- Covers: 后端模块涉及子进程、定时器（`setInterval`）、长连接（WebSocket / 数据库连接）时，必须注册 `SIGINT` / `SIGTERM` 清理钩子，进程退出时按序释放资源。
- 适用对象：所有创建子进程、定时器、长连接的 service / module / bootstrap 文件。
- Does NOT cover: 无状态路由 handler；Serverless 函数（生命周期由平台管理）；测试用例中的临时资源。

> 所有资源关键词、关闭信号、清理顺序均从 [config/review-config.md](../config/review-config.md) 的"优雅停止参数"节读取，本规则文件不硬编码任何具体值。

## Rules

### GS-1 创建子进程/定时器/长连接的模块必须注册 SIGINT/SIGTERM 清理钩子

- Category: reliability
- Severity: critical
- Description: 后端模块创建子进程（`spawn` / `exec`）、轮询定时器（`setInterval`）、长连接（`connect` / `listen`）后，若进程退出（Ctrl-C / kill / 容器停止）时未注册 `SIGINT` / `SIGTERM` 钩子，子进程会变成孤儿进程继续占用资源，定时器在退出前仍在触发，长连接句柄泄露。问题在开发期不易察觉，但在生产环境滚动更新或容器重启时会累积为资源泄漏与僵尸进程。必须为每个资源创建模块注册信号钩子，按 `cleanup_order` 顺序释放。
- Judgment logic:
  1. 用 `Grep` 检索文件内是否出现 `resource_keywords`（如 `spawn|setInterval|connect|listen`）——若存在，则该模块认定为"持有需清理资源"。
  2. 同模块内检索 `process.on('SIGINT'` 与 `process.on('SIGTERM'`（或封装后的 `registerShutdownHandler`），缺失即视为缺陷。
  3. 检查清理函数是否按 `cleanup_order`（默认 `['child_process', 'timer', 'connection']`）顺序释放——优先停止子进程（避免孤儿），再清定时器（避免退出前触发），最后关连接。
  4. 清理函数末尾必须调用 `process.exit(0)`（或等价显式退出），避免钩子注册后进程仍挂起等待未关闭句柄。
- Applicable scenarios: 长连接服务（WebSocket / gRPC stream）；子进程管理（tunnel / 浏览器自动化 / 外部引擎）；轮询定时器（健康检查 / 状态同步 / 缓存刷新）；容器化部署的滚动更新场景。
- Not applicable: 无状态路由 handler（请求-响应模型，无长期资源）；Serverless 函数（生命周期由平台管理，平台负责回收）；CLI 一次性脚本（执行完即退出）；测试用例的临时 mock 资源。
- Configuration parameters: 见 [config/review-config.md](../config/review-config.md) 的"优雅停止参数"节——`resource_keywords` / `shutdown_signals` / `cleanup_order`。
- Suggested fix: 提供统一的 `registerShutdownHandler()` 工具，在创建资源的模块初始化时调用；钩子内按序调用各资源的 `.kill()` / `.close()` / `.clear()`，最后 `process.exit(0)`。
- Example:
  - Bad:
    ```typescript
    class TunnelService {
      private child: ChildProcess | null = null;
      private timer: NodeJS.Timeout | null = null;

      start(): void {
        // 创建子进程与定时器，但未注册任何退出钩子
        this.child = spawn('tunnel', args);
        this.timer = setInterval(() => this.heartbeat(), 5000);
      }
      // 进程退出时 child 变孤儿、timer 继续触发，资源泄漏
    }
    ```
  - Good:
    ```typescript
    class TunnelService {
      private child: ChildProcess | null = null;
      private timer: NodeJS.Timeout | null = null;

      start(): void {
        this.child = spawn('tunnel', args);
        this.timer = setInterval(() => this.heartbeat(), 5000);
        // 创建资源后立即注册退出钩子
        registerShutdownHandler(this.cleanup.bind(this));
      }

      private async cleanup(): Promise<void> {
        // 按 cleanup_order 顺序：子进程 → 定时器 → 连接
        if (this.child) {
          this.child.kill('SIGTERM');
          this.child = null;
        }
        if (this.timer) {
          clearInterval(this.timer);
          this.timer = null;
        }
      }
    }

    // 统一的退出钩子注册器，按注册顺序逆序执行清理，最后显式退出
    const handlers: Array<() => Promise<void>> = [];
    function registerShutdownHandler(fn: () => Promise<void>): void {
      handlers.push(fn);
    }
    for (const sig of SHUTDOWN_SIGNALS) {
      process.on(sig, async () => {
        for (const fn of handlers.reverse()) {
          try { await fn(); } catch (err) { console.error('清理失败:', err); }
        }
        process.exit(0);
      });
    }
    ```
- Checklist:
  - [ ] 创建子进程 / 定时器 / 长连接的模块均注册了 `SIGINT` / `SIGTERM` 钩子（或封装的统一注册器）。
  - [ ] 清理顺序符合 `cleanup_order`，子进程优先于定时器、定时器优先于连接。
  - [ ] 清理函数末尾调用 `process.exit(0)`，避免进程因未关闭句柄挂起。
  - [ ] 清理函数本身用 try-catch 包裹，单个资源清理失败不阻塞其他资源释放。
- Related rules: 空值守卫与子进程崩溃后的字段引用见 [null-guard-rule.md](null-guard-rule.md)；外部调用错误转换见 [error-handling-rule.md](error-handling-rule.md)。
