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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _shared import click_nav_tab, safe_click, js_click


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
        safe_click(ctx["page"], selector, force=force)

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
                        elem.click(force=force, timeout=3000)
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
