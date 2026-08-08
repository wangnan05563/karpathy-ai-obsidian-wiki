# 故障排查指南

本文档收录 wiki-auto-testing 技能运行中遇到的常见问题及解决方案。
当测试流程中出现异常时，参考本节进行排查。

## 1. CORS 跨域错误

**症状**：控制台出现 Access-Control-Allow-Origin 错误
**原因**：测试脚本从浏览器端直接 fetch 跨域 API
**解决**：在 pi_tests 中设置 use_playwright_request: true，使用 context.request.get() 代替浏览器端 fetch

## 2. 构建脚本 pause 阻塞

**症状**：运行 bat 脚本后流程卡住等待输入
**原因**：bat 脚本中的 pause 命令等待按键
**解决**：通过管道输入空行绕过："" | & "script.bat" 或 cmd /c "script.bat" < nul

## 3. 工作目录不一致导致 FileNotFoundError

**症状**：FileNotFoundError: No such file or directory: 'config.yaml'
**原因**：AI 在子目录中执行 Python 脚本，但 config.yaml 在项目根目录
**解决**：
1. 在 config.yaml 中配置 working_directory.auto_chdir: true
2. 脚本通过 ind_project_root() 从脚本位置向上查找 .git 标记
3. 自动 os.chdir(project_root) 切换到项目根目录

## 4. Python 脚本 GBK 编码

**症状**：SyntaxError: invalid character 或 UnicodeDecodeError
**原因**：Windows 上编辑工具以 GBK 编码保存含中文的 .py 文件
**解决**：
`python
# 检测并转换编码
content = open('script.py', 'r', encoding='gbk').read()
open('script.py', 'w', encoding='utf-8').write(content)
`
或在 config.yaml 中设置 encoding_safety.auto_fix_python_encoding: true，脚本启动时自动检测和转换。

## 5. PSReadLine 缓冲区崩溃

**症状**：System.ArgumentOutOfRangeException: top 或终端无响应
**原因**：PowerShell PSReadLine 模块对超长命令行（>200字符）缓冲区溢出
**解决**：
1. 拆分长命令为多条短命令（每条 < 200 字符）
2. 使用 	arget_terminal: new 创建新终端
3. 将复杂逻辑写入 .ps1 / .py 脚本文件，通过 python script.py 调用
4. 在 config.yaml 中设置 	erminal.split_long_commands: true

## 6. Glob 工具与中文路径不兼容

**症状**：Glob 工具对包含中文的路径返回 "No file found"
**原因**：Glob 工具的路径匹配引擎对 Unicode 字符处理有局限
**解决**：
1. 改用 RunCommand + PowerShell Get-ChildItem 列举文件
2. 使用绝对路径直接读取文件
3. 避免在 Glob pattern 中使用中文路径段

## 7. PowerShell `&&` 语法不支持导致命令链断开

**症状**：PowerShell 执行 `cmd1 && cmd2` 报错 "The token '&&' is not a valid statement separator"
**原因**：PowerShell（5.1 及以前）不支持 `&&` 语法，这是 bash/cmd 的语法
**解决**：
1. 用 `;` 分隔顺序执行的命令（不关心前一条是否成功）
2. 用 `if ($LASTEXITCODE -eq 0) { cmd2 }` 实现条件执行
3. PowerShell 7+ 支持 `&&` / `||`，但 Windows 10 默认 PowerShell 5.1 不支持
4. 在 config.yaml 中设置 `terminal.split_long_commands: true`，技能会拆分命令

## 8. vue-tsc 路径找不到导致类型检查失败

**症状**：`npx vue-tsc --noEmit` 报 "command not found" 或解析到错误版本
**原因**：npx 在 monorepo 或 pnpm 环境下解析 bin 路径不可靠
**解决**：
1. 直接调用 bin 脚本：`node frontend/node_modules/vue-tsc/bin/vue-tsc.js --noEmit`
2. 或用 pnpm：`pnpm --filter web exec vue-tsc -- --noEmit`
3. 在测试编排中用 `RunCommand` + 直接 bin 路径，不依赖 npx 解析

## 9. pnpm install EPERM 文件占用

**症状**：`pnpm install` 报 EPERM: operation not permitted, unlink
**原因**：开发服务进程占用 node_modules 中的文件句柄
**解决**：
1. 先停止所有开发服务（前端 dev server + 后端 API server）
2. 用 `npx <tool>` 跳过 install 检查直接执行已安装的工具
3. 在 config.yaml 中设置 `startup.stop_after_test: false`，测试后手动停服务再 install

## 10. 配置保存后 GET 返回旧值（缓存未刷新）

**症状**：`PUT /api/ai/config` 成功后立即 `GET /api/ai/config` 返回修改前的旧值
**原因**：后端配置缓存有 TTL（如 30s），写盘函数未同步刷新内存缓存
**解决**：
1. 后端写盘函数必须在 `await fs.writeFile(...)` 成功后调用 `refreshConfigCache(data)`
2. 用 `persistence_crud_test` 步骤类型自动验证（PUT 后立即 GET 对比值）
3. 在 config.yaml 的 `persistence_tests` 中配置 `ai_config` 资源端点进行回归
4. 缓存 TTL 不替代显式刷新：即使 TTL 很短，写盘后仍必须立即刷新

## 11. 编码乱码（U+FFFD 替换字符）

