# Storage Boundary Rule

> 所有参数从 `config/coding-standards-config.md` 的 `storage_boundary` 节读取，禁止在规则文件中硬编码。示例中的项目特定值（如 `karpathy-wiki:conversations:*`）仅为说明用途，实际值应从配置读取。

## 触发关键词
localStorage, IndexedDB, sessionStorage, origin, dbGet, dbPut, 浏览器存储

## 规则

### SB-1：跨 origin 数据必须后端持久化
**严重级别**：critical

浏览器存储（localStorage / IndexedDB / sessionStorage）按 origin 隔离。跨 origin 共享的数据必须用后端持久化，浏览器存储仅作单 origin 缓存。

**为什么**：开发模式（localhost:5173）与生产模式（localhost:3000）origin 不同，IndexedDB 数据互不可见，造成"数据丢失"假象。

**正确架构**：
```
权威源：后端文件系统/DB
   ↓
读取：前端通过 API 读取
   ↓
缓存：前端 IndexedDB/localStorage 作为单 origin 缓存（可降级）
```

### SB-2：浏览器存储必须有降级路径
**严重级别**：critical

后端不可用时，前端必须能降级到浏览器存储缓存，主流程不阻断。

**实现模式**：
```typescript
async function loadConversations() {
  try {
    const res = await fetch('/api/conversations');
    if (res.ok) return await res.json();
  } catch {
    // 后端不可用降级
  }
  return await dbGetAll(STORE); // IndexedDB 缓存
}
```

### SB-3：敏感数据禁止明文存 localStorage
**严重级别**：critical

API Key、密码、token 等敏感数据禁止明文存 localStorage（XSS 风险）。必须：
- 后端 config.json 作为唯一权威源
- 前端仅缓存脱敏值（如 ****2345）
- 明文值仅用户输入时短暂存在内存

### SB-4：浏览器存储键必须有命名空间
**严重级别**：suggestion

避免与其他应用冲突，localStorage / IndexedDB 键必须有项目命名空间前缀：
- localStorage: `karpathy-wiki:conversations:*`
- IndexedDB: `karpathy-wiki-chat`

## 检查清单
- [ ] 跨 origin 数据是否用后端持久化
- [ ] 浏览器存储是否有降级路径
- [ ] 敏感数据是否避免 localStorage 明文
- [ ] 存储键是否有命名空间