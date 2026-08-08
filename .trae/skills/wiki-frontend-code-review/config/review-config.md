# 评审配置 — wiki-frontend-code-review

> 所有可配置参数集中管理。规则文件只描述通用模式，具体数值以本文件为准。

## 项目目录映射

|用途      |目录约定（相对于项目根）|
|----------|-------------------------|
|页面视图  |`frontend/src/views/`|
|状态仓库  |`frontend/src/stores/`|
|通用组件  |`frontend/src/components/`|
|类型定义  |`frontend/src/types/`|
|工具函数  |`frontend/src/utils/`|
|API 请求层|`frontend/src/api/`|

评审范围：仅 `frontend/` 下 `.vue`、`.ts`、`.tsx` 文件。

## 技术栈

|维度      |技术选型                                 |
|----------|-----------------------------------------|
|框架      |Vue 3.4+                                 |
|UI 库     |Element Plus                             |
|状态管理  |Pinia（setup 语法）                      |
|图谱可视化|vis-network 9.x                          |
|语言      |TypeScript（严格模式）                   |
|构建工具  |Vite                                     |
|包管理    |pnpm                                     |

## 组件设计规范

- **IP 头像**：用 `RobotAvatar` 组件，避免静态图片。
- **配色体系**：马卡龙配色（低饱和粉/蓝/绿/黄/紫），CSS 变量管理，禁硬编码色值。
- **卡片样式**：毛玻璃卡片（`backdrop-filter: blur()` + 半透明底 + 细边框）。
- **圆角与间距**：遵循 Element Plus 设计令牌。

## 主题色系统

### 主题列表

|主题 key|标签|基调|
|----------|------|------|
|`macaron`|马卡龙|浅粉浅青 · 圆润可爱|
|`enterprise`|现代企业|科技蓝灰 · 专业可信赖|
|`creative`|创意品牌|霓虹赛博 · 大胆渐变（默认）|
|`product`|产品展示|暗黑霓虹 · 科技未来|
|`ecommerce`|电商零售|明亮扁平 · 橙蓝活力|
|`portfolio`|艺术作品集|米色金黑 · 优雅极简|

### CSS 变量目录

|文件路径|用途|
|----------|------|
|`frontend/src/style.css` `:root`|creative 默认主题变量|
|`frontend/src/styles/themes/macaron.css`|马卡龙主题覆盖|
|`frontend/src/styles/themes/enterprise.css`|现代企业主题覆盖|
|`frontend/src/styles/themes/product.css`|产品展示主题覆盖|
|`frontend/src/styles/themes/ecommerce.css`|电商零售主题覆盖|
|`frontend/src/styles/themes/portfolio.css`|艺术作品集主题覆盖|
|`frontend/src/styles/themes/index.css`|@import 入口|
|`frontend/src/composables/useTheme.ts`|主题状态管理与持久化|

### CSS 变量三层架构

|层级|前缀|用途|
|------|------|------|
|L1 基础调色板|`--neon-*` / `--bg-*` / `--text-*`|主题底色、背景、文字|
|L2 子系统|`--robot-*` / `--graph-*`|IP 形象、图谱节点专属色|
|L3 场景|`--bg-scene` / `--accent-*-aXX`|容器深度背景、半透明强调色|

### alpha 变体命名规则

统一格式：`a` + 两位数字（`a03`~`a70`，见主题文件）。

### 主题色白名单（允许硬编码）

|色值|原因|
|------|------|
|`rgba(255, 255, 255, X)`|纯白高光，所有主题通用|
|`transparent`|透明值，无主题差异|
|`inherit` / `currentColor`|继承值，自动适配|

## 性能阈值

### vis-network 节点数三级降级

|级别|节点数阈值         |降级策略                                                           |
|----|-------------------|-------------------------------------------------------------------|
|L1  |`nodes <= 200`     |默认：平滑曲线、完整物理引擎、完整样式                              |
|L2  |`200 < nodes <= 500`|关闭平滑曲线（`smooth: false`）                                    |
|L3  |`nodes > 500`      |简化节点样式（去阴影/透明度）+ 减少稳定化迭代次数                  |

### 响应式断点

|断点          |行为                                                  |
|--------------|------------------------------------------------------|
|`width >= 768`|默认图谱视图（Canvas 渲染）                           |
|`width < 768` |自动切换为列表视图，减少 Canvas 渲染开销与交互抖动    |

## SSE 事件类型约定

SSE 事件按类型推送，前端分发到 store：

|事件类型  |语义                                      |处理 action|
|----------|------------------------------------------|-----------------------|
|`answer`  |模型回答的增量文本块                      |`appendAnswer`         |
|`refs`    |引用来源列表                              |`setRefs`              |
|`done`    |回答结束标记                              |`finalizeAnswer`       |
|`error`   |流式错误                                  |`markError`            |
|`progress`|进度信息              |`setProgress`          |
|`page`    |分页信息（爬取/修复任务当前页）           |`setPage`              |
|`fixing`  |修复任务开始/进行中                       |`markFixing`           |
|`fixed`   |修复任务完成                             |`markFixed`            |

未知事件记日志不抛异常。

## 配置隔离审查参数

> 配置隔离规则（config-isolation-rule.md）参数。

### 多实例配置维度标识

|维度场景      |标识来源       |localStorage key 模板                 |
|--------------|---------------|--------------------------------------|
|LLM 预设      |预设 key       |`llmPresetConfig:${presetKey}`        |
|多账号        |账号 ID        |`accountConfig:${accountId}`          |

切换实例按 key 模板读取，禁共用同一 key。

### 脱敏值前缀

|字段      |脱敏前缀|含义                                      |
|----------|--------|------------------------------------------|
|`apiKey`  |`****`  |后端返显的脱敏占位，表示未修改原值        |

判断逻辑：`****` 开头视为未修改跳过；else 处理新值（空串=清空）。禁 `value && !value.startsWith` 反向匹配。

### 恢复默认值接口路径

|用途              |HTTP 方法|路径                             |
|------------------|---------|---------------------------------|
|恢复 LLM 预设默认值|`POST`   |`/api/config/llm-preset/reset`   |
|恢复账号配置默认值|`POST`   |`/api/config/account/reset`      |

调用前须弹 `ElMessageBox.confirm` 二次确认。

### 破坏性按钮白名单

以下按钮允许 `type="danger"` 并二次确认：

|按钮文案      |触发动作                      |
|--------------|------------------------------|
|恢复初始配置  |调用恢复默认值接口并刷新表单  |
|删除          |删除预设/账号/单条记录        |

## 适用 / 不适用场景

### 适用

- 评审 `frontend/` 下新增或修改的 Vue 3 / TypeScript 前端文件。
- 评审涉及 Element Plus 组件、Pinia store、vis-network 图谱、SSE 流式消费的代码。
- 提交前自查（pending-change review）或针对指定文件的定向评审（file-targeted review）。

### 不适用

- 后端代码（`api/`、Python、Node 服务端）。
- 纯配置文件（`vite.config.ts` 等），除非涉及上述规则违反。
- 构建脚本/CI/文档/第三方兼容性评估。

## 持久化与存储边界审查参数

> 持久化与存储边界（persistence-boundary-rule.md）参数。

### 存储类型与权威源

|数据类型|浏览器缓存|后端权威源|跨 origin 共享|
|---------|---------------------|-----------|---------------|
|AI 配置（apiKey）|localStorage（仅脱敏值）|`/api/ai/config` + config.json|是|
|历史会话|IndexedDB（降级缓存）|`/api/conversations` + data/conversations/|是|
|LLM 预设 UI|localStorage（baseUrl/model）|无（前端独立）|否|
|主题偏好|localStorage|无（前端独立）|否|

跨 origin 列为"是"的数据以服务器为权威源，浏览器存储仅作降级缓存。

### 敏感数据禁止 localStorage 明文清单

|字段|禁止明文存储原因|替代方案|
|------|----------------|---------|
|`apiKey`（LLM/webSearch）|XSS 风险 + 双轨不一致|后端 config.json 唯一权威源，前端仅展示脱敏值|
|`cpolarAuthtoken`|凭证泄露风险|后端 config.json|
|`certFile` 内容|凭证泄露风险|后端文件系统|

### 降级策略参数

|参数|值|说明|
|------|-----|------|
|`backend_unavailable_fallback`|`indexed-db-cache`|后端不可用时降级到 IndexedDB|
|`cache_write_failure_action`|`non-blocking`|缓存写入失败不阻断主流程|
|`fallback_log_level`|`warn`|降级日志级别（console.warn）|

### 一次性迁移触发条件

|迁移类型|触发条件|幂等性|
|---------|---------|--------|
|IndexedDB → 后端会话|应用启动时检测到 IndexedDB 有数据但后端为空|是（PUT upsert）|
|localStorage apiKey 清理|用户点击"恢复初始配置"或检测到遗留 apiKey:* 键|是（删除操作）|

## 编码安全审查参数

> 编码安全规则（encoding-safety-rule.md）参数。

|参数|值|说明|
|------|-----|------|
|`source_encoding_required`|`utf-8-no-bom`|源文件要求编码|
|`meta_encoding_required`|`utf-8-no-bom`|元配置文件要求编码|
|`encoding_detection`|`utf8-strict-decode`|检测方法（严格 UTF-8 解码）|
|`encoding_scan_scope`|`.vue,.ts,.tsx,.json,.md`|扫描文件扩展名|
|`fffd_indicator`|`U+FFFD`|乱码指示字符|
|`ascii_whitelist`|`true`|纯 ASCII 文件免检|
|`check_replacement_char`|`true`|在严格 UTF-8 解码后额外扫描 `U+FFFD` 替换字符，识别"解码合法但内容已损坏"的文件|
|`replacement_char_threshold`|`0`|允许出现的 `U+FFFD` 数量上限；`0` 表示完全禁止|
|`replacement_char_action`|`block`|命中时的动作：`block` 阻断提交 / `warn` 仅告警|

## 危险操作审查参数

> 危险操作规则（dangerous-action-rule.md）参数。

