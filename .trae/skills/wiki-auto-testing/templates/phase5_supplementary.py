# -*- coding: utf-8 -*-
"""Phase 5: Supplementary tests - responsive, API endpoints, console errors."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))


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
    for ep in cfg["api_tests"]["endpoints"]:
        url = f"{api_url}{ep['path']}"
        try:
            resp = ctx.request.get(url)
            results.log(f"API-{ep['path']}", resp.status == ep["expected_status"],
                        f"Status: {resp.status} (expected {ep['expected_status']})")
        except Exception as e:
            results.log(f"API-{ep['path']}", False, f"Error: {str(e)[:80]}")


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


def run_phase(cfg, results, page, ctx, console_errors, quiet=False):
    """Execute Phase 5 tests."""
    if not quiet:
        print("\n=== Phase 5: Supplementary Tests ===")
    test_responsive(page, cfg, results)
    test_api_endpoints(ctx, cfg, results)
    test_console_errors(console_errors, cfg, results)
