# Rule Catalog — 主题色变量映射（前端审查视角）

> 本规则文件基于「仪表盘最近操作面板与悬浮问答图标主题色适配」复盘提炼，
> 对应编码规范 CODING-041~046（见 wiki-code-dev/references/theme-color-mapping-rule.md）。
> 所有参数从 [config/review-config.md](../config/review-config.md) 的"主题色变量映射审查参数（theme_color_mapping_frontend）"节读取，
> 规则文件不硬编码任何具体颜色值、alpha 列表或主题名。

## Scope

- Covers: 硬编码颜色检测、alpha 变体命名、语义变量选择、编辑工具使用、类型检查门禁、多主题视觉一致性
- 适用对象：所有 `.vue` / `.css` / `.scss` / `.ts` 文件中涉及颜色值的修改
- Does NOT cover: 通用主题系统规则（见 [theming-rule.md](theming-rule.md)）、JS 驱动颜色（见 theming-rule.md 的 getComputedStyle 规则）

## Rules

### FR-035 主题色变量映射合规性

- Category: theme-color-mapping
- Severity: urgent
- Description: 所有跨主题可见的颜色（背景、边框、文字、阴影、渐变）必须通过 CSS 变量引用，禁止硬编码 `rgba()` / `rgb()` / `#hex` / `hsl()` / `hsla()`。硬编码色值在切换主题后不会变化，导致浅色主题下出现深色背景块、文字不可读等问题。允许硬编码的白名单参见 `theme_color_mapping_frontend.whitelist_patterns`。
- Check: 扫描 `theme_color_mapping_frontend.forbidden_color_formats` 列出的颜色格式，命中后检查是否匹配 `whitelist_patterns`；未匹配的必须替换为 CSS 变量。
- Suggested fix: 按「读变量清单 → 设计映射表 → 精准替换」三步法执行，禁止跳过清单直接猜测变量名。

### FR-036 alpha 变体命名合规性

- Category: theme-color-mapping
- Severity: urgent
- Description: 新增的 `--accent-{color}-a{NN}` 变量引用，`{NN}` 必须 ∈ `theme_color_mapping_frontend.allowed_alpha_values` 列表，`{color}` 必须 ∈ `color_identifiers` 列表。使用未定义的 alpha 值（如 `a07`）或未注册的颜色标识会导致变量不存在，回退到默认值或 `unset`。
- Check: 对所有新增的 alpha 变体引用，核对 `{NN}` 是否在允许列表中，变量名格式是否匹配 `alpha_variable_pattern` 模板。
- Suggested fix: 从 `allowed_alpha_values` 列表选取最接近的 alpha 值，或在主题文件中先定义新变体再引用。

### FR-037 语义变量选择正确性

- Category: theme-color-mapping
- Severity: urgent
- Description: CSS 变量选择必须按 `theme_color_mapping_frontend.semantic_priority` 顺序匹配语义用途：页面背景须用 `--bg-scene`、卡片/面板背景须用 `--bg-card-solid`、文字须用 `--text-base`/`--text-muted`、边框须用 `--accent-{color}-a15`、阴影/光晕须用 `--glow-{color}`、滚动条须用 `--accent-{color}-a20`/`a40`。跨语义层选择变量会导致对比度不足或视觉层次混乱。
- Check: 对所有新增的 CSS 变量引用，按语义优先级顺序验证用途是否匹配。
- Suggested fix: 重新审视元素的语义角色（背景/文字/边框/阴影），选择对应语义层的变量。

### FR-038 编辑工具使用合规性

- Category: theme-color-mapping
- Severity: suggestion
- Description: 含非 ASCII 字符的 `.vue` / `.ts` 文件被 Write 重写而非 Edit 精准替换时，可能导致中文注释被破坏为 GBK 字节（Write 工具可能以默认编码回写）。修改范围 < `edit_threshold_ratio`（默认 0.5）时应用单次 Edit，> 0.5 时分多次 Edit。
- Check: 若评审范围为 pending-change 模式，检查 `git diff` 中单个文件修改行数占比；若占比超阈值且文件含非 ASCII 字符，标记为「疑似使用 Write 重写」。
- Suggested fix: 改用 Edit 分块精准替换，保持原文件编码。

### FR-039 类型检查通过性

- Category: theme-color-mapping
- Severity: urgent
- Description: 代码修改涉及类型变更时必须执行后端 `tsc --noEmit` + 前端 `vue-tsc --noEmit` 双重门禁，退出码均为 0 才允许提交。仅运行前端 vue-tsc 会漏掉 API 契约不匹配的问题。
- Check: 若评审范围涉及 `.ts` / `.vue` 文件类型变更，要求 PR 中包含 `backend_typecheck_command` 与 `frontend_typecheck_command` 的双重通过截图或 CI 日志；`require_both_pass` 为 true 时缺失任一即标记 Urgent。
- Suggested fix: 在本地依次执行后端和前端类型检查命令，确认均无错误后再提交。

### FR-040 多主题视觉一致性

- Category: theme-color-mapping
- Severity: suggestion
- Description: 涉及 CSS 变量引用或主题色适配的修改，必须在 `theme_color_mapping_frontend.test_themes` 列出的所有主题下验证视觉效果。浅色主题（`light_themes`）和深色主题（`dark_themes`）的对比度需求不同，仅在单一主题下验证会遗漏对比度不足的问题。
- Check: 要求 PR 描述中包含所有 `test_themes` 列出的主题切换截图；缺失任一主题截图标记为 Suggestion；截图须能证明元素在对应主题下对比度可读。
- Suggested fix: 依次切换到每个主题，截图验证元素的背景色、文字色、边框色在对应主题下均可读。
