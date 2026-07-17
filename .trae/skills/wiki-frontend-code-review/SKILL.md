---
name:。 wiki-frontend-code-review
description: "Review Vue 3 + Element Plus + Pinia frontend code for the wiki project. Invoke when user asks to review, analyze, or improve frontend files (e.g., .vue, .ts) under packages/web/. Covers Vue Composition API, Element Plus, Pinia, performance, and type safety."
---

# Wiki Frontend Code Review

## Intent
Use this skill whenever the user asks to review, analyze, or improve frontend code of the wiki project (especially `.vue` / `.ts` / `.tsx` files under `packages/web/`). Support two review modes:

1. **Pending-change review** – inspect staged/working-tree files slated for commit and flag checklist violations before submission.
2. **File-targeted review** – review the specific file(s) the user names and report the relevant checklist findings.

Scope and non-goals (backend code, build scripts, config files) are defined in [config/review-config.md](config/review-config.md) under "适用 / 不适用场景". When in doubt about whether a file is in scope, consult that section first.
## Context Loading Strategy

Follow the loading sequence in [skill-loader.md](skill-loader.md) to minimize context tokens.

### 1. Baseline (always load)
- [SKILL.md](SKILL.md) — this file
- [config/review-config.md](config/review-config.md) — project thresholds, tech stack, conventions

### 2. Rule routing (load selectively)
Read [skill-loader.md](skill-loader.md) once (~3KB) to determine which rule files apply:
1. Match target file extension against `file_patterns[].pattern`
2. Scan the first 50 lines for category keywords (see skill-loader.md)
3. Load only matched rule files from `rule_categories[].file`
4. Load corresponding examples files only when generating fix code

### 3. On-demand examples
Only load `references/examples/{category}-examples.md` when:
- Generating specific code fixes
- The rule description needs Wrong/Right comparison

This selective loading typically reduces context from ~13k to ~6-8k tokens per review.



Stick to the checklist below for every applicable file and mode. Do not invent rules outside the catalog.

## Checklist

Use [skill-loader.md](checklist-index.md) for the complete rule overview and quick routing table.

### Loading Procedure
1. Read [skill-loader.md](checklist-index.md) once to understand all rules and their dependencies
2. Match target files against the quick routing table to select applicable rules
3. Load [config/review-config.md](config/review-config.md) for thresholds and conventions
4. Load matched rule files from the checklist
5. Load examples files only when generating specific fix code

All configurable parameters (directory mapping, tech stack, performance thresholds, SSE event types) live in [config/review-config.md](config/review-config.md). Rule files describe general patterns only and reference the config for concrete values — never hardcode thresholds in rule files.

Flag each rule violation with urgency metadata so future reviewers can prioritize fixes.

## Review Process

### Mode Detection
First, determine the review mode from the user request:

- **pending-change review**: User mentions staged/working-tree files, git diff, or commit prep. Use diff-aware mode.
- **file-targeted review**: User names specific files. Use full-file mode.
- **auto-detect**: If unclear, check `git status` / `git diff --cached` to see if there are pending changes.

### Diff-Aware Mode (for pending changes)

When reviewing staged or working-tree files:

1. **Get diff first**: Run `git diff --cached` (staged) or `git diff` (working tree) to identify changed files and lines.
2. **Extract context**: For each changed file, read only the diff hunks + 5 lines of surrounding context. Do NOT read the entire file.
3. **Route rules**: Use the quick routing table in [skill-loader.md](skill-loader.md) to determine which rule files apply to the changed areas.
4. **Targeted review**: Apply rules only to changed lines and their immediate context. Mark unchanged code as "verified, skip."
5. **Track cumulative issues**: If reviewing the same file across multiple commits, note pre-existing issues separately.

### Full-File Mode (for file-targeted or auto-detect with no diff)

1. **定位文件**：定位待评审的 `.vue` / `.ts` / `.tsx` 文件，按 `config/review-config.md` 的目录映射确认其在 `packages/web/` 范围内；不在范围内则跳过并说明原因。
2. **读取配置**：打开 [config/review-config.md](config/review-config.md) 获取当前的技术栈版本、性能阈值、SSE 事件类型约定、组件设计规范、主题色系统配置。
3. **路由规则**：根据文件路径与内容特征，匹配上表中的规则文件；一个文件可能命中多个规则文件，均需逐条核对。
4. **判断偏离**：对每条规则，记录代码偏离的具体位置（文件路径 + 行号）与一段代表性代码片段。需要参考示例时，加载规则文件中链接的 examples 文件。
5. **组装输出**：按下方 Required output 输出。先按 **Urgent** 分组（urgent 在前），再按类别顺序排序（Vue Composition -> Element Plus -> Pinia Store -> Performance -> Type Safety -> Theming）。无任何偏离时使用 Template B。

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

### Template B。 (no issues)
```
## Code review
No issues found.
```





