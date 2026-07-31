# 完整文档结构

> 从 SKILL.md 拆分而来

```
wiki-code-dev/
├── SKILL.md                          # 本文件 - Skill 定义
├── config/
│   ├── tech-stack.json               # 技术栈版本、路径、SSE 事件类型与 ESM 参数配置
│   └── coding-standards-config.md    # 编码规范参数表
├── assets/
│   └── templates/                    # 代码模板
│       ├── backend/
│       │   ├── route.ts              # Fastify SSE 路由模板
│       │   ├── workflow.ts           # Harness 工作流模板
│       │   └── vault-service.ts      # Vault 文件系统模板
│       └── frontend/
│           ├── view.tsx              # Vue 视图模板
│           ├── store.ts              # Pinia Store 模板
│           └── types.ts              # 类型定义模板
└── references/                       # 参考文档（按需加载）
    ├── architecture-patterns.md      # 架构模式知识库
    ├── project-rules.md              # 项目硬约束
    ├── development-workflow.md       # 开发工作流（四维度复盘）
    ├── encoding-and-io.md            # 编码与 I/O 规范
    ├── encoding-guard-rule.md        # 编码守卫规则（Edit 前/构建前门禁）
    ├── esm-module-guard-rule.md      # ESM 模块守卫规则（CODING-017~020）
    ├── async-reliability-rule.md     # Async 可靠性守卫规则（CODING-021~025）
    ├── powershell-constraints-rule.md # PowerShell 约束规则
    ├── error-handling.md             # 错误处理规范
    ├── sse-streaming.md              # SSE 流式输出规范
    ├── filesystem-vault.md           # 文件系统/Vault 操作规范
    ├── harness-integration.md        # Harness 集成规范
    ├── theming-and-css-variables.md  # 主题系统与 CSS 变量规范
    ├── multi-instance-config.md      # 多实例配置与状态一致性规范
    ├── faq.md                        # 常见问题
    ├── persistence-rule.md           # 持久化规则
    ├── cache-rule.md                 # 缓存规则
    ├── path-resolution-rule.md       # 路径解析规则
    ├── storage-boundary-rule.md      # 存储边界规则
    ├── single-source-rule.md         # 单一权威源规则
    ├── input-validation-rule.md      # 输入校验规则
    ├── fallback-rule.md              # 降级规则
    ├── route-registration-rule.md    # 路由注册规则
    ├── null-guard-rule.md            # 空值守卫规则
    ├── graceful-shutdown-rule.md     # 优雅停止规则
    ├── sensitive-field-masking-rule.md # 敏感字段脱敏规则
    ├── type-sync-rule.md             # 类型同步规则
    ├── scroll-container-rule.md      # 滚动容器规则
    ├── spa-navigation-rule.md       # SPA 导航规则
    ├── update-check-rule.md          # 更新检查规则
    ├── svg-resource-rule.md          # SVG 资源规则
    ├── build-verification-rule.md    # 构建验证规则
    ├── powershell-string-verification-rule.md # PowerShell 字符串验证规则
    ├── browser-automation-fallback-rule.md # 浏览器自动化降级规则
    ├── theme-aware-icon-rule.md      # 主题感知图标规则
    ├── nav-dual-mode-rule.md         # 导航栏双模式规则
    ├── typecheck-cache-rule.md       # 类型检查缓存清理规则（CODING-026）
    ├── composable-api-rule.md       # Composable API 先读后用规则（CODING-027）
    ├── mixed-type-dispatch-rule.md  # 混合类型运行时分流规则（CODING-028）
    ├── sfc-single-script-rule.md     # Vue SFC 单 script 块规则（CODING-029）
    ├── e2e-precheck-rule.md          # E2E 测试前置服务检查规则（CODING-030）
    ├── test-case-sync-rule.md        # 测试用例与代码结构同步规则（CODING-031）
    ├── reading-viewport-rule.md     # 阅读视野优化规则（CODING-032）
    ├── project-structure-rule.md   # 项目目录结构规则（CODING-033~040）
    ├── theme-color-mapping-rule.md # 主题色变量映射规则（CODING-041~046）
    ├── tauri-acl-rule.md            # Tauri 2.x ACL 三层声明规则（CODING-047）
    ├── tauri-external-url-rule.md   # Tauri 2.x 外部 URL capability 配置规则（CODING-048）
    ├── tauri-webview-isolation-rule.md # Tauri 多 webview 状态隔离规则（CODING-049）
    ├── tauri-transparent-window-rule.md # Tauri 透明窗口 CSS 全覆盖规则（CODING-050）
    ├── tauri-build-script-rule.md   # Tauri 构建脚本 SPA 构建步骤规则（CODING-051）
    ├── tauri-drag-click-conflict-rule.md # Tauri drag-region 与 click 冲突规则（CODING-052）
    ├── powershell-stderr-rule.md    # PowerShell 调用 cargo 的 stderr 处理规则（CODING-053）
    ├── auth-endpoint-classification-rule.md # 认证端点分类守卫规则（CODING-054）
    ├── windows-file-operation-rule.md   # Windows 文件操作验证规则（CODING-055）
    ├── external-api-contract-rule.md    # 外部 API 集成契约规则（CODING-056）
    ├── timeout-tier-rule.md             # 超时分级策略规则（CODING-057）
    ├── api-key-resolution-rule.md       # 多源密钥解析规则（CODING-058）
    ├── long-task-architecture-rule.md   # 长/短任务架构分离规则（CODING-059）
    ├── media-archive-frontmatter-rule.md # 媒体归档 frontmatter 标准化规则（CODING-060）
    ├── session-store-rule.md            # 会话存储双层淘汰 + 防篡改规则（CODING-061）
    ├── prompt-store-rule.md             # prompt 单点存储规则（CODING-062）
    ├── sse-event-dispatch-rule.md       # SSE 事件对象映射分发规则（CODING-063）
    ├── sse-stream-error-rule.md         # SSE 流消费错误处理规则（CODING-064）
    ├── long-task-polling-ui-rule.md     # 长任务轮询 UI 模式规则（CODING-065）
    ├── event-delegation-rule.md         # 事件委托 + 生命周期清理规则（CODING-066）
    ├── heavy-library-rule.md            # 第三方重库动态加载规则（CODING-067）
    ├── parallel-loading-rule.md         # 多资源并行加载规则
    ├── timeout-chain-rule.md            # 超时阈值链式匹配规则
    ├── third-party-error-guard-rule.md  # 第三方库错误防护三层法规则
    ├── control-layering-rule.md         # 控件分层规则
    ├── folding-panel-event-rule.md      # 折叠面板事件冲突规则
    ├── document-structure.md            # 完整文档结构（本文件）
    ├── checklist-details.md             # 必检清单（详细版）
    └── changelog.md                     # 版本历史（完整记录）
```
