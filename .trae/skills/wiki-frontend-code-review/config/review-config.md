# 评审配置 — wiki-frontend-code-review

> 本文件集中管理评审过程中所有可配置参数。规则文件（references/*.md）只描述通用模式，不硬编码具体阈值与路径，所有具体数值以本文件为准。修改项目结构或技术栈时，只需更新本文件。

## 项目目录映射

| 用途       | 目录约定（相对于项目根） |
| ---------- | ------------------------- |
| 页面视图   | `frontend/src/views/` |
| 状态仓库   | `frontend/src/stores/` |
| 通用组件   | `frontend/src/components/` |
| 类型定义   | `frontend/src/types/` |
| 工具函数   | `frontend/src/utils/` |
| API 请求层 | `frontend/src/api/` |

评审范围：仅评审 `frontend/` 下的 `.vue`、`.ts`、`.tsx` 文件。其他目录（如 `api/`、`scripts/`）不在本技能覆盖范围内。

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
| `frontend/src/style.css` `:root` | creative 默认主题变量 |
| `frontend/src/styles/themes/macaron.css` | 马卡龙主题覆盖 |
| `frontend/src/styles/themes/enterprise.css` | 现代企业主题覆盖 |
| `frontend/src/styles/themes/product.css` | 产品展示主题覆盖 |
| `frontend/src/styles/themes/ecommerce.css` | 电商零售主题覆盖 |
| `frontend/src/styles/themes/portfolio.css` | 艺术作品集主题覆盖 |
| `frontend/src/styles/themes/index.css` | @import 入口 |
| `frontend/src/composables/useTheme.ts` | 主题状态管理与持久化 |

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

- 评审 `frontend/` 下新增或修改的 Vue 3 / TypeScript 前端文件。
- 评审涉及 Element Plus 组件、Pinia store、vis-network 图谱、SSE 流式消费的代码。
- 提交前自查（pending-change review）或针对指定文件的定向评审（file-targeted review）。

### 不适用

- 后端代码（`api/`、Python、Node 服务端逻辑）。
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

## 编码安全审查参数

> 编码安全规则（见 [references/encoding-safety-rule.md](../references/encoding-safety-rule.md)）所依赖的可配置参数集中在此管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `source_encoding_required` | `utf-8-no-bom` | 源文件要求编码 |
| `meta_encoding_required` | `utf-8-no-bom` | 元配置文件要求编码 |
| `encoding_detection` | `utf8-strict-decode` | 检测方法（严格 UTF-8 解码） |
| `encoding_scan_scope` | `.vue,.ts,.tsx,.json,.md` | 扫描文件扩展名 |
| `fffd_indicator` | `U+FFFD` | 乱码指示字符 |
| `ascii_whitelist` | `true` | 纯 ASCII 文件免检 |
| `check_replacement_char` | `true` | 在严格 UTF-8 解码后额外扫描 `U+FFFD` 替换字符，识别"解码合法但内容已损坏"的文件 |
| `replacement_char_threshold` | `0` | 允许出现的 `U+FFFD` 数量上限；`0` 表示完全禁止 |
| `replacement_char_action` | `block` | 命中时的动作：`block` 阻断提交 / `warn` 仅告警 |

## 危险操作审查参数

> 危险操作规则（见 [references/dangerous-action-rule.md](../references/dangerous-action-rule.md)）所依赖的可配置参数集中在此管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `dry_run_default` | `true` | dry_run 默认值（安全优先） |
| `danger_class` | `danger` | 关闭 dry_run 时按钮添加的 CSS 类 |
| `confirm_component` | `ElMessageBox.confirm` | 二次确认组件 |
| `confirm_type` | `warning` | 确认弹窗类型 |
| `cancel_no_request` | `true` | 取消确认不发起请求 |
| `irreversible_hint_required` | `true` | 确认文案必须含不可撤销提示 |
| `destructive_button_patterns` | `启动\|停止\|保存\|删除\|清除\|重置` | 破坏性按钮文案匹配模式（正则 alternation） |
| `required_guards` | `['loading', 'disabled', 'confirm']` | 破坏性按钮必须满足的防护类型（至少其一） |
| `guard_min_match` | `1` | 至少需满足的防护数量 |
| `destructive_button_whitelist` | `[]` | 豁免按钮文案清单（如纯前端状态切换按钮） |

## 多表单状态管理参数

> 多表单状态管理规则（见 [references/config-state-rule.md](../references/config-state-rule.md) 与 [references/dangerous-action-rule.md](../references/dangerous-action-rule.md)）所依赖的可配置参数集中在此管理。

| 参数 | 值 | 说明 |
|------|-----|------|
| `multi_form_pattern` | `Record<key, FormState>` | 多表单状态模式 |
| `independent_loading` | `true` | 每个表单独立 loading |
| `independent_result` | `true` | 每个表单独立 result |
| `reset_on_submit` | `true` | 提交时重置 result |

## 前端视图注册审查参数

> 前端视图注册规则（见 [references/route-registration-frontend-rule.md](../references/route-registration-frontend-rule.md)）所依赖的可配置参数集中在此管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `views_directory` | `frontend/src/views/` | 视图文件所在目录（相对项目根） |
| `app_entry` | `frontend/src/App.vue` | 应用入口文件路径 |
| `view_type_name` | `ViewName` | 视图 key 的字面量联合类型名称 |
| `required_hooks` | `['import', 'type', 'v-for', 'v-else-if']` | 视图注册必须完成的钩子列表 |

> 适用场景：SPA 手动路由项目（入口文件通过 `v-if` / `v-else-if` 链路切换视图）。若项目已采用 vue-router / react-router 等自动路由方案，本段配置不生效，规则文件不参与审查。

## 前后端类型同步审查参数

> 前后端类型同步规则（见 [references/type-sync-frontend-rule.md](../references/type-sync-frontend-rule.md)）所依赖的可配置参数集中在此管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `backend_types_path` | `api/src/types.ts` | 后端 types 文件路径（相对项目根） |
| `frontend_types_path` | `frontend/src/types.ts` | 前端 types 文件路径 |
| `sync_interfaces` | `[]` | 需同步的接口名清单；留空表示全部 `export interface` 都需同步 |
| `ignore_optional_marker` | `true` | 是否忽略 `?` 可选标记差异（后端必填前端可选视为兼容） |

> 适用场景：全栈 TypeScript 项目，前后端通过手动维护的 `types.ts` 文件约定共享类型。若项目使用 GraphQL / tRPC / OpenAPI Generator 自动生成前端类型，本段配置不生效。

## 敏感字段展示审查参数

> 敏感字段展示规则（见 [references/sensitive-field-display-rule.md](../references/sensitive-field-display-rule.md)）所依赖的可配置参数集中在此管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `sensitive_field_patterns` | `key\|token\|secret\|password\|authtoken` | 敏感字段名匹配模式（正则 alternation，大小写不敏感） |
| `display_strategy` | `masked_placeholder` | 敏感字段展示策略：`masked`（脱敏值回显）/ `masked_placeholder`（空输入框 + 提示） |
| `masked_prefix` | `****` | `masked` 策略下脱敏值前缀（用于识别"已是脱敏值"避免二次处理） |
| `placeholder_hint` | `留空不修改` | `masked_placeholder` 策略下输入框 placeholder 必须包含的提示关键词 |
| `sensitive_field_whitelist` | `[]` | 豁免字段名清单（如内部测试用字段） |

> 适用场景：从后端拉取后回显到表单输入框的凭证类字段（API Key、authtoken、password、secret、token）。登录/注册/修改密码流程的"新密码输入框"（用户主动输入，非后端回显）不适用本规则。

## 滚动容器审查参数

> 滚动容器规则（见 [references/scroll-container-rule.md](../references/scroll-container-rule.md)）所依赖的可配置参数集中在此管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `scroll_container.max_overflow_layers` | `1` | 容器链路上 `overflow-y: auto` 最大嵌套层数；超过即告警 |
| `scroll_container.flex_shrink_required_in_flex_column` | `true` | `flex-direction: column + flex: 1` 容器内的自然高度子项必须 `flex-shrink: 0` |
| `scroll_container.glass_card_selectors` | `.glass-card` | 全局可能产生 `overflow: hidden` 副作用的卡片类选择器清单（逗号分隔） |
| `scroll_container.outer_scroll_selectors` | `.content, .app-shell` | 已设 `overflow-y: auto` 接管滚动的外层容器选择器清单（逗号分隔） |

> 适用场景：Vue 3 + flex 布局的多卡片长内容页面（帮助文档、设置面板、仪表盘卡片堆叠），且外层已设 `overflow-y: auto` 接管页面滚动。CSS Grid 布局、原生块级元素堆叠不适用。

## SPA 内部跳转审查参数

> SPA 内部跳转规则（见 [references/spa-navigation-rule.md](../references/spa-navigation-rule.md)）所依赖的可配置参数集中在此管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `spa_navigation.event_name_pattern` | `{project}:navigate` | 事件名模式，`{project}` 占位符运行时替换为 `project_name` |
| `spa_navigation.project_name` | `karpathy` | 项目名，替换事件名中的 `{project}` 占位符 |
| `spa_navigation.app_entry` | `frontend/src/App.vue` | 监听事件的入口组件路径（相对项目根） |
| `spa_navigation.allowed_views` | `[]` | 允许跳转的视图名白名单；留空表示不校验 |
| `spa_navigation.require_lifecycle_pair` | `true` | 监听器必须在 `onMounted` / `onBeforeUnmount` 配对管理 |

> 适用场景：Vue 3 + `<script setup>` SPA 手动路由项目，入口组件通过 `currentView` ref + `v-if` / `v-else-if` 链路切换视图。vue-router / react-router / Next.js / Nuxt.js 等基于配置或文件约定的自动路由项目不适用。

## 检查更新审查参数

> 检查更新状态机规则（见 [references/update-check-rule.md](../references/update-check-rule.md)）所依赖的可配置参数集中在此管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `check_update.cache_ttl_ms` | `300000` | 后端缓存 TTL（毫秒），默认 5 分钟 |
| `check_update.poll_interval_ms` | `300000` | 前端轮询间隔（毫秒），必须 ≥ `cache_ttl_ms` |
| `check_update.first_check_delay_ms` | `5000` | 首次检查延迟（毫秒），避免与首屏渲染竞争 |
| `check_update.latest_to_idle_ms` | `3000` | `latest` 状态自动回 `idle` 的延迟（毫秒） |
| `check_update.offline_mode` | `true` | 离线模式开关；`true` 时后端固定返回 `has_update: false` |
| `check_update.required_states` | `idle, loading, latest, newer, error` | 必需状态列表（逗号分隔） |
| `check_update.update_endpoint` | `/api/about/check-update` | 后端检查更新接口路径 |
| `check_update.cleanup_hook` | `onBeforeUnmount` | 定时器清理生命周期钩子名 |

> 适用场景：Vue 3 + `<script setup>` 的"关于"页面或"设置"面板的检查更新功能，含轮询定时的异步状态机。PWA Service Worker 更新、Electron autoUpdater、一次性检查（无轮询）不适用。

## 图标与导航栏审查参数

> 图标与导航栏规则（见 [references/icon-and-navigation-rule.md](../references/icon-and-navigation-rule.md)）所依赖的可配置参数集中在此管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `icon_navigation.enabled` | `true` | 是否启用图标与导航栏审查 |
| `icon_navigation.severity` | `error` | 违规严重级别 |
| `icon_navigation.color_attribute` | `currentColor` | SVG 必须使用的颜色属性值 |
| `icon_navigation.forbidden_color_values` | `#hex, rgb(), rgba(), hsl()` | 禁止硬编码的颜色值格式 |
| `icon_navigation.nav_threshold` | `7` | 菜单项数量阈值，超过此值必须实现双模式 |
| `icon_navigation.tooltip_implementation` | `pure-css-hover` | tooltip 实现方式（pure-css-hover=纯 CSS hover，js-tooltip=JS 库） |
| `icon_navigation.transition_mode` | `out-in` | Vue Transition 切换模式 |
| `icon_navigation.state_persistence_key` | `navCollapsed` | localStorage 持久化 key 名 |
| `icon_navigation.state_persistence_type` | `boolean` | 持久化值类型 |
| `icon_navigation.expanded_icon_size` | `16` | 展开模式图标尺寸（px） |
| `icon_navigation.collapsed_icon_size` | `22` | 折叠模式图标尺寸（px） |
| `icon_navigation.tooltip_position` | `bottom` | tooltip 出现位置 |
| `icon_navigation.tooltip_delay_ms` | `200` | tooltip 显示延迟（毫秒） |
| `icon_navigation.glow_filter_template` | `drop-shadow(0 0 {radius}px currentColor)` | 主题色光晕滤镜模板 |
| `icon_navigation.glow_radius_default` | `4` | 光晕默认半径（px） |
| `icon_navigation.glow_radius_hover` | `8` | hover 时光晕半径（px） |
| `icon_navigation.viewbox_standard` | `0 0 24 24` | SVG viewBox 标准 |
| `icon_navigation.stroke_width_default` | `1.8` | stroke 默认宽度 |
| `icon_navigation.whitelist_pure_white` | `true` | 纯白高光 rgba(255,255,255,X) 允许硬编码 |

> 适用场景：Vue 3 + `<script setup>` + 多主题切换 + SVG 矢量图标的 SPA 项目，导航栏菜单项 >7 需折叠。Font Awesome 字体图标、单主题项目、移动端无 hover 场景不适用。

## 严重级别定义

| 参数 | 值 | 说明 |
|------|-----|------|
| `severity_critical` | `🔴 严重` | 必须修复，阻止合并 |
| `severity_warning` | `🟡 警告` | 建议修复，不阻止合并 |
| `severity_suggestion` | `🟢 建议` | 可选优化 |
| `severity_positive` | `✅ 优点` | 正面反馈 |

## Vue 3 审查参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `vue.required_script_setup` | `true` | 必须使用 script setup |
| `vue.required_lang_ts` | `true` | 必须使用 lang="ts" |
| `vue.forbidden_options_api` | `true` | 禁止 Options API |
| `vue.cleanup_required` | `true` | 事件监听器必须清理 |

## 类型收窄审查参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `type_narrowing.ref_nullable_pattern` | `computed_or_local_var` | 可空 ref 访问模式 |
| `type_narrowing.ref_await_rule` | `use_local_var` | await 后访问 ref 必须用局部变量 |
| `type_narrowing.ref_template_rule` | `use_computed` | 模板中访问可空 ref 必须用计算属性 |

## 预设配置审查参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `preset.source` | `backend_api` | 预设来源应为后端 API |
| `preset.hardcode_forbidden` | `true` | 禁止前端硬编码预设 |
| `preset.fetch_pattern` | `fetch('/api/.../presets')` | 预设获取模式 |

## SSE 消费审查参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `sse.consumer_pattern` | `consumeSSEStream` | SSE 消费统一函数 |
| `sse.content_type` | `text/event-stream` | SSE Content-Type |
| `sse.event_format` | `event: <name>\ndata: <json>\n\n` | SSE 事件格式 |

## 输出格式参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `output.max_issues_per_section` | `10` | 每个级别最多输出条数 |
| `output.include_code_snippet` | `true` | 是否包含代码片段 |
| `output.include_rule_reference` | `true` | 是否引用规范依据 |
| `output.suggest_fix_code` | `true` | 是否提供修复代码示例 |

## 编码与运行时审查参数

> 用于 ES-7 ~ ES-9 规则，详见 references/encoding-safety-rule.md。

| 参数 | 值 | 说明 |
|------|-----|------|
| `encoding.disabled_attribute_required` | `true` | 禁用元素必须用 disabled 属性 |
| `encoding.disabled_attribute_name` | `disabled` | 禁用属性名 |
| `encoding.ui_text_consistency_required` | `true` | UI 文本必须与设计文档一致 |
| `encoding.ui_text_source` | `设计文档 + 源码` | UI 文本一致性验证来源 |
| `encoding.multi_instance_data_source` | `backend_api,config_file` | 多实例数据来源 |
| `encoding.multi_instance_hardcode_forbidden` | `true` | 禁止硬编码多实例数据 |
| `encoding.theme_list_source` | `config_file` | 主题列表来源 |
| `encoding.preset_list_source` | `backend_api` | 预设列表来源 |

## Async 可靠性审查参数

> 供 references/async-reliability-rule.md 引用，禁止在规则文件硬编码。

| 参数 | 值 | 说明 |
|------|-----|------|
| `async_reliability.default_call_timeout_sec` | `5.0` | 前端 async 请求默认超时（秒） |
| `async_reliability.heartbeat_interval_sec` | `3.0` | SSE 心跳检测间隔（秒） |
| `async_reliability.heartbeat_miss_threshold` | `3` | 心跳丢失阈值（连续 N 次无消息判定断线） |
| `async_reliability.reconnect_enabled` | `true` | SSE 断线是否自动重连 |
| `async_reliability.reconnect_max_retries` | `3` | 最大重连次数 |
| `async_reliability.reconnect_delay_sec` | `2.0` | 重连延迟（秒） |
| `async_reliability.timeout_whitelist` | `Promise.resolve,EventSource.open` | 无需超时保护的调用白名单 |
| `async_reliability.ui_feedback_required` | `true` | async 失败必须有 UI 反馈 |
| `async_reliability.timer_cleanup_required` | `true` | 定时器必须在 onBeforeUnmount 清理 |
| `async_reliability.fallback_ui_patterns` | `ElMessage.error,empty_state,retry_button` | 降级 UI 模式 |

## 类型检查缓存清理审查参数（FR-026）

> 供 references/typecheck-cache-frontend-rule.md 引用，禁止在规则文件硬编码。本规则针对 vue-tsc / tsc 幽灵错误（源码已收窄但工具仍报错）场景下的清缓存流程与绕过关键字禁令。

| 参数 | 值 | 说明 |
|------|-----|------|
| `typecheck_cache_frontend.typecheck_command` | `vue-tsc --noEmit` | 类型检查命令 |
| `typecheck_cache_frontend.cache_cleanup_targets` | `*.tsbuildinfo, node_modules/.vite, src/**/*.js` | 幽灵错误时清理的缓存产物 glob 列表（逗号分隔） |
| `typecheck_cache_frontend.bypass_keywords` | `as any, as unknown as, @ts-ignore, !.` | 禁止用作常规修复手段的绕过关键字（逗号分隔） |
| `typecheck_cache_frontend.allow_ts_expect_error` | `true` | 是否允许 `@ts-expect-error`（须配 issue 链接） |
| `typecheck_cache_frontend.test_file_allowlist` | `*.spec.ts, *.test.ts, **/__mocks__/**` | 允许放宽类型的测试文件 glob（逗号分隔） |
| `typecheck_cache_frontend.recheck_after_clean` | `true` | 清缓存后必须重新执行 typecheck_command 验证 |

> 适用场景：Vue 3 + `<script setup lang="ts">` 项目使用 `vue-tsc` 报告与源码逻辑不一致的错误（幽灵错误）。React/Next.js 改用 `tsc --noEmit`，清理目标含 `.next/`；纯 JavaScript 项目不适用。第三方库 `d.ts` 不完整走 `declare module` 或 `@ts-expect-error` + issue 引用例外路径。

## Composable API 先读后用审查参数（FR-027）

> 供 references/composable-api-frontend-rule.md 引用，禁止在规则文件硬编码。本规则约束调用 `useXxx` 前必须读源码确认 API 形状，并禁止诊断代码用 `$dispose` / `_s.delete` 重建 store。

| 参数 | 值 | 说明 |
|------|-----|------|
| `composable_api_frontend.use_xxx_pattern` | `use[A-Z]\w*` | 标识 composable 调用的正则 |
| `composable_api_frontend.store_lifecycle_forbidden` | `pinia._s.delete, $dispose, $reset` | 诊断代码禁止的 store 生命周期 API（逗号分隔） |
| `composable_api_frontend.diagnostic_allowlist_in_tests` | `*.spec.ts, *.test.ts` | 允许使用上述 API 的测试文件 glob（逗号分隔） |
| `composable_api_frontend.must_read_source_before_use` | `true` | 调用 useXxx 前必须读源码 |
| `composable_api_frontend.required_source_read_evidence` | `false` | 是否要求 PR 描述中显式贴出源码片段（推荐开启） |
| `composable_api_frontend.cleanup_hooks_to_check` | `onBeforeUnmount, onScopeDispose` | 检查 composable 副作用清理的生命周期钩子（逗号分隔） |

> 适用场景：Vue 3 Composition API 项目中调用任意 `useXxx`（自定义 composable / `useStore` / `useRoute` / `useRouter` / `useI18n` / `useHead` 等）与 Pinia store 状态诊断。React Hooks 同样要求先读源码（返回元组 vs 对象易混淆）；Vue 2 降级为"先读 Vuex store 字段定义"；纯 JavaScript 仅保留先读源码要求。

## 混合类型运行时分流审查参数（FR-028）

> 供 references/mixed-type-dispatch-frontend-rule.md 引用，禁止在规则文件硬编码。本规则约束联合类型 `T | U` 升级时的运行时分流方式与跨形态强转禁令。

| 参数 | 值 | 说明 |
|------|-----|------|
| `mixed_type_dispatch_frontend.forbidden_casts` | `as any, as unknown as` | 禁止的跨形态强转关键字（逗号分隔） |
| `mixed_type_dispatch_frontend.typeguard_module` | `frontend/src/types/guards.ts` | 集中导出 `isXxx` 类型守卫的模块路径 |
| `mixed_type_dispatch_frontend.required_dispatch_keywords` | `typeof, in, isXxx` | 允许的运行时分流方式（任一即可，逗号分隔） |
| `mixed_type_dispatch_frontend.required_test_per_member` | `true` | 联合类型每个成员必须有测试覆盖 |
| `mixed_type_dispatch_frontend.exhaustive_branch_required` | `true` | 消费联合类型的代码必须穷尽所有分支 |
| `mixed_type_dispatch_frontend.allowed_structural_cast` | `extends, optional field extension` | 允许的结构兼容强转场景（不视为违规，逗号分隔） |

> 适用场景：后端响应从单形态升级为联合形态（成功/失败分支、旧版/新版 schema 共存）、消息总线事件多态、第三方库返回联合类型。React/Next.js 守卫模块路径改为 `app/_types/guards.ts` 或 `src/types/guards.ts`；Vue 2 仍建议抽到独立模块；纯 JavaScript 降级为"运行时必须用 typeof/in 分流"。

## Vue SFC 单 script 块审查参数（FR-029）

> 供 references/sfc-single-script-frontend-rule.md 引用，禁止在规则文件硬编码。本规则约束 `.vue` 文件中 `<script>` 块的数量、属性与例外标注。

| 参数 | 值 | 说明 |
|------|-----|------|
| `sfc_script_block_frontend.allowed_script_count` | `1` | 每个 `.vue` 文件允许的 `<script>` 块数量上限 |
| `sfc_script_block_frontend.required_attrs` | `setup, lang="ts"` | 必须同时具备的 script 块属性（逗号分隔） |
| `sfc_script_block_frontend.exception_marker` | `// 例外：` | 例外注释必须包含的关键字 |
| `sfc_script_block_frontend.allowed_exceptions` | `named-export-non-reactive, options-extends-compat` | 允许的例外场景标识（逗号分隔） |
| `sfc_script_block_frontend.banned_macros_in_plain_script` | `defineProps, defineEmits, defineExpose, defineOptions, defineSlots` | 禁止在非 setup 块中调用的编译宏（逗号分隔） |
| `sfc_script_block_frontend.name_via` | `defineOptions({ name })` | 组件名声明的合规方式 |

> 适用场景：Vue 3 + `<script setup>` 项目中的所有 `.vue` 文件，包括 Options API → Composition API 迁移 PR 与新建 `.vue` 文件评审。Vue 2 不适用（无 `<script setup>` 语法）；纯 JavaScript 降级为"`<script setup>` 必须存在且唯一"，去掉 `lang="ts"` 要求；React/Next.js 不适用（非 SFC）。

## E2E 测试前置服务检查审查参数（FR-030）

> 供 references/e2e-precheck-frontend-rule.md 引用，禁止在规则文件硬编码。本规则约束 E2E 测试套件执行前的端口监听 + 健康检查 + 失败中止流程。

| 参数 | 值 | 说明 |
|------|-----|------|
| `e2e_precheck_frontend.required_ports` | `5173, 8000` | 必须监听的端口列表（逗号分隔，前端 dev + 后端 API） |
| `e2e_precheck_frontend.health_endpoints` | `http://localhost:5173/, http://localhost:8000/health` | 健康检查端点列表（逗号分隔） |
| `e2e_precheck_frontend.health_timeout_ms` | `3000` | 单次健康检查请求超时（毫秒） |
| `e2e_precheck_frontend.retry_count` | `5` | 服务就绪检查失败重试次数 |
| `e2e_precheck_frontend.retry_interval_ms` | `1000` | 重试间隔（毫秒） |
| `e2e_precheck_frontend.abort_on_failure` | `true` | 服务未就绪时是否中止测试 |
| `e2e_precheck_frontend.distinct_report_section` | `true` | 测试报告中是否独立 preflight 段 |
| `e2e_precheck_frontend.connection_refused_indicator` | `ERR_CONNECTION_REFUSED, ECONNREFUSED` | 标识"服务未起"的错误码关键字（逗号分隔） |

> 适用场景：项目使用 Playwright / Cypress / Selenium / Puppeteer 运行 E2E 测试，且前端 dev server 与后端 API 服务为独立进程。React/Next.js 端口改为 `3000` 或 `4173`；Vue 2 dev server 默认 `8080`（vue-cli）；纯 JavaScript 项目仍适用；Docker Compose 启动可借助 `docker compose up --wait` 内置健康检查。

## 测试用例与代码结构同步审查参数（FR-031）

> 供 references/test-case-sync-frontend-rule.md 引用，禁止在规则文件硬编码。本规则约束 DOM 变更与测试选择器同步、try/catch 静默吞错禁令、选择器优先级与集中化。

| 参数 | 值 | 说明 |
|------|-----|------|
| `test_case_sync_frontend.dom_impact_triggers` | `class rename, id rename, data-testid change, structural change, text change, v-if/v-show change` | 触发测试同步的 DOM 变更类型（逗号分隔） |
| `test_case_sync_frontend.same_commit_required` | `true` | DOM 变更与测试更新必须在同一 commit/PR |
| `test_case_sync_frontend.silence_patterns` | `try/catch with empty body, try/except pass, catch with only console.log` | 禁止的静默吞错模式（逗号分隔） |
| `test_case_sync_frontend.allowed_catch_terminators` | `throw, test.fail, test.skip, pytest.fail, expect.assertions` | catch 块必须包含的至少一种终止符（逗号分隔） |
| `test_case_sync_frontend.selector_priority` | `data-testid, aria-label, role, text, class` | 选择器优先级（从高到低，逗号分隔） |
| `test_case_sync_frontend.class_selector_discouraged` | `true` | 是否禁止 class 选择器（仅用于样式断言时允许） |
| `test_case_sync_frontend.selector_module` | `e2e/selectors.ts` | 集中导出选择器常量的模块路径 |
| `test_case_sync_frontend.selector_lint_files` | `e2e/**/*.spec.ts, e2e/**/*.test.ts, e2e/test_*.py, tests/**/*.spec.ts` | 需扫描选择器同步情况的测试文件 glob（逗号分隔） |

> 适用场景：Vue 3 / React 项目修改 `.vue` / `.tsx` 文件中影响 DOM 的代码、PR 同时涉及前端组件与对应测试用例、Python / TypeScript E2E 测试套件维护。React/Next.js 选择器模块路径改为 `__tests__/selectors.ts`；Vue 2 触发条件相同；纯 JavaScript 通过 ESLint `no-empty-catch` 自动化；Python E2E 通过 `flake8-bugbear` B902 检查。

## 阅读视野优化与输入区固定审查参数（FR-032）

> 供 references/reading-viewport-frontend-rule.md 引用，禁止在规则文件硬编码。本规则约束阅读类视口的版面占比（标题头 ≤15%、内容区 ≥75%）与输入区 sticky bottom + 毛玻璃 + z-index 样式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `reading_viewport_frontend.target_views` | `Query.vue, Reader.vue, Help.vue, ChatView.vue` | 适用本规则的视图文件名清单（逗号分隔） |
| `reading_viewport_frontend.header_max_ratio` | `0.15` | 标题头区垂直占比上限（占视口高度比例） |
| `reading_viewport_frontend.content_min_ratio` | `0.75` | 内容阅读区垂直占比下限 |
| `reading_viewport_frontend.responsive_breakpoint` | `768` | 响应式断点（px），断点下用 mobile_* 阈值 |
| `reading_viewport_frontend.mobile_header_max_ratio` | `0.20` | 移动端标题头占比上限 |
| `reading_viewport_frontend.mobile_content_min_ratio` | `0.65` | 移动端内容区占比下限 |
| `reading_viewport_frontend.input_bar_position` | `sticky` | 输入区定位方式（sticky / fixed） |
| `reading_viewport_frontend.input_bar_bottom` | `0` | 输入区 bottom 偏移（px） |
| `reading_viewport_frontend.input_bar_blur_radius` | `12px` | 毛玻璃模糊半径 |
| `reading_viewport_frontend.input_bar_alpha` | `0.85` | 输入区背景色 alpha 值（0-1） |
| `reading_viewport_frontend.input_bar_min_zindex` | `2` | 输入区最小 z-index |
| `reading_viewport_frontend.input_bar_border_top` | `1px solid rgba(0,0,0,0.08)` | 输入区顶部分隔边框 |
| `reading_viewport_frontend.input_bar_outside_scroll` | `true` | 输入区必须在滚动容器外 |

> 适用场景：Vue 3 阅读类视图（Query.vue / Reader.vue / Help.vue / ChatView.vue 等含大量文本 + 底部输入区的页面）。React/Next.js 可用 Tailwind 类实现，参数仍从 config 读取；Vue 2 兼容；纯 JavaScript 降级为 CSS 审查；移动端优先项目可调整 `responsive_breakpoint` 与 mobile 阈值。

## 主题色变量映射审查参数（FR-035 ~ FR-040）

> 供 references/theme-color-mapping-frontend-rule.md 引用，禁止在规则文件硬编码。
> 复盘来源：仪表盘 .recent-log 与 FloatingChat 在浅色主题下辨识度低，11 处硬编码 rgba() 颜色替换为 CSS 变量。

| 参数 | 值 | 说明 |
|------|-----|------|
| `theme_color_mapping_frontend.enabled` | `true` | 是否启用主题色变量映射审查 |
| `theme_color_mapping_frontend.severity` | `error` | 违规严重级别 |
| `theme_color_mapping_frontend.variable_definition_files` | `["frontend/src/styles/themes.css", "frontend/src/styles/variables.css"]` | CSS 变量定义文件列表（Grep 查找可用变量名） |
| `theme_color_mapping_frontend.whitelist_patterns` | `rgba(255, 255, 255, *), transparent, inherit, currentColor` | 允许硬编码的颜色值模式（逗号分隔，支持通配符） |
| `theme_color_mapping_frontend.forbidden_color_formats` | `rgba(), rgb(), #hex, hsl(), hsla()` | 禁止硬编码的颜色值格式（逗号分隔） |
| `theme_color_mapping_frontend.allowed_alpha_values` | `03, 05, 06, 08, 10, 12, 15, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70` | 允许的 alpha 百分比列表（两位数字，逗号分隔） |
| `theme_color_mapping_frontend.alpha_variable_pattern` | `--accent-{color}-a{NN}` | alpha 变体变量名命名模板 |
| `theme_color_mapping_frontend.color_identifiers` | `cyan, purple, pink, magenta` | 支持的颜色标识列表（替换 {color} 占位符） |
| `theme_color_mapping_frontend.semantic_priority` | `scene_bg, card_bg, text, border, shadow, scrollbar` | 语义变量优先级（从高到低，逗号分隔） |
| `theme_color_mapping_frontend.semantic_variable_map` | `scene_bg=--bg-scene, card_bg=--bg-card-solid, text=--text-base\|--text-muted, border=--accent-{color}-a15, shadow=--glow-{color}, scrollbar=--accent-{color}-a20\|--accent-{color}-a40` | 语义场景到变量名的映射表（\| 分隔多个可选变量） |
| `theme_color_mapping_frontend.edit_tool_preferred` | `true` | 是否优先使用 Edit 精准替换（禁止 Write 重写整个文件） |
| `theme_color_mapping_frontend.edit_threshold_ratio` | `0.5` | 修改范围占文件总行数的阈值，高于此值且文件含非 ASCII 时标记「疑似 Write 重写」 |
| `theme_color_mapping_frontend.backend_typecheck_command` | `npx tsc --noEmit` | 后端类型检查命令 |
| `theme_color_mapping_frontend.frontend_typecheck_command` | `npx vue-tsc --noEmit` | 前端类型检查命令（Vue 项目用 vue-tsc） |
| `theme_color_mapping_frontend.require_both_pass` | `true` | 是否要求前后端类型检查均通过才允许提交 |
| `theme_color_mapping_frontend.test_themes` | `macaron, enterprise, portfolio, creative, product` | PR 须提供的主题切换截图列表（浅色 + 深色） |
| `theme_color_mapping_frontend.light_themes` | `macaron, enterprise, portfolio` | 浅色主题列表（用于对比度验证） |
| `theme_color_mapping_frontend.dark_themes` | `creative, product` | 深色主题列表（用于对比度验证） |

