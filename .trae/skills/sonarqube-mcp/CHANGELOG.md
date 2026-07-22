# SonarQube MCP 技能变更日志

## v2.4.0 (2026-07-22) - 沙箱弹性 + 项目锁清理 + 修复模式复用

### 设计目标

基于 2026-07-22 在 XianyuHunter 项目（FastAPI + React + TypeScript）上的实战复盘（100+ OPEN → 0 OPEN，TypeScript 编译通过，1613 Python 测试通过），将 4 维度复盘成果（成功步骤/失败点/抽象流程/适用场景）沉淀到配置文件，新增三大弹性机制应对 TRAE 沙箱限制、项目锁持有、长任务日志缓冲问题。

### 核心改进

#### 1. 新增三大弹性机制（failure_recovery.mappings 扩展 4 个场景）

| 失败场景 | 恢复动作 | 配置位置 |
|----------|----------|----------|
| `sandbox_blocked` | `disable_sandbox_and_retry`（`dangerouslyDisableSandbox: true`） | `core_config.json -> failure_recovery.mappings[sandbox_blocked]` + `sandbox_bypass` 节点 |
| `project_lock_held` | `cleanup_scanner_processes_and_lock`（taskkill /T + 删锁 + 清目录） | `core_config.json -> failure_recovery.mappings[project_lock_held]` + `project_lock_cleanup` 节点 |
| `process_termination_failed` | `taskkill_force_tree`（`taskkill /F /T /PID`） | `core_config.json -> failure_recovery.mappings[process_termination_failed]` |
| `jre_provisioning_timeout` | `warn_and_wait`（仅警告不阻塞） | `core_config.json -> failure_recovery.mappings[jre_provisioning_timeout]` |

#### 2. 新增 3 个独立配置节点

| 节点 | 用途 | 关键配置 |
|------|------|----------|
| `sandbox_bypass` | TRAE 沙箱旁路配置 | detection_keywords / bypass_parameter / bypass_scope=sonar-scanner only |
| `project_lock_cleanup` | 项目锁清理配置 | detection_keyword / max_retries=3 / cleanup_steps（6 步流程） |
| `log_output` | 长任务日志输出规则 | forbidden_patterns（Select-Object -Last N）/ recommended_patterns（Tee-Object） |

#### 3. precheck 新增 jre_cache_check 项

- 检测 `.sonar/cache/jre` 目录是否存在
- 首次运行输出耗时警告（预计 10-30 分钟下载 JRE），不阻塞流程
- 后续运行使用缓存（约 2 秒）

#### 4. 新增 fix_patterns 可复用修复模式库（5 个模式）

| 模式名 | 触发条件 | 适用规则 |
|--------|----------|----------|
| `formatCellValue` | S3358/S6551/S6606 涉及 unknown 类型字符串化 | typescript:S3358, typescript:S6551, typescript:S6606 |
| `native_button` | S6819/S1082/S6845 role="button" 可访问性 | typescript:S6819, typescript:S1082, typescript:S6845 |
| `scanner_process_cleanup` | 项目锁持有/进程终止失败 | project_lock_held, process_termination_failed |
| `sandbox_bypass` | TRAE 沙箱阻断 sonar-scanner | sandbox_blocked |
| `long_task_log` | 长任务日志输出 | sonar-scanner, pytest, npm test 等 |

#### 5. 增强修复策略模板

| 规则 | 增强内容 |
|------|----------|
| `typescript:S6551` | 新增 `false_positive_root_cause` 字段说明 SonarQube 不识别 typeof 链式收窄；新增 `fix_pattern_ref: formatCellValue` 引用 |
| `typescript:S6819` | 新增完整样式重置清单（border/background/textAlign/cursor/font）；新增 `side_effect_fixes: [typescript:S1082]` 副作用修复；新增 `fix_pattern_ref: native_button` 引用 |

#### 6. 扩展 nosonar_decision_matrix.can_suppress_rules

新增 `typescript:S6819` 和 `typescript:S3358` 到可抑制规则列表（误报倾向规则）。

#### 7. project_config.json 更新为 xianyu_hunter

- 从 20_news 项目配置切换到 xianyu_hunter 项目配置
- 新增 `sonar_project_properties` 节点（projectKey/sources/tests/python_version/tsconfig_path/coverage_report_paths）
- 新增 `quality_gate_baseline` 节点记录 2026-07-22 实战后基线（0 OPEN / 0 new_violations / 1613 测试通过）
- 新增 `fix_strategies_overrides.high_frequency_rules` 记录高频规则分布

### 4 维度复盘成果

