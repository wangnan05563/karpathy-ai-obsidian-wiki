---
name: wiki-code-dev
description: "Karpathy-Wiki 项目编码规范与开发准则。在新功能开发、Bug 修复、代码重构前加载，提供持久化、缓存、路径解析、存储边界、输入校验等通用规则。所有规则与具体业务解耦，可适配不同模块。"
whenToUse: "用户要求在 Karpathy Wiki 项目（d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki）进行任何代码层面的开发/修改/重构/修复/测试编写工作，包括后端 TypeScript/Fastify 代码、前端 Vue 3/TypeScript 代码、SSE 流式功能、Harness 集成、Vault 文件系统操作"
triggers:
  - "在 Karpathy Wiki/karpathy-wiki 项目 写/做/添加/实现/新增/开发 一个 功能/接口/页面/组件"
  - "修复/解决 wiki bug/问题/缺陷/报错/异常"
  - "wiki 项目 重构/优化/改造/升级 现有代码"
  - "wiki 项目 编写 测试/路由/store/工作流/Vault 服务"
  - "wiki 项目 实现/对接 SSE 流式输出"
  - "wiki 项目 涉及 Harness/EngineAdapter/LLM Agent"
---

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
| 需要参考历史复盘/工作流模板 | [references/development-workflow.md](references/development-workflow.md) |
| 不确定加载哪些 | 全部加载（约 50KB） |

### 3. 示例按需
仅当生成修复代码时加载 `references/examples/<rule>-examples.md`。

## 硬约束（不可违反）

