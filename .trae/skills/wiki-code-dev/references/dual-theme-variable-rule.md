# 双主题统一 --m-* 变量架构规则（CODING-DUAL-THEME-VAR）

> 本规则基于「移动端双主题（浅白风 / 毛玻璃）切换」复盘提炼：用一套 `--m-*` 主题变量承载全部主题相关样式，切换主题只改根元素主题类、切换变量取值，组件零主题分支。
> 所有参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `dual_theme_var` 段读取。
> 规则文件本身不硬编码任何颜色值 / 模糊值 / 主题名；全部来自配置。

## 触发关键词

- `--m-` 前缀变量（`--m-bg` / `--m-blur` / `--m-text` / `--m-border` / `--m-shadow`）
- `:root` 默认值 + `.theme-light` / `.theme-dark` 局部覆盖
- `data-theme` / `class="theme-*"` / `useMobileTheme` / `useTheme`
- `localStorage` 主题持久化键（如 `karpathy-mobile-theme`）
- `backdrop-filter: var(--m-blur)`（与 CODING-BACKDROP-FILTER-CB 协同）
- `theme === 'light' ? a : b`（组件级主题分支，违规信号）

## 规则

### DT-1 主题相关样式全部走 --m-* 变量（standard）

多主题项目须定义一套 `--m-*` 主题变量承载所有主题相关样式（背景 / 模糊 / 文字 / 边框 / 阴影 / 光晕）。`:root` 给出默认主题取值；特定主题类（如 `.theme-light`）**仅局部覆盖 `--m-*` 变量**。

- 组件样式一律引用 `var(--m-*)`，不得写主题相关字面量。
- 切换主题 = 给根容器（如 `.mobile-root`）挂/换主题类，组件样式不变。

**判断逻辑**：

```
IF 组件样式含主题相关字面量（rgba/rgb/#hex 且与主题相关）或不引用 --m-* 变量:
    IF 存在对应 --m-* 变量:
        违规（severity = dual_theme_var.severity，默认 standard）：应改用变量
    ELSE:
        先建立 --m-* 变量（dual_theme_var.var_definition_files）再引用
```

### DT-2 切换主题不得写组件级分支（standard）

禁止在组件 `<style>` / `<script>` 里写 `theme === 'light' ? a : b`、`data-theme` 硬编码分支、或为某主题特判新增/移除样式。所有差异收敛到 `--m-*` 取值变化。

```
IF 组件文件含 theme 条件分支 / 媒体查询硬性改写主题样式:
    违规（severity = suggestion）：应改为 --m-* 变量驱动
```

### DT-3 主题状态集中单一 composable（standard）

主题切换入口、默认主题、持久化 key、是否跟随系统须集中到单一 composable（如 `useMobileTheme`）：

- 模块级单例 `ref<MobileTheme>`，避免多实例不一致；
- `localStorage` 持久化 key 从 `dual_theme_var.persist_key` 读取，默认主题从 `dual_theme_var.default_theme` 读取；
- 根容器主题类由该 composable 统一驱动（如 `MobileShell` 按 `theme` 挂 `.theme-light`）。

```
IF 主题状态散落在多个 store / 组件本地 ref / 硬编码 key:
    违规（severity = suggestion）：应收敛到单一 composable
```

## 反例

```css
/* 反例 1：组件写死毛玻璃主题字面量，浅色主题下不跟随变量 */
.mobile-content {
  background: rgba(20, 8, 42, 0.42);   /* 浅色主题仍显示深色背景，不随主题变 */
  backdrop-filter: blur(18px);
}
```

```vue
<!-- 反例 2：组件级主题分支 -->
<div :style="theme === 'light' ? { background: '#fff' } : { background: 'rgba(20,8,42,.42)' }">
```

```ts
// 反例 3：主题状态散落，默认主题硬编码 'glass'
const theme = ref<'light' | 'glass'>('glass')   // 与 useMobileTheme 单例重复且不持久化
```

## 正例

