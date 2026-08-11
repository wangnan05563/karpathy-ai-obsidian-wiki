# Rule Catalog — 异步操作 loading 复位 (CODING-AUTH-LOADING-RESET)

通用前端编码规范：登录、提交、请求等进入"等待态"的交互，其 `loading` / `submitting` 状态必须在 `try/finally`（或 Promise `.finally`）中复位，无论成功、失败还是超时。遗漏复位会使按钮永久灰显、一直显示「登录中/提交中」，用户无法重试。本规则是前端审查条目 `wiki-frontend-code-review` FR-083 的上位规范。

> 复盘来源：登录视图 `handler` 在 `await` 登录请求外层无 `finally` 复位 `loading`，一旦请求抛错或超时，按钮持续「登录中」灰显，用户只能刷新页面。修正：所有进入等待态的 handler 用 `try { ... } finally { loading = false }` 包住。

## Scope

- Covers: 任何设置 `loading=true` / `submitting=true` 后发起异步请求、且需复位的交互（登录、注册、保存配置、发送消息、上传等）。
- Does NOT cover: 纯展示 loading（骨架屏）由生命周期钩子自动管理；无禁用态切换的纯查询。

## Rules

### CODING-AUTH-LOADING-RESET-1: 等待态必须在 finally 复位

IsUrgent: True（严重）
Category: 异步可靠性 / 前端

#### Description

设置 `loading=true` 后，必须在 `finally` 中置 `loading=false`，覆盖成功、失败、超时、abort 全部路径。禁止只在 `try` 成功分支复位而 `catch` 遗漏。

#### Suggested Fix

```ts
// ✅ 无论如何都复位 loading
async function onLogin() {
  loading.value = true
  try {
    await store.login(form)
    router.push('/')
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    loading.value = false // 成功/失败/超时均复位
  }
}
```

### CODING-AUTH-LOADING-RESET-2: 复位不得被提前 return 跳过

IsUrgent: False
Category: 异步可靠性 / 前端

#### Description

`loading` 复位逻辑不得依赖函数末尾的线性执行——若存在提前 `return` / `throw` 分支，必须仍在 `finally` 覆盖。优先用 `try/finally` 而非分散的 `loading=false`。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `auth_loading_reset.enabled` | `true` | 启用异步 loading 复位审查 |
| `auth_loading_reset.set_pattern` | `loading\s*=\s*true|submitting\s*=\s*true` | 进入等待态的赋值模式 |
| `auth_loading_reset.reset_required_in` | `finally` | 复位语句须出现在 finally 或 .finally 中 |
| `auth_loading_reset.severity` | `major` | 遗漏复位导致按钮卡死的违规级别 |
