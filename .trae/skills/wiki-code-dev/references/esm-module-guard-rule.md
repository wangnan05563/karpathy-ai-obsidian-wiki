# ESM Module Guard Rule

## 触发关键词

ESM, __dirname, __filename, import.meta.url, fileURLToPath, registerRoute, 模块接线, 入口文件, SonarQube, S6606, 静态分析, 三元表达式, ?? 运算符, U+FFFD, 锟斤拷, 编码损坏, UTF-8, git stash, git checkout

## 规则

### CODING-017：ESM 模块下禁止使用 `__dirname` / `__filename`

**严重级别**：critical

ESM 模块下（`package.json` 含 `"type": "module"` 或 `.mts` / `.ts` 由 ESM loader 解析），禁止以任何形式引用 `forbidden_globals` 列表中的全局变量（默认 `__dirname` / `__filename`）。需要当前模块所在目录时，必须使用 `dirname_derive_pattern`（来自 `config.esm.dirname_derive_pattern`）派生，并确保 `required_imports`（来自 `config.esm.required_imports`）已正确导入。

**为什么**：Node.js ESM 模式下不注入 CommonJS 全局变量。引用 `__dirname` / `__filename` 时直接抛 `ReferenceError: __dirname is not defined`（注意：是抛错而非返回 `undefined`），导致 `?? ` / `|| ` 等短路运算符无法兜底——左操作数在求值阶段就已经抛错，短路逻辑根本不会被执行。 SonarQube S6606 等静态分析工具建议把 `typeof __dirname !== 'undefined' ? __dirname : fallback` 简化为 `__dirname ?? fallback`，这一"修复"会引入运行时 ReferenceError，是典型的静态分析回归（见 CODING-018）。

**正确模板**（参数来自 `config.esm`）：

```typescript
// ✅ ESM 标准派生方式（dirname_derive_pattern）
// required_imports 必须先于使用导入
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// <来自 config.esm.dirname_derive_pattern>
const dirname = path.dirname(fileURLToPath(import.meta.url));
```

**错误示例**：

```typescript
// ❌ 直接引用 __dirname：ESM 模式下抛 ReferenceError
const dirname = __dirname;

// ❌ 用 ?? 兜底：左操作数抛错，?? 不会被执行
const dirname = __dirname ?? path.dirname(fileURLToPath(import.meta.url));

// ❌ 用 typeof 守卫：仍然引用了 __dirname，TS 类型系统不报错但运行时抛错
const dirname = typeof __dirname !== 'undefined'
  ? __dirname
  : path.dirname(fileURLToPath(import.meta.url));
```

> **例外：SEA 可执行检测（本规则唯一合法用途）**。本规则禁止的是"为获取目录而引用 `__filename`/`__dirname`"。但**检测当前是否处于 SEA（Single Executable Application）打包模式**是 `__filename` 的唯一合法用途，且必须用 `declare const` + `typeof` 守卫保证安全（见实战 `api/src/utils/runtime.ts`）：
> ```typescript
> declare const __filename: string | undefined; // 类型层声明：开发 ESM 运行时值 = undefined，SEA CJS = bundle 路径
> const cjsFilename = typeof __filename === 'undefined' ? undefined : __filename; // ✅ typeof 对未声明变量不抛错，配合 declare 双模式安全
> export const IS_SEA = Boolean(cjsFilename === process.execPath || (cjsFilename && !fs.existsSync(cjsFilename)));
> ```
> 之所以安全：① `declare const` 让 TS 知晓该标识符，避免"真未声明"导致的运行时 `ReferenceError`；② `typeof` 对未声明变量返回 `'undefined'`（不会抛错），而 SEA CJS 下 `__filename` 真实存在、值为 bundle 路径。此用法**不**用于目录派生（目录仍走 `import.meta.url` 派生），仅用于模式判别，可豁免本规则。

**检测方式**：使用 Grep 工具搜索 `__dirname` / `__filename` 在 `.ts` / `.mts` / `.js` / `.mjs` 文件中的引用，命中的全部为违规。

