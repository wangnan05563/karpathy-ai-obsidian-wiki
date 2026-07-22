# 多实例配置与状态一致性规范

本文档记录 Karpathy Wiki 项目在多实例配置场景下的编码规范，源于 LLM 预设切换功能的四维度复盘。适用于所有涉及多预设、多账号、多环境配置的开发场景。

## CODING-011 多实例配置隔离原则

**编号**：CODING-011

**内容描述**：
同一系统中存在多个同类配置实例（如多 LLM 预设、多账号、多环境）时，必须按维度独立持久化，不能共享单一存储位置。每个实例的存储 key 必须包含维度标识，确保实例之间的数据互不污染、互不覆盖。

**检查点**：
- localStorage key 是否包含维度标识（如 `prefix:${dimensionKey}`）
- 不同实例的配置是否能独立读取/写入，互不覆盖
- 新增实例时是否影响已有实例的持久化数据

**适用场景**：
- 多 LLM 预设切换（每个预设有独立的 API Key、模型、温度等）
- 多账号体系（每个账号有独立的 token、偏好设置）
- 多环境配置（dev/staging/prod 各自独立的端点、密钥）

**不适用场景**：
- 单一全局配置（如系统级开关、主题模式）
- 只读的常量配置（如预设模板列表本身）

**Bad**：所有预设共享单一 key，切换预设时覆盖彼此的 API Key
```typescript
// 所有预设共享同一个 localStorage key，后切换的预设会覆盖前一个
const saveApiKey = (apiKey: string) => {
  localStorage.setItem('llm_api_key', apiKey);
};

const getApiKey = () => localStorage.getItem('llm_api_key') ?? '';
```

**Good**：按预设维度独立持久化，每个预设拥有独立的存储空间
```typescript
// 按预设 ID 维度独立持久化，预设之间互不污染
const saveApiKey = (presetId: string, apiKey: string) => {
  localStorage.setItem(`llm_api_key:${presetId}`, apiKey);
};

const getApiKey = (presetId: string) =>
  localStorage.getItem(`llm_api_key:${presetId}`) ?? '';
```

## CODING-012 脱敏值回传判断规范

**编号**：CODING-012

**内容描述**：
敏感字段（密码/API Key）以脱敏形式显示时，提交判断必须用正向匹配（startsWith）识别脱敏值，禁止用 truthy 反向匹配。脱敏值通常以 `****` 开头，正向匹配能准确识别"未修改"状态；而 truthy 反向匹配会把空串误判为"未修改"，导致用户清空字段时无法提交。

**检查点**：
- 脱敏值判断是否使用 `value.startsWith('****')` 正向匹配
- 是否存在 `value && !value.startsWith('****')` 这类 truthy 反向匹配
- 用户清空敏感字段（空串）时是否能正确提交空值

**适用场景**：
- 所有包含脱敏字段的表单提交（API Key 编辑、密码修改、Token 更新）
- 后端返回脱敏值供前端回显，前端提交时需判断是否修改

**不适用场景**：
- 非敏感字段（如用户名、备注）的表单提交
- 前端纯展示、无回传需求的场景

**Bad**：truthy 反向匹配，空串被误判为"未修改"
```typescript
// value 为空串时，value && ... 短路返回空串（falsy），进入 else 分支误判为"未修改"
// 导致用户清空 API Key 时无法提交
const handleSubmit = (form: { apiKey: string }) => {
  if (form.apiKey && !form.apiKey.startsWith('****')) {
    // 只有非空且非脱敏值才更新 —— 空串被漏掉
    updateApiKey(form.apiKey);
  }
  // 空串走到这里，被视为"未修改"，无法清空 API Key
};
```

**Good**：正向匹配识别脱敏值，else 分支处理新值和空串
```typescript
// startsWith 正向匹配脱敏值：命中 = 未修改，未命中 = 新值或空串
const handleSubmit = (form: { apiKey: string }) => {
  if (form.apiKey.startsWith('****')) {
    // 脱敏值未修改，不提交该字段
    return;
  }
  // 新值或空串都走到这里，正确处理用户清空操作
  updateApiKey(form.apiKey);
};
```

## CODING-013 前后端状态一致性规范

**编号**：CODING-013

