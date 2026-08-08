# Rule Catalog — Runtime Data Privacy (Frontend)

前端运行时数据隐私审查规则：前端新增的落盘目录（IndexedDB 库 / localStorage 命名空间 / 文件系统缓存）须被 gitignore，且持久化默认保守（会话默认不服务端存储）。本规则对应后端 BR-065 的前端视角。

> 复盘来源：前端引入新的 IndexedDB 库或 localStorage 命名空间存储运行期数据（如会话缓存、搜素索引），若对应目录 / 键未纳入 `.gitignore` 或误在服务端持久化，会泄露用户内容。前端侧重点是：(1) 任何新的浏览器端持久化命名空间须在评审中确认其不被意外提交 / 不被服务端当作权威源；(2) 会话默认留在客户端，服务端仅存用户显式保存的对话。

## Scope
- Covers: `frontend/` 下新增的 IndexedDB 库、localStorage 键、Service Worker 缓存、任何持久化到用户本机的存储命名空间；与后端会话存储策略的一致性。
- Does NOT cover: 后端落盘目录的 gitignore（见后端 BR-065）；纯内存状态（不持久化即无隐私风险）。

## Rules

### FR-063-1: 新增浏览器端持久化目录/命名空间须确认 gitignore 与隐私边界

IsUrgent: True
Category: Runtime Data Privacy

#### Description

前端新增的持久化存储（IndexedDB 库名、localStorage 键前缀、Cache Storage 命名空间）若对应"运行期生成、含用户内容"的数据，必须在评审中确认：(a) 浏览器端存储不会被错误提交（如测试固化的 `test_*.json` 等，见 FR-034）；(b) 存储的敏感数据遵循 `persistence-boundary-rule.md` 的"跨 origin 后端权威源 + 浏览器降级缓存"边界——含 `apiKey` / `authtoken` 等敏感字段禁止写入 localStorage 明文。评审时确认：新增持久化命名空间不存敏感字段，且运行期产物不入库。

#### Suggested Fix

```ts
// ❌ 错误：把 apiKey 明文写 localStorage
localStorage.setItem('apiKey', res.data.apiKey) // ❌ 敏感字段明文，XSS 风险

// ✅ 正确：仅存脱敏值/非敏感字段，敏感字段回显用脱敏占位
localStorage.setItem('theme', theme)
// apiKey 仅后端 config.json 权威源，前端展示 '****' 脱敏占位
```

> **示例代码**: 见 persistence-boundary-rule.md 与 sensitive-field-display-rule.md（SF-1）。

### FR-063-2: 持久化默认保守——会话默认不服务端存储

IsUrgent: True
Category: Runtime Data Privacy

#### Description

与后端 BR-065-2 对齐：会话 / 临时交互状态默认留在客户端（IndexedDB 降级缓存），仅当用户显式开启"保存对话"时才将其同步到服务端权威源。前端不得默认把每次交互 POST 到服务端会话存储。评审时确认：会话保存受配置开关（`persistSessions` 之类）保护，默认关闭；未开启时仅本地 IndexedDB 缓存（且按 FR-034 / FR-033 规则不被提交）。

#### Suggested Fix

```ts
// ❌ 错误：每次交互都 POST 服务端会话存储
await fetch('/api/conversations', { method: 'POST', body: JSON.stringify(session) }) // ❌ 默认服务端存

// ✅ 正确：受开关保护，默认仅本地
if (config.persistSessions) {
  await fetch('/api/conversations', { method: 'POST', body: JSON.stringify(session) })
}
// 默认：写入 IndexedDB 降级缓存，不触发服务端
```

> **示例代码**: 见 persistence-boundary-rule.md 降级策略段（backend_unavailable_fallback = indexed-db-cache）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `runtime_data_privacy_frontend.enabled` | `true` | 启用本组规则（FR-063，对应后端 BR-065） |
| `runtime_data_privacy_frontend.severity_br063_1` | `critical` | FR-063-1 敏感字段明文/产物入库违规级别 |
| `runtime_data_privacy_frontend.severity_br063_2` | `critical` | FR-063-2 默认服务端存会话违规级别 |
| `runtime_data_privacy_frontend.forbidden_localstorage_fields` | `apiKey,authtoken,password,secret,cpolarAuthtoken` | 禁止 localStorage 明文字段 |
| `runtime_data_privacy_frontend.server_side_sessions_config_field` | `persistSessions` | 服务端存会话开关字段 |
| `runtime_data_privacy_frontend.gitignore_runtime_artifacts` | `test_screenshots/,test_*.json` | 须 gitignore 的运行期产物 |