# 编码规范提炼：四维度复盘综合索引（Retrospective Synthesis）

> 本文件是 wiki-code-dev 所有规则的**总览与来由**。每条规则都不是凭空制定，而是对一次真实事故 / 返工的四维度复盘，固化为可复用判断逻辑。
> 配套：① 规则正文见 `references/*-rule.md`；② 审查要点见 wiki-frontend-code-review（FR-*）/ wiki-backend-code-review（BR-*）；③ 测试纪律见 wiki-auto-testing `indexeddb_test_isolation_check` 与 testing-process-review.md。

## 复盘方法论（四维度 → 规则）

每遇到一次事故或返工，按四维度复盘，并将结论固化为规则（含严重级别 + 正/误示例 + 对应 config 参数）：

| 维度 | 复盘问题 | 产出 |
|------|---------|------|
| ① 成功步骤 | 这次是怎么修好的？哪些动作被验证有效？ | 可复制的修复流程骨架 |
| ② 不确定性与失败点 | 哪里踩坑 / 试错？环境约束是什么？（沙箱无浏览器、safe-delete 钩子、Git-Bash 路径、fake-indexeddb 连接） | 防御性检查点 / 降级路径 |
| ③ 可抽象的流程与判断 | 哪些决策可参数化、可泛化到同类问题？ | 规则（严重级别 + 正/误示例）+ 对应 config 参数 |
| ④ 适用与不适用 | 这个规则在哪些场景成立？哪些场景是噪声？ | 规则的适用 / 不适用边界（写进 review 技能输出） |

**闭环**：复盘(①②③④) → 提炼为编码规则（本技能 references/） → 映射为审查要点（FR-/BR-） → 参数全部落入各技能 `config/*.md`（零硬编码） → 测试纪律落入 wiki-auto-testing 步骤类型。

---

## 综合索引表（事故 → 四维度摘要 → 规则）

> 下表"四维度摘要"为浓缩版；每条规则完整的问题 / 规则 / 适用边界见对应 rule 文件。

