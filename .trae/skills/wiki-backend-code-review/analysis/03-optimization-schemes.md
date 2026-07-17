
## 三、交互优化方案设计

---

### 优化方案 A：分层规则加载 + 规则摘要索引

#### 核心思路
将每个规则文件拆分为"索引层"和"详情层"。SKILL.md 中的 Checklist 只引用索引，仅在真正匹配时才加载对应规则文件的完整内容。

#### 实施方案

**1. 创建规则索引文件（references/.rules-index.md）**
`markdown
# Rules Index

## sse-streaming
- 触发条件: text/event-stream, reply.raw.write, SSE helper
- 规则数: 6 (5 critical, 1 suggestion)
- 核心检查: headers完整性, 事件格式, finally收尾, 错误推送, 禁止reply.send, 统一send函数
- 详情文件: sse-streaming-rule.md

## filesystem-vault
- 触发条件: fs/promises, index.md, log.md, FileStateStore, vault/
- 规则数: 6 (5 critical, 1 suggestion)
- 核心检查: 白名单写入, 路径遍历防护, 并发锁, 部分失败策略, 异步API, 临时文件
- 详情文件: filesystem-vault-rule.md

[... 其他规则的索引条目 ...]
`

**2. 精简规则文件**
- 移除每个规则文件顶部的冗长 Scope 描述（已在索引中）
- 移除重复的 Bad/Good 示例（仅保留最具代表性的 1 个）
- 保留规则描述和 Suggested Fix 的核心文本

**3. 修改 SKILL.md Checklist**
- 将 Checklist 改为先读取索引 → 根据代码特征匹配 → 按需加载详情
- 移除通用规则部分（已由专用规则覆盖）

#### Token 节省估算

| 项目 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| SKILL.md | ~2500 | ~1200 | -1300 |
| 规则文件（3-4个） | ~8000 | ~4000 | -4000 |
| 索引文件 | 0 | ~500 | +500 |
| **合计** | **16300** | **~9700** | **-6600 (-40%)** |

#### 优势
- 规则详情按需加载，避免无关规则消耗 Token
- 索引层极小，增加开销可忽略
- 规则文件精简后更易维护

#### 劣势
- 需要修改所有规则文件格式
- 首次使用需要理解新的索引机制

---

### 优化方案 B：规则内联 + 单一 SKILL.md

#### 核心思路
将所有规则浓缩进一个精简的 SKILL.md，消除多文件读取开销。规则按类别组织，每个规则仅保留一行核心描述 + 一个最小示例。

#### 实施方案

**重构后的 SKILL.md 结构：**
`markdown
---
name: wiki-backend-code-review
description: "Review Fastify + TypeScript backend code..."
---

# Wiki Backend Code Review

## 1. 确定审查模式
[pending-change / snippet / file-focused]

## 2. 读取配置
加载 config/review-config.md 获取目录映射、SSE约定、并发阈值

## 3. 规则检查清单
（每条规则一行核心描述 + 可选"查看详情"标记）

### 3.1 SSE 流式 (sse)
- [C] headers必须完整含X-Accel-Buffering
- [C] 事件格式: event+data双行+\n\n结尾
- [C] finally中必须reply.raw.end()
- [C] 错误通过error事件推送，不可抛异常
- [C] 禁止return reply.send()
- [S] 统一封装send辅助函数

### 3.2 文件系统/Vault (fs)
- [C] 写入路径必须在白名单内，禁止修改SCHEMA.md
- [C] 用户输入路径须正则白名单校验
- [C] 并发追加须withCompileLock串行化
- [C] 部分失败不回滚，标记draft
- [C] 使用fs/promises异步API
- [S] 临时文件用os.tmpdir()+唯一前缀

### 3.3 路由设计 (route)
[... 类似压缩格式 ...]

### 3.4 安全 (security)
[... 类似压缩格式 ...]

[C] = Critical, [S] = Suggestion, [B] = Best Practice

## 4. 输出格式
[精简的 Template A/B]
`

#### Token 节省估算

