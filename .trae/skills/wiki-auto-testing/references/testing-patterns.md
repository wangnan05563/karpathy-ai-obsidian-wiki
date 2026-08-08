# 测试模式与复盘提炼

> 本文档从 SKILL.md 拆分而来，含持久化层/系统清理/Async可靠性/配置一致性/热更新/降级机制/目录结构/v3媒体生成/端到端编排 共 10 个测试复盘章节。
> 当测试流程遇到特定模块问题或需要参考历史测试模式时按需加载。
> SKILL.md 入口文件保留章节导航链接。

## 持久化层测试（复盘提炼）

> 本节步骤类型基于持久化数据丢失问题的修复验证复盘提炼，所有参数从 `config.persistence_tests` 读取，不在代码中硬编码业务端点或攻击向量。

### 适用场景

- 后端新增持久化资源（配置、会话、文件落盘）后的回归测试
- 涉及缓存机制修改后的缓存刷新验证
- 涉及 HTTP 路由参数到文件系统映射的安全验证
- 涉及前后端数据同步、降级策略的容错验证

### 不适用场景

- 纯 UI 样式修改（用现有 `responsive_check` 即可）
- 纯 prompt 文本修改
- 纯构建配置修改

### 测试编排示例

在 `config.yaml` 的 `test_plan.phases` 中编排持久化测试步骤：

```yaml
test_plan:
  phases:
    persistence:
      steps:
        - type: persistence_crud_test
          resource: "conversations"
        - type: path_traversal_test
          resource: "conversations"
        - type: fallback_degradation_test
          api_patterns:
            - "/api/conversations"
          expected_behavior: "no-crash"
```

### 验证逻辑

| 步骤类型 | 验证点 | 通过条件 |
|---------|--------|---------|
| persistence_crud_test | PUT 创建 → GET 读取 → PUT 更新 → GET 验证更新（缓存刷新）→ DELETE → GET 确认删除 | 6 步全部通过，特别验证 PUT 后立即 GET 返回新值 |
| path_traversal_test | 遍历 `malicious_ids` 逐个请求 | 全部返回 4xx（5xx 或 200 均视为失败） |
| fallback_degradation_test | 拦截 API 返回 503，前端加载页面 | body 仍可见（不崩溃）|

## 系统清理模块测试（复盘提炼）

> 本节步骤类型基于系统清理模块 Playwright 前端验证复盘提炼，所有参数从 `config.encoding_tests`、`config.dangerous_action_tests`、`config.service_lifecycle`、`config.cleanup` 读取，不在代码中硬编码页面、表单、选择器或攻击向量。

### 适用场景

- Windows 中文环境下，页面 tab 标签或表单标签可能编码乱码的回归测试
- 有危险操作（dry_run/二次确认/danger 样式）的清理类模块
- 多表单独立状态管理（每表单独立 loading/result）的模块
- 测试前需停止旧服务、测试后需清理临时脚本的场景

### 不适用场景

- 纯静态 HTML 页面（用 `responsive_check` 即可）
- 移动端 App 测试
- 无前端界面的纯 API 测试

### 测试编排示例

在 `config.yaml` 的 `test_plan.phases` 中编排系统清理模块测试步骤：

```yaml
test_plan:
  phases:
    cleanup_module:
      steps:
        - type: service_lifecycle
          stop_old_process: true
        - type: encoding_check
          check_pages: ["dashboard", "cleanup"]
        - type: dangerous_action_test
          test_pages:
            - key: "cleanup"
              forms:
                - key: "compileCache"
                  has_days_input: false
                  default_dry_run: true
        - type: multi_form_test
          test_pages:
            - key: "cleanup"
        - type: temp_cleanup
          cleanup_dirs: ["."]
```

### 验证逻辑

| 步骤类型 | 验证点 | 通过条件 |
|---------|--------|---------|
| encoding_check | 遍历 `check_pages` 中每个页面的 `scan_selectors`，dump DOM 文本码点 | 不含 `fffd_codepoint`（默认 `0xFFFD`），即无替换字符 |
| dangerous_action_test | dry_run 默认开启 → 关闭 dry_run 出现 danger 样式 → 点击触发二次确认 → 取消不发请求 → 确认执行成功 | 全部断言通过，特别验证"取消"路径不发请求 |
| multi_form_test | 每个 `form_container_selector` 独立显示 loading 和 result | 表单 A 的 loading 不影响表单 B，结果互不污染 |
| service_lifecycle | 停止旧进程 → 启动后端/前端 → 轮询端口 Listen | 所有 `required_ports` 在 `startup_timeout_ms` 内进入 Listen 状态 |
| temp_cleanup | 按 pattern 匹配并删除临时文件 | 删除过程中无异常，残留文件计数为 0 |

