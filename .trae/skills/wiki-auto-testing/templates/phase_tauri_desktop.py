# -*- coding: utf-8 -*-
"""Phase: Tauri 桌面应用测试阶段

基于 Tauri 2.x 桌面应用集成测试过程复盘提炼，覆盖 6 个测试阶段：
  1. 测试前预检（环境验证 + SPA 产物时间戳 + 端口占用）
  2. 构建与启动（SPA 构建 + Rust 编译 + Tauri 启动 + 后端健康检查）
  3. 功能验证（窗口创建 + invoke 权限 + 交互功能）
  4. 错误诊断（Tauri stderr + DevTools Console + invoke 错误分类）
  5. 结果汇总
  6. 测试后清理

所有参数从 config.yaml 的 tauri / spa / health_check / invoke / disk_space / console_log 节读取，
不在代码中硬编码任何项目特定路径、命令名、URL 模式或阈值。
适配不同 Tauri 项目时仅需修改 config.yaml，无需改本文件。
"""
import sys
import os
import time
import json
import glob
import re
import subprocess
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _shared import (
    TestResults, load_config, find_project_root,
    stop_port_processes, verify_ports_listening,
)


# ============================================================
# 阶段 1：测试前预检
# ============================================================

def test_environment_verification(cfg, results):
    """阶段 1.1：环境验证。

    检查 Tauri 桌面应用构建所需的 cargo / LLD / windres / 磁盘空间是否就绪。
    所有阈值从 config.disk_space 读取，不在代码中硬编码。
    """
    disk_cfg = cfg.get("disk_space", {})
    debug_min_gb = disk_cfg.get("debug_min_gb", 5)
    release_min_gb = disk_cfg.get("release_min_gb", 10)
    # 优先检查 debug 模式所需空间（release 在 release 测试时另查）
    required_min_gb = debug_min_gb

    checks = []

    # cargo 可用性（Rust 工具链是否安装）
    try:
        proc = subprocess.run(
            ["cargo", "--version"],
            capture_output=True, text=True, timeout=10,
            shell=True  # Windows 下 PATH 解析需要 shell=True
        )
        cargo_ok = proc.returncode == 0 and "cargo" in (proc.stdout or "")
        checks.append(("cargo_available", cargo_ok,
                       f"rc={proc.returncode}, out={(proc.stdout or '').strip()[:50]}"))
    except Exception as e:
        checks.append(("cargo_available", False, f"err:{str(e)[:50]}"))

    # LLD 链接器可用性（Tauri 2.x 默认推荐 LLD 加速链接）
    try:
        proc = subprocess.run(
            ["where.exe", "lld-link"],
            capture_output=True, text=True, timeout=5,
            shell=True
        )
        lld_ok = proc.returncode == 0 and bool(proc.stdout.strip())
        checks.append(("lld_link_available", lld_ok,
                       f"rc={proc.returncode}, paths={len((proc.stdout or '').strip().splitlines())}"))
    except Exception as e:
        checks.append(("lld_link_available", False, f"err:{str(e)[:50]}"))

    # windres 可用性（Windows 资源编译器，Tauri 编译图标与清单需要）
    try:
        proc = subprocess.run(
            ["where.exe", "windres"],
            capture_output=True, text=True, timeout=5,
            shell=True
        )
        windres_ok = proc.returncode == 0 and bool(proc.stdout.strip())
        checks.append(("windres_available", windres_ok,
                       f"rc={proc.returncode}"))
    except Exception as e:
        checks.append(("windres_available", False, f"err:{str(e)[:50]}"))

    # 磁盘空间检查（Rust 编译产物 + node_modules 占用大，必须预检）
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-PSDrive C).Free / 1GB"],
            capture_output=True, text=True, timeout=5
        )
        free_gb_str = (proc.stdout or "").strip()
        free_gb = float(free_gb_str) if free_gb_str else 0
        disk_ok = free_gb >= required_min_gb
        checks.append(("disk_space_debug", disk_ok,
                       f"free={free_gb:.1f}GB, required={required_min_gb}GB"))
    except Exception as e:
        checks.append(("disk_space_debug", False, f"err:{str(e)[:50]}"))

    # 汇总
    all_pass = all(c[1] for c in checks)
    detail = "; ".join(f"{c[0]}:{'P' if c[1] else 'F'}" for c in checks)
    results.log("Tauri-Phase1.1-Environment", all_pass, detail)
    return all_pass


