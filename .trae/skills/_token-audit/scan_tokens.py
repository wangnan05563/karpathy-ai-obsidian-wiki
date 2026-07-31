#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wiki-* 技能 Token 审计扫描脚本

功能：
1. 扫描 .trae/skills/ 下所有技能的 .md/.yaml/.yml/.py 文件
2. 统计字符数/行数/近似 token（chars/3.5）
3. 读取 token-budget.yaml 预算配置，标记超预算文件
4. 识别冗余信号：defaults/config 顶层 key 重合率、SKILL.md 大章节
5. 输出控制台报告 + report.json（供 --compare 对比）

用法：
    python scan_tokens.py                    # 扫描全部技能
    python scan_tokens.py --skill wiki-code-dev  # 扫描单个技能
    python scan_tokens.py --compare baseline.json  # 与基线对比
    python scan_tokens.py --json report.json  # 指定输出 JSON 路径

纯 Python 标准库，无第三方依赖。
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ============================================================
# 配置常量
# ============================================================

# 脚本所在目录（_token-audit/）
SCRIPT_DIR = Path(__file__).resolve().parent

# skills 根目录（_token-audit 的上级）
SKILLS_ROOT = SCRIPT_DIR.parent

# 预算配置文件
BUDGET_FILE = SCRIPT_DIR / "token-budget.yaml"

# 默认报告输出路径
DEFAULT_REPORT = SCRIPT_DIR / "report.json"

# 纳入统计的文件扩展名
SCANNED_EXTENSIONS = {".md", ".yaml", ".yml", ".py"}

# 排除的目录（避免扫描缓存）
EXCLUDED_DIRS = {"__pycache__", ".git", "node_modules"}

# token 估算系数（中文混合英文约 3.5 字符/token）
CHARS_PER_TOKEN = 3.5

# YAML 顶层 key 正则（用于 defaults/config 重复度检测）
# 匹配行首非缩进的 key: 形式
TOPLEVEL_KEY_PATTERN = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:")

# Markdown 一级章节正则（## 标题）
MD_H2_PATTERN = re.compile(r"^##\s+(.+?)\s*$")


# ============================================================
# 核心扫描逻辑
# ============================================================

def read_text_safely(path: Path) -> str:
    """安全读取文件文本，UTF-8 优先，降级 GBK 兜底。"""
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, OSError):
            continue
    return ""


def count_lines(text: str) -> int:
    """统计行数（空文本返回 0）。"""
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def estimate_tokens(chars: int) -> int:
    """近似 token 估算（字符数 / 3.5）。"""
    return round(chars / CHARS_PER_TOKEN)


def classify_file(rel_path: str) -> str:
    """根据文件相对路径分类，用于匹配预算类别。

    返回类别名：skill_md / config_file / references_single / defaults_yaml /
    skill_loader / template_py / other
    """
    name = Path(rel_path).name
    parent = Path(rel_path).parent.name
    ext = Path(rel_path).suffix

    if name == "SKILL.md":
        return "skill_md"
    if name == "defaults.yaml":
        return "defaults_yaml"
    if name == "skill-loader.md":
        return "skill_loader"
    if parent == "config" and ext in (".md", ".yaml", ".yml"):
        return "config_file"
    if parent == "references" and ext == ".md":
        return "references_single"
    if parent == "templates" and ext == ".py":
        return "template_py"
    return "other"


def scan_single_file(path: Path, skill_name: str) -> dict:
    """扫描单个文件，返回统计信息。"""
    text = read_text_safely(path)
    rel_path = str(path.relative_to(SKILLS_ROOT)).replace("\\", "/")
    return {
        "skill": skill_name,
        "rel_path": rel_path,
        "category": classify_file(rel_path),
        "chars": len(text),
        "lines": count_lines(text),
        "tokens": estimate_tokens(len(text)),
    }


def scan_skill(skill_dir: Path) -> list:
    """扫描单个技能目录下所有文件。"""
    results = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        # 排除缓存目录
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix not in SCANNED_EXTENSIONS:
            continue
        results.append(scan_single_file(path, skill_dir.name))
    return results


def scan_all_skills() -> list:
    """扫描 SKILLS_ROOT 下所有技能目录。"""
    all_results = []
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        # 跳过 _token-audit 自身
        if skill_dir.name.startswith("_"):
            continue
        all_results.extend(scan_skill(skill_dir))
    return all_results


