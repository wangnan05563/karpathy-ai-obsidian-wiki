# Rule Catalog - Route Registration (Frontend SPA)

## Scope
- Covers: SPA 手动路由项目中新增视图文件时在应用入口的同步注册守卫——导入、类型扩展、tab 数组、视图分支。
- Does NOT cover: vue-router / react-router 等基于配置文件或文件约定的自动路由（此类项目由路由库保证注册完整性）、后端路由（属后端评审范畴）。

> 所有可配置参数（视图目录、入口文件、视图类型名、必须的注册钩子等）集中定义在 [config/review-config.md](../config/review-config.md) 的"前端视图注册审查参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### RR-1: 新增视图必须在应用入口同步完成四处注册

IsUrgent: True
Category: Route Registration

### Description

SPA 手动路由项目（无 vue-router / react-router）通过应用入口文件（如 `App.vue`）以 `v-if` / `v-else-if` 链路手动切换视图。新增 `views/*.vue` 视图文件时，必须在应用入口同步完成配置 `required_hooks` 指定的四处注册：

1. **import**：在 `<script setup>` 顶部导入新视图组件。
2. **type**：扩展视图类型字面量联合（如 `type ViewName = 'home' | 'about' | 'newView'`），否则 TypeScript 无法识别新视图 key。
3. **v-for**：在 tab/导航数组（如 `tabs: Array<{ key: ViewName; label: string }>`）中添加新视图项，否则导航栏缺失入口、用户无法切换到新视图。
4. **v-else-if**：在模板的视图切换分支链路中添加新视图的 `v-else-if` 渲染分支，否则即使导航有入口，点击切换后内容区不渲染任何视图（呈现空白）。

复盘 Tunnel.vue 时发现：新增视图文件后仅完成 import 与 type 扩展，遗漏 v-for tab 项与 v-else-if 分支，导致导航栏看不到入口、即使通过开发者工具强行切换也呈现空白区域。

任一注册项缺失都会导致视图不可达或呈现空白，且 TypeScript 不会报错（v-for 数组与 v-else-if 链路是运行时结构，类型系统无法约束其完整性），必须通过评审守卫保障。

### Judgment Logic

1. 通过 `Glob` 列出配置 `views_directory` 下的所有 `*.vue` 文件，得到视图集合 `V_actual`。
2. 读取配置 `app_entry` 指定的入口文件内容。
3. 对每个视图文件 `Foo.vue`（视图 key 推导为 `foo` 或文件名去扩展名），在入口文件中检查 `required_hooks` 中的每一项：
   - `import`：是否包含 `import Foo from '.../views/Foo.vue'`（或匹配的导入语句）。
   - `type`：`view_type_name` 类型别名中是否包含该视图 key 字面量。
   - `v-for`：tab/导航数组中是否包含 `{ key: 'foo', ... }` 项。
   - `v-else-if`：模板中是否包含 `v-else-if="currentView === 'foo'"`（或等价条件）分支。
4. 任一钩子缺失即告警，明确指出缺失的钩子名称与期望的插入位置。

### Applicable Scenarios

- SPA 手动路由项目（Vue 3 + `<script setup>` 或 React 函数组件）。
- 入口文件通过 `v-if` / `v-else-if` 链路或条件渲染切换视图。
- 视图类型用字面量联合类型表达。

### Non-Applicable Scenarios

- vue-router / react-router / @tanstack/router 等基于配置或文件约定的自动路由项目（由路由库与构建工具保证注册完整性）。
- Next.js / Nuxt.js 等基于文件系统的路由框架。
- 微前端框架（如 qiankun）的子应用注册（属于框架层职责）。

### Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `views_directory` | `views/` | 视图文件所在目录（相对项目根） |
| `app_entry` | `App.vue` | 应用入口文件路径 |
| `view_type_name` | `ViewName` | 视图 key 的字面量联合类型名称 |
| `required_hooks` | `['import', 'type', 'v-for', 'v-else-if']` | 视图注册必须完成的钩子列表 |

### Example

```vue
<!-- App.vue -->
<script setup lang="ts">
import Home from './views/Home.vue'
import About from './views/About.vue'
import Tunnel from './views/Tunnel.vue'  // ✅ import

type ViewName = 'home' | 'about' | 'tunnel'  // ✅ type 扩展

const tabs: Array<{ key: ViewName; label: string }> = [
  { key: 'home', label: '首页' },
  { key: 'about', label: '关于' },
  { key: 'tunnel', label: '隧道' }  // ✅ v-for tab 项
]

const currentView = ref<ViewName>('home')
</script>

<template>
  <nav>
    <button v-for="tab in tabs" :key="tab.key" @click="currentView = tab.key">
      {{ tab.label }}
    </button>
  </nav>
  <Home v-if="currentView === 'home'" />
  <About v-else-if="currentView === 'about'" />
  <Tunnel v-else-if="currentView === 'tunnel'" />  // ✅ v-else-if 分支
</template>
```

### Checklist

- [ ] 新增视图文件已 `import` 到应用入口
- [ ] 视图 key 已加入 `view_type_name` 字面量联合类型
- [ ] 视图项已加入 tab/导航 v-for 数组
- [ ] 视图分支已加入模板 `v-else-if` 链路