```css
/* 正例：全部走 --m-* 变量；:root 默认 + .theme-light 局部覆盖 */
:root {
  --m-bg: rgba(20, 8, 42, 0.42);
  --m-blur: 18px;
  --m-text: #f5f5f5;
}
.mobile-root.theme-light {
  --m-bg: #ffffff;
  --m-blur: none;
  --m-text: #111111;
}
.mobile-content {
  background: var(--m-bg);
  backdrop-filter: var(--m-blur);   /* 切换主题只改变量取值 */
}
```

```ts
// 正例：主题状态集中单一 composable
// useMobileTheme.ts —— 模块级单例 + localStorage 持久化 + 默认主题参数化
const theme = ref<MobileTheme>(loadTheme())   // loadTheme 读 persist_key，缺省 default_theme
watch(theme, (t) => localStorage.setItem('karpathy-mobile-theme', t))
```

## 适用场景

- 任意多主题 SPA（≥2 主题，尤其浅色 / 深色 / 毛玻璃风并存）
- 主题间差异大（背景、模糊、文字、边框、阴影均不同）的项目
- 需要"切换主题零组件改动"的可维护性诉求

## 不适用场景

- 单主题项目（无主题切换需求，变量化收益低）
- 主题差异极小（仅 1-2 个颜色微调），引入整套 `--m-*` 架构过度设计
- 第三方库内部样式（无法控制其变量体系）
- 设计稿原型阶段（主题频繁变动，变量化反而增加维护成本）

## 复盘记录（四维度）

### 成功执行任务的完整步骤

1. **统一变量底座**：在 `:root` 定义 glass 风格默认值（`--m-blur:18px`、`--m-bg:rgba(20,8,42,.42)` 等），所有组件引用 `var(--m-*)`。
2. **作用域化浅色覆盖**：新建 `mobile-light.css`，仅对 `.mobile-root.theme-light` 局部覆盖 `--m-*` 为浅色值（`--m-bg:#ffffff`、`--m-blur:none`）并隐藏极光装饰层。
3. **单例主题状态**：`useMobileTheme` 模块级单例 `ref<MobileTheme>` + `localStorage` 持久化（key `karpathy-mobile-theme`）+ 默认 `'light'`。
4. **根容器挂类**：`MobileShell` 按 `theme` 给 `.mobile-root` 挂 `.theme-light` / 默认类；`MobileMe` 提供切换分段控件。
5. **双主题验证**：两种主题切换后布局/可读性一致，组件样式无任何主题分支。

### 不确定性与失败点

1. **变量未全量覆盖**：新组件偶尔漏用 `--m-*` 而写死字面量，浅色主题下出现"深色补丁"——需 FR-035 主题色变量映射 + 本规则 DT-1 双重审查。
2. **模糊变量副作用盲区**：`--m-blur` 在浅色为 `none`、glass 为 `blur()`，未意识到这会让 `.mobile-content` 在 glass 主题变成 fixed 后代的包含块（与 CODING-BACKDROP-FILTER-CB 交叉）——单独看变量架构正确，组合后才暴露 bug。
3. **持久化 key 漂移**：若 composable 与组件各存一份主题状态，刷新后状态不一致——必须单例 + 统一 key。

### 可抽象的固定流程与判断逻辑

「**主题差异收敛到变量**」：新增任何主题相关样式 → 先确认 `--m-*` 变量是否已定义（否则在 `:root` + 各 `.theme-*` 补定义）→ 组件只引用 `var(--m-*)` → 切换主题只挂根容器主题类。
→ 抽象为规则 DT-1（变量承载）+ DT-2（禁组件分支）+ DT-3（状态集中）。
→ 与 CODING-BACKDROP-FILTER-CB 共用变量架构：主题切换只改变量，不碰组件级 `backdrop-filter` 字面量。

### 适用场景与不适用场景（边界）

- **适用**：多主题 SPA、主题差异大、需"零组件改动切换"。
- **不适用**：单主题；差异极小；第三方库样式；原型阶段。
- 边界判定由 `dual_theme_var` 配置段参数化（变量前缀、默认主题、根容器选择器、浅色类选择器、持久化 key），适配任意前端项目。