|参数|值|说明|
|------|-----|------|
|`dry_run_default`|`true`|dry_run 默认值（安全优先）|
|`danger_class`|`danger`|关闭 dry_run 时按钮添加的 CSS 类|
|`confirm_component`|`ElMessageBox.confirm`|二次确认组件|
|`confirm_type`|`warning`|确认弹窗类型||`cancel_no_request`|`true`|取消确认不发起请求||`irreversible_hint_required`|`true`|确认文案须含不可撤销提示|
|`destructive_button_patterns`|`启动\|停止\|保存\|删除\|清除\|重置`|破坏性按钮文案匹配模式（正则 alternation）||`required_guards`|`['loading', 'disabled', 'confirm']`|破坏性按钮须满足的防护类型（至少其一）|
|`guard_min_match`|`1`|至少需满足的防护数量|
|`destructive_button_whitelist`|`[]`|豁免按钮文案清单（如纯前端状态切换按钮）|

## 多表单状态管理参数

> 多表单状态管理（config-state-rule.md / dangerous-action-rule.md）参数。

|参数|值|说明|
|------|-----|------|
|`multi_form_pattern`|`Record<key, FormState>`|多表单状态模式|
|`independent_loading`|`true`|每个表单独立 loading|
|`independent_result`|`true`|每个表单独立 result|
|`reset_on_submit`|`true`|提交时重置 result|

## 前端视图注册审查参数

> 前端视图注册规则（route-registration-frontend-rule.md）参数。

|参数|值|说明|
|------|-----|------|
|`views_directory`|`frontend/src/views/`|视图文件所在目录（相对项目根）|
|`app_entry`|`frontend/src/App.vue`|应用入口文件路径||`view_type_name`|`ViewName`|视图 key 的字面量联合类型名称||`required_hooks`|`['import', 'type', 'v-for', 'v-else-if']`|视图注册须完成的钩子列表|

> 适用：SPA 手动路由（v-if/v-else-if）。vue-router 等自动路由不适用。

## 前后端类型同步审查参数

> 前后端类型同步规则（type-sync-frontend-rule.md）参数。

|参数|值|说明|
|------|-----|------|
|`backend_types_path`|`api/src/types.ts`|后端 types 文件路径（相对项目根）|
|`frontend_types_path`|`frontend/src/types.ts`|前端 types 文件路径|
|`sync_interfaces`|`[]`|需同步的接口名清单；留空表示全部 `export interface` 都需同步|
|`ignore_optional_marker`|`true`|是否忽略 `?` 可选标记差异（后端必填前端可选视为兼容）|

> 适用：全栈 TS 手动 types.ts。GraphQL/tRPC 不适用。

## 敏感字段展示审查参数

> 敏感字段展示规则（sensitive-field-display-rule.md）参数。

|参数|值|说明|
|------|-----|------|
|`sensitive_field_patterns`|`key\|token\|secret\|password\|authtoken`|敏感字段名匹配模式（正则 alternation，大小写不敏感）|
|`display_strategy`|`masked_placeholder`|敏感字段展示策略：`masked`（脱敏值回显）/ `masked_placeholder`（空输入框 + 提示）||`masked_prefix`|`****`|`masked` 策略下脱敏值前缀（用于识别"已是脱敏值"避免二次处理）||`placeholder_hint`|`留空不修改`|`masked_placeholder` 策略下输入框 placeholder 须包含的提示关键词|
|`sensitive_field_whitelist`|`[]`|豁免字段名清单（如内部测试用字段）|

> 适用：后端回显凭证字段。新密码输入框不适用。

## 滚动容器审查参数

> 滚动容器规则（scroll-container-rule.md）参数。

|参数|值|说明|
|------|-----|------||`scroll_container.max_overflow_layers`|`1`|容器链路上 `overflow-y: auto` 最大嵌套层数；超过即告警||`scroll_container.flex_shrink_required_in_flex_column`|`true`|`flex-direction: column + flex: 1` 容器内的自然高度子项须 `flex-shrink: 0`|
|`scroll_container.glass_card_selectors`|`.glass-card`|全局可能产生 `overflow: hidden` 副作用的卡片类选择器清单|
|`scroll_container.outer_scroll_selectors`|`.content, .app-shell`|已设 `overflow-y: auto` 接管滚动的外层容器选择器清单|

> 适用：Vue 3+flex 多卡片长页面。CSS Grid 不适用。

## SPA 内部跳转审查参数

> SPA 内部跳转规则（spa-navigation-rule.md）参数。

|参数|值|说明|
|------|-----|------|
|`spa_navigation.event_name_pattern`|`{project}:navigate`|事件名模式，`{project}` 占位符运行时替换为 `project_name`|
|`spa_navigation.project_name`|`karpathy`|项目名，替换事件名中的 `{project}` 占位符|
|`spa_navigation.app_entry`|`frontend/src/App.vue`|监听事件的入口组件路径（相对项目根）||`spa_navigation.allowed_views`|`[]`|允许跳转的视图名白名单；留空表示不校验||`spa_navigation.require_lifecycle_pair`|`true`|监听器须在 `onMounted` / `onBeforeUnmount` 配对管理|

> 适用：Vue 3 手动路由 SPA。vue-router 不适用。

## 检查更新审查参数

> 检查更新状态机规则（update-check-rule.md）参数。

|参数|值|说明|
|------|-----|------||`check_update.cache_ttl_ms`|`300000`|后端缓存 TTL(ms)，默认 5 分钟||`check_update.poll_interval_ms`|`300000`|前端轮询间隔(ms)，须 ≥ `cache_ttl_ms`|
|`check_update.first_check_delay_ms`|`5000`|首次检查延迟(ms)，避免与首屏渲染竞争|
|`check_update.latest_to_idle_ms`|`3000`|`latest` 状态自动回 `idle` 的延迟(ms)|
|`check_update.offline_mode`|`true`|离线模式开关；`true` 时后端固定返回 `has_update: false`|
|`check_update.required_states`|`idle, loading, latest, newer, error`|必需状态列表|
|`check_update.update_endpoint`|`/api/about/check-update`|后端检查更新接口路径|
|`check_update.cleanup_hook`|`onBeforeUnmount`|定时器清理生命周期钩子名|

> 适用：Vue 3 轮询检查更新。PWA/Electron 不适用。

## 图标与导航栏审查参数

> 图标与导航栏规则（icon-and-navigation-rule.md）参数。

|参数|值|说明|
|------|-----|------|
|`icon_navigation.enabled`|`true`|启用图标与导航栏审查||`icon_navigation.severity`|`error`|违规严重级别||`icon_navigation.color_attribute`|`currentColor`|SVG 须使用的颜色属性值|
|`icon_navigation.forbidden_color_values`|`#hex, rgb(), rgba(), hsl()`|禁止硬编码的颜色值格式||`icon_navigation.nav_threshold`|`7`|菜单项数量阈值，超过此值须实现双模式|
|`icon_navigation.tooltip_implementation`|`pure-css-hover`|tooltip 实现方式（pure-css-hover=纯 CSS hover，js-tooltip=JS 库）|
|`icon_navigation.transition_mode`|`out-in`|Vue Transition 切换模式|
|`icon_navigation.state_persistence_key`|`navCollapsed`|localStorage 持久化 key 名|
|`icon_navigation.state_persistence_type`|`boolean`|持久化值类型|
|`icon_navigation.expanded_icon_size`|`16`|展开模式图标尺寸|
|`icon_navigation.collapsed_icon_size`|`22`|折叠模式图标尺寸|
|`icon_navigation.tooltip_position`|`bottom`|tooltip 出现位置|
|`icon_navigation.tooltip_delay_ms`|`200`|tooltip 显示延迟(ms)|
|`icon_navigation.glow_filter_template`|`drop-shadow(0 0 {radius}px currentColor)`|主题色光晕滤镜模板|
|`icon_navigation.glow_radius_default`|`4`|光晕默认半径|
|`icon_navigation.glow_radius_hover`|`8`|hover 时光晕半径|
|`icon_navigation.viewbox_standard`|`0 0 24 24`|SVG viewBox 标准|
|`icon_navigation.stroke_width_default`|`1.8`|stroke 默认宽度|
|`icon_navigation.whitelist_pure_white`|`true`|纯白高光 rgba(255,255,255,X) 允许硬编码|

> 适用：Vue 3+多主题+SVG 图标 SPA。单主题/无 hover 不适用。

## 严重级别定义

|参数|值|说明||------|-----|------||`severity_critical`|`🔴 严重`|须修复，阻止合并|
|`severity_warning`|`🟡 警告`|建议修复，不阻止合并|
|`severity_suggestion`|`🟢 建议`|可选优化|
|`severity_positive`|`✅ 优点`|正面反馈|

## Vue 3 审查参数

|参数|值|说明||------|-----|------||`vue.required_script_setup`|`true`|须使用 script setup|
|`vue.required_lang_ts`|`true`|须使用 lang="ts"|
|`vue.forbidden_options_api`|`true`|禁止 Options API||`vue.cleanup_required`|`true`|事件监听器须清理|

## 类型收窄审查参数

|参数|值|说明|
|------|-----|------||`type_narrowing.ref_nullable_pattern`|`computed_or_local_var`|可空 ref 模式||`type_narrowing.ref_await_rule`|`use_local_var`|await 后访问 ref 须用局部变量|
|`type_narrowing.ref_template_rule`|`use_computed`|模板中访问可空 ref 须用计算属性|

## 预设配置审查参数

|参数|值|说明|
|------|-----|------|
|`preset.source`|`backend_api`|预设来源应为后端 API|
|`preset.hardcode_forbidden`|`true`|禁止前端硬编码预设|
|`preset.fetch_pattern`|`fetch('/api/.../presets')`|预设获取模式|

## SSE 消费审查参数

|参数|值|说明|
|------|-----|------|
|`sse.consumer_pattern`|`consumeSSEStream`|SSE 消费统一函数|
|`sse.content_type`|`text/event-stream`|SSE Content-Type|
|`sse.event_format`|`event: <name>\ndata: <json>\n\n`|SSE 事件格式|

## 输出格式参数

|参数|值|说明|
|------|-----|------|
|`output.max_issues_per_section`|`10`|每个级别最多输出条数|
|`output.include_code_snippet`|`true`|包含代码片段|
|`output.include_rule_reference`|`true`|引用规范依据|
|`output.suggest_fix_code`|`true`|提供修复代码示例|

## 编码与运行时审查参数

> encoding-safety-rule.md ES-7~ES-9 参数。

