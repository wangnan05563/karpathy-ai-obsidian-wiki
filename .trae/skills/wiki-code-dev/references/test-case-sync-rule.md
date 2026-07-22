# 测试用例与代码结构同步规则（CODING-031）

> 复盘来源：UI 改造去除 `.query-head` 后，E2E 测试仍检查该元素，导致测试用例全部失败。根因是代码变更未同步更新测试选择器。
> 所有可变参数从 `config/coding-standards-config.md` 的 `test_case_sync` 字段读取，禁止在规则文件中硬编码选择器名称。

## 规则

**代码变更影响 DOM 结构（class 名、id、元素层级）时，必须同步更新测试用例的选择器与断言**，禁止测试用例引用已被删除的 DOM 元素，禁止用 `try/except` 静默吞掉选择器失效错误。

## 适用场景

- 重构组件 template，class 名变更（如 `.query-head` → `.query-topbar`）
- 删除页面元素（如去除标题头）
- 新增页面元素（如添加折叠按钮）
- 调整元素层级（如 `<div class="head-actions">` → `<div class="topbar-actions">`）
- 修改 v-for 渲染逻辑导致 DOM 数量变化

## 不适用场景

- 纯样式修改（CSS 属性调整，DOM 结构不变）
- 纯逻辑修改（API 调用、数据处理）
- 测试用例新增（不影响现有用例）
- 临时调试代码（不进入主分支）

## 同步检查流程

```
修改 .vue / .tsx 文件 template
   ↓
1. 识别变更的 DOM 选择器（新增/删除/重命名）
   ↓
2. Grep 测试脚本中是否引用了这些选择器
   ↓
   引用 → 必须同步更新测试用例
   ↓
3. 同步更新选择器与断言
   ↓
4. 运行测试用例验证通过
   ↓
5. 提交代码与测试用例（同一 commit）
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `test_case_sync.enabled` | `true` | 是否启用测试同步守卫 |
| `test_case_sync.severity` | `error` | 违规严重级别 |
| `test_case_sync.test_file_patterns` | `**/test_*.py,**/test_*.ts,**/*.spec.ts,**/*.test.ts` | 测试文件 glob 模式（逗号分隔） |
| `test_case_sync.selector_patterns` | `\.[-\w]+, #[-\w]+, \[class="[^"]+"\], data-testid="[^"]+"` | 选择器匹配模式（CSS class / id / attribute） |
| `test_case_sync.require_same_commit` | `true` | 代码与测试用例是否必须在同一 commit |
| `test_case_sync.silent_failure_forbidden` | `true` | 禁止 try/except 静默吞掉选择器失效错误 |
| `test_case_sync.stale_selector_threshold` | `0` | 允许的失效选择器数量（默认 0） |
| `test_case_sync.auto_update_on_refactor` | `true` | 重构时是否自动建议更新测试用例 |

## 检查方式

1. **变更识别**：`git diff` 中识别 template 段的 class / id 变更
2. **选择器引用扫描**：Grep 测试脚本中是否引用了被删除的选择器
3. **try/except 审计**：扫描测试用例的 try/except 块，确认 except 分支未静默吞掉选择器失效错误（必须 `record(..., False, str(e))` 标记失败）
4. **同 commit 验证**：检查 commit 中是否同时包含代码与测试用例修改

## 正确示例

```python
# 步骤 1：去除 .query-head 后，Grep 测试脚本：
# grep -r "query-head" scripts/test_full_e2e.py
# 命中：page.locator(".query-head")

# 步骤 2：同步更新为 .query-topbar
topbar = page.locator(".query-topbar").first
if topbar.is_visible():
    record("顶栏渲染", True)
else:
    record("顶栏渲染", False, ".query-topbar not found")

# 步骤 3：添加新增的折叠按钮测试
nav_toggle = nav.locator(".nav-toggle-btn").first
if nav_toggle.is_visible():
    nav_toggle.click()
    record("导航栏折叠", "collapsed" in (nav.get_attribute("class") or ""))
```

```typescript
// E2E 测试（TypeScript 版）
test('query topbar renders', async ({ page }) => {
  const topbar = page.locator('.query-topbar').first();
  await expect(topbar).toBeVisible();  // 同步更新选择器
});
```

## 错误示例

```python
# 错误：未同步更新，仍引用 .query-head
head = page.locator(".query-head").first  # 已被删除，永远找不到
if head.is_visible():  # 返回 False
    record("标题头", True)
# 测试用例报失败，但实际是选择器失效而非功能 bug

# 错误：try/except 静默吞掉错误
try:
    head = page.locator(".query-head")
    record("标题头", head.is_visible())
except Exception:
    pass  # 违规：静默吞掉错误，测试用例假"通过"

# 错误：代码与测试用例分两个 commit
# commit 1: refactor: 去除 .query-head
# commit 2: test: 同步更新测试用例
# 违反 require_same_commit，CI 在 commit 1 时会失败
```

## 适配新项目

- 适配 Cypress 项目：`test_file_patterns` 改为 `**/cypress/integration/*.spec.js`
- 适配 Jest 项目：`test_file_patterns` 改为 `**/__tests__/*.test.ts`
- 适配无自动化测试项目：将 `enabled` 设为 `false`，但建议补充测试

## 与其他规则的关系

- 与 CODING-030（E2E 测试前置服务检查）联动：CODING-030 确保运行环境就绪，CODING-031 确保测试用例本身正确
- 与 wiki-auto-testing skill 配合：本规则是 wiki-auto-testing 测试流程的同步性补充
