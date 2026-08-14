# 毛玻璃 backdrop-filter 包含块陷阱规则（CODING-BACKDROP-FILTER-CB）

> 本规则基于「移动端双主题切换 + 滚动回顶 FAB 主题间行为不一致」复盘提炼（glass 主题下 FAB 随页面滚动离开视口固定位置，浅色主题正常）。
> 所有参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `backdrop_filter_cb` 段读取。
> 规则文件本身不硬编码任何具体选择器 / 模糊值 / 主题名；全部来自配置。

## 触发关键词

- `backdrop-filter` / `-webkit-backdrop-filter` / `filter: blur()`
- `position: fixed` / `position: absolute`（位于可能含毛玻璃的祖先内）
- 滚动容器：`.mobile-content` / `.scroll-container` / `overflow-y: auto` + `backdrop-filter` 同元素
- 滚动回顶 FAB：`scroll-fab` / `locate-fab`；全屏遮罩：`sheet-mask` / `dialog-mask`
- `Teleport` / `to=".mobile-root"`（合法逃逸写法）

## 规则

### CB-1 毛玻璃容器不得成为 fixed 后代的包含块（critical）

按 CSS 规范（Filter Effects Module / CSS Positioned Layout），**任何元素的 `backdrop-filter` 取值非 `none`（含 var 解析后为非 none）时，该元素即成为其 `position: fixed` 与 `position: absolute` 后代的 containing block**。

后果：这些 fixed 后代不再相对视口（viewport）定位，而是相对该毛玻璃容器定位 → 容器滚动时，FAB / 遮罩随内容一起滚走，失去"固定悬浮"语义。

**判断逻辑**：

```
IF 容器 C 设置 backdrop-filter != none（解析后）:
    IF C 含后代 D 且 D 为 position: fixed / absolute:
        违规（severity = backdrop_filter_cb.severity，默认 critical）
        说明：D 将相对 C 定位，随 C 滚动脱离视口固定预期
```

**多主题放大效应**：若 `backdrop-filter` 走 `var(--m-blur)`，而浅色主题 `--m-blur: none`、毛玻璃主题 `--m-blur: blur(18px)`，则同一组件在浅色主题正常、在毛玻璃主题失固定 → **主题间行为不一致，直接命中多主题一致性审查（FR-040）**。这是本规则最关键的危害面：问题只在特定主题显现，单主题验证无法暴露。

### CB-2 切换主题不得改组件级 backdrop-filter 字面量（standard）

多主题项目切换主题时，**禁止**在组件 `<style>` 里写 `theme === 'light' ? a : b` 或新增/移除 `backdrop-filter` 表达式；应统一切换 `--m-*` 主题变量值（见 CODING-DUAL-THEME-VAR）。组件样式保持 `backdrop-filter: var(--m-blur)` 不变，主题差异只体现在变量取值。

**判断逻辑**：

```
IF 组件文件含 theme 分支条件（theme === / data-theme= / 媒体查询硬性改写 backdrop-filter）:
    违规（severity = suggestion~major）：应改为变量驱动
```

## 修复模板（两种，择一）

发现"毛玻璃主题下 fixed FAB / 遮罩随滚动离开固定位"时：

**方案 A（推荐，最小改动）**：从滚动容器移除 `backdrop-filter` / `-webkit-backdrop-filter` 两行。把毛玻璃模糊保留在**同级兄弟节点**（如底部 tabbar）而非滚动容器本身；兄弟节点不在 fixed 后代的祖先链上，不影响其包含块。
前提：该滚动容器本身不需要毛玻璃背景（内容区透出底层即可）。

**方案 B（需保留容器毛玻璃时）**：将 fixed 子元素用 `<Teleport to=".mobile-root">` 逃逸到毛玻璃容器的祖先之外（如 `.mobile-root`），使其重新相对视口定位。
前提：被 Teleport 的元素不依赖原作用域内的局部状态引用（或已通过 props / 全局 store 解耦）。

**验证**：在浅色与毛玻璃两种主题下分别滚动页面，确认 FAB / 遮罩始终钉在视口固定位置（不随内容滚走）；并确认 `backdrop_filter_cb.guard_patterns`（如 `Teleport`）未被重构误删。

## 反例

```css
/* 反例：滚动容器带毛玻璃 → 内部 fixed FAB 成为其包含块，随滚动失固定 */
.mobile-content {
  overflow-y: auto;
  backdrop-filter: var(--m-blur);          /* glass 主题解析为 blur(18px) → 成为包含块 */
  -webkit-backdrop-filter: var(--m-blur);
}
.mb-scroll-fab {
  position: fixed;                          /* 相对 .mobile-content 定位，非视口 */
  right: 16px;
  bottom: 72px;
}
/* 浅色主题 --m-blur:none → 表现正常；glass 主题 → FAB 随列表滚动而漂移 */
```

```vue
<!-- 反例：全屏 sheet 遮罩在毛玻璃容器内，glass 主题下遮罩不覆盖全屏 -->
<div class="mobile-content">   <!-- 含 backdrop-filter -->
  <div class="mq-sheet-mask" style="position: fixed; inset: 0;"></div>
</div>
```

## 正例

