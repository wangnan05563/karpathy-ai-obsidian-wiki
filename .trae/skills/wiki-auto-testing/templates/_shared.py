# -*- coding: utf-8 -*-
"""
Shared utilities for wiki-auto-testing.
Contains config loading, result tracking, and helper functions.
All parameters from config.yaml - no hardcoded values.
"""
import json
import os
import sys
import glob
import subprocess
import yaml
from playwright.sync_api import sync_playwright


# ============================================================
# Config Loading with Two-Layer Merging
# ============================================================

def find_project_root(script_path, marker=".git"):
    """Walk up from script location to find project root."""
    current = os.path.dirname(os.path.abspath(script_path))
    for _ in range(10):
        if os.path.exists(os.path.join(current, marker)):
            return current
        if os.path.exists(os.path.join(current, "package.json")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.dirname(os.path.dirname(os.path.dirname(script_path)))


def deep_merge(base, override):
    """Recursively merge override dict into base dict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path=None):
    """
    Load config with two-layer merging:
    defaults.yaml (skill-wide) + config.yaml (project-specific).
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)
    skill_root = os.path.dirname(skill_dir)

    # Load defaults
    defaults_cfg = {}
    defaults_candidates = [
        os.path.join(skill_root, "defaults.yaml"),
        os.path.join(os.getcwd(), ".trae", "skills", "wiki-auto-testing", "defaults.yaml"),
    ]
    for dc in defaults_candidates:
        if os.path.exists(dc):
            with open(dc, "r", encoding="utf-8") as f:
                defaults_cfg = yaml.safe_load(f) or {}
            break

    # Load project config
    if config_path is None:
        candidates = [
            os.environ.get("WIKI_TEST_CONFIG"),
            os.path.join(skill_root, "config.yaml"),
            os.path.join(os.getcwd(), ".trae", "skills", "wiki-auto-testing", "config.yaml"),
            os.path.join(os.getcwd(), "config.yaml"),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                config_path = c
                break

    if config_path is None or not os.path.exists(config_path):
        print("ERROR: config.yaml not found")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        project_cfg = yaml.safe_load(f) or {}

    cfg = deep_merge(defaults_cfg, project_cfg)

    # Auto chdir to project root
    wd_cfg = cfg.get("working_directory", {})
    if wd_cfg.get("auto_chdir", True):
        marker = wd_cfg.get("project_root_marker", ".git") or ".git"
        project_root = find_project_root(config_path, marker)
        os.chdir(project_root)

    return cfg


# ============================================================
# Encoding Safety
# ============================================================

def ensure_utf8(file_path, fallback_encoding="gbk"):
    """Check and fix file encoding (GBK -> UTF-8)."""
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
            with open(file_path, "wb") as f:
                f.write(raw)
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        try:
            content = raw.decode(fallback_encoding)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False


# ============================================================
# Test Result Tracking
# ============================================================

class TestResults:
    """Thread-safe test result tracker with quiet mode."""
    def __init__(self, quiet=False):
        self.items = []
        self.quiet = quiet

    def log(self, name, passed, details=""):
        status = "PASS" if passed else "FAIL"
        self.items.append({"test": name, "status": status, "details": details})
        if not self.quiet:
            print(f"[{status}] {name}: {details}")

    def skip(self, name, reason=""):
        """记录 SKIP 状态：不计入 failed，用于设计上禁用或良性限流的测试项"""
        status = "SKIP"
        self.items.append({"test": name, "status": status, "details": reason})
        if not self.quiet:
            print(f"[{status}] {name}: {reason}")

    @property
    def passed(self):
        return sum(1 for r in self.items if r["status"] == "PASS")

    @property
    def failed(self):
        return sum(1 for r in self.items if r["status"] == "FAIL")

    @property
    def skipped(self):
        return sum(1 for r in self.items if r["status"] == "SKIP")

    @property
    def total(self):
        return len(self.items)

    def summary(self):
        return f"Total: {self.total} | Passed: {self.passed} | Failed: {self.failed} | Skipped: {self.skipped}"

    def save(self, path, encoding="utf-8"):
        with open(path, "w", encoding=encoding) as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)


# ============================================================
# Playwright Helpers
# ============================================================

