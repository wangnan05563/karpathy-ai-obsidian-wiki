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

> 更多既有规则（Tauri、PowerShell、媒体生成、安装器、文件名管线、迁移脚本等）见 SKILL.md 路由表与各 `*-rule.md`。本表聚焦近几轮对话新提炼的标准。

---

## 维度三细化：可抽象的判断逻辑（Judgment Logic）

跨上述问题可抽取出 5 条通用判断，供新代码 / 新审查直接套用：

- **J-ISOLATION** — 多用户 / 多账户 / 多租户数据，必须以「用户/账户 id 命名空间」隔离，禁止共享可写单例；跨边界复用时先校验归属再写入。
- **J-NO-FALLBACK-SECRET** — 用户自带密钥场景，缺密钥直接拒绝（400），禁止回落到共享/默认密钥；密钥只走请求体，不落盘/不回显/不记日志。
- **J-PURE-OVERRIDE** — 配置/参数覆盖抽为**纯函数**（`??`/`?.` 合并，无 `!`/`as`），空/默认覆盖须回退原值，绝不能清空服务端共享能力。
- **J-FRESH-DIR-DEPLOY** — 受限环境部署写**全新目录**、不原地覆盖；spaRoot 启动时算一次，写完须重启；孤儿进程须先杀再起。
- **J-TEST-NAMESPACE** — 含状态的测试用唯一命名空间隔离，禁止 `beforeEach` 删库；后端重置模块态/mock；异步落盘断言多轮 flush。
- **J-SSML-SAFE** — 外部输入拼进 SSML/TTS 前必须校验 prosody 格式（rate/volume/pitch 白名单正则）+ 转义 `<>&` + 禁用不支持标签（express-as 在免费端点 1007）；前后端双重防护（前端先校验再下发，后端兜底校验）。
- **J-SYNC-BOUNDARY** — 子进程调用按"要同步结果 / 要异步事件"二选一 API：需同步结果用 `execFileSync`（带超时）或 `await` Promise，禁止把异步 `execFile` 当同步用；可用性检测用能力命令（如 `ffmpeg -version`）而非冗余探针。
- **J-NO-SILENT-FAIL** — 关键写失败必须传播（throw / log+throw），禁止空 catch 假成功；关键文件读取须区分 not-found 与 corrupt，损坏须备份+回退默认，禁止静默清零。
- **J-NO-HARDCODE** — 超时/阈值一律从配置键读取，禁止硬编码字面量（如 30000）；多层超时自下而上递增 ×1.5（与 BR-053 一致）。
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

---

## 与审查 / 测试技能的衔接

- 每条规则在 wiki-frontend-code-review / wiki-backend-code-review 有对应 FR-/BR- 条目；审查输出须标注**适用性（适用/不适用）**，与维度④对齐。
- 测试纪律（J-TEST-NAMESPACE 等）落入 wiki-auto-testing 步骤类型（`indexeddb_test_isolation_check` 等），参数集中在 `defaults.yaml`/`config.yaml`。
- 所有阈值 / 路径 / 端口 / 命名空间前缀均经 config 注入，规则文件与审查文件**零硬编码**。
