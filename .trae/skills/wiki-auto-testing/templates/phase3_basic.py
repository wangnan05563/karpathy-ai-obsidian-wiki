# -*- coding: utf-8 -*-
"""Phase 3: Basic tests - homepage, navigation, page elements, console errors."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from _shared import (
    TestResults, click_nav_tab, js_click, get_enabled_phases,
    setup_browser, teardown_browser
)


def test_homepage(page, cfg, results):
    """Test homepage loads successfully."""
    frontend_url = cfg["service"]["frontend_url"]
    timeout_cfg = cfg.get("timeout", {})
    nav_cfg = cfg.get("navigation", {})
    # 从配置读取等待策略：默认 domcontentloaded，避免 networkidle 被持续加载资源阻塞
    wait_until = nav_cfg.get("page_load_wait_until", "domcontentloaded")
    try:
        page.goto(frontend_url, wait_until=wait_until,
                  timeout=timeout_cfg.get("page_load_ms", 30000))
        title = page.title()
        results.log("Homepage-Load", bool(title), f"Title: {title[:50]}")
    except Exception as e:
        results.log("Homepage-Load", False, f"Error: {str(e)[:80]}")


def test_api_health(ctx, cfg, results):
    """Test API health endpoint."""
    api_url = cfg["service"]["api_url"]
    health_ep = cfg["service"]["health_endpoint"]
    try:
        resp = ctx.request.get(f"{api_url}{health_ep}")
        results.log("API-Health", resp.status == 200, f"Status: {resp.status}")
    except Exception as e:
        results.log("API-Health", False, f"Error: {str(e)[:80]}")


def test_navigation(page, cfg, results):
    """Test navigation tabs. Skips disabled tabs (business logic may disable them)."""
    tab_sel = cfg["navigation"]["tab_selector"]
    nav_wait = cfg["navigation"]["page_render_wait_ms"]
    for p in cfg["navigation"]["pages"]:
        label = p["label"]
        try:
            tab = page.locator(f'{tab_sel}:has-text("{label}")')
            if tab.count() > 0:
                # 检查是否 disabled（如"编译进度"在无编译任务时被禁用，属正常业务逻辑）
                is_disabled = tab.first.get_attribute('disabled') is not None
                if is_disabled:
                    results.log(f"Nav-{p['key']}", True, f"Tab disabled (expected): {label}")
                else:
                    tab.first.click(timeout=5000)
                    page.wait_for_timeout(nav_wait)
                    results.log(f"Nav-{p['key']}", True, f"Clicked: {label}")
            else:
                results.log(f"Nav-{p['key']}", False, f"Tab not found: {label}")
        except Exception as e:
            results.log(f"Nav-{p['key']}", False, f"Error: {str(e)[:80]}")


def test_page_elements(page, cfg, results):
    """Test expected elements exist on each page (navigates to each page first)."""
    tab_sel = cfg["navigation"]["tab_selector"]
    nav_wait = cfg["navigation"]["page_render_wait_ms"]
    for p in cfg["navigation"]["pages"]:
        # 先导航到该页面，确保元素可见（避免上一轮导航停留在其他页面导致元素不可见）
        clicked = click_nav_tab(page, tab_sel, p["label"], nav_wait)
        if not clicked:
            # tab disabled 或不存在，跳过元素检查
            continue
        # 元素检查前先点击 pre_open_selectors 列出的按钮，展开条件渲染的隐藏面板
        # 为什么放在 page 级而不是 element 级：同一页面多个元素可能共享同一面板，
        # 在面板外层 click 一次即可，比逐个 element.click 重复触发更稳定
        for pre_sel in p.get("pre_open_selectors", []) or []:
            try:
                btn = page.locator(pre_sel)
                if btn.count() > 0:
                    js_click(page, pre_sel)
                    page.wait_for_timeout(400)  # 等面板过渡动画完成
            except Exception:
                # 展开失败不阻塞元素检查（元素可能本就在面板外可见）
                pass
        for elem in p.get("expected_elements", []):
            sel = elem["selector"]
            name = elem.get("name", sel)
            count = page.locator(sel).count()
            results.log(f"Element-{p['key']}-{name}", count > 0, f"Count: {count}")


def run_phase(cfg, results, page, ctx, shot_dir, quiet=False):
    """Execute Phase 3 tests."""
    if not quiet:
        print("\n=== Phase 3: Basic Tests ===")
    test_homepage(page, cfg, results)
    test_api_health(ctx, cfg, results)
    test_navigation(page, cfg, results)
    test_page_elements(page, cfg, results)
    page.screenshot(path=os.path.join(shot_dir, "homepage.png"))
