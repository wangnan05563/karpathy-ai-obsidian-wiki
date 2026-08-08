# 成对操作按钮样式一致性（确认 / 取消幽灵按钮）

**代码**：CODING-BUTTON-STYLE-CONSISTENCY
**严重级别**：minor

## 问题（Problem）

同一操作组内的「确认 / 取消」按钮若基础样式不一致（如确认高亮、取消朴素，或颜色 / 描边 / 圆角各异），会传递错误的信息层级，让用户难以判断哪一个是主操作，甚至误点。此类样式漂移通常在功能测试（只验证点击行为）中漏掉，却是真实 UI 质量与可访问性的高频缺陷。

> 真实代码佐证（`frontend/src/views/Query.vue` `.edit-btn.confirm` / `.edit-btn.cancel`）：修复前确认与取消按钮颜色不协调，修复后二者统一为幽灵按钮（透明背景 + 柔和文字 + 淡青描边），仅 hover 时高亮青色；`.edit-btn` 基类统一 `padding/border-radius/font-size`，`confirm` 与 `cancel` 仅继承基类，差异仅在于 hover 强调。

## 规则（Rule）

### R-1：同一操作组的成对按钮须共享一致基础样式

确认 / 取消（或同组任意成对操作按钮）必须共享同一基础样式（背景、文字色、描边、圆角、字号、内边距）。区分仅通过 hover / active 的强调（如高亮描边色），**不**通过基础配色差异。

```css
.edit-btn { padding: 5px 14px; border-radius: 8px; border: 1px solid transparent; font-size: 13px; }
.edit-btn.confirm { background: transparent; color: var(--text-soft); border-color: var(--accent-cyan-a20); }
.edit-btn.cancel  { background: transparent; color: var(--text-soft); border-color: var(--accent-cyan-a20); }
.edit-btn.confirm:hover, .edit-btn.cancel:hover { color: var(--neon-cyan); border-color: var(--neon-cyan); }
```

### R-2：使用主题感知 CSS 变量，禁止硬编码颜色

按钮配色须引用主题变量（`var(--text-soft)` / `var(--neon-cyan)` / `var(--accent-cyan-a20)` 等），禁止硬编码具体色值，确保随主题切换保持一致观感（与 CODING 主题色映射规范对齐）。

### R-3：`type="primary"` 仅留给唯一真正主操作

成对按钮（确认 + 取消）不应同时用 `type="primary"` 强调；真正的主操作才标记 primary，取消 / 次级动作保持次级视觉权重，避免双主操作误导。

## 适用 / 不适用

- **适用**：弹窗 / 内联编辑 / 表单等存在「确认 + 取消」或任意成对操作按钮的场景；需传递明确主次之分的 UI。
- **不适用**：分处不同上下文、彼此无关的独立按钮；天然需要不同视觉权重的导航与工具按钮（如主 CTA 与危险操作）。

## 检查清单

- [ ] 同组确认 / 取消按钮是否共享一致基础样式（背景 / 文字 / 描边 / 圆角 / 字号）（`button_style.shared_base`）
- [ ] 差异是否仅体现在 hover / active 强调，而非基础配色（`button_style.diff_via_hover`）
- [ ] 配色是否使用主题变量、无硬编码色值（`button_style.theme_vars`）
- [ ] 是否避免确认 / 取消同时 `type="primary"`（`button_style.single_primary`）
