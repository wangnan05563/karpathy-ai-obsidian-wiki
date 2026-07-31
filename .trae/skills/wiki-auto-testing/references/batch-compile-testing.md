# 文件夹上传批量编译测试复盘

> 本文件保留 wiki-auto-testing 的"文件夹上传批量编译测试复盘"章节，按需加载。基于文件夹上传批量编译功能的 E2E 测试执行过程复盘，提炼可复用的六阶段测试流程与失败模式。

## 成功执行任务的完整步骤

| 步骤 | 操作 | 验证点 | 对应阶段 |
|------|------|--------|----------|
| 1 | 预检查（环境/端口/配置/PowerShell） | 所有预检项通过 | 阶段 1：预检查 |
| 2 | 服务启动（非阻塞模式） | 端口在 startup_timeout_ms 内就绪 | 阶段 2：服务启动 |
| 3 | API 端点测试（10 个端点） | 全部返回 200 | 阶段 3：动态验证 |
| 4 | 路由注册验证 + 类型同步验证 | 后端路由全部注册、前后端 types.ts 对齐 | 阶段 3：静态验证（并行） |
| 5 | UI 元素验证（11 个页面） | expected_elements 选择器全部存在 | 阶段 3：动态验证 |
| 6 | SSE 事件流验证 | batch_start→file_start→progress×8→file_done→file_complete→batch_done 完整 | 阶段 3：动态验证 |
| 7 | 编码乱码检测 + 危险操作测试 + 滚动容器测试 + SPA 跳转测试 + 检查更新测试 | 全部通过 | 阶段 4：专项验证 |
| 8 | 测试后清理（停止服务+清理临时文件） | 无残留进程 | 阶段 5：清理 |

## 不确定性与失败点

1. **端口占用冲突**：5173 被其他项目占用，被迫改用 5174，导致 config.yaml 中硬编码的 5173 失效 → 已由 port_conflict_resolution 配置块的自动迁移策略解决
2. **Vite proxy SSE 中断**：简写形式 `'/api': 'http://localhost:3000'` 缺少 changeOrigin/timeout，导致 SSE 长连接被中断，出现 'Failed to fetch' → 已由 vite_proxy_check 配置块检测
3. **PRESETS_PATH 路径解析错误**：api/src/routes/ai.ts:13 少一个 '../'，导致 llm-presets.json 找不到，API 启动崩溃 → 已由 compile_artifact_check 配置块检测路径解析
4. **PowerShell 5.1 语法限制**：不支持 &&/||，需用 ; 分隔 → 已由 powershell_compatibility 配置块检测
5. **bat 脚本 pause 阻塞**：自动化调用时 pause 等待用户按键 → 已由 bat_script.bypass_pause 配置解决
6. **日志重定向 cmd 进程残留**：taskkill 主进程后，日志重定向 cmd 仍持有句柄 → 已由 process_cleanup 配置块的 Get-CimInstance Win32_Process 命令行匹配清理
7. **Vite dev server 优先加载 .js 编译产物**：src 下同时存在 .ts 和 .js 时，Vite 直接读 .js 导致旧版代码被加载 → 已由 compile_artifact_check 配置块检测

## 可抽象的固定流程

### 六阶段测试流程

```
阶段 1：预检查（环境/端口/配置/PowerShell）→ 并行执行
    ↓（全过才继续）
阶段 2：服务启动（非阻塞+端口轮询）
    ↓
阶段 3：动态验证（API+UI+SSE） ← 并行 → 静态验证（路由注册+类型同步）
    ↓（API+UI 通过才继续）
阶段 4：专项验证（编码+危险操作+滚动+SPA+检查更新）
    ↓
阶段 5：清理（停止服务+清理临时文件）
```

### 故障分类与诊断决策树

```
服务未启动 → 检查端口占用+旧进程残留（process_cleanup）
SSE 中断 → 检查 Vite proxy 配置（vite_proxy_check：简写形式 vs 对象形式）
API 崩溃 → 检查路径解析（compile_artifact_check：import.meta.url vs process.cwd）
类型不同步 → 检查前后端 types.ts interface 字段（type_sync_check）
```

## 适用场景

- Vue 3 + Vite + Fastify 全栈项目
- SPA 手动路由（无 vue-router）项目
- SSE 长连接项目
- 多主题切换项目
- Windows PowerShell 环境项目

## 不适用场景

- 纯后端项目（无前端 UI 元素验证）
- 使用 vue-router 的 SPA（路由注册验证逻辑不同）
- Linux/macOS 环境（PowerShell 约束不适用，需改为 bash 兼容）
- 无 SSE 的项目（SSE 事件流验证不适用）
- 容器化部署项目（服务生命周期由容器编排管理，不需手动启停）

## 阶段间 DAG 依赖关系

测试阶段间存在有向无环图（DAG）依赖关系：

| 阶段 | 依赖前置阶段 | 故障传播规则 |
|------|-------------|-------------|
| 预检查 | 无（并行执行） | critical 故障中断后续所有阶段 |
| 服务启动 | 预检查全过 | critical 故障中断后续所有阶段 |
| API 端点测试 | 服务启动 | critical 故障中断 UI/SSE/专项验证 |
| 路由注册验证 + 类型同步验证 | 无（与服务启动并行，静态检查） | warning/suggestion 不中断 |
| UI 元素验证 + SSE 事件流验证 | 服务启动 + API 端点测试通过 | critical 故障中断专项验证 |
| 编码乱码检测 + 危险操作测试 + 滚动容器测试 + SPA 跳转测试 + 检查更新测试 | UI 元素验证通过 | warning/suggestion 不中断 |
| 测试后清理 | 最后执行（无论前序成败） | 必须执行 |

关键规则：
- **critical 故障**从任意阶段向上传播，中断后续依赖阶段
- **warning/suggestion**不中断后续阶段
- **测试后清理**必须执行（即使前序阶段失败）

## 新增配置块说明

### vite_proxy_check（Vite Proxy 配置检查）

检测 Vite proxy 配置是否为对象形式（含 changeOrigin/timeout/proxyTimeout），避免 SSE 长连接中断。

### port_conflict_resolution（端口冲突自动迁移）

配置端口被占用时的自动迁移策略（检测实际可用端口并更新 config）。

### compile_artifact_check（编译产物污染检测）

检测 src 下是否同时存在 .ts 和 .js 文件，避免 Vite 加载旧编译产物；检测路径解析是否采用 import.meta.url 三级策略。

### process_cleanup 增强（进程残留清理增强）

在 service_lifecycle 基础上增强：日志重定向 cmd 残留清理策略（Get-CimInstance Win32_Process 命令行匹配）。
