# 评审配置 — wiki-frontend-code-review

> 本文件集中管理评审过程中所有可配置参数。规则文件（references/*.md）只描述通用模式，不硬编码具体阈值与路径，所有具体数值以本文件为准。修改项目结构或技术栈时，只需更新本文件。

## 项目目录映射

| 用途       | 目录约定（相对于项目根） |
| ---------- | ------------------------- |
| 页面视图   | `packages/web/src/views/` |
| 状态仓库   | `packages/web/src/stores/` |
| 通用组件   | `packages/web/src/components/` |
| 类型定义   | `packages/web/src/types/` |
| 工具函数   | `packages/web/src/utils/` |
| API 请求层 | `packages/web/src/api/` |

评审范围：仅评审 `packages/web/` 下的 `.vue`、`.ts`、`.tsx` 文件。其他目录（如 `packages/server/`、`scripts/`）不在本技能覆盖范围内。

## 技术栈

| 维度       | 技术选型                                  |
| ---------- | ----------------------------------------- |
| 框架       | Vue 3.4+                                  |
| UI 库      | Element Plus                              |
| 状态管理   | Pinia（setup 语法）                       |
| 图谱可视化 | vis-network 9.x                           |
| 语言       | TypeScript（严格模式）                    |
| 构建工具   | Vite                                      |
| 包管理     | pnpm                                      |

## 组件设计规范

- **IP 头像**：使用 `RobotAvatar` 组件呈现会话/问答的机器人形象，避免直接使用静态图片。
- **配色体系**：马卡龙配色（粉/蓝/绿/黄/紫的低饱和组合），通过 CSS 变量统一管理；禁止散落硬编码色值。
- **卡片样式**：毛玻璃卡片（`backdrop-filter: blur()` + 半透明白底 + 细边框 + 阴影），用于对话气泡、图谱节点详情面板。
- **圆角与间距**：遵循 Element Plus 设计令牌，不引入第三方设计体系。

## 主题色系统

### 主题列表

| 主题 key | 标签 | 基调 |
|----------|------|------|
| `macaron` | 马卡龙 | 浅粉浅青 · 圆润可爱 |
| `enterprise` | 现代企业 | 科技蓝灰 · 专业可信赖 |
| `creative` | 创意品牌 | 霓虹赛博 · 大胆渐变（默认） |
| `product` | 产品展示 | 暗黑霓虹 · 科技未来 |
| `ecommerce` | 电商零售 | 明亮扁平 · 橙蓝活力 |
| `portfolio` | 艺术作品集 | 米色金黑 · 优雅极简 |

### CSS 变量目录

| 文件路径 | 用途 |
|----------|------|
| `packages/web/src/style.css` `:root` | creative 默认主题变量 |
| `packages/web/src/styles/themes/macaron.css` | 马卡龙主题覆盖 |
| `packages/web/src/styles/themes/enterprise.css` | 现代企业主题覆盖 |
| `packages/web/src/styles/themes/product.css` | 产品展示主题覆盖 |
| `packages/web/src/styles/themes/ecommerce.css` | 电商零售主题覆盖 |
| `packages/web/src/styles/themes/portfolio.css` | 艺术作品集主题覆盖 |
| `packages/web/src/styles/themes/index.css` | @import 入口 |
| `packages/web/src/composables/useTheme.ts` | 主题状态管理与持久化 |

### CSS 变量三层架构

| 层级 | 前缀 | 用途 |
|------|------|------|
| L1 基础调色板 | `--neon-*` / `--bg-*` / `--text-*` | 主题底色、背景、文字 |
| L2 子系统 | `--robot-*` / `--graph-*` | IP 形象、图谱节点专属色 |
| L3 场景 | `--bg-scene` / `--accent-*-aXX` | 容器深度背景、半透明强调色 |

### alpha 变体命名规则

统一格式：`a` + 两位数字（`a03` / `a05` / `a08` / `a10` / `a12` / `a15` / `a18` / `a20` / `a25` / `a30` / `a35` / `a40` / `a45` / `a50` / `a60` / `a70`）。

### 主题色白名单（允许硬编码）

| 色值 | 原因 |
|------|------|
| `rgba(255, 255, 255, X)` | 纯白高光，所有主题通用 |
| `transparent` | 透明值，无主题差异 |
| `inherit` / `currentColor` | 继承值，自动适配 |

## 性能阈值

### vis-network 节点数三级降级

| 级别 | 节点数阈值          | 降级策略                                                            |
| ---- | ------------------- | ------------------------------------------------------------------- |
| L1   | `nodes <= 200`      | 默认配置：开启平滑曲线、完整物理引擎、完整样式                      |
| L2   | `200 < nodes <= 500` | 关闭平滑曲线（`smooth: false` 或 `smooth.enabled: false`）          |
| L3   | `nodes > 500`       | 简化节点样式（去除阴影/透明度）+ 减少稳定化迭代次数（如 `stabilization.iterations` 降至 100 以下） |

### 响应式断点

| 断点           | 行为                                                   |
| -------------- | ------------------------------------------------------ |
| `width >= 768` | 默认图谱视图（Canvas 渲染）                            |
| `width < 768`  | 自动切换为列表视图，减少 Canvas 渲染开销与交互抖动     |

## SSE 事件类型约定

SSE 流式接口须按下列事件类型分段推送，前端按类型分发到对应 store action：

| 事件类型   | 语义                                       | 前端处理 action（建议） |
| ---------- | ------------------------------------------ | ----------------------- |
| `answer`   | 模型回答的增量文本块                       | `appendAnswer`          |
| `refs`     | 引用来源列表                               | `setRefs`               |
| `done`     | 回答结束标记                               | `finalizeAnswer`        |
| `error`    | 流式错误                                   | `markError`             |
| `progress` | 进度信息（如"正在检索文档"）              | `setProgress`           |
| `page`     | 分页信息（如爬取/修复任务的当前页）        | `setPage`               |
| `fixing`   | 修复任务开始/进行中                        | `markFixing`            |
| `fixed`    | 修复任务完成                              | `markFixed`             |

未知事件类型应记录日志但不抛出异常，避免中断流式消费。

## 配置隔离审查参数

> 配置隔离规则（见 [references/config-isolation-rule.md](../references/config-isolation-rule.md)）所依赖的可配置数值集中在此管理，规则文件只描述通用模式。

### 多实例配置维度标识

| 维度场景       | 标识来源        | localStorage key 模板                  |
| -------------- | --------------- | -------------------------------------- |
| LLM 预设       | 预设 key        | `llmPresetConfig:${presetKey}`         |
| 多账号         | 账号 ID         | `accountConfig:${accountId}`           |

切换实例时按上述 key 模板读取返显，禁止多实例共用同一 key。

### 脱敏值前缀

| 字段       | 脱敏前缀 | 含义                                       |
| ---------- | -------- | ------------------------------------------ |
| `apiKey`   | `****`   | 后端返显的脱敏占位，表示未修改原值         |

判断逻辑：以 `****` 开头视为"未修改"分支跳过该字段；`else` 分支处理新值（含空串，表示用户主动清空）。禁止用 `value && !value.startsWith('****')` 反向匹配。

### 恢复默认值接口路径

| 用途               | HTTP 方法 | 路径                              |
| ------------------ | --------- | --------------------------------- |
| 恢复 LLM 预设默认值 | `POST`    | `/api/config/llm-preset/reset`    |
| 恢复账号配置默认值 | `POST`    | `/api/config/account/reset`       |

调用前必须弹出 `ElMessageBox.confirm` 二次确认。

### 破坏性按钮白名单

以下按钮文案允许使用 `type="danger"` 并配合 `ElMessageBox.confirm` 二次确认，其他破坏性操作须先经设计评审后加入本白名单：

| 按钮文案       | 触发动作                       |
| -------------- | ------------------------------ |
| 恢复初始配置   | 调用恢复默认值接口并刷新表单   |
| 删除           | 删除预设/账号/单条记录         |

## 适用 / 不适用场景

### 适用

- 评审 `packages/web/` 下新增或修改的 Vue 3 / TypeScript 前端文件。
- 评审涉及 Element Plus 组件、Pinia store、vis-network 图谱、SSE 流式消费的代码。
- 提交前自查（pending-change review）或针对指定文件的定向评审（file-targeted review）。

### 不适用

- 后端代码（`packages/server/`、Python、Node 服务端逻辑）。
- 纯配置文件（`vite.config.ts`、`tsconfig.json`）的评审，除非涉及上述规则的具体违反。
- 构建脚本、CI 配置、文档文件。
- 第三方依赖升级的兼容性评估（属于迁移任务，非评审任务）。

## 持久化与存储边界审查参数

> 持久化与存储边界规则（见 [references/persistence-boundary-rule.md](../references/persistence-boundary-rule.md)）所依赖的可配置参数集中在此管理。

### 存储类型与权威源

| 数据类型 | 浏览器存储（缓存层） | 后端权威源 | 跨 origin 共享 |
|---------|---------------------|-----------|---------------|
| AI 配置（apiKey） | localStorage（仅脱敏值） | `/api/ai/config` + config.json | 是 |
| 历史会话 | IndexedDB（降级缓存） | `/api/conversations` + data/conversations/ | 是 |
| LLM 预设 UI 状态 | localStorage（baseUrl/model） | 无（前端独立） | 否 |
| 主题偏好 | localStorage | 无（前端独立） | 否 |

判断逻辑：跨 origin 列为"是"的数据必须以后端为权威源，浏览器存储仅作降级缓存。

### 敏感数据禁止 localStorage 明文清单

| 字段 | 禁止明文存储原因 | 替代方案 |
|------|----------------|---------|
| `apiKey`（LLM/webSearch） | XSS 风险 + 双轨不一致 | 后端 config.json 唯一权威源，前端仅展示脱敏值 |
| `cpolarAuthtoken` | 凭证泄露风险 | 后端 config.json |
| `certFile` 内容 | 凭证泄露风险 | 后端文件系统 |

### 降级策略参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `backend_unavailable_fallback` | `indexed-db-cache` | 后端不可用时降级到 IndexedDB |
| `cache_write_failure_action` | `non-blocking` | 缓存写入失败不阻断主流程 |
| `fallback_log_level` | `warn` | 降级日志级别（console.warn） |

### 一次性迁移触发条件

| 迁移类型 | 触发条件 | 幂等性 |
|---------|---------|--------|
| IndexedDB → 后端会话 | 应用启动时检测到 IndexedDB 有数据但后端为空 | 是（PUT upsert） |
| localStorage apiKey 清理 | 用户点击"恢复初始配置"或检测到遗留 apiKey:* 键 | 是（删除操作） |