**症状**：页面 tab 标签或表单 label 全显示为 `?` 或方块，`has_text("仪表盘")` 中文匹配失败；DOM dump 文本中出现 U+FFFD
**原因**：
1. Windows 终端默认 GBK 编码，Playwright 通过 stdout 输出中文时被替换为 U+FFFD
2. 测试脚本本身被以 GBK 保存，含中文的字符串字面量被破坏
3. Vite/前端构建产物的 HTML charset 与实际编码不匹配
**解决**：
1. 启用 `encoding_tests.enabled: true`，让技能自动检测 DOM 文本中的 U+FFFD
2. 用 Unicode 码点匹配替代中文字符串匹配：调用 `_shared.get_dom_text_codepoints(page, selector)` 获取码点列表，用 `0x4eea` 等码点比对而非 `"仪"`
3. 在 config.yaml 中配置 `encoding_tests.scan_selectors` 缩窄扫描范围（如只扫 `.el-tabs__item`、`.el-form-item__label`），减少噪音
4. 测试失败时 `encoding_tests.screenshot_on_fail: true` 自动截图取证
5. 确认前端 `index.html` 含 `<meta charset="utf-8">`，且 Vite 配置 `build.target: 'es2015'` 以上

## 12. Playwright 中文匹配失败

**症状**：`page.locator('.el-tabs__item:has-text("仪表盘")')` 返回 0 个元素，但页面上明显存在该 tab
**原因**：
1. `has_text` 伪类在 Playwright 内部走文本节点比对，对终端编码透传敏感
2. 测试脚本字符串字面量在 GBK 终端下被解释为非 UTF-8 字节序列
3. Element Plus 的 tab 文本可能被 `<i>` 图标或空白字符分隔，导致 `has_text` 整词匹配失败
**解决**：
1. 改用 Unicode 码点验证：`get_dom_text_codepoints(page, '.el-tabs__item')` 返回 `[[0x4eea, 0x8868, 0x76d8], ...]`，逐个码点比对
2. 用 `:text-is()` 或 `:text()` 代替 `:has-text()`：`page.locator(".el-tabs__item", has_text=...)` 在 Python 端用 `lambda` 过滤
3. 用 `nth(i)` 按位置点击，绕开文本匹配：`page.locator('.el-tabs__item').nth(0).click()`
4. 用 `evaluate` 直接取 `textContent` 并在 Python 端用码点比对：
   ```python
   texts = page.evaluate('() => [...document.querySelectorAll(".el-tabs__item")].map(e => e.textContent)')
   codepoints = [[ord(c) for c in t] for t in texts]
   ```
5. 确保 Python 脚本以 UTF-8 保存（首行 `# -*- coding: utf-8 -*-`），且终端 `chcp 65001` 切到 UTF-8

## 13. 端口占用导致新服务启动失败

**症状**：`npm run dev:api` 启动时报 `EADDRINUSE: address already in use`，或前端 `npm run dev:web` 启动后 5173 端口无响应
**原因**：
1. 上次测试未正常退出，dev server 进程仍占用端口
2. VSCode/IDE 集成终端残留 dev server 进程
3. Node 进程僵尸化，TCP 连接处于 TIME_WAIT 状态
**解决**：
1. 启用 `service_lifecycle.stop_old_process: true`，测试前自动清理占用端口的旧进程
2. 手动排查：`Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in @(3000, 5173) }`
3. 强制停止：`Get-NetTCPConnection -State Listen -LocalPort 3000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }`
4. 在 config.yaml 的 `service.required_ports` 中列出所有需要的端口，`service_lifecycle` 会逐一清理
5. 若 TIME_WAIT 占用，等待 60 秒或调整内核参数 `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\TcpTimedWaitDelay`

## 14. bat 脚本 pause 卡住自动化流程

**症状**：执行 `启动服务.bat` 后流程卡住，提示"请按任意键继续..."，AI 终端无响应
**原因**：bat 脚本末尾的 `pause` 命令等待按键输入，非阻塞模式下无人按键
**解决**：
1. 启用 `powershell_constraints.bypass_bat_pause: true`，技能启动 bat 时自动注入空输入
2. 通过管道输入空字符串绕过：`'' | & "启动服务.bat"` 或 `Get-Content nul | & "启动服务.bat"`
3. 修改 bat 脚本本身：在 `pause` 前加 `if "%CI%"=="1" goto skip_pause`，并在测试时 `$env:CI=1`
4. 用 `Start-Process` 异步启动 bat：`Start-Process -FilePath "启动服务.bat" -WindowStyle Hidden -PassThru`，pause 不影响主流程
5. 改用直接调用 npm 命令（`npm run dev:api`、`npm run dev:web`）而非 bat 脚本，避开 pause

## 15. Playwright 浏览器 GPU 崩溃

**症状**：`browser.new_context()` 后立即崩溃，报 `GPU process isn't usable. Goodbye.` 或 `ContextResultCode::kGpuChannelDestroyed`
**原因**：
1. Windows 10 虚拟机或无 GPU 硬件加速的环境下，Chromium 默认启用 GPU 渲染失败
2. RDP 远程桌面会话不支持 GPU 加速
3. 显卡驱动与 Chromium 版本不兼容
**解决**：
1. 确认 config.yaml 中 `browser.launch_args` 含 `--disable-gpu`（默认已包含）
2. 追加 `--disable-software-rasterizer`、`--disable-extensions` 进一步隔离
3. 设置 `browser.headless: true`（headless 模式不依赖 GPU）
4. 设置环境变量：`$env:CHROMIUM_FLAGS="--disable-gpu"`；或在 Python 端 `os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "..."`
5. 若仍崩溃，尝试 `--use-gl=swiftshader` 软件渲染（性能下降但稳定）

## 16. Python 文件编码声明缺失导致 SyntaxError

