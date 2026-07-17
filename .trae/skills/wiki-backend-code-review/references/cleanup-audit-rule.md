# Rule Catalog — 清理操作审计

## Scope

- Covers: 清理类路由（删除、归档、回收、过期数据清理）的审计日志、`days` 参数下限保护、`dry_run` 预览模式、单子项失败独立 try-catch、实际执行后状态刷新。
- 适用对象：`services/api/src/routes/` 下涉及批量删除/清理的路由（如 `cleanup.ts`、`archive.ts`）、清理 workflow、清理任务的审计日志写入逻辑。
- Does NOT cover: 通用错误处理模式（见 [error-handling-rule.md](error-handling-rule.md)）、配置项硬编码（见 [config-management-rule.md](config-management-rule.md)）、跨目录路径计算（见 [filesystem-vault-rule.md](filesystem-vault-rule.md)）。

> 所有具体审计路径、下限值、默认值均从 [config/review-config.md](../config/review-config.md) 的"清理操作审计参数"节读取，本规则文件只描述通用模式，不硬编码任何具体值。

## Rules

### CA-1 清理操作必须记录 JSONL 审计日志

- Category: cleanup-audit
- Severity: critical
- Description: 清理操作具有破坏性且不可逆，若无审计日志，事故后无法追溯"谁在何时清理了哪些数据、清理了多少、是否 dry_run"。清理类路由必须按 `audit_log_format`（默认 `jsonl`）向 `audit_log_path`（默认 `.harness/cleanup-audit.log`）追加一条审计记录，每行一个 JSON 对象，便于后续按行 grep / jq 分析。审计日志写入失败必须按 `audit_failure_action`（默认 `non-blocking`）降级——独立 try-catch 包裹，仅记日志，不阻塞主清理流程。
- Suggested fix: 在清理路由的 finally 块中追加审计记录；审计写入用独立 try-catch 包裹，失败时 `console.warn` 记录降级事件。
- Example:
  - Bad:
    ```typescript
    app.post('/api/cleanup', async (request, reply) => {
      const deleted = await deleteExpired(days);
      // 无审计日志，事故后无法追溯
      return reply.send({ deleted: deleted.length });
    });
    ```
  - Good:
    ```typescript
    app.post('/api/cleanup', async (request, reply) => {
      const errors: { target: string; error: string }[] = [];
      let cleanedCount = 0;
      try {
        const targets = await listExpired(days);
        for (const target of targets) {
          try {
            await deleteOne(target);
            cleanedCount++;
          } catch (err) {
            // 单子项失败收集到 errors 数组，不中断整体流程
            errors.push({ target, error: errMsg(err) });
          }
        }
      } catch (err) {
        // 主流程只捕获致命错误（如配置缺失、权限拒绝）
        request.log.error(err);
        return reply.code(500).send({ error: errMsg(err) });
      } finally {
        // 审计日志独立 try-catch，失败不阻塞主流程
        try {
          const record = {
            timestamp: new Date().toISOString(),
            target: 'expired-runs',
            days,
            dry_run: dryRun ?? false,
            cleaned_count: cleanedCount,
            errors,
          };
          await fs.appendFile(AUDIT_LOG_PATH, JSON.stringify(record) + '\n', 'utf-8');
        } catch (auditErr) {
          // 降级：仅记日志，不抛错
          console.warn('[降级] 审计日志写入失败:', auditErr);
        }
      }
      return reply.send({ cleaned_count: cleanedCount, errors });
    });
    ```

### CA-2 审计日志字段必须完整且语义明确