def click_nav_tab(page, tab_selector, label, wait_ms=1500):
    """Click a navigation tab by label text. Skips disabled tabs. Never raises."""
    try:
        tab = page.locator(f'{tab_selector}:has-text("{label}")')
        if tab.count() > 0:
            # 跳过 disabled 按钮，避免 Playwright 默认 30s 超时
            if tab.first.get_attribute('disabled') is not None:
                return False
            tab.first.click(timeout=5000)
            page.wait_for_timeout(wait_ms)
            return True
        return False
    except Exception:
        return False


def safe_click(page, selector, wait_ms=500, force=False, timeout=None):
    """Safely click an element.

    timeout: 超时毫秒数。None 时使用 Playwright 默认超时。
             调用方应从 cfg.timeout.click_timeout_ms 读取并传入，避免硬编码。
    """
    elem = page.locator(selector)
    if elem.count() > 0:
        click_kwargs = {"force": force}
        if timeout is not None:
            click_kwargs["timeout"] = timeout
        elem.first.click(**click_kwargs)
        page.wait_for_timeout(wait_ms)
        return True
    return False


def js_click(page, selector):
    """Click via JS dispatch (bypasses transition issues)."""
    page.evaluate(f'document.querySelector("{selector}").click()')


def is_destructive(text, destructive_texts):
    """Check if button text matches destructive action list."""
    if not text or not destructive_texts:
        return False
    text_lower = text.lower()
    return any(dt.lower() in text_lower for dt in destructive_texts)


# ============================================================
# Phase Selection
# ============================================================

def get_enabled_phases(cfg):
    """Determine which phases to run from test_plan config."""
    test_plan = cfg.get("test_plan", {})
    enabled = test_plan.get("enabled_phases", ["basic", "interactions", "supplementary"])
    return set(enabled)


def setup_browser(cfg, quiet=False):
    """Create browser, context, and page. Returns (browser, ctx, page, console_errors)."""
    launch_args = cfg["browser"].get("launch_args", [])
    headless = cfg["browser"].get("headless", True)
    desktop = cfg["browser"]["viewports"]["desktop"]
    shot_dir = os.path.join(os.getcwd(), cfg["output"]["screenshot_dir"])
    os.makedirs(shot_dir, exist_ok=True)

    console_errors = []

    if not quiet:
        print(f"Launching browser (headless={headless})...")

    browser = sync_playwright().start().chromium.launch(
        headless=headless, args=launch_args
    )
    ctx = browser.new_context(
        viewport={"width": desktop["width"], "height": desktop["height"]}
    )
    page = ctx.new_page()

    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: console_errors.append(f"PAGE ERROR: {e}"))

    return browser, ctx, page, console_errors, shot_dir


def teardown_browser(browser, ctx):
    """Clean up browser resources."""
    ctx.close()
    browser.close()