def test_spa_artifact_timestamp(cfg, results):
    """阶段 1.2：SPA 产物时间戳验证。

    防止源码已修改但产物未重建，导致 Tauri 加载旧版前端代码。
    通过比较源码 mtime 与产物 mtime 判定是否需要重建。
    所有源码目录、产物路径从 config.spa 读取，不在代码中硬编码。
    """
    spa_cfg = cfg.get("spa", {})
    source_dirs = spa_cfg.get("source_dirs", [])
    output_dir = spa_cfg.get("output_dir", "")
    artifact_marker = spa_cfg.get("artifact_marker_file", "index.html")
    source_extensions = spa_cfg.get("source_extensions", [".ts", ".tsx", ".vue", ".js", ".jsx"])
    force_rebuild = spa_cfg.get("force_rebuild", False)

    if not source_dirs or not output_dir:
        results.log("Tauri-Phase1.2-SPATimestamp", True,
                    "No source_dirs or output_dir configured, skipped")
        return True

    # 取产物标记文件的 mtime（默认 index.html）
    artifact_path = os.path.join(output_dir, artifact_marker)
    if not os.path.exists(artifact_path):
        results.log("Tauri-Phase1.2-SPATimestamp", False,
                    f"Artifact not found: {artifact_path}")
        return False

    artifact_mtime = os.path.getmtime(artifact_path)

    # 遍历源码目录，取所有源码文件的 mtime 最大值
    source_max_mtime = 0
    latest_source_file = ""
    for src_dir in source_dirs:
        if not os.path.exists(src_dir):
            continue
        for root, dirs, files in os.walk(src_dir):
            # 跳过 node_modules 防止误判（构建依赖的 mtime 通常新于业务源码）
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            for fname in files:
                ext = os.path.splitext(fname)[1]
                if ext not in source_extensions:
                    continue
                fpath = os.path.join(root, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    if mtime > source_max_mtime:
                        source_max_mtime = mtime
                        latest_source_file = fpath
                except OSError:
                    continue

    if force_rebuild:
        results.log("Tauri-Phase1.2-SPATimestamp", True,
                    "force_rebuild=true, skip timestamp check")
        return True

    # 判定：源码 mtime 不得晚于产物 mtime
    if source_max_mtime > artifact_mtime:
        latest_src_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(source_max_mtime))
        artifact_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(artifact_mtime))
        results.log("Tauri-Phase1.2-SPATimestamp", False,
                    f"Source newer: {latest_src_time} ({os.path.basename(latest_source_file)}) "
                    f"> artifact: {artifact_time}")
        return False

    results.log("Tauri-Phase1.2-SPATimestamp", True,
                f"Artifact up-to-date (source_max={time.strftime('%Y-%m-%d', time.localtime(source_max_mtime))})")
    return True