**症状**：执行 `.py` 脚本报 `SyntaxError: Non-UTF-8 code starting in ...` 或 `UnicodeDecodeError: 'gbk' codec can't decode`
**原因**：
1. Windows 默认 Python 解释器以 GBK 读取源文件，但文件以 UTF-8 保存且含中文
2. 缺少 PEP 263 编码声明，Python 无法判断源文件编码
3. Edit/Write 工具默认以 UTF-8 写入，但 PowerShell 终端 stdout 是 GBK
**解决**：
1. 所有 `.py` 文件首行加编码声明：`# -*- coding: utf-8 -*-`
2. 启用 `encoding_safety.auto_fix_python_encoding: true`，技能启动时自动检测并转换
3. 在 PowerShell 中执行前设置 PYTHONUTF8：`$env:PYTHONUTF8=1; python script.py`
4. 检测文件编码并转换：
   ```powershell
   $bytes = [System.IO.File]::ReadAllBytes("script.py")
   if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
       Write-Host "BOM detected, UTF-8 with BOM"
   } elseif (-not ($bytes -contains 0)) {
       # 无 BOM 且无 null 字节，可能是 UTF-8 或 ASCII
   }
   ```
5. 用 `ensure_utf8(file_path)` 工具函数自动 GBK→UTF-8 转换（在 `_shared.py` 中提供）

## 17. API 测试返回 404（路由未注册）

**症状**：前端调用 `/api/xxx` 返回 404，但路由文件已存在于 `routes/` 目录

**原因**：新增 `routes/*.ts` 文件但未在 `index.ts` 中导入与注册

**解决方案**：
1. 检查 `routes/` 目录下所有 `.ts` 文件
2. 在 `index.ts` 中添加 `import` 语句
3. 在路由注册区添加 `registerXxxRoute(app, ...)` 调用
4. 重启服务验证

**预防**：启用 `route_registration_check.enabled: true` 配置项，测试时自动检测后端路由目录下所有 `.ts` 文件是否在入口文件中注册，未注册即提前失败并输出缺失列表

---

## 18. 前后端类型不匹配

**症状**：前端 TypeScript 类型检查失败，或运行时字段 `undefined`

**原因**：后端 `types.ts` 新增 `interface` 但前端 `types.ts` 未同步

**解决方案**：
1. 对比后端 `types.ts` 的 `export interface`
2. 在前端 `types.ts` 同步新增对应类型
3. 运行 `vue-tsc --noEmit` 验证

**预防**：启用 `type_sync_check.enabled: true` 配置项，测试时自动检测前后端 `types.ts` 接口字段对齐情况；通过 `ignore_interfaces` 排除仅后端使用的内部接口（如 `EngineAdapter` / `VaultService`）

---

## 19. Chromium headless 模式崩溃

**症状**：浏览器启动后立即崩溃，Canvas/WebGL 相关错误，报 `GPU process isn't usable` 或 `ContextResultCode::kGpuChannelDestroyed`

**原因**：headless 模式下 GPU 加速不稳定（虚拟机/RDP/无 GPU 环境尤为常见）

**解决方案**：
1. 添加 `--disable-gpu` 启动参数
2. 添加 `--no-sandbox` `--disable-dev-shm-usage` `--disable-setuid-sandbox`
3. 检查 `browser.launch_args` 配置
4. 仍崩溃时追加 `--use-gl=swiftshader` 软件渲染

**预防**：启用 `headless_crash_guard.enabled: true` 配置项，自动验证 `browser.launch_args` 包含 `headless_crash_guard.required_launch_args` 中所有必需参数；启动崩溃时按 `max_retries` 自动重试，间隔 `retry_interval_ms`

---

## 20. Python 测试脚本编码错误

**症状**：运行 Python 脚本报 `SyntaxError` 或 `UnicodeDecodeError`

**原因**：脚本含中文但以 GBK 编码写入，与声明的 utf-8 不符

**解决方案**：
1. 检查文件首字节是否为 BOM（`0xEF 0xBB 0xBF`）
2. 用 UTF-8 无 BOM 重新保存
3. 验证文件无 U+FFFD 替换字符

**预防**：启用 `encoding_safety_enhanced.verify_after_write: true` 配置项，写入后自动验证编码；`encoding_safety_enhanced.check_replacement_char: true` 检测 U+FFFD 替换字符（编码损坏标志），`replacement_char_threshold: 0` 即不允许任何 U+FFFD 出现

---

## 21. PowerShell 命令拼接失败

**症状**：执行命令报 `Empty pipe element` 或 `The token '&&' is not a valid statement separator`

**原因**：PowerShell 5.1 不支持 `&&` 和 `||` 语法（这是 bash/cmd 的语法）

**解决方案**：
1. 将 `&&` 替换为 `;`
2. 将 `||` 替换为 `;`（需手动判断错误处理逻辑）
3. 拆分长命令为多条短命令（每条 < 200 字符）

**预防**：启用 `powershell_compatibility.enabled: true` 配置项，自动扫描测试脚本与配置文件中是否出现 `forbidden_syntaxes`（默认 `&&` / `||`）；命中即判定失败，并提示用 `syntax_replacements` 中的替代语法；`split_long_commands: true` 自动拆分超过 `max_command_length` 的长命令

## 22. 章节卡片仅显示标题（双重滚动裁切）

**症状**：帮助文档页面的章节卡片只显示图标+标题一行（约 50px 高度），下方 intro/blocks/表格内容全部不可见，标题文字"快速开始使用文档"被截断为"快速开始"

