# Rule Catalog - Sensitive Field Display

## Scope
- Covers: 表单中敏感字段（API Key / authtoken / password / secret / token 等）的回显策略——必须使用脱敏值或空输入框占位，禁止明文回显。
- Does NOT cover: 脱敏值回传判断逻辑（config-isolation-rule.md）、敏感数据存储边界（persistence-boundary-rule.md）、登录认证流程的密码字段（属认证模块专有规则）。

> 所有可配置参数（敏感字段模式、展示策略、占位提示文案等）集中定义在 [config/review-config.md](../config/review-config.md) 的"敏感字段展示审查参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### SF-1: 敏感字段回显必须使用脱敏值或空输入框，禁止明文回显

IsUrgent: True
Category: Sensitive Field Display

### Description

表单回显敏感字段（API Key、authtoken、password、secret、token 等凭证类字段）时，必须采用以下两种展示策略之一（对应配置 `display_strategy`，默认 `masked_placeholder`）：

1. **masked**：输入框回显后端返回的脱敏值（如 `****xxxx`、`••••••`），用户看到的是掩码字符，原始值不可见。
2. **masked_placeholder**：输入框保持空，通过 `placeholder` 提示"留空不修改"（或同义提示），表示"不修改原值"——用户留空提交时后端跳过该字段更新，用户输入新值时表示主动覆盖。

禁止从后端拉取明文凭证直接绑定到输入框 `value`，原因：
- 浏览器 DOM 与 Vue reactive 状态中明文存储凭证，XSS 攻击者可通过 `document.querySelector` 或 Vue DevTools 直接读取。
- 屏幕共享、截图、旁观场景下明文凭证泄露。
- 浏览器表单自动填充历史记录会缓存明文凭证到本地数据库。

复盘 Tunnel.vue 的 authtoken 字段时发现：表单加载时直接将后端返回的明文 authtoken 绑定到 `<el-input v-model="form.authtoken">`，导致：
- 输入框可见明文，旁观/截图即泄露。
- Vue DevTools 中 reactive 状态明文可见。
- 浏览器自动填充缓存明文。

### Judgment Logic

1. 扫描 `.vue` 文件的 `<template>` 段，提取所有 `<el-input>` / `<input>` 元素及其绑定属性。
2. 对每个输入框，若以下任一条件命中，标记为敏感字段输入框：
   - `name` 属性或 `v-model` 变量名匹配 `sensitive_field_patterns`（如 `key|token|secret|password|authtoken`）。
   - `type="password"`。
   - `prop` 属性（Element Plus 表单字段）匹配 `sensitive_field_patterns`。
3. 对每个敏感字段输入框，按 `display_strategy` 检查：
   - `masked`：`v-model` 绑定的初始值是否为脱敏格式（如以 `****` 开头，或全部为掩码字符）。若初始值是明文（含完整凭证字符串），告警"敏感字段明文回显"。
   - `masked_placeholder`：`placeholder` 是否包含"留空不修改"或同义提示；`v-model` 绑定的初始值是否为空字符串。若初始值非空且为明文，告警。
4. 命中即输出告警，列出字段名、文件位置、当前展示策略、建议的修复方式。

### Applicable Scenarios

- 配置类表单（API Key、authtoken、access token、secret key 等凭证字段）。
- 账号设置页（密码、二次验证密钥）。
- 第三方集成配置（OAuth client secret、webhook secret）。
- 任何从后端拉取后回显到输入框的凭证类字段。

### Non-Applicable Scenarios

- 登录/注册/修改密码流程的"新密码输入框"（用户主动输入，非后端回显）。
- 仅前端使用的非敏感字段（如用户昵称、主题偏好）。
- 已通过浏览器 Password Manager 加密存储的密码字段（属浏览器层职责）。

### Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `sensitive_field_patterns` | `key\|token\|secret\|password\|authtoken` | 敏感字段名匹配模式（正则 alternation，大小写不敏感） |
| `display_strategy` | `masked_placeholder` | 敏感字段展示策略：`masked`（脱敏值回显）/ `masked_placeholder`（空输入框 + 提示） |
| `masked_prefix` | `****` | `masked` 策略下脱敏值前缀（用于识别"已是脱敏值"避免二次处理） |
| `placeholder_hint` | `留空不修改` | `masked_placeholder` 策略下输入框 placeholder 必须包含的提示关键词 |
| `sensitive_field_whitelist` | `[]` | 豁免字段名清单（如内部测试用字段） |

### Example

```vue
<!-- ❌ 明文回显 authtoken -->
<script setup lang="ts">
const form = reactive({
  authtoken: '',  // 从后端加载后会被赋值为明文
})
onMounted(async () => {
  const config = await api.getTunnelConfig()
  form.authtoken = config.authtoken  // ❌ 明文赋值
})
</script>

<template>
  <el-input v-model="form.authtoken" />
</template>
```

```vue
<!-- ✅ masked_placeholder 策略：空输入框 + 留空不修改提示 -->
<script setup lang="ts">
const form = reactive({
  authtoken: '',  // 留空，不回显
})
</script>

<template>
  <el-input
    v-model="form.authtoken"
    type="password"
    placeholder="留空不修改，输入新值则覆盖"
    show-password
  />
</template>
```

```vue
<!-- ✅ masked 策略：回显后端脱敏值 ****xxxx -->
<script setup lang="ts">
const form = reactive({
  authtoken: '',  // 从后端加载脱敏值
})
onMounted(async () => {
  const config = await api.getTunnelConfig()
  // 后端返回 ****xxxx 格式的脱敏值
  form.authtoken = config.authtokenMasked
})
</script>

<template>
  <el-input v-model="form.authtoken" type="password" show-password />
</template>
```

### Checklist

- [ ] 敏感字段输入框（API Key / authtoken / password / secret / token）未明文回显后端返回的原始值
- [ ] `masked_placeholder` 策略：输入框初始为空，`placeholder` 包含"留空不修改"或同义提示
- [ ] `masked` 策略：输入框初始值为脱敏格式（如 `****xxxx`），非明文
- [ ] 敏感字段输入框使用 `type="password"` 或 `show-password` 隐藏字符
- [ ] 提交时按 `masked_prefix` 判断"未修改"分支跳过该字段（与 config-isolation-rule.md 一致）