|参数|值|说明||------|-----|------||`encoding.disabled_attribute_required`|`true`|禁用元素须用 disabled 属性|
|`encoding.disabled_attribute_name`|`disabled`|禁用属性名||`encoding.ui_text_consistency_required`|`true`|文本须与设计一致|
|`encoding.ui_text_source`|`设计文档+源码`|文本验证来源|
|`encoding.multi_instance_data_source`|`backend_api,config_file`|多实例来源|
|`encoding.multi_instance_hardcode_forbidden`|`true`|禁硬编码多实例|
|`encoding.theme_list_source`|`config_file`|主题列表来源|
|`encoding.preset_list_source`|`backend_api`|预设列表来源|

## Async 可靠性审查参数

> async-reliability-rule.md 参数。

|参数|值|说明|
|------|-----|------|
|`async_reliability.default_call_timeout_sec`|`5.0`|前端 async 默认超时(s)|
|`async_reliability.heartbeat_interval_sec`|`3.0`|SSE 心跳间隔(s)|
|`async_reliability.heartbeat_miss_threshold`|`3`|心跳丢失阈值|
|`async_reliability.reconnect_enabled`|`true`|SSE 断线自动重连|
|`async_reliability.reconnect_max_retries`|`3`|最大重连次数|
|`async_reliability.reconnect_delay_sec`|`2.0`|重连延迟(s)|
|`async_reliability.timeout_whitelist`|`Promise.resolve,EventSource.open`|超时白名单|
|`async_reliability.ui_feedback_required`|`true`|失败须 UI 反馈|
|`async_reliability.timer_cleanup_required`|`true`|定时器须清理|
|`async_reliability.fallback_ui_patterns`|`ElMessage.error,empty_state,retry_button`|降级 UI 模式|

## 类型检查缓存清理审查参数（FR-026）

> typecheck-cache-frontend-rule.md 参数。 vue-tsc / tsc 幽灵错误（源码已收窄但工具仍报错）。

|参数|值|说明|
|------|-----|------|
|`typecheck_cache_frontend.typecheck_command`|`vue-tsc --noEmit`|类型检查命令|
|`typecheck_cache_frontend.cache_cleanup_targets`|`*.tsbuildinfo,node_modules/.vite,src/**/*.js`|清理缓存 glob|
|`typecheck_cache_frontend.bypass_keywords`|`as any,as unknown as,@ts-ignore,!.`|禁用作常规修复|
|`typecheck_cache_frontend.allow_ts_expect_error`|`true`|允许@ts-expect-error||`typecheck_cache_frontend.test_file_allowlist`|`*.spec.ts,*.test.ts,**/__mocks__/**`|测试文件允许列表||`typecheck_cache_frontend.recheck_after_clean`|`true`|清缓存后须重新执行 typecheck_command 验证|

> 适用：Vue 3 vue-tsc 幽灵错误。

## Composable API 先读后用审查参数（FR-027）

> composable-api-frontend-rule.md 参数。调用 `useXxx` 前必须读源码确认 API 形状，并禁止诊断代码用 `$dispose` / `_s.delete` 重建 store。

|参数|值|说明|
|------|-----|------|
|`composable_api_frontend.use_xxx_pattern`|`use[A-Z]\w*`|composable 调用正则|
|`composable_api_frontend.store_lifecycle_forbidden`|`pinia._s.delete, $dispose, $reset`|诊断禁用的 store API||`composable_api_frontend.diagnostic_allowlist_in_tests`|`*.spec.ts, *.test.ts`|允许上述 API 的测试文件||`composable_api_frontend.must_read_source_before_use`|`true`|调用 useXxx 前须读源码|
|`composable_api_frontend.required_source_read_evidence`|`false`|PR 贴源码片段|
|`composable_api_frontend.cleanup_hooks_to_check`|`onBeforeUnmount, onScopeDispose`|副作用清理钩子|

> 适用：Vue 3 useXxx/Pinia。

## 混合类型运行时分流审查参数（FR-028）

> mixed-type-dispatch-frontend-rule.md 参数。联合类型 `T|U` 升级时的运行时分流方式与跨形态强转禁令。

|参数|值|说明|
|------|-----|------|
|`mixed_type_dispatch_frontend.forbidden_casts`|`as any,as unknown as`|禁跨形态强转|
|`mixed_type_dispatch_frontend.typeguard_module`|`frontend/src/types/guards.ts`|类型守卫模块||`mixed_type_dispatch_frontend.required_dispatch_keywords`|`typeof,in,isXxx`|运行时分流方式||`mixed_type_dispatch_frontend.required_test_per_member`|`true`|联合类型每个成员须有测试覆盖|
|`mixed_type_dispatch_frontend.exhaustive_branch_required`|`true`|消费联合类型的代码须穷尽所有分支|
|`mixed_type_dispatch_frontend.allowed_structural_cast`|`extends,optional field extension`|允许结构强转|

> 适用：联合形态后端/消息总线。

## Vue SFC 单 script 块审查参数（FR-029）

> sfc-single-script-frontend-rule.md 参数。 `.vue` 文件中 `<script>` 块的数量、属性与例外标注。

|参数|值|说明|
|------|-----|------||`sfc_script_block_frontend.allowed_script_count`|`1`|每个 `.vue` 文件允许的 `<script>` 块数量上限||`sfc_script_block_frontend.required_attrs`|`setup, lang="ts"`|须同时具备的 script 块属性|
|`sfc_script_block_frontend.exception_marker`|`// 例外：`|例外注释须包含的关键字|
|`sfc_script_block_frontend.allowed_exceptions`|`named-export-non-reactive,options-extends-compat`|例外场景|
|`sfc_script_block_frontend.banned_macros_in_plain_script`|`defineProps,defineEmits,defineExpose,defineOptions,defineSlots`|禁在非 setup 调用|
|`sfc_script_block_frontend.name_via`|`defineOptions({name})`|组件名声明方式|

> 适用：Vue 3 .vue 文件。

## E2E 测试前置服务检查审查参数（FR-030）

> 供 references/e2e-precheck-frontend-rule.md 引用，禁止在规则文件硬编码。本规则约束 E2E 测试套件执行前的端口监听 + 健康检查 + 失败中止流程。

|参数|值|说明||------|-----|------||`e2e_precheck_frontend.required_ports`|`5173, 8000`|须监听的端口列表（逗号分隔，前端 dev + 后端 API）|
|`e2e_precheck_frontend.health_endpoints`|`http://localhost:5173/,http://localhost:8000/health`|健康检查端点|
|`e2e_precheck_frontend.health_timeout_ms`|`3000`|单次健康检查请求超时(ms)|
|`e2e_precheck_frontend.retry_count`|`5`|重试次数|
|`e2e_precheck_frontend.retry_interval_ms`|`1000`|重试间隔(ms)|
|`e2e_precheck_frontend.abort_on_failure`|`true`|服务未就绪中止|
|`e2e_precheck_frontend.distinct_report_section`|`true`|独立 preflight 段|
|`e2e_precheck_frontend.connection_refused_indicator`|`ERR_CONNECTION_REFUSED,ECONNREFUSED`|服务未起错误码|

> 适用：前后端独立进程 E2E。

## 测试用例与代码结构同步审查参数（FR-031）

> test-case-sync-frontend-rule.md 参数。 DOM 变更与测试选择器同步、try/catch 静默吞错禁令、选择器优先级与集中化。

|参数|值|说明|
|------|-----|------||`test_case_sync_frontend.dom_impact_triggers`|`class rename,id rename,data-testid change,structural change,text change,v-if/v-show change`|DOM 变更触发类型||`test_case_sync_frontend.same_commit_required`|`true`|DOM 变更与测试更新须在同一 commit/PR|
|`test_case_sync_frontend.silence_patterns`|`try/catch empty body,try/except pass,catch only console.log`|禁静默吞错模式||`test_case_sync_frontend.allowed_catch_terminators`|`throw, test.fail, test.skip, pytest.fail, expect.assertions`|catch 块须包含的至少一种终止符|
|`test_case_sync_frontend.selector_priority`|`data-testid,aria-label,role,text,class`|选择器优先级|
|`test_case_sync_frontend.class_selector_discouraged`|`true`|禁 class 选择器|
|`test_case_sync_frontend.selector_module`|`e2e/selectors.ts`|选择器模块路径|
|`test_case_sync_frontend.selector_lint_files`|`e2e/**/*.spec.ts,e2e/**/*.test.ts,e2e/test_*.py,tests/**/*.spec.ts`|测试文件 glob|

> 适用：组件+测试同步变更 PR。

## 阅读视野优化与输入区固定审查参数（FR-032）

> reading-viewport-frontend-rule.md 参数。阅读类视口的版面占比（标题头 ≤15%、内容区 ≥75%）与输入区 sticky bottom + 毛玻璃 + z-index 样式。

|参数|值|说明|
|------|-----|------|
|`reading_viewport_frontend.target_views`|`Query.vue,Reader.vue,Help.vue,ChatView.vue`|适用视图|
|`reading_viewport_frontend.header_max_ratio`|`0.15`|标题头占比上限|
|`reading_viewport_frontend.content_min_ratio`|`0.75`|内容区占比下限|
|`reading_viewport_frontend.responsive_breakpoint`|`768`|响应式断点，断点下用 mobile_* 阈值|
|`reading_viewport_frontend.mobile_header_max_ratio`|`0.20`|移动端标题头占比上限|
|`reading_viewport_frontend.mobile_content_min_ratio`|`0.65`|移动端内容区占比下限|
|`reading_viewport_frontend.input_bar_position`|`sticky`|输入区定位|
|`reading_viewport_frontend.input_bar_bottom`|`0`|输入区 bottom 偏移|
|`reading_viewport_frontend.input_bar_blur_radius`|`12px`|毛玻璃模糊|
|`reading_viewport_frontend.input_bar_alpha`|`0.85`|背景 alpha|
|`reading_viewport_frontend.input_bar_min_zindex`|`2`|输入区最小 z-index||`reading_viewport_frontend.input_bar_border_top`|`1px solid rgba(0,0,0,0.08)`|输入区顶部分隔边框||`reading_viewport_frontend.input_bar_outside_scroll`|`true`|输入区须在滚动容器外|

> 适用：Vue 3 阅读视图+底部输入区。React 用 Tailwind。

## 主题色变量映射审查参数（FR-035 ~ FR-040）

> theme-color-mapping-frontend-rule.md 参数。复盘：仪表盘 .recent-log 与 FloatingChat 在浅色主题下辨识度低，11 处硬编码 rgba() 颜色替换为 CSS 变量。

