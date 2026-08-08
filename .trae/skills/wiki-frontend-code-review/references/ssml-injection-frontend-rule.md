# SSML / TTS Prosody 参数前端校验（FR-073）

> 复盘来源：前端朗读功能把用户可调的 `rate/volume/pitch` 直接拼进后端 TTS 端点 SSML，畸形值（非法百分比 / 注入字符）触发后端免费端点 `SSML is invalid`（WebSocket 关闭 1007）；`<mstts:express-as>` 免费端点不支持。后端 BR-074 已做服务端校验，本规则为**前端防御纵深**：下发给后端前先按白名单校验并 clamp，避免畸形值白跑一轮失败（UX 降级），并防止前端任何 SSML 构造直接拼接未转义文本。对应 wiki-code-dev CODING-SSML-INJECTION（后端 BR-074 为权威校验，本规则为前端侧协同）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"ssml_injection_frontend"章节读取，禁止在本规则文件硬编码正则或端点名。

## Trigger Keywords
/api/tts/synthesize, EdgeTtsProvider, prosody, rate, volume, pitch, SSML, express-as, escapeXml, 朗读, 语音合成, 1007, mstts

## Rules

### FR-073-1: 下发前按白名单校验并 clamp prosody 参数

- **Severity**: critical
- **Description**: 前端在把 `rate/volume/pitch` 发给 TTS 端点前，必须先用 `ssml_injection_frontend.rate_regex` / `volume_regex` / `pitch_regex` 校验，超范围或格式不符须 clamp 到 `ssml_injection_frontend.default_value`（如 `default`），禁止把原始用户输入直接转发给后端（后端 BR-074 仍是权威校验，本规则为防御纵深，避免畸形值触发后端 1007 失败往返）。
- **Suggested fix**:
```typescript
const RATE_RE = /^(default|\d{1,3}%|x-?\d(\.\d)?|\+\d(\.\d)?|-?\d(\.\d)?)$/ // 从 ssml_injection_frontend.rate_regex 读取
function safeRate(v: unknown): string {
  return typeof v === 'string' && RATE_RE.test(v.trim()) ? v.trim() : 'default'
}
// 下发给后端前先校验
await synthesize({ text, rate: safeRate(uiRate), volume: safeVolume(uiVolume), pitch: safePitch(uiPitch) })
```

### FR-073-2: 用户文本转义 `<>&` 且禁用 unsupported 标签

- **Severity**: critical
- **Description**: 若前端参与任何 SSML 构造（或透传文本给后端拼 SSML），用户朗读文本必须转义 `ssml_injection_frontend.escape_chars`（`<>&`），禁止破坏 SSML 结构；`<mstts:express-as>` 在免费端点不支持（WebSocket 1007），须禁止或在 UI 层禁止选择该拟人化（与 FR-067 FR-TTS-3 一致）。
- **Suggested fix**:
```typescript
function escapeXml(s: string): string {
  return s.replace(/[<>&]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]!))
}
// 文本透传给后端拼 SSML 前转义
const safeText = escapeXml(userText)
```

### FR-073-3: UI 控件对 prosody 参数做范围约束

- **Severity**: suggestion
- **Description**: 前端 rate/volume/pitch 调节控件（滑块 / 数字输入）应在 UI 层限制取值范围（与正则白名单语义一致），从源头减少畸形值；非法输入即时提示而非允许提交。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `ssml_injection_frontend.enabled` | `true` | 是否启用本规则 |
| `ssml_injection_frontend.rate_regex` | `^(default\|\d{1,3}%\...)$` | 语速白名单正则（绝对百分比 / 相对倍数 / default） |
| `ssml_injection_frontend.volume_regex` | `^(default\|\d{1,3}%\...)$` | 音量白名单正则 |
| `ssml_injection_frontend.pitch_regex` | `^(default\|\d{1,3}Hz\...)$` | 语调白名单正则 |
| `ssml_injection_frontend.default_value` | `default` | 校验失败回退值 |
| `ssml_injection_frontend.escape_chars` | `<>&` | 用户文本拼入 SSML 前须转义字符 |
| `ssml_injection_frontend.forbidden_tags_regex` | `<mstts:express-as` | 免费端点不支持标签（命中即禁止/提示） |
| `ssml_injection_frontend.unsupported_endpoint_code` | `1007` | 免费端点拒绝 SSML 的 WebSocket 关闭码 |

## 检查方式

1. Grep 检索 TTS 调用点（`/api/tts/synthesize` / `EdgeTtsProvider` / `prosody` 构造），提取 `rate/volume/pitch` 的来源。
2. 若参数来自 UI 输入且发送前未过 `ssml_injection_frontend.*_regex` 校验、未 clamp → FR-073-1 违规。
3. 若前端参与 SSML 构造且用户文本拼接前无 `<>&` 转义，或 UI 允许选择 `mstts:express-as` → FR-073-2 违规。
4. 若 rate/volume/pitch 调节控件无取值范围约束 → FR-073-3 建议级提示。

## 适配新项目

- **不同 TTS 服务商**：调整 `forbidden_tags_regex` 与 `unsupported_endpoint_code`；付费端点若支持 express-as，将对应标签移出禁止清单并加显式开关。
- **纯浏览器 speechSynthesis**：无 SSML 构造，本规则不适用；但参数范围校验仍建议保留（对应 FR-067 FR-TTS 系列）。
