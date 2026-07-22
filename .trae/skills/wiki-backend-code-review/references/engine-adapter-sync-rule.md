# EngineAdapter 接口变更实现同步（BR-029）

> 复盘来源：`EngineAdapter` 接口新增/修改方法（如 `beforeLoop` / `afterLoop` / `healthCheckFix`）后，部分实现类未同步更新，导致运行时 workflow 调用未实现的方法抛 `TypeError: xxx is not a function`，或被 `as unknown as EngineAdapter` 断言绕过编译期检查后在运行时崩溃。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"engine_adapter_sync"章节读取，禁止在本规则文件硬编码具体接口路径或方法名。

## Trigger Keywords
EngineAdapter, interface, implements, beforeLoop, afterLoop, yield, compile, query, healthCheckFix, AsyncIterable, EngineEvent, adapter, as unknown as

## Rules

### BR-029-1: EngineAdapter 接口新增/修改方法时所有实现类必须同步更新

- **Severity**: critical
- **Description**: `EngineAdapter` 接口（路径见 `engine_adapter_sync.engine_adapter_interface_path`）新增或修改方法签名时，所有 `implements EngineAdapter` 的实现类必须同步新增/修改对应方法，签名（参数名、参数类型、返回类型）与接口完全一致。TypeScript 的 `implements` 子句会在编译期强制完整性检查，但若实现类用 `as unknown as EngineAdapter` 断言绕过 implements，编译期不报错，运行时调用未实现方法会抛 `TypeError`。评审时必须对比接口方法列表与每个实现类的方法列表，差异即视为不通过。
- **Suggested fix**:
```typescript
// api/src/engine/adapter.ts —— 接口定义
export interface EngineAdapter {
  compile(input: CompileInput): AsyncIterable<EngineEvent>;
  query(input: QueryInput): AsyncIterable<EngineEvent>;
  healthCheckFix(): Promise<void>;
  beforeLoop(ctx: LoopContext): Promise<void>;   // 新增方法
  afterLoop(ctx: LoopContext, result: LoopResult): Promise<void>; // 新增方法
}

// api/src/engine/local-adapter.ts —— 实现类同步更新
export class LocalEngineAdapter implements EngineAdapter {
  async *compile(input: CompileInput): AsyncIterable<EngineEvent> { /* ... */ }
  async *query(input: QueryInput): AsyncIterable<EngineEvent> { /* ... */ }
  async healthCheckFix(): Promise<void> { /* ... */ }

  // 新增方法同步实现（签名与接口一致）
  async beforeLoop(ctx: LoopContext): Promise<void> {
    await this.loadSchema(ctx);
  }
  async afterLoop(ctx: LoopContext, result: LoopResult): Promise<void> {
    await this.updateIndex(ctx, result);
  }
}
```

### BR-029-2: 新增抽象方法必须在所有新实现中提供

