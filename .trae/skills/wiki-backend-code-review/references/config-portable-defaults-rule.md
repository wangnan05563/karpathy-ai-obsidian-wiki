# 配置可移植默认审查规则（BR-066）

> 复盘来源：SEA / 多机场景下，配置中把 `dataDir` / `stateDir` 写成机器绝对路径（如 `C:\Users\xxx\...` 或 `/home/xxx/...`），并依赖 `vaultPath` 推导数据目录。结果：(1) 配置在不同机器间不可移植，换机即失效；(2) 首次持久化把机器绝对路径写进 `config.json`，该文件被提交后泄露用户目录结构。正确做法：数据目录从稳定的"用户数据目录"（与 vault 无关）推导，首次持久化只写相对 / 可重派生路径，绝不提交机器绝对路径。本规则扩展 BR-035 的路径解析三级策略。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"配置可移植默认审查参数（config_portable_defaults）"章节读取。

## Trigger Keywords

dataDir, stateDir, userData, user-data dir, appData, vaultPath, 可移植, portable defaults, 相对路径, relative path, 机器绝对路径, machine-absolute, SEA, 多机, multi-machine, 首次持久化, first persist, re-derive, 重派生, config.json, 提交

## Rules

### BR-066-1：dataDir/stateDir 须从稳定的用户数据目录推导，独立于 vaultPath

- **Severity**: critical
- **Description**: 数据与状态目录必须基于"稳定的用户数据目录"（如 OS 提供的 appData / 用户主目录下的固定子目录）推导，不得依赖 `vaultPath`（vault 位置可变、且属于用户内容而非应用数据）。这样换 vault、换机器时应用数据仍可定位。评审时确认：`getStateDir()` / `getDataDir()` 的实现基于用户数据目录锚点（如 `os.homedir()` + 固定子路径，或注入的 `userDataDir`），而非 `vaultPath` 拼接。
- **Suggested fix**:

```typescript
// 错误：数据目录依赖 vaultPath，换 vault 即丢失/错位
function getStateDir() {
  return path.join(config.vaultPath, '.wiki-state'); // ❌ 随 vault 移动
}

// 正确：基于稳定的用户数据目录
function getStateDir() {
  const base = config.userDataDir ?? path.join(os.homedir(), '.karpathy-wiki');
  return path.join(base, 'state'); // ✅ 独立于 vaultPath
}
```

### BR-066-2：首次持久化须写可移植默认（相对 / 可重派生），禁止提交机器绝对路径

- **Severity**: critical
- **Description**: 应用首次写入 `config.json`（或其他持久化文件）时，凡涉及目录的字段必须写"相对路径"或"运行时可重派生的锚点标识"，绝对禁止写入机器绝对路径（如 `C:\Users\...\` / `/home/...\`）。被提交的配置文件若含绝对路径，换机即失效且泄露目录结构。评审时确认：首次 persist 的路径字段为相对 / 锚点形式；写入逻辑有责任在保存前把绝对路径归一化为可移植形式。
- **Suggested fix**:

```typescript
// 错误：首次写入机器绝对路径
config.dataDir = '/home/alice/.karpathy-wiki/data'; // ❌ 提交后换机失效 + 泄露目录
await writeConfig(config);

// 正确：写相对/可重派生锚点，运行时再展开
config.dataDir = '${userDataDir}/data'; // 或存 'data' 相对标识
// 读取时：resolveUserDataDir(config.dataDir)
await writeConfig(config);
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `config_portable_defaults.enabled` | `true` | 是否启用本组规则（BR-066） |
| `config_portable_defaults.severity_br066_1` | `critical` | BR-066-1 依赖 vaultPath 推导违规级别 |
| `config_portable_defaults.severity_br066_2` | `critical` | BR-066-2 写机器绝对路径违规级别 |
| `config_portable_defaults.user_data_dir_anchor` | `os.homedir()/.karpathy-wiki` | 用户数据目录锚点 |
| `config_portable_defaults.forbidden_absolute_prefixes` | `C:\Users\,/home/,/Users/,/root/` | 禁止写入的绝对路径前缀 |
| `config_portable_defaults.portable_token` | `${userDataDir}` | 可重派生锚点占位符 |

## 检查方式

1. **目录推导检查**：Grep `getStateDir` / `getDataDir` / `vaultPath` 拼接，确认数据目录不基于 `vaultPath` 推导；基于 `vaultPath` → **BR-066-1 违规**。
2. **绝对路径写入检查**：Grep 首次 `writeConfig` / `saveConfig` 处涉及路径字段的赋值，确认无 `forbidden_absolute_prefixes` 命中；写入机器绝对路径 → **BR-066-2 违规**。

## 与其他规则的关系

- 与 BR-035（路径解析三级策略）联动：本规则是其"可移植性"维度的强化（数据目录须稳定可重派生）。
- 与 BR-065（运行时数据隐私）联动：可移植默认避免提交机器绝对路径泄露目录结构。
- 与 BR-037（跨 origin 持久化边界）联动：数据目录解析是持久化边界的前置。
- 与 CODING-CONFIG-PORTABLE（配置可移植默认 / 多机）对应：本规则是 CODING-CONFIG-PORTABLE 的后端审查视角。
