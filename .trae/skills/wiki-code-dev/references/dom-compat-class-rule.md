# DOM 变更保留测试兼容 class 名规则（CODING-056）

> 复盘来源：顶部导航栏挪到左侧侧边栏改造时，重命名 `<header>` 为 `<aside>` 但保留原 class 名（`nav`/`nav-collapsed`/`nav-tabs`/`tab-btn`/`icon-btn`/`nav-user-name`），避免 E2E 测试选择器同步成本。
> 所有可变参数从 `config/coding-standards-config.md` 的 `dom_compat_class` 字段读取，禁止在规则文件中硬编码选择器或阈值。

## 触发场景

- 导航栏 / 侧栏 / 工具栏等结构性组件重构
- HTML 标签语义化调整（如 `<header>` → `<aside>`、`<div>` → `<nav>`）
- CSS 类对应的 DOM 结构变化但视觉行为不变
- 组件内部布局调整但对外暴露的 class 契约不变

## 规则

### DCC-1：DOM 结构变更时优先保留原 class 名

当变更涉及 HTML 标签替换、DOM 层级调整、布局方向改变（如水平→垂直）时，**必须保留原 class 名**，仅调整标签与内部结构。

禁止在重构时顺便重命名 class（如 `nav` → `sidebar-nav`），除非有明确的语义错误。

### DCC-2：必须重命名时同步更新测试用例

若 class 名必须重命名（如语义错误、命名冲突），必须按 `test_case_sync_rule`（CODING-031）同步更新所有引用该 class 的测试用例，禁止先改代码后补测试的异步提交。

### DCC-3：class 删除前必须交叉验证测试引用

删除 class 前，必须用 `dom_compat_class.verify_methods`（默认 `["grep", "glob"]`）交叉验证测试文件中是否引用该 class：
- Grep 搜索测试目录下 `.py` / `.ts` / `.spec.ts` 文件中的 class 名
- 若有引用，按 `dom_compat_class.stale_class_threshold`（默认 0，零容忍）判定是否阻断

### DCC-4：响应式断点降级时保留 class 名

响应式布局降级（如宽屏侧栏 → 窄屏顶部条）时，**必须保留原 class 名**，仅通过 CSS 媒体查询调整 `flex-direction` / `width` 等属性。禁止为不同断点创建不同 class 名（如 `nav-desktop` / `nav-mobile`）。

## 设计流程

```
DOM 结构变更需求
   ↓
1. 识别受影响的 class 名（Grep 搜索现有 class）
   ↓
2. 评估是否必须重命名
   ↓
   是 → 按 CODING-031 同步更新测试用例
   否 → 保留原 class 名，仅调整标签与内部结构
   ↓
3. 删除 class 前，Grep 测试目录验证引用
   ↓
   有引用 → 保留 class 或同步更新测试
   无引用 → 安全删除
   ↓
4. 响应式降级：保留 class，用媒体查询调整 CSS 属性
   ↓
5. vue-tsc + E2E 测试双重验证
```

## 适用场景

- 导航栏重构（顶部→左侧、水平→垂直）
- 侧栏改造（宽窄双模式、折叠展开）
- 工具栏调整（图标位置、按钮分组）
- 任何涉及 DOM 结构变化但视觉行为不变的重构
- 响应式布局降级（宽屏→窄屏）

## 不适用场景

- 新建组件（无历史 class 名负担，可自由命名）
- class 名存在语义错误（如 `.user-list` 实际显示产品列表，必须重命名）
- class 名与技术栈冲突（如与 UI 库内置 class 冲突）
- 一次性废弃代码（删除后无任何引用）

## 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `dom_compat_class.verify_methods` | `["grep", "glob"]` | class 引用交叉验证方法 |
| `dom_compat_class.test_file_patterns` | `["**/test_*.py", "**/*.spec.ts"]` | 测试文件 glob 匹配模式 |
| `dom_compat_class.stale_class_threshold` | `0` | 失效 class 引用容忍阈值（0=零容忍） |
| `dom_compat_class.require_same_commit` | `true` | class 重命名与测试更新是否要求同 commit |