**原因**：容器链路上 `overflow-y: auto` 嵌套层数超过 1，形成双重滚动：
- 外层 `.content` 已设 `overflow-y: auto` 接管页面滚动
- 内层 `.help-content-area` 又设 `overflow-y: auto`，与外层形成双重滚动
- 全局 `.glass-card` 类的 `overflow: hidden` 进一步裁切内容
- flex 子项默认 `flex: 0 1 auto`，在双重滚动嵌套中被等比压缩到 `min-content` 高度

**解决方案**：
1. 移除内层容器的 `overflow-y: auto`，让外层 `.content` 统一接管滚动
2. 给自然高度的 flex 子项加 `flex-shrink: 0`，防止被压缩

**预防**：启用 `scroll_container_tests.enabled: true` 配置项，自动遍历 `test_pages` 中每个页面：
- 检查 `inner_overflow_selectors` 选择器的 `overflow-y` computed style
- 统计容器链路上 `overflow-y: auto` 嵌套层数（超过 `max_overflow_layers` 即告警）
- 获取 `card_selectors` 的 `boundingRect().height`，低于 `min_card_height_px`（默认 200px）即判定为被压缩
- `require_content_visible: true` 时验证卡片内除标题外至少有一个内容块可见

## 23. 跨组件跳转失效（About → Help 无响应）

**症状**：点击 About 页面的"查看帮助文档"按钮后，视图未切换到 Help，控制台无错误

**原因**：跨组件视图跳转未通过 `CustomEvent` 派发，或入口组件未在 `onMounted` / `onBeforeUnmount` 配对管理监听器：
- 直接操作入口组件的 ref（违反组件隔离原则）
- 通过 localStorage 间接传递跳转意图（异步且不可靠）
- 监听器用匿名箭头函数，`removeEventListener` 无法引用同一函数
- 监听器只在 `onMounted` 中 `addEventListener`，未在 `onBeforeUnmount` 中 `removeEventListener`（内存泄漏）

**解决方案**：
1. 派发方使用 `globalThis.dispatchEvent(new CustomEvent('karpathy:navigate', { detail: 'help' }))`
2. 入口组件用具名函数（非匿名箭头函数）作为监听器
3. `onMounted` 中 `addEventListener`，`onBeforeUnmount` 中 `removeEventListener` 配对管理
4. 监听器内校验 `detail` 字段在白名单内后才切换视图

**预防**：启用 `spa_navigation_tests.enabled: true` 配置项，自动遍历 `test_routes` 中每条跳转链路：
- 导航到 `from` 页面，点击 `trigger_selector` 触发跳转
- 等待 `switch_wait_ms` 后验证 `to` 视图已渲染
- 读取 `app_entry` 文件，搜索 `addEventListener` 与 `removeEventListener` 调用
- 验证事件名匹配 `event_name_pattern`（`{project}:navigate` → `karpathy:navigate`）
- `require_lifecycle_pair: true` 时验证 add 在 `onMounted` 中、remove 在 `onBeforeUnmount` 中
- `validate_detail_whitelist: true` 时验证派发的 `detail` 字段在 `allowed_views` 白名单内

## 24. 检查更新卡在 loading 不恢复

**症状**：点击"检查更新"按钮后，按钮一直显示 loading 状态，无法恢复到 idle 或其他状态；组件卸载后定时器仍在执行，控制台出现"组件已卸载仍更新状态"警告

**原因**：检查更新状态机不完整或定时器未清理：
- 状态机缺少 `error` 状态，请求失败时无法恢复
- 状态机缺少 `idle` 初始态，首次进入页面时按钮状态不确定
- `setInterval` 未在 `onBeforeUnmount` 中 `clearInterval`，组件卸载后定时器仍执行
- 轮询间隔 < 后端缓存 TTL，每次轮询都命中缓存，相当于无意义的额外请求
- 离线模式下仍发起真实 GitHub API 调用，增加延迟

**解决方案**：
1. 状态机覆盖 5 态：`idle` / `loading` / `latest` / `newer` / `error`
2. `latest` 状态 3 秒后自动回 `idle`
3. `setInterval` 在 `onMounted` 启动，`clearInterval` 在 `onBeforeUnmount` 配对清理
4. 轮询间隔 ≥ 后端缓存 TTL（推荐均设为 5 分钟）
5. 离线模式 `offline_mode: true` 时后端固定返回 `{ has_update: false, source: 'local' }`

**预防**：启用 `update_check_tests.enabled: true` 配置项，自动遍历 `test_pages` 中每个页面：
- 验证状态机覆盖 `required_states` 全部状态（默认 5 态）
- 检查 UI 中每个状态有对应的 `v-if` / `v-else-if` 分支
- 调用 `update_endpoint` 接口，`offline_mode: true` 时验证响应固定为 `{ has_update: false, source: 'local' }`
- `validate_no_external_call_in_offline: true` 时验证后端未发起外部 GitHub API 调用
- `validate_poll_ge_ttl: true` 时读取前端代码中的 `setInterval` 间隔，验证 ≥ `cache_ttl_ms`
- `require_timer_cleanup: true` 时读取 `app_entry` 文件，验证 `setInterval` 与 `clearInterval` 在 `onMounted` / `onBeforeUnmount` 配对

## 25. 构建产物 HTTP 404 或内容截断

**症状**：vite build 后访问 `http://localhost:3000/assets/index-{hash}.js` 返回 404，或 `Invoke-WebRequest` 下载的内容远小于磁盘文件大小。

**根因**：后端 tsx watch / nodemon 未自动加载新构建产物（特别是 hash 文件名变化时），或返回了 JSON 错误响应（如 `{ "error": "Not Found" }` 通常仅数百字节）。

