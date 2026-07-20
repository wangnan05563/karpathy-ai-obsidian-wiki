# 滚动容器单一职责规则

> 防止多层 `overflow-y: auto` 嵌套导致 flex 子项被压缩到 min-content 高度，内容被裁切不可见。
> 本规则由历史问题复盘提炼（Help.vue 章节卡片仅显示标题一行，blocks 全部不可见）。

## 触发关键词

- `overflow-y: auto` / `overflow-y: scroll` / `overflow: auto`
- `flex: 1` / `flex-direction: column`
- `height: 100%` / `height: 100vh` / `max-height`
- `glass-card` / `overflow: hidden`

## 规则

### R-1 滚动容器链路唯一性（critical）

容器链路上禁止出现两层及以上 `overflow-y: auto`（或 `overflow: auto`）。若外层已设 `overflow-y: auto`，内层不得再设；若必须内层滚动，外层应改为 `overflow: visible`。

**判断逻辑**：从根容器开始向下追溯，统计 `overflow-y: auto` 出现的层数；超过 1 层即违规。

### R-2 flex 容器与滚动容器分离（critical）

`flex: 1 + overflow-y: auto` 的容器，其子项若需按内容自然高度撑开，必须满足：
- 子项显式 `flex-shrink: 0`，或
- 父容器改为 `display: block` + 内部子项自然排列

**为什么需要**：flex 默认 `flex: 0 1 auto`，在容器有限高度时会被等比压缩到 min-content，导致只显示一行内容。

### R-3 glass-card 包裹长内容时的预检查（critical）

`overflow: hidden`（glass-card 全局样式）会裁切被 flex 压缩的子内容。使用 glass-card 包裹长内容时必须确认：
- 父容器未被 flex 压缩（即满足 R-2），或
- glass-card 内部不再嵌套 flex 收缩场景

## 反例

```css
/* 反例 1：双重滚动 */
.parent {
  overflow-y: auto;        /* 外层滚动 */
}
.child {
  flex: 1;
  overflow-y: auto;        /* 内层又滚动 → 双重滚动嵌套 */
  display: flex;
  flex-direction: column;
}

/* 反例 2：flex 子项未加 flex-shrink: 0 */
.scroll-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.card {
  /* 缺少 flex-shrink: 0 → 被 flex 等比压缩到 min-content 高度 */
  padding: 20px;
}
```

## 正例

```css
/* 正例：单一滚动 + flex-shrink 守卫 */
.parent {
  overflow-y: auto;        /* 只在外层滚动 */
}
.child {
  flex: 1;
  min-width: 0;
  /* 不再设 overflow-y: auto，让外层接管滚动 */
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card {
  flex-shrink: 0;          /* 关键：防止被压缩 */
  padding: 20px;
}
```

## 修复模板

发现"内容只显示标题一行"的渲染异常时，按以下顺序排查：

1. 检查外层 `.content` 是否已设 `overflow-y: auto`
2. 检查内层容器是否又设了 `overflow-y: auto` → 移除
3. 给内容卡片加 `flex-shrink: 0`
4. 验证卡片高度从 ~50px 变为内容自然高度

## 适用场景

- Vue 3 / React 等 SPA 应用的多卡片长内容页面
- 玻璃卡片（glass-card）设计系统
- flex 布局中有动态高度内容

## 不适用场景

- 表格/列表等需要内部独立滚动的场景（必须双重滚动，但应显式标注）
- CSS Grid 布局（grid 子项默认不收缩）
- 固定高度卡片（无 flex 压缩风险）
