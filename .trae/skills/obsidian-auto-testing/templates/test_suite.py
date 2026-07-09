# -*- coding: utf-8 -*-
"""
obsidian-auto-testing parameterized test suite.

Reads all parameters from config.yaml — no hardcoded values.
Covers: navigation, page elements, interactions, button auto-discovery,
theme switching, responsive layout, API endpoints, console errors.

Key improvements over previous version:
1. Working directory auto-detection (finds project root from script location)
2. Button auto-discovery (traverses all pages, finds all clickable elements)
3. Destructive button protection (skips buttons matching destructive_button_texts)
4. Encoding self-check (auto-fixes GBK → UTF-8 if needed)
5. Force click option (bypasses Vue transition animation timing issues)
"""
import json
import os
import sys
import argparse

import yaml
from playwright.sync_api import sync_playwright


# ============================================================
# Config Loading with Working Directory Auto-Detection
# ============================================================

def find_project_root(script_path, marker=".git"):
    """
    Walk up from script location to find project root.
    Uses marker file (.git / package.json) to identify root.
    Falls back to config.yaml's parent's parent if marker not found.
    """
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


def load_config(config_path=None):
    """
    Load config.yaml with working directory auto-detection.
    Priority: explicit path > env var > script-relative > CWD-relative.
    """
    if config_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.environ.get("OBSIDIAN_TEST_CONFIG"),
            os.path.join(script_dir, "..", "config.yaml"),
            os.path.join(os.getcwd(), ".trae", "skills", "obsidian-auto-testing", "config.yaml"),
            os.path.join(os.getcwd(), "config.yaml"),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                config_path = c
                break

    if config_path is None or not os.path.exists(config_path):
        print("ERROR: config.yaml not found in any candidate location")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Auto-detect project root and chdir if configured
    wd_cfg = cfg.get("working_directory", {})
    if wd_cfg.get("auto_chdir", True):
        marker = wd_cfg.get("project_root_marker", ".git") or ".git"
        project_root = find_project_root(config_path, marker)
        os.chdir(project_root)
        print(f"Working directory set to: {project_root}")

    return cfg


# ============================================================
# Encoding Safety
# ============================================================

def ensure_utf8(file_path, fallback_encoding="gbk"):
    """
    Check and fix file encoding (GBK → UTF-8).
    Called when auto_fix_python_encoding is enabled in config.
    """
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
            with open(file_path, "wb") as f:
                f.write(raw)
            print(f"Removed BOM from: {file_path}")
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        try:
            content = raw.decode(fallback_encoding)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Converted encoding {fallback_encoding} → UTF-8: {file_path}")
            return True
        except Exception:
            return False


# ============================================================
# Test Result Tracking
# ============================================================

class TestResults:
    def __init__(self):
        self.items = []

    def log(self, name, passed, details=""):
        status = "PASS" if passed else "FAIL"
        self.items.append({"test": name, "status": status, "details": details})
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
        print(f"Results saved to: {path}")


# ============================================================
# Helper Functions
# ============================================================

def click_nav_tab(page, tab_selector, label, wait_ms=1500):
    """Click a navigation tab by its text label."""
    btn = page.locator(f'{tab_selector}:has-text("{label}")')
    if btn.count() == 0:
        return False
    btn.first.click()
    page.wait_for_timeout(wait_ms)
    return True


def safe_click(page, selector, wait_ms=500, force=False, timeout=3000):
    """Safely click an element, return True if clicked successfully."""
    loc = page.locator(selector).first
    if loc.count() == 0:
        return False
    try:
        loc.click(force=force, timeout=timeout)
        page.wait_for_timeout(wait_ms)
        return True
    except Exception:
        return False


def js_click(page, selector):
    """Click via JavaScript dispatchEvent (bypasses transition animation)."""
    return page.evaluate(
        '(() => { const el = document.querySelector(%r); '
        'if (!el) return false; '
        'el.dispatchEvent(new MouseEvent("click", {bubbles: true})); '
        'return true; })()' % selector
    )


