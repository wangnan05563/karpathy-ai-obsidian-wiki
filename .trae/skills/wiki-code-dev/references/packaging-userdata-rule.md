# 打包用户数据与安装器保护规则（SEA / 多机部署）

**代码**：CODING-PACKAGING-USERDATA
**严重级别**：critical

## 问题（Problem）

打包（SEA / 单一可执行 / 安装器）应用把"可写用户数据"（config.json / .env / vault / data / 日志）与"随版本更新的程序文件"（exe / public / prompts / node_modules）混放，导致三类事故：

1. **安装器覆盖用户配置**：升级时把打包进去的旧 config.json 覆盖用户已修改的配置；或用户数据被安装到 Program Files，普通用户无写权限（"保存配置"静默失败）、卸载被清除。
2. **路径解析错基准**：SEA exe 中 `import.meta.url` 指向构建时 `bundle.cjs`（用户机器不存在），基于它派生的资源路径全部失败；早期代码从 `vaultPath` 派生 `dataDir`，用户自定义 vault 导致会话存储漂移。
3. **机器绝对路径固化进配置**：config.json 写入 `C:\Users\xxx\AppData\Local\KarpathyWiki\data\vault` 这类机器相关绝对路径，换机 / 漫游配置失效。

## 规则（Rule）

### R-1：安装器绝不覆盖用户数据，且用户数据不打包到 `{app}`
- 程序文件（exe / public / prompts / node_modules / llm-presets.json / .env.example / 图标）用 `Flags: ignoreversion`（升级即覆盖，随版本更新）。
- 用户数据（config.json / .env / vault / data）**不**出现在安装器 `[Files]` 段，绝不安装到 `{app}`（Program Files）。
- 由应用在首次运行时自建到按用户隔离的可写目录（普通用户可写、不受卸载影响、多用户互不干扰）。

### R-2：严格区分"资源路径"与"用户数据路径"
- **资源路径**（prompts / llm-presets.json / package.json 等随版本更新）：SEA 模式走 exe 目录（`process.execPath` / `import.meta.url` 经 banner 重定向），开发模式走源码目录向上查找锚点文件（如 `llm-presets.json`）。
- **用户数据路径**（config.json / .env / vault / data / 日志）：一律通过 `getUserDataDir()` 派生，**绝不**基于 `vaultPath` 或 exe 同级派生；`dataDir`/`stateDir` 也须从用户数据目录派生（与 CODING-CONFIG-PORTABLE 一致）。
- `IS_SEA` 标志统一识别打包模式；`getUserDataDir()` 解析为 `LOCALAPPDATA || APPDATA || os.homedir()` + 应用名目录，首次运行 `mkdirSync(recursive)` 自建。

### R-3：首次持久化写"干净默认"，不固化机器绝对路径
- SEA 首次运行落盘 config.json 时，把被 rebase 成机器绝对路径的字段（vaultPath / auth.* / urlCrawl.* / logging.*）回退为相对 / 重派生默认值，保持可移植且单一真相源。
- 尊重用户在配置中**显式指定**的绝对路径（不强制 rebase 用户明确值）；仅对相对路径字段归一化到用户数据目录。

## 适用 / 不适用

- **适用**：SEA / 单一可执行 / Electron / Tauri / Inno Setup 等打包应用；多机部署；config.json 持久化；安装器脚本。
- **不适用**：纯前端（无磁盘 config）；只读配置消费；服务端容器（用 volume 挂载而非 LOCALAPPDATA）。
- 与 CODING-CONFIG-PORTABLE（BR-066）互为补充：本规则聚焦**打包 / 安装器 / 用户数据目录解析与防覆盖**，CONFIG-PORTABLE 覆盖更广义的"dataDir 独立于 vaultPath + 首次写可移植默认"。

## 检查清单
- [ ] 安装器 `[Files]` 是否仅含程序文件且用 `ignoreversion`；用户数据是否未打包到 `{app}`
- [ ] 资源路径 vs 用户数据路径是否经不同函数派生（getApiDir/getResourcePath vs getUserDataDir/getDataDir）
- [ ] `IS_SEA` 是否统一驱动路径分支
- [ ] 首次落盘是否回退机器绝对路径为相对默认
- [ ] 用户显式绝对路径是否被尊重（仅相对路径被 rebase）
- [ ] 用户数据目录是否首次运行自建（mkdirSync recursive）
