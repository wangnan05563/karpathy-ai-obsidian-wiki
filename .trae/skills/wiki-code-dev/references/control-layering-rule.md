# Control Layering Rule

## 触发关键词
工具栏, toolbar, 高级设置, 折叠面板, 控件分层, button-bar, input-area

## 规则

### CL-1：工具栏控件 > 阈值时必须分层
**严重级别**：suggestion

工具栏控件数量超过 `control_layering.threshold`（默认值见 `config/coding-standards-config.md` 的 `control_layering` 段，禁止在源码硬编码）时，必须将控件分层：常用控件保留在主工具栏，低频控件折叠到"高级设置"面板。

**为什么**：工具栏拥挤影响可用性与视觉清晰度。历史问题：Query.vue 工具栏有 6+ 控件挤在一行，多模态选择器/输出模式/流式开关等低频控件占据空间。

**分层标准**：
- 常用控件（使用频率 > `control_layering.frequent_threshold`）：保留主工具栏
- 高级控件（使用频率 ≤ 阈值）：折叠到高级设置面板
- 破坏性控件（如删除/重置）：必须有二次确认，独立放置

### CL-2：折叠面板必须放在 button-bar 外、input-area 内
**严重级别**：critical

折叠面板（高级设置面板）的 HTML 结构位置必须在 `button-bar` 结束之后、`input-area` 结束之前。禁止放在 `button-bar` 内部（会导致布局错乱）。

**为什么**：`button-bar` 是 flex 容器，面板放入其中会被 flex 布局压缩；放在 `button-bar` 外作为兄弟元素，面板可正常展开占满宽度。

**正确的 HTML 结构**（class 名从 `config/coding-standards-config.md` 的 `control_layering` 段读取，禁止在源码硬编码）：
```html
<div class="input-area">  <!-- control_layering.input_area_class，默认 input-area -->
  <div class="button-bar">  <!-- control_layering.button_bar_class，默认 button-bar -->
    <!-- 常用控件 -->
  </div>
  <!-- 高级设置面板：button-bar 的兄弟元素，input-area 的子元素 -->
  <Transition :name="advanced-panel">  <!-- control_layering.transition_component，默认 Transition -->
    <div v-if="showAdvanced" class="advanced-settings-panel" @mousedown.stop>  <!-- control_layering.panel_root_class -->
      <!-- 高级控件 -->
    </div>
  </Transition>
</div>
```

### CL-3：折叠面板展开/收起必须有平滑动画
**严重级别**：suggestion

折叠面板展开/收起必须用 Vue `<Transition>` 组件实现平滑动画，禁止直接 v-if 瞬间显示/隐藏。

**为什么**：瞬间显示/隐藏会造成视觉跳跃，影响用户体验。

**实现模式**（动画时长与缓动函数从 `config/coding-standards-config.md` 的 `control_layering` 段读取）：
```vue
<Transition :name="advanced-panel">
  <div v-if="showAdvanced" class="advanced-settings-panel">
    <!-- 控件 -->
  </div>
</Transition>

<style scoped>
/* duration 与 easing 从 config.control_layering.animation_duration_ms / animation_easing 读取 */
.advanced-panel-enter-active,
.advanced-panel-leave-active {
  transition: all var(--panel-duration, 300ms) var(--panel-easing, ease);
  overflow: hidden;
}
.advanced-panel-enter-from,
.advanced-panel-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
```

### CL-4：触发按钮必须有激活状态视觉反馈
**严重级别**：suggestion

高级设置触发按钮（如齿轮图标）在面板展开时必须有视觉反馈（如旋转 90°、颜色变化），让用户感知当前状态。

**为什么**：无反馈时用户无法判断面板是否已展开，尤其在面板内容未立即渲染时。

### CL-5：面板内控件事件必须阻止冒泡
**严重级别**：critical

折叠面板内的控件（如下拉菜单、输入框）必须用 `@mousedown.stop` / `@click.stop` 阻止事件冒泡，防止触发外部的 click outside 关闭逻辑。

**为什么**：click outside 监听会捕获面板内控件的 mousedown 事件，误判为"点击外部"而关闭面板。详见 [folding-panel-event-rule.md](folding-panel-event-rule.md)。

## 适用场景
- 工具栏控件 > 5 个
- 空间有限的输入区（如聊天框、查询框）
- 控件使用频率差异大（部分常用，部分低频）

## 不适用场景
- 控件 ≤ 3 个（空间充足，无需折叠）
- 所有控件使用频率相近（无法分层）
- 移动端（通常用全屏弹窗而非折叠面板）

## 检查清单
- [ ] 工具栏控件 > 阈值时是否分层
- [ ] 折叠面板是否在 button-bar 外、input-area 内
- [ ] 展开/收起是否有 Transition 动画
- [ ] 触发按钮是否有激活状态反馈
- [ ] 面板内控件是否阻止事件冒泡
