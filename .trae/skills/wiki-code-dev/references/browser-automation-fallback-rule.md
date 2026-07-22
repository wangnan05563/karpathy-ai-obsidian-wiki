# 浏览器自动化降级规则

## 触发场景

- Playwright MCP 报 `MCP server is not found`
- browser_use subagent 截图工具不可用
- 需要前端交互验证但无浏览器自动化工具

## 规则

### BAF-1：必须实现三级降级链

浏览器自动化不可用时，必须按以下链路降级，不可静默失败：

1. **Playwright MCP**（首选）：完整的浏览器自动化能力
2. **browser_use subagent**（次选）：通过 Task 工具启动 subagent，支持 DOM 检查、点击、截图
3. **PowerShell + curl.exe/Invoke-WebRequest**（兜底）：仅能验证 HTTP 可访问性与静态内容，无法验证交互

### BAF-2：每级降级必须记录降级原因

降级时必须记录：
- 上一级工具为何失败（如 `MCP server is not found`）
- 降级到哪一级（如 `降级到 browser_use subagent`）
- 降级后能力限制（如 `无法保存截图，但 DOM 检查可用`）

### BAF-3：降级后仍须完成核心验证

即使降级到兜底级别，也必须完成以下核心验证：
- HTTP 状态码验证
- 关键 CSS 类/字符串包含性验证
- 构建产物完整性验证

交互验证（点击、hover、主题切换）若无法完成，须在报告中明确标注"未验证"。

## 检测方法

1. 检查测试脚本是否实现降级链路（至少 2 级）
2. 降级日志是否包含降级原因
3. 降级后是否仍完成核心验证项

## 配置参数

所有参数见 [config/coding-standards-config.md](../config/coding-standards-config.md) 的"浏览器自动化降级参数"段。

## 适配说明

- 无 MCP 环境：`chain` 移除 `playwright-mcp`
- 纯命令行环境：`chain` 仅保留 `powershell-curl`
- CI/CD 环境：用 headless 浏览器替代 MCP
