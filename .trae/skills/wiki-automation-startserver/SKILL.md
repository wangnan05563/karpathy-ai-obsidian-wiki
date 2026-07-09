---
name: "wiki-automation-startserver"
description: "Karpathy-Wiki 项目服务生命周期自动化管理：启动/停止/重新构建前端/环境检查/状态查询，含环境预检查、日志记录、失败回滚。当用户要求'启动/开始/运行/起一下/打开/跑起来'Karpathy-Wiki 服务，'停止/关闭/退出/停一下/关掉'服务，'重新构建/重新编译/rebuild'前端 SPA，'检查环境/看看环境就绪没/环境是否OK'，或提到'wiki-automation-startserver / Karpathy-Wiki 启动 停止 重建'时调用。仅管理 Karpathy-Wiki 项目自身服务生命周期；其他项目或系统级服务请用 RunCommand 直接操作。"
whenToUse: "用户要求启动/停止/重新构建 Karpathy-Wiki 项目服务，或检查项目运行环境是否就绪、查询服务当前状态（3000/5173 端口）"
triggers:
  - "启动/开始/运行/起一下/打开/跑起来 Karpathy-Wiki/wiki 服务/web"
  - "停止/关闭/退出/停一下/关掉 Karpathy-Wiki 服务"
  - "重新构建/重新编译/rebuild Karpathy 前端/SPA/vite"
  - "检查/看看 Karpathy 项目 环境/依赖 就绪/是否OK"
  - "Karpathy 服务 状态/端口 查询"
  - "wiki-automation-startserver / Karpathy-Wiki 启动 停止 重建"
version: "1.0.0"
updated: "2026-07-09"
---

# Wiki Automation StartServer

整合 `scripts\启动服务.bat`、`scripts\停止服务.bat`、`scripts\前端构建.bat` 三个脚本，提供 Karpathy-Wiki 项目的自动化生命周期管理。

## 项目特征

| 项 | 值 |
|---|---|
| 项目根 | `d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki` |
| 后端 API | `services\api`（Fastify + TypeScript），端口 **3000** |
| 前端 Web | `packages\web`（Vite + Vue3），端口 **5173** |
| 包管理器 | pnpm workspace（`pnpm` 优先，回退 `npm`） |
| 构建产物 | `services\api\public\`（vite outDir，由后端静态托管） |
| 健康检查 | `http://localhost:3000/health` |
| 访问入口 | `http://localhost:5173`（开发模式） |

## 何时触发

满足以下任一条件即应调用本技能：

- 用户要求"启动 / 开始 / 运行" Karpathy-Wiki、wiki web 服务
- 用户要求"停止 / 关闭 / 退出" Karpathy-Wiki 服务
- 用户要求"重新构建 / 重新编译 / rebuild"前端 SPA
- 用户要求检查项目环境是否就绪
- 用户明确提到 `wiki-automation-startserver` 技能名

## 支持的动作

| 动作 | 命令 | 说明 |
|------|------|------|
| 启动 | `start` | 环境检查 → 调用 `启动服务.bat` → 验证 3000/5173 端口 |
| 停止 | `stop` | 调用 `停止服务.bat` → 验证端口已释放 |
| 重新构建 | `rebuild` | 停止 → 调用 `前端构建.bat` → 启动 |
| 环境检查 | `check` | 仅执行依赖与配置检查，不启动服务 |
| 状态查询 | `status` | 查询 3000/5173 端口与进程状态 |

## 执行入口

**统一通过 PowerShell 调用自动化脚本**（不要直接调用 .bat，由脚本内部按序调用）：

```powershell
# 在项目根目录执行
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\automation.ps1 -Action <start|stop|rebuild|check|status>
```

参数说明：
- `-Action`：必填，取值见上表
- `-LogFile`：可选，默认 `logs\automation.log`

## 执行流程

### 1. 启动 (start)

1. **环境预检查**（失败立即终止，不调用 .bat）：
   - `where node` 能找到 Node.js
   - `where pnpm` 或 `where npm` 至少有一个可用（优先 pnpm）
   - `node_modules` 目录存在（根依赖已安装）
   - `services\api\node_modules` 存在（后端依赖已安装）
   - `packages\web\node_modules` 存在（前端依赖已安装）
   - `logs\` 目录存在（不存在则自动创建）
2. **调用** `scripts\启动服务.bat`（内部已做端口清理、依赖检查、后端+前端分别在新窗口启动）
3. **验证**：等待最多 30 秒检查 3000 端口、15 秒检查 5173 端口
4. **失败回滚**：
   - 后端 30 秒未就绪 → 提示检查 `services\api` 下的配置与日志
   - 前端 15 秒未就绪 → 仅告警不回滚（Vite 可能慢启动，可手动访问）

### 2. 停止 (stop)

1. **调用** `scripts\停止服务.bat`（内部已做端口扫描、taskkill /F /T /PID、窗口标题清理）
2. **验证**：检查 3000 与 5173 端口均已释放
3. **失败提示**：若端口仍被占用，列出占用 PID，提示用户手动检查任务管理器

### 3. 重新构建 (rebuild)

按依赖顺序串联执行（**任一步失败立即终止后续步骤**）：

1. **Step 1 停止**：调用 `scripts\停止服务.bat`
   - 必须先停服，否则 vite 构建可能因文件锁定失败
   - 失败 → 提示端口冲突，不进入构建
2. **Step 2 构建**：调用 `scripts\前端构建.bat`
   - 内部执行 `pnpm run build`（vite build），产物输出到 `services\api\public\`
   - 失败 → 不启动服务，提示检查 `packages\web` 与 vite 错误输出
   - 成功验证：`services\api\public\index.html` 存在
3. **Step 3 启动**：调用 `scripts\启动服务.bat`
   - 失败 → 保留构建产物，提示检查后端日志

## 环境检查清单 (check 动作)

按以下顺序检查并输出 ✅ / ❌：

1. **Node.js**：`where node` 并打印版本
2. **包管理器**：`where pnpm`（优先）或 `where npm`，打印版本
3. **根 node_modules**：`node_modules\` 是否存在
4. **后端依赖**：`services\api\node_modules\` 是否存在
5. **前端依赖**：`packages\web\node_modules\` 是否存在
6. **后端入口**：`services\api\src\index.ts` 是否存在
7. **前端入口**：`packages\web\index.html` 是否存在
8. **构建产物**：`services\api\public\index.html` 是否存在（生产模式必需，开发模式可选）
9. **日志目录**：`logs\` 是否存在（不存在则创建）
10. **3000 端口状态**：是否被占用、占用 PID
11. **5173 端口状态**：是否被占用、占用 PID

## 状态查询 (status 动作)

输出当前服务运行状态：

```
========================================
  Karpathy-Wiki 服务状态
