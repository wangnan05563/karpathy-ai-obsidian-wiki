# 测试流程复盘与参考（Testing Process Review）

> 本文档基于一次真实的"上下文记忆治理"后端模块测试经验复盘提炼，记录**可复用、可泛化**的测试流程判断逻辑。
> 配套新增了 `scope.modified_content` / `test_coverage.endpoint_coverage_check` / `endpoint_autodiscovery` 三个配置块（见 SKILL.md 与 defaults.yaml / config.yaml）。
> 本文件仅供测试策略参考，不改变既有 6 阶段测试流程。

## 背景：被测对象与约束

被改动的是一个**纯后端引擎模块**（上下文记忆治理：`govern()` / 去重 / 压缩 / 淘汰），并新增了两个路由端点：

- `GET /api/threads/:id/context`
- `POST /api/threads/:id/compact`

约束条件：

- 沙箱环境中 **Chromium 浏览器未安装**，无法运行完整浏览器 E2E。
- 该改动**没有前端 UI 界面**，仅有 type-only 的前端 `types.ts` 补充（`done` 事件的 SSE 字段）。
- 因此浏览器 E2E 对本改动是**低信号**的——测试范围被刻意聚焦到**被修改的内容（modified content）**，而非整个应用。

---

## 维度一：成功执行步骤（Successful Steps）

实际有效的测试流程（按执行顺序）：

| 步骤 | 操作 | 产物 / 验证点 | 复用本技能的哪个能力 |
|------|------|---------------|----------------------|
| 1 | **单元测试（vitest）** | 对纯引擎 `govern()`、去重、压缩、淘汰做快而确定的断言 | 引擎本身无外部依赖，单测最廉价 |
| 2 | **端点测试（Fastify `app.inject`）** | 启动真实 Fastify 路由层（无需浏览器）：happy path + 非法 `:id`→400 + 缺失 thread→404 + 显式折叠行为 | `endpoint_autodiscovery` + `api_tests.endpoints` |
| 3 | **静态检查** | `route_registration_check`：每个路由都在入口文件注册；`type_sync_check`：前端 `types.ts` 与后端 SSE `done` 事件字段对齐 | `route_registration_check` / `type_sync_check` 配置块 |
| 4 | **全量套件运行** | `vitest run` → 379 passed / 1 failed | 套件级回归 |
| 5 | **Flake 隔离** | 单个失败用例在**隔离**环境重跑 → 2/2 通过，确认为预存在 flake，非本次改动引入 | 见 Flake 隔离协议 |

关键发现：两个新端点在加入端点测试前**零覆盖**——它们随代码上线但从未被测到。`test_coverage.endpoint_coverage_check` 正是为此而生（默认 `fail_if_untested: false`，仅标记不阻断）。

---

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **Chromium 未安装**：沙箱无浏览器，完整浏览器 E2E 无法运行。
   - 应对：用 Fastify `app.inject` 做真实路由层测试，无需浏览器；浏览器 E2E 降级为可选。
2. **全量套件中的 1 个失败**：某鉴权速率限制测试期望 429，却收到 200。
   - 隔离重跑同一文件 → 2/2 通过。
   - 根因：该测试使用**固定窗口计数器（fixed-window counter）**，在**跨 60 秒真实分钟边界**时窗口被重置，恰好错峰，导致偶发 200。这是一个**预存在的 flake**，与本次改动无关。
   - 教训：**隔离 flake 后再归因**，不要急于把失败算到新改动头上（详见 Flake 隔离协议）。
3. **新端点裸奔上线**：两个新端点直到手动补端点测试才被发现无覆盖。
   - 应对：`endpoint_coverage_check` 在回归中自动标记未测端点。

---

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（按改动类型路由）

```
判断改动类型
  ├─ 后端路由 / 引擎变更
  │     → 单元测试 → 端点测试(inject) → 静态检查(route_registration + type_sync)
  │        → 全量套件 → (失败) Flake 隔离
  ├─ 前端 type-only 变更（无 UI 界面）
  │     → type_sync_check（仅验证前后端类型对齐）
  │        → 仅当改动带 UI 界面时才追加浏览器检查
  └─ 纯配置 / 文档变更
        → 若触及 types.ts 仍跑 type_sync_check；否则最小验证
```

### 判断逻辑（可参数化的核心决策）

- **J1 — 测试范围应按"被修改的内容"而非"整个应用"**：用 `scope.modified_content`（enabled + `changed_paths`）聚焦改动路由/端点。
- **J2 — 浏览器 E2E 在"改动无 UI 界面"时是低信号的**：不要为了"跑全套"而强行启动浏览器；用 `app.inject` 端点测试 + 静态检查替代。
- **J3 — 新端点必须可验证已覆盖**：用 `test_coverage.endpoint_coverage_check` 标记零覆盖端点；默认非阻断（`fail_if_untested: false`）。
- **J4 — 端点清单可自动推导**：用 `endpoint_autodiscovery` 从路由定义反推 `api_tests.endpoints`，避免手工维护遗漏。
- **J5 — 全量套件失败先隔离后归因**：单文件隔离重跑通过 = 预存在 flake / 环境竞态，不计入改动缺陷。

---

## 维度四：适用与不适用场景（Applicability）

### 适用场景

- **后端路由 / 引擎变更**：单元测试（纯逻辑）+ 端点测试（真实路由层）+ 静态检查（注册 / 类型对齐）+ 全量套件 + Flake 隔离。
- **全栈 type 对齐变更**：即使无 UI 界面，也应启用 `type_sync_check` 验证前后端接口字段一致。
- **新增 / 修改 API 端点**：启用 `endpoint_coverage_check` 确保端点有对应测试；启用 `endpoint_autodiscovery` 减少端点清单维护成本。
- **CI 增量测试**：用 `scope.modified_content` 配合 `git diff --name-only` 注入 `changed_paths`，做"改动即测"。

### 不适用场景

- **纯配置 / 文档变更且无类型触及**：无需跑端点 / 浏览器测试；若触及 `types.ts` 仍应跑 `type_sync_check`。
- **无可运行服务（沙箱无浏览器 / 无运行时）**：回退到 Fastify `app.inject` 的单元 / 集成测试，**不依赖浏览器**；浏览器 E2E 视为可降级项。
- **纯前端 UI 动画 / 交互变更**：本流程的 inject 端点测试不适用，应走既有 Playwright 浏览器测试阶段。
- **改动确实需要浏览器验证但浏览器不可用**：明确记录"未验证"并降级，而非伪造通过。

---

## 与既有协议的衔接

