# Rule Catalog — 子进程异步/同步正确性 (CODING-CHILD-PROCESS-SYNC)

通用编码规范：调用子进程（`execFile` / `execFileSync` / `spawn`）时，必须明确"要同步结果还是异步事件"，并选用匹配的 API：需要立即拿到结果就用 `*Sync` 或在 `async` 函数内 `await` 回调/Promise；需要异步事件流（SSE 心跳、长任务进度）才用回调/事件式。把异步 API（如 `execFile`）当成同步用——结果未产生就被当作已完成——是典型的"假同步" bug。本规则是后端审查条目 `wiki-backend-code-review` BR-075 的上位规范。

> 复盘来源：音频后处理 `audioPostprocess.ts` 用 `execFile`（异步）调 ffmpeg，却直接把"已调用"当作"已完成"继续后续逻辑，导致音量与响度归一偶发未生效。修正：需同步结果处改用 `execFileSync`（带超时），或 `await` 返回的 Promise；仅在真正需要异步事件流时保留回调式。

## Scope

- Covers: 任何 `child_process` 调用、ffmpeg / ffprobe / 外部 CLI 封装、音频 / 视频后处理、需要子进程退出码或 stdout 的同步计算。
- Does NOT cover: 纯前端浏览器 API；无需子进程结果的"即发即忘"日志类调用（仍须处理错误）。

## Rules

### CODING-CHILD-PROCESS-SYNC-1: 需同步结果必须用 *Sync 或显式 await

IsUrgent: True（严重）
Category: 子进程 / 异步同步

#### Description

在 `async` 函数内若后续逻辑依赖子进程结果（退出码 / stdout / 文件产物），要么 `await` 回调/Promise 包装，要么改用 `execFileSync`（带超时）。禁止"调用异步 `execFile` 后不等待就使用结果"——事件循环不会自动等待回调完成。

#### Suggested Fix

```ts
// ✅ 需要同步结果：execFileSync + 超时
import { execFileSync } from 'node:child_process'
const out = execFileSync('ffmpeg', ['-i', src, '-af', 'loudnorm', dst], {
  timeout: child_process_sync.timeout_ms, // 从配置读取
  stdio: ['ignore', 'pipe', 'pipe'],
})
// ✅ 或 await 回调式
const { stdout } = await new Promise<{ stdout: string }>((res, rej) => {
  execFile('ffmpeg', [...], (err, stdout) => err ? rej(err) : res({ stdout }))
})
```

### CODING-CHILD-PROCESS-SYNC-2: 子进程调用须带超时与错误传播

IsUrgent: True（严重）
Category: 子进程 / 异步同步

#### Description

`execFileSync` 必须设置 `timeout`（从配置读取，禁止硬编码字面量），超时须抛错并被上层捕获处理；禁止 `try/catch` 静默吞掉子进程失败导致下游用残缺产物。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `child_process_sync.enabled` | `true` | 启用本组规则（CODING-CHILD-PROCESS-SYNC） |
| `child_process_sync.sync_calls` | `ffmpeg` | 须同步拿结果的子进程命令清单（白名单） |
| `child_process_sync.timeout_ms` | `30000` | 子进程同步调用超时（毫秒，从配置读取，禁硬编码） |
| `child_process_sync.require_await_pattern` | `await | execFileSync` | 结果被使用前的必要同步标志 |
| `child_process_sync.severity_fake_sync` | `critical` | 异步 API 当同步用（结果未等待）违规级别 |
