# 项目目录结构与文件组织审查规则（BR-030~033）

> 复盘来源：P0/P1/P2 目录结构优化复盘发现——源码目录混放运行时数据（`data/vault/`）、构建产物未 `.gitignore` 登记、已跟踪文件未 `git rm --cached`、`config.json` 中 `vaultPath` 默认值指向源码目录、`package.json` 中 `file:../` 协议引用路径未验证、外部工具链（`w64devkit/`）混入源码目录。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"项目目录结构审查参数（project_structure_review）"章节读取，禁止在本规则文件硬编码具体目录名、命令或正则。

## Trigger Keywords
vaultPath, data/vault/, services/api/vault/, .gitignore, git rm --cached, file:../, w64devkit/, dist/, build/, node_modules/, 公共工具链, 运行时数据, 构建产物, package.json, dependencies, devDependencies

## Rules

### BR-030: 目录结构分离审查

- **Severity**: critical
- **Description**: 源码目录（`source_dirs`）中不得混放运行时数据（`runtime_data_dir`，如 `data/vault/`）、构建产物（`build_output_dirs`，如 `dist/`、`build/`）以及外部工具链（`external_toolchain_dirs`，如 `w64devkit/`）。混放会导致：（1）运行时写入污染源码目录，IDE 索引抖动；（2）构建产物被误提交到版本控制；（3）外部工具链膨胀仓库体积且不可跨平台复用。评审时须按 `source_dirs` 列举的源码目录，检查其下是否存在匹配 `runtime_data_dir` / `build_output_dirs` / `external_toolchain_dirs` 的子目录或文件。
- **Suggested fix**:
```typescript
// 错误：运行时数据写入源码目录
// api/src/vault/file-state-store.ts
const STATE_DIR = path.join(__dirname, '..', 'vault-data'); // ❌ 源码目录内
await fs.writeFile(path.join(STATE_DIR, 'run-state.json'), data);

// 正确：运行时数据外迁到 data/ 目录，路径从 config 读取
// api/src/vault/file-state-store.ts
import { getRuntimeDataDir } from '../config/paths.js';
const STATE_DIR = getRuntimeDataDir(); // ✅ 从 config 解析到 data/vault-state/
await fs.writeFile(path.join(STATE_DIR, 'run-state.json'), data);

// 错误：外部工具链 w64devkit/ 直接放在项目根
// 项目根/w64devkit/x86_64-w64-mingw32/...  ❌

// 正确：外部工具链通过 .gitignore 排除或放到项目外
// .gitignore
// w64devkit/   # 本地工具链，不入库
```

### BR-031: .gitignore 完整性审查

- **Severity**: critical
- **Description**: 运行时产物（`runtime_data_ignore`，如 `data/`、`*.log`）和构建产物（`build_output_ignore`，如 `dist/`、`build/`）必须在 `.gitignore` 中登记排除规则；若文件已被 git 跟踪（tracked），仅添加 `.gitignore` 规则不足以移除——必须执行 `git rm --cached <path>` 将其从索引中移除后再提交。评审时按 `verification_command`（如 `git check-ignore -v <path>`）验证规则是否生效，按 `tracked_check_command`（如 `git ls-files <path>`）检查已跟踪文件是否需 `git rm --cached`。
- **Suggested fix**:
```typescript
// 错误：data/vault/ 已被跟踪，仅添加 .gitignore 无效
// git status 仍显示 data/vault/run-state.json 已跟踪
// .gitignore
// data/vault/   # ❌ 规则对已跟踪文件无效

// 正确：先 git rm --cached 移除索引，再 .gitignore 持久化排除
// 步骤 1：移除索引（保留本地文件）
// git rm -r --cached data/vault/
// 步骤 2：.gitignore 登记排除规则
// .gitignore
// data/vault/        # 运行时数据
// data/conversations/ # 历史会话
// *.log              # 运行日志

// 验证：规则生效 + 文件不再被跟踪
// git check-ignore -v data/vault/run-state.json  # 输出匹配的 .gitignore 行
// git ls-files data/vault/                        # 应为空
```

### BR-032: 运行时数据外迁审查

