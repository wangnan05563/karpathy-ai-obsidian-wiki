# 项目目录结构与文件组织规则（CODING-033~040）

> 本规则从 P0/P1/P2 目录结构优化实战复盘中提炼，所有参数从 `config/coding-standards-config.md` 的"项目目录结构参数"章节读取。

## CODING-033：目录结构分离原则

**规则**：项目顶层目录必须按职责分离——源码、运行时数据、构建产物、外部工具链、文档各自独立目录，禁止混放。

**目录约定**（从 config 的 `project_structure` 章节读取）：

| 目录类别 | 路径模板 | 说明 |
|---------|---------|------|
| 源码根 | `packages/` + `services/` | 前端包 + 后端服务 |
| 运行时数据 | `data/vault/` | 运行时生成的数据（raw/entities/queries/log） |
| 构建产物 | `dist/` + `build/` | 编译输出，gitignore |
| 外部工具链 | 不入库 | 由 setup 脚本自动安装，gitignore |
| 文档 | `docs/{requirements,design,plan,dev-guides}/` | 按类型分类 |
| 脚本 | `scripts/` | 构建/启停/校验脚本 |
| IDE 技能 | `.trae/skills/` | TRAE 技能定义 |

**判断逻辑**：
- 新增文件时，先确定其类别（源码/数据/产物/文档/脚本），再放入对应目录
- 运行时生成的数据禁止放在源码目录（如 `services/api/vault/raw/`），必须外迁到 `data/`
- 外部工具链（如 w64devkit）禁止入库，由 setup 脚本自动安装

**反面案例**：`services/api/vault/raw/` 混放运行时数据与源码 → 应迁移到 `data/vault/raw/`

## CODING-034：脚本命名统一原则

**规则**：同一目录下的脚本文件命名风格必须统一，禁止中英文混杂。bat 文件仅作为 ps1 的薄包装（调用入口），复杂逻辑全部在 ps1 中实现。

**命名规范**（从 config 的 `script_naming` 章节读取）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `naming_style` | `kebab-case` | 脚本文件命名风格 |
| `bat_role` | `thin-wrapper` | bat 文件角色（薄包装） |
| `bat_content_pattern` | `@call powershell -File "%~dp0{script}.ps1" %*` | bat 标准内容模板 |
| `language_prefix` | `en` | 命名语言（英文） |

**判断逻辑**：
- 扫描 `scripts/` 目录，若存在中文文件名与非中文文件名混杂，判定为违规
- bat 文件内容超过 5 行（不含注释），判定为"bat 承载过多逻辑"违规
- 同义脚本存在多个命名（如 `启动服务.bat` + `start-service.bat`），判定为重复

**修复方式**：重命名为统一英文 kebab-case + 批量更新所有引用（Grep 搜索旧名 → PowerShell 批量替换 → Grep 验证无残留）

## CODING-035：.gitignore 完整性原则

**规则**：运行时产物、构建产物、外部工具链、二进制 wrapper 必须在 .gitignore 中登记。已跟踪的文件变更 gitignore 后需 `git rm --cached` 移除索引。

**必须 gitignore 的类别**（从 config 的 `gitignore_rules` 章节读取）：

| 类别 | 模式示例 | 说明 |
|------|---------|------|
| 运行时数据 | `data/vault/raw/`, `data/vault/log.md` | 运行时生成的文件 |
| 构建产物 | `dist/`, `build/`, `*.exe` | 编译输出 |
| 外部工具链 | `w64devkit/` | 第三方工具 |
| 二进制 wrapper | `scripts/windres.exe` | 编译生成的二进制 |
| 测试截图 | `test_screenshots/` | 测试运行时产物 |
| 临时结果 | `test_*.json` | 临时测试输出 |

**验证四步法**（固定流程）：
1. 更新 .gitignore 规则
2. `git check-ignore -v <file>` 验证规则匹配
3. `git ls-files --error-unmatch <file>` 检查是否已被跟踪
4. 若已跟踪 → `git rm --cached <file>` 移除索引（非破坏性，磁盘文件保留）

**判断逻辑**：
- 新建落盘目录时，若未同步在 .gitignore 登记排除规则，判定为违规
- .gitignore 规则更新后未执行 `git check-ignore` 验证，判定为流程不完整
- 已跟踪文件变更 gitignore 后未执行 `git rm --cached`，判定为索引未清理

## CODING-036：文档归并原则

**规则**：项目文档必须统一到 `docs/` 目录下，按类型分子目录管理，禁止散落在项目根或源码目录中。

**目录结构**（从 config 的 `docs_structure` 章节读取）：

