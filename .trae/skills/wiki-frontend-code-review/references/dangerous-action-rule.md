# Rule Catalog - Dangerous Action

## Scope
- Covers: 破坏性操作的预览模式、危险样式、二次确认、取消不请求、不可撤销提示、审计日志、多表单状态隔离。
- Does NOT cover: 通用 Element Plus 用法（element-plus-rule.md）、配置项隔离（config-isolation-rule.md）、敏感数据存储边界（persistence-boundary-rule.md）。

> 所有可配置参数（dry_run 默认值、danger 类名、确认组件、不可撤销提示等）集中定义在 [config/review-config.md](../config/review-config.md) 的"危险操作审查参数"与"多表单状态管理参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### DA-1: 破坏性操作必须提供 dry_run 预览模式，默认开启

IsUrgent: True
Category: Dangerous Action

### Description

破坏性操作（删除、清理、重置、批量修改等不可逆或难以恢复的动作）必须提供 `dry_run` 预览模式，且默认值为 `true`（对应配置 `dry_run_default`）。`dry_run = true` 时仅返回"将要操作哪些数据"的预览结果，不实际修改任何数据。用户在确认预览结果符合预期后，主动关闭 `dry_run` 再执行真实操作。

不提供预览直接执行的破坏性操作，用户无法预知影响范围（如清理任务可能误删有用数据），造成不可挽回的损失。

### Suggested Fix

请求参数默认携带 `dry_run: true`；预览结果展示后，提供"确认执行"入口，点击后再以 `dry_run: false` 发起真实请求。

> **示例代码**: 参见 [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md)。

### DA-2: 关闭 dry_run 时按钮必须切换为 danger 样式

IsUrgent: True
Category: Dangerous Action

### Description

当 `dry_run` 由 `true` 切换为 `false`（即准备真实执行）时，触发按钮必须切换为危险样式：添加配置 `danger_class` 指定的 CSS 类，或使用 `type="danger"`。视觉强警示让用户在点击前再次意识到"这次会真执行"，避免误以为仍是预览。

仅靠文案区分（如"预览" / "执行"）不足以引起注意，色觉障碍用户尤其依赖样式变化感知状态切换。

### Suggested Fix

按钮 class 或 type 绑定 `dry_run` 状态：

```vue
<el-button
  :type="dryRun ? 'primary' : 'danger'"
  :class="{ [config.danger_class]: !dryRun }"
  @click="handleSubmit"
>
  {{ dryRun ? '预览' : '确认执行' }}
</el-button>
```

> **示例代码**: 参见 [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md)。

### DA-3: 实际执行前必须弹出二次确认对话框

IsUrgent: True
Category: Dangerous Action

### Description

当 `dry_run = false` 准备发起真实破坏性请求时，点击按钮后必须先弹出 `ElMessageBox.confirm`（对应配置 `confirm_component`）二次确认对话框，确认后才发请求。直接发起请求会让用户因误点（如鼠标抖动、回车误触）造成不可逆操作。

确认弹窗类型应使用配置 `confirm_type`（默认 `warning`），文案必须包含不可撤销提示（见 DA-5）。

### Suggested Fix

```ts
try {
  await ElMessageBox.confirm('本次操作将实际执行...且无法撤销。', '执行确认', {
    type: 'warning',
    confirmButtonText: '确认执行',
    cancelButtonText: '取消'
  })
  await api.runAction({ dry_run: false })
} catch {
  // 用户取消，不发起请求
}
```

> **示例代码**: 参见 [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md)。

### DA-4: 取消二次确认不发起任何请求

IsUrgent: True
Category: Dangerous Action

### Description

用户在二次确认对话框点击"取消"或关闭对话框时，必须不发起任何破坏性请求（对应配置 `cancel_no_request = true`）。`ElMessageBox.confirm` 在取消时 reject Promise，须用 `try/catch` 捕获并在 catch 分支直接返回，不得在 catch 中"重试"或"以 dry_run 模式继续发请求"——取消即用户明确中止意图，任何后续请求都是越权。

### Suggested Fix

