# NOSONAR 抑制注释位置规则

> **单一信息源**：本文件是 NOSONAR 位置判断的单一可信源。配置驱动的位置规则表见 `config/fix_strategies.json -> nosonar_position_rules`。本文件提供背景、原理与决策树，子代理修复时优先查表，本文件用于理解为何要查表。

---

## 背景

SonarQube 的 `# NOSONAR` 抑制注释能让分析器忽略该行的问题，但有一个关键限制：**必须放在问题所在物理行的末尾**。不同 SonarQube 规则报问题时的物理行不同，例如：

- S107（参数过多）报的是**第一个参数所在行**，不是 `def` 行
- S7483（timeout 参数）报的是 **timeout 参数所在行**，不是 `def` 行
- S125（注释代码）报的是**被识别为代码的注释行**
- S5850（正则优先级）报的是**正则赋值行**

如果 NOSONAR 放错了行，扫描后 OPEN 数不会下降，需要二次修复。

---

## 核心原则

| 原则 | 说明 |
|------|------|
| 大小写 | 必须是大写 `# NOSONAR`，不能是 `# nosonar` 或 `# NOsonar` |
| Python 注释格式 | 用 `# NOSONAR`（井号 + 空格 + NOSONAR） |
| TypeScript/JavaScript 注释格式 | 用 `// NOSONAR`（双斜杠 + 空格 + NOSONAR） |
| JSX 标签内部 | 用 `/* NOSONAR */`（标签外仍用 `// NOSONAR`） |
| Vue 文件分区 | `<template>` 用 `<!-- NOSONAR -->`，`<script>` 用 `// NOSONAR` 或 `/* NOSONAR */`，`<style>` 用 `/* NOSONAR */` |
| WXML 文件 | 用 `<!-- NOSONAR -->`（HTML 注释语法） |
| WXSS 文件 | 用 `/* NOSONAR */`（CSS 注释语法） |
| 多行函数定义首行规则 | Python 多行函数定义时，NOSONAR 必须加在 `def func(` 行尾，**不能**加在 `-> ReturnType:` 行尾 |
| 必须在注释中 | NOSONAR 必须在 `#` 或 `//` 注释中，在 docstring 字符串内**不生效** |
| SonarQube 不识别 `# noqa` | Python 的 `# noqa` 是 flake8 指令，SonarQube 默认不识别 |
| 物理行精确匹配 | NOSONAR 必须在 SonarQube 报告的 `issue.line` 所在物理行末尾 |

---

## 决策树

```
子代理修复一个 OPEN issue 时：

1. 查 fix_strategies.json -> nosonar_position_rules 表
   ├─ 找到 rule_pattern 匹配的条目
   │   ├─ position = "issue_line"              → 在 issue.line 末尾追加 NOSONAR
   │   ├─ position = "first_param_line"        → 在函数第一个参数所在行末尾追加 NOSONAR
   │   ├─ position = "multiline_def_first_line" → 在多行函数定义的 def 行末尾追加 NOSONAR
   │   ├─ position = "n/a"                     → 该规则不需要 NOSONAR，用其他方式修复
   │   └─ 未找到                               → 用默认规则（position = "issue_line"）
   │
2. 确定注释格式（查 core_config.json -> frontend_comment_syntax.mappings）
   ├─ Python                          → # NOSONAR
   ├─ .js / .ts                       → // NOSONAR（标签外）或 /* NOSONAR */（标签内）
   ├─ .vue <template>                 → <!-- NOSONAR -->
   ├─ .vue <script>                   → // NOSONAR 或 /* NOSONAR */
   ├─ .vue <style> / .wxss / .css     → /* NOSONAR */
   ├─ .wxml / .html                   → <!-- NOSONAR -->
   ├─ JSX 标签内                      → /* NOSONAR */
   └─ 其他                            → 查 frontend_comment_syntax.mappings 表
   │
3. 多行函数定义首行规则（Python 专项）
   ├─ 如果是 Python 且 NOSONAR 所在行是 )->ReturnType:  → ❌ 错误
   │   └─ 移动到 def func( 行尾
   └─ 如果 NOSONAR 所在行是 def func(  → ✅ 正确
   │
4. 检查 NOSONAR 是否在有效位置
   ├─ 在 # 或 // 注释中              → ✅ 有效
   ├─ 在 docstring 字符串内           → ❌ 无效，需先转为 # 注释
   └─ 在普通字符串内                  → ❌ 无效
   │
5. NOSONAR 抑制 vs 代码修复决策（查 nosonar_decision_matrix）
   ├─ rule in must_fix_rules          → ❌ 必须代码修复，禁止 NOSONAR
   ├─ rule in can_suppress_rules      → ✅ 允许 NOSONAR，但需附带原因注释
   └─ rule 未在矩阵中                 → 默认允许 NOSONAR
   │
6. 修复后扫描验证
   ├─ OPEN 数下降                   → ✅ NOSONAR 生效
   └─ OPEN 数未下降                  → ❌ NOSONAR 位置错误，按 failure_recovery -> nosonar_not_effective 重新放置
```

---

