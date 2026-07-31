# Folding Panel Event Conflict Rule

## 触发关键词
click outside, clickOutside, teleport, el-dropdown, 折叠面板, 事件冲突, mousedown.stop

## 规则

### FPE-1：click outside 监听必须排除面板内控件
**严重级别**：critical

折叠面板的 click outside 关闭监听必须排除面板内所有控件，特别是 teleport-to-body 的下拉菜单（如 `el-dropdown`）。

**为什么**：Element Plus 的 `el-dropdown` 菜单默认 teleport 到 `<body>`，点击菜单项时事件源在 body 而非面板内，click outside 监听会误判为"点击外部"而关闭面板。

**实现模式**（选择器从 `config/coding-standards-config.md` 的 `folding_panel_event` 段读取，禁止在源码硬编码）：
```typescript
import { config } from './config';

function handleAdvancedOutsideClick(event: MouseEvent) {
  const target = event.target as HTMLElement;
  const panel = document.querySelector(config.control_layering.panel_root_class); // 默认 .advanced-settings-panel
  if (panel?.contains(target)) return;
  // teleport-to-body 组件从 config.folding_panel_event.teleport_selectors 读取（逗号分隔）
  const teleportSelectors = config.folding_panel_event.teleport_selectors.split(',');
  for (const sel of teleportSelectors) {
    if (target.closest(sel.trim())) return; // 默认含 .el-dropdown-menu / .el-popover 等
  }
  const trigger = document.querySelector(config.control_layering.trigger_class); // 默认 .advanced-trigger
  if (trigger?.contains(target)) return;
  showAdvanced.value = false;
}
```

### FPE-2：el-dropdown 必须设置 :hide-on-click="false"
**严重级别**：critical

折叠面板内的 `el-dropdown`（如多选下拉）必须设置 `:hide-on-click="false"`，防止点击菜单项时整个下拉关闭。

### FPE-3：el-dropdown-menu 必须添加 @click.stop
**严重级别**：critical

折叠面板内的 `el-dropdown-menu` 必须添加 `@click.stop`，防止点击菜单项时事件冒泡触发外部 click outside。

**实现模式**（事件修饰符从 `config.folding_panel_event.required_event_modifiers` 读取，禁止在源码硬编码）：
```vue
<!-- :hide-on-click 来自 config.folding_panel_event.required_dropdown_props，默认 "hide-on-click: false" -->
<el-dropdown :hide-on-click="false" trigger="click">
  <span class="trigger">多选</span>
  <template #dropdown>
    <!-- @click.stop 来自 config.folding_panel_event.required_event_modifiers，默认 "@click.stop,@mousedown.stop" -->
    <el-dropdown-menu @click.stop>
      <el-dropdown-item v-for="item in items" :key="item">
        <el-checkbox :model-value="selected.includes(item)" @change="toggle(item)" />
        {{ item }}
      </el-dropdown-item>
    </el-dropdown-menu>
  </template>
</el-dropdown>
```

### FPE-4：面板必须用 @mousedown.stop 阻止 mousedown 冒泡
**严重级别**：critical

折叠面板根元素必须添加 `@mousedown.stop`，阻止 mousedown 事件冒泡到 document。

**为什么**：click outside 监听通常绑定 mousedown，如果面板不阻止 mousedown 冒泡，点击面板内任何控件都会触发关闭。

### FPE-5：teleport-to-body 组件必须在 click outside 中显式排除
**严重级别**：critical

使用 teleport-to-body 的组件必须在 click outside 监听中显式排除其选择器。排除列表从 `config.folding_panel_event.teleport_selectors` 读取（逗号分隔，禁止在源码硬编码），默认含：
- `.el-dropdown-menu`（el-dropdown 菜单）
- `.el-popover`（el-popover）
- `.el-select-dropdown`（el-select 下拉）
- `.el-picker-panel`（日期/时间选择器面板）
- `.el-cascader-panel`（级联选择面板）

## 适用场景
- 折叠面板 + click outside 关闭
- 折叠面板内含 el-dropdown / el-select / el-popover 等 teleport 组件
- 多选下拉菜单在面板内

## 不适用场景
- 静态面板（无 click outside）
- 面板内无 teleport 组件
- 全屏弹窗（用 Esc 关闭而非 click outside）

## 检查清单
- [ ] click outside 是否排除面板内控件
- [ ] el-dropdown 是否设置 :hide-on-click="false"
- [ ] el-dropdown-menu 是否添加 @click.stop
- [ ] 面板根元素是否添加 @mousedown.stop
- [ ] teleport-to-body 组件是否在 click outside 中显式排除