**解决**：
1. 启用 `build_artifact_verification.enabled: true` 自动验证 HTTP 三要素
2. 若 `restart_backend_on_404: true`，自动停止旧后端进程并重启
3. 轮询 `health_check_endpoint` 直到返回 200

## 26. Playwright MCP 报 "MCP server is not found"

**症状**：调用 chrome-devtools-mcp 或 playwright-mcp 时报 `MCP server is not found` 错误。

**根因**：MCP 服务未配置或未启动。

**解决**：
1. 启用 `browser_automation_fallback.enabled: true` 自动降级
2. 降级链路：`playwright-mcp` → `browser-use-subagent` → `powershell-curl`
3. 每级降级记录降级原因（`log_degradation_reason: true`）
4. browser_use subagent 截图可能不可用（不可见 tab 限制），降级为 DOM 检查

## 27. 导航栏折叠/展开切换失效

**症状**：点击折叠/展开按钮无响应，或切换后布局抖动。

**根因**：未用 Vue Transition `mode="out-in"`，或折叠状态未持久化到 localStorage。

**解决**：
1. 启用 `nav_dual_mode_tests.enabled: true` 自动验证切换逻辑
2. 检查 `<Transition name="..." mode="out-in">` 是否正确包裹
3. 验证 `localStorage.getItem('navCollapsed')` 持久化逻辑
4. 验证 `menu_items` 列表与实际菜单项数量一致

## 28. 图标不跟随主题变色

**症状**：切换主题后图标颜色保持不变，或所有图标显示为同一硬编码色值。

**根因**：SVG 图标的 `stroke` / `fill` 属性未设为 `currentColor`，或 CSS 中硬编码了色值。

**解决**：
1. 启用 `icon_theme_tests.enabled: true` 自动验证 currentColor 生效
2. 扫描 `.vue` / `.svg` 文件中的 `<svg>` 标签
3. 将 `stroke="#hex"` / `fill="rgb()"` 改为 `stroke="currentColor"` / `fill="currentColor"`
4. 验证 `filter: drop-shadow(0 0 Xpx currentColor)` 用 currentColor 而非硬编码色值

## 29. PowerShell 字符串验证输出混乱

**症状**：`$js = curl.exe -s "url"; $js.Contains("keyword")` 输出非预期布尔值，或变量类型不可预测。

**根因**：PowerShell 中 `curl.exe` 输出可能被解析为多个对象（数组），`.Contains()` 行为不可预测。

**解决**：
1. 启用 `powershell_string_verification.enabled: true` 自动检测禁止模式
2. 改用 `Invoke-WebRequest` + `.Content.Contains()` 模式：
   ```powershell
   $r = Invoke-WebRequest -Uri "url" -UseBasicParsing
   $r.Content.Contains("keyword")  # 始终返回正确的布尔值
   ```
3. `Invoke-WebRequest` 返回的 `.Content` 属性始终是单一字符串

## 30. 折叠面板展开后立即收起

**症状**：点击折叠面板触发按钮展开后，面板立即自动收起，无法保持展开状态；或展开/收起动画闪烁，状态不稳定。

**根因**：Transition 动画未完成即读取状态，或触发按钮激活状态类未正确应用：
- Transition 组件未设 `mode="out-in"`，展开/收起动画冲突
- 动画完成前提前判定面板可见性，状态读取错误
- 触发按钮激活 CSS 类（如 `.active`）未绑定到展开状态
- 连续快速点击导致状态机紊乱

**解决**：
1. 启用 `control_layering_tests.enabled: true` 自动验证控件分层逻辑
2. 验证 `<Transition name="..." mode="out-in">` 正确包裹折叠面板
3. 等待 `animation_duration_ms`（默认 300ms）后再验证面板可见性
4. 验证触发按钮在展开状态下带 `trigger_active_class` 激活样式
5. 连续点击切换 5 次，验证状态稳定无闪烁

## 31. 第三方库渲染显示 Syntax error in text

**症状**：页面中 mermaid 图表或 katex 公式渲染失败，显示 "Syntax error in text" 或原始 Markdown 文本，控制台报解析错误。

**根因**：第三方库缺少三层防护，LLM 输出的错误语法直接传到渲染层：
- 缺少库级错误抑制配置（如 mermaid 未设 `suppressErrors: true`，katex 未设 `throwOnError: false`）
- 缺少 LLM 内容预校验，错误语法直接传入解析器
- 缺少 CSS 兜底样式，错误容器显示原始文本而非友好提示
- 错误容器未在下次渲染时清空，残留旧错误

**解决**：
1. 启用 `third_party_error_guard_tests.enabled: true` 自动验证三层防护
2. **第一层：库级配置** - 验证 `suppress_config_keys`（如 `suppressErrors: true` / `throwOnError: false`）已设置
3. **第二层：预校验** - 注入 `invalid_inputs` 中的错误语法，验证 LLM 输出在渲染前被预校验拦截
4. **第三层：CSS 兜底** - 验证 `error_css_classes` 中的兜底类已应用到错误容器
5. `require_container_clear: true` 时验证错误容器在下次渲染时被清空

## 32. MCP 工具加载导致 AI 未回复

**症状**：用户提问后 AI 长时间无响应，控制台显示某个 MCP 工具加载超时或失败，整个回复流程被阻塞。

**根因**：多资源加载未使用 `Promise.allSettled`，单个失败导致整体中断：
- 使用 `Promise.all` 而非 `Promise.allSettled`，单个 MCP 工具加载失败导致全部中断
- 缺少错误收集机制，失败信息被丢弃
- 缺少降级路径，加载失败后无兜底数据
- 缺少总超时配置，单个资源加载超时无限等待

