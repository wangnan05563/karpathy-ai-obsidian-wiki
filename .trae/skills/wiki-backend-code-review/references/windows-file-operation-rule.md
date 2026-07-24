# Windows 文件操作审查规则（BR-050~051）

> 复盘来源：Skill 导入模块开发中 `deleteSkill` 用 `fs.rm` 删除目录，API 服务进程上下文中 Windows 文件句柄占用导致 `fs.rm`/`rmSync` 静默失败（不抛异常但目录仍然存在），删除后未用 `existsSync` 验证结果导致返回 `{ ok: true }` 但目录残留（CODING-055）。
> 所有可变参数（平台名、删除命令、回退方法、重试次数）从 [config/review-config.md](../config/review-config.md) 的"Windows 文件操作审查参数（windows_file_operation）"章节读取，禁止在本规则文件硬编码具体命令名或平台名。

## Trigger Keywords

fs.rm, rmSync, rd /s /q, execSync, existsSync, Windows, win32, 文件句柄, 静默失败, 路径穿越, SKILL_ID_PATTERN, child_process, 删除目录, 目录残留, fallback, retry

## Rules

### BR-050-1：win32 平台目录删除必须用原生命令 + existsSync 验证

- **Severity**: critical
- **Description**: 在 `windows_file_operation.platform`（默认 `win32`）环境下，API 服务进程上下文中文件句柄占用会导致 `fs.rm`/`rmSync` 静默失败——调用完成、不抛异常，但目录仍然存在。这是因为 Node.js 的 `fs.rm` 在 Windows 上依赖底层 `RemoveDirectory` API，文件句柄占用时返回失败但 Node.js 不一定抛出异常（取决于触发时机与句柄释放竞争）。因此服务进程中的目录删除必须用 `windows_file_operation.delete_command`（默认 `rd /s /q`，通过 `child_process.execSync` 执行）+ `windows_file_operation.verify_after_delete`（默认 `true`，删除后用 `existsSync` 验证）。`fs.rm`/`rmSync` 仅作为 `windows_file_operation.fallback_method` 在原生命令失败时回退使用。评审时确认 win32 平台的目录删除代码使用了 `execSync` + `rd /s /q` 模式而非直接 `fs.rm`。
- **Suggested fix**:

```typescript
// 错误：win32 平台用 fs.rm 删除目录，文件句柄占用时静默失败
import { fs } from 'fs/promises';
await fs.rm(targetDir, { recursive: true, force: true }); // ❌ 不抛异常但目录残留
return { ok: true }; // ❌ 谎报成功

// 正确：win32 用原生命令 rd /s /q + existsSync 验证（命令从 config 读取）
// config: windows_file_operation.delete_command = 'rd /s /q'
import { execSync } from 'child_process';
import { existsSync } from 'fs';

function deleteDirectoryWin32(targetDir: string): void {
  // 原生命令强制释放句柄并删除
  execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' });
  // existsSync 验证删除结果
  if (existsSync(targetDir)) {
    throw new Error(`删除失败：${targetDir} 仍然存在`);
  }
}
```

### BR-050-2：fallback 仍失败必须抛错，禁止静默返回成功

- **Severity**: critical
- **Description**: 原生命令（`rd /s /q`）失败时回退到 `windows_file_operation.fallback_method`（默认 `fs.rmSync`），fallback 仍失败必须抛错——禁止返回 `{ ok: true }` 但目录仍然存在。静默成功会导致上层逻辑误以为删除已完成（如 Skill 导入模块认为旧 Skill 已删除，继续导入新版本，结果两份目录并存）。fallback 应支持 `windows_file_operation.retry_count`（默认 `1`）次重试，重试间隔 `windows_file_operation.retry_delay_ms`（默认 `100` 毫秒）。评审时确认删除函数返回值反映真实删除结果（existsSync 验证为 false 才返回 true）。
- **Suggested fix**:

