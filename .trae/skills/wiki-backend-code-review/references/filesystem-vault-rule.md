# Rule Catalog — 文件系统 / Vault 操作

## Scope
- Covers: 对 Obsidian Vault 及本地文件系统的读写、追加、临时文件、状态持久化操作。
- 适用对象：`vault/` 目录下的实现、`fs/promises` 调用、`index.md` / `log.md` 追加逻辑、`FileStateStore`、临时文件处理。

## Rules

### 写入路径必须在白名单内，禁止修改 SCHEMA.md
- Category: security
- Severity: critical
- Description: AI 工具的写入能力必须收敛在白名单目录内。`SCHEMA.md` 是 Vault 的结构契约文件，由人工维护，AI 改写会破坏后续编译的依据。无白名单约束的写入会带来"AI 误删/误改核心文件"的不可逆风险。
- Suggested fix: 在 vault 模块内维护一份白名单常量，所有写入操作前校验目标路径是否落在白名单内；对 `SCHEMA.md` 等禁改文件单独拦截。
- Example:
  - Bad:
    ```typescript
    // 直接根据用户输入拼路径写入，无白名单校验，可能命中 SCHEMA.md
    const target = path.join(vaultRoot, userFile);
    await fs.writeFile(target, content);
    ```
  - Good:
    ```typescript
    const WRITABLE_DIRS = ['drafts/', 'attachments/', 'work/'];
    const FORBIDDEN_FILES = ['SCHEMA.md'];

    async function safeWrite(vaultRoot: string, relPath: string, content: string): Promise<void> {
      const normalized = path.normalize(relPath);
      if (FORBIDDEN_FILES.some(f => normalized === f || normalized.endsWith('/' + f))) {
        throw new Error(`禁止修改契约文件: ${normalized}`);
      }
      const inWhitelist = WRITABLE_DIRS.some(d => normalized.startsWith(d));
      if (!inWhitelist) {
        throw new Error(`写入路径不在白名单内: ${normalized}`);
      }
      const abs = path.resolve(vaultRoot, normalized);
      // 二次校验：resolve 后的绝对路径必须仍落在 vaultRoot 内，防止符号链接绕过
      if (!abs.startsWith(path.resolve(vaultRoot))) {
        throw new Error(`路径越界: ${normalized}`);
      }
      await fs.writeFile(abs, content, 'utf-8');
    }
    ```

### 用户输入路径须正则白名单校验，防路径遍历
- Category: security
- Severity: critical
- Description: `runId`、文件名、目录段等用户可控输入若直接拼接到文件系统路径，会形成路径遍历漏洞（`../../../etc/passwd`）。必须先正则白名单校验，再拼接，最后用 `path.resolve` + `startsWith` 二次确认落在允许根目录内。
- Suggested fix: 在 utils 下提供统一的路径校验函数，所有来自 HTTP 请求的路径段必须先过校验。
- Example:
  - Bad:
    ```typescript
    // runId 直接拼路径，攻击者可构造 ../../../ 跳出 vault
    const stateFile = path.join(stateDir, `${runId}.json`);
    await fs.readFile(stateFile);
    ```
  - Good:
    ```typescript
    // 白名单正则集中在 config，便于单点维护
    const RUN_ID_RE = /^[a-fA-F0-9-]{36}$/;

    function assertRunId(runId: string): void {
      if (!RUN_ID_RE.test(runId)) {
        throw new Error(`非法 runId: ${runId}`);
      }
    }

    async function readState(stateDir: string, runId: string): Promise<unknown> {
      assertRunId(runId);
      const abs = path.resolve(stateDir, `${runId}.json`);
      // resolve 后再次确认仍在 stateDir 内，防御符号链接等绕过
      if (!abs.startsWith(path.resolve(stateDir) + path.sep)) {
        throw new Error('路径越界');
      }
      return fs.readFile(abs, 'utf-8');
    }
    ```

