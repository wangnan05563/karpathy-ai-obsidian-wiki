# 通用 SonarQube 规则豁免与误报处理指南

> **单一信息源**：硬约束规则的完整定义（pattern/severity/applies_to）见 `config/hard_constraints/core.json`（通用）与 `config/hard_constraints/business/*.json`（业务特定）。本文件仅描述规则豁免的**通用判断标准与编写范式**，业务特定的规则覆盖应放在 `examples/{project}/rule-overrides.md`。

## 编写原则

1. **配置驱动**：规则覆盖的具体清单不应硬编码在文档中，应通过 `project_config.json -> fix_strategies_overrides.rule_overrides` 字段配置
2. **业务隔离**：通用规则覆盖写在本文件，业务特定覆盖写在 `examples/{project}/rule-overrides.md`，避免污染通用逻辑
3. **判断标准优先**：每个规则覆盖必须明确"豁免条件"与"不豁免条件"，禁止模糊判断
4. **comment 模板化**：豁免时填写的 comment 必须有模板，便于追溯

## 通用豁免判断范式

### 范式 1：框架装饰器导致的"未使用导入"误报

**适用规则**：`{language}:S1481`（未使用的导入）

**触发场景**：Web 框架（FastAPI/Flask/Spring/Django）的路由文件中，装饰器注册的函数和模型导入在静态分析中显示为未使用

**通用判断标准**：
- 文件包含框架路由装饰器（如 `@app.get/post/put/delete/patch`、`@router.*`、`@Controller`、`@RequestMapping`）→ 豁免
- 导入的 ORM/Schema 模型用于类型注解 → 豁免
- 导入的依赖注入装饰器（如 `Depends`、`@Autowired`）→ 豁免
- 确实无任何调用且非装饰器使用 → 不豁免，需删除

**comment 模板**：
```
框架误报：{framework_name} 路由装饰器模式，导入的符号在运行时通过反射调用。
```

> 具体框架装饰器清单从 `config/framework_patterns.json` 读取，不在本文件硬编码。

### 范式 2：依赖注入导致的"可变默认参数"误报

**适用规则**：`{language}:S2949`（可变默认参数）

**触发场景**：依赖注入框架使用 `Depends()`、`@Autowired` 等返回的是注入器，并非真正的可变对象

**通用判断标准**：
- 默认值为框架依赖注入函数（如 `Depends(...)`、`Body(...)`、`Query(...)`、`Path(...)`）→ 豁免
- 默认值为 `[]`、`{}`、`set()` → 不豁免，需改为 `None` 并在函数内初始化

### 范式 3：惯例命名导致的"未使用变量"误报

**适用规则**：`{language}:S3508`（未使用的局部变量）

**触发场景**：循环变量或解构变量有意忽略

**通用判断标准**：
- 变量名以 `_` 开头（如 `_unused`、`_`）→ 豁免
- 确实未使用且无 `_` 前缀 → 不豁免，需添加 `_` 前缀或删除

### 范式 4：类型注解导致的"未使用导入"误报

**适用规则**：`{language}:S1481`（未使用的导入）

**触发场景**：Python `TYPE_CHECKING` 块或 TypeScript `import type` 中的类型导入

**通用判断标准**：
- 导入语句在 `if TYPE_CHECKING:` 块内（Python）→ 豁免
- 使用 `import type` 或 `import { type X }` 语法（TypeScript）→ 豁免
- 仅用于类型注解的 `Optional`、`Union`、`List` 等 → 豁免

### 范式 5：配置文件导致的"硬编码凭据"误报

**适用规则**：`{language}:S2068`（硬编码凭据）

**触发场景**：配置文件示例中的占位符字符串被识别为凭据

**通用判断标准**：
- 字符串为占位符模式（如 `<your-token>`、`{placeholder}`、`example_*`）→ 豁免
- 字符串明确标记为示例（如 `example.com`、`test@example.org`）→ 豁免
- 实际凭据值 → 不豁免，必须改为环境变量读取

## 业务特定覆盖编写指南

当通用范式无法覆盖业务特定场景时，按以下步骤编写业务覆盖：

1. 在 `examples/{project}/` 目录下创建 `rule-overrides.md`
2. 引用本文件的通用范式作为基础
3. 增加业务特定的判断标准与 comment 模板
4. 在 `project_config.json -> fix_strategies_overrides.rule_overrides` 中配置覆盖清单
5. 通过 `scripts/validate-config.ps1` 校验配置一致性

## 与配置文件的关系

| 文件 | 用途 | 覆盖范围 |
|------|------|----------|
| 本文件（`references/rule-overrides.md`） | 通用豁免判断范式 | 所有项目 |
| `examples/{project}/rule-overrides.md` | 业务特定豁免判断 | 单个项目 |
| `config/hard_constraints/core.json` | 通用硬约束规则定义 | 所有项目 |
| `config/hard_constraints/business/*.json` | 业务特定硬约束规则定义 | 单个项目 |
| `project_config.json -> fix_strategies_overrides.rule_overrides` | 项目级规则覆盖清单 | 单个项目 |

## 豁免操作流程

1. **识别**：扫描结果中标记为"疑似误报"的问题
2. **判断**：按本文件的通用范式或业务覆盖文件判断是否豁免
3. **配置**：在 `project_config.json -> fix_strategies_overrides.rule_overrides` 中记录豁免清单
4. **执行**：调用 `change_sonar_issue_status(issueKey, "falsepositive", comment)` 标记误报
5. **验证**：通过 `scripts/validate-config.ps1` 校验配置一致性