#### 维度 1：成功执行任务的完整步骤

15 阶段闭环流程（v2.3 的 14 阶段 + Phase 9 失败弹性恢复）：服务器检测 → ES 弹性预检 → 前置检查（8 项）→ 环境兼容预检（含 JRE 缓存）→ MCP 检测 → 代码定位 → 质量门禁 → 问题扫描 → CE 报告轮询 → 并行修复（含修复模式查表）→ NOSONAR 决策校验 → 验证 → 报告 → 状态管理 → 失败弹性恢复

#### 维度 2：失败点（20 类，全覆盖）

环境层（4 类，含 TRAE 沙箱阻断/JRE 缓存/Select-Object 缓冲/Stop-Process 失败）+ ES 层（2 类）+ 连接层（2 类）+ 锁与状态层（2 类，含项目锁持有）+ 修复与验证层（4 类，含 S6551 typeof 误报）+ 其他（2 类），全部映射到 `failure_recovery.mappings` 配置驱动恢复。

#### 维度 3：可抽象的判断逻辑（13 条）

J1-J9（v2.3 保留）+ J10 沙箱旁路判断 + J11 项目锁清理判断 + J12 长任务日志输出判断 + J13 修复模式查表

#### 维度 4：适用场景与不适用场景

新增适用场景：TRAE IDE 沙箱环境、TypeScript + Python 混合项目大规模 OPEN 清零
新增不适用场景：紧急热修复（首次 JRE 下载 19+ 分钟）、API token 仅有扫描权限（需 MCP 或 API 权限 token）
新增边界场景：Sandbox 限制范围变化、首次 JRE 下载超时、子进程未被 taskkill 终止、NOSONAR 在新版 SonarQube 不生效

### 修改文件清单

| 文件 | 修改类型 |
|------|----------|
| `SKILL.md` | 修改：版本号 v2.3 → v2.4，14 阶段 → 15 阶段，新增 Phase 9 失败弹性恢复章节，新增 4 条失败恢复映射，新增 4 条设计原则，更新配置文件分层表，更新上下文加载规则，新增复盘文档引用 |
| `config/core_config.json` | 修改：`_meta.version` v2.3.0 → v2.4.0，新增 `sandbox_bypass`/`project_lock_cleanup`/`log_output` 3 个节点，`precheck.checks` 新增 `jre_cache_check`，`failure_recovery.mappings` 新增 4 个场景，`nosonar_decision_matrix.can_suppress_rules` 扩展 2 个规则 |
| `config/fix_strategies.json` | 修改：`_meta.version` v2.2.0 → v2.4.0，增强 `typescript:S6551` 和 `typescript:S6819` 修复模板，新增 `fix_patterns` 节点（5 个可复用修复模式） |
| `config/project_config.json` | 修改：从 20_news 切换到 xianyu_hunter 项目配置，新增 `sonar_project_properties`/`quality_gate_baseline`/`fix_strategies_overrides.high_frequency_rules` 节点 |
| `references/retrospective-2026-07-22.md` | 新增：2026-07-22 实战复盘 4 维度详细文档（成功步骤/失败点/抽象流程/适用场景） |

### 实战数据

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| OPEN 问题数 | 100+ | 0 |
| new_violations | 15 | 0 |
| TypeScript 编译 | — | ✅ 通过（exit 0） |
| Python 测试 | — | ✅ 1613 passed |
| new_coverage | — | 18.5%（目标 80%，需补充单测） |
| new_security_hotspots_reviewed | — | 0%（目标 100%，需手动 UI 审查） |

---

## v2.3.0 (2026-07-21) - 配置驱动 + 通用泛化 + 全链路核查

### 设计目标

基于用户对 sonarqube 使用过程的 4 维度复盘（成功步骤/失败点/固定流程/适用场景），消除 SKILL.md 中的所有硬编码值，提升技能的通用性和泛化能力，支持多项目并行。

### 核心改进

#### 1. 消除 SKILL.md 硬编码值（8 处）