- **Severity**: suggestion
- **Description**: 配置文件（`config_files_to_check`，如 `api/config.json`、`config/default.json`）中 `vaultpath_config_field`（如 `vaultPath`）字段的默认值不得指向源码目录（`source_dirs` 中的任一目录），否则运行时写入会污染源码目录。运行时数据（如 vault 状态、会话历史、缓存）应统一外迁到 `runtime_data_patterns`（如 `data/`）约定的目录下。评审时须读取 `config_files_to_check` 中所有配置文件，提取 `vaultpath_config_field` 字段值，检查是否落在 `source_dirs` 范围内。
- **Suggested fix**:
```typescript
// 错误：config.json 中 vaultPath 默认值指向源码目录
// api/config.json
{
  "vault": {
    "vaultPath": "./api/src/vault-data"  // ❌ 源码目录内
  }
}

// 正确：vaultPath 指向 data/ 下的运行时目录
// api/config.json
{
  "vault": {
    "vaultPath": "./data/vault"  // ✅ 运行时数据目录
  }
}

// 路径解析逻辑也应从 config 读取，禁止硬编码源码目录
// api/src/vault/vault-path.ts
import { loadConfig } from '../config/loader.js';
const config = await loadConfig();
const vaultPath = path.resolve(process.cwd(), config.vault.vaultPath);
// 验证：vaultPath 不得落在 source_dirs 任一目录内
const sourceDirs = config.review.source_dirs; // 从 config 读取
if (sourceDirs.some(dir => vaultPath.startsWith(path.resolve(dir)))) {
  throw new Error('vaultPath 不得指向源码目录，请配置到 data/ 下');
}
```

### BR-033: file: 协议路径验证审查

- **Severity**: suggestion
- **Description**: `package.json`（`package_json_files`，如根目录 `package.json`、`api/package.json`、`frontend/package.json`）中 `file:../` 协议引用（`file_protocol_pattern`，如 `"file:../shared"`）必须经过路径存在性验证——被引用路径必须实际存在且可解析。未验证的 `file:` 引用会导致 `npm install` / `pnpm install` 在不同环境下失败（如 CI 环境、新克隆仓库）。评审时按 `verify_command`（如 `npm ls <pkg>` 或 `node -e "require('fs').existsSync('<path>')"`）验证所有 `file:` 引用路径。
- **Suggested fix**:
```typescript
// 错误：package.json 中 file: 引用未验证，路径不存在
// api/package.json
{
  "dependencies": {
    "shared": "file:../shared"  // ❌ ../shared 目录不存在
  }
}

// 正确：先验证路径存在，再使用 file: 引用
// 步骤 1：创建被引用目录或修正路径
// mkdir -p ../shared && cd ../shared && npm init -y
// 步骤 2：package.json 使用已验证的 file: 引用
// api/package.json
{
  "dependencies": {
    "shared": "file:../shared"  // ✅ 路径已验证存在
  }
}

// 验证脚本（可加入 preinstall 或 CI 检查）
// scripts/verify-file-refs.js
import fs from 'node:fs';
import path from 'node:path';
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const deps = { ...pkg.dependencies, ...pkg.devDependencies };
for (const [name, ref] of Object.entries(deps)) {
  if (ref.startsWith('file:')) {
    const target = path.resolve(ref.slice(5));
    if (!fs.existsSync(target)) {
      console.error(`✗ file: 引用 ${name} 路径不存在: ${target}`);
      process.exit(1);
    }
    console.log(`✓ file: 引用 ${name} 路径有效: ${target}`);
  }
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `project_structure_review.enabled` | `true` | 是否启用本组规则 |
| `project_structure_review.source_dirs` | `api/src/,frontend/src/,scripts/` | 源码目录列表（逗号分隔，相对项目根） |
| `project_structure_review.runtime_data_dir` | `data/` | 运行时数据统一存放目录（相对项目根） |
| `project_structure_review.build_output_dirs` | `dist/,build/` | 构建产物目录列表（逗号分隔） |
| `project_structure_review.external_toolchain_dirs` | `w64devkit/` | 外部工具链目录列表（逗号分隔） |
| `project_structure_review.runtime_data_ignore` | `data/,*.log` | 须在 .gitignore 登记的运行时数据规则（逗号分隔） |
| `project_structure_review.build_output_ignore` | `dist/,build/` | 须在 .gitignore 登记的构建产物规则（逗号分隔） |
| `project_structure_review.verification_command` | `git check-ignore -v <path>` | 验证 .gitignore 规则是否生效的命令 |
| `project_structure_review.tracked_check_command` | `git ls-files <path>` | 检查文件是否被 git 跟踪的命令 |
| `project_structure_review.vaultpath_config_field` | `vaultPath` | 配置文件中 vaultPath 字段名 |
| `project_structure_review.config_files_to_check` | `api/config.json,config/default.json` | 须检查 vaultPath 的配置文件列表（逗号分隔） |
| `project_structure_review.runtime_data_patterns` | `data/` | 运行时数据应外迁到的目录模式（逗号分隔） |
| `project_structure_review.file_protocol_pattern` | `file:` | package.json 中本地路径引用的协议前缀 |
| `project_structure_review.verify_command` | `npm ls <pkg>` | 验证 file: 引用路径有效性的命令 |
| `project_structure_review.package_json_files` | `package.json,api/package.json,frontend/package.json` | 须检查 file: 引用的 package.json 文件列表（逗号分隔） |

## 检查方式

1. **BR-030 目录结构分离**：
   - 用 Grep / Glob 扫描 `source_dirs` 中每个目录，检查是否存在匹配 `runtime_data_dir` / `build_output_dirs` / `external_toolchain_dirs` 的子目录或文件。
   - 用 Grep 检索源码文件中硬编码的路径字符串，确认未指向运行时数据目录或构建产物目录。
2. **BR-031 .gitignore 完整性**：
   - 用 Read 读取项目根 `.gitignore`，检查 `runtime_data_ignore` 与 `build_output_ignore` 中的规则是否已登记。
   - 对每条规则，用 `verification_command` 验证规则对目标路径生效。
   - 用 `tracked_check_command` 检查 `runtime_data_dir` / `build_output_dirs` 下是否存在已跟踪文件——存在则需 `git rm --cached`。
3. **BR-032 运行时数据外迁**：
   - 用 Read 读取 `config_files_to_check` 中每个配置文件，提取 `vaultpath_config_field` 字段值。
   - 检查字段值是否落在 `source_dirs` 任一目录范围内（用 `path.resolve` 解析后 `startsWith` 检查）。
   - 检查运行时数据写入路径是否落在 `runtime_data_patterns` 约定的目录下。
4. **BR-033 file: 协议路径验证**：
   - 用 Read 读取 `package_json_files` 中每个 `package.json`，提取 `dependencies` / `devDependencies` 中匹配 `file_protocol_pattern` 的引用。
   - 对每个 `file:` 引用，用 `verify_command` 或 `fs.existsSync` 验证路径是否存在。
   - 若路径不存在，标记为 BR-033 违规。

## 正确示例

```typescript
// 1. 项目目录结构（源码 / 运行时数据 / 构建产物 分离）
// project-root/
// ├── api/src/           # 源码目录（BR-030）
// ├── frontend/src/      # 源码目录
// ├── data/              # 运行时数据目录（BR-032）
// │   ├── vault/         # vaultPath 默认值
// │   └── conversations/
// ├── dist/              # 构建产物目录（BR-031，.gitignore 登记）
// └── .gitignore

