# 审查结果输出格式（Review Output Format）

> 本文件定义 wiki-frontend-code-review 的结构化审查结果模板。所有规则文件输出的 findings 须遵循此格式，便于人类快速分级与追踪。严重级别定义与 `config/review-config.md` 的 `severity_critical` / `severity_warning` / `severity_suggestion` / `severity_positive` 一致。
>
> 本格式为呈现层约定，不改变任何规则判定逻辑；规则文件本身不硬编码严重级别文案。与 SKILL.md 的 Template A / Template B 并存：先按严重级别分组，每条 finding 用下方行格式，最后追加固定区块。

## 严重级别图例（Severity Legend）

| 图标 | 级别 | 含义 | 是否阻断合并 |
|------|------|------|--------------|
| 🔴 Critical | 严重 | 安全漏洞 / 路径穿越 / 硬编码密钥 / ESM 接线断裂 / 前后端类型漂移（type-drift）/ `.ts` 被 `.js` 遮蔽导致修改不生效等 | 是，必须修复 |
| 🟡 Warning | 警告 | 隐私 / 持久化边界 / 契约不匹配（contract-mismatch，如后端事件新增字段前端未同步）/ 配置可移植性等应修复但不立即阻断的问题 | 建议修复 |
| 🟢 Suggestion | 建议 | 最佳实践 / nit / 可选优化 | 可选 |

> 具体每条 finding 的严重级别由对应规则在 `config/review-config.md` 中定义的 `severity_*` 参数决定（如 `ts_js_shadowing_frontend.severity_br061_1`、`type_sync_done_event_frontend.severity_br062_1`）。

## 单条发现格式（Per-finding Format）

每条 finding 严格按以下字段顺序呈现，字段间用 `|` 分隔：

```
File:line | Rule code | Severity | Problem | Fix | Verification
```

- **File:line**：触发文件相对项目根路径 + 行号（如 `frontend/src/types.ts:30`）。
- **Rule code**：对应规则编号（如 `FR-061-1`、`FR-062-1`、`FR-063-2`）。
- **Severity**：从图例取 🔴/🟡/🟢。
- **Problem**：一句话描述问题本质（必要时附代表性片段）。
- **Fix**：建议修复动作（可附最小代码示例引用）。
- **Verification**：验证修复是否生效的命令/步骤（如 `git ls-files 'frontend/src/**/*.js'`、`npx vue-tsc --noEmit && npx vite build`、跨文件比对 types.ts）。

### 示例

```
frontend/src/types.ts:30 | FR-062-1 | 🟡 Warning | 后端 done 事件新增 governor/threadId，前端 DoneEvent 未同步，消费时为 undefined | 同 PR 给 DoneEvent 加 governor?: string; threadId?: string | 跨文件比对 api/src/types.ts 与 frontend/src/types.ts 字段
frontend/src/views/Query.vue:88 | FR-061-1 | 🔴 Critical | src/ 下存在编译产物 foo.js，Vite 优先解析 .js，foo.ts 修改静默不生效 | 清理 src/**/*.js 与 *.js.map，CI 增加 git ls-files 检查 | npx vue-tsc --noEmit && npx vite build 验证
```

## 结尾区块（Mandatory Sections）

每次审查输出在 findings 之后须包含：

### ✅ What's Good（优点）

列出本次变更中做得好的点（正面反馈），至少 1 条；若无则写"本次无特别亮点"。例如：
- `vite.config.ts` 已显式 `resolve.extensions` 且 `.ts` 在 `.js` 之前。
- done 事件新字段已加法且可选，向后兼容。

### 总体结论（Overall Verdict Line）

一行总结，明确是否可合并：

```
Verdict: 🔴 BLOCKED — N 个 Critical 须修复后方可合并。  /  🟡 NEEDS FIX — M 个 Warning 建议修复。  /  🟢 APPROVED — 无阻断项，可合并。
```

## 与既有模板的关系

- SKILL.md 的 Template A（有发现）/ Template B（无发现）仍用于前端评审主输出骨架。
- 本格式作为结构化 findings 的统一渲染约定：先按严重级别（🔴→🟡→🟢）分组，组内按规则类别排序，每条 finding 用上述 `File:line | ...` 行呈现，最后追加 ✅ What's Good 与 Verdict，再按 SKILL.md 要求决定是否追问是否应用修复。