def test_spa_artifact_keys(cfg, results):
    """阶段 1.3：SPA 产物 JS chunk 特征验证（可选）。

    在 SPA 产物的 JS chunk 文件中搜索关键字符串，验证新功能已编译到产物中。
    所有关键字符串从 config.spa.key_strings 读取，不在代码中硬编码。
    """
    spa_cfg = cfg.get("spa", {})
    output_dir = spa_cfg.get("output_dir", "")
    key_strings = spa_cfg.get("key_strings", [])
    require_all = spa_cfg.get("require_all_keys", True)

    if not key_strings or not output_dir:
        results.log("Tauri-Phase1.3-SPAKeys", True,
                    "No key_strings or output_dir configured, skipped")
        return True

    # 列出产物目录下所有 JS 文件（含子目录 assets/）
    js_files = []
    for pattern in ["*.js", "**/*.js"]:
        js_files.extend(glob.glob(os.path.join(output_dir, pattern), recursive=True))

    if not js_files:
        results.log("Tauri-Phase1.3-SPAKeys", False,
                    f"No JS files found in {output_dir}")
        return False

    # 在 JS 文件中搜索关键字符串
    hit_keys = set()
    miss_keys = set()
    for key in key_strings:
        key_hit = False
        for js_file in js_files:
            try:
                with open(js_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if key in content:
                    key_hit = True
                    break
            except OSError:
                continue
        if key_hit:
            hit_keys.add(key)
        else:
            miss_keys.add(key)

    # 判定
    if require_all:
        ok = len(miss_keys) == 0
    else:
        ok = len(hit_keys) > 0

    detail = f"hit={len(hit_keys)}/{len(key_strings)}, miss={list(miss_keys)[:3]}"
    results.log("Tauri-Phase1.3-SPAKeys", ok, detail)
    return ok


def test_port_occupancy(cfg, results):
    """阶段 1.4：端口占用检查。

    防止 health_check.endpoint 配置的端口被其他进程占用。
    端口列表从 config.service.required_ports 读取，复用 precheck 协议的端口检查方法。
    """
    required_ports = cfg.get("service", {}).get("required_ports", [])
    precheck_cfg = cfg.get("precheck", {})
    stop_old = precheck_cfg.get("stop_old_process", False) and cfg.get("service_management", {}).get("stop_old_process", False)

    if not required_ports:
        results.log("Tauri-Phase1.4-PortOccupancy", True,
                    "No required_ports configured, skipped")
        return True

    # 检查端口是否被占用
    listening = verify_ports_listening(required_ports)
    occupied_ports = [p for p, ok in listening.items() if ok]

    if not occupied_ports:
        results.log("Tauri-Phase1.4-PortOccupancy", True,
                    f"All ports free: {required_ports}")
        return True

    # 若启用 stop_old_process，尝试停止占用进程
    if stop_old:
        stop_result = stop_port_processes(occupied_ports)
        stopped_count = sum(1 for r in stop_result.values() if r["stopped"])
        # 等待端口释放
        time.sleep(2)
        # 重新检查
        listening_after = verify_ports_listening(required_ports)
        still_occupied = [p for p, ok in listening_after.items() if ok]
        if not still_occupied:
            results.log("Tauri-Phase1.4-PortOccupancy", True,
                        f"Stopped {stopped_count} processes, all ports free")
            return True
        else:
            results.log("Tauri-Phase1.4-PortOccupancy", False,
                        f"Still occupied after stop: {still_occupied}")
            return False
    else:
        results.log("Tauri-Phase1.4-PortOccupancy", False,
                    f"Ports occupied (stop_old_process=false): {occupied_ports}")
        return False


# ============================================================
# 阶段 2：构建与启动
# ============================================================

def test_spa_build(cfg, results):
    """阶段 2.1：SPA 构建。

    执行构建脚本并验证产物 index.html 存在且非空。
    构建脚本路径从 config.tauri.build_script_path 读取，不在代码中硬编码。
    """
    tauri_cfg = cfg.get("tauri", {})
    spa_cfg = cfg.get("spa", {})
    build_script = tauri_cfg.get("build_script_path", "")
    output_dir = spa_cfg.get("output_dir", "")
    build_timeout = cfg.get("build", {}).get("timeout_sec", 120)

    if not build_script:
        results.log("Tauri-Phase2.1-SPABuild", True,
                    "No build_script_path configured, skipped")
        return True

    if not os.path.exists(build_script):
        results.log("Tauri-Phase2.1-SPABuild", False,
                    f"Build script not found: {build_script}")
        return False

    # 执行构建脚本（PowerShell 兼容性：bat 脚本需用 cmd /c 或直接执行）
    try:
        proc = subprocess.run(
            build_script,
            capture_output=True, text=True, timeout=build_timeout,
            shell=True,  # shell=True 让 Windows 解析 bat 脚本路径
            cwd=os.getcwd()
        )
        build_ok = proc.returncode == 0
    except subprocess.TimeoutExpired:
        results.log("Tauri-Phase2.1-SPABuild", False,
                    f"Build timeout after {build_timeout}s")
        return False
    except Exception as e:
        results.log("Tauri-Phase2.1-SPABuild", False,
                    f"Build error: {str(e)[:80]}")
        return False

    if not build_ok:
        # 输出 stderr 前 200 字符便于诊断
        stderr_snippet = (proc.stderr or "")[:200].replace("\n", " ")
        results.log("Tauri-Phase2.1-SPABuild", False,
                    f"Build failed (rc={proc.returncode}): {stderr_snippet}")
        return False

    # 验证产物 index.html 存在且非空
    artifact_path = os.path.join(output_dir, spa_cfg.get("artifact_marker_file", "index.html"))
    if not os.path.exists(artifact_path):
        results.log("Tauri-Phase2.1-SPABuild", False,
                    f"Artifact not found after build: {artifact_path}")
        return False

    artifact_size = os.path.getsize(artifact_path)
    if artifact_size == 0:
        results.log("Tauri-Phase2.1-SPABuild", False,
                    f"Artifact empty: {artifact_path}")
        return False

    results.log("Tauri-Phase2.1-SPABuild", True,
                f"Build OK, artifact={artifact_size}B")
    return True


def test_rust_compile(cfg, results):
    """阶段 2.2：Rust 编译。

    进入 src-tauri 目录执行 cargo build，监控编译错误。
    编译超时从 config.tauri.compile_timeout_sec 读取。
    """
    tauri_cfg = cfg.get("tauri", {})
    src_tauri_dir = tauri_cfg.get("src_tauri_dir", "src-tauri")
    compile_timeout = tauri_cfg.get("compile_timeout_sec", 600)
    release_mode = tauri_cfg.get("release_mode", False)

    if not os.path.exists(src_tauri_dir):
        results.log("Tauri-Phase2.2-RustCompile", False,
                    f"src_tauri_dir not found: {src_tauri_dir}")
        return False

    # 构造编译命令
    cmd = ["cargo", "build"]
    if release_mode:
        cmd.append("--release")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=compile_timeout,
            cwd=src_tauri_dir,
            shell=True  # Windows 下 cargo 需通过 shell 解析 PATH
        )
        compile_ok = proc.returncode == 0
    except subprocess.TimeoutExpired:
        results.log("Tauri-Phase2.2-RustCompile", False,
                    f"Compile timeout after {compile_timeout}s")
        return False
    except Exception as e:
        results.log("Tauri-Phase2.2-RustCompile", False,
                    f"Compile error: {str(e)[:80]}")
        return False

    if not compile_ok:
        # 提取首个 error[E 开头的编译错误行
        stderr_lines = (proc.stderr or "").splitlines()
        error_lines = [l for l in stderr_lines if l.startswith("error[") or l.startswith("error:")][:3]
        error_summary = "; ".join(error_lines)[:200]
        results.log("Tauri-Phase2.2-RustCompile", False,
                    f"Compile failed (rc={proc.returncode}): {error_summary}")
        return False

    # 验证 exe 文件存在
    exe_name = tauri_cfg.get("exe_name", "tauri-app")
    target_subdir = "release" if release_mode else "debug"
    exe_path = os.path.join(src_tauri_dir, "target", target_subdir, f"{exe_name}.exe")
    if not os.path.exists(exe_path):
        # 某些项目 exe 名与 Cargo.toml 的 [[bin]] name 不同，尝试用 src_tauri_dir 名字兜底
        alt_exe_name = os.path.basename(os.path.normpath(src_tauri_dir)).replace("-", "_")
        alt_exe_path = os.path.join(src_tauri_dir, "target", target_subdir, f"{alt_exe_name}.exe")
        if os.path.exists(alt_exe_path):
            exe_path = alt_exe_path
        else:
            results.log("Tauri-Phase2.2-RustCompile", False,
                        f"Compile OK but exe not found: {exe_path}")
            return False

    exe_size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    results.log("Tauri-Phase2.2-RustCompile", True,
                f"Compile OK, exe={exe_size_mb:.1f}MB")
    return True


