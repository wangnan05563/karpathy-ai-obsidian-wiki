# element-plus-rule - Code Examples

> This file contains Wrong/Right code examples extracted from [element-plus-rule.md](../element-plus-rule.md).
> Load on demand when you need to reference examples or generate fix code.

---

## 消息提示用 ElMessage，禁止 alert/confirm

### Wrong

```ts
if (!form.value.title) {
  alert('标题不能为空')
  return
}
```

### Right

```ts
import { ElMessage } from 'element-plus'
if (!form.value.title) {
  ElMessage.warning('标题不能为空')
  return
}
```

---

## 按钮须用 el-button，含 size 和 type 属性

### Wrong

```ts
<el-button @click="handleSubmit">提交</el-button>
<el-button @click="handleDelete">删除</el-button>
```

### Right

```ts
<el-button type="primary" size="default" @click="handleSubmit">提交</el-button>
<el-button type="danger" size="default" @click="handleDelete">删除</el-button>
```

---

## 表单校验用 el-form + rules，提交前 validate

### Wrong

```ts
const handleSubmit = async () => {
  if (!form.value.email) return
  if (!form.value.email.includes('@')) return
  await api.save(form.value)
}
```

### Right

```ts
<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
const formRef = ref<FormInstance>()
const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}
const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    await api.save(form.value)
  })
}
</script>
```

---

## 图标从 @element-plus/icons-vue 导入，按需注册

### Wrong

```ts
<template>
  <button><i class="el-icon-edit"></i> 编辑</button>
</template>
```

### Right

```ts
<script setup lang="ts">
import { Edit } from '@element-plus/icons-vue'
</script>
<template>
  <el-button :icon="Edit">编辑</el-button>
</template>
```

---

## loading 状态用 :loading 或 v-loading

### Wrong

```ts
<template>
  <div>{{ loading ? '加载中...' : data }}</div>
  <el-button @click="load">刷新</el-button>
</template>
```

### Right

```ts
<template>
  <div v-loading="loading">{{ data }}</div>
  <el-button :loading="loading" @click="load">刷新</el-button>
</template>
```

---

## 弹窗用 el-dialog，须有 title 和 v-model 控制

### Wrong

```ts
<template>
  <div v-if="visible" class="my-modal">
    <h3>编辑</h3>
    <!-- ... -->
  </div>
</template>
```

### Right

```ts
<template>
  <el-dialog v-model="visible" title="编辑">
    <!-- ... -->
  </el-dialog>
</template>
```

---

*End of examples*