**解决**：
1. 启用 `parallel_loading_tests.enabled: true` 自动验证并行加载逻辑
2. 验证代码使用 `required_wrapper`（`Promise.allSettled`）包裹并行加载
3. 模拟单个资源加载失败，验证其他资源不受影响（`error_collection_required: true`）
4. 验证有降级路径（`degradation_path_required: true`），如使用兜底数据
5. 验证总超时 `total_timeout_ms`（默认 30000ms）配置生效

## 33. 超时阈值不匹配导致 AI 回复被丢弃

**症状**：AI 已生成完整回复，但前端因超时丢弃了回复，用户看到"请求超时"提示；或后端 MCP 工具超时导致前端连锁超时。

**根因**：前后端超时阈值未呈递增覆盖关系：
- 前端超时（如 30s）< 后端 MCP 超时（如 60s），后端还在处理时前端已超时
- 超时层级未递增覆盖，下层超时导致上层连锁失败
- 超时后未保留部分结果，全部丢弃
- 缺少降级路径，超时后无兜底提示

**解决**：
1. 启用 `timeout_chain_tests.enabled: true` 自动验证超时链式匹配
2. 验证 `layer_order` 中各层超时呈递增关系（前端 120s > 后端 API 60s > 后端 MCP 30s）
3. 验证每层超时 >= 下层超时 × `margin_multiplier`（默认 1.5 倍）
4. 模拟下层超时（`simulate_timeout_ms`），验证上层不中断
5. `partial_result_required: true` 时验证部分结果被保留而非全部丢弃
6. `degradation_path_required: true` 时验证有降级路径（如兜底数据或提示用户）

## 34. 折叠面板内下拉菜单点击后关闭

**症状**：在折叠面板内点击 el-dropdown 下拉菜单选项时，面板误关闭，导致用户需要重新展开面板才能继续操作。

**根因**：click outside 事件传播未正确处理 teleport 组件：
- click outside 监听器未排除 el-dropdown 的 teleport 到 body 的 popper 元素
- el-dropdown 未配置 `teleported` / `append-to-body` props
- 缺少 `@mousedown.stop` / `@click.stop` 事件修饰符
- teleport 到 body 的 dropdown 被判定为"面板外元素"触发关闭

**解决**：
1. 启用 `folding_panel_event_tests.enabled: true` 自动验证事件冲突处理
2. 验证 `click_outside_exclude_selectors` 中的选择器（如 `.el-dropdown` / `.el-popper`）被排除
3. 验证 `teleport_selectors` 中的 teleport 组件不触发面板关闭
4. 验证 el-dropdown 配置了 `required_dropdown_props`（如 `teleported` / `append-to-body`）
5. 验证 `required_event_modifiers`（如 `@mousedown.stop`）已应用到 dropdown 事件
6. 点击 dropdown 选项后验证 dropdown 关闭但面板保持展开

## 35. 视频生成卡在 processing 不返回

**症状**：用户提交视频生成请求后，UI 一直显示"处理中"（processing），既不进入 completed 也不进入 failed；关闭对话框后定时器仍在执行，控制台出现"组件已卸载仍更新状态"警告。

**根因**：长任务状态机不完整或定时器未正确清理（对应 CODING-065）：
- 状态机缺少 `failed` 状态，请求失败时无法恢复（卡在 processing）
- 轮询单次失败即终止，未容忍网络抖动（`single_failure_no_abort` 未生效）
- 完成/失败时未显式 `stopXxxPolling()`，依赖 GC 回收定时器
- `setInterval` 未在 `onBeforeUnmount` 中 `clearInterval`，组件卸载后定时器仍执行
- 超时用 `AbortSignal.timeout` 而非 `setTimeout`，无法同步设 `abortReason` 标记
- "关闭对话框"与"重置状态"合为一个函数，关闭后无法保持对话框重新生成

**解决**：
1. 启用 `media_generation_tests.long_task_state_machine.enabled: true` 自动验证状态机
2. 验证状态机覆盖 `required_states` 全部 5 态（idle/queued/processing/completed/failed）
3. `single_failure_no_abort: true` 时验证轮询单次失败仅更新 error 文案，不终止轮询
4. `require_timer_cleanup: true` 时验证 `setInterval` 与 `clearInterval` 在 `onMounted` / `onBeforeUnmount` 配对
5. `require_settimeout_for_abort: true` 时验证超时用 `setTimeout` 而非 `AbortSignal.timeout`（因需同步设 `abortReason`）
6. `require_close_reset_split: true` 时验证"关闭对话框"（停轮询+关对话框+重置全部）与"重置状态保持对话框"（停轮询+清状态）拆为两个函数
7. 验证 `required_abort_reasons` 三态（user/timeout/null）区分用户停止/超时/正常完成

**预防**：所有长任务（视频生成、批量处理等）前端必须用 5 状态机驱动 UI，禁止用单一 `isLoading: boolean` 表达全生命周期；超时用 `setTimeout` 同步设 `abortReason`；关闭/重置拆为两个函数；`onBeforeUnmount` 必须清理 `abortController` + 所有 `addEventListener` + `setInterval` timer。

## 36. 归档 Markdown frontmatter 字段缺失

**症状**：LLM 生成的图像/PPT/视频归档到 vault 后，文件无法被知识浏览/检索功能正确识别，或在 queries 目录下显示为普通 markdown 而非媒体归档；文件名格式混乱，无法按时间排序。

