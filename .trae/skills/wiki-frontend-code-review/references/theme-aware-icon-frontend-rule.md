# 主题感知图标（FR-075）

> 复盘来源：归档按钮迁移新增 SVG 图标时，硬编码 `fill`/`stroke` 为固定色、尺寸非 24x24、风格与现有线条图标不一致，导致主题切换下图标不可见（深色主题白图标 / 浅色主题浅图标）。本规则要求 SVG 图标颜色用 `currentColor`、尺寸遵循 24x24、风格与现有线条图标一致。对应 wiki-code-dev theme-aware-icon-rule.md（TAI）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"theme_aware_icon"章节读取，禁止在本规则文件硬编码颜色值 / 尺寸。

## Trigger Keywords
<svg, currentColor, fill=, stroke=, 24x24, viewBox, 线条图标, icon, rgba(255,255,255, stroke-width, 主题切换, 新增图标

## Rules

### FR-075-1: SVG 图标颜色须用 currentColor（禁硬编码固定色）

- **Severity**: critical
- **Description**: 图标 SVG 的 `fill`/`stroke` 必须使用 `theme_aware_icon.color_attribute`（默认 `currentColor`），禁止硬编码 `theme_aware_icon.forbidden_color_values`（默认 `#hex,rgb(),rgba(),hsl()` 之外的纯固定色），否则主题切换时图标不可见。`theme_aware_icon.whitelist_pure_white` 默认 true —— 纯白高光 `rgba(255,255,255,X)` 允许硬编码（用于阴影/高光，不随主题反相）。
- **Suggested fix**:
```html
<!-- 错误：硬编码固定色，主题切换下不可见 -->
<svg fill="#333333" stroke="#333333">...</svg>
<!-- 正确：currentColor 跟随主题 -->
<svg fill="currentColor" stroke="currentColor">...</svg>
```

### FR-075-2: 图标尺寸与风格须与现有线条图标一致

- **Severity**: suggestion
- **Description**: 新增图标 viewBox 须为 `0 0 theme_aware_icon.size theme_aware_icon.size`（默认 24x24），`stroke-width` 默认 `theme_aware_icon.stroke_width_default`（1.8），风格（线性 / 线条）与项目现有图标库一致，避免混入实心/异尺寸图标破坏视觉统一。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `theme_aware_icon.enabled` | `true` | 是否启用本规则 |
| `theme_aware_icon.color_attribute` | `currentColor` | SVG 须使用的颜色属性值（禁硬编码 #hex/rgb/rgba/hsl） |
| `theme_aware_icon.forbidden_color_values` | `#hex,rgb(),rgba(),hsl()` | 禁止硬编码的颜色值格式 |
| `theme_aware_icon.size` | `24` | 图标尺寸（SVG viewBox `0 0 24 24`） |
| `theme_aware_icon.stroke_width_default` | `1.8` | stroke 默认宽度（与现有线条图标一致） |
| `theme_aware_icon.whitelist_pure_white` | `true` | 纯白高光 rgba(255,255,255,X) 允许硬编码 |
| `theme_aware_icon.severity_color` | `critical` | 硬编码固定色导致主题切换不可见违规级别 |
| `theme_aware_icon.severity_style` | `suggestion` | 尺寸/风格与现有图标不一致违规级别 |

## 检查方式

1. Grep 检索 `<svg` / `fill=` / `stroke=` / `viewBox`。
2. 若图标 `fill`/`stroke` 命中 `forbidden_color_values`（且非纯白高光白名单）→ FR-075-1 违规。
3. 若 viewBox 非 `0 0 24 24` 或 stroke-width 偏离默认 → FR-075-2 建议级提示。

## 适配新项目

- **Font Awesome 等字体图标**：本规则不适用（图标颜色由 font color 控制，天然随主题）。
- **不同默认尺寸规范**：调整 `theme_aware_icon.size` 与 `stroke_width_default` 匹配项目图标库。