1. **路径解析禁用 CWD**：持久化文件路径必须基于 `import.meta.url` 或配置的锚点目录，禁止依赖 `process.cwd()`
2. **写后即刷**：任何写盘函数必须同步刷新对应内存缓存，禁止依赖 TTL 自然过期
3. **单一权威源**：每类数据只能有一个权威存储，其他存储仅作缓存且必须可降级
4. **存储边界明确**：跨 origin/进程/会话共享的数据必须用后端持久化，浏览器存储仅作单 origin 缓存
5. **输入白名单**：用户输入作为文件名/路径时必须用白名单正则校验，禁止直接拼接
6. **降级不阻断**：后端不可用时前端必须能降级到本地缓存，主流程不阻断
7. **配置化无硬编码**：所有参数（路径、TTL、正则、阈值）必须在 config 文件管理，规则文件仅描述模式
8. **UTF-8 无 BOM**：所有源文件与 meta 文件 UTF-8 无 BOM（Windows cmd.exe 兼容）
9. **编码守卫**：Edit/Write 含非 ASCII 字符文件前必须严格 UTF-8 解码检测；非 UTF-8 文件用 `encoding_fallback` 读写；构建前必须执行 `encoding_scan_command` 门禁
10. **PowerShell 约束**：禁用 `&&`（用 `command_separator`）、禁用只读变量赋值（`readonly_vars`）、禁用 `cmd /c`（`blocked_commands`）；工作目录通过 `cwd_param` 指定而非 `cd`
11. **路由注册守卫**：新增 `routes/*.ts` 文件必须在 `entry_file` 同步 import 与调用 `register_function_pattern`；自动发现框架（NestJS 等）可豁免
12. **空值守卫**：由 `async_assignment_keywords`（spawn/exec/connect 等）赋值的字段使用前必须 `if (!x)` 守卫并重建/抛错，禁止直接访问
13. **优雅停止**：创建子进程/定时器/长连接的模块必须注册 `shutdown_signals` 钩子，按"子进程→定时器→连接"顺序清理后 `process.exit`
14. **敏感字段脱敏**：GET 接口返回字段名匹配 `sensitive_field_patterns` 时必须脱敏 + 附 `configured` 标志；POST 空串语义为"不修改"
15. **类型同步**：后端 `backend_types_path` 与前端 `frontend_types_path` 同名 interface 字段必须对齐，提交前通过两端 `typecheck_command` 门禁
16. **滚动容器单一职责**：容器链路上 `overflow-y: auto` 层数不得超过 `scroll_container.max_overflow_layers`（默认 1）；`flex-direction: column + flex: 1` 容器内的自然高度子项必须 `flex-shrink: 0`
17. **SPA 内部跳转**：跨组件视图切换必须通过 `spa_navigation.event_name_pattern` 派发 CustomEvent，由入口组件监听切换；监听器必须在 onMounted/onBeforeUnmount 配对管理
18. **更新检查缓存**：`/api/about/check-update` 类接口必须有 `check_update.cache_ttl_ms`（默认 5 分钟）后端缓存；轮询间隔 `poll_interval_ms` 必须 ≥ `cache_ttl_ms`；离线模式 `offline_mode: true` 时固定返回 `has_update: false`
19. **SVG/资源文件创建**：含中文 SVG 必须用纯 ASCII 或 UTF-8 无 BOM；Write 工具不可靠时用 PowerShell `[System.IO.File]::WriteAllText` + `[System.Text.UTF8Encoding]::new($false)` 重写；HTML 引用 SVG 资源时必须加 `?v={version}` 版本参数破浏览器缓存
20. **构建产物验证三要素**：vite build 后必须验证：① HTTP 状态码 200 ② Content-Length 与磁盘文件大小一致 ③ bundle 中包含新增的关键 CSS 类/字符串标识（如新组件的 class 名）
21. **PowerShell 字符串验证模式**：禁用 `curl.exe -s` 管道赋值给变量再 `.Contains()`（PowerShell 变量捕获会混乱），改用 `Invoke-WebRequest` + `.Content.Contains()` 模式
22. **浏览器自动化降级链**：MCP 不可用时按链路降级：Playwright MCP → browser_use subagent → PowerShell + curl.exe；每级降级须记录降级原因，不可静默失败
23. **主题感知图标设计**：矢量图标必须用 `currentColor` + CSS 变量自动跟随主题；stroke 线条风格统一；禁止硬编码 stroke 色值；通过 `filter: drop-shadow(0 0 Xpx currentColor)` 实现主题色光晕效果
24. **导航栏双模式设计**：菜单项较多时（> `nav_threshold`，默认 7）应支持折叠/展开双模式；折叠模式用纯 CSS hover tooltip 显示菜单名（无 JS 依赖）；切换用 Vue Transition `mode="out-in"`；折叠状态持久化到 localStorage
25. **Async 可靠性**：async 调用必须设置超时（`asyncio.wait_for` / `Promise.race`）；事件循环阻塞场景必须用线程级心跳（`threading.Thread` / `worker_threads`，禁止 `asyncio.Task`）；状态文件 `ts` 字段更新必须独立于业务事件循环；超时必须提供兜底数据（`best_holder`）；长时任务必须多层超时防护
26. **类型检查缓存清理**：vue-tsc 报告与源文件不一致的"幽灵错误"时，必须先清理 `typecheck_cache.incremental_cache_files` + `vite_cache_dirs` + `stale_artifact_patterns` 再重新检查，禁止用 `as any` / `!` / `@ts-ignore` 绕过（CODING-026）
27. **Composable API 先读后用**：使用非自己编写的 composable / hook / store 前必须 Read 源码确认导出形状、方法签名、setup 顺序；诊断代码禁止调用 `$dispose` / `_s.delete` 重建运行时 store（CODING-027）
28. **混合类型运行时分流**：类型从 T 升级为 U 时必须用 helper 函数（`isXxx` 命名）+ `typeof` / `in` / `instanceof` 运算符运行时分流，禁止用 `as any` / `as unknown as U` 强制断言（CODING-028）
29. **Vue SFC 单 script 块**：`.vue` 文件只能有一个 `<script setup lang="ts">` 块；例外情况（如 name 导出、inheritAttrs:false）必须显式注释 `// 例外：` 说明用途（CODING-029）
30. **E2E 测试前置服务检查**：运行 E2E 测试前必须检查 `required_ports` 端口监听 + `health_check_endpoint` 健康检查，失败时中止测试并提示启动脚本，禁止直接运行用例（CODING-030）
31. **测试用例与代码结构同步**：代码变更影响 DOM 结构（class/id/层级）时必须同步更新测试用例选择器，禁止 try/except 静默吞掉选择器失效错误，代码与测试用例必须在同一 commit（CODING-031）
32. **阅读视野优化与输入区固定**：阅读型视图标题头占比 ≤ `max_header_ratio`（默认 15%）；内容区 ≥ `min_content_ratio`（默认 75%）；输入区必须 `position: sticky; bottom: 0` + 毛玻璃背景 + `z-index` ≥ 2（CODING-032）
33. **目录结构分离**：源码/运行时数据/构建产物/外部工具链/文档必须分离到不同顶层目录（`source_dirs`/`runtime_data_dir`/`build_output_dirs`/`external_toolchain_dirs`/`docs_base_dir`），禁止混放（CODING-033）
34. **脚本命名统一**：同目录下脚本命名风格必须统一（`naming_style` 默认 kebab-case，`naming_language` 默认 en），bat 仅作 ps1 薄包装（`bat_role` 默认 thin-wrapper，`bat_max_lines` 默认 5），禁止中英文混杂（CODING-034）
35. **.gitignore 完整性**：运行时产物/构建产物/外部工具链/二进制 wrapper 必须在 .gitignore 登记；已跟踪文件需 `git rm --cached` 移除索引；变更后必须执行四步验证（更新→`git check-ignore -v`→`git ls-files`→`git rm --cached`）（CODING-035）
36. **文档归并**：项目文档统一到 `docs_base_dir`（默认 `docs/`）下按 `docs_subdirs` 分类，禁止散落在项目根或源码目录；开发规范禁止放在源码目录（CODING-036）
37. **运行时数据外迁**：运行时生成的数据（`runtime_data_patterns`：raw/entities/queries/log.md/index.md）必须外迁到 `runtime_data_dir`（默认 `data/vault/`），源码中只保留 `seed_data_patterns` 种子数据；迁移后必须同步更新 `config_files_to_update` 中所有配置文件（CODING-037）
38. **file: 协议路径验证**：package.json 中 `file:` 协议引用路径必须用 `verify_command`（默认 `Resolve-Path`）验证解析结果，`manual_calculation_forbidden` 为 true 时禁止手动计算 `../` 层级（CODING-038）
39. **搜索结果交叉验证**：Glob/Grep/LS 任一方法未找到目标时，必须用 `fallback_search_tools` 交叉验证；`cross_verify_required` 为 true 时禁止基于单一方法的阴性结果下结论；LS 输出超 `ls_truncate_threshold`（默认 40000 字符）时须用 Glob 或 Test-Path 补充验证（CODING-039）
40. **构建产物源码化**：编译生成的二进制 wrapper（`binary_extensions`：.exe/.dll）必须保留 `source_extensions`（.c/.rs）源码入库，二进制产物 gitignore，`setup_script_files` 中必须包含自动编译步骤（CODING-040）
41. **主题色变量映射三步法**：替换硬编码颜色值必须按「读变量清单→设计映射表→精准替换」三步执行，禁止跳过清单直接猜测变量名（CODING-041）
42. **主题色白名单**：`rgba(255,255,255,X)` / `transparent` / `inherit` / `currentColor` 为允许硬编码，其他所有 `rgba()` / `rgb()` / `#hex` / `hsl()` 必须替换为 CSS 变量（CODING-042）
43. **alpha 变体命名规范**：alpha 变体变量名必须为 `--accent-{color}-a{NN}`，`{NN}` 必须从 `theme_color_mapping.allowed_alpha_values` 列表选取，禁止使用未定义的 alpha 值（CODING-043）
44. **语义变量优先级**：选择 CSS 变量必须按「场景背景 > 卡片背景 > 文字 > 边框 > 阴影 > 滚动条」语义优先级判断，禁止跨语义层选择变量（CODING-044）
45. **编辑工具选择原则**：修改含非 ASCII 字符的文件必须优先使用 Edit 精准替换，禁止使用 Write 重写整个文件（防止编码破坏），修改范围 <50% 时单次 Edit，>50% 时分多次 Edit（CODING-045）
46. **类型检查双重门禁**：代码修改涉及类型变更时必须执行后端 `tsc --noEmit` + 前端 `vue-tsc --noEmit` 双重门禁，退出码均为 0 才允许提交（CODING-046）
47. **Tauri ACL 三层声明**：Tauri 2.x 新增 `invoke` 命令必须同步在 `build.rs`（`AppManifest::commands`）+ `capabilities/default.json`（`permissions` 数组含 `allow-<cmd>`）+ `src/lib.rs`（`generate_handler!`）三层声明；'Plugin not found'→第1层缺失，'not allowed'→第2层缺失，'command X not found'→第3层缺失（CODING-047）
48. **Tauri 外部 URL capability 配置**：Tauri 2.x 加载外部 HTTP/HTTPS URL 必须在 capability 的 `remote.urls` 子字段配置（非顶层 `urls`），URL 模式支持通配符 `http://localhost:PORT/*`；'URL: local only' → `remote.urls` 未配置或 URL 放错位置（CODING-048）
49. **Tauri 多 webview 状态隔离**：同源多 webview 禁止用 `initialization_script` 写 `localStorage`（共享存储会污染），必须用 `webview.eval()` 设置 `window` 属性（JS context 隔离）；`WebviewUrl::External` 的 hash 不可靠，禁止用作模式检测信号（CODING-049）
50. **Tauri 透明窗口 CSS 全覆盖**：`transparent(true)` 时必须覆盖 `html` + `body` + `#app` + 所有容器元素（`*`）的 `background-color: transparent !important`，仅设置单一元素会导致默认背景透出；scoped CSS 必须用 `:global()` 突破作用域限制（CODING-050）
51. **Tauri 构建脚本 SPA 构建步骤**：`tauri-build-debug.ps1` 与 `tauri-build-release.ps1` 必须包含「清理旧产物→构建 SPA→产物验证→构建 Tauri」四步；SPA 构建用 `pnpm --filter <pkg> build`（禁止 `pnpm run build`，递归构建风险）；验证含 mtime 对比 + JS chunk 关键字符串搜索（CODING-051）
52. **Tauri drag-region 与 click 冲突**：`data-tauri-drag-region` 会吞掉 click 事件，需同时支持拖动与点击的元素必须用 JS 区分：`mousedown` 记录位置，`mousemove` 超 5px 触发 `invoke('start_dragging')`，`mouseup` 未超阈值视为 click；配合 Rust 端 `start_dragging` 命令（需 ACL 三层声明）（CODING-052）
53. **PowerShell 调用 cargo 的 stderr 处理**：调用 `cargo`/`rustc`/`go build` 等输出 stderr 进度的工具必须用 `Start-Process -NoNewWindow -Wait -PassThru` 替代直接调用，避免 `$ErrorActionPreference=Stop` 拦截 stderr 进度；用 `$process.ExitCode` 判断真实错误（0=成功），stderr 有输出不代表失败（CODING-053）

