# Wiki Code Dev

Karpathy-Wiki 项目的通用编码规范与开发准则。规则与具体业务解耦，抽象为可跨模块复用的判断逻辑。

## 触发条件

- 新功能开发前加载规则
- Bug 修复前对照必检清单
- 代码重构前确认未违反硬约束
- Code Review 时作为规则源
- 不确定某写法是否合规时查询

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
| 需要参考历史复盘/工作流模板 | [references/development-workflow.md](references/development-workflow.md) |
| 不确定加载哪些 | 全部加载（约 50KB） |