# Null Guard Rule

## 触发关键词

this.provider, this.child, this.connection, spawn, exec, connect, TS2531, possibly null, undefined, 空指针, 子进程崩溃, 重连, 重建

## 规则描述

### NG-1：外部异步赋值的字段使用前必须空值守卫

**严重级别**：critical

类成员字段若由外部异步操作（`child_process.spawn` / `exec` / 数据库 `connect` / 远程 `connect` / 第三方 SDK 初始化）赋值，使用前必须 `if (!x)` 守卫，并在守卫分支内重建资源或抛出明确错误。禁止直接 `await this.x.method()`。

**为什么**：异步赋值的字段存在"尚未赋值"与"已被置空"两种 null 状态。子进程崩溃后引用被置为 `null`、数据库连接断开后被显式释放、SDK 重连过程中临时为 null，都是常见场景。直接调用方法会触发 TS2531 编译错误；运行期则抛 `Cannot read properties of null`，导致服务不可用且难以定位。

## 判断逻辑

```
1. Grep '<nullable_field_patterns>' 找出所有可空字段引用（默认匹配 this.provider / this.child / this.connection）
2. 对每个引用检查前序代码是否包含 if (!x) 守卫
3. 若字段由 spawn/exec/connect 等异步操作赋值 → 标记为"可空字段"，使用必须守卫
4. 守卫分支必须有以下之一：
   - 重建资源（重新 spawn / connect / init）
   - 抛出明确错误（throw new Error('xxx not initialized')）
   - 返回降级值（return null / 默认值）
5. 禁止守卫后留空（吞错）或仅 console.warn 后继续访问
```

## 适用场景

- 子进程管理（`child_process.spawn` / `exec` / `fork`）
- 数据库连接（mongoose / pg / mysql2 的 `connect` / `pool`）
- 长连接客户端（WebSocket / MQTT / Redis client）
- 第三方 SDK 客户端（云服务 SDK、AI Provider 等）
- 文件句柄、网络套接字等需要显式打开/关闭的资源

## 不适用场景

- 构造函数中直接赋值的不可空字段（`this.x = createX()`）
- 通过依赖注入在类初始化时确保非 null 的字段（DI 容器保证）
- TypeScript `definite assignment assertion`（`!:`）且能静态证明赋值的字段
- 纯函数库中由参数传入的值（参数校验属于 input-validation-rule 范畴）

## 配置参数

> 所有参数从 `config/coding-standards-config.md` 的 `null_guard` 段读取。

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `nullable_field_patterns` | `this.provider, this.child, this.connection` | 可空字段名模式（逗号分隔，支持正则） |
| `async_assignment_keywords` | `spawn, exec, fork, connect, createClient, init` | 触发"可空字段"标记的异步赋值关键字 |
| `guard_required_severity` | `error` | 缺失守卫的严重级别 |
| `rebuild_required` | `true` | 守卫分支是否必须包含重建逻辑（true）或允许抛错（false） |

## 示例

### 错误示例

```typescript
class ProviderClient {
  private provider: ProviderHandle | null = null;

  async start() {
    this.provider = spawn('binary', ['--port', '7000']);
    this.provider.on('exit', () => { this.provider = null; });  // 崩溃后置空
  }

  async call() {
    // ❌ TS2531: Object is possibly 'null'
    // ❌ 运行期：子进程崩溃后调用直接抛错
    await this.provider.send({ cmd: 'ping' });
  }
}
```

### 正确示例

```typescript
class ProviderClient {
  private provider: ProviderHandle | null = null;

  async start() {
    this.provider = spawn('binary', ['--port', '7000']);
    this.provider.on('exit', () => { this.provider = null; });
  }

  async call() {
    // ✅ 守卫 + 重建
    if (!this.provider) {
      await this.start();  // 重建资源
      if (!this.provider) {
        throw new Error('Provider 重建失败，请检查二进制路径与端口');
      }
    }
    await this.provider.send({ cmd: 'ping' });
  }
}
```

### 数据库连接场景

```typescript
class UserRepository {
  private connection: DbConnection | null = null;

  async connect() {
    this.connection = await createConnection(config);
  }

  async findUser(id: string) {
    // ✅ 守卫 + 抛出明确错误（数据库不可重建时由调用方降级）
    if (!this.connection) {
      throw new Error('Database not connected. Call connect() first.');
    }
    return this.connection.query('SELECT * FROM users WHERE id = ?', [id]);
  }
}
```

## 检查清单

- [ ] 异步赋值的字段是否声明为 `T | null`
- [ ] 使用前是否有 `if (!x)` 守卫
- [ ] 守卫分支是否包含重建 / 抛错 / 降级返回（非空分支）
- [ ] 子进程崩溃 / 连接断开回调中是否将字段置 null（保持状态一致）
- [ ] 是否避免在守卫分支仅 `console.warn` 后继续访问字段