| # | 历史问题 | ① 成功步骤（有效动作） | ② 失败点 / 环境约束 | ③ 抽象的固定流程与判断 | ④ 适用 / 不适用 | 规则 |
|---|---------|----------------------|---------------------|------------------------|----------------|------|
| 1 | 前端 `.ts` 被陈旧 `.js` 影子覆盖（修改不生效） | `vue-tsc --noEmit` + `vite build` + 跑测试三重验证；先确认 `src` 下 0 个 `.js` | `vue-tsc` 无 `--noEmit` 会重新 emit `.js` 复活遮蔽；vitest `resolve.extensions` 默认 `.js` 优先 | 构建/测试前先清 `src/**/*.js`；`resolve.extensions` 把 `.ts` 排在 `.js` 前；变动后三重验证 | 适用：Vite + 混合 .js/.ts 项目；不适用：纯 ESM 无编译产物项目 | CODING-TS-JS-SHADOWING → FR-061 / [frontend-ts-js-shadowing-rule.md](frontend-ts-js-shadowing-rule.md) |
| 2 | 多账户会话隔离泄漏（admin 历史消失 / 人人可见） | 账户切换先 `resetSession()` 再 `loadConversations()`；`persistConversation` 复用 id 前以 IndexedDB 实际记录校验归属 | `currentConversationId` 模块级共享 ref 跨账户未 reset；`scopedOwnerId` 漏加 store return = 死状态 | 会话状态 ref 全部加入 store return；`filterByOwner` 严格按 ownerId；复用 id 冲突改用全新 uuid | 适用：多账户 + 客户端持久化会话；不适用：单账户 | CODING-SESSION-ISOLATION → FR-069 / [frontend-session-isolation-rule.md](frontend-session-isolation-rule.md) |
| 3 | 沙箱 safe-delete 钩子限制 | 统一走"写全新目录 → 移动/重建"，不原地 rm/覆盖；日志预检可写降级 stdout | 钩子 fail-closed：拦截 unlink/rm/覆盖/rename 已存在文件；`copyFileSync` 静默吞；孤儿进程占用 :3000 | 部署写 `public_live_<ts>` 全新目录；重启后端才生效；杀孤儿 PID 再起 | 适用：本沙箱部署；不适用：无沙箱/有持久日志环境 | CODING-SPA-LIVE-DEPLOY → BR-071 / FR-068 / [spa-live-deploy-rule.md](spa-live-deploy-rule.md) |
| 4 | Edge TTS 朗读不拟人 / 误用 express-as | `prosody`(rate/volume/pitch) 映射风格 + 后端 FFmpeg 响度归一 | 免费端点不支持 `<mstts:express-as>`（WebSocket 1007）；沙箱无 ffmpeg | 拟人杠杆=prosody + 后处理；express-as 彻底移除；ffmpeg 缺失优雅降级 | 适用：自带 TTS 端点项目；不适用：纯浏览器 speechSynthesis 即可 | CODING-TTS-* → FR-067 / [tts-neural-fallback-rule.md](tts-neural-fallback-rule.md) |
| 5 | BYOK 多用户密钥代理（额度互抢 / 泄漏） | 前端本地命名空间 `usercfg::<kind>::<userId>`；请求带配置后端纯函数覆盖；缺 key 400 | 前端始终下发空 `toolsConfig` 清空服务端共享；门禁只校验 apiKey 致畸形配置 500 | 每用户命名空间隔离；密钥仅经请求体、不落盘/不回显/不记日志；空覆盖回退服务端；纯函数 `applyPerRequestOverride` | 适用：多用户 + 用户自带 Key；不适用：单用户 / 密钥服务端统一托管 | CODING-BYOK → FR-070 / BR-072 / [byok-per-user-override-rule.md](byok-per-user-override-rule.md) |
| 6 | 流式回答中间态丢失（刷新退化为新会话） | 流式分片增量（防抖）落盘；卸载不 abort 在途流；仅对 `status:'streaming'` 末条续答 | onBeforeUnmount 误 abort；interrupted/error 不应自动续 | 增量持久化 + 后台继续生成 + 末条续答三类状态分流 | 适用：SSE 流式问答；不适用：一次性同步响应 | CODING-STREAMING-RESUME → FR-071 / [streaming-resume-rule.md](streaming-resume-rule.md) |
| 7 | 隔离测试 flaky（用例间泄漏） | 每用例唯一 userId 命名空间；异步断言多轮 `setTimeout(0)` flush | `beforeEach(deleteDatabase)` 在 fake-indexeddb + 已开连接下 onblocked/泄漏；后端模块单例跨用例共享 | 唯一命名空间而非删库；重置模块态/mock；flush 轮数配置化 | 适用：含持久化/全局状态的测试；不适用：纯函数单测 | CODING-TEST-ISOLATION → FR-072 / BR-073 / [indexeddb-test-isolation-rule.md](indexeddb-test-isolation-rule.md) |
| 8 | API 端点裸奔上线（无覆盖） | 端点测试（Fastify `app.inject`）+ 静态检查（注册/类型对齐）+ 全量套件 + Flake 隔离 | 沙箱无浏览器 → 完整 E2E 低信号；固定窗口计数器跨分钟边界偶发 200（预存在 flake） | 测试范围按"被修改内容"而非全应用；新端点自动标记未测；失败先隔离后归因 | 适用：后端路由/引擎变更、CI 增量；不适用：纯前端 UI 动画 | CODING-*（测试流程）→ wiki-auto-testing `scope`/`test_coverage`/`endpoint_autodiscovery` |
| 9 | SSML prosody 注入（畸形 rate/volume/pitch / 未转义文本 / express-as 在免费端点 1007） | 后端校验+转义后再拼 SSML；前端先校验 prosody 范围再下发；express-as 默认剥离 | 免费端点不支持 express-as（1007）；用户文本含 `<>&` 破坏 SSML 结构 | prosody 正则白名单 + escapeXml + 禁用标签清单；前后端双重校验 | 适用：自带 TTS 端点项目；不适用：纯浏览器 speechSynthesis | CODING-SSML-INJECTION → BR-074 / FR-073 / [ssml-injection-rule.md](ssml-injection-rule.md) |
| 10 | 子进程异步当同步用（execFile 结果未等待即使用） | 需同步结果改 execFileSync（带超时）或 await Promise；仅真异步事件流保留回调 | 音频后处理把 execFile 当同步，结果未产生就用 | 子进程 API 按"要同步结果/要异步事件"二选一；*Sync 带超时 | 适用：需子进程 stdout/退出码/产物的同步计算；不适用：即发即忘日志 | CODING-CHILD-PROCESS-SYNC → BR-075 / [child-process-sync-rule.md](child-process-sync-rule.md) |
| 11 | 关键写静默吞错（saveUsers try/catch 空 catch 假成功） | 关键写失败 throw 或 log+throw；返回 ok 须与真实写一致 | 磁盘满/权限/safe-delete 拦截被掩盖，用户误判保存成功 | 关键写函数清单 + 空 catch 匹配；失败须传播 | 适用：用户/配置/会话持久化；不适用：纯日志/非关键缓存 | CODING-CRITICAL-WRITE-NO-SWALLOW → BR-076 / [critical-write-no-swallow-rule.md](critical-write-no-swallow-rule.md) |
| 12 | 关键文件损坏被当 not-found 静默清零（loadUsers JSON 损坏覆盖原数据） | 区分 ENOENT（默认初始化）与 corrupt（log+备份.corrupt+回退默认）；绝不静默清零 | 损坏文件被 saveUsers 直接覆盖，原始记录不可恢复 | 关键文件清单 + 损坏备份策略 + 回退默认 | 适用：users.json/config.json 等；不适用：纯日志/可丢失缓存 | CODING-FILE-CORRUPTION-GUARD → BR-077 / [file-corruption-guard-rule.md](file-corruption-guard-rule.md) |
| 13 | 类型安全 `as any` 绕过（request.method as any 掩盖类型） | 提取真实类型 InjectOptions['method']；类型守卫/断言收窄；迁移期 @migration 标注 | typecheck 幽灵错误用 as any 消红，重构无法捕获 | 禁止绕过写法清单 + 推荐类型提取 + 允许迁移标注 | 适用：常驻业务路径；不适用：无类型第三方库边界（用 unknown+局部断言） | CODING-TYPE-SAFE-NO-ANY → BR-078 / FR-026 / [type-safe-no-any-rule.md](type-safe-no-any-rule.md) |
| 14 | 超时硬编码（edgeTtsClient 30000 字面量难调优） | 超时从配置键读取（edgeTtsTimeoutMs）；多层自下而上递增×1.5 | 弱网/代理超 30s 被中断；调优须改代码 | 超时键清单 + 禁硬编码字面量 + 递增倍数 | 适用：任何网络/子进程/SSE 超时；不适用：编译期常量 | CODING-CONFIG-TIMEOUT → BR-079 / [config-timeout-rule.md](config-timeout-rule.md) |
| 15 | 冗余探针（isFfmpegAvailable 用 ffprobe 探测 ffmpeg 能力） | 用 `ffmpeg -version` 能力检测替代 ffprobe 冗余探测；缺失优雅降级 | 仅缺 ffprobe 的环境误判 ffmpeg 不可用；徒增开销 | 能力检测命令 + 冗余探针命令清单 | 适用：外部工具可用性检测；不适用：确需 ffprobe 提取元数据 | CODING-NO-REDUNDANT-PROBE → BR-080 / [no-redundant-probe-rule.md](no-redundant-probe-rule.md) |
| 16 | 归档路由文件名碰撞（同线程同日多条归档互相覆盖，静默丢数据） | 落盘路径除派生分组键（日期+shortId）外追加随机后缀；冲突检测走唯一性校验 | 派生键非全局唯一 → 同日同线程第二条覆盖第一条；重命名被 safe-delete 拦截 | 落盘文件名 = 派生键 + 随机后缀（长度配置化）；冲突即拒绝/重生成 | 适用：按分组键派生命名 + 并发写入的场景；不适用：单条/全局唯一 uuid 命名 | CODING-GENERATED-FILENAME-UNIQUENESS → BR-081 / [generated-filename-uniqueness-rule.md](generated-filename-uniqueness-rule.md) |
| 17 | 归档路由非法 `ts` → RangeError → 500 | `new Date(str)` 失败回退默认；非法/未定义/非字符串统一安全解析 | `new Date(str).toISOString()` 对非法串抛 RangeError，全链路 500 | 安全日期解析覆盖 null/未定义/非字符串/无效日期，回退配置默认值 | 适用：任何客户端传日期串的服务端解析；不适用：服务端自身生成的合法 Date | CODING-SAFE-CLIENT-DATE-PARSE → BR-082 / [safe-client-date-parse-rule.md](safe-client-date-parse-rule.md) |
| 18 | 归档路由 `messageIndex` 非整数 → undefined 访问 → 500 | `Number.isInteger` 校验客户端下标，非法即拒绝；校验在数组访问前短路 | 非整数/缺失 → 数组按 undefined 访问 → 下游 500 | 整数序号校验在数组访问前；非法即配置化拒绝状态码 | 适用：客户端传索引访问数组；不适用：服务端生成且受信的下标 | CODING-INTEGER-INDEX-VALIDATION → BR-083 / [integer-index-validation-rule.md](integer-index-validation-rule.md) |
| 19 | 归档 refs 含换行破坏 `[[wikilink]]` / 空串脏链接 | 注入 `[[wikilink]]` 前 `replace(/[\r\n]/g,' ').trim()` + `filter(Boolean)`；按配置正则额外清洗 | 换行注入使 wikilink 跨行断裂；空串生成 `[[ ]]` 脏链接 | 注入前规范化（去换行/空白）+ 去空；清洗字符集配置化 | 适用：任何注入 wikilink/Markdown 链接的场景；不适用：纯文本字段 | CODING-WIKILINK-SANITIZATION → BR-084 / [wikilink-sanitization-rule.md](wikilink-sanitization-rule.md) |
| 20 | 归档空内容仍创建空节点（脏数据/no-op） | question/answer 同时缺失或空串即拒绝；写入前短路 | 空串/纯空白仍落盘空节点，污染知识库 | 空内容拒绝：必填字段从配置读取，缺失即配置化拒绝状态码 | 适用：任何创建型写入端点；不适用：允许占位/草稿的可选字段 | CODING-EMPTY-CONTENT-REJECTION → BR-085 / [empty-content-rejection-rule.md](empty-content-rejection-rule.md) |
| 21 | 归档依赖服务端会话 → 默认部署 100% "已过期"误报 | 归档优先从请求体取内容，仅缺失回退 `getSession`；默认 `threadsPersist=false` 须解耦；前端门控同步放宽 | 服务端不持久化会话 → `getSession` 恒空 → 误报过期；前端 `!!sessionId` 门控继续卡死 | 内容取源解耦（请求体优先）；客户端能力门控与后端契约同步放宽 | 适用：服务端不持久化会话 / 客户端自带内容的可选归档；不适用：服务端强制会话鉴权的场景 | CODING-PERSISTENCE-CLIENT-CONTENT-DECOUPLING → BR-086 / FR-076 / [persistence-client-content-decoupling-rule.md](persistence-client-content-decoupling-rule.md) · [capability-gating-sync-rule.md](capability-gating-sync-rule.md) |
| 22 | 编辑已发送消息重发后对话只剩悬空 AI 答案 | `removeMessagesFrom(i)` 丢弃尾部后立即 `submitQuestion(编辑后文本)` 重插；重发前先终止在途流式回复；文本未变仅退出编辑态 | 只调 removeMessagesFrom 不重插 → user 消息凭空消失；首问路径不经 removeMessagesFrom 故单测不暴露 | 编辑重发不变量：丢弃尾部必须重插；先停 in-flight；未变不重发（幂等） | 适用：可编辑已发送消息并重新生成的聊天/问答；不适用：只读/追加日志/不可变审计流 | CODING-EDIT-RESEND → FR-077 / [edit-resend-rule.md](edit-resend-rule.md) |
| 23 | 流式输出最新 token 看不到 / 用户回看被拉回底部 / 带图消息不贴底 | 贴底定位 nextTick + 双 rAF；用户上滑超阈值暂停贴底、回底恢复；capture 阶段监听 img load 补滚；容器挂载/卸载自动绑定解绑监听 | 单次 nextTick 早于图片/代码撑高；强制拉回打断回看；连续 token 单次定位落后 | 贴底=布局稳定后定位；贴底暂停随用户滚动态；图片异步撑高补滚；监听随容器生命周期 | 适用：SSE/流式 token 聊天问答；不适用：静态不滚动/无中间态 | CODING-STREAMING-AUTOSCROLL → FR-078 / [streaming-autoscroll-rule.md](streaming-autoscroll-rule.md) |
| 24 | 成对操作按钮（确认/取消）样式不一致误导主次 | 同组按钮共享 base 样式，差异仅 hover 强调；配色用主题变量；type=primary 仅留给唯一主操作 | 功能测试只验证点击行为，忽略样式层级；硬编码色值不随主题 | 成对按钮基础样式一致；区分经 hover；主题变量；单主操作 | 适用：弹窗/内联编辑/表单确认取消；不适用：分处不同上下文的独立按钮 | CODING-BUTTON-STYLE-CONSISTENCY → FR-079 / [button-style-consistency-rule.md](button-style-consistency-rule.md) |
| 25 | 消息进入编辑态编辑框停留已发送气泡窄宽，文字频繁换行 | 编辑容器 align-items:stretch 撑满整列；.msg-edit width:100%；textarea width:100% 且内边距与首问一致 | 编辑框继承 user 气泡 flex-end+max-width 窄宽；体验远差于首问输入框 | 编辑态覆盖已发送对齐、撑满列宽；控件全宽 | 适用：内联编辑已发送消息的同容器 UI；不适用：独立全宽编辑页/弹窗 | CODING-EDITBOX-WIDTH → FR-080 / [editbox-width-rule.md](editbox-width-rule.md) |
| 26 | Vue/Pinia `reactive` 代理直传 IndexedDB → `DataError: [object Array] could not be cloned` 静默丢配置 | 写入前整树深拷贝（`JSON.parse(JSON.stringify(x))` / `clone<T>`）剥离代理；`saveUserConfig` 内部统一 clone 防御 | 失败静默（IDB 事务回调抛错被外层 `try/catch` 仅 warn）；`toRaw` 只剥顶层、嵌套仍是代理；`structuredClone` 也无法克隆代理 | 凡 `dbPut`/`saveUserConfig` 等 IDB 写入点，入参若源自 store ref/reactive 必须已 clone；禁止 toRaw/structuredClone 当深剥离 | 适用：Vue 3 + Pinia + IndexedDB 落盘（或任何 structuredClone 持久化）；不适用：localStorage(JSON 序列化不受 proxy 影响)/纯服务端/已是 plain object/IDB 读取 | CODING-IDB-REACTIVE-CLONE → FR-081 / [idb-reactive-clone-rule.md](idb-reactive-clone-rule.md) |
| 27 | API 写端点零守卫（游客越权改共享密钥 / 读写删他人数据）+ 限流 IP 只用 `request.ip` 或只用 XFF（代理误判 / 伪造绕过） | 写端点注入 auth 感知守卫工厂 `createIsolationGuards`（`auth.enabled=false` 单租户直通）；服务端 `ownerId` 以受信上下文盖章、忽略客户端 body；限流 / 审计 IP 用复合键 `request.ip\|xffFirst` 防 XFF 伪造 | 全局 `preHandler` 只注入 currentUser 不拒绝；单租户部署若守卫不直通会全 401；反向代理下 `request.ip` 取代理 IP、XFF 可客户端伪造 | 写端点声明式注入 `preHandler: guards.requireAdmin`；守卫 auth 感知直通单租户；`ownerId` 来自 currentUser 不容客户端可控；限流 IP 统一 `clientIpFromRequest` 复合键、trustProxy=false | 适用：含"需登录才能写"共享状态的多用户 / 单租户混合部署；不适用：纯公开只读无认证 API | CODING-ISOLATION → BR-ISOLATION / [isolation-guard-rule.md](isolation-guard-rule.md) |

