# dangerous-action-rule - Code Examples

> This file contains Wrong/Right code examples extracted from [dangerous-action-rule.md](../dangerous-action-rule.md).
> Load on demand when you need to reference examples or generate fix code.

---

## DA-1: 破坏性操作必须提供 dry_run 预览模式，默认开启

### Wrong

```ts
// Wrong：清理接口直接执行，无预览模式
const handleCleanup = async () => {
  const res = await api.cleanup({ before: sevenDaysAgo })
  // 用户无法预知将删除多少条记录，误删无法挽回
  ElMessage.success(`已清理 ${res.affected} 条记录`)
}
```

### Right

```ts
// Right：默认 dry_run = true 仅预览，用户确认后再实际执行
const dryRun = ref(true)

const handleSubmit = async () => {
  const res = await api.cleanup({ before: sevenDaysAgo, dry_run: dryRun.value })
  if (dryRun.value) {
    ElMessage.info(`预览：将清理 ${res.affected} 条记录`)
  } else {
    ElMessage.success(`已清理 ${res.affected} 条记录`)
  }
}
```

---

## DA-2: 关闭 dry_run 时按钮必须切换为 danger 样式

### Wrong

```vue
<template>
  <!-- Wrong：dry_run 状态变化时按钮样式不变，用户无法感知严重性 -->
  <el-button type="primary" @click="handleSubmit">
    {{ dryRun ? '预览' : '确认执行' }}
  </el-button>
  <el-switch v-model="dryRun" active-text="预览" inactive-text="执行" />
</template>
```

### Right

```vue
<template>
  <!-- Right：dry_run = false 时按钮变红（type=danger 或 .danger 类） -->
  <el-button
    :type="dryRun ? 'primary' : 'danger'"
    :class="{ danger: !dryRun }"
    @click="handleSubmit"
  >
    {{ dryRun ? '预览' : '确认执行' }}
  </el-button>
  <el-switch v-model="dryRun" active-text="预览" inactive-text="执行" />
</template>

<style scoped>
.danger {
  /* 关闭 dry_run 时的强警示样式 */
  animation: pulse-red 1.2s infinite;
}
@keyframes pulse-red {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.6); }
  50% { box-shadow: 0 0 0 8px rgba(245, 108, 108, 0); }
}
</style>
```

---

## DA-3: 实际执行前必须弹出二次确认对话框

### Wrong

```ts
// Wrong：dry_run = false 时直接发请求，误点造成不可逆操作
const handleSubmit = async () => {
  await api.cleanup({ dry_run: dryRun.value })
}
```

### Right

```ts
import { ElMessageBox, ElMessage } from 'element-plus'

const handleSubmit = async () => {
  if (!dryRun.value) {
    // 实际执行前必须二次确认
    try {
      await ElMessageBox.confirm(
        '本次操作将实际清理选中的会话记录，且无法撤销。',
        '执行确认',
        { type: 'warning', confirmButtonText: '确认执行', cancelButtonText: '取消' }
      )
    } catch {
      return // 见 DA-4：取消不发起请求
    }
  }
  const res = await api.cleanup({ dry_run: dryRun.value })
  ElMessage.success(`已${dryRun.value ? '预览' : '清理'} ${res.affected} 条`)
}
```

---

## DA-4: 取消二次确认不发起任何请求

### Wrong

```ts
// Wrong：catch 中"以 dry_run 模式继续发请求"，违背用户取消意图
const handleSubmit = async () => {
  if (!dryRun.value) {
    try {
      await ElMessageBox.confirm('...', '执行确认')
    } catch {
      // 错误：取消后仍以预览模式发请求，越权
      dryRun.value = true
      await api.cleanup({ dry_run: true })
      return
    }
  }
  await api.cleanup({ dry_run: dryRun.value })
}
```

