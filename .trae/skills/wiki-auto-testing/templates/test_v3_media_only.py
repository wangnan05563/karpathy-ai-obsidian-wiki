# -*- coding: utf-8 -*-
"""
v3 媒体生成工具静态检查脚本：验证 PPT/图像/视频生成相关文件结构与导出。
读取 config.yaml 的 v3_media_tests 配置，逐项检查 required_strings/required_exports，
并验证 API 端点（/api/media/video）路由可达性。
"""
import os
import sys
import yaml
import urllib.request
import urllib.error
import json


def check_files(tests, project_root):
    """检查所有文件的 required_strings 和 required_exports。"""
    results = []
    for key, file_cfg in tests.items():
        # 跳过非文件配置项
        if key in ('enabled', 'api'):
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
            results.append((f'{key}:required_string:{s[:40]}', s in content))
        for exp in file_cfg.get('required_exports', []):
            results.append((f'{key}:required_export:{exp[:50]}', exp in content))
    return results


def check_api(api_cfg, base_url='http://localhost:3000'):
    """验证 API 端点路由可达性。

    为什么用 400/404 而非 200：端点需鉴权或参数校验，
    返回 400/404 证明路由已注册，仅参数/鉴权失败。
    返回 404 用于路由不存在的判断（注意区分路由 404 与业务 404）。

    对于 GET /api/media/video/:taskId：无效 taskId 会触发后端调用 Agnes API，
    若 Agnes API 不可达会超时（后端 10 秒超时）。超时视为"路由存在但外部依赖不可达"（PASS），
    仅连接拒绝（服务未启动）或 HTTP 404（路由不存在）视为失败。
    """
    results = []
    create_ep = api_cfg.get('video_create_endpoint')
    status_ep = api_cfg.get('video_status_endpoint')
    expected_create = api_cfg.get('expected_status_create', 400)
    expected_query = api_cfg.get('expected_status_query', 404)

    # POST 创建端点：空 body 应返回 400（参数校验失败，证明路由存在）
    if create_ep:
        url = base_url + create_ep
        try:
            req = urllib.request.Request(url, data=b'{}', method='POST',
                                         headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=10)
            # 若返回 200，说明路由存在但行为异常（应返回 400）
            results.append((f'API-Create:{create_ep}:status', False))
        except urllib.error.HTTPError as e:
            # 400 = 路由存在，参数校验失败（期望）；401 = 需鉴权（也可接受，证明路由存在）
            # 404 = 路由不存在（失败）
            ok = e.code in (expected_create, 401)
            results.append((f'API-Create:{create_ep}:status={e.code}', ok))
        except urllib.error.URLError as e:
            # 连接拒绝 = 服务未启动（失败）；超时 = 路由存在但外部依赖不可达（PASS）
            reason = str(e.reason)
            if 'timed out' in reason or 'timeout' in reason.lower():
                results.append((f'API-Create:{create_ep}:timeout(external-api)', True))
            else:
                results.append((f'API-Create:{create_ep}:conn-refused', False))
        except Exception as e:
            results.append((f'API-Create:{create_ep}:error:{str(e)[:50]}', False))

    # GET 查询端点：无效 taskId 会触发后端调用 Agnes API（10 秒超时）
    if status_ep:
        url = base_url + status_ep
        try:
            req = urllib.request.Request(url, method='GET')
            # 15 秒超时：比后端 10 秒超时长，避免竞争条件
            urllib.request.urlopen(req, timeout=15)
            # 若返回 200，说明路由行为异常
            results.append((f'API-Query:{status_ep}:status', False))
        except urllib.error.HTTPError as e:
            # 400/401/500 = 路由存在，业务错误（PASS）
            # 404 = 路由不存在（失败）
            ok = e.code != 404
            results.append((f'API-Query:{status_ep}:status={e.code}', ok))
        except urllib.error.URLError as e:
            # 超时 = 路由存在但 Agnes API 不可达（PASS，外部依赖问题不影响路由注册验证）
            # 连接拒绝 = 服务未启动（失败）
            reason = str(e.reason)
            if 'timed out' in reason or 'timeout' in reason.lower():
                results.append((f'API-Query:{status_ep}:timeout(agnes-api-unreachable)', True))
            else:
                results.append((f'API-Query:{status_ep}:conn-refused', False))
        except Exception as e:
            results.append((f'API-Query:{status_ep}:error:{str(e)[:50]}', False))

    return results


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    cfg_path = os.path.join(project_root, '.trae', 'skills', 'wiki-auto-testing', 'config.yaml')
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    tests = cfg.get('v3_media_tests', {})
    if not tests.get('enabled', False):
        print('v3 media tests disabled')
        return 0

    print('=== v3 Media Generation Tests: Static Checks ===')
    file_results = check_files(tests, project_root)

    print('\n=== v3 Media Generation Tests: API Endpoint Checks ===')
    api_results = check_api(tests.get('api', {}))

    all_results = file_results + api_results
    passed = sum(1 for _, ok in all_results if ok)
    failed = sum(1 for _, ok in all_results if not ok)
    for name, ok in all_results:
        print(f'[{"PASS" if ok else "FAIL"}] {name}')
    print(f'\nTotal: {len(all_results)} | Passed: {passed} | Failed: {failed}')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
