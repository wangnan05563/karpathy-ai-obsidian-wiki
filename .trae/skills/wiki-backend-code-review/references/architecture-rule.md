# 架构审查规则

> 所有参数从 `config/review-config.md` 的"架构审查参数"章节读取，禁止在规则文件中硬编码。

## 适用范围
审查涉及 routes/workflows/engine/vault 分层的代码变更。

## 检查清单

### 1. 分层依赖方向
- ✅ routes → workflows → engine → vault（正确，顺序 `<来自 config.layer_order>`）
- ❌ routes → vault（跨层调用，禁止模式 `<来自 config.cross_layer_call_forbidden>`）
- ❌ vault → routes（反向依赖）

### 2. 单一职责
- 每个模块只负责一个领域
- 路由层只做 HTTP 适配，不包含业务逻辑
- 工作流层包含业务逻辑，不包含 HTTP 适配

### 3. 依赖注入
- EngineAdapter 通过构造函数注入
- VaultService 通过构造函数注入
- 禁止在模块内部 new 依赖实例

### 4. 模块导出
- 每个模块只导出必要的接口
- 内部实现不暴露

## 交叉引用
- ESM 全局变量、模块接线、路由注册相关：[esm-and-wiring-rule.md](esm-and-wiring-rule.md)
- 安全相关：[security-rule.md](security-rule.md)
- 配置读取一致性：[config-consistency-rule.md](config-consistency-rule.md)
- 热更新闭环：[hot-update-rule.md](hot-update-rule.md)