| 子目录 | 用途 |
|--------|------|
| `docs/requirements/` | 需求规格说明书、评审报告 |
| `docs/design/` | 概要设计、详细设计、评审报告 |
| `docs/plan/` | 实施计划、迭代提示词 |
| `docs/dev-guides/` | 开发规范、编码指南 |

**判断逻辑**：
- 扫描项目根和源码目录，若存在散落的 .md 设计文档，判定为违规
- 开发规范（如 SKILL.md）禁止放在源码目录（如 `services/api/src/.skills/`），必须迁到 `docs/dev-guides/` 或 `.trae/skills/`

## CODING-037：运行时数据外迁原则

**规则**：运行时生成的数据（用户上传、日志、索引、缓存）必须与源码分离，外迁到独立的 `data/` 目录。源码中只保留种子数据和结构契约文件（如 SCHEMA.md）。

**数据分类**（从 config 的 `data_separation` 章节读取）：

| 数据类型 | 存放位置 | 入库 | 说明 |
|---------|---------|------|------|
| 种子数据 | `data/vault/concepts/` | 是 | 初始知识库内容 |
| 结构契约 | `data/vault/SCHEMA.md` | 是 | 数据结构定义 |
| 用户上传 | `data/vault/raw/` | 否 | 运行时摄入 |
| 运行时索引 | `data/vault/entities/` | 否 | 运行时生成 |
| 操作日志 | `data/vault/log.md` | 否 | 运行时追加 |

**判断逻辑**：
- 源码目录（`services/`、`packages/`）中存在运行时写入的文件，判定为违规
- 配置文件中的 `vaultPath` 默认值指向源码目录，判定为违规
- 迁移数据后未更新代码中的默认路径（config.json + config.ts + install.ps1），判定为引用未同步

## CODING-038：file: 协议路径验证原则

**规则**：package.json 中 `file:` 协议引用的路径必须用工具验证解析结果，禁止手动计算 `../` 层级。

**验证方法**：
```powershell
# 验证 file: 引用路径解析
$resolved = (Resolve-Path (Join-Path $packageDir $fileRef)).Path
Test-Path "$resolved\package.json"
```

**判断逻辑**：
- package.json 中 `file:../xxx` 或 `file:../../xxx` 引用，未用 `Resolve-Path` 验证，判定为流程不完整
- 手动计算 `../../../` 层级时漏算一层，导致路径指向错误目录，判定为违规

**反面案例**：`services/api/package.json` 的 `file:../../../wiki-harness` 被手动计算为指向 `otherProjects/`，实际 `Resolve-Path` 验证指向项目根目录。

## CODING-039：搜索结果交叉验证原则

**规则**：使用 Glob/Grep/LS 搜索文件或目录时，任一方法未找到目标时，必须用另一种方法交叉验证，禁止基于单一方法的阴性结果下结论。

**交叉验证矩阵**（从 config 的 `search_verification` 章节读取）：

| 搜索方法 | 适用场景 | 已知局限 |
|---------|---------|---------|
| Glob | 文件名模式匹配 | 路径含特殊字符时可能转义失败 |
| Grep | 文件内容搜索 | 无法搜索未入库的文件 |
| LS | 目录列表 | 输出超长时可能截断（>40000字符） |
| PowerShell `Test-Path` | 精确路径存在性 | 需已知完整路径 |

**判断逻辑**：
- Glob 未找到文件时，未用 Grep 搜索文件内容或 LS 列出父目录交叉验证，判定为流程不完整
- LS 输出被截断时，未用 Glob 或 PowerShell `Test-Path` 补充验证，判定为流程不完整
- 基于单一搜索方法的阴性结果下"文件不存在"结论，判定为违规

**反面案例**：Glob 搜索 `wiki-harness\**` 因路径转义返回空 + LS 输出截断未显示该目录 → 草率下"源码缺失"结论 → 用户质疑后 Grep 搜索 `export class Harness` 找到源码。

## CODING-040：构建产物源码化原则

**规则**：编译生成的二进制 wrapper（如 windres.exe）必须保留源码（.c 文件）入库，二进制产物 gitignore，构建脚本自动从源码编译。

**判断逻辑**：
- scripts/ 目录存在二进制文件（.exe/.dll）但无对应源码（.c/.rs），判定为违规
- 二进制文件已入库但未 gitignore，判定为违规
- setup 脚本中缺少自动编译二进制 wrapper 的步骤，判定为流程不完整

**修复方式**：
1. 保留 `.c` 源码入库
2. `.gitignore` 添加二进制文件规则
3. `git rm --cached` 移除已跟踪的二进制
4. setup 脚本添加编译步骤（如 `gcc -o windres.exe windres-wrapper.c`）
