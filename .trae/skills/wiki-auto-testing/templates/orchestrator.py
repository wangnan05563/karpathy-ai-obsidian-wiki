# -*- coding: utf-8 -*-
"""
wiki-auto-testing orchestrator.

Supports two execution modes:
1. Traditional: calls phase scripts directly (backward compatible)
2. Dynamic engine: reads step definitions from config.yaml

Usage:
    python orchestrator.py                  # Full test run (traditional)
    python orchestrator.py --engine          # Use dynamic step engine
    python orchestrator.py --quiet          # Suppress per-test logs
    python orchestrator.py --phase basic    # Run only basic tests
"""
import sys
import os
import argparse

_template_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _template_dir)

from _shared import (
    load_config, TestResults, get_enabled_phases,
    setup_browser, teardown_browser
)


def run_traditional(phases_set, cfg, results, browser, ctx, page,
                    console_errors, shot_dir, quiet=False):
    """Run using phase scripts (traditional mode)."""
    from phase3_basic import run_phase as run_phase3
    from phase4_interactions import run_phase as run_phase4
    from phase5_supplementary import run_phase as run_phase5

    if "basic" in phases_set:
        if not quiet: print("\\n=== Phase 3: Basic Tests ===")
        run_phase3(cfg, results, page, ctx, shot_dir, quiet)
    if "interactions" in phases_set:
        if not quiet: print("\\n=== Phase 4: Interaction Tests ===")
        run_phase4(cfg, results, page, ctx, quiet)
    if "supplementary" in phases_set:
        if not quiet: print("\\n=== Phase 5: Supplementary Tests ===")
        run_phase5(cfg, results, page, ctx, console_errors, quiet)


def run_dynamic(phases_config, cfg, results, browser, ctx, page,
                console_errors, shot_dir, quiet=False):
    """Run using dynamic step engine from config.yaml."""
    from _step_engine import StepEngine

    engine = StepEngine()
    phase_names = ["basic", "interactions", "supplementary"]

    for pname in phase_names:
        if pname not in phases_config:
            continue
        phase_steps = phases_config[pname]
        if isinstance(phase_steps, list):
            steps = phase_steps
        else:
            steps = phase_steps.get("steps", [])

        if not steps:
            continue

        if not quiet:
            print(f"\\n=== Phase: {pname} ({len(steps)} steps) ===")

        context = {
            "page": page, "cfg": cfg, "results": results,
            "ctx": ctx, "console_errors": console_errors,
            "shot_dir": shot_dir, "browser": browser
        }
        engine.execute_plan(steps, context)


def run(config_path=None, quiet=False, use_engine=False):
    """Main entry point."""
    cfg = load_config(config_path)
    results = TestResults(quiet=quiet)
    phases = get_enabled_phases(cfg)

    browser, ctx_obj, page, console_errors, shot_dir = setup_browser(cfg, quiet)

    try:
        if use_engine:
            # Dynamic engine mode: read steps from config
            phases_config = cfg.get("test_plan", {}).get("phases", {})
            if phases_config:
                run_dynamic(phases_config, cfg, results, browser, ctx_obj,
                          page, console_errors, shot_dir, quiet)
            else:
                run_traditional(phases, cfg, results, browser, ctx_obj,
                              page, console_errors, shot_dir, quiet)
        else:
            # Traditional mode
            if phases == {"basic", "interactions", "supplementary"}:
                run_traditional(phases, cfg, results, browser, ctx_obj,
                              page, console_errors, shot_dir, quiet)
            else:
                run_traditional(phases, cfg, results, browser, ctx_obj,
                              page, console_errors, shot_dir, quiet)
    finally:
        teardown_browser(browser, ctx_obj)

    print(results.summary())

    rf = cfg["output"]["result_file"]
    enc = cfg["output"].get("encoding", "utf-8")
    results.save(rf, enc)

    return results.failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="wiki-auto-testing orchestrator")
    parser.add_argument("--config", type=str, default=None, help="Path to config.yaml")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-test logs")
    parser.add_argument("--phase", type=str, nargs="+",
                        choices=["basic", "interactions", "supplementary"],
                        help="Run only specified phase(s)")
    parser.add_argument("--engine", action="store_true",
                        help="Use dynamic step engine from config")
    args = parser.parse_args()

    if args.phase:
        import tempfile, yaml
        cfg_path = args.config
        temp_cfg_path = None
        if cfg_path:
            with open(cfg_path, "r", encoding="utf-8") as f:
                actual_cfg = yaml.safe_load(f) or {}
            actual_cfg["test_plan"] = {"enabled_phases": args.phase}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml",
                                            delete=False, encoding="utf-8") as f:
                yaml.dump(actual_cfg, f)
                temp_cfg_path = f.name
            cfg_path = temp_cfg_path
        success = run(cfg_path, quiet=args.quiet, use_engine=args.engine)
        if temp_cfg_path:
            os.unlink(temp_cfg_path)
        sys.exit(0 if success else 1)
    else:
        success = run(args.config, quiet=args.quiet, use_engine=args.engine)
        sys.exit(0 if success else 1)
