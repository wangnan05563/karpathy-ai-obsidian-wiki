# 主题感知图标设计规则

## 触发场景

- 设计菜单图标、导航图标、工具栏图标
- 项目支持多主题切换
- 使用 SVG 矢量图标而非位图

## 规则

### TAI-1：SVG 图标必须用 currentColor 跟随主题

矢量图标的 `stroke` / `fill` 属性必须设为 `currentColor`，通过 CSS `color` 属性自动跟随主题变色。

**禁止**：
```html
<svg stroke="#ff00ff" />  <!-- 硬编码色值，不跟随主题 -->
```

**推荐**：
```html
<svg stroke="currentColor" />  <!-- 自动跟随 CSS color -->
```

### TAI-2：stroke 线条风格必须统一

同一图标集必须统一使用 stroke 线条风或 fill 填充风，不可混用。推荐 stroke 线条风：
- `stroke-width: 1.8`（统一线宽）
- `stroke-linecap: round`（圆头线帽）
- `stroke-linejoin: round`（圆角连接）
- `fill: none`（不填充）

### TAI-3：禁止硬编码颜色值

SVG 内禁止出现 `#hex`、`rgb()`、`rgba()`、`hsl()` 等硬编码颜色值。所有颜色通过 CSS 变量或 `currentColor` 引用。

**例外**：纯白高光 `rgba(255, 255, 255, X)` 在所有主题中通用，可硬编码。

### TAI-4：必须用 drop-shadow 实现主题色光晕

图标光晕效果必须用 `filter: drop-shadow(0 0 {radius}px currentColor)`，不可用硬编码色值。

```css
.nav-icon {
  filter: drop-shadow(0 0 4px currentColor);
  transition: filter 0.3s ease;
}
.nav-icon:hover {
  filter: drop-shadow(0 0 8px currentColor);
}
```

### TAI-5：viewBox 必须用 24x24 标准网格

所有图标必须用 `viewBox="0 0 24 24"` 标准 24x24 网格，确保不同图标视觉大小一致。

## 检测方法

1. 扫描 `.vue` / `.svg` 文件中的 `<svg>` 标签
2. 检查 `stroke` / `fill` 属性是否为 `currentColor`
3. 若出现 `#hex` / `rgb()` / `rgba()` / `hsl()` 字面量，告警
4. 检查 `filter: drop-shadow` 是否用 `currentColor`

## 配置参数

所有参数见 [config/coding-standards-config.md](../config/coding-standards-config.md) 的"主题感知图标设计参数"段。

## 适配说明

- Material Design 图标：`stroke_style` 改为 `fill`，`stroke_width_default` 不适用
- 无主题项目：`color_attribute` 改为具体色值，`glow_filter` 设为空
- Font Awesome 等字体图标：本规则不适用
