# CODING-MEDIA-OBJECT-URL — ObjectURL 生命周期管理

> 对应前端 FR-087 / wiki-auto-testing `frontend_review_static_check` 派生组。
> 基于「聆听页用 `URL.createObjectURL(blob)` 持有 TTS 合成音频、组件常驻导致对象泄漏」四维度复盘。

## 问题背景

音频 / 视频播放前用 `URL.createObjectURL(blob)` 把合成结果（Blob）转为可播放 URL 赋给 `<audio>.src`。
浏览器为每份 ObjectURL 保留底层 Blob 引用，**直到显式 `revokeObjectURL` 才释放**——常驻组件切换曲目 / 重置状态 / 卸载时若不复活释放，Blob 常驻内存逐渐堆积（内存泄漏）。

## 规则（2 条）

### MO-1 创建 / 释放成对
`createObjectURL` 与 `revokeObjectURL` 必须成对：每次重新合成（赋新 `a.src`）前，先 `revokeObjectURL` 旧 URL；
状态重置 / 切换曲目 / 组件卸载（`onBeforeUnmount`）前必须释放。
```ts
// 错误：每次合成都新建 URL，旧 Blob 永不释放
a.src = URL.createObjectURL(blob);

// 正确：赋新值前先释放旧值
if (objectUrl) URL.revokeObjectURL(objectUrl);
objectUrl = URL.createObjectURL(blob);
a.src = objectUrl;
```

### MO-2 收口到单一变量
ObjectURL 句柄须收口到单一模块级 / 组件级变量（如 `objectUrl`），集中管理"释放时机"，避免散落多处 `createObjectURL` 无从追踪。
配合 CODING-PERSISTENT-COMPONENT 的账户重置 watch：重置状态的第一步即 `revokeObjectURL` 当前句柄。

## 适用 / 不适用（维度④）

| 适用场景 | 不适用场景 |
|---------|-----------|
| 前端用 `URL.createObjectURL` 持有 Blob（TTS 音频 / 图片预览 / 文件下载）且组件**常驻或频繁重建** | 一次性短命组件且明确 `onBeforeUnmount` 释放（仍建议成对，但泄漏窗口短） |
| 同一资源被反复重新合成 / 替换（如朗读队列逐曲切换） | 静态资源用 `<img src>` / 打包资源 URL（无 ObjectURL 生命周期问题） |

## 对应审查要点

- 前端：`wiki-frontend-code-review` FR-087（media-object-url-frontend-rule.md）。
- 测试：`wiki-auto-testing` `frontend_review_static_check` 派生组 `object_url_revoked`（扫描 `createObjectURL` 调用点附近是否存在 `revokeObjectURL`，缺失即告警）。
