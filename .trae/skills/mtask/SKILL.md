***

name: "mtask"
description: "通过 mtask MCP 按序查询、处理、回传待办任务（含 Txxxx 编号任务）。当用户指令含「mtask」「待办」「执行并回传」「按顺序处理」或引用任务编号时触发。"
whenToUse: "用户要求用 mtask MCP 查询/执行/处理/回传待办任务，或引用 Txxxx 任务编号要求执行并回传结论时"
triggers: "mtask | 待办 | 处理任务 | 回传任务 | 按顺序处理待办 | Txxxx任务编号 | 执行并回传"
------------------------------------------------------------------

# mtask —— 待办任务处理 Skill

通过 `mtask` MCP 服务器，把外部任务系统（MTask）中的待办任务（`status=todo`）按序处理、回传结论文档、并标注完成。该 Skill 沉淀了「查询清单 → 澄清范围 → 逐条判归属/判可落地 → 实际执行 → 回传结论 → 完成标注」的完整工作流，以及回传文档的输出标准。

## 职责

- 用 mtask MCP 列出并解析待办任务清单。

- 对每条任务判定「是否归属当前工作区」「当前环境能否真正落地」。

- 在可落地的任务上完成实际排查/修复，并输出结构化结论文档。

- 把结论文档写入任务「处理结果」字段，并在通过验证后把任务标记为完成。

- 对跨项目/缺环境的任务如实标注「不可在本环境落地」，不做伪修复。

## 触发场景

- 用户说：`mtask 执行 T00224 并回传`。

- 用户说：`mtask 按顺序处理待办任务`。

- 用户说：`处理待办` / `回传任务` / `把结果回传到 mtask 对应任务并标注完成`。

- 用户引用形如 `Txxxx` 的任务编号并要求执行/回传。

## 执行步骤（固定流程）

### 0. 连接检查

先调用一次 `mtask_list_tasks`（或 `mtask_get_task`）探测 MCP 可用性。

- 若返回 `list tools failed` 等 server 级错误（同一 server 所有工具都不可用），说明服务器未连接/端点不可达，**重试 1–2 次**；仍失败则**停止并告知用户需要重新连接/授权 mtask**，不要反复调用或假装成功。

- 关于 tts/超时：工具箱本轮长任务的 MCP 输出可能很大，交由 `scripts/list-todo.ps1` 解析，避免直接读原始文本。

### 1. 获取清单并排序

- `mtask_list_tasks({})` 拉取全部任务（含各项目）。

- 返回是**双层嵌套 JSON 字符串**（外层是 MCP 文本包装，内层才是任务数组），需二次解析；优先交给 `scripts/list-todo.ps1`。

- 筛选 `status == 'todo'`，按 `task_no` 数值**升序**排列作为处理顺序。

### 2. 澄清范围（关键防空转）

- 明确用户意图：`处理全部待办` 还是 `仅某条 Txxxx`。

- 当清单**跨多个项目**、且部分不在当前工作区时：**用 AskUserQuestion 让用户确认范围**，默认只处理「与当前工作区 `project_id` 一致」的待办，其余保持待办不动。

- 不要默默选择一种解释就开始；不确定就询问（见 `references/4-scope-judgement.md`）。

### 3. 逐条处理（按 task\_no 升序）

对每条任务执行：

1. `mtask_get_task({taskNo})` 读取 title / description / project\_id / status。
2. **归属判定**：`project_id` 与当前项目一致才落地；不一致 → 标记「跨项目不可在本环境落地」，跳过或告知用户。
3. **可落地判定**：当前工作区有代码/环境可修改才「真修复」；只有模板性描述或依赖外部测试环境 → 输出评估/说明，不做伪修复（见 `references/4-scope-judgement.md`）。
4. **执行**：在代码库完成修改，并做基本自检（类型检查 / 构建 / 单测）。
5. **回传**：`mtask_update_task_result({taskNo, result})` 写入 Markdown 结论文档（模板见 `assets/result-template.md`）。
6. **（可选）运行验证**：存在运行环境时实测；把实测证据补充进 result（见 `references/3-output-standard.md`）。

### 4. 完成标注

- 仅当任务「已完成实际修改/评估」且「已回传结论文档」（必要时含实测验证）时，才 `mtask_update_task({taskNo, status:'done', verified:true})`。

- 否则保持 `status='todo'` / `verified=false`，并说明原因。

- 完成标注前若用户要求「先验证」，需先给用户看验证结论，再标注完成。

### 5. 汇总汇报

向用户给出每条的：**根因 / 修复（文件路径）/ 验证 / 状态**，并注明哪些任务未处理及其原因。

## 输出标准

详见 `references/3-output-standard.md`。要点：

- **回传字段** **`result`** 为 Markdown，结构固定：

  ```markdown
  ## 根因
  ...
  ## 影响范围
  ...
  ## 修复
  ...（含文件绝对路径与改动点）
  ## 验证
  ...（实测证据 / 命令 / 结论）
  ```

- **完成标注判定**：能给出可核验的修复 + 验证才置 `done`；仅做了书面探讨且无法验证的不置完成。

- **诚实边界**：跨项目 / 外部环境的任务，必须标注「不可在本环境落地」，绝不伪执行或伪造结论。

## 复盘要点（实际踩过的坑）

1. **双层嵌套 JSON**：MCP 返回文本是 `The MCP server responded with: [{"type":"text","text":"<inner-json>"}]`，内层才是任务数组；直接用文本提取按需二次 `ConvertFrom-Json`。
2. **Read 工具读不到大/特殊编码文件**：任务清单文件用 PowerShell `Get-Content -Raw` 读取解析，不要依赖 Read 工具直接读它。
3. **`list tools failed`** **是连接问题**：是整层工具枚举失败，不是参数错误；重试或让用户修连接。
4. **跨项目甄别**：根据每条任务的 `project_id` 判断归属；同是待办可能分属不同项目，混在一起处理会误改非本项目的代码。
5. **不擅自改生产配置**：排查/修复以展示层与必要代码为主，不擅动 AI 服务实际配置；改前先列明约束。

## 适用场景 / 不适用场景

**适用**：

- mtask MCP 已连接，任务以 `Txxxx` 编号存在、需「排查/修复 + 结论回传 + 完成标注」。

- 待办归属当前可访问的工作区（project\_id 匹配），可实际读取代码、修改并自检。

- 任务体量可拆为逐条独立处理的单元。

**不适用**：

- mtask MCP 未连接 / 未授权（无法读取任务）。

- 任务依赖人工施测、外部系统或大量实时数据，Agent 无法在本会话独立闭环。

- 用户要求纯只读（不改任何文件）时，不做修复只出结论。

- 任务横跨多个互不相关仓储且无对应环境/凭据，只能输出书面评估。

## 相关文件

- 清单解析脚本：`scripts/list-todo.ps1`

- 回传/结论文档模板：`assets/result-template.md`

- 配置项：`config/config.yaml`

- 详细 reference：

  - `references/1-listing-parsing.md`

  - `references/2-handling-workflow.md`

  - `references/3-output-standard.md`

  - `references/4-scope-judgement.md`