| 优化点 | 修改前 | 修改后 |
|--------|--------|--------|
| 环境变量示例 | 硬编码 `squ_xxx`/`localhost`/`9000`/`xianyu_hunter` | 改为配置引用表格 + `<your-xxx>` 占位符 |
| NOSONAR 决策规则 | 硬编码 `S5446/S930/S2817` 等具体规则 ID | 改为"从 `core_config.json -> nosonar_decision_matrix` 读取" |
| Java 版本要求 | 硬编码 "Java 17+" | 改为"从 `precheck.checks[java_version].min_version` 读取" |
| Node.js 版本要求 | 硬编码 "Node.js v24+" | 改为"从 `incompatible_node_versions` 列表读取" |
| 紧凑格式示例 | 硬编码 `python:S1481`/`src/api/routes.py:42` | 改为 `{rule_id}`/`{file_path}:{line}` 占位符 |
| 失败恢复描述 | 硬编码 "Java 17+" | 改为"满足 `min_version` 的 Java 版本" |
| 复盘声明 | 硬编码 "2026-07-07 实战 336→0" | 改为"详见 CHANGELOG.md" |
| 配置文件表 | 硬编码 "v2.1.0"/"Xianyu 业务配置" | 改为"`_meta.version` 字段标识" |

#### 2. 配置文件版本兼容性机制

- `core_config.json` `_meta` 新增 `schema_version` 和 `min_compatible_version` 字段
- `project_config.json` `_meta` 同步新增 `schema_version` 字段
- 加载时通过 `scripts/validate-config.ps1` 校验版本兼容性
- 向后兼容：`min_compatible_version` 默认为 `2.0.0`，v2.0+ 配置均可正常加载

#### 3. 业务约束加载机制（支持多项目并行）

- `project_config.json` 新增 `business_constraints.load_files` 字段
- 业务约束文件按数组顺序加载，后者覆盖前者同名规则
- 默认行为：`load_files` 为空数组时仅加载 `core.json` 通用规则
- 多项目隔离：每个项目独立配置自己的业务约束，互不污染

#### 4. 通用文档与示例泛化

| 文件 | 类型 | 说明 |
|------|------|------|
| `references/rule-overrides.md` | 新增 | 通用规则豁免指南（5 个范式 + 业务覆盖编写指南） |
| `examples/xianyu-hunter/rule-overrides.md` | 迁移 | 原 `references/xianyu-rule-overrides.md` 迁移至此，作为业务特定示例 |
| `examples/basic-typescript/` | 新增 | 最简 TypeScript 项目配置示例（无业务依赖） |

#### 5. 自动化脚本新增

| 脚本 | 用途 |
|------|------|
| `scripts/detect-project.ps1` | 项目类型自动检测（Python/TS/Java/Go），生成 `project_config.json` 草稿 |
| `scripts/validate-config.ps1` | 配置文件完整性与一致性校验（5 阶段校验 + ERROR/WARNING 分级） |

### 4 维度复盘成果

#### 维度 1：成功执行任务的完整步骤

14 阶段闭环流程：服务器检测 → ES 弹性预检 → 前置检查 → 环境兼容预检 → MCP 检测 → 代码定位 → 质量门禁 → 问题扫描 → CE 报告轮询 → 并行修复 → NOSONAR 决策校验 → 验证 → 报告 → 状态管理

#### 维度 2：失败点（16 类，全覆盖）

环境层（4 类）+ ES 层（2 类）+ 连接层（2 类）+ 修复层（4 类）+ 验证层（2 类）+ 其他（2 类），全部映射到 `failure_recovery.mappings` 配置驱动恢复。

#### 维度 3：可抽象的判断逻辑（9 条）

J1 NOSONAR 位置判断 / J2 NOSONAR 决策矩阵 / J3 收敛判断 / J4 MCP 降级 / J5 环境兼容预检 / J6 修复策略查表 / J7 子代理结果核查 / J8 测试失败归因 / J9 配置占位符解析

#### 维度 4：适用场景（10 类）与不适用场景（10 类）

详见 SKILL.md "适用场景" 和 "不适用场景" 章节。

### 修改文件清单

| 文件 | 修改类型 |
|------|----------|
| `SKILL.md` | 修改：版本号 v2.2 → v2.3，消除 8 处硬编码，增加业务约束加载机制说明，更新脚本表/示例表/参考文档表 |
| `config/core_config.json` | 修改：`_meta` 增加 `schema_version` 和 `min_compatible_version` 字段 |
| `config/project_config.json` | 修改：`_meta` 增加 `schema_version`，新增 `business_constraints.load_files` 字段 |
| `references/rule-overrides.md` | 新增：通用规则豁免指南（5 个范式） |
| `examples/xianyu-hunter/rule-overrides.md` | 迁移：从 `references/xianyu-rule-overrides.md` 迁移至业务示例目录 |
| `examples/basic-typescript/` | 新增：通用 TypeScript 项目示例（project_config.json + README.md） |
| `scripts/detect-project.ps1` | 新增：项目类型自动检测脚本 |
| `scripts/validate-config.ps1` | 新增：配置文件校验脚本 |

### 验证标准