| 项目 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| SKILL.md | ~2500 | ~1500 | -1000 |
| 规则文件（3-4个） | ~8000 | ~0 | -8000 |
| 配置 | ~2000 | ~2000 | 0 |
| 输出模板 | ~800 | ~400 | -400 |
| **合计** | **16300** | **~3900** | **-12400 (-76%)** |

#### 优势
- 最大的 Token 节省（~76%）
- 单文件结构，零文件读取开销
- 审查启动速度最快

#### 劣势
- 规则详情丢失，复杂规则的理解深度下降
- 单文件维护难度增加
- 新规则添加需要编辑大文件
- 违反"关注点分离"的设计原则

---

### 优化方案 C：智能上下文裁剪 + 动态规则选择

#### 核心思路
保持现有文件结构不变，但在 SKILL.md 中引入"代码特征检测"机制，在读取规则前先分析代码内容，精确选择需要的规则子集。同时优化输出模板。

#### 实施方案

**1. 增强 SKILL.md 的预处理步骤：**
`markdown
## 预处理：代码特征检测
在匹配规则前，先扫描代码中出现的关键词/模式：
- 搜索 "text/event-stream" / "reply.raw.write" → 标记需要 SSE 规则
- 搜索 "fs/promises" / "vault/" → 标记需要文件系统规则
- 搜索 "app.post" / "app.get" / "request.body" → 标记需要路由规则
- 搜索 "process.env" / "path.join" / "execFile" → 标记需要安全规则
- 搜索 "EngineAdapter" / "AsyncIterable" / "yield" → 标记需要 Harness 规则
- 搜索 "reset-config" / "restore" / "updateConfig" → 标记需要配置管理规则
- 搜索 "brand" / "display" / "normalize" → 标记需要数据一致性规则
- 搜索 "invalidate_cache" / "cookie" / "session" → 标记需要会话状态规则

仅加载标记的规则文件，跳过未标记的。
`

**2. 精简输出模板：**
`markdown
## 精简 Template A
# Code Review Summary

## 🚨 Critical (<N> issues)
### 1. <标题>
**File:** path:line
<代码片段，最多3行>
**Issue:** <一句话解释>
**Fix:** <一句话建议>（附代码示例仅当复杂时）

---
[重复...]

## 💡 Suggestions (<N>)
[同上格式]

## 🔧 Nits (<N>)
[同上格式]

## ✅ What's Good
- <正面反馈，最多3条>

[仅在有修复建议时询问]
`

**3. 配置优化：**
- 将 review-config.md 中不常变化的部分（技术栈、预设ID列表）从 prompt 上下文中移除
- 保留动态部分（目录映射、路径规则）

#### Token 节省估算

| 项目 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| SKILL.md | ~2500 | ~2000 | -500 |
| 规则文件（智能选择2-3个） | ~8000 | ~4500 | -3500 |
| 输出模板 | ~800 | ~350 | -450 |
| 配置（精简传输） | ~2000 | ~1200 | -800 |
| **合计** | **16300** | **~10050** | **-6250 (-38%)** |

#### 优势
- 保持现有文件结构，改动最小
- 智能规则选择避免加载无关规则
- 输出模板精简减少输出 Token
- 向后兼容性好

#### 劣势
- 需要模型具备代码特征检测能力（依赖模型理解力）
- 特征匹配可能遗漏边界情况
- 仍需多文件读取

---

### 优化方案 D：配置驱动规则版本 + 最小 SKILL.md

#### 核心思路
创建一个"元配置"文件，定义每种审查场景应加载的规则版本。SKILL.md 缩减为纯调度器，所有规则和配置都通过元配置驱动。

#### 实施方案

**1. 创建 meta-config.yaml（或 .json）：**
`yaml
# meta-config.yaml
scenes:
  sse_review:
    rules: [sse-streaming, error-handling]
    config_sections: [sse_event_format, concurrency_thresholds]
    detail_level: full
  
  filesystem_review:
    rules: [filesystem-vault, security]
    config_sections: [path_traversal_protection, vault_whitelist]
    detail_level: full
    
  full_review:
    rules: [all]
    config_sections: [all]
    detail_level: minimal  # 仅加载规则摘要
    
  quick_review:
    rules: [security, error-handling]
    config_sections: []
    detail_level: minimal
`

