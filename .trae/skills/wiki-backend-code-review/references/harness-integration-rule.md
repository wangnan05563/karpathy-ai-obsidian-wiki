# Rule Catalog — Harness 集成

## Scope
- Covers: `EngineAdapter` 接口实现、AsyncIterable 事件流产出、预算控制、Hook 注册、状态持久化、prompt 存储。
- 适用对象：`engine/` 目录下的 adapter 实现、`workflows/` 中的 hook 注册逻辑、`state/` 下的 `FileStateStore`、prompt 引用方式。

## Rules

### EngineAdapter 接口须完整实现
- Category: correctness
- Severity: critical
- Description: `EngineAdapter` 是 workflow 与外部引擎之间的契约接口。若实现不完整（缺少 `compile` / `query` / `healthCheckFix` 等方法），workflow 调用时会运行时崩溃，且 TypeScript 在接口断言时可能被绕过（如用 `as unknown as EngineAdapter`）。必须完整实现接口声明的全部方法，并保持方法签名一致。
- Suggested fix: 让类显式 `implements EngineAdapter`，由编译器强制完整性；禁止用 `as` 断言绕过接口检查。
- Example:
  - Bad:
    ```typescript
    // 用 as 断言绕过接口检查，运行时调用 query 会崩溃
    const adapter = {
      compile: async function* () { yield { type: 'done' }; },
    } as unknown as EngineAdapter;

    // workflow 中调用 adapter.query() —— 运行时不存在该方法
    const result = await adapter.query(input);
    ```
  - Good:
    ```typescript
    // 显式 implements，编译器强制实现全部方法
    export class LocalEngineAdapter implements EngineAdapter {
      async *compile(input: CompileInput): AsyncIterable<EngineEvent> { ... }
      async *query(input: QueryInput): AsyncIterable<EngineEvent> { ... }
      async healthCheckFix(): Promise<void> { ... }
    }
    ```

### AsyncIterable 事件流须正确 yield 进度事件
- Category: correctness
- Severity: critical
- Description: adapter 的 `compile` / `query` 返回 `AsyncIterable<EngineEvent>`，workflow 依赖 yield 的事件来驱动 SSE 推送与状态更新。若实现中忘记 yield（如直接 return 最终结果），客户端全程无进度反馈，且 hook（如 afterLoop）无法被触发。必须在关键步骤 yield 对应类型的事件。
- Suggested fix: 在每个显著步骤（开始、单步完成、最终完成）yield 事件；异常路径 yield error 事件。
- Example:
  - Bad:
    ```typescript
    async *compile(input: CompileInput): AsyncIterable<EngineEvent> {
      const result = await this.runLongTask(input);
      // 只 return 最终结果，中间无任何 yield，客户端全程无反馈
      return result;
    }
    ```
  - Good:
    ```typescript
    async *compile(input: CompileInput): AsyncIterable<EngineEvent> {
      yield { type: 'progress', data: { stage: 'started' } };
      for (const step of input.steps) {
        const part = await this.runStep(step);
        // 每步产出都 yield，驱动 SSE 推送与 hook
        yield { type: 'result', data: part };
      }
      yield { type: 'done', data: { stage: 'finished' } };
    }
    ```

### 预算耗尽须返回部分结果（budget_exceeded），不抛异常
- Category: reliability
- Severity: critical
- Description: 引擎调用有预算限制（token/时间/步数）。预算耗尽是预期内的正常情况，不应抛异常中断流程——已产出的部分结果对用户有价值。应返回 `status: budget_exceeded` 与部分结果，由上层决定是否继续或停止。抛异常会导致已产出结果丢失、SSE 流被破坏。
- Suggested fix: 在循环中检查预算，超限时 yield `budget_exceeded` 事件并 break，不抛异常。
- Example:
  - Bad:
    ```typescript
    async *compile(input: CompileInput): AsyncIterable<EngineEvent> {
      let used = 0;
      for (const step of input.steps) {
        if (used >= input.budget) {
          // 抛异常会丢失已产出结果，且破坏 SSE 流
          throw new Error('预算耗尽');
        }
        used += step.cost;
        yield { type: 'result', data: await this.runStep(step) };
      }
    }
    ```
  - Good:
    ```typescript
    async *compile(input: CompileInput): AsyncIterable<EngineEvent> {
      let used = 0;
      const partial: unknown[] = [];
      for (const step of input.steps) {
        if (used + step.cost > input.budget) {
          // 预算耗尽是预期情况，返回部分结果而非抛异常
          yield { type: 'result', data: { status: 'budget_exceeded', partial } };
          return;
        }
        used += step.cost;
        const r = await this.runStep(step);
        partial.push(r);
        yield { type: 'result', data: r };
      }
      yield { type: 'done', data: { status: 'ok' } };
    }
    ```

