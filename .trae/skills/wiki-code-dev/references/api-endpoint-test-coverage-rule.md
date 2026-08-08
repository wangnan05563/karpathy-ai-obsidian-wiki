# API 端点测试覆盖规则（新增路由必测）

**代码**：CODING-API-ENDPOINT-COVERAGE
**严重级别**：critical

## 问题（Problem）

两个新 REST 端点（`GET /api/threads/:id/context`、`POST /api/threads/:id/compact`）在**显式补充前没有任何自动化测试**；只有 `route_registration_check` + `type_sync_check` 这类结构性检查能发现"零覆盖缺口"。

## 规则（Rule）

### R-1：每个新路由必须同时满足三项
1. **端点测试**：启动**真实 router**（非 mock）的测试，覆盖 happy path + 非法输入(400) + 不存在资源(404) + 边界；
2. **入口注册**：在入口文件（如 `server.ts` / 路由聚合处）登记该路由；
3. **前后端类型同步**：相应的 `types.ts` 改动同步到前端。

### R-2：跑全量套件并隔离既有 flakes
改动后运行**完整**测试套件；若失败，**先单独运行失败文件**排查是否为既有 flaky，再归咎于新代码。结构性检查（`route_registration_check`、`type_sync_check`）应纳入 CI 门禁以防零覆盖漏网。

## 适用 / 不适用

- **适用**：新增/修改 REST 路由、API 端点、路由聚合、前后端类型同步。
- **不适用**：纯前端组件（无后端路由）、纯文档变更。

## 检查清单
- [ ] 新路由是否有启动真实 router 的端点测试（happy/invalid/404/400）
- [ ] 新路由是否在入口文件登记
- [ ] 前后端 types 是否同步
- [ ] 是否跑全量套件并单独隔离失败文件 flakes