```typescript
// 错误：fallback 失败时静默返回成功
async function deleteSkill(skillId: string): Promise<{ ok: boolean }> {
  try {
    execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' });
  } catch {
    await fs.rm(targetDir, { recursive: true, force: true }); // fallback
  }
  return { ok: true }; // ❌ 即使目录仍存在也返回成功
}

// 正确：fallback 后用 existsSync 验证，失败抛错
async function deleteSkill(skillId: string): Promise<{ ok: boolean }> {
  try {
    execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' });
  } catch {
    // fallback：fs.rmSync + 重试（次数与间隔从 config 读取）
    for (let i = 0; i <= retryCount; i++) {
      try {
        fs.rmSync(targetDir, { recursive: true, force: true });
        break;
      } catch (err) {
        if (i === retryCount) throw err; // 重试耗尽，抛错
        await new Promise(r => setTimeout(r, retryDelayMs));
      }
    }
  }
  // existsSync 验证删除结果
  if (existsSync(targetDir)) {
    throw new Error(`删除失败：${targetDir} 仍然存在`); // ✅ 抛错而非谎报
  }
  return { ok: true }; // ✅ 真实成功
}
```

### BR-051-1：删除后必须用 existsSync 验证目录已不存在

- **Severity**: critical
- **Description**: 删除操作完成后必须用 `existsSync` 验证目标目录已不存在，返回值反映真实删除结果——禁止假设删除成功。Windows 文件系统的删除操作可能因句柄占用、权限不足、文件被锁定等原因静默失败，`execSync` 不抛异常不等于删除成功。`windows_file_operation.verify_after_delete`（默认 `true`）启用时，所有删除函数必须在删除后调用 `existsSync(targetDir)`，返回 `true`（仍存在）时抛错或返回 `{ ok: false }`。评审时确认删除函数末尾有 `existsSync` 验证逻辑。
- **Suggested fix**:

```typescript
// 错误：删除后未验证，假设成功
execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' });
return { ok: true }; // ❌ 未验证，可能目录仍存在

// 正确：删除后 existsSync 验证
execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' });
if (existsSync(targetDir)) {
  throw new Error(`删除失败：${targetDir} 仍然存在`); // ✅ 验证失败抛错
}
return { ok: true }; // ✅ 验证通过
```

### BR-051-2：路径穿越防护必须在删除前执行

- **Severity**: critical
- **Description**: 删除前必须用白名单正则校验路径参数（如 `SKILL_ID_PATTERN` 校验 skillId），禁止直接拼接用户输入到 `execSync` 命令中。未校验的路径参数可能包含 `..`、`;`、`&` 等特殊字符，导致路径穿越（删除目录外的文件）或命令注入（执行任意命令）。`SKILL_ID_PATTERN` 等正则视为配置项（见 [config/review-config.md](../config/review-config.md) 的"UUID 白名单正则"节），禁止在代码内联硬编码。评审时确认删除函数入口处有路径校验，且 `execSync` 命令中的路径参数经过校验。
- **Suggested fix**:

