# Deploy Marker Verify Rule（部署产物关键特征串校验，防被后续构建覆盖）

## 触发关键词

部署, deploy, 移动端, 特征串, marker, bundle, index-*.js, 覆盖, 覆盖危机,
public_live_, 构建轮转, 移动端标记, 关键功能, 产物校验, 切流

## 规则

### DM-1：部署前/部署后须校验产物含关键功能特征串，防被不含该功能的后续构建覆盖

**严重级别**：critical

单端口 SPA+API 同体应用（`resolveSpaRoot` 按时间戳选最新 `public_live_<ts>` 目录）存在
**覆盖危机**：一旦后续某次构建漏掉某项关键功能（如移动端），新的时间戳目录会「顶掉」旧目录成为线上版本，
而源码始终完好——表现为「源码有、线上没有」。必须在部署切流前校验产物 bundle 含关键特征串。

**为什么**：真实事故——移动端功能在 `public_live_1786298894713` 部署后，磁盘出现 4 次**不含移动端**的构建，
`resolveSpaRoot` 按时间戳选最新 → 若线上重启会切到不含移动端版本。靠「源码有」无法发现，
必须「读磁盘 bundle 校验特征串」。

**正确示例**（部署校验清单）：

```bash
# 部署后读磁盘最新 public_live_<ts> 的 bundle，grep 关键特征串
LATEST=$(ls -dt api/public_live_* | head -1)
grep -l "MobileListen\|聆听" "$LATEST/assets/index-*.js"   # 移动端标记
grep -l "MobileShell" "$LATEST/assets/index-*.js"
```

> 特征串清单（如 `MobileListen` / `MobileShell` / `聆听`）须来自配置（`marker_strings` 列表），
> 不同项目/阶段的关键功能不同，新增关键功能时只改配置。与 wiki-backend-code-review **BR-096**
> （读磁盘最新目录 + `.deploy-complete` 完整性门禁）、前端 **FR-068**（SPA 部署完整性）互补：
> BR-096 回答「部署是否发生、是否最新」，本规则回答「部署的 bundle 是否真含功能 X」。

### DM-2：关键特征串校验须与「全新时间戳目录 + 重启后端」部署纪律同用

**严重级别**：major

校验只在「写全新时间戳目录（不覆盖式）+ 重启后端伺服新目录」的部署纪律下才有效。
若用覆盖式部署或忘记重启，`resolveSpaRoot` 仍指向旧目录，特征串校验会「看起来通过」却线上未切流。

**正确示例**（门禁顺序，详见 CODING-DEPLOY-VERIFY-DISK / BR-096）：

```
构建 → 全新时间戳目录 + .deploy-complete → 杀 :3000 → 重启后端 → /health 200 → 读磁盘 bundle 校验特征串
```

> 禁止覆盖式写入已伺服目录；时间戳目录 + 重启切流是唯一安全路径（与 **CODING-SPA-LIVE-DEPLOY** 一致）。

## 检查清单

- [ ] 部署切流前是否校验产物 bundle 含关键功能特征串（移动端标记等）
- [ ] 特征串清单是否来自配置（非硬编码），新增关键功能时只改配置
- [ ] 是否采用「全新时间戳目录 + 重启后端」部署纪律（非覆盖式）
- [ ] 是否读磁盘（非两次 HTTP 请求）定位最新目录并校验（规避目录轮转竞态）
- [ ] 校验是否覆盖「部署发生 / 是否最新 / 是否含功能」三层（与 BR-096 / FR-068 协同）