## 开发流程

### 新功能开发
1. 加载 config + 相关规则文件
2. 识别涉及的存储边界（前端/后端/文件/缓存）
3. 设计数据流：明确权威源、缓存层、降级路径
4. 编码时对照必检清单
5. 若新增路由文件 → 同步在 `entry_file` 导入与注册
6. 若涉及子进程/定时器/长连接 → 注册 `shutdown_signals` 清理钩子
7. 若新增 GET 配置接口 → 检查响应字段是否匹配敏感模式并脱敏
8. 若后端 types.ts 新增/修改 interface → 同步前端 types.ts
9. 编写端到端验证（含缓存刷新、降级、边界条件）

### Bug 修复
1. 用 systematic-debugging 流程定位根因
2. 修复前对照硬约束确认未违反
3. 修复后必做：写盘函数→刷新缓存、路径函数→检查锚点、用户输入→白名单校验
4. 修复后必做：子进程字段→空值守卫、敏感字段→脱敏、类型变更→前后端同步
5. 编写复现脚本验证

### 重构
1. 重构前梳理数据流（权威源、缓存、降级）
2. 逐文件改造，每步保持测试通过
3. 重构后对照必检清单全量自查
4. 重构后必做：路由文件与入口注册对账、信号钩子覆盖、types.ts 两端对齐