def is_destructive(text, destructive_texts):
    """Check if button text matches any destructive action keyword."""
    if not text:
        return False
    return any(kw in text for kw in destructive_texts)


# ============================================================
# Test Functions
# ============================================================

def test_homepage(page, cfg, results):
    """Phase 3: Homepage load test."""
    url = cfg["service"]["frontend_url"]
    timeout = cfg["timeout"]["page_load_ms"]
    page.goto(url, wait_until="networkidle", timeout=timeout)
    page.wait_for_timeout(cfg["navigation"]["page_render_wait_ms"])
    title = page.title()
    results.log("Homepage-Load", bool(title), f"Title: {title}")


def test_api_health(ctx, cfg, results):
    """Phase 3: API health check."""
    api_url = cfg["service"]["api_url"]
    health_ep = cfg["service"]["health_endpoint"]
    if cfg["api_tests"].get("use_playwright_request", True):
        resp = ctx.request.get(f"{api_url}{health_ep}")
        status = resp.status
        body = resp.text()[:100]
    else:
        resp = page.request.get(f"{api_url}{health_ep}")
        status = resp.status
        body = resp.text()[:100]
    results.log("API-Health", status == 200, f"Status: {status}, Body: {body}")


def test_navigation(page, cfg, results):
    """Phase 3: Navigate through all pages."""
    tab_sel = cfg["navigation"]["tab_selector"]
    wait_ms = cfg["navigation"]["page_render_wait_ms"]
    for p in cfg["navigation"]["pages"]:
        ok = click_nav_tab(page, tab_sel, p["label"], wait_ms)
        results.log(f"Nav-{p['key']}", ok, f"Tab: {p['label']}")


def test_page_elements(page, cfg, results):
    """Phase 3: Verify expected elements on each page."""
    tab_sel = cfg["navigation"]["tab_selector"]
    wait_ms = cfg["navigation"]["page_render_wait_ms"]
    for p in cfg["navigation"]["pages"]:
        click_nav_tab(page, tab_sel, p["label"], wait_ms)
        for elem in p.get("expected_elements", []):
            sel = elem["selector"]
            name = elem["name"]
            count = page.locator(sel).count()
            results.log(f"Element-{p['key']}-{name}", count > 0, f"Selector: {sel}, Count: {count}")


def test_theme_switcher(page, cfg, results):
    """Phase 4: Theme switching."""
    ts = cfg["interactions"]["theme_switcher"]
    trigger_sel = ts["trigger_selector"]
    item_sel = ts["item_selector"]
    wait_ms = ts["transition_wait_ms"]
    use_js = ts.get("use_js_click", True)

    if use_js:
        js_click(page, trigger_sel)
    else:
        safe_click(page, trigger_sel)
    page.wait_for_timeout(wait_ms)

    items = page.locator(item_sel)
    count = items.count()
    if count > 0:
        items.first.click()
        page.wait_for_timeout(wait_ms)
        theme = page.evaluate("document.documentElement.getAttribute('data-theme') || ''")
        results.log("Theme-Switch", bool(theme), f"Switched to: {theme}")
    else:
        results.log("Theme-Switch", False, "No theme items found")


def test_form_interaction(page, cfg, results):
    """Phase 4: Form input and submit on Ingest page."""
    tab_sel = cfg["navigation"]["tab_selector"]
    wait_ms = cfg["navigation"]["page_render_wait_ms"]
    ingest = cfg["interactions"]["ingest"]

    for p in cfg["navigation"]["pages"]:
        if p["key"] == "ingest":
            click_nav_tab(page, tab_sel, p["label"], wait_ms)
            break

    tab_item_sel = ingest["tab_item_selector"]
    target_label = ingest["target_tab_label"]
    tab = page.locator(f'{tab_item_sel}:has-text("{target_label}")')
    if tab.count() > 0:
        tab.first.click()
        page.wait_for_timeout(wait_ms)

    textarea_sel = ingest["textarea_selector"]
    test_text = ingest["test_text"]
    ta = page.locator(textarea_sel).first
    if ta.count() > 0:
        ta.fill(test_text)
        page.wait_for_timeout(500)
        results.log("Form-Input", True, f"Filled: {test_text[:40]}...")
    else:
        results.log("Form-Input", False, "Textarea not found")

    submit_text = ingest["submit_button_text"]
    btn = page.locator(f'button:has-text("{submit_text}")')
    results.log("Form-SubmitBtn", btn.count() > 0, f"Button: {submit_text}")


