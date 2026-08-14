# Download Endpoint Auth Rule（文件流出端点鉴权门 / fail-closed）

## 触发关键词

下载, download, /api/files/download, 附件, 文件流出, 读端点, requireAuth,
filesReadAuthRequired, 匿名, fail-closed, 401, 知识库仅登录可见, preHandler

## 规则

### BR-097-1（critical）：向外暴露文件内容的读端点必须挂鉴权守卫（fail-closed）

`/api/files/tree`、`/api/files/pages`、`/api/files`、`/api/files/download` 等把 vault 用户数据
以文件流/下载响应向外暴露的端点，注册时须挂 `preHandler: guards.requireAuth`。
缺失守卫 = fail-open，匿名用户可直接拖走知识库。

### BR-097-2（critical）：鉴权开关缺失时默认拒绝（401），而非默认放行

安全开关语义须「显式开启才放行」。`filesReadAuthRequired` 未设置或守卫未挂载时，
请求应得 `401`（或等价拒绝），不允许「默认放行、靠配置补齐」。

### BR-097-3（standard）：单租户直通（auth.enabled=false）须显式，不与读鉴权开关混淆

`auth.enabled=false` 时守卫恒放行是预期（单租户本地），但不得因此删除
`filesReadAuthRequired` 的挂载逻辑——多租户下它才是安全闸门。两维度正交，评审不得误删。

> 对应 wiki-code-dev **CODING-DOWNLOAD-AUTH / DA-1~DA-3**；与 **BR-094 / CODING-AUTH-REQUEST-FETCH**
> 协同（前端须走带鉴权封装注入 Bearer，否则 401 静默失效）；与 **FR-084** 共享「受保护端点禁裸 fetch」语义。

## 检查清单

- [ ] 所有文件流出读端点是否挂 `preHandler` 鉴权守卫（或显式 fail-closed 说明）
- [ ] 鉴权开关缺失/未配置时是否向拒绝（401）回落，非默认放行
- [ ] 守卫开关与实现是否分离，开关值是否来自 config（非硬编码）
- [ ] 单租户直通是否显式处理且未误删多租户读鉴权挂载
- [ ] 前端调这些端点是否走带鉴权封装（注入 Authorization），避 401 静默失效
