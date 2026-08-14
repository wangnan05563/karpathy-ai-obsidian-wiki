# Download Endpoint Auth Rule（文件流出端点鉴权门 / fail-closed）

## 触发关键词

下载, download, /api/files/download, 附件, 文件流出, 读端点, requireAuth,
filesReadAuthRequired, 匿名, anonymous, fail-closed, 401, 知识库仅登录可见

## 规则

### DA-1：向外暴露文件内容/下载的 HTTP 端点必须挂载鉴权守卫（fail-closed）

**严重级别**：critical

任何把 vault 用户数据以「文件流 / 下载响应 / 附件」形式向外暴露的 HTTP 端点
（`/api/files/tree`、`/api/files/pages`、`/api/files`、`/api/files/download` 等读端点），
必须在路由注册时挂上 `preHandler` 鉴权守卫（`guards.requireAuth`）。缺失守卫 = fail-open，
匿名用户可直接拖走知识库。

**为什么**：下载功能最初四个读端点未挂 `requireAuth`，仅依赖全局 auth 是否启用；
当 `auth.enabled=true` 且产品要求「知识库仅登录可见」时，漏挂守卫等于把整库公开。
这是 fail-open 型默认错误——安全相关默认值必须向「拒绝」侧回落。

**正确示例**（配置驱动的守卫，缺失配置即 fail-closed）：

```typescript
// opts.filesReadAuthRequired 来自 config.auth.filesReadAuthRequired（默认 false 不破坏既有公开可读性）
// guards.enabled 来自 auth.enabled；仅当「要求读鉴权 且 已启用鉴权」才挂守卫
const readPreHandler =
  opts?.filesReadAuthRequired && guards.enabled ? guards.requireAuth : undefined;
app.get('/api/files/download', { preHandler: readPreHandler }, handler);
```

> 守卫开关（`filesReadAuthRequired`）与守卫实现（`requireAuth`）必须分离：
> 配置缺失 / 显式为 false 时，**不得**让端点「裸奔」，应显式 fail-closed（见 DA-2）。

### DA-2：鉴权配置缺失时默认拒绝（fail-closed 401），而非放行

**严重级别**：critical

安全相关开关的语义必须是「显式开启才放行」，不允许「默认放行、靠配置补齐」。
当 `filesReadAuthRequired` 未设置或环境要求鉴权但守卫未挂载时，请求应得到 `401`
（或等价拒绝），而不是 `200` 漏出文件。

**正确示例**（守卫工厂的失败默认）：

```typescript
// createIsolationGuards：auth.enabled=false（单租户直通）时守卫恒放行；
// 一旦启用鉴权，未带合法凭证即 401，绝不降级为放行。
export function createIsolationGuards(auth: AuthConfig) {
  const enabled = !!auth?.enabled;
  const authGuard: HookHandler = enabled
    ? (req, reply, done) => verifyToken(req, reply, done)
    : (_req, _reply, done) => done(); // 单租户直通
  return { enabled, requireAuth: authGuard };
}
```

> 与 wiki-backend-code-review **BR-097** 一致；与 **BR-094 / CODING-AUTH-REQUEST-FETCH** 协同——
> 前端调这些受保护端点须统一经带鉴权封装（注入 Bearer Token），否则登录态正常也会 401 静默失效。

### DA-3：单租户（auth.enabled=false）直通须显式，不与读鉴权开关混淆

**严重级别**：standard

`auth.enabled=false` 表示单租户本地部署，守卫恒放行是**预期行为**，不视为漏洞；
但「单租户直通」与「读鉴权开关 `filesReadAuthRequired`」是两个正交维度，评审时
不得因「反正单租户」而删除 `filesReadAuthRequired` 的挂载逻辑——多租户部署下它才是安全闸门。

## 检查清单

- [ ] 所有向外暴露文件内容的读端点是否都挂了 `preHandler` 鉴权守卫（或显式 fail-closed 说明）
- [ ] 鉴权开关缺失/未配置时是否向「拒绝（401）」回落，而非默认放行
- [ ] 守卫开关与守卫实现是否分离，开关值是否来自 config（非硬编码）
- [ ] 单租户直通（auth.enabled=false）是否显式处理，且未误删多租户下的读鉴权挂载
- [ ] 前端调用这些端点是否走带鉴权封装（注入 Authorization），避免 401 静默失效
