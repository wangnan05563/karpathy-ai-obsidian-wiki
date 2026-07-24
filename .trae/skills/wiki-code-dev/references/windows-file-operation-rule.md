# Windows 文件操作验证规则（CODING-055）

> 复盘来源：Skill 导入模块开发中，API 服务进程调用 `fs.rm` 删除目录，调用完成不抛异常，但目录仍然存在。根因是 Windows 文件句柄占用导致 `fs.rm` / `rmSync` 静默失败（不抛异常但目录未删除）。改用 `child_process.execSync` 执行 Windows 原生 `rd /s /q` 命令，fallback 到 `rmSync`，并用 `existsSync` 验证删除结果。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `windows_file_operation` 字段读取，禁止在规则文件中硬编码命令名或平台名。

## 规则

**Windows 环境下服务进程的目录删除应使用原生命令（`rd /s /q`）+ `existsSync` 验证**：`windows_file_operation.platform`（默认 `win32`）环境下，API 服务进程上下文中 Windows 文件句柄占用会导致 `fs.rm` / `rmSync` 静默失败（不抛异常但目录仍存在）。必须用 `windows_file_operation.delete_command`（默认 `rd /s /q`）执行原生删除，`windows_file_operation.fallback_method`（默认 `fs.rmSync`）作为回退，`windows_file_operation.verify_after_delete`（默认 `true`）要求删除后用 `existsSync` 验证目录确实不存在，`windows_file_operation.retry_count`（默认 1）次重试后仍失败必须抛错。

## 适用场景

- Windows 环境下 Node.js 服务进程删除目录（API 服务 / 后台任务 / 构建脚本）
- 删除被文件句柄占用的目录（如服务进程持有 vault 目录的文件句柄）
- Skill 导入模块 / 插件热加载等需要清理旧目录再写入新内容的场景
- CI/CD 流水线在 Windows runner 上清理构建产物
- 任何"fs.rm 调用完成但目录仍存在"的排查场景

## 不适用场景

- Linux / macOS 环境（`fs.rm` 通常可靠，文件句柄占用机制不同）
- 容器环境（容器内文件系统隔离，`fs.rm` 通常可靠）
- 删除单个文件（非目录，文件句柄占用问题较少）
- 前端浏览器环境（无 fs 模块，本规则不适用）
- 静态资源清理（构建产物一次性删除，无句柄占用）

## 前置检查流程

```
服务进程需删除目录:
   ↓
1. 检测当前平台（process.platform）
   ↓
   platform === windows_file_operation.platform (win32) → 使用原生命令删除
   ↓
   其他平台 → 直接用 fs.rmSync（跨平台兼容）
   ↓
2. 执行 windows_file_operation.delete_command (rd /s /q)
   ↓
   命令执行成功 → 进入验证步骤
   ↓
   命令执行失败 → fallback 到 windows_file_operation.fallback_method (fs.rmSync)
   ↓
3. windows_file_operation.verify_after_delete (true) → existsSync 验证目录已删除
   ↓
   目录仍存在 → 重试（windows_file_operation.retry_count 次，间隔 retry_delay_ms）
   ↓
   重试后仍存在 → 抛错（不可静默失败）
   ↓
   目录已删除 → ✅ 完成
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `windows_file_operation.enabled` | `true` | 是否启用 Windows 文件操作守卫 |
| `windows_file_operation.severity` | `error` | 违规严重级别（error = 必须修复） |
| `windows_file_operation.platform` | `win32` | 触发原生命令的平台（process.platform 值） |
| `windows_file_operation.delete_command` | `rd /s /q` | Windows 原生删除命令 |
| `windows_file_operation.delete_command_flags` | `/s /q` | 递归 + 静默标志（/s 递归，/q 静默不确认） |
| `windows_file_operation.fallback_method` | `fs.rmSync` | 原生命令失败时的回退方法 |
| `windows_file_operation.verify_after_delete` | `true` | 删除后必须 existsSync 验证 |
| `windows_file_operation.retry_count` | `1` | fallback 重试次数 |
| `windows_file_operation.retry_delay_ms` | `100` | 重试间隔（毫秒） |

## 检查方式

1. **平台检测**：删除目录前必须检测 `process.platform`，仅 `win32` 平台走原生命令路径
2. **删除验证**：`verify_after_delete` 为 `true` 时，删除后必须 `existsSync` 确认目录不存在，禁止假设删除成功
3. **重试机制**：`fallback_method` 执行后仍失败时，按 `retry_count` 重试，间隔 `retry_delay_ms`
4. **失败抛错**：重试后目录仍存在必须抛错，禁止静默失败（静默失败会导致后续操作读取到旧目录内容）
5. **日志记录**：原生命令执行 / fallback 触发 / 重试 / 最终失败都必须记录日志，便于排查

## 正确示例

```typescript
// services/api/src/utils/fs-operations.ts
import { execSync } from 'child_process';
import { existsSync, rmSync } from 'fs';
// 配置从 config 读取，禁止硬编码命令名或平台名
import { config } from './config.js';

/**
 * Windows 环境下服务进程的目录删除——用原生命令避免 fs.rm 静默失败
 * 为什么不用 fs.rmSync 直接删：Windows 文件句柄占用会导致 fs.rm 静默失败（不抛异常但目录仍存在），
 * 服务进程持有 vault 目录句柄时尤为常见。rd /s /q 是 Windows 原生命令，绕过 Node.js fs 层。
 */
