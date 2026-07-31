# 必检清单（详细版）

> 从 SKILL.md 拆分而来

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
□ 外部 API 调用全部用 fetchWithDiagnostics 包装（Grep 搜索业务代码无原生 fetch 调用），错误码按 external_api.diagnostic_error_codes 映射
□ 外部 API 响应关键字段用双重路径兼容（data.x || data.y?.x），Go/Rust 后端字段已显式类型转换（String()/Number()）
□ AbortSignal.timeout 按任务类型分级（task_creation/task_polling/image_generation/video_download/llm_small/llm_large），无字面量硬编码超时值
□ API Key 解析按"专用段→共享段→环境变量"三级回退，全部缺失时错误消息列出三个配置位置
□ 长任务（>30s）走独立 JSON 端点 + 前端轮询（非 SSE 流），破坏性端点限流 ≤5/min，轮询端点限流 60/min
□ 长任务错误码区分配置缺失（400）与 API 失败（500），错误同时输出 JSON 响应 + request.log.error 双日志通道
□ 路由文件顶部含"设计要点"块注释（端点职责/限流策略/关键设计决策的"为什么"）
□ LLM 生成产物归档到 vault/queries/ 含 type/output_mode/generated_at 三必备字段，文件名匹配 <mode>-YYYYMMDD-HHmmss.<ext> 模式
□ 归档/查询接口不接受客户端传内容字段，只接受 sessionId+messageIndex 引用，内容从服务端 sessions 取
□ LLM prompt 模板存放在 prompts/ 目录（非源码内联），运行时 fs.readFile 加载，长度 >200 字符的 prompt 未内联
□ SSE 事件处理器用 Record<string, Handler> 对象映射表（事件类型 ≥3 时），认知复杂度 <15，未知事件有默认 handler
□ SSE 流消费函数吞掉 AbortError（err.name === 'AbortError' 直接 return），finally 中 reader.cancel() 兜底释放，signal 参数可空
□ 长任务 UI 用 5 状态机（idle/queued/processing/completed/failed），轮询单次失败不终止（连续 3 次才终止），完成/失败显式 stopPolling()
□ 长任务超时用 setTimeout（非 AbortSignal.timeout）以同步设 abortReason，"关闭对话框"与"重置状态保持对话框"拆为两个函数
□ v-html 渲染内容的事件用父容器 addEventListener 委托（非 Vue 指令），onBeforeUnmount 移除所有监听器（函数引用保存，非匿名）
□ 全局事件 globalThis.addEventListener 已配对 removeEventListener，第三方库实例（mermaid/marp）已调用 destroy/dispose
□ 重库（>200KB）用动态 import() 加载，模块级 xxxLoaded 标志避免重复加载，CJS 命名导出用 mod.X ?? mod.default?.X 兼容访问
□ 不可控重库已实现五层错误防护（库选项抑制 + parse 预验证 + 渲染前清空 + catch 清空 + CSS 隐藏错误元素），渲染失败降级显示 <pre>{{ raw }}</pre>
```