```powershell
# Grep 工具模式：pattern = "__dirname|__filename"，glob = "*.{ts,mts,js,mjs}"
```

---

### CODING-018：静态分析建议必须人工验证运行时语义

**严重级别**：critical

`static_analysis_tools` 列表（来自 `config.esm.static_analysis_tools`，默认 SonarQube / ESLint）产出的修复建议，在合入代码前必须按 `manual_verification_checklist`（来自 `config.esm.manual_verification_checklist`）逐项人工验证运行时语义。禁止盲目采纳"语义等价"的自动修复。

**为什么**：静态分析工具基于语法/类型层面判断"可简化"，但语法等价不等于运行时等价。典型反例：SonarQube S6606 建议 `typeof x !== 'undefined' ? x : fallback` → `x ?? fallback`，在 `x` 是 ESM 全局变量（如 `__dirname`）时，原写法的 `typeof` 守卫不会触发 ReferenceError（`typeof` 对未声明变量返回 `'undefined'`），而简化后的 `x ?? fallback` 在求值左操作数 `x` 时直接抛 ReferenceError，短路逻辑失效。同类陷阱还包括：类型守卫被绕过、副作用顺序变化、`this` 绑定改变等。

**检查清单模板**（每条静态分析建议必须逐项验证，项目清单来自 `config.esm.manual_verification_checklist`）：

```
□ operand_throws_on_reference     操作数在引用时是否可能抛错（未声明全局、getter 抛错等）？
□ type_guard_bypassed             原写法的类型守卫（typeof / instanceof / in）是否被简化绕过？
□ side_effect_changed             副作用顺序/次数是否变化（短路 vs 非短路、赋值副作用等）？
```

**正确流程**：

```
SonarQube / ESLint 给出建议
   ↓
逐项过 manual_verification_checklist
   ↓
任一项不通过 → 拒绝采纳，标记 false positive
   ↓
全部通过 → 采纳修改，并在 commit message 注明验证结论
```

**错误示例**：

```typescript
// ❌ 原代码：typeof 守卫不会抛错
const dirname = typeof __dirname !== 'undefined'
  ? __dirname
  : path.dirname(fileURLToPath(import.meta.url));

// ❌ 盲目采纳 SonarQube S6606 建议：__dirname 求值时直接抛 ReferenceError
const dirname = __dirname ?? path.dirname(fileURLToPath(import.meta.url));
```

**适用**：所有 `static_analysis_tools` 列表工具产出的修复建议，无论规则编号（S6606 / no-unused-vars / ...）。

---

### CODING-019：新增模块必须完成接线三步骤

**严重级别**：critical

新增 routes / workflows / services 等可被入口加载的模块时，必须在 `wiring_entry_file`（来自 `config.esm.wiring_entry_file`，默认 `src/index.ts`）中完成 `wiring_required_steps`（来自 `config.esm.wiring_required_steps`）的全部三步：① `import` 语句 ② `instantiate` 实例化（如需） ③ `registerRoute` 注册调用。任一步骤遗漏将导致 API 404 或模块不被加载。

**为什么**：分层架构中 routes 模块只暴露 `registerXxxRoute(app, service)` 工厂函数，必须由入口文件主动调用才会生效。开发者常在新增 `routes/xxx.ts` 后忘记在 `index.ts` 接线，导致代码已存在但 API 返回 404，类型检查（`tsc --noEmit`）也无法捕获此类遗漏（因为模块本身合法，只是没被引用）。Tunnel API 在本次复盘中发生两次同类遗漏。

**接线检查清单模板**（步骤清单来自 `config.esm.wiring_required_steps`）：

```
□ import            在 wiring_entry_file 中 import { registerXxxRoute } from './routes/xxx.js'
□ instantiate       在 wiring_entry_file 中实例化依赖（如 const xxxService = new XxxService();）
□ registerRoute     在 wiring_entry_file 中调用 registerXxxRoute(app, xxxService)
```

**正确模板**：