**根因**：归档 Markdown frontmatter 未标准化（对应 CODING-060）：
- 缺少 `type: query` 字段，归档文件被识别为普通笔记
- 缺少 `output_mode` 字段，无法区分图像/PPT/视频/播客类型
- 缺少 `generated_at` 字段或格式非 ISO8601，无法按生成时间排序
- 文件名不符合 `<output_mode>-YYYYMMDD-HHmmss.<ext>` 模式，排序混乱
- 业务字段（如 `image_file` / `video_file` / `task_id` / `source_url`）缺失，无法溯源
- 文件名前缀与 frontmatter `output_mode` 不一致（如文件名 `image-xxx.png` 但 frontmatter `output_mode: video`）

**解决**：
1. 启用 `media_generation_tests.archive_frontmatter_check.enabled: true` 自动验证归档 frontmatter
2. 验证 `required_fields`（type/output_mode/generated_at）齐全，缺失任一即失败
3. 验证 `type` 字段值为 `expected_type_value`（默认 `query`）
4. 验证 `output_mode` 字段值在 `expected_output_modes` 枚举内（image/ppt/video/podcast）
5. 验证 `generated_at` 字段匹配 `generated_at_pattern`（ISO8601 格式：`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}`）
6. 验证文件名匹配 `filename_pattern`（`^(image|ppt|video|podcast)-\d{8}-\d{6}\.(md|png|mp4|marp\.md)$`）
7. `validate_filename_mode_consistency: true` 时验证文件名前缀与 frontmatter `output_mode` 一致
8. 按 `business_fields_by_mode` 验证业务字段（如 video 必须含 `video_file` / `task_id` / `source_url` 之一）

**预防**：所有 LLM 生成产物归档到 `vault/queries/` 目录时，frontmatter 必须含 `type: query` + `output_mode: <image|ppt|video|podcast>` + `generated_at: ISO8601`；文件名格式 `<output_mode>-YYYYMMDD-HHmmss.<ext>`（与 podcast-workflow 一致，排序友好）；业务字段（`image_file` / `video_file` / `task_id` / `source_url`）放同 frontmatter；Marp 类归档文件 frontmatter 可合并 marp 字段（`marp: true` + 归档字段），避免双重 frontmatter。

## 37. 外部 API 类型契约不匹配（seconds 字段）

**症状**：调用外部视频生成 API 时返回 400 错误，提示字段类型不匹配；或响应字段路径变更后前端无法获取 url，导致下载失败；或网络错误时前端统一显示"后端服务未运行"，无法区分 DNS 失败/连接拒绝/证书错误。

**根因**：外部 API 集成契约不完整（对应 CODING-056）：
- 调用方后端语言要求的字段类型未显式转换（如 Go 后端 string 类型，前端传 number 导致 400）
- 响应字段未做双重路径兼容（`data.url || data.metadata?.url`），外部 API 字段路径变更后失效
- 未用 `fetchWithDiagnostics` 包装原生 fetch，错误码未翻译为可读诊断信息
- 错误消息硬编码"后端服务未运行"，无法区分网络超时/DNS 失败/连接拒绝/证书错误
- `fetchWithDiagnostics` 未 export，无法单元测试验证错误转换逻辑

**解决**：
1. 启用 `media_generation_tests.external_api_contract.enabled: true` 自动验证外部 API 契约
2. 验证 `require_fetch_wrapper: true` 时源码中使用了 `fetchWithDiagnostics` 包装（便于单元测试）
3. 验证响应字段双重路径兼容（`data.url || data.metadata?.url`），应对外部 API 字段路径变更
4. 验证调用方后端语言要求的字段类型已显式转换（如 Go 后端 string 类型用 `String(value)`）
5. 按 `diagnostic_error_codes` 映射验证错误码翻译：
   - `ENOTFOUND` → "DNS 解析失败，请检查网络或代理配置"
   - `ECONNREFUSED` → "连接被拒绝，目标服务未启动或端口错误"
   - `ECONNRESET` → "连接被重置，可能是代理超时或目标服务崩溃"
   - `CERT_HAS_EXPIRED` → "证书已过期，请更新 CA 证书或检查系统时间"
   - `UND_ERR_CONNECT_TIMEOUT` → "连接超时，目标服务响应过慢或不可达"
6. 验证 `fetchWithDiagnostics` 已 export，便于单元测试直接验证错误转换逻辑

**预防**：调用第三方/外部 API 必须用 `fetchWithDiagnostics` 包装原生 fetch，按 `err.cause.code` 分类翻译为可读诊断信息；响应字段必须做双重路径兼容（`data.url || data.metadata?.url`）；调用方后端语言要求的字段类型必须显式转换（如 Go 后端 string 类型用 `String(value)`）；`fetchWithDiagnostics` 必须 export，便于单元测试直接验证错误转换逻辑。

## 38. 长任务轮询定时器未清理

**症状**：用户关闭视频生成对话框后，控制台持续出现"组件已卸载仍更新状态"警告；或切换页面后定时器仍在执行网络请求，消耗带宽；或同一组件多次打开关闭后，多个定时器叠加导致请求频率异常增高。

**根因**：长任务轮询定时器未在组件卸载时清理（对应 CODING-065）：
- `setInterval` 未在 `onBeforeUnmount` 中 `clearInterval`，组件卸载后定时器仍执行
- "关闭对话框"与"重置状态"合为一个函数，关闭时未显式停止轮询
- 完成/失败时未显式 `stopXxxPolling()`，依赖 GC 回收定时器（GC 无法回收 setInterval）
- `addEventListener` 注册的监听器未在 `onBeforeUnmount` 中 `removeEventListener`（函数引用未保存）
- 第三方库实例（mermaid/marp）未在 `onBeforeUnmount` 调用其 `destroy` / `dispose` 方法