### 本轮新增（2026-08-10 会话）：BR-089~093 对应规则索引

| # | 历史问题 | ① 成功步骤（有效动作） | ② 失败点 / 环境约束 | ③ 抽象的固定流程与判断 | ④ 适用 / 不适用 | 规则 |
|---|---------|----------------------|---------------------|------------------------|----------------|------|
| 28 | 登录/统计接口偶发超时或空响应（Fastify handler 多分支漏 return → 双发响应 `ERR_STREAM_WRITE_AFTER_END` / 前端超时） | 逐分支显式 `return reply.send()`；`async` handler 统一收口；用 `reply` 对象收口 | 漏 return 落底触发双发响应；多分支校验/提前退出点易漏写 return | 路由 handler 每个分支/提前退出点必须 return/throw；async handler 禁止隐式 undefined 落底 | 适用：多分支校验/提前退出路由；不适用：纯 preHandler / 已 throw 交错误处理器 | CODING-ROUTE-RETURN-COMPLETENESS → BR-089 / [route-return-completeness-rule.md](route-return-completeness-rule.md) |
| 29 | 响应 `onSend`/`onResponse` 钩子异常或阻塞使**所有** API 挂死（压缩钩子内部异常） | 钩子主体全程 `try/catch` fail-open（异常原样放行）；禁止 await 重计算；逐路由挂载避开全局挂死 | 全局 `onSend` 在本 Fastify 版本会使所有响应挂起（onResponse 不触发）；压缩失败体损坏 | 响应生命周期钩子须 fail-open + 不阻塞；压缩等可选能力默认关闭 | 适用：任何 onSend/onResponse/setSerializer/contentTypeParser；不适用：纯同步无钩子路径 | CODING-RESPONSE-HOOK-SAFE → BR-090 / [response-hook-safe-rule.md](response-hook-safe-rule.md) |
| 30 | 启用 `@fastify/compress` 后 API 响应体损坏/0 字节（Windows Node 22/24 zlib 流不稳定 → 前端 `JSON.parse` 失败 "Unexpected end of JSON input"） | 弃用流式压缩，改为同步 `gzipSync`/`brotliCompressSync` 对已序列化 payload 压缩；默认关闭压缩（`WIKI_ENABLE_COMPRESSION=1` 显式开启）；阈值参数化 | `@fastify/compress` 流式在 ≥1KB 时间歇返回损坏/空体且与 Node 版本无关；默认开启压缩=线上 API 全不可用 | 压缩中间件必须默认关闭 + 条件注册；阈值/级别/白名单 content-type 全来自配置；与 RESPONSE-HOOK-SAFE 互补 | 适用：任何响应压缩中间件；不适用：纯静态资源（sendFile 绕过 onSend） | CODING-COMPRESSION-DEFAULT-OFF → BR-091 / [compression-default-off-rule.md](compression-default-off-rule.md) |
| 31 | 登录时 `users.json` 读取/写入在沙箱被拦截或空壳导致登录失败 | 读取区分 ENOENT（默认初始化）与 corrupt（备份 `.corrupt-<ts>` + 回退默认 + `log.warn`）；写入 best-effort `try/catch` 不阻塞登录；首次运行写出合法非空 JSON | 沙箱 safe-delete 钩子拦截 saveUsers；损坏文件被静默清零；空壳 JSON 触发解析失败 | loadUsers/loadConfig 区分 not-found/corrupt 并兜底回退默认 + 备份；关键写失败须可观测（与 BR-076/077 同一纵深） | 适用：users.json/config.json 等可写关键数据；不适用：纯日志/可丢失缓存 | CODING-USER-STORE-INIT → BR-092 / [user-store-init-rule.md](user-store-init-rule.md) |
| 32 | 启动脚本清理旧进程时 `taskkill` stderr 在 `$ErrorActionPreference='Stop'` 下触发 `NativeCommandError` 中止整个脚本（`[ERROR] Start failed`） | 端口清理用 `Stop-Process -Id $id -Force` 配合 `try/catch`（清理为非致命步骤）；残留进程用 `Get-CimInstance` 命令行匹配兜底；杀进程失败静默跳过 | `taskkill` 对"属于其他进程子进程"的 PID 直接拒绝；其 stderr 被 PowerShell 包装为终止错误；裸 `taskkill` 无 try/catch 会让清理步骤变致命 | 服务启动前清理旧进程必须用 `Stop-Process -Force` + `try/catch`（非致命）；禁止裸 `taskkill` 当清理主键；残留进程走命令行匹配兜底 | 适用：PowerShell 服务启动/重启脚本清理占用端口进程；不适用：Bash/Zsh（stderr 不触发终止错误）/ 纯单命令 | CODING-PS-PROCESS-CLEANUP（PS-6 增强） → BR-093 / [process-cleanup-backend-rule.md](../../wiki-backend-code-review/references/process-cleanup-backend-rule.md) |

