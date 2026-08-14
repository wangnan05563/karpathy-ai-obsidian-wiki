# Rule Catalog — 部署产物磁盘验证（BR-096）

> 对应 wiki-code-dev `references/deploy-verify-disk-rule.md`（CODING-DEPLOY-VERIFY-DISK，DV-1/DV-2）。
> 基于「环境存在自动部署钩子导致 `api/public_live_<ts>` 目录高频轮转，两次 HTTP 请求校验 bundle 会命中 404 / 错版本」四维度复盘（含 Sequential Thinking）。

## 问题背景

部署架构：每次前端构建写入全新 `public_live_<ts>` 时间戳目录，后端 `resolveSpaRoot` 启动只解析一次（选数值时间戳最大且通过完整性门禁的目录）。环境存在**自动部署钩子**，会在你校验期间又切到更新的目录 → 两次 HTTP 请求之间目录已轮转：

- 第一次请求拿到旧目录的 `index.html`，第二次请求（同样的 URL）后端已指向新目录但新 `index-*.js` 尚未写完整 → 404 / 版本错乱。
- 用 HTTP 请求来"验证产物"本质是竞态，不可靠。

## 规则（2 条）

### BR-096-1：验证读磁盘最新目录，而非两次 HTTP 请求（Major）

部署后验证产物须**直接读磁盘**定位最新 `public_live_<ts>` 目录并 grep 关键 bundle，而不是发起两次 HTTP 请求比对：

```bash
# 读磁盘最新目录并校验关键 bundle（不依赖 HTTP 轮转）
D=$(ls -dt api/public_live_* | head -1)
JS=$(ls "$D/assets/index-"*.js | head -1)
grep -q "$EXPECTED_PATTERN" "$JS" && echo "OK: $(basename "$D")" || echo "FAIL"
```

- 适用：任何"部署后校验前端产物"的脚本 / 测试 / 人工核对步骤。
- 不适用：纯静态单目录部署（无时间戳轮转，HTTP 校验稳定）——但本项目 SPA 实时部署为时间戳目录，必须走磁盘。

### BR-096-2：验证与重启顺序铁律（Critical）

部署链路必须按固定顺序，且**重启后端后才读磁盘确认**：

```
构建 → 部署到全新时间戳目录 + 写入 .deploy-complete → 杀 :3000 旧进程 → 重启后端 → GET /health 200 → 读磁盘确认最新目录 bundle 完整
```

- 缺失"重启后端"步骤 → 后端仍指向旧 `spaRoot`（启动只解析一次），新产物不生效（扩展 BR-071 重启要求）。
- 缺失"读磁盘确认"且以 HTTP 报告成功 → 实际可能落到半写入 / 旧目录。

## 适用 / 不适用（维度④）

| 适用场景 | 不适用场景 |
|---------|-----------|
| 时间戳轮转式 SPA 实时部署（本项目 `public_live_<ts>`）的产物验证 | 固定单目录部署（无轮转，HTTP 校验稳定） |
| 任何含"自动部署钩子"导致目录高频切换的环境 | 明确无自动部署、部署串行且可阻塞等待完成的环境 |
| 部署后回归验证脚本 / 测试 | 仅校验后端 API 健康（/health），不涉及前端产物 |

## 对应审查 / 测试要点

- 前端：`wiki-frontend-code-review` FR-068（SPA 部署完整性，`.deploy-complete` 门禁）。
- 后端：`wiki-backend-code-review` BR-071（SPA 实时部署解析，`resolveSpaRoot` 选最大时间戳 + 完整性门禁）。
- 测试：`wiki-auto-testing` `spa_live_deploy_check` 新增 `verify_via_disk: true`（替换原两次 HTTP 校验）。

## 参数（来自 config/review-config.md `deploy_verify_disk_backend` 段，零硬编码）

`enabled` / `live_dir_pattern` / `sort_command` / `asset_bundle_glob` / `severity_disk` / `severity_order`。
