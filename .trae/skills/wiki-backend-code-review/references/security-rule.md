# Rule Catalog — 安全

## Scope
- Covers: API Key 管理、路径遍历防护、子进程调用安全、网络绑定、错误信息脱敏。
- 适用对象：所有 `services/api/` 下的代码，重点是涉及外部服务调用、文件路径拼接、子进程执行、网络监听的实现。

## Rules

### API Key 仅通过环境变量引用（apiKeyRef 存变量名），不落盘
- Category: security
- Severity: critical
- Description: API Key 若硬编码在代码或写入配置文件，会随代码库泄露（git 历史、镜像层、日志）。必须仅通过环境变量引用，配置中只存变量名（`apiKeyRef`），运行时从 `process.env` 读取。这样密钥不会进入版本控制。
- Suggested fix: 配置中存 `apiKeyRef: 'OPENAI_API_KEY'`，代码用 `process.env[config.apiKeyRef]` 读取；启动时校验存在性。
- Example:
  - Bad:
    ```typescript
    // 密钥硬编码，会进入 git 历史与镜像
    const adapter = new EngineAdapter({ apiKey: 'sk-xxxxxxxxxxxx' });
    ```
  - Good:
    ```typescript
    // 配置只存变量名，密钥本身只在环境变量中
    const config = { apiKeyRef: 'OPENAI_API_KEY' };
    const apiKey = process.env[config.apiKeyRef];
    if (!apiKey) throw new Error(`环境变量 ${config.apiKeyRef} 未设置`);
    const adapter = new EngineAdapter({ apiKey });
    ```

### 用户输入的文件名/路径须正则校验，禁止 .. 和绝对路径
- Category: security
- Severity: critical
- Description: 用户可控的文件名或路径段若直接拼接到文件系统操作，会形成路径遍历漏洞，攻击者可读写 Vault 之外的任意文件。必须正则白名单校验，拒绝含 `..`、绝对路径（`/` 或盘符开头）、null byte、换行符的输入。
- Suggested fix: 提供统一的路径段校验函数，所有来自 HTTP 请求的路径段必须先过校验。
- Example:
  - Bad:
    ```typescript
    // 直接用用户输入拼路径，../../../ 可跳出 vault
    const file = path.join(vaultRoot, request.params.name);
    await fs.readFile(file);
    ```
  - Good:
    ```typescript
    // 仅允许字母/数字/下划线/短横线/点，且禁止开头为 .
    const NAME_RE = /^[A-Za-z0-9_][A-Za-z0-9._-]*$/;

    function assertSafeName(name: string): void {
      if (!NAME_RE.test(name)) {
        throw new Error(`非法文件名: ${name}`);
      }
      // 二次拦截 .. 和绝对路径，防御正则遗漏
      if (name.includes('..') || path.isAbsolute(name)) {
        throw new Error(`路径遍历: ${name}`);
      }
    }

    const name = (request.params as { name: string }).name;
    assertSafeName(name);
    const file = path.join(vaultRoot, name);
    await fs.readFile(file);
    ```

### 子进程调用须校验命令白名单，禁止 shell: true
- Category: security
- Severity: critical
- Description: `execFile` / `spawn` 若允许 shell 解释（`shell: true`）或命令名来自用户输入，会形成命令注入漏洞，攻击者可通过 `;` / `|` / `` ` `` 等元字符执行任意命令。必须：命令名走白名单、参数以数组形式传入、显式 `shell: false`。
- Suggested fix: 维护允许的命令白名单，`execFile` 必须传参数数组且 `shell: false`。
- Example:
  - Bad:
    ```typescript
    import { exec } from 'child_process';
    // shell 解释 + 用户输入，命令注入
    exec(`git commit -m "${message}"`, (err) => { ... });
    ```
  - Good:
    ```typescript
    import { execFile } from 'child_process/promises';

    const ALLOWED_CMDS = new Set(['git', 'node']);
    async function safeExec(cmd: string, args: string[]): Promise<void> {
      if (!ALLOWED_CMDS.has(cmd)) {
        throw new Error(`命令不在白名单: ${cmd}`);
      }
      // execFile + 参数数组 + shell:false，命令注入无注入点
      await execFile(cmd, args, { shell: false });
    }
    await safeExec('git', ['commit', '-m', message]);
    ```

### localOnly 须默认 true，绑定 localhost
- Category: security
- Severity: critical
- Description: 后端服务若默认绑定 `0.0.0.0`，会暴露在所有网络接口上，局域网甚至公网可直接访问，绕过前端鉴权。开发期也容易因误绑导致服务被外部访问。必须默认 `localOnly: true` 绑定 `127.0.0.1`，显式配置才能开放。
- Suggested fix: 监听地址由配置决定，默认 `127.0.0.1`；生产开放需显式设置并配合鉴权。
- Example:
  - Bad:
    ```typescript
    // 默认绑所有接口，局域网可直接访问
    await app.listen({ port: 3000, host: '0.0.0.0' });
    ```
  - Good:
    ```typescript
    // 默认仅本地访问，需显式配置才开放
    const localOnly = config.localOnly ?? true;
    const host = localOnly ? '127.0.0.1' : '0.0.0.0';
    await app.listen({ port: config.port, host });
    ```

### 错误信息不泄露内部路径/堆栈
- Category: security
- Severity: critical
- Description: 错误响应中若包含内部文件路径、堆栈信息，会帮助攻击者了解服务结构、定位可利用的文件。面向客户端的错误必须只含可读的通用描述，内部细节仅记录到服务端日志。
- Suggested fix: 错误响应统一走脱敏函数，剥离路径/堆栈；服务端日志保留完整信息用于排查。
- Example:
  - Bad:
    ```typescript
    try {
      await fs.readFile(path.join(vaultRoot, name));
    } catch (err) {
      // 直接把含内部路径的错误回给客户端
      return reply.code(500).send({ error: String(err) });
    }
    ```
  - Good:
    ```typescript
    try {
      await fs.readFile(path.join(vaultRoot, name));
    } catch (err) {
      // 服务端记录完整信息用于排查
      request.log.error(err);
      // 客户端只收到脱敏的通用描述
      return reply.code(500).send({ error: '文件读取失败，请检查文件名' });
    }
    ```
