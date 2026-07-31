# 功能回滚最小化原则规则（CODING-060）

> 复盘来源：删除问答页侧栏"新对话"按钮后，用户要求恢复展开态的 `.new-btn`（新对话按钮 + Plus 图标）。按删除时的反向顺序恢复（导入→emit→模板→样式→父组件绑定），每步用 Edit 精准替换，避免遗漏。
> 所有可变参数从 `config/coding-standards-config.md` 的 `rollback_minimal` 字段读取，禁止在规则文件中硬编码文件名或步骤数。

## 触发场景

- 误删功能后需恢复
- 需求变更要求恢复已删除的代码
- A/B 测试后回滚到原版本
- Git revert 后需手动恢复部分文件
- 用户反馈"恢复 XXX 功能"

## 规则

### RBM-1：按删除反向顺序恢复

回滚已删除功能时，必须按删除时的**反向顺序**恢复，确保每步的依赖关系满足：

| 删除顺序 | 恢复顺序 |
|---------|---------|
| 1. 删除父组件事件绑定 | 1. 恢复导入（import） |
| 2. 删除模板元素 | 2. 恢复 emit 事件声明 |
| 3. 删除 emit 事件 | 3. 恢复模板元素 |
| 4. 删除导入 | 4. 恢复样式 |
| 5. 删除样式 | 5. 恢复父组件事件绑定 |

### RBM-2：每步用 Edit 精准替换

回滚必须用 Edit 工具精准替换，**禁止用 Write 重写整个文件**（CODING-045 编码守卫）：

```typescript
// 禁止：Write 重写整个文件（编码破坏风险）
Write(file_path, fullContent)

// 必须：Edit 精准替换
Edit(file_path, old_string, new_string)
```

### RBM-3：回滚后必须验证类型检查 + E2E 测试

回滚完成后，必须执行双重验证：
1. `vue-tsc --noEmit`（或 `tsc --noEmit`）类型检查退出码 0
2. E2E 测试通过（或至少相关功能的测试用例通过）

### RBM-4：部分回滚时明确保留删除的部分

当用户要求"恢复展开态的 X，但不恢复折叠态的 Y"时，必须在代码注释中明确标注哪些部分已恢复、哪些保持删除：

```vue
<!-- 已恢复：展开态新对话按钮 -->
<button class="new-btn" @click="emit('newSession')">...</button>

<!-- 保持删除：折叠态加号按钮（二态切换后无 collapsed 状态） -->
<!-- <div class="collapsed-bar">...</div> -->
```

## 设计流程

```
收到回滚需求
   ↓
1. 识别需恢复的功能范围（全部回滚 or 部分回滚）
   ↓
2. 查看删除时的操作顺序（git log 或对话历史）
   ↓
3. 按反向顺序逐步恢复：
   ① 恢复导入（import）
   ② 恢复 emit/props 声明
   ③ 恢复模板元素
   ④ 恢复样式
   ⑤ 恢复父组件绑定
   ↓
4. 每步用 Edit 精准替换
   ↓
5. 部分回滚时，注释标注保留删除的部分
   ↓
6. vue-tsc 类型检查（退出码 0）
   ↓
7. E2E 测试验证（相关功能通过）
   ↓
8. 硬刷新浏览器（Ctrl+F5）验证视觉效果
```

## 适用场景

- 误删功能恢复（如误删按钮、误删事件绑定）
- 需求变更回滚（用户要求恢复已删除的功能）
- A/B 测试后回滚到原版本
- 部分回滚（恢复 A 但不恢复 B，如恢复展开态按钮但不恢复折叠态按钮）
- Git revert 后需手动恢复部分文件

## 不适用场景

- 新功能开发（无历史代码可回滚）
- 全量重写（用 Write 重写整个文件更高效）
- 依赖库版本回滚（用 git checkout 恢复 package.json）
- 配置文件回滚（用 git checkout 恢复 config 文件）

## 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `rollback_minimal.recovery_order` | `["import", "emit", "template", "style", "parent-binding"]` | 恢复顺序 |
| `rollback_minimal.required_tool` | `Edit` | 必须使用的编辑工具（禁止 Write） |
| `rollback_minimal.require_typecheck` | `true` | 回滚后是否必须类型检查 |
| `rollback_minimal.require_e2e_test` | `true` | 回滚后是否必须 E2E 测试 |
| `rollback_minimal.require_partial_annotation` | `true` | 部分回滚时是否必须注释标注 |