```css
/* 正例 A：滚动容器不带毛玻璃；毛玻璃只给同级 tabbar（不在 fixed 后代祖先链） */
.mobile-content {
  overflow-y: auto;        /* 无 backdrop-filter，fixed 后代相对视口 */
}
.mobile-tabbar {
  position: fixed;
  backdrop-filter: var(--m-blur);   /* tabbar 与 content 是 .mobile-root 的兄弟，安全 */
}
```

```vue
<!-- 正例 B：必须用容器毛玻璃时，Teleport 逃逸 fixed 子元素 -->
<div class="mobile-content">   <!-- 含 backdrop-filter -->
  <Teleport to=".mobile-root">
    <div class="mb-scroll-fab" style="position: fixed; right: 16px; bottom: 72px;"></div>
  </Teleport>
</div>
```

## 适用场景

- 多主题 SPA（至少 2 个主题，且主题间 `--m-blur` 等毛玻璃变量取值不同）
- 滚动容器内嵌 `position: fixed` 悬浮元素（滚动回顶 FAB、定位按钮、全屏 sheet / dialog 遮罩）
- 任何 `backdrop-filter` 与 `position: fixed` 后代共存的布局（含 Tauri 透明窗口、桌面端毛玻璃面板）

## 不适用场景

- 单主题项目（`backdrop-filter` 恒为非 none 且全局一致，包含块效应可预测，不构成"主题间不一致"）
- 滚动容器本身无 fixed 后代（毛玻璃仅作用于背景视觉，无定位副作用）
- 固定元素本就希望相对某滚动容器定位（如吸顶于某卡片内）——此时语义正确，非违规
- 纯 `filter: blur()`（不创建包含块；仅 `backdrop-filter` 有此规范行为）作用于非定位上下文

## 复盘记录（四维度）

### 成功执行任务的完整步骤

1. **现象定位**：浅色主题下浏览/聆听页滚动回顶 FAB 正常钉底，切到毛玻璃主题后 FAB 随列表滚动飘走——确认是主题相关而非逻辑 bug。
2. **根因回溯**：按 CSS 规范确认 `backdrop-filter != none` 的元素成为 fixed 后代 containing block；`MobileShell.vue` 的 `.mobile-content` 同时承担"滚动容器 + 毛玻璃背景（glass 主题）"两个职责，使内部 `.mb-scroll-fab` / `.ml-scroll-fab` / `.mq-sheet-mask` 全部相对它定位。
3. **变量链路核对**：`.mobile-content { backdrop-filter: var(--m-blur) }`，`--m-blur` 在 `:root` 默认 `blur(18px)`、在 `.theme-light` 覆盖为 `none` → 主题切换只改 `--m-blur` 值（符合双主题变量架构），但副作用是"glass 主题下 .mobile-content 变成包含块"未被纳入审查。
4. **修复择一**：滚动容器去掉 `backdrop-filter` 两行（保留 `.mobile-tabbar` 兄弟节点的模糊），或 `<Teleport to=".mobile-root">` 逃逸 fixed 子元素。
5. **双主题验证**：两种主题分别滚动，确认 FAB / 遮罩始终视口固定。

### 不确定性与失败点

1. **单主题验证盲区**：只在浅色主题（默认）验证会完全漏掉 glass 主题的包含块失效——必须按 FR-040 双主题切换截图验证。
2. **规范认知缺口**：容易误以为 `position: fixed` 永远相对视口；实际 `backdrop-filter` / `transform` / `filter` / `will-change` / `perspective` 等都会创建 containing block，需逐条核对祖先链。
3. **Teleport 误删**：重构时若把 `<Teleport>` 当"多余包裹"删掉，会静默 reintroduce 包含块 bug——需在静态守卫里守护 `guard_patterns`。
4. **兄弟节点判断**：需确认 tabbar 与 content 确为 `.mobile-root` 的兄弟（同层），否则 tabbar 的 fixed 也会受影响。

### 可抽象的固定流程与判断逻辑

「**祖先链包含块排查**」：对任意 `position: fixed/absolute` 元素，向上追溯祖先，若任一祖先含 `backdrop-filter != none`（或 `transform` / `filter` / `will-change` / `perspective`），则该祖先即其 containing block，fixed 语义失效。
→ 抽象为规则 CB-1（critical）+ 静态守卫（扫描"含 backdrop-filter 的容器 + 含 position:fixed 后代"共现）。
→ 抽象为规则 CB-2（standard）：主题切换只改 `--m-*` 变量，不碰组件级 `backdrop-filter` 字面量（与 CODING-DUAL-THEME-VAR 共用变量架构）。

### 适用场景与不适用场景（边界）

- **适用**：多主题 SPA 的滚动容器 + fixed 悬浮元素；Tauri 透明窗口毛玻璃面板。
- **不适用**：单主题恒模糊（无主题间不一致）；无 fixed 后代的纯背景毛玻璃；本就希望相对容器吸顶的场景（语义正确）；纯 `filter: blur()` 非定位上下文。
- 边界判定由 `backdrop_filter_cb` 配置段参数化（滚动容器选择器、模糊变量名、fixed 后代选择器、severity），适配任意前端项目。
