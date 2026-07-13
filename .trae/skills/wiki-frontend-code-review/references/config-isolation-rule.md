# Rule Catalog — Config Isolation

> 通用规则文件，多实例配置维度标识、脱敏值前缀、恢复默认值接口路径、破坏性按钮白名单等具体数值以 `config/review-config.md` 为准。

## 多实例配置必须按维度独立持久化

IsUrgent: True
Category: Config Isolation

### Description

当存在多实例配置（如多套 LLM 预设、多账号）时，`localStorage` 必须按维度标识（预设 key、账号 ID 等）独立存储，避免不同实例共用同一个 key 在切换时互相覆盖。共用 key 会导致切换后丢失上一实例的修改，且返显时拿到的是最后写入实例的值而非当前实例的真实配置。

### Suggested Fix

为每个实例拼接独立 key（如 `llmPresetConfig:${presetKey}`），切换实例时从对应 key 读取返显，保存时写入对应 key。

Wrong:

```ts
// 所有预设共用同一个 key，切换预设时覆盖上一预设的配置
const saveConfig = (presetKey: string, config: LlmConfig) => {
  localStorage.setItem('llmPresetConfig', JSON.stringify(config))
}
const loadConfig = (presetKey: string): LlmConfig => {
  return JSON.parse(localStorage.getItem('llmPresetConfig') || '{}')
}
```

Right:

```ts
// 每个预设独立存储，切换时从对应 key 读取返显
const saveConfig = (presetKey: string, config: LlmConfig) => {
  localStorage.setItem(`llmPresetConfig:${presetKey}`, JSON.stringify(config))
}
const loadConfig = (presetKey: string): LlmConfig => {
  return JSON.parse(localStorage.getItem(`llmPresetConfig:${presetKey}`) || '{}')
}
```

## 脱敏值回传判断必须用正向匹配

IsUrgent: True
Category: Config Isolation

### Description

表单提交时，对脱敏值（如以 `****` 开头的 apiKey）的"未修改"判断必须用正向匹配（`value.startsWith('****')`）。若用反向匹配（`value && !value.startsWith('****')`），当用户清空输入框（空串）时会被 `value &&` 短路为 falsy，误判为"未修改"，导致空串无法覆盖原值，用户无法主动清空敏感字段。

### Suggested Fix

用 `value.startsWith('****')` 判断为"未修改"分支（跳过该字段），`else` 分支处理新值（含空串，表示用户主动清空）。

Wrong:

```ts
const handleSubmit = async (form: LlmConfigForm) => {
  const payload: Partial<LlmConfig> = { ...form }
  // 空串被 value && 短路为 falsy，误判为"未修改"，用户无法清空 apiKey
  if (form.apiKey && !form.apiKey.startsWith('****')) {
    payload.apiKey = form.apiKey
  } else {
    delete payload.apiKey
  }
  await api.save(payload)
}
```

Right:

```ts
const handleSubmit = async (form: LlmConfigForm) => {
  const payload: Partial<LlmConfig> = { ...form }
  // 正向匹配：以 **** 开头视为未修改，跳过；else 分支处理新值（含空串表示主动清空）
  if (form.apiKey.startsWith('****')) {
    delete payload.apiKey
  }
  await api.save(payload)
}
```

## 前端状态变更须同步后端

IsUrgent: True
Category: Config Isolation

### Description

涉及持久化配置的前端状态变更（如切换预设、修改默认参数）必须调用后端同步接口，且同步失败须有降级处理（try-catch + ElMessage 提示 + 回滚前端状态）。仅更新前端表单而不调用后端 API 会导致刷新后状态丢失、多端不一致。

### Suggested Fix

在状态变更后异步调用后端 PUT/POST 接口，用 try-catch 包裹，失败时回滚前端状态并提示用户。

Wrong:

```ts
const handlePresetSwitch = (presetKey: string) => {
  // 只更新前端表单，不调用后端 API，刷新后状态丢失
  currentPreset.value = presetKey
  Object.assign(form, loadConfig(presetKey))
}
```