```ts
const handleSubmit = async () => {
  if (!dryRun.value) {
    try {
      await ElMessageBox.confirm(/* ... */)
    } catch {
      // 用户取消：直接返回，不发任何请求
      return
    }
  }
  await api.runAction({ dry_run: dryRun.value })
}
```

> **示例代码**: 参见 [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md)。

### DA-5: 确认文案必须包含"不可撤销"提示

IsUrgent: True
Category: Dangerous Action

### Description

二次确认对话框的文案必须包含"不可撤销"或同义提示（对应配置 `irreversible_hint_required = true`），明确告知用户该操作无法回退。仅说"确认执行？"不足以让用户意识到严重性，用户可能误以为可以撤销或后端有备份。

提示文案示例："本次操作将实际删除选中的会话记录，且无法撤销。"

### Suggested Fix

确认文案模板：

```ts
const message = `本次操作将实际${actionVerb}选中的${targetName}，且无法撤销。`
```

> **示例代码**: 参见 [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md)。

### DA-6: 实际执行后必须记录审计日志

IsUrgent: False
Category: Dangerous Action

### Description

破坏性操作实际执行（`dry_run = false`）成功后，必须记录审计日志：操作类型、操作目标、操作人、时间戳、操作参数。审计日志用于事后追溯（如用户投诉数据丢失、合规审计），仅在出错时打印 console 日志无法满足追溯需求——浏览器日志会在刷新后丢失。

审计日志的存储位置与格式由后端定义，前端只需在请求成功后调用日志接口或确保请求本身携带可追溯字段。

### Suggested Fix

```ts
const res = await api.runAction({ dry_run: false })
if (!res.error) {
  // 实际执行成功后记录审计日志
  await api.logAction({
    action: 'cleanup',
    target: res.affected,
    timestamp: Date.now()
  })
}
```

> **示例代码**: 参见 [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md)。

### DA-7: 多表单场景必须按 key 独立管理 loading 与 result 状态

IsUrgent: True
Category: Dangerous Action

### Description

同一页面存在多个独立破坏性表单（如系统清理模块的 4 个清理表单：过期会话、孤儿节点、无效引用、冗余缓存）时，每个表单的 `loading` 与 `result` 状态必须按 key 独立管理（对应配置 `multi_form_pattern = Record<key, FormState>`、`independent_loading`、`independent_result`）。

共用单一 `loading` / `result` 会导致：
- 表单 A 提交时表单 B 的按钮也进入 loading，用户误以为 B 也在执行
- 表单 A 的结果覆盖表单 B 之前的结果，B 区域显示 A 的内容
- 多个表单并发提交时状态互相覆盖，无法判断哪个表单正在执行

`loading` 用 `reactive<Record<Key, boolean>>`，`result` 用 `ref<Record<Key, Result | null>>`。表单提交时必须先重置对应 key 的 result（对应配置 `reset_on_submit = true`），避免显示陈旧结果。

### Suggested Fix