## 必检清单（每次提交前）

```
□ 持久化文件路径基于 import.meta.url 或配置锚点，不依赖 CWD
□ 写盘函数同步刷新内存缓存
□ 跨边界数据有单一权威源，其他存储可降级
□ 用户输入作文件名/路径有白名单校验
□ 后端不可用时前端有降级路径
□ 所有参数在 config 文件管理，无硬编码
□ 源文件 UTF-8 无 BOM
□ Edit 含中文文件前已检测编码，非 UTF-8 用 encoding_fallback 读写
□ 构建前已执行 encoding_scan_command 门禁
□ PowerShell 命令未用 &&、未赋值只读变量、未用 cmd /c
□ 启动服务前已停止占用端口的旧进程
□ 新增 routes/*.ts 已在 entry_file 同步导入与 register
□ 异步赋值字段（this.provider/child/connection 等）使用前有空值守卫
□ 创建子进程/定时器/长连接的模块已注册 SIGINT/SIGTERM 清理钩子
□ GET 接口返回的敏感字段已脱敏并附 configured 标志
□ POST 接口空串语义为"不修改"，未误清空敏感字段
□ 后端 types.ts 与前端 types.ts 同名 interface 字段对齐
□ 已通过后端 tsc --noEmit 与前端 vue-tsc --noEmit 门禁
□ 端到端验证脚本通过（含缓存刷新、降级、路径穿越）
□ 滚动容器链路上 overflow-y: auto 层数 ≤ 1，flex 子项需自然撑开时已加 flex-shrink: 0
□ 跨组件 SPA 跳转通过 CustomEvent 派发，监听器在 onMounted/onBeforeUnmount 配对管理
□ 检查更新类接口有后端缓存（≥ 1 分钟），轮询间隔 ≥ 缓存 TTL，离线模式返回固定值
□ 含中文 SVG 资源以 UTF-8 无 BOM 保存，HTML 引用加 ?v={version} 破缓存
□ vite build 后已验证 HTTP 200 + Content-Length 一致 + 关键字符串包含
□ PowerShell 字符串验证用 Invoke-WebRequest + .Content.Contains()，未用 curl.exe 管道赋值
□ 浏览器自动化降级链路已记录（MCP→subagent→curl），降级原因已日志化
□ 矢量图标用 currentColor + CSS 变量，未硬编码 stroke 色值
□ 菜单项 >7 时已实现折叠/展开双模式 + 纯 CSS tooltip + Vue Transition + localStorage 持久化
□ async 调用已用 asyncio.wait_for / Promise.race 包裹，超时后有 best_holder 兜底数据
□ vue-tsc 报告与源码不一致时已清理增量缓存（tsbuildinfo + .vite + src/**/*.js）而非用 as any 绕过
□ 调用他人 composable / store 前已 Read 源码确认 API 形状，诊断代码未调用 $dispose / _s.delete 重建 store
□ 类型升级 T→U 时已用 isXxx helper + typeof/in 运行时分流，未用 as any / as unknown as U
□ .vue 文件仅含单个 <script setup lang="ts">；例外情况已显式注释 // 例外： 说明用途
□ 运行 E2E 测试前已检查 required_ports 监听 + health 端点返回 200，失败时已中止并提示启动脚本
□ 代码变更影响 DOM 时已同步更新测试用例选择器，未用 try/except 静默吞掉选择器失效错误
□ 阅读型视图标题头占比 ≤15%，内容区 ≥75%，输入区 position: sticky bottom:0 + 毛玻璃背景 + z-index ≥2
□ 源码/运行时数据/构建产物/外部工具链/文档已分离到不同顶层目录，无混放
□ scripts/ 目录脚本命名风格统一（kebab-case 英文），bat 仅作 ps1 薄包装（≤5 行）
□ .gitignore 已登记运行时产物/构建产物/外部工具链/二进制 wrapper，已用 git check-ignore -v 验证
□ 已跟踪文件变更 gitignore 后已执行 git rm --cached 移除索引
□ 项目文档统一到 docs/ 下按类型分类，无散落在项目根或源码目录
□ 运行时数据已外迁到 data/ 目录，config 文件中默认路径已同步更新
□ package.json 中 file: 协议引用路径已用 Resolve-Path 验证，未手动计算 ../ 层级
□ 文件/目录搜索阴性结果已用多种方法交叉验证（Glob+Grep+LS+Test-Path）
□ 二进制 wrapper 已保留 .c/.rs 源码入库，二进制产物已 gitignore，setup 脚本含编译步骤
□ 主题色硬编码替换已按「读变量清单→设计映射表→精准替换」三步执行，未跳步猜测变量名
□ 主题色白名单内的值（rgba(255,255,255,X)/transparent/inherit/currentColor）已保留，其他硬编码颜色已替换为 CSS 变量
□ alpha 变体变量名符合 --accent-{color}-a{NN} 规范，{NN} 取自 allowed_alpha_values 列表
□ CSS 变量选择已按语义优先级（场景背景>卡片背景>文字>边框>阴影>滚动条）判断
□ 含中文文件修改已用 Edit 精准替换，未用 Write 重写整个文件
□ 类型变更已通过后端 tsc --noEmit + 前端 vue-tsc --noEmit 双重门禁（退出码均为 0）
□ Tauri 2.x 新增 invoke 命令已在 build.rs（AppManifest::commands）+ capabilities/default.json（permissions 含 allow-<cmd>）+ lib.rs（generate_handler!）三层同步声明
□ Tauri 2.x 加载外部 URL 已在 capability 的 remote.urls 子字段配置（非顶层 urls），URL 模式含路径通配符（如 http://localhost:PORT/*）
□ Tauri 多 webview 状态隔离用 webview.eval() 设置 window 属性，未用 initialization_script 写 localStorage，未用 URL hash 作模式检测
□ Tauri 透明窗口 CSS 已覆盖 html + body + #app + * 全部层级的 background-color: transparent !important，scoped CSS 已用 :global() 突破作用域
□ Tauri 构建脚本含「清理旧产物→pnpm --filter <pkg> build→产物 mtime + JS chunk 关键字符串验证→cargo build」四步，未用 pnpm run build（递归风险）
□ Tauri 自定义标题栏需同时拖动与点击的元素未用 data-tauri-drag-region + @click，改用 JS 区分（mousedown 记录位置，mousemove 超 5px 触发 start_dragging，mouseup 未超阈值视为 click）
□ PowerShell 调用 cargo/rustc/go build 用 Start-Process -NoNewWindow -Wait -PassThru，未用直接调用 + $ErrorActionPreference=Stop，用 $process.ExitCode 判断真实错误
```

