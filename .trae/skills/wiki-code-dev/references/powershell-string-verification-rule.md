# PowerShell 字符串验证规则

## 触发场景

- 在 PowerShell 中验证 HTTP 响应内容是否包含特定字符串
- 用 `curl.exe -s` 下载内容并赋值给变量
- 自动化测试中检查 bundle 是否包含关键 CSS 类

## 规则

### PSV-1：禁用 curl.exe 管道赋值 + .Contains() 模式

PowerShell 中 `$var = curl.exe -s "url"; $var.Contains("keyword")` 模式存在变量捕获陷阱：
- `curl.exe` 输出可能被 PowerShell 解析为多个对象
- 变量赋值后 `.Contains()` 可能因对象类型不一致而输出混乱
- 多行输出时 `$var` 是数组而非字符串，`.Contains()` 行为不可预测

**禁止模式**：
```powershell
$js = curl.exe -s "http://localhost:3000/assets/index.js"
$js.Contains("nav-collapsed")  # 输出可能混乱
```

### PSV-2：必须用 Invoke-WebRequest + .Content.Contains()

**推荐模式**：
```powershell
$r = Invoke-WebRequest -Uri "http://localhost:3000/assets/index.js" -UseBasicParsing
$r.Content.Contains("nav-collapsed")  # 始终返回正确的布尔值
```

`Invoke-WebRequest` 返回的 `HttpResponseMessage` 对象的 `.Content` 属性始终是单一字符串，`.Contains()` 行为可预测。

## 检测方法

1. 扫描测试脚本与 PowerShell 命令中的 `$var = curl.exe` 模式
2. 若后续调用 `$var.Contains()` 或 `$var.Length`，告警
3. 建议改用 `Invoke-WebRequest` + `.Content` 属性

## 配置参数

所有参数见 [config/coding-standards-config.md](../config/coding-standards-config.md) 的"PowerShell 字符串验证参数"段。

## 适配说明

- Linux/Mac bash：`curl` 输出天然是字符串，本规则不适用
- Python 脚本：用 `requests.get().text.contains()` 替代
- Node.js 脚本：用 `fetch().then(r => r.text())` + `String.includes()` 替代
