---
name: wiki-frontend-code-review
description: "Review Vue 3 + Element Plus + Pinia frontend code for the wiki project. Invoke when user asks to review, analyze, or improve frontend files (e.g., .vue, .ts) under packages/web/. Covers Vue Composition API, Element Plus, Pinia, performance, and type safety."
---

# Wiki Frontend Code Review

## Intent
Use this skill whenever the user asks to review, analyze, or improve frontend code of the wiki project (especially `.vue` / `.ts` / `.tsx` files under `packages/web/`). Support two review modes:

1. **Pending-change review** – inspect staged/working-tree files slated for commit and flag checklist violations before submission.
2. **File-targeted review** – review the specific file(s) the user names and report the relevant checklist findings.

Scope and non-goals (backend code, build scripts, config files) are defined in [config/review-config.md](config/review-config.md) under "适用 / 不适用场景". When in doubt about whether a file is in scope, consult that section first.

Stick to the checklist below for every applicable file and mode. Do not invent rules outside the catalog.

## Checklist
The living checklist is split by category across the rule files below. Treat them as the canonical set of rules to follow — route each file to the matching rule file by its path/content pattern.

| 路径 / 内容模式                                  | 适用规则文件                                                     |
| ------------------------------------------------ | ---------------------------------------------------------------- |
| `.vue` 文件、`<script setup>`、生命周期、watch   | [references/vue-composition-rule.md](references/vue-composition-rule.md) |
| 使用 `el-*` 组件、`ElMessage`、表单、弹窗、图标  | [references/element-plus-rule.md](references/element-plus-rule.md)       |
| `defineStore`、store 内部状态/action、SSE action | [references/pinia-store-rule.md](references/pinia-store-rule.md)         |
| vis-network、resize、v-for、SSE 流式消费         | [references/performance-rule.md](references/performance-rule.md)         |
| `interface`/`type`、fetch、JSON.parse、ref 泛型  | [references/type-safety-rule.md](references/type-safety-rule.md)        |
| CSS 变量、`data-theme`、`rgba()`、SVG `fill`/`stroke`、`getComputedStyle` | [references/theming-rule.md](references/theming-rule.md) |
| localStorage、apiKey、预设切换、脱敏值 ****、恢复初始配置 | [references/config-isolation-rule.md](references/config-isolation-rule.md) |

All configurable parameters (directory mapping, tech stack, performance thresholds, SSE event types) live in [config/review-config.md](config/review-config.md). Rule files describe general patterns only and reference the config for concrete values — never hardcode thresholds in rule files.

Flag each rule violation with urgency metadata so future reviewers can prioritize fixes.

## Review Process
1. **打开相关组件/模块**：定位待评审的 `.vue` / `.ts` / `.tsx` 文件，按 `config/review-config.md` 的目录映射确认其在 `packages/web/` 范围内；不在范围内则跳过并说明原因。
2. **读取评审参数**：打开 [config/review-config.md](config/review-config.md) 获取当前的技术栈版本、性能阈值（vis-network 三级降级节点数、窄屏断点）、SSE 事件类型约定、组件设计规范（RobotAvatar / 马卡龙配色 / 毛玻璃卡片）。获取主题色系统配置（主题列表、CSS 变量目录、alpha 命名规则、主题色白名单）。
3. **按 Checklist 路由**：根据文件路径与内容特征，匹配上表中的规则文件；一个文件可能命中多个规则文件（如 `.vue` 既命中 Vue Composition 又命中 Element Plus），均需逐条核对。
4. **记录偏离**：对每条规则，记录代码偏离的具体位置（文件路径 + 行号）与一段代表性代码片段；若规则中给出 Wrong/Right 示例，对照判断。
5. **组装输出**：按下方 Required output 输出。先按 **Urgent** 分组（urgent 在前），再按类别顺序排序（Vue Composition → Element Plus → Pinia Store → Performance → Type Safety → Theming）。无任何偏离时使用 Template B。

## Required output
When invoked, the response must exactly follow one of the two templates:

### Template A (any findings)
```
# Code review
Found <N> urgent issues need to be fixed:

## 1 <brief description of bug>
FilePath: <path> line <line>
<relevant code snippet or pointer>


### Suggested fix
<brief description of suggested fix>

---
... (repeat for each urgent issue) ...

Found <M> suggestions for improvement:

## 1 <brief description of suggestion>
FilePath: <path> line <line>
<relevant code snippet or pointer>


### Suggested fix
<brief description of suggested fix>

---

... (repeat for each suggestion) ...
```

If there are no urgent issues, omit that section. If there are no suggestions, omit that section.

If the issue number is more than 10, summarize as "10+ urgent issues" or "10+ suggestions" and just output the first 10 issues.

Don't compress the blank lines between sections; keep them as-is for readability.

If you use Template A (i.e., there are issues to fix) and at least one issue requires code changes, append a brief follow-up question after the structured output asking whether the user wants you to apply the suggested fix(es). For example: "Would you like me to use the Suggested fix section to address these issues?"

### Template B (no issues)
```
## Code review
No issues found.
```