|参数|值|说明|
|------|-----|------|
|`theme_color_mapping_frontend.enabled`|`true`|启用主题色变量映射审查|
|`theme_color_mapping_frontend.severity`|`error`|违规严重级别|
|`theme_color_mapping_frontend.variable_definition_files`|`["frontend/src/styles/themes.css","frontend/src/styles/variables.css"]`|变量定义文件|
|`theme_color_mapping_frontend.whitelist_patterns`|`rgba(255,255,255,*),transparent,inherit,currentColor`|允许硬编码模式|
|`theme_color_mapping_frontend.forbidden_color_formats`|`rgba(),rgb(),#hex,hsl(),hsla()`|禁止硬编码格式|
|`theme_color_mapping_frontend.allowed_alpha_values`|`03,05,06,08,10,12,15,18,20,25,30,35,40,45,50,60,70`|alpha 值列表|
|`theme_color_mapping_frontend.alpha_variable_pattern`|`--accent-{color}-a{NN}`|alpha 变体命名模板|
|`theme_color_mapping_frontend.color_identifiers`|`cyan,purple,pink,magenta`|颜色标识列表|
|`theme_color_mapping_frontend.semantic_priority`|`scene_bg,card_bg,text,border,shadow,scrollbar`|语义变量优先级|
|`theme_color_mapping_frontend.semantic_variable_map`|`scene_bg=--bg-scene, card_bg=--bg-card-solid, text=--text-base\|--text-muted, border=--accent-{color}-a15, shadow=--glow-{color}, scrollbar=--accent-{color}-a20\|--accent-{color}-a40`|语义场景到变量名的映射表（\|分隔多个可选变量）|
|`theme_color_mapping_frontend.edit_tool_preferred`|`true`|优先 Edit 替换|
|`theme_color_mapping_frontend.edit_threshold_ratio`|`0.5`|修改行数比阈值|
|`theme_color_mapping_frontend.backend_typecheck_command`|`npx tsc --noEmit`|后端类型检查命令|
|`theme_color_mapping_frontend.frontend_typecheck_command`|`npx vue-tsc --noEmit`|前端类型检查命令（Vue 项目用 vue-tsc）|
|`theme_color_mapping_frontend.require_both_pass`|`true`|须前后端类型检查均通过|
|`theme_color_mapping_frontend.test_themes`|`macaron,enterprise,portfolio,creative,product`|须截图主题列表|
|`theme_color_mapping_frontend.light_themes`|`macaron,enterprise,portfolio`|浅色主题|
|`theme_color_mapping_frontend.dark_themes`|`creative,product`|深色主题|

> 适用：Vue 3+CSS 变量多主题。

## Tauri invoke 命令三层声明审查参数（FR-041）

> tauri-invoke-rule.md 参数。 Tauri 2.x 桌面应用前端调用 `invoke()` 命令时，命令名必须在 build.rs / capabilities / lib.rs 三层同时声明。

|参数|值|说明|
|------|-----|------|
|`tauri_invoke_frontend.enabled`|`true`|启用 invoke 三层声明审查|
|`tauri_invoke_frontend.build_manifest_path`|`src-tauri/build.rs`|L1 构建清单路径|
|`tauri_invoke_frontend.capabilities_path`|`src-tauri/capabilities/default.json`|L2 权限清单路径|
|`tauri_invoke_frontend.runtime_handler_path`|`src-tauri/src/lib.rs`|L3 运行时注册路径|
|`tauri_invoke_frontend.commands`|`[]`|invoke 命令名（留空=自动扫描）|
|`tauri_invoke_frontend.permission_prefix`|`allow-`|L2 权限名去前缀|
|`tauri_invoke_frontend.error_keyword_layer1`|`Plugin not found`|第 1 层缺失的运行时错误关键词|
|`tauri_invoke_frontend.error_keyword_layer2`|`not allowed`|第 2 层缺失的运行时错误关键词|
|`tauri_invoke_frontend.error_keyword_layer3`|`command not found`|第 3 层缺失的运行时错误关键词|
|`tauri_invoke_frontend.plugin_command_allowlist`|`start_dragging,set_title,set_size,set_position,close,show,hide,maximize,minimize,unmaximize,unminimize`|插件命令白名单|

> 适用：Tauri 2.x。1.x/Web 不适用。

## Tauri 透明窗口 CSS 覆盖审查参数（FR-042）

> tauri-transparent-css-rule.md 参数。 `transparent: true` 的 Tauri 窗口须对 html/body/#app/* 四层选择器全覆盖透明背景，并在 floating-active 状态下用通配符 + `!important` 强制覆盖。

|参数|值|说明|
|------|-----|------|
|`tauri_transparent_css_frontend.enabled`|`true`|启用透明窗口 CSS 审查|
|`tauri_transparent_css_frontend.tauri_conf_path`|`src-tauri/tauri.conf.json`|Tauri 配置路径|
|`tauri_transparent_css_frontend.floating_active_class`|`floating-active`|激活态 class||`tauri_transparent_css_frontend.app_root_selector`|`#app`|根选择器||`tauri_transparent_css_frontend.required_transparent_layers`|`html, body, #app, *`|须设置透明背景的四层选择器|
|`tauri_transparent_css_frontend.glass_card_selectors`|`.glass-card`|毛玻璃卡片选择器|
|`tauri_transparent_css_frontend.glass_card_min_alpha`|`0.3`|最小 alpha|
|`tauri_transparent_css_frontend.forbidden_transparent_properties`|`opacity:0,visibility:hidden`|禁止替代属性||`tauri_transparent_css_frontend.require_global_wrapper`|`true`|须:global()包裹||`tauri_transparent_css_frontend.require_important_on_wildcard`|`true`|通配符规则是否须带 `!important`（覆盖组件库内联背景）|

> 适用：Tauri 2.x transparent 窗口。非透明不适用。

## Tauri drag+click 冲突处理审查参数（FR-043）

> tauri-drag-click-rule.md 参数。同时承担窗口拖动与点击交互的 UI 元素必须用 JS mousedown/mousemove/mouseup 三阶段区分，禁用 `data-tauri-drag-region` 直接挂载。

|参数|值|说明|
|------|-----|------|
|`tauri_drag_click_frontend.enabled`|`true`|启用 drag+click 冲突审查|
|`tauri_drag_click_frontend.move_threshold_px`|`5`|鼠标移动阈值(px)，超过此值视为拖动意图而非点击抖动|
|`tauri_drag_click_frontend.start_dragging_command`|`start_dragging`|调用 Rust 端启动原生拖动的 invoke 命令名（须与 FR-041 plugin_command_allowlist 中一致）||`tauri_drag_click_frontend.drag_region_attribute`|`data-tauri-drag-region`|Tauri drag 属性||`tauri_drag_click_frontend.required_mouse_events`|`mousedown, mousemove, mouseup`|drag+click 元素须绑定的鼠标事件列表|
|`tauri_drag_click_frontend.click_max_move_px`|`5`|click 最大移动|
|`tauri_drag_click_frontend.dblclick_timeout_ms`|`300`|双击间隔(ms)，元素含 @dblclick 时须额外检查时序|
|`tauri_drag_click_frontend.allow_data_tauri_drag_region_on_pure_drag`|`true`|纯 drag 允许原生属性|
|`tauri_drag_click_frontend.prevent_duplicate_invoke`|`true`|禁重复 invoke|

> 适用：Tauri 2.x drag+click 元素。纯 Web 不适用。

## 测试选择器优先级审查参数（FR-044）

> 测试选择器优先级（test-selector-priority-rule.md）参数。

|参数|默认值|说明|
|------|--------|------|
|`test_selector_priority.enabled`|`true`|启用测试选择器优先级审查|
|`test_selector_priority.severity`|`suggestion`|违规严重级别（suggestion = 非阻断性建议）|
|`test_selector_priority.selector_priority_order`|`#id,[data-testid],[aria-label],.class,[placeholder],:has-text()`|选择器优先级顺序（从高到低）|
|`test_selector_priority.forbidden_wait_strategy`|`networkidle`|禁用等待策略|
|`test_selector_priority.recommended_wait_strategy`|`domcontentloaded`|推荐等待策略||`test_selector_priority.persistent_resource_patterns`|`background-image,event-stream,video,polling`|持续加载资源模式||`test_selector_priority.required_stable_attributes`|`id,data-testid`|关键交互元素须提供的稳定属性|

- 适配 Cypress：`forbidden_wait_strategy` 改为 `networkIdle`，`recommended_wait_strategy` 改为 `domContentLoaded`。
- 适配纯静态页面（无背景图/SSE）：`forbidden_wait_strategy` 可设为空字符串跳过检查。

## 控件分层（FR-045）|control-layering-frontend-rule.md

|`control_layering_frontend.enabled`|`true`|启用|
|`control_layering_frontend.threshold`|`5`|控件分层阈值|
|`control_layering_frontend.frequent_threshold`|`3`|主操作保留阈值|
|`control_layering_frontend.button_bar_selector`|`.button-bar`|工具栏选择器|
|`control_layering_frontend.input_area_selector`|`.input-area`|输入区选择器|
|`control_layering_frontend.transition_name_prefix`|`panel-`|Transition name 前缀|
|`control_layering_frontend.panel_root_selectors`|`.folding-panel,.el-collapse,.el-popover`|折叠面板根选择器|
|`control_layering_frontend.trigger_active_class`|`is-active`|触发按钮激活态|
|`control_layering_frontend.require_aria_expanded`|`true`|aria-expanded|
|`control_layering_frontend.counted_control_tags`|`button,el-button,el-dropdown,el-input,el-switch,el-tooltip`|纳入统计标签|

## 第三方库错误防护（FR-046）|third-party-error-guard-frontend-rule.md