## Async 可靠性测试（复盘提炼）

> 本节基于浏览器登录 91s 超时复盘提炼，验证 async/await + IPC 场景的可靠性。所有参数从 `config.async_reliability_tests` 读取，不在代码中硬编码检查模式或阈值。

### 子阶段 3.6：Async 可靠性静态检查（可选）

仅在 `async_reliability_tests.enabled: true` 时执行：

1. **超时防护检查**（`timeout_protection.enabled: true`）：
   - 按配置的 `pattern` 扫描未包裹超时的 await 调用
   - 排除 `whitelist_pattern` 中的白名单调用
   - 验证违规调用是否被 `required_wrapper` 包裹
   - 命中违规 → 标记为 `severity` 级别（critical/warning/suggestion）

2. **心跳线程实现检查**（`heartbeat_reliability.enabled: true`）：
   - 检查心跳是否使用 `forbidden_in_heartbeat` 中禁止的异步实现
   - 验证是否使用 `required_impl`（如 threading.Thread）
   - 验证状态文件 ts 字段更新独立性（是否在 `required_context` 内）

3. **兜底数据检查**（`fallback_data.enabled: true`）：
   - 扫描超时后的异常处理分支
   - 验证是否包含 `forbidden_actions`（如 raise、pass）
   - 验证是否包含 `required_action`（如 fallback_data_assignment）

### 子阶段 5.5：Async 可靠性运行时验证（可选）

仅在 `async_reliability_tests.runtime_verification.enabled: true` 时执行：

1. 启动子进程（如 browser_login.py）
2. 监控状态文件 ts 字段更新间隔
3. 若间隔 > `max_gap_sec`（默认 10s）→ 测试失败
4. 可选：模拟 IPC 阻塞，验证心跳线程仍能更新 ts

### 测试报告格式

Async 可靠性测试结果必须包含以下字段：

```
## Async 可靠性测试报告
- CODING-021 超时保护：✅/❌（N 处违规）
- CODING-022 心跳线程实现：✅/❌（心跳使用 asyncio.Task 违规）
- CODING-023 状态文件更新独立性：✅/❌（ts 更新间隔最大 Xs）
- CODING-024 兜底数据：✅/❌（N 处超时后无兜底）
- CODING-025 多层超时：✅/❌（仅单层超时）
```

详细的测试方法、模拟阻塞模板和覆盖矩阵见 [async-reliability-testing.md](async-reliability-testing.md)。

## 配置一致性验证（复盘提炼）

> 基于历史配置读取不一致问题复盘提炼，验证所有入口使用统一的配置读取函数。

仅在 `verification.config_consistency_check.enabled: true` 时执行：

### 验证流程

1. 修改 config.json 中的配置项（如 apiKey）
2. 重启服务
3. 调用 GET /api/ai/config 验证返回值是否反映新配置
4. 调用 POST /api/ai/test-connection 验证是否使用新配置
5. 如果结果不一致，说明存在配置读取不一致问题

### 判断标准

- config.json 中的值 == GET 接口返回的值 == 测试连接使用的值

## 热更新闭环验证（复盘提炼）

> 基于保存配置后运行实例未同步更新问题复盘提炼，验证保存配置后运行实例是否同步更新（无需重启）。

仅在 `verification.hot_update_verification.enabled: true` 时执行：

### 验证流程

1. 记录当前配置状态（GET /api/ai/config）
2. 保存新配置（PUT /api/ai/config）
3. 不重启服务，立即调用 GET /api/ai/config 验证返回值
4. 调用 POST /api/ai/test-connection 验证使用的是新配置
5. 恢复原始配置

### 判断标准

- 保存后 GET 返回新值（无需重启）
- 保存后测试连接使用新值（无需重启）

## 降级机制验证（复盘提炼）

> 基于无效 API Key 场景复盘提炼，覆盖正常路径和降级路径。

仅在 `verification.degradation_verification.enabled: true` 时执行：

### 验证流程

1. 正常路径：配置有效 API Key，验证 LLM 问答正常
2. 降级路径：配置无效 API Key，验证降级为检索模式
3. 兜底路径：服务不可用时，验证兜底提示

### 判断标准

- 正常路径：LLM 问答正常，无降级标记
- 降级路径：显示降级提示信息
- 兜底路径：显示服务不可用提示

测试用例在 `verification.degradation_verification.test_cases` 中配置，每条包含 `name`、`simulate`（模拟方式）和 `expected`（期望行为）。

## 目录结构验证测试（复盘提炼）

