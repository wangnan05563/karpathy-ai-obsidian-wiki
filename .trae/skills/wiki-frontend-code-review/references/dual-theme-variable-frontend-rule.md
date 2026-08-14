# 双主题统一 --m-* 变量架构（FR-090）

> 前端规则文件，对应 wiki-code-dev CODING-DUAL-THEME-VAR。
> 所有选择器 / 变量名 / key 来自 `config/review-config.md` 的 `dual_theme_var_frontend` 段，零硬编码。

## 核心机理

多主题项目须用一套 `--m-*` 主题变量承载全部主题相关样式（背景 / 模糊 / 文字 / 边框 / 阴影 / 光晕）：`:root` 给出默认主题取值，特定主题类（如 `.theme-light`）仅局部覆盖 `--m-*` 变量。切换主题 = 给根容器（如 `.mobile-root`）挂/换主题类，组件样式保持 `var(--m-*)` 不变 → **组件零主题分支**。

## 审查检查点

- **FR-090-1（standard）**：主题相关样式须引用 `var(--m-*)`（前缀 `theme_variable_prefix` 默认 `--m-`）而非字面量；新增主题样式须先在 `var_definition_files`（默认 `mobile-light.css` + `:root`）补 `--m-*` 定义再引用。与 FR-035 主题色变量映射互补：FR-035 针对通用主题色白名单，本规则针对 `--m-*` 双主题专用变量。
- **FR-090-2（standard）**：主题切换状态须集中单一 composable（如 `useMobileTheme`）——模块级单例 `ref` + `localStorage` 持久化 key 统一（`persist_key` 默认 `karpathy-mobile-theme`）+ 默认主题参数化（`default_theme` 默认 `light`）；禁止主题状态散落多个 store / 组件本地 ref / 硬编码默认。
- **FR-090-3（standard）**：组件 `<style>` / `<script>` 不得写 `theme === ? a : b` / `data-theme` 硬编码分支；主题差异全部收敛到 `--m-*` 取值（与 FR-089-2 协同）。

## 反例

```css
/* 反例 1：组件写死毛玻璃主题字面量，浅色主题下不跟随变量 */
.mobile-content { background: rgba(20, 8, 42, 0.42); backdrop-filter: blur(18px); }
```

```vue
<!-- 反例 2：组件级主题分支 -->
<div :style="theme === 'light' ? { background: '#fff' } : { background: 'rgba(20,8,42,.42)' }">
```

```ts
// 反例 3：主题状态散落，默认硬编码 'glass'，与 useMobileTheme 单例重复且不持久化
const theme = ref<'light' | 'glass'>('glass')
```

## 正例

```css
:root { --m-bg: rgba(20, 8, 42, 0.42); --m-blur: 18px; --m-text: #f5f5f5; }
.mobile-root.theme-light { --m-bg: #ffffff; --m-blur: none; --m-text: #111111; }
.mobile-content { background: var(--m-bg); backdrop-filter: var(--m-blur); }  /* 切换主题只改变量取值 */
```

```ts
// 主题状态集中单一 composable：模块级单例 + localStorage 持久化 + 默认主题参数化
const theme = ref<MobileTheme>(loadTheme())   // loadTheme 读 persist_key，缺省 default_theme
watch(theme, (t) => localStorage.setItem('karpathy-mobile-theme', t))
```

## 与静态守卫协同

本规则以配置驱动为主；纯变量引用 / 主题分支属可静态识别模式，可由 `review-config.md` 的 `config_driven_frontend` 透镜（CODING-CONFIG-DRIVEN）扫描主题相关字面量与 `theme ===` 分支信号；运行时主题状态单例性由浏览器 E2E（theme_switch）验证。

## 适用 / 不适用

- **适用**：多主题 SPA（浅色 / 深色 / 毛玻璃并存）、主题差异大、需零组件改动切换。
- **不适用**：单主题；差异极小；第三方库样式；原型阶段。

> 四维度复盘（成功步骤 / 不确定性与失败点 / 可抽象流程 / 适用与不适用边界）见 wiki-code-dev `references/dual-theme-variable-rule.md` 的「复盘记录」段。