|`third_party_error_guard_frontend.enabled`|`true`|启用|
|`third_party_error_guard_frontend.libraries`|`mermaid,katex,prism`|审查库列表|
|`third_party_error_guard_frontend.suppress_config_keys`|`mermaid=suppressErrorRendering:true,katex=throwOnError:false,prism=logErrors:false`|各库抑制配置|
|`third_party_error_guard_frontend.parse_method_names`|`parseMermaid,parseKatex,parsePrism`|预校验方法|
|`third_party_error_guard_frontend.error_css_classes`|`.mermaid-error,.katex-error,.prism-error`|错误降级 CSS|
|`third_party_error_guard_frontend.require_container_clear`|`true`|渲染前清空容器|
|`third_party_error_guard_frontend.container_clear_methods`|`innerHTML='',replaceChildren(),empty()`|容器清空方式|
|`third_party_error_guard_frontend.llm_source_patterns`|`EventSource,fetch(stream),consumeSSEStream,OpenAI,Claude,LLM`|LLM 流式源|
|`third_party_error_guard_frontend.max_content_length`|`10000`|预校验长度上限|
|`third_party_error_guard_frontend.fallback_message`|`渲染失败，请检查内容语法`|降级提示文案|
|`third_party_error_guard_frontend.version_change_files`|`package.json,pnpm-lock.yaml,package-lock.json,yarn.lock`|版本升级文件|

## 折叠面板事件冲突（FR-047）|folding-panel-event-frontend-rule.md

|`folding_panel_event_frontend.enabled`|`true`|启用|
|`folding_panel_event_frontend.click_outside_exclude_selectors`|`.folding-panel,.folding-panel *`|click outside 排除|
|`folding_panel_event_frontend.teleport_selectors`|`.el-dropdown-menu,.el-popover,.el-select-dropdown,.el-picker-panel,.el-cascader-panel`|teleport 组件|
|`folding_panel_event_frontend.required_dropdown_props`|`hide-on-click:false`|el-dropdown 须属性|
|`folding_panel_event_frontend.required_event_modifiers`|`@click.stop,@mousedown.stop`|事件修饰符|
|`folding_panel_event_frontend.panel_root_selectors`|`.folding-panel,.el-collapse,.el-popover`|面板根选择器|
|`folding_panel_event_frontend.click_outside_patterns`|`v-click-outside,useClickOutside,@click.outside,onClickOutside`|click outside 实现|
|`folding_panel_event_frontend.teleport_to_body_patterns`|`<Teleport to="body">,teleport-to-body,ElTooltip.teleport`|teleport 识别|
|`folding_panel_event_frontend.require_listener_cleanup`|`true`|清理监听器|

## 长短任务架构分离（FR-048）|long-task-architecture-frontend-rule.md

|`long_task_architecture_frontend.enabled`|`true`|启用|
|`long_task_architecture_frontend.sse_threshold_ms`|`30000`|SSE/独立端点分界(ms)|
|`long_task_architecture_frontend.long_task_names`|`video,batch,podcast`|长任务名|
|`long_task_architecture_frontend.short_task_names`|`query,search,summarize`|短任务名|
|`long_task_architecture_frontend.status_code_strategy`|`400=config_redirect,500=external_retry,429=rate_limit_wait,5xx=service_unavailable`|状态码→UI|
|`long_task_architecture_frontend.config_redirect_message`|`配置缺失，请前往配置页设置`|400 提示|
|`long_task_architecture_frontend.external_failure_message`|`外部服务调用失败，请重试`|500 提示|
|`long_task_architecture_frontend.rate_limit_message`|`操作过于频繁，请稍后重试`|429 提示|
|`long_task_architecture_frontend.service_unavailable_message`|`服务暂不可用，请稍后重试`|5xx 提示|
|`long_task_architecture_frontend.retry_after_header`|`Retry-After`|429 header|
|`long_task_architecture_frontend.create_method`|`POST`|创建方法|
|`long_task_architecture_frontend.query_method`|`GET`|查询方法|

## SSE 事件对象分发（FR-049）|sse-event-dispatch-frontend-rule.md

|`sse_event_dispatch_frontend.enabled`|`true`|启用|
|`sse_event_dispatch_frontend.object_dispatch_threshold`|`3`|对象映射表阈值|
|`sse_event_dispatch_frontend.known_event_types`|`answer,refs,done,error,progress,page,image,ppt,video,fixing,fixed`|已知事件类型|
|`sse_event_dispatch_frontend.unknown_event_strategy`|`warn`|未知事件策略|
|`sse_event_dispatch_frontend.output_mode_field`|`outputMode`|结构模式字段|
|`sse_event_dispatch_frontend.output_modes_field`|`outputModes`|事件可见性字段|
|`sse_event_dispatch_frontend.allowed_output_modes`|`normal,mindmap,image,ppt`|允许 outputMode|
|`sse_event_dispatch_frontend.inline_threshold_lines`|`3`|内联行数上限|
|`sse_event_dispatch_frontend.sonarqube_complexity_threshold`|`15`|认知复杂度阈值|

## SSE 流错误处理（FR-050）|sse-stream-error-frontend-rule.md

|`sse_stream_error_frontend.enabled`|`true`|启用|
|`sse_stream_error_frontend.abort_error_indicators`|`AbortError`|用户取消错误名|
|`sse_stream_error_frontend.abort_reason_values`|`user,timeout,null`|abortReason 三态|
|`sse_stream_error_frontend.reader_release_error_indicators`|`already released,AbortError,InvalidStateError`|reader.cancel 异常|
|`sse_stream_error_frontend.signal_param_optional`|`true`|signal 可选|
|`sse_stream_error_frontend.partial_data_strategy`|`mark_truncated`|中断处理策略|
|`sse_stream_error_frontend.loading_state_fields`|`isLoading,isStreaming,isGenerating`|须复位 loading 字段|
|`sse_stream_error_frontend.finally_cleanup_required`|`true`|finally 清理 reader|

## 长任务轮询 UI（FR-051）|long-task-polling-ui-frontend-rule.md

|`long_task_polling_ui_frontend.enabled`|`true`|启用|
|`long_task_polling_ui_frontend.poll_interval_ms`|`5000`|轮询间隔(ms)|
|`long_task_polling_ui_frontend.timeout_ms`|`300000`|超时(ms)|
|`long_task_polling_ui_frontend.state_machine_values`|`idle,queued,processing,completed,failed`|状态机|
|`long_task_polling_ui_frontend.abort_reason_values`|`user,timeout,null`|abortReason 三态|
|`long_task_polling_ui_frontend.single_failure_strategy`|`update_error_only`|单次失败策略|
|`long_task_polling_ui_frontend.close_function_name`|`closeDialog`|关闭对话框函数|
|`long_task_polling_ui_frontend.reset_function_name`|`resetState`|重置状态函数|
|`long_task_polling_ui_frontend.cleanup_hooks`|`onBeforeUnmount`|清理钩子|
|`long_task_polling_ui_frontend.required_cleanup_targets`|`abortController,eventListeners,timers`|清理资源|
|`long_task_polling_ui_frontend.long_task_names`|`video,batch,podcast`|长任务名|

## 事件委托（FR-052）|event-delegation-frontend-rule.md

|`event_delegation_frontend.enabled`|`true`|启用|
|`event_delegation_frontend.target_selectors`|`a,button,img,code,.copy-btn,.mermaid`|委托目标选择器|
|`event_delegation_frontend.tag_names_to_handle`|`A,BUTTON,IMG,CODE`|tagName 命中标签|
|`event_delegation_frontend.cleanup_hook`|`onBeforeUnmount`|清理钩子|
|`event_delegation_frontend.global_event_targets`|`globalThis,window,document`|全局事件目标|
|`event_delegation_frontend.library_instances`|`mermaid,marp,monaco,codemirror,chartjs,d3`|库实例|
|`event_delegation_frontend.destroy_method_names`|`destroy,dispose,cleanup,terminate`|销毁方法|
|`event_delegation_frontend.require_named_function_ref`|`true`|具名函数|
|`event_delegation_frontend.vhtml_directive`|`v-html`|v-html 指令|

## 第三方重库动态加载（FR-053）|heavy-library-frontend-rule.md

|`heavy_library_frontend.enabled`|`true`|启用|
|`heavy_library_frontend.dynamic_import_threshold_kb`|`200`|体积阈值|
|`heavy_library_frontend.heavy_libraries`|`mermaid,marpit,monaco,codemirror,chartjs,d3,pdfjs,videojs`|重库清单|
|`heavy_library_frontend.library_module_paths`|`mermaid=mermaid,marpit=@marp-team/marp-core,monaco=monaco-editor,codemirror=codemirror,chartjs=chart.js,d3=d3`|库→包映射|
|`heavy_library_frontend.require_loaded_flag`|`true`|loaded 标志|
|`heavy_library_frontend.require_instance_cache`|`true`|实例缓存|
|`heavy_library_frontend.cjs_compat_pattern`|`mod.X??mod.default?.X`|CJS 兼容|
|`heavy_library_frontend.require_next_tick_in_watch`|`true`|watch 须 nextTick|
|`heavy_library_frontend.fallback_to_raw_content`|`true`|降级原始内容|
|`heavy_library_frontend.fallback_tag`|`pre`|降级标签|
|`heavy_library_frontend.error_suppress_selectors`|`.error-icon,.error-text`|错误元素|
|`heavy_library_frontend.ssr_static_import`|`false`|SSR 导入|

## TS/JS 遮蔽审查参数（FR-061）

> ts-js-shadowing-frontend-rule.md 参数。Vite 默认 `resolve.extensions` 中 `.js` 先于 `.ts`，`src/` 残留 `.js`/`.map` 会导致 `.ts` 修改静默不生效。

|参数|值|说明|
|------|-----|------|
|`ts_js_shadowing_frontend.enabled`|`true`|启用本组规则（FR-061）|
|`ts_js_shadowing_frontend.severity_br061_1`|`critical`|FR-061-1 src/ 残留 .js/.map 违规级别|
|`ts_js_shadowing_frontend.severity_br061_2`|`critical`|FR-061-2 resolve.extensions 顺序违规级别|
|`ts_js_shadowing_frontend.severity_br061_3`|`suggestion`|FR-061-3 验证步骤违规级别|
|`ts_js_shadowing_frontend.src_glob`|`frontend/src/**`|受管控源码目录|
|`ts_js_shadowing_frontend.forbidden_extensions`|`*.js,*.js.map`|禁止出现在 src/ 的扩展名|
|`ts_js_shadowing_frontend.typecheck_command`|`vue-tsc --noEmit`|类型检查命令|
|`ts_js_shadowing_frontend.build_command`|`vite build`|构建命令|

> 适用：Vite + Vue 3 + TypeScript 项目，CI / pre-commit 须含清理与验证。

## 前后端类型同步（SSE done 事件字段新增）审查参数（FR-062）

