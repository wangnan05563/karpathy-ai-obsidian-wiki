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
        # 第四轮复盘补充步骤类型：后端逻辑单元验证 + 迁移/修复脚本端到端
        self.register("backend_logic_unit_test", self._handle_backend_logic_unit_test)
        self.register("migration_script_e2e", self._handle_migration_script_e2e)
        # 第十一轮复盘补充步骤类型：后端行为级缺陷静态守卫（配置化 forbid 扫描）
        self.register("backend_review_static_check", self._handle_backend_review_static_check)
        # 第十二轮复盘补充步骤类型：路由响应分支覆盖（配置化逐分支断言返回状态码）
        self.register("route_response_branch_coverage", self._handle_route_response_branch_coverage)
        # 第十三轮复盘补充步骤类型：前端行为级缺陷静态守卫（配置化 forbidden + required 扫描，比后端更泛化）
        self.register("frontend_review_static_check", self._handle_frontend_review_static_check)
        # 第十四轮复盘补充步骤类型：IndexedDB 写入前剥离 Vue/Pinia 响应式代理（配置化静态守卫）
        self.register("idb_reactive_clone_check", self._handle_idb_reactive_clone_check)
        self.register("dependency_store_hygiene_check", self._handle_dependency_store_hygiene_check)
        # 第十九轮复盘补充步骤类型：部署产物磁盘验证（BR-096 配置化磁盘校验，取代两次 HTTP 比对）
        self.register("spa_live_deploy_check", self._handle_spa_live_deploy_check)

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

    # --- 第四轮复盘补充步骤类型：后端逻辑单元验证 + 迁移/修复脚本端到端 ---
    # 适用：沙箱无浏览器 / 无 PyYAML 时，对后端"落盘前逻辑"做直接实例化单元验证，
    # 或对数据迁移 / 修复脚本做真实 --apply 端到端验证。所有参数从对应 config 块读取，
    # step 可覆盖，不在代码中硬编码任何业务路径 / 命令 / 运行时。
    # 注意 Windows 路径陷阱：嵌套子进程（execFileSync / subprocess 列表参数）调用的是
    # Windows API，只认 Windows 原生路径（C:\Users\...），不认 Git-Bash 的 /c/Users/...，
    # 否则报 ENOENT。故 runtime / script_path / cwd 一律从 config 取 Windows 原生路径。

    def _handle_backend_logic_unit_test(self, step, ctx):
        """后端逻辑单元验证：直接运行单元测试文件，该文件会实例化某个后端 service，
        对"落盘前的纯逻辑"（如文件名清洗 / 内部前缀剥离 / 路径穿越二次校验）做断言。

        触发场景：沙箱无浏览器，无法跑完整 E2E；但后端某些逻辑（文件名管线、文本治理）
        在写入磁盘前即可单元测试，无需启动服务或浏览器。

        所有 runner、测试文件路径、工作目录、判定模式从 config.backend_logic_unit_test 读取，
        step 可覆盖，不在代码中硬编码具体业务值。
        """
        blk = ctx["cfg"].get("backend_logic_unit_test", {})
        if not blk.get("enabled", True) and not step.get("force", False):
            ctx["results"].log("BackendLogicUnit", True, "Disabled, skipped")
            return

        runner_path = step.get("runner_path", blk.get("runner_path"))
        test_file = step.get("test_file", blk.get("test_file"))
        cwd = step.get("cwd", blk.get("cwd", ctx.get("project_root", os.getcwd())))
        # 判定模式：runner 退出码 + 输出关键字（不在代码中硬编码具体业务关键字）
        fail_patterns = step.get("fail_patterns", blk.get("fail_patterns", ["FAIL", "failed", "❌"]))
        pass_patterns = step.get("pass_patterns", blk.get("pass_patterns", ["PASS", "passed", "✓"]))
        timeout_ms = step.get("timeout_ms", blk.get("timeout_ms", 120000))

        if not runner_path or not test_file:
            ctx["results"].log("BackendLogicUnit", True,
                               "No runner_path/test_file configured, skipped")
            return

        cmd = [runner_path, test_file]
        try:
            proc = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True,
                timeout=timeout_ms / 1000.0,
                shell=False,
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            # 判定：退出码 0 且输出不含失败关键字；或输出含通过关键字
            exited_ok = proc.returncode == 0
            has_fail = any(p.lower() in out.lower() for p in fail_patterns)
            has_pass = any(p.lower() in out.lower() for p in pass_patterns)
            ok = exited_ok and not has_fail and (has_pass or exited_ok)
            detail = out.strip().splitlines()[-5:] if out.strip() else [f"rc={proc.returncode}"]
            ctx["results"].log("BackendLogicUnit", ok, "; ".join(detail)[-200:])
        except subprocess.TimeoutExpired:
            ctx["results"].log("BackendLogicUnit", False, f"Timeout after {timeout_ms}ms")
        except Exception as e:
            ctx["results"].log("BackendLogicUnit", False, f"Err: {str(e)[:80]}")

    def _handle_migration_script_e2e(self, step, ctx):
        """迁移 / 修复脚本端到端验证：对临时 vault 真实调用迁移/修复脚本（默认 dry-run，
        显式 --apply 才写盘），验证其确实按预期改写数据；可选 setup_command 造临时 vault，
        可选 verify_command 做改动后断言，cleanup_temp 控制是否回收临时目录。

        触发场景：数据迁移 / 文件名修复脚本必须真实跑一次才能验证"既不破坏原数据、又能正确改写"，
        仅看源码无法证明正确性；脚本默认 dry-run 保证安全。

        所有脚本路径、运行时、目标参数名、apply 标志、临时目录、验证命令从
        config.migration_script_e2e 读取，step 可覆盖，不在代码中硬编码业务值。
        """
        import shutil
        blk = ctx["cfg"].get("migration_script_e2e", {})
        if not blk.get("enabled", True) and not step.get("force", False):
            ctx["results"].log("MigrationScriptE2E", True, "Disabled, skipped")
            return

        script_path = step.get("script_path", blk.get("script_path"))
        runtime = step.get("runtime", blk.get("runtime"))
        target_arg = step.get("target_arg", blk.get("target_arg", "--vault"))
        apply_flag = step.get("apply_flag", blk.get("apply_flag", "--apply"))
        temp_vault = step.get("temp_vault_dir", blk.get("temp_vault_dir"))
        setup_command = step.get("setup_command", blk.get("setup_command"))
        verify_command = step.get("verify_command", blk.get("verify_command"))
        cleanup_temp = step.get("cleanup_temp", blk.get("cleanup_temp", True))
        cwd = step.get("cwd", blk.get("cwd", ctx.get("project_root", os.getcwd())))
        timeout_ms = step.get("timeout_ms", blk.get("timeout_ms", 120000))

        if not script_path or not runtime or not temp_vault:
            ctx["results"].log("MigrationScriptE2E", True,
                               "Insufficient config (script_path/runtime/temp_vault_dir), skipped")
            return

        try:
            # 1. 准备临时 vault（造数据）：setup_command 可以是 copy / mkdir / 生成 fixture
            if setup_command:
                subprocess.run(setup_command, cwd=cwd, shell=True,
                               capture_output=True, text=True, timeout=timeout_ms / 1000.0)

            # 2. 真实调用脚本：dry-run 为默认安全态，显式 apply_flag 才写盘
            cmd = [runtime, script_path, target_arg, temp_vault, apply_flag]
            proc = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True,
                timeout=timeout_ms / 1000.0, shell=False,
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            apply_ok = proc.returncode == 0

            # 3. 改动后断言（可选）：verify_command 通常会引用 temp_vault
            verify_ok = True
            verify_detail = "no verify_command"
            if verify_command:
                vcmd = verify_command.replace("{temp_vault}", temp_vault)
                vproc = subprocess.run(vcmd, cwd=cwd, shell=True,
                                       capture_output=True, text=True,
                                       timeout=timeout_ms / 1000.0)
                vout = (vproc.stdout or "") + "\n" + (vproc.stderr or "")
                # verify_command 约定：退出码 0 = 断言通过
                verify_ok = vproc.returncode == 0
                verify_detail = vout.strip().splitlines()[-3:]
                verify_detail = "; ".join(verify_detail)[-200:] if verify_detail else "verified"

            ok = apply_ok and verify_ok
            detail = f"apply_rc={proc.returncode}; {verify_detail}"
            ctx["results"].log("MigrationScriptE2E", ok, detail)
        except subprocess.TimeoutExpired:
            ctx["results"].log("MigrationScriptE2E", False, f"Timeout after {timeout_ms}ms")
        except Exception as e:
            ctx["results"].log("MigrationScriptE2E", False, f"Err: {str(e)[:80]}")
        finally:
            # 4. 回收临时 vault（仅清理本次新建的临时目录，不触碰项目源码树）
            if cleanup_temp and temp_vault and os.path.isdir(temp_vault):
                try:
                    shutil.rmtree(temp_vault, ignore_errors=True)
                except Exception:
                    pass

    def _handle_backend_review_static_check(self, step, ctx):
        """后端行为级缺陷静态守卫：配置化扫描后端源码中的"禁止模式组"，
        把第十一轮复盘的"静态守卫"判断逻辑（J4）落地为可执行检查。

        触发场景：七类后端行为级缺陷（类型绕过 / 冗余探测 / 关键写吞错 / 硬编码超时 /
        异步当同步）类型检查与构建都无法捕获，需在源码层做 forbid 扫描；error 级命中即阻断，
        warn 级仅标记。

        所有扫描目录、文件 glob、模式组（name/patterns/message/rule_ref/severity）、判定
        全部来自 config.backend_review_static_check，step 可覆盖，不在代码中硬编码业务值。
        """
        import re
        import fnmatch
        blk = ctx["cfg"].get("backend_review_static_check", {})
        if not blk.get("enabled", False) and not step.get("force", False):
            ctx["results"].log("BackendReviewStatic", True, "Disabled, skipped")
            return

        scan_dirs = step.get("scan_dirs", blk.get("scan_dirs", ["api/src"]))
        file_glob = step.get("file_glob", blk.get("file_glob", "*.ts"))
        groups = step.get("groups", blk.get("groups", []))
        if not groups:
            ctx["results"].log("BackendReviewStatic", True, "No groups configured, skipped")
            return

        project_root = ctx.get("project_root", os.getcwd())
        files = []
        for d in scan_dirs:
            base = d if os.path.isabs(d) else os.path.join(project_root, d)
            if not os.path.isdir(base):
                continue
            for root, _dirs, fnames in os.walk(base):
                for fn in fnames:
                    if fnmatch.fnmatch(fn, file_glob):
                        files.append(os.path.join(root, fn))
        if not files:
            ctx["results"].log("BackendReviewStatic", True, "No files matched, skipped")
            return

        error_hits = []
        warn_hits = []
        for grp in groups:
            gname = grp.get("name", "group")
            patterns = grp.get("patterns", [])
            use_regex = grp.get("regex", False)
            severity = grp.get("severity", "warn")
            message = grp.get("message", gname)
            rule_ref = grp.get("rule_ref", "")
            for fpath in files:
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        flines = fh.readlines()
                except Exception:
                    continue
                rel = os.path.relpath(fpath, project_root)
                for ln, content in enumerate(flines, 1):
                    for pat in patterns:
                        if use_regex:
                            try:
                                matched = re.search(pat, content) is not None
                            except re.error:
                                matched = False
                        else:
                            matched = pat in content
                        if not matched:
                            continue
                        hit = f"{rel}:{ln}: {message}" + (f" [{rule_ref}]" if rule_ref else "")
                        if severity == "error":
                            error_hits.append(hit)
                        else:
                            warn_hits.append(hit)

        ok = len(error_hits) == 0
        parts = []
        if error_hits:
            parts.append(f"ERROR({len(error_hits)}): " + " | ".join(error_hits[:5]))
        if warn_hits:
            parts.append(f"WARN({len(warn_hits)}): " + " | ".join(warn_hits[:5]))
        if not parts:
            parts.append("no forbidden patterns matched")
        ctx["results"].log("BackendReviewStatic", ok, "; ".join(parts)[-300:])

    def _handle_frontend_review_static_check(self, step, ctx):
        """前端行为级缺陷静态守卫：配置化扫描前端源码中的「禁止模式组」与「必须存在模式组」，
        把第十三轮复盘的「前端编码标准静态守卫」判断逻辑（J4）落地为可执行检查。

        与 backend_review_static_check 的区别：除 forbidden_patterns（命中即违规）外，
        额外支持 required_patterns（若扫描文件中**完全不存在**该模式则违规），用于守护
        "保护性代码被重构误删" 这类失败模式——例如 autoscroll 的 double rAF、
        edit-resend 的 removeMessagesFrom+submitQuestion 配对、成对按钮的 .edit-btn.confirm/.cancel
        样式、编辑框撑满的 .msg-content-wrapper/.msg-edit。这是比后端守卫更泛化的"存在性 + 禁止性"
        双模式静态检查。

        所有扫描目录、文件 glob、模式组（name/forbidden_patterns/required_patterns/message/rule_ref/severity）、
        判定全部来自 config.frontend_review_static_check，step 可覆盖，不在代码中硬编码业务值。
        """
        import re
        import fnmatch
        blk = ctx["cfg"].get("frontend_review_static_check", {})
        if not blk.get("enabled", False) and not step.get("force", False):
            ctx["results"].log("FrontendReviewStatic", True, "Disabled, skipped")
            return

        scan_dirs = step.get("scan_dirs", blk.get("scan_dirs", ["frontend/src"]))
        file_glob = step.get("file_glob", blk.get("file_glob", "*.{ts,vue}"))
        groups = step.get("groups", blk.get("groups", []))
        if not groups:
            ctx["results"].log("FrontendReviewStatic", True, "No groups configured, skipped")
            return

        project_root = ctx.get("project_root", os.getcwd())
        files = []
        for d in scan_dirs:
            base = d if os.path.isabs(d) else os.path.join(project_root, d)
            if not os.path.isdir(base):
                continue
            for root, _dirs, fnames in os.walk(base):
                for fn in fnames:
                    if fnmatch.fnmatch(fn, file_glob):
                        files.append(os.path.join(root, fn))
        if not files:
            ctx["results"].log("FrontendReviewStatic", True, "No files matched, skipped")
            return

        # 预读所有文件内容（required_patterns 需在"整个扫描集"维度判断存在性）
        file_contents = {}
        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    file_contents[fpath] = fh.readlines()
            except Exception:
                file_contents[fpath] = []

        error_hits = []
        warn_hits = []
        for grp in groups:
            gname = grp.get("name", "group")
            use_regex = grp.get("regex", False)
            severity = grp.get("severity", "warn")
            message = grp.get("message", gname)
            rule_ref = grp.get("rule_ref", "")
            forbidden = grp.get("forbidden_patterns", [])
            required = grp.get("required_patterns", [])

            # 1) forbidden_patterns：逐文件逐行命中即违规
            for fpath in files:
                rel = os.path.relpath(fpath, project_root)
                for ln, content in enumerate(file_contents[fpath], 1):
                    for pat in forbidden:
                        if use_regex:
                            try:
                                matched = re.search(pat, content) is not None
                            except re.error:
                                matched = False
                        else:
                            matched = pat in content
                        if not matched:
                            continue
                        hit = f"{rel}:{ln}: {message}" + (f" [{rule_ref}]" if rule_ref else "")
                        (error_hits if severity == "error" else warn_hits).append(hit)

            # 2) required_patterns：在整个扫描集中完全缺失即违规（守护保护性代码被删）
            if required:
                present = False
                for fpath in files:
                    for content in file_contents[fpath]:
                        for pat in required:
                            if use_regex:
                                try:
                                    found = re.search(pat, content) is not None
                                except re.error:
                                    found = False
                            else:
                                found = pat in content
                            if found:
                                present = True
                                break
                        if present:
                            break
                    if present:
                        break
                if not present:
                    hit = f"[scan-set] missing required pattern(s): {','.join(required)} — {message}" + (f" [{rule_ref}]" if rule_ref else "")
                    (error_hits if severity == "error" else warn_hits).append(hit)

        ok = len(error_hits) == 0
        parts = []
        if error_hits:
            parts.append(f"ERROR({len(error_hits)}): " + " | ".join(error_hits[:5]))
        if warn_hits:
            parts.append(f"WARN({len(warn_hits)}): " + " | ".join(warn_hits[:5]))
        if not parts:
            parts.append("no forbidden patterns matched; all required patterns present")
        ctx["results"].log("FrontendReviewStatic", ok, "; ".join(parts)[-300:])

    def _handle_dependency_store_hygiene_check(self, step, ctx):
        """依赖 store 卫生静态守卫：校验 pnpm store 收敛与孤儿 .pnpm-store 检测。

        把 CODING-PNPM-STORE-HYGIENE（前端 FR-085 / 后端 BR-095）的"pnpm store 散落盘根"
        判断逻辑落地为可执行静态检查：
        - 全局 ~/.npmrc 须显式声明 store-dir 收敛键（assert_npmrc_store_dir）；
        - scan_root 下不得存在与 canonical_store_dir 不一致的孤儿 .pnpm-store。

        所有扫描根、收敛键、统一 store 路径、孤儿目录名、severity、rule_ref 全部来自
        config.dependency_store_hygiene_check，step 可覆盖，不在代码中硬编码业务值。
        本检查是 CI / 环境初始化的前置断言，避免 safe-delete 沙箱钩子打断 pnpm 主目录
        探测后退化为盘根散落 .pnpm-store（污染工作区且让 node_modules 解析不到统一 store）。
        """
        import os
        import re
        blk = ctx["cfg"].get("dependency_store_hygiene_check", {})
        if not blk.get("enabled", False) and not step.get("force", False):
            ctx["results"].log("DependencyStoreHygiene", True, "Disabled, skipped")
            return

        store_dir_key = step.get("store_dir_key", blk.get("store_dir_key", "store-dir"))
        canonical = step.get("canonical_store_dir", blk.get("canonical_store_dir", ""))
        forbidden = step.get("forbidden_store_dirs",
                             blk.get("forbidden_store_dirs", [".pnpm-store"]))
        scan_root_rel = step.get("scan_root", blk.get("scan_root", "."))
        assert_npmrc = step.get("assert_npmrc_store_dir",
                                blk.get("assert_npmrc_store_dir", True))
        severity = step.get("severity", blk.get("severity", "warn"))
        rule_ref = step.get("rule_ref",
                            blk.get("rule_ref", "FR-085 / BR-095 / CODING-PNPM-STORE-HYGIENE"))

        project_root = ctx.get("project_root", os.getcwd())
        scan_root = scan_root_rel if os.path.isabs(scan_root_rel) else os.path.join(project_root, scan_root_rel)
        canonical_abs = os.path.abspath(canonical) if canonical else ""

        error_hits = []
        warn_hits = []

        # 1) 全局 ~/.npmrc 收敛键断言（根因修复：避免 pnpm 退化散落 store）
        if assert_npmrc:
            npmrc = os.path.join(os.path.expanduser("~"), ".npmrc")
            found_key = False
            try:
                with open(npmrc, "r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        if re.match(r"^\s*" + re.escape(store_dir_key) + r"\s*=", line):
                            found_key = True
                            break
            except Exception:
                pass
            if not found_key:
                msg = (f"全局 ~/.npmrc 未显式声明收敛键 '{store_dir_key}'"
                       f"（pnpm 主目录探测被沙箱钩子打断会退化为盘根散落 .pnpm-store） [{rule_ref}]")
                (error_hits if severity == "error" else warn_hits).append(msg)

        # 2) 孤儿 .pnpm-store 检测（剪枝 node_modules/.git/dist/build/public 等重目录，避免深遍历）
        skip_dirs = {".git", "node_modules", "dist", "build", "public", "public_live", ".pnpm-store"}
        for root, dirs, _fnames in os.walk(scan_root):
            # 检测本层目录中的孤儿 store（含 .pnpm-store 自身，但不深入）
            for d in list(dirs):
                if d in forbidden:
                    full = os.path.abspath(os.path.join(root, d))
                    if canonical_abs and full == canonical_abs:
                        continue  # 统一 store，合法
                    rel = os.path.relpath(full, project_root)
                    msg = (f"发现孤儿 store 目录 {rel}"
                           f"（与统一 store '{canonical}' 不一致，须确认无 node_modules/.modules.yaml 引用后清理） [{rule_ref}]")
                    (error_hits if severity == "error" else warn_hits).append(msg)
            # 剪枝：不深入重目录（含 .pnpm-store 自身）以避免巨大目录遍历
            dirs[:] = [d for d in dirs if d not in skip_dirs]

        ok = len(error_hits) == 0
        parts = []
        if error_hits:
            parts.append(f"ERROR({len(error_hits)}): " + " | ".join(error_hits[:5]))
        if warn_hits:
            parts.append(f"WARN({len(warn_hits)}): " + " | ".join(warn_hits[:5]))
        if not parts:
            parts.append("npmrc store-dir converged; no orphan .pnpm-store found")
        ctx["results"].log("DependencyStoreHygiene", ok, "; ".join(parts)[-300:])

    def _handle_spa_live_deploy_check(self, step, ctx):
        """SPA 实时部署产物磁盘验证：第十九轮复盘 / BR-096 落地。

        把「部署产物磁盘验证」判断逻辑（J4）落地为可执行检查，取代旧版「两次 HTTP 请求比对」
        的错误做法（spaRoot 启动只解析一次，目录高频轮转下两次 HTTP 校验会读到不同根而误判）：
        - 读磁盘：枚举 live_base_dir 下匹配 live_dir_pattern 的目录，按 mtime 取最新（等价于
          `ls -dt | head -1`），校验其内含 complete_marker 与 assets/index-*.js 资源包；
        - 无完整新目录则回退 legacy_dir 并降级告警（BR-096-2 验证/重启顺序铁律的静默失效保护）；
        - 若 restart_required：轮询 required_ports 监听（部署后须重启后端），未监听即判定部署/重启失败。

        所有目录基准、前缀、标记、资源前缀、恶意路径样本、端口、verify_via_disk 全部来自
        config.spa_live_deploy_check，step 可覆盖，不在代码中硬编码业务值。
        """
        import glob as _glob
        blk = ctx["cfg"].get("spa_live_deploy_check", {})
        if not blk.get("enabled", False) and not step.get("force", False):
            ctx["results"].log("SpaLiveDeploy", True, "Disabled, skipped")
            return

        verify_via_disk = step.get("verify_via_disk", blk.get("verify_via_disk", True))
        live_base_dir = step.get("live_base_dir", blk.get("live_base_dir", "api"))
        live_dir_pattern = step.get("live_dir_pattern", blk.get("live_dir_pattern", "public_live_"))
        legacy_dir = step.get("legacy_dir", blk.get("legacy_dir", "public"))
        complete_marker = step.get("complete_marker", blk.get("complete_marker", ".deploy-complete"))
        asset_prefix = step.get("asset_prefix", blk.get("asset_prefix", "/wiki/"))
        restart_required = step.get("restart_required", blk.get("restart_required", True))
        required_ports = step.get("required_ports", blk.get("required_ports", []))

        project_root = ctx.get("project_root", os.getcwd())
        base = live_base_dir if os.path.isabs(live_base_dir) else os.path.join(project_root, live_base_dir)

        error_hits = []
        warn_hits = []
        resolved_dir = None

        if verify_via_disk:
            if not os.path.isdir(base):
                error_hits.append(f"live 基准目录不存在: {base}（部署未产出 live 目录？）")
            else:
                # 枚举匹配前缀的目录，按 mtime 取最新（等价于 ls -dt | head -1）
                candidates = []
                for name in os.listdir(base):
                    full = os.path.join(base, name)
                    if os.path.isdir(full) and name.startswith(live_dir_pattern):
                        candidates.append((os.path.getmtime(full), full))
                candidates.sort(reverse=True)
                if not candidates:
                    error_hits.append(f"未找到任何匹配 '{live_dir_pattern}' 的部署目录于 {base}")
                else:
                    latest = candidates[0][1]
                    # 完整性标记
                    marker_path = os.path.join(latest, complete_marker)
                    if not os.path.exists(marker_path):
                        warn_hits.append(
                            f"最新部署目录 {os.path.relpath(latest, project_root)} 缺少完整性标记 "
                            f"'{complete_marker}'（部署未真正完成 / 回退判定）"
                        )
                    # 资源包（assets/index-*.js）
                    bundle_glob = os.path.join(latest, "assets", "index-*.js")
                    if not _glob.glob(bundle_glob):
                        warn_hits.append(
                            f"最新部署目录 {os.path.relpath(latest, project_root)} 未找到资源包 "
                            f"assets/index-*.js（构建产物缺失）"
                        )
                    resolved_dir = latest
                    # 兜底目录不应仍存在（若存在说明回退发生过，需清理避免静默生效）
                    legacy_full = os.path.join(base, legacy_dir)
                    if os.path.isdir(legacy_full):
                        warn_hits.append(
                            f"兜底目录 {os.path.relpath(legacy_full, project_root)} 仍存在"
                            f"（确认新目录完整后清理，避免回退静默生效）"
                        )
        else:
            # 旧版两次 HTTP 校验路径已弃用，提示改用 verify_via_disk
            warn_hits.append("verify_via_disk=false：旧版两次 HTTP 校验已弃用（目录轮转会误判），建议置 true")

        # 重启后端口监听校验（BR-096-2 验证/重启顺序铁律）
        if restart_required and required_ports:
            try:
                listening = verify_ports_listening(required_ports)
            except Exception:
                listening = {}
            not_listening = [p for p, ok in listening.items() if not ok]
            if not_listening:
                error_hits.append(
                    f"部署后端口未监听（须重启后端使 spaRoot 重新解析）：{not_listening}"
                )
            else:
                warn_hits.append(f"ports_listening: {list(listening.keys())}")

        ok = len(error_hits) == 0
        parts = []
        if resolved_dir:
            parts.append(f"resolved:{os.path.relpath(resolved_dir, project_root)}")
        if error_hits:
            parts.append(f"ERROR({len(error_hits)}): " + " | ".join(error_hits[:5]))
        if warn_hits:
            parts.append(f"WARN({len(warn_hits)}): " + " | ".join(warn_hits[:5]))
        if not parts:
            parts.append("disk live dir verified; ports listening")
        ctx["results"].log("SpaLiveDeploy", ok, "; ".join(parts)[-300:])

    def _handle_route_response_branch_coverage(self, step, ctx):
        """路由响应分支覆盖：配置化逐分支断言被测路由在各请求参数组合下的返回状态码，
        把第十二轮复盘"归档路由响应分支覆盖 + 静默缺陷回归"判断逻辑落地为可执行检查。

        静默缺陷特征：类型检查 / 构建 / 端点冒烟都"通过"，但某个非法输入分支返回了
        错误状态码（或错误地把非法输入当作合法处理）。必须逐分支断言 expected_status，
        并对 200 分支校验响应含 required_fields（如 content / refs）。

        所有路由、方法、分支用例（params / expected_status / required_fields）、判定
        全部来自 config.route_response_branch_coverage，step 可覆盖，不在代码中硬编码业务值。
        """
        import urllib.parse
        blk = ctx["cfg"].get("route_response_branch_coverage", {})
        if not blk.get("enabled", False) and not step.get("force", False):
            ctx["results"].log("RouteBranchCoverage", True, "Disabled, skipped")
            return

        base_url = ctx["cfg"].get("service", {}).get("api_url", "http://localhost:3000")
        req_timeout = (int(blk.get("timeout_ms", 120000)) if blk.get("timeout_ms") else 120000) / 1000.0

        # 构造路由规格列表：优先 routes 列表（多路由），否则用遗留单路由字段（向后兼容）
        routes = step.get("routes", blk.get("routes")) or []
        if not routes:
            rn = step.get("route_name", blk.get("route_name", ""))
            mt = step.get("method", blk.get("method", "GET")).upper()
            bc = step.get("branch_cases", blk.get("branch_cases", []))
            if rn and bc:
                routes = [{"route_name": rn, "method": mt, "branch_cases": bc,
                           "token_env": blk.get("token_env")}]
        if not routes:
            ctx["results"].log("RouteBranchCoverage", True, "No route_name/branch_cases/routes configured, skipped")
            return

        pctx = ctx.get("ctx")
        req = getattr(pctx, "request", None) if pctx is not None else None
        if req is None:
            ctx["results"].log("RouteBranchCoverage", False, "No HTTP request context available")
            return

        overall_ok = True
        details = []
        import os
        for spec in routes:
            route_name = spec.get("route_name", "")
            method = str(spec.get("method", "GET")).upper()
            branch_cases = spec.get("branch_cases", [])
            token_env = spec.get("token_env") or blk.get("token_env")
            extra_headers = dict(spec.get("extra_headers", {}) or {})
            if not route_name or not branch_cases:
                ctx["results"].log("RouteBranchCoverage", True, f"Route {route_name or '(empty)'} skipped (no name/cases)")
                continue
            # 解析鉴权令牌（仅注入到需登录的分支；匿名分支不注入，断言 fail-closed 401）
            auth_header = None
            if token_env:
                tok = os.environ.get(token_env)
                if tok:
                    auth_header = f"Bearer {tok}"

            for case in branch_cases:
                cname = case.get("name", "case")
                params = dict(case.get("params", {}))
                expected = int(case.get("expected_status", 200))
                required_fields = case.get("required_fields", [])
                required_headers = case.get("required_headers", [])
                # 路径占位符替换（:param 从 params 中移除并填入路径），其余作为 query 参数
                path = route_name
                for k in list(params.keys()):
                    ph = ":" + k
                    if ph in path:
                        path = path.replace(ph, urllib.parse.quote(str(params[k]), safe=""))
                        del params[k]
                qs = urllib.parse.urlencode(params) if params else ""
                url = base_url.rstrip("/") + path + (("?" + qs) if qs else "")
                headers = dict(extra_headers)
                if auth_header:
                    headers["Authorization"] = auth_header
                try:
                    kwargs = {"timeout": req_timeout}
                    if headers:
                        kwargs["headers"] = headers
                    resp = req.request(method, url, **kwargs)
                    status = resp.status
                    ok = status == expected
                    extra = ""
                    if ok and status == 200:
                        if required_fields:
                            try:
                                body = resp.json()
                                missing = [f for f in required_fields if f not in body]
                                if missing:
                                    ok = False
                                    extra = f"; missing fields: {missing}"
                            except Exception:
                                ok = False
                                extra = "; response not JSON"
                        if ok and required_headers:
                            hdr_missing = [h for h in required_headers
                                           if not (resp.headers.get(h) if hasattr(resp, "headers") else None)]
                            if hdr_missing:
                                ok = False
                                extra = f"; missing headers: {hdr_missing}"
                    if not ok:
                        overall_ok = False
                    details.append(f"{route_name}::{cname}:{status}" + (extra if extra else ""))
                except Exception as e:
                    overall_ok = False
                    details.append(f"{route_name}::{cname}:ERR({str(e)[:40]})")

        ctx["results"].log("RouteBranchCoverage", overall_ok, "; ".join(details))

    def _handle_idb_reactive_clone_check(self, step, ctx):
        """IndexedDB 写入前剥离 Vue/Pinia 响应式代理静态守卫：配置化扫描前端源码中的
        IndexedDB 写入点（dbPut / saveUserConfig / idbPut / store.put / transactions.add），
        核对写入值若源自 store state ref / reactive() 是否在写入前整树深拷贝
        （JSON.parse(JSON.stringify(x)) / clone(x)），并对"伪剥离"写法（toRaw( /
        structuredClone(reactiveObj)）判违规。

        把 CODING-IDB-REACTIVE-CLONE（前端 FR-081）的"reactive 代理直传 IndexedDB 导致
        [object Array] could not be cloned 静默丢配置"判断逻辑落地为可执行静态检查。

        判定语义（与 FR-081 三子规则对齐）：
        - R-2 禁 toRaw() 当深剥离：toRaw( 出现在写入点上下文 → 必违规（仅剥顶层）。
        - R-3 禁 structuredClone(reactiveObj)：structuredClone( 无法克隆代理，将其排除在
          安全深拷贝指示符之外，故"响应式来源 + 未见安全深拷贝"分支持自然覆盖。
        - R-1 写入前必须整树深拷贝：窗口内含响应式来源（reactive_indicators / reactive_arg_regex）
          但无安全深拷贝指示符（safe_clone_indicators）→ 命中缺失克隆违规。

        所有扫描目录、文件 glob、写入点模式、响应式指示符、安全深拷贝指示符、伪剥离模式、
        判定 severity 与 rule_ref 全部来自 config.idb_reactive_clone_check，step 可覆盖，
        不在代码中硬编码业务值。本检查是运行时单测（写入 reactive 对象后验证落盘）的
        互补静态守卫——静态扫描用于防回归，不替代真实写入验证。
        """
        import re
        import fnmatch
        blk = ctx["cfg"].get("idb_reactive_clone_check", {})
        if not blk.get("enabled", False) and not step.get("force", False):
            ctx["results"].log("IdbReactiveClone", True, "Disabled, skipped")
            return

        scan_dirs = step.get("scan_dirs", blk.get("scan_dirs", ["frontend/src"]))
        file_glob = step.get("file_glob", blk.get("file_glob", "*.{ts,vue}"))
        scan_patterns = step.get("scan_patterns", blk.get("scan_patterns",
            ["dbPut", "saveUserConfig", "idbPut", "store.put", "transactions.add"]))
        reactive_indicators = step.get("reactive_indicators", blk.get("reactive_indicators",
            ["reactive(", "toRefs(", "toRef(", "defineStore("]))
        reactive_arg_regex = step.get("reactive_arg_regex", blk.get("reactive_arg_regex",
            r"(store\.|state\.|this\.|\.value\b|reactiveStore)"))
        safe_clone_indicators = step.get("safe_clone_indicators", blk.get("safe_clone_indicators",
            ["JSON.parse(JSON.stringify", "clone(", "deepClone(", "cloneDeep("]))
        forbidden_unsafe = step.get("forbidden_unsafe_patterns",
            blk.get("forbidden_unsafe_patterns", ["toRaw("]))
        scan_window = int(step.get("scan_window_lines", blk.get("scan_window_lines", 40)))
        severity_missing = step.get("severity_missing_clone",
            blk.get("severity_missing_clone", "error"))
        severity_unsafe = step.get("severity_unsafe", blk.get("severity_unsafe", "error"))
        rule_ref = step.get("rule_ref",
            blk.get("rule_ref", "FR-081 / CODING-IDB-REACTIVE-CLONE"))

        project_root = ctx.get("project_root", os.getcwd())
        files = []
        for d in scan_dirs:
            base = d if os.path.isabs(d) else os.path.join(project_root, d)
            if not os.path.isdir(base):
                continue
            for root, _dirs, fnames in os.walk(base):
                for fn in fnames:
                    if fnmatch.fnmatch(fn, file_glob):
                        files.append(os.path.join(root, fn))
        if not files:
            ctx["results"].log("IdbReactiveClone", True, "No files matched, skipped")
            return

        # 预读所有文件内容（按行存储，便于窗口切片）
        file_lines = {}
        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    file_lines[fpath] = fh.readlines()
            except Exception:
                file_lines[fpath] = []

        try:
            arg_re = re.compile(reactive_arg_regex)
        except re.error:
            arg_re = re.compile(r"(store\.|state\.|this\.|\.value\b|reactiveStore)")

        error_hits = []
        warn_hits = []
        for fpath in files:
            rel = os.path.relpath(fpath, project_root)
            lines = file_lines[fpath]
            for li, content in enumerate(lines):
                # 命中 IndexedDB 写入点才进入判定（缩小扫描面）
                if not any(p in content for p in scan_patterns):
                    continue
                # 写入点上方 scan_window 行 + 本行作为上下文窗口
                start = max(0, li - scan_window)
                window_text = "".join(lines[start:li + 1])

                # 1) 伪剥离：toRaw( 在写入点上下文中出现 → 必违规（R-2）
                for fu in forbidden_unsafe:
                    if fu in window_text:
                        hit = (f"{rel}:{li+1}: 发现伪剥离写法 '{fu.strip()}'"
                               f"（toRaw 仅剥顶层、嵌套代理仍会 [object Array] could not be cloned）"
                               f"—写入前必须整树深拷贝 [{rule_ref}]")
                        (error_hits if severity_unsafe == "error" else warn_hits).append(hit)
                        break

                # 2) 响应式代理直传风险：窗口/本行含响应式来源，但未见安全深拷贝指示符（R-1）
                has_reactive = any(r in window_text for r in reactive_indicators) \
                    or bool(arg_re.search(content))
                has_safe_clone = any(c in window_text for c in safe_clone_indicators)
                if has_reactive and not has_safe_clone:
                    hit = (f"{rel}:{li+1}: IndexedDB 写入点疑似直传 reactive 代理"
                           f"（含响应式来源但未见安全深拷贝：{', '.join(safe_clone_indicators)}）"
                           f"—直传将导致 [object Array] could not be cloned 静默丢配置 [{rule_ref}]")
                    (error_hits if severity_missing == "error" else warn_hits).append(hit)

        ok = len(error_hits) == 0
        parts = []
        if error_hits:
            parts.append(f"ERROR({len(error_hits)}): " + " | ".join(error_hits[:5]))
        if warn_hits:
            parts.append(f"WARN({len(warn_hits)}): " + " | ".join(warn_hits[:5]))
        if not parts:
            parts.append("no reactive-proxy-in-IDB write sites, or all cloned safely before put")
        ctx["results"].log("IdbReactiveClone", ok, "; ".join(parts)[-300:])
