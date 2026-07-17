# Wiki-Backend-Code-Review 技能全面分析与 Token 优化方案

## 一、技能全面能力梳理

### 1.1 基本信息

| 属性 | 值 |
|------|------|
| 技能名称 | wiki-backend-code-review |
| 文件总数 | 11 个文件 |
| 总行数 | ~1385 行 |
| 总大小 | ~86.8 KB |
| 语言 | 中文（规则描述）+ 英文（代码示例/数据结构） |
| 目标技术栈 | Fastify 4.x + TypeScript (ES2022/ESM) |

### 1.2 文件组织结构

`
wiki-backend-code-review/
├── SKILL.md                          # 技能入口（~178行）
├── config/
│   └── review-config.md             # 集中配置（~225行）
└── references/
    ├── sse-streaming-rule.md        # SSE 流式规则（~152行）
    ├── filesystem-vault-rule.md     # 文件系统/Vault 规则（~170行）
    ├── route-design-rule.md         # 路由设计规则（~148行）
    ├── harness-integration-rule.md  # Harness 集成规则（~154行）
    ├── security-rule.md             # 安全规则（~112行）
    ├── error-handling-rule.md       # 错误处理规则（~132行）
    ├── session-state-rule.md        # 会话状态规则（~111行）
    ├── data-consistency-rule.md     # 数据一致性规则（~123行）
    └── config-management-rule.md    # 配置管理规则（~130行）
`

### 1.3 核心功能模块

#### 功能一：多模式审查触发
- **待变更审查**：检查暂存区/工作树文件
- **代码片段审查**：审查粘贴的代码片段
- **文件定向审查**：审查指定文件/目录

#### 功能二：智能路由匹配（Checklist 机制）
根据审查范围自动匹配相关规则文件：
1. SSE 流式输出 → sse-streaming-rule.md
2. 文件系统/Vault 操作 → filesystem-vault-rule.md
3. 路由设计 → route-design-rule.md
4. Harness 集成 → harness-integration-rule.md
5. 安全 → security-rule.md
6. 配置管理 → config-management-rule.md
7. 配置恢复 → config-management-rule.md
8. 数据一致性 → data-consistency-rule.md
9. 会话状态/缓存一致性 → session-state-rule.md
10. 默认通用规则（安全/性能/代码质量/测试）

#### 功能三：分级问题输出
- **Critical（必须修复）**：安全问题、正确性问题、可靠性问题
- **Suggestions（应该考虑）**：可维护性、最佳实践
- **Nits（可选）**：小改进建议
- **What's Good**：正面反馈

#### 功能四：配置集中管理
- 技术栈定义
- 项目目录映射
- SSE 事件格式约定
- 并发控制阈值
- 路径遍历防护规则
- Vault 写入白名单
- 临时文件策略
- 预设 ID 列表
- 密钥存储命名规范
- 热更新安全要求

### 1.4 规则统计

| 规则文件 | 规则数 | Critical | Suggestion | Best Practice |
|----------|--------|----------|------------|---------------|
| SSE 流式 | 6 | 5 | 1 | 0 |
| 文件系统/Vault | 6 | 5 | 1 | 0 |
| 路由设计 | 5 | 4 | 1 | 0 |
| Harness 集成 | 6 | 6 | 0 | 0 |
| 安全 | 5 | 5 | 0 | 0 |
| 错误处理 | 5 | 5 | 0 | 0 |
| 会话状态 | 7 | 0 | 0 | 7 |
| 数据一致性 | 8 | 0 | 0 | 8 |
| 配置管理 | 5 | 3 | 2 | 0 |
| 通用规则 | 4组 | - | - | - |
| **合计** | **57+** | **33** | **5** | **15+** |

### 1.5 输入参数

| 参数 | 来源 | 说明 |
|------|------|------|
| 审查模式 | 用户指令 | pending-change/snippet/file-focused |
| 审查范围 | 用户提供 | 文件路径/代码片段/暂存区 |
| 配置参数 | review-config.md | 从配置文件动态读取 |
| 规则匹配 | Checklist | 根据代码特征自动路由 |

### 1.6 输出成果

1. 结构化审查报告（Template A/B）
2. 每个问题包含：文件路径+行号、代码片段、解释、建议修复
3. 可选：是否应用修复的后续询问