> 适用场景：Vue 3 + CSS 变量分层架构（L1/L2/L3）+ 多主题切换项目。React/Next.js 可用 CSS-in-JS 变量，参数仍从 config 读取；单主题项目将 `enabled` 设为 `false`；CSS-in-JS 项目（styled-components/emotion）变量引用方式改为 `theme.xxx`；Material Design 项目修改 `semantic_priority` 为 `surface, background, on_surface, outline, shadow`。

## Tauri invoke 命令三层声明审查参数（FR-041）

> 供 references/tauri-invoke-rule.md 引用，禁止在规则文件硬编码。本规则约束 Tauri 2.x 桌面应用前端调用 `invoke()` 命令时，命令名必须在 build.rs / capabilities / lib.rs 三层同时声明。

| 参数 | 值 | 说明 |
|------|-----|------|
| `tauri_invoke_frontend.enabled` | `true` | 是否启用 invoke 三层声明审查 |
| `tauri_invoke_frontend.build_manifest_path` | `src-tauri/build.rs` | 第 1 层构建清单文件路径（相对项目根，AppManifest::commands 数组所在） |
| `tauri_invoke_frontend.capabilities_path` | `src-tauri/capabilities/default.json` | 第 2 层权限清单文件路径（permissions 数组所在） |
| `tauri_invoke_frontend.runtime_handler_path` | `src-tauri/src/lib.rs` | 第 3 层运行时注册文件路径（invoke_handler + generate_handler! 所在） |
| `tauri_invoke_frontend.commands` | `[]` | 项目实际使用的 invoke 命令名清单（逗号分隔）；留空表示从前端源码自动扫描 invoke('xxx') 调用 |
| `tauri_invoke_frontend.permission_prefix` | `allow-` | 第 2 层权限名前缀，去除后与命令名比对（如 `allow-save-config` → `save-config`） |
| `tauri_invoke_frontend.error_keyword_layer1` | `Plugin not found` | 第 1 层缺失的运行时错误关键词 |
| `tauri_invoke_frontend.error_keyword_layer2` | `not allowed` | 第 2 层缺失的运行时错误关键词 |
| `tauri_invoke_frontend.error_keyword_layer3` | `command not found` | 第 3 层缺失的运行时错误关键词 |
| `tauri_invoke_frontend.plugin_command_allowlist` | `start_dragging, set_title, set_size, set_position, close, show, hide, maximize, minimize, unmaximize, unminimize` | 插件自带命令白名单（逗号分隔），不纳入三层检查（由 Tauri window/shell 等插件注册） |

