# 子进程异步/同步正确性（BR-075）

> 复盘来源：`audioPostprocess.ts` 用异步 `execFile` 调 ffmpeg，却把"已调用"当作"已完成"继续后续逻辑，导致音量与响度归一偶发未生效。修正：需同步结果处用 `execFileSync`（带超时）或 `await` Promise。对应 wiki-code-dev CODING-CHILD-PROCESS-SYNC。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"child_process_sync"章节读取，禁止在本规则文件硬编码超时或命令名。

## Trigger Keywords
execFile, execFileSync, spawn, child_process, ffmpeg, ffprobe, await, Promise, callback, timeout, 同步, 异步

## Rules

### BR-075-1: 需同步结果必须用 *Sync 或显式 await

- **Severity**: critical
- **Description**: 在 `async` 函数内若后续逻辑依赖子进程结果（退出码 / stdout / 文件产物），须 `await` 回调/Promise 包装，或改用 `execFileSync`（带超时）。禁止"调用异步 `execFile` 后不等待就使用结果"——事件循环不会自动等待回调完成。
- **Suggested fix**:
```typescript
import { execFileSync } from 'node:child_process'
const out = execFileSync('ffmpeg', ['-i', src, '-af', 'loudnorm', dst], {
  timeout: child_process_sync.timeout_ms, // 从配置读取
  stdio: ['ignore', 'pipe', 'pipe'],
})
```

### BR-075-2: 子进程调用须带超时与错误传播

- **Severity**: critical
- **Description**: `execFileSync` 必须设置 `timeout`（从配置读取，禁硬编码字面量），超时须抛错并被上层捕获；禁止 `try/catch` 静默吞掉子进程失败导致下游用残缺产物（与 BR-076 一致）。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `child_process_sync.enabled` | `true` | 是否启用本规则 |
| `child_process_sync.sync_calls` | `ffmpeg` | 须同步拿结果的子进程命令清单 |
| `child_process_sync.timeout_ms` | `30000` | 子进程同步调用超时（毫秒，从配置读取） |
| `child_process_sync.require_await_pattern` | `await \| execFileSync` | 结果被使用前的必要同步标志 |
| `child_process_sync.severity_fake_sync` | `critical` | 异步 API 当同步用违规级别 |

## 检查方式

1. Grep 检索 `execFile(` / `spawn(` / `child_process` 调用点。
2. 若调用为异步形式（无 `await`、无 Promise 返回）而后续逻辑直接使用其"结果" → BR-075-1 违规。
3. 若 `execFileSync` 未设 `timeout` 或 `timeout` 为硬编码字面量 → BR-075-2 违规。

## 适配新项目

- **Python 后端**：等价规则为 `subprocess.run(..., check=True, timeout=cfg)` 而非 `subprocess.Popen` 不等待；超时从配置读取。
- **纯前端**：子进程不可用，本规则不适用；但前端调用 TTS 端点仍受 BR-074 / FR-073 约束。
