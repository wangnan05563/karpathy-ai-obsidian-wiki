# Vue SFC 单 script 块规则（CODING-029）

> 复盘来源：InputToolbar.vue 重写时混合了 `<script>` 和 `<script setup lang="ts">` 两个 script 块，导致 vue-tsc 报错且组件状态不共享。
> 所有可变参数从 `config/coding-standards-config.md` 的 `sfc_script_block` 字段读取，禁止在规则文件中硬编码标签名。

## 规则

**Vue 3 Single File Component（`.vue`）中只能有一个 `<script setup lang="ts">` 块**，禁止混合 `<script>` + `<script setup>` 双 script 块结构。需要 Options API 的迁移场景必须全量迁移到 Composition API，而非混合使用。

## 适用场景

- 所有 Vue 3 + `<script setup>` 项目的 `.vue` 文件
- 从 Options API 迁移到 Composition API 的过渡期
- 在 SFC 中需要同时使用 `<script setup>` 和普通 `<script>` 的特殊场景（见"例外情况"）

## 不适用场景

- Vue 2 项目（无 `<script setup>` 语法）
- React / Svelte / Angular 项目
- `.ts` / `.tsx` / `.js` 文件
- 已全量使用 Options API 的 Vue 3 项目（无 setup 语法）

## 例外情况

Vue 3 官方允许 `<script setup>` 与 `<script>` 共存，仅当需要以下场景之一：
1. **导出非默认组件选项**：如 `name` 属性用于 keep-alive 缓存
2. **inheritAttrs: false**：需要关闭 attribute 继承
3. **自定义选项**：第三方库要求在 Options API 中注册

**例外必须显式标注注释说明用途**，否则仍视为违规。

## 检查流程

```
读取 .vue 文件
   ↓
统计 <script> 与 <script setup> 块数量
   ↓
0 个 script 块 → 检查是否有 inline template（允许）
   ↓
1 个 <script setup> → 通过
   ↓
1 个 <script> → 告警：建议迁移到 <script setup>
   ↓
2 个 script 块（<script> + <script setup>）→ 检查例外条件
   ↓
满足例外且注释说明 → 通过
   ↓
不满足例外 → 违规
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `sfc_script_block.enabled` | `true` | 是否启用 SFC 单 script 块守卫 |
| `sfc_script_block.severity` | `error` | 违规严重级别 |
| `sfc_script_block.allowed_blocks` | `script setup lang="ts"` | 允许的 script 块类型（唯一） |
| `sfc_script_block.exception_allowed` | `true` | 是否允许例外情况（双 script 块） |
| `sfc_script_block.exception_conditions` | `name export,inheritAttrs:false,custom_options,third_party_lib` | 例外条件（逗号分隔） |
| `sfc_script_block.exception_comment_required` | `true` | 例外必须显式注释说明用途 |
| `sfc_script_block.exception_comment_pattern` | `// 例外：` | 例外注释前缀模式 |

## 检查方式

1. **块数量统计**：对 `.vue` 文件用正则 `<script(\s|>)` 匹配，统计 `<script>` 与 `<script setup>` 块数量
2. **例外注释验证**：双 script 块时检查 `<script>` 块首行是否包含 `exception_comment_pattern` 注释
3. **例外条件验证**：注释后必须匹配 `exception_conditions` 之一

## 正确示例

```vue
<!-- 正确：单 script setup 块 -->
<template>
  <div>{{ message }}</div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
const message = ref('Hello');
</script>

<style scoped>
.message { color: var(--text-primary); }
</style>
```

```vue
<!-- 正确：例外情况（需注释说明） -->
<template>
  <div>{{ message }}</div>
</template>

<!-- 例外：keep-alive 需要 name 属性 -->
<script>
export default { name: 'InputToolbar' };
</script>

<script setup lang="ts">
import { ref } from 'vue';
const message = ref('Hello');
</script>
```

## 错误示例

```vue
<!-- 错误：混合双 script 块，无注释说明 -->
<script>
export default {
  data() { return { oldData: '' }; }
};
</script>

<script setup lang="ts">
import { ref } from 'vue';
const newData = ref('');
</script>

<!-- 错误：纯 Options API 在 Vue 3 项目中 -->
<script>
export default {
  data() { return {}; }
};
</script>
```

## 适配新项目

- 适配 Vue 2 项目：将 `enabled` 设为 `false`（无 setup 语法）
- 适配 React 项目：本规则不适用
- 适配全 Options API Vue 3 项目：将 `allowed_blocks` 改为 `script`，`exception_allowed` 改为 `false`

## 与其他规则的关系

- 独立于 CODING-026 / 027 / 028：本规则是文件结构约束，不涉及类型或运行时行为
- 与 CODING-027（Composable API 先读后用）配合：单 script setup 块确保 composable 调用顺序清晰