> 适用场景：Tauri 2.x 桌面应用项目，前端通过 `@tauri-apps/api` 的 `invoke()` 调用 Rust 后端命令。Tauri 1.x 项目不适用（命令注册机制不同，无 capabilities 权限层）；纯 Web 项目不适用；Electron 项目不适用（IPC 机制不同）。

## Tauri 透明窗口 CSS 覆盖审查参数（FR-042）

> 供 references/tauri-transparent-css-rule.md 引用，禁止在规则文件硬编码。本规则约束 `transparent: true` 的 Tauri 窗口须对 html/body/#app/* 四层选择器全覆盖透明背景，并在 floating-active 状态下用通配符 + `!important` 强制覆盖。

| 参数 | 值 | 说明 |
|------|-----|------|
| `tauri_transparent_css_frontend.enabled` | `true` | 是否启用透明窗口 CSS 审查 |
| `tauri_transparent_css_frontend.tauri_conf_path` | `src-tauri/tauri.conf.json` | Tauri 配置文件路径，用于读取 `app.windows[].transparent` 字段 |
| `tauri_transparent_css_frontend.floating_active_class` | `floating-active` | 窗口激活态 class 名（挂到 `<html>` 元素上），用于通配符规则选择器 |
| `tauri_transparent_css_frontend.app_root_selector` | `#app` | 前端入口根选择器（Vue 默认 `#app`，React 可改为 `#root`） |
| `tauri_transparent_css_frontend.required_transparent_layers` | `html, body, #app, *` | 必须设置透明背景的四层选择器（逗号分隔） |
| `tauri_transparent_css_frontend.glass_card_selectors` | `.glass-card` | 毛玻璃卡片选择器清单（逗号分隔），须显式声明半透明背景 |
| `tauri_transparent_css_frontend.glass_card_min_alpha` | `0.3` | 毛玻璃卡片背景色最小 alpha 值（低于此值可读性差，告警） |
| `tauri_transparent_css_frontend.forbidden_transparent_properties` | `opacity: 0, visibility: hidden` | 禁止用作窗口透明替代的属性（逗号分隔，会清空文字与子元素） |
| `tauri_transparent_css_frontend.require_global_wrapper` | `true` | scoped 样式场景是否要求 `:global()` 包裹通配符规则 |
| `tauri_transparent_css_frontend.require_important_on_wildcard` | `true` | 通配符规则是否必须带 `!important`（覆盖组件库内联背景） |