def test_tauri_startup(cfg, results, log_files):
    """阶段 2.3：Tauri 应用启动。

    非阻塞启动 Tauri exe，将 stdout/stderr 重定向到临时日志文件。
    启动超时从 config.tauri.startup_timeout_ms 读取。
    返回 (success, process) 供阶段 3 使用。
    """
    tauri_cfg = cfg.get("tauri", {})
    exe_name = tauri_cfg.get("exe_name", "tauri-app")
    src_tauri_dir = tauri_cfg.get("src_tauri_dir", "src-tauri")
    startup_timeout_ms = tauri_cfg.get("startup_timeout_ms", 15000)
    release_mode = tauri_cfg.get("release_mode", False)

    target_subdir = "release" if release_mode else "debug"
    exe_path = os.path.join(src_tauri_dir, "target", target_subdir, f"{exe_name}.exe")

    if not os.path.exists(exe_path):
        alt_exe_name = os.path.basename(os.path.normpath(src_tauri_dir)).replace("-", "_")
        alt_exe_path = os.path.join(src_tauri_dir, "target", target_subdir, f"{alt_exe_name}.exe")
        if os.path.exists(alt_exe_path):
            exe_path = alt_exe_path
        else:
            results.log("Tauri-Phase2.3-TauriStartup", False,
                        f"Exe not found: {exe_path}")
            return False, None

    # 重定向 stdout/stderr 到临时日志文件（供阶段 4 诊断使用）
    stdout_log = os.path.join(os.getcwd(), "_tauri_stdout.log")
    stderr_log = os.path.join(os.getcwd(), "_tauri_stderr.log")
    log_files["stdout"] = stdout_log
    log_files["stderr"] = stderr_log

    try:
        stdout_fd = open(stdout_log, "w", encoding="utf-8")
        stderr_fd = open(stderr_log, "w", encoding="utf-8")
        log_files["_stdout_fd"] = stdout_fd
        log_files["_stderr_fd"] = stderr_fd
    except Exception as e:
        results.log("Tauri-Phase2.3-TauriStartup", False,
                    f"Cannot open log files: {str(e)[:80]}")
        return False, None

    # 非阻塞启动
    try:
        proc = subprocess.Popen(
            [exe_path],
            stdout=stdout_fd, stderr=stderr_fd,
            cwd=os.getcwd()
        )
    except Exception as e:
        results.log("Tauri-Phase2.3-TauriStartup", False,
                    f"Failed to start: {str(e)[:80]}")
        stdout_fd.close()
        stderr_fd.close()
        return False, None

    # 等待 startup_timeout_ms，轮询进程是否存活
    deadline = time.time() + (startup_timeout_ms / 1000.0)
    while time.time() < deadline:
        retcode = proc.poll()
        if retcode is not None:
            # 进程已退出，判定启动失败
            # 刷新 stderr 日志并读取，用于诊断
            stderr_fd.flush()
            try:
                with open(stderr_log, "r", encoding="utf-8", errors="ignore") as f:
                    stderr_content = f.read()
            except OSError:
                stderr_content = ""
            # 提取 panicked at 行
            panic_lines = [l for l in stderr_content.splitlines() if "panicked at" in l][:2]
            panic_summary = "; ".join(panic_lines)[:200]
            results.log("Tauri-Phase2.3-TauriStartup", False,
                        f"Process exited (rc={retcode}): {panic_summary or stderr_content[:100]}")
            return False, None
        time.sleep(0.5)

    # 进程在超时内未退出，判定启动成功
    results.log("Tauri-Phase2.3-TauriStartup", True,
                f"Process alive (pid={proc.pid})")
    return True, proc


def test_backend_health_check(cfg, results):
    """阶段 2.4：后端健康检查。

    轮询 health_check.endpoint，重试 retry_count 次。
    所有端点、重试次数、超时从 config.health_check 读取。
    """
    hc_cfg = cfg.get("health_check", {})
    endpoint = hc_cfg.get("endpoint", "http://localhost:3000/health")
    retry_count = hc_cfg.get("retry_count", 30)
    timeout_ms = hc_cfg.get("timeout", 1000)
    expected_status = hc_cfg.get("expected_status", 200)

    for attempt in range(retry_count):
        try:
            req = urllib.request.Request(endpoint, method="GET")
            with urllib.request.urlopen(req, timeout=timeout_ms / 1000.0) as resp:
                status = resp.status
                if status == expected_status:
                    results.log("Tauri-Phase2.4-HealthCheck", True,
                                f"OK (attempt={attempt + 1}, status={status})")
                    return True
        except urllib.error.HTTPError as e:
            status = e.code
            if status == expected_status:
                results.log("Tauri-Phase2.4-HealthCheck", True,
                            f"OK (attempt={attempt + 1}, status={status})")
                return True
        except (urllib.error.URLError, ConnectionError, OSError):
            # 连接被拒绝，继续重试
            pass
        except Exception:
            pass

        time.sleep(timeout_ms / 1000.0)

    results.log("Tauri-Phase2.4-HealthCheck", False,
                f"Failed after {retry_count} retries")
    return False


