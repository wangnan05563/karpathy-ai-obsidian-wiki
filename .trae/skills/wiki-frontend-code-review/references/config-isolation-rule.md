# Rule Catalog — Config Isolation

配置隔离审查规则：确保多实例配置按维度独立持久化，防止状态串扰与配置泄露。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

## 多实例配置必须按维度独立持久化

IsUrgent: True
Category: Config Isolation

### Description

当存在多实例配置（如多套 LLM 预设、多账号）时，`localStorage` 必须按维度标识（预设 key、账号 ID 等）独立存储，避免不同实例共用同一个 key 在切换时互相覆盖。共用 key 会导致切换后丢失上一实例的修改，且返显时拿到的是最后写入实例的值而非当前实例的真实配置。

### Suggested Fix

为每个实例拼接独立 key（如 `llmPresetConfig:${presetKey}`），切换实例时从对应 key 读取返显，保存时写入对应 key。

> **示例代码**: 参见 [examples/config-isolation-rule-examples.md](examples/config-isolation-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 脱敏值回传判断必须用正向匹配

IsUrgent: True
Category: Config Isolation

### Description

表单提交时，对脱敏值（如以 `****` 开头的 apiKey）的"未修改"判断必须用正向匹配（`value.startsWith('****')`）。若用反向匹配（`value && !value.startsWith('****')`），当用户清空输入框（空串）时会被 `value &&` 短路为 falsy，误判为"未修改"，导致空串无法覆盖原值，用户无法主动清空敏感字段。

### Suggested Fix

用 `value.startsWith('****')` 判断为"未修改"分支（跳过该字段），`else` 分支处理新值（含空串，表示用户主动清空）。

> **示例代码**: 参见 [examples/config-isolation-rule-examples.md](examples/config-isolation-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 前端状态变更须同步后端

IsUrgent: True
Category: Config Isolation

### Description

涉及持久化配置的前端状态变更（如切换预设、修改默认参数）必须调用后端同步接口，且同步失败须有降级处理（try-catch + ElMessage 提示 + 回滚前端状态）。仅更新前端表单而不调用后端 API 会导致刷新后状态丢失、多端不一致。

### Suggested Fix

在状态变更后异步调用后端 PUT/POST 接口，用 try-catch 包裹，失败时回滚前端状态并提示用户。

> **示例代码**: 参见 [examples/config-isolation-rule-examples.md](examples/config-isolation-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 可编辑配置须提供恢复默认值能力

IsUrgent: False
Category: Config Isolation

### Description

可编辑的配置页面须提供"恢复初始配置"按钮，并通过 `ElMessageBox.confirm` 二次确认后再执行恢复，避免用户误触丢失自定义配置。仅提供保存按钮而无恢复入口，会让用户在多次修改后无法回到已知良好的初始状态。

### Suggested Fix

在配置页面操作区添加"恢复初始配置"按钮（`type="danger"`），点击后弹出 `ElMessageBox.confirm` 确认对话框，确认后调用恢复默认值接口并刷新表单。

> **示例代码**: 参见 [examples/config-isolation-rule-examples.md](examples/config-isolation-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 同类功能多入口须共享存储

IsUrgent: False
Category: Config Isolation

### Description

同类功能若有多个入口（如 `Config.vue` 配置页与 `model.ts` 运行时模型加载器都需要读取同一预设的 apiKey），必须共享同一 `localStorage` key，否则会出现"配置页保存的值在运行时读不到"的不一致问题。若历史原因导致 key 命名不同，保存时须同步写入两个 key，保持一致性。

### Suggested Fix

统一多入口的 localStorage key 命名；若无法立即统一，在保存时同步写入两个 key，并在读取时优先使用规范 key。

> **示例代码**: 参见 [examples/config-isolation-rule-examples.md](examples/config-isolation-rule-examples.md)。

## 预设列表必须从后端 API 获取，禁止前端硬编码

IsUrgent: True
Category: Config Isolation

### Description

预设列表（LLM 预设、配置模板等）必须通过后端 API 获取，禁止在前端代码中硬编码预设数组。前端硬编码预设列表会导致前后端不一致——后端新增预设时前端无法展示，需同步修改前端代码再部署。

此规则是 ES-9（多实例数据集中管理）在预设场景下的具体应用。预设作为动态配置数据，其权威源必须是后端 API 或配置文件，前端仅做展示与交互。

### Suggested Fix

```typescript
// ❌ 前端硬编码预设列表
const PRESETS = [
  { key: 'openai', label: 'OpenAI', ... },
  { key: 'deepseek', label: 'DeepSeek', ... },
];

// ✅ 通过 API 获取预设
const resp = await fetch('/api/ai/presets');
const data = await resp.json();
const presets = data.presets;
```

预设类型须与后端返回结构一致，使用 `types.ts` 中定义的接口。

> **示例代码**: 参见 [examples/config-isolation-rule-examples.md](examples/config-isolation-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。
