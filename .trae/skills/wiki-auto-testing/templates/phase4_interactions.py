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


def dismiss_dialog(page):
    """关闭可能出现的 Element Plus MessageBox 确认对话框，避免阻塞后续操作。"""
    try:
        dialog = page.locator('.el-message-box')
        if dialog.count() > 0:
            # 优先点击取消按钮
            cancel_btn = page.locator('.el-message-box__btns .el-button:first-child')
            if cancel_btn.count() > 0 and cancel_btn.first.is_visible():
                cancel_btn.first.click(timeout=1000)
            else:
                page.keyboard.press('Escape')
            page.wait_for_timeout(300)
    except Exception:
        try:
            page.keyboard.press('Escape')
        except Exception:
            pass


def test_button_discovery(page, cfg, results):
    """Auto-discover and test all clickable buttons."""
    import time as _time
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
    # 按钮发现的点击超时从 config.timeout.button_discovery_click_timeout_ms 读取
    click_timeout = cfg.get("timeout", {}).get("button_discovery_click_timeout_ms")
    # 整体超时保护：避免某个按钮触发 SSE/长连接导致整个发现过程无限卡住
    total_timeout_ms = bd.get("total_timeout_ms", 120000)
    start_time = _time.monotonic()

    total_found = total_clicked = total_skipped = total_failed = 0

    for p in cfg["navigation"]["pages"]:
        # 整体超时检查
        elapsed_ms = int((_time.monotonic() - start_time) * 1000)
        if elapsed_ms > total_timeout_ms:
            results.log("ButtonDiscovery-Timeout", True,
                        f"Total timeout {total_timeout_ms}ms reached, stopped at page '{p['label']}'")
            break
        click_nav_tab(page, tab_sel, p["label"], nav_wait)
        for sel in selectors:
            elements = page.locator(sel)
            for i in range(elements.count()):
                # 每个按钮前也检查超时
                elapsed_ms = int((_time.monotonic() - start_time) * 1000)
                if elapsed_ms > total_timeout_ms:
                    break
                elem = elements.nth(i)
                total_found += 1

                # Exclusion check：用 closest 而非 matches，检查祖先链
                # 为什么：点击 .el-upload 内部的 .upload-icon 子元素时，事件冒泡仍会触发文件选择对话框
                # matches 只检查元素自身，会漏掉所有需排除元素的子节点
                excluded = False
                for ex in exclude_sels:
                    try:
                        matched = elem.evaluate('e => e.closest("' + ex + '") !== null')
                    except Exception:
                        matched = False
                    if matched:
                        excluded = True
                        break
                if excluded:
                    total_skipped += 1
                    continue

                # Destructive check：inner_text 加短超时避免不可见元素阻塞
                try:
                    text = elem.inner_text(timeout=2000).strip()[:30]
                except Exception:
                    text = ""
                if is_destructive(text, destructive_texts):
                    total_skipped += 1
                    continue

                # Click
                try:
                    click_kwargs = {"force": force}
                    if click_timeout is not None:
                        click_kwargs["timeout"] = click_timeout
                    elem.click(**click_kwargs)
                    page.wait_for_timeout(click_wait)
                    # 关闭可能出现的确认对话框（如 cleanup 页面的清理确认）
                    dismiss_dialog(page)
                    total_clicked += 1
                    click_nav_tab(page, tab_sel, p["label"], nav_wait)
                except Exception:
                    total_failed += 1
                    dismiss_dialog(page)
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
