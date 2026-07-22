# 配置一致性审查规则

> 所有参数从 `config/review-config.md` 的"配置一致性审查参数"章节读取，禁止在规则文件中硬编码。

## 适用范围
审查涉及配置读取的代码（config.json、环境变量、热更新）。

## 复盘背景
AI 服务模块开发中，新增 getEffectiveApiKey() 函数，但启动入口仍用 process.env 读取，导致 config.json 中的 apiKey 被忽略，引发 LLM 401 错误。

## 检查清单

### 1. 配置读取一致性
- ✅ 所有读取入口使用统一函数（`<来自 config.required_unified_functions>`）
- ❌ 绕过统一函数直接读 process.env
- ❌ 不同入口读取同一配置项但逻辑不一致

### 2. 检查方法
```powershell
# 查找直接读取环境变量的代码（应使用统一函数）
grep -rn "process.env\[config" api/src

# 查找新增的配置读取函数，确认所有入口已同步
grep -rn "getEffectiveApiKey|loadConfig|saveAiConfig" api/src
```

### 3. 新增配置字段检查
新增配置字段时必须：
- [ ] 在 types.ts 中定义类型
- [ ] 在 config.ts 中实现读取逻辑
- [ ] 在入口文件使用统一函数读取
- [ ] 在 routes 层 GET 接口返回正确状态
- [ ] 在 routes 层 PUT 接口正确保存

### 4. 向后兼容
- ✅ 新增可选字段使用 `?` 标注
- ✅ 读取优先级：新字段 > 环境变量 > 默认值
- ❌ 新增必填字段不提供默认值

## 交叉引用
- ESM 全局变量、模块接线、路由注册相关：[esm-and-wiring-rule.md](esm-and-wiring-rule.md)
- 架构分层相关：[architecture-rule.md](architecture-rule.md)
- 安全相关：[security-rule.md](security-rule.md)
- 热更新闭环：[hot-update-rule.md](hot-update-rule.md)
