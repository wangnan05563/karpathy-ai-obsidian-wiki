# Rule Catalog - Harness Integration

## Scope
- Covers: EngineAdapter interface implementation, AsyncIterable event streams, budget control, hook registration, state persistence, prompt storage.
- Applies to: engine/ adapter implementations, workflows/ hook registration, state/ FileStateStore, prompt loading patterns.

## Rules

### EngineAdapter 接口须完整实现
- Category: correctness | Severity: critical
- Description: EngineAdapter 是 workflow 与外部引擎之间的契约接口。若实现不完整（缺少 compile/query/healthCheckFix 等方法），workflow 调用时会运行时崩溃。TypeScript 在接口断言时可能被绕过（如 s unknown as EngineAdapter）。必须完整实现接口声明的全部方法，并保持方法签名一致。
- Suggested fix: 让类显式 implements EngineAdapter，由编译器强制完整性；禁止用 s 断言绕过接口检查。
- Example (Bad):
  `	ypescript
  const adapter = { compile: async function* () { yield { type: 'done' }; } } as unknown as EngineAdapter;
  // workflow 中调用 adapter.query() —— 运行时不存在该方法
  `
- Example (Good):
  `	ypescript
  export class LocalEngineAdapter implements EngineAdapter {
    async *compile(input: CompileInput): AsyncIterable<EngineEvent> { ... }
    async *query(input: QueryInput): AsyncIterable<EngineEvent> { ... }
    async healthCheckFix(): Promise<void> { ... }
  }
  `

### AsyncIterable 事件流须正确 yield 进度事件
- Category: correctness | Severity: critical
- Description: adapter 的 compile/query 返回 AsyncIterable<EngineEvent>，workflow 依赖 yield 的事件来驱动 SSE 推送与状态更新。若实现中忘记 yield（如直接 return 最终结果），客户端全程无进度反馈，hook（如 afterLoop）无法被触发。必须在关键步骤 yield 对应类型的事件。
- Suggested fix: 在每个显著步骤（开始、单步完成、最终完成）yield 事件；异常路径 yield error 事件。

### 预算耗尽须返回部分结果（budget_exceeded），不抛异常
- Category: reliability | Severity: critical
- Description: 引擎调用有预算限制（token/时间/步数）。预算耗尽是预期内的正常情况，不应抛异常中断流程——已产出的部分结果对用户有价值。应返回 status: budget_exceeded 与部分结果，由上层决定是否继续或停止。抛异常会导致已产出结果丢失、SSE 流被破坏。
- Suggested fix: 在循环中检查预算，超限时 yield udget_exceeded 事件并 break，不抛异常。

### Hook 须注册确定性逻辑（beforeLoop / afterLoop）
- Category: correctness | Severity: critical
- Description: workflow 通过 hook 串接确定性副作用：beforeLoop 读 SCHEMA 提供编译依据，afterLoop 更新 index/log 持久化产出。若这些逻辑散落在循环体内或被省略，会导致：编译缺依据、索引不更新、产出无法被后续检索。hook 必须在 workflow 入口注册且逻辑确定。
- Suggested fix: 在 workflow 启动时注册 beforeLoop/afterLoop，禁止在循环体内重复实现等价逻辑。

### 状态持久化须用 FileStateStore，runId 唯一
- Category: reliability | Severity: critical
- Description: 每次 run 的状态（进度、产出、错误）必须持久化，以便客户端断线重连后恢复、历史可追溯。直接用内存变量会随进程重启丢失；用裸文件写入会与并发追加冲突。必须用 FileStateStore，且 runId 全局唯一，避免状态文件互相覆盖。
- Suggested fix: 所有状态读写走 FileStateStore，runId 在创建时生成 UUID 并校验唯一性。

### prompt 须单点存储于 prompts/ 目录，禁止内联到代码
- Category: maintainability | Severity: critical
- Description: prompt 文本若内联在 .ts 代码里，会导致：修改 prompt 必须改代码并重新构建、prompt 版本无法独立管理、非开发人员无法调整。prompt 必须作为独立文件放在 prompts/ 目录，代码运行时按需加载。
- Suggested fix: prompt 存为 .md / .txt 文件，代码通过路径加载并缓存内容。
