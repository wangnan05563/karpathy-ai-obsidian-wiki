# 第三方 UI 库 API 时效性规则（Third-Party UI API Currency）

> 复盘来源：开发模式点击"知识浏览"页时，前端控制台打印 `ElementPlusError: [el-radio] [API] label act as value is about to be deprecated in version 3.0.0`。根因是 Element Plus 2.6.0 起 `el-radio` / `el-radio-button` 的 `label` 作 value 已被弃用、3.0.0 移除，而代码仍用 `label="x"` 承载选项值。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的"第三方 UI 库 API 时效性（ui_library_api）"章节读取，禁止在本规则文件硬编码组件名 / 属性名 / 版本号。

## 适用场景

使用第三方 UI 组件库（Element Plus / Ant Design Vue / MUI / Naive UI 等）的任意前端项目。规则与具体业务解耦，抽象为"库 API 须跟随当前主版本、升级前全量迁移弃用 API"的通用判断逻辑。

## Trigger Keywords

el-radio, el-radio-button, label act as value, ElementPlusError, deprecated, @deprecated, major version, 弃用, 升级, value=, label=

## Rules

### CODING-UI-API-1：禁止在新代码中沿用库已标记 deprecated 的属性 / 事件 / 插槽

- **Severity**: critical
- **Description**: 组件库标记 `deprecated` 的属性（如 Element Plus `el-radio` / `el-radio-button` 的 `label` 作 value）不得在新代码中使用，须改用官方推荐的替代写法（如 `value` 属性承载选项值 + 默认插槽承载显示文本）。这类用法在控制台打印弃用告警，并在下一个主版本被移除——属于"现在只是警告、升级即断"的定时炸弹。`v-model` 绑定不变。
- **Suggested fix**:

```vue
<!-- 错误：label 被当作 value（EP 2.6+ 弃用，3.0 移除） -->
<el-radio-group v-model="mode">
  <el-radio-button label="knowledge">知识</el-radio-button>
</el-radio-group>

<!-- 正确：value 承载选项值，默认插槽承载显示文本 -->
<el-radio-group v-model="mode">
  <el-radio-button value="knowledge">知识</el-radio-button>
</el-radio-group>
```

### CODING-UI-API-2：升级 UI 库主版本（major）前须全量扫描并迁移弃用 API

- **Severity**: critical
- **Description**: 升级组件库主版本前，必须用 grep 全量扫描受影响的组件标签与弃用属性/事件组合（如 `ui_library_api.scan_components` + `ui_library_api.deprecated_attrs`），并逐一迁移到替代写法。禁止带着 deprecated 用法直接升级——否则升级后旧 API 被移除，功能静默失效（选项值丢失、事件不触发等），且无编译期报错。
- **Suggested fix**:

```bash
# 升级前全量扫描弃用用法（组件 + 弃用属性）
grep -rn "el-radio" --include=*.vue . | grep -E "label="
# 命中项逐一改为 value= + 插槽，再执行升级
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `ui_library_api.scan_components` | `el-radio,el-radio-button,el-radio-group` | 受影响组件（按项目实际使用的库调整） |
| `ui_library_api.deprecated_attrs` | `label` | 禁止用作选项值的弃用属性 |
| `ui_library_api.replacement_attrs` | `value` | 替代属性（选项值） |
| `ui_library_api.display_text_strategy` | `slot` | 显示文本改用默认插槽 |
| `ui_library_api.deprecation_since_version` | `2.6.0` | 该用法被标记弃用的库版本 |
| `ui_library_api.removal_version` | `3.0.0` | 该用法被移除的库主版本 |

## 检查方式

1. **新增沿用检查**：Grep `ui_library_api.scan_components` 与 `ui_library_api.deprecated_attrs` 的组合，确认 `deprecated_attrs` 未被当作值使用；命中即 **CODING-UI-API-1 违规**（critical）。
2. **升级迁移检查**：组件库升级类 PR 须包含 `grep` 全量扫描弃用用法的证据与迁移清单；缺失即 **CODING-UI-API-2 违规**（critical）。

## 与其他规则的关系

- 与前端审查规则 FR-065（Element Plus 单选组件弃用属性）互为表里：本规则是编码侧的通用标准，FR-065 是审查侧的具体条目。
- 与 `frontend-ts-js-shadowing-rule.md`（FR-061）同为前端"升级/构建后才暴露"类风险：弃用 API 与 .ts 遮蔽都表现为"改了看似没事、特定条件才断"。
