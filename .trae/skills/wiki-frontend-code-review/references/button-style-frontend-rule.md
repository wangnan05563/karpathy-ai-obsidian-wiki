# Rule Catalog — Paired Action Button Style Consistency (Frontend)

前端「成对操作按钮样式一致性」审查规则：同一操作组（如弹窗/内联编辑的「确认 / 取消」）按钮必须共享一致基础样式，差异仅经 hover/active 强调；配色须用主题变量、禁止硬编码；`type="primary"` 仅留给唯一真正主操作。所有参数从 `config/review-config.md` 读取，禁止硬编码。

> 复盘来源：编辑重发场景的 confirm / cancel 按钮早期基础样式不一致（确认高亮、取消朴素），传递错误信息层级、易误点。`Query.vue` `.edit-btn.confirm` / `.edit-btn.cancel` 修复后统一为幽灵按钮（透明背景 + 柔和文字 + 淡青描边），仅 hover 高亮青色；`.edit-btn` 基类统一 padding/border-radius/font-size，confirm 与 cancel 仅继承基类。

## Scope
- Covers: `frontend/src/views/**/*.vue` / `frontend/src/components/**/*.vue`（成对操作按钮，如 `.edit-btn.confirm` / `.edit-btn.cancel`、模态框确认/取消、`el-button` 组）、关联 `<style>` 块。
- Does NOT cover：分处不同上下文、彼此无关的独立按钮；天然需不同视觉权重的导航与工具按钮（主 CTA 与危险操作）。

## Rules

### FR-079-1: 同组确认/取消按钮共享一致基础样式

IsUrgent: False
Category: Button Style

#### Description

确认 / 取消（或同组任意成对操作按钮）必须共享同一基础样式（背景、文字色、描边、圆角、字号、内边距）。区分仅通过 hover / active 的强调（如高亮描边色），**不**通过基础配色差异（FR-079-1，建议级）。

### FR-079-2: 配色使用主题变量、禁止硬编码

IsUrgent: False
Category: Button Style

#### Description

按钮配色须引用主题变量（`var(--text-soft)` / `var(--neon-cyan)` / `var(--accent-cyan-a20)` 等），禁止硬编码具体色值，确保随主题切换保持一致观感（与主题色映射规范对齐，FR-079-2，建议级）。

### FR-079-3: type="primary" 仅留给唯一主操作

IsUrgent: False
Category: Button Style

#### Description

成对按钮（确认 + 取消）不应同时用 `type="primary"` 强调；真正的主操作才标记 primary，取消 / 次级动作保持次级视觉权重，避免双主操作误导（FR-079-3，建议级）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `button_style_frontend.enabled` | `true` | 启用本组规则（FR-079） |
| `button_style_frontend.severity_shared_base` | `minor` | FR-079-1 同组按钮基础样式不一致的违规级别 |
| `button_style_frontend.severity_theme_vars` | `minor` | FR-079-2 硬编码色值、未用主题变量的违规级别 |
| `button_style_frontend.severity_single_primary` | `minor` | FR-079-3 确认/取消同时 type=primary 的违规级别 |
| `button_style_frontend.paired_selectors` | `.edit-btn.confirm,.edit-btn.cancel` | 待核对的成对按钮选择器（配置化） |
| `button_style_frontend.theme_var_pattern` | `var\(--` | 配色须匹配的主题变量前缀 |
