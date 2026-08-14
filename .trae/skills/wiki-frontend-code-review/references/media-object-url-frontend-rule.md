# FR-087 — ObjectURL 生命周期管理（前端）

> 对应 wiki-code-dev CODING-MEDIA-OBJECT-URL（MO-1~MO-2）；wiki-auto-testing `frontend_review_static_check` 派生组 `object_url_revoked`。
> 基于「聆听页用 `URL.createObjectURL(blob)` 持有 TTS 合成音频、组件常驻（v-show）导致对象泄漏」四维度复盘（含 Sequential Thinking）。

## 规则要点

前端用 `URL.createObjectURL(blob)` 把合成结果（Blob）转为可播放 URL 赋给 `<audio>.src` / `<img>` 时，浏览器为每份 ObjectURL 保留底层 Blob 引用，**直到显式 `revokeObjectURL` 才释放**。常驻组件切换曲目 / 重置状态 / 卸载时若不复活释放，Blob 常驻内存逐渐堆积（内存泄漏）。

- **FR-087-1（create / revoke 成对，Major）**：每次重新合成（赋新 `a.src`）前，先 `revokeObjectURL` 旧 URL；状态重置 / 切换曲目 / 组件卸载（`onBeforeUnmount`）前必须释放当前句柄。
- **FR-087-2（句柄收口到单一变量，Suggestion）**：ObjectURL 句柄须收口到单一组件级变量（如 `objectUrl`），集中管理"释放时机"，避免散落多处 `createObjectURL` 无从追踪；配合 FR-086 的账户重置 watch，重置状态的第一步即 `revokeObjectURL` 当前句柄。

## Wrong / Right

```ts
// Wrong：每次合成都新建 URL，旧 Blob 永不释放（常驻组件下持续泄漏）
function play(blob: Blob) {
  audioEl.value!.src = URL.createObjectURL(blob);
  audioEl.value!.play();
}

// Right：赋新值前先释放旧值，句柄收口到单一变量
let objectUrl: string | null = null;
function play(blob: Blob) {
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = URL.createObjectURL(blob);
  audioEl.value!.src = objectUrl;
  audioEl.value!.play();
}
// 账户切换 / 卸载时：if (objectUrl) { URL.revokeObjectURL(objectUrl); objectUrl = null; }
```

## 适用 / 不适用（维度④）

- **适用**：前端用 `URL.createObjectURL` 持有 Blob（TTS 音频 / 图片预览 / 文件下载）且组件**常驻或频繁重建**（如 v-show 常驻的聆听页、逐曲切换的朗读队列）；同一资源被反复重新合成 / 替换。
- **不适用**：一次性短命组件且明确 `onBeforeUnmount` 释放（仍建议成对，但泄漏窗口短）；静态资源用 `<img src>` / 打包资源 URL（无 ObjectURL 生命周期问题）。

## 参数（来自 config/review-config.md `media_object_url_frontend` 段，零硬编码）

`enabled` / `handle_var_hint` / `severity`。
