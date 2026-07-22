# Rule Catalog — Element Plus

Element Plus 组件使用审查规则：确保 UI 反馈使用组件库 API，禁止原生弹窗。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

## 消息提示用 ElMessage，禁止 alert/confirm

IsUrgent: True
Category: Element Plus

### Description

用户反馈类提示必须使用 `ElMessage`（success/error/warning/info），确认对话必须使用 `ElMessageBox.confirm`。禁止使用浏览器原生 `alert`/`confirm`/`prompt`——它们会阻塞主线程、无法被主题覆盖、破坏视觉一致性。

### Suggested Fix

把原生弹窗替换为 `ElMessage` 或 `ElMessageBox`，并按语义选择 type。

> **示例代码**: 参见 [examples/element-plus-rule-examples.md](examples/element-plus-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 按钮须用 el-button，含 size 和 type 属性

IsUrgent: False
Category: Element Plus

### Description

交互按钮统一使用 `el-button`，并显式声明 `size`（`large`/`default`/`small`）与 `type`（`primary`/`success`/`warning`/`danger`/`info`/`default`）。缺省 size 会导致不同区域按钮高度不一致；缺省 type 会让主操作与次要操作视觉层级模糊。

### Suggested Fix

为每个 `el-button` 补齐 `size` 与 `type`；主操作用 `type="primary"`，破坏性操作用 `type="danger"`。

> **示例代码**: 参见 [examples/element-plus-rule-examples.md](examples/element-plus-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 表单校验用 el-form + rules，提交前 validate

IsUrgent: True
Category: Element Plus

### Description

表单必须使用 `el-form` 配合 `rules` 定义校验规则，提交前调用 `formRef.value?.validate()` 校验通过后再发起请求。禁止在提交逻辑里手写 if 校验散落各处——规则集中可维护、可在失焦时即时反馈。

### Suggested Fix

把散落的校验条件改写为 `rules` 对象；提交函数前置 `validate` 回调。

> **示例代码**: 参见 [examples/element-plus-rule-examples.md](examples/element-plus-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 图标从 @element-plus/icons-vue 导入，按需注册

IsUrgent: False
Category: Element Plus

### Description

图标组件从 `@element-plus/icons-vue` 导入，按需引入到使用它的组件，禁止全局注册全部图标以减小打包体积。模板中作为子组件使用，搭配 `el-icon` 包裹以获得统一尺寸。

### Suggested Fix

把 `<i class="el-icon-edit">` 之类用法改为图标组件导入。

> **示例代码**: 参见 [examples/element-plus-rule-examples.md](examples/element-plus-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## loading 状态用 :loading 或 v-loading

IsUrgent: False
Category: Element Plus

### Description

异步操作的 loading 视觉须通过 `el-button` 的 `:loading` 属性或 `v-loading` 指令呈现，禁止自定义"加载中..."文本或自建遮罩。统一机制可保证遮罩层级、动画与无障碍语义一致。

### Suggested Fix

用 `v-loading` 包裹等待区域，或给触发按钮绑定 `:loading`。

> **示例代码**: 参见 [examples/element-plus-rule-examples.md](examples/element-plus-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 弹窗用 el-dialog，须有 title 和 v-model 控制

IsUrgent: True
Category: Element Plus

### Description

模态弹窗统一使用 `el-dialog`，必须通过 `v-model` 控制显隐（而非 `v-if`/`v-show` 自行管理），并显式声明 `title`。自行用 `v-if` 包裹 `div` 实现的弹窗缺少遮罩、焦点陷阱、ESC 关闭等无障碍能力。

### Suggested Fix

把自建模态替换为 `el-dialog`，把控制变量绑到 `v-model`。

> **示例代码**: 参见 [examples/element-plus-rule-examples.md](examples/element-plus-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。