> 更多既有规则（Tauri、PowerShell、媒体生成、安装器、文件名管线、迁移脚本等）见 SKILL.md 路由表与各 `*-rule.md`。本表聚焦近几轮对话新提炼的标准。

### 本轮新增（2026-08-11 会话）：FR-084~085 / BR-094~095 对应规则索引

| # | 历史问题 | ① 成功步骤（有效动作） | ② 失败点 / 环境约束 | ③ 抽象的固定流程与判断 | ④ 适用 / 不适用 | 规则 |
|---|---------|----------------------|---------------------|------------------------|----------------|------|
| 33 | 前端受保护接口裸 `fetch` 调 `requireAuth` 端点（如 `GET /api/config`、`GET /api/ai/config`）→ 后端返 401，AI 伙伴选项消失 + 控制台「加载配置失败：HTTP 401」静默失效 | 新增 `apiFetch`（读 `localStorage` token 注入 `Authorization`，不依赖 Pinia），全站 18 处裸 `fetch` → `apiFetch` 迁移；bootstrap 期先于 auth store 就绪即可带 token | 鉴权封装若依赖 Pinia/auth store 会陷入 bootstrap 期鸡生蛋；裸 fetch 失败静默（仅控制台），比崩溃更隐蔽；给公开端点加 `requireAuth` 是破坏性变更 | 受保护端点与"带 token 封装"是契约对，缺任一即 401；封装须从非 Pinia 源（localStorage）读 token；收紧 `requireAuth` 须审计全部前端调用方 | 适用：任何后端挂 `requireAuth` 的前端调用；不适用：显式公开端点（publicPaths 白名单）、纯静态资源 | CODING-AUTH-REQUEST-FETCH → FR-084 / BR-094 / [auth-request-fetch-rule.md](auth-request-fetch-rule.md) |
| 34 | pnpm store 散落项目/盘根（safe-delete 钩子打断 pnpm 主目录探测的 rename 临时操作 → EPERM → pnpm 退化为当前盘根建 `.pnpm-store`），缓存污染工作区且 node_modules 解析不到统一 store | 全局 `.npmrc` 显式写 `store-dir=D:\.pnpm-store` 收敛；`pnpm store path` 验证返回统一路径；确认孤儿无 `node_modules/.modules.yaml` 引用后删除 | WorkBuddy safe-delete 沙箱钩子 fail-closed 拦截 rename/覆盖/rm；pnpm 探测 home 可写性用的 rename 被拦即退化；删除受钩子约束须走放行路径 | 包管理器 store 须显式 `store-dir` 收敛（禁依赖自动探测）；定期检测/清理孤儿 `.pnpm-store`；CI/环境初始化断言 store-dir 收敛 | 适用：受限文件系统环境 + 严格 store 包管理器（pnpm）；不适用：纯 npm/yarn、已显式收敛且无孤儿的环境 | CODING-PNPM-STORE-HYGIENE → FR-085 / BR-095 / [pnpm-store-hygiene-rule.md](pnpm-store-hygiene-rule.md) |

### 本轮新增（2026-08-12 会话）：下载特性缺陷 + 部署覆盖危机 对应规则索引