## 适用场景

- 全栈项目（前端 SPA + 后端 API + 文件系统持久化）
- 有内存缓存层的服务
- 多 origin/多启动方式的应用
- 需要降级容错的本地优先应用

## 不适用场景

- 纯静态站点（无后端、无持久化）
- SSR 应用（渲染时机与持久化模式不同，需独立规范）
- 移动端 App（存储模型不同）
- 无 IO 的纯函数库

## 项目背景速查

| 项 | 值 |
|---|---|
| 项目代号 | Karpathy Wiki / 知识库 |
| 当前版本 | 1.0.0 |
| 项目根 | `d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki` |
| 后端入口 | `services/api/src/index.ts`（Fastify） |
| 前端入口 | `packages/web/src/main.ts`（Vue 3） |
| 配置文件 | `config/tech-stack.json` |
| 设计文档 | `Karpathy-AI+Obsidian知识库概要设计说明书.md` |
| 交付文档 | `DELIVERY.md` |

## 技术栈速查

| 类别 | 技术 | 版本 |
|---|---|---|
| 后端语言 | TypeScript | strict 模式 |
| 后端框架 | Fastify | 4.x |
| 模块系统 | ESM | - |
| 异步模型 | AsyncIterable + SSE | - |
| 前端框架 | Vue | 3.4+ |
| UI 库 | Element Plus | - |
| 状态管理 | Pinia | setup 语法 |
| 图可视化 | vis-network | 9.x |
| 构建工具 | Vite | 5.x |
| Harness | @wiki/harness | Agent = LLM + Harness |

