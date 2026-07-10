---
name: "wiki-auto-testing"
description: "Automates end-to-end frontend testing with Playwright: build, start services, run page/interaction/API/responsive tests, button auto-discovery, fix issues. Invoke when user asks to test frontend, run e2e tests, or verify system after changes."
---

# Wiki Auto Testing

基于 Playwright 的前端自动化测试技能。覆盖构建、启动、页面导航、交互功能、API 端点、响应式布局、控制台错误检查的全流程测试。

## 触发条件

当用户提出以下请求时调用本技能：
- "测试前端" / "全面测试" / "e2e 测试"
- "构建后测试" / "启动后测试"
- "验证系统是否正常"
- "Playwright 测试" / "浏览器测试"

## 前置条件

1. **Playwright 已安装**：`python -c "from playwright.sync_api import sync_playwright"` 可正常执行
2. **PyYAML 已安装**：`python -c "import yaml"` 可正常执行
3. **配置文件存在**：`.trae/skills/wiki-auto-testing/config.yaml` 已按项目实际情况配置
4. **项目根标记存在**：项目根目录下有 `.git` 或 `package.json`（用于工作目录自动定位）
5. **构建脚本可用**（如需构建）：`build.script_path` 指向的构建脚本存在
6. **启动脚本可用**（如需启动）：`startup.script_path` 指向的启动脚本存在
7. **编码兼容**：Python 脚本以 UTF-8 无 BOM 保存（脚本内置 `ensure_utf8()` 自动修复）

## 配置文件

所有参数集中在 `config.yaml` 中管理，技能本身不含任何硬编码值。修改配置文件即可适配不同项目，无需改动技能代码。

关键配置项：

| 配置块 | 用途 | 适配场景 |
|--------|------|----------|
| `working_directory` | 项目根目录标记、自动 chdir | 避免 CWD 不一致导致 FileNotFoundError |
| `build` | 构建脚本路径、产物路径、超时 | dev server 模式可设 enabled: false 跳过 |
| `startup` | 启动脚本路径、停止脚本 | 服务已运行时可设 enabled: false 跳过 |
| `service` | 前后端地址、端口、健康检查 | 不同项目的端口/地址 |
| `browser` | headless、启动参数、视口 | CI/调试切换、响应式测试 |
| `navigation` | 导航选择器、页面列表 | 不同 SPA 的 tab 结构 |
| `button_discovery` | 按钮选择器、排除规则、破坏性保护 | 自动发现并测试所有可交互按钮 |
| `interactions` | 交互行为定义 | 不同页面的表单/按钮 |
| `api_tests` | API 端点列表 | 不同后端的 API 路由 |
| `console_error_filter` | 错误过滤关键词 | 忽略第三方库噪声 |
| `timeout` | 各类超时 | 网络慢/页面大的项目 |
| `output` | 截图/结果路径、编码 | 输出位置自定义 |
| `encoding_safety` | BOM、编码检查、自动修复 | Windows 环境编码处理 |
| `bat_script` | pause 绕过 | bat 脚本自动化 |
| `terminal` | 命令拆分、新终端 | PowerShell PSReadLine 兼容 |

## 测试流程（6 阶段）

### 阶段 1：构建

```
1. 读取 config.yaml 获取构建脚本路径
2. 运行构建脚本（bat 文件通过管道输入绕过 pause）
3. 检查构建产物是否存在（index.html）
4. 如果构建失败 → 检查源码问题 → 修复 → 重新构建
```

**判断逻辑**：构建成功 = exit code 0 ∧ 产物 index.html 存在

**常见问题**：
- 源文件编码损坏（GBK/UTF-8 混乱）→ 检测编码并重写
- TypeScript 编译错误 → 修复类型错误后重新构建
- bat 脚本 `pause` 阻塞 → 管道输入 `""` 或 `< nul` 绕过

### 阶段 2：启动服务

```
1. 运行启动脚本
2. 轮询端口（config.startup_timeout_sec 内每 port_check_interval_sec 秒检查一次）
3. 验证 API 健康检查端点返回 HTTP 200
4. 验证前端页面可访问
```