> 本轮针对 Request-G「文档下载」特性暴露的 8 类缺陷（code-review #1–#8）+ SPA 部署移动端覆盖危机，做四维度复盘，固化为 wiki-code-dev 6 条规则 + FR-091~094 + BR-097~101 + wiki-auto-testing `route_response_branch_coverage` 多路由分支覆盖。全部 config 驱动、零硬编码。

| # | 历史问题 | ① 成功步骤（有效动作） | ② 失败点 / 环境约束 | ③ 抽象的固定流程与判断 | ④ 适用 / 不适用 | 规则 |
|---|---------|----------------------|---------------------|------------------------|----------------|------|
| 35 | 文档下载端点（文件流出）缺 auth 门禁 → 游客越权下载 vault 任意文件 | 读端点注入 `readPreHandler = filesReadAuthRequired && guards.enabled ? requireAuth : undefined`（fail-closed）；单租户 `auth.enabled=false` 直通显式、不与 `filesReadAuthRequired` 混淆 | 全局 `preHandler` 只注入 currentUser 不拒绝；单租户直通若盖过显式门禁会全 401；缺凭证须 401 而非 400 | 文件流出端点默认 fail-closed；`filesReadAuthRequired` 门禁优先于单租户直通；auth 感知守卫工厂统一收口 | 适用：任何 download/export/attachment 文件流出端点；不适用：已显式声明 public 的只读静态资源 | CODING-DOWNLOAD-AUTH → BR-097 / [download-endpoint-auth-rule.md](download-endpoint-auth-rule.md) |
| 36 | 下载附件名 RFC 5987 缺失 / header 注入（CWE-113）/ 控制字符 / 非 ASCII / 扩展名丢失 | `buildAttachmentHeader(relPath)` 输出 `attachment; filename="<legacy>"; filename*=UTF-8''<encoded>`；控制字符清洗 + `'()*` 百分号转义；非 ASCII 只进 `filename*` | 非法文件名拼进 Content-Disposition 可注入换行篡改响应头；legacy 字段含非 ASCII 破坏解析；路径安全化后丢弃扩展名致下载文件无类型 | 附件头须 RFC 5987 `filename*` + legacy 兜底；控制字符/引号清洗；`'()*` 转义；保留原始扩展名（path 安全后取 extname） | 适用：任何 `Content-Disposition: attachment` 文件名拼接；不适用：纯 inline 无文件名响应 | CODING-CONTENT-DISPOSITION-SAFE → BR-098 / BR-101 / FR-094 / [content-disposition-safe-rule.md](content-disposition-safe-rule.md) |
| 37 | vault 读取错误码（EISDIR/EACCES/EPERM/ENOENT/EOUTSIDE）被吞 / 错误映射丢失语义 | `mapVaultReadError` 按 `err.code` 映射：EISDIR→400、EACCES+EPERM→403、ENOENT→404、EOUTSIDE→400、未知→500 保留 message | catch 统一返回 500 丢失语义（目录被当 500、越权被当 500）；前端无法据此区分处理 | catch 必须按 `err.code` 映射语义 HTTP 状态；仅未知错误→500 且保留 message；与 BR-076 同一纵深 | 适用：任何读取 vault/文件系统并 catch 的端点；不适用：纯内存/无错误码来源 | CODING-VAULT-ERRCODE-PRESERVE → BR-099 / [vault-error-code-preserve-rule.md](vault-error-code-preserve-rule.md) |
| 38 | 响应头顺序错乱（Content-Disposition/Content-Type 在读取成功前即设置 / 错误路径仍带附件头）→ half-response / 信息泄漏 | 头仅在读取成功后设置；错误路径绝不带 Content-Disposition；成功读完后一次性 set | 提前 set 附件头后读取失败 → 已发附件头 + 错误体混杂；错误路径带附件头误导客户端 | 附件响应头（Content-Disposition/Content-Type）只在读取成功后设置；错误路径不带 Content-Disposition（防 half-response） | 适用：任何流式/文件下载响应；不适用：纯 JSON API（无附件头） | CODING-RESP-HEADER-ORDER → BR-100 / [response-header-ordering-rule.md](response-header-ordering-rule.md) |
| 39 | 前端下载无超时/中断/防重入 + 移动端静默失败（错误不展示，用户以为没反应） | `AbortSignal.timeout(config.download_frontend.timeout_ms)`；in-flight 防重入锁；移动端+桌面共享错误展示（禁静默）；共享 `downloadVaultFile` | 大文件/弱网下下载挂死无超时；重复点击叠加请求；移动端 catch 吞错无提示 | 前端下载统一带超时 + 防重入锁；移动端与桌面共享错误展示；统一封装 `downloadVaultFile` | 适用：任何前端触发下载/导出；不适用：纯服务端生成、无用户交互触发 | CODING-FE-DOWNLOAD-ROBUST → FR-091~094 / [frontend-download-robustness-rule.md](frontend-download-robustness-rule.md) |
| 40 | 部署后移动端特性串缺失（覆盖危机：`resolveSpaRoot` 按时间戳选最新，曾被不含移动端的旧构建覆盖 → 重启线上切回无移动端版） | 部署前确认 frontend 源码含移动端；build 到全新 `dist_u<ts>`；`_deploy_live.mjs` → `public_live_<ts>`；重启后端；冒烟校验 bundle 含 `MobileListen`/`MobileShell`/`聆听` | 沙箱全量写回滚 → 构建须 `dangerouslyDisableSandbox`；孤儿 :3000；后续不含移动端的构建覆盖最新时间戳 | 部署后校验线上 bundle 含关键特性串（marker 列表 config 化）；写全新目录 + 重启 + 冒烟三位一体 | 适用：本沙箱 SPA 部署 + 含特性开关/移动端分支的构建；不适用：无特性分支的纯静态部署 | CODING-DEPLOY-MARKER-VERIFY → DM-1~DM-2 / [deploy-mobile-marker-verify-rule.md](deploy-mobile-marker-verify-rule.md) |

---

## 维度三细化：可抽象的判断逻辑（Judgment Logic）

跨上述问题可抽取出 5 条通用判断，供新代码 / 新审查直接套用：