> 基于 P0/P1/P2 目录结构优化复盘提炼，覆盖 .gitignore 规则、目录结构完整性、脚本引用完整性、类型检查回归四个子项。所有参数从 `config.structure_verification` 读取，不在代码中硬编码路径、命令或模式。

仅在 `structure_verification.enabled: true` 时执行。**目录结构变更后的强制回归测试**（在阶段 5 补充测试中执行），覆盖 .gitignore 规则匹配、文件迁移后的目录结构、脚本引用无残留旧名、TypeScript 类型检查四个维度。

### 子阶段 5.6：.gitignore 规则验证测试

#### 测试目标
验证更新 .gitignore 后，目标规则正确匹配预期文件，且已跟踪文件已从 git 索引移除（避免 .gitignore 对已跟踪文件不生效的陷阱）。

#### 测试步骤
1. 遍历 `gitignore_target_patterns` 中的每个模式
2. 对每个模式执行 `gitignore_verify_command`（如 `git check-ignore -v`），验证规则匹配
3. 对每个匹配的文件执行 `gitignore_tracked_check`（如 `git ls-files --error-unmatch`），检查是否仍被跟踪
4. 若仍被跟踪，按 `gitignore_untrack_command`（如 `git rm --cached`）移除索引
5. 验证移除后 `gitignore_tracked_check` 返回非零退出码（即已不被跟踪）

#### 预期结果
- 所有 `gitignore_target_patterns` 都被 .gitignore 规则匹配
- 所有匹配的文件都已从 git 索引移除（`git ls-files` 不再列出）
- .gitignore 工作树状态干净（无未提交的索引变更残留）

#### 失败处理
- 规则不匹配：检查 .gitignore 语法（路径分隔符、通配符、前导斜杠语义）
- 已跟踪未移除：执行 `gitignore_untrack_command` 移除索引，验证 .gitignore 对该文件生效
- 移除后仍被跟踪：检查 global .gitignore 或 .git/info/exclude 是否有冲突规则

### 子阶段 5.7：目录结构完整性测试

#### 测试目标
验证文件迁移后目录结构完整，运行时数据与源码分离（避免运行时数据污染源码目录导致 git 仓库膨胀与跨环境不一致）。

#### 测试步骤
1. 验证 `expected_source_dirs` 中每个源码目录存在
2. 验证 `expected_data_dir`、`expected_docs_dir`、`expected_scripts_dir` 存在
3. 遍历 `forbidden_mixing_patterns`，对每个 `pattern` 用 Glob/Grep 检测是否命中
4. 命中即判定为运行时数据与源码混合（违反分离原则）
5. 输出违规路径列表及对应 `reason`

#### 预期结果
- 所有预期目录存在
- 无 `forbidden_mixing_patterns` 命中（运行时数据未混入源码目录）
- 源码目录、运行时数据目录、文档目录、脚本目录各司其职

#### 失败处理
- 预期目录缺失：检查文件迁移是否遗漏，补全目录创建
- 命中禁止混合模式：将运行时数据迁移到 `expected_data_dir`，从源码目录移除
- 重复检查迁移后状态，直到无禁止模式命中

### 子阶段 5.8：脚本引用完整性测试

#### 测试目标
验证文件重命名后无残留旧名引用（避免脚本运行时找不到文件导致 ENOENT）。

#### 测试步骤
1. 对每次文件重命名，将旧文件名作为 `script_rename_grep_pattern`
2. 执行 `script_rename_verify_command`（如 `git grep`）搜索旧名引用
3. 排除 .git 历史与备份文件（仅扫描工作树）
4. 命中即判定为残留引用
5. 输出命中文件列表与行号

#### 预期结果
- 工作树中无任何旧文件名引用
- 所有引用都已更新为新文件名
- `git grep` 退出码为 1（即未找到匹配）

#### 失败处理
- 命中残留引用：逐个更新引用为新文件名
- 排除合法引用（如 CHANGELOG、迁移日志）后再次验证
- 重复检查直到 `git grep` 无匹配

### 子阶段 5.9：类型检查回归测试

#### 测试目标
验证文件迁移/路径变更后 TypeScript 类型检查通过（避免 import 路径断裂导致运行时 undefined）。

#### 测试步骤
1. 遍历 `typecheck_working_dirs` 中每个工作目录（如 `backend` / `frontend`）
2. 在对应工作目录执行 `typecheck_commands` 中的命令（如 `npx tsc --noEmit`）
3. 捕获命令退出码与 stdout/stderr
4. 退出码非零即判定为类型检查失败
5. 解析输出中的错误行号与错误信息

#### 预期结果
- 所有 `typecheck_commands` 退出码为 0
- 无 TS2xxx / TS6xxx 错误（特别是 "Cannot find module" 与 "Cannot find name"）
- 类型检查报告无新增错误（与基线对比）

