# Wiki Code Dev

Karpathy-Wiki 项目的通用编码规范与开发准则。规则与具体业务解耦，抽象为可跨模块复用的判断逻辑。

## 触发条件

- 新功能开发前加载规则
- Bug 修复前对照必检清单
- 代码重构前确认未违反硬约束
- Code Review 时作为规则源
- 不确定某写法是否合规时查询

## 规范提炼方法论（四维度复盘 → 规则）

本技能的规则不是凭空制定的，而是对**已解决问题的系统性复盘**沉淀而来。每遇到一次事故或返工，
按以下四维度复盘，并将结论固化为可复用规则（UF-/MS-/BR-/FR- 等）：

| 维度 | 复盘问题 | 产出 |
|------|---------|------|
| ① 成功步骤 | 这次是怎么修好的？哪些动作被验证有效？ | 可复制的修复流程骨架 |
| ② 不确定性与失败点 | 哪里踩坑/试错？环境约束是什么？（如沙箱无浏览器、safe-delete 钩子、Git-Bash 路径） | 防御性检查点 / 降级路径 |
| ③ 可抽象的流程与判断 | 哪些决策可参数化、可泛化到同类问题？ | 规则（严重级别 + 正/误示例）+ 对应 config 参数 |
| ④ 适用与不适用 | 这个规则在哪些场景成立？哪些场景是噪声？ | 规则的适用 / 不适用边界（写进 review 技能） |

**闭环**：复盘(①②③④) → 提炼为编码规则（本技能 references/） → 映射为审查要点（wiki-backend-code-review BR- / wiki-frontend-code-review FR-） → 参数全部落入各技能 `config/*.md`（零硬编码）。
每次新增规则须同步：① 在本技能 SKILL.md 路由表登记；② 在对应 review 技能加 BR-/FR- 条目；③ 在 review `config` 加参数段。

测试侧的四维度复盘范本见 [wiki-auto-testing references/testing-process-review.md](../../wiki-auto-testing/references/testing-process-review.md)。

## 加载策略

按需加载以节省 context token：

### 1. 基线（必读）
- [SKILL.md](SKILL.md) — 本文件
- [config/coding-standards-config.md](config/coding-standards-config.md) — 项目参数（路径锚点、缓存 TTL、白名单正则、降级策略）

### 2. 规则路由（按需）
根据任务类型选择性加载：

