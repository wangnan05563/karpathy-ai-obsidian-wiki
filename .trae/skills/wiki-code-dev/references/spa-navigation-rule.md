# SPA 内部跳转规则

> 防止在 SPA（手动路由切换）中直接使用 `<a href="#...">` 或 `router.push` 失效。
> 本规则由历史问题复盘提炼（About.vue→Help.vue 内部跳转需要通过 CustomEvent 派发）。

## 触发关键词

- `currentView` / `currentRoute` / `view state`
- `CustomEvent` / `dispatchEvent`
- `<a href="#">` / `router-link`
- 内部跳转 / 视图切换 / navigate event

## 规则

### R-1 SPA 手动路由跳转必须用事件派发（critical）

当 SPA 通过 `currentView = ref('xxx')` 手动管理视图切换时，跨组件跳转必须通过 `CustomEvent` 派发，由 App.vue 监听后切换 `currentView`，禁止：
- 直接修改父组件 ref（违反数据流单向性）
- 使用 `<a href="#help">` 浏览器原生锚点（会刷新页面或修改 URL hash）
- 使用 `router.push`（项目未引入 vue-router 时无效）

**事件命名约定**：`<project-name>:navigate`，detail 为目标视图名。

### R-2 事件监听器生命周期管理（critical）

`addEventListener` 必须在 `onMounted` 中注册，在 `onBeforeUnmount` 中移除，避免内存泄漏。监听器函数必须具名（不能用匿名箭头函数），否则无法精确移除。

### R-3 事件参数校验（suggestion）

监听器收到事件后，必须校验 `detail` 是否在允许的视图名列表内，避免无效视图切换导致空白页。

## 反例

```typescript
// 反例 1：直接修改父组件 ref（违反单向数据流）
// 子组件通过 props 直接修改父组件状态
function handleHelpClick() {
  parentRef.value.currentView = 'help'; // ❌
}

// 反例 2：使用浏览器原生锚点
// <a href="#help">帮助</a>  // 会修改 URL hash 但不切换 SPA 视图

// 反例 3：匿名函数无法移除
onMounted(() => {
  window.addEventListener('karpathy:navigate', (e) => { // ❌ 匿名
    // ...
  });
});
// onBeforeUnmount 时无法精确移除该监听器
```

## 正例

```typescript
// 派发方（如 About.vue）
function handleMenuClick(item: MenuItem, e: MouseEvent) {
  if (item.internal) {
    e.preventDefault();
    // 为什么用 CustomEvent：About 是路由终端组件，
    // 通过事件派发避免层层传递 props 修改父组件状态
    globalThis.dispatchEvent(
      new CustomEvent('karpathy:navigate', { detail: item.key })
    );
  }
}

// 监听方（App.vue）
function handleNavigateEvent(e: Event) {
  const detail = (e as CustomEvent<string>).detail;
  // 为什么校验 detail：避免无效视图名导致空白页
  const allowedViews: ViewName[] = ['dashboard', 'help', 'about', /* ... */];
  if (allowedViews.includes(detail as ViewName)) {
    currentView.value = detail as ViewName;
  }
}

onMounted(() => {
  // 为什么具名函数：onBeforeUnmount 时才能精确移除
  globalThis.addEventListener('karpathy:navigate', handleNavigateEvent as EventListener);
});

onBeforeUnmount(() => {
  globalThis.removeEventListener('karpathy:navigate', handleNavigateEvent as EventListener);
});
```

## 适用场景

- SPA 手动路由项目（无 vue-router / react-router）
- 跨多层组件的视图切换
- 路由终端组件（如关于页、设置页）发起的内部跳转

## 不适用场景

- 已使用 vue-router / react-router 的项目（直接用 `router.push`）
- 父子组件直接相邻的简单状态切换（用 props/emit 即可）
- 需要保留浏览器历史记录的场景（用 vue-router 的 history 模式）