#### 失败处理
- TS2307 Cannot find module：检查 import 路径是否在迁移后更新，修正相对路径或 alias
- TS2503 Cannot find namespace：检查 types.ts 是否迁移到新位置，更新引用
- 其他类型错误：按错误信息逐个修复，修复后重新运行 `typecheck_commands`

## v3 媒体生成工具测试（复盘提炼）

> 本节基于 v3 媒体生成工具（PPT/图像/视频）开发过程的四维度复盘提炼，覆盖外部 API 集成契约、超时分级、归档 frontmatter、长任务状态机、外部 API 不可达降级五个子阶段。
> 所有参数从 `config.media_generation_tests` 读取，不在代码中硬编码端点、超时阈值、状态枚举或错误消息。
> 对应 wiki-code-dev 的 CODING-056/057/059/060/061/063/064/065 编码规范。
> 与已存在的 `v3_media_tests` 配置块互补：`v3_media_tests` 侧重 API 路由可达性，本配置块侧重编码规范层面的契约/超时/归档/状态机/降级验证。

### 适用场景

- 调用外部 API（如 Agnes Image/Video API、OpenAI 兼容接口）的媒体生成功能
- 涉及长任务（视频生成、批量处理等）的前端轮询 + 状态机 UI
- LLM 生成产物（图像/PPT/视频/播客）归档到 vault 的 frontmatter 标准化验证
- 外部 API 不可达时的降级策略验证（禁止硬编码"后端服务未运行"）
- SSE 流式消费 + AbortController 主动取消的错误处理验证

### 不适用场景

- 纯本地 LLM 调用（无外部 API 集成，外部 API 契约验证不适用）
- 秒级同步任务（无长任务轮询，状态机验证不适用）
- 无归档需求的临时查询（frontmatter 标准化验证不适用）

### 子阶段 5.15：外部 API 集成契约验证（可选）

> 对应 CODING-056 外部 API 集成契约。验证 fetchWithDiagnostics 包装 + 字段双重路径兼容 + 类型显式转换。

仅在 `media_generation_tests.external_api_contract.enabled: true` 时执行：

1. 遍历 `test_endpoints` 中配置的端点（image/ppt/video_creation/video_polling）
2. 对每个端点按 `body_template` 从 `test_payloads` 取请求体发起请求
3. 验证响应字段双重路径兼容（`data.url || data.metadata?.url`），应对外部 API 字段路径变更
4. 验证调用方后端语言要求的字段类型已显式转换（如 Go 后端 string 类型用 `String(value)`）
5. 验证 `require_fetch_wrapper: true` 时源码中使用了 `fetchWithDiagnostics` 包装（便于单元测试）
6. 按 `diagnostic_error_codes` 映射验证错误码翻译（ENOTFOUND → DNS 解析失败 等）

### 子阶段 5.16：超时分级验证（可选）

> 对应 CODING-057 超时分级策略。验证不同任务类型使用不同超时阈值。

仅在 `media_generation_tests.timeout_tier_verification.enabled: true` 时执行：

1. 按 `verify_method`（默认 `grep_abort_signal_timeout`）扫描 `scan_directories` 中的源码
2. 提取所有 `AbortSignal.timeout(ms)` 调用，记录超时值与所在函数/任务类型
3. 与 `expected_tiers` 比对：task_creation=30s / task_polling=30s / image_generation=60s / video_download=120s / llm_short_context=60s / llm_long_context=180s
4. `forbidden_uniform_timeout: true` 时，所有调用用同一超时值即判定失败
5. 输出超时分级报告（任务类型 → 实际超时值 → 期望超时值 → 是否匹配）

### 子阶段 5.17：归档 frontmatter 验证（可选）

> 对应 CODING-060 媒体归档 Markdown frontmatter 标准化。验证归档到 vault 的 LLM 生成产物字段完整。

仅在 `media_generation_tests.archive_frontmatter_check.enabled: true` 时执行：

1. 扫描 `archive_dir`（默认 `karpathy-wiki/data/vault/queries`）下的所有归档文件
2. 解析每个文件的 YAML frontmatter，验证 `required_fields`（type/output_mode/generated_at）齐全
3. 验证 `type` 字段值为 `expected_type_value`（默认 `query`）
4. 验证 `output_mode` 字段值在 `expected_output_modes` 枚举内（image/ppt/video/podcast）
5. 验证 `generated_at` 字段匹配 `generated_at_pattern`（ISO8601 格式）
6. 验证文件名匹配 `filename_pattern`（`<output_mode>-YYYYMMDD-HHmmss.<ext>`）
7. `validate_filename_mode_consistency: true` 时验证文件名前缀与 frontmatter output_mode 一致
8. 按 `business_fields_by_mode` 验证业务字段（如 video 必须含 video_file/task_id/source_url 之一）

