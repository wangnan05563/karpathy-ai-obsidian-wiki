# config-isolation-rule - Code Examples

> This file contains Wrong/Right code examples extracted from [config-isolation-rule.md](../config-isolation-rule.md).
> Load on demand when you need to reference examples or generate fix code.

---

## 多实例配置必须按维度独立持久化

### Wrong

```ts
// 所有预设共用同一个 key，切换预设时覆盖上一预设的配置
const saveConfig = (presetKey: string, config: LlmConfig) => {
  localStorage.setItem('llmPresetConfig', JSON.stringify(config))
}
const loadConfig = (presetKey: string): LlmConfig => {
  return JSON.parse(localStorage.getItem('llmPresetConfig') || '{}')
}
```

### Right

```ts
// 每个预设独立存储，切换时从对应 key 读取返显
const saveConfig = (presetKey: string, config: LlmConfig) => {
  localStorage.setItem(`llmPresetConfig:${presetKey}`, JSON.stringify(config))
}
const loadConfig = (presetKey: string): LlmConfig => {
  return JSON.parse(localStorage.getItem(`llmPresetConfig:${presetKey}`) || '{}')
}
```

---

## 脱敏值回传判断必须用正向匹配

### Wrong

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

### Right

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

---

## 前端状态变更须同步后端

### Wrong

```ts
const handlePresetSwitch = (presetKey: string) => {
  // 只更新前端表单，不调用后端 API，刷新后状态丢失
  currentPreset.value = presetKey
  Object.assign(form, loadConfig(presetKey))
}
```

### Right

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

---

## 可编辑配置须提供恢复默认值能力

### Wrong

```ts
<template>
  <!-- 配置页面只有保存按钮，没有恢复功能 -->
  <el-button type="primary" @click="handleSave">保存</el-button>
</template>
```

### Right

```ts
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

---

## 同类功能多入口须共享存储

### Wrong

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

### Right

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

---

*End of examples*