**内容描述**：
前端本地状态（localStorage/内存）如果影响后端行为，变更后必须同步到后端。同步失败不阻断用户操作（try-catch 降级处理），避免前端状态与后端状态脱节导致行为不一致。

**检查点**：
- 前端 localStorage/内存状态变更后，是否调用后端接口同步
- 同步失败时是否使用 try-catch 降级，而非抛错阻断用户操作
- 降级后是否有日志或提示告知用户同步失败

**适用场景**：
- 前端有本地缓存且后端依赖该配置的场景（如当前选中预设、模型偏好）
- 前端切换状态后，后端 SSE 流式响应需要感知该切换

**不适用场景**：
- 纯前端状态（如 UI 偏好设置：侧边栏折叠、列表排序方式）
- 前端缓存仅用于加速展示，后端有独立数据源的场景

**Bad**：前端切换后未同步后端，或同步失败阻断用户操作
```typescript
// 切换预设只更新前端 localStorage，后端仍用旧预设
const switchPreset = (presetId: string) => {
  localStorage.setItem('current_preset', presetId);
  // 缺少后端同步，后端 SSE 流仍按旧预设请求 LLM
};

// 或者同步失败直接抛错，阻断用户切换
const switchPresetThrow = async (presetId: string) => {
  localStorage.setItem('current_preset', presetId);
  await api.updateCurrentPreset(presetId); // 失败时抛错，用户操作被阻断
};
```

**Good**：try-catch 降级，同步失败不阻断用户操作
```typescript
// 前端先更新本地状态，再异步同步后端，失败降级不阻断
const switchPreset = async (presetId: string) => {
  localStorage.setItem('current_preset', presetId);
  try {
    await api.updateCurrentPreset(presetId);
  } catch (err) {
    // 同步失败降级：用户操作不阻断，记录日志提示后续重试
    console.warn('后端预设同步失败，将使用上次同步的值:', err);
  }
};
```

## CODING-014 配置可恢复性规范

**编号**：CODING-014

**内容描述**：
所有可编辑配置必须提供恢复默认值的能力。恢复机制包含五个要素：后端 `defaultConfig()` 函数 + reset 接口 + 前端恢复按钮 + 确认对话框 + 恢复后清除前端持久化。缺一不可，确保用户配置错误时能一键回退到可用状态。

**检查点**：
- 后端是否提供 `defaultConfig()` 函数返回默认配置
- 后端是否提供 reset 接口（如 `POST /api/config/reset`）
- 前端是否有"恢复默认值"按钮
- 点击恢复按钮是否弹出确认对话框（防止误操作）
- 恢复成功后是否清除前端 localStorage 中对应的持久化数据

**适用场景**：
- 所有可编辑的配置页面（LLM 预设配置、主题配置、Vault 路径配置）
- 用户可能配置错误导致系统不可用的场景

**不适用场景**：
- 只读配置（如系统常量、版本号）
- 一次性配置（如初始化向导，无默认值概念）

**Bad**：配置可编辑但无恢复机制，用户配置错误后无法回退
```typescript
// 后端：只有 update 接口，无 defaultConfig() 和 reset 接口
app.post('/api/llm/config', async (req, reply) => {
  await saveConfig(req.body);
  return { success: true };
});

// 前端：只有保存按钮，无恢复默认值入口
<template>
  <el-button @click="handleSave">保存</el-button>
  <!-- 用户配置错误后无法回退到默认值 -->
</template>
```

**Good**：五要素齐备，用户可一键恢复
```typescript
// 后端：提供 defaultConfig() + reset 接口
const defaultConfig = (): LlmConfig => ({
  model: 'gpt-4',
  temperature: 0.7,
  maxTokens: 2000,
});

app.post('/api/llm/config/reset', async (_req, reply) => {
  const config = defaultConfig();
  await saveConfig(config);
  return { success: true, config };
});

// 前端：恢复按钮 + 确认对话框 + 清除持久化
<template>
  <el-button @click="handleReset">恢复默认值</el-button>
</template>

<script setup lang="ts">
const handleReset = async () => {
  // 确认对话框防止误操作
  await ElMessageBox.confirm('确定恢复默认配置？当前配置将被覆盖。', '提示', {
    type: 'warning',
  });
  const { config } = await api.resetLlmConfig();
  // 恢复后清除前端持久化，避免旧值残留
  localStorage.removeItem('llm_config');
  Object.assign(formConfig, config);
};
</script>
```