> 适用场景：Tauri 2.x 桌面应用，`tauri.conf.json` 中 `app.windows[].transparent = true`，前端含悬浮卡片 / 浮动面板布局。非透明窗口项目、Electron / PWA 项目、全屏独占模式应用不适用。

## Tauri drag+click 冲突处理审查参数（FR-043）

> 供 references/tauri-drag-click-rule.md 引用，禁止在规则文件硬编码。本规则约束同时承担窗口拖动与点击交互的 UI 元素必须用 JS mousedown/mousemove/mouseup 三阶段区分，禁用 `data-tauri-drag-region` 直接挂载。

| 参数 | 值 | 说明 |
|------|-----|------|
| `tauri_drag_click_frontend.enabled` | `true` | 是否启用 drag+click 冲突审查 |
| `tauri_drag_click_frontend.move_threshold_px` | `5` | 鼠标移动阈值（像素），超过此值视为拖动意图而非点击抖动 |
| `tauri_drag_click_frontend.start_dragging_command` | `start_dragging` | 调用 Rust 端启动原生拖动的 invoke 命令名（须与 FR-041 plugin_command_allowlist 中一致） |
| `tauri_drag_click_frontend.drag_region_attribute` | `data-tauri-drag-region` | Tauri 原生 drag 属性名（用于识别误用） |
| `tauri_drag_click_frontend.required_mouse_events` | `mousedown, mousemove, mouseup` | drag+click 元素必须绑定的鼠标事件列表（逗号分隔） |
| `tauri_drag_click_frontend.click_max_move_px` | `5` | 视为 click 的最大移动距离（与 move_threshold_px 通常一致） |
| `tauri_drag_click_frontend.dblclick_timeout_ms` | `300` | 双击间隔（毫秒），元素含 @dblclick 时须额外检查时序 |
| `tauri_drag_click_frontend.allow_data_tauri_drag_region_on_pure_drag` | `true` | 是否允许在纯 drag 元素（无 click 职责）上使用 `data-tauri-drag-region` |
| `tauri_drag_click_frontend.prevent_duplicate_invoke` | `true` | 单次 mousedown 周期内是否禁止重复调用 start_dragging |