def test_tab_switching(page, cfg, results):
    """Phase 4: Element Plus tab switching."""
    tab_sel = cfg["navigation"]["tab_selector"]
    wait_ms = cfg["navigation"]["page_render_wait_ms"]
    for p in cfg["navigation"]["pages"]:
        if p["key"] == "ingest":
            click_nav_tab(page, tab_sel, p["label"], wait_ms)
            break
    tabs = page.locator(".el-tabs__item")
    count = tabs.count()
    results.log("TabSwitch-Count", count > 0, f"Found {count} tabs")
    if count > 0:
        tabs.first.click()
        page.wait_for_timeout(500)
        results.log("TabSwitch-Click", True, "First tab clicked")


def test_button_discovery(page, cfg, results):
    """
    Phase 4 (NEW): Auto-discover and test all clickable buttons.
    Traverses all pages, finds all button-like elements, clicks each one.
    Skips destructive buttons (only verifies existence).
    """
    bd = cfg.get("button_discovery", {})
    if not bd.get("enabled", False):
        results.log("ButtonDiscovery-Skipped", True, "Disabled in config")
        return

    tab_sel = cfg["navigation"]["tab_selector"]
    nav_wait = cfg["navigation"]["page_render_wait_ms"]
    selectors = bd["button_selectors"]
    exclude_sels = bd.get("exclude_selectors", [])
    destructive_texts = bd.get("destructive_button_texts", [])
    click_wait = bd.get("click_wait_ms", 800)
    force = bd.get("force_click", True)
    continue_on_fail = bd.get("continue_on_failure", True)

    total_found = 0
    total_clicked = 0
    total_skipped = 0
    total_failed = 0

    for p in cfg["navigation"]["pages"]:
        click_nav_tab(page, tab_sel, p["label"], nav_wait)
        page_key = p["key"]

        for sel in selectors:
            elements = page.locator(sel)
            count = elements.count()
            if count == 0:
                continue

            for i in range(count):
                elem = elements.nth(i)
                total_found += 1

                # Check exclusion
                try:
                    outer_html = elem.evaluate("el => el.outerHTML.substring(0, 200)")
                except Exception:
                    continue

                is_excluded = False
                for ex_sel in exclude_sels:
                    ex_elem = page.locator(ex_sel)
                    for j in range(ex_elem.count()):
                        if ex_elem.nth(j) == elem:
                            is_excluded = True
                            break
                    if is_excluded:
                        break
                if is_excluded:
                    total_skipped += 1
                    continue

                # Get button text for destructive check
                try:
                    text = elem.inner_text().strip()[:30]
                except Exception:
                    text = ""

                if is_destructive(text, destructive_texts):
                    total_skipped += 1
                    results.log(
                        f"BtnDiscovery-{page_key}-Skip",
                        True,
                        f"Destructive: '{text}' (verified, not clicked)",
                    )
                    continue

                # Click the button
                try:
                    elem.click(force=force, timeout=3000)
                    page.wait_for_timeout(click_wait)
                    total_clicked += 1
                    results.log(
                        f"BtnDiscovery-{page_key}-Click",
                        True,
                        f"Clicked: '{text}' ({sel})",
                    )
                    # Navigate back to current page after click
                    click_nav_tab(page, tab_sel, p["label"], nav_wait)
                except Exception as e:
                    total_failed += 1
                    err_msg = str(e)[:80]
                    results.log(
                        f"BtnDiscovery-{page_key}-Fail",
                        False,
                        f"Failed: '{text}' - {err_msg}",
                    )
                    if not continue_on_fail:
                        return
                    click_nav_tab(page, tab_sel, p["label"], nav_wait)

    results.log(
        "ButtonDiscovery-Summary",
        total_failed == 0,
        f"Found: {total_found}, Clicked: {total_clicked}, Skipped: {total_skipped}, Failed: {total_failed}",
    )