详细版本与路径参见 [config/tech-stack.json](config/tech-stack.json)。

## 完整文档结构

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
    └── reading-viewport-rule.md     # 阅读视野优化规则（CODING-032）
    └── project-structure-rule.md   # 项目目录结构规则（CODING-033~040）
    └── theme-color-mapping-rule.md # 主题色变量映射规则（CODING-041~046）
    └── tauri-acl-rule.md            # Tauri 2.x ACL 三层声明规则（CODING-047）
    └── tauri-external-url-rule.md   # Tauri 2.x 外部 URL capability 配置规则（CODING-048）
    └── tauri-webview-isolation-rule.md # Tauri 多 webview 状态隔离规则（CODING-049）
    └── tauri-transparent-window-rule.md # Tauri 透明窗口 CSS 全覆盖规则（CODING-050）
    └── tauri-build-script-rule.md   # Tauri 构建脚本 SPA 构建步骤规则（CODING-051）
    └── tauri-drag-click-conflict-rule.md # Tauri drag-region 与 click 冲突规则（CODING-052）
    └── powershell-stderr-rule.md    # PowerShell 调用 cargo 的 stderr 处理规则（CODING-053）
```

## 执行步骤（Karpathy Wiki 专项）

### 第一阶段：需求分析与规范确认

1. **需求理解**
   - 仔细阅读用户需求，定位概要设计说明书对应章节（如 §12.3）
   - 识别涉及的层（routes → workflows → engine → vault）

2. **规范检查【强制】**
   - 必须先阅读 [project-rules.md](references/project-rules.md) 了解项目硬约束
   - 后端开发：必须检查 SSE headers、err instanceof Error 守卫
   - ESM 项目：必须检查 [esm-module-guard-rule.md](references/esm-module-guard-rule.md)（CODING-017~020）
   - Async 可靠性检查：涉及 async/await + IPC/Playwright 时，必须检查 [async-reliability-rule.md](references/async-reliability-rule.md)（CODING-021~025）
   - 前端开发：必须使用 `<script setup lang="ts">`

3. **参考分析**
   - 同类功能实现：在 `services/api/src/` 与 `packages/web/src/` 中搜索相似模式
   - 架构模式：参考 [architecture-patterns.md](references/architecture-patterns.md)
   - FAQ：遇到问题先查阅 [faq.md](references/faq.md)

4. **设计先行【强制】**
   - 在概要设计说明书中补充对应章节
   - 确认前后端接口契约

### 第二阶段：开发实施

1. **后端开发**
   - **路由层**：新增 `services/api/src/routes/api_<域>.ts`
   - **工作流层**：新增/修改 `services/api/src/workflows/<域>.ts`
   - **引擎层**：实现 EngineAdapter 接口（如需要）
   - **Vault 层**：新增 `services/api/src/vault/<域>.ts`
   - **模块接线【强制】**：在 `services/api/src/index.ts` 完成 import + 实例化 + registerXxxRoute 三步（CODING-019）

2. **前端开发**
   - **类型定义**：在 `packages/web/src/types.ts` 追加类型
   - **Store**：新增 `packages/web/src/stores/<功能>.ts`
   - **视图**：新增 `packages/web/src/views/<功能>.vue`
   - **SSE 消费**：使用 `consumeSSEStream` 统一封装

3. **Harness 集成**
   - 参考 [harness-integration.md](references/harness-integration.md)
   - 确保 EngineAdapter 接口完整实现
   - Prompt 模板单点存储

### 第三阶段：验证与交付

1. **类型检查【强制】**
   ```powershell
   # 后端
   cd karpathy-wiki/services/api
   npx tsc --noEmit

   # 前端
   cd karpathy-wiki/packages/web
   npx vue-tsc --noEmit
   ```
   两个检查必须 exit 0。

2. **ESM 与编码守卫【强制】**
   - Grep `__dirname|__filename` 在 `.ts` 文件中无命中（CODING-017）
   - Edit/Write 修改含中文文件后用 `UTF8Encoding(false, true)` 严格解码复检（CODING-020）
   - 失败按 `git stash → git checkout HEAD → git stash pop → re-edit → re-verify` 五步恢复

3. **功能验证**
   - 后端：curl 测试 SSE 路由
   - 前端：手动测试页面交互

4. **文档同步【强制】**
   - 更新 DELIVERY.md 记录交付清单

### 第四阶段：Git 操作规范与 Bug 修复

1. **Bug 修复流程**
   - **根因定位**：读取相关文件 → 追踪数据流 → 定位最小修改点
   - **最小修改**：只修改必要的部分，不顺便重构
   - **验证策略**：tsc → vue-tsc → curl → 手动测试

2. **PowerShell 环境适配**
   - 避免使用 `$pid`（只读变量），改用 `$procId`
   - 不支持 `&&` 语法，用分号 `;` 分隔命令
   - 单引号 here-string 中 `` `n `` 为字面量，用 `.Replace()` 修复

