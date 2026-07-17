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
