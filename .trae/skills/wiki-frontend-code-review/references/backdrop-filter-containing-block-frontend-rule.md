# 毛玻璃 backdrop-filter 包含块陷阱（FR-089）

> 前端规则文件，对应 wiki-code-dev CODING-BACKDROP-FILTER-CB。
> 所有选择器 / 变量名 / 模糊值来自 `config/review-config.md` 的 `backdrop_filter_frontend` 段，零硬编码。

## 核心机理

按 CSS 规范（Filter Effects Module / CSS Positioned Layout），**任何元素的 `backdrop-filter` 取值非 `none`（含 `var()` 解析后为非 none）时，该元素即成为其 `position: fixed` 与 `position: absolute` 后代的 containing block**。

后果：这些 fixed 后代不再相对视口定位，而是相对该毛玻璃容器定位 → 容器滚动时，FAB / 遮罩随内容一起滚走，失去"固定悬浮"语义。

## 多主题放大效应（最关键危害面）

若 `backdrop-filter` 走 `var(--m-blur)`，而浅色主题 `--m-blur: none`、毛玻璃主题 `--m-blur: blur(18px)`，则：
- **浅色主题**：`.mobile-content` 无包含块效应 → fixed FAB / 遮罩正常。
- **毛玻璃主题**：`.mobile-content` 成为包含块 → fixed FAB / 遮罩随滚动漂移。

→ 同一组件主题间行为不一致，**直接命中 FR-040 多主题一致性**。问题只在毛玻璃主题显现，单主题验证无法暴露。

## 审查检查点

- **FR-089-1（critical）**：含 `backdrop-filter` 的滚动容器（如 `.mobile-content`）内有 `position: fixed` 后代（滚动回顶 FAB / 定位按钮 / 全屏 sheet 遮罩）时，须确认容器在毛玻璃主题下不会成为该 fixed 后代的包含块。修复二选一：
  1. 从滚动容器移除 `backdrop-filter` / `-webkit-backdrop-filter`（毛玻璃保留在**同级兄弟节点**如底部 tabbar，其 fixed 不受影响）；
  2. 将 fixed 子元素 `<Teleport to=".mobile-root">` 逃逸到毛玻璃祖先之外，恢复相对视口定位。
- **FR-089-2（standard）**：多主题切换下组件写了主题分支（`theme === ? a : b` / `data-theme` 硬编码 / 为某主题特判改 `backdrop-filter`）→ 须改为 `--m-*` 变量驱动（与 FR-090 协同）。

## 反例

```css
/* 反例：滚动容器带毛玻璃 → 内部 fixed FAB 成为其包含块，glass 主题下随滚动失固定 */
.mobile-content {
  overflow-y: auto;
  backdrop-filter: var(--m-blur);          /* glass 主题 = blur(18px) → 包含块 */
  -webkit-backdrop-filter: var(--m-blur);
}
.mb-scroll-fab { position: fixed; right: 16px; bottom: 72px; }  /* 相对 .mobile-content，非视口 */
```

## 正例

```css
/* 正例 A：滚动容器不带毛玻璃；毛玻璃给同级兄弟 tabbar（不在 fixed 后代祖先链） */
.mobile-content { overflow-y: auto; }                 /* 无 backdrop-filter */
.mobile-tabbar { position: fixed; backdrop-filter: var(--m-blur); }
```

```vue
<!-- 正例 B：必须容器毛玻璃时，Teleport 逃逸 fixed 子元素 -->
<div class="mobile-content">   <!-- 含 backdrop-filter -->
  <Teleport to=".mobile-root">
    <div class="mb-scroll-fab" style="position: fixed; right: 16px; bottom: 72px;"></div>
  </Teleport>
</div>
```

## 与静态守卫协同

`wiki-auto-testing` 的 `frontend_review_static_check` 派生组 `backdrop_filter_fixed_ancestor` 以纯配置扫描"含 `backdrop-filter` 的滚动容器 + 含 `position: fixed` 后代"共现并告警，`guard_patterns`（如 `Teleport`）守护逃逸写法不被重构误删，无需改引擎即可覆盖本规则。

## 适用 / 不适用

- **适用**：多主题 SPA 滚动容器内嵌 `position: fixed` 悬浮元素；Tauri 透明窗口毛玻璃面板。
- **不适用**：单主题恒模糊（无主题间不一致）；无 fixed 后代的纯背景毛玻璃；本就希望相对容器吸顶（语义正确）；纯 `filter: blur()` 非定位上下文。

> 四维度复盘（成功步骤 / 不确定性与失败点 / 可抽象流程 / 适用与不适用边界）见 wiki-code-dev `references/backdrop-filter-containing-block-rule.md` 的「复盘记录」段。