## 相关 Skills 协作

| Skill | 协作场景 |
|---|---|
| `wiki-backend-code-review` | 后端代码评审（TypeScript/Fastify） |
| `wiki-frontend-code-review` | 前端代码评审（Vue 3/TypeScript） |
| `wiki-automation-startserver` | 启停服务、构建、状态检查 |

## 阶段交接声明

- 当前阶段：v2.1.0 Tauri 2.x 桌面应用集成复盘与编码规范提炼 ✅ 已完成
- 下一阶段：v2.2.0 基于后续开发任务持续迭代
- 下一阶段智能体：wiki-code-dev 或 wiki 代码审查相关智能体
- 下一阶段技能：wiki-code-dev / wiki-backend-code-review / wiki-frontend-code-review / wiki-auto-testing
- 交接上下文：v2.1.0 基于 Tauri 2.x 桌面应用集成历史问题复盘，提炼 CODING-047~053 七条规则，覆盖 ACL 三层声明、外部 URL capability、多 webview 状态隔离、透明窗口 CSS 全覆盖、构建脚本 SPA 步骤、drag-click 冲突、PowerShell stderr 处理。参数全部从 config/coding-standards-config.md 的 tauri_acl / tauri_external_url / tauri_webview_isolation / tauri_transparent_window / tauri_build_script / tauri_drag_click_conflict / powershell_stderr 段读取。复盘系统覆盖 Tauri 桌面集成的四维度（成功步骤/不确定性/可抽象流程/适用场景）。

## 版本历史