**2. 极简化 SKILL.md（~50行）：**
`markdown
---
name: wiki-backend-code-review
description: "Fastify+TypeScript backend reviewer"
---

# Wiki Backend Code Review

## Steps
1. Detect review mode from user input
2. Load meta-config.yaml → determine rule set
3. Load config/review-config.md (selected sections only)
4. Load matched rule files (summary mode for quick_review)
5. Scan code for feature keywords
6. Apply matched rules → compose output
7. Use Template A (condensed) or Template B

## Feature Detection
Scan code for: event-stream, fs/promises, app.(get|post), 
EngineAdapter, reset-config, invalidate_cache, brand/display

## Output (Condensed Template)
# Code Review

## Critical (<N>)
### 1. <title>
**ile:line** | <issue in 1 sentence>
Fix: <1-line suggestion> [code if complex]

## Suggestions (<N>)
[same format]

## What's Good
- <up to 3 points>

[Ask to apply fixes if any critical/suggestion]
`

#### Token 节省估算

| 项目 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| SKILL.md | ~2500 | ~500 | -2000 |
| 元配置 | 0 | ~300 | +300 |
| 规则文件（按需） | ~8000 | ~3000 | -5000 |
| 配置 | ~2000 | ~800 | -1200 |
| 输出模板 | ~800 | ~250 | -550 |
| **合计** | **16300** | **~4850** | **-11450 (-70%)** |

#### 优势
- 高度模块化，规则/配置/调度完全分离
- 支持多种审查粒度（full/quick/minimal）
- 最小 SKILL.md 大幅降低基础 Token 开销
- 易于扩展新规则和新场景

#### 劣势
- 引入新的元配置文件格式
- 需要实现配置解析逻辑
- 规则详情的"minimal"模式可能损失信息
- 实施复杂度最高

---

## 四、方案对比与实施优先级

### 4.1 综合对比

| 维度 | 方案A | 方案B | 方案C | 方案D |
|------|-------|-------|-------|-------|
| **Token 节省** | ~40% | ~76% | ~38% | ~70% |
| **功能完整性** | 完整 | 部分损失 | 完整 | 完整 |
| **输出质量** | 提升 | 下降 | 提升 | 持平 |
| **实施复杂度** | 中 | 低 | 低 | 高 |
| **维护性** | 好 | 差 | 好 | 优秀 |
| **通用性** | 好 | 差 | 好 | 优秀 |
| **可扩展性** | 好 | 差 | 中 | 优秀 |
| **硬编码风险** | 无 | 低 | 无 | 无 |
| **向后兼容** | 中 | 差 | 好 | 中 |

### 4.2 实施优先级建议

#### 第一优先级：方案 C（智能上下文裁剪）
- **理由**：改动最小、收益可观（~38%）、不影响现有结构、保持功能完整性
- **预计实施工作量**：1-2 小时
- **风险**：低

#### 第二优先级：方案 A（分层规则加载）
- **理由**：平衡了 Token 节省（~40%）与维护性，索引机制提供良好的可扩展性
- **预计实施工作量**：3-4 小时
- **风险**：中

#### 第三优先级：方案 D（配置驱动）
- **理由**：长期价值最高（~70%节省 + 优秀可扩展性），但短期实施成本高
- **预计实施工作量**：1-2 天
- **风险**：中-high

#### 不建议优先采用：方案 B
- **理由**：虽然 Token 节省最大，但牺牲了关注点分离、维护性和规则深度，长期不利于技能演进

### 4.3 混合实施路线图

`
阶段1（1-2周）: 实施方案C
  ├─ 增强 SKILL.md 的代码特征检测
  ├─ 精简输出模板
  └─ 验证审查质量不降级

阶段2（2-4周）: 实施方案A
  ├─ 创建规则索引文件
  ├─ 精简规则文件（去重示例）
  └─ 整合 SKILL.md 通用规则

阶段3（1-2月）: 实施方案D（可选）
  ├─ 设计元配置格式
  ├─ 实现场景化规则加载
  └─ 支持多粒度审查模式
`