- Category: cleanup-audit
- Severity: critical
- Description: 审计日志字段缺失会导致事故后无法复盘。必备字段：`timestamp`（ISO 8601）、`target`（清理目标类别，如 `expired-runs` / `archived-sessions`）、`days`（清理窗口）、`dry_run`（是否预览模式）、`cleaned_count`（实际清理数量）、`errors`（单子项错误数组，含 `target` / `error` 字段）。字段命名必须用下划线（snake_case），与 JSONL 生态约定一致。
- Suggested fix: 提供 `buildAuditRecord()` 工厂函数，统一构造审计对象；TypeScript 类型定义强制必填字段。
- Example:
  - Bad:
    ```typescript
    // 字段缺失，dry_run 与 errors 未记录
    await fs.appendFile(AUDIT_LOG_PATH, JSON.stringify({ time: Date.now(), count: 5 }) + '\n');
    ```
  - Good:
    ```typescript
    interface CleanupAuditRecord {
      timestamp: string;       // ISO 8601
      target: string;          // 清理目标类别
      days: number;            // 清理窗口
      dry_run: boolean;        // 是否预览模式
      cleaned_count: number;   // 实际清理数量
      errors: { target: string; error: string }[];
    }

    function buildAuditRecord(input: Omit<CleanupAuditRecord, 'timestamp'>): CleanupAuditRecord {
      return { ...input, timestamp: new Date().toISOString() };
    }
    ```

### CA-3 days 参数必须下限保护

- Category: cleanup-audit
- Severity: suggestion
- Description: `days` 参数若被传 0 或负数（如 `-1`），会清理所有数据或语义反转（"清理未来数据"）。必须用 `days_protection` 公式（默认 `Math.max(days_min_value, input)`，下限 `1`）做下限保护。下限值由 config 管理，规则文件不硬编码。
- Suggested fix: 在路由入口对 `days` 做下限保护；若客户端传值小于下限，记 warn 日志但继续执行（用下限值）。
- Example:
  - Bad:
    ```typescript
    const days = (request.body as { days: number }).days;
    // 不做下限保护，days=-1 会清理所有数据
    const targets = await listExpired(days);
    ```
  - Good:
    ```typescript
    const rawDays = (request.body as { days: number }).days;
    // 下限保护：下限值从 config 读取
    const days = Math.max(DAYS_MIN_VALUE, rawDays);
    if (days !== rawDays) {
      request.log.warn({ rawDays, days }, 'days 参数低于下限，已自动提升');
    }
    const targets = await listExpired(days);
    ```

### CA-4 dry_run 预览模式默认必须为 true

- Category: cleanup-audit
- Severity: suggestion
- Description: 清理操作破坏性高，未显式传 `dry_run` 时默认应是预览模式（`dry_run_default` 默认 `true`），让用户先看到"将清理哪些"再决定是否实际执行。仅当客户端显式传 `dry_run: false` 时才执行真实删除。
- Suggested fix: 路由入口用 `??` 取默认值；预览模式下不调用 delete，只返回 `would_clean` 列表。
- Example:
  - Bad:
    ```typescript
    // 不显式传 dry_run 即默认执行真实删除，误触即丢数据
    const dryRun = (request.body as { dry_run?: boolean }).dry_run ?? false;
    ```
  - Good:
    ```typescript
    // 默认预览模式，客户端须显式 dry_run: false 才执行真实删除
    const dryRun = (request.body as { dry_run?: boolean }).dry_run ?? DRY_RUN_DEFAULT;
    if (dryRun) {
      const targets = await listExpired(days);
      return reply.send({ dry_run: true, would_clean: targets });
    }
    // ... 真实删除逻辑
    ```

### CA-5 实际执行后必须刷新状态

