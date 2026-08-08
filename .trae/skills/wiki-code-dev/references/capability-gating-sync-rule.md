# CODING-CAPABILITY-GATING-SYNC — 前端功能门控须与后端契约变更同步

> 来源：归档按钮迁移时，后端改为从请求体取内容（不再需要 `sessionId`），但前端 `:can-archive="role==='assistant' && !!sessionId"` 仍要求 sessionId → 默认部署下 `sessionId` 永不存在 → 归档按钮被静默禁用。修复：门控放宽为仅 `role==='assistant'`。
> 对应审查规则：前端 FR-076。

## 触发关键词

`:can-archive` / `canArchive` / 功能门控 / `disabled` / `v-if` / 后端解耦 / 放宽条件 / 后端契约变更 / sessionId

## 严重级别

🟢 Suggestion（功能被静默禁用 / 误报，非崩溃）

## 规则

- **CGS-1**：前端功能门控（按钮 `disabled` / `v-if` / `:can-xxx`）必须随后端契约前提变更**同步放宽/收紧**：后端不再要求某字段（如 `sessionId`）时，前端对应门控必须同步移除该条件，否则功能被静默禁用。
- **CGS-2**：门控条件须以"**内容可得性**"为依据（如 `role==='assistant'` 表示有可归档内容），而非"服务端会话是否存在"（默认部署下永不存在）。
- **CGS-3**：后端放宽 + 前端门控放宽须在**同一变更**完成，禁止只改一端导致契约漂移（对应 FR-062 / FR-066 加法可选 + 跨文件一致性）。
- **CGS-4**：解耦后 grep 前端所有引用该字段的门控点（如 `sessionId`），确保无遗漏的残留条件。

## 正 / 误示例

```vue
<!-- ❌ 误：默认部署 sessionId 永不存在 → 归档按钮永远 disabled -->
<MessageToolbar :can-archive="msg.role === 'assistant' && !!msg.sessionId" />

<!-- ✅ 正：内容自请求体带，门控仅看内容角色 -->
<MessageToolbar :can-archive="msg.role === 'assistant'" />
```

## 检查清单

- [ ] 后端解耦某前提（如不再需 sessionId）时，grep 前端对应 `:can-` 门控是否同步放宽？
- [ ] 门控依据是否为"内容可得性"而非"服务端会话存在性"？
- [ ] 后端 + 前端门控是否同一变更完成（无契约漂移）？