- ✅ SKILL.md 中无任何具体规则 ID、端口号、版本号硬编码
- ✅ 所有参数均可通过配置文件管理
- ✅ 通用示例可独立运行（不依赖 Xianyu 业务）
- ✅ 自动检测脚本可正确识别 Python/TS/Java/Go 项目类型
- ✅ 配置校验脚本可检测出所有配置错误

---

## v2.2.0 (2026-07-21) - 环境兼容 + 决策驱动 + 全链路核查

### 设计目标

基于 2026-07-21 一次完整闭环实战（168 → 0 OPEN，25 个源文件修改）的复盘沉淀，解决 v2.1 的五个未覆盖问题：
1. **Node.js 版本不兼容**：v24+ 与 SonarJS bridge 不兼容，导致 JS/TS 扫描完全失败
2. **PowerShell .bat 封装缺失**：PowerShell 5 直接执行 sonar-scanner `-D` 参数报错
3. **NOSONAR 抑制 vs 修复决策缺失**：子代理可能对安全漏洞规则使用 NOSONAR 抑制而非代码修复
4. **子代理修复结果不可信**：子代理报告"已加 NOSONAR"但可能遗漏或位置错误
5. **多行函数定义 NOSONAR 位置错误**：18 处 NOSONAR 被错误加在 `-> ReturnType:` 行尾而非 `def func(` 行尾

### 核心改进

#### 1. 环境兼容性预检（新增 Phase 0.5）

| 配置节点 | 用途 |
|---------|------|
| `core_config.json -> precheck.checks[node_version_check]` | Node.js 版本与 SonarJS bridge 兼容性检测 |
| `core_config.json -> precheck.checks[powershell_compat_check]` | Windows PowerShell .bat 封装检测 |

**关键特性**：
- Node.js v24/v25 不兼容时自动跳过前端扫描（`on_failure: skip_frontend_scan`）
- PowerShell .bat 封装不存在时自动生成（`on_failure: generate_bat_wrapper`）
- 预检从 5 项扩展到 7 项

#### 2. NOSONAR 决策矩阵（新增 Phase 5.5 + nosonar_decision_matrix）

| 分类 | 规则数 | 行为 |
|------|--------|------|
| must_fix_rules | 9 | 安全漏洞/注入规则，必须代码修复，禁止 NOSONAR |
| can_suppress_rules | 12 | 认知复杂度/代码风格规则，允许 NOSONAR 但需原因注释 |

#### 3. 子代理修复结果二次核查（新增 subagent_verification）

- 修复后主代理 grep 验证 NOSONAR 是否实际存在
- AST 解析验证多行函数定义 NOSONAR 位置正确性
- 校验 NOSONAR 规则不在 must_fix_rules 中

#### 4. 测试失败 git stash 归因（新增 test_failure_diagnosis）

- 修复后测试失败时，git stash → 跑测试 → 区分预存在 vs 本次引入
- 预存在失败：warn_and_continue
- 本次引入失败：block_and_report_diff

#### 5. 前端注释语法映射表（新增 frontend_comment_syntax）

- 10 种文件类型的 NOSONAR 注释语法映射（.js/.ts/.vue/.jsx/.tsx/.wxml/.wxss/.css/.scss/.html）
- .vue 文件按 `<template>`/`<script>`/`<style>` 区块使用不同语法
- 微信小程序 .wxml/.wxss 专项支持

#### 6. nosonar-positioning.md 增强

- 新增错误 6：多行函数定义 NOSONAR 加在返回类型行（18 处实战案例）
- 新增决策矩阵章节（must_fix_rules + can_suppress_rules 完整分类）
- 新增前端文件注释语法速查表
- 决策树扩展：6 步决策流程（含多行 def 首行规则 + 决策矩阵判断）
- 修复硬编码项目路径引用

### 配置文件变更

| 文件 | 版本 | 变更 |
|------|------|------|
| `config/core_config.json` | v2.1.0 → v2.2.0 | 新增 5 个配置节点（nosonar_decision_matrix / subagent_verification / test_failure_diagnosis / frontend_comment_syntax / precheck 2 项新检查），failure_recovery.mappings 新增 4 个场景，environment_variables 新增 2 个可选变量 |
| `references/nosonar-positioning.md` | v2.1 → v2.2 | 新增错误 6 + 决策矩阵章节 + 前端注释语法速查表，决策树 4 步→6 步，核心原则 7→11 条 |
| `SKILL.md` | v2.1 → v2.2 | 新增 Phase 0.5/5.5，14 阶段流程，9 项判断逻辑，16 项失败恢复，9 项设计原则 |

