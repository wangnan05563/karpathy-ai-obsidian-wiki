# 安全删除 DOM 节点（FR-074）

> 复盘来源：归档按钮迁移时，删除了功能 DOM 节点（如 `.msg-actions`）但未确认其 class/id 的引用已清零，导致 CSS 选择器、测试断言、事件绑定悬空失效（选择器匹配不到、测试误报通过、交互无响应）。本规则要求"删除 DOM 节点前必须交叉验证所有引用清零，且 DOM 删除与引用更新在同一变更完成"。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"safe_dom_delete"章节读取，禁止在本规则文件硬编码 glob / 阈值。

## Trigger Keywords
removeChild, classList.remove, remove, 删除 DOM, 删节点, 删 .msg-actions, 引用清零, 安全删, stale reference, grep, querySelector, getElementsByClassName

## Rules

### FR-074-1: 删除仍被引用的 DOM 节点前须交叉验证引用清零

- **Severity**: critical
- **Description**: 当评审范围涉及移除/重命名 DOM 节点（删除元素、移除 class/id、迁移按钮）时，必须先用 `safe_dom_delete.verify_methods`（默认 grep + glob）在 `safe_dom_delete.test_file_patterns`（默认 `**/test_*.py,**/*.spec.ts,**/*.test.ts`）与样式/脚本中交叉核查该 class/id 的引用；`safe_dom_delete.stale_reference_threshold` 默认 0，即不允许任何残留引用。残留引用会导致选择器悬空、测试误报、交互失效。
- **Suggested fix**:
```typescript
// 删除 .msg-actions 前，先 grep 全仓确认无残留引用（含测试选择器）：
//   grep -rn "msg-actions" frontend/src frontend/tests
// 若仍有引用（如 ChatView.vue 的 test selector、e2e 断言），须在本次变更内一并清除
function removeMsgActions(el: HTMLElement) {
  el.remove() // 仅当 grep 显示引用计数 = 0 时执行
}
```

### FR-074-2: DOM 变更与引用更新须同 PR 完成

- **Severity**: critical
- **Description**: `safe_dom_delete.require_same_commit` 默认 true —— DOM 删除（或 class/id 变更）与所有引用更新（CSS 选择器、测试断言、事件绑定）必须落在**同一变更**内，禁止"先删节点、后续 PR 再清理引用"的割裂做法，否则中间态会引入悬空引用 / 误报。

### FR-074-3: DOM 变更优先保留原 class 名再同步引用

- **Severity**: suggestion
- **Description**: `safe_dom_delete.preserve_original_class_first` 默认 true —— 做 DOM 结构调整时，优先保留原 class 名作为对照，逐步同步引用，而非直接重命名 + 删旧引用导致中间态不可观测。仅作建议级提示。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `safe_dom_delete.enabled` | `true` | 是否启用本规则 |
| `safe_dom_delete.test_file_patterns` | `**/test_*.py,**/*.spec.ts,**/*.test.ts` | 须核查引用清零的测试文件 glob |
| `safe_dom_delete.verify_methods` | `grep,glob` | class/id 引用交叉验证方法 |
| `safe_dom_delete.stale_reference_threshold` | `0` | 失效 class/id 引用容忍阈值（0 = 必须清零） |
| `safe_dom_delete.require_same_commit` | `true` | DOM 删除与引用更新须同 PR 完成 |
| `safe_dom_delete.preserve_original_class_first` | `true` | DOM 变更时优先保留原 class 名再同步引用 |
| `safe_dom_delete.severity` | `critical` | 删除仍被引用节点导致选择器/断言悬空违规级别 |

## 检查方式

1. Grep 检索 `removeChild` / `classList.remove` / 删除语句 / 被删 class/id（如 `.msg-actions`）。
2. 对每个被删节点，用 `verify_methods` 在 `test_file_patterns` 与源码交叉核查引用计数；若 > `stale_reference_threshold` → FR-074-1 违规。
3. 若 DOM 删除与引用更新不在同一变更 → FR-074-2 违规。
4. 若直接重命名 + 删旧引用、无保留对照 → FR-074-3 建议级提示。

## 适配新项目

- **不同测试框架**：调整 `test_file_patterns` 匹配本项目测试后缀（如 `.spec.js` / `test_*.rs`）。
- **纯服务端模板（无前端 DOM）**：本规则不适用。