### 并发文件追加须串行化（withCompileLock）
- Category: correctness
- Severity: critical
- Description: `index.md` / `log.md` 等索引类文件会被多个并发请求追加。若不加锁并发 `appendFile`，会出现行交错、内容覆盖，导致索引损坏、后续编译失败。必须用进程内互斥锁串行化对同一文件的追加操作。
- Suggested fix: 提供基于文件路径 key 的互斥锁（如 `withCompileLock(filePath, fn)`），所有追加操作走锁通道。
- Example:
  - Bad:
    ```typescript
    // 两个并发请求同时 append，行可能交错
    await fs.appendFile(indexPath, `- [[${entry}]]\n`);
    ```
  - Good:
    ```typescript
    // 按 filePath 维度的进程内锁，同一文件追加串行执行
    const locks = new Map<string, Promise<unknown>>();

    async function withCompileLock<T>(filePath: string, fn: () => Promise<T>): Promise<T> {
      const prev = locks.get(filePath) ?? Promise.resolve();
      let release!: () => void;
      const next = new Promise<void>(r => (release = r));
      locks.set(filePath, prev.then(() => next));
      await prev;
      try {
        return await fn();
      } finally {
        release();
        // 仅在当前 promise 仍是链尾时清理，避免误删后续锁
        if (locks.get(filePath) === next) locks.delete(filePath);
      }
    }

    await withCompileLock(indexPath, () =>
      fs.appendFile(indexPath, `- [[${entry}]]\n`, 'utf-8')
    );
    ```

### 部分失败不回滚，标记 draft 保留半成品
- Category: reliability
- Severity: critical
- Description: 长流程中某一步失败时，若回滚已写入内容，会丢失可能很有价值的中间产出（如已生成的一半笔记）。应保留半成品并标记 `draft` 状态，由人工或后续流程收尾。回滚还会增加文件系统一致性风险。
- Suggested fix: 工作流中捕获单步失败，不删除已写文件，仅在状态文件中标记 `draft: true` 与失败原因。
- Example:
  - Bad:
    ```typescript
    try {
      await writeNote(notePath, content);
      await appendIndex(entry);
    } catch (err) {
      // 失败回滚已写文件，丢失中间产出
      await fs.unlink(notePath).catch(() => {});
      throw err;
    }
    ```
  - Good:
    ```typescript
    try {
      await writeNote(notePath, content);
      await appendIndex(entry);
    } catch (err) {
      // 保留半成品，仅标记状态，由人工或后续流程收尾
      await stateStore.mark(runId, { draft: true, error: errMsg(err) });
      // 不 rethrow，让上层决定是否继续
    }
    ```

### 文件操作须使用 fs/promises 异步 API，禁止同步阻塞
- Category: performance
- Severity: critical
- Description: Node.js 单线程模型下，同步文件 API（`fs.readFileSync` / `fs.writeFileSync` 等）会阻塞事件循环，导致所有 SSE 连接、其他请求都被卡住。后端代码必须使用 `fs/promises` 的异步 API。
- Suggested fix: 全量替换同步 API 为 `fs/promises`；启动期一次性加载的只读配置可例外，但须注释说明。
- Example:
  - Bad:
    ```typescript
    import * as fs from 'fs';
    // 阻塞事件循环，SSE 连接会被卡住
    const content = fs.readFileSync(schemaPath, 'utf-8');
    ```
  - Good:
    ```typescript
    import { promises as fs } from 'fs';
    // 异步读取，不阻塞事件循环
    const content = await fs.readFile(schemaPath, 'utf-8');
    ```

### 临时文件须用 os.tmpdir() + 唯一前缀
- Category: reliability
- Severity: suggestion
- Description: 临时文件若硬编码文件名或写到工作目录，并发请求会互相覆盖，且进程退出后残留垃圾。必须用 `os.tmpdir()` 作为根目录，文件名带唯一前缀，并在 finally 中清理。
- Suggested fix: 提供统一的临时文件创建 helper，返回路径与清理函数。
- Example:
  - Bad:
    ```typescript
    // 硬编码文件名，并发请求互相覆盖
    const tmp = path.join(process.cwd(), 'tmp.txt');
    await fs.writeFile(tmp, data);
    ```
  - Good:
    ```typescript
    import os from 'os';

    async function withTempFile<T>(prefix: string, fn: (p: string) => Promise<T>): Promise<T> {
      const tmp = path.join(os.tmpdir(), `${prefix}-${Date.now()}-${process.pid}.tmp`);
      try {
        return await fn(tmp);
      } finally {
        // 无论成功失败都清理，避免残留
        await fs.unlink(tmp).catch(() => {});
      }
    }

    await withTempFile(runId, async (p) => {
      await fs.writeFile(p, data);
      // ... 处理
    });
    ```