## CODING-015 同类功能多入口一致性规范

**编号**：CODING-015

**内容描述**：
同类功能如果有多个入口（如 Config.vue 的 applyPreset 和 model.ts 的 switchModel），必须保持状态一致性。多个入口应共享同一存储 key，一个入口更新后另一个入口能读取到最新值，避免不同入口操作后状态脱节。

**检查点**：
- 同类功能的不同入口是否共享同一 localStorage key 或同一 Pinia store
- 一个入口更新状态后，另一个入口读取时是否能看到最新值
- 是否存在不同入口写入不同 key 导致状态分叉的情况

**适用场景**：
- 同一功能在不同页面/组件中都有操作入口（如预设切换在 Config 页面和顶部导航栏都能操作）
- 同一状态被多个组件读取和修改

**不适用场景**：
- 功能独立、无状态共享的入口（如不同页面的独立配置）
- 只读展示入口（只读取不修改状态）

**Bad**：两个入口写入不同 key，状态分叉
```typescript
// Config.vue：applyPreset 写入 'config_preset'
const applyPreset = (presetId: string) => {
  localStorage.setItem('config_preset', presetId);
};

// model.ts：switchModel 写入 'model_preset'，与 Config.vue 不同 key
const switchModel = (presetId: string) => {
  localStorage.setItem('model_preset', presetId);
};

// 后果：Config.vue 切换预设后，model.ts 读取的还是旧值
```

**Good**：共享同一 key，多入口状态一致
```typescript
// 统一存储 key 常量，多入口共享
const CURRENT_PRESET_KEY = 'current_preset';

// Config.vue：applyPreset 写入共享 key
const applyPreset = (presetId: string) => {
  localStorage.setItem(CURRENT_PRESET_KEY, presetId);
};

// model.ts：switchModel 写入同一共享 key
const switchModel = (presetId: string) => {
  localStorage.setItem(CURRENT_PRESET_KEY, presetId);
};

// 两个入口操作后，对方都能读取到最新值
```

## CODING-016 预设/配置集中管理规范

**编号**：CODING-016

**内容描述**：
预设列表（如 LLM 预设）应集中管理在配置文件或常量中，便于校验和更新。修改预设只需改一个地方，避免预设散落在多个文件导致维护困难、新增/删除预设时遗漏。

**检查点**：
- 预设列表是否集中定义在单一文件/常量中
- 业务代码是否通过引用该常量获取预设列表，而非硬编码
- 新增/删除预设时是否只需修改一处

**适用场景**：
- 有预设/模板列表的功能（LLM 预设、提示词模板、导出格式模板）
- 需要对预设进行校验的场景（如校验用户传入的 presetId 是否合法）

**不适用场景**：
- 动态生成的配置列表（如从数据库读取的用户自定义项）
- 一次性使用的临时配置

**Bad**：预设散落在多个文件，新增预设需改多处
```typescript
// Config.vue 中硬编码预设列表
const presets = [
  { id: 'gpt4', name: 'GPT-4' },
  { id: 'claude', name: 'Claude' },
];

// model.ts 中又硬编码了一份
const validPresetIds = ['gpt4', 'claude'];

// 后果：新增预设需改两个文件，容易遗漏
```

**Good**：预设集中管理，修改只需改一处
```typescript
// constants/llm-presets.ts：集中定义预设列表
export const LLM_PRESETS = [
  { id: 'gpt4', name: 'GPT-4', model: 'gpt-4' },
  { id: 'claude', name: 'Claude', model: 'claude-3-opus' },
] as const;

export const VALID_PRESET_IDS = LLM_PRESETS.map(p => p.id);

// Config.vue：引用常量
import { LLM_PRESETS } from '@/constants/llm-presets';
const presets = LLM_PRESETS;

// model.ts：引用同一常量校验
import { VALID_PRESET_IDS } from '@/constants/llm-presets';
const isValidPreset = (id: string) => VALID_PRESET_IDS.includes(id);

// 新增预设只需修改 llm-presets.ts 一处
```