Right:

```ts
import { ElMessage } from 'element-plus'

const handlePresetSwitch = async (presetKey: string) => {
  const prevPreset = currentPreset.value
  currentPreset.value = presetKey
  Object.assign(form, loadConfig(presetKey))
  try {
    // 切换预设后异步调用后端 PUT 接口同步
    await api.updateActivePreset({ presetKey })
  } catch (e) {
    // 同步失败降级：回滚前端状态并提示用户
    currentPreset.value = prevPreset
    Object.assign(form, loadConfig(prevPreset))
    ElMessage.error('预设切换同步失败，已回滚')
  }
}
```

## 可编辑配置须提供恢复默认值能力

IsUrgent: False
Category: Config Isolation

### Description

可编辑的配置页面须提供"恢复初始配置"按钮，并通过 `ElMessageBox.confirm` 二次确认后再执行恢复，避免用户误触丢失自定义配置。仅提供保存按钮而无恢复入口，会让用户在多次修改后无法回到已知良好的初始状态。

### Suggested Fix

在配置页面操作区添加"恢复初始配置"按钮（`type="danger"`），点击后弹出 `ElMessageBox.confirm` 确认对话框，确认后调用恢复默认值接口并刷新表单。

Wrong:

```vue
<template>
  <!-- 配置页面只有保存按钮，没有恢复功能 -->
  <el-button type="primary" @click="handleSave">保存</el-button>
</template>
```

Right:

```vue
<template>
  <el-button type="primary" @click="handleSave">保存</el-button>
  <!-- 有"恢复初始配置"按钮，配合 ElMessageBox.confirm 二次确认 -->
  <el-button type="danger" @click="handleReset">恢复初始配置</el-button>
</template>

<script setup lang="ts">
import { ElMessageBox, ElMessage } from 'element-plus'

const handleReset = async () => {
  try {
    await ElMessageBox.confirm('确认恢复初始配置？当前自定义配置将被覆盖，且无法撤销。', '恢复确认', {
      type: 'warning',
      confirmButtonText: '确认恢复',
      cancelButtonText: '取消'
    })
    await api.resetConfig()
    Object.assign(form, await api.loadConfig())
    ElMessage.success('已恢复初始配置')
  } catch {
    // 用户取消，无需处理
  }
}
</script>
```

## 同类功能多入口须共享存储

IsUrgent: False
Category: Config Isolation

### Description

同类功能若有多个入口（如 `Config.vue` 配置页与 `model.ts` 运行时模型加载器都需要读取同一预设的 apiKey），必须共享同一 `localStorage` key，否则会出现"配置页保存的值在运行时读不到"的不一致问题。若历史原因导致 key 命名不同，保存时须同步写入两个 key，保持一致性。

### Suggested Fix

统一多入口的 localStorage key 命名；若无法立即统一，在保存时同步写入两个 key，并在读取时优先使用规范 key。

Wrong:

```ts
// Config.vue 用 llmPresetConfig:${key}
const saveApiKey = (key: string, apiKey: string) => {
  localStorage.setItem(`llmPresetConfig:${key}`, JSON.stringify({ apiKey }))
}

// model.ts 用 apiKey:${key}，互不读取，运行时拿不到配置页保存的值
const loadApiKey = (key: string): string => {
  return JSON.parse(localStorage.getItem(`apiKey:${key}`) || '{}').apiKey
}
```

Right:

```ts
// 统一 key 命名，多入口共享存储
const PRESET_KEY = (key: string) => `llmPresetConfig:${key}`

// Config.vue 保存
const saveApiKey = (key: string, apiKey: string) => {
  localStorage.setItem(PRESET_KEY(key), JSON.stringify({ apiKey }))
}

// model.ts 读取（同一 key）
const loadApiKey = (key: string): string => {
  return JSON.parse(localStorage.getItem(PRESET_KEY(key)) || '{}').apiKey
}
```