```typescript
// wiring_entry_file（默认 src/index.ts）中新增三步
import { registerTunnelRoute } from './routes/tunnel.js';        // ① import
import { TunnelService } from './services/tunnel-service.js';    // ① import 依赖

const tunnelService = new TunnelService();                       // ② instantiate
registerTunnelRoute(app, tunnelService);                         // ③ registerRoute
```

**错误示例**：

```typescript
// ❌ 只新增了 routes/tunnel.ts，但 index.ts 未做接线
// 结果：curl /api/tunnel → 404，tsc 不报错
```

**检测方式**：新增模块后，使用 Grep 工具搜索其导出函数名（如 `registerTunnelRoute`）是否在 `wiring_entry_file` 中被调用：

```powershell
# Grep 工具模式：pattern = "registerTunnelRoute", path = wiring_entry_file
# 期望：至少 1 次 import + 至少 1 次调用
```

---

### CODING-020：Edit / Write 后必须验证文件编码未损坏

**严重级别**：critical

使用 Edit / Write 工具修改含非 ASCII 字符（中文 / 日文 / 韩文 / Emoji 等）的文件后，必须立即按 `encoding_verification_method`（来自 `config.esm.encoding_verification_method`）验证文件编码未损坏。检测失败时按 `encoding_failure_recovery`（来自 `config.esm.encoding_failure_recovery`）的步骤从 git 恢复后重新编辑。

**为什么**：Edit / Write 工具在某些情况下会用系统默认编码（Windows 中文环境为 GBK）写回，UTF-8 文件被 GBK 解码再写回会产生不可逆的 U+FFFD 替换字符（俗称"锟斤拷"乱码）。Vite / esbuild 按 UTF-8 读取源文件时无报错，但 UI 显示乱码，运行时无堆栈可追，定位成本极高。本次复盘中 Config.vue / Tunnel.vue / config.ts 三个文件均出现 U+FFFD，类型检查与编译均不报错，仅人工目视或 Playwright 截图能发现。

**验证模板**（PowerShell，方法名来自 `config.esm.encoding_verification_method`）：

```powershell
# encoding_verification_method = "UTF8Encoding(false, true) strict decode"
# 第一参数 emitBOM=false（无 BOM），第二参数 throwOnInvalidBytes=true（严格）
function Test-FileUtf8Strict {
  param([string]$Path)
  $bytes = [System.IO.File]::ReadAllBytes($Path)
  try {
    $enc = New-Object System.Text.UTF8Encoding($false, $true)
    [void]$enc.GetString($bytes)
    return $true
  } catch {
    return $false
  }
}

# Edit 后立即验证
if (-not (Test-FileUtf8Strict $editedPath)) {
  Write-Error "编码损坏：$editedPath 出现非 UTF-8 字节，按 encoding_failure_recovery 恢复"
}
```

**失败恢复模板**（步骤来自 `config.esm.encoding_failure_recovery`，按顺序执行）：

```powershell
# encoding_failure_recovery 步骤：
#   1. git stash           暂存当前所有修改
#   2. git checkout HEAD -- <files>   从 HEAD 恢复损坏文件
#   3. git stash pop       恢复其他未损坏修改
#   4. re-edit             重新用 Edit / Write 工具编辑目标文件
#   5. re-verify           复检编码

# 1. 暂存当前修改
git stash

# 2. 从 HEAD 恢复损坏文件（path1 path2 ... 为损坏文件列表）
git checkout HEAD -- path1 path2

# 3. 恢复其他未损坏修改
git stash pop

# 4-5. 重新 Edit 后立即复检 Test-FileUtf8Strict
```

**适用**：所有含非 ASCII 字符的文件（`.vue` / `.ts` / `.tsx` / `.json` / `.md` / `.css` 等），无论用 Edit / Write / PowerShell 哪种方式修改。

## 检测流程