| 任务类型 | 加载规则文件 |
|---------|------------|
| 涉及文件读写/持久化 | [references/persistence-rule.md](references/persistence-rule.md) |
| 涉及内存缓存/写后读 | [references/cache-rule.md](references/cache-rule.md) |
| 涉及路径解析 | [references/path-resolution-rule.md](references/path-resolution-rule.md) |
| 涉及前端存储(localStorage/IndexedDB) | [references/storage-boundary-rule.md](references/storage-boundary-rule.md) |
| 涉及多源数据同步 | [references/single-source-rule.md](references/single-source-rule.md) |
| 涉及用户输入作文件名/路径 | [references/input-validation-rule.md](references/input-validation-rule.md) |
| 涉及错误处理/降级 | [references/fallback-rule.md](references/fallback-rule.md) |
| 涉及文件编辑/编码/中文/构建门禁 | [references/encoding-guard-rule.md](references/encoding-guard-rule.md) |
| 涉及 PowerShell/服务管理/端口 | [references/powershell-constraints-rule.md](references/powershell-constraints-rule.md) |
| 涉及新增路由/接口注册 | [references/route-registration-rule.md](references/route-registration-rule.md) |
| 涉及子进程/外部资源/异步赋值字段 | [references/null-guard-rule.md](references/null-guard-rule.md) |
| 涉及子进程/定时器/长连接/服务退出 | [references/graceful-shutdown-rule.md](references/graceful-shutdown-rule.md) |
| 涉及敏感字段/API Key/密码/GET 配置接口 | [references/sensitive-field-masking-rule.md](references/sensitive-field-masking-rule.md) |
| 涉及后端/前端 types.ts 同步 | [references/type-sync-rule.md](references/type-sync-rule.md) |
| 涉及 flex 布局/滚动容器/内容裁切 | [references/scroll-container-rule.md](references/scroll-container-rule.md) |
| 涉及 SPA 内部跳转/视图切换/CustomEvent | [references/spa-navigation-rule.md](references/spa-navigation-rule.md) |
| 涉及检查更新/版本对比/缓存轮询 | [references/update-check-rule.md](references/update-check-rule.md) |
| 涉及 SVG/资源文件创建/HTML 破缓存 | [references/svg-resource-rule.md](references/svg-resource-rule.md) |
| 涉及 vite build/构建产物验证 | [references/build-verification-rule.md](references/build-verification-rule.md) |
| 涉及 PowerShell 字符串验证 | [references/powershell-string-verification-rule.md](references/powershell-string-verification-rule.md) |
| 涉及浏览器自动化/MCP 降级 | [references/browser-automation-fallback-rule.md](references/browser-automation-fallback-rule.md) |
| 涉及矢量图标设计/主题感知 | [references/theme-aware-icon-rule.md](references/theme-aware-icon-rule.md) |
| 涉及导航栏折叠/展开/tooltip | [references/nav-dual-mode-rule.md](references/nav-dual-mode-rule.md) |
| 涉及 vue-tsc 幽灵错误/类型检查缓存 | [references/typecheck-cache-rule.md](references/typecheck-cache-rule.md) |
| 涉及调用他人 composable/store | [references/composable-api-rule.md](references/composable-api-rule.md) |
| 涉及类型升级 T→U/混合类型分流 | [references/mixed-type-dispatch-rule.md](references/mixed-type-dispatch-rule.md) |
| 涉及 .vue 文件 script 块结构 | [references/sfc-single-script-rule.md](references/sfc-single-script-rule.md) |
| 涉及 E2E 测试运行前置检查 | [references/e2e-precheck-rule.md](references/e2e-precheck-rule.md) |
| 涉及测试用例选择器同步更新 | [references/test-case-sync-rule.md](references/test-case-sync-rule.md) |
| 涉及阅读型视图布局/输入区固定 | [references/reading-viewport-rule.md](references/reading-viewport-rule.md) |
| 涉及目录结构/文件迁移/gitignore/脚本命名/文档归并/路径验证/搜索验证 | [references/project-structure-rule.md](references/project-structure-rule.md) |
| 涉及主题色变量映射/硬编码颜色替换/alpha 变体/语义变量选择 | [references/theme-color-mapping-rule.md](references/theme-color-mapping-rule.md) |
| 涉及 Tauri 2.x 自定义命令 invoke 新增/报错 Plugin not found/not allowed | [references/tauri-acl-rule.md](references/tauri-acl-rule.md) |
| 涉及 Tauri 2.x 外部 URL 加载/报错 URL: local only/capability 配置 | [references/tauri-external-url-rule.md](references/tauri-external-url-rule.md) |
| 涉及 Tauri 多 webview 窗口状态隔离/initialization_script/localStorage 污染 | [references/tauri-webview-isolation-rule.md](references/tauri-webview-isolation-rule.md) |
| 涉及 Tauri 透明窗口 transparent/floating-active/毛玻璃背景未透明 | [references/tauri-transparent-window-rule.md](references/tauri-transparent-window-rule.md) |
| 涉及 Tauri 构建脚本/SPA 构建/产物验证/递归构建死循环 | [references/tauri-build-script-rule.md](references/tauri-build-script-rule.md) |
| 涉及 Tauri 自定义标题栏/drag-region 吞 click/拖动与点击冲突 | [references/tauri-drag-click-conflict-rule.md](references/tauri-drag-click-conflict-rule.md) |
| 涉及 PowerShell 调用 cargo/rustc/go build 的 stderr 进度中断 | [references/powershell-stderr-rule.md](references/powershell-stderr-rule.md) |
| 涉及认证中间件/publicPaths/全局 preHandler | [references/auth-endpoint-classification-rule.md](references/auth-endpoint-classification-rule.md) |
| 涉及 Windows 文件删除/目录操作/fs.rm 静默失败 | [references/windows-file-operation-rule.md](references/windows-file-operation-rule.md) |
| 涉及 DOM 结构变更保留测试兼容 class 名 | [references/dom-compat-class-rule.md](references/dom-compat-class-rule.md) |
| 涉及 flex 容器高度自适应（删除固定元素后 calc(100vh) 失效） | [references/flex-viewport-adapt-rule.md](references/flex-viewport-adapt-rule.md) |
| 涉及状态机简化（多态→二态、折叠一步到位） | [references/state-machine-simplify-rule.md](references/state-machine-simplify-rule.md) |
| 涉及 PowerShell 长时进程管道陷阱（EPIPE/退出码异常） | [references/powershell-long-process-rule.md](references/powershell-long-process-rule.md) |
| 涉及功能回滚（按删除反向顺序恢复） | [references/rollback-minimal-rule.md](references/rollback-minimal-rule.md) |
| 涉及前端 .ts 被 .js 影子覆盖 / vite resolve.extensions / 构建双验证 | [references/frontend-ts-js-shadowing-rule.md](references/frontend-ts-js-shadowing-rule.md) |
| 涉及 Unicode 分词 / 去重 / 压缩 / 淘汰的确定性文本处理 | [references/deterministic-text-processing-rule.md](references/deterministic-text-processing-rule.md) |
| 涉及运行时数据目录隐私 / .gitignore / 持久化默认 | [references/runtime-data-privacy-rule.md](references/runtime-data-privacy-rule.md) |
| 涉及 SEA 多机打包 / config 可移植默认 / dataDir 派生 | [references/config-portable-defaults-rule.md](references/config-portable-defaults-rule.md) |
| 涉及安装器防覆盖 / SEA 用户数据目录解析 / 资源路径与用户数据路径分离 / 首次落盘干净默认 | [references/packaging-userdata-rule.md](references/packaging-userdata-rule.md) |
| 涉及限流韧性 / 真实 IP / 滑动窗口 / 时钟无关测试 | [references/rate-limit-resilience-rule.md](references/rate-limit-resilience-rule.md) |
| 涉及新增路由测试覆盖 / 端点测试 / 前后端类型同步 | [references/api-endpoint-test-coverage-rule.md](references/api-endpoint-test-coverage-rule.md) |
| 涉及第三方 UI 组件库（Element Plus 等）API 升级 / 弃用属性迁移 / 主版本升级前全量扫描 | [references/third-party-ui-api-currency-rule.md](references/third-party-ui-api-currency-rule.md) |
| 涉及用户输入作文件名/路径（中文/全角/CJK 清洗 + 内部前缀剥离 + `..` 二次校验） | [references/user-upload-filename-rule.md](references/user-upload-filename-rule.md) |
| 涉及数据迁移/修复脚本（dry-run 默认 / 幂等 / 无丢失 / 冲突后缀 / 函数式替换 / pageCache） | [references/data-repair-script-safety-rule.md](references/data-repair-script-safety-rule.md) |
| 涉及语音合成/TTS/朗读/浏览器 Web Speech API / neural 音色优雅降级 | [references/tts-neural-fallback-rule.md](references/tts-neural-fallback-rule.md) |
| 涉及 SPA 实时部署目录解析（最新时间戳目录 + 完整性门禁）/ `/wiki/*` within-root 防穿越 / 部署写全新目录不覆盖 | [references/spa-live-deploy-rule.md](references/spa-live-deploy-rule.md) |
| 涉及多账户会话隔离（Pinia 模块级共享 ref 跨账户未重置 / 复用 id 持久化未校验归属 / 会话按 ownerId 隔离） | [references/frontend-session-isolation-rule.md](references/frontend-session-isolation-rule.md) |
| 涉及 BYOK 多用户密钥代理（前端本地命名空间隔离 / 密钥仅经请求体下发不落服务端 / 覆盖纯函数 + 缺密钥不回落服务端共享） | [references/byok-per-user-override-rule.md](references/byok-per-user-override-rule.md) |
| 涉及流式回答增量持久化与断点续答（SSE 部分答案仅内存 / 切页 abort 在途流 / 刷新丢失中间态） | [references/streaming-resume-rule.md](references/streaming-resume-rule.md) |
| 涉及隔离测试纪律（含状态测试用唯一命名空间而非 beforeEach deleteDatabase / fake-indexeddb 异步多轮 flush / 后端模块态与 mock 隔离） | [references/indexeddb-test-isolation-rule.md](references/indexeddb-test-isolation-rule.md) |
| 涉及 SSML / TTS prosody 注入防护（用户文本 `<>&` 转义 / rate·volume·pitch 格式校验 / 禁用 express-as / 免费端点 1007） | [references/ssml-injection-rule.md](references/ssml-injection-rule.md) |
| 涉及子进程异步/同步正确性（execFile 异步当同步用 / execFileSync 带超时 / 需同步结果须 await） | [references/child-process-sync-rule.md](references/child-process-sync-rule.md) |
| 涉及关键写不得静默吞错（saveUsers 等持久化写失败须传播 / 禁止空 catch 假成功） | [references/critical-write-no-swallow-rule.md](references/critical-write-no-swallow-rule.md) |
| 涉及关键数据文件损坏防护（loadUsers 区分 not-found 与 corrupt / 损坏备份回退默认 / 禁静默清零） | [references/file-corruption-guard-rule.md](references/file-corruption-guard-rule.md) |
| 涉及类型安全禁止 `as any` 绕过（提取真实类型 InjectOptions['method'] / 类型守卫 / 迁移期标注） | [references/type-safe-no-any-rule.md](references/type-safe-no-any-rule.md) |
| 涉及超时/阈值可配置化（禁止硬编码 30000 / 从配置读取超时键 / 多层递增） | [references/config-timeout-rule.md](references/config-timeout-rule.md) |
| 涉及去除冗余探测/探针（isFfmpegAvailable 用 `ffmpeg -version` 能力检测 / 禁 ffprobe 冗余探测） | [references/no-redundant-probe-rule.md](references/no-redundant-probe-rule.md) |
| 涉及归档/落盘文件名唯一性（同线程同日多条归档互相覆盖 / 派生键非全局唯一须追加随机后缀 / 冲突拒绝） | [references/generated-filename-uniqueness-rule.md](references/generated-filename-uniqueness-rule.md) |
| 涉及服务端解析客户端日期串（非法 `ts` → RangeError → 500 / 禁 `new Date(str).toISOString()` / 安全解析回退默认） | [references/safe-client-date-parse-rule.md](references/safe-client-date-parse-rule.md) |
| 涉及客户端传下标访问数组（messageIndex 非整数 → undefined 访问 → 500 / Number.isInteger 校验短路） | [references/integer-index-validation-rule.md](references/integer-index-validation-rule.md) |
| 涉及注入 `[[wikilink]]`/Markdown 链接（换行破坏/空串脏链接 / 注入前去换行+trim+去空+字符集清洗） | [references/wikilink-sanitization-rule.md](references/wikilink-sanitization-rule.md) |
| 涉及创建型写入端点空内容（空串/no-op 落盘污染 / 必填字段缺失即拒绝） | [references/empty-content-rejection-rule.md](references/empty-content-rejection-rule.md) |
| 涉及归档内容取源解耦（服务端不持久化会话→误报过期 / 请求体优先取内容 / 前端门控随后端契约同步放宽） | [references/persistence-client-content-decoupling-rule.md](references/persistence-client-content-decoupling-rule.md) · [references/capability-gating-sync-rule.md](references/capability-gating-sync-rule.md) |
| 涉及编辑已发送消息并重发（removeMessagesFrom 后必须 submitQuestion 重插 / 先停 in-flight / 未变不重发） | [references/edit-resend-rule.md](references/edit-resend-rule.md) |
| 涉及流式聊天自动贴底滚动（双 rAF / 用户上滑暂停 / 图片加载补滚 / 监听挂载卸载绑定） | [references/streaming-autoscroll-rule.md](references/streaming-autoscroll-rule.md) |
| 涉及成对操作按钮样式一致性（确认/取消幽灵按钮 / 主题变量 / 单主操作） | [references/button-style-consistency-rule.md](references/button-style-consistency-rule.md) |
| 涉及消息气泡进入编辑态撑满问答列宽（align-items:stretch / width:100% 覆盖已发送窄宽） | [references/editbox-width-rule.md](references/editbox-width-rule.md) |
| 涉及 Vue 3 / Pinia state 写入 IndexedDB（reactive 代理无法被 structuredClone 克隆 → `[object Array] could not be cloned` 静默丢数据 / toRaw 只剥顶层 / 须整树深拷贝） | [references/idb-reactive-clone-rule.md](references/idb-reactive-clone-rule.md) |
| 涉及服务端权限隔离（auth 感知守卫工厂 createIsolationGuards / 写端点 requireAdmin 注入 / auth.enabled=false 单租户直通 / 服务端 ownerId 盖章不信任客户端 body） | [references/isolation-guard-rule.md](references/isolation-guard-rule.md) |
| 涉及限流/审计真实客户端 IP（clientIpFromRequest 复合键 request.ip\|xffFirst / 防 XFF 伪造 / trustProxy=false） | [references/isolation-guard-rule.md](references/isolation-guard-rule.md) |
| 涉及认证/关键异步请求超时兜底（登录/会话校验无超时悬挂 / AbortController + 可配置阈值 / 超时文案可重试） | [references/auth-request-timeout-rule.md](references/auth-request-timeout-rule.md) |
| 涉及异步操作 loading 复位（登录/提交 handler 须在 try/finally 复位 loading / 禁永久「登录中」灰显） | [references/auth-loading-reset-rule.md](references/auth-loading-reset-rule.md) |
| 涉及路由 return 完整性（每个分支必须 return/reply / 漏 return 触发双发响应 ERR_STREAM_WRITE_AFTER_END） | [references/route-return-completeness-rule.md](references/route-return-completeness-rule.md) |
| 涉及响应/序列化钩子安全（onSend/onResponse 不得阻塞/抛错挂死全量 API / 须 fail-open） | [references/response-hook-safe-rule.md](references/response-hook-safe-rule.md) |
| 涉及响应压缩默认关闭（@fastify/compress 默认 off / 条件注册 / 阈值参数化） | [references/compression-default-off-rule.md](references/compression-default-off-rule.md) |
| 涉及用户库初始化完整性（users.json 空壳/损坏须备份回退默认 / 禁静默清零 / 首次运行非空默认） | [references/user-store-init-rule.md](references/user-store-init-rule.md) |
| 需要参考历史复盘/工作流模板 | [references/development-workflow.md](references/development-workflow.md) · [references/retrospective-synthesis.md](references/retrospective-synthesis.md)（四维度复盘综合索引：事故→规则→审查→测试闭环） |
| 不确定加载哪些 | 全部加载（约 50KB） |