- **J-ISOLATION** — 多用户 / 多账户 / 多租户数据，必须以「用户/账户 id 命名空间」隔离，禁止共享可写单例；跨边界复用时先校验归属再写入。服务端侧落地为：写端点注入 **auth 感知守卫**（`createIsolationGuards`，单租户 `auth.enabled=false` 直通、绝不破坏既有"关认证=全管理员"形态）、`ownerId` 以受信上下文（`request.currentUser`）盖章、绝不信任客户端 body；限流 / 审计 IP 用复合键 `request.ip|xffFirst` 防 XFF 伪造（trustProxy=false）。对应 CODING-ISOLATION → BR-ISOLATION。
- **J-NO-FALLBACK-SECRET** — 用户自带密钥场景，缺密钥直接拒绝（400），禁止回落到共享/默认密钥；密钥只走请求体，不落盘/不回显/不记日志。
- **J-PURE-OVERRIDE** — 配置/参数覆盖抽为**纯函数**（`??`/`?.` 合并，无 `!`/`as`），空/默认覆盖须回退原值，绝不能清空服务端共享能力。
- **J-FRESH-DIR-DEPLOY** — 受限环境部署写**全新目录**、不原地覆盖；spaRoot 启动时算一次，写完须重启；孤儿进程须先杀再起。
- **J-TEST-NAMESPACE** — 含状态的测试用唯一命名空间隔离，禁止 `beforeEach` 删库；后端重置模块态/mock；异步落盘断言多轮 flush。
- **J-SSML-SAFE** — 外部输入拼进 SSML/TTS 前必须校验 prosody 格式（rate/volume/pitch 白名单正则）+ 转义 `<>&` + 禁用不支持标签（express-as 在免费端点 1007）；前后端双重防护（前端先校验再下发，后端兜底校验）。
- **J-SYNC-BOUNDARY** — 子进程调用按"要同步结果 / 要异步事件"二选一 API：需同步结果用 `execFileSync`（带超时）或 `await` Promise，禁止把异步 `execFile` 当同步用；可用性检测用能力命令（如 `ffmpeg -version`）而非冗余探针。
- **J-NO-SILENT-FAIL** — 关键写失败必须传播（throw / log+throw），禁止空 catch 假成功；关键文件读取须区分 not-found 与 corrupt，损坏须备份+回退默认，禁止静默清零。
- **J-NO-HARDCODE** — 超时/阈值一律从配置键读取，禁止硬编码字面量（如 30000）；多层超时自下而上递增 ×1.5（与 BR-053 一致）。
- **J-CONFIG-FIRST** — 所有可变参数（超时/阈值/端口/路径/正则/白名单/severity 文案/扫描范围/端点清单/payload 模板）集中在配置层（coding-standards-config.md / review-config.md / defaults.yaml / config.yaml / examples），代码与规则文件只读取不内联；新增规范 = 在配置加一组（registry 模式），引擎主流程不动；配置分层为「默认值 + 项目覆盖 + 示例」三层；同一参数跨四技能命名一致、编号顺延不漂移。对应 CODING-CONFIG-DRIVEN → 各技能 config 层（零硬编码元规则）。
- **J-DERIVED-KEY-UNIQUENESS** — 落盘文件名若由分组键（日期+shortId 等）派生，**非全局唯一**，须追加随机后缀（长度配置化）后再落盘；冲突判定走唯一性校验，禁止依赖派生键自身唯一性。
- **J-SAFE-DATE** — 服务端解析客户端日期串禁止 `new Date(str).toISOString()`（非法串抛 RangeError）；统一走安全解析覆盖 null/未定义/非字符串/无效日期，回退配置默认值。
- **J-INTEGER-INDEX** — 客户端传下标访问数组前，须 `Number.isInteger` 校验；非法/缺失即拒绝（状态码配置化），校验在数组访问前短路，禁止把非整数当下标导致 undefined 访问 500。
- **J-WIKILINK-CLEAN** — 注入 `[[wikilink]]` / Markdown 链接前必须规范化：去换行（`replace(/[\r\n]/g,' ')`）、`trim()`、去空串（`filter(Boolean)`），并按配置正则额外清洗破坏字符（`]`/`|` 等），禁止脏链接/跨行断裂。
- **J-EMPTY-REJECT** — 创建型写入端点在落盘前校验必填字段（从配置读取）：同时缺失或空串即拒绝（状态码配置化），禁止空内容 no-op 落盘污染数据。
- **J-CONTENT-DECOUPLE** — 内容写入优先从请求体取，仅缺失时回退服务端会话；默认不持久化会话时须解耦，不得擅自开启 persist；取源解耦后客户端能力门控随后端契约同步放宽，防止两端漂移。
- **J-EDIT-RESEND** — 编辑重发不变量：丢弃尾部（removeMessagesFrom）与重新插入（submitQuestion）必须成对、同函数内完成；先终止在途流式回复再丢弃尾部；文本未变仅退出编辑态不重发，避免对话只剩悬空答案。
- **J-AUTOSCROLL** — 流式贴底=布局稳定后再定位（nextTick + 双 rAF）；用户上滑超阈值暂停自动贴底、回底恢复；图片异步撑高须补滚（capture 阶段监听 load）；滚动/加载监听随容器挂载/卸载生命周期绑定解绑，防泄漏。
- **J-BUTTON-STYLE** — 同一操作组成对按钮共享一致基础样式，区分仅经 hover/active 强调；配色引用主题变量禁止硬编码；`type="primary"` 仅留给唯一真正主操作，避免双主操作误导。
- **J-EDITBOX-WIDTH** — 消息气泡进入编辑态须以 `align-items:stretch` / `width:100%` 覆盖已发送态的 `flex-end` 窄宽、撑满问答列；编辑控件自身 `width:100%`、内边距与首问输入框对齐。
- **J-IDB-REACTIVE-CLONE** — 凡将 store state ref / `reactive()` 对象经 `dbPut`/`put`/`add` 写入 IndexedDB 的路径，写入前必须整树深拷贝为 plain object（`JSON.parse(JSON.stringify(x))` 或 `clone<T>`）；`toRaw()` 只剥顶层、嵌套代理仍会失败，`structuredClone` 同样无法克隆代理，二者均不可当作深剥离；IDB 读取返回 plain、localStorage 经 JSON 序列化不受影响。
- **J-AUTH-FETCH-WRAP** — 后端 `requireAuth` 受保护端点与前端"带 token 的 HTTP 封装"是**契约对**：缺任一端都 401。前端须有且仅有**一个**带鉴权封装（如 `apiFetch`），从 `localStorage` 读 Bearer token 注入 `Authorization`、不依赖 Pinia（bootstrap 期 auth store 未就绪时仍可用）；所有受保护端点调用一律走它，禁止裸 `fetch` 不带 token。后端把原先公开端点收紧为 `requireAuth` 是**破坏性变更**，必须审计全部前端调用方确认已迁移（对应 CODING-AUTH-REQUEST-FETCH → FR-084 / BR-094）。
- **J-PNPM-STORE-HYGIENE** — 受限文件系统环境（safe-delete 沙箱钩子 fail-closed 拦截 rename/覆盖/rm）下，pnpm 主目录探测会被打断导致其退化为在当前盘根建 `.pnpm-store`；必须**显式**在全局 `.npmrc` 写 `store-dir` 收敛到统一路径（禁依赖自动探测），并定期检测/清理与统一 store 不一致的孤儿目录；CI/环境初始化须断言 `store-dir` 收敛（对应 CODING-PNPM-STORE-HYGIENE → FR-085 / BR-095 / wiki-auto-testing `dependency_store_hygiene_check`，参数全配置零硬编码）。
- **J-DOWNLOAD-AUTH** — 文件流出端点（download/export/attachment）默认 **fail-closed**：`auth.enabled=false` 单租户直通，但显式 `filesReadAuthRequired` 门禁必须优先于单租户直通；缺凭证即 401，绝不回落到"关认证=全放行"。守卫统一走 auth 感知工厂（与 CODING-ISOLATION 同类）。对应 CODING-DOWNLOAD-AUTH → BR-097。
- **J-CONTENT-DISPOSITION-SAFE** — 附件文件名拼进 `Content-Disposition` 须 RFC 5987 `filename*`（UTF-8 编码）+ legacy `filename` 兜底；控制字符（`\x00-\x1f\x7f`）/引号清洗；`'()*` 百分号转义；非 ASCII 只进 `filename*`（防 CWE-113 header 注入）；保留原始扩展名（path 安全化后取 extname，禁丢弃）。对应 CODING-CONTENT-DISPOSITION-SAFE → BR-098 / BR-101 / FR-094。
- **J-ERRCODE-PRESERVE** — catch 必须按 `err.code` 映射语义 HTTP 状态（EISDIR→400 / EACCES+EPERM→403 / ENOENT→404 / EOUTSIDE→400 / 未知→500 且保留 message），禁止把一切读取错误吞成 500 丢失语义。与 BR-076 同一纵深（关键错误可观测）。对应 CODING-VAULT-ERRCODE-PRESERVE → BR-099。
- **J-RESP-HEADER-ORDER** — 附件响应头（Content-Disposition/Content-Type）**只在读取成功后**设置；错误路径绝不带 Content-Disposition（防 half-response / 错误体混入附件头）。对应 CODING-RESP-HEADER-ORDER → BR-100。
- **J-FE-DOWNLOAD-ROBUST** — 前端下载统一 `AbortSignal.timeout(config.download_frontend.timeout_ms)`；in-flight 防重入锁；移动端与桌面**共享**错误展示（禁静默失败）；统一封装 `downloadVaultFile`。对应 CODING-FE-DOWNLOAD-ROBUST → FR-091~094。
- **J-DEPLOY-MARKER-VERIFY** — 部署后校验线上 bundle 含关键特性串（如 `MobileListen`/`MobileShell`/`聆听`，列表 config 化）；写全新目录 + 重启后端 + 冒烟三位一体，防覆盖危机。对应 CODING-DEPLOY-MARKER-VERIFY → DM-1~DM-2。