# ============================================================
# 冗余检测
# ============================================================

def extract_yaml_toplevel_keys(path: Path) -> set:
    """提取 YAML 文件的顶层 key 集合（用于重复度检测）。"""
    text = read_text_safely(path)
    keys = set()
    for line in text.splitlines():
        # 跳过注释和空行
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = TOPLEVEL_KEY_PATTERN.match(line)
        if m:
            keys.add(m.group(1))
    return keys


def detect_defaults_config_overlap(skill_dir: Path) -> dict:
    """检测 defaults.yaml 与 config.yaml 的顶层 key 重合率。"""
    defaults_path = skill_dir / "defaults.yaml"
    config_path = skill_dir / "config.yaml"
    if not defaults_path.exists() or not config_path.exists():
        return {"applicable": False}

    defaults_keys = extract_yaml_toplevel_keys(defaults_path)
    config_keys = extract_yaml_toplevel_keys(config_path)
    if not defaults_keys:
        return {"applicable": False}

    overlap = defaults_keys & config_keys
    overlap_pct = round(len(overlap) / len(defaults_keys) * 100, 1)
    return {
        "applicable": True,
        "defaults_keys_count": len(defaults_keys),
        "config_keys_count": len(config_keys),
        "overlap_count": len(overlap),
        "overlap_pct": overlap_pct,
    }


def detect_skill_md_large_sections(skill_md_path: Path, threshold_lines: int = 50) -> list:
    """检测 SKILL.md 中超过阈值行数的章节（建议拆分）。"""
    text = read_text_safely(skill_md_path)
    if not text:
        return []

    lines = text.splitlines()
    sections = []
    current_title = None
    current_start = 0

    for i, line in enumerate(lines):
        m = MD_H2_PATTERN.match(line)
        if m:
            # 结束上一章节
            if current_title is not None:
                section_lines = i - current_start
                if section_lines >= threshold_lines:
                    sections.append({
                        "title": current_title,
                        "start_line": current_start + 1,
                        "end_line": i,
                        "lines": section_lines,
                    })
            current_title = m.group(1)
            current_start = i

    # 结束最后一章节
    if current_title is not None:
        section_lines = len(lines) - current_start
        if section_lines >= threshold_lines:
            sections.append({
                "title": current_title,
                "start_line": current_start + 1,
                "end_line": len(lines),
                "lines": section_lines,
            })

    return sections


# ============================================================
# 预算检查
# ============================================================

def parse_budget_yaml() -> dict:
    """解析 token-budget.yaml（简单解析，避免依赖 PyYAML）。

    仅提取 budgets / skill_total_budgets / redundancy_thresholds 三段。
    """
    text = read_text_safely(BUDGET_FILE)
    if not text:
        return {}

    budget = {"budgets": {}, "skill_total_budgets": {}, "redundancy_thresholds": {}}
    current_section = None
    current_nested = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # 顶层段
        if not line.startswith(" ") and stripped.endswith(":"):
            key = stripped[:-1]
            if key in budget:
                current_section = key
                current_nested = None
            continue

        # 嵌套段（如 redundancy_thresholds 下的子项）
        if current_section and ":" in stripped:
            parts = stripped.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip().strip("'\"")
            # 尝试转 int
            try:
                val = int(val)
            except ValueError:
                pass
            budget[current_section][key] = val

    return budget


def check_budget(file_info: dict, budgets: dict) -> dict:
    """检查单个文件是否超预算。"""
    category = file_info["category"]
    limit = budgets.get("budgets", {}).get(category)
    if limit is None:
        return {"has_budget": False}
    over = file_info["chars"] > limit
    return {
        "has_budget": True,
        "limit": limit,
        "over": over,
        "over_by": file_info["chars"] - limit if over else 0,
    }


# ============================================================
# 报告生成
# ============================================================

def aggregate_by_skill(results: list) -> dict:
    """按技能聚合统计。"""
    agg = {}
    for r in results:
        skill = r["skill"]
        if skill not in agg:
            agg[skill] = {"files": 0, "chars": 0, "lines": 0, "tokens": 0}
        agg[skill]["files"] += 1
        agg[skill]["chars"] += r["chars"]
        agg[skill]["lines"] += r["lines"]
        agg[skill]["tokens"] += r["tokens"]
    return agg