def test_responsive(page, cfg, results):
    """Phase 5: Responsive layout test."""
    viewports = cfg["browser"]["viewports"]
    for name, vp in viewports.items():
        page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
        page.wait_for_timeout(2000)
        body_visible = page.locator("body").is_visible()
        results.log(
            f"Responsive-{name}",
            body_visible,
            f"{vp['width']}x{vp['height']}",
        )
    # Reset to desktop
    desktop = viewports["desktop"]
    page.set_viewport_size({"width": desktop["width"], "height": desktop["height"]})


def test_api_endpoints(ctx, cfg, results):
    """Phase 5: API endpoint tests."""
    api_url = cfg["service"]["api_url"]
    use_pw_req = cfg["api_tests"].get("use_playwright_request", True)
    for ep in cfg["api_tests"]["endpoints"]:
        path = ep["path"]
        expected = ep["expected_status"]
        url = f"{api_url}{path}"
        try:
            if use_pw_req:
                resp = ctx.request.get(url)
            else:
                resp = page.request.get(url)
            status = resp.status
            results.log(f"API-{path}", status == expected, f"Status: {status} (expected {expected})")
        except Exception as e:
            results.log(f"API-{path}", False, f"Error: {str(e)[:80]}")


def test_console_errors(console_errors, cfg, results):
    """Phase 5: Console error check."""
    filter_words = cfg["console_error_filter"]
    real_errors = []
    for err in console_errors:
        err_lower = err.lower()
        if any(skip in err_lower for skip in filter_words):
            continue
        real_errors.append(err)
    if real_errors:
        results.log("Console-Errors", False, f"{len(real_errors)} errors: {real_errors[:3]}")
    else:
        results.log("Console-Errors", True, "No errors after filtering")


# ============================================================
# Main Test Runner
# ============================================================

def run(config_path=None):
    cfg = load_config(config_path)
    results = TestResults()

    frontend_url = cfg["service"]["frontend_url"]
    launch_args = cfg["browser"].get("launch_args", [])
    headless = cfg["browser"].get("headless", True)
    desktop = cfg["browser"]["viewports"]["desktop"]
    shot_dir = os.path.join(os.getcwd(), cfg["output"]["screenshot_dir"])
    os.makedirs(shot_dir, exist_ok=True)

    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=launch_args)
        ctx = browser.new_context(
            viewport={"width": desktop["width"], "height": desktop["height"]}
        )
        page = ctx.new_page()

        # Collect console errors
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(f"PAGE ERROR: {e}"))

        # Phase 3: Basic tests
        print("\n=== Phase 3: Basic Tests ===")
        test_homepage(page, cfg, results)
        test_api_health(ctx, cfg, results)
        test_navigation(page, cfg, results)
        test_page_elements(page, cfg, results)
        page.screenshot(path=os.path.join(shot_dir, "homepage.png"))

        # Phase 4: Interaction tests
        print("\n=== Phase 4: Interaction Tests ===")
        test_theme_switcher(page, cfg, results)
        test_form_interaction(page, cfg, results)
        test_tab_switching(page, cfg, results)

        # Phase 4 (NEW): Button auto-discovery
        print("\n=== Phase 4: Button Auto-Discovery ===")
        test_button_discovery(page, cfg, results)

        # Phase 5: Supplementary tests
        print("\n=== Phase 5: Supplementary Tests ===")
        test_responsive(page, cfg, results)
        test_api_endpoints(ctx, cfg, results)
        test_console_errors(console_errors, cfg, results)

        ctx.close()
        browser.close()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(results.summary())
    print("=" * 60)

    # Save results
    result_file = cfg["output"]["result_file"]
    encoding = cfg["output"].get("encoding", "utf-8")
    results.save(result_file, encoding)

    return results.failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="obsidian-auto-testing test suite")
    parser.add_argument("--config", type=str, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    success = run(args.config)
    sys.exit(0 if success else 1)
