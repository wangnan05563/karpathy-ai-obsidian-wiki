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
