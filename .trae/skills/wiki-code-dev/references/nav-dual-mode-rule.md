# 导航栏双模式设计规则

## 触发场景

- 导航栏菜单项较多（>7 个）
- 需要支持折叠/展开双模式切换
- 折叠模式下用纯图标 + tooltip 显示菜单名

## 规则

### NDM-1：菜单项超过阈值时必须实现双模式

当菜单项数量超过 `nav_threshold`（默认 7）时，必须实现折叠/展开双模式：
- **展开模式**：图标 + 文字水平排列
- **折叠模式**：一行纯图标，鼠标悬浮显示菜单名 tooltip

### NDM-2：折叠模式的 tooltip 必须用纯 CSS hover

tooltip 实现必须用纯 CSS `:hover` + `opacity` 过渡，禁用 JS tooltip 库（减少依赖、提升性能）。

```css
.icon-tooltip {
  position: absolute;
  bottom: -32px;
  left: 50%;
  transform: translateX(-50%) translateY(-4px);
  opacity: 0;
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.icon-btn:hover .icon-tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
```

### NDM-3：切换必须用 Vue Transition mode="out-in"

折叠/展开切换必须用 Vue `<Transition name="..." mode="out-in">`，确保旧模式完全移除后再渲染新模式，避免布局抖动。

### NDM-4：折叠状态必须持久化到 localStorage

折叠/展开状态必须持久化到 `localStorage`，刷新页面后保持上次状态。

```typescript
const navCollapsed = ref(localStorage.getItem('navCollapsed') === 'true');
function toggleNav() {
  navCollapsed.value = !navCollapsed.value;
  localStorage.setItem('navCollapsed', String(navCollapsed.value));
}
```

### NDM-5：菜单项必须抽为单一数据源

菜单项列表（key + icon + label）必须抽为单一常量数组，展开模式与折叠模式共用，避免两处硬编码导致不一致。

```typescript
const menuItems = [
  { key: 'dashboard' as ViewName, icon: 'dashboard', label: '仪表盘' },
  // ...
];
```

### NDM-6：禁用项的 tooltip 必须提示禁用原因

若菜单项有禁用状态（如"编译进度"在未编译时禁用），tooltip 必须同时显示菜单名与禁用原因，避免用户困惑。

## 检测方法

1. 统计导航栏菜单项数量，若 > `nav_threshold` 检查是否实现双模式
2. 扫描折叠模式的 tooltip，验证是否用纯 CSS `:hover` 实现
3. 检查切换逻辑是否用 `<Transition mode="out-in">`
4. 检查 `localStorage.getItem('navCollapsed')` 持久化逻辑
5. 验证展开模式与折叠模式是否共用同一 `menuItems` 数组

## 配置参数

所有参数见 [config/coding-standards-config.md](../config/coding-standards-config.md) 的"导航栏双模式参数"段。

## 适配说明

- 移动端优先项目：`nav_threshold` 改为 `5`，`tooltip_implementation` 改为 `js-tooltip`（移动端无 hover）
- vue-router 项目：`enabled` 设为 `false`，由路由库管理导航
- 菜单项固定较少（≤7）的项目：`enabled` 设为 `false`