### 子阶段 5.18：长任务状态机覆盖验证（可选）

> 对应 CODING-065 长任务轮询 UI 模式。验证前端长任务 5 状态机完整覆盖 + 定时器清理 + abortReason 三态。

仅在 `media_generation_tests.long_task_state_machine.enabled: true` 时执行：

1. 遍历 `test_views` 中配置的页面（如 `query`）
2. 验证状态机覆盖 `required_states` 全部 5 态（idle/queued/processing/completed/failed）
3. 对每个状态，检查 UI 中有对应的 `state_ui_selectors` 元素（或 `data-state` 属性）
4. `require_timer_cleanup: true` 时验证 `setInterval` 在 `onBeforeUnmount` 中 `clearInterval` 配对
5. `require_close_reset_split: true` 时验证"关闭对话框"与"重置状态"拆为两个函数（停轮询+关对话框 vs 停轮询+清状态）
6. `single_failure_no_abort: true` 时验证轮询单次失败仅更新 error 文案，不终止轮询
7. `require_settimeout_for_abort: true` 时验证超时用 `setTimeout` 而非 `AbortSignal.timeout`（因需同步设 abortReason）
8. 验证 `required_abort_reasons` 三态（user/timeout/null）区分用户停止/超时/正常完成
9. 失败时 `screenshot_on_fail: true` 截图取证

### 子阶段 5.19：外部 API 不可达降级测试（可选）

> 对应 CODING-056 错误码翻译 + CODING-064 SSE 流消费错误处理。验证外部 API 不可达时前端不崩溃。

仅在 `media_generation_tests.external_api_unavailable.enabled: true` 时执行：

1. 按 `simulate_method`（默认 `intercept_request`）拦截 `intercepted_endpoints` 中的端点
2. 拦截响应 `response_status`（默认 503），让前端走错误处理路径
3. 等待 `wait_after_intercept_ms`（默认 2000ms）让前端处理完错误
4. 验证 `expected_behavior: no_crash`（前端 body 仍可见，不白屏）
5. 验证错误消息分类正确：按 `expected_error_classification`（网络超时/DNS 失败/连接拒绝/证书错误）匹配
6. 验证不出现 `forbidden_error_messages`（后端服务未运行/未知错误/请稍后重试）等硬编码统一提示
7. `require_abort_error_swallow: true` 时验证 SSE 流消费函数吞掉 AbortError（`err.name === 'AbortError'` 直接 return）
8. `require_no_abort_pollution: true` 时验证 errorMessage 状态未被 AbortError 污染
9. `require_reader_cancel_finally: true` 时验证 finally 中 `reader.cancel()` 兜底释放
10. 失败时 `screenshot_on_fail: true` 截图取证

### 测试编排示例

在 `config.yaml` 的 `test_plan.phases` 中编排 v3 媒体生成工具测试步骤：

```yaml
test_plan:
  enabled_phases:
    - "build"
    - "startup"
    - "basic"
    - "interactions"
    - "supplementary"
    - "summary"
    - "media_generation"  # 新增 v3 媒体生成工具测试阶段

media_generation_tests:
  enabled: true
  external_api_contract:
    enabled: true
    test_endpoints:
      - name: "video_creation"
        method: "POST"
        path: "/api/media/video"
        expected_status: [200, 202]
        required_response_fields: ["taskId"]
```

### 验证逻辑

| 步骤类型 | 验证点 | 通过条件 |
|---------|--------|---------|
| external_api_contract_check | 端点契约 + 字段双重路径 + 类型转换 + 错误码翻译 | 全部端点契约通过，fetchWithDiagnostics 已包装，错误码翻译完整 |
| timeout_tier_check | 超时分级 + 禁止统一超时 | 各任务类型超时值匹配 expected_tiers，无统一超时 |
| archive_frontmatter_check | frontmatter 字段 + 文件名模式 + 业务字段 | 所有归档文件字段完整，文件名匹配模式，业务字段齐全 |
| long_task_state_machine_check | 5 态覆盖 + 定时器清理 + abortReason 三态 + 关闭/重置拆分 | 状态机完整，定时器配对清理，超时用 setTimeout |
| external_api_unavailable_test | 拦截 503 + 不崩溃 + 错误分类 + AbortError 吞掉 | 前端不崩溃，错误消息分类正确，无硬编码统一提示 |

## v2 导航栏改造测试复盘（2026-07-22）

