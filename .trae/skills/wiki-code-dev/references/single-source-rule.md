# Single Source Rule

## 触发关键词
saveApiKey, persistConfig, savePreset, 双写, 同步, 缓存与后端

## 规则

### SS-1：每类数据单一权威源
**严重级别**：critical

每类数据（配置/会话/用户偏好）只能有一个权威存储，其他存储仅作缓存且必须可降级。

**为什么**：双轨保存（如 apiKey 同时存 localStorage 和 config.json）会导致两者独立变化，状态不一致。

**正确架构**：
```
权威源：后端 config.json
   ↓ 写入
前端 localStorage：仅缓存非敏感 UI 状态（baseUrl/model）
   ↓ 读取
前端展示：从后端读取脱敏值
```

### SS-2：权威源变更必须传播
**严重级别**：critical

权威源变更后，所有缓存层必须能感知并更新：
- 主动模式：写入后立即刷新所有缓存
- 被动模式：缓存 TTL + 失效标记

### SS-3：缓存层冲突时以权威源为准
**严重级别**：suggestion

当缓存层与权威源数据冲突时，以权威源为准，缓存层覆盖。

**实现模式**：
```typescript
async function saveApiKey(key: string) {
  await fetch('/api/ai/config', { method: 'PUT', body: JSON.stringify({ apiKey: key }) });
  // 不写 localStorage（避免双轨），仅更新内存展示状态
  apiKeyMasked.value = maskKey(key);
}
```

### SS-4：迁移历史双轨数据
**严重级别**：best-practice

发现历史双轨数据时，必须提供一次性迁移函数：
- 检测旧存储中的明文数据
- 上传到权威源
- 清除旧存储（避免后续读取旧值）

## 检查清单
- [ ] 每类数据是否只有一个权威源
- [ ] 缓存层是否可降级
- [ ] 权威源变更是否传播到缓存
- [ ] 历史双轨数据是否有迁移