```
┌─────────────────────────────────────────────────────────┐
│  开发阶段触发                                            │
└──────────┬──────────────────────────────────────────────┘
           │
           ├──────────────────────┐
           ▼                      ▼
┌──────────────────┐    ┌──────────────────────────┐
│ 新增 / 修改 .ts  │    │ 接收 SonarQube/ESLint 建议│
└────────┬─────────┘    └────────────┬─────────────┘
         ▼                           ▼
┌──────────────────┐    ┌──────────────────────────┐
│ CODING-017       │    │ CODING-018               │
│ Grep __dirname / │    │ manual_verification_     │
│ __filename       │    │ checklist 三项验证        │
└────────┬─────────┘    └────────────┬─────────────┘
         │ 命中 = 违规                │ 任一项不通过 = 拒绝采纳
         ▼                           ▼
┌──────────────────────────────────────────────────────┐
│  改用 dirname_derive_pattern + required_imports       │
└──────────────────────────────────────────────────────┘

           │
           ▼
┌──────────────────────────────────────────┐
│  新增 routes/workflows/services 模块      │
└────────────────┬─────────────────────────┘
                 ▼
┌──────────────────────────────────────────┐
│ CODING-019：在 wiring_entry_file 完成三步│
│   ① import  ② instantiate  ③ registerRoute│
└────────────────┬─────────────────────────┘
                 ▼
┌──────────────────────────────────────────┐
│ Grep 导出函数名是否在入口被调用           │
└────────────────┬─────────────────────────┘
                 │ 任一步遗漏 = 修复后复检
                 ▼
┌──────────────────────────────────────────┐
│  Edit / Write 修改含非 ASCII 字符文件     │
└────────────────┬─────────────────────────┘
                 ▼
┌──────────────────────────────────────────┐
│ CODING-020：encoding_verification_method │
│   UTF8Encoding(false, true) 严格解码检测  │
└────────────────┬─────────────────────────┘
                 │ 失败
                 ▼
┌──────────────────────────────────────────┐
│ encoding_failure_recovery 五步恢复流程   │
│   stash → checkout HEAD → stash pop →    │
│   re-edit → re-verify                    │
└──────────────────────────────────────────┘
```

## 适用场景

- Node.js ESM 项目（`package.json` 含 `"type": "module"` 或 `.mts` / `.mjs` / `.ts` 由 tsx / ts-node ESM loader 解析）
- 使用 Fastify / Express 等 Web 框架，路由由入口文件 registerXxxRoute 模式加载的项目
- 引入 SonarQube / ESLint 等静态分析工具并启用自动修复建议的项目
- Windows 中文环境下编辑含中文/日文/韩文/Emoji 的源文件、文档、配置
- TypeScript strict 模式下需要运行时与静态分析联合验证的场景

## 不适用场景

- CommonJS 项目（`require` / `module.exports`，`__dirname` / `__filename` 由运行时正常注入）
- Linux/macOS 原生 UTF-8 环境，且未启用静态分析自动修复
- 单文件脚本（无入口文件、无路由注册步骤）
- 纯 ASCII 内容文件（无中文/Emoji，编码损坏无可见症状，但仍是潜在风险）
- 已通过 CI 强制 ESM / 编码 / 静态分析门禁的项目（CI 兜底，本地可省略部分步骤）

## 检查清单

- [ ] ESM 项目中是否还有 `__dirname` / `__filename` 引用（Grep `__dirname|__filename`）
- [ ] 派生目录是否使用 `dirname_derive_pattern`（`path.dirname(fileURLToPath(import.meta.url))`）
- [ ] `required_imports`（`path` / `fileURLToPath`）是否在派生之前导入
- [ ] SonarQube / ESLint 修复建议是否逐项过 `manual_verification_checklist` 三项验证
- [ ] 是否有"盲目采纳 S6606 / no-extra-boolean-cast 等简化建议"的提交
- [ ] 新增 routes / workflows / services 模块是否在 `wiring_entry_file` 完成 `wiring_required_steps` 三步
- [ ] 新增模块的导出函数名是否在入口文件被调用（Grep 验证）
- [ ] Edit / Write 修改含非 ASCII 字符文件后是否立即按 `encoding_verification_method` 验证编码
- [ ] 编码验证失败时是否按 `encoding_failure_recovery` 五步恢复（git stash → checkout HEAD → stash pop → re-edit → re-verify）
- [ ] 复检通过后才进入构建 / 类型检查 / 提交环节
