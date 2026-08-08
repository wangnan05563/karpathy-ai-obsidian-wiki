# 去除冗余探测/探针（BR-080）

> 复盘来源：`audioPostprocess.ts` 的 `isFfmpegAvailable` 先调 `ffprobe` 探测再决定后续逻辑——但判断的是 ffmpeg 能力，ffprobe 探测既冗余又让"仅缺 ffprobe"的环境误判为不可用。修正：用 `ffmpeg -version`（或 `execFileSync('ffmpeg', ['-version'])` 退出码）做能力检测，移除 ffprobe 探测分支。对应 wiki-code-dev CODING-NO-REDUNDANT-PROBE。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"no_redundant_probe"章节读取，禁止在本规则文件硬编码探测命令。

## Trigger Keywords
isFfmpegAvailable, ffprobe, ffmpeg -version, execFileSync, capability, 可用性检测, 探测, probe

## Rules

### BR-080-1: 用能力检测替代冗余探针

- **Severity**: suggestion
- **Description**: 判断工具可用性时，调用该工具自身的最小能力检查（如 `ffmpeg -version`），禁止为判断 A 工具而调用 B 工具探测。冗余探针在 B 缺失的环境会误报 A 不可用，且徒增开销。
- **Suggested fix**:
```typescript
// ❌ 冗余：用 ffprobe 探测 ffmpeg 能力
function isFfmpegAvailable() {
  try { execFileSync('ffprobe', ['-version']); return true } catch { return false }
}
// ✅ 能力检测：直接探 ffmpeg
function isFfmpegAvailable() {
  try { execFileSync('ffmpeg', ['-version'], { stdio: 'ignore' }); return true } catch { return false }
}
```

### BR-080-2: 缺失工具须优雅降级而非崩溃

- **Severity**: critical
- **Description**: 能力检测失败（工具不存在）时须返回 `false` 并由调用方降级（如跳过后处理、提示用户），禁止让探测异常冒泡中断主流程。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `no_redundant_probe.enabled` | `true` | 是否启用本规则 |
| `no_redundant_probe.capability_check` | `ffmpeg -version` | 工具可用性能力检测命令 |
| `no_redundant_probe.redundant_probe_regex` | `ffprobe` | 冗余探针命令（命中即告警） |
| `no_redundant_probe.forbidden_commands` | `ffprobe` | 禁止用于可用性探测的命令清单 |
| `no_redundant_probe.severity` | `suggestion` | 冗余探测违规级别 |

## 检查方式

1. Grep 检索 `no_redundant_probe.redundant_probe_regex`（如 `ffprobe`）在可用性检测函数中的出现。
2. 若 `ffprobe` 仅用于判断 `ffmpeg` 是否存在（而非真正提取元数据）→ BR-080-1 违规。
3. 若探测异常未 catch 返回 `false` 而是冒泡 → BR-080-2 违规。

## 适配新项目

- **不同工具**：把 `capability_check` 改为目标工具自身的最小版本/存在检查；`forbidden_commands` 列出本项目冗余探针。
- **确需元数据**：若功能本就需要 ffprobe 提取时长/编码，那是功能调用非可用性探测，不在本规则禁止范围。
