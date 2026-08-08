# SSML / TTS Prosody 注入防护（BR-074）

> 复盘来源：后端 Edge TTS 端点把前端下发的 `rate/volume/pitch` 直接拼进 `<prosody>`、用户文本未转义，畸形值/注入字符导致免费端点返回 `SSML is invalid`（WebSocket 关闭 1007）；`<mstts:express-as>` 在免费端点不被支持。对应 wiki-code-dev CODING-SSML-INJECTION（前端 FR-073 为防御纵深）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"ssml_injection"章节读取，禁止在本规则文件硬编码正则或端点名。

## Trigger Keywords
prosody, rate, volume, pitch, SSML, express-as, escapeXml, /api/tts/synthesize, speak, speechSynthesis, 1007, WebSocket close, mstts

## Rules

### BR-074-1: prosody 的 rate/volume/pitch 必须格式校验 + 范围约束

- **Severity**: critical
- **Description**: 来自用户/前端下发的 `rate/volume/pitch` 必须匹配白名单正则（绝对百分比 / 相对倍数 / default），超范围或格式不符须 clamp 到默认或拒绝，禁止原样拼进 `<prosody ...>`。畸形值触发免费端点 `SSML is invalid`（1007）。
- **Suggested fix**:
```typescript
const RATE_RE = /^(default|\d{1,3}%|x-?\d(\.\d)?|\+\d(\.\d)?|-?\d(\.\d)?)$/ // 从 ssml_injection.rate_regex 读取
function safeRate(v: unknown): string {
  return typeof v === 'string' && RATE_RE.test(v.trim()) ? v.trim() : 'default'
}
```

### BR-074-2: 用户文本注入 SSML 前转义 `<>&`

- **Severity**: critical
- **Description**: 用户朗读文本在拼入 SSML 前必须转义 `<>&`，禁止破坏 SSML 结构。

### BR-074-3: 禁用免费端点不支持的标签（express-as）

- **Severity**: critical
- **Description**: `<mstts:express-as>` 在免费端点不被支持（WebSocket 1007），须剥离或走已配置付费端点；拟人化改用 `<prosody>`。命中 `ssml_injection.forbidden_tags_regex` 即拒绝/剥离。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `ssml_injection.enabled` | `true` | 是否启用本规则 |
| `ssml_injection.rate_regex` | `^(default\|\d{1,3}%\...)$` | 语速白名单正则 |
| `ssml_injection.volume_regex` | `^(default\|\d{1,3}%\...)$` | 音量白名单正则 |
| `ssml_injection.pitch_regex` | `^(default\|\d{1,3}Hz\...)$` | 语调白名单正则 |
| `ssml_injection.default_value` | `default` | 校验失败回退值 |
| `ssml_injection.escape_chars` | `<>&` | 须转义字符 |
| `ssml_injection.forbidden_tags_regex` | `<mstts:express-as` | 不支持标签（命中即剥离） |
| `ssml_injection.unsupported_endpoint_code` | `1007` | 免费端点拒绝 SSML 的关闭码 |

## 检查方式

1. Grep 检索 TTS 端点（`/api/tts/synthesize` 或 `prosody` 构造处），提取拼 SSML 的字段来源。
2. 若字段来自外部输入且未过 `ssml_injection.*_regex` 校验 → BR-074-1 违规。
3. 若用户文本拼接前无 `<>&` 转义 → BR-074-2 违规。
4. 若 SSML 含 `ssml_injection.forbidden_tags_regex` 命中标签且未剥离 → BR-074-3 违规。

## 适配新项目

- **不同 TTS 服务商**：调整 `forbidden_tags_regex` 与 `unsupported_endpoint_code`；付费端点若支持 express-as，将对应标签移出禁止清单并加显式开关。
- **纯浏览器 speechSynthesis**：本规则不适用（无 SSML 构造），前端 FR-073 仍须校验参数范围。