```typescript
// 错误：未校验 skillId 直接拼接到 execSync 命令
async function deleteSkill(skillId: string): Promise<void> {
  const targetDir = path.join(SKILLS_DIR, skillId);
  execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' }); // ❌ skillId 可能为 ../../../etc
}

// 正确：删除前用 SKILL_ID_PATTERN 校验（正则从 config 读取）
async function deleteSkill(skillId: string): Promise<void> {
  // 路径穿越防护：白名单正则校验（正则从 config 读取，禁止硬编码）
  if (!SKILL_ID_PATTERN.test(skillId)) {
    throw new Error(`无效的 skillId：${skillId}`); // ✅ 校验失败拒绝
  }
  const targetDir = path.join(SKILLS_DIR, skillId);
  // 二次防护：path.resolve 后校验仍在允许根目录内
  const resolved = path.resolve(targetDir);
  if (!resolved.startsWith(path.resolve(SKILLS_DIR))) {
    throw new Error(`路径越界：${targetDir}`); // ✅ startsWith 检查
  }
  execSync(`rd /s /q "${resolved}"`, { stdio: 'ignore' }); // ✅ 已校验
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `windows_file_operation.enabled` | `true` | 是否启用本组规则（BR-050~051） |
| `windows_file_operation.severity` | `critical` | 违规严重级别（critical = 数据丢失风险） |
| `windows_file_operation.platform` | `win32` | 触发原生命令的平台 |
| `windows_file_operation.delete_command` | `rd /s /q` | Windows 原生删除命令 |
| `windows_file_operation.fallback_method` | `fs.rmSync` | 原生命令失败时的回退方法 |
| `windows_file_operation.verify_after_delete` | `true` | 删除后必须 existsSync 验证 |
| `windows_file_operation.retry_count` | `1` | fallback 重试次数 |
| `windows_file_operation.retry_delay_ms` | `100` | 重试间隔（毫秒） |

## 检查方式

1. 用 Grep 在 `api/` 目录检索 `fs.rm`、`fs.rmSync`、`rmSync` 关键字，定位所有目录删除调用点。
2. **BR-050-1 检查**：对每个删除调用点，确认所在平台判断逻辑：
   - `process.platform === 'win32'` 分支内用 `execSync` + `rd /s /q`（或从 config 读取的 `delete_command`） → 通过
   - win32 分支内直接用 `fs.rm`/`rmSync` → **BR-050-1 违规**（未用原生命令）
3. **BR-050-2 检查**：用 Grep 检索删除函数的返回语句：
   - 返回 `{ ok: true }` 前有 `existsSync` 验证 → 通过
   - 直接返回 `{ ok: true }` 无验证 → **BR-050-2 违规**（可能静默成功）
   - fallback 分支有 `retry_count` 重试逻辑 → 通过
   - fallback 分支无重试直接 return → suggestion（建议增加重试）
4. **BR-051-1 检查**：用 Grep 检索 `existsSync` 关键字，确认每个删除函数末尾有验证逻辑：
   - 删除后调用 `existsSync(targetDir)` → 通过
   - 未调用 `existsSync` → **BR-051-1 违规**（未验证删除结果）
5. **BR-051-2 检查**：用 Grep 检索 `execSync` 调用前的路径校验：
   - 调用前有正则校验（如 `SKILL_ID_PATTERN.test(...)`） + `path.resolve` + `startsWith` 检查 → 通过
   - 无校验直接拼接 → **BR-051-2 违规**（路径穿越/命令注入风险）
6. 用 Grep 检索 `process.platform` 判断逻辑：
   - 同时处理 win32 / linux / darwin 分支 → 通过
   - 仅 win32 分支无 fallback → suggestion（建议补充其他平台 fallback）

## 正确示例

```typescript
// services/skills.ts —— 完整合规实现
import { execSync } from 'child_process';
import { existsSync, rmSync } from 'fs';
import path from 'path';
import { config } from '../config/index.js';

// 从 config 读取参数（禁止硬编码）
const SKILL_ID_PATTERN = /^[a-zA-Z0-9_-]+$/; // 实际从 config 读取
const deleteCommand = config.windows_file_operation.delete_command; // 'rd /s /q'
const fallbackMethod = config.windows_file_operation.fallback_method; // 'fs.rmSync'
const retryCount = config.windows_file_operation.retry_count; // 1
const retryDelayMs = config.windows_file_operation.retry_delay_ms; // 100

