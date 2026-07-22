# 热更新闭环审查规则

> 所有参数从 `config/review-config.md` 的"热更新闭环审查参数"章节读取，禁止在规则文件中硬编码。

## 适用范围
审查涉及可热更新配置字段的代码（updateConfig、路由层保存逻辑）。

## 复盘背景
保存 AI 配置后 adapter 实例仍持有旧 apiKey，需重启服务才生效。原因是路由层保存配置后未调用 adapter.updateConfig()。

## 检查清单

### 1. updateConfig 方法完整性
- ✅ 所有可热更新字段都在 `<来自 config.hot_update_methods>` 中处理
- ✅ undefined 表示不修改，空串表示清除
- ❌ 可热更新字段未在 `<来自 config.hot_update_methods>` 中处理

### 2. 路由层调用闭环
- ✅ PUT 保存配置后调用 `<来自 config.hot_update_methods>`
- ✅ 热更新后返回最新配置供前端验证
- ❌ 只保存到文件，不热更新运行实例

### 3. 热更新验证
- ✅ 热更新后可通过 GET 接口验证生效
- ✅ 功能测试覆盖"保存→验证"流程

### 4. 闭环流程
```
保存请求 → saveAiConfig（落盘）→ adapter.updateConfig（热更新）→ 返回最新配置
```
流程链：`<来自 config.hot_update_chain>`

### 5. 检查方法
```powershell
# 查找 saveAiConfig 调用，确认附近有 updateConfig
grep -rn "saveAiConfig" api/src/routes

# 查找 updateConfig 实现，确认覆盖所有可热更新字段
grep -rn "updateConfig" api/src/engine
```

## 交叉引用
- ESM 全局变量、模块接线、路由注册相关：[esm-and-wiring-rule.md](esm-and-wiring-rule.md)
- 架构分层相关：[architecture-rule.md](architecture-rule.md)
- 安全相关：[security-rule.md](security-rule.md)
- 配置读取一致性：[config-consistency-rule.md](config-consistency-rule.md)
