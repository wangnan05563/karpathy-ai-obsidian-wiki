# Rule Catalog — 去除冗余探测/探针 (CODING-NO-REDUNDANT-PROBE)

通用编码规范：检测外部工具（ffmpeg / ffprobe / 二进制）是否可用时，应使用"能力检测"（命令是否存在 / `ffmpeg -version` 退出码 / 路径探测），禁止为单一目的额外发起一次冗余探测（如用 `ffprobe` 只为判断 ffmpeg 是否存在）。冗余探测增加一次子进程调用、延长启动、且在受限环境（无 ffprobe）下误报不可用。本规则是后端审查条目 `wiki-backend-code-review` BR-080 的上位规范。

> 复盘来源：`audioPostprocess.ts` 的 `isFfmpegAvailable` 先调 `ffprobe` 探测再决定后续逻辑——但判断的是 ffmpeg 能力，ffprobe 探测既冗余又让"仅缺 ffprobe"的环境误判为不可用。修正：用 `ffmpeg -version`（或 `execFileSync('ffmpeg', ['-version'])` 退出码）做能力检测，移除 ffprobe 探测分支。

## Scope

- Covers: 任何"外部工具可用性检测"逻辑（音频 / 视频后处理、压缩、转码前置检查）。
- Does NOT cover: 确实需要 ffprobe 提取元数据的场景（那是功能调用，不是可用性探测）；需要探测多工具能力时的必要最小集合。

## Rules

### CODING-NO-REDUNDANT-PROBE-1: 用能力检测替代冗余探针

IsUrgent: False（建议级）
Category: 子进程 / 健壮性

#### Description

判断工具可用性时，调用该工具自身的最小能力检查（如 `ffmpeg -version`），禁止为判断 A 工具而调用 B 工具探测。冗余探针在 B 缺失的环境会误报 A 不可用，且徒增开销。

#### Suggested Fix

```ts
// ❌ 冗余：用 ffprobe 探测 ffmpeg 能力
function isFfmpegAvailable() {
  try { execFileSync('ffprobe', ['-version']); return true } catch { return false }
}
// ✅ 能力检测：直接探 ffmpeg
function isFfmpegAvailable() {
  try { execFileSync('ffmpeg', ['-version'], { stdio: 'ignore' }); return true } catch { return false }
}
```

### CODING-NO-REDUNDANT-PROBE-2: 缺失工具须优雅降级而非崩溃

IsUrgent: True（严重）
Category: 子进程 / 健壮性

#### Description

能力检测失败（工具不存在）时须返回 `false` 并由调用方降级（如跳过后处理、提示用户），禁止让探测异常冒泡中断主流程。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `no_redundant_probe.enabled` | `true` | 启用本组规则（CODING-NO-REDUNDANT-PROBE） |
| `no_redundant_probe.capability_check` | `ffmpeg -version` | 工具可用性能力检测命令 |
| `no_redundant_probe.redundant_probe_regex` | `ffprobe` | 冗余探针命令（命中即告警） |
| `no_redundant_probe.forbidden_commands` | `ffprobe` | 禁止用于可用性探测的命令清单 |
| `no_redundant_probe.severity` | `suggestion` | 冗余探测违规级别 |
