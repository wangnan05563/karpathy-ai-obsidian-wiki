# Fallback Rule

## 触发关键词
try/catch, fetch, 降级, fallback, 后端不可用

## 规则

### FB-1：后端不可用时前端必须降级
**严重级别**：critical

后端 API 调用失败时，前端必须能降级到本地缓存，主流程不阻断。

**实现模式**：
```typescript
async function loadData() {
  try {
    const res = await fetch('/api/data');
    if (res.ok) return await res.json();
  } catch {
    // 后端不可用降级到 IndexedDB
  }
  return await dbGetAll(STORE);
}
```

### FB-2：缓存层失败不阻断主流程
**严重级别**：critical

IndexedDB/localStorage 写入失败（如隐私模式）不阻断主流程，仅记录日志。

**为什么**：缓存是优化而非必需，失败不应影响核心功能。

### FB-3：降级路径必须有日志
**严重级别**：suggestion

降级触发时必须记录日志（console.warn / request.log.error），便于排障：
```typescript
catch (err) {
  console.warn('Backend unavailable, falling back to cache:', err);
  return await dbGetAll(STORE);
}
```

### FB-4：降级数据必须标记来源
**严重级别**：best-practice

降级读缓存数据时，前端应标记数据来源（"cache" / "backend"），UI 可提示用户"离线数据可能过期"。

### FB-5：写入失败的静默层必须明确
**严重级别**：suggestion

明确哪些层的失败可静默：
- 缓存写入（IndexedDB/localStorage）：可静默
- 后端持久化：不可静默，必须抛错
- 主流程数据：不可静默

## 检查清单
- [ ] 后端调用是否有 try/catch 降级
- [ ] 缓存失败是否不阻断主流程
- [ ] 降级路径是否有日志
- [ ] 静默失败层是否明确