// 2. .gitignore 完整登记（BR-031）
// .gitignore
// node_modules/
// dist/                  # 构建产物
// build/
// data/                  # 运行时数据
// *.log
// w64devkit/             # 外部工具链

// 3. config.json vaultPath 指向 data/（BR-032）
// api/config.json
{
  "vault": {
    "vaultPath": "./data/vault"  // ✅ 运行时数据目录
  }
}

// 4. package.json file: 引用路径已验证（BR-033）
// api/package.json
{
  "dependencies": {
    "shared": "file:../shared"  // ✅ ../shared 目录已存在
  }
}
```

## 错误示例

```typescript
// 错误 1：运行时数据写入源码目录（BR-030）
// api/src/vault/file-state-store.ts
const STATE_DIR = path.join(__dirname, 'vault-data'); // ❌ 源码目录内
await fs.writeFile(path.join(STATE_DIR, 'run-state.json'), data);

// 错误 2：构建产物 dist/ 未在 .gitignore 登记（BR-031）
// .gitignore
// node_modules/
// // ❌ 缺 dist/ 和 data/

// 错误 3：data/vault/ 已跟踪但仅添加 .gitignore（BR-031）
// git ls-files data/vault/  仍返回文件列表
// ❌ 需先 git rm -r --cached data/vault/

// 错误 4：vaultPath 默认值指向源码目录（BR-032）
// api/config.json
{
  "vault": {
    "vaultPath": "./api/src/vault-data"  // ❌ 源码目录内
  }
}

// 错误 5：file: 引用路径不存在（BR-033）
// api/package.json
{
  "dependencies": {
    "shared": "file:../shared"  // ❌ ../shared 目录不存在
  }
}
// npm install 时报错：npm ERR! ENOENT: no such file or directory

// 错误 6：外部工具链混入源码目录（BR-030）
// project-root/w64devkit/x86_64-w64-mingw32/bin/gcc.exe  // ❌ 工具链入库
```

## 适配新项目

- **Monorepo 项目**：`source_dirs` 调整为 `packages/*/src/,apps/*/src/`，`runtime_data_dir` 调整为 `packages/*/data/` 或统一 `data/`，`package_json_files` 调整为 `package.json,packages/*/package.json`。
- **Express 项目**：`source_dirs` 改为 `src/`，`config_files_to_check` 改为 `config/default.json,.env`，`vaultpath_config_field` 按项目实际字段名调整（如 `dataDir`）。
- **NestJS 项目**：`source_dirs` 改为 `src/`，`build_output_dirs` 改为 `dist/`，`config_files_to_check` 按项目配置文件实际路径调整。
- **非 Node.js 项目**：`file_protocol_pattern` 改为对应包管理器的本地路径引用格式（如 Python 的 `-e ./local-pkg`），`verify_command` 改为 `pip show <pkg>` 或 `python -c "import os; os.path.exists('<path>')"`。
- **CI/CD 环境**：将 BR-031 与 BR-033 的验证命令集成到 CI pipeline 的 pre-check 阶段，在 `npm install` / `git commit` 前自动校验。
