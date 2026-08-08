# Rule Catalog — SSML / Prosody 注入防护 (CODING-SSML-INJECTION)

通用编码规范：任何把外部输入（用户文本 / 前端下发的语速·音量·语调 / 任意 SSML 片段）拼进 TTS 合成请求的场景，必须对 prosody 的 rate/volume/pitch 做格式校验与范围约束，对用户文本做 `<>&` 转义，并禁用免费端点不支持的标签（如 `<mstts:express-as>`，WebSocket 关闭 `code=1007`）。本规则是后端审查条目 `wiki-backend-code-review` BR-074 与前端审查条目 `wiki-frontend-code-review` FR-073 的上位规范。

> 复盘来源：问答页「朗读」改后端 Edge TTS 拟人化。踩坑：① 前端下发的 `rate/volume/pitch` 未校验直接拼进 `<prosody>`，畸形值（如 `rate="1000%"` / 含注入字符）让免费端点返回 `SSML is invalid`（WebSocket 1007）或行为异常；② 用户文本含 `<>&` 未转义破坏 SSML 结构；③ `<mstts:express-as>` 在免费端点不被支持，须用 `<prosody>` 替代。

## Scope

- Covers: 任何 SSML 构造、TTS 请求封装、prosody 参数（语速/音量/语调）来源为用户或前端下发的合成能力。
- Does NOT cover: 纯音频文件播放（无实时合成）；后端合成服务内部实现细节（属后端 BR-*）；无障碍 read-aloud 规范（WCAG）。

## Rules

### CODING-SSML-INJECTION-1: prosody 的 rate/volume/pitch 必须格式校验 + 范围约束

IsUrgent: True（严重）
Category: TTS / SSML 注入防护

#### Description

来自用户 / 前端下发的 `rate` / `volume` / `pitch` 必须匹配白名单正则（绝对百分比 `30%`-`100%`、相对 `x-2`/`+0.5`、或 `default`），超范围或格式不符须 clamp 到默认值或拒绝，禁止原样拼进 `<prosody ...>`。畸形值会触发免费端点 `SSML is invalid`（WebSocket 关闭 1007）或产生异常语速。

#### Suggested Fix

```ts
// ✅ 校验 + 约束后再拼 SSML
const RATE_RE = /^(default|\d{1,3}%|x-?\d(\.\d)?|\+\d(\.\d)?|-?\d(\.\d)?)$/
function safeRate(v: unknown): string {
  return typeof v === 'string' && RATE_RE.test(v.trim()) ? v.trim() : 'default'
}
const ssml = `<speak><prosody rate="${safeRate(rate)}" volume="${safeVolume(volume)}" pitch="${safePitch(pitch)}">${escapeXml(text)}</prosody></speak>`
```

### CODING-SSML-INJECTION-2: 用户文本注入 SSML 前转义 `<>&`

IsUrgent: True（严重）
Category: TTS / SSML 注入防护

#### Description

用户朗读文本在拼入 SSML 前必须转义 `<` `>` `&`（与 `<mstts:express-as>` 等标签无关，任何外部文本都不得破坏 SSML 结构）。未转义文本会让合成端点解析错位或直接报错。

### CODING-SSML-INJECTION-3: 禁用免费端点不支持的标签（express-as）

IsUrgent: True（严重）
Category: TTS / SSML 注入防护

#### Description

`<mstts:express-as>` 在免费 Edge 端点不被支持（WebSocket 关闭 `code=1007 "SSML is invalid"`）。拟人化风格改用 `<prosody rate/volume/pitch>` 表达；若硬要支持 express-as，须走付费/自建端点且显式配置开启，默认关闭。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ssml_injection.enabled` | `true` | 启用本组规则（CODING-SSML-INJECTION） |
| `ssml_injection.rate_regex` | `^(default|\d{1,3}%|x-?\d(\.\d)?|\+\d(\.\d)?|-?\d(\.\d)?)$` | 语速白名单正则 |
| `ssml_injection.volume_regex` | `^(default|\d{1,3}%|x-?\d(\.\d)?|\+\d(\.\d)?|-?\d(\.\d)?)$` | 音量白名单正则 |
| `ssml_injection.pitch_regex` | `^(default|\d{1,3}Hz|x-?\d(\.\d)?|\+\d(\.\d)?|-?\d(\.\d)?)$` | 语调白名单正则 |
| `ssml_injection.default_value` | `default` | 校验失败时的回退值 |
| `ssml_injection.escape_chars` | `<>&` | 须转义的特殊字符 |
| `ssml_injection.forbidden_tags_regex` | `<mstts:express-as` | 免费端点不支持的标签（命中即拒绝/剥离） |
| `ssml_injection.unsupported_endpoint_code` | `1007` | 免费端点拒绝 SSML 的 WebSocket 关闭码 |