> type-sync-done-event-rule.md 参数。后端在 API 响应 / SSE 事件（如 `done`）新增字段时，前端 `types.ts` interface 须同 PR 同步，且新字段加法可选。

|参数|值|说明|
|------|-----|------|
|`type_sync_done_event_frontend.enabled`|`true`|启用本组规则（FR-062，扩展 TS-1）|
|`type_sync_done_event_frontend.severity_br062_1`|`critical`|FR-062-1 未同 PR 同步 interface 违规级别|
|`type_sync_done_event_frontend.severity_br062_2`|`critical`|FR-062-2 非加法/非可选违规级别|
|`type_sync_done_event_frontend.backend_types_path`|`api/src/types.ts`|后端 types 路径|
|`type_sync_done_event_frontend.frontend_types_path`|`frontend/src/types.ts`|前端 types 路径|
|`type_sync_done_event_frontend.watch_event_types`|`done,result,progress,error`|重点关注的 SSE 事件类型|
|`type_sync_done_event_frontend.ignore_optional_marker`|`true`|忽略 `?` 可选标记差异|

> 适用：全栈 TS 手动 types.ts。GraphQL / tRPC 不适用。

## 前端运行时数据隐私审查参数（FR-063）

> runtime-data-privacy-frontend-rule.md 参数。前端新增浏览器端持久化命名空间须确认隐私边界与 gitignore，会话默认不服务端存储（对应后端 BR-065）。

|参数|值|说明|
|------|-----|------|
|`runtime_data_privacy_frontend.enabled`|`true`|启用本组规则（FR-063，对应后端 BR-065）|
|`runtime_data_privacy_frontend.severity_br063_1`|`critical`|FR-063-1 敏感字段明文/产物入库违规级别|
|`runtime_data_privacy_frontend.severity_br063_2`|`critical`|FR-063-2 默认服务端存会话违规级别|
|`runtime_data_privacy_frontend.forbidden_localstorage_fields`|`apiKey,authtoken,password,secret,cpolarAuthtoken`|禁止 localStorage 明文字段|
|`runtime_data_privacy_frontend.server_side_sessions_config_field`|`persistSessions`|服务端存会话开关字段|
|`runtime_data_privacy_frontend.gitignore_runtime_artifacts`|`test_screenshots/,test_*.json`|须 gitignore 的运行期产物|

## 打包脚本与安装器审查参数（FR-064）

> packaging-config-rule.md 参数。前端代码（及配套打包/安装器脚本）不得硬编码应与打包或配置同源的常量；用户数据路径须由后端 API 提供，前端不得自行拼接 exe 同级 / Program Files 路径；安装器不得覆盖用户数据。

|参数|值|说明|
|------|-----|------|
|`packaging_config_frontend.enabled`|`true`|启用本组规则（FR-064，对应后端 BR-068 / CODING-PACKAGING-USERDATA）|
|`packaging_config_frontend.severity_br064_1`|`critical`|FR-064-1 前端硬编码机器绝对路径/安装路径/版本号违规级别|
|`packaging_config_frontend.severity_br064_2`|`critical`|FR-064-2 前端自行拼接 exe 同级/Program Files 用户数据路径违规级别|
|`packaging_config_frontend.severity_br064_3`|`suggestion`|FR-064-3 安装器/打包脚本覆盖用户数据违规级别（跨文件核对）|
|`packaging_config_frontend.forbidden_hardcoded_patterns`|`C:\Users\,C:\Program Files,/Applications,/usr/local,/opt/,vaultPath=absolute,version: 'x.y.z' literal`|前端禁止硬编码的路径/版本字面量|
|`packaging_config_frontend.user_data_source`|`backend API (/api/ai/config 等)`|用户数据路径须由后端提供，禁止前端拼接|
|`packaging_config_frontend.version_source`|`package.json / build define / 后端 /version`|版本号须同源派生，禁止前端字面量|
|`packaging_config_frontend.installer_script_glob`|`**/*.iss,**/*.ps1,**/build*.{ps1,sh}`|安装器/构建脚本扫描范围（跨文件核对）|
|`packaging_config_frontend.installer_program_files_flags`|`ignoreversion`|程序文件安装 Flags（升级即覆盖）|
|`packaging_config_frontend.installer_exclude_user_data`|`true`|用户数据（config.json/.env/vault/data）禁止打包到 {app}|

> 适用：Vite + Vue 3 前端项目、打包（SEA/Tauri/Electron/Inno Setup）应用的安装器与构建脚本。不适用：纯静态无打包项目、无桌面分发的 Web 项目（安装器相关子项不适用）。

## Element Plus 单选组件弃用属性审查参数（FR-065）

> element-plus-rule.md FR-065 参数。Element Plus 2.6.0+ 弃用 `el-radio` / `el-radio-button` 的 `label` 作 value，3.0.0 移除；选项值须用 `value`，显示文本用插槽。

|参数|值|说明|
|------|-----|------|
|`element_plus_radio.enabled`|`true`|启用本组规则（FR-065）|
|`element_plus_radio.severity_br065_1`|`critical`|FR-065-1 沿用 `label` 作 value 违规级别|
|`element_plus_radio.severity_br065_2`|`suggestion`|FR-065-2 升级前未全量扫描弃用用法违规级别|
|`element_plus_radio.frontend_glob`|`frontend/src/**/*.vue`|须扫描的源码范围|
|`element_plus_radio.components`|`el-radio,el-radio-button,el-radio-group`|受影响的组件|
|`element_plus_radio.deprecated_value_attr`|`label`|禁止用作选项值的弃用属性|
|`element_plus_radio.replacement_attr`|`value`|替代属性（选项值）|
|`element_plus_radio.display_text_strategy`|`slot`|显示文本改用默认插槽|
|`element_plus_radio.removal_version`|`3.0.0`|该用法被移除的 Element Plus 大版本|
|`element_plus_radio.deprecation_since_version`|`2.6.0`|该用法被标记弃用的 Element Plus 版本|

## 可选契约字段同步审查参数（FR-066）

> optional-contract-field-rule.md 参数。后端在 API 契约（如 CompileInput/QueryInput）新增可选字段、且前端不消费该内部字段时，前端 types.ts 须同 PR 同步声明可选；前端禁止对该字段做必填访问或分支依赖；后端须 `??` 兜底且跨文件核对字段一致性。扩展 TS-1 / FR-062 的"加法+可选"原则。

|参数|值|说明|
|------|-----|------|
|`optional_contract_field_frontend.enabled`|`true`|启用本组规则（FR-066，扩展 TS-1 / FR-062）|
|`optional_contract_field_frontend.severity_br066_1`|`suggestion`|FR-066-1 未在 types.ts 同步声明可选字段违规级别（契约清晰性，非运行时阻断）|
|`optional_contract_field_frontend.severity_br066_2`|`critical`|FR-066-2 对不消费字段做必填访问 / 分支依赖违规级别|
|`optional_contract_field_frontend.severity_br066_3`|`suggestion`|FR-066-3 后端缺运行时兜底 / 跨文件字段不一致违规级别|
|`optional_contract_field_frontend.backend_types_path`|`api/src/types.ts`|后端 types 路径|
|`optional_contract_field_frontend.frontend_types_path`|`frontend/src/types.ts`|前端 types 路径|
|`optional_contract_field_frontend.ignored_unconsumed_internal_fields`|`originalName`|后端专属、前端不消费的可选字段清单（逗号分隔）；这些字段在前端 types.ts 须可选且前端禁止强依赖|
|`optional_contract_field_frontend.watch_request_bodies`|`CompileInput,QueryInput`|重点关注的 API 请求体 interface 名|

> 适用：全栈 TS 手动 types.ts。对应后端 BR-069-4 / BR-026。

> 适用：使用 Element Plus 单选组件的 Vue 3 项目；升级 EP 主版本前须全量迁移。

## 语音合成（TTS）审查参数（FR-067）

