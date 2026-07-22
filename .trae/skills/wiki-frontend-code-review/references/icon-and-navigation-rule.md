# 图标与导航栏审查规则

> 基于菜单图标设计与折叠/展开双模式改造复盘提炼，防止图标不跟随主题、导航栏菜单过多导致布局拥挤、tooltip 依赖 JS 库等问题。

## 触发场景

- 评审涉及 `.vue` 文件中的 `<svg>` 矢量图标组件
- 评审涉及导航栏菜单项数量 >7 的 `App.vue` 或布局组件
- 评审涉及折叠/展开切换、tooltip、Vue Transition 的代码

## 规则

### IN-1：SVG 图标必须用 currentColor 跟随主题

矢量图标的 `stroke` / `fill` 属性必须设为 `currentColor`，通过 CSS `color` 属性自动跟随主题变色。

**违规示例**：
```html
<svg stroke="#ff00ff" />
<svg fill="rgba(255, 0, 255, 0.8)" />
```

**合规示例**：
```html
<svg stroke="currentColor" />
```

### IN-2：图标尺寸必须通过 props 传入

图标组件的 `width` / `height` 必须通过 props 传入，禁止在 SVG 内硬编码尺寸，确保不同使用场景下尺寸可调。

**违规示例**：
```html
<svg width="20" height="20" />  <!-- 硬编码尺寸 -->
```

**合规示例**：
```html
<svg :width="size || 20" :height="size || 20" />
```

### IN-3：菜单项超过阈值时必须实现折叠/展开双模式

当导航栏菜单项数量超过 `icon_navigation.nav_threshold`（默认 7）时，必须实现双模式：
- **展开模式**：图标 + 文字水平排列
- **折叠模式**：一行纯图标，鼠标悬浮显示菜单名 tooltip

### IN-4：折叠模式的 tooltip 必须用纯 CSS hover

tooltip 实现必须用纯 CSS `:hover` + `opacity` 过渡，禁用 JS tooltip 库（如 tippy.js、popper.js），减少依赖、提升性能。

**违规示例**：
```typescript
import tippy from 'tippy.js';
tippy(button, { content: '菜单名' });
```

**合规示例**：
```css
.icon-tooltip {
  opacity: 0;
  transition: opacity 0.2s ease;
}
.icon-btn:hover .icon-tooltip {
  opacity: 1;
}
```

### IN-5：折叠/展开切换必须用 Vue Transition mode="out-in"

切换必须用 `<Transition name="..." mode="out-in">`，确保旧模式完全移除后再渲染新模式，避免布局抖动与过渡冲突。

### IN-6：折叠状态必须持久化到 localStorage

折叠/展开状态必须持久化到 `localStorage`（key 名见 `icon_navigation.state_persistence_key`），刷新页面后保持上次状态。

**违规示例**：
```typescript
const navCollapsed = ref(false);  // 未持久化，刷新后丢失
```

**合规示例**：
```typescript
const navCollapsed = ref(localStorage.getItem('navCollapsed') === 'true');
function toggleNav() {
  navCollapsed.value = !navCollapsed.value;
  localStorage.setItem('navCollapsed', String(navCollapsed.value));
}
```

### IN-7：菜单项必须抽为单一数据源

菜单项列表（key + icon + label）必须抽为单一常量数组，展开模式与折叠模式共用，避免两处硬编码导致不一致。

**违规示例**：
```html
<!-- 展开模式 -->
<button v-for="tab in [{key:'dashboard',label:'仪表盘'},...]">...</button>
<!-- 折叠模式 -->
<button v-for="tab in [{key:'dashboard',label:'仪表盘'},...]">...</button>
```

**合规示例**：
```typescript
const menuItems = [
  { key: 'dashboard' as ViewName, icon: 'dashboard', label: '仪表盘' },
  // ...
];
```
```html
<!-- 展开模式 -->
<button v-for="tab in menuItems">...</button>
<!-- 折叠模式 -->
<button v-for="tab in menuItems">...</button>
```

## 检测方法

1. 扫描 `.vue` 文件中的 `<svg>` 标签，检查 `stroke` / `fill` 是否为 `currentColor`
2. 扫描 `<svg>` 的 `width` / `height` 是否为字面量数字（非 props 绑定）
3. 统计导航栏菜单项数量，若 > `nav_threshold` 检查是否实现双模式
4. 扫描折叠模式的 tooltip，验证是否用纯 CSS `:hover` 实现
5. 检查切换逻辑是否用 `<Transition mode="out-in">`
6. 检查 `localStorage.getItem` / `localStorage.setItem` 持久化逻辑
7. 验证展开模式与折叠模式是否共用同一 `menuItems` 数组

## 配置参数

所有参数见 [config/review-config.md](../config/review-config.md) 的"图标与导航栏审查参数"段。

## 适配说明

- 移动端优先项目：`nav_threshold` 改为 `5`，`tooltip_implementation` 改为 `js-tooltip`（移动端无 hover）
- vue-router 项目：`enabled` 设为 `false`，由路由库管理导航
- 菜单项固定较少（≤7）的项目：`enabled` 设为 `false`
- Font Awesome 等字体图标：IN-1 / IN-2 不适用
