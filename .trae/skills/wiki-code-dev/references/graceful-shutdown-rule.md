# Graceful Shutdown Rule

## 触发关键词

SIGINT, SIGTERM, process.on, spawn, setInterval, setTimeout, child_process, close, kill, 退出, 资源泄漏, 僵尸进程, 优雅停止, graceful shutdown

## 规则描述

### GS-1：子进程与定时器必须注册信号清理钩子

**严重级别**：critical

任何创建子进程（`spawn` / `exec` / `fork`）、长轮询定时器（`setInterval`）、长连接（WebSocket / TCP / 数据库）的模块，必须注册 `process.on('SIGINT')` 与 `process.on('SIGTERM')` 钩子，钩子内按"子进程 → 定时器 → 连接"的顺序释放资源，最后 `process.exit(0)`。

**为什么**：Ctrl+C / docker stop / pm2 reload 都会发送 SIGINT/SIGTERM。未注册钩子时，Node.js 主进程直接退出，子进程变孤儿（被 init 收养但无人管理），定时器继续持有引用导致 GC 无法回收，端口仍被占用，下次启动失败。僵尸进程在容器环境会触发 OOM，在本地开发环境会累积耗尽端口。

## 判断逻辑

```
1. Grep '<resource_keywords>' 找出模块中创建资源的代码（默认 spawn / setInterval / connect）
2. 检查同模块或入口文件是否包含 process.on('SIGINT'/'SIGTERM') 注册
3. 钩子内是否按"子进程优先"顺序清理：
   - 子进程：child.kill('SIGTERM') → 超时后 child.kill('SIGKILL')
   - 定时器：clearInterval / clearTimeout
   - 连接：await client.close() / await db.end()
4. 钩子末尾是否调用 process.exit(0)（避免长连接延迟阻塞退出）
5. 多模块场景：建议统一在入口文件聚合所有清理函数，避免信号钩子散落各处
```

## 适用场景

- 启动子进程的 CLI 工具或服务（如本地 tunnel / 内嵌 LSP server）
- 后台轮询服务（`setInterval` 定时同步 / 心跳 / 清理）
- 长连接客户端（WebSocket / MQTT / TCP / 数据库连接池）
- 容器化部署的 Node.js 服务（K8s pod 终止发送 SIGTERM）
- 本地开发服务（Ctrl+C 触发 SIGINT）

## 不适用场景

- 无状态路由处理函数（请求结束自动释放，无需信号钩子）
- Serverless 函数（FaaS 平台管理生命周期，进程不可拦截信号）
- 一次性 CLI 脚本（无长期资源，进程结束即释放）
- 纯前端浏览器代码（用 `beforeunload` 而非 POSIX 信号）

## 配置参数

> 所有参数从 `config/coding-standards-config.md` 的 `graceful_shutdown` 段读取。

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `resource_keywords` | `spawn, setInterval, connect, createClient` | 触发"需要清理钩子"检查的资源创建关键字 |
| `shutdown_signals` | `SIGINT, SIGTERM` | 必须注册的信号列表 |
| `child_terminate_signal` | `SIGTERM` | 通知子进程停止的信号 |
| `child_force_kill_timeout_ms` | `5000` | SIGTERM 后等待子进程退出的超时，超时改用 SIGKILL |
| `exit_code_on_clean` | `0` | 清理完成后的退出码 |
| `aggregate_in_entry` | `true` | 是否在入口文件聚合所有清理函数（推荐，避免散落） |

## 示例

### 错误示例

```typescript
class TunnelService {
  private child: ChildProcess | null = null;
  private timer: NodeJS.Timeout | null = null;

  start() {
    this.child = spawn('tunnel', ['--config', 'config.yaml']);
    this.timer = setInterval(() => this.heartbeat(), 5000);
    // ❌ 未注册 SIGINT/SIGTERM 钩子
    // Ctrl+C 后主进程退出，tunnel 子进程变孤儿，端口仍被占用
  }
}
```

### 正确示例

```typescript
class TunnelService {
  private child: ChildProcess | null = null;
  private timer: NodeJS.Timeout | null = null;

  start() {
    this.child = spawn('tunnel', ['--config', 'config.yaml']);
    this.timer = setInterval(() => this.heartbeat(), 5000);
    this.registerShutdownHooks();  // ✅ 注册清理钩子
  }

  private registerShutdownHooks() {
    const cleanup = async () => {
      // 1. 停止定时器（避免新一轮心跳触发已关闭的子进程）
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
      // 2. 停止子进程（SIGTERM 优先，超时 SIGKILL）
      if (this.child) {
        this.child.kill('SIGTERM');
        await new Promise(resolve => {
          const forceKill = setTimeout(() => {
            this.child?.kill('SIGKILL');
            resolve(undefined);
          }, 5000);  // force_kill_timeout_ms 来自 config
          this.child.once('exit', () => {
            clearTimeout(forceKill);
            resolve(undefined);
          });
        });
        this.child = null;
      }
      process.exit(0);  // exit_code_on_clean 来自 config
    };
    // shutdown_signals 来自 config
    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);
  }

  private heartbeat() { /* ... */ }
}
```

### 入口聚合模式（多模块推荐）

```typescript
// src/index.ts
import { tunnelService } from './services/tunnel.js';
import { pollService } from './services/poll.js';
import { dbService } from './services/db.js';

async function shutdown() {
  // 按依赖顺序：子进程 → 定时器 → 连接
  await tunnelService.stop();
  await pollService.stop();
  await dbService.close();
  process.exit(0);
}

// shutdown_signals 来自 config
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
```

## 检查清单

- [ ] 创建子进程的模块是否注册 SIGINT / SIGTERM 钩子
- [ ] 创建 setInterval 的模块是否注册信号钩子并在钩子内 clearInterval
- [ ] 长连接客户端是否在钩子内调用 close / end
- [ ] 钩子内是否按"子进程 → 定时器 → 连接"顺序清理
- [ ] 子进程停止是否优先 SIGTERM，超时后 SIGKILL 兜底
- [ ] 钩子末尾是否调用 process.exit(0)（避免长连接阻塞退出）
- [ ] 多模块场景是否在入口文件聚合清理函数（避免散落）
