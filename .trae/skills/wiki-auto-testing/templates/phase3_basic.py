# -*- coding: utf-8 -*-
"""Phase 3: Basic tests - homepage, navigation, page elements, console errors."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from _shared import (
    TestResults, click_nav_tab, get_enabled_phases,
    setup_browser, teardown_browser
)


def test_homepage(page, cfg, results):
    """Test homepage loads successfully."""
    frontend_url = cfg["service"]["frontend_url"]
    timeout_cfg = cfg.get("timeout", {})
    try:
        page.goto(frontend_url, wait_until="networkidle",
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
    """Test navigation tabs."""
    tab_sel = cfg["navigation"]["tab_selector"]
    nav_wait = cfg["navigation"]["page_render_wait_ms"]
    for p in cfg["navigation"]["pages"]:
        click_nav_tab(page, tab_sel, p["label"], nav_wait)


def test_page_elements(page, cfg, results):
    """Test expected elements exist on each page."""
    for p in cfg["navigation"]["pages"]:
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