export function removeDirectory(dirPath: string): void {
  const wfo = config.windows_file_operation;
  if (!wfo.enabled) {
    // 守卫禁用时直接用 fs.rmSync
    rmSync(dirPath, { recursive: true, force: true });
    return;
  }

  // 仅 win32 平台用原生命令，其他平台用 fs.rmSync
  const useNativeCommand = process.platform === wfo.platform;

  if (useNativeCommand) {
    try {
      // ✅ Windows 原生命令 rd /s /q，绕过 Node.js fs 层的句柄占用问题
      execSync(`${wfo.delete_command} "${dirPath}"`, { stdio: 'pipe' });
    } catch (e) {
      // 原生命令失败，fallback 到 fs.rmSync
      console.warn(`[fs-ops] 原生命令失败，fallback 到 ${wfo.fallback_method}:`, e);
      rmSync(dirPath, { recursive: true, force: true });
    }
  } else {
    // 非 Windows 平台直接用 fs.rmSync
    rmSync(dirPath, { recursive: true, force: true });
  }

  // ✅ 删除后必须 existsSync 验证（fs.rm 静默失败的兜底）
  if (wfo.verify_after_delete && existsSync(dirPath)) {
    // 验证失败，按 retry_count 重试
    for (let i = 0; i < wfo.retry_count; i++) {
      console.warn(`[fs-ops] 目录仍存在，重试 ${i + 1}/${wfo.retry_count}: ${dirPath}`);
      setTimeout(() => {}, wfo.retry_delay_ms); // 等待句柄释放
      try {
        if (useNativeCommand) {
          execSync(`${wfo.delete_command} "${dirPath}"`, { stdio: 'pipe' });
        } else {
          rmSync(dirPath, { recursive: true, force: true });
        }
      } catch (e) {
        console.error(`[fs-ops] 重试失败:`, e);
      }
      if (!existsSync(dirPath)) break;
    }

    // 重试后仍存在，必须抛错（禁止静默失败）
    if (existsSync(dirPath)) {
      throw new Error(`目录删除失败（重试 ${wfo.retry_count} 次后仍存在）: ${dirPath}`);
    }
  }
}
```

```typescript
// 使用示例：Skill 导入模块清理旧目录
import { removeDirectory } from './utils/fs-operations.js';

async function importSkill(skillPath: string) {
  const targetDir = path.join(skillsDir, skillPath);
  // ✅ 用封装好的 removeDirectory，自动处理 Windows 句柄占用
  if (existsSync(targetDir)) {
    removeDirectory(targetDir); // 原生命令 + existsSync 验证 + 重试
  }
  // 写入新内容...
}
```

## 错误示例

```typescript
// ❌ 错误：直接用 fs.rmSync，不验证删除结果
import { rmSync } from 'fs';

function cleanDir(dirPath: string) {
  rmSync(dirPath, { recursive: true, force: true });
  // ⚠️ Windows 文件句柄占用时，rmSync 静默失败（不抛异常）
  // 目录仍存在，后续写入会读到旧内容
}

// ❌ 错误：假设删除成功，不 existsSync 验证
function importSkill(skillPath: string) {
  const targetDir = path.join(skillsDir, skillPath);
  rmSync(targetDir, { recursive: true, force: true });
  // ⚠️ 未验证 targetDir 是否真的删除
  writeNewSkill(targetDir); // 可能写入到旧目录的残留文件中
}
```

```typescript
// ❌ 错误：硬编码命令名和平台名，未从 config 读取
import { execSync } from 'child_process';

function removeDir(dirPath: string) {
  if (process.platform === 'win32') { // 硬编码平台名
    execSync(`rd /s /q "${dirPath}"`); // 硬编码命令名
  } else {
    rmSync(dirPath, { recursive: true, force: true });
  }
  // ⚠️ 未 existsSync 验证，未重试，未从 config 读取参数
}
```

```typescript
// ❌ 错误：静默失败（删除失败不抛错）
function removeDir(dirPath: string) {
  try {
    rmSync(dirPath, { recursive: true, force: true });
  } catch (e) {
    // ⚠️ 吞掉异常，调用方以为删除成功
    console.error('删除失败:', e);
  }
  // ⚠️ 目录可能仍存在，后续操作读到旧内容
}
```

## 适配新项目

- 适配 Linux/macOS：`platform` 改为 `linux` / `darwin`，`delete_command` 改为 `rm -rf`，`delete_command_flags` 改为 `-rf`
- 适配容器环境：`enabled` 设为 `false`（容器内 `fs.rm` 通常可靠，文件系统隔离无句柄占用问题）
- 适配 WSL 环境：`platform` 检测需区分 WSL（`process.platform === 'linux'` 但 `/mnt/c` 路径走 Windows 文件系统），建议 WSL 中访问 Windows 路径时仍用原生命令
- 适配删除单个文件：`delete_command` 改为 `del /f /q`，`fallback_method` 改为 `fs.unlinkSync`
- 适配需要保留部分文件的场景：不用 `rd /s /q`（会递归删除全部），改用逐文件 `del /f /q` + `existsSync` 验证

## 与其他规则的关系

- 与 CODING-001（路径解析禁用 CWD）联动：删除目录的路径必须基于 `import.meta.url` 或配置锚点，禁止依赖 `process.cwd()`
- 与 CODING-002（写后即刷）联动：删除目录后若有内存缓存指向该目录，必须同步刷新缓存（置为 null 或重建）
- 与 PowerShell 约束规则联动：PowerShell 脚本中删除目录用 `Remove-Item -Recurse -Force`，但服务进程内（Node.js）必须用 `execSync` 调 `rd /s /q`，两者场景不同
- 与 CODING-013（优雅停止）联动：服务进程退出时若需清理临时目录，必须用本规则的原生命令方式，避免退出时 fs.rm 静默失败残留目录
- 与 CODING-027（Composable API 先读后用）联动：调用第三方 fs 工具库（如 `fs-extra` 的 `remove`）前必须 Read 源码确认其在 Windows 下的行为，若仍用 `fs.rm` 底层则有同样的静默失败风险
