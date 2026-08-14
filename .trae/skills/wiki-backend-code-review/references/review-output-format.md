# 审查结果输出格式（Review Output Format）

> 本文件定义 wiki-backend-code-review 的结构化审查结果模板。所有规则文件输出的 findings 须遵循此格式，便于人类快速分级与追踪。严重级别定义与 `config/review-config.md` 的 `severity_critical` / `severity_warning` / `severity_suggestion` / `severity_positive` 一致。
>
> 本格式为呈现层约定，不改变任何规则判定逻辑；规则文件本身不硬编码严重级别文案。

## 严重级别图例（Severity Legend）

| 图标 | 级别 | 含义 | 是否阻断合并 |
|------|------|------|--------------|
| 🔴 Critical | 严重 | 安全漏洞 / 路径穿越 / 硬编码密钥 / ESM 接线断裂 / 前后端类型漂移（type-drift）等会导致运行失败或泄露的问题 | 是，必须修复 |
| 🟡 Warning | 警告 | 隐私 / 持久化边界 / 契约不匹配（contract-mismatch）/ 配置可移植性等应修复但不立即阻断的问题 | 建议修复 |
| 🟢 Suggestion | 建议 | 最佳实践 / nit / 可选优化 | 可选 |

> 具体每条 finding 的严重级别由对应规则在 `config/review-config.md` 中定义的 `severity_*` 参数决定（如 `rate_limit_resilience.severity_br063_1`）。

## 单条发现格式（Per-finding Format）

每条 finding 严格按以下字段顺序呈现，字段间用 `|` 分隔：

```
File:line | Rule code | Severity | Problem | Fix | Verification | Applicability
```

- **File:line**：触发文件绝对/相对路径 + 行号（如 `api/src/routes/media.ts:42`）。
- **Rule code**：对应规则编号（如 `BR-063-1`、`BR-064-2`）。
- **Severity**：从图例取 🔴/🟡/🟢。
- **Problem**：一句话描述问题本质（避免堆代码，必要时附代表性片段）。
- **Fix**：建议修复动作（可附最小代码示例引用，不在正文内联大段代码）。
- **Verification**：验证修复是否生效的命令/步骤（如 `git check-ignore -v <path>`、`npx tsc --noEmit`、单测名）。
- **Applicability（可选）**：该规则在此改动上的**适用 / 不适用**边界标注（如 `适用：多用户写端点；不适用：纯公开只读 API`），与 wiki-code-dev 复盘维度④对齐；纯适用场景可省略。

### 配置化与泛化维度（Config-driven & Generalization）

凡涉及「硬编码字面量（超时/路径/端口/阈值/白名单）/ 非泛化特判（`if (kind==='x')`）/ 配置可移植性」的发现，须显式标注为**配置化/泛化**类问题，并指向 `config/review-config.md` 的对应参数键（如 `timeout.edge_tts_ms`、`compress.min_bytes`、`scan_dirs`），而非在 finding 中内联具体数值。严重级别沿用既有图例（硬编码密钥=🔴 Critical；硬编码阈值/可移植性=🟡 Warning），但**修复动作一律要求改为配置键引用**，支撑跨业务泛化（对应 CODING-CONFIG-DRIVEN / J-CONFIG-FIRST）。

### 示例

```
api/src/routes/media.ts:88 | BR-063-1 | 🔴 Critical | 限流键直接用 request.ip，反向代理下取到代理 IP，限流对所有用户共享一桶 | 从 X-Forwarded-For 最左非信任跳取真实客户端 IP（trusted_proxy_hop=1） | 单测注入 XFF 头断言限流键为真实 IP
frontend/src/types.ts:30 | BR-062-1 | 🟡 Warning | 后端 done 事件新增 governor/threadId，前端 DoneEvent 未同步，消费时为 undefined | 同 PR 给 DoneEvent 加 governor?: string; threadId?: string | 跨文件比对 api/src/types.ts 与 frontend/src/types.ts 字段
```

## 结尾区块（Mandatory Sections）

每次审查输出在 findings 之后须包含：

### ✅ What's Good（优点）

列出本次变更中做得好的点（正面反馈），至少 1 条；若无则写"本次无特别亮点"。例如：
- 限流值全部从 config 读取，无硬编码。
- done 事件新字段已加法且可选，向后兼容。
- 新增规范以配置组形式接入（registry），引擎主流程零改动，泛化性好。

### 📐 适用性说明（Applicability）

在 findings 之后、Verdict 之前，用 1-2 句说明本次变更范围内各规则的**适用 / 不适用**边界（与 wiki-code-dev 复盘维度④一致）。例如：
- `BR-ISOLATION`：本次改动含多个写端点，守卫注入适用；纯公开只读 API 不适用，已排除。
- `BR-091`（压缩默认关闭）：本次未启用压缩，不适用，仅作配置合规性确认。
此区块确保评审结论不把"规则噪声"误判为缺陷，也明确哪些规则在本题面下被主动跳过。

### 总体结论（Overall Verdict Line）

一行总结，明确是否可合并：

```
Verdict: 🔴 BLOCKED — N 个 Critical 须修复后方可合并。  /  🟡 NEEDS FIX — M 个 Warning 建议修复。  /  🟢 APPROVED — 无阻断项，可合并。
```

## 与既有模板的关系

- 前端 SKILL.md 的 Template A / Template B 仍用于前端 pending-change / file-targeted 评审。
- 本格式作为后端结构化 findings 的统一渲染约定，可与后端既有"按类别分组"输出并存：先按严重级别（🔴→🟡→🟢）分组，组内按规则类别排序，每条 finding 用上述 `File:line | ...` 行呈现，最后追加 ✅ What's Good 与 Verdict。
