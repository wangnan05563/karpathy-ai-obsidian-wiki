# 构建产物验证规则

## 触发场景

- 执行 `vite build` / `webpack build` 后验证产物可访问性
- 后端 tsx watch / nodemon 未自动加载新构建产物
- 构建产物 HTTP 404 或返回截断内容

## 规则

### BV-1：构建产物必须验证 HTTP 三要素

`vite build` 后必须验证：
1. **HTTP 状态码 = 200**：后端正确托管产物
2. **Content-Length 与磁盘文件大小一致**：避免返回截断内容或错误 JSON
3. **bundle 中包含新增的关键字符串**：确认新代码已打包进产物

### BV-2：后端 watch 模式未加载新产物时必须重启

`tsx watch` / `nodemon` 在 vite 重新构建后可能未自动加载新产物（特别是 hash 文件名变化时），导致 404。必须：
1. 停止旧后端进程（通过端口反查 PID）
2. 重新启动后端
3. 轮询端口进入 Listen 状态
4. 验证健康检查端点返回 200

### BV-3：HTTP 下载内容截断时优先排查 404

若 `Invoke-WebRequest` 下载的 bundle 内容远小于磁盘文件大小，优先检查是否实际返回了 404 JSON 错误响应（如 Fastify 的 `{ "error": "Not Found" }` 通常仅数百字节）。

## 检测方法

```powershell
# 三要素验证
$r = Invoke-WebRequest -Uri "$endpoint" -UseBasicParsing
$diskSize = (Get-Item $bundlePath).Length
if ($r.StatusCode -ne 200) { throw "HTTP 状态码异常: $($r.StatusCode)" }
if ($r.Content.Length -ne $diskSize) { throw "Content-Length 不匹配" }
if (-not $r.Content.Contains($keyString)) { throw "关键字符串未包含" }
```

## 配置参数

所有参数见 [config/coding-standards-config.md](../config/coding-standards-config.md) 的"构建产物验证参数"段。

## 适配说明

- CDN 部署：`serving_endpoint` 改为 CDN URL
- 多入口项目：遍历所有入口文件逐一验证
- SSR 项目：本规则不适用，SSR 无静态 bundle