> tts-neural-fallback-rule.md 参数。朗读 / 语音合成功能：优先 neural TTS（后端合成端点 + 优质 neural 音色）而非浏览器 Web Speech API；必须保留浏览器 TTS 为优雅降级；SSML 须转义且禁用免费端点不支持的 express-as；播放前校验音频有效性并重试。对应 wiki-code-dev CODING-TTS-*。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tts_neural_fallback_frontend.enabled` | `true` | 启用本组规则（FR-067，对应 wiki-code-dev CODING-TTS-*） |
| `tts_neural_fallback_frontend.severity_prefer_neural` | `suggestion` | FR-TTS-1 未优先 neural TTS 违规级别（建议级，非运行时阻断） |
| `tts_neural_fallback_frontend.severity_fallback_required` | `critical` | FR-TTS-2 缺浏览器 TTS 降级 / 静默失败违规级别 |
| `tts_neural_fallback_frontend.severity_ssml_safety` | `critical` | FR-TTS-3 未转义 SSML / 用 express-as 违规级别 |
| `tts_neural_fallback_frontend.severity_resilience` | `suggestion` | FR-TTS-4 缺音频校验 / 重试违规级别 |
| `tts_neural_fallback_frontend.synthesize_endpoint` | `/api/tts/synthesize` | neural 合成端点路径（前端 provider 调用） |
| `tts_neural_fallback_frontend.voice_whitelist_pattern` | `^[a-z]{2}-[A-Z]{2}-[A-Za-z]+Neural$` | 音色白名单正则（防非法 / 注入 voice） |
| `tts_neural_fallback_frontend.browser_fallback_api` | `speechSynthesis` | 浏览器优雅降级 API |
| `tts_neural_fallback_frontend.retry_count` | `3` | 空 / 失败响应重试次数 |
| `tts_neural_fallback_frontend.mp3_magic_bytes` | `ff f3, ff fb, 49 44 33` | 有效 MP3 魔数（含 ID3 头） |

> 适用：Vue 3 朗读 / 语音合成功能（provider / composable / UI 控件）。纯音频播放器（无合成逻辑）不适用。

## SPA 部署完整性审查参数（FR-068）

> spa-deploy-integrity-frontend-rule.md 参数。前端构建产物部署：outDir 须可被部署注入为全新时间戳目录（不硬编码固定目录原地覆盖，规避 safe-delete 钩子 + 残留旧产物 + 清空在服目录）；部署须最后写入完整性标记供后端门禁识别；前端验证链构建后须校验产物完整。对应后端 BR-071 / wiki-code-dev CODING-SPA-LIVE-DEPLOY。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `spa_live_deploy_frontend.enabled` | `true` | 启用本组规则（FR-068，对应后端 BR-071 / CODING-SPA-LIVE-DEPLOY） |
| `spa_live_deploy_frontend.severity_fresh_dir` | `suggestion` | FR-068-1 outDir 硬编码固定原地覆盖违规级别（建议级） |
| `spa_live_deploy_frontend.severity_marker` | `critical` | FR-068-2 部署缺完整性标记（后端会选到半写入目录）违规级别 |
| `spa_live_deploy_frontend.severity_artifact_check` | `suggestion` | FR-068-3 构建后未校验产物完整违规级别 |
| `spa_live_deploy_frontend.out_dir_env_key` | `BUILD_OUT_DIR` | 部署注入全新输出目录的环境变量键 |
| `spa_live_deploy_frontend.live_dir_pattern` | `public_live_` | 时间戳部署目录前缀（后接数值时间戳） |
| `spa_live_deploy_frontend.complete_marker` | `.deploy-complete` | 完整性标记文件名（必须最后写入） |
| `spa_live_deploy_frontend.require_fresh_dir` | `true` | 部署须写全新目录、不覆盖已存在目录 |
| `spa_live_deploy_frontend.require_marker` | `true` | 部署须产出完整性标记供后端门禁 |

> 适用：前端 `vite.config.ts` 构建配置 + 部署脚本（_deploy_live*.mjs / build*.ps1 / build*.sh）。固定单目录部署（无时间戳切换）放宽 FR-068-1，但仍须 emptyOutDir 不残留旧产物（对应后端 SH-3）。

## 会话跨账户隔离审查参数（FR-069）

> session-isolation-frontend-rule.md 参数。客户端按用户隔离的会话状态（IndexedDB 按 ownerId）在账户切换/登出时须真正失效：Pinia setup store 会话 state ref 必须加入 return 对象（漏加则 reset 不可观测）；auth watch 须先 resetSession 再 load；persistConversation 复用 id 前须以存储实际记录校验归属、他人记录绝不覆盖。对应 wiki-code-dev CODING-SESSION-ISOLATION。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `session_isolation_frontend.enabled` | `true` | 启用本组规则（FR-069） |
| `session_isolation_frontend.severity_return_ref` | `critical` | FR-069-1 会话状态 ref 漏加 return 违规级别 |
| `session_isolation_frontend.severity_reset_on_auth` | `critical` | FR-069-2 账户切换/登出未 resetSession 违规级别 |
| `session_isolation_frontend.severity_persist_owner_check` | `critical` | FR-069-3 复用 id 未校验归属违规级别 |
| `session_isolation_frontend.severity_defense_in_depth` | `suggestion` | FR-069-4 二次防御/严格隔离/落盘后归属违规级别 |
| `session_isolation_frontend.session_state_refs` | `currentConversationId,scopedOwnerId` | 须加入 store return 的会话状态 ref |
| `session_isolation_frontend.auth_watch_signal` | `user?.id` | auth watch 信号（变化即跨账户） |
| `session_isolation_frontend.owner_store` | `chatDb (IndexedDB)` | 会话隔离存储（按 ownerId） |

> 适用：`frontend/src/stores/**/*store*.ts`（会话 state ref 与 return）、`frontend/src/views/**/*.vue`（auth watch 与 reset 调用）、`chatDb.ts` / 持久化层（`persistConversation` / `dbGet` / `dbPut` / `filterByOwner` / `migrateOwnerless`）。纯服务端会话（按 token 自然隔离）、单账户应用不适用。

## BYOK 多用户配置代理审查参数（FR-070）

> 对应 BYOK 多用户密钥代理（前端本地命名空间隔离 + 密钥仅经请求体下发 + 覆盖纯函数 + 缺密钥不回落服务端共享）。CODING-BYOK（wiki-code-dev references/byok-per-user-override-rule.md）。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `byok_per_user_override_frontend.enabled` | `true` | 启用本组规则（FR-070） |
| `byok_per_user_override_frontend.severity_namespace_isolation` | `critical` | FR-070-1 每用户配置未本地命名空间隔离违规级别 |
| `byok_per_user_override_frontend.severity_secret_in_body` | `critical` | FR-070-2 密钥未仅经请求体下发 / 始终下发空块违规级别 |
| `byok_per_user_override_frontend.severity_menu_gate` | `suggestion` | FR-070-3 配置菜单访问门控违规级别 |
| `byok_per_user_override_frontend.user_config_namespaces` | `usercfg::ai::,usercfg::search::,usercfg::tools::` | 按用户命名空间键前缀（键内化 userId） |
| `byok_per_user_override_frontend.config_menu_permission` | `dashboard` | 配置菜单项的可见权限（全员） |
| `byok_per_user_override_frontend.admin_only_tabs` | `schema,system,ai-service,tools,qq-import,prompt-ide` | 仅管理员可见的敏感 tab |
| `byok_per_user_override_frontend.secret_fields` | `apiKey` | 仅经请求体下发、禁止回显 / 日志的敏感字段 |

## 流式回答增量持久化与续答审查参数（FR-071）

> 对应流式回答增量持久化与断点续答（前端流式 UI）。CODING-STREAMING-RESUME（wiki-code-dev references/streaming-resume-rule.md）。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `streaming_resume_frontend.enabled` | `true` | 启用本组规则（FR-071） |
| `streaming_resume_frontend.severity_incremental_persist` | `critical` | FR-071-1 仅完成时落盘、未增量防抖落盘违规级别 |
| `streaming_resume_frontend.severity_no_abort_on_unmount` | `critical` | FR-071-2 卸载 / 切页 abort 在途流违规级别 |
| `streaming_resume_frontend.severity_resume_gate` | `critical` | FR-071-3 续答门禁（仅 streaming 续、interrupted / error 不续）违规级别 |
| `streaming_resume_frontend.persist_debounce_ms` | `1500` | 流式分片增量落盘防抖毫秒 |
| `streaming_resume_frontend.last_active_key` | `LAST_ACTIVE_CONVERSATION` | 上次活跃会话存储键 |
| `streaming_resume_frontend.streaming_status` | `streaming` | 触发续答的会话末条状态 |
| `streaming_resume_frontend.skip_when_loading` | `true` | SPA 重挂载且后台流活跃(isLoading)时跳过续答 |

## 隔离测试纪律（Test Isolation — FR-072）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `test_isolation_frontend.namespaces_prefixes` | `usercfg::`,`tts-config::` | 隔离测试须唯一化的命名空间前缀（每用例用唯一 userId / 线程 id 拼接） |
| `test_isolation_frontend.forbidden_patterns` | `indexedDB.deleteDatabase`,`deleteDatabase` | `beforeEach` 中禁止的删库模式（fake-indexeddb + 已开连接会 onblocked / 泄漏） |
| `test_isolation_frontend.flush_rounds` | `3` | 异步落盘断言前 `await new Promise(r => setTimeout(r, 0))` 的轮数 |
| `test_isolation_frontend.severity_namespace` | `critical` | FR-072-1 未用唯一命名空间 / 用 beforeEach 删库的违规级别 |
| `test_isolation_frontend.severity_flush` | `suggestion` | FR-072-2 异步断言未多轮 flush 的违规级别 |
| `test_isolation_frontend.severity_module_state` | `suggestion` | FR-072-3 后端用例未重置模块态 / mock 的违规级别 |

> 参数与 wiki-auto-testing `indexeddb_test_isolation_check`（`namespace_prefixes` / `forbidden_patterns` / `flush_rounds`）对齐。

## SSML / TTS Prosody 参数前端校验审查参数（FR-073）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `ssml_injection_frontend.enabled` | `true` | 是否启用本规则 |
| `ssml_injection_frontend.rate_regex` | `^(default\|\d{1,3}%\...)$` | 语速白名单正则（绝对百分比 / 相对倍数 / default） |
| `ssml_injection_frontend.volume_regex` | `^(default\|\d{1,3}%\...)$` | 音量白名单正则 |
| `ssml_injection_frontend.pitch_regex` | `^(default\|\d{1,3}Hz\...)$` | 语调白名单正则 |
| `ssml_injection_frontend.default_value` | `default` | 校验失败回退值 |
| `ssml_injection_frontend.escape_chars` | `<>&` | 用户文本拼入 SSML 前须转义字符 |
| `ssml_injection_frontend.forbidden_tags_regex` | `<mstts:express-as` | 免费端点不支持标签（命中即禁止/提示） |
| `ssml_injection_frontend.unsupported_endpoint_code` | `1007` | 免费端点拒绝 SSML 的 WebSocket 关闭码 |

## 安全删 DOM 节点审查参数（FR-074）

> 对应「前端归档按钮迁移」中删除功能 DOM（如 `.msg-actions`）前的引用清零核查（dom-compat-class-frontend-rule.md，与后端 BR-050-2 同一纵深）。删除与引用更新须同一 PR 完成，禁止仅因代码不报错就删除仍被 CSS / 测试引用的 class/id。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `safe_dom_delete.enabled` | `true` | 是否启用本规则 |
| `safe_dom_delete.test_file_patterns` | `**/test_*.py,**/*.spec.ts,**/*.test.ts` | 须核查引用清零的测试文件 glob |
| `safe_dom_delete.verify_methods` | `grep,glob` | class/id 引用交叉验证方法 |
| `safe_dom_delete.stale_reference_threshold` | `0` | 失效 class/id 引用容忍阈值（0 = 必须清零） |
| `safe_dom_delete.require_same_commit` | `true` | DOM 删除与引用更新须同 PR 完成 |
| `safe_dom_delete.preserve_original_class_first` | `true` | DOM 变更时优先保留原 class 名再同步引用 |
| `safe_dom_delete.severity` | `critical` | 删除仍被引用节点导致选择器/断言悬空违规级别 |

## 主题感知图标审查参数（FR-075）

> 对应「前端归档按钮迁移」中新增/修改 SVG 图标的主题感知（theme-aware-icon-frontend-rule.md，TAI）。图标须用 `currentColor`（禁硬编码固定色，否则主题切换下不可见）+ 默认 24x24 + 风格与现有线条图标一致。复用 FR 图标与导航栏审查参数（icon_navigation.*）的 currentColor / viewbox 约定。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `theme_aware_icon.enabled` | `true` | 是否启用本规则 |
| `theme_aware_icon.color_attribute` | `currentColor` | SVG 须使用的颜色属性值（禁硬编码 #hex/rgb/rgba/hsl） |
| `theme_aware_icon.forbidden_color_values` | `#hex,rgb(),rgba(),hsl()` | 禁止硬编码的颜色值格式 |
| `theme_aware_icon.size` | `24` | 图标尺寸（SVG viewBox `0 0 24 24`） |
| `theme_aware_icon.stroke_width_default` | `1.8` | stroke 默认宽度（与现有线条图标一致） |
| `theme_aware_icon.whitelist_pure_white` | `true` | 纯白高光 rgba(255,255,255,X) 允许硬编码 |
| `theme_aware_icon.severity_color` | `critical` | 硬编码固定色导致主题切换不可见违规级别 |
| `theme_aware_icon.severity_style` | `suggestion` | 尺寸/风格与现有图标不一致违规级别 |