> 本节基于 v2 导航栏改造（折叠/展开双模式 + 12 图标导航）的 E2E 测试执行过程复盘，提炼可复用的固定流程与失败模式。

### 成功执行任务的完整步骤

| 步骤 | 操作 | 验证点 | 对应协议 |
|------|------|--------|----------|
| 1 | 端口监听检查（3000/5173） | 两端口均处于 Listen 状态 | Pre-flight Check |
| 2 | 健康检查（GET /health） | HTTP 200 响应 | Pre-flight Check |
| 3 | 浏览器启动检查（about:blank） | Playwright 环境可用 | Pre-flight Check |
| 4 | 停止占用端口的旧进程 | 无残留 cmd.exe / node.exe 占用端口 | Service Management |
| 5 | 启动后端 + 前端服务 | 端口在 startup_timeout_ms 内就绪 | Service Management |
| 6 | 执行阶段 1-6 测试用例 | 全部断言通过 | 标准流程 |
| 7 | 失败时按错误消息模式分类 | 输出对应修复建议 | Failure Classification |
| 8 | selector_not_found 自动触发同步检查 | 检测 git diff 选择器变更 | Test Case Sync |
| 9 | 测试后清理残留进程 | 无日志重定向 cmd.exe 残留 | Service Management |

### 不确定性与失败点

1. **ERR_CONNECTION_REFUSED**：服务未启动或启动未完成时，所有用例报连接拒绝 → 已由 Pre-flight Check 协议在测试入口拦截
2. **选择器失效**：v2 改造删除/重命名了 `.tab-btn` / `.nav-toggle` 等选择器后，旧测试用例引用失效 → 已由 Test Case Sync 协议在阶段 5 检测
3. **静默吞错**：测试用例 except 分支用 `pass` 吞掉异常，导致用例"假通过" → 已由 Test Case Sync 协议的 silent_failure_forbidden 检测
4. **端口冲突**：旧服务未停止即启动新服务，导致新服务绑定端口失败 → 已由 Service Management 协议的 stop_old_process 预防
5. **日志重定向残留**：`pnpm run dev > log.txt 2>&1` 产生的 cmd.exe 残留进程占用资源 → 已由 Service Management 协议的 cleanup_residual 清理

### 可抽象的固定流程

#### 前置检查流程（Pre-flight Check Flow）

```
端口检查 → 健康检查 → 浏览器检查 → (失败) 自动启动服务 → 轮询端口 → 通过/中止
```

该流程与具体业务无关，可作为所有 E2E 测试的统一入口。

#### 测试同步流程（Test Case Sync Flow）

```
git diff 选择器变更 → Grep 测试文件引用 → 命中失效引用 → 检测静默吞错 → 同 commit 验证 → 失败/通过
```

该流程与具体页面无关，可作为所有代码变更后的测试同步验证。

### 适用场景

- v2 导航栏改造后的回归测试（折叠/展开切换、12 图标导航、tooltip、localStorage 持久化）
- 服务重启或端口变更后的环境就绪验证
- 代码变更涉及 DOM 选择器删除/重命名时的测试同步检查
- 测试失败原因不明确时按错误消息模式自动分类
- 长时间测试流程中的服务生命周期管理

### 不适用场景

- 纯静态 HTML 页面（无服务启动需求，Pre-flight Check 仅需浏览器检查）
- 无 git 仓库的项目（Test Case Sync 的 git diff 扫描不适用）
- 单次性临时测试（Service Management 的残留清理不必要）
- 已知失败原因明确无需分类的场景（Failure Classification 的分类开销不必要）

## 端到端测试/部署/冒烟编排（复盘提炼，第十轮）

> 本模式基于「类型门禁→单测→全量→构建(全新目录)→部署(全新目录)→干净重启(杀孤儿 :3000)→冒烟」的固定交付顺序提炼（详见 testing-process-review.md 第十轮）。**所有参数从 `config.yaml` / `defaults.yaml` 读取，不在步骤中硬编码命令、路径、端口或门禁值**，从而适配不同业务项目与沙箱策略（如 safe-delete fail-closed 的「写全新目录」约束）。

### 适用场景

- 前后端分离 + SPA 静态伺服 + 多用户（BYOK / 会话隔离）的前端应用交付回归
- 沙箱环境下受 safe-delete 钩子限制（清空/覆盖已存在目录被 EPERM）的构建/部署
- 后端有改动需确保「干净重启」避免孤儿进程伺服旧代码的场景
- CI 端到端交付门禁（类型→单测→全量→构建→部署→冒烟 全绿才放行）

### 不适用场景

