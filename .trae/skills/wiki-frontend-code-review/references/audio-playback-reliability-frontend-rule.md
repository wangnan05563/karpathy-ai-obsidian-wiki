# FR-088 — 音频播放可靠性与文案区分（前端）

> 对应 wiki-code-dev CODING-AUDIO-PLAYBACK-RELIABILITY（AP-1~AP-2）；wiki-auto-testing `frontend_review_static_check` 派生组 `audio_autoplay_distinguished`。
> 基于「聆听页 TTS 合成 + 浏览器播放，两类失败被混为'语音合成失败'误导排查」四维度复盘（含 Sequential Thinking）。

## 规则要点

`<audio>.play()` 的 reject 原因有两种，必须区分，否则会把"浏览器自动播放策略拦截"误报为"语音合成失败"，误导用户与排查方向（合成其实成功，只是被浏览器拦截需用户手势）：

1. **合成失败**：`res.ok === false`（后端 4xx/5xx）/ `res.blob()` 解析失败 / 网络错误——真正的合成链路问题。
2. **播放被拦截**：`a.play()` 返回 Promise reject（`NotAllowedError` / `AbortError`），浏览器自动播放策略要求用户手势触发——合成产物本身没问题。

- **FR-088-1（合成失败 vs 播放拦截，文案分两条，Major）**：把 `synthAndPlay` 的 try 拆为两段——合成段（res.ok / blob 解析）与播放段（`a.play()`）分开 catch，各自给出区分文案（"语音合成失败" / "播放被浏览器拦截，请点按播放按钮"）。
- **FR-088-2（切换曲目 / 重合成前重置进度，Suggestion）**：`synthAndPlay` / 切换曲目开头清零 `position` / `duration`，避免沿用上一曲旧进度导致进度条错乱。

## Wrong / Right

```ts
// Wrong：合成失败与播放拦截混为一条文案，误导排查
try {
  const res = await apiFetch('/api/tts/synthesize', { method: 'POST', /* ... */ });
  const blob = await res.blob();
  audioEl.value!.src = URL.createObjectURL(blob);
  await audioEl.value!.play();
} catch (e) {
  errorMsg.value = '语音合成失败：' + (e as Error).message; // 误把"被浏览器拦截"也报成合成失败
  isPlaying.value = false;
}

// Right：合成段与播放段分开 try / catch，文案分离
try {
  const res = await apiFetch(`${API_BASE}/tts/synthesize`, { method: 'POST', /* ... */ });
  if (!res.ok) throw new Error(`合成失败 HTTP ${res.status}`);
  const blob = await res.blob();
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = URL.createObjectURL(blob);
  audioEl.value!.src = objectUrl;
} catch (e) {
  errorMsg.value = '语音合成失败：' + (e as Error).message; // 仅合成段失败
  isPlaying.value = false; return;
}
try {
  position.value = 0; duration.value = 0; // 重置进度再播放
  await audioEl.value!.play();
  isPlaying.value = true;
} catch (e) {
  errorMsg.value = '播放被浏览器拦截，请点按播放按钮'; // 仅播放被拦截
  isPlaying.value = false;
}
```

## 适用 / 不适用（维度④）

- **适用**：前端用 `<audio>` / Web Audio 播放用户触发的媒体，且合成（后端 / TTS）与播放分两步；朗读 / TTS 逐曲切换队列（进度须每曲重置）；无用户手势的自动播放（更易触发浏览器拦截）。
- **不适用**：后端直接返回已托管音频文件 URL、前端仅 `<audio src>` 播放（无合成段，失败均归网络/404）；单文件连续播放器（进度保留是期望行为）。

## 参数（来自 config/review-config.md `audio_playback_frontend` 段，零硬编码）

`enabled` / `synth_fail_pattern` / `autoplay_block_pattern` / `reset_progress_on_resynth` / `severity`。
