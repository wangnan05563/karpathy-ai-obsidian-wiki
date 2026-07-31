# -*- coding: utf-8 -*-
"""
FR-09-3 静态检查脚本：验证 podcast 相关文件结构与导出。
读取 config.yaml 的 fr09_3_podcast_tests 配置，逐项检查 required_strings/required_exports。
"""
import os
import sys
import yaml


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    cfg_path = os.path.join(project_root, '.trae', 'skills', 'wiki-auto-testing', 'config.yaml')
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    tests = cfg.get('fr09_3_podcast_tests', {})
    if not tests.get('enabled', False):
        print('FR-09-3 tests disabled')
        return 0

    results = []
    for key, file_cfg in tests.items():
        if key == 'enabled':
            continue
        rel = file_cfg.get('relative_path')
        if not rel:
            continue
        full = os.path.join(project_root, rel.replace('/', os.sep))
        exists = os.path.exists(full)
        results.append((f'{key}:file_exists:{os.path.basename(rel)}', exists))
        if not exists:
            continue
        with open(full, 'r', encoding='utf-8') as f:
            content = f.read()
        for s in file_cfg.get('required_strings', []):
            results.append((f'{key}:required_string:{s[:30]}', s in content))
        for exp in file_cfg.get('required_exports', []):
            results.append((f'{key}:required_export:{exp[:40]}', exp in content))

    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    for name, ok in results:
        print(f'[{"PASS" if ok else "FAIL"}] {name}')
    print(f'\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