def build_report(results: list, budgets: dict) -> dict:
    """构建完整报告。"""
    by_skill = aggregate_by_skill(results)

    # 冗余检测：每个技能的 defaults/config 重合 + SKILL.md 大章节
    redundancies = {}
    for skill_name in by_skill:
        skill_dir = SKILLS_ROOT / skill_name
        overlap = detect_defaults_config_overlap(skill_dir)
        skill_md = skill_dir / "SKILL.md"
        large_sections = []
        if skill_md.exists():
            threshold = budgets.get("redundancy_thresholds", {}).get(
                "skill_md_movable_section_lines", 50
            )
            large_sections = detect_skill_md_large_sections(skill_md, threshold)

        redundancies[skill_name] = {
            "defaults_config_overlap": overlap,
            "skill_md_large_sections": large_sections,
        }

    # 预算违规文件
    over_budget = []
    for r in results:
        b = check_budget(r, budgets)
        if b.get("over"):
            over_budget.append({
                "rel_path": r["rel_path"],
                "category": r["category"],
                "chars": r["chars"],
                "limit": b["limit"],
                "over_by": b["over_by"],
            })

    # 技能总预算检查
    skill_total_over = []
    skill_budgets = budgets.get("skill_total_budgets", {})
    for skill, agg in by_skill.items():
        limit = skill_budgets.get(skill)
        if limit and agg["tokens"] > limit:
            skill_total_over.append({
                "skill": skill,
                "tokens": agg["tokens"],
                "limit": limit,
                "over_by": agg["tokens"] - limit,
            })

    return {
        "totals": {
            "total_files": len(results),
            "total_chars": sum(r["chars"] for r in results),
            "total_lines": sum(r["lines"] for r in results),
            "total_tokens": sum(r["tokens"] for r in results),
        },
        "by_skill": by_skill,
        "by_file": sorted(results, key=lambda x: x["chars"], reverse=True),
        "redundancies": redundancies,
        "over_budget_files": over_budget,
        "over_budget_skills": skill_total_over,
    }


def print_console_report(report: dict, budgets: dict):
    """打印控制台报告。"""
    t = report["totals"]
    print("=" * 70)
    print("Token 审计报告 — wiki-* 技能")
    print("=" * 70)
    print(f"总文件数: {t['total_files']}  总字符: {t['total_chars']:,}  "
          f"总行数: {t['total_lines']:,}  近似 token: {t['total_tokens']:,}")
    print()

    # 按技能汇总
    print("-" * 70)
    print("按技能汇总:")
    print(f"{'技能':<32} {'文件':>5} {'字符':>10} {'token':>10}")
    print("-" * 70)
    skill_budgets = budgets.get("skill_total_budgets", {})
    for skill, agg in sorted(report["by_skill"].items(), key=lambda x: -x[1]["tokens"]):
        limit = skill_budgets.get(skill, "")
        limit_str = f"/{limit}" if limit else ""
        flag = "  ⚠超" if skill in [s["skill"] for s in report["over_budget_skills"]] else ""
        print(f"{skill:<32} {agg['files']:>5} {agg['chars']:>10,} "
              f"{agg['tokens']:>8,}{limit_str:<8}{flag}")
    print()

    # Top 10 大文件
    print("-" * 70)
    print("Top 10 大文件:")
    print(f"{'文件':<60} {'字符':>9} {'类别':<18}")
    print("-" * 70)
    file_budgets = budgets.get("budgets", {})
    for r in report["by_file"][:10]:
        name = r["rel_path"]
        if len(name) > 58:
            name = "..." + name[-55:]
        limit = file_budgets.get(r["category"], "")
        flag = " ⚠" if any(o["rel_path"] == r["rel_path"] for o in report["over_budget_files"]) else ""
        print(f"{name:<60} {r['chars']:>9,} {r['category']:<18}{flag}")
    print()

    # 冗余信号
    print("-" * 70)
    print("冗余信号:")
    print("-" * 70)
    overlap_threshold = budgets.get("redundancy_thresholds", {}).get(
        "defaults_config_overlap_pct", 30
    )
    for skill, red in report["redundancies"].items():
        overlap = red["defaults_config_overlap"]
        if overlap.get("applicable"):
            flag = " ⚠告警" if overlap["overlap_pct"] > overlap_threshold else ""
            print(f"  {skill}: defaults/config 顶层 key 重合率 "
                  f"{overlap['overlap_pct']}% ({overlap['overlap_count']}/"
                  f"{overlap['defaults_keys_count']}){flag}")
        sections = red["skill_md_large_sections"]
        if sections:
            print(f"  {skill}: SKILL.md 有 {len(sections)} 个大章节建议拆分:")
            for s in sections[:5]:
                print(f"    - {s['title']} (L{s['start_line']}-{s['end_line']}, {s['lines']} 行)")
    print()

    # 预算违规
    if report["over_budget_files"]:
        print("-" * 70)
        print(f"超预算文件 ({len(report['over_budget_files'])} 个):")
        print("-" * 70)
        for o in report["over_budget_files"][:15]:
            print(f"  {o['rel_path']}: {o['chars']:,} > {o['limit']} (超 {o['over_by']:,})")
        print()