**解决**：
1. 启用 `media_generation_tests.long_task_state_machine.require_timer_cleanup: true` 自动验证定时器清理
2. 验证 `setInterval` 在 `onMounted` 启动，`clearInterval` 在 `onBeforeUnmount` 配对清理
3. `require_close_reset_split: true` 时验证"关闭对话框"（停轮询+关对话框+重置全部）与"重置状态保持对话框"（停轮询+清状态）拆为两个函数
4. 验证完成/失败显式 `stopXxxPolling()` 停止定时器，不依赖 GC 回收
5. 验证 `addEventListener` 注册的监听器在 `onBeforeUnmount` 中 `removeEventListener`（函数引用需保存，用具名函数非匿名箭头函数）
6. 验证全局事件（`globalThis.addEventListener`）配对 `globalThis.removeEventListener`
7. 验证第三方库实例（mermaid/marp）在 `onBeforeUnmount` 调用其 `destroy` / `dispose` 方法（若存在）

**预防**：长任务轮询必须用 `setInterval(poll_interval_ms)` 定时查询状态，并用 5 状态机驱动 UI 模板切换；`onBeforeUnmount` 必须清理 `abortController` + 所有 `addEventListener` + `setInterval` timer；"关闭对话框"（停轮询+关对话框+重置全部）与"重置状态保持对话框"（停轮询+清状态，允许重新生成）拆为两个函数；完成/失败显式 `stopXxxPolling()` 停止定时器，不依赖 GC 回收。

## 39. PowerShell 管道导致 EPIPE 断裂（退出码 -1）

**症状**：运行 `python orchestrator.py | Out-String` 或 `npx vue-tsc --noEmit | Select-String` 时，命令以退出码 -1 异常终止，输出被截断；或测试流程因退出码 -1 被误判为失败。

**根因**：PowerShell 对长时进程（≥30s）的管道输出处理存在 EPIPE 风险（对应 CODING-059）：
- 管道右侧命令（Select-String/Out-String/Where-Object）提前关闭读取端时，左侧写入端收到 SIGPIPE 信号
- PowerShell 将 EPIPE 映射为退出码 -1（非 0 也非 1），与真实失败混淆
- 长时进程（vue-tsc 编译 1-10 分钟、orchestrator.py 1-5 分钟）更容易触发 EPIPE
- 增量缓存未清理时 vue-tsc 耗时更长（>2 分钟），EPIPE 概率更高

**解决**：
1. 启用 `powershell_long_process.enabled: true` 自动检测长时进程管道使用
2. 移除管道，直接运行长时进程：`python orchestrator.py`（而非 `python orchestrator.py | Out-String`）
3. 需过滤输出时重定向到文件后读取：`npx vue-tsc --noEmit > tsc-output.txt 2>&1`，然后用 Grep 工具搜索
4. 退出码 -1 视为管道断裂，重新直接运行验证真实退出码
5. vue-tsc > 2 分钟时先清理增量缓存：`Remove-Item -Recurse -Force node_modules/.tmp, tsconfig.tsbuildinfo, tsconfig.app.tsbuildinfo, node_modules/.vite -ErrorAction SilentlyContinue`；同时清理 src 下 .ts 对应的 .js 编译产物

**预防**：所有运行时间 ≥ 30s 的进程必须在 PowerShell 中直接运行（不用管道）；需过滤输出时重定向到文件后用 Grep 工具读取；vue-tsc 运行前清理增量缓存确保运行时间 < 2 分钟。

## 40. 沙箱无浏览器 / 无 PyYAML 导致 E2E 与部分脚本无法运行

**症状**：运行 Playwright 浏览器 E2E 时报 Chromium 未安装（`Executable doesn't exist`）；或依赖 PyYAML 的 Python 测试脚本报 `ModuleNotFoundError: No module named 'yaml'`；或 Git Bash 下 `seq` / `sleep` / `nohup` / `ps` 命令找不到。

**根因**：
1. 沙箱环境未安装 Chromium 浏览器，完整浏览器 E2E 无法启动。
2. 沙箱 Python 环境未安装 PyYAML，部分测试脚本（`import yaml`）直接失败。
3. Git Bash（Windows）是精简 shell，缺 GNU coreutils 的 `seq` / `sleep` / `nohup` / `ps`，常用 shell 写法不兼容。

**解决**：
1. 浏览器 E2E 回退：用 Fastify `app.inject` 做真实路由层测试 + 真实 HTTP API 集成测试（vitest + `fetch`），无需浏览器；浏览器 E2E 明确降级为"未验证"项，不伪造通过。
2. PyYAML 缺失：将测试数据改为 JSON 或内联 dict，避免 `import yaml`；或仅在环境具备 PyYAML 时启用对应测试（配置项开关）。
3. Git Bash 兼容：用工具 `run_in_background` 启动长时进程（替代 `nohup ... &`）；循环用 C 风格 `for ((i=1;i<=N;i++))` 替代 `seq`；用 `taskkill /F /PID` 替代 `ps` + `kill` 清理端口占用进程。
4. 端口冲突先清理占用进程再启动：启用 `service_lifecycle.stop_old_process: true` 或 `service_manage` 步骤。

**预防**：在沙箱/CI 环境运行测试前，先探测可用能力（浏览器是否安装、PyYAML 是否可用、shell 类型），据此选择测试策略；浏览器 E2E 与依赖第三方库的脚本须有**可降级**的替代验证路径（unit + app.inject + HTTP 集成），而非硬依赖单一环境。
