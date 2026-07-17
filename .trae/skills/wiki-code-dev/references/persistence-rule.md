# Persistence Rule

## 触发关键词
fs.writeFile, fs.writeFileSync, dbPut, fetch PUT, saveConfig, writeConfig, persistConversation, 落盘, 持久化

## 规则

### P-1：写盘后必须刷新内存缓存
**严重级别**：critical

任何将数据写入持久化介质（文件系统/数据库/远程 API）的函数，写盘成功后必须同步刷新对应的内存缓存。

**错误示例**：
```typescript
async function saveConfig(updates: ConfigUpdates) {
  const merged = { ...current, ...updates };
  await fs.writeFile(configPath, JSON.stringify(merged));
  return merged; // 未刷新 configCache，30s 内 GET 返回旧值
}
```

**正确示例**：
```typescript
async function saveConfig(updates: ConfigUpdates) {
  const merged = { ...current, ...updates };
  await fs.writeFile(configPath, JSON.stringify(merged));
  refreshConfigCache(merged); // 同步刷新缓存
  return merged;
}
```

### P-2：写盘失败必须明确处理
**严重级别**：critical

写盘失败不能静默忽略，必须：抛错给调用方 / 记录日志 / 返回错误码。静默忽略会导致数据丢失无感知。

### P-3：多写入点必须同步
**严重级别**：critical

当数据需写入多个位置（如后端 + 本地缓存）时，必须明确主从关系，主写入失败时从写入的处理策略：
- 主写入成功 + 从写入失败：记录日志，不阻断（从写入是优化）
- 主写入失败 + 从写入成功：降级使用从写入数据，标记为"未同步"
- 主从都失败：抛错给调用方

## 检查清单
- [ ] 每个 writeFile/dbPut 后是否有对应的 cache 刷新
- [ ] 写盘 catch 块是否有日志或抛错
- [ ] 多写入点是否明确主从关系
- [ ] 写盘函数返回值是否反映实际状态