# ============================================================
# 阶段 3：功能验证
# ============================================================

def test_window_creation(cfg, results, tauri_process):
    """阶段 3.1：窗口创建验证。

    通过进程名查找 Tauri 进程，验证主窗口已创建且标题匹配。
    窗口标题期望值从 config.tauri.expected_window_title 读取。
    """
    tauri_cfg = cfg.get("tauri", {})
    exe_name = tauri_cfg.get("exe_name", "tauri-app")
    expected_title = tauri_cfg.get("expected_window_title", "")

    # 验证 Tauri 进程存活
    if tauri_process is None or tauri_process.poll() is not None:
        results.log("Tauri-Phase3.1-WindowCreation", False,
                    "Tauri process not alive")
        return False

    # 用 PowerShell Get-Process 验证主窗口标题
    # MainWindowTitle 能反映窗口是否已创建并显示
    try:
        ps_script = (
            f"$proc = Get-Process -Name '{exe_name}' -ErrorAction SilentlyContinue; "
            f"if ($proc) {{ Write-Output $proc.MainWindowTitle }} else {{ Write-Output '' }}"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=5
        )
        window_title = (proc.stdout or "").strip()
    except Exception as e:
        results.log("Tauri-Phase3.1-WindowCreation", False,
                    f"Get-Process error: {str(e)[:80]}")
        return False

    if not window_title:
        results.log("Tauri-Phase3.1-WindowCreation", False,
                    "Process alive but no main window")
        return False

    # 验证窗口标题匹配（若配置了期望值）
    if expected_title and expected_title not in window_title:
        results.log("Tauri-Phase3.1-WindowCreation", False,
                    f"Title mismatch: got='{window_title}', expected contains='{expected_title}'")
        return False

    results.log("Tauri-Phase3.1-WindowCreation", True,
                f"Window created (title='{window_title[:40]}')")
    return True


def test_invoke_permissions(cfg, results):
    """阶段 3.2：invoke 权限三层验证。

    静态预检 invoke 调用所需的插件依赖、权限声明、URL 白名单。
    所有命令名、权限名、URL 模式从 config.invoke 读取，不在代码中硬编码。

    详见 references/invoke-permission-verification.md。
    """
    invoke_cfg = cfg.get("invoke", {})
    tauri_cfg = cfg.get("tauri", {})
    src_tauri_dir = tauri_cfg.get("src_tauri_dir", "src-tauri")
    commands = invoke_cfg.get("commands", [])
    permissions = invoke_cfg.get("permissions", [])
    url_patterns = invoke_cfg.get("url_patterns", [])
    capabilities_glob = invoke_cfg.get("capabilities_glob", "capabilities/*.json")
    cargo_toml_path = invoke_cfg.get("cargo_toml_path", "Cargo.toml")

    if not commands and not permissions:
        results.log("Tauri-Phase3.2-InvokePermissions", True,
                    "No commands or permissions configured, skipped")
        return True

    # 第 1 层：插件依赖检查
    layer1_pass = True
    layer1_details = []
    cargo_full_path = os.path.join(src_tauri_dir, cargo_toml_path)
    if os.path.exists(cargo_full_path):
        try:
            with open(cargo_full_path, "r", encoding="utf-8") as f:
                cargo_content = f.read()
            # 跳过注释行（# 开头），只检查 [dependencies] 节内的实际依赖
            cargo_lines = [l for l in cargo_content.splitlines()
                           if not l.strip().startswith("#")]
            cargo_text = "\n".join(cargo_lines)
            for cmd in commands:
                # 提取插件名：plugin:log|info → log
                match = re.match(r"plugin:([^|]+)\|", cmd)
                if not match:
                    continue
                plugin_name = match.group(1)
                dep_name = f"tauri-plugin-{plugin_name}"
                if dep_name in cargo_text:
                    layer1_details.append(f"{plugin_name}:FOUND")
                else:
                    layer1_pass = False
                    layer1_details.append(f"{plugin_name}:MISSING")
        except OSError:
            layer1_pass = False
            layer1_details.append("Cargo.toml:READ_ERR")
    else:
        layer1_pass = False
        layer1_details.append(f"Cargo.toml:NOT_FOUND@{cargo_full_path}")

    # 第 2 层：命令权限声明检查
    layer2_pass = True
    layer2_details = []
    cap_files = glob.glob(os.path.join(src_tauri_dir, capabilities_glob))
    all_declared_perms = set()
    for cap_file in cap_files:
        try:
            with open(cap_file, "r", encoding="utf-8") as f:
                cap_data = json.load(f)
            all_declared_perms.update(cap_data.get("permissions", []))
        except (OSError, json.JSONDecodeError):
            continue

    for perm in permissions:
        if perm in all_declared_perms:
            layer2_details.append(f"{perm}:FOUND")
        else:
            layer2_pass = False
            layer2_details.append(f"{perm}:MISSING")

    # 第 3 层：远程 URL 白名单检查（仅在 url_patterns 非空时执行）
    layer3_pass = True
    layer3_details = []
    if url_patterns:
        all_remote_urls = set()
        for cap_file in cap_files:
            try:
                with open(cap_file, "r", encoding="utf-8") as f:
                    cap_data = json.load(f)
                remote = cap_data.get("remote", {})
                all_remote_urls.update(remote.get("urls", []))
            except (OSError, json.JSONDecodeError):
                continue

        for pattern in url_patterns:
            if pattern in all_remote_urls:
                layer3_details.append(f"{pattern}:EXACT_MATCH")
            else:
                # 检查是否有更宽松的模式覆盖
                covered = _pattern_covers_any(all_remote_urls, pattern)
                if covered:
                    layer3_details.append(f"{pattern}:COVERED")
                else:
                    layer3_pass = False
                    layer3_details.append(f"{pattern}:NOT_MATCHED")

    all_pass = layer1_pass and layer2_pass and layer3_pass
    detail = f"L1:{'P' if layer1_pass else 'F'}[{','.join(layer1_details[:3])}]; "
    detail += f"L2:{'P' if layer2_pass else 'F'}[{','.join(layer2_details[:3])}]; "
    detail += f"L3:{'P' if layer3_pass else 'F'}[{','.join(layer3_details[:3])}]"
    results.log("Tauri-Phase3.2-InvokePermissions", all_pass, detail)
    return all_pass


