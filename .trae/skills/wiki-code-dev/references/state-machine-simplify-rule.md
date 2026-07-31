# 状态机简化原则规则（CODING-058）

> 复盘来源：问答页侧栏三态折叠（expanded→collapsed→hidden）需点击两次才能完全折叠，用户需求"折叠一步到位"。简化为二态（expanded↔hidden）后，一次点击即完全折叠，减少状态空间与测试覆盖成本。
> 所有可变参数从 `config/coding-standards-config.md` 的 `state_machine_simplify` 字段读取，禁止在规则文件中硬编码状态名或阈值。

## 触发场景

- UI 组件状态切换需多步操作（如三态折叠需点击两次）
- 状态枚举存在冗余中间态（如 expanded→collapsed→hidden 中 collapsed 为中间过渡态）
- 用户反馈"操作步骤过多"、"点击次数太多"
- 状态机测试覆盖成本高（3 态需 6 次切换测试，2 态仅需 2 次）

## 规则

### SMS-1：多态枚举能简化为二态时优先简化

当状态枚举存在可合并的中间态时，必须简化为更少的状态数：
- **三态→二态**：如 `expanded | collapsed | hidden` → `expanded | hidden`（collapsed 作为过渡态无独立业务价值）
- **四态→二态**：如 `idle | loading | success | error` → `idle | done`（当 loading/success/error 可合并为 done 时）

简化条件：
1. 中间态无独立业务价值（如 collapsed 仅显示图标，无独立功能）
2. 用户需求明确要求"一步到位"
3. 简化后 UX 无退化（如折叠态仍可通过其他方式访问功能）

### SMS-2：状态切换函数避免嵌套三元

状态切换函数禁止使用嵌套三元表达式（触发 `S3358` 警告），必须用单层三元或 if/else：

```typescript
// 禁止：嵌套三元（S3358）
const next = state === 'a' ? 'b' : state === 'b' ? 'c' : 'a';

// 必须：单层三元（二态）或 if/else（多态）
const next = state === 'expanded' ? 'hidden' : 'expanded';
// 或
let next: State;
if (state === 'expanded') next = 'hidden';
else next = 'expanded';
```

### SMS-3：简化后必须删除废弃状态的 UI 和样式

状态简化后，必须同步删除废弃状态的所有引用：
- 模板中的 `v-if="state === 'collapsed'"` 分支
- 样式中的 `.collapsed` 修饰符
- 脚本中的 `collapsed` 类型字面量
- 测试用例中的 collapsed 态测试

### SMS-4：简化后必须更新快捷键与注释

状态机简化后，必须同步更新：
- 快捷键处理函数的注释（如 "三态循环切换" → "二态切换"）
- 状态类型定义的注释（如 "三态：expanded/collapsed/hidden" → "二态：expanded/hidden"）
- 相关 emit 事件的类型声明

## 设计流程

```
识别多态状态机
   ↓
1. 评估每个状态是否有独立业务价值
   ↓
2. 识别可合并的中间态（无独立功能、仅过渡用途）
   ↓
   有可合并态 → 简化为更少状态
   无可合并态 → 保留原状态机
   ↓
3. 更新类型定义（type SidebarState = 'expanded' | 'hidden'）
   ↓
4. 简化切换函数（单层三元或 if/else）
   ↓
5. 删除废弃状态的 UI（v-if 分支）+ 样式（.collapsed）+ 脚本（类型字面量）
   ↓
6. 更新快捷键与注释
   ↓
7. Grep 搜索废弃状态名，确认无残留引用
   ↓
8. vue-tsc + E2E 测试验证
```

## 适用场景

- 侧栏折叠（三态→二态）
- 面板展开/收起（多步向导→一步切换）
- 抽屉/模态框（三态→二态）
- 任何中间态无独立业务价值的状态机
- 用户反馈"操作步骤过多"的场景

## 不适用场景

- 业务逻辑必须的多态（如 `pending | loading | success | error` 四态各有独立 UI）
- 异步流程状态机（如 `idle | fetching | success | error` 必须区分 fetching 与 error）
- 有明确业务语义的三态（如 `未开始 | 进行中 | 已完成`）
- 状态间有严格顺序依赖（如必须 A→B→C 不能跳转）

## 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `state_machine_simplify.max_state_count` | `2` | 简化后的最大状态数（二态优先） |
| `state_machine_simplify.forbidden_switch_syntax` | `nested-ternary` | 禁止的状态切换语法 |
| `state_machine_simplify.require_cleanup` | `true` | 简化后是否必须删除废弃状态引用 |
| `state_machine_simplify.require_comment_update` | `true` | 简化后是否必须更新注释 |
| `state_machine_simplify.stale_state_threshold` | `0` | 废弃状态引用容忍阈值（0=零容忍） |