def authenticate(page, ctx, cfg, quiet=False):
    """通过 API 登录获取 token，注入浏览器 localStorage。

    为什么需要：项目启用了认证（config.json auth.enabled=true），
    若不登录直接访问 /，会被路由守卫重定向到登录页，后续所有导航测试都会失败。
    通过 API 调用 /api/auth/login 获取 token，再用 page.evaluate 注入 localStorage，
    避免依赖具体的登录表单 UI（选择器易变），且不阻塞测试流程。

    失败时抛 RuntimeError，由调用方决定是否中止测试。
    """
    auth_cfg = cfg.get("auth", {})
    if not auth_cfg.get("enabled", False):
        return
    api_url = cfg["service"]["api_url"]
    login_endpoint = auth_cfg["login_endpoint"]
    creds = auth_cfg["credentials"]
    token_key = auth_cfg["token_storage_key"]
    token_field = auth_cfg["token_field"]

    # 必须先访问页面，让同源 localStorage 可用
    # 用 domcontentloaded 避免被背景图等持续加载资源阻塞（与 playwright_wait_strategy 配置对齐）
    page.goto(cfg["service"]["frontend_url"], wait_until="domcontentloaded")

    login_url = f"{api_url}{login_endpoint}"
    # Playwright APIRequestContext.post 不支持 json 参数，需用 data + headers 显式传 JSON
    resp = ctx.request.post(
        login_url,
        data=json.dumps(creds),
        headers={"Content-Type": "application/json"},
    )
    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"Login API returned non-JSON (HTTP {resp.status}): {e}")

    if not data.get("ok", False):
        raise RuntimeError(f"Login failed: {data.get('message', data)}")

    token = data.get(token_field)
    if not token:
        raise RuntimeError(f"Login response missing '{token_field}': {data}")

    # 注入 localStorage：前端 restoreSession() 会读取此 token 并调 /api/auth/me 验证
    page.evaluate(
        '(args) => localStorage.setItem(args[0], args[1])',
        [token_key, token]
    )

    # 重置导航栏折叠状态：v2 导航栏将 navCollapsed 持久化到 localStorage，
    # 若上轮测试遗留折叠态，本轮测试将找不到 .tab-btn（折叠态渲染为 .icon-btn）
    # 为什么放在 token 注入之后：避免页面刷新后 token 丢失
    page.evaluate('localStorage.setItem("navCollapsed", "false")')

    # 重新加载页面：前端 restoreSession() 在页面加载时执行，
    # 注入 token 后必须 reload 才能让前端读取新 token 并渲染主应用（而非登录页）
    # 为什么用 domcontentloaded：避免背景图等持续加载资源阻塞（与 playwright_wait_strategy 对齐）
    page.reload(wait_until="domcontentloaded")
    # 等待前端 restoreSession 异步调用 /api/auth/me 完成并渲染主应用
    # 为什么用 wait_for_selector：restoreSession 是异步的，reload 返回时主应用可能尚未渲染
    page.wait_for_selector(".nav-tabs, .nav-collapsed", timeout=10000)

    if not quiet:
        print(f"Authenticated via API (token injected to localStorage['{token_key}'])")


# ============================================================
# 编码检测工具（系统清理模块复盘补充）
# 通过 Unicode 码点匹配规避终端 GBK 编码对中文字符串的破坏
# ============================================================

def get_dom_text_codepoints(page, selector):
    """获取 DOM 元素文本的 Unicode 码点列表。

    用 page.evaluate 在浏览器端取 textContent，再在 Python 端转码点，
    避免终端 GBK 编码影响字符串比对（has_text 中文匹配失败的根因）。

    参数：
        page: Playwright Page 对象
        selector: CSS 选择器（匹配多个元素时返回多组码点）

    返回：
        list[list[int]]：每个元素的文本码点列表，例如 [[0x4eea, 0x8868, 0x76d8], ...]
        若 evaluate 失败（如选择器无匹配）返回空列表
    """
    # 在浏览器端取 textContent，绕过 Python 字符串编码透传问题
    js = f'''() => {{
        const els = document.querySelectorAll({selector!r});
        return Array.from(els).map(e => e.textContent || '');
    }}'''
    try:
        texts = page.evaluate(js)
    except Exception:
        return []
    # 在 Python 端转 Unicode 码点，便于后续比对（避免 has_text 中文匹配坑）
    return [[ord(c) for c in t] for t in texts]


def check_encoding(page, fffd_codepoint="0xFFFD", scan_selectors=None):
    """检测页面 DOM 文本是否包含 U+FFFD 替换字符（编码乱码标志）。

    参数：
        page: Playwright Page 对象
        fffd_codepoint: 替换字符码点字符串（默认 "0xFFFD"），
                       用字符串避免 YAML 解析器对 0xFFFD 的歧义
        scan_selectors: 扫描的 CSS 选择器列表；为 None 时扫 body 全文

    返回：
        dict：
          - has_fffd (bool)：是否检测到 U+FFFD
          - affected_selectors (list[str])：哪些选择器命中了 U+FFFD
          - sample_codepoints (list[int])：首个命中位置的码点片段（用于排查）
    """
    # 字符串码点转 int（如 "0xFFFD" -> 0xFFFD），兼容十六进制和十进制
    try:
        target_cp = int(fffd_codepoint, 16) if isinstance(fffd_codepoint, str) else int(fffd_codepoint)
    except (ValueError, TypeError):
        target_cp = 0xFFFD

    selectors = scan_selectors if scan_selectors else ["body"]
    affected = []
    sample = []
    for sel in selectors:
        cps_list = get_dom_text_codepoints(page, sel)
        for cps in cps_list:
            if target_cp in cps:
                affected.append(sel)
                # 取 U+FFFD 前后各 10 个码点作为现场样本，便于事后排查
                idx = cps.index(target_cp)
                start = max(0, idx - 10)
                end = min(len(cps), idx + 11)
                sample = cps[start:end]
                break
        if affected:
            break

    return {
        "has_fffd": bool(affected),
        "affected_selectors": affected,
        "sample_codepoints": sample,
    }