### Hook 须注册确定性逻辑（beforeLoop / afterLoop）
- Category: correctness
- Severity: critical
- Description: workflow 通过 hook 串接确定性副作用：`beforeLoop` 读 SCHEMA 提供编译依据，`afterLoop` 更新 index/log 持久化产出。若这些逻辑散落在循环体内或被省略，会导致：编译缺依据、索引不更新、产出无法被后续检索。hook 必须在 workflow 入口注册且逻辑确定。
- Suggested fix: 在 workflow 启动时注册 beforeLoop/afterLoop，禁止在循环体内重复实现等价逻辑。
- Example:
  - Bad:
    ```typescript
    async function run(prompt: string) {
      for (const step of steps) {
        // 每步都读 schema，且忘记更新 index —— 副作用散落/缺失
        const schema = await fs.readFile('SCHEMA.md', 'utf-8');
        yield await engine.run(step, schema);
      }
    }
    ```
  - Good:
    ```typescript
    async function* run(prompt: string): AsyncIterable<EngineEvent> {
      // beforeLoop：确定性读取编译依据
      const schema = await fs.readFile('SCHEMA.md', 'utf-8');
      for (const step of steps) {
        yield await engine.run(step, schema);
      }
      // afterLoop：确定性更新索引与日志
      await withCompileLock(indexPath, () => appendIndex(entries));
      await withCompileLock(logPath, () => appendLog(entries));
    }
    ```

### 状态持久化须用 FileStateStore，runId 唯一
- Category: reliability
- Severity: critical
- Description: 每次 run 的状态（进度、产出、错误）必须持久化，以便客户端断线重连后恢复、历史可追溯。直接用内存变量会随进程重启丢失；用裸文件写入会与并发追加冲突。必须用 `FileStateStore`，且 `runId` 全局唯一，避免状态文件互相覆盖。
- Suggested fix: 所有状态读写走 `FileStateStore`；runId 在创建时生成 UUID 并校验唯一性。
- Example:
  - Bad:
    ```typescript
    // 状态存内存，进程重启即丢失；runId 可能重复导致覆盖
    const state = new Map<string, RunState>();
    state.set(runId, { stage: 'running' });
    ```
  - Good:
    ```typescript
    const stateStore = new FileStateStore(stateDir);

    async function startRun(): Promise<string> {
      const runId = crypto.randomUUID();
      // 校验唯一性，避免覆盖历史 run 的状态
      if (await stateStore.exists(runId)) {
        throw new Error('runId 冲突，请重试');
      }
      await stateStore.init(runId, { stage: 'running', draft: true });
      return runId;
    }
    ```

### prompt 须单点存储于 prompts/ 目录，禁止内联到代码
- Category: maintainability
- Severity: critical
- Description: prompt 文本若内联在 .ts 代码里，会导致：修改 prompt 必须改代码并重新构建、prompt 版本无法独立管理、非开发人员无法调整。prompt 必须作为独立文件放在 `prompts/` 目录，代码运行时按需加载。
- Suggested fix: prompt 存为 `.md` / `.txt` 文件，代码通过路径加载并缓存内容。
- Example:
  - Bad:
    ```typescript
    // prompt 内联在代码里，修改需重新构建
    const prompt = `你是一个 wiki 编译器，请根据 schema:\n${schema}\n生成笔记...`;
    await engine.run(prompt);
    ```
  - Good:
    ```typescript
    // prompt 作为独立文件，非开发人员也可调整，代码只负责加载
    const promptPath = path.join(promptsDir, 'compile.md');
    const template = await fs.readFile(promptPath, 'utf-8');
    const prompt = template.replace('{{schema}}', schema);
    await engine.run(prompt);
    ```