========================================
  后端 API (3000)：[运行中] PID=12345
  前端 Web (5173)：[运行中] PID=12346
  健康检查：       http://localhost:3000/health
  访问入口：       http://localhost:5173
========================================
```

或：

```
  后端 API (3000)：[未运行]
  前端 Web (5173)：[未运行]
```

## 日志记录

所有操作写入 `logs\automation.log`，每行格式：

```
2026-07-09 10:30:15 [INFO]  ACTION=start STEP=env-check RESULT=pass
2026-07-09 10:30:16 [INFO]  ACTION=start STEP=call-bat RESULT=pass
2026-07-09 10:30:45 [ERROR] ACTION=start STEP=verify-port RESULT=fail MSG="port 3000 not listening after 30s"
```

字段说明：
- `ACTION`：start / stop / rebuild / check / status
- `STEP`：env-check / call-bat / verify-port / verify-stop / build / clean
- `RESULT`：pass / fail / skip
- `MSG`：失败时的额外信息

## 用户交互接口

AI 智能体在触发本技能时，应：

1. **明确动作**：从用户指令中识别 start/stop/rebuild/check/status，若模糊则用 `AskUserQuestion` 确认
2. **执行前确认**：对 `rebuild` 动作，需提示用户"将停止当前服务并重新构建前端 SPA，确认继续？"
3. **执行中反馈**：每个步骤完成后输出简短进度（如 `[2/3] 构建前端 SPA...`）
4. **执行后总结**：输出最终状态、访问地址（http://localhost:5173）、健康检查 URL、日志路径

## Windows 兼容性要点

- 所有路径使用反斜杠 `\`
- PowerShell 不支持 `&&`，串联命令使用 `;` 或换行
- 调用 .bat 时使用 `cmd /c` 包裹，避免 PowerShell 解析 .bat 中的 `&` 等特殊字符
- 中文脚本名（`启动服务.bat` 等）需指定编码：脚本首行 `chcp 936 >nul 2>&1` 已处理
- 进程清理使用 `taskkill /F /T /PID`，递归终止子进程
- 端口查询使用 `netstat -aon | findstr ":<port>.*LISTENING"`

## 错误处理与回滚

| 错误场景 | 处理方式 |
|---------|---------|
| Node.js 未安装 | 输出修复命令：运行 `scripts\环境配置.bat` 后终止 |
| 包管理器缺失 | 提示安装 pnpm：`npm install -g pnpm` 后终止 |
| `node_modules` 不存在 | 提示运行 `scripts\环境配置.bat` 或 `pnpm install` 后终止 |
| 3000 端口被未知进程占用 | 列出占用 PID，提示用户确认后用 `停止服务.bat` 或手动 `taskkill /F /PID <pid>` |
| 5173 端口被未知进程占用 | 同上 |
| 前端构建失败 | 不启动服务，保留旧 `services\api\public\`（如有），提示检查 vite 错误输出 |
| 启动 30 秒后 3000 端口未监听 | 提示检查 `services\api\` 配置与终端输出 |
| 启动 15 秒后 5173 端口未监听 | 仅告警不回滚（Vite 可能慢启动） |

## 使用示例

**用户**："启动 Karpathy-Wiki"
**AI**：识别为 `start` 动作 → 执行环境检查 → 调用 `scripts\automation.ps1 -Action start` → 输出访问地址

**用户**："重新构建前端"
**AI**：识别为 `rebuild` 动作 → 用 `AskUserQuestion` 确认 → 执行 stop → build → start 三步 → 报告结果

**用户**："检查环境"
**AI**：识别为 `check` 动作 → 执行 `scripts\automation.ps1 -Action check` → 输出 11 项检查清单

**用户**："服务状态"
**AI**：识别为 `status` 动作 → 执行 `scripts\automation.ps1 -Action status` → 输出端口与 PID

## 文件清单

| 文件 | 用途 |
|------|------|
| `.trae\skills\wiki-automation-startserver\SKILL.md` | 本技能指南 |
| `scripts\automation.ps1` | PowerShell 自动化执行器 |
| `scripts\启动服务.bat` | 启动服务原始脚本 |
| `scripts\停止服务.bat` | 停止服务原始脚本 |
| `scripts\前端构建.bat` | 前端 SPA 构建脚本 |
| `logs\automation.log` | 自动化操作日志 |