- **Severity**: critical
- **Description**: `EngineAdapter` 接口新增的抽象方法必须在所有现有实现类和未来新增实现类中提供具体实现。禁止用 `as unknown as EngineAdapter` 断言绕过 implements 检查；禁止用 `// @ts-ignore` 抑制方法缺失错误；禁止在实现类中抛 `not implemented` 错误作为占位——若方法对当前实现确实无意义，应在接口中将其声明为可选方法（`beforeLoop?: (...) => ...`），由调用方做存在性检查，而非强制实现类提供空实现。
- **Suggested fix**:
```typescript
// 错误：用 as unknown as 断言绕过 implements 检查
const adapter = {
  compile: async function* () { yield { type: 'done' }; },
  // ❌ 缺 query / healthCheckFix / beforeLoop / afterLoop
} as unknown as EngineAdapter;

// 正确：显式 implements，由编译器强制完整性
export class RemoteEngineAdapter implements EngineAdapter {
  async *compile(input: CompileInput): AsyncIterable<EngineEvent> { /* ... */ }
  async *query(input: QueryInput): AsyncIterable<EngineEvent> { /* ... */ }
  async healthCheckFix(): Promise<void> { /* ... */ }
  async beforeLoop(ctx: LoopContext): Promise<void> { /* ... */ }
  async afterLoop(ctx: LoopContext, result: LoopResult): Promise<void> { /* ... */ }
}

// 可选方案：方法对某些实现无意义时，接口声明为可选
export interface EngineAdapter {
  compile(input: CompileInput): AsyncIterable<EngineEvent>;
  query(input: QueryInput): AsyncIterable<EngineEvent>;
  healthCheckFix(): Promise<void>;
  // 可选 hook：调用方做存在性检查
  beforeLoop?(ctx: LoopContext): Promise<void>;
  afterLoop?(ctx: LoopContext, result: LoopResult): Promise<void>;
}

// workflow 调用方做存在性检查
if (adapter.beforeLoop) {
  await adapter.beforeLoop(ctx);
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `engine_adapter_sync.enabled` | `true` | 是否启用本规则 |
| `engine_adapter_sync.severity` | `critical` | 违规严重级别 |
| `engine_adapter_sync.engine_adapter_interface_path` | `api/src/engine/adapter.ts` | EngineAdapter 接口定义文件路径（相对项目根） |
| `engine_adapter_sync.adapter_implementations_directory` | `api/src/engine/` | 适配器实现类所在目录（相对项目根） |
| `engine_adapter_sync.forbidden_assertion_patterns` | `as unknown as,@ts-ignore,@ts-expect-error` | 禁用的绕过检查模式（逗号分隔） |
| `engine_adapter_sync.required_methods` | `` | 必备方法名列表（留空则校验接口声明的全部方法） |
| `engine_adapter_sync.optional_methods` | `beforeLoop,afterLoop` | 可选方法名列表（接口中声明为可选，调用方做存在性检查） |
| `engine_adapter_sync.allow_not_implemented_placeholder` | `false` | 是否允许 `throw new Error('not implemented')` 占位实现 |

## 检查方式

1. 用 Read 读取 `engine_adapter_sync.engine_adapter_interface_path`，提取 `interface EngineAdapter { ... }` 中声明的全部方法签名（方法名 + 参数 + 返回类型）。
2. 用 Grep 检索 `engine_adapter_sync.adapter_implementations_directory` 下所有 `.ts` 文件，匹配 `implements EngineAdapter` 的类定义。
3. 对每个实现类，用 Read 提取其方法列表，与接口方法列表对比：
   - 接口必备方法（非 `optional_methods`）在实现类中缺失 → BR-029-1 违规
   - 实现类方法签名与接口不一致（参数数量、类型、返回类型）→ BR-029-1 违规
4. 用 Grep 检索 `engine_adapter_sync.forbidden_assertion_patterns` 中的模式：
   - `as unknown as EngineAdapter` → BR-029-2 违规（绕过 implements 检查）
   - `@ts-ignore` / `@ts-expect-error` 紧邻 `implements EngineAdapter` 或方法签名 → BR-029-2 违规
5. 用 Grep 检索 `throw new Error\(['"]not implemented['"]\)` 或 `throw new Error\(['"]未实现['"]\)`：
   - 若 `allow_not_implemented_placeholder` 为 `false` 且该方法在 `required_methods` 列表中 → BR-029-2 违规
   - 若方法在 `optional_methods` 列表中，应改为接口声明可选，调用方做存在性检查
6. 若 `engine_adapter_sync.required_methods` 非空，仅校验该列表中的方法；否则校验接口声明的全部方法。

## 正确示例

```typescript
// 1. api/src/engine/adapter.ts —— 接口定义
export interface EngineAdapter {
  compile(input: CompileInput): AsyncIterable<EngineEvent>;
  query(input: QueryInput): AsyncIterable<EngineEvent>;
  healthCheckFix(): Promise<void>;
  // 可选 hook：调用方做存在性检查
  beforeLoop?(ctx: LoopContext): Promise<void>;
  afterLoop?(ctx: LoopContext, result: LoopResult): Promise<void>;
}

// 2. api/src/engine/local-adapter.ts —— 完整实现
export class LocalEngineAdapter implements EngineAdapter {
  async *compile(input: CompileInput): AsyncIterable<EngineEvent> {
    yield { type: 'progress', data: { percent: 0 } };
    // ... 编译逻辑
    yield { type: 'done', data: { result: '...' } };
  }
  async *query(input: QueryInput): AsyncIterable<EngineEvent> { /* ... */ }
  async healthCheckFix(): Promise<void> {
    await this.fixPermissions();
  }
  async beforeLoop(ctx: LoopContext): Promise<void> {
    await this.loadSchema(ctx);
  }
  async afterLoop(ctx: LoopContext, result: LoopResult): Promise<void> {
    await this.updateIndex(ctx, result);
  }
}

// 3. api/src/engine/remote-adapter.ts —— 可选 hook 省略实现
export class RemoteEngineAdapter implements EngineAdapter {
  async *compile(input: CompileInput): AsyncIterable<EngineEvent> { /* ... */ }
  async *query(input: QueryInput): AsyncIterable<EngineEvent> { /* ... */ }
  async healthCheckFix(): Promise<void> { /* ... */ }
  // beforeLoop / afterLoop 为可选方法，RemoteEngineAdapter 不需要时省略
}

// 4. workflow 调用方做存在性检查
async function runWorkflow(adapter: EngineAdapter, ctx: LoopContext) {
  if (adapter.beforeLoop) {
    await adapter.beforeLoop(ctx);
  }
  // ... 主循环
  if (adapter.afterLoop) {
    await adapter.afterLoop(ctx, result);
  }
}
```

## 错误示例

```typescript
// 错误 1：用 as unknown as 断言绕过 implements 检查
const adapter = {
  compile: async function* () { yield { type: 'done' }; },
  query: async function* () { yield { type: 'done' }; },
  // ❌ 缺 healthCheckFix / beforeLoop / afterLoop
} as unknown as EngineAdapter;
// workflow 中调用 adapter.healthCheckFix() → TypeError: not a function

// 错误 2：用 @ts-ignore 抑制方法缺失错误
// @ts-ignore  // ❌ 抑制错误，运行时仍会崩
export class BrokenAdapter implements EngineAdapter {
  async *compile(input: CompileInput): AsyncIterable<EngineEvent> { /* ... */ }
  async *query(input: QueryInput): AsyncIterable<EngineEvent> { /* ... */ }
  // 缺 healthCheckFix
}

// 错误 3：throw 'not implemented' 占位（required 方法不允许）
export class StubAdapter implements EngineAdapter {
  async *compile(input: CompileInput): AsyncIterable<EngineEvent> { /* ... */ }
  async *query(input: QueryInput): AsyncIterable<EngineEvent> { /* ... */ }
  // ❌ required 方法用 throw 占位，调用时崩溃
  healthCheckFix(): Promise<void> {
    throw new Error('not implemented');
  }
}

// 错误 4：方法签名与接口不一致
export class MismatchedAdapter implements EngineAdapter {
  // ❌ 接口声明返回 AsyncIterable<EngineEvent>，实现返回 Promise<void>
  async compile(input: CompileInput): Promise<void> { /* ... */ }
  async *query(input: QueryInput): AsyncIterable<EngineEvent> { /* ... */ }
  async healthCheckFix(): Promise<void> { /* ... */ }
}
```

## 适配新项目

- **Express 项目**：EngineAdapter 模式不变，`engine_adapter_interface_path` 调整为项目实际路径（如 `src/engine/adapter.ts`），其余规则不变。
- **NestJS 项目**：适配器用 `@Injectable()` 装饰器声明，通过 DI 注入——`adapter_implementations_directory` 改为 `src/engine/adapters/`，Grep 模式 `implements EngineAdapter` 不变；NestJS 的 provider token 可作为接口实现的发现机制，但本规则仍以 `implements` 子句为准。
- **Koa 项目**：与 Express 相同，调整路径配置即可。
- **Strategy / Plugin 模式项目**：若项目用 Strategy 模式而非 EngineAdapter 命名（如 `interface CompilerStrategy`），将 `engine_adapter_interface_path` 指向实际接口文件，Grep 模式调整为 `implements CompilerStrategy`，其余规则不变。
- **多接口项目**：若引擎适配器有多个接口分层（如 `EngineAdapter` + `HealthCheckable` + `Hookable`），将多个接口路径列入 `engine_adapter_interface_path`（逗号分隔），逐个接口校验实现完整性。
- **动态加载项目**：若适配器通过动态 `import()` 加载，仍要求实现类显式 `implements EngineAdapter`——动态加载不影响编译期类型检查，仅运行时实例化时机不同。