def compare_reports(current: dict, baseline_path: Path):
    """与基线报告对比，输出差异。"""
    if not baseline_path.exists():
        print(f"  [对比] 基线文件不存在: {baseline_path}")
        return

    baseline = json.loads(read_text_safely(baseline_path))
    print("=" * 70)
    print("Token 优化对比报告（当前 vs 基线）")
    print("=" * 70)

    cur_total = current["totals"]["total_tokens"]
    base_total = baseline["totals"]["total_tokens"]
    diff = cur_total - base_total
    pct = round(diff / base_total * 100, 1) if base_total else 0
    sign = "+" if diff >= 0 else ""
    print(f"总 token: {base_total:,} → {cur_total:,} ({sign}{diff:,}, {sign}{pct}%)")
    print()

    print(f"{'技能':<32} {'基线':>10} {'当前':>10} {'差异':>10}")
    print("-" * 70)
    for skill in sorted(set(list(current["by_skill"].keys()) + list(baseline["by_skill"].keys()))):
        base_t = baseline["by_skill"].get(skill, {}).get("tokens", 0)
        cur_t = current["by_skill"].get(skill, {}).get("tokens", 0)
        d = cur_t - base_t
        s = "+" if d >= 0 else ""
        print(f"{skill:<32} {base_t:>10,} {cur_t:>10,} {s}{d:>9,}")
    print()

    # Top 文件差异
    cur_files = {f["rel_path"]: f["chars"] for f in current["by_file"]}
    base_files = {f["rel_path"]: f["chars"] for f in baseline["by_file"]}
    diffs = []
    for path in set(list(cur_files.keys()) + list(base_files.keys())):
        base_c = base_files.get(path, 0)
        cur_c = cur_files.get(path, 0)
        d = cur_c - base_c
        if d != 0:
            diffs.append((path, base_c, cur_c, d))
    diffs.sort(key=lambda x: x[3])

    print("文件级差异（Top 15 减少 / Top 5 增加）:")
    print("-" * 70)
    for path, base_c, cur_c, d in diffs[:15] + (diffs[-5:] if len(diffs) > 15 else []):
        s = "+" if d >= 0 else ""
        name = path if len(path) < 55 else "..." + path[-52:]
        print(f"  {name:<55} {base_c:>8,} → {cur_c:>8,} {s}{d:>7,}")


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="wiki-* 技能 Token 审计扫描")
    parser.add_argument("--skill", help="只扫描指定技能")
    parser.add_argument("--compare", help="与基线 JSON 报告对比")
    parser.add_argument("--json", default=str(DEFAULT_REPORT), help="输出 JSON 报告路径")
    args = parser.parse_args()

    # 扫描
    if args.skill:
        skill_dir = SKILLS_ROOT / args.skill
        if not skill_dir.exists():
            print(f"错误: 技能目录不存在: {skill_dir}")
            sys.exit(1)
        results = scan_skill(skill_dir)
    else:
        results = scan_all_skills()

    # 加载预算
    budgets = parse_budget_yaml()

    # 构建报告
    report = build_report(results, budgets)

    # 控制台输出
    print_console_report(report, budgets)

    # 对比
    if args.compare:
        compare_reports(report, Path(args.compare))

    # 写 JSON
    out_path = Path(args.json)
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nJSON 报告已写入: {out_path}")


if __name__ == "__main__":
    main()