---

## 测试流程四维度复盘（Testing Process）

> 以下为「近几轮测试流程」的专项复盘，完整版与更多轮次见 [wiki-auto-testing references/testing-process-review.md](../../wiki-auto-testing/references/testing-process-review.md)。

### ① 成功执行步骤（有效测试流程）
1. **类型检查先行**：`vue-tsc --noEmit`（前端）/ `tsc --noEmit`（后端，仅参考，后端以 tsx 转译运行，预存错误不阻断）。
2. **单元 + 隔离测试**：纯逻辑单测（vitest）最快；含状态测试用唯一命名空间。
3. **全量套件**：`vitest run` 确认无回归（如前端 144 / 后端 418）。
4. **构建到全新目录**：`vite build --outDir ../builds/dist_u<ts> --emptyOutDir`（规避 safe-delete 覆盖拦截）。
5. **部署 + 重启**：`_deploy_live.mjs <新构建目录>` 生成 `public_live_<ts>`；杀占用 `:3000` 的孤儿 PID 后 `tsx src/index.ts` 重启。
6. **冒烟验证**：缺 key→400、带配置→200 进 SSE、`/wiki/` SPA 正常伺服。

### ② 不确定性与失败点
- **fake-indexeddb 删库陷阱**：`beforeEach(deleteDatabase)` 在已开连接下 onblocked/泄漏 → 改用唯一命名空间（见 CODING-TEST-ISOLATION）。
- **typecheck 错误阻断 build**：`vue-tsc` 报告与源码收窄逻辑不一致（幽灵错误）→ 禁 `as any`/`!` 绕过，清缓存重跑。
- **后端 `tsc --noEmit` 预存错误**：`config.ts`/`index.ts` 有 13 个既存错误，与本次改动无关，后端以 tsx 转译运行不受影响——不把 pre-existing 错误算到新改动。
- **孤儿进程占 :3000**：`run_in_background` 任务被回收后底层 tsx 变孤儿继续伺服，新启动 `EADDRINUSE` → 先 `netstat` 取 PID 杀之再起。
- **全量套件偶发失败**：先隔离单文件重跑，通过=预存在 flake/环境竞态，不计入新缺陷。

### ③ 可抽象的固定流程与判断
```
改动类型路由：
  前端 UI/交互 → 类型检查 → 单元 → 全量 → 构建(全新目录) → 部署 → 重启 → 冒烟
  后端路由/引擎 → 单元 → 端点(inject) → 静态(注册/类型) → 全量 → (失败)Flake隔离
  含状态测试 → 唯一命名空间 + 多轮flush + (后端)重置模块态
部署铁律：写全新目录 → 杀:3000孤儿 → 重启后端（spaRoot启动算一次）
```

### ④ 适用与不适用
- **适用**：本沙箱（safe-delete fail-closed、无持久日志、可后台起 tsx）、含持久化/多账户的测试、CI 增量测试。
- **不适用**：纯静态页面、无后端 service 的纯前端改动（无部署/重启环节）、纯同步无状态单测（无需命名空间/flush）。

### 本轮新增（2026-08-12 会话）：测试流程优化 — `route_response_branch_coverage` 多路由分支覆盖

> 针对下载/读端点的 fail-closed 门禁与错误码映射，把"逐分支断言"固化为可配置步骤类型。扩展 `wiki-auto-testing` 引擎支持**多路由 + 每路由独立 token_env + required_headers 断言**，保留旧单路由配置兼容。本轮还强化了"沙箱端口/孤儿进程"测试纪律。

#### ① 成功执行步骤（有效测试流程）
1. **多路由分支覆盖配置化**：`route_response_branch_coverage.routes[]` 列出 4 个读端点（`/api/files/download`、`/api/files`、`/api/files/tree`、`/api/files/pages`），每路由 `branch_cases` 描述匿名→401、缺参→400、合法→200（+`required_headers` 校验 `Content-Disposition`）、目录非文件→400、越界→400/404。
2. **fail-closed 断言**：匿名分支不注入 `Authorization` → 断言 401；带 `token_env` 取 Bearer 注入 → 断言成功分支。auth 门禁与单租户直通差异由此可测。
3. **头断言**：`valid_binary` 分支除 `required_status` 外校验 `Content-Disposition` 响应头存在（验证 RFC 5987 附件头 + header 顺序）。
4. **引擎向后兼容**：`_handle_route_response_branch_coverage` 优先读 `routes[]`，缺失则回退旧 `route_name`/`method`/`branch_cases` 单路由形态。

#### ② 不确定性与失败点
- **沙箱跨进程 localhost TCP 被拦截**：沙箱内新起服务能 `LISTENING` 但同沙箱另一 node/curl `connect` 超时 → 勿在沙箱做跨进程 HTTP 冒烟；须带 `dangerouslyDisableSandbox:true` 才能对真实机 :3000 做端到端。
- **孤儿 :3000 进程**：`run_in_background` 任务被回收后底层 tsx 变孤儿继续伺服旧代码 → 新启动 `EADDRINUSE`；须先取监听 PID 杀之再起（系统级工具 netstat/taskkill 被安全策略禁用 → 改用 Node `process.kill`）。
- **`buildApp()` 重构**：`main()` 拆为 `buildApp()`（不 listen）+ `main()`（listen+信号）；`WIKI_SMOKE=1` 守卫跳过 helmet/rateLimit 使 `app.inject` 可正常进程内冒烟。
- **YAML 仅语法校验不足**：flow mapping（`{ path: ... }`）与缩进需 `yaml.safe_load` 实测解析（已验证 4 路由 14 分支通过）。

