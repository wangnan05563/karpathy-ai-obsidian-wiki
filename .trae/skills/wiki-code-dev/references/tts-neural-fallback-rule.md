# Rule Catalog — TTS Neural Fallback (CODING-TTS-*)

通用编码规范：涉及朗读 / 语音合成 / TTS 功能时，优先采用 neural TTS（后端合成端点 + 优质 neural 音色）而非浏览器原生 Web Speech API；必须保留浏览器 TTS 为优雅降级；SSML 须转义且禁用免费端点不支持的 `express-as` 风格标签；播放前校验音频有效性并具备重试韧性。本规则是前端审查条目 `wiki-frontend-code-review` FR-067 的上位规范，前端落地细节与检查清单见该技能 `references/tts-neural-fallback-rule.md`。

> 复盘来源：问答页「朗读」原用浏览器 `speechSynthesis`，自然度差；改后端 Edge TTS（neural 音色）拟人化显著提升。踩坑：① 免费 Edge 端点不支持 `<mstts:express-as>`（WebSocket 关闭 `code=1007`）；② 出网抖动偶发返回 0 字节空 MP3，须重试；③ 用户文本未转义破坏 SSML。

## Scope

- Covers: 任何「把文本念出来」的能力——朗读、语音播报、TTS 请求封装、SSML 构造、音色 / 语速 / 语调配置、合成失败处理。
- Does NOT cover: 纯音频文件播放（无实时合成）；后端合成服务内部实现（属后端 BR-*）；无障碍 read-aloud 规范（WCAG）。

## Rules

### CODING-TTS-1: 优先 neural TTS，而非浏览器 Web Speech API

IsUrgent: False（建议级）
Category: TTS / Neural Fallback

#### Description

朗读 / 语音合成默认走 neural TTS：由前端 provider 调用后端合成端点（如 `/api/tts/synthesize`）拿到优质 neural 音色音频，而不是 `new SpeechSynthesisUtterance` + `speechSynthesis.speak`。理由：neural 音色自然度显著优于各 OS / browser 自带 voice，跨平台一致、参数可控。

#### Suggested Fix

```ts
// ✅ 优先 neural TTS（provider 抽象后端合成端点）
await ttsProvider.speak(text, { voice: 'zh-CN-XiaoxiaoNeural' })
```

### CODING-TTS-2: 浏览器 TTS 必须作为优雅降级，失败不得静默

IsUrgent: True（严重）
Category: TTS / Neural Fallback

#### Description

无论 neural TTS 多优先，浏览器 `speechSynthesis` 必须保留为 graceful fallback。合成失败（网络错误 / 0 字节空 MP3 / 非音频 / 超时）须回退浏览器 TTS 或明确报错，禁止静默无音频。

### CODING-TTS-3: SSML 转义 `<>&`，禁用免费端点不支持的 express-as

IsUrgent: True（严重）
Category: TTS / Neural Fallback

#### Description

用户文本注入 SSML 前转义 `<>&`。`<mstts:express-as>` 在免费 Edge 端点不被支持（WebSocket 关闭 `code=1007 "SSML is invalid"`），拟人化改用 `<prosody rate/volume/pitch>`。

### CODING-TTS-4: 播放前校验音频有效性并重试

IsUrgent: False（建议级）
Category: TTS / Neural Fallback

#### Description

出网抖动偶发返回 0 字节空 MP3；播放前校验 magic bytes（`ff f3` / `ff fb` / `ID3`），失败前重试 2–3 次，仍失败再降级或提示。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tts_neural_fallback.enabled` | `true` | 启用本组规则（CODING-TTS-*） |
| `tts_neural_fallback.synthesize_endpoint` | `/api/tts/synthesize` | neural 合成端点路径 |
| `tts_neural_fallback.voice_whitelist_pattern` | `^[a-z]{2}-[A-Z]{2}-[A-Za-z]+Neural$` | 音色白名单正则 |
| `tts_neural_fallback.browser_fallback_api` | `speechSynthesis` | 浏览器优雅降级 API |
| `tts_neural_fallback.retry_count` | `3` | 空 / 失败响应重试次数 |
| `tts_neural_fallback.mp3_magic_bytes` | `ff f3, ff fb, 49 44 33` | 有效 MP3 魔数（含 ID3 头） |
