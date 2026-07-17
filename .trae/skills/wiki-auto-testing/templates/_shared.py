# -*- coding: utf-8 -*-
"""
Shared utilities for wiki-auto-testing.
Contains config loading, result tracking, and helper functions.
All parameters from config.yaml - no hardcoded values.
"""
import json
import os
import sys
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

    @property
    def passed(self):
        return sum(1 for r in self.items if r["status"] == "PASS")

    @property
    def failed(self):
        return sum(1 for r in self.items if r["status"] == "FAIL")

    @property
    def total(self):
        return len(self.items)

    def summary(self):
        return f"Total: {self.total} | Passed: {self.passed} | Failed: {self.failed}"

    def save(self, path, encoding="utf-8"):
        with open(path, "w", encoding=encoding) as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)


# ============================================================
# Playwright Helpers
# ============================================================

def click_nav_tab(page, tab_selector, label, wait_ms=1500):
    """Click a navigation tab by label text."""
    tab = page.locator(f'{tab_selector}:has-text("{label}")')
    if tab.count() > 0:
        tab.first.click()
        page.wait_for_timeout(wait_ms)
        return True
    return False


def safe_click(page, selector, wait_ms=500, force=False, timeout=3000):
    """Safely click an element."""
    elem = page.locator(selector)
    if elem.count() > 0:
        elem.first.click(force=force, timeout=timeout)
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