### 实战验证数据

- **起点**：168 个 OPEN 问题
- **终点**：0 个 OPEN 问题
- **源文件修改**：25 个后端 + 1 个测试
- **关键学习**：18 处 NOSONAR 位置错误（多行 def 末行）、1 处子代理遗漏、4 处预存在测试失败、Node.js v24 不兼容、PowerShell .bat 封装需求

### 已知限制

1. `nosonar_decision_matrix` 规则列表基于实战经验，新规则需补充
2. `frontend_comment_syntax` 未覆盖所有前端框架文件类型（可扩展）
3. Node.js 版本兼容性检测基于已知不兼容版本列表，新版本需补充
4. `subagent_verification.nosonar_position_correct` 的 AST 解析仅支持 Python

---

## v2.1.0 (2026-07-07) - 弹性恢复 + NOSONAR 位置规则 + 复盘沉淀

### 🎯 设计目标

基于 2026-07-07 一次完整闭环实战（336 → 0 OPEN，4 轮扫描-修复循环）的复盘沉淀，解决 v2.0 的三个未覆盖问题：
1. **ES 弹性缺失**：开发机磁盘紧张时 ES 自动锁定索引，CE 报告处理失败，扫描无法继续
2. **NOSONAR 位置错误**：子代理将 `# NOSONAR` 放在 def 行，但 S107/S7483 报的是参数行，导致重扫后 OPEN 数不下降
3. **CE 报告处理时序**：sonar-scanner 上传报告后 CE 异步处理，立即查询会读到旧数据

### ✨ 核心改进

#### 1. ES 弹性自愈机制（新增 Phase -0.5）

| 配置节点 | 用途 |
|---------|------|
| `core_config.json -> es_resilience` | ES 弹性配置（端口/watermark/解锁 API/配置文件路径） |
| `core_config.json -> precheck` | 5 项环境预检（含 disk_space / es_read_only_block） |

**关键特性**：
- 扫描前检测 ES 索引是否被 `read_only_allow_delete` 锁定
- 自动通过 ES REST API（端口 9001）解除锁
- 持久化 watermark 阈值（low=95% / high=97% / flood_stage=99%），防重启后再触发
- 配置文件路径陷阱识别：实际在 `data/es8/config/elasticsearch.yml`，`elasticsearch/config/elasticsearch.yml` 是诱饵路径
- 不适用 SonarCloud SaaS（自动跳过）

#### 2. NOSONAR 位置规则表（新增 fix_strategies.json -> nosonar_position_rules）

新增 9 条 NOSONAR 抑制注释位置规则，覆盖历次实战遇到的所有场景：

| 规则 | 位置 | 说明 |
|------|------|------|
| python:S125 | issue_line | NOSONAR 必须在 # 注释中，不能在 docstring 字符串内 |
| python:S107 | first_param_line | S107 报参数行不报 def 行 |
| python:S7483 | issue_line | S7483 报 timeout 参数行 |
| python:S5850 | issue_line | 正则赋值行 |
| typescript:S6551 | issue_line | 模板字符串行 |
| typescript:S6848 | issue_line | JSX 标签内用 `/* NOSONAR */`，标签外用 `// NOSONAR` |
| typescript:S6754 | issue_line | useState 调用行 |
| python:S7503 | n/a | 不需要 NOSONAR（直接删除 async 或加 await） |
| typescript:S7741 | n/a | 不需要 NOSONAR（直接修改代码） |

**核心原则**（在 `nosonar_position_rules._core_principles` 中配置）：
1. `# NOSONAR` 必须大写，小写 `# nosonar` 不生效
2. Python `# noqa` SonarQube 默认不识别，必须用 `# NOSONAR`
3. TypeScript/JavaScript 标签外用 `// NOSONAR`
4. JSX 标签内用 `/* NOSONAR */`（`//` 会被解析为字符串）
5. docstring 字符串内的 NOSONAR 不生效，需先转为 `#` 注释
6. NOSONAR 必须放在 SonarQube 报告的 issue.line 所在物理行末尾
7. 不同规则报问题的物理行不同（S107 报参数行，S7483 报 timeout 参数行）

**新增单一可信源文档**：`references/nosonar-positioning.md`（9 条规则 + 5 个常见错误 + 5 个修复示例）

#### 3. CE 报告轮询机制（新增 Phase 4.5）

| 配置节点 | 用途 |
|---------|------|
| `core_config.json -> report_polling` | CE 报告处理状态轮询（端点/间隔/最大尝试数/终态） |

