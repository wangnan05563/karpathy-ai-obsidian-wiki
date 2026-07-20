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