**判断逻辑**：服务就绪 = API 端口监听 ∧ 前端端口监听 ∧ /health 返回 200

### 阶段 3：基础功能测试

```
1. 首页加载：goto(frontend_url) + wait_for_load_state('networkidle')
2. 验证 page.title() 非空
3. API 健康检查：访问 health_endpoint，解析响应
4. 逐个点击 navigation.pages 中的 tab 按钮
5. 每个页面验证 expected_elements 存在性（locator.count() > 0）
6. 截图保存到 output.screenshot_dir
7. 收集控制台错误（过滤 console_error_filter 中的关键词）
```

**判断逻辑**：
- 页面加载成功 = HTTP 200 ∧ title 非空 ∧ networkidle 完成
- 元素存在 = `locator.count() > 0`
- 无控制台错误 = 过滤后错误列表为空

### 阶段 4：交互功能测试

```
1. 主题切换：打开面板 → 选择主题 → 验证 data-theme 属性变化
2. 表单输入：定位输入框 → fill 文本 → 提交 → 验证无异常
3. 标签页切换：点击 el-tabs__item → 验证内容区域变化
4. 按钮交互：点击编辑/保存/运行按钮 → 验证状态变化
5. 按钮自动发现（NEW）：遍历所有页面 → 按 button_selectors 发现按钮
   → 检查排除选择器 → 检查破坏性文本 → 安全点击 → 验证无异常
   → 点击后导航回当前页面 → 继续下一个按钮
```

**判断逻辑**：交互成功 = 操作完成无异常 ∧ 预期状态变化已发生

**按钮自动发现策略**：
- 遍历 `navigation.pages` 中所有页面
- 对每个页面应用 `button_discovery.button_selectors` 中的所有选择器
- 排除匹配 `exclude_selectors` 的元素（如 `.is-disabled`）
- 匹配 `destructive_button_texts` 的按钮仅验证存在，不执行点击
- 使用 `force_click: true` 绕过 Vue transition 动画时序问题
- 每次点击后导航回当前页面，确保测试隔离

**常见问题**：
- Vue transition 动画导致元素不稳定 → 使用 `dispatchEvent` 或 `force=True`
- Element Plus 选择器不匹配 → 使用 `.el-tabs__item` 等组件库特定选择器
- textarea 不可见 → 先切换到对应标签页再操作（使用 `:visible` 伪选择器）
- 破坏性按钮误点击 → 配置 `destructive_button_texts` 列表保护

### 阶段 5：补充测试

```
1. 响应式测试：切换到 mobile 视口 → 验证页面渲染
2. API 端点测试：遍历 api_tests.endpoints → 验证 HTTP 状态码
3. CORS 注意：使用 Playwright context.request API 而非浏览器端 fetch
```

**判断逻辑**：
- 响应式正常 = 不同视口下 body 可见 ∧ 页面渲染无崩溃
- API 正常 = 所有端点返回 expected_status

### 阶段 6：结果汇总与修复

```
1. 汇总所有测试结果（PASS/FAIL 计数）
2. 将结果写入 output.result_file（JSON 格式）
3. 如有失败 → 分析原因 → 修复 → 重新运行失败项
4. 最终验证：全部测试通过（failed == 0）
```

**判断逻辑**：测试通过 = `failed == 0`

## 判断逻辑汇总

| 检查项 | 判断方式 | 失败处理 |
|--------|----------|----------|
| 工作目录 | .git 标记存在 ∧ auto_chdir 成功 | 手动指定 config 路径 |
| 构建成功 | exit code 0 ∧ 产物存在 | 检查源码编码/类型错误 |
| 服务就绪 | 端口监听 ∧ /health 200 | 检查启动日志/依赖 |
| 页面加载 | HTTP 200 ∧ title 非空 | 检查前端路由/构建 |
| 元素存在 | count() > 0 | 检查选择器/组件渲染 |
| 交互成功 | 操作无异常 ∧ 状态变化 | 检查事件绑定/transition |
| 按钮发现 | found > 0 ∧ failed == 0 | 检查选择器/force_click |
| API 正常 | response.ok | 检查后端路由/CORS |
| 控制台无错误 | 过滤后列表为空 | 检查 JS 运行时错误 |
| 响应式正常 | 多视口渲染成功 | 检查 CSS 媒体查询 |
| 脚本编码 | UTF-8 可解码 ∧ 无 BOM | 自动转换 GBK → UTF-8 |