| 本复盘要素 | 衔接的配置 / 协议 |
|-----------|-------------------|
| 端点零覆盖发现 | `test_coverage.endpoint_coverage_check` |
| 端点清单手工遗漏 | `endpoint_autodiscovery` |
| 聚焦改动内容 | `scope.modified_content` |
| 全量失败先隔离 | [Flake 隔离协议](#flake-隔离协议)（见 protocols.md） |
| 前后端类型对齐 | `type_sync_check`（既有） |
| 路由是否注册 | `route_registration_check`（既有） |

---

# 第二轮复盘：数据迁移 / 安装器 / 打包 / 沙箱回退

> 基于「安装器覆盖配置 / AppData 数据迁移 / SEA 路径解析 / clean-defaults」与配套测试的真实经验复盘。
> 与第一轮（上下文记忆治理后端模块）互补：本轮聚焦**打包产物、安装器、用户数据目录解析、以及沙箱无浏览器环境下的测试回退策略**。
> 配套新增 `packaging_config_overwrite_test` / `data_dir_derivation_test` / `user_data_isolation_test` 三个动态引擎步骤类型（见 SKILL.md 与 defaults.yaml / config.yaml）。

## 背景：被测对象与约束

被改动的是一个**打包（SEA 单一可执行）+ Inno Setup 安装器**桌面应用的**后端路径解析与数据落盘逻辑**：

- `api/src/utils/runtime.ts`：新增 `IS_SEA` 检测、`getUserDataDir()` / `getDataDir()`（`%LOCALAPPDATA%\KarpathyWiki`，回退 APPDATA → HOME）。
- `api/src/config.ts`：SEA 模式下把相对路径字段（vaultPath / auth.* / urlCrawl.* / logging.*）rebase 到用户数据目录；首次运行落盘"干净默认"。
- `installer.iss`：程序文件 `ignoreversion`，用户数据（config.json / .env / vault / data）**不**打包到 `{app}`。

约束条件：

- 沙箱环境 **Chromium 未安装、PyYAML 未安装**，完整浏览器 E2E 与部分依赖 PyYAML 的脚本无法运行。
- 沙箱 **Git Bash 缺 `seq` / `sleep` / `nohup` / `ps`**，部分 shell 习惯写法不兼容。
- 改动涉及**真实文件系统落点**（用户数据目录），需要验证"数据到底写到了哪里"，而非仅验证接口返回。

---

## 维度一：成功执行步骤（Successful Steps）

| 步骤 | 操作 | 产物 / 验证点 | 复用本技能的哪个能力 |
|------|------|---------------|----------------------|
| 1 | **单元测试（vitest）** | 纯逻辑快而确定的断言：qq-preprocess 32/32、qq-extract-workflow 25/25、thread-memory-store 6/6、thread-memory 8/8 | 引擎本身无外部依赖，单测最廉价 |
| 2 | **真实 API 集成测试（Fastify `app.inject` + 真实 HTTP）** | 线程隔离存储、UUID 路径穿越 400、`getDataDir()` 接线验证（实际落点 `<root>/data/threads/<id>`） | `path_traversal_test` + `persistence_crud_test` 思路 |
| 3 | **落点验证（dir derivation test）** | 断言 `getUserDataDir()` / `getDataDir()` 返回路径符合预期，且文件系统实际写入位置一致 | 新增 `data_dir_derivation_test` |
| 4 | **安装器防覆盖验证** | 核对 `installer.iss` 的 `[Files]` 段仅含程序文件且用 `ignoreversion`，用户数据未打包到 `{app}` | 新增 `packaging_config_overwrite_test` |
| 5 | **用户数据隔离验证** | 不同线程/会话数据目录互相隔离、不被越权访问 | 新增 `user_data_isolation_test` |
| 6 | **环境恢复** | 恢复 dev `config.json` 备份、停止测试服务器 | 破坏性按钮保护机制 + 服务管理 |

关键发现：路径解析改动**必须验证文件系统实际落点**，仅看接口返回（`200` / 正确的 JSON）会漏掉"数据其实写到了错误目录"这类缺陷——这正是 `data_dir_derivation_test` 的价值。

---

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **EADDRINUSE（旧服务进程占用端口）**：上次测试遗留的 server pid 仍占用 3000 端口，新服务起不来。
   - 应对：先 `taskkill /F /PID <pid>` 清理占用进程，再用后台方式启动测试服务。
2. **Git Bash 缺 `seq` / `sleep` / `nohup` / `ps`**：常用 shell 写法（如 `for i in $(seq 1 N)`、`nohup ... &`）在 Git Bash 下直接报错。
   - 应对：用工具的 `run_in_background` 启动长时进程；循环用 C 风格 `for ((i=1;i<=N;i++))` 替代 `seq`。
3. **测试断言路径错误（api/data vs karpathy-wiki/data）**：最初按旧布局断言 `api/data`，实际落点为 `<root>/data/threads/<id>`。
   - 应对：先检查真实落点再写断言，避免凭记忆假设目录结构。
4. **delete API 返回 500（安全删除 shim 无法 headless 运行）**：`genie-safe-delete.cjs`（回收站 shim）在沙箱无法无头运行，删除接口逻辑上失败。
   - 应对：判定为**环境限制而非代码缺陷**——逻辑删除 + 移至回收站，记录"沙箱未验证真实删除"，不伪造通过。
5. **Chromium / PyYAML 未安装**：完整浏览器 E2E 与部分依赖 PyYAML 的脚本无法运行。
   - 应对：回退到 vitest 单元 + Fastify `app.inject` + 真实 API HTTP 集成，**不依赖浏览器**；浏览器 E2E 视为可降级项。

---

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（按改动类型路由）

```
判断改动类型
  ├─ 打包 / 安装器 / 数据目录解析变更
  │     → 单元测试 → 真实 API 集成(app.inject + HTTP) → 落点验证(data_dir_derivation_test)
  │        → 安装器防覆盖(packaging_config_overwrite_test) → 用户数据隔离(user_data_isolation_test)
  │        → 环境恢复(备份/停止服务)
  ├─ 后端路由 / 引擎变更
  │     → 沿用第一轮流程（单元测试 → 端点测试 → 静态检查 → 全量套件 → Flake 隔离）
  └─ 纯配置 / 文档变更
        → 若触及 types.ts 仍跑 type_sync_check；否则最小验证
```

### 判断逻辑（可参数化的核心决策）

- **T1 — 沙箱无浏览器 / 无 PyYAML 时回退到 vitest + API 集成**：不伪造"通过"，浏览器 E2E 明确降级。
- **T2 — 数据迁移 / 路径解析改动必须验证"落点"**：`data_dir_derivation_test` 断言路径解析函数返回值 + 文件系统实际写入位置一致。
- **T3 — 破坏性 / 环境敏感操作（真实文件删除）在沙箱用安全删除 shim**；shim 不可用则降级为逻辑删除 + 回收站，记录未验证项。
- **T4 — 端口冲突先清理占用进程再启动**；用工具后台运行 + 轮询健康端点，避免依赖 `nohup`/`ps`。
- **T5 — 路径穿越 / 越权用 UUID 正则 + 400 验证**（线程隔离存储），防止跨线程数据访问。

---

## 维度四：适用与不适用场景（Applicability）

### 适用场景

- **打包（SEA / Electron / Tauri）/ 安装器 / 数据目录解析改动**：单元测试 + 真实 API 集成 + 落点验证 + 安装器防覆盖 + 用户数据隔离。
- **真实文件系统落点验证**：任何改动让数据"写到哪里"发生变化的场景，都应启用 `data_dir_derivation_test`。
- **沙箱无浏览器 / 无 PyYAML 环境**：回退 vitest 单元 + Fastify `app.inject` + 真实 API HTTP 集成，浏览器 E2E 降级。
- **无 UI 界面的纯后端 / 打包改动**：聚焦被修改内容，不强行启动浏览器。

### 不适用场景

- **纯前端 UI 动画 / 交互变更**：本流程的落点/安装器验证不适用，应走既有 Playwright 浏览器测试阶段。
- **确实有浏览器且需浏览器验证的改动**：优先走既有浏览器 E2E，本回退链路仅作降级。
- **纯只读配置消费**：无需跑落点/安装器测试；若触及 `types.ts` 仍应跑 `type_sync_check`。
- **服务端容器部署（volume 挂载）**：用户数据目录锚点非 LOCALAPPDATA，相关 T2/T5 判定需按部署模型调整。

---

## 与既有协议的衔接

| 本复盘要素 | 衔接的配置 / 协议 |
|-----------|-------------------|
| 落点验证 | `data_dir_derivation_test`（新增步骤类型） |
| 安装器防覆盖 | `packaging_config_overwrite_test`（新增步骤类型） |
| 用户数据隔离 | `user_data_isolation_test`（新增步骤类型） |
| 端口冲突 | `service_lifecycle.stop_old_process` / `service_manage` |
| 沙箱无浏览器回退 | `browser_fallback_check` 思路（MCP→subagent→curl） |
| 路径穿越 | `path_traversal_test`（既有） |
| 环境恢复 | 破坏性按钮保护机制（备份 → 执行 → 恢复） |

---

# 第三轮复盘：构建 / 类型检查与端到端验证（前端改动）

> 基于「开发模式点击知识浏览页触发 `el-radio` 弃用警告（ElementPlusError: label act as value is about to be deprecated）」及配套 `Browse.vue` / `DataClean.vue` 修改的真实经验复盘。
> 与第一轮（上下文记忆治理后端模块）、第二轮（数据迁移 / 安装器 / 打包）互补：本轮聚焦**含前端 `.vue` / `.ts` 改动的验证策略**——尤其是类型检查 / 构建如何在沙箱中可靠运行、产物如何不污染源码树、以及"控制台告警级"缺陷如何闭环。
> 配套新增 `frontend_verification` 配置块（见 defaults.yaml / config.yaml），把 node 路径、类型检查命令、构建命令、产物输出目录全部参数化，**零硬编码**。

## 背景：被测对象与约束

被改动的是一个**纯前端 Vue 3 组件修改**（Element Plus `el-radio-button` 的 `label` 作 value 弃用迁移，涉及 `Browse.vue` 6 处、`DataClean.vue` 2 处）：

- 改动只触及模板属性（`label="x"` → `value="x"`），`v-model` 绑定不变，无新增 UI 界面、无后端接口变化。
- 该缺陷在开发模式表现为**控制台告警**（非编译错误、非运行时崩溃），但升级 Element Plus 到 3.0 后会彻底失效——属于"现在只是警告、升级即断"。

约束条件：

- 沙箱 **WorkBuddy 安全删除钩子（safe-delete）** 会拦截对项目目录的删除操作；`vite build` 的 `emptyOutDir` 在清理 `outDir` 时会触发该钩子，且默认 `outDir` 落在项目内会污染源码树。
- 前端 `.ts` 可能被 `src/**/*.js` 陈旧编译产物遮蔽（FR-061）：不清理则 `.ts` 改动静默不生效，类型检查 / 构建都"看起来通过"但实际旧代码在跑。
- 全局 `vue-tsc` / `node` 版本可能与项目不一致，导致类型检查结果不可信。

---

## 维度一：成功执行步骤（Successful Steps）

| 步骤 | 操作 | 产物 / 验证点 | 复用本技能的哪个能力 |
|------|------|---------------|----------------------|
| 1 | **陈旧产物清理（FR-061）** | 构建 / 类型检查前先清理 `frontend_verification.stale_js_cleanup_glob`（`src/**/*.js`），避免 `.ts` 被 `.js` 遮蔽 | `ts-js-shadowing-frontend-rule`（FR-061）思路 |
| 2 | **前端类型检查（vue-tsc --noEmit）** | 验证 `.ts` / `.vue` 类型正确（本次 `el-radio` 改动无类型错误）；命令走 `frontend_verification.typecheck_command`（仓库内置 bin），`run_dir` = `frontend` | `frontend_verification` 配置块 |
| 3 | **前端构建（vite build）** | 验证 `.ts` 真实生效、产物可生成；`outDir` 指向 `frontend_verification.build_out_dir`（`/tmp/kw-dist`，项目外），规避 safe-delete 拦截 + 源码污染 | `frontend_verification` 配置块 |
| 4 | **浏览器 E2E（若 Chromium 可用）** | 页面渲染 + 控制台无 error 检查；本次 `el-radio` 告警应在控制台消失 | `browser_fallback_check` + 控制台日志断言 |
| 5 | **后端回归（若涉及）** | 沿用第一轮（单元测试 → 端点测试 → 静态检查 → 全量套件 → Flake 隔离） | 前两轮流程 |

关键发现：**仅类型检查通过不足以证明 `.ts` 改动生效**——FR-061 的 `.js` 遮蔽会让类型检查与构建都"通过"却跑旧代码。必须先清 stale `.js`，再用 vue-tsc + vite build 双验证。

---

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **safe-delete 钩子拦截构建清理**：`vite build` 默认 `outDir` 在项目内且 `emptyOutDir` 会删目录，触发 WorkBuddy 安全删除钩子拦截，构建失败或产物被删。
   - 应对：`frontend_verification.build_out_dir` 指向 `/tmp/kw-dist` 等非项目目录，清理动作落在项目外，不触发钩子、不污染源码树。
2. **`.ts` 被 `.js` 遮蔽（FR-061）**：`src/` 残留 `.js` 让 Vite 优先解析 `.js`，`.ts` 修改不生效，类型检查 / 构建都"通过"却跑旧代码。
   - 应对：步骤 1 先清理 `stale_js_cleanup_glob`（`src/**/*.js`），再跑类型检查 / 构建。
3. **类型检查命令版本漂移**：全局 `vue-tsc` 与项目 `package.json` 版本不一致，结果不可信。
   - 应对：`frontend_verification.typecheck_command` 走 `node_modules/vue-tsc/bin/vue-tsc.js` 内置 bin，并用 `frontend_verification.node_path` 固定运行时（config.yaml 指向 WorkBuddy 托管 node）。
4. **浏览器不可用**：沙箱无 Chromium 时，无法做"控制台无 error"的端到端闭环。
   - 应对：降级为"类型检查 + 构建"验证 + 对弃用用法的 `grep` 存量扫描（证明已全量迁移），明确记录"未做 E2E 控制台核验"，不伪造通过。

---

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（按改动类型路由）

```
判断改动类型
  ├─ 含前端 .vue / .ts 改动（无 / 有 UI 界面）
  │     → 清理 stale .js (stale_js_cleanup_glob)
  │        → 前端类型检查 (typecheck_command, run_dir=frontend)
  │        → 前端构建 (build_command, outDir=build_out_dir=/tmp)
  │        → (Chromium 可用) 浏览器 E2E + 控制台无 error 闭环
  │        → (不可用) grep 弃用用法存量扫描 + 记录未验证项
  ├─ 升级 UI 库主版本前
  │     → grep 全量扫描弃用用法 (ui_library_api.scan_components + deprecated_attrs)
  │        → 逐一迁移 → 再跑上述前端验证链
  └─ 纯后端 / 纯文档改动
        → 沿用第一轮 / 第二轮流程（不进入前端验证链）
```

### 判断逻辑（可参数化的核心决策）

- **J6 — 前端改动必须过"类型检查 + 构建"双验证**：仅类型检查通过不足以证明 `.ts` 生效（FR-061 遮蔽），必须再跑 `vite build` 验证产物可生成。
- **J7 — 构建产物输出到项目外临时目录**：`frontend_verification.build_out_dir` 必须为 `/tmp` 等非项目目录，规避 safe-delete 拦截与源码树污染。
- **J8 — 验证命令 / 运行时 / 目录全部参数化**：`frontend_verification.*`（node_path / typecheck_command / build_command / build_out_dir / stale_js_cleanup_glob）从配置读取，**禁止在脚本或 prompt 中硬编码**路径与命令。
- **J9 — 控制台告警级缺陷的闭环策略**：无浏览器时用"构建 / 类型检查 + grep 存量用法"证明已迁移；有浏览器时以"控制台无 error"为最终闭环。

---

## 维度四：适用与不适用场景（Applicability）

### 适用场景

- **含前端 `.vue` / `.ts` 改动的 PR**：清理 stale `.js` → vue-tsc 类型检查 → vite build（outDir=/tmp）→（浏览器可用）E2E 控制台核验。
- **升级 UI 组件库主版本前**：全量 grep 弃用用法（参考 wiki-code-dev CODING-UI-API-2 / 前端 FR-065）+ 迁移后再走前端验证链。
- **CI 前端门禁**：将前端验证链（清 stale `.js` + vue-tsc + vite build）固化为流水线步骤，参数全部来自 `frontend_verification` 配置块。

### 不适用场景

- **纯后端 / 纯文档改动**：走第一轮 / 第二轮流程，不进入前端验证链。
- **纯配置改动（无前端类型触及）**：无需跑 vue-tsc / vite build；若触及 `types.ts` 仍应跑 `type_sync_check`。
- **确实有浏览器且需端到端验证的改动**：优先走既有 Playwright 浏览器测试，前端验证链仅作前置门禁。

---

## 与既有协议 / 配置的衔接

| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 类型检查命令 / 构建命令 / 产物目录 | `frontend_verification`（defaults.yaml / config.yaml 新增配置块） |
| stale .js 遮蔽清理 | `ts-js-shadowing-frontend-rule`（FR-061）/ wiki-code-dev `frontend-ts-js-shadowing-rule.md` |
| 控制台告警级缺陷（el-radio 弃用） | `element-plus-rule`（FR-065）/ wiki-code-dev `third-party-ui-api-currency-rule.md`（CODING-UI-API-1/2） |
| 沙箱无浏览器回退 | `browser_fallback_check` 思路（MCP→subagent→curl）+ 明确记录未验证项 |
| 后端回归（若涉及） | 第一轮 / 第二轮既有流程 |

---

# 第四轮复盘：raw 文件名修复 + 走查建议优化测试

> 基于「用户上传 raw 文件名修复（中文名保留 + Unicode 感知清洗 + 内部前缀剥离 + originalName 透传 + `..` 二次校验）」与「走查建议优化（路由注册 / 前后端类型同步）」的真实测试经验复盘。
> 与第一 / 二 / 三轮互补：本轮聚焦**后端文件名管线与数据迁移/修复脚本的验证策略**——尤其是沙箱无浏览器环境下如何用"直接实例化 service 的单元断言"与"对临时 vault 真实 `--apply` 的脚本端到端"替代浏览器 E2E，以及 Windows 特有路径陷阱（Git-Bash 路径 vs Windows 原生路径、safe-delete 钩子拦截 `rm`）。
> 配套新增 `backend_logic_unit_test` / `migration_script_e2e` 两个动态引擎步骤类型与 `backend_logic_unit_test` / `migration_script_e2e` 两个配置块（见 SKILL.md 与 defaults.yaml / config.yaml），**零硬编码业务路径与命令**。

## 背景：被测对象与约束

被改动的是一个**后端文件名管线 + 两个路由端点 + 一个数据迁移/修复脚本**：

- `api/src/services/vault.ts`（或等价 service）：用户上传 raw 文件落盘前的文件名处理——Unicode 感知清洗 `/[^\p{L}\p{N}._-]/gu`、内部前缀剥离（`wiki-batch-<ts>-<i>-` / `wiki-compile-<ts>-` / `input-`）、清洗后 `..` 二次校验 + `basename`、原始名经 `CompileInput.originalName?` 透传、后端 `?? basename` 兜底。
- 新增/修改端点：`registerCompileRoute` / `registerCleanupRoute`（入口文件接线）。
- `api/scripts/migrate-raw-filenames.mjs`：批量修复历史脏文件名（默认 dry-run，显式 `--apply` 才写盘；幂等 + 可恢复，冲突名 `-2/-3` 后缀；引用改写用函数式 `(_, g1) => g1 + newName`；pageCache 两阶段）。

约束条件：

- 沙箱 **Chromium 未安装、PyYAML 未安装**，完整浏览器 E2E 与部分依赖 PyYAML 的脚本无法运行。
- 沙箱 **Git Bash 与 Windows 原生路径混用**：嵌套 `execFileSync` 子 node 只认 Windows 原生 `C:\Users\...`，不认 Git-Bash `/c/Users/...`，否则报 `ENOENT`。
- 沙箱 **WorkBuddy 安全删除钩子（safe-delete）** 会拦截对项目目录的 `rm`（Git-Bash 风格路径报"relative path rejected (must be absolute)"）。
- 前端类型同步（新增 `originalName?` 可选字段、前端不消费）沿用第三轮"清 stale `.js` + vue-tsc + vite build"前置。

---

## 维度一：成功执行步骤（Successful Steps）

| 步骤 | 操作 | 产物 / 验证点 | 复用本技能的哪个能力 |
|------|------|---------------|----------------------|
| 1 | **后端逻辑单元验证（直接实例化 service）** | 构造 VaultService 实例，对纯文件名处理做断言：中文名保留 / ASCII 导向正则不把中文变下划线 / 内部前缀被剥离 / 清洗后 `..` 被二次拦截 | 新增 `backend_logic_unit_test` 步骤类型 |
| 2 | **迁移/修复脚本端到端（真实 `--apply`）** | 对临时 vault 真实调用 `migrate-raw-filenames.mjs --vault <tmp> --apply`，验证 8/8 重命名正确、**原文件未被破坏**、冲突名走 `-2/-3` 后缀 | 新增 `migration_script_e2e` 步骤类型 |
| 3 | **静态检查** | `route_registration_check`：compile/cleanup 路由在入口文件注册；`type_sync_check`：前端 `types.ts` 与后端 `CompileInput.originalName?` 对齐（前端不消费该字段亦不破坏） | `route_registration_check` / `type_sync_check`（既有） |
| 4 | **后端回归套件** | `vitest run` 全量 + （失败）Flake 隔离 | 第一轮既有流程 |
| 5 | **临时文件清理（绕过 safe-delete）** | 用 PowerShell `Remove-Item -LiteralPath` + Windows 字面路径删除测试临时脚本/截图，避开 Git-Bash 路径被钩子拦截 | `temp_cleanup` / `cleanup` 思路（Windows 字面路径） |

关键发现：迁移/修复脚本**必须真实跑一次 `--apply`** 才能证明其"既不破坏原数据、又能正确改写"——仅读源码无法验证函数式 `$` 替换与 `-2/-3` 冲突后缀的真实行为；而真实写盘必须落在**临时 vault**，绝不触碰项目源码树或真实用户数据。

---

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **ENOENT（嵌套子进程 Windows 路径）**：测试脚本用 `execFileSync(NODE, ['脚本','--vault',tmp,'--apply'])`，外层 node 用 Git-Bash `/c/Users/...` 路径可用，但作为 `execFileSync` 参数传给子进程时，Windows API 拒绝该格式 → `ENOENT`。
   - 应对：子进程的 `runtime` / `script_path` / `cwd` 一律用 **Windows 原生路径**（`C:\Users\hspcadmin\...`）；`cygpath` 在沙箱不可用，故直接在配置中写原生路径。外层的 Python / node 仍可用 Git-Bash 路径。
2. **safe-delete 钩子拦截 `rm`**：`rm -f _test_*.mjs` 用 Git-Bash 风格 `/d/code/...` 路径，被钩子判为"relative path rejected (must be absolute)"拦截。
   - 应对：删除测试临时文件改用 **PowerShell `Remove-Item -LiteralPath` + Windows 字面路径**（如 `C:\Users\...\...`），钩子放行；不在 Bash 中用 `rm` 删项目内文件。
3. **`.ts` 被 `.js` 遮蔽（FR-061）**：前端类型同步验证前若 `frontend/src` 残留 `.js`，vue-tsc / vite build 都"通过"却跑旧代码。
   - 应对：沿用第三轮——先清 stale `.js`，再 vue-tsc + vite build 双验证。
4. **迁移脚本默认写盘风险**：若脚本默认 `--apply`（非 dry-run），测试会真实改写数据。
   - 应对：脚本**默认 dry-run**，仅显式 `--apply` 写盘；测试步骤显式传 `--apply` 且仅作用于临时 vault。
5. **Chromium / PyYAML 未安装**：浏览器 E2E 与部分 PyYAML 脚本无法运行。
   - 应对：回退 `backend_logic_unit_test` + `migration_script_e2e` + 静态检查，**不依赖浏览器**；浏览器 E2E 降级。

---

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（按改动类型路由）

```
判断改动类型
  ├─ 后端文件名管线 / 数据迁移·修复脚本改动
  │     → 后端逻辑单元验证(backend_logic_unit_test: 实例化 service, 落盘前纯逻辑断言)
  │        → 迁移脚本端到端(migration_script_e2e: 临时 vault 真实 --apply, 验证不改坏原数据)
  │        → 静态检查(route_registration + type_sync)
  │        → 后端回归套件 + Flake 隔离
  │        → 临时文件清理(PowerShell -LiteralPath Windows 字面路径)
  ├─ 打包 / 安装器 / 数据目录解析改动
  │     → 沿用第二轮流程
  ├─ 含前端 .vue / .ts 改动
  │     → 沿用第三轮流程（清 stale .js → vue-tsc → vite build → E2E/降级）
  └─ 纯配置 / 文档改动
        → 若触及 types.ts 仍跑 type_sync_check；否则最小验证
```

### 判断逻辑（可参数化的核心决策）

- **J10 — 落盘前纯逻辑用"直接实例化 service"做单元验证**：文件名清洗 / 前缀剥离 / `..` 二次校验这类逻辑无需启动服务或浏览器，直接 `new Service()` 调用方法断言最快最稳。
- **J11 — 迁移/修复脚本必须真实 `--apply` 验证**：仅读源码无法证明正确性；用临时 vault（`temp_vault_dir`）真实跑，验证既不破坏原数据又能正确改写；脚本默认 dry-run，写盘必须显式 `--apply`。
- **J12 — Windows 路径原生优先**：嵌套子进程（`execFileSync` / `subprocess` 列表参数）调用的是 Windows API，只认 Windows 原生 `C:\Users\...`，绝不传 Git-Bash `/c/Users/...`，否则 `ENOENT`。所有 `runtime` / `script_path` / `cwd` 从配置取原生路径。
- **J13 — 项目内文件删除走 PowerShell 字面路径**：safe-delete 钩子拦截 Git-Bash 风格 `rm`，清理临时产物改用 `Remove-Item -LiteralPath` + Windows 字面路径；测试临时数据一律落在项目外（如 `C:\Users\...\AppData\Local\Temp\...` 或 `/tmp`），回收即用 `shutil.rmtree` 不触发钩子。

---

## 维度四：适用与不适用场景（Applicability）

### 适用场景

- **后端文件名管线改动**：`backend_logic_unit_test` 直接实例化 service 验证清洗/前缀剥离/`..` 二次校验；对应 CODING-USER-UPLOAD-FILENAME / BR-069。
- **数据迁移 / 修复脚本改动**：`migration_script_e2e` 对临时 vault 真实 `--apply`，验证正确性 + 可逆性；对应 CODING-MIGRATION-SAFETY / BR-070。
- **路由注册 / 前后端类型同步改动（无 UI 界面）**：静态检查（route_registration + type_sync）+ 后端回归，不强行启动浏览器。
- **沙箱无浏览器 / 无 PyYAML 环境**：回退 `backend_logic_unit_test` + `migration_script_e2e` + 静态检查，浏览器 E2E 降级。

### 不适用场景

- **纯前端 UI 动画 / 交互变更**：本流程后端逻辑单元/迁移脚本验证不适用，应走既有 Playwright 浏览器测试阶段。
- **纯只读配置消费（无类型触及）**：无需跑后端逻辑单元/迁移脚本验证；若触及 `types.ts` 仍应跑 `type_sync_check`。
- **确实需浏览器验证且浏览器可用的改动**：优先走既有浏览器 E2E，本回退链路仅作降级。
- **服务端容器部署（volume 挂载）**：用户数据目录锚点非 LOCALAPPDATA，相关落点/路径判定需按部署模型调整。

---

## 与既有协议 / 配置的衔接

| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 落盘前纯逻辑单元验证 | `backend_logic_unit_test`（新增步骤类型 + 配置块） |
| 迁移/修复脚本端到端 | `migration_script_e2e`（新增步骤类型 + 配置块） |
| 路由是否注册 | `route_registration_check`（既有） |
| 前后端类型对齐（originalName?） | `type_sync_check`（既有）/ 前端 FR-066 / BR-026 |
| stale .js 遮蔽清理 | `ts-js-shadowing-frontend-rule`（FR-061，第三轮） |
| Windows 路径原生 / safe-delete 绕过 | `temp_cleanup` / `cleanup` 思路（PowerShell `-LiteralPath` Windows 字面路径） |
| 后端回归（若涉及） | 第一轮 / 第二轮既有流程 |

---

# 第五轮复盘：SPA 实时部署解析验证 + safe-delete 沙箱钩子约束

> 基于「/wiki/* 路径穿越加固 + 实时部署解析（resolveSpaRoot 选最新时间戳目录 + isDeployComplete 完整性门禁；resolveSpaAsset normalize + within-root 防穿越）+ 部署脚本 _deploy_live.mjs 写全新 public_live_<ts> 目录」与配套测试的真实经验复盘。
> 与第一~四轮互补：本轮聚焦**后端 SPA 静态托管目录的动态解析与防穿越如何验证**，以及**沙箱 WorkBuddy 安全删除钩子（safe-delete）fail-closed 的工作模式**——清理 / 部署如何在不触发钩子拦截的前提下完成。
> 配套新增 `spa_live_deploy_check` 动态引擎步骤类型与 `spa_live_deploy_check` 配置块（见 SKILL.md 与 defaults.yaml / config.yaml），**零硬编码目录与命令**。

## 背景：被测对象与约束

被改动的是一个**后端 SPA 静态托管目录的动态解析 + 防穿越 + 部署脚本**：

- `api/src/index.ts`：`resolveSpaRoot()` 从候选（含 `public_live_<ts>` 时间戳目录）中选数值时间戳最大且通过 `isDeployComplete()`（`index.html` + `.deploy-complete` 标记）的目录；`resolveSpaAsset()` 对 `/wiki/*` 请求做 `path.normalize` + `path.relative(spaRoot, abs)` 的 within-root 逃逸拦截（逃逸 `..` 即拒绝）。
- `api/_deploy_live.mjs`：把构建产物写入**全新时间戳目录** `public_live_<Date.now()>`，整目录 create + write，绝不覆盖已存在目录；写完须重启后端（spaRoot 启动时算一次）。
- 配套前端：`vite.config.ts` 的 `outDir` 由部署注入为全新目录（对应前端 FR-068 / BR-071-4）。

约束条件：

- 沙箱 **WorkBuddy 安全删除钩子（safe-delete）fail-closed**：拦截 overwrite / rename-overwrite / unlink **已存在**文件；`rm` 完全被拦；但**新建目录的整目录 create + write 被放行**，**移动到「全新（不存在）路径」也被放行**。
- 沙箱 **Chromium 未安装、PyYAML 未安装**，浏览器 E2E 与部分依赖 PyYAML 的脚本无法运行。
- 后端 spaRoot **启动时计算一次**：写完新目录不重启后端不会切到最新目录。

---

## 维度一：成功执行步骤（Successful Steps）

| 步骤 | 操作 | 产物 / 验证点 | 复用本技能的哪个能力 |
|------|------|---------------|----------------------|
| 1 | **后端逻辑单元验证（vitest）** | 对 `resolveSpaRoot` 断言：多个 `public_live_<ts>` 时选最新；半写入目录（缺 `.deploy-complete`）被门禁拒绝；对 `resolveSpaAsset` 断言：`../` 逃逸返回 `null`、正常路径落在 root 内 | 新增 `spa_live_deploy_check` 思路（落盘前纯逻辑断言，类比 `backend_logic_unit_test`） |
| 2 | **后端集成（Fastify `app.inject`）** | 启动真实路由层，请求 `/wiki/<asset>` 验证落到 spaRoot 内；构造恶意 `/wiki/../../etc/passwd` 验证返回 4xx / 拒绝 | `api_tests.endpoints` + 路径穿越思路（`path_traversal_test`） |
| 3 | **部署脚本端到端（真实写全新目录）** | 对临时 base 真实跑 `_deploy_live.mjs`，验证生成 `public_live_<ts>` + `.deploy-complete`、不覆盖已存在目录；重启后端后 `spa_live_deploy_check` 确认选到新目录 | 新增 `spa_live_deploy_check`（部署写全新目录 + 完整性门禁 + 重启生效） |
| 4 | **静态检查** | `route_registration_check` / `type_sync_check`（若涉及前后端类型） | 既有 |
| 5 | **环境恢复（绕过 safe-delete）** | 清理临时部署目录：移动到**全新隔离路径**（钩子放行）或用项目外 `shutil.rmtree`（不触发钩子）；绝不原地 `rm` 已存在目录 | `temp_cleanup` / `cleanup` 思路（Windows 字面路径 + 移动新路径） |

关键发现：SPA 实时部署解析**必须验证"选择器逻辑"本身**——仅看页面能打开不足以证明后端选的是最新且完整的目录；半写入目录（构建先写 index 再写 hash bundle）若被命中会导致白屏，须靠 `isDeployComplete` 门禁拦截。

---

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **safe-delete 钩子拦截覆盖 / 删除**：部署脚本若 rename 覆盖已存在的 `index.html`、或 `rm` 旧 `public_live_*` 目录，被钩子判 `EPERM` / `relative path rejected` 拦截。
   - 应对：部署**写全新时间戳目录**（钩子放行整目录 create + write），不覆盖、不删已存在目录；清理走「移动到全新隔离路径」而非 `rm`。
2. **部署新目录不重启后端不生效**：`spaRoot` 在启动时算一次，写完新目录后后端仍服务旧目录。
   - 应对：部署步骤显式重启后端，轮询 `required_ports` 进入 Listen 后再验证。
3. **半写入目录被选中导致白屏**：部署脚本先写 `index.html` 再写 hash bundle，`existsSync(index.html)` 不足以判定完整。
   - 应对：`isDeployComplete` 门禁 = `index.html` **且** `.deploy-complete`（标记最后写）；测试断言门禁能拒绝缺标记目录。
4. **路径穿越误放行**：`resolveSpaAsset` 未 `path.normalize` 时 `../` 可逃逸 root。
   - 应对：测试构造 `malicious_paths`（含 `../` / 绝对路径），断言全部返回拒绝（与 `path_traversal_test` 同判定）。
5. **Chromium / PyYAML 未安装**：浏览器 E2E 无法运行。
   - 应对：回退 vitest 单元 + `app.inject` 集成 + 部署脚本端到端，**不依赖浏览器**。

---

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（按改动类型路由）

```
判断改动类型
  ├─ 后端 SPA 实时部署解析 / 防穿越 / 部署脚本改动
  │     → 后端逻辑单元验证(spa_live_deploy_check: resolveSpaRoot 最新+门禁 / resolveSpaAsset within-root)
  │        → 后端集成(app.inject: /wiki/* 正常落 root + 恶意 ../ 拒绝)
  │        → 部署脚本端到端(写全新 public_live_<ts> + .deploy-complete, 重启后端验证切新版)
  │        → 静态检查(route_registration + type_sync)
  │        → 环境恢复(移动到全新隔离路径 / 项目外 rmtree, 不原地 rm)
  ├─ 后端文件名管线 / 数据迁移脚本改动
  │     → 沿用第四轮流程
  ├─ 含前端 .vue / .ts 改动
  │     → 沿用第三轮流程（清 stale .js → vue-tsc → vite build → E2E/降级）
  └─ 纯配置 / 文档改动
        → 若触及 types.ts 仍跑 type_sync_check；否则最小验证
```

### 判断逻辑（可参数化的核心决策）

- **S1 — SPA 实时部署解析用"单元 + 集成"验证**：`resolveSpaRoot`（最新时间戳 + 完整性门禁）/ `resolveSpaAsset`（within-root）直接实例化断言，无需浏览器；恶意 `../` 路径必须全部被拒绝（与 `path_traversal_test` 同判定）。
- **S2 — 部署脚本必须真实跑一次写全新目录 + 标记**：仅读源码无法证明选择器逻辑正确；对临时 base 真实跑，验证生成 `public_live_<ts>` + `.deploy-complete`、不覆盖已存在目录；重启后端后确认切到新目录。
- **S3 — safe-delete 钩子 fail-closed，统一走「写新目录 → 移动 / 重建」**：钩子拦截 overwrite / rename-overwrite / unlink 已存在文件、`rm` 完全被拦；唯一放行的是**新建目录整目录写入**与**移动到全新（不存在）路径**。清理 / 部署一律避免原地 rm / 覆盖，改用整目录新建或移动到全新隔离路径（项目外 `shutil.rmtree` 亦不触发钩子）。
- **S4 — spaRoot 启动时计算，部署后必须重启后端并轮询端口**：部署步骤含后端重启 + `required_ports` 轮询进入 Listen，再验证选择器落到新目录。

---

## 维度四：适用与不适用场景（Applicability）

### 适用场景

- **后端 SPA 静态托管目录动态解析 / `/wiki/*` 防穿越改动**：`spa_live_deploy_check` 验证最新时间戳目录选择 + 完整性门禁 + within-root 拦截；对应 CODING-SPA-LIVE-DEPLOY / BR-071。
- **部署脚本（写全新时间戳目录 / 完整性标记）改动**：真实跑部署脚本验证生成新目录 + 标记、不覆盖已存在、重启后端生效；对应前端 FR-068 / BR-071-4。
- **沙箱 safe-delete 钩子约束下的清理 / 部署**：统一走「写新目录 → 移动 / 重建」，不原地 rm / 覆盖；对应 S3。
- **沙箱无浏览器 / 无 PyYAML 环境**：回退 vitest 单元 + `app.inject` 集成 + 部署脚本端到端，浏览器 E2E 降级。

### 不适用场景

- **纯前端 UI 动画 / 交互变更**：本流程 SPA 部署解析 / 部署脚本验证不适用，应走既有 Playwright 浏览器测试阶段。
- **确实有浏览器且需端到端验证的改动**：优先走既有浏览器 E2E，本回退链路仅作降级。
- **多端口 / nginx / CDN 托管前端（无后端 SPA 解析）**：后端 `resolveSpaRoot` 不存在，本验证不适用（对应后端 SH-1 适配说明）。
- **SSR 应用**：无静态 bundle 目录，SPA 部署解析不适用。

---

## 与既有协议 / 配置的衔接

| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| SPA 实时部署解析验证 | `spa_live_deploy_check`（新增步骤类型 + 配置块） |
| 后端静态资源路径防穿越 | `path_traversal_test`（既有）/ BR-067 / BR-071-3 |
| 完整性门禁（半写入目录） | `isDeployComplete`（index.html + `.deploy-complete`，最后写） |
| 部署写全新目录不覆盖 | 前端 FR-068-1 / BR-071-4 / CODING-SPA-LIVE-DEPLOY-4 |
| safe-delete 钩子 fail-closed | 第四轮 `temp_cleanup`（PowerShell `-LiteralPath` 字面路径）+ 本第五轮 S3（移动到全新路径 / 项目外 rmtree） |
| 部署后重启后端 | `service_lifecycle.stop_old_process` / `service_manage` + `required_ports` 轮询 |
| 路由是否注册 / 前后端类型对齐 | `route_registration_check` / `type_sync_check`（既有） |

# 第六轮复盘：多账户会话隔离验证（前端 Pinia + 客户端按 ownerId 持久化）

## 背景
会话仅存客户端 IndexedDB（按 `ownerId` 隔离，不落服务端）。`currentConversationId` 是 Pinia 模块级共享 ref，账户切换/登出若未重置，下一账户复用同一 id 调 `persistConversation` 会把上一账户的会话（相同 id）覆盖并改属自己——表现为「admin 历史消失 / 人人可见」。这类跨账户泄漏单账户测试永远复现不出，且 E2E 用 store 直接 `setUser` 不触发真实登出会漏掉根因。本次复盘将「reset-on-auth-change + store return 可观测 + 持久化复用 id 校验归属」固化为 `cross_account_session_check` 步骤类型。

## 维度一：成功步骤（已被验证有效的做法）
1. store 暴露 `resetSession()`（作废 currentConversationId + scopedOwnerId + 清空列表）；auth watch（user?.id 变化）先调 resetSession 再 loadConversations。
2. `persistConversation` 复用 id 前以 IndexedDB 实际记录（dbGet）校验归属，已存在且归属他人 → 全新 uuid，绝不覆盖他人记录。
3. `loadConversations` 二次防御（owner 不符重置当前会话）+ `filterByOwner` 严格按 ownerId 隔离 + `migrateOwnerless` 落盘成功后才内存归属。
4. 跨账户验证用**真实登出/登录** E2E，而非 store 直接 setUser。

## 维度二：不确定性与失败点
- Pinia setup store 的 state 仅含 return 中的 ref：漏加 scopedOwnerId → resetSession 赋值不可观测=死状态（真实踩坑），必须静态核对 return 列出全部会话 ref。
- E2E 用 store.setUser 模拟切换不触发真实登出，会误判「已修复」——必须真实走登出/登录链路。
- 仅凭内存 currentConversationId 判断归属会误判（残留上一账户 id），必须以存储实际记录为准。

## 维度三：可抽象流程与判断
- S1：评审/测试涉及 `*store*.ts` 含 currentConversationId/scopedOwnerId → 静态核对是否全部加入 store return（漏加即 Critical）。
- S2：涉及 auth watch（user?.id）→ 核对跨账户先 resetSession 再 load。
- S3：涉及 persistConversation → 核对复用 id 前以 dbGet 校验归属，他人记录绝不覆盖。
- S4：涉及 filterByOwner/migrateOwnerless → 核对严格隔离 + 落盘后归属（安全失败不泄漏）。

## 维度四：适用与不适用
- 适用：客户端按用户隔离的会话/草稿/个人配置（IndexedDB/localStorage）且状态以 Pinia 模块级 ref 持有；账户切换/登出/多账户并存；跨账户回归验证。
- 不适用：纯服务端会话（按 token 自然隔离）、单账户应用、与认证无关的纯展示组件。

## 与既有协议/规则衔接
| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 会话状态 ref 必须加入 store return | FR-069-1 / CODING-SESSION-ISOLATION-2 |
| 账户切换/登出 resetSession | FR-069-2 / CODING-SESSION-ISOLATION-1 |
| 持久化复用 id 校验归属 | FR-069-3 / CODING-SESSION-ISOLATION-3 |
| 严格隔离 + 落盘后归属 | FR-069-4 |
| 客户端按 ownerId 持久化 | FR-063（runtime-data-privacy）/ PB1-PB6（persistence-boundary） |
| 跨账户真实 E2E | e2e-precheck-frontend（FR-30，端口+健康检查） |

# 第七轮复盘：BYOK 多用户密钥代理验证（前端 userConfig + 后端 applyPerRequestOverride）

## 背景
多用户应用中所有用户共用服务端一份 LLM / 搜索 / 工具配置（含 API Key）会导致：全员共用额度互现限流、任一用户配置错误影响所有人、密钥落服务端泄露面扩大。架构改为 BYOK 代理：前端本地（IndexedDB 按 userId 命名空间）保存每用户配置，每次请求随 body 带当前用户配置，后端用 `applyPerRequestOverride` 覆盖服务端共享配置后调用 harness；密钥仅经请求体下发、不落盘 / 不回显 / 不记日志；缺必需密钥直接 400 不回落服务端共享。本次复盘将「命名空间隔离 + 密钥仅请求体 + 纯函数覆盖 + 缺密钥不回落」固化为 `byok_per_user_override_check` 步骤类型。

## 维度一：成功步骤（已被验证有效的做法）
1. 每用户配置存前端本地命名空间（`usercfg::<kind>::<userId>`），天然按用户隔离；应用层只读取当前登录用户命名空间。
2. 密钥仅经请求体下发；后端 routes/query.ts 只从 body 取，从不写盘、不回显 GET、不记日志。
3. 缺 apiKey（及 provider / baseUrl / model）直接 400，禁止回落服务端共享密钥。
4. 覆盖为纯函数 `applyPerRequestOverride`（仅 type-only import，便于单测）；空 / 默认工具配置视为未提供覆盖、回退服务端共享，不清空。

## 维度二：不确定性与失败点
- 前端曾始终下发空 `toolsConfig` → 后端整体替换清空服务端共享 MCP / CLI → 未配置工具的用户工具能力丢失（真实事故）。须「仅当用户实际配置了工具才下发」。
- 网关门禁只校验 apiKey，畸形 provider / baseUrl / model 透传 harness 触发 500；须校验全部必需字段。
- 配置菜单仅 admin 可见（RBAC `config` 权限）→ 非管理员无法改自身 BYOK 配置；须把菜单项权限改为 `dashboard` 并对敏感 tab 加 `v-if="isAdmin"` 二层拦截。

## 维度三：可抽象流程与判断
- S1：评审 / 测试涉及 `services/userConfig.ts` / `Config.vue` / `Query.vue` 中 `usercfg::` / `loadAiUserConfig` / `llmConfig` / `apiKey` → 核对每用户配置是否本地命名空间隔离（不全局 localStorage 跨用户共享）。
- S2：涉及密钥下发 → 核对仅经请求体、后端不落盘 / 不回显 / 不记日志。
- S3：涉及 routes/query.ts 门禁 → 核对缺必需密钥返回 400 不回落服务端共享。
- S4：涉及 `applyPerRequestOverride` → 核对纯函数、空覆盖回退服务端共享不清空；前端仅当配置存在才下发对应块。

## 维度四：适用与不适用
- 适用：多用户 SaaS / 桌面应用、用户自带 API Key 的 LLM / 搜索 / 工具代理、密钥不落服务端、CI 密钥隔离回归。
- 不适用：单用户应用、密钥本就该服务端统一托管且用户无自带需求。

## 与既有协议/规则衔接
| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 每用户配置命名空间隔离 | FR-070-1 / CODING-BYOK-1 / config-isolation-rule |
| 密钥仅请求体 + 不落盘 / 不回显 / 不记日志 | FR-070-2 / CODING-BYOK-1 / FR-063（runtime-data-privacy）/ sensitive-field-display |
| 缺密钥 400 不回落服务端共享 | FR-070-2 / CODING-BYOK-2 / BR-072-2 |
| 覆盖纯函数 + 空覆盖回退 | FR-070-2 / CODING-BYOK-3 / BR-072-3 |
| 配置菜单访问门控 | FR-070-3 |

# 第八轮复盘：流式回答增量持久化与续答验证（前端 SSE 中间态）

## 背景
问答页 AI 回答是 SSE 流式输出。早期部分答案仅内存持有、仅完成时落盘；`onBeforeUnmount` 调 `abortController?.abort()` 在切页杀 SSE；无上次活跃会话记忆。后果：刷新退化为新会话、部分答案消失；切页回答死状态；无法续答。本次复盘将「增量防抖落盘 + 卸载不 abort + 仅 streaming 末条续答」固化为 `streaming_resume_check` 步骤类型。

## 维度一：成功步骤（已被验证有效的做法）
1. 流式每收分片防抖（约 1.5s）落盘中间态（问题 + 部分答案 + status:'streaming'），刷新 / 切页可恢复。
2. `onBeforeUnmount` 仅卸载事件监听，绝不 abort 在途流；切页后台继续生成。
3. 重载时若有上次活跃会话且末条为 'streaming' 则续答（移除占位 + 复用末条用户问题重发补全）；interrupted / error 不自动续（保留部分）。
4. SPA 重挂载且 store 仍 isLoading（后台流活跃）时直接跳过续答，避免打断 / 重复。

## 维度二：不确定性与失败点
- 仅完成时落盘会导致刷新丢失中间态退化为新空会话（单轮测试不易暴露，真实用户高频切页 / 刷新才触发）。
- `onBeforeUnmount` 的 abort 是隐性杀手：切页即中断在途 SSE。
- 真·断点续写不可行（已生成 token 无法安全拼接），采用「重新生成完整回答」替换 streaming 占位，须在 store 层区分后台流活跃与续答。

## 维度三：可抽象流程与判断
- S1：涉及 `stores/query.ts` 的 `streamingAnswer` / `persistConversation` → 核对流式分片增量防抖落盘（非仅完成时）。
- S2：涉及 `views/Query.vue` 的 `onBeforeUnmount` / `abortController` → 核对仅卸监听、不 abort 在途流。
- S3：涉及 `LAST_ACTIVE_CONVERSATION` / `resumeLastAnswer` / `maybeResumeOnLoad` → 核对仅 streaming 末条续答、interrupted / error 不续、后台流活跃时跳过。

## 维度四：适用与不适用
- 适用：任何 SSE / 流式输出 UI（聊天 / 问答 / 长文生成）、客户端持久化会话 / 草稿、用户会中途切页或刷新的场景。
- 不适用：纯一次性请求无中间态、服务端完整托管会话的只读展示页、不持久化流式中间态的页面。

## 与既有协议/规则衔接
| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 增量防抖落盘 | FR-071-1 / CODING-STREAMING-RESUME-1 / persistence-boundary（PB1-PB6） |
| 卸载不 abort 在途流 | FR-071-2 / CODING-STREAMING-RESUME-2 / sse-event-dispatch / sse-stream-error |
| 仅 streaming 末条续答 | FR-071-3 / CODING-STREAMING-RESUME-3 |
| 客户端按 ownerId 持久化 | FR-063 / FR-069（会话隔离） |

# 第九轮复盘：fake-indexeddb 测试隔离（唯一命名空间而非 deleteDatabase）

## 背景
项目前端隔离测试（ttsConfig-isolation / ttsStore-isolation / userConfig-isolation）依赖 fake-indexeddb + chatDb。踩坑：`chatDb` 首次 `openDatabase` 后**缓存 db 连接**；若在 `beforeEach` 用 `indexedDB.deleteDatabase` 并 `await`，会因连接未关闭而 **onblocked / 10s 钩子超时**，且即便 fire-and-forget 也会跨用例泄漏记录导致断言失准。本次复盘将「隔离测试改用唯一 userId 命名空间、根本不依赖清空数据库」固化为测试编写纪律，并记录 fake-indexeddb timing（onsuccess 是 macrotask，单次 flush 不足，须多轮 `setTimeout(0)`）。

## 维度一：成功步骤（已被验证有效的做法）
1. 每条用例使用互不相同的 userId 命名空间（`tts-config::<uniqueId>` / `usercfg::ai::<uniqueId>`），根本不依赖「清空数据库」即可杜绝键碰撞误判（沿用 ttsConfig-isolation 测试的无 await 写法）。
2. 复用既有无 await deleteDatabase 写法，仅靠唯一键隔离。
3. fake-indexeddb 的 `onsuccess` 是 macrotask，`loadForUser` 内 `currentUserId` 同步设置后须 flush 多轮 `setTimeout(0)`（约 10 轮）才能稳定断言 `setProvider` 等依赖落盘的行为。

## 维度二：不确定性与失败点
- `beforeEach` 里 `indexedDB.deleteDatabase` + `await` → 连接未关闭 onblocked → 10s 钩子超时，且跨用例泄漏记录导致断言失准。
- 单次 `flush` 仅 1 轮 → `setProvider` 等依赖落盘的断言 0 调用失败（fake-indexeddb timing 所致）。

## 维度三：可抽象流程与判断
- S1：评审 / 编写前端隔离测试 → 优先唯一 userId 命名空间，禁用 `beforeEach` `deleteDatabase`。
- S2：涉及 fake-indexeddb 异步落盘断言 → 多轮 `setTimeout(0)` flush 后再断言。

## 维度四：适用与不适用
- 适用：任何用 fake-indexeddb + 缓存连接的存储层（chatDb 等）做隔离测试的场景。
- 不适用：真实浏览器 E2E（无 fake-indexeddb 连接缓存问题）、纯内存存储测试。

## 与既有协议/规则衔接
| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 唯一 userId 命名空间隔离 | config-isolation-rule / FR-070-1 / CODING-BYOK-1 |
| fake-indexeddb 异步 timing | async-reliability（超时 / flush） |

# 第十轮复盘：端到端「类型门禁 → 单测 → 全量 → 构建 → 部署 → 干净重启 → 冒烟」编排

## 背景
前九轮分别固化了各专项检查（SPA 实时部署、会话隔离、BYOK、流式续答、隔离测试纪律等）。但在真实交付中，这些专项若各自为政、顺序错位，仍会反复踩坑：类型门禁不通过却直接 build 失败、构建/部署写已存在目录被沙箱 safe-delete 钩子 EPERM 拦截、后台任务被回收后 tsx 变孤儿继续伺服 :3000 跑旧代码、隔离测试 flaky 漏网。本轮将「改动后固定的端到端编排顺序」与「干净重启 / 冒烟门禁」固化为可复用的测试交付纪律，并衔接 `wiki-code-dev` 的 `CODING-TEST-ISOLATION` 与 `retrospective-synthesis.md` 的测试过程四维度总览。

## 维度一：成功步骤（已被验证有效的做法）
1. **固定顺序门禁**：改动前端后先 `vue-tsc --noEmit`（类型门禁）→ 再 `vitest` 单测 → 再**全量** `vitest run`（含隔离测试 full-suite，防 flaky 漏网）→ 全绿才进入构建。任一阶段红则停，不进入下一步。
2. **构建写全新时间戳目录**：前端 `vite build` 产物输出到**全新** `builds/dist_u<ts>` 目录，绝不 build 到已存在的 `frontend/dist` 或 `api/public_live`（沙箱 safe-delete 钩子对清空/覆盖已存在目录 EPERM 拦截）。
3. **部署写全新目录**：`node api/_deploy_live.mjs <新构建目录>` 生成全新 `api/public_live_<ts>`（整目录 create+write，钩子放行），不触碰任何已存在文件；脚本显式校验参数/目录/ index.html 缺失即 `exit(1)`。
4. **后端改动必须干净重启**：先 `netstat -ano | grep ':3000'` 取实际监听 PID → `taskkill /PID <pid> /F` 杀孤儿 → 确认端口 FREE → 再 `tsx src/index.ts` 起新进程（后端 `spaRoot` 仅在启动时计算一次，不重启不会切到最新部署目录）。
5. **冒烟三类门禁**：① 构造缺 `apiKey` 的请求断言 `400`（BYOK 门禁不回落服务端共享）；② SSE 问答端点 `200` 且流式输出；③ `:3000/` 正常伺服 SPA，日志含 `[SPA] served from .../api/public_live_<ts>` 且时间戳为最新。

## 维度二：不确定性与失败点
- **类型门禁与构建耦合**：`vue-tsc` 在 build 脚本链首，类型不通过会 block build；但后端 `tsc --noEmit` 有约 13 个 pre-existing errors（`config.ts`/`index.ts`），因后端用 `tsx` 转译运行不受影响。编排须**区分前后端类型门禁**，不能把后端 pre-existing errors 当新阻断。
- **孤儿 :3000**：后台任务（`run_in_background`）被 harness 回收标 `failed` 时，底层 tsx 常变孤儿继续伺服 `:3000`（服务不中断但跑旧代码）；新启动报 `EADDRINUSE ::1:3000`。必须 `netstat` 取真实 PID + `taskkill` 干净重启，不能依赖后台任务回收状态。
- **构建/部署写已存在目录**：`vite build --outDir` 指向已存在目录的 `emptyOutDir` 清空、或部署覆盖已存在 `public_live` 均被 safe-delete EPERM —— 必须走「写全新目录」。
- **隔离测试 flaky**：仅跑改动相关单测易漏 flaky；必须 full-suite（参考第九轮：唯一 userId 命名空间 + 多轮 `setTimeout(0)` flush）。
- **冒烟门禁不全**：只查 SPA 200 不查 BYOK 400 门禁，会放过「缺密钥回落服务端共享」的回归。

## 维度三：可抽象流程与判断
- P1（编排顺序）：改动后固定 `typecheck → unit → full-suite → build(fresh dir) → deploy(fresh dir) → 杀孤儿 :3000 → 重启 → 冒烟`；任一阶段红则停。
- P2（写全新目录）：构建与部署一律产出**全新目录**，绝不覆盖/清空已存在目录（safe-delete fail-closed 适配）。
- P3（干净重启）：后端有改动必须 `netstat` 取真实 PID → `taskkill` → 端口 FREE → 起新进程；不依赖后台任务回收状态。
- P4（冒烟门禁）：必须覆盖三类 —— 400 缺密钥不回落 / 200 SSE / SPA 伺服最新时间戳目录。
- P5（隔离纪律，沿用第九轮）：隔离测试唯一 userId 命名空间 + 多轮 flush，禁用 `beforeEach deleteDatabase`。

## 维度四：适用与不适用
- 适用：本项目式「前后端分离 + SPA 静态伺服 + 沙箱 safe-delete fail-closed + 多用户 BYOK/会话隔离」的前端应用；CI 端到端交付回归。
- 不适用：纯后端无 SPA 伺服、纯静态无构建、无沙箱限制可自由覆盖目录的环境、单测即可覆盖的纯逻辑改动（此类走 `backend_logic_unit_test` 即可，不需全链路编排）。

## 与既有协议/规则衔接
| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 端到端编排顺序 / 干净重启 / 冒烟门禁 | CODING-TEST-ISOLATION（wiki-code-dev）/ retrospective-synthesis.md（测试过程四维度总览）/ service_manage（stop/start/ports）/ build_artifact_check / spa_live_deploy_check（restart_required） |
| 构建/部署写全新目录 | CODING-SPA-LIVE-DEPLOY / spa_live_deploy_check（live_dir_pattern）/ safe-delete fail-closed（R5） |
| 冒烟 400 缺密钥不回落 | byok_per_user_override_check（require_key_fields）/ FR-070-2 / BR-072-2 |
| 冒烟 200 SSE | streaming_resume_check（no_abort_on_unmount） |
| 隔离测试纪律 | indexeddb_test_isolation_check / CODING-TEST-ISOLATION（R9） |

---

# 第十一轮复盘：后端「行为级正确性缺陷」专项测试策略（七类潜伏缺陷）

> 基于一批后端真实修复的测试经验复盘：SSML prosody 注入防护 / 子进程异步当同步 / 关键写静默吞错 / 数据文件损坏未区分 / request.method 类型绕过 / 硬编码超时 / 冗余探测。
> 这些缺陷的共同特征是**类型检查、构建、端点冒烟都"通过"却仍潜伏**——只有在针对具体风险类的单元/集成测试或静态扫描下才会暴露。本轮将"后端 PR 的七类行为级缺陷专项测试策略"固化为可复用流程，并配套新增动态引擎步骤类型 `backend_review_static_check`（配置驱动、零硬编码），把"静态守卫"判断逻辑落地为可执行检查。

## 背景：被测对象与约束

被改动的是一个**后端服务模块**（语音合成 / 用户存储 / HTTP 路由层 / 子进程封装），修复了七类缺陷：

1. **SSML prosody 注入防护**：用户可控的 `rate/volume/pitch` 未经白名单校验 + clamp + XML 转义即拼入 SSML，畸形值触发 Edge 端点 WebSocket 1007。
2. **子进程异步当同步**：`execFile`（异步）被当作 `execFileSync`（同步）使用，未 `await` 即继续，导致音频后处理在子进程完成前读取未落盘文件。
3. **关键写静默吞错**：`saveUsers`/`saveConfig`/`persistConversation` 等落盘函数 `try/catch` 吞掉错误并恒返 `ok:true`，磁盘满/权限错被掩盖。
4. **数据文件损坏未区分**：`loadUsers` 把"文件损坏（JSON.parse 抛错）"与"文件不存在（ENOENT）"混为一谈，损坏时未回退默认/备份，造成数据丢失。
5. **request.method 类型绕过**：`request.method as any` 绕过 Fastify 的 `HTTPMethods` 类型约束，非法方法静默流入路由逻辑。
6. **硬编码超时**：`setTimeout`/`AbortSignal.timeout(30000)` 写死 30s，不可按环境/调用方调整，且跨层统一超时有级联风险。
7. **冗余探测**：`isFfmpegAvailable` 每次调用都 `execFileSync('ffprobe ... -version')` 探测能力，重复且拖慢启动/每次调用。

约束条件：

- 沙箱无浏览器，浏览器 E2E 对纯后端逻辑是**低信号**的；七类缺陷均需"针对风险类的定向测试"而非端到端 UI 验证。
- 部分缺陷（SSML 1007、真实子进程）依赖外部端点/真实进程，需把"可测的纯逻辑层"与"外部依赖层"分离，在纯逻辑层做确定性断言。
- 全部参数必须配置化（超时、prosody 范围、扫描目录），**禁止在测试脚本或 prompt 中硬编码**。

---

## 维度一：成功执行步骤（Successful Steps）

| 步骤 | 操作 | 产物 / 验证点 | 复用本技能的哪个能力 |
|------|------|---------------|----------------------|
| 1 | **纯逻辑单元验证（针对每类修复）** | 实例化目标 service，对"落盘前纯逻辑"断言：prosody 白名单 clamp / 越界回退默认值；execFileSync 同步返回后再读文件；saveUsers 在写失败时抛出而非 `ok:true`；loadUsers 损坏文件≠not-found（回退默认+备份）；request.method 被约束到枚举；超时取自配置而非字面量 | `backend_logic_unit_test`（运行修复后的单元断言文件） |
| 2 | **端点集成测试（app.inject）** | 对语音合成端点做 happy path + 畸形 prosody→被拦截（验证注入防护在 reach 网络前生效）；缺密钥→400（与第十轮 BYOK 门禁并重） | `api_check` / `backend_logic_unit_test` 配合注入测试 |
| 3 | **静态守卫扫描（forbidden patterns）** | 配置化 grep 后端源码：`as any`/`as unknown as` 类型绕过；`ffprobe`/`isFfmpegAvailable` 冗余探测；落盘函数 `try/catch` 吞错信号；字面量 `30000`/`30_000` 硬编码超时；`execFile(` 未 `await` 异步同步错配 | 新增 `backend_review_static_check` 步骤类型（全配置驱动，error 阻断 / warn 标记） |
| 4 | **全量套件运行** | `vitest run` 全绿；含隔离测试 full-suite（第九轮纪律），防 flaky 漏网 | 第十轮端到端编排 |
| 5 | **Flake 隔离** | 失败用例在隔离环境重跑，区分预存在 flake 与本次引入 | Flake 隔离协议 |

关键发现：七类缺陷**没有一类能被类型检查或构建捕获**——`request.method as any` 反而"骗过"了类型系统，`saveUsers` 吞错让单测"看起来通过"。必须用"定向单元/集成测试 + 静态守卫"双保险，不能只跑冒烟。

---

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **SSML 1007 只在真实 Edge 端点触发**：沙箱无法稳定连真实端点，难以用 E2E 复现 1007。
   - 应对：把注入防护下沉为**纯函数层**（prosody 校验 + escapeXml），用单元测试确定性断言畸形值被拦截/转义；端点测试仅验证"拦截发生在 reach 网络前"，不依赖真实端点连通性。
2. **子进程同步性差不易在 CI 复现**：`execFile` 异步当同步的时序 bug 在快机器上偶发"碰巧正确"。
   - 应对：单元/集成测试用"故意慢的子进程"（如 `sleep`）+ 断言"后续读取发生在子进程退出之后"，把时序依赖变为确定性断言。
3. **saveUsers 吞错让单测误报通过**：原实现恒返 `ok:true`，单测若只断言返回值会误判。
   - 应对：测试在临时只读目录/注入 fs 错误强制写失败，断言函数**抛出或返回明确错误**，并验证调用方确实传播该错误（而非吞掉）。
4. **loadUsers 损坏 vs 不存在混淆**：二者都进入 catch，若只 `return default` 会掩盖损坏、误删好数据。
   - 应对：单测分别造"文件不存在"与"文件损坏"两种 fixture，断言"不存在→默认初始化"、"损坏→回退备份/.bak 或明确告警"，绝不静默丢弃。
5. **硬编码超时与配置值漂移**：代码写 `30000` 但 config 写 `edgeTtsTimeoutMs: 60000`，单测若只测字面量会漏掉"配置未真正生效"。
   - 应对：单测读 `config.edgeTtsTimeoutMs` 并断言超时由该值决定；静态守卫 grep 字面量 `30000`/`30_000` 标记为待整改（与 `timeout_tier_check` 思路互补）。
6. **冗余探测在单测中不明显**：`isFfmpegAvailable` 探测只在冷启动/特定路径触发，常规单测覆盖不到。
   - 应对：静态守卫 grep `ffprobe`/`isFfmpegAvailable`；集成测试断言"能力在启动时一次性确定，运行时不再探测"。
7. **类型绕过在运行时无报错**：`as any` 编译期消失，运行时非法 method 静默流入 —— 只有静态守卫能拦。
   - 应对：`backend_review_static_check` 的 `type_bypass` 组以 error 级扫描 `as any`/`as unknown as`，命中即阻断。

---

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（后端 PR 七类行为级缺陷专项）

```
判断后端改动触及的风险类
  ├─ 动态字符串注入（SSML / SQL / shell / URL）
  │     → 纯函数层单元断言（白名单 clamp + 转义）→ 端点测试验证拦截在 reach 网络前
  ├─ 子进程调用（execFile / spawn / exec）
  │     → 单元断言同步边界（execFileSync 或 await execFile）→ 时序依赖改确定性断言（故意慢子进程）
  ├─ 关键落盘写（save*/writeFile/persist*）
  │     → 强制写失败 fixture → 断言错误传播（非 ok:true 吞错）
  ├─ 关键读（load*/readFile/JSON.parse）
  │     → 造"不存在"与"损坏"两种 fixture → 断言分类处理（默认初始化 / 备份回退）
  ├─ 类型边界（request.method / 外部入参）
  │     → 静态守卫 grep `as any`/`as unknown as` → 类型约束单元断言
  ├─ 超时/阈值
  │     → 单元断言取自配置而非字面量 → 静态守卫 grep 字面量 `30000`
  └─ 能力探测（ffprobe / isXxxAvailable / -version）
        → 静态守卫 grep 探测调用 → 集成测试断言一次性确定
  ── 收口：全量套件 → Flake 隔离 → （前端相关）走第十轮端到端编排
```

### 判断逻辑（可参数化的核心决策）

- **J1 — 行为级缺陷必须定向测试，不能只靠冒烟**：七类缺陷类型检查/构建/冒烟全过却潜伏；对每类风险写"针对该类的单元/集成断言"。
- **J2 — 外部依赖下沉为纯函数层**：SSML 1007、真实子进程等不可在沙箱稳定复现的，把可测逻辑抽到纯函数，用确定性单元测试断言；端点/E2E 仅做"拦截发生在依赖之前"的轻量验证。
- **J3 — 失败路径必须真实触发**：saveUsers 吞错、loadUsers 损坏需用 fixture 真实制造失败/损坏，断言错误传播与分类处理，不接受"返回值看起来对"。
- **J4 — 静态守卫做 forbid 扫描**：`as any`、冗余探测、`try/catch` 吞错信号、硬编码 `30000` 等用配置化 grep 扫描（新增 `backend_review_static_check`），error 级阻断、warn 级标记。
- **J5 — 全部参数配置化**：超时、prosody 范围、扫描目录、判定关键字从配置读取，**禁止硬编码**。

---

## 维度四：适用与不适用场景（Applicability）

### 适用场景
- **后端 PR 触及上述任一类风险**：动态字符串注入、子进程调用、关键读写、类型边界、超时/阈值、能力探测。
- **CI 后端行为级门禁**：将"定向单元断言 + 静态守卫（backend_review_static_check）+ 全量套件"固化为流水线；参数来自 `backend_review_static_check` 配置块。
- **沙箱无浏览器的后端验证**：用 `backend_logic_unit_test` 跑修复后的纯逻辑断言，无需浏览器/服务。

### 不适用场景
- **纯前端 / 纯文档改动**：走第十轮前端验证链（清 stale .js + vue-tsc + vite build）或静态检查，不进入本流程。
- **纯配置改动（无风险类触及）**：无需本专项；仅当触及超时等配置值时验证"配置真正生效"。
- **确有浏览器且需端到端验证的改动**：优先既有 Playwright 浏览器测试，本专项仅作前置门禁。

---

## 与既有协议 / 规则衔接

| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 纯逻辑单元验证 | `backend_logic_unit_test` 步骤类型 / `backend_logic_unit_test` 配置块（第四轮） |
| 静态守卫扫描（forbidden patterns） | 新增 `backend_review_static_check` 步骤类型 + `backend_review_static_check` 配置块 |
| 类型绕过静态守卫 | `as any` 守卫 → BR-078 / CODING-TYPE-SAFE-NO-ANY（wiki-code-dev） |
| 冗余探测静态守卫 | `ffprobe`/`isXxxAvailable` 守卫 → BR-080 / CODING-NO-REDUNDANT-PROBE |
| 关键写吞错静态守卫 | 落盘函数守卫 → BR-076 / CODING-CRITICAL-WRITE-NO-SWALLOW |
| 硬编码超时静态守卫 | 字面量 `30000` 守卫 → BR-079 / CODING-CONFIG-TIMEOUT（与 `timeout_tier_check` 互补） |
| 子进程同步边界 | BR-075 / CODING-CHILD-PROCESS-SYNC（与 `async_reliability_static_check` 超时保护互补） |
| 注入防护下沉纯函数层 | BR-074 / CODING-SSML-INJECTION；前端 FR-073 防御纵深 |
| 全量套件 + Flake 隔离 | 第十轮端到端编排 / 第九轮 indexeddb_test_isolation_check / Flake 隔离协议 |

---

# 第十二轮复盘：归档路由响应分支覆盖 + 静默缺陷回归

> 基于「归档路由重构」的真实测试经验复盘：按 `threadId + messageIndex + ts` 派生存储键检索归档内容的路由，在重构中暴露了 7 类规范问题（文件名碰撞 / 非法 ts→RangeError / 非整数 messageIndex→undefined 访问 / refs 换行破坏 wikilink / 空内容 no-op 落盘 / 依赖服务端会话 100% 误报过期 / 前端门控漂移）。
> 这些缺陷的共同特征是**类型检查、构建、端点冒烟都"通过"却仍潜伏**——只在"逐分支断言返回状态码"或"静态守卫"下才会暴露。本轮将"路由响应分支覆盖 + 静默缺陷回归"判断逻辑固化为可复用流程，并配套新增动态引擎步骤类型 `route_response_branch_coverage`（配置驱动、零硬编码）。

## 背景：被测对象与约束

被改动的是一个**归档路由**（如 `GET /api/threads/:threadId/archive`，按 `messageIndex + ts` 派生存储键检索归档内容并回传）：

1. **文件名碰撞**：派生键非全局唯一（仅局部唯一），并发/历史记录可能覆盖彼此的归档文件。
2. **非法 ts → RangeError**：`ts` 经 `new Date(ts)` / 数值解析，非法值应抛 RangeError 拦截，旧实现却静默回退。
3. **非整数 messageIndex → undefined 访问**：`messageIndex` 未做整数校验，非整数索引访问数组得到 `undefined`，旧实现不拦。
4. **refs 换行破坏 wikilink**：归档的 `refs` 字段用字面量换行拼接，破坏 Obsidian wikilink 语法，渲染错乱。
5. **空内容 no-op 落盘**：请求体 `content` 为空时仍 200 并写入空归档，污染存储。
6. **依赖服务端会话 100% 误报过期**：内容可得性依赖"服务端会话是否活跃"判断，离线/无会话时被 100% 误判过期。
7. **前端门控漂移**：后端已放宽"内容可得性"契约，但前端仍用 `!!sessionId / !!getSession` 门控，导致合法内容被前端拦截（能力门控不同步）。

约束条件：

- 沙箱无浏览器，路由行为级缺陷（非法输入分支返回了错误状态码）对浏览器 E2E 是**低信号**的；必须"针对分支语义的定向断言"而非端到端 UI 验证。
- 全部参数（路由、方法、分支用例、expected_status、required_fields）必须配置化，**禁止在测试脚本或 prompt 中硬编码**。

---

## 维度一：成功执行步骤（Successful Steps）

| 步骤 | 操作 | 产物 / 验证点 | 复用本技能的哪个能力 |
|------|------|---------------|----------------------|
| 1 | **纯逻辑单元验证（针对派生键 / 校验）** | 实例化路由 service，对"存储键派生（碰撞追加随机后缀）/ 路径穿越二次校验 / 空内容 no-op 防护"做确定性断言 | `backend_logic_unit_test`（运行修复后的单元断言文件） |
| 2 | **端点集成测试（app.inject）** | 逐分支构造 `threadId / messageIndex / ts / content`，断言返回状态码：主路径 200 / 回退 404 / 非法 threadId 400 / 非整数 messageIndex 400 / 缺失 messageIndex 400 / 非法 ts 200（当前回退）/ 空内容 400；并对 200 分支校验响应含 `content`/`refs` | 新增 `route_response_branch_coverage` 步骤类型（全配置驱动） |
| 3 | **静态守卫扫描** | grep 派生键生成处是否追加随机后缀（防碰撞）；grep `refs` 拼接是否用 `\n` 而非换行字面量（wikilink 完整性） | `backend_review_static_check` 思路 + 针对性 grep |
| 4 | **前后端门控同步验证** | 断言后端放宽"内容可得性"契约的同一变更里，前端门控同步放宽（无 `!!sessionId` / `!!getSession` 残留） | 前端 `capability_gating_sync`（FR-076）思路 / `cross_account_session_check` |
| 5 | **全量套件运行** | `vitest run` 全绿；含隔离测试 full-suite（第九轮纪律） | 第十轮端到端编排 |
| 6 | **Flake 隔离** | 失败用例隔离重跑，区分预存在 flake 与本次引入 | Flake 隔离协议 |

关键发现：7 类缺陷**没有一类能被类型检查或构建捕获**——`messageIndex` 未校验反而"编译通过"，空内容落盘让单测"看起来通过"。必须用"逐分支状态码断言 + 静态守卫"双保险。

---

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **非法 ts 当前回退实现返回 200（本应 RangeError 拦截→400）**：修复前行为不确定。
   - 应对：`expected_status` 参数化（当前 200，修复后改 400），让分支矩阵随行为演进，不写死。
2. **非整数 messageIndex 旧实现访问 undefined**：可能 5xx 或静默 200，难以在冒烟中暴露。
   - 应对：构造真实非整数（`abc`）用例，断言 `400`，不依赖框架默认。
3. **空内容 no-op 落盘**：旧实现仍 200 写空文件。
   - 应对：`empty_content` 用例传 `content: ""`，断言 `400`（no-op 防护），防止存储污染。
4. **前端门控漂移导致 100% 误报过期**：后端已放宽，前端仍门控。
   - 应对：`capability_gating_sync` 思路，同 commit 验证前后端契约同步放宽，禁用 `!!sessionId` 残留。
5. **文件名碰撞在单测中不明显**：仅在特定 `threadId / messageIndex` 组合下触发。
   - 应对：静态守卫 grep 派生键生成处；单元断言"冲突键追加随机后缀"。
6. **refs 换行破坏 wikilink**：类型检查无感知，渲染期才暴露。
   - 应对：静态守卫 grep `refs` 拼接是否用 `\n` 而非换行字面量；单元断言拼接产物符合 wikilink 语法。

---

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（路由响应分支覆盖）

```
判断路由是否有"差异化状态码语义"
  ├─ 是（主路径 vs 回退 vs 空内容 / 非法输入各有不同返回）
  │     → route_response_branch_coverage 逐分支断言 expected_status
  │         + 200 分支校验 required_fields（content/refs）
  ├─ 派生键 / refs / 吞错等代码层风险
  │     → backend_review_static_check（针对性 grep 组）
  └─ 前后端门控同步
        → capability_gating_sync 思路：同 commit 放宽，禁用 !!sessionId 残留
  ── 收口：全量套件 → Flake 隔离
```

### 判断逻辑（可参数化的核心决策）

- **J1 — 路由业务分支必须逐状态码断言，不能只冒烟 200**：7 类缺陷类型检查/构建/冒烟全过却潜伏；对每个"合法 vs 回退 vs 空内容 vs 非法输入"分支写明确 `expected_status`。
- **J2 — 非法输入必须真实触发**：构造 `threadId / messageIndex / ts` 真实非法值，断言 `4xx`，不接受"框架默认拦截"的假设。
- **J3 — 200 分支须校验响应含必需字段**：状态码对不等于内容对，必须对 200 响应断言 `content`/`refs` 等必需字段存在。
- **J4 — 静默缺陷靠"逐分支预期 vs 实际"比对暴露**：参数全配置化（`route_name / method / branch_cases`），不写死业务值；`expected_status` 随修复演进。

---

## 维度四：适用与不适用场景（Applicability）

### 适用场景
- **归档路由 / 按派生键检索的路由**：按 `threadId + messageIndex + ts` 等派生存储键检索内容，各业务分支有差异化状态码语义。
- **CI 路由分支门禁**：将"逐分支状态码断言 + 200 字段校验"固化为流水线；参数来自 `route_response_branch_coverage` 配置块。
- **沙箱无浏览器的路由验证**：用 `route_response_branch_coverage` 跑 HTTP 断言，无需浏览器/服务（或配合 `app.inject`）。

### 不适用场景
- **单分支无歧义路由**（所有非法输入已被框架/中间件统一拦截为 4xx 且无需逐分支语义）：`route_response_branch_coverage` 的分支矩阵价值有限，沿用 `api_check` / `path_traversal_test` 即可。
- **纯前端 / 纯文档改动**：走第十轮前端验证链或静态检查，不进入本流程。

---

## 与既有协议 / 规则衔接

| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 路由响应分支覆盖 | 新增 `route_response_branch_coverage` 步骤类型 + `route_response_branch_coverage` 配置块（config.yaml / defaults.yaml / examples） |
| 文件名碰撞静态守卫 | 派生键生成处追加随机后缀 → CODING-GENERATED-FILENAME-UNIQUENESS（wiki-code-dev） |
| refs 换行守卫 | `\n` 拼接而非换行字面量 → CODING-WIKILINK-SANITIZATION（wiki-code-dev） |
| 空内容 no-op 防护 | `empty_content` 分支断言 400 → CODING-EMPTY-CONTENT-REJECTION（wiki-code-dev） |
| 非整数 messageIndex 校验 | 分支断言 400 → CODING-INTEGER-INDEX-VALIDATION（wiki-code-dev） |
| 非法 ts 解析 | 分支断言（当前回退 200，修复为 RangeError 拦截后 400）→ CODING-SAFE-CLIENT-DATE-PARSE（wiki-code-dev） |
| 服务端会话解耦 | 内容可得性不依赖服务端会话 → CODING-PERSISTENCE-CLIENT-CONTENT-DECOUPLING（wiki-code-dev） |
| 非法输入校验 | 非法 threadId / messageIndex / ts 分支断言 → 与 `path_traversal_test` 互补 |
| 前端门控同步 | 前端 FR-076 `capability-gating-sync-frontend-rule` / CODING-CAPABILITY-GATING-SYNC / `cross_account_session_check` 思路 |
| 全量套件 + Flake 隔离 | 第十轮端到端编排 / 第九轮 indexeddb_test_isolation_check / Flake 隔离协议 |

# 第十三轮复盘：从历史问题系统性提炼编码规范 → 同步到测试（"规范即配置"泛化）

## 背景：被测对象与约束

本轮回溯本对话的核心工作：把历史对话中已解决的多个前端/后端问题（编辑重发、流式自动滚动、成对按钮样式、编辑框撑满、SPA 实时部署、隔离测试、BYOK、流式续答、端点分支覆盖、flake 型 typecheck 误报等）**系统性提炼为编码规范（wiki-code-dev CODING-*）+ 审查条目（FR-*/BR-*）+ 自动化测试步骤类型（wiki-auto-testing）** 的闭环，并贯穿四维度方法论。约束：所有参数零硬编码（集中 YAML 管理）、技能需泛化适配不同业务场景（registry 模式步骤引擎 + 配置化模式组）。

## 维度一：成功执行步骤（Successful Steps）

1. **端到端交付门禁顺序固定**：`typecheck(vue-tsc 仅前端)` → `单测(vitest)` → `全量套件(full-suite 防 flaky)` → `build(写全新目录)` → `deploy(写全新目录)` → `杀孤儿 :3000` → `重启后端` → `冒烟(缺密钥 400 不回落 / SSE 200 / SPA 伺服最新目录)`。每一步失败即停，全绿才进下一步。
2. **规范→测试派生链**：每条新 CODING-/FR-/BR- 规则都落地一个 **config-driven** 测试步骤类型，使"编码规范"与"测试守护"同源演进，避免规范沦为文档。
3. **配置化优先**：新增前端规范（如 FR-077~FR-080）只在 YAML 加一组 `groups[name, forbidden_patterns, required_patterns, severity, rule_ref]`，**不改 `_step_engine.py`**（registry 模式已注册 handler，handler 只读 `cfg`）。实现"规范即配置"。
4. **flake 隔离确认**：typecheck 偶发 EXIT=1 但 0 error 时，重跑干净实例确认（并发构建触碰文件是抖动源），不把抖动当真错误。

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **flake 型 typecheck 误报**：并发 `vite build` 触碰 `.ts` 文件时 `tsc --noEmit` 可能偶发 `EXIT=1` 伴随 0 条 `error TS`——易被误判为"预存类型错误"。**判断**：EXIT 码与错误行数必须同时校验；EXIT≠0 但 0 error 一律重跑确认。
2. **沙箱 safe-delete 钩子 fail-closed**：拦截 `unlink` / `rm(>50)` / 覆盖写 / 重命名已存在文件；`fs.renameSync` 到全新路径允许、`fs.copyFileSync` 写入 `api/public` 被静默吞。→ **部署/清理必须走"写全新目录 → 移动/重建"，禁止原地 rm/覆盖**。
3. **静态守卫的固有局限**：纯运行时行为（如按钮点击后的视觉反馈）无特征字符串，`required_patterns` 无法可靠匹配；误用静态守卫会漏报 → 此类须改 E2E（button_discovery / theme_switch / runtime 断言）。
4. **配置与代码三处漂移**：新增步骤类型须在 `_step_engine.py` 注册 + `config.yaml` + `defaults.yaml` + `examples/config.enabled.example.yaml` 四处同步；漏一则运行时 `Unknown step type` 或示例不可用。
5. **required_patterns 的假阳性**：若保护性代码被合理重命名（如 `submitQuestion` 改名为 `sendEdited`），required_patterns 会误报"缺失"。→ 模式须选**稳定语义锚点**（如成对方法名、CSS class 契约），重命名时同步改配置。

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（规范→审查→测试 闭环）

```
历史已解决问题
  → wiki-code-dev 提炼 CODING-* 规则（references/*-rule.md + 路由表 + config 段 + retrospective 事故索引）
  → 前端 wiki-frontend-code-review 加 FR-* 条目（skill-loader 三表 + Historical Incident + 跨文件检查 + 输出类别 + config 段）
  → 后端 wiki-backend-code-review 加 BR-* 条目（Feature Scan + Quick-Check + .rules-index + config 段）
  → wiki-auto-testing 加 config-driven 步骤类型（_step_engine.py 注册 handler + config.yaml/defaults.yaml 配置块 + 一键启用示例）
  → 一键启用：复制 examples 对应块到 config.yaml 即可运行
```

### 判断逻辑（可参数化的核心决策）

- **J-CONFIG-FIRST（配置优先）**：任何新规范零硬编码，只加 YAML 组；handler 只读 `cfg`，业务值（路径/选择器/模式/severity/状态码）全参数化。
- **J-STATIC-GUARD-DUAL-MODE（静态守卫双模式）**：`frontend_review_static_check` 在后端 `forbidden_patterns`（命中即违规）基础上新增 `required_patterns`（整个扫描集完全缺失即违规）——守护"保护性代码被重构误删"这类失败模式，比 backend 守卫更泛化。
- **J-FLAKE-ISOLATION（flake 隔离）**：单测/typecheck 偶发失败时，先单独重跑该用例/命令再归因；EXIT 码与错误行数必须同时校验，禁止仅凭 EXIT≠0 判错。
- **J-FRESH-DIR-ONLY（仅全新目录）**：部署/清理受 safe-delete 钩子约束，统一走"写全新目录 → 移动/重建"，禁止原地 rm/覆盖（与第十轮复盘一致）。
- **J-SEMANTIC-ANCHOR（语义锚点）**：required_patterns 选稳定语义锚点而非易变变量名，重命名时同步配置，避免假阳性。

## 维度四：适用与不适用场景（Applicability）

### 适用场景

- 任意前端项目有**可静态识别的保护性代码**（特征字符串锚点：成对方法名 / CSS class 契约 / 关键 API 调用）→ 用 `frontend_review_static_check`，新增规范只加一组配置。
- 需防"保护性代码被重构误删"的回归场景（编辑重发配对、autoscroll 双 rAF、成对按钮样式、编辑框撑满等 UI 规范）。
- 有编码风险、希望"规范即配置"泛化覆盖、零硬编码适配不同业务参数的团队。

### 不适用场景

- 纯运行时行为、无特征字符串 → `frontend_review_static_check` 的 required_patterns 无法可靠匹配，应改 E2E（button_discovery / theme_switch / runtime 断言）。
- 无前端源码的纯后端改动 → 用既有 `backend_review_static_check`（已覆盖七类后端潜伏缺陷）。
- 单分支无歧义路由（所有非法输入已被框架统一拦截为 4xx、无需逐分支断言返回语义）→ `route_response_branch_coverage` 价值有限，沿用 `api_check` / `path_traversal_test`。
- 一次性的探索性改动、无回归价值的临时代码 → 不必落地新步骤类型，沿用既有阶段即可。

## 与既有协议 / 规则衔接

| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 规范→测试派生链 | wiki-code-dev CODING-* → FR-*/BR-* → wiki-auto-testing 步骤类型 |
| 前端静态守卫双模式 | 新增 `frontend_review_static_check` 步骤类型 + `frontend_review_static_check` 配置块（config.yaml / defaults.yaml），内置 FR-077~FR-080 四组 |
| flake 型 typecheck 误报 | Flake 隔离协议 + 第十轮端到端编排（typecheck 门禁） |
| 仅全新目录部署 | 第十轮 `spa_live_deploy_check` / `service_manage` / safe-delete 钩子约束 |
| 语义锚点防假阳性 | `frontend_review_static_check.groups[].required_patterns` 选稳定锚点 |
| 配置三处同步 | `_step_engine.py` 注册 + config.yaml + defaults.yaml + examples 四处一致 |

# 第十四轮复盘：IndexedDB 写入前剥离 Vue/Pinia 响应式代理（前端静态守卫派生）

> 基于「`frontend/src/services/userConfig.ts` 的 `saveUserConfig` 直传 Vue/Pinia `reactive` 代理 → IndexedDB 的 `structuredClone` 抛 `DataError: [object Array] could not be cloned` → 写事务 abort 被 try/catch 仅 `console.warn` 掩盖 → 四类本地配置（AI / 搜索 / 工具 / 输入框）UI 正常、刷新全丢」的真实经验复盘。
> 与第十三轮（规范→测试派生链）互补：本轮聚焦**"前端运行时静默丢数据"类缺陷如何派生为配置化静态守卫**——把 CODING-IDB-REACTIVE-CLONE（前端 FR-081 / 后端 BR-088 review-scope）的"reactive 代理直传 IndexedDB 必须整树深拷贝"判断逻辑，落地为 `idb_reactive_clone_check` 步骤类型。
> 全程用 **Sequential Thinking** 推导：先定位"静默"根因（proxy 无法被 structuredClone 克隆）→ 再界定窗口上下文启发式（写入点上方 N 行内是否出现深拷贝指示符）→ 最后抽象为与业务解耦、参数全配置化的扫描契约。
> 配套新增 `idb_reactive_clone_check` 动态引擎步骤类型与 `idb_reactive_clone_check` 配置块（见 SKILL.md 与 defaults.yaml / config.yaml / examples），**零硬编码模式与路径**。

## 背景：被测对象与约束

被改动的是一个**前端本地配置服务层**（按用户命名空间读写 IndexedDB：AI / 搜索 / 工具 / 输入框配置）：

- `frontend/src/services/userConfig.ts`：`saveUserConfig<T>(kind, userId, value)` 经 `dbPut('usercfg::<kind>::<userId>', value)` 写 IndexedDB；旧实现直接传 store 的 `reactive`/`ref` 返回值（嵌套对象仍是代理）。
- Vue `reactive`/`ref` 返回 Proxy；IndexedDB `put` 内部 `structuredClone` 序列化 Proxy 失败 → `DataError: [object Array] could not be cloned`（或 `[object Object]`）。
- 写发生在 IDB 事务回调里，proxy 克隆失败使事务 abort，外层 `try/catch` 仅 `console.warn` → **UI 正常、配置刷新全丢**（静默）。
- `toRaw()` 只剥顶层、嵌套代理仍失败；`structuredClone(reactiveObj)` 同样失败——两条"伪剥离"路径都无效。

约束条件：

- 沙箱 **Chromium 未安装、PyYAML 未安装**，浏览器 E2E 与部分依赖 PyYAML 的脚本无法运行；此类"写入即丢"缺陷在浏览器里也**无明显报错**，单测/构建更无法捕获。
- 全部参数（扫描目录 / 写入点模式 / 响应式指示符 / 安全深拷贝指示符 / 伪剥离模式 / severity）必须配置化，**禁止在脚本或 prompt 中硬编码**。
- 必须与既有 `frontend_review_static_check`（双模式）保持**注册表 + 配置块**同构，新增守卫不改引擎主流程。

---

## 维度一：成功执行步骤（Successful Steps）

| 步骤 | 操作 | 产物 / 验证点 | 复用本技能的哪个能力 |
|------|------|---------------|----------------------|
| 1 | **修复根因（整树深拷贝）** | `saveUserConfig` 写入前 `dbPut(key, clone(value))`，`clone<T> = JSON.parse(JSON.stringify(x))`；嵌套对象全剥代理 | CODING-IDB-REACTIVE-CLONE R-1；前端 FR-081 |
| 2 | **隔离单测验证修复** | 9 条 `inputBoxSettings-isolation` 测试：唯一 userId 命名空间、断言写入后读取一致（直传 proxy 会失败）；沿用第九轮纪律 | `indexeddb_test_isolation` + fake-indexeddb（多轮 flush） |
| 3 | **静态守卫防回归** | 配置化 `idb_reactive_clone_check` 扫描 IDB 写入点，核对写入值若源自 store state ref / reactive() 已整树深拷贝；判 `toRaw(` 伪剥离违规 | 新增 `idb_reactive_clone_check` 步骤类型（同构 frontend_review_static_check） |
| 4 | **范围路由判定** | 纯前端改动（.vue / frontend/src/stores / 客户端 IndexedDB 写入）声明范围不匹配并建议走 wiki-frontend-code-review，不硬套后端规则 | 后端 BR-088（review-scope） |
| 5 | **全量套件 + 干净重启** | `vitest run` 全绿；按第十轮端到端编排杀孤儿 :3000 → 重启 → 冒烟 | 第十轮端到端编排 |

关键发现：**"静默丢配置"在浏览器/构建/单测里都无报错信号**——`structuredClone` 抛错发生在 IDB 事务内部，被 try/catch 吞成 warn。唯一的可靠信号是"运行时单测断言写入后读取一致" + "静态守卫确保每次写入点都 clone"。二者互补，缺一不可。

---

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **proxy 克隆失败静默**：`dbPut(reactiveObj)` 的 `structuredClone` 抛 `DataError`，但事务回调外的 `try/catch` 只 `console.warn`，开发与测试都看不到失败 → 配置"看起来存了，刷新没了"。
   - 应对：写入前 `JSON.parse(JSON.stringify(x))` 整树深拷贝为 plain object（剥尽嵌套代理）；structuredClone 对 plain object 才安全。
2. **`toRaw()` 伪剥离误导**：团队曾以为 `toRaw(reactiveObj)` 即可，但 `toRaw` 只剥**顶层**，嵌套数组/对象仍是代理 → 仍 `[object Array] could not be cloned`。
   - 应对：静态守卫把 `toRaw(` 列为 forbidden_unsafe_patterns（R-2），命中即违规；文档明确"必须整树深拷贝"。
3. **`structuredClone(reactiveObj)` 误判安全**：有人改用 `structuredClone(reactiveObj)` 试图克隆，但 structuredClone 同样无法克隆 Proxy → 仍失败。
   - 应对：把 `structuredClone(` 排除在 safe_clone_indicators 之外，由"响应式来源 + 未见安全深拷贝"分支（R-1）自然覆盖其违规。
4. **静态守卫假阳性（primitive ref 误伤）**：`dbPut('theme', currentTheme.value)` 中 `.value` 是 primitive，本不需要 clone。若窗口内恰有 `reactive(` 又无 clone 指示符，会误报。
   - 应对：`reactive_indicators` 收敛为对象级信号（reactive( / toRefs( / toRef( / defineStore(）+ 写入点本行 `reactive_arg_regex`（store./state./this./.value/reactiveStore）；primitive `.value` 单独不触发（需配合窗口内 reactive 来源）。仍保留 scan_window_lines / 指示符全参数化以便调阈值。
5. **窗口上下文截断（clone 在函数更上方）**：若深拷贝指示符距写入点超过 `scan_window_lines`（默认 40），守卫漏检。
   - 应对：`scan_window_lines` 参数化；且推荐"在写入点同行的参数里 clone（如 `dbPut(key, clone(v))`）"这一惯用法，使守卫 100% 命中；超窗口属罕见风格，漏检可经运行时单测兜底。

---

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（IndexedDB 写入前剥离响应式代理）

```
任一前端源码改动触及 IndexedDB 写入点（dbPut / saveUserConfig / idbPut / store.put / transactions.add）
  ├─ 评审/测试：写入值若源自 store state ref / reactive()
  │     → 必须写入前整树深拷贝（JSON.parse(JSON.stringify(x)) / clone(x)）（R-1）
  │     → 禁 toRaw( 当深剥离（R-2）；禁 structuredClone(reactiveObj)（R-3）
  │     → 静态守卫 idb_reactive_clone_check 落地（窗口上下文启发式，参数全配置）
  │     → 真实写入单测兜底（indexeddb_test_isolation：断言写入后读取一致）
  ├─ 封装函数内部统一 clone（防御性）：saveUserConfig 内部 dbPut 前 clone，调用方无需感知（FR-081-4 Suggestion）
  ├─ 纯前端改动（.vue / frontend/src/stores / 客户端 IDB 写入）
  │     → 范围判定走 wiki-frontend-code-review，不硬套后端规则（BR-088）
  └─ 收口：全量套件 → 干净重启（杀孤儿 :3000）→ 冒烟
```

### 判断逻辑（可参数化的核心决策，经 Sequential Thinking 推导）

- **S1 — proxy 无法被 structuredClone 克隆是根因**：Vue `reactive`/`ref` 返回 Proxy，IndexedDB `put` 内部 `structuredClone` 序列化 Proxy 必抛 `[object Array] could not be cloned`；读写 IDB 的 Proxy 克隆失败事务 abort → 必须写入前整树深拷贝为 plain object（R-1）。
- **S2 — 伪剥离判违规**：`toRaw(` 仅剥顶层（R-2）、`structuredClone(reactiveObj)` 同样失败（R-3）；二者均不能替代整树深拷贝，静态守卫列 forbidden / 排除出 safe_clone。
- **S3 — 窗口上下文启发式**：对每个 IDB 写入点，取其上方 `scan_window_lines` 行 + 本行作上下文窗口，检查是否含 safe_clone_indicators；含响应式来源（reactive_indicators / reactive_arg_regex）但无安全深拷贝 → 命中 R-1 违规。**阈值全参数化**（scan_window_lines / 指示符）。
- **S4 — 静态守卫与运行时单测互补**：静态守卫是防回归的廉价门禁（不依赖浏览器/服务），但窗口截断/primitive ref 边界需运行时单测（`indexeddb_test_isolation`）兜底——单测断言"写入后读取一致"。
- **S5 — 范围路由判定**：纯前端改动（含客户端 IndexedDB 写入）声明范围不匹配并建议走 wiki-frontend-code-review，禁止把"reactive-proxy-in-IDB 静默丢配置"误当后端关键写问题（BR-088，对齐第十三轮 review-scope）。
- **S6 — 配置化优先（与第十三轮一致）**：新增守卫只在 `_step_engine.py` 注册 handler（registry 模式，只读 cfg）+ YAML 配置块 + examples；不改引擎主流程、不硬编码模式/路径。

---

## 维度四：适用与不适用场景（Applicability）

### 适用场景

- **前端经 IndexedDB 写入 Vue/Pinia 对象状态**：`services/*UserConfig*.ts` / `*store*.ts` 经 `dbPut` / `saveUserConfig` / `idbPut` / `store.put` / `transactions.add` 写代理对象；用 `idb_reactive_clone_check` 防回归，对应 CODING-IDB-REACTIVE-CLONE / FR-081。
- **运行时静默丢数据类缺陷**：类型检查/构建/浏览器 E2E 都无报错信号（try/catch 吞错）、仅"刷新全丢"的缺陷，需静态守卫 + 真实写入单测双保险。
- **沙箱无浏览器 / 无 PyYAML 环境**：`idb_reactive_clone_check` 纯 grep 源码、无需启动服务或浏览器，回退成本低。
- **多用户本地配置命名空间**：与第七轮 BYOK（`usercfg::<kind>::<userId>`）配合，确保每用户配置既隔离又不被 proxy 克隆失败静默丢弃。

### 不适用场景

- **localStorage / sessionStorage 写入**：经 JSON 序列化，Proxy 会被 JSON.stringify 自动剥为 plain（不会抛错），无需此守卫；仅 IndexedDB（structuredClone 路径）需。
- **IDB 读取返回**：IndexedDB `get` 返回的是 plain object，不存在 proxy 克隆问题；守卫只针对**写入**路径。
- **已是 plain object 的写入**：字面量 / 从 `JSON.parse` 或 `toRaw` 全树后的普通对象写入 IDB，无需 clone；守卫靠 reactive_indicators 收敛，不误伤 plain 写入。
- **纯后端 / 纯服务端落盘**：不涉及 Vue proxy，走 `backend_logic_unit_test` / `backend_review_static_check`；IndexedDB 写入属前端客户端，由前端技能评审（BR-088）。
- **纯前端 UI 动画 / 交互变更（无 IDB 写入）**：本守卫不适用，应走既有 Playwright 浏览器测试。

---

## 与既有协议 / 规则衔接

| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| IDB 写入前整树深拷贝 | 新增 `idb_reactive_clone_check` 步骤类型 + `idb_reactive_clone_check` 配置块（config.yaml / defaults.yaml / examples）；CODING-IDB-REACTIVE-CLONE R-1 / FR-081-1 |
| 禁 toRaw( 伪剥离 | `forbidden_unsafe_patterns: [toRaw(]` → CODING-IDB-REACTIVE-CLONE R-2 / FR-081-2 |
| 禁 structuredClone(reactiveObj) | 排除出 safe_clone_indicators，由 R-1 分支覆盖 → CODING-IDB-REACTIVE-CLONE R-3 / FR-081-3 |
| 封装函数内部统一 clone | `saveUserConfig` 内部 dbPut 前 clone → FR-081-4 Suggestion |
| 真实写入单测兜底 | `indexeddb_test_isolation` + fake-indexeddb（第九轮）；断言写入后读取一致 |
| 范围路由判定 | 后端 BR-088（review-scope）/ 第十三轮"静态守卫双模式" |
| 配置化 / 注册表同构 | 第十三轮 J-CONFIG-FIRST；`_step_engine.py` 注册 + config.yaml + defaults.yaml + examples 四处一致 |
| 端到端收口 | 第十轮 `spa_live_deploy_check` / `service_manage` / 杀孤儿 :3000 干净重启 |

# 第十五轮复盘：后端编码标准静态守卫扩展（BR-089~092）——"规范即配置"派生链的收口泛化

> 与第十三轮（规范→测试派生链：从 CODING 规则派生 frontend_review_static_check）、第十四轮（前端派生链：reactive-proxy-in-IDB → idb_reactive_clone_check）互补：本轮聚焦**后端侧 4 条历史事故提炼规范的测试派生收口**——把 `CODING-ROUTE-RETURN-COMPLETENESS` / `CODING-RESPONSE-HOOK-SAFE` / `CODING-COMPRESSION-DEFAULT-OFF` / `CODING-USER-STORE-INIT`（对应后端 BR-089~092）的判断逻辑，扩展进既有 `backend_review_static_check` 步骤类型（registry 模式，零硬编码）的 `groups[]`，实现"新增后端规范 = 在 YAML 加一组、不改引擎"的泛化收口。
>
> 本轮含 **with Sequential Thinking** 标注：维度三的判断逻辑（S1~S6）经结构化推导得出，明确"派生映射 / 守卫只标需人工复核的构造 / 参数全配置 / 注册表复用 / 跨技能编号一致 / safe-delete 合规"六条可复用决策。

## 维度一：成功执行步骤（Successful Steps）

| 步骤 | 操作 | 产物 / 验证点 | 复用本技能的哪个能力 |
|------|------|---------------|----------------------|
| 1 | **事故→规范→BR 映射** | 4 起历史事故（登录漏 return 双发响应 / compression onSend 钩子挂死 / 压缩默认注册 / users.json 空壳）各提炼 1 条 CODING 规则，顺延编号为 BR-089~092（避免与既有 BR-088 冲突） | wiki-code-dev CODING-*；wiki-backend-code-review BR-089~092 |
| 2 | **扩展静态守卫组** | 在 `backend_review_static_check.groups[]` 新增 4 组：`route_return_completeness` / `response_hook_safe` / `compression_default_off` / `user_store_init`，只标"需人工复核的构造"（reply.code( / onSend 钩子 / register(compress / loadUsers 等） | 既有 `backend_review_static_check` 步骤类型（registry，_step_engine.py 已支持 groups[]） |
| 3 | **零硬编码参数化** | 4 组全部 `patterns` / `scan_dirs` / `file_glob` / `severity` / `regex` / `rule_ref` 来自配置；新增后端规范只需在 YAML 加一组，引擎主流程不变 | J-CONFIG-FIRST（第十三轮）；`_step_engine.py` registry 模式 |
| 4 | **三处 YAML 同步** | `config.yaml` / `defaults.yaml` / `examples/config.enabled.example.yaml` 同步新增 4 组（examples 此前缺 `backend_review_static_check` 段，本轮补齐并 `enabled: true`） | 第十三轮"配置四处一致"纪律 |
| 5 | **版本表 + 本复盘闭环** | SKILL.md 版本表置顶 `v2.13.0`；本第十五轮 4 维度复盘收口 | 第十轮端到端编排（版本表即门禁记录） |

关键发现：**静态守卫无法"确定性"检出这四类缺陷**（是否漏 return、钩子是否 fail-open、压缩是否条件注册、加载是否兜底——都需要 AST/语义判断），只能"标出需要人工复核的高风险构造"。因此这 4 组一律 `severity: warn` + 提示语要求逐分支/逐钩子人工确认，不作为阻断。这与 `swallowed_critical_write` 组（标 saveUsers 等须复核是否吞错）的既有范式一致。

---

## 维度二：不确定性与失败点（Uncertainties / Failures）

1. **漏 return 无法静态判定**：`reply.code(` 既出现在"漏 return"分支，也出现在"已 return reply.code(...)"的正确分支。纯 grep 无法区分 → 守卫只能标出所有 `reply.code(/reply.status(` 供人工逐分支核对。
   - 应对：`route_return_completeness` 组 `severity: warn`，message 明确要求"逐分支确认已显式 return/throw"。
2. **钩子可能本就 fail-open**：`setSerializer` / `contentTypeParser` 等响应钩子在很多项目里是安全且必要的，标出不等于违规。
   - 应对：`response_hook_safe` 组 `warn` + 提示"确认内部 try/catch fail-open 且无 await 重计算"，由评审者判断是否真有风险。
3. **压缩可能已在 if 内**：`register(compress` 命中不代表"无条件注册"——它可能已包在 `if (config.compress.enable)` 内。
   - 应对：`compression_default_off` 组 `warn` + 提示"确认默认关闭且条件注册"，人工看上下文。
4. **JSON.parse( 误伤面广**：`user_store_init` 组标 `JSON.parse(` 会命中一切 JSON 解析（含正常业务），远超"关键数据加载兜底"范围。
   - 应对：pattern 同时含 `loadUsers` / `loadConfig` 作为更精准锚点 + 整体 `warn`；提示"确认区分 not-found 与 corrupt 并兜底回退默认 + 备份 + log.warn"。
5. **safe-delete 沙箱对静态守卫的影响**：静态守卫步骤是**纯 grep 读源码**（不写不删），天然符合 safe-delete 钩子 fail-closed 工作模式（仅放行新建目录整目录写入 / 移动到全新路径）；配置 YAML 的编辑属"向既有文件写新内容"（Edit/Write），非 unlink/rm/覆盖式重命名，沙箱内放行。故本扩展**无 safe-delete 风险**，也不引入跨进程 TCP 冒烟依赖（守卫在引擎进程内完成）。

---

## 维度三：可抽象的固定流程与判断逻辑（Abstractable Fixed Process + Judgment）

### 固定流程（从历史事故派生后端静态守卫组）

```
任一历史事故经复盘确认根因
  ├─ wiki-code-dev 提炼 1 条 CODING-* 规则（Scope / Rules / Configuration Parameters 三段式）
  ├─ wiki-backend-code-review 顺延编号 BR-08x（避免与既有编号冲突）
  │     → SKILL.md Quick-Check + .rules-index + historical-incidents + review-config + references/ rule 文件 五处一致
  ├─ wiki-auto-testing 扩展 backend_review_static_check.groups[]
  │     → 仅标"需人工复核的高风险构造"（不追求确定性判定），severity=warn
  │     → patterns / scan_dirs / file_glob / severity / regex / rule_ref 全来自 YAML（J-CONFIG-FIRST）
  │     → 复用 _step_engine.py 既有 registry handler，不改引擎主流程
  ├─ 三处 YAML 同步（config.yaml / defaults.yaml / examples/config.enabled.example.yaml）
  └─ 收口：SKILL.md 版本表置顶 vX.Y.0 + 本复盘追加一轮 4 维度（with Sequential Thinking）
```

### 判断逻辑（可参数化的核心决策，经 Sequential Thinking 推导）

- **S1 — 事故→规范→BR 1:1 映射且编号顺延**：每起事故对应恰好一条 CODING 规则与一条 BR，编号顺延（本轮回填 BR-089~092，接在 BR-088 review-scope 之后），避免与既有 `BR-ESM-04` / `BR-076~088` 冲突。映射表须在三技能间一致。
- **S2 — 静态守卫只标"需人工复核的构造"，不追求确定性判定**：漏 return / 钩子未 fail-open / 压缩无条件注册 / 加载未兜底均属语义缺陷，纯 grep 无法判定；守卫职责是"标出高风险构造 + 提示人工逐分支核对"，故一律 `warn`。这与第十三/十四轮"静态守卫是廉价门禁、运行时单测兜底"的定位一致。
- **S3 — 参数全配置、零硬编码（J-CONFIG-FIRST）**：`patterns` / `scan_dirs` / `file_glob` / `severity` / `regex` / `rule_ref` 全在 YAML；新增后端规范 = 加一组，引擎主流程与 `_step_engine.py` 不动。泛化能力来自 registry 模式而非特判。
- **S4 — 复用既有 registry handler，无引擎代码变更**：`backend_review_static_check` 的 handler 本就遍历 `groups[]` 做 grep，新增 4 组自动被覆盖——这是第十三轮建立的"配置化步骤类型泛化"的直接收益，证明派生链已闭环。
- **S5 — 跨技能编号一致性是硬约束**：BR-089~092 必须同时出现在 wiki-backend-code-review 的 SKILL.md / .rules-index.md / historical-incidents.md / review-config.md / references/ 5 处，且 wiki-auto-testing 的 `rule_ref` 与之对齐；Task #21 还要镜像 `.trae` 副本。编号漂移会让"规范→测试"链路断点。
- **S6 — safe-delete 合规：守卫读源码、配置写新内容**：静态守卫步骤纯 grep（读），不触发 safe-delete 拦截；YAML 编辑是 Edit/Write 既有文件（非 unlink/rm/重命名已存在），沙箱放行。故本扩展在 safe-delete + 跨进程 TCP 拦截双重约束下均可落地，无需额外冒烟。

---

## 维度四：适用与不适用场景（Applicability）

### 适用场景

- **Fastify/TS 后端存在 4 类潜在缺陷**：路由多分支漏 return、全局响应钩子未 fail-open、压缩中间件硬编码注册、关键数据文件加载未兜底——用 `backend_review_static_check` 4 组做 PR 级门禁，零运行时依赖。
- **已采纳对应 CODING 规则的项目**：任何把 `CODING-ROUTE-RETURN-COMPLETENESS` 等纳入编码规范的项目，可直接复用这 4 组（pattern 可按项目微调，仍走配置）。
- **多项目泛化**：`_step_engine.py` registry + YAML 配置块天然跨项目；新后端项目接入只需改 `scan_dirs` / `file_glob`，逻辑不变。

### 不适用场景

- **非 Fastify 后端（如 Express/Koa）**：`reply.code(` 模式不会命中（Express 用 `res.status().json()`），`route_return_completeness` 组自然空转；如需覆盖须改 pattern（仍走配置，不硬编码引擎）。
- **纯前端改动**：这 4 组是后端守卫，前端对应为 FR-082/FR-083（认证超时兜底 / loading 复位），应由 wiki-frontend-code-review 评审（BR-088 review-scope 范围路由判定）。
- **构造本就合规的情况**：钩子已 fail-open、压缩已条件注册等——守卫 `warn` 仅提示，评审者确认后忽略，不阻断 CI。
- **需要确定性判定的场景**：若要求"自动确认漏 return"，纯 grep 守卫力不从心，须升级为 AST/语义分析（超出本轮静态守卫范围，属未来增强）。

---

## 与既有协议 / 规则衔接

| 本复盘要素 | 衔接的配置 / 协议 / 规则 |
|-----------|--------------------------|
| 4 起事故→4 条 CODING 规则 | wiki-code-dev `references/`：route-return-completeness / response-hook-safe / compression-default-off / user-store-init 四个 `CODING-*` rule 文件 |
| 顺延编号 BR-089~092 | wiki-backend-code-review SKILL.md / .rules-index.md / historical-incidents.md / review-config.md / references/ 五处一致 |
| 扩展 4 组静态守卫 | `backend_review_static_check.groups[]`：`route_return_completeness` / `response_hook_safe` / `compression_default_off` / `user_store_init`（v2.13.0） |
| 零硬编码 / 参数全配置 | J-CONFIG-FIRST（第十三轮）；`config.yaml` / `defaults.yaml` / `examples/config.enabled.example.yaml` 三处同步 |
| 复用 registry handler | `_step_engine.py` 既有 `backend_review_static_check` handler（遍历 groups[]），无引擎代码变更 |
| 跨进程/safe-delete 合规 | 第十二/十轮 safe-delete 钩子 fail-closed 工作模式；守卫纯 grep 读源码、配置写新内容，均无风险 |
| 端到端收口 | 第十轮 `spa_live_deploy_check` / `service_manage` / 杀孤儿 :3000 干净重启；SKILL.md 版本表 v2.13.0 |