## 高频规则位置速查表

> 完整数据源：`config/fix_strategies.json -> nosonar_position_rules`

| 规则 | position | 说明 | 示例 |
|------|----------|------|------|
| python:S107 | first_param_line | 报第一个参数行，不是 def 行 | `def foo(\n    x: int,  # NOSONAR\n    y: int\n):` |
| python:S7483 | issue_line | 报 timeout 参数行 | `async def f(self, loc, timeout: float = 0.8) -> None:  # NOSONAR` |
| python:S125 | issue_line | 报被识别为代码的注释行；docstring 起始行需先转为 # 注释 | `# 暂停状态描述  # NOSONAR` |
| python:S5850 | issue_line | 报正则赋值行 | `content = re.sub(r'...', '', content)  # NOSONAR` |
| python:S1172 | n/a | 通过重命名 _ 前缀解决，不需要 NOSONAR | `def f(_started_at: datetime):` |
| typescript:S6551 | issue_line | 报模板字符串插值行；typeof 收窄后仍误报用 // NOSONAR | `typeof v === 'object' ? JSON.stringify(v) : String(v) // NOSONAR` |
| typescript:S6754 | issue_line | 报 useState 调用行；已正确解构仍误报用 // NOSONAR | `const [mode, setMode] = useState<ThemeMode>(() => { // NOSONAR` |
| typescript:S6848 | issue_line | 报非原生交互元素行；拖放容器用 /* NOSONAR */ | `<div /* NOSONAR - 拖放容器非交互元素 */>` |
| *（默认） | issue_line | 未在表中显式列出的规则，NOSONAR 放在 issue.line 末尾 | - |

---

## 常见错误与修复

### 错误 1：NOSONAR 放在 def 行但规则报参数行

**错误示例（python:S107）**：

```python
def foo(  # NOSONAR  ← 错误：S107 报的是参数行不是 def 行
    x: int,
    y: int,
):
```

**正确示例**：

```python
def foo(
    x: int,  # NOSONAR  ← 正确：放在第一个参数所在行
    y: int,
):
```

### 错误 2：NOSONAR 在 docstring 内

**错误示例（python:S125 报在 docstring 起始行）**：

```python
"""批量采集执行历史领域数据访问  # NOSONAR  ← 错误：NOSONAR 在字符串内不生效

提供批量采集历史的保存、查询、更新等方法。
"""
```

**正确示例**：

```python
# 批量采集执行历史领域数据访问  # NOSONAR  ← 正确：先转为 # 注释
"""
提供批量采集历史的保存、查询、更新等方法。
"""
```

### 错误 3：使用小写 NOSONAR

**错误示例**：

```python
timeout: float = 0.8,  # nosonar  ← 错误：必须大写
```

**正确示例**：

```python
timeout: float = 0.8,  # NOSONAR  ← 正确：大写
```

### 错误 4：使用 Python # noqa

**错误示例**：

```python
def foo(  # noqa: S107  ← 错误：SonarQube 默认不识别 # noqa
    x: int,
):
```

**正确示例**：

```python
def foo(
    x: int,  # NOSONAR  ← 正确：SonarQube 原生抑制注释
):
```

### 错误 5：JSX 标签内用 // NOSONAR

**错误示例**：

```tsx
<div // NOSONAR  ← 错误：JSX 标签内不能用 // 注释
  onClick={...}
>
```

**正确示例**：

```tsx
<div /* NOSONAR - 拖放容器非交互元素 */
  onClick={...}
>
```

### 错误 6：多行函数定义 NOSONAR 加在返回类型行

**错误示例**：

```python
async def process_data(
    self,
    items: list[dict],
    timeout: float = 30.0,
) -> dict[str, Any]:  # NOSONAR  ← 错误：加在返回类型行尾，不生效
    ...
```

**正确示例**：

```python
async def process_data(  # NOSONAR  ← 正确：加在 def 行尾
    self,
    items: list[dict],
    timeout: float = 30.0,
) -> dict[str, Any]:
    ...
```

> **根因**：SonarQube 报告的 `issue.line` 指向 def 行，而子代理经常把 NOSONAR 加在函数签名最后一行（返回类型行）。2026-07-21 扫描中发现 **18 处**此类型错误。

---

## 与配置的关系

| 配置节点 | 作用 |
|----------|------|
| `config/fix_strategies.json -> nosonar_position_rules` | 位置规则的配置化数据源（rule_pattern → position 映射） |
| `config/core_config.json -> nosonar_validation` | 校验开关与回退策略 |
| `config/core_config.json -> verify.validate_nosonar_position` | 修复后扫描若 OPEN 数未下降，自动触发 NOSONAR 位置校验 |
| `config/core_config.json -> failure_recovery.mappings[nosonar_not_effective]` | NOSONAR 未生效时的恢复动作（重新放置） |

---

## 子代理 prompt 模板片段

子代理修复 OPEN issue 时，主代理在 prompt 中应包含以下指令：

