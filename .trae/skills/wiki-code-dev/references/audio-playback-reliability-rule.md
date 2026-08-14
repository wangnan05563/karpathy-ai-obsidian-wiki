# CODING-AUDIO-PLAYBACK-RELIABILITY — 音频播放可靠性与文案区分

> 对应前端 FR-088 / wiki-auto-testing `frontend_review_static_check` 派生组。
> 基于「聆听页 TTS 合成 + 浏览器播放，两类失败被混为'语音合成失败'误导排查」四维度复盘。

## 问题背景

`<audio>.play()` 的 reject 原因有两种，必须区分，否则会把"浏览器自动播放策略拦截"误报为"语音合成失败"，
误导用户与排查方向（合成其实成功，只是被浏览器拦截需用户手势）：

1. **合成失败**：`res.ok === false`（后端 4xx/5xx）/ `res.blob()` 解析失败 / 网络错误——这是真正的合成链路问题。
2. **播放被拦截**：`a.play()` 返回 Promise reject（`NotAllowedError` / `AbortError`），浏览器自动播放策略要求用户手势触发——合成产物本身没问题。

此外，**切换曲目 / 重新合成前若不重置 `position`/`duration`**，进度条会沿用上一曲的旧值，UI 显示错乱。

## 规则（2 条）

### AP-1 合成失败 vs 播放拦截，文案分两条
把 `synthAndPlay` 的 try 拆为两段：`await` 合成（res.ok / blob 解析）与 `await a.play()` 分开 catch。
```ts
try {
  // —— 合成段 ——
  const res = await apiFetch(`${API_BASE}/tts/synthesize`, { method:'POST', /* ... */ });
  if (!res.ok) throw new Error(`合成失败 HTTP ${res.status}`);
  const blob = await res.blob();
  /* 赋 src ... */
} catch (e) {
  errorMsg.value = '语音合成失败：' + (e as Error).message;  // 仅合成段失败
  isPlaying.value = false; return;
}
try {
  // —— 播放段（独立 try）——
  await a.play();
  isPlaying.value = true;
} catch (e) {
  errorMsg.value = '播放被浏览器拦截，请点按播放按钮';  // 仅播放被拦截
  isPlaying.value = false;
}
```

### AP-2 切换曲目 / 重合成前重置进度
`synthAndPlay` / `startAt` 开头清零 `position.value = 0; duration.value = 0;`，避免沿用上一曲旧进度。
- 不适用：单曲循环且进度本就该保留的场景（但本项目朗读队列逐曲切换，须重置）。

## 适用 / 不适用（维度④）

| 适用场景 | 不适用场景 |
|---------|-----------|
| 前端用 `<audio>` / Web Audio 播放用户触发的媒体，且合成（后端 / TTS）与播放分两步 | 后端直接返回已托管音频文件 URL、前端仅 `<audio src>` 播放（无合成段，失败均归网络/404） |
| 朗读 / TTS 逐曲切换队列（进度须每曲重置） | 单文件连续播放器（进度保留是期望行为） |
| 无用户手势的自动播放（更易触发浏览器拦截） | 用户明确 click 触发的播放（拦截概率低，但仍建议分文案） |

## 对应审查要点

- 前端：`wiki-frontend-code-review` FR-088（audio-playback-reliability-frontend-rule.md）。
- 测试：`wiki-auto-testing` `frontend_review_static_check` 派生组 `audio_autoplay_distinguished`（扫描合成失败文案与播放拦截文案是否分离、进度重置是否到位）。