```ts
// Wrong：catch 中忽略返回，继续执行后续请求
const handleSubmit = async () => {
  if (!dryRun.value) {
    try {
      await ElMessageBox.confirm('...', '执行确认')
    } catch {
      // 仅日志，不 return
      console.log('用户取消')
    }
  }
  // 用户取消后仍会执行这一行
  await api.cleanup({ dry_run: dryRun.value })
}
```

### Right

```ts
const handleSubmit = async () => {
  if (!dryRun.value) {
    try {
      await ElMessageBox.confirm('...', '执行确认')
    } catch {
      // 用户取消：直接 return，不发任何请求
      return
    }
  }
  await api.cleanup({ dry_run: dryRun.value })
}
```

---

## DA-5: 确认文案必须包含"不可撤销"提示

### Wrong

```ts
// Wrong：文案过于简短，未说明不可撤销
await ElMessageBox.confirm('确认执行？', '提示', { type: 'warning' })
```

```ts
// Wrong：仅说"将删除"，未强调不可撤销
await ElMessageBox.confirm('将删除选中的会话记录。', '提示', { type: 'warning' })
```

### Right

```ts
// Right：明确说明操作内容 + "无法撤销"提示
const actionVerb = '删除'
const targetName = '选中的会话记录'
await ElMessageBox.confirm(
  `本次操作将实际${actionVerb}${targetName}，且无法撤销。`,
  '执行确认',
  { type: 'warning', confirmButtonText: '确认执行', cancelButtonText: '取消' }
)
```

---

## DA-6: 实际执行后必须记录审计日志

### Wrong

```ts
// Wrong：仅在出错时 console.error，成功执行无任何记录
const handleSubmit = async () => {
  try {
    await api.cleanup({ dry_run: false })
    ElMessage.success('清理完成')
  } catch (e) {
    console.error('清理失败', e) // 刷新后丢失，无法追溯
  }
}
```

### Right

```ts
const handleSubmit = async (key: CleanKey) => {
  const res = await api.cleanup({ key, dry_run: false })
  if (!res.error) {
    ElMessage.success('清理完成')
    // 实际执行成功后记录审计日志
    await api.logAction({
      action: `cleanup:${key}`,
      target: res.affected,
      operator: currentUser.value?.id,
      timestamp: Date.now()
    })
  }
}
```

---

## DA-7: 多表单场景必须按 key 独立管理 loading 与 result 状态

### Wrong

```ts
// Wrong：4 个清理表单共用单一 loading 与 result，互相干扰
const loading = ref(false)
const result = ref<CleanResult | null>(null)

const handleSubmit = async (key: CleanKey) => {
  loading.value = true
  try {
    // 表单 A 提交时表单 B 按钮也 loading
    // 表单 A 结果会覆盖表单 B 的结果
    result.value = await api.cleanup({ key, dry_run: dryRun.value })
  } finally {
    loading.value = false
  }
}
```

### Right

```ts
import { reactive, ref } from 'vue'

type CleanKey = 'expired' | 'orphan' | 'broken' | 'redundant'
interface CleanResult { affected: number; items: string[] }

// 每个表单按 key 独立持有 loading 与 result
const loading = reactive<Record<CleanKey, boolean>>({
  expired: false, orphan: false, broken: false, redundant: false
})
const result = ref<Record<CleanKey, CleanResult | null>>({
  expired: null, orphan: null, broken: null, redundant: null
})

const handleSubmit = async (key: CleanKey) => {
  // 提交时重置对应 key 的 result，避免显示陈旧结果
  result.value[key] = null
  loading[key] = true
  try {
    result.value[key] = await api.cleanup({ key, dry_run: dryRun.value })
  } finally {
    loading[key] = false
  }
}
```

```vue
<template>
  <!-- 每个表单绑定自己的 key 状态，互不干扰 -->
  <CleanForm
    v-for="key in cleanKeys"
    :key="key"
    :loading="loading[key]"
    :result="result[key]"
    @submit="handleSubmit(key)"
  />
</template>
```

---

*End of examples*