def _pattern_covers_any(wider_patterns, narrower_pattern):
    """检查 wider_patterns 中是否有任一模式覆盖 narrower_pattern。

    例如 "http://localhost:*" 覆盖 "http://localhost:3000"。
    用正则实现通配符匹配，* 转为 .* 实现任意长度匹配。
    """
    for wider in wider_patterns:
        # 将通配符 * 转为正则 .*，转义 . 防止任意字符匹配
        regex = wider.replace(".", r"\.").replace("*", ".*")
        if re.fullmatch(regex, narrower_pattern):
            return True
    return False


# ============================================================
# 阶段 4：错误诊断
# ============================================================

def test_stderr_log_analysis(cfg, results, log_files):
    """阶段 4.1：Tauri stderr 日志分析。

    读取阶段 2 启动时重定向的 stderr 日志，按错误关键词分类。
    所有关键词从 config.console_log.error_keywords 读取，不在代码中硬编码。
    """
    console_cfg = cfg.get("console_log", {})
    error_keywords = console_cfg.get("error_keywords", [])
    stderr_log = log_files.get("stderr")

    if not stderr_log or not os.path.exists(stderr_log):
        results.log("Tauri-Phase4.1-StderrAnalysis", True,
                    "No stderr log file, skipped")
        return True

    try:
        # flush 确保缓冲区内容已写入文件
        stderr_fd = log_files.get("_stderr_fd")
        if stderr_fd:
            stderr_fd.flush()
        with open(stderr_log, "r", encoding="utf-8", errors="ignore") as f:
            stderr_content = f.read()
    except OSError as e:
        results.log("Tauri-Phase4.1-StderrAnalysis", False,
                    f"Cannot read stderr log: {str(e)[:80]}")
        return False

    if not stderr_content.strip():
        results.log("Tauri-Phase4.1-StderrAnalysis", True,
                    "stderr log empty")
        return True

    # 按关键词扫描
    matched_errors = []
    for keyword in error_keywords:
        if keyword in stderr_content:
            # 提取匹配行（按行扫描，提取含关键词的行）
            for line in stderr_content.splitlines():
                if keyword in line:
                    matched_errors.append(f"{keyword}:{line.strip()[:60]}")
                    break  # 每个关键词只取首条匹配

    if matched_errors:
        results.log("Tauri-Phase4.1-StderrAnalysis", False,
                    f"{len(matched_errors)} errors: " + "; ".join(matched_errors[:3]))
        return False

    results.log("Tauri-Phase4.1-StderrAnalysis", True,
                "No error keywords matched in stderr")
    return True