| 版本 | 日期 | 变更说明 |
|---|---|---|
| v1.0.0 | 2026-07-10 | 初始版本：技能框架、模板、参考文档 |
| v1.1.0 | 2026-07-10 | **编码规范迭代**：`check-encoding.js` 集成元配置扫描（源码 + 元配置 + 根 .md 一次查完），`fix-encoding-all.ps1` 同步覆盖元配置；project-rules.md / encoding-and-io.md / faq.md 固化"元配置文件本身是 GBK"复发根因 + 故障排查 Checklist |
| v1.2.0 | 2026-07-10 | **编码门禁三层防御**：pre-commit hook（提交前拦检 GBK）、.gitattributes（working-tree-encoding=UTF-8）、CI 门禁（encode-check.sh → check-encoding.js --ci）|
| v1.3.0 | 2026-07-09 | **主题色规范**：新增 theming-and-css-variables.md（CSS 变量三层架构、硬编码禁令、alpha 命名规范、JS 驱动颜色适配）；project-rules.md 新增第 10 条硬约束（禁止硬编码主题色值）；development-workflow.md 新增主题色切换四维度复盘；encoding-and-io.md 补充 rgba(#hex) 无效 CSS 语法陷阱 |
| v1.4.0 | 2026-07-12 | 编码规范迭代：新增多实例配置隔离规范（CODING-011~016），涵盖配置隔离、脱敏值判断、前后端状态同步、配置可恢复性、多入口一致性、预设集中管理 |
| v1.5.0 | 2026-07-17 | **编码守卫与 PowerShell 约束抽象**：新增 encoding-guard-rule.md（Edit 前编码检测/构建门禁/bat pause 禁令/PowerShell 直写回退）；新增 powershell-constraints-rule.md（禁用 &&/cmd /c/只读变量赋值，服务生命周期管理模板）；development-workflow.md 追加"系统清理模块复盘（2026-07-10）"四维度复盘 |
| v1.6.0 | 2026-07-18 | **ESM 模块守卫与编码验证复盘**：新增 esm-module-guard-rule.md（CODING-017~020：ESM 禁用 `__dirname`/`__filename`、静态分析建议人工验证、模块接线三步骤、Edit 后编码验证）；config/tech-stack.json 新增 `esm` 字段集中管理 ESM 相关参数；development-workflow.md 追加"ESM 模块与编码守卫复盘（2026-07-18）"四维度复盘；project-rules.md 追加 ESM 与模块接线约束章节（第 17~20 条） |
| v1.7.0 | 2026-07-21 | **Async 可靠性守卫**：新增 async-reliability-rule.md（CODING-021~025：async 调用必须设置超时、事件循环阻塞场景必须使用线程级保护、状态文件通信必须独立于业务事件循环、async 调用超时必须提供兜底数据、长时 async 任务必须多层超时防护）；config/tech-stack.json 新增 async_reliability 字段集中管理 async 相关参数；development-workflow.md 追加"Async 可靠性复盘（2026-07-21）"四维度复盘；project-rules.md 追加 Async 可靠性约束章节（第 21~25 条） |
| v1.8.0 | 2026-07-22 | **v2 导航栏改造与编码规范提炼**：新增 7 个规则文件 typecheck-cache-rule.md / composable-api-rule.md / mixed-type-dispatch-rule.md / sfc-single-script-rule.md / e2e-precheck-rule.md / test-case-sync-rule.md / reading-viewport-rule.md（CODING-026~032）；config/coding-standards-config.md 新增 7 个参数章节（typecheck_cache / composable_api / mixed_type_dispatch / sfc_script_block / e2e_precheck / test_case_sync / reading_viewport）；development-workflow.md 追加"v2 导航栏改造复盘（2026-07-22）"四维度复盘；project-rules.md 追加工程稳定性约束章节（第 26~32 条）；SKILL.md 必检清单追加 7 条；版本号从 v1.7.0 升级到 v1.8.0 |
| v1.9.0 | 2026-07-13 | **目录结构优化复盘与编码规范提炼**：新增 project-structure-rule.md（CODING-033~040：目录结构分离、脚本命名统一、gitignore 完整性、文档归并、运行时数据外迁、file: 协议路径验证、搜索结果交叉验证、构建产物源码化）；config/coding-standards-config.md 新增 7 个参数章节（project_structure / script_naming / gitignore_rules / docs_structure / path_verification / search_verification / build_artifact_source）；SKILL.md 硬约束追加 8 条（第 33~40 条）、必检清单追加 10 条、规则路由表追加 1 行；版本号从 v1.8.0 升级到 v1.9.0 |
| v2.0.0 | 2026-07-22 | **主题色变量映射规则提炼**：新增 theme-color-mapping-rule.md（CODING-041~046：三步法流程、白名单豁免、alpha 命名规范、语义优先级、编辑工具选择、双重类型检查门禁）；config/coding-standards-config.md 新增 theme_color_mapping 参数章节；SKILL.md 硬约束追加 6 条（第 41~46 条）、必检清单追加 6 条、规则路由表追加 1 行；基于「仪表盘最近操作面板与悬浮问答图标主题色适配」任务四维度复盘（成功步骤/不确定性/可抽象流程/适用场景）；版本号从 v1.9.0 升级到 v2.0.0 |
| v2.1.0 | 2026-07-22 | **Tauri 2.x 桌面应用集成复盘与编码规范提炼**：新增 7 个规则文件 tauri-acl-rule.md / tauri-external-url-rule.md / tauri-webview-isolation-rule.md / tauri-transparent-window-rule.md / tauri-build-script-rule.md / tauri-drag-click-conflict-rule.md / powershell-stderr-rule.md（CODING-047~053）；config/coding-standards-config.md 新增 7 个参数章节（tauri_acl / tauri_external_url / tauri_webview_isolation / tauri_transparent_window / tauri_build_script / tauri_drag_click_conflict / powershell_stderr）；SKILL.md 硬约束追加 7 条（第 47~53 条）、必检清单追加 7 条、规则路由表追加 7 行、文档结构树追加 7 个文件；基于 Tauri 2.x 桌面应用集成历史问题复盘（ACL 三层声明、外部 URL capability、多 webview 隔离、透明窗口 CSS、构建脚本 SPA 步骤、drag-click 冲突、PowerShell stderr 处理）；版本号从 v2.0.0 升级到 v2.1.0 |
