# CODING-DEPLOY-VERIFY-DISK — 部署产物验证须读磁盘最新目录而非 HTTP

> 对应后端 BR-096 / 前端 FR-068（SPA 部署完整性）/ wiki-auto-testing `spa_live_deploy_check` 派生参数 `verify_via_disk`。
> 基于「环境存在自动部署钩子，两次 HTTP 请求间部署目录被替换，导致经 HTTP 校验 bundle 404 / 错版本」四维度复盘。

## 问题背景

本项目 SPA 部署采用"每次构建写入全新 `public_live_<ts>` 目录、后端 `resolveSpaRoot` 启动只解析一次"模式
（见 CODING-SPA-LIVE-DEPLOY / BR-071）。本环境还存在**自动部署钩子**：文件变动后会自动 `vite build` +
新建 `public_live_<ts>` + 重启后端，导致"最新部署目录"持续滚动。

后果：两次 HTTP 请求（第一次 GET `/wiki/` 取 index.html、第二次 GET `/wiki/assets/index-xxx.js`）之间，
目录可能已被自动部署钩子替换 → 第二次请求 404 或拿到**不同 bundle**，使"经 HTTP 校验线上 bundle 含修复标记"判定失效。

## 规则（2 条）

### DV-1 验证读磁盘最新目录，避开 HTTP 轮转
确认线上实际伺服的 bundle 时，**直接读磁盘**：
```bash
D=$(ls -dt api/public_live_* | head -1)   # 数值时间戳降序，最新在前
JS=$(ls "$D/assets/index-"*.js | head -1)
grep -c "修复标记文案" "$JS"
```
而非经 `curl http://127.0.0.1:3000/wiki/...` 两次请求（其间目录可能被自动部署钩子替换）。
- 与 BR-071 一致：`resolveSpaRoot` 启动只解析一次，正在服务的就是"当前最新目录"（磁盘 `ls -dt` 结果）。

### DV-2 验证与重启顺序铁律
部署新 `public_live_<ts>` 后**必须重启后端**才生效（BR-071-4）。验证闭环：
构建 → 部署新时间戳目录 → 杀旧 `:3000` 进程 → 后台重启后端 → 轮询 `/health` 200 →
**读磁盘最新目录**确认 bundle 含修复标记（非 HTTP）。

## 适用 / 不适用（维度④）

| 适用场景 | 不适用场景 |
|---------|-----------|
| 采用"时间戳目录 + 后端启动解析一次"部署模式**且**存在自动部署钩子（目录高频轮转）的项目 | 部署目录稳定（无自动部署钩子、无多写手），两次 HTTP 请求间目录不变化 |
| 沙箱 localhost 回环被拦截、HTTP 取大资源易超时/空响应的环境 | 真实机构建机、网络稳定、HTTP 校验可靠 |
| 验证"线上 bundle 是否含某修复标记"的发布后核对 | 仅验证"服务是否起来"（用 `/health` 200 即可，无需读磁盘） |

## 对应审查 / 测试要点

- 后端：`wiki-backend-code-review` BR-096（deploy-verify-disk-rule.md），扩展 BR-071 验证纪律。
- 测试：`wiki-auto-testing` `spa_live_deploy_check` 新增 `verify_via_disk: true` 参数（默认 true），
  校验实现从"HTTP 两次请求"改为"读磁盘最新 `public_live_<ts>` 目录"，规避自动部署钩子轮转导致的 404 / 错版本。