## 常见问题处理

### 1. 浏览器崩溃（Canvas/WebGL 页面）

**症状**：`Target crashed` / `Page closed`
**原因**：headless 模式下 Canvas/WebGL 渲染消耗过多内存
**解决**：在 `config.yaml` 的 `browser.launch_args` 中确保包含 `--disable-gpu`

### 2. 源文件编码损坏

**症状**：TypeScript 编译报大量语法错误（Unterminated string literal 等）
**原因**：文件以 GBK 编码保存，在 UTF-8 环境下中文字符损坏
**解决**：
1. 读取文件检查编码
2. 如有损坏，根据代码结构推断原始内容并重写
3. 以 UTF-8 编码（无 BOM）重新保存

### 3. Python 脚本 BOM 问题

**症状**：`SyntaxError: invalid character '?' (U+FEFF)`
**原因**：PowerShell `[System.IO.File]::WriteAllText` 默认添加 BOM
**解决**：用 Python 写入文件，或写入后用 Python 移除 BOM：
```python
content = open('script.py', 'rb').read()
if content.startswith(b'\xef\xbb\xbf'):
    content = content[3:]
open('script.py', 'wb').write(content)
```

### 4. Python stdout 缓冲

**症状**：测试执行完成但终端无输出
**原因**：Python stdout 在 PowerShell 管道中被缓冲
**解决**：
1. 使用 `python -u` 参数运行（unbuffered）
2. 将结果写入 JSON 文件而非依赖 stdout
3. 避免在 Python 文件中使用非 ASCII 注释（或确保文件以 UTF-8 无 BOM 保存）

### 5. Vue transition 动画时序

**症状**：`Locator.click: Timeout` / `element is not stable`
**原因**：Vue `<transition>` 组件的过渡动画期间元素不可点击
**解决**：
1. 使用 `page.evaluate()` + `dispatchEvent(new MouseEvent('click', {bubbles: true}))` 绕过
2. 或使用 `locator.click(force=True)` 跳过稳定性检查
3. 增加 `transition_wait_ms` 等待时间

### 6. CORS 错误

**症状**：控制台出现 `Access-Control-Allow-Origin` 错误
**原因**：测试脚本从浏览器端直接 fetch 跨域 API
**解决**：在 `api_tests` 中设置 `use_playwright_request: true`，使用 `context.request.get()` 代替浏览器端 fetch

### 7. bat 脚本 pause 阻塞

**症状**：运行 bat 脚本后流程卡住等待输入
**原因**：bat 脚本中的 `pause` 命令等待按键
**解决**：通过管道输入空行绕过：`"" | & "script.bat"` 或 `cmd /c "script.bat" < nul`

### 8. 工作目录不一致导致 FileNotFoundError

**症状**：`FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'`
**原因**：AI 在子目录（如 `karpathy-wiki/`）中执行 Python 脚本，但 config.yaml 在项目根目录
**解决**：
1. 在 config.yaml 中配置 `working_directory.auto_chdir: true`
2. 脚本通过 `find_project_root()` 从脚本位置向上查找 `.git` 标记
3. 自动 `os.chdir(project_root)` 切换到项目根目录
4. 优先使用绝对路径而非相对路径

### 9. Python 脚本 GBK 编码（Write 工具副作用）

