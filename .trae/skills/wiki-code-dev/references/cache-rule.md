# Cache Rule

## 触发关键词
configCache, cache, TTL, loadConfig, getCached, memoize, 缓存

## 规则

### C-1：写后即刷
**严重级别**：critical

任何修改持久化数据的函数，写盘后必须立即刷新内存缓存，禁止依赖 TTL 自然过期。

**为什么**：用户保存配置后立即读取，期望看到新值。若依赖 TTL（如 30s），用户会看到"保存未生效"假象。

**实现模式**：
```typescript
function refreshCache(data: T): void {
  cache.data = data;
  cache.loadedAt = Date.now();
}

async function save(data: T): Promise<T> {
  await persist(data);
  refreshCache(data); // 写后即刷
  return data;
}
```

### C-2：缓存读取必须有降级
**严重级别**：suggestion

缓存 miss 时必须降级到源头读取（文件/DB/远程），不能返回 null/undefined 而不尝试源头。

### C-3：缓存失效条件必须明确
**严重级别**：suggestion

缓存必须明确以下失效条件之一：
- TTL 过期（时间维度）
- 主动刷新（事件维度）
- 版本号变化（数据维度）

### C-4：并发写缓存的原子性
**严重级别**：best-practice

多并发写入同一缓存键时，最后写入会覆盖前面。若数据有依赖关系，需用锁或队列保证原子性。

## 检查清单
- [ ] 每个 save/write/update 函数是否调用 refreshCache
- [ ] 缓存 miss 是否降级到源头
- [ ] TTL 是否在 config 中可配置
- [ ] 并发写是否有保护