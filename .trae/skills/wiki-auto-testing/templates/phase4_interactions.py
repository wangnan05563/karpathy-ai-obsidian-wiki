# -*- coding: utf-8 -*-
"""Phase 4: Interaction tests - theme, forms, tabs, button auto-discovery."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from _shared import (
    TestResults, click_nav_tab, safe_click, js_click, is_destructive
)


def test_theme_switcher(page, cfg, results):
    """Test theme switcher interaction."""
    tc = cfg["interactions"].get("theme_switcher", {})
    trigger_sel = tc.get("trigger_selector")
    item_sel = tc.get("item_selector")
    wait_ms = tc.get("transition_wait_ms", 1000)
    use_js = tc.get("use_js_click", True)

    if not trigger_sel or not item_sel:
        results.log("Theme-Switch", True, "Skipped (no config)")
        return

    if use_js:
        js_click(page, trigger_sel)
    else:
        safe_click(page, trigger_sel)
    page.wait_for_timeout(wait_ms)

    items = page.locator(item_sel)
    if items.count() > 0:
        items.first.click()
        page.wait_for_timeout(wait_ms)
        theme = page.evaluate("document.documentElement.getAttribute('data-theme') || ''")
        results.log("Theme-Switch", bool(theme), f"Switched to: {theme}")
    else:
        results.log("Theme-Switch", False, "No theme items found")


def test_form_interaction(page, cfg, results):
    """Test form input and submit on Ingest page."""
    tab_sel = cfg["navigation"]["tab_selector"]
    wait_ms = cfg["navigation"]["page_render_wait_ms"]
    ingest = cfg["interactions"].get("ingest", {})

    for p in cfg["navigation"]["pages"]:
        if p["key"] == "ingest":
            click_nav_tab(page, tab_sel, p["label"], wait_ms)
            break

    tis = ingest.get("tab_item_selector")
    tlb = ingest.get("target_tab_label")
    if tis and tlb:
        tab = page.locator(tis + ':has-text("' + tlb + '")')
        if tab.count() > 0:
            tab.first.click()
            page.wait_for_timeout(wait_ms)

    ts = ingest.get("textarea_selector")
    tt = ingest.get("test_text", "Test input")
    ta = page.locator(ts).first if ts else None
    if ta and ta.count() > 0:
        ta.fill(tt)
        page.wait_for_timeout(500)
        results.log("Form-Input", True, "Filled: " + tt[:40])
    else:
        results.log("Form-Input", False, "Textarea not found")

    sbt = ingest.get("submit_button_text")
    if sbt:
        btn = page.locator('button:has-text("' + sbt + '")')
        results.log("Form-SubmitBtn", btn.count() > 0, "Button: " + sbt)


def test_tab_switching(page, cfg, results):
    """Test Element Plus tab switching."""
    tab_sel = cfg["navigation"]["tab_selector"]
    wait_ms = cfg["navigation"]["page_render_wait_ms"]
    for p in cfg["navigation"]["pages"]:
        if p["key"] == "ingest":
            click_nav_tab(page, tab_sel, p["label"], wait_ms)
            break
    tabs = page.locator(".el-tabs__item")
    count = tabs.count()
    results.log("TabSwitch-Count", count > 0, "Found " + str(count) + " tabs")
    if count > 0:
        tabs.first.click()
        page.wait_for_timeout(500)
        results.log("TabSwitch-Click", True, "First tab clicked")


def test_button_discovery(page, cfg, results):
    """Auto-discover and test all clickable buttons."""
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

    total_found = total_clicked = total_skipped = total_failed = 0

    for p in cfg["navigation"]["pages"]:
        click_nav_tab(page, tab_sel, p["label"], nav_wait)
        for sel in selectors:
            elements = page.locator(sel)
            for i in range(elements.count()):
                elem = elements.nth(i)
                total_found += 1

                # Exclusion check
                excluded = False
                for ex in exclude_sels:
                    try:
                        matched = elem.evaluate('e => e.matches("' + ex + '")')
                    except Exception:
                        matched = False
                    if matched:
                        excluded = True
                        break
                if excluded:
                    total_skipped += 1
                    continue

                # Destructive check
                try:
                    text = elem.inner_text().strip()[:30]
                except Exception:
                    text = ""
                if is_destructive(text, destructive_texts):
                    total_skipped += 1
                    continue

                # Click
                try:
                    elem.click(force=force, timeout=3000)
                    page.wait_for_timeout(click_wait)
                    total_clicked += 1
                    click_nav_tab(page, tab_sel, p["label"], nav_wait)
                except Exception:
                    total_failed += 1
                    if not continue_on_fail:
                        return
                    click_nav_tab(page, tab_sel, p["label"], nav_wait)

    results.log("ButtonDiscovery-Summary", total_failed == 0,
                "Found:" + str(total_found) + " Clicked:" + str(total_clicked) +
                " Skipped:" + str(total_skipped) + " Failed:" + str(total_failed))


def run_phase(cfg, results, page, ctx, quiet=False):
    """Execute Phase 4 tests."""
    if not quiet:
        print("\n=== Phase 4: Interaction Tests ===")
    test_theme_switcher(page, cfg, results)
    test_form_interaction(page, cfg, results)
    test_tab_switching(page, cfg, results)

    if not quiet:
        print("\n=== Phase 4: Button Auto-Discovery ===")
    test_button_discovery(page, cfg, results)
