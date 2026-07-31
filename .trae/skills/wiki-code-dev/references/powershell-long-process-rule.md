# PowerShell 长时进程管道陷阱规则（CODING-059）

> 复盘来源：E2E 测试运行 `python orchestrator.py | Out-String` 与 `npx vue-tsc | Select-String` 时，PowerShell 管道导致 EPIPE broken pipe 错误（退出码 -1），进程异常终止。改为直接运行不用管道后，测试正常完成。
> 所有可变参数从 `config/coding-standards-config.md` 的 `powershell_long_process` 字段读取，禁止在规则文件中硬编码进程名或超时值。

## 触发场景

- PowerShell 中运行 vue-tsc / tsc 类型检查（耗时 1-10 分钟）
- PowerShell 中运行 Python 测试脚本（orchestrator.py 等耗时 1-5 分钟）
- PowerShell 中运行 cargo / rustc / go build（耗时 5-30 分钟）
- 任何运行时间超过 `powershell_long_process.long_process_threshold_ms`（默认 30000ms）的进程

## 规则

### PLP-1：长时进程禁止通过 PowerShell 管道运行

运行时间可能超过 `powershell_long_process.long_process_threshold_ms`（默认 30s）的进程，**禁止通过 PowerShell 管道**（`| Select-String` / `| Out-String` / `| grep` / `| Where-Object`）运行。

```powershell
# 禁止：长时进程通过管道（EPIPE 风险）
npx vue-tsc --noEmit | Select-String "Query.vue"
python orchestrator.py | Out-String
cargo build 2>&1 | Select-String "error"

# 必须：直接运行，不用管道
npx vue-tsc --noEmit
python orchestrator.py
```

### PLP-2：需过滤输出时用重定向到文件后读取

若需过滤长时进程的输出，必须用重定向到文件，然后用 Read 工具或 Grep 工具读取文件：

```powershell
# 必须：重定向到文件后读取
npx vue-tsc --noEmit > tsc-output.txt 2>&1
# 然后用 Grep 工具搜索 tsc-output.txt 中的错误
```

### PLP-3：退出码 -1 视为管道断裂而非真实失败

PowerShell 退出码 `-1`（非 0 也非 1）通常表示管道断裂（EPIPE），而非进程真实失败。必须重新直接运行（不用管道）验证真实退出码：

```powershell
# 第一次：管道运行退出码 -1
python script.py | Out-String  # exit -1

# 第二次：直接运行验证真实退出码
python script.py  # exit 0（真实成功）
```

### PLP-4：vue-tsc 耗时过长时先清理增量缓存

vue-tsc 运行时间超过 `powershell_long_process.vue_tsc_timeout_ms`（默认 120000ms，2 分钟）时，必须先清理增量缓存再重新运行：

```powershell
# 清理增量缓存
Remove-Item -Recurse -Force node_modules/.tmp, tsconfig.app.tsbuildinfo, tsconfig.tsbuildinfo -ErrorAction SilentlyContinue
# 清理 Vite 缓存
Remove-Item -Recurse -Force node_modules/.vite -ErrorAction SilentlyContinue
# 清理 src 下 .ts 对应的 .js 编译产物
Remove-Item -Force src/**/*.js -ErrorAction SilentlyContinue
# 重新运行
npx vue-tsc --noEmit
```

## 设计流程

```
需运行长时进程（vue-tsc / orchestrator / cargo）
   ↓
1. 评估预期运行时间
   ↓
   < 30s → 可通过管道运行
   ≥ 30s → 禁止管道，直接运行
   ↓
2. 需过滤输出 → 重定向到文件后用 Grep 工具读取
   ↓
3. 退出码 -1 → 管道断裂，重新直接运行验证
   ↓
4. vue-tsc > 2 分钟 → 清理增量缓存 + Vite 缓存 + .js 产物
   ↓
5. 重新运行验证真实退出码
   ↓
6. 退出码 0 → 成功 / 退出码 1 → 真实失败
```

## 适用场景

- PowerShell 运行 vue-tsc / tsc 类型检查
- PowerShell 运行 Python 测试脚本（Playwright / pytest / orchestrator）
- PowerShell 运行 cargo / rustc / go build 编译
- 任何运行时间 ≥ 30 秒的进程
- 任何需要过滤长时进程输出的场景

## 不适用场景

- 短时进程（< 30s）：`git status` / `ls` / `npm list` 等可通过管道
- Linux/macOS bash 环境（bash 管道无 EPIPE 问题）
- CMD.exe 环境（管道行为不同）
- 实时流式输出（如 `tail -f`，需用管道）

## 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `powershell_long_process.long_process_threshold_ms` | `30000` | 长时进程阈值（超过则禁管道） |
| `powershell_long_process.vue_tsc_timeout_ms` | `120000` | vue-tsc 超时阈值（超过则清缓存） |
| `powershell_long_process.forbidden_pipe_commands` | `["Select-String", "Out-String", "Where-Object"]` | 禁止对长时进程使用的管道命令 |
| `powershell_long_process.redirect_method` | `> file 2>&1` | 推荐的输出捕获方式 |
| `powershell_long_process.epipe_exit_code` | `-1` | EPIPE 管道断裂退出码 |
| `powershell_long_process.cache_cleanup_targets` | `["node_modules/.tmp", "tsconfig.tsbuildinfo", "node_modules/.vite", "src/**/*.js"]` | 增量缓存清理目标 |