def test_console_log_analysis(cfg, results):
    """阶段 4.2：DevTools Console 日志分析（辅助诊断）。

    通过 CDP（Chrome DevTools Protocol）连接 Tauri WebView 采集 Console 日志。
    若 CDP 不可用，降级为静态分析前端代码中的 console.error 调用。

    所有日志前缀、关键词从 config.console_log 读取，不在代码中硬编码。
    """
    console_cfg = cfg.get("console_log", {})
    error_keywords = console_cfg.get("error_keywords", [])
    prefixes = console_cfg.get("prefixes", [])

    # CDP 连接尝试（Tauri 2.x 默认 DevTools 端口为 9222，但仅在 dev 模式或显式开启时可用）
    # 这里只做静态预检：检查前端源码中是否有 invoke 调用而 Rust 端无对应命令
    # 实际 CDP 日志采集需要在 Tauri 启动时配置 --remote-debugging-port
    spa_cfg = cfg.get("spa", {})
    source_dirs = spa_cfg.get("source_dirs", [])

    # 静态扫描：在前端源码中查找 invoke 调用，提取命令名
    invoke_commands_in_frontend = set()
    invoke_pattern = re.compile(r'invoke\s*\(\s*["\']([^"\']+)["\']')
    for src_dir in source_dirs:
        if not os.path.exists(src_dir):
            continue
        for root, dirs, files in os.walk(src_dir):
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            for fname in files:
                ext = os.path.splitext(fname)[1]
                if ext not in (".ts", ".tsx", ".vue", ".js", ".jsx"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    # 提取 invoke 调用的命令名
                    for match in invoke_pattern.finditer(content):
                        invoke_commands_in_frontend.add(match.group(1))
                except OSError:
                    continue

    # 静态扫描：在 Rust 源码中查找 invoke_handler 注册的命令
    tauri_cfg = cfg.get("tauri", {})
    src_tauri_dir = tauri_cfg.get("src_tauri_dir", "src-tauri")
    registered_commands_in_rust = set()
    # generate_handler![cmd1, cmd2, ...] 或 .invoke_handler(tauri::generate_handler![...])
    handler_pattern = re.compile(r'generate_handler!\s*\[([^\]]+)\]')
    for root, dirs, files in os.walk(src_tauri_dir):
        if "target" in dirs:
            dirs.remove("target")  # 跳过编译产物
        for fname in files:
            if not fname.endswith(".rs"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for match in handler_pattern.finditer(content):
                    # 提取命令名列表
                    cmd_text = match.group(1)
                    for cmd in re.findall(r'\b([a-z_][a-z0-9_]*)\b', cmd_text):
                        registered_commands_in_rust.add(cmd)
            except OSError:
                continue

    # 静态诊断：前端调用的 invoke 命令是否在 Rust 端注册
    # 注意：plugin:xxx|yyy 形式的命令由插件自动注册，不在此检查范围
    frontend_custom_commands = {c for c in invoke_commands_in_frontend
                                if not c.startswith("plugin:")}
    unregistered = frontend_custom_commands - registered_commands_in_rust

    if unregistered:
        results.log("Tauri-Phase4.2-ConsoleAnalysis", False,
                    f"Unregistered commands: {list(unregistered)[:3]}")
        return False

    results.log("Tauri-Phase4.2-ConsoleAnalysis", True,
                f"All {len(frontend_custom_commands)} custom commands registered")
    return True


def test_invoke_error_classify(cfg, results, log_files):
    """阶段 4.3：invoke 错误分类。

    读取 stderr 日志，按错误关键词映射到失败层级。
    关键词与失败类型映射从 config.failure_classification.rules 读取。
    """
    fc_cfg = cfg.get("failure_classification", {})
    rules = fc_cfg.get("rules", [])
    stderr_log = log_files.get("stderr")

    if not stderr_log or not os.path.exists(stderr_log):
        results.log("Tauri-Phase4.3-InvokeClassify", True,
                    "No stderr log, nothing to classify")
        return True

    try:
        stderr_fd = log_files.get("_stderr_fd")
        if stderr_fd:
            stderr_fd.flush()
        with open(stderr_log, "r", encoding="utf-8", errors="ignore") as f:
            stderr_content = f.read()
    except OSError:
        results.log("Tauri-Phase4.3-InvokeClassify", True,
                    "Cannot read stderr log, skipped")
        return True

    # 按规则匹配（rules 已按优先级排序，首个命中即停止）
    matched_rules = []
    for rule in rules:
        pattern = rule.get("pattern", "")
        rtype = rule.get("type", "unknown")
        suggestion = rule.get("suggestion", "")
        try:
            if re.search(pattern, stderr_content):
                matched_rules.append((rtype, suggestion))
        except re.error:
            continue

    if matched_rules:
        # 取首个命中的规则作为主要失败类型
        primary_type, primary_suggestion = matched_rules[0]
        results.log("Tauri-Phase4.3-InvokeClassify", False,
                    f"type={primary_type}, suggestion={primary_suggestion[:60]}")
        return False

    results.log("Tauri-Phase4.3-InvokeClassify", True,
                "No failure rules matched")
    return True


# ============================================================
# 阶段 5：结果汇总
# ============================================================

def summarize_results(results):
    """阶段 5：结果汇总。

    输出 PASS/FAIL/SKIP 报告。
    """
    print("\n=== Tauri Desktop Test Report ===")
    print(results.summary())
    print("=" * 50)


# ============================================================
# 阶段 6：测试后清理
# ============================================================

def cleanup_tauri_process(cfg, results, tauri_process):
    """阶段 6.1：停止 Tauri 进程。

    优雅停止 Tauri 进程，必要时强制终止。
    """
    tauri_cfg = cfg.get("tauri", {})
    exe_name = tauri_cfg.get("exe_name", "tauri-app")

    if tauri_process is not None and tauri_process.poll() is None:
        try:
            tauri_process.terminate()
            tauri_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # 优雅终止失败，强制 kill
            tauri_process.kill()
            tauri_process.wait(timeout=2)
        except Exception:
            pass

    # 兜底：用 PowerShell Stop-Process 清理同名进程
    try:
        ps_script = (
            f"Get-Process -Name '{exe_name}' -ErrorAction SilentlyContinue | "
            f"Stop-Process -Force -ErrorAction SilentlyContinue"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, timeout=5
        )
    except Exception:
        pass

    # 等待 2 秒后验证进程已退出
    time.sleep(2)
    try:
        ps_check = (
            f"$p = Get-Process -Name '{exe_name}' -ErrorAction SilentlyContinue; "
            f"if ($p) {{ Write-Output '1' }} else {{ Write-Output '0' }}"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_check],
            capture_output=True, text=True, timeout=5
        )
        still_alive = (proc.stdout or "").strip() == "1"
    except Exception:
        still_alive = False

    results.log("Tauri-Phase6.1-ProcessCleanup", not still_alive,
                f"still_alive={still_alive}")


def cleanup_temp_logs(cfg, results, log_files):
    """阶段 6.2：临时日志清理。

    关闭日志文件句柄并删除临时日志文件。
    """
    # 关闭文件句柄
    for fd_key in ("_stdout_fd", "_stderr_fd"):
        fd = log_files.get(fd_key)
        if fd and not fd.closed:
            try:
                fd.close()
            except Exception:
                pass

    deleted = 0
    failed = 0
    for key in ("stdout", "stderr"):
        log_path = log_files.get(key)
        if log_path and os.path.exists(log_path):
            try:
                os.remove(log_path)
                deleted += 1
            except OSError:
                failed += 1

    results.log("Tauri-Phase6.2-LogCleanup", failed == 0,
                f"deleted={deleted}, failed={failed}")


# ============================================================
# 主流程编排
# ============================================================

def run_phase(cfg, results, quiet=False):
    """执行 Tauri 桌面应用测试的 6 个阶段。

    阶段间为 DAG 依赖关系：阶段 1 的 critical 故障中断后续所有阶段；
    阶段 4 在阶段 3 失败时仍需执行（用于诊断根因）。
    """
    tauri_cfg = cfg.get("tauri", {})
    if not tauri_cfg.get("enabled", False):
        if not quiet:
            print("\n=== Tauri Desktop Tests: Disabled, skipped ===")
        return

    if not quiet:
        print("\n=== Tauri Desktop Tests ===")

    log_files = {}
    tauri_process = None

    try:
        # === 阶段 1：测试前预检 ===
        if not quiet:
            print("--- Phase 1: Pre-check ---")
        phase1_pass = test_environment_verification(cfg, results)
        phase1_pass = test_spa_artifact_timestamp(cfg, results) and phase1_pass
        test_spa_artifact_keys(cfg, results)  # 可选验证，不影响 phase1_pass
        phase1_pass = test_port_occupancy(cfg, results) and phase1_pass

        if not phase1_pass:
            # 阶段 1 失败，中断后续阶段
            if not quiet:
                print("Phase 1 failed, aborting subsequent phases")
            return

        # === 阶段 2：构建与启动 ===
        if not quiet:
            print("--- Phase 2: Build & Start ---")
        phase2_pass = test_spa_build(cfg, results)
        phase2_pass = test_rust_compile(cfg, results) and phase2_pass
        if phase2_pass:
            startup_ok, tauri_process = test_tauri_startup(cfg, results, log_files)
            phase2_pass = startup_ok and phase2_pass
        if phase2_pass:
            test_backend_health_check(cfg, results)

        if not phase2_pass:
            # 阶段 2 失败，仍执行阶段 4 错误诊断（读取 stderr 日志）
            if not quiet:
                print("Phase 2 failed, running diagnostics before abort")
            test_stderr_log_analysis(cfg, results, log_files)
            test_invoke_error_classify(cfg, results, log_files)
            return

        # === 阶段 3：功能验证 ===
        if not quiet:
            print("--- Phase 3: Functional Verification ---")
        phase3_pass = test_window_creation(cfg, results, tauri_process)
        phase3_pass = test_invoke_permissions(cfg, results) and phase3_pass

        # === 阶段 4：错误诊断（无论阶段 3 成败都执行）===
        if not quiet:
            print("--- Phase 4: Diagnostics ---")
        test_stderr_log_analysis(cfg, results, log_files)
        test_console_log_analysis(cfg, results)
        # 仅在阶段 3 失败时执行 invoke 错误分类
        if not phase3_pass:
            test_invoke_error_classify(cfg, results, log_files)

        # === 阶段 5：结果汇总 ===
        if not quiet:
            print("--- Phase 5: Summary ---")
        summarize_results(results)

    finally:
        # === 阶段 6：测试后清理（无论前序阶段成败都必须执行）===
        if not quiet:
            print("--- Phase 6: Cleanup ---")
        cleanup_tauri_process(cfg, results, tauri_process)
        cleanup_temp_logs(cfg, results, log_files)


# ============================================================
# 独立运行入口
# ============================================================

if __name__ == "__main__":
    cfg = load_config()
    results = TestResults(quiet="--quiet" in sys.argv)
    run_phase(cfg, results, quiet="--quiet" in sys.argv)
    # 保存结果到统一的结果文件
    output_cfg = cfg.get("output", {})
    result_file = output_cfg.get("result_file", "test_result.json")
    results.save(result_file, encoding=output_cfg.get("encoding", "utf-8"))
    print(f"\nResults saved to {result_file}")
    sys.exit(1 if results.failed > 0 else 0)