## 能力门控同步审查参数（FR-076）

> 对应「前端归档按钮迁移」中前端功能门控（`:can-archive` 等）须随后端契约放宽同步（capability-gating-sync-frontend-rule.md）。后端改为请求体取内容解耦（不再依赖 `sessionId` / 服务端会话）后，前端门控须移除 `!!sessionId` 等过期依赖、改为依据"内容可得性"；前后端放宽须同一变更完成。对应后端 BR-086 / wiki-code-dev CODING-CAPABILITY-GATING-SYNC（与 persistence-client-content-decoupling 同一变更闭环）。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `capability_gating_sync.enabled` | `true` | 是否启用本规则 |
| `capability_gating_sync.sync_with_backend_contract` | `true` | 前端门控须与后端契约同步放宽 |
| `capability_gating_sync.relax_signal` | `content availability` | 放宽依据（内容可得性而非 sessionId 存在） |
| `capability_gating_sync.stale_gating_patterns` | `!!sessionId,!!getSession` | 过期门控依赖模式（命中即告警） |
| `capability_gating_sync.complete_in_same_change` | `true` | 前后端放宽须同一变更完成 |
| `capability_gating_sync.severity` | `critical` | 门控漂移导致功能卡死违规级别 |

## 编辑重发审查参数（FR-077）

> 对应「编辑后重新发送」中删除重发：必须先 `removeMessagesFrom(tailIndex)` 移除尾随 AI 答案，再 `submitQuestion()` 重新插入用户消息并发送；禁止仅移除 AI 答案而漏插用户消息导致「悬空答案」；编辑态不得处于 `isLoading` 等流式中（FR-071-2 卸载不 abort 同一约束）。对应 wiki-code-dev CODING-EDIT-RESEND。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `edit_resend.enabled` | `true` | 是否启用本规则 |
| `edit_resend.remove_then_submit_order` | `true` | 须先 removeMessagesFrom 移除尾随 AI 答案、再 submitQuestion 重新插入用户消息 |
| `edit_resend.resend_user_message_required` | `true` | 编辑重发必须重新插入用户消息（否则悬空答案） |
| `edit_resend.block_while_loading` | `true` | 编辑态处于 isLoading / 流式中时禁止发起重发 |
| `edit_resend.severity` | `critical` | 漏插用户消息导致悬空答案 / 流式中编辑竞态违规级别 |

## 对话自动滚动审查参数（FR-078）

> 对应「流式回答自动滚动」中须用 double rAF（单次 nextTick 过早、内容未 reflow）；用户主动上滑须暂停强制贴底（用 `stickToBottom` 标记避免拉回）；图片 onload 后须补滚（异步高度变化）。监听须 onMounted 绑定、onUnmounted 解绑，避免内存泄漏 / 多实例串扰。对应 wiki-code-dev CODING-STREAMING-AUTOSCROLL。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `chat_autoscroll.enabled` | `true` | 是否启用本规则 |
| `chat_autoscroll.require_double_raf` | `true` | 滚动到底须用 double requestAnimationFrame（禁单次 nextTick） |
| `chat_autoscroll.respect_user_scroll` | `true` | 用户主动上滑须暂停强制贴底（stickToBottom 标记） |
| `chat_autoscroll.reroll_on_image_load` | `true` | 图片 onload 后须补滚（异步高度变化） |
| `chat_autoscroll.bind_unbind_lifecycle` | `true` | 监听须 onMounted 绑定、onUnmounted 解绑 |
| `chat_autoscroll.severity` | `suggestion` | 滚动跳动 / 内存泄漏违规级别 |

## 按钮样式一致性审查参数（FR-079）

> 对应「成对按钮样式统一」中编辑态确认/取消按钮须风格一致（同尺寸/同圆角/同主题变量，禁止一处 primary 另一处 plain 导致视觉失衡）；成对动作按钮（确认/取消、保存/重置）统一用主题 CSS 变量，禁硬编码固定色。对应 wiki-code-dev CODING-BUTTON-STYLE-CONSISTENCY。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `button_style.enabled` | `true` | 是否启用本规则 |
| `button_style.paired_buttons_consistent` | `true` | 成对按钮（确认/取消等）须同尺寸/同圆角/同风格 |
| `button_style.use_theme_variables` | `true` | 按钮样式须用主题 CSS 变量（禁硬编码固定色） |
| `button_style.severity` | `suggestion` | 成对按钮风格失衡 / 硬编码色值违规级别 |

## 编辑框撑满宽度审查参数（FR-080）

> 对应「编辑态输入框撑满」中编辑态 wrapper（`.msg-content-wrapper.editing` / `.msg-edit`）须 `align-items:stretch` + `width:100%` 撑满 Q&A 列宽，禁止 `align-items:flex-end` 导致编辑框比原消息窄、内容被截断。对应 wiki-code-dev CODING-EDITBOX-WIDTH。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `editbox_width.enabled` | `true` | 是否启用本规则 |
| `editbox_width.fill_column_width` | `true` | 编辑态 wrapper 须 align-items:stretch + width:100% 撑满列宽 |
| `editbox_width.forbid_flex_end_shrink` | `true` | 禁止 align-items:flex-end 导致编辑框窄于原消息 |
| `editbox_width.severity` | `suggestion` | 编辑框窄于原消息 / 内容截断违规级别 |

## IndexedDB 写入前剥离响应式代理审查参数（FR-081）

> idb-reactive-clone-frontend-rule.md 参数。凡将 Pinia store state ref / `reactive()` 对象经 `dbPut`/`saveUserConfig`/`idbPut`/`store.put` 写入 IndexedDB 的路径，写入前必须整树深拷贝剥离代理，否则 proxy 无法被 `structuredClone` 克隆 → `DataError: [object Array] could not be cloned` → 静默丢配置。对应 wiki-code-dev CODING-IDB-REACTIVE-CLONE。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `idb_reactive_clone_frontend.enabled` | `true` | 启用本组规则（FR-081） |
| `idb_reactive_clone_frontend.scan_patterns` | `dbPut,saveUserConfig,idbPut,store.put,transactions.add` | 命中即须核对入参是否已深拷贝的 IndexedDB 写入点（逗号分隔） |
| `idb_reactive_clone_frontend.severity_clone_before_put` | `critical` | FR-081-1 直传 reactive 代理导致静默丢配置违规级别 |
| `idb_reactive_clone_frontend.severity_toraw` | `critical` | FR-081-2 用 toRaw() 当深剥离（嵌套代理仍失败）违规级别 |
| `idb_reactive_clone_frontend.severity_structured_clone` | `critical` | FR-081-3 structuredClone(reactiveObj)（代理无法被克隆）违规级别 |
| `idb_reactive_clone_frontend.severity_wrap_clone` | `suggestion` | FR-081-4 封装函数内部统一 clone 防御缺失违规级别 |
| `idb_reactive_clone_frontend.forbidden_unsafe_patterns` | `toRaw(,structuredClone(` | 命中即判违规的"伪剥离"写法 |
| `idb_reactive_clone_frontend.recommended_clone` | `JSON.parse(JSON.stringify(x))` | 推荐深拷贝范式（纯数据模型）；含 Date/函数/undefined 改用 toRaw+递归 |

> 适用：`frontend/src/services/*UserConfig*.ts` / `*store*.ts`（将 store state 写入 IndexedDB 的 `dbPut` / `saveUserConfig` / `idbPut` / `store.put`），以及任何 `reactive()` 对象落盘路径。不适用：localStorage（`JSON.stringify` 序列化到字符串、不受代理影响）、纯服务端（无 Vue reactive）、写入值已是 `JSON.parse` 反序列化的 plain object、IndexedDB 读取（`dbGet` 返回 plain）。

## 审查流程优化（Review Process Optimization）

> 以下判定步骤适用于每次评审，旨在降低误报与漏报。规则文件与脚本不硬编码阈值，所有参数从本文件读取。

### 1. Flake 隔离（Flake Isolation）

当某条测试在完整测试套件中失败，但在单独运行时通过，先**单独运行该测试文件**再决定是否归咎于本次变更。预存在的时序 / 状态 flake 很常见（例如固定窗口限流跨过 60s 边界偶发触发 429，对应后端 BR-063-4；前端 vue-tsc 幽灵错误见 FR-026）。流程：

1. 复现：单独运行失败测试文件（如 `vitest run x.spec.ts` / `playwright test e2e/foo.spec.ts`）。
2. 若单独通过 → 判定为 flake，不计入本次变更问题；记录为预存在 issue。
3. 若单独也失败 → 才进入变更内容排查。

### 2. 变更内容范围（Modified-content Scope）

评审时聚焦**实际变更的文件**，不扩大扫描面：

- 优先用 `git diff` / `git diff --cached` 取得变更文件清单与行号。
- 对新增 / 修改的**路由**或 **API 调用**（涉及 types.ts / SSE 事件），必须运行 `route_registration_check` + `type_sync_check`（前后端 types.ts 同步，见 TS-1 / FR-062）。
- 仅对变更行及其直接上下文应用规则；未变更代码标记为"已验证，跳过"。

### 3. 配置驱动（Config-driven）

所有阈值 / 参数 / 严重级别均从本文件读取，**禁止在审查逻辑（规则文件、脚本、prompt）中硬编码**。新增规则须同步在对应"审查参数"段落追加参数表，并默认从 config 引用。若某判定需要新阈值，先加到本文件再在规则中引用。
