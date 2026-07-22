# 主题色变量映射规则（CODING-041 ~ CODING-046）

> 本规则基于「仪表盘最近操作面板与悬浮问答图标主题色适配」复盘提炼。
> 所有参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `theme_color_mapping` 段读取。
> 规则文件本身不硬编码任何具体颜色值、变量名或 alpha 列表。

## 触发场景

- 修改 `.vue` / `.css` / `.scss` 文件中硬编码的 `rgba()` / `rgb()` / `#hex` / `hsl()` 颜色值
- 新增 UI 组件时选择主题变量
- 多主题切换项目下，发现某元素在浅色主题（如 macaron/enterprise/portfolio）下辨识度低
- Code Review 时检查主题色合规性

## CODING-041 主题色变量映射三步法

### 问题

跳过「读变量清单」直接猜测变量名，导致：
- 使用未定义的变量名（Vite 编译警告或样式失效）
- 语义不一致（如把卡片背景硬编码值映射为场景背景变量）
- alpha 值不匹配（如把 `rgba(0, 245, 255, 0.1)` 映射为 `--accent-cyan-a15`）

### 规则

任何主题色硬编码值替换必须按以下三步执行，禁止跳步：

1. **读变量清单**：通过 Grep 查找项目 CSS 变量定义文件，确认可用变量名与 alpha 变体列表
2. **设计映射表**：为每处硬编码生成「原值 → 新变量」映射表，记录语义判断依据
3. **精准替换**：按映射表逐处执行 Edit，禁止使用 Write 重写整个文件

### 判断逻辑

```
IF 硬编码颜色值 ∈ 主题色白名单:
    跳过替换（CODING-042）
ELSE:
    STEP 1: 读取项目 CSS 变量定义文件
    STEP 2: 按 CODING-044 语义优先级选择变量
    STEP 3: 确认 alpha 变体存在（CODING-043）
    STEP 4: Edit 精准替换（CODING-045）
    STEP 5: vue-tsc --noEmit 验证（CODING-046）
```

### 适配新项目

- 读取 `theme_color_mapping.variable_definition_files` 列出的文件确认变量清单
- 若项目无 CSS 变量分层架构，先建立 L1/L2/L3 三层架构再应用此规则

## CODING-042 主题色白名单

### 问题

把 `rgba(255, 255, 255, X)`（白色透明度，所有主题通用）也替换为变量，导致：
- 变量过度抽象，增加维护成本
- 白色透明度本身在不同主题下行为一致，无需变量化

### 规则

以下硬编码颜色值允许保留，不强制替换为 CSS 变量：

| 模式 | 示例 | 允许原因 |
|------|------|---------|
| `rgba(255, 255, 255, X)` | `rgba(255, 255, 255, 0.1)` | 白色透明度所有主题通用 |
| `transparent` | `transparent` | 语义明确，无主题依赖 |
| `inherit` | `inherit` | 继承父级，自动跟随主题 |
| `currentColor` | `currentColor` | 跟随文字颜色，自动跟随主题 |

其他所有 `rgba()` / `rgb()` / `#hex` / `hsl()` 值必须替换为 CSS 变量。

### 判断逻辑

```
IF 硬编码值匹配 theme_color_mapping.whitelist_patterns:
    允许保留，不替换
ELSE:
    必须替换为 CSS 变量
```

### 适配新项目

- 若项目无主题切换需求，所有硬编码颜色均可保留（`theme_color_mapping.enabled = false`）
- 若项目使用 CSS-in-JS（如 styled-components），白名单模式不变，但变量引用方式改为 `theme.xxx`

## CODING-043 alpha 变体命名规范

### 问题

使用项目未定义的 alpha 变体（如 `--accent-cyan-a07`），导致：
- Vite 编译警告 `undefined variable`
- 样式回退到默认值，视觉效果与预期不符

### 规则

alpha 变体变量名必须遵循命名规范：

- 格式：`--accent-{color}-a{NN}`
- `{color}` 为颜色标识（如 `cyan` / `purple` / `pink` / `magenta`）
- `{NN}` 为两位数字的 alpha 百分比，必须从 `theme_color_mapping.allowed_alpha_values` 列表中选取

### 允许的 alpha 值列表

从 `theme_color_mapping.allowed_alpha_values` 读取（默认值见 config 文件）。

### 判断逻辑

```
IF 变量名匹配 --accent-{color}-a{NN}:
    IF {NN} ∈ theme_color_mapping.allowed_alpha_values:
        通过
    ELSE:
        失败：使用未定义的 alpha 变体
ELSE:
    失败：变量名不符合命名规范
```

### 适配新项目

- 若项目使用不同的 alpha 步进（如 5% 步进），修改 `allowed_alpha_values` 列表
- 若项目无 alpha 变体体系，先建立变量定义再应用此规则

## CODING-044 语义变量优先级

### 问题

把场景背景硬编码值映射为卡片背景变量，导致：
- 卡片背景在场景背景上对比度不足
- 主题切换时视觉层次混乱

### 规则

选择 CSS 变量时，必须按以下语义优先级判断：

| 优先级 | 语义场景 | 变量示例 |
|--------|---------|---------|
| 1 | 场景背景（页面级背景） | `--bg-scene` |
| 2 | 卡片背景（卡片/面板背景） | `--bg-card-solid` |
| 3 | 文字颜色（主文字/辅助文字） | `--text-base` / `--text-muted` |
| 4 | 边框颜色 | `--accent-cyan-a15` |
| 5 | 阴影/光晕效果 | `--glow-cyan` |
| 6 | 滚动条颜色 | `--accent-cyan-a20` / `--accent-cyan-a40` |

