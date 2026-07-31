"""
FR-15-6 独立静态检查脚本（不依赖 Playwright/UI）
验证 compile.md prompt + SCHEMA.md + compile-workflow.ts 的 FR-15-6 实现完整性
"""
import os
import sys
import yaml
import json

# 定位项目根
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for _ in range(5):
    if os.path.exists(os.path.join(PROJECT_ROOT, ".git")):
        break
    PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)

print(f"Project root: {PROJECT_ROOT}")

# 加载 config
config_path = os.path.join(SCRIPT_DIR, "skills", "wiki-auto-testing", "config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

fr15_6 = cfg.get("fr15_6_entity_extraction_tests", {})
if not fr15_6.get("enabled"):
    print("FR-15-6 disabled in config")
    sys.exit(0)

results = []


def log(name, ok, msg):
    results.append({"test": name, "status": "PASS" if ok else "FAIL", "details": msg})
    print(f"[{'PASS' if ok else 'FAIL'}] {name} | {msg}")


# 步骤 1：compile.md prompt 静态检查
prompt_cfg = fr15_6["compile_prompt"]
prompt_file = os.path.join(PROJECT_ROOT, "karpathy-wiki", "api", "src", "prompts", "compile.md")
try:
    with open(prompt_file, "r", encoding="utf-8") as f:
        content = f.read()
    required_strs = prompt_cfg.get("required_strings", [])
    missing = [s for s in required_strs if s not in content]
    required_steps = prompt_cfg.get("required_steps", [])
    missing_steps = [s for s in required_steps if s not in content]
    log(
        "FR15-6-Prompt-Strings",
        len(missing) == 0 and len(missing_steps) == 0,
        f"len: {len(content)}, missing strs: {missing}, missing steps: {missing_steps}",
    )
except Exception as e:
    log("FR15-6-Prompt-Strings", False, f"Error: {str(e)[:80]}")

# 步骤 2：SCHEMA.md 静态检查
schema_cfg = fr15_6["schema_file"]
schema_path = os.path.join(PROJECT_ROOT, schema_cfg["relative_path"])
try:
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_content = f.read()
    required_schema_strs = schema_cfg.get("required_strings", [])
    missing_schema = [s for s in required_schema_strs if s not in schema_content]
    log(
        "FR15-6-Schema-Strings",
        len(missing_schema) == 0,
        f"missing: {missing_schema}",
    )
except Exception as e:
    log("FR15-6-Schema-Strings", False, f"Error: {str(e)[:80]}")

# 步骤 3：compile-workflow.ts 静态检查
workflow_cfg = fr15_6["workflow_file"]
workflow_path = os.path.join(PROJECT_ROOT, workflow_cfg["relative_path"])
try:
    with open(workflow_path, "r", encoding="utf-8") as f:
        wf_content = f.read()
    required_symbols = workflow_cfg.get("required_symbols", [])
    missing_syms = [s for s in required_symbols if s not in wf_content]
    log(
        "FR15-6-Workflow-Symbols",
        len(missing_syms) == 0,
        f"missing symbols: {missing_syms}",
    )
except Exception as e:
    log("FR15-6-Workflow-Symbols", False, f"Error: {str(e)[:80]}")

# 步骤 4：write_file handler 调用 ensureEntitiesField 验证
try:
    call_pattern = fr15_6["write_handler_check"]["required_call_pattern"]
    call_count = wf_content.count(call_pattern)
    log(
        "FR15-6-Handler-Call",
        call_count >= 2,
        f"Pattern: '{call_pattern}', occurrences: {call_count} (need >= 2: definition + call)",
    )
except Exception as e:
    log("FR15-6-Handler-Call", False, f"Error: {str(e)[:80]}")

# 总结
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")

# 保存结果
result_file = os.path.join(SCRIPT_DIR, "fr15_6_result.json")
with open(result_file, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Result saved: {result_file}")

sys.exit(0 if failed == 0 else 1)