- 纯后端无 SPA 伺服（无需部署/冒烟 SPA 环节，走 `backend_logic_unit_test` 即可）
- 纯静态无构建页面
- 无沙箱限制可自由覆盖目录的环境（「写全新目录」约束不适用，但仍建议全链路门禁）
- 单测即可覆盖的纯逻辑改动（不需全链路编排）

### 关键判断（来自第十轮 维度三）

- **P1 固定顺序门禁**：`typecheck → unit → full-suite → build(fresh dir) → deploy(fresh dir) → 杀孤儿 :3000 → 重启 → 冒烟`；任一阶段红则停，不进入下一步。
- **P2 写全新目录**：构建与部署一律产出**全新目录**，绝不覆盖/清空已存在目录（safe-delete fail-closed 适配）。
- **P3 干净重启**：后端有改动必须 `netstat` 取真实 PID → `taskkill` → 端口 FREE → 起新进程；不依赖后台任务回收状态（孤儿 :3000 会导致 `EADDRINUSE` 且跑旧代码）。
- **P4 冒烟三类门禁**：① 缺必需密钥请求 `400` 不回落服务端共享（BYOK）；② SSE 端点 `200` 流式；③ `:3000/` 伺服 SPA 且为最新时间戳目录。
- **P5 隔离纪律（第九轮）**：隔离测试用唯一 userId 命名空间 + 多轮 `setTimeout(0)` flush，禁用 `beforeEach deleteDatabase`。

### 测试编排示例（配置驱动，零硬编码）

端到端交付顺序「类型门禁 → 单测 → 全量 → 构建(全新目录) → 部署(全新目录) → 干净重启 → 冒烟」中，**前三道门禁由技能标准流程与项目测试运行器执行（配置驱动，不在技能内硬编码命令）**，后四步落地为动态引擎 `test_plan.phases` 的真实步骤类型。所有参数从 `config.yaml` / `defaults.yaml` 读取。

```yaml
# 前三道门禁（技能标准「前端验证」+ 项目测试运行器，零硬编码）
frontend_verification:
  enabled: true
  typecheck_enabled: true
  typecheck_command: "node_modules/vue-tsc/bin/vue-tsc.js --noEmit"   # 仅卡前端类型（不卡后端 pre-existing tsc errors）
  build_enabled: true
  build_command: "node_modules/vite/bin/vite.js build"
  build_out_dir: "/tmp/kw-dist"      # 全新输出目录，规避 safe-delete 拦截
# 单测 / 全量（vitest 等）由项目测试运行器或 CI 管理，不在本技能硬编码

# 后四步：动态引擎阶段（步骤参数全部来自下方配置块）
test_plan:
  phases:
    e2e_delivery:
      steps:
        # 4. 构建产物验证（构建命令来自 frontend_verification.build_command）
        - type: build_artifact_check
          bundle_directory: "/tmp/kw-dist"     # 对应 frontend_verification.build_out_dir
          required_http_status: 200
          key_strings: ["<项目关键字符串>"]     # 对应 build_artifact_check.key_strings 配置
          abort_on_fail: true
        # 5. 部署写全新目录（_deploy_live.mjs <新构建目录> → api/public_live_<ts>）+ 重启后端
        - type: spa_live_deploy_check
          live_base_dir: "api"                 # spa_live_deploy_check.live_base_dir
          live_dir_pattern: "public_live_"     # spa_live_deploy_check.live_dir_pattern
          complete_marker: ".deploy-complete"  # spa_live_deploy_check.complete_marker
          asset_prefix: "/wiki/"               # spa_live_deploy_check.asset_prefix
          restart_required: true               # 部署后必须重启后端才生效
          abort_on_fail: true
        # 6. 干净重启：杀孤儿 :3000 → 端口 FREE → 起新进程
        - type: service_manage
          action: stop
          required_ports: [3000]               # 来自 service 端口配置
        - type: service_manage
          action: start
          required_ports: [3000]
          abort_on_fail: true
        # 7. 冒烟三类门禁
        - type: byok_per_user_override_check   # 缺必需密钥 → 400 不回落服务端共享（读 byok_per_user_override 配置块）
        - type: api_check                      # SSE 端点 200 流式
          path: "/api/query"                   # 来自 api_tests 端点配置
          expected_status: 200
        - type: api_check                      # SPA 根路由 200（后端静态伺服最新 public_live_<ts>）
          path: "/"
          expected_status: 200
```

> 切换项目只需改 `config.yaml` / `defaults.yaml` 中的上述配置块（如 `live_base_dir` / `build_out_dir` / `byok_per_user_override.require_key_fields` / `api_tests`），无需改步骤定义，满足通用性与无硬编码要求。后端有改动时步骤 5-7 必跑；纯前端改动可保留 1-4 + 7 的 SPA 伺服冒烟。