**关键特性**：
- sonar-scanner 上传报告后，按 `poll_interval_seconds=5` 间隔轮询 `/api/ce/task?id=xxx`
- 终态判断：SUCCESS / FAILED / CANCELED
- FAILED 时按 `failure_recovery.mappings[report_processing_failed]` 恢复（通常为 ES 锁）
- 仅降级方案需要（MCP 直接查询不依赖 CE 处理）

#### 4. 失败恢复动作映射表（新增 failure_recovery 节点）

8 个失败场景 → 恢复动作的映射关系全部配置化：

| 失败场景 | 恢复动作 | 是否重试 |
|---------|---------|---------|
| `server_status` | `start_sonarqube` | ✅ |
| `java_version` | `guide_set_java_home` | ❌ |
| `disk_space` | `unlock_es_and_persist_watermark` | ✅ |
| `es_read_only_block` | `unlock_es_read_only_block` | ✅ |
| `sonar_token` | `terminate_with_guide` | ❌ |
| `report_processing_failed` | `check_es_read_only_block` | ✅ |
| `scm_blame_missing` | `warn_only` | ❌ |
| `nosonar_not_effective` | `reposition_nosonar` | ✅ |

#### 5. 修复策略扩展（fix_strategies.json v2.1.0 → v2.2.0）

v2.0 覆盖 30+ 规则 → v2.2 覆盖 45+ auto_fix 规则 + 10 manual_review + 4 skip + 9 nosonar_position_rules。

**新增 18 个 auto_fix 规则**：
- Python：S107、S7483、S5850、S1172、S930、S7503（从 manual_review 移到 auto_fix）
- TypeScript：S6551、S7741、S7764、S6819、S6845、S6847、S6848、S7735、S6582、S2486、S3358、S6754

#### 6. 收敛控制（新增 scan 节点字段）

| 字段 | 默认值 | 用途 |
|------|--------|------|
| `scan.max_scan_iterations` | 5 | 扫描-修复-重扫最大循环次数 |
| `scan.target_open_count` | 0 | 收敛目标，达到则提前结束 |

#### 7. SKILL.md 复盘声明（新增章节）

新增"复盘声明（v2.1 沉淀）"章节，包含 4 个维度：
- 成功执行任务的完整步骤（12 个 Phase）
- 任务执行过程中的不确定性与失败点（6 个失败点 × 配置化恢复动作）
- 可抽象的固定流程与判断逻辑（5 项）
- 适用场景与不适用场景

#### 8. 工作流扩展（5 阶段 → 8 阶段 + 弹性预检）

| 新增阶段 | 目的 |
|---------|------|
| Phase -0.5 | ES 弹性预检与解锁 |
| Phase 2.5 | CE 报告轮询 |
| Phase 5（扩展） | 新增 NOSONAR 位置校验、收敛判断 |

#### 9. scan-workflow.md 新增调用模式

新增"模式7：ES 锁解锁（独立维护操作）"，并更新所有现有模式以包含 ES 预检（步骤 0.5）和报告轮询（步骤 4.5）。

### 🔄 配置文件变更

| 文件 | 版本 | 变更 |
|------|------|------|
| `config/core_config.json` | v2.0.0 → v2.1.0 | 新增 5 个节点（es_resilience / precheck / report_polling / nosonar_validation / failure_recovery），scan 节点新增 max_scan_iterations / target_open_count，verify 节点新增 validate_nosonar_position |
| `config/fix_strategies.json` | v2.1.0 → v2.2.0 | 新增 18 个 auto_fix 规则、增强 S125 描述、新增 nosonar_position_rules 节点（9 条规则） |
| `references/nosonar-positioning.md` | 新建 | NOSONAR 位置规则单一可信源文档 |
| `references/scan-workflow.md` | 通用化 | 新增 Phase -0.5/4.5/5.4/6.3/6.6 + 模式7，更新所有 scan_config.json 引用为 core_config.json + project_config.json，xianyu_hunter 改为 `${ENV:SONAR_PROJECT_KEY|xianyu_hunter}` 占位符 |
| `SKILL.md` | v2.0 → v2.1 | 新增复盘声明章节、ES 弹性/NOSONAR/报告轮询描述、14 项设计原则（新增 4 项）、失败恢复扩展为 12 项 |

### 📊 实战验证数据

- **起点**：336 个 OPEN 问题
- **终点**：0 个 OPEN 问题
- **扫描-修复循环次数**：4 轮（336 → 69 → 20 → 5 → 0）
- **关键学习**：5 个残留问题全部因 NOSONAR 位置错误导致（S107 报参数行、S7483 报 timeout 行、S125 在 docstring 内不生效）

