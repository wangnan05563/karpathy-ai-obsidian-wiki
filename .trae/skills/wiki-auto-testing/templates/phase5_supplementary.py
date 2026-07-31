# -*- coding: utf-8 -*-
"""Phase 5: Supplementary tests - responsive, API endpoints, console errors."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from _shared import click_nav_tab


def test_responsive(page, cfg, results):
    """Test responsive layout across viewports."""
    viewports = cfg["browser"]["viewports"]
    for name, vp in viewports.items():
        page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
        page.wait_for_timeout(2000)
        results.log(f"Responsive-{name}",
                    page.locator("body").is_visible(),
                    f"{vp['width']}x{vp['height']}")
    d = viewports["desktop"]
    page.set_viewport_size({"width": d["width"], "height": d["height"]})


def test_api_endpoints(ctx, cfg, results):
    """Test API endpoints using Playwright request API."""
    api_url = cfg["service"]["api_url"]
    # 默认超时：从 defaults.yaml 的 api_tests.default_timeout_ms 读取，未配置时回退 30s
    default_timeout = cfg.get("api_tests", {}).get("default_timeout_ms", 30000)
    # 429 视为良性限流（全局 60/min 兜底，测试密集调用可能触发），与 console_error_filter 对齐
    benign_statuses = cfg.get("api_tests", {}).get("benign_statuses", [429])
    for ep in cfg["api_tests"]["endpoints"]:
        path = ep["path"]
        expected = ep["expected_status"]
        url = f"{api_url}{path}"
        # per-endpoint 超时覆盖：重 IO 端点（如 /api/stats）可在 config.yaml 单独配置
        timeout = ep.get("timeout_ms", default_timeout)
        try:
            resp = ctx.request.get(url, timeout=timeout)
            if resp.status in benign_statuses:
                # 限流是间歇性良性错误，标记 SKIP 避免误报 FAIL
                results.skip(f"API-{path}", f"Benign status {resp.status} (rate-limited)")
            else:
                results.log(f"API-{path}", resp.status == expected,
                            f"Status: {resp.status} (expected {expected}, timeout: {timeout}ms)")
        except Exception as e:
            results.log(f"API-{path}", False, f"Error (timeout={timeout}ms): {str(e)[:80]}")


def test_console_errors(console_errors, cfg, results):
    """Check for unfiltered console errors."""
    fw = cfg.get("console_error_filter", [])
    real_errors = [e for e in console_errors
                   if not any(s in e.lower() for s in fw)]
    if real_errors:
        results.log("Console-Errors", False,
                    f"{len(real_errors)} errors: {real_errors[:3]}")
    else:
        results.log("Console-Errors", True, "No errors after filtering")


def test_fr11_browse_views(page, ctx, cfg, results):
    """
    Phase 5 (FR-11): Browse.vue 三视图切换 + 看板分列 + 日历分组 + 状态持久化测试。
    复盘来源：FR-11 新增看板/日历视图，需验证视图切换、数据加载、localStorage 持久化。
    """
    fr11 = cfg.get("fr11_browse_views_tests", {})
    if not fr11.get("enabled", False):
        results.log("FR11-Skipped", True, "Disabled in config")
        return

    tab_sel = cfg["navigation"]["tab_selector"]
    wait_ms = cfg["navigation"]["page_render_wait_ms"]
    view_wait = fr11.get("view_render_wait_ms", 1500)
    switcher_sel = fr11["view_switcher_selector"]
    state_key = fr11["state_persistence_key"]
    api_path = fr11["pages_api_path"]
    api_url = cfg["service"]["api_url"]

    # ---- 步骤 1：API 数据源验证（/api/files/pages 返回 200 + pages 数组） ----
    benign_statuses = cfg.get("api_tests", {}).get("benign_statuses", [429])
    try:
        resp = ctx.request.get(f"{api_url}{api_path}", timeout=30000)
        if resp.status in benign_statuses:
            results.skip("FR11-API-Pages", f"Benign status {resp.status} (rate-limited)")
            pages_count = 0
        else:
            api_ok = resp.status == 200
            pages_count = 0
            if api_ok:
                data = resp.json()
                pages_count = len(data.get("pages", []))
            results.log("FR11-API-Pages", api_ok, f"Status: {resp.status}, pages: {pages_count}")
    except Exception as e:
        results.log("FR11-API-Pages", False, f"Error: {str(e)[:80]}")

    # ---- 步骤 2：导航到 Browse 页面 ----
    browse_label = None
    for p in cfg["navigation"]["pages"]:
        if p["key"] == fr11["test_page_key"]:
            browse_label = p["label"]
            break
    if not browse_label:
        results.log("FR11-Nav", False, "Browse page not found in navigation config")
        return
    nav_result = click_nav_tab(page, tab_sel, browse_label, wait_ms)
    if nav_result is None:
        results.skip("FR11-Nav", "Browse tab disabled by design")
        return
    results.log("FR11-Nav", nav_result, f"Tab: {browse_label}")

    # ---- 步骤 3：视图切换器存在性验证 ----
    switcher_count = page.locator(switcher_sel).count()
    results.log("FR11-Switcher-Exists", switcher_count > 0,
                f"Selector: {switcher_sel}, count: {switcher_count}")

    # ---- 步骤 4：逐个视图切换验证 ----
    # 为什么先 tree：默认视图，确保初始状态可恢复
    # 为什么再 kanban/calendar：覆盖新增视图的渲染与数据加载
    view_results = fr11["views"]
    for view_key in ["tree", "kanban", "calendar"]:
        v_cfg = view_results[view_key]
        expected_sel = v_cfg["expected_selector"]
        label_text = v_cfg["label"]

        # Element Plus radio-button 用 label 内文本点击
        radio_label = page.locator(f'.el-radio-button:has-text("{label_text}")')
        if radio_label.count() == 0:
            results.log(f"FR11-View-{view_key}", False, f"Radio label not found: {label_text}")
            continue
        try:
            radio_label.first.click()
            # 为什么用 wait_for_selector 替代固定 wait：loadAllPages 是异步 fetch，
            # 1500ms 固定等待在某些机器上不够；显式等待特征元素出现更可靠
            page.wait_for_selector(expected_sel, state="visible", timeout=5000)
        except Exception as e:
            results.log(f"FR11-View-{view_key}", False, f"Click/wait failed: {str(e)[:60]}")
            continue

        # 验证视图特征元素出现
        expected_count = page.locator(expected_sel).count()
        # 为什么允许 0：vault 可能为空，看板/日历会显示空态；只要特征元素选择器命中即可
        ok = expected_count > 0
        results.log(
            f"FR11-View-{view_key}",
            ok,
            f"Label: {label_text}, expected: {expected_sel}, count: {expected_count}",
        )

        # 看板视图额外验证：所有列容器存在（即使列为空也要渲染列骨架）
        # 为什么仅在 .kanban-scroll 存在时验证列数：空态渲染 .tree-empty 而非 .kanban-col
        if view_key == "kanban" and ok:
            kanban_scroll_count = page.locator(".kanban-scroll").count()
            if kanban_scroll_count > 0:
                col_count = page.locator(".kanban-col").count()
                expected_cols = len(fr11.get("kanban_columns", []))
                results.log(
                    "FR11-Kanban-Columns",
                    col_count >= expected_cols,
                    f"Columns rendered: {col_count}, expected >= {expected_cols}",
                )
            else:
                # 空态时跳过列数验证（allPages 为空，看板显示 .tree-empty 提示）
                results.log(
                    "FR11-Kanban-Columns",
                    True,
                    "Skipped (empty state, .tree-empty shown)",
                )

        # 日历视图额外验证：日期分组按降序排列
        if view_key == "calendar" and ok:
            date_texts = page.locator(".calendar-date .date-text").all_inner_texts()
            if len(date_texts) >= 2:
                is_desc = all(date_texts[i] >= date_texts[i + 1] for i in range(len(date_texts) - 1))
                results.log(
                    "FR11-Calendar-Sort",
                    is_desc,
                    f"Dates: {date_texts[:3]}...",
                )
            else:
                # 不足 2 个日期时无法验证排序，跳过（vault 数据少不视为失败）
                results.log(
                    "FR11-Calendar-Sort",
                    True,
                    f"Only {len(date_texts)} date groups, sort check skipped",
                )

    # ---- 步骤 5：视图状态持久化验证（刷新后保持） ----
    # 验证 localStorage 中的视图状态在页面刷新后仍保持为 kanban
    # 为什么仅验证 localStorage：DOM 渲染依赖 API 数据加载（步骤 4 已验证切换功能），
    # 持久化的核心是 localStorage 跨刷新保持，这是 AC-11-7 的验收点
    try:
        kanban_label = view_results["kanban"]["label"]
        page.locator(f'.el-radio-button:has-text("{kanban_label}")').first.click()
        page.wait_for_timeout(view_wait)
        stored_before = page.evaluate(f"localStorage.getItem('{state_key}')")
        if stored_before != "kanban":
            results.log(
                "FR11-Persistence",
                False,
                f"localStorage before reload: {stored_before}, expected: kanban",
            )
            return
        # 刷新页面，验证 localStorage 持久化
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(wait_ms)
        stored_after = page.evaluate(f"localStorage.getItem('{state_key}')")
        results.log(
            "FR11-Persistence",
            stored_after == "kanban",
            f"Before: {stored_before}, After: {stored_after}",
        )
    except Exception as e:
        results.log("FR11-Persistence", False, f"Error: {str(e)[:80]}")


def run_phase(cfg, results, page, ctx, console_errors, quiet=False):
    """Execute Phase 5 tests."""
    if not quiet:
        print("\n=== Phase 5: Supplementary Tests ===")
    test_responsive(page, cfg, results)
    test_api_endpoints(ctx, cfg, results)
    # FR-11 看板/日历视图专项测试（新增视图需独立验证切换/渲染/持久化）
    if not quiet:
        print("\n=== Phase 5 (FR-11): Browse Views Tests ===")
    test_fr11_browse_views(page, ctx, cfg, results)
    test_console_errors(console_errors, cfg, results)