export function deleteSkill(skillId: string): { ok: boolean } {
  // 1. 路径穿越防护（BR-051-2）：正则校验 + path.resolve + startsWith
  if (!SKILL_ID_PATTERN.test(skillId)) {
    throw new Error(`无效的 skillId：${skillId}`);
  }
  const targetDir = path.join(SKILLS_DIR, skillId);
  const resolved = path.resolve(targetDir);
  if (!resolved.startsWith(path.resolve(SKILLS_DIR))) {
    throw new Error(`路径越界：${targetDir}`);
  }

  // 2. 平台判断 + 原生命令删除（BR-050-1）
  if (process.platform === 'win32') {
    try {
      execSync(`${deleteCommand} "${resolved}"`, { stdio: 'ignore' });
    } catch {
      // 3. fallback：fs.rmSync + 重试（BR-050-2）
      for (let i = 0; i <= retryCount; i++) {
        try {
          rmSync(resolved, { recursive: true, force: true });
          break;
        } catch (err) {
          if (i === retryCount) throw err;
          // 同步等待不可用，用 Atomics.wait 或废弃重试
        }
      }
    }
  } else {
    // 非 win32 平台用 fs.rmSync（Linux/macOS 通常可靠）
    rmSync(resolved, { recursive: true, force: true });
  }

  // 4. existsSync 验证删除结果（BR-051-1）
  if (existsSync(resolved)) {
    throw new Error(`删除失败：${resolved} 仍然存在`);
  }

  return { ok: true }; // ✅ 真实成功
}
```

## 错误示例

```typescript
// 错误 1：win32 用 fs.rm 删除目录，文件句柄占用时静默失败（BR-050-1 违规）
import { fs } from 'fs/promises';
await fs.rm(targetDir, { recursive: true, force: true }); // ❌ 不抛异常但目录残留
return { ok: true };

// 错误 2：fallback 失败时静默返回成功（BR-050-2 违规）
async function deleteSkill(skillId: string) {
  try {
    execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' });
  } catch {
    await fs.rm(targetDir, { recursive: true, force: true }); // fallback 无验证
  }
  return { ok: true }; // ❌ 谎报成功
}

// 错误 3：删除后未 existsSync 验证（BR-051-1 违规）
execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' });
return { ok: true }; // ❌ 未验证，可能目录仍存在

// 错误 4：未校验 skillId 直接拼接（BR-051-2 违规，路径穿越/命令注入）
async function deleteSkill(skillId: string) {
  const targetDir = path.join(SKILLS_DIR, skillId);
  execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' }); // ❌ skillId 可能为 ../../../etc
}

// 错误 5：命令字符串拼接用户输入（BR-051-2 违规，命令注入）
execSync(`rd /s /q ${skillId}`, { stdio: 'ignore' }); // ❌ skillId 含 ; rm -rf / 等命令

// 错误 6：仅 win32 分支无 fallback（suggestion）
if (process.platform === 'win32') {
  execSync(`rd /s /q "${targetDir}"`, { stdio: 'ignore' });
} // ❌ 未处理 execSync 抛错的情况，无 fallback
```

## 适配新项目

- **Linux/macOS 项目**：`platform` 改为 `linux`/`darwin`，`delete_command` 改为 `rm -rf`；`fs.rm`/`rmSync` 在 Linux/macOS 上通常可靠，可作为首选方法，但 `existsSync` 验证仍然必需。
- **容器环境项目**：`windows_file_operation.enabled` 设为 `false`（容器内 fs.rm 通常可靠，无文件句柄占用问题）；但 `existsSync` 验证仍建议保留。
- **跨平台项目**：用 `process.platform` 判断分支，win32 用 `rd /s /q`，其他平台用 `rm -rf` 或 `fs.rm`；统一封装 `deleteDirectory(dir)` 工具函数。
- **Electron 项目**：主进程的目录删除同样适用本规则（Electron 主进程在 Windows 上同样面临文件句柄占用问题）。
- **Tauri 项目**：Rust 后端的 `std::fs::remove_dir_all` 在 Windows 上相对可靠（Rust 的所有权模型减少了句柄占用），但仍建议删除后用 `std::fs::metadata` 验证；本规则主要适用于 Tauri 项目中 Node.js sidecar 进程的文件操作。
- **批量删除项目**：循环删除多个目录时，每个目录独立 `existsSync` 验证，单目录失败不阻塞其他目录删除（错误收集到 `errors[]` 数组返回）。
