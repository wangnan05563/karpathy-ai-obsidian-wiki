# E2E 测试前置服务检查规则（CODING-030）

> 复盘来源：UI 改造后运行 test_full_e2e.py，首条用例即报 ERR_CONNECTION_REFUSED。根因是改造前未确认服务状态，automation.ps1 启动失败但未察觉。
> 所有可变参数从 `config/coding-standards-config.md` 的 `e2e_precheck` 字段读取，禁止在规则文件中硬编码端口号或健康检查路径。

## 规则

**运行 E2E 测试前必须执行前置服务检查**：确认所有 `required_ports` 已进入 `port_check_state` 状态，且 `health_check_endpoint` 返回 `health_check_expected_status`。检查失败必须先启动服务，禁止直接运行测试用例。

## 适用场景

- 所有 Playwright / Cypress / Puppeteer E2E 测试套件运行前
- 集成测试 / 端到端验证 / UI 自动化测试
- CI/CD 流水线测试阶段启动前
- 手动运行测试脚本前（`python test_full_e2e.py`）

## 不适用场景

- 单元测试（不依赖运行时服务）
- 静态类型检查（tsc / vue-tsc）
- 纯前端组件测试（已 mock 后端）
- 快照测试（不发起真实网络请求）

## 前置检查流程

```
准备运行 E2E 测试
   ↓
1. 遍历 e2e_precheck.required_ports
   ↓
   端口未监听 → 启动服务（automation.ps1 -Action start）→ 等待 startup_timeout_ms
   ↓
2. 调用 e2e_precheck.health_check_endpoint
   ↓
   返回非 e2e_precheck.health_check_expected_status → 启动失败，中止测试
   ↓
3. 检查浏览器可启动（如配置 e2e_precheck.browser_launch_check: true）
   ↓
   浏览器启动失败 → 中止测试
   ↓
4. 运行 E2E 测试用例
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `e2e_precheck.enabled` | `true` | 是否启用前置服务检查 |
| `e2e_precheck.severity` | `error` | 违规严重级别（error = 测试中止） |
| `e2e_precheck.required_ports` | `3000,5173` | 必须监听的端口列表（逗号分隔） |
| `e2e_precheck.port_check_state` | `Listen` | 端口就绪状态判定 |
| `e2e_precheck.port_check_method` | `Get-NetTCPConnection` | 端口检测方法 |
| `e2e_precheck.health_check_endpoint` | `/health` | 健康检查路径 |
| `e2e_precheck.health_check_expected_status` | `200` | 健康检查期望状态码 |
| `e2e_precheck.startup_timeout_ms` | `30000` | 服务启动超时（毫秒） |
| `e2e_precheck.port_poll_interval_ms` | `1000` | 端口轮询间隔（毫秒） |
| `e2e_precheck.browser_launch_check` | `true` | 是否检查浏览器可启动 |
| `e2e_precheck.service_start_script` | `automation.ps1 -Action start` | 服务启动脚本 |
| `e2e_precheck.auto_start_on_failure` | `true` | 检查失败时是否自动启动服务 |

## 检查方式

1. **测试脚本入口检查**：测试套件入口文件必须包含前置检查代码（PowerShell 端口检测 + HTTP 健康检查）
2. **失败中止行为**：前置检查失败时必须中止测试，禁止继续运行用例（避免误报"全部失败"）
3. **日志输出**：前置检查必须输出诊断信息（端口状态、健康检查响应），便于排查

## 正确示例

```python
# test_full_e2e.py 入口
import socket
import urllib.request
import sys

def precheck_services():
    """E2E 测试前置服务检查"""
    required_ports = [3000, 5173]  # 从配置读取
    health_url = "http://localhost:3000/health"
    
    for port in required_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        if result != 0:
            print(f"[PRECHECK] Port {port} not listening")
            return False
    
    try:
        resp = urllib.request.urlopen(health_url, timeout=5)
        if resp.status != 200:
            print(f"[PRECHECK] Health check failed: {resp.status}")
            return False
    except Exception as e:
        print(f"[PRECHECK] Health check error: {e}")
        return False
    
    print("[PRECHECK] All services ready")
    return True

if not precheck_services():
    print("[PRECHECK] Services not ready. Run: automation.ps1 -Action start")
    sys.exit(1)

# 继续运行测试用例...
```

```powershell
# PowerShell 版前置检查
function Test-ServiceReady {
    param([int[]]$RequiredPorts, [string]$HealthEndpoint)
    foreach ($port in $RequiredPorts) {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if (-not $conn) {
            Write-Host "[PRECHECK] Port $port not listening" -ForegroundColor Red
            return $false
        }
    }
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:3000$HealthEndpoint" -UseBasicParsing
        if ($resp.StatusCode -ne 200) { return $false }
    } catch {
        return $false
    }
    return $true
}
```

## 错误示例

```python
# 错误：直接运行测试，无前置检查
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    page = p.chromium.launch()
    page.goto("http://localhost:5173")  # 可能 ERR_CONNECTION_REFUSED
    # 所有用例报"导航失败"，但实际是服务未启动

# 错误：前置检查失败仍继续运行
def precheck():
    # 检查代码...
    return False  # 失败

precheck()  # 调用但不检查返回值
run_tests()  # 继续运行，全部用例误报失败
```

## 适配新项目

- 适配纯前端项目（无后端）：`required_ports` 改为仅前端端口（如 `5173`），`health_check_endpoint` 设为空字符串跳过
- 适配 Docker 部署：`service_start_script` 改为 `docker-compose up -d`
- 适配 CI 环境：`auto_start_on_failure` 设为 `false`（CI 通常已独立启动服务）
- 适配云环境：`port_check_method` 改为 `Test-NetConnection`（跨网络）

## 与其他规则的关系

- 与 CODING-031（测试用例与代码结构同步）联动：CODING-030 确保测试运行环境就绪，CODING-031 确保测试用例与代码结构一致
- 与 PowerShell 约束规则联动：端口检测脚本必须符合 PowerShell 约束（禁用 `&&`）