### 判断逻辑

```
STEP 1: 判断硬编码值的语义用途
        - 页面背景 → --bg-scene
        - 卡片/面板背景 → --bg-card-solid
        - 文字 → --text-base / --text-muted
        - 边框 → --accent-{color}-a15
        - 阴影/光晕 → --glow-{color}
        - 滚动条 → --accent-{color}-a20/a40
STEP 2: 若语义不明确，按上下文判断
        - 元素是 body/html/main → 场景背景
        - 元素是 .card/.panel/.glass-card → 卡片背景
        - 元素是 .text/.label/.title → 文字
        - 元素是 .border/.divider → 边框
        - 元素是 box-shadow → 阴影
        - 元素是 ::-webkit-scrollbar → 滚动条
```

### 适配新项目

- 若项目使用不同的语义分层（如 Material Design 的 surface/background），修改 `theme_color_mapping.semantic_priority` 列表
- 若项目无光晕效果（`--glow-*`），从优先级表中移除该项

## CODING-045 编辑工具选择原则

### 问题

使用 Write 工具重写整个 `.vue` 文件，导致：
- 中文注释被破坏为 GBK 字节（Write 工具编码不稳定）
- 未修改的代码也被重写，增加 git diff 噪音
- 难以 review，无法定位具体修改点

### 规则

修改含非 ASCII 字符的文件时，必须遵循工具选择优先级：

1. **首选**：Edit 工具精准替换（`old_string` → `new_string`）
2. **次选**：多次 Edit 调用，每次替换一处
3. **禁止**：Write 工具重写整个文件（除非文件为纯 ASCII 或新建文件）

### 判断逻辑

```
IF 文件含非 ASCII 字符（中文/日文/韩文等）:
    IF 修改范围 < 文件总行数 50%:
        使用 Edit 精准替换（CODING-045）
    ELSE:
        分多次 Edit，每次替换一个逻辑块
ELSE:
    可使用 Write 重写（但仍推荐 Edit）
```

### 适配新项目

- 若项目所有源文件均为纯 ASCII，可放宽此规则
- 若项目使用 prettier/eslint 强制格式化，Edit 后需运行格式化命令确保一致性

## CODING-046 类型检查双重门禁

### 问题

仅运行前端类型检查，导致：
- 后端类型变更未同步前端，运行时 API 契约不匹配
- 后端 types.ts 新增字段未同步前端 types.ts，前端访问 undefined

### 规则

代码修改涉及类型变更时，必须执行双重类型检查门禁：

1. **后端门禁**：`tsc --noEmit`（退出码必须为 0）
2. **前端门禁**：`vue-tsc --noEmit`（退出码必须为 0）

两个检查均通过才允许提交。

### 判断逻辑

```
IF 修改涉及 .ts 文件（后端）:
    运行 theme_color_mapping.backend_typecheck_command
    IF 退出码 != 0:
        失败：后端类型检查未通过
IF 修改涉及 .vue / .tsx 文件（前端）:
    运行 theme_color_mapping.frontend_typecheck_command
    IF 退出码 != 0:
        失败：前端类型检查未通过
IF 两者均通过:
    允许提交
```

### 适配新项目

- 纯 React 项目：`frontend_typecheck_command` 改为 `npx tsc --noEmit`
- 纯后端项目：跳过前端门禁
- monorepo：各子项目独立运行类型检查

## 复盘记录

### 成功执行任务的完整步骤

1. **问题定位**：明确 `.recent-log` 使用 `rgba(5, 0, 16, 0.6)` 深色背景在 macaron/enterprise/portfolio 浅色主题下显示不协调
2. **读取变量清单**：通过 Grep 查找项目 CSS 变量定义（`--neon-*` / `--bg-*` / `--text-*` / `--accent-*-aXX` / `--glow-cyan`）
3. **识别白名单**：确定 `rgba(255, 255, 255, X)` / `transparent` / `inherit` / `currentColor` 为允许硬编码
4. **选择替换变量**：为每个硬编码颜色选择语义匹配的 CSS 变量
5. **执行 Edit**：精确替换每一处硬编码
6. **验证**：运行 `vue-tsc --noEmit` 类型检查确认退出码为 0

### 不确定性与失败点

1. **变量名记忆不准确**：alpha 变体（a06/a08/a10/a12/a15/a20/a25/a30/a35/a40/a45/a50/a60/a70）具体哪些被定义，需先查文件确认
2. **语义变量选择**：`rgba(10, 10, 20, 0.85)` 是映射为 `--bg-card-solid` 还是 `--bg-scene`？需根据语义判断
3. **glow 效果变量**：`box-shadow` 中的 `rgba(0, 245, 255, 0.3)` 该用 `--accent-cyan-a30` 还是 `--glow-cyan`？需查项目是否定义了 glow 专用变量
4. **Write 工具隐患**：重写整个文件可能以非 UTF-8 编码保存导致中文乱码

### 可抽象的固定流程

「先建立可用变量白名单，再设计映射表，最后精准替换」三步法。

### 适用场景

- 任何使用 CSS 变量分层架构的项目（L1/L2/L3）
- 多主题切换项目（至少 2 个主题）
- Vue/React 组件中硬编码 `rgba()`/`#hex` 颜色需迁移为变量的场景

### 不适用场景

- 单主题项目（无主题切换需求，硬编码颜色不会因主题变化产生冲突）
- 第三方库内部样式（无法控制其变量体系）
- 一次性脚本样式（如动画关键帧中临时使用的颜色）
- 设计稿原型阶段（颜色频繁变动，变量化反而增加维护成本）
- CSS 变量未定义的项目（需先建立变量体系再应用此流程）