> 适用场景：Tauri 2.x 桌面应用，存在同时需要拖动窗口与点击交互的 UI 元素（如悬浮卡片标题栏、可折叠工具栏）。纯拖动元素（无 click 职责）不适用本规则；纯点击元素（无 drag 职责）不适用；浏览器 Web 应用、Electron 项目不适用（拖动机制不同）。

## 测试选择器优先级审查参数（FR-044）

> 测试选择器优先级规则（见 [references/test-selector-priority-rule.md](../references/test-selector-priority-rule.md)）所依赖的参数集中在本节。
> 规则文件不硬编码选择器或等待策略，所有参数从本节读取，便于适配不同测试框架。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `test_selector_priority.enabled` | `true` | 是否启用测试选择器优先级审查 |
| `test_selector_priority.severity` | `suggestion` | 违规严重级别（suggestion = 非阻断性建议） |
| `test_selector_priority.selector_priority_order` | `#id,[data-testid],[aria-label],.class,[placeholder],:has-text()` | 选择器优先级顺序（从高到低） |
| `test_selector_priority.forbidden_wait_strategy` | `networkidle` | 禁用的等待策略（有持续加载资源时） |
| `test_selector_priority.recommended_wait_strategy` | `domcontentloaded` | 推荐的等待策略 |
| `test_selector_priority.persistent_resource_patterns` | `background-image,event-stream,video,polling` | 持续加载资源模式（触发禁用 networkidle） |
| `test_selector_priority.required_stable_attributes` | `id,data-testid` | 关键交互元素必须提供的稳定属性 |

- 适配 Cypress：`forbidden_wait_strategy` 改为 `networkIdle`，`recommended_wait_strategy` 改为 `domContentLoaded`。
- 适配纯静态页面（无背景图/SSE）：`forbidden_wait_strategy` 可设为空字符串跳过检查。