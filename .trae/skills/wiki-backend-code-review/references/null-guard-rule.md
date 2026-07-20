# Rule Catalog — 空值守卫

## Scope

- Covers: 后端字段由外部异步赋值（子进程 spawn / exec、数据库连接、文件句柄、长连接客户端）时，使用前必须空值检查。
- 适用对象：所有持有外部资源引用的类成员字段（如 `this.provider` / `this.child` / `this.connection`），尤其是生命周期与外部进程绑定的字段。
- Does NOT cover: 构造函数中直接赋值的不可空字段；依赖注入的 singleton；纯计算函数的局部变量。

> 所有可空字段名模式、异步赋值关键词均从 [config/review-config.md](../config/review-config.md) 的"空值守卫参数"节读取，本规则文件不硬编码任何具体值。

## Rules

### NG-1 外部异步赋值字段使用前必须空值守卫

- Category: correctness
- Severity: critical
- Description: 当字段由外部异步操作赋值（如 `spawn` / `exec` 启动子进程、`connect` 建立数据库连接、`listen` 打开 socket）时，该字段在生命周期内可能因外部进程崩溃、连接断开、超时回收等原因变为 null。若使用前不守卫，TS 编译会报 TS2531（Object is possibly null），运行时则抛 `TypeError: Cannot read properties of null`，导致整个服务不可用。必须在每次使用前用 `if (!x)` 守卫，并选择"重建资源"或"抛出友好错误"两种降级路径之一。
- Judgment logic:
  1. 用 `Grep` 检索类成员字段，匹配 `nullable_field_patterns`（如 `this\.provider|this\.child|this\.connection`）。
  2. 检索同文件内是否出现 `async_assignment_keywords`（如 `spawn|exec|connect|listen`）的赋值语句——若存在，则该字段认定为"外部异步赋值"。
  3. 对该字段的每次读取（`await this.provider.start()` / `this.connection.query()` 等）检查前一行/同块内是否有 `if (!x)` 守卫，缺失即视为缺陷。
  4. 守卫分支必须包含可观察的恢复动作（重建资源 / 抛错 / 记录日志后降级），不能仅 `return` 静默吞错。
- Applicable scenarios: 子进程管理（`child_process.spawn/exec`）；数据库连接池客户端；文件句柄长期持有；WebSocket / 长连接客户端；第三方 SDK 实例（LLM provider、云服务 client）。
- Not applicable: 构造函数中直接赋值且不会被回收的字段（如 `this.config = config`）；依赖注入的 singleton（生命周期由容器管理）；纯计算函数的局部变量；只读 const 引用。
- Configuration parameters: 见 [config/review-config.md](../config/review-config.md) 的"空值守卫参数"节——`nullable_field_patterns` / `async_assignment_keywords`。
- Suggested fix: 在使用前 `if (!this.x) { 重建或抛错 }`，重建路径必须设置上限避免无限循环；抛错路径必须返回友好消息给客户端而非裸 TypeError。
- Example:
  - Bad:
    ```typescript
    class TunnelService {
      private provider: ChildProvider | null = null;

      async start(): Promise<void> {
        // spawn 后赋值，但子进程崩溃后 provider 会被置 null
        this.provider = spawn('tunnel', args);
      }

      async send(msg: string): Promise<void> {
        // TS2531: Object is possibly null. 运行时崩溃：子进程崩溃后 provider 为 null
        await this.provider.send(msg);
      }
    }
    ```
  - Good:
    ```typescript
    class TunnelService {
      private provider: ChildProvider | null = null;

      async start(): Promise<void> {
        this.provider = spawn('tunnel', args);
      }

      async send(msg: string): Promise<void> {
        // 使用前守卫，子进程崩溃后重建或抛友好错误
        if (!this.provider) {
          this.provider = spawn('tunnel', args); // 重建
          // 或：throw new Error('Tunnel 未就绪，请稍后重试');
        }
        await this.provider.send(msg);
      }
    }
    ```
- Checklist:
  - [ ] 所有匹配 `nullable_field_patterns` 的字段，使用前均有 `if (!x)` 守卫。
  - [ ] 守卫分支包含可观察的恢复动作（重建 / 抛错 / 日志降级），不静默 `return`。
  - [ ] 重建路径有上限保护（重试次数 / 退避），避免无限重建循环。
  - [ ] 字段类型显式标注为 `T | null`，让 TS 编译器协助检查。
- Related rules: 优雅停止与子进程生命周期见 [graceful-shutdown-rule.md](graceful-shutdown-rule.md)；外部调用错误转换见 [error-handling-rule.md](error-handling-rule.md) 的"外部错误须 try-catch 并转为用户友好消息"。
