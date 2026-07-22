# Vue SFC 单 script 块（FR-029）

> 复盘来源：项目改造中部分 `.vue` 文件同时存在 `<script setup lang="ts">` 与 `<script lang="ts">` 两个 script 块，导致：（1）IDE / Volar 对变量提升与导出语义产生混乱推断；（2）`defineOptions` / `defineProps` 的返回值被另一个 `<script>` 块的局部变量遮蔽；（3）新人 PR 误以为是"现代写法"，复制到其他文件扩散。
> 所有可变参数从 config/review-config.md 的 `sfc_script_block_frontend` 字段读取。

## 规则

### FR-029-1：`.vue` 文件只能有一个 `<script setup lang="ts">`

每个 `.vue` 文件最多只能包含一个 `<script>` 块，且必须满足：

1. 块标签形式：`<script setup lang="ts">`（同时满足 `setup` 与 `lang="ts"` 两个属性）。
2. 编译宏 `defineProps` / `defineEmits` / `defineExpose` / `defineOptions` / `defineSlots` 必须在此 `<script setup>` 内使用，禁止在另一个普通 `<script>` 块中再调用。
3. 组件名（`name`）通过 `defineOptions({ name: 'XxxView' })` 声明，禁止为"设置组件名"而新增第二个 `<script>` 块写 `export default { name: 'XxxView' }`。
4. 与 `<script setup>` 同一文件中**禁止**再出现任何形式的其他 `<script>` 块（含无属性 `<script>`、`<script lang="ts">`、`<script setup>` 不带 lang 等）。

### FR-029-2：例外必须用 `// 例外：` 行内注释显式说明

仅以下场景允许同时存在两个 script 块，且每次例外必须在普通 `<script>` 块的第一行用注释显式标注：

1. **导出非组件默认导出的具名导出**（如组件静态常量 `export const META = {...}`，setup 块无法具名导出非响应式常量）。
2. **第三方库要求 Options 形式扩展**（如 `extends` 某些 Vue 2 兼容插件），且无替代 API。

注释模板（必须出现，且紧跟 `<script>` 标签下一行）：

```vue
<script lang="ts">
// 例外：导出 META 常量供非 Vue 上下文消费（setup 块无法具名导出非响应式值）
export const META = { version: '1.0' }
</script>
```

未标注 `// 例外：` 的双 script 块一律视为违规。

## 适用场景

- Vue 3 + `<script setup>` 项目中的所有 `.vue` 文件。
- 把 Options API 组件改造为 Composition API 的迁移 PR。
- 新建 `.vue` 文件的初始化评审。

## 不适用场景

- Vue 2 项目（无 `<script setup>` 语法支持，本规则不适用）。
- JSX / TSX 文件（非 SFC，由 vue-composition / type-safety 规则覆盖）。
- 单纯的 `.ts` 文件（非 SFC）。

## 检查流程

```
[开始] 扫描目标 .vue 文件
  │
  ▼
[1] 统计 <script> 块数量（任意属性）
  │  └─ =0 → 标记建议（SFC 应至少有一个 script setup）
  │  └─ =1 → 检查是否为 <script setup lang="ts">
  │            └─ 是 → [通过]
  │            └─ 否 → 标记 Urgent（FR-029-1）
  │
  ▼ ≥2
[2] 是否每个额外 <script> 块首行都有 "// 例外：" 注释？
  │  └─ 否 → 标记 Urgent（FR-029-2）
  │
  ▼ 是
[3] 例外理由是否属于 config 允许的例外清单？
  │  └─ 否 → 标记 Urgent（FR-029-2）
  │
  ▼ 是
[4] <script setup lang="ts"> 是否仍存在且为默认块？
  │  └─ 否 → 标记 Urgent（FR-029-1）
  │
  ▼
[结束：例外通过]
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `sfc_script_block_frontend.allowed_script_count` | `1` | 每个 `.vue` 文件允许的 `<script>` 块数量上限 |
| `sfc_script_block_frontend.required_attrs` | `setup, lang="ts"` | 必须同时具备的 script 块属性（逗号分隔） |
| `sfc_script_block_frontend.exception_marker` | `// 例外：` | 例外注释必须包含的关键字 |
| `sfc_script_block_frontend.allowed_exceptions` | `named-export-non-reactive, options-extends-compat` | 允许的例外场景标识（逗号分隔） |
| `sfc_script_block_frontend.banned_macros_in_plain_script` | `defineProps, defineEmits, defineExpose, defineOptions, defineSlots` | 禁止在非 setup 块中调用的编译宏 |
| `sfc_script_block_frontend.name_via` | `defineOptions({ name })` | 组件名声明的合规方式 |

## 检查方式

1. 用正则 `<script(\s[^>]*)?>` 统计目标 `.vue` 文件中 `<script>` 块数量。
2. 若数量 > `allowed_script_count`，检查每个额外块第一行是否含 `exception_marker` 关键字。
3. 提取注释中理由关键字，与 `allowed_exceptions` 比对，不在清单内即违规。
4. 用 `banned_macros_in_plain_script` 扫描非 setup 块中是否调用编译宏。
5. 检查组件 `name` 声明方式：若通过 `export default { name }` 而非 `defineOptions({ name })`，提示改写。

## 正确示例

```vue
<!-- ✅ 单 script setup 块 -->
<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ title: string }>()
defineOptions({ name: 'HeroView' })  // ✅ 组件名通过 defineOptions 声明

const count = ref(0)
</script>

<template>
  <h1>{{ title }}</h1>
  <button @click="count++">{{ count }}</button>
</template>
```

```vue
<!-- ✅ 合法例外：导出非响应式常量 -->
<script lang="ts">
// 例外：named-export-non-reactive — 导出 META 常量供非 Vue 上下文消费
//       （setup 块无法具名导出非响应式值，需用普通 script 块）
export const META = { version: '1.0', kind: 'hero' }
</script>

<script setup lang="ts">
import { ref } from 'vue'
import { META } from './HeroView.vue'  // 同文件引用也允许
const count = ref(0)
</script>
```

## 错误示例

```vue
<!-- ❌ 双 script 块：为声明 name 而引入 Options 写法 -->
<script lang="ts">
export default {
  name: 'HeroView',  // ❌ 应用 defineOptions({ name: 'HeroView' }) 替代
}
</script>

<script setup lang="ts">
import { ref } from 'vue'
const count = ref(0)
</script>
```

```vue
<!-- ❌ 双 script 块且无例外注释 -->
<script lang="ts">
export const helper = () => { /* ... */ }
</script>

<script setup lang="ts">
import { ref } from 'vue'
</script>
```

```vue
<!-- ❌ 在非 setup 块中调用编译宏 -->
<script lang="ts">
// 例外：某理由
defineProps({ x: Number })  // ❌ 编译宏禁止在普通 script 块中使用
export default { name: 'Wrong' }
</script>
```

```vue
<!-- ❌ 单 script 但属性不全 -->
<script>           <!-- ❌ 缺 setup 与 lang="ts" -->
import { ref } from 'vue'
const count = ref(0)
export default { setup() { return { count } } }
</script>
```

## 适配新项目

- **React / Next.js**：本规则不适用（非 SFC）。
- **Vue 2**：本规则不适用（无 `<script setup>` 语法），但可降级为"禁止混用 Options API 与 Composition API（@vue/composition-api 插件）在同一组件"。
- **纯 JavaScript**：本规则降级为"`<script setup>` 必须存在且唯一"，去掉 `lang="ts"` 要求。
- **Nuxt 3 / Vite + Vue 3**：完全适用，参数无需调整。