```
## NOSONAR 位置规则（重要）

修复时若需要使用 # NOSONAR 抑制注释，必须按以下步骤确定位置：

1. 查 fix_strategies.json -> nosonar_position_rules 表，按 rule ID 匹配 position
2. position = "issue_line"              → 在 SonarQube 报告的 issue.line 末尾追加 NOSONAR
3. position = "first_param_line"        → 在函数第一个参数所在行末尾追加 NOSONAR
4. position = "multiline_def_first_line" → 在多行函数定义的 def 行末尾追加 NOSONAR
5. position = "n/a"                     → 该规则不需要 NOSONAR，用其他方式修复
6. 未找到 rule                          → 用默认规则（issue_line）

注释格式（查 core_config.json -> frontend_comment_syntax.mappings）：
- Python: # NOSONAR
- .js/.ts: // NOSONAR（标签外）或 /* NOSONAR */（JSX 标签内）
- .vue <template>: <!-- NOSONAR -->
- .vue <script>: // NOSONAR 或 /* NOSONAR */
- .vue <style>: /* NOSONAR */
- .wxml: <!-- NOSONAR -->
- .wxss: /* NOSONAR -->

多行函数定义首行规则（Python）：
- NOSONAR 必须加在 def func( 行尾，不能加在 )->ReturnType: 行尾

NOSONAR 抑制 vs 代码修复决策（查 nosonar_decision_matrix）：
- must_fix_rules（安全漏洞）→ 必须代码修复，禁止 NOSONAR
- can_suppress_rules（代码风格）→ 允许 NOSONAR，但需附带原因注释

关键限制：
- NOSONAR 必须大写
- 必须在 # 或 // 注释中，在 docstring 字符串内不生效
- SonarQube 不识别 Python # noqa
```

---

## NOSONAR 抑制 vs 代码修复决策矩阵

> 配置化数据源：`core_config.json -> nosonar_decision_matrix`

### must_fix_rules（必须代码修复，禁止 NOSONAR）

| 规则 | 说明 | 为什么禁止抑制 |
|------|------|---------------|
| python:S5443 | 硬编码凭据 | 安全漏洞，抑制会留下安全隐患 |
| python:S930 | SQL 注入 | 安全漏洞，必须参数化查询 |
| python:S2817 | 命令注入 | 安全漏洞，必须避免 shell=True |
| python:S5886 | 不安全赋值表达式 | 可能导致逻辑漏洞 |
| python:S3699 | 除以零 | 运行时错误，抑制无法解决问题 |
| typescript:S2817 | 命令注入 | 安全漏洞 |
| typescript:S5446 | 硬编码凭据 | 安全漏洞 |
| java:S2076 / go:S2076 | 注入 | 安全漏洞 |

### can_suppress_rules（允许 NOSONAR 抑制，需附带原因注释）

| 规则 | 说明 | 典型抑制原因 |
|------|------|-------------|
| python:S3776 | 认知复杂度过高 | 框架路由/生命周期方法无法拆分 |
| python:S7503 | async 无 await | FastAPI 依赖注入需 async 声明 |
| python:S125 | 注释中的代码 | 配置示例/调试代码保留 |
| python:S6353 | 正则非捕获组 | 框架路由模式要求 |
| python:S107 | 参数过多 | 框架函数签名无法修改 |
| python:S7483 | timeout 参数 | 框架超时参数无法移除 |
| python:S5850 | 正则优先级 | 框架正则模式 |
| typescript:S3776 | 认知复杂度过高 | React 组件渲染逻辑 |
| typescript:S6353 | 正则字符类 | 路由模式要求 |
| typescript:S6551 | 模板字符串 | typeof 收窄误报 |
| typescript:S6754 | useState | 已正确解构仍误报 |
| typescript:S6848 | 非原生交互元素 | 拖放容器 |

---

## 前端文件注释语法速查

> 配置化数据源：`core_config.json -> frontend_comment_syntax.mappings`

| 文件类型 | 区块 | NOSONAR 语法 | 示例 |
|---------|------|-------------|------|
| `.py` | — | `# NOSONAR` | `def foo():  # NOSONAR` |
| `.js` / `.ts` | 标签外 | `// NOSONAR` | `const x = 1; // NOSONAR` |
| `.js` / `.ts` | JSX 标签内 | `/* NOSONAR */` | `<div /* NOSONAR */>` |
| `.vue` | `<template>` | `<!-- NOSONAR -->` | `<!-- NOSONAR -->` |
| `.vue` | `<script>` | `// NOSONAR` | `const x = 1; // NOSONAR` |
| `.vue` | `<style>` | `/* NOSONAR */` | `/* NOSONAR */` |
| `.wxml` | — | `<!-- NOSONAR -->` | `<!-- NOSONAR -->` |
| `.wxss` | — | `/* NOSONAR */` | `/* NOSONAR */` |
| `.css` | — | `/* NOSONAR */` | `/* NOSONAR */` |
| `.scss` | 行注释 | `// NOSONAR` | `// NOSONAR` |
| `.scss` | 块注释 | `/* NOSONAR */` | `/* NOSONAR */` |
| `.html` | — | `<!-- NOSONAR -->` | `<!-- NOSONAR -->` |