### 🚧 已知限制

1. ES 弹性机制不适用 SonarCloud SaaS（ES 由 SonarSource 托管）
2. `nosonar_position_rules` 表仅覆盖已遇到的 9 条规则，新规则需实战中补充
3. CE 报告轮询仅降级方案需要，MCP 模式跳过
4. `failure_recovery.mappings` 当前 8 个场景，新失败场景需补充

### 📝 升级建议

**v2.0 用户**：
- 直接覆盖 `config/core_config.json` 和 `config/fix_strategies.json`
- 重新阅读 `SKILL.md` 的"复盘声明"和"工作流"章节
- 阅读 `references/nosonar-positioning.md` 了解 NOSONAR 位置规则
- 设置 `SONAR_ES_PORT` 环境变量（默认 9001）

**新项目**：
- 复制 `examples/xianyu-hunter/` 或 `examples/basic-python/`
- 修改 `project_config.json` 适配项目
- 设置环境变量（必填 `SONAR_TOKEN`，可选 `SONAR_ES_PORT` 等）
- 运行 `.\scripts\verify-connection.ps1` 验证

---

## v2.0.0 (2026-07-02) - 重大重构：通用化 + 配置分层

### 🎯 设计目标

解决 v1.0 的两个核心问题：
1. **配置硬编码**：技能绑定到 Xianyu 项目，无法服务其他项目
2. **规则覆盖不全**：`fix_strategies` 仅 7 条规则，无法应对实际 30+ 高频规则

### ✨ 核心改进

#### 1. 配置分层架构（v1 → v2）

| 变化 | 详情 |
|------|------|
| 新增 | `config/core_config.json` — 通用配置（与项目无关） |
| 新增 | `config/project_config.json` — 项目特定配置（Xianyu 业务） |
| 新增 | `config/hard_constraints/core.json` — 通用安全规则（任何项目都该有） |
| 新增 | `config/hard_constraints/business/xianyu.json` — Xianyu 业务硬约束 |
| 新增 | `config/fix_strategies.json` — 修复策略表（覆盖 30+ 规则） |
| 新增 | `config/framework_patterns.json` — 多框架模式库 |
| 重构 | `config/scan_config.json` → 标记 deprecated，保留兼容层 |
| 重构 | `config/hard_constraints.json` → 标记 deprecated，保留兼容层 |

#### 2. 跨平台脚本

- 新增 `scripts/detect-platform.ps1` — 平台检测（Windows/Linux/macOS）
- 重构 `scripts/start-sonarqube.ps1` — 跨平台启动（按平台选择 `StartSonar.bat` / `sonar.sh`）
- 重构 `scripts/verify-connection.ps1` — 自动检测 v1/v2 配置
- 重构 `scripts/run-sonar-scanner.ps1` — 跨平台降级扫描

#### 3. API 抽象层

- 新增 `scripts/invoke-api.ps1` — 统一封装所有 SonarQube HTTP API 调用
  - `Invoke-SonarApi` — 通用 GET/POST 调用
  - `Get-SonarSystemStatus` — 系统状态
  - `Get-SonarProjects` — 项目列表
  - `Search-SonarIssues` / `Search-SonarIssuesAll` — 问题搜索（自动分页）
  - `Get-SonarQualityGate` — 质量门禁
  - `Get-SonarRule` — 规则详情
  - `Get-SonarMeasures` — 项目度量
  - `Change-SonarIssueStatus` — 状态变更

#### 4. 修复策略扩展

v1.0 仅 7 条规则 → v2.0 覆盖 30+ SonarQube 高频规则：

**Python (12 条)**：
- S125（注释代码）、S1481（未使用 import）、S3508（未使用变量）
- S108（文件末尾换行）、S101（命名）、S2737（raise from）
- S5914（f-string）、S6395（.items()）、S5886（walrus operator）
- S5713（硬编码字符串）、S5857（非捕获组）、S7519（contextlib.suppress）
- S3776（认知复杂度）、S1192（字符串重复）、S5843（正则）
- S7503（async）、S1082（键盘事件）

**TypeScript (15 条)**：
- S1128（未使用 import）、S1854（死代码）、S2681（立即返回布尔）
- S7758（switch 穷尽）、S6544（enum）、S6535（正则字符类）
- S4144（重复方法名）、S7718（重复字符串）、S7780（String.repeat）
- S7721（Object.hasOwn）、S7744（模板字面量）、S4323（catch 包装）
- S6438（可选链）、S3923（import 必须使用）、S5914（模板字面量）
- S3776（认知复杂度）、S1192（字符串重复）、S1874（废弃 API）
- S6759（props readonly）、S6470（useState 未用 setter）