```ts
type CleanKey = 'expired' | 'orphan' | 'broken' | 'redundant'
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

> **示例代码**: 参见 [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md)。

### DA-8: 破坏性按钮必须有 loading / disabled / confirm 至少其一的防护

IsUrgent: True
Category: Dangerous Action

### Description

启动、停止、保存、删除、清除、重置等破坏性按钮（文案匹配配置 `destructive_button_patterns`）在点击后会触发实际的后端操作或不可逆状态变更，必须有显式防护机制，避免被自动测试脚本、误点、回车误触触发。

复盘 Tunnel.vue 等控制类页面时发现：启动/停止按钮未设置 `loading` 状态、未禁用、也无二次确认，自动化测试脚本在表单填写后顺次点击页面所有按钮，触发了真实的隧道启停操作；保存按钮未禁用，测试脚本点击后把测试数据写入后端 config.json。

满足以下任一防护即视为合规（对应配置 `required_guards`，至少满足其一）：

1. **loading**：按钮 `:loading="submitting"` 绑定请求状态，请求期间按钮自动禁用，防止重复点击与测试脚本连续点击。
2. **disabled**：按钮 `:disabled="!formValid"` 绑定前置条件，前置条件不满足时按钮不可点击（如必填字段为空、未选择目标、未勾选确认复选框）。
3. **confirm**：按钮 `@click` 处理函数内先调用 `ElMessageBox.confirm` 二次确认，用户取消后不发起请求（与 DA-3 一致）。

无任何防护的破坏性按钮在自动化测试、E2E 回归、键盘导航场景下极易被误触发，造成真实业务影响（如生产环境启停服务、覆盖配置、删除数据）。

### Judgment Logic

1. 扫描 `.vue` 文件的 `<template>` 段，提取所有 `<el-button>` 或原生 `<button>` 的文本内容。
2. 对每个按钮，若文本匹配 `destructive_button_patterns` 中的任一模式（如 `启动|停止|保存|删除|清除|重置`），标记为破坏性按钮。
3. 对每个破坏性按钮，检查是否满足 `required_guards` 中的至少一项：
   - `loading`：按钮元素是否绑定 `:loading="..."` 属性。
   - `disabled`：按钮元素是否绑定 `:disabled="..."` 属性。
   - `confirm`：按钮的 `@click` 处理函数中是否调用 `ElMessageBox.confirm`（或同义确认组件）。
4. 任一防护都未满足即告警，列出按钮文案、文件位置、缺失的防护类型。

### Applicable Scenarios

- 配置类页面（保存、恢复默认、重置）。
- 控制类页面（启动、停止、重启服务/任务）。
- 数据操作类页面（删除、清除、批量操作）。
- 任何会被自动化测试（Playwright / Cypress / Selenium）或 E2E 回归触碰到的页面。

### Non-Applicable Scenarios

- 纯导航/查询类按钮（如"刷新"、"查询"、"切换 Tab"），不触发实际状态变更。
- 已通过 DA-1 ~ DA-5 完整防护的破坏性操作（loading + confirm + danger 样式齐备，自然满足本规则）。
- 内部工具页面且明确不接入自动化测试的按钮（应在配置豁免清单中显式列出）。

### Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `destructive_button_patterns` | `启动\|停止\|保存\|删除\|清除\|重置` | 破坏性按钮文案匹配模式（正则 alternation） |
| `required_guards` | `['loading', 'disabled', 'confirm']` | 破坏性按钮必须满足的防护类型（至少其一） |
| `guard_min_match` | `1` | 至少需满足的防护数量 |
| `destructive_button_whitelist` | `[]` | 豁免按钮文案清单（如纯前端状态切换按钮） |

### Suggested Fix

```vue
<!-- ❌ 无防护的破坏性按钮 -->
<el-button @click="startService">启动</el-button>
<el-button @click="stopService">停止</el-button>
<el-button @click="saveConfig">保存</el-button>

<!-- ✅ loading + disabled 双重防护 -->
<el-button
  :loading="starting"
  :disabled="!configValid"
  @click="startService"
>启动</el-button>

<!-- ✅ confirm 二次确认防护 -->
<el-button @click="handleStop">停止</el-button>

<script setup lang="ts">
const starting = ref(false)
async function handleStop() {
  try {
    await ElMessageBox.confirm('本次操作将停止服务，且可能中断进行中的任务。', '停止确认', {
      type: 'warning',
      confirmButtonText: '确认停止',
      cancelButtonText: '取消'
    })
    await stopService()
  } catch {
    // 用户取消，不发请求
  }
}
</script>
```

> **示例代码**: 参见 [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md)。

## Checklist
- [ ] 破坏性操作提供 `dry_run` 预览模式，默认 `true`
- [ ] 关闭 `dry_run` 时按钮切换为 danger 样式
- [ ] 实际执行前弹出 `ElMessageBox.confirm` 二次确认
- [ ] 取消确认不发起任何请求
- [ ] 确认文案包含"不可撤销"提示
- [ ] 实际执行后记录审计日志
- [ ] 多表单场景按 key 独立管理 loading 与 result，提交时重置对应 result
- [ ] 破坏性按钮（启动/停止/保存/删除/清除/重置）满足 loading / disabled / confirm 至少其一的防护
