# Rule Catalog — Theming

主题系统审查规则：确保 UI 元素使用 CSS 变量适配主题切换，禁止硬编码色值。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

## 禁止硬编码主题色值，必须用 CSS 变量

IsUrgent: True
Category: Theming

### Description

所有跨主题可见的颜色（背景、边框、文字、阴影、渐变）必须通过 CSS 变量引用，禁止硬编码 `rgba(R, G, B, A)` 或 `#hex`。硬编码色值在切换主题后不会变化，导致浅色主题下出现深色背景块、文字不可读等问题。

允许硬编码的白名单（不随主题变化的颜色）参见 `config/review-config.md` 的"主题色白名单"。

### Suggested Fix

将硬编码色值替换为对应的 CSS 变量。场景背景用 `var(--bg-scene)`，半透明强调色用 `var(--accent-{color}-a{XX})`。

> **示例代码**: 参见 [examples/theming-rule-examples.md](examples/theming-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## JS 驱动颜色须用 getComputedStyle 读取 CSS 变量

IsUrgent: True
Category: Theming

### Description

vis-network、Canvas 等 JS 驱动图形无法直接使用 CSS `var()` 语法，必须通过 `getComputedStyle(document.documentElement).getPropertyValue('--var-name')` 读取 CSS 变量值。直接在 JS 中硬编码颜色字符串（如 `'#b026ff'`）不会随主题切换变化。

### Suggested Fix

封装 `getThemeVar(name)` 工具函数，所有 JS 驱动颜色通过该函数读取 CSS 变量。主题切换后须重新调用（不能缓存）。

> **示例代码**: 参见 [examples/theming-rule-examples.md](examples/theming-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## alpha 变体命名须统一 aXX 格式

IsUrgent: False
Category: Theming

### Description

CSS 变量中的半透明色变体命名必须统一使用 `a` + 两位数字后缀（如 `a05`、`a10`、`a15`、`a20`）。禁止使用 `05`（无前缀）、`0.5`（带小数点）、`5`（单位数）等不一致命名。命名不一致会导致代码中引用变量名拼写错误，且增加维护成本。

### Suggested Fix

检查所有 `--accent-*-aXX` 变量命名，统一为 `a` + 两位数字格式。

> **示例代码**: 参见 [examples/theming-rule-examples.md](examples/theming-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## SVG fill/stroke/stop-color 须用 var() 引用 CSS 变量

IsUrgent: True
Category: Theming

### Description

SVG 元素的 `fill`、`stroke`、`stop-color` 属性可以直接使用 CSS `var()` 引用 CSS 变量。硬编码 SVG 色值（如 `fill="#b026ff"`）不会随主题切换变化，导致 IP 形象/图标在非默认主题下颜色不协调。

### Suggested Fix

将 SVG 硬编码色值替换为 `var(--xxx)` 引用。

> **示例代码**: 参见 [examples/theming-rule-examples.md](examples/theming-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 主题文件须覆盖全部 L1/L2/L3 变量

IsUrgent: False
Category: Theming

### Description

每个 `[data-theme="xxx"]` 选择器块必须覆盖全部三层 CSS 变量：L1 基础调色板（`--neon-*`/`--bg-*`/`--text-*`）、L2 子系统变量（`--robot-*`/`--graph-*`）、L3 场景变量（`--bg-scene`/`--accent-*-aXX`）。遗漏任何一层会导致该主题下部分区域不随主题变化。

### Suggested Fix

新增主题时，从已有主题文件复制全部变量定义，逐个替换为基础色值。使用 diff 工具确认新主题文件与基准主题文件变量数量一致。

> **示例代码**: 参见 [examples/theming-rule-examples.md](examples/theming-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。