- Category: cleanup-audit
- Severity: critical
- Description: 清理路由若在删除后不刷新状态（如 `loadStatus()` / `refreshConfigCache()`），后续读状态接口会返回过期数据，用户误以为清理未生效而重复触发。配置项 `refresh_after_execute`（默认 `true`）控制此行为。预览模式（`dry_run=true`）不实际删除，无需刷新。
- Suggested fix: 真实删除分支在 finally 或返回前调用对应的状态刷新函数；刷新失败时 `console.warn` 记录，不阻塞响应。
- Example:
  - Bad:
    ```typescript
    for (const target of targets) {
      await deleteOne(target);
    }
    // 不刷新状态，下次 GET /status 返回旧值
    return reply.send({ cleaned_count: targets.length });
    ```
  - Good:
    ```typescript
    for (const target of targets) {
      try {
        await deleteOne(target);
        cleanedCount++;
      } catch (err) {
        errors.push({ target, error: errMsg(err) });
      }
    }
    // 实际执行后刷新状态，保证后续读取一致
    try {
      await loadStatus();
    } catch (refreshErr) {
      console.warn('[降级] 状态刷新失败:', refreshErr);
    }
    return reply.send({ cleaned_count: cleanedCount, errors });
    ```

### CA-6 单子项删除失败必须独立 try-catch，错误收集到 errors 数组

- Category: cleanup-audit
- Severity: critical
- Description: 批量清理中单个子项（一条记录、一个文件）删除失败时若直接抛异常中断，会丢失已成功清理的进度，且剩余子项无机会执行。每个子项删除必须用独立 try-catch 包裹（`single_item_try_catch` 默认 `true`），错误信息收集到 `single_item_error_collection`（默认 `errors[]`）数组返回给客户端。主流程 try-catch 只捕获致命错误（`main_flow_catch` 默认 `fatal-only`，如配置缺失、权限拒绝）。审计日志写入用独立 try-catch（`audit_write_catch` 默认 `independent`）降级。
- Suggested fix: 嵌套 try-catch——外层捕获致命错误，内层（循环内）捕获单子项错误。所有参数从 config 的"批量操作错误处理参数"节读取。
- Example:
  - Bad:
    ```typescript
    try {
      for (const target of targets) {
        // 单子项失败直接中断，剩余子项未执行，已清理进度丢失
        await deleteOne(target);
      }
      await writeAuditLog(...);
    } catch (err) {
      // 主流程 catch 同时处理了"单子项失败"和"审计失败"，职责混淆
      return reply.code(500).send({ error: errMsg(err) });
    }
    ```
  - Good:
    ```typescript
    const errors: { target: string; error: string }[] = [];
    let cleanedCount = 0;
    try {
      for (const target of targets) {
        try {
          await deleteOne(target);
          cleanedCount++;
        } catch (err) {
          // 单子项错误收集到数组，不中断循环
          errors.push({ target, error: errMsg(err) });
        }
      }
    } catch (err) {
      // 主流程只捕获致命错误（如配置缺失、权限拒绝）
      request.log.error(err);
      return reply.code(500).send({ error: errMsg(err) });
    } finally {
      // 审计写入独立 try-catch，失败降级
      try {
        await fs.appendFile(AUDIT_LOG_PATH, JSON.stringify(buildAuditRecord({
          target: 'expired-runs', days, dry_run: dryRun,
          cleaned_count: cleanedCount, errors,
        })) + '\n', 'utf-8');
      } catch (auditErr) {
        console.warn('[降级] 审计日志写入失败:', auditErr);
      }
    }
    return reply.send({ cleaned_count: cleanedCount, errors });
    ```

## 适用 / 不适用场景

### 适用

- 评审 `services/api/src/routes/` 下清理/归档/回收类路由（如 `cleanup.ts`、`archive.ts`）。
- 评审批量删除 workflow、定时清理任务、过期数据回收逻辑。
- 评审审计日志写入函数、`days` 参数解析、`dry_run` 默认值处理。
- 评审清理后状态刷新（`loadStatus` / `refreshConfigCache`）逻辑。

### 不适用

- 单条记录的常规删除（如 `DELETE /api/items/:id`）——非批量操作，无审计需求（除非项目策略要求）。
- 通用错误处理模式（见 [error-handling-rule.md](error-handling-rule.md)）。
- 路径遍历防护（见 [security-rule.md](security-rule.md)）——清理目标路径仍须过路径校验，但属另一规则职责。