**症状**：`SyntaxError: invalid character` 或 `UnicodeDecodeError`
**原因**：Windows 上 Write/编辑工具以 GBK 编码保存含中文的 .py 文件
**解决**：
```python
# 检测并转换编码
p = 'script.py'
content = open(p, 'r', encoding='gbk').read()
open(p, 'w', encoding='utf-8').write(content)
```
或在 config.yaml 中设置 `encoding_safety.auto_fix_python_encoding: true`，脚本启动时自动检测和转换。

### 10. PSReadLine 缓冲区崩溃

**症状**：`System.ArgumentOutOfRangeException: top` 或终端无响应
**原因**：PowerShell PSReadLine 模块对超长命令行（>200字符）缓冲区溢出
**解决**：
1. 拆分长命令为多条短命令（每条 < 200 字符）
2. 使用 `target_terminal: new` 创建新终端（避免 PSReadLine 状态污染）
3. 将复杂逻辑写入 .ps1 / .py 脚本文件，通过 `python script.py` 调用
4. 在 config.yaml 中设置 `terminal.split_long_commands: true`

### 11. Glob 工具与中文路径不兼容

**症状**：Glob 工具对包含中文的路径返回 "No file found"，但文件实际存在
**原因**：Glob 工具的路径匹配引擎对 Unicode 字符处理有局限
**解决**：
1. 改用 RunCommand + PowerShell `Get-ChildItem` 列举文件
2. 使用绝对路径（包含中文字符）直接 Read 文件
3. 避免在 Glob pattern 中使用中文路径段

## 适用场景

- ? Vue 3 / React / Angular 等 SPA 应用
- ? Vite / Webpack 构建的前端项目
- ? 有独立后端 API 的全栈项目
- ? Element Plus / Ant Design / Vuetify 等组件库项目
- ? Windows 环境下的 Playwright 测试
- ? 有构建脚本（bat/sh）和启动脚本的项目

## 不适用场景

- ? 纯静态 HTML 页面（无需 networkidle 等待，可直接用 file:// URL）
- ? 移动端 App 测试（需要 Appium 或 Espresso 等工具）
- ? 需要 OAuth/SSO 认证的页面（需要额外的登录流程配置）
- ? SSR 应用（服务端渲染时机不同，需要不同的等待策略）
- ? WebSocket 密集的应用（需要特殊的等待和断言策略）
- ? 无构建脚本的裸 HTML 项目

## 技能文件结构

```
.trae/skills/wiki-auto-testing/
├── SKILL.md              # 本文件：技能定义和流程指导
├── config.yaml           # 所有可配置参数（无硬编码）
└── templates/
    └── test_suite.py     # 参数化测试脚本模板
```

## 使用方式

1. 确保 `config.yaml` 已按项目实际情况配置（端口、选择器、页面列表等）
2. 如服务已运行，设 `build.enabled: false` 和 `startup.enabled: false` 跳过构建/启动
3. 调用本技能（或告知 AI "测试前端"）
4. AI 将按照 6 阶段流程执行测试：
   - 阶段1-2：构建+启动（可跳过）
   - 阶段3：基础功能（导航+元素+控制台）
   - 阶段4：交互功能（主题+表单+标签页+**按钮自动发现**）
   - 阶段5：补充测试（响应式+API端点）
   - 阶段6：结果汇总+修复+回归
5. 测试结果保存在 `output.result_file` 和 `output.screenshot_dir` 中
6. 如有问题，AI 会自动修复并重新验证
7. 按钮自动发现会遍历所有页面、点击所有非破坏性按钮，覆盖盲区

## 适配新项目

将本技能适配新项目只需修改 `config.yaml`：

1. **服务地址**：修改 `service.frontend_url` 和 `service.api_url`
2. **导航结构**：修改 `navigation.tab_selector` 和 `navigation.pages` 列表
3. **按钮选择器**：修改 `button_discovery.button_selectors` 匹配目标项目的组件库
4. **API 端点**：修改 `api_tests.endpoints` 列表
5. **构建/启动脚本**：修改 `build.script_path` 和 `startup.script_path`
6. **破坏性按钮**：在 `button_discovery.destructive_button_texts` 中添加需要保护的按钮文本