## 归档路由响应分支覆盖（复盘提炼，第十二轮）

> 本模式基于「归档路由重构（7 条规范）」经验提炼：**路由对"合法请求的不同业务结果"（主路径 / 回退 / 空内容）与"非法输入"（非法 threadId / 非整数 messageIndex / 缺失 messageIndex / 非法 ts）各有差异化状态码语义，类型检查 / 构建 / 端点冒烟全过却仍潜伏**。用 `route_response_branch_coverage` 步骤类型逐分支断言 `expected_status` 并校验 200 响应含必需字段，把"响应分支覆盖 + 静默缺陷回归"判断逻辑落地。**所有路由 / 方法 / 分支用例 / 判定从 `config.yaml` 读取，不在步骤中硬编码**。

### 适用场景

- 按 `threadId + messageIndex + ts` 等派生存储键检索内容的归档 / 历史路由
- 对"合法请求的不同业务结果"有差异化状态码语义的路由（主路径 200 / 回退 404 / 空内容 400）
- 沙箱无浏览器环境下的路由行为级验证（配合 `app.inject` 或真实 HTTP 断言）
- CI 路由分支门禁（逐分支状态码 + 200 字段校验固化为流水线）

### 不适用场景

- 单分支无歧义路由（所有非法输入已被框架 / 中间件统一拦截为 4xx 且无需逐分支语义）：沿用 `api_check` / `path_traversal_test`
- 纯前端 / 纯文档改动（走第十轮前端验证链或静态检查）

### 关键判断（来自第十二轮 维度三）

- **P1 逐分支状态码断言**：主路径 200 / 回退 404 / 非法 threadId 400 / 非整数 messageIndex 400 / 缺失 messageIndex 400 / 非法 ts 200（当前回退实现）/ 空内容 400，每个分支独立 `expected_status`。
- **P2 200 分支须校验必需字段**：对 200 响应断言 `content` / `refs` 等 `required_fields` 存在，防"状态码对但内容缺"。
- **P3 非法输入真实构造**：用例用真实非法值（`..%2f..` / `abc` / `not-a-number` / `""`），断言 4xx，不依赖框架默认拦截假设。
- **P4 参数随行为演进**：`expected_status` 配置化（如非法 ts 修复为 RangeError 拦截后由 200 改 400），不写死业务值。
- **P5 配套静态守卫**：派生键碰撞（追加随机后缀）/ refs `\n` 拼接（wikilink 完整性）/ 空内容 no-op 用 `backend_review_static_check` 针对性 grep；前后端门控同步用 `capability_gating_sync`（FR-076）思路同 commit 放宽。

### 测试编排示例（配置驱动，零硬编码）

```yaml
# route_response_branch_coverage 配置块（来自 defaults.yaml / config.yaml）
route_response_branch_coverage:
  enabled: true
  route_name: "/api/threads/:threadId/archive"   # 支持 :param 路径占位符
  method: "GET"
  branch_cases:
    - name: "valid_main_path"
      params: { threadId: "<valid>", messageIndex: "0", ts: "<valid_ts>" }
      expected_status: 200
      required_fields: ["content", "refs"]        # 200 分支校验响应含必需字段
    - name: "fallback_no_content"
      params: { threadId: "<valid>", messageIndex: "0", ts: "<valid_ts>" }
      expected_status: 404                        # 无归档内容回退
    - name: "illegal_thread_id"
      params: { threadId: "..%2f..", messageIndex: "0", ts: "<valid_ts>" }
      expected_status: 400
    - name: "non_integer_message_index"
      params: { threadId: "<valid>", messageIndex: "abc", ts: "<valid_ts>" }
      expected_status: 400
    - name: "missing_message_index"
      params: { threadId: "<valid>", ts: "<valid_ts>" }
      expected_status: 400
    - name: "illegal_ts"
      params: { threadId: "<valid>", messageIndex: "0", ts: "not-a-number" }
      expected_status: 200                        # 当前回退实现；修复为 RangeError 拦截后改 400
    - name: "empty_content"
      params: { threadId: "<valid>", messageIndex: "0", ts: "<valid_ts>", content: "" }
      expected_status: 400                        # no-op 落盘防护
  timeout_ms: 120000

# 动态引擎阶段（步骤参数全部来自上述配置块）
test_plan:
  phases:
    archive_route:
      steps:
        - type: route_response_branch_coverage    # 读 route_response_branch_coverage 配置块
          force: false                            # 随 enabled 开关
```

> 切换项目只需改 `config.yaml` / `defaults.yaml` 中的 `route_response_branch_coverage` 配置块（如 `route_name` / `branch_cases` / `required_fields`），无需改步骤定义，满足通用性与无硬编码要求。
