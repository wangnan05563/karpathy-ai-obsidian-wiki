# 主题系统与 CSS 变量规范

本文档记录 Karpathy Wiki 项目的多主题系统架构、CSS 变量分层设计与硬编码色值禁令。

## CSS 变量分层架构

项目采用三层 CSS 变量体系，每层在各主题文件中独立覆盖：

| 层级 | 变量前缀 | 用途 | 示例 |
|------|----------|------|------|
| L1 基础调色板 | `--neon-*` / `--bg-*` / `--text-*` | 主题基础色彩、背景、文字 | `--neon-purple`, `--bg-void`, `--text-bright` |
| L2 子系统变量 | `--robot-*` / `--graph-*` | IP 形象、图谱节点等子系统专属色 | `--robot-accent`, `--graph-entities` |
| L3 场景变量 | `--bg-scene` / `--accent-*-aXX` | 容器深度背景、半透明强调色 | `--bg-scene`, `--accent-purple-a15` |

### 各层职责

- **L1 基础调色板**：定义主题的"底色"，所有其他变量从此层派生
- **L2 子系统变量**：为独立视觉子系统（机器人 IP、知识图谱）定义专属色，避免与通用色耦合
- **L3 场景变量**：为代码块、树容器、统计卡片等"场景区域"定义深度背景，以及半透明强调色变体

## 主题切换核心模式

```
data-theme 属性 → CSS 变量覆盖 → localStorage 持久化
```

- `document.documentElement.setAttribute('data-theme', themeName)` 切换主题
- 每个 `[data-theme="xxx"]` 选择器块内覆盖全部 L1/L2/L3 变量
- `localStorage.setItem('theme', themeName)` 持久化用户选择
- 主题文件通过 `@import` 在 `styles/themes/index.css` 中集中导入

## 硬编码色值禁令

**所有跨主题可见的颜色必须通过 CSS 变量引用，禁止硬编码。**

### 禁止模式

```css
/* 错误：硬编码 creative 主题的深色背景 */
background: rgba(5, 0, 16, 0.5);
border: 1px solid rgba(176, 38, 255, 0.2);
```

### 正确模式

```css
/* 正确：使用场景变量，随主题切换 */
background: var(--bg-scene);
border: 1px solid var(--accent-purple-a20);
```

### 例外白名单

以下颜色不随主题变化，允许硬编码：
- `rgba(255, 255, 255, X)` 纯白高光（所有主题通用）
- `transparent` 透明值
- `inherit` / `currentColor` 继承值

## Alpha 变体命名规范

半透明色变体统一用 `a` + 两位数字后缀：

| 透明度 | 变量后缀 | 示例 |
|--------|----------|------|
| 0.03 | `a03` | `--accent-purple-a03` |
| 0.05 | `a05` | `--accent-cyan-a05` |
| 0.08 | `a08` | `--accent-pink-a08` |
| 0.10 | `a10` | `--accent-purple-a10` |
| 0.12 | `a12` | `--accent-cyan-a12` |
| 0.15 | `a15` | `--accent-pink-a15` |
| 0.18 | `a18` | `--accent-magenta-a18` |
| 0.20 | `a20` | `--accent-purple-a20` |
| 0.25 | `a25` | `--accent-cyan-a25` |
| 0.30 | `a30` | `--accent-pink-a30` |
| 0.35 | `a35` | `--accent-purple-a35` |
| 0.40 | `a40` | `--accent-cyan-a40` |
| 0.45 | `a45` | `--accent-pink-a45` |
| 0.50 | `a50` | `--accent-magenta-a50` |
| 0.60 | `a60` | `--accent-purple-a60` |
| 0.70 | `a70` | `--accent-cyan-a70` |

禁止使用 `05`（无前缀 `a`）或 `0.5`（带小数点）等不一致命名。

## JS 驱动颜色适配

vis-network、Canvas 等 JS 驱动图形无法直接使用 CSS `var()`，须用 `getComputedStyle` 读取：

```typescript
function getThemeVar(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim() || '#b026ff'; // fallback
}

function getDirColors(): Record<string, string> {
  return {
    entities: getThemeVar('--graph-entities'),
    concepts: getThemeVar('--graph-concepts'),
    comparisons: getThemeVar('--graph-comparisons'),
    queries: getThemeVar('--graph-queries'),
  };
}
```

**注意**：`getComputedStyle` 在主题切换后需重新调用以获取新值，不能缓存。

## rgba() 语法陷阱

### 无效语法

```css
/* 错误：rgba() 不接受 hex 参数 */
--accent-purple-a05: rgba(#b026ff, 0.05);
```

### 正确语法

```css
/* 正确：必须先转换为 r, g, b 数值 */
--accent-purple-a05: rgba(176, 38, 255, 0.05);
```

### 转换函数（Node.js 批量生成时使用）

```javascript
function hexToRgb(hex) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!m) throw new Error('Invalid hex: ' + hex);
  return `${parseInt(m[1], 16)}, ${parseInt(m[2], 16)}, ${parseInt(m[3], 16)}`;
}
function rgba(hex, a) {
  return `rgba(${hexToRgb(hex)}, ${a})`;
}
```

## 主题文件结构

```
packages/web/src/styles/themes/
├── index.css          # @import 入口
├── macaron.css        # 马卡龙主题（浅粉浅青）
├── enterprise.css     # 现代企业主题（科技蓝灰）
├── product.css        # 产品展示主题（暗黑霓虹）
├── ecommerce.css      # 电商零售主题（明亮扁平）
└── portfolio.css      # 艺术作品集主题（米色金黑）
```

creative 主题变量定义在 `packages/web/src/style.css` 的 `:root` 中（作为默认主题）。

## 故障排查 Checklist

当"颜色没随主题变化"时按顺序检查：

1. `Grep` 搜索 `rgba(\d+, \d+, \d+` 确认是否有硬编码色值残留
2. 检查对应 CSS 变量是否在所有 6 个主题文件中都有定义
3. 检查 alpha 变体命名是否一致（`aXX` 格式）
4. JS 驱动颜色是否用了 `getComputedStyle` 而非硬编码字符串
5. 主题切换后 `getComputedStyle` 是否重新调用（不能缓存旧值）
6. 检查 `[data-theme="xxx"]` 选择器是否正确覆盖了所有变量
7. Playwright 截图验证至少 3 个主题（浅色/深色/中间色）切换正常
