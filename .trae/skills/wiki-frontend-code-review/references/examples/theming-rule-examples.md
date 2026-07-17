# theming-rule - Code Examples

> This file contains Wrong/Right code examples extracted from [theming-rule.md](../theming-rule.md).
> Load on demand when you need to reference examples or generate fix code.

---

## 禁止硬编码主题色值，必须用 CSS 变量

### Wrong

```ts
.scene-container {
  background: rgba(5, 0, 16, 0.5);
  border: 1px solid rgba(176, 38, 255, 0.2);
}
```

### Right

```ts
.scene-container {
  background: var(--bg-scene);
  border: 1px solid var(--accent-purple-a20);
}
```

---

## JS 驱动颜色须用 getComputedStyle 读取 CSS 变量

### Wrong

```ts
const dirColors = {
  entities: '#ff006e',
  concepts: '#b026ff',
  comparisons: '#00f5ff',
  queries: '#ff3ec9',
}
```

### Right

```ts
function getThemeVar(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name).trim() || '#b026ff'
}
function getDirColors(): Record<string, string> {
  return {
    entities: getThemeVar('--graph-entities'),
    concepts: getThemeVar('--graph-concepts'),
    comparisons: getThemeVar('--graph-comparisons'),
    queries: getThemeVar('--graph-queries'),
  }
}
```

---

## alpha 变体命名须统一 aXX 格式

### Wrong

```ts
--accent-purple-05: rgba(176, 38, 255, 0.05);    /* 缺 a 前缀 */
--accent-purple-0.5: rgba(176, 38, 255, 0.5);    /* 带小数点 */
--accent-purple-5: rgba(176, 38, 255, 0.5);      /* 单位数 */
```

### Right

```ts
--accent-purple-a05: rgba(176, 38, 255, 0.05);
--accent-purple-a50: rgba(176, 38, 255, 0.5);
```

---

## SVG fill/stroke/stop-color 须用 var() 引用 CSS 变量

### Wrong

```ts
<stop offset="0%" stop-color="#1a0533" />
<circle cx="50" cy="40" r="8" fill="#00f5ff" />
```

### Right

```ts
<stop offset="0%" stop-color="var(--robot-head-1)" />
<circle cx="50" cy="40" r="8" fill="var(--robot-eye)" />
```

---

## 主题文件须覆盖全部 L1/L2/L3 变量

### Wrong

```ts
[data-theme="new-theme"] {
  /* 只覆盖了 L1 基础色，遗漏 L2 robot/graph 和 L3 scene 变量 */
  --neon-purple: #custom;
  --bg-void: #custom;
}
```

### Right

```ts
[data-theme="new-theme"] {
  /* L1 基础调色板 */
  --neon-purple: #custom;
  --bg-void: #custom;
  /* ... 全部 L1 变量 ... */

  /* L2 子系统变量 */
  --robot-head-1: #custom;
  --graph-entities: #custom;
  /* ... 全部 L2 变量 ... */

  /* L3 场景变量 */
  --bg-scene: #custom;
  --accent-purple-a05: rgba(..., 0.05);
  /* ... 全部 L3 变量 ... */
}
```

---

*End of examples*