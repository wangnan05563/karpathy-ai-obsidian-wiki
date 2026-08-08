# Rule Catalog — TTS Neural Fallback (Read-Aloud)

朗读 / 语音合成功能：优先采用 neural TTS（后端合成端点 + 优质 neural 音色）而非浏览器原生 Web Speech API；必须保留浏览器 TTS 为优雅降级；SSML 须转义且禁用免费端点不支持的 `express-as` 风格标签；播放前校验音频有效性并具备重试韧性。本规则基于本项目 Edge TTS 拟人化朗读改造的四维度复盘沉淀（对应 wiki-code-dev `references/tts-neural-fallback-rule.md` CODING-TTS-*）。

> 复盘来源：问答页「朗读」原用浏览器 `speechSynthesis`，自然度差。改为后端 Edge TTS（neural 音色）后拟人化显著提升；但踩坑：① 免费 Edge 端点不支持 `<mstts:express-as>`（WebSocket 关闭 `code=1007 reason="SSML is invalid"`），须改用 `<prosody>`；② 出网抖动偶发返回 0 字节空 MP3，须重试；③ 用户文本未转义会破坏 SSML。前端 `edgeTtsProvider` 调 `/api/tts/synthesize`，首段失败回退浏览器 TTS。

## Scope

- Covers: 新增 / 修改朗读、语音合成、TTS 相关前端代码（provider / composable / UI 控件）；SSML 构造；音色 / 语速 / 语调配置；TTS 失败处理与降级路径。
- Does NOT cover: 后端 TTS 合成实现细节（属后端 BR-*）；纯音频播放器 UI（无合成逻辑）；无障碍 read-aloud 规范（WCAG / ARIA live region）。

## Rules

### FR-TTS-1: 朗读功能优先 neural TTS，而非浏览器 Web Speech API

IsUrgent: False（建议级）
Category: TTS / Neural Fallback

#### Description

朗读 / 语音合成功能应优先使用 neural TTS：前端通过 provider 调用后端合成端点（如 `/api/tts/synthesize`）获取优质 neural 音色音频（如 Edge TTS `zh-CN-XiaoxiaoNeural` 等），而非直接使用浏览器原生 `speechSynthesis` / `SpeechSynthesisUtterance`。理由：neural 音色自然度显著优于各 OS / browser 自带 voice，且跨平台一致、参数可控（语速 / 音量 / 语调）。

#### Suggested Fix

```ts
// ✅ 优先 neural TTS：provider 调后端合成端点
const audio = await ttsProvider.speak(text, { voice: 'zh-CN-XiaoxiaoNeural' })
// ❌ 避免直接依赖浏览器语音（自然度差、跨平台不一致、音色随机）
// const u = new SpeechSynthesisUtterance(text); speechSynthesis.speak(u)
```

> **示例代码**: 见 `edgeTtsProvider.ts`（`composables/tts/`）的 provider 抽象。

### FR-TTS-2: 必须保留浏览器 TTS 为优雅降级，失败不得静默

IsUrgent: True（严重）
Category: TTS / Neural Fallback

#### Description

无论 neural TTS 多优先，必须保留浏览器 `speechSynthesis` 作为优雅降级（graceful fallback）。当 neural 合成失败——网络错误、返回 0 字节空 MP3、非音频响应、超时——须回退到浏览器 TTS 或给出明确错误提示。禁止在合成失败时静默无操作，导致用户点击「朗读」却无任何音频输出。

#### Suggested Fix

```ts
try {
  await speakNeural(text)
} catch (e) {
  // ✅ 回退浏览器 TTS（或明确提示，禁止静默）
  fallbackToBrowserTTS(text)
  // 或：ElMessage.error('朗读失败，请重试')
}
```

> **示例代码**: 见 `edgeTtsProvider.ts` 的「首段失败回退浏览器 TTS」分支。

### FR-TTS-3: SSML 须转义 `<>&` 且禁用免费端点不支持的 express-as

IsUrgent: True（严重）
Category: TTS / Neural Fallback

#### Description

构造 SSML（`<speak>` / `<prosody>`）注入用户文本前，必须转义 `< > &`（`&lt; &gt; &amp;`），防止 SSML 结构破坏或注入。`<mstts:express-as>` 说话风格标签在**免费 Edge TTS 端点不被支持**（WebSocket 关闭 `code=1007 reason="SSML is invalid"`），拟人化请改用 `<prosody rate/volume/pitch>` 参数；不要依赖 express-as（不仅无效，还会多一次失败重试的延迟）。

#### Suggested Fix

```ts
// ✅ 转义用户输入，防 SSML 破坏 / 注入
const safe = text.replace(/[<>&]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]!))
// ✅ 拟人化用 prosody（免费端点支持）
`<speak><voice name="${voice}"><prosody rate="-5%" volume="+2%" pitch="+1Hz">${safe}</prosody></voice></speak>`
// ❌ 免费端点不支持 express-as（1007 关闭，零收益）
// `<speak><mstts:express-as style="narration-relaxed">${text}</mstts:express-as></speak>`
```

> **示例代码**: 见 `edgeTtsClient.ts` 的 `buildSSML` 转义与 prosody 构造。

### FR-TTS-4: 播放前校验音频有效性并具备重试韧性

IsUrgent: False（建议级）
Category: TTS / Neural Fallback

#### Description

出网抖动可能偶发返回 0 字节空 MP3（HTTP 200 但 body 为空）。播放前须校验响应为有效音频（magic bytes `ff f3` / `ff fb` / `ID3`），并在判定失败前重试 2–3 次；连续失败再回退浏览器 TTS 或提示。避免单次空响应即误判为功能失效。

#### Suggested Fix

```ts
// ✅ 校验 magic 后重试，仍失败再降级
for (let i = 1; i <= 3; i++) {
  const buf = await synthesize(text)
  if (buf.length > 1000 && isMp3(buf)) return buf   // isMp3: 前 2 字节 ff f3 / ff fb 或 ID3
}
fallbackToBrowserTTS(text)
```

> **示例代码**: 见 `routes/tts.ts` 的音频响应返回与前端 provider 重试逻辑。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tts_neural_fallback_frontend.enabled` | `true` | 启用本组规则（FR-067） |
| `tts_neural_fallback_frontend.severity_prefer_neural` | `suggestion` | FR-TTS-1 未优先 neural TTS 违规级别 |
| `tts_neural_fallback_frontend.severity_fallback_required` | `critical` | FR-TTS-2 缺浏览器 TTS 降级 / 静默失败违规级别 |
| `tts_neural_fallback_frontend.severity_ssml_safety` | `critical` | FR-TTS-3 未转义 SSML / 用 express-as 违规级别 |
| `tts_neural_fallback_frontend.severity_resilience` | `suggestion` | FR-TTS-4 缺音频校验 / 重试违规级别 |
| `tts_neural_fallback_frontend.synthesize_endpoint` | `/api/tts/synthesize` | neural 合成端点路径 |
| `tts_neural_fallback_frontend.voice_whitelist_pattern` | `^[a-z]{2}-[A-Z]{2}-[A-Za-z]+Neural$` | 音色白名单正则（防非法 / 注入 voice） |
| `tts_neural_fallback_frontend.browser_fallback_api` | `speechSynthesis` | 浏览器优雅降级 API |
| `tts_neural_fallback_frontend.retry_count` | `3` | 空 / 失败响应重试次数 |
| `tts_neural_fallback_frontend.mp3_magic_bytes` | `ff f3, ff fb, 49 44 33` | 有效 MP3 魔数（含 ID3 头） |