# ============================================================
# 服务生命周期工具（系统清理模块复盘补充）
# 测试前停止占用端口的旧进程 / 验证端口监听
# 通过 PowerShell 的 Get-NetTCPConnection 实现，避免硬编码 PID
# ============================================================

def stop_port_processes(ports, shell_executable="powershell.exe"):
    """停止占用指定端口的进程。

    用 PowerShell Get-NetTCPConnection 反查占用端口的进程 PID，再 Stop-Process。
    避免 taskkill 模糊匹配进程名误杀同名进程。

    参数：
        ports: 端口列表，如 [3000, 5173]
        shell_executable: PowerShell 可执行文件名

    返回：
        dict：每个端口的停止结果 {port: {"stopped": bool, "pid": int|None, "error": str|None}}
    """
    results = {}
    for port in ports:
        # 用 Get-NetTCPConnection 反查 Listen 状态的进程 PID
        # 注意：PowerShell 不支持 &&，用 ; 分隔顺序执行
        ps_script = (
            f"$conn = Get-NetTCPConnection -State Listen -LocalPort {port} -ErrorAction SilentlyContinue; "
            f"if ($conn) {{ Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue; "
            f"Write-Output $conn.OwningProcess }} else {{ Write-Output '0' }}"
        )
        try:
            proc = subprocess.run(
                [shell_executable, "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=10, encoding="utf-8"
            )
            output = (proc.stdout or "").strip()
            if output and output != "0":
                # 成功停止并输出被停止的 PID
                results[port] = {"stopped": True, "pid": int(output), "error": None}
            else:
                # 端口未被占用或进程已退出
                results[port] = {"stopped": False, "pid": None, "error": None}
        except Exception as e:
            results[port] = {"stopped": False, "pid": None, "error": str(e)[:100]}
    return results


def verify_ports_listening(ports, shell_executable="powershell.exe"):
    """验证端口是否处于 Listen 状态。

    参数：
        ports: 端口列表
        shell_executable: PowerShell 可执行文件名

    返回：
        dict：{port: bool}，True 表示该端口在监听
    """
    results = {}
    for port in ports:
        ps_script = (
            f"$conn = Get-NetTCPConnection -State Listen -LocalPort {port} -ErrorAction SilentlyContinue; "
            f"if ($conn) {{ Write-Output '1' }} else {{ Write-Output '0' }}"
        )
        try:
            proc = subprocess.run(
                [shell_executable, "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=5, encoding="utf-8"
            )
            output = (proc.stdout or "").strip()
            results[port] = (output == "1")
        except Exception:
            results[port] = False
    return results


# ============================================================
# 临时文件清理工具（系统清理模块复盘补充）
# 测试产生的临时 Python 脚本和截图的统一清理
# ============================================================

def cleanup_temp_files(patterns, cleanup_dirs=None):
    """按 pattern 清理临时文件。

    约定临时文件命名前缀为 _test_，便于识别和清理，
    避免误删项目正式文件。

    参数：
        patterns: glob pattern 列表，如 ["_test_*.py", "_test_*.png"]
        cleanup_dirs: 清理目录列表，默认 ["."]

    返回：
        dict：
          - deleted (list[str])：已删除的文件路径
          - failed (list[dict])：删除失败的文件和错误信息
          - total (int)：匹配到的总文件数
    """
    dirs = cleanup_dirs if cleanup_dirs else ["."]
    deleted = []
    failed = []
    total = 0

    for d in dirs:
        if not os.path.exists(d):
            continue
        for pattern in patterns:
            # glob 递归匹配，确保子目录中的临时文件也能清理
            full_pattern = os.path.join(d, "**", pattern)
            for fp in glob.glob(full_pattern, recursive=True):
                total += 1
                try:
                    os.remove(fp)
                    deleted.append(fp)
                except Exception as e:
                    failed.append({"file": fp, "error": str(e)[:100]})

    return {
        "deleted": deleted,
        "failed": failed,
        "total": total,
    }