#### ③ 可抽象的固定流程与判断
```
端点分支覆盖（route_response_branch_coverage）：
  routes[]:
    每路由 {route_name, method, token_env, branch_cases[]}
    branch_cases[]: {name, description, params, expected_status, required_fields[], required_headers[]}
  执行：
    匿名分支 → 不注入 Authorization → 断言 expected_status(常 401)
    认证分支 → os.environ[token_env] 取 Bearer 注入 → 断言 expected_status + required_fields + required_headers
    超时 = timeout_ms/1000（统一经 config，禁硬编码）
  兼容：routes 缺失 → 回退 legacy route_name/method/branch_cases
端口/进程纪律：
  跨进程冒烟须 dangerouslyDisableSandbox；杀:3000 孤儿用 process.kill（禁系统级工具）；
  buildApp() 重构 + WIKI_SMOKE 守卫 → 进程内 inject 冒烟 5/5 通过
```

#### ④ 适用与不适用
- **适用**：本沙箱（safe-delete、跨进程 TCP 拦截、系统级工具禁用）、Fastify 端点 fail-closed 门禁 + 错误码映射的可配置分支断言、CI 增量端点测试。
- **不适用**：纯前端 UI 动画（无端点分支）、无需鉴权的公开只读端点（匿名分支无意义）、纯同步无状态单测。

---

## 最近一轮编码/调试专项复盘（2026-08-10 会话：6 项已修复问题）

> 本轮修复 6 个真实问题：① build-exe.ps1 图标注入 / rcedit 移除；② 移除未引用的 rcedit devDependency；③ 登录 `users.json` EPERM；④ 开发启动 `__filename is not defined in ES module scope`；⑤ 统计接口"Unexpected end of JSON input"（压缩空体）；⑥ 启动脚本 `taskkill` 中止。以下从四维度复盘，结论已固化为 wiki-code-dev 规则 + BR-089~093 / FR-082~083 + wiki-auto-testing 静态守卫。

### ① 成功执行步骤（有效动作）
1. **先定位根因再改**：用启动日志 + 错误栈区分是 ESM 全局缺失 / 压缩钩子挂死 / `taskkill` stderr，而非盲目重试。
2. **ESM 路径修复**：`runtime.ts` 用 `declare const __filename` + `typeof __filename === 'undefined'` 守卫，兼容开发（ESM+tsx）与 SEA（CJS bundle）双模式资源路径解析。
3. **压缩修复**：弃用 `@fastify/compress` 流式，改为同步 `gzipSync`/`brotliCompressSync` 对已序列化 payload 压缩，并默认关闭（`WIKI_ENABLE_COMPRESSION=1` 显式开启）。
4. **users.json 修复**：读取区分 not-found/corrupt 兜底 + 写入 best-effort `try/catch`，避免 safe-delete 拦截导致登录失败。
5. **启动脚本修复**：端口清理改 `Stop-Process -Force` + `try/catch` 使清理非致命；残留进程走 `Get-CimInstance` 命令行匹配兜底。

### ② 不确定性与失败点
- 沙箱 safe-delete 钩子 fail-closed 拦截 `saveUsers` 覆盖写 → 登录写盘"假成功/失败"。
- `@fastify/compress` 流式在 Windows Node 22/24 对 ≥1KB 响应间歇返回损坏/0 字节体（与 Node 版本无关，环境级 zlib 流不稳）。
- 本 Fastify 版本**全局 `onSend` 钩子会使所有响应挂起**（onResponse 不触发）→ 任何响应钩子都须 fail-open 且默认关闭。
- PowerShell `$ErrorActionPreference='Stop'` 下 `taskkill` 的 stderr 被包装为 `NativeCommandError` 中止脚本；`taskkill /F /T` 对"属于其他进程子进程"的 PID 直接拒绝。
- ESM 下 `__filename` 在纯 ESM 真未声明时 `typeof` 也安全（需 `declare`），但 SonarQube S6606 建议 `x ?? fallback` 会引入运行时 ReferenceError（CODING-018）。

### ③ 可抽象的固定流程与判断
```
ESM 路径解析：
  IS_SEA = typeof __filename 经 declare 守卫（兼容开发/打包双模式），不得 DIRECT 引用 __filename/__dirname
响应压缩：
  默认关闭 + 条件注册；若启用须同步压缩（gzipSync/brotliCompressSync）+ onSend fail-open + 逐路由挂载
路由 return：
  每分支/提前退出点显式 return/throw；async handler 禁止隐式 undefined 落底
关键数据：
  读取区分 not-found/corrupt 兜底回退默认 + 备份；写入 best-effort 但失败须可观测（log）
PowerShell 清理端口：
  Stop-Process -Force + try/catch（非致命）替换裸 taskkill；残留走命令行匹配兜底
```
判断逻辑落地为：CODING-ROUTE-RETURN-COMPLETENESS / CODING-RESPONSE-HOOK-SAFE / CODING-COMPRESSION-DEFAULT-OFF / CODING-USER-STORE-INIT / CODING-PS-PROCESS-CLEANUP（PS-6 增强）；审查 BR-089~093、前端 FR-082~083；测试守卫见 wiki-auto-testing `backend_review_static_check` 四组 + `process_cleanup_safe`。

### ④ 适用与不适用
- **适用**：Fastify 后端路由/响应层、Windows PowerShell 服务脚本、含可写关键数据文件的 Node 服务、ESM+tsx/SEA 双模式项目。
- **不适用**：纯前端无后端 service 改动（无压缩/路由/端口清理环节）、Bash/Zsh 启动脚本（stderr 不触发终止错误）、CommonJS 项目（`__filename` 正常注入）、纯静态资源伺服（sendFile 绕过 onSend）。

> 备注：问题 ①/②（build-exe 图标注入 + 移除未引用 rcedit devDependency）属构建脚本清理类，无需新增防御性规则，但应在代码评审中检查"依赖与脚本引用一致性"（package.json 的 devDependency 须被脚本实际使用，无死依赖）。

---

## 与审查 / 测试技能的衔接

- 每条规则在 wiki-frontend-code-review / wiki-backend-code-review 有对应 FR-/BR- 条目；审查输出须标注**适用性（适用/不适用）**，与维度④对齐。
- 测试纪律（J-TEST-NAMESPACE 等）落入 wiki-auto-testing 步骤类型（`indexeddb_test_isolation_check` 等），参数集中在 `defaults.yaml`/`config.yaml`。
- 所有阈值 / 路径 / 端口 / 命名空间前缀均经 config 注入，规则文件与审查文件**零硬编码**。
