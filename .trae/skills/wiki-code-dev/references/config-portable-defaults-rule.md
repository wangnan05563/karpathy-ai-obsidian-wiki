# 配置可移植默认值规则（多机 / SEA 打包）

**代码**：CODING-CONFIG-PORTABLE
**严重级别**：critical

## 问题（Problem）

打包（SEA）应用把**机器绝对路径**（vaultPath、auth.*、日志路径）写进了 `config.json`，并且从 `vaultPath` 派生 `dataDir`。后果：换机器后路径失效；若用户自定义 vault，`dataDir` 被迁移到磁盘根目录，会话存储位置随 vault 漂移。

## 规则（Rule）

### R-1：`dataDir` / `stateDir` 必须基于稳定用户数据目录，独立于 `vaultPath`
通过 `getUserDataDir()`（或等效的 OS 用户数据目录）派生状态目录，**不要**从 `vaultPath` 派生，避免 vault 自定义导致存储漂移。

### R-2：首次持久化写入"可移植默认值"
首次写入 `config.json` 时，写**相对路径 / 运行时重派生**的默认值，**绝不**硬编码机器绝对路径。`vaultPath`、`auth.*`、日志路径等机器相关项不应作为静态默认值提交。

### R-3：不提交机器绝对路径
仓库中的配置模板/默认值不得包含任何机器绝对路径；机器相关值必须在运行时按当前环境派生。

## 适用 / 不适用

- **适用**：SEA/打包应用、多机部署、`config.json` 持久化、状态目录派生。
- **不适用**：纯前端（无需写 `config.json` 到磁盘）、只读配置消费。

## 检查清单
- [ ] `dataDir`/`stateDir` 是否来自 `getUserDataDir()` 而非 `vaultPath`
- [ ] 首次写入是否使用相对/重派生默认值
- [ ] config 默认值中是否不含机器绝对路径