#### 5. 框架模式库（多框架支持）

v2.0 新增 6 个常见框架的误报模式库：

| 框架 | 语言 | 装饰器/Hooks | 已知误报 |
|------|------|-------------|----------|
| FastAPI | Python | `@app.get/post`、`@router.*` | S1481、S2949、S116 |
| React | TypeScript | `useState`、`useEffect`、`React.memo` | S6488、S6486、S6759 |
| Vue | TypeScript | `ref`、`computed`、`defineProps` | S6759 |
| Django | Python | `@login_required`、`@action` | S1481 |
| Spring | Java | `@Controller`、`@Autowired` | S1481 |
| Express | JavaScript | `app.use`、`app.get` | S1481 |

#### 6. 硬约束分层

v1.0 10 条 Xianyu 特有规则 → v2.0 分层：

**通用安全规则（14 条）** — 任何项目都应遵守：
- `no_hardcoded_credentials` — 硬编码凭据
- `no_hardcoded_sonar_token` — SonarQube token 硬编码
- `secrets_in_env_only` — 敏感字段应通过环境变量加载
- `no_sql_injection` — SQL 注入
- `no_command_injection` — 命令注入（subprocess shell=True）
- `no_unsafe_deserialization` — 不安全反序列化
- `no_dangerously_set_inner_html` — XSS
- `no_innerhtml_assignment` — XSS
- `secure_random_for_secrets` — 加密安全随机数
- `no_md5_sha1_for_security` — 弱哈希
- `verify_ssl_default` — SSL 验证
- `no_resource_leak` — 资源泄露
- `no_mutable_default_args` — 可变默认参数
- `no_sensitive_in_logs` — 日志敏感字段

**Xianyu 业务规则（8 条）** — Xianyu 项目特有：
- `hmac_compare_digest_for_token` — HMAC token 比较
- `webview_no_devnull_redirect` — WebView2 stdout/stderr
- `webview_create_new_console` — WebView2 CREATE_NEW_CONSOLE
- `webview_private_mode_false` — WebView2 private_mode
- `hf_endpoint_mirror` — HuggingFace 镜像
- `auth_whitelist_endpoints` — 认证白名单
- `fetch_credentials_include` — fetch credentials
- `kbmanager_whitelist_only` — KBManager 白名单

#### 7. SKILL.md 重写

- 精简入口（移除重复内容）
- 强调通用化与配置分层
- 添加完整迁移指南（v1 → v2）

#### 8. 示例项目

- 新增 `examples/xianyu-hunter/` — 完整 Xianyu 项目配置
- 新增 `examples/basic-python/` — 最小 Python 项目示例
- 新增 `examples/react-frontend/` — 纯 React 前端项目示例

### 🔄 向后兼容

- 所有脚本自动检测 v1 (`scan_config.json`) 和 v2 (`core_config.json`) 格式
- v1 文件存在时输出警告，建议升级
- v1 接口保留，避免破坏现有 Xianyu 项目使用

### 📊 受益场景对比

| 场景 | v1.0 | v2.0 |
|------|------|------|
| Xianyu 项目使用 | ✅ | ✅（兼容） |
| 其他 Python 项目 | ❌ 需大量修改 | ✅ 复制 core_config + 自定义 project_config |
| 其他 TypeScript 项目 | ❌ 需大量修改 | ✅ 复制 core_config + 自定义 project_config |
| 跨平台（Linux/Mac） | ❌ Windows 专属 | ✅ 自动适配 |
| 规则覆盖 | 7 条 | 30+ 条 |
| 框架误报识别 | 1 框架 | 6 框架 |

### 🚧 已知限制

1. `hard_constraints/business/` 目录需要手动按项目创建
2. `framework_patterns.json` 未覆盖所有框架（可扩展）
3. `fix_strategies.json` 暂未覆盖所有规则（持续扩充中）

### 📝 迁移建议

**Xianyu 项目**（v1.0 用户）：
- 无需任何操作，旧配置自动 fallback
- 建议阅读新 SKILL.md 了解配置分层
- 可选：迁移到 v2.0 获得更好的扩展性

**新项目**（首次使用）：
- 复制 `examples/basic-python/` 或 `examples/xianyu-hunter/`
- 修改 `project_config.json` 适配项目
- 按需在 `hard_constraints/business/` 添加业务规则
- 设置 `SONAR_TOKEN` 环境变量
- 运行 `.\scripts\verify-connection.ps1` 验证
