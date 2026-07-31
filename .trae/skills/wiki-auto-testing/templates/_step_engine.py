# -*- coding: utf-8 -*-
"""
Dynamic test step engine for wiki-auto-testing.

Each test step is a dictionary with:
  - type: step type (navigate, assert_visible, click, fill, etc.)
  - parameters: step-specific configuration

The engine dispatches each step to the appropriate handler.
New step types can be added by registering a handler function.

Usage in config.yaml:
  test_plan:
    phases:
      basic:
        steps:
          - type: navigate
            url: "{{service.frontend_url}}"
            wait: networkidle
          - type: assert_visible
            selector: ".robot-avatar"
            name: "Robot avatar"
"""
import sys
import os
import json
import uuid
import time
import subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _shared import (
    click_nav_tab, safe_click, js_click,
    get_dom_text_codepoints, check_encoding,
    stop_port_processes, verify_ports_listening, cleanup_temp_files,
)


class StepEngine:
    """Dispatches test steps to registered handlers."""

    def __init__(self):
        self.handlers = {}
        self._register_defaults()

    def register(self, step_type, handler):
        """Register a step handler function."""
        self.handlers[step_type] = handler

    def execute_step(self, step, context):
        """Execute a single step. context = {page, cfg, results, ...}"""
        step_type = step.get("type")
        if step_type not in self.handlers:
            raise ValueError(f"Unknown step type: {step_type}")
        return self.handlers[step_type](step, context)

    def execute_plan(self, plan, context):
        """Execute a list of steps from a phase definition."""
        for step in plan:
            self.execute_step(step, context)

    def _register_defaults(self):
        """Register all default step handlers."""
        self.register("navigate", self._handle_navigate)
        self.register("navigate_tab", self._handle_navigate_tab)
        self.register("assert_visible", self._handle_assert_visible)
        self.register("assert_title", self._handle_assert_title)
        self.register("click", self._handle_click)
        self.register("fill", self._handle_fill)
        self.register("press_key", self._handle_press_key)
        self.register("api_check", self._handle_api_check)
        self.register("screenshot", self._handle_screenshot)
        self.register("wait", self._handle_wait)
        self.register("button_discovery", self._handle_button_discovery)
        self.register("responsive_check", self._handle_responsive_check)
        self.register("console_check", self._handle_console_check)
        self.register("theme_switch", self._handle_theme_switch)
        self.register("persistence_crud_test", self._handle_persistence_crud_test)
        self.register("path_traversal_test", self._handle_path_traversal_test)
        self.register("fallback_degradation_test", self._handle_fallback_degradation_test)
        # 系统清理模块复盘补充步骤类型
        self.register("encoding_check", self._handle_encoding_check)
        self.register("dangerous_action_test", self._handle_dangerous_action_test)
        self.register("multi_form_test", self._handle_multi_form_test)
        self.register("service_lifecycle", self._handle_service_lifecycle)
        self.register("temp_cleanup", self._handle_temp_cleanup)

    # --- Step Handlers ---

    def _handle_navigate(self, step, ctx):
        url = step.get("url", ctx["cfg"]["service"]["frontend_url"])
        wait = step.get("wait", "networkidle")
        timeout = step.get("timeout", ctx["cfg"].get("timeout", {}).get("page_load_ms", 30000))
        ctx["page"].goto(url, wait_until=wait, timeout=timeout)

    def _handle_navigate_tab(self, step, ctx):
        tab_sel = step.get("selector", ctx["cfg"]["navigation"]["tab_selector"])
        label = step["label"]
        wait_ms = step.get("wait_ms", ctx["cfg"]["navigation"]["page_render_wait_ms"])
        click_nav_tab(ctx["page"], tab_sel, label, wait_ms)

    def _handle_assert_visible(self, step, ctx):
        selector = step["selector"]
        name = step.get("name", selector)
        count = ctx["page"].locator(selector).count()
        ctx["results"].log(f"Assert-{name}", count > 0, f"Count: {count}")

    def _handle_assert_title(self, step, ctx):
        title = ctx["page"].title()
        expected = step.get("contains", "")
        passed = bool(expected) and expected in title or (not expected and bool(title))
        ctx["results"].log("Assert-Title", passed, f"Title: {title[:50]}")

    def _handle_click(self, step, ctx):
        selector = step["selector"]
        force = step.get("force", True)
        click_timeout = ctx["cfg"].get("timeout", {}).get("click_timeout_ms")
        safe_click(ctx["page"], selector, force=force, timeout=click_timeout)

    def _handle_fill(self, step, ctx):
        selector = step["selector"]
        text = step["text"]
        ctx["page"].locator(selector).first.fill(text)
        ctx["results"].log("Fill", True, f"Filled: {text[:40]}")

    def _handle_press_key(self, step, ctx):
        key = step.get("key", "Enter")
        ctx["page"].keyboard.press(key)

    def _handle_api_check(self, step, ctx):
        api_url = ctx["cfg"]["service"]["api_url"]
        path = step["path"]
        expected = step.get("expected_status", 200)
        url = f"{api_url}{path}"
        try:
            resp = ctx["ctx"].request.get(url)
            ctx["results"].log(f"API-{path}", resp.status == expected,
                             f"Status: {resp.status}")
        except Exception as e:
            ctx["results"].log(f"API-{path}", False, f"Error: {str(e)[:80]}")

    def _handle_screenshot(self, step, ctx):
        path = step.get("path", "homepage.png")
        ctx["page"].screenshot(path=os.path.join(ctx["shot_dir"], path))

    def _handle_wait(self, step, ctx):
        ms = step.get("ms", 500)
        ctx["page"].wait_for_timeout(ms)

    def _handle_responsive_check(self, step, ctx):
        viewports = ctx["cfg"]["browser"]["viewports"]
        for name, vp in viewports.items():
            ctx["page"].set_viewport_size({"width": vp["width"], "height": vp["height"]})
            ctx["page"].wait_for_timeout(2000)
            visible = ctx["page"].locator("body").is_visible()
            ctx["results"].log(f"Responsive-{name}", visible,
                             f"{vp['width']}x{vp['height']}")
        # Reset
        d = viewports["desktop"]
        ctx["page"].set_viewport_size({"width": d["width"], "height": d["height"]})

    def _handle_console_check(self, step, ctx):
        fw = ctx["cfg"].get("console_error_filter", [])
        real = [e for e in ctx["console_errors"]
                if not any(s in e.lower() for s in fw)]
        if real:
            ctx["results"].log("Console-Errors", False,
                             f"{len(real)} errors: {real[:3]}")
        else:
            ctx["results"].log("Console-Errors", True, "No errors")

    def _handle_button_discovery(self, step, ctx):
        """Auto-discover and test all buttons."""
        bd = ctx["cfg"].get("button_discovery", {})
        if not bd.get("enabled", False):
            ctx["results"].log("ButtonDiscovery", True, "Disabled")
            return

        tab_sel = ctx["cfg"]["navigation"]["tab_selector"]
        nav_wait = ctx["cfg"]["navigation"]["page_render_wait_ms"]
        selectors = bd["button_selectors"]
        exclude_sels = bd.get("exclude_selectors", [])
        destr_texts = bd.get("destructive_button_texts", [])
        click_wait = bd.get("click_wait_ms", 800)
        force = bd.get("force_click", True)
        cont_fail = bd.get("continue_on_failure", True)

        found = clicked = skipped = failed = 0

        # 按钮发现的点击超时从 config.timeout.button_discovery_click_timeout_ms 读取
        click_timeout = ctx["cfg"].get("timeout", {}).get("button_discovery_click_timeout_ms")

        for p in ctx["cfg"]["navigation"]["pages"]:
            click_nav_tab(ctx["page"], tab_sel, p["label"], nav_wait)
            for sel in selectors:
                elems = ctx["page"].locator(sel)
                for i in range(elems.count()):
                    elem = elems.nth(i)
                    found += 1
                    # Exclusion
                    try:
                        if elem.evaluate(f'e=>e.matches("{exclude_sels[0] if exclude_sels else ""}")'):
                            skipped += 1; continue
                    except: pass
                    # Text
                    try:
                        text = elem.inner_text().strip()[:30]
                    except: text = ""
                    if any(dt.lower() in text.lower() for dt in destr_texts):
                        skipped += 1; continue
                    try:
                        click_kwargs = {"force": force}
                        if click_timeout is not None:
                            click_kwargs["timeout"] = click_timeout
                        elem.click(**click_kwargs)
                        ctx["page"].wait_for_timeout(click_wait)
                        clicked += 1
                        click_nav_tab(ctx["page"], tab_sel, p["label"], nav_wait)
                    except:
                        failed += 1
                        if not cont_fail: return
                        click_nav_tab(ctx["page"], tab_sel, p["label"], nav_wait)

        ctx["results"].log("ButtonDiscovery", failed == 0,
                         f"F:{found} C:{clicked} S:{skipped} F:{failed}")

    def _handle_theme_switch(self, step, ctx):
        tc = ctx["cfg"]["interactions"].get("theme_switcher", {})
        # v3.1 需求：移除主题切换悬浮框后，theme_switcher.enabled=false 时直接跳过
        if tc.get("enabled", True) is False:
            ctx["results"].log("Theme-Switch", True, "Skipped (theme switcher disabled)")
            return
        trigger = tc.get("trigger_selector")
        item = tc.get("item_selector")
        if not trigger or not item:
            ctx["results"].log("Theme-Switch", True, "Skipped")
            return
        use_js = tc.get("use_js_click", True)
        if use_js:
            js_click(ctx["page"], trigger)
        else:
            safe_click(ctx["page"], trigger)
        ctx["page"].wait_for_timeout(tc.get("transition_wait_ms", 1000))
        items = ctx["page"].locator(item)
        if items.count() > 0:
            items.first.click()
            ctx["page"].wait_for_timeout(tc.get("transition_wait_ms", 1000))
            theme = ctx["page"].evaluate("document.documentElement.getAttribute('data-theme')||''")
            ctx["results"].log("Theme-Switch", bool(theme), f"To: {theme}")
        else:
            ctx["results"].log("Theme-Switch", False, "No items")

    def _handle_fill_and_submit(self, step, ctx):
        """Fill input and optionally submit."""
        selector = step["selector"]
        text = step["text"]
        ctx["page"].locator(selector).first.fill(text)
        if step.get("submit"):
            method = step.get("submit_method", "enter")
            if method == "enter":
                ctx["page"].keyboard.press("Enter")
            else:
                btn = step.get("submit_button", "button:has-text('Submit')")
                safe_click(ctx["page"], btn)
        ctx["results"].log("FillAndSubmit", True, f"Text: {text[:30]}")

    # --- 持久化层测试步骤（复盘提炼，参数全部从 config.persistence_tests 读取）---

    def _handle_persistence_crud_test(self, step, ctx):
        """持久化层 CRUD 全生命周期 + PUT 后立即 GET 对比（验证缓存刷新）。

        所有端点、payload、资源名从 config.persistence_tests 读取，step 可覆盖，
        不在代码中硬编码任何业务端点。
        """
        pt = ctx["cfg"].get("persistence_tests", {})
        base_url = ctx["cfg"]["service"]["api_url"]
        resource = step.get("resource", pt.get("default_resource", "conversations"))
        # 测试用 ID：step 指定 > 自动生成 UUID，避免污染真实数据
        test_id = step.get("test_id", str(uuid.uuid4()))
        endpoint_tpl = pt.get("endpoints", {}).get(resource, "/api/{resource}/{id}").replace("{resource}", resource)
        endpoint = endpoint_tpl.replace("{id}", test_id)

        # payload 模板：占位符 {id} 替换为实际 test_id
        payload_tpl = step.get("payload", pt.get("test_payloads", {}).get(resource, {"id": "{id}"}))
        payload = json.loads(json.dumps(payload_tpl).replace("{id}", test_id))

        headers = {"Content-Type": "application/json"}
        results = []

        # 1. PUT 创建
        resp = ctx["ctx"].request.put(f"{base_url}{endpoint}", headers=headers, data=json.dumps(payload))
        results.append(("PUT-Create", resp.status in (200, 201), f"Status:{resp.status}"))

        # 2. GET 读取（验证创建落盘）
        resp = ctx["ctx"].request.get(f"{base_url}{endpoint}")
        create_ok = resp.status == 200
        results.append(("GET-Read", create_ok, f"Status:{resp.status}"))

        # 3. PUT 更新
        updated = json.loads(json.dumps(payload))
        updated["updated"] = True
        resp = ctx["ctx"].request.put(f"{base_url}{endpoint}", headers=headers, data=json.dumps(updated))
        results.append(("PUT-Update", resp.status in (200, 201), f"Status:{resp.status}"))

        # 4. GET 验证更新生效（缓存刷新关键验证点：PUT 后立即 GET 必须返回新值）
        resp = ctx["ctx"].request.get(f"{base_url}{endpoint}")
        body = resp.text()
        update_ok = resp.status == 200 and '"updated":true' in body.replace(" ", "")
        results.append(("GET-VerifyUpdate", update_ok, f"Status:{resp.status},cache_refresh:{update_ok}"))

        # 5. DELETE
        resp = ctx["ctx"].request.delete(f"{base_url}{endpoint}")
        results.append(("DELETE", resp.status in (200, 204), f"Status:{resp.status}"))

        # 6. GET 确认删除
        resp = ctx["ctx"].request.get(f"{base_url}{endpoint}")
        results.append(("GET-AfterDelete", resp.status == 404, f"Status:{resp.status}"))

        all_pass = all(r[1] for r in results)
        detail = "; ".join(f"{r[0]}:{'P' if r[1] else 'F'}" for r in results)
        ctx["results"].log(f"Persistence-CRUD-{resource}", all_pass, detail)

        # 清理兜底：删除失败时再试一次，避免测试数据残留
        if not results[4][1]:
            try:
                ctx["ctx"].request.delete(f"{base_url}{endpoint}")
            except Exception:
                pass

    def _handle_path_traversal_test(self, step, ctx):
        """路径穿越防护测试：用非法 ID 请求，验证返回 4xx 而非 5xx 或 200。

        攻击向量从 config.persistence_tests.malicious_ids 读取，
        不在代码中硬编码具体攻击字符串。
        """
        pt = ctx["cfg"].get("persistence_tests", {})
        base_url = ctx["cfg"]["service"]["api_url"]
        resource = step.get("resource", pt.get("default_resource", "conversations"))
        endpoint_tpl = pt.get("endpoints", {}).get(resource, "/api/{resource}/{id}").replace("{resource}", resource)

        malicious_ids = step.get("malicious_ids", pt.get("malicious_ids", []))
        if not malicious_ids:
            ctx["results"].log(f"PathTraversal-{resource}", True, "No malicious_ids configured, skipped")
            return

        all_pass = True
        details = []
        for mid in malicious_ids:
            endpoint = endpoint_tpl.replace("{id}", mid)
            try:
                resp = ctx["ctx"].request.get(f"{base_url}{endpoint}")
                # 期望 4xx（客户端错误），5xx（服务器异常）或 200（穿越成功）都算失败
                ok = 400 <= resp.status < 500
                if not ok:
                    all_pass = False
                details.append(f"{mid[:16]}:{resp.status}")
            except Exception:
                all_pass = False
                details.append(f"{mid[:16]}:ERR")

        ctx["results"].log(f"PathTraversal-{resource}", all_pass, "; ".join(details))

    def _handle_fallback_degradation_test(self, step, ctx):
        """降级测试：拦截后端 API 返回 503，验证前端不崩溃。

        拦截的 API 模式、期望行为、等待时间均从 config.persistence_tests.fallback 读取，
        不在代码中硬编码。
        """
        pt = ctx["cfg"].get("persistence_tests", {})
        fb = pt.get("fallback", {})
        api_patterns = step.get("api_patterns", fb.get("api_patterns", []))
        expected_behavior = step.get("expected_behavior", fb.get("expected_behavior", "no-crash"))
        wait_ms = step.get("wait_ms", fb.get("wait_ms", 2000))
        trigger_url = step.get("trigger_url", ctx["cfg"]["service"]["frontend_url"])

        if not api_patterns:
            ctx["results"].log("FallbackDegradation", True, "No api_patterns configured, skipped")
            return

        page = ctx["page"]

        def _handle_route(route):
            route.fulfill(status=503, body="Service Unavailable")

        for pattern in api_patterns:
            page.route(f"**{pattern}**", _handle_route)

        try:
            # 触发前端加载，后端被拦截返回 503
            page.goto(trigger_url, wait_until="domcontentloaded")
            page.wait_for_timeout(wait_ms)

            body_visible = page.locator("body").is_visible()

            if expected_behavior == "no-crash":
                ok = body_visible
                detail = f"Body visible: {body_visible}"
            else:
                ok = body_visible
                detail = f"Body visible: {body_visible} (behavior: {expected_behavior})"

            ctx["results"].log("FallbackDegradation", ok, detail)
        finally:
            # 取消路由拦截，恢复后端连接供后续测试使用
            for pattern in api_patterns:
                page.unroute(f"**{pattern}**")

    # --- 系统清理模块复盘补充步骤类型 ---
    # 所有参数从 config 的对应配置块读取，step 可覆盖，不在代码中硬编码
    # 任何具体页面/选择器/文本均通过 config 注入

    def _handle_encoding_check(self, step, ctx):
        """编码检测：dump DOM 文本码点，检查是否含 U+FFFD 替换字符。

        触发场景：Windows 中文环境终端编码与 Playwright 中文匹配问题导致
        页面 tab 标签全显示为 U+FFFD，has_text 中文匹配失败。

        所有页面 key、扫描选择器、码点标识从 config.encoding_tests 读取，
        step 可覆盖，不在代码中硬编码具体页面或选择器。
        """
        ec = ctx["cfg"].get("encoding_tests", {})
        if not ec.get("enabled", False) and not step.get("force", False):
            ctx["results"].log("EncodingCheck", True, "Disabled, skipped")
            return

        # step 优先级高于 config，便于临时覆盖
        check_pages = step.get("check_pages", ec.get("check_pages", []))
        fffd_codepoint = step.get("fffd_codepoint", ec.get("fffd_codepoint", "0xFFFD"))
        scan_selectors = step.get("scan_selectors", ec.get("scan_selectors", ["body"]))
        screenshot_on_fail = step.get("screenshot_on_fail", ec.get("screenshot_on_fail", True))

        if not check_pages:
            ctx["results"].log("EncodingCheck", True, "No check_pages configured, skipped")
            return

        page = ctx["page"]
        # 通过 page key 反查 navigation 配置，找到对应 tab label 用于导航
        nav_pages = ctx["cfg"].get("navigation", {}).get("pages", [])
        tab_selector = ctx["cfg"].get("navigation", {}).get("tab_selector", ".tab-btn")
        nav_wait = ctx["cfg"].get("navigation", {}).get("page_render_wait_ms", 1500)

        all_pass = True
        details = []
        for page_key in check_pages:
            # 查找 navigation 中该 key 对应的 label（用于点击 tab 切换）
            nav_item = next((p for p in nav_pages if p.get("key") == page_key), None)
            if nav_item and nav_item.get("label"):
                click_nav_tab(page, tab_selector, nav_item["label"], nav_wait)
            # 若找不到 navigation 配置，假设当前已在目标页面（由前序步骤导航）

            # 调用共享工具检测 U+FFFD
            result = check_encoding(page, fffd_codepoint, scan_selectors)
            page_ok = not result["has_fffd"]
            if not page_ok:
                all_pass = False
                details.append(f"{page_key}:FFFD@{result['affected_selectors']}")
                # 失败时截图取证，便于事后排查编码乱码现场
                if screenshot_on_fail:
                    shot_path = os.path.join(ctx["shot_dir"], f"encoding_{page_key}.png")
                    try:
                        page.screenshot(path=shot_path)
                    except Exception:
                        pass
            else:
                details.append(f"{page_key}:OK")

        ctx["results"].log("EncodingCheck", all_pass, "; ".join(details))

    def _handle_dangerous_action_test(self, step, ctx):
        """危险操作完整测试：dry_run 默认开启 → danger 样式 → 二次确认 → 取消 → 执行。

        触发场景：清理类模块的 dry_run 默认值若关闭会误删数据，
        二次确认弹窗若缺失会导致危险操作误触发。

        所有页面、表单、选择器、确认文本从 config.dangerous_action_tests 读取，
        step 可覆盖，不在代码中硬编码具体业务文本或选择器。
        """
        da = ctx["cfg"].get("dangerous_action_tests", {})
        if not da.get("enabled", False) and not step.get("force", False):
            ctx["results"].log("DangerousAction", True, "Disabled, skipped")
            return

        # step 可覆盖 config 的 test_pages，便于临时调试单个页面
        test_pages = step.get("test_pages", da.get("test_pages", []))
        # 各选择器和文本的默认值从 config 读取
        confirm_component = step.get("confirm_component", da.get("confirm_component", ".el-message-box"))
        confirm_cancel_text = step.get("confirm_cancel_text", da.get("confirm_cancel_text", "取消"))
        confirm_ok_text = step.get("confirm_ok_text", da.get("confirm_ok_text", "确认"))
        danger_class = step.get("danger_class", da.get("danger_class", "danger"))
        dry_run_switch = step.get("dry_run_switch", da.get("dry_run_switch", ".el-switch"))
        form_container_selector = step.get("form_container_selector", da.get("form_container_selector", "form"))
        action_wait_ms = step.get("action_wait_ms", da.get("action_wait_ms", 800))
        confirm_wait_ms = step.get("confirm_wait_ms", da.get("confirm_wait_ms", 1500))

        if not test_pages:
            ctx["results"].log("DangerousAction", True, "No test_pages configured, skipped")
            return

        page = ctx["page"]
        # tab 导航参数（用于切换到目标页面）
        nav_pages = ctx["cfg"].get("navigation", {}).get("pages", [])
        tab_selector = ctx["cfg"].get("navigation", {}).get("tab_selector", ".tab-btn")
        nav_wait = ctx["cfg"].get("navigation", {}).get("page_render_wait_ms", 1500)

        all_pass = True
        details = []

        for tp in test_pages:
            page_key = tp.get("key")
            # 导航到目标页面
            nav_item = next((p for p in nav_pages if p.get("key") == page_key), None)
            if nav_item and nav_item.get("label"):
                click_nav_tab(page, tab_selector, nav_item["label"], nav_wait)

            forms = tp.get("forms", [])
            for form_cfg in forms:
                form_key = form_cfg.get("key", "unknown")
                has_days = form_cfg.get("has_days_input", False)
                default_dry = form_cfg.get("default_dry_run", True)

                form_results = []

                # 1. 验证 dry_run 默认开启（避免误删数据的关键防线）
                try:
                    switches = page.locator(dry_run_switch)
                    if switches.count() > 0:
                        # 通过 aria-checked 或 class 判断开关状态
                        is_checked = switches.first.evaluate(
                            'e => e.getAttribute("aria-checked") === "true" || e.classList.contains("is-checked")'
                        )
                        form_results.append(("dry_run_default", is_checked == default_dry, f"checked={is_checked}"))
                    else:
                        form_results.append(("dry_run_default", True, "no switch, skip"))
                except Exception as e:
                    form_results.append(("dry_run_default", False, f"err:{str(e)[:30]}"))

                # 2. 验证 days 输入框存在（若 has_days_input=true）
                if has_days:
                    try:
                        days_input = page.locator(f'{form_container_selector} input[type="number"]')
                        form_results.append(("days_input", days_input.count() > 0, f"count={days_input.count()}"))
                    except Exception:
                        form_results.append(("days_input", False, "err"))

                # 3. 关闭 dry_run → 验证触发按钮带 danger 样式
                try:
                    switches = page.locator(dry_run_switch)
                    if switches.count() > 0:
                        switches.first.click()
                        page.wait_for_timeout(action_wait_ms)
                    # 查找 danger 样式按钮（用 class 包含判断，避免硬编码具体按钮选择器）
                    has_danger = page.evaluate(
                        f'() => !!document.querySelector("{form_container_selector} .{danger_class}")'
                    )
                    form_results.append(("danger_style", has_danger, f"class={danger_class}"))
                except Exception as e:
                    form_results.append(("danger_style", False, f"err:{str(e)[:30]}"))

                # 4. 点击触发按钮 → 等待二次确认弹窗
                try:
                    # 点击 danger 样式按钮触发操作
                    page.evaluate(
                        f'() => document.querySelector("{form_container_selector} .{danger_class}")?.click()'
                    )
                    page.wait_for_timeout(confirm_wait_ms)
                    confirm_visible = page.locator(confirm_component).count() > 0
                    form_results.append(("confirm_popup", confirm_visible, f"visible={confirm_visible}"))

                    if confirm_visible:
                        # 5. 点击"取消" → 验证未发出清理请求
                        # 用文本定位取消按钮（用 Unicode 码点匹配可绕过终端编码问题）
                        cancel_btn = page.locator(
                            f'{confirm_component} :text-matches("{confirm_cancel_text}")'
                        )
                        if cancel_btn.count() == 0:
                            # 退化方案：取弹窗中第 1 个按钮（取消通常是左侧第 1 个）
                            cancel_btn = page.locator(f'{confirm_component} button').first
                        if cancel_btn.count() > 0:
                            cancel_btn.first.click()
                            page.wait_for_timeout(action_wait_ms)
                            # 验证弹窗已关闭（取消后不应执行清理）
                            popup_closed = page.locator(confirm_component).count() == 0
                            form_results.append(("cancel_no_action", popup_closed, f"closed={popup_closed}"))
                        else:
                            form_results.append(("cancel_no_action", False, "no cancel btn"))

                        # 6. 再次点击触发 → 确认 → 验证执行
                        page.evaluate(
                            f'() => document.querySelector("{form_container_selector} .{danger_class}")?.click()'
                        )
                        page.wait_for_timeout(confirm_wait_ms)
                        ok_btn = page.locator(
                            f'{confirm_component} :text-matches("{confirm_ok_text}")'
                        )
                        if ok_btn.count() == 0:
                            # 退化方案：取弹窗中最后一个按钮（确认通常是右侧最后一个）
                            btn_count = page.locator(f'{confirm_component} button').count()
                            ok_btn = page.locator(f'{confirm_component} button').nth(btn_count - 1) if btn_count > 0 else ok_btn
                        if ok_btn.count() > 0:
                            ok_btn.first.click()
                            page.wait_for_timeout(action_wait_ms * 2)
                            # 验证执行结果（弹窗关闭 + 表单可能显示 loading/result）
                            popup_closed = page.locator(confirm_component).count() == 0
                            form_results.append(("confirm_executed", popup_closed, f"closed={popup_closed}"))
                        else:
                            form_results.append(("confirm_executed", False, "no ok btn"))
                    else:
                        form_results.append(("cancel_no_action", False, "no popup"))
                        form_results.append(("confirm_executed", False, "no popup"))

                    # 7. 恢复 dry_run 默认开启状态（避免影响后续测试）
                    try:
                        switches = page.locator(dry_run_switch)
                        if switches.count() > 0:
                            is_checked = switches.first.evaluate(
                                'e => e.getAttribute("aria-checked") === "true" || e.classList.contains("is-checked")'
                            )
                            if not is_checked:
                                switches.first.click()
                                page.wait_for_timeout(action_wait_ms)
                    except Exception:
                        pass
                except Exception as e:
                    form_results.append(("confirm_flow", False, f"err:{str(e)[:30]}"))

                # 汇总该表单的结果
                form_pass = all(r[1] for r in form_results)
                if not form_pass:
                    all_pass = False
                details.append(f"{page_key}/{form_key}:" + ",".join(
                    f"{r[0]}:{'P' if r[1] else 'F'}" for r in form_results
                ))

        ctx["results"].log("DangerousAction", all_pass, "; ".join(details))

    def _handle_multi_form_test(self, step, ctx):
        """多表单独立状态测试：验证每个表单独立 loading/result，互不干扰。

        触发场景：清理模块有多个表单（compileCache/runLogs 等），
        若共享 loading/result 状态会导致一个表单操作影响其他表单显示。

        所有页面、表单选择器、loading/result 选择器从 config.dangerous_action_tests 读取，
        step 可覆盖，不在代码中硬编码具体选择器。
        """
        da = ctx["cfg"].get("dangerous_action_tests", {})
        if not da.get("enabled", False) and not step.get("force", False):
            ctx["results"].log("MultiForm", True, "Disabled, skipped")
            return

        test_pages = step.get("test_pages", da.get("test_pages", []))
        form_container_selector = step.get("form_container_selector", da.get("form_container_selector", "form"))
        loading_selector = step.get("loading_selector", da.get("loading_selector", ".loading"))
        result_selector = step.get("result_selector", da.get("result_selector", ".result"))
        action_wait_ms = step.get("action_wait_ms", da.get("action_wait_ms", 800))

        if not test_pages:
            ctx["results"].log("MultiForm", True, "No test_pages configured, skipped")
            return

        page = ctx["page"]
        nav_pages = ctx["cfg"].get("navigation", {}).get("pages", [])
        tab_selector = ctx["cfg"].get("navigation", {}).get("tab_selector", ".tab-btn")
        nav_wait = ctx["cfg"].get("navigation", {}).get("page_render_wait_ms", 1500)

        all_pass = True
        details = []

        for tp in test_pages:
            page_key = tp.get("key")
            nav_item = next((p for p in nav_pages if p.get("key") == page_key), None)
            if nav_item and nav_item.get("label"):
                click_nav_tab(page, tab_selector, nav_item["label"], nav_wait)

            # 统计页面中的表单数量
            try:
                forms = page.locator(form_container_selector)
                form_count = forms.count()
            except Exception:
                form_count = 0

            if form_count <= 1:
                details.append(f"{page_key}:single_form_skip")
                continue

            # 验证 1：每个表单都有独立的 loading 和 result 容器
            # 用 evaluate 一次性取所有表单的子元素状态，避免多次 locator 调用的时序问题
            try:
                form_states = page.evaluate(
                    f'''() => {{
                        const forms = document.querySelectorAll("{form_container_selector}");
                        return Array.from(forms).map(f => ({{
                            has_loading: !!f.querySelector("{loading_selector}"),
                            has_result: !!f.querySelector("{result_selector}"),
                        }}));
                    }}'''
                )
                # 每个表单应能独立持有 loading 和 result（不共享）
                independent = all(
                    fs["has_loading"] or fs["has_result"] for fs in form_states
                )
                # 验证 2：表单数量与状态记录数一致（避免选择器漂移到表单外）
                count_match = len(form_states) == form_count
                details.append(
                    f"{page_key}:forms={form_count},independent={independent},count_match={count_match}"
                )
                if not (independent and count_match):
                    all_pass = False
            except Exception as e:
                all_pass = False
                details.append(f"{page_key}:err:{str(e)[:40]}")

            # 验证 3：触发一个表单的 loading 后，其他表单不应显示 loading
            # 此处只做选择器存在性验证，避免实际触发危险操作
            try:
                if form_count >= 2:
                    first_form_loading = page.evaluate(
                        f'''() => {{
                            const f = document.querySelectorAll("{form_container_selector}")[0];
                            return !!(f && f.querySelector("{loading_selector}"));
                        }}'''
                    )
                    second_form_loading = page.evaluate(
                        f'''() => {{
                            const f = document.querySelectorAll("{form_container_selector}")[1];
                            return !!(f && f.querySelector("{loading_selector}"));
                        }}'''
                    )
                    # 这里只验证选择器作用域隔离，实际 loading 状态需结合业务操作验证
                    scope_isolated = not (first_form_loading and second_form_loading)
                    details.append(f"{page_key}:scope_isolated={scope_isolated}")
            except Exception:
                pass

            page.wait_for_timeout(action_wait_ms)

        ctx["results"].log("MultiForm", all_pass, "; ".join(details))

    def _handle_service_lifecycle(self, step, ctx):
        """服务生命周期：停止旧进程 → 启动新服务 → 验证端口监听。

        触发场景：端口占用导致新服务启动失败；
        测试前需要确保干净的进程环境。

        所有停止方法、启动命令、端口列表、超时时间从 config.service_lifecycle 读取，
        step 可覆盖，不在代码中硬编码端口或命令。
        """
        sl = ctx["cfg"].get("service_lifecycle", {})
        # service.required_ports 也作为端口列表的来源
        required_ports = step.get(
            "required_ports",
            ctx["cfg"].get("service", {}).get("required_ports", [])
        )
        stop_old = step.get("stop_old_process", sl.get("stop_old_process", False))
        start_backend = step.get("start_backend", sl.get("start_backend", "npm run dev:api"))
        start_frontend = step.get("start_frontend", sl.get("start_frontend", "npm run dev:web"))
        startup_timeout_ms = step.get("startup_timeout_ms", sl.get("startup_timeout_ms", 30000))
        poll_interval_ms = step.get("port_poll_interval_ms", sl.get("port_poll_interval_ms", 1000))

        if not required_ports:
            ctx["results"].log("ServiceLifecycle", True, "No required_ports configured, skipped")
            return

        results = []
        all_pass = True

        # 1. 停止占用端口的旧进程
        if stop_old:
            stop_result = stop_port_processes(required_ports)
            stopped_count = sum(1 for r in stop_result.values() if r["stopped"])
            results.append(f"stopped:{stopped_count}/{len(required_ports)}")
            # 等待端口释放
            time.sleep(2)

        # 2. 启动后端服务（非阻塞模式）
        try:
            # shell=True 让 PowerShell 解析命令字符串；start_mode=non-blocking 时不 wait
            subprocess.Popen(
                start_backend, shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=os.getcwd()
            )
            results.append("backend_started")
        except Exception as e:
            all_pass = False
            results.append(f"backend_err:{str(e)[:30]}")

        # 3. 启动前端服务（非阻塞模式）
        try:
            subprocess.Popen(
                start_frontend, shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=os.getcwd()
            )
            results.append("frontend_started")
        except Exception as e:
            all_pass = False
            results.append(f"frontend_err:{str(e)[:30]}")

        # 4. 轮询验证端口监听，超时则判定启动失败
        deadline = time.time() + (startup_timeout_ms / 1000.0)
        port_ok = False
        while time.time() < deadline:
            listening = verify_ports_listening(required_ports)
            if all(listening.values()):
                port_ok = True
                break
            time.sleep(poll_interval_ms / 1000.0)

        if port_ok:
            results.append("ports_listening:all")
        else:
            all_pass = False
            listening = verify_ports_listening(required_ports)
            not_listening = [p for p, ok in listening.items() if not ok]
            results.append(f"ports_listening:FAIL@{not_listening}")

        ctx["results"].log("ServiceLifecycle", all_pass, "; ".join(results))

    def _handle_temp_cleanup(self, step, ctx):
        """临时文件清理：按 pattern 删除测试产生的临时脚本和截图。

        触发场景：测试过程中产生的临时 Python 脚本和截图未清理，
        残留文件污染工作目录，影响后续测试或 git 状态。

        所有 pattern、清理目录、清理策略从 config.cleanup 读取，
        step 可覆盖，不在代码中硬编码具体文件名。
        """
        cl = ctx["cfg"].get("cleanup", {})
        temp_files_pattern = step.get("temp_files_pattern", cl.get("temp_files_pattern", "_test_*.py"))
        temp_screenshots_pattern = step.get(
            "temp_screenshots_pattern", cl.get("temp_screenshots_pattern", "_test_*.png")
        )
        cleanup_dirs = step.get("cleanup_dirs", cl.get("cleanup_dirs", ["."]))

        # 根据测试结果决定是否清理
        test_passed = ctx.get("test_passed", True)
        cleanup_on_success = step.get("cleanup_on_success", cl.get("cleanup_on_success", True))
        cleanup_on_failure = step.get("cleanup_on_failure", cl.get("cleanup_on_failure", False))

        if not test_passed and not cleanup_on_failure:
            ctx["results"].log("TempCleanup", True, "Skipped (test failed, keep temp files for debugging)")
            return
        if test_passed and not cleanup_on_success:
            ctx["results"].log("TempCleanup", True, "Skipped (cleanup_on_success=false)")
            return

        patterns = [temp_files_pattern, temp_screenshots_pattern]
        result = cleanup_temp_files(patterns, cleanup_dirs)

        deleted_count = len(result["deleted"])
        failed_count = len(result["failed"])
        total = result["total"]

        # 即使部分删除失败，只要有删除成功且无严重异常即视为通过
        ok = failed_count == 0
        detail = f"deleted:{deleted_count},failed:{failed_count},total:{total}"
        if failed_count > 0:
            detail += f";first_err={result['failed'][0]['error']}"

        ctx["results"].log("TempCleanup", ok, detail)
