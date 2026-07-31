# 开发工作流（四维度复盘提炼）

> ⚠️ **项目特定知识库文档**：本文档含硬编码项目路径与端口（如 `karpathy-wiki/`、`5173`），这些值来源于项目实际复盘沉淀，非配置化参数。通用规则见同目录下其他规则文件。

本文档从四个维度提炼标准化开发工作流。

## 一、成功执行任务的完整步骤

### 标准流程（7 步）

| 步骤 | 动作 | 产出物 |
|---|---|---|
| 1. 需求分析 | 理解需规 V2.2 → 设计文档 V1.3 → 定位对应章节 | 明确的功能边界 |
| 2. 依赖检查 | ls/grep 确认现有代码模式、技术栈版本、目录结构 | 技术决策依据 |
| 3. 设计先行 | 在概要设计说明书中补充对应章节 | 更新后的设计文档 |
| 4. 编码实施 | 按分层架构逐步实现 | 功能代码 |
| 5. 类型验证 | `tsc --noEmit` + `vue-tsc --noEmit` 双重检查 | 类型通过证明 |
| 6. 功能验证 | curl 测试后端路由，手动测试前端交互 | 功能通过证明 |
| 7. 文档同步 | 更新 DELIVERY.md 记录交付清单 | 更新后的交付文档 |

### 详细操作

**步骤 1 - 需求分析**：
- 找到需求对应的章节编号（如 §12.3）
- 确认涉及的前后端层

**步骤 2 - 依赖检查**：
```powershell
# 检查现有路由模式
Get-ChildItem services/api/src/routes/ -Filter "*.ts"

# 检查前端 store 模式
Get-ChildItem packages/web/src/stores/ -Filter "*.ts"
```

**步骤 4 - 编码实施顺序**：
- 后端：routes → workflows → engine → vault
- 前端：types → store → view

## 二、不确定性与失败点

### 1. Write 工具磁盘写入失败

**现象**：Write 报告成功但文件仅 6 字节。

**根因**：Write 工具在某些情况下存在异步写入竞态。

**解决方案**：改用 PowerShell `[System.IO.File]::WriteAllText` 直写。

```powershell
[System.IO.File]::WriteAllText(
  "path\to\file.txt",
  $content,
  [System.Text.UTF8Encoding]::new($false)
)
```

### 2. PowerShell here-string 转义陷阱

**现象**：单引号 here-string 中 `` `n `` 被视为字面量。

**根因**：PowerShell 单引号 here-string 不进行任何转义解析。

**解决方案**：使用 `.Replace()` 修复。

```powershell
$content = @'
line1
line2
'@
$content = $content.Replace("`n", "`r`n")
```

### 3. TypeScript 联合类型窄化失败

**现象**：TS 无法基于独立 discriminant 窄化 `string | {from, to}`。

**根因**：TypeScript 的 control flow analysis 无法跨独立属性推断联合类型。

**解决方案**：使用 `as` 断言或 type guard 函数。

```typescript
// 方案 A：as 断言
const result = data as { from: string; to: string };

// 方案 B：type guard
function isRange(obj: unknown): obj is { from: string; to: string } {
  return typeof obj === 'object' && obj !== null && 'from' in obj && 'to' in obj;
}
```

### 4. 端口占用

**现象**：旧 server 进程未释放 3000 端口。

**解决方案**：
```powershell
# 查找占用进程
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object OwningProcess

# 终止进程
Stop-Process -Id <PID> -Force
```

### 5. PowerShell 只读变量

**现象**：`$pid` 是只读变量，赋值时报错。

**解决方案**：用 `$procId` 或其他变量名替代。

## 三、固定流程

### 1. 设计文档驱动开发

```
需求 → 更新概要设计 → 编码 → 更新 DELIVERY.md
```

### 2. 分层实现顺序

| 层 | 后端 | 前端 |
|---|---|---|
| 入口层 | routes/ | views/ |
| 业务层 | workflows/ | stores/ |
| 引擎层 | engine/ | components/ |
| 数据层 | vault/ | types.ts |

### 3. 验证闭环

```
tsc → vue-tsc → curl → 手动测试
```

### 4. PowerShell 环境适配

- 避免使用 `$pid`、`$PWD`、`$HOME` 等只读变量
- 不支持 `&&` 语法，用分号 `;` 或换行
- 引号处理注意 here-string 行为

## 四、适用场景与不适用场景

### 适用场景

- 新功能开发（编译/查询/健康检查等）
- Bug 修复（类型错误/运行时错误）
- 设计文档更新
- 类型修复
- SSE 流式功能开发

### 不适用场景

- 模型训练/微调
- 移动端 App 开发
- CI/CD 配置
- 数据库迁移（本项目用文件系统）

## 主题色切换复盘（2026-07-09）

### 成功执行任务的完整步骤

| 步骤 | 动作 | 产出物 |
|------|------|--------|
| 1. 变量分层设计 | 基础调色板 → 子系统变量 → 场景变量三层架构 | 变量层级规划 |
| 2. 主题文件创建 | 为 6 个主题各创建 CSS 文件，覆盖全部变量 | 6 个 theme.css |
| 3. 主题切换器 | data-theme 属性 + localStorage 持久化 | ThemeSwitcher.vue |
| 4. SVG 适配 | RobotAvatar 硬编码色值替换为 var() | 主题感知 IP 形象 |
| 5. JS 驱动适配 | vis-network 用 getComputedStyle 读取变量 | 主题感知图谱 |
| 6. 场景变量注入 | 为 6 主题添加 bg-scene + accent-*-aXX 变量 | 完整 alpha 变体 |
| 7. 批量替换 | 154 处硬编码 rgba 替换为 CSS 变量 | 主题适配视图 |
| 8. 验证 | vue-tsc + Playwright 3 主题截图 | 类型通过 + 视觉验证 |

### 不确定性与失败点

1. **第一轮修复不彻底**：只替换了 robot SVG 和 graph 节点色，遗漏了 8 个视图组件中的场景背景
   - 教训：硬编码色值检测必须覆盖全部 `.vue` 文件，不能只扫组件和图谱
2. **rgba(#hex, alpha) 无效 CSS**：批量生成脚本直接把 hex 塞进 rgba() 导致 CSS 解析失败
   - 教训：rgba() 只接受 `r, g, b` 数值，必须先 hexToRgb 转换
3. **alpha 变体不完整**：第一次只生成 11 个透明度，实际代码用到 0.03/0.35/0.45 等
   - 教训：先 Grep 扫描全部 alpha 值再生成变体，支持增量补充
4. **Windows 编码损坏**：Edit/Write 工具操作含中文的 CSS 文件产生 U+FFFD
   - 教训：含中文文件用 Node.js `fs.writeFileSync` 或 PowerShell `[System.IO.File]::WriteAllText`

### 可抽象的固定流程

1. **CSS 变量分层**：L1 基础 → L2 子系统 → L3 场景，每层在主题文件中独立覆盖
2. **硬编码检测**：`Grep rgba\(\s*\d+` → 按 rgb 元组分类 → 映射到 CSS 变量名 → 批量替换
3. **alpha 命名**：统一 `aXX` 后缀（a03/a05/a10...），禁止 `05` 或 `0.5` 等不一致格式
4. **JS 颜色适配**：getComputedStyle 读取变量，主题切换后重新调用

### 适用场景与不适用场景

**适用**：
- 多主题系统开发/维护
- 任何使用 CSS 变量的前端项目色值统一管理
- 批量重构硬编码色值为主题变量
- SVG/Canvas/vis-network 等 JS 驱动图形的主题适配

**不适用**：
- 单主题项目（无需 CSS 变量分层）
- 颜色不随主题变化的固定视觉元素（如纯白高光）
- CSS-in-JS 方案（有自己的主题机制）
- Tailwind 方案（用 config 而非 CSS 变量管理主题）


---

## 系统清理模块复盘（2026-07-10）

### 一、成功执行任务的完整步骤

| 步骤 | 动作 | 产出物 |
|------|------|--------|
| 1. 需求确认 | 阅读需规对应章节 → 明确清理范围（会话/缓存/索引）与边界（不清理什么） | 功能边界清单 |
| 2. 参考既有模式 | Grep 现有 routes/workflows → 确认路由命名、错误码、SSE 风格 | 技术决策依据 |
| 3. 后端实现 | routes → workflows → vault 分层实现清理 API | 后端清理接口 |
| 4. 前端实现 | types → store → view 分层实现清理 UI | 前端清理面板 |
| 5. 类型检查 | `tsc --noEmit` + `vue-tsc --noEmit` 双重门禁 | 类型通过证明 |
| 6. 构建 | `encoding_scan_command` 门禁 → `npm run build` | 构建产物 |
| 7. Playwright | 启动服务 → 截图 → 交互验证 → 中文文案匹配 | 端到端验证证明 |
| 8. 文档同步 | DELIVERY.md 追加交付章节（保持原编码） | 更新后的交付文档 |

**详细操作要点**：

- **步骤 2 - 参考既有模式**：必须先用 `Grep` 扫描同类路由（`app.get/post/delete`）的命名、参数、错误码模式，禁止凭直觉命名导致风格漂移
- **步骤 5 - 双重类型门禁**：`tsc` 通过不代表 `vue-tsc` 通过，Vue SFC 模板中的类型错误只有 `vue-tsc` 能捕获
- **步骤 6 - 编码门禁**：构建前必须运行 `encoding_scan_command`，扫描失败先 `encoding_fix_command` 修复再复扫
- **步骤 7 - Playwright 中文匹配**：用 `getByText` 配合精确中文文案，禁止用模糊正则；启动前先停止旧进程释放端口
- **步骤 8 - 文档同步**：DELIVERY.md 追加章节必须保持原文件编码（非 UTF-8 时用 `encoding_fallback`）

### 二、不确定性与失败点

#### 1. 编码混乱（critical）

**现象**：Edit/Write 工具修改含中文文件后，Vite 构建注入 U+FFFD 替换字符，前端 UI 显示"???"或乱码。

**根因**：Windows 中文系统下部分历史文件以 GB2312 保存。Edit 工具默认 UTF-8 读写，把原字节按 UTF-8 解码产生不可逆替换字符。

**解决方案**：参见 [encoding-guard-rule.md](encoding-guard-rule.md)
- Edit 前用 `UTF8Encoding(false, true)` 严格解码检测
- 非 UTF-8 文件用 `encoding_fallback`（默认 gb2312）读写
- 构建前 `node scripts/check-encoding.js` 门禁

#### 2. vue-tsc 类型错误（critical）

**现象**：`tsc --noEmit` 通过，但 `vue-tsc --noEmit` 报错。

**根因**：
- `reactive` 对象属性访问类型推断不包含额外属性，需从元数据获取（如 `cards.find(c => c.key === key).showDays` 而非 `form.showDays`）
- unused imports 在 TypeScript strict 模式下报错
- 联合类型窄化失败（`string | {from, to}` 无法跨属性推断）

**解决方案**：
- 删除所有未使用的 import
- 跨属性联合类型用 `as` 断言或 type guard 函数
- `reactive` 额外属性从源头（元数据/接口）查询，不在 reactive 对象上动态扩展

```typescript
// type guard 模板
function isRange(obj: unknown): obj is { from: string; to: string } {
  return typeof obj === 'object' && obj !== null && 'from' in obj && 'to' in obj;
}
```

#### 3. Edit 工具失败（critical）

**现象**：Edit 报告成功但文件仅 6 字节，或 Edit 直接抛错无法写入。

**根因**：Edit 工具封装层较多，长路径/锁文件/编码不一致时行为不可预期。

**解决方案**：回退到 PowerShell `[System.IO.File]::WriteAllText` 直写，显式控制编码：
```powershell
[System.IO.File]::WriteAllText(
  $path,
  $content,
  [System.Text.UTF8Encoding]::new($false)
)
```

#### 4. bat 脚本 pause 卡住自动化（suggestion）

**现象**：调用项目内 .bat 启动脚本，命令表现为"挂起"，最终超时失败但无错误输出。

**根因**：.bat 末尾 `pause` 等待按键，RunCommand 自动化调用永远拿不到按键事件。

**解决方案**：
- 直接用 `npm run` 命令替代 .bat 脚本（来自 config `bat_alternative`）
- 必须用 .bat 时，移除末尾 `pause` 或用 `if "%~1"=="" pause` 仅交互模式暂停

#### 5. 端口占用（critical）

**现象**：旧 server 进程未释放 3000/5173 端口，新启动失败或连接到旧服务。

**解决方案**：参见 [powershell-constraints-rule.md](powershell-constraints-rule.md) 服务生命周期管理模板
```powershell
# 停止占用端口的旧进程
$conns = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if ($conns) { Stop-Process -Id $conns.OwningProcess -Force }
```

#### 6. Playwright 中文匹配失败（suggestion）

**现象**：`page.getByText('清理会话')` 匹配失败，但 UI 确实显示该文案。

**根因**：
- 中文文案被多个 span 拆分，`getByText` 默认不跨节点匹配
- 编码损坏导致实际 DOM 文本是 U+FFFD 而非中文字符
- 等待时机不对，元素尚未渲染

**解决方案**：
- 用 `{ exact: false }` 模糊匹配或 `page.locator('text=清理')`
- 先用 `encoding_scan_command` 确保源文件编码正确
- 用 `await page.waitForSelector('text=清理', { state: 'visible' })` 显式等待

### 三、可抽象的固定流程

#### 1. 编码守卫流程

```
Edit 前：检测编码 → 非 UTF-8 用 encoding_fallback 读写
Edit 后：可选复检
构建前：encoding_scan_command 门禁 → 失败则 fix_command 修复 → 复扫
```

详见 [encoding-guard-rule.md](encoding-guard-rule.md)。

#### 2. 类型检查双重门禁

```
tsc --noEmit  →  vue-tsc --noEmit  →  构建
   ↓                ↓                    ↓
后端类型         前端 SFC 模板类型       编码门禁 + bundle
```

- `tsc` 不通过：后端类型错误，修复 TS 代码
- `vue-tsc` 不通过：Vue SFC 模板类型错误，修复模板或 reactive 类型
- 都通过才允许构建

#### 3. 服务生命周期管理

```
停止旧进程（Get-NetTCPConnection + Stop-Process）
   ↓
启动服务（RunCommand blocking=false, command_type=web_server）
   ↓
验证端口监听（Get-NetTCPConnection -State Listen）
   ↓
运行验证（curl / Playwright）
   ↓
（可选）停止服务
```

详见 [powershell-constraints-rule.md](powershell-constraints-rule.md) 服务生命周期管理模板。

#### 4. Playwright 端到端测试流程

```
1. 停止旧服务释放端口
2. 启动 dev:api + dev:web（非阻塞）
3. Wait-PortListening 验证端口监听
4. page.goto + waitForSelector 等待首屏
5. 中文文案用 getByText({ exact: false }) 或 locator('text=...')
6. 截图 + 交互验证
7. 收集 console / network 错误
8. 停止服务
```

#### 5. 文档同步流程

```
检测 DELIVERY.md 编码（严格 UTF-8 解码）
   ↓
UTF-8：用 Edit/Write 追加章节
非 UTF-8：用 PowerShell + encoding_fallback 读写追加
   ↓
追加章节内容（按"模块名（日期）"标题）
   ↓
可选：复检编码未变
```

### 四、适用场景与不适用场景

#### 适用场景

- Windows 中文环境下的全栈模块开发（前后端 + 文件持久化）
- 含中文文案/中文注释的项目（编码守卫必需）
- Vue 3 + TypeScript + Vite 项目（vue-tsc 双重门禁）
- 需要 Playwright 端到端验证的功能
- 需要在 DELIVERY.md 追加交付章节的工作流
- 端口固定（3000/5173）的 dev 服务

#### 不适用场景

- Linux/macOS 原生环境（无 GB2312 历史包，编码守卫可省略）
- 纯后端项目（无 vue-tsc 门禁、无 Playwright）
- 纯 ASCII 项目（编码守卫无意义）
- CI/CD 流水线（已有独立编码校验和服务管理）
- 容器化部署（容器内通常 Linux + UTF-8，且服务由编排器管理）
- SSR/移动端（渲染时机与持久化模式不同，需独立规范）

---

## ESM 模块与编码守卫复盘（2026-07-18）

### 一、成功执行任务的完整步骤

| 步骤 | 动作 | 产出物 |
|------|------|--------|
| 1. 复盘背景确认 | 列出本次任务修复的 4 类高价值问题（ESM `__dirname` / SonarQube S6606 / 模块接线 / 编码损坏） | 问题清单 |
| 2. 规则参数化 | 把 4 条规则的可变参数（`__dirname`、`dirname_derive_pattern`、`wiring_required_steps` 等）抽取到 `config/tech-stack.json` 的 `esm` 字段 | 参数化配置 |
| 3. 规则文档化 | 新建 `references/esm-module-guard-rule.md`，4 条规则按"严重级别 + 描述 + 根因 + 正确模板 + 错误示例"四维度组织 | 规则文件 |
| 4. 项目硬约束同步 | 在 `references/project-rules.md` 追加 ESM 与模块接线约束章节，简明版规则 | 项目硬约束 |
| 5. 工作流复盘同步 | 在 `references/development-workflow.md` 追加本章节（四维度复盘） | 工作流文档 |
| 6. SKILL.md 升级 | 版本号 v1.5.0 → v1.6.0，变更记录追加 v1.6.0 条目，references 列表新增 `esm-module-guard-rule.md` | Skill 元数据 |
| 7. 编码自验 | 每个新增/修改文件用 `UTF8Encoding(false, true)` 严格解码自检（CODING-020 自适用） | 编码自验证明 |

**详细操作要点**：

- **步骤 2 - 参数化**：所有可变字符串值（`__dirname` / `__filename` / `import.meta.url` / S6606 / U+FFFD 等）必须以 `config.esm.*` 引用，禁止在规则文件硬编码
- **步骤 3 - 规则文档化**：每条规则必须包含"为什么"根因段，根因要追溯到运行时语义而非表象
- **步骤 6 - SKILL.md 升级**：版本号、变更记录、references 列表、阶段交接声明四项必须同步更新

### 二、不确定性与失败点

#### 1. ESM `__dirname` 运行时 ReferenceError（critical）

**现象**：4 个文件（index.ts、compile-workflow.ts、query-workflow.ts、health-check-fix-workflow.ts）调用 `__dirname` 时直接抛 `ReferenceError: __dirname is not defined`，Node.js ESM 进程立即崩溃。原本期望 `__dirname ?? path.dirname(fileURLToPath(import.meta.url))` 能用 `?? ` 兜底，但 `?? ` 的左操作数在求值阶段就已经抛错，短路逻辑根本不会被执行。

**根因**：Node.js ESM 模式下不注入 CommonJS 全局变量 `__dirname` / `__filename`。与 `undefined` 不同，引用未声明全局变量抛的是 `ReferenceError`（不可被 `?? ` / `|| ` 兜底），而非返回 `undefined`。SonarQube S6606 把 `typeof __dirname !== 'undefined' ? __dirname : fallback` 简化为 `__dirname ?? fallback`，绕过了 `typeof` 的安全守卫（`typeof` 对未声明变量返回 `'undefined'`，不抛错）。

**解决方案**：参见 [esm-module-guard-rule.md](esm-module-guard-rule.md) CODING-017
- 4 个文件移除所有 `__dirname` 引用
- 改用 `const dirname = path.dirname(fileURLToPath(import.meta.url));`（来自 `config.esm.dirname_derive_pattern`）
- 确保先 `import path from 'node:path'` 与 `import { fileURLToPath } from 'node:url'`（来自 `config.esm.required_imports`）

#### 2. SonarQube S6606 静态分析回归（critical）

**现象**：SonarQube S6606 报告 `typeof __dirname !== 'undefined' ? __dirname : fallback` 是"可简化的三元表达式"，建议改为 `__dirname ?? fallback`。开发者盲目采纳后引入运行时 ReferenceError（见问题 1）。

**根因**：静态分析工具基于语法层面判断"可简化"，但语法等价不等于运行时等价。`typeof x` 对未声明变量安全（返回 `'undefined'`），而直接引用 `x` 会抛 ReferenceError。SonarQube 的等价性分析未考虑"变量是否在运行时已声明"这一维度。

**解决方案**：参见 [esm-module-guard-rule.md](esm-module-guard-rule.md) CODING-018
- 每条 SonarQube / ESLint 修复建议必须人工逐项过 `config.esm.manual_verification_checklist` 三项：
  - `operand_throws_on_reference`：操作数在引用时是否可能抛错？
  - `type_guard_bypassed`：原写法的类型守卫是否被简化绕过？
  - `side_effect_changed`：副作用顺序/次数是否变化？
- 任一项不通过 → 拒绝采纳，标记 false positive

#### 3. 模块接线遗漏导致 API 404（critical）

**现象**：新增 `routes/tunnel.ts` 后，`curl /api/tunnel` 返回 404。TypeScript 类型检查（`tsc --noEmit`）通过，因为 `routes/tunnel.ts` 本身合法、`registerTunnelRoute` 函数也被正确导出，只是没有被入口文件 `index.ts` 引用。Tunnel API 在本次复盘中发生两次同类遗漏。

**根因**：分层架构中 routes 模块只暴露 `registerXxxRoute(app, service)` 工厂函数，必须由入口文件主动调用才会生效。开发者常在新增 routes 模块后忘记在 `index.ts` 完成接线三步骤（import + 实例化 + registerRoute）。TypeScript 编译器无法检测"模块未被引用"，因为模块本身合法。

**解决方案**：参见 [esm-module-guard-rule.md](esm-module-guard-rule.md) CODING-019
- 在 `index.ts`（来自 `config.esm.wiring_entry_file`）中完成 `config.esm.wiring_required_steps` 三步：
  ```typescript
  import { registerTunnelRoute } from './routes/tunnel.js';        // ① import
  import { TunnelService } from './services/tunnel-service.js';    // ① import 依赖
  const tunnelService = new TunnelService();                       // ② instantiate
  registerTunnelRoute(app, tunnelService);                         // ③ registerRoute
  ```
- 新增模块后 Grep 其导出函数名（如 `registerTunnelRoute`）在 `wiring_entry_file` 中是否被调用

#### 4. Edit 工具导致 UTF-8 文件编码损坏（critical）

**现象**：Config.vue / Tunnel.vue / config.ts 三个含中文文件经 Edit 工具修改后产生 U+FFFD 替换字符（俗称"锟斤拷"乱码）。Vite 构建无报错，`tsc` / `vue-tsc` 均通过，但前端 UI 显示乱码，仅人工目视或 Playwright 截图能发现。

**根因**：Edit 工具在某些情况下会用系统默认编码（Windows 中文环境为 GBK）写回。UTF-8 文件被 GBK 解码再写回，会产生不可逆的 U+FFFD 替换字符。运行时无堆栈可追，定位成本极高。

**解决方案**：参见 [esm-module-guard-rule.md](esm-module-guard-rule.md) CODING-020
- Edit / Write 修改含非 ASCII 字符文件后立即按 `config.esm.encoding_verification_method`（`UTF8Encoding(false, true)` 严格解码）验证
- 验证失败按 `config.esm.encoding_failure_recovery` 五步恢复：
  ```powershell
  git stash                                     # 1. 暂存当前修改
  git checkout HEAD -- Config.vue Tunnel.vue config.ts  # 2. 从 HEAD 恢复损坏文件
  git stash pop                                 # 3. 恢复其他未损坏修改
  # 4. re-edit：重新用 Edit 工具编辑目标文件
  # 5. re-verify：复检 Test-FileUtf8Strict
  ```

### 三、可抽象的固定流程

#### 1. ESM 守卫流程

```
新增/修改 .ts / .mts / .js / .mjs 文件
   ↓
Grep __dirname|__filename
   ↓
命中 = 违规 → 改用 config.esm.dirname_derive_pattern
   ↓
确保 config.esm.required_imports 已导入（path / fileURLToPath）
   ↓
提交前再次 Grep 复检
```

详见 [esm-module-guard-rule.md](esm-module-guard-rule.md) CODING-017。

#### 2. 模块接线流程

```
新增 routes/xxx.ts 或 workflows/xxx.ts
   ↓
在 config.esm.wiring_entry_file（默认 src/index.ts）中：
  ① import { registerXxxRoute } from './routes/xxx.js'
  ② import { XxxService } from './services/xxx-service.js'
     const xxxService = new XxxService();
  ③ registerXxxRoute(app, xxxService);
   ↓
Grep registerXxxRoute 在 wiring_entry_file 中是否被调用
   ↓
curl /api/xxx 验证路由可访问（非 404）
```

详见 [esm-module-guard-rule.md](esm-module-guard-rule.md) CODING-019。

#### 3. 静态分析验证流程

```
SonarQube / ESLint 产出修复建议
   ↓
逐项过 config.esm.manual_verification_checklist：
  □ operand_throws_on_reference    操作数在引用时是否可能抛错？
  □ type_guard_bypassed            原写法的类型守卫是否被简化绕过？
  □ side_effect_changed            副作用顺序/次数是否变化？
   ↓
任一项不通过 → 拒绝采纳，标记 false positive
   ↓
全部通过 → 采纳修改，commit message 注明验证结论
```

详见 [esm-module-guard-rule.md](esm-module-guard-rule.md) CODING-018。

#### 4. 编码验证流程

```
Edit / Write 修改含非 ASCII 字符文件
   ↓
立即用 config.esm.encoding_verification_method 严格 UTF-8 解码检测
  （UTF8Encoding(false, true)，第二参数 throwOnInvalidBytes=true）
   ↓
通过 → 进入下一环节（类型检查 / 构建 / 提交）
   ↓
失败 → 按 config.esm.encoding_failure_recovery 五步恢复：
  1. git stash
  2. git checkout HEAD -- <损坏文件>
  3. git stash pop
  4. re-edit：重新 Edit
  5. re-verify：复检 Test-FileUtf8Strict
   ↓
复检通过才继续
```

详见 [esm-module-guard-rule.md](esm-module-guard-rule.md) CODING-020。

### 四、适用场景与不适用场景

#### 适用场景

- Node.js ESM 项目（`package.json` 含 `"type": "module"` 或 `.mts` / `.mjs` 由 ESM loader 解析）
- 使用 Fastify / Express 等框架，路由由入口文件 registerXxxRoute 模式加载的项目
- 引入 SonarQube / ESLint 等静态分析工具并启用自动修复建议的项目
- Windows 中文环境下编辑含中文/日文/韩文/Emoji 的源文件、文档、配置
- TypeScript strict 模式下需要运行时与静态分析联合验证的场景
- 任何采用"分层架构 + 入口注册"模式的 Node.js 项目

#### 不适用场景

- CommonJS 项目（`__dirname` / `__filename` 由运行时正常注入，CODING-017 不适用）
- Linux/macOS 原生 UTF-8 环境，且未启用静态分析自动修复（CODING-018 / CODING-020 可省略）
- 单文件脚本（无入口文件、无路由注册步骤，CODING-019 不适用）
- 纯 ASCII 内容文件（无中文/Emoji，CODING-020 无可见症状但仍建议执行）
- 已通过 CI 强制 ESM / 编码 / 静态分析门禁的项目（CI 兜底，本地可省略部分步骤）

---

## Async 可靠性复盘（2026-07-21）

### 一、成功执行任务的完整步骤

| 步骤 | 动作 | 产出物 |
|------|------|--------|
| 1. 证据收集 | 读取状态文件（%TEMP%\xh_browser_login\*.json），对比 timings 字段 | 卡死阶段定位：settle_cookies_sec 未写入 |
| 2. 根因分析 | 读取源码，定位 context.cookies() 卡死点，追踪心跳检测逻辑 | 根因：Playwright IPC 永久挂起阻塞事件循环 |
| 3. 第一次修复（失败） | 加 asyncio.wait_for 5s 超时 + asyncio.Task 独立心跳 | py_compile + pytest 通过，但实际部署仍失败 |
| 4. 根因升级 | 分析新状态文件，确认 asyncio.Task 心跳也失效 | 根因升级：事件循环被阻塞，asyncio.Task 无法调度 |
| 5. 第二次修复（成功） | 改用 threading.Thread 独立心跳 + best_holder 兜底 | 11 个单元测试通过 |

### 二、不确定性与失败点

#### 1. asyncio.wait_for 取消信号无法传播（critical）

**现象**：`asyncio.wait_for(context.cookies(), timeout=5.0)` 超时后，被等待的 Playwright future 仍在后台运行，cancel 信号未传播。

**根因**：Playwright 1.60.0 的 `_channel.send` 在浏览器进程无响应时，cancel 信号传播不完整。asyncio.wait_for 超时后会抛 TimeoutError，但底层 IPC future 仍挂起。

**解决方案**：参见 [async-reliability-rule.md](async-reliability-rule.md) CODING-021
- 所有 Playwright async 调用必须用 asyncio.wait_for 包裹
- 超时后降级到 best_holder 中的最后已知数据

#### 2. asyncio.Task 心跳在事件循环阻塞时失效（critical）

**现象**：第一次修复新增 asyncio.Task 独立心跳，预期即使 _collect_settled_cookies 卡住，心跳仍能更新 status file。实际部署后心跳仍失效，91s 后被判"无响应"。

**根因**：asyncio.Task 依赖事件循环调度。当事件循环线程被 Playwright IPC 阻塞时，**所有 asyncio Task 都无法执行**。asyncio.Task 的"独立性"是相对于其他协程的，不是相对于事件循环的。

**解决方案**：参见 [async-reliability-rule.md](async-reliability-rule.md) CODING-022
- 心跳必须用 threading.Thread 实现
- 线程是操作系统调度单元，独立于事件循环

### 三、可抽象的固定流程

#### 1. async 可靠性防护流程

```
新增/修改 async 调用
   ↓
判断是否在 config.async_reliability.blocking_risk_apis 列表中
   ↓
是 → 必须 asyncio.wait_for 包裹（CODING-021）
   ↓
判断是否有心跳/状态更新逻辑
   ↓
是 → 必须用 threading.Thread 实现（CODING-022）
   ↓
判断是否有兜底数据
   ↓
是 → 用 best_holder 模式传递（CODING-024）
   ↓
判断是否为长时任务
   ↓
是 → 配置多层超时（CODING-025）
```

#### 2. 状态文件通信可靠性流程

```
子进程通过状态文件与主进程通信
   ↓
确认 ts 字段更新策略 = config.async_reliability.status_file_update_strategy
   ↓
strategy=thread → 启动独立心跳线程（CODING-023）
   ↓
strategy=async_loop → 确认循环间隔 ≤ heartbeat_max_interval_sec
   ↓
心跳线程在任务完成后正常退出（join timeout = thread_join_timeout_sec）
```

### 四、适用场景与不适用场景

#### 适用场景

- Python asyncio + Playwright/aiohttp/异步 IPC 的项目
- Node.js + Playwright/native addon 的项目
- 子进程通过状态文件与主进程通信的架构
- 需要心跳检测的长时任务（登录、爬取、批量处理）
- 使用 SSE 流式响应且需要保活检测的场景

#### 不适用场景

- 纯同步代码（无需 asyncio，用 threading.Timer 即可）
- 单次快速 async 调用（<1s，阻塞风险可忽略）
- 无子进程通信的简单 Web API
- CI/CD 流水线任务（通常有独立的超时机制）

---

## 后续复盘模板

新复盘按以下结构追加到本文件末尾：

```markdown
## <模块名>复盘（YYYY-MM-DD）

### 一、成功执行任务的完整步骤
| 步骤 | 动作 | 产出物 |
|------|------|--------|
| ... | ... | ... |

### 二、不确定性与失败点
#### 1. <问题名>（critical/suggestion）
**现象**：...
**根因**：...
**解决方案**：...

### 三、可抽象的固定流程
#### 1. <流程名>
\`\`\`
<流程图>
\`\`\`

### 四、适用场景与不适用场景
#### 适用场景
- ...
#### 不适用场景
- ...
```

---

## 帮助文档与关于模块复盘（2026-07-20）

### 一、成功执行任务的完整步骤

| 步骤 | 动作 | 产出物 |
|------|------|--------|
| 1. 参考已有项目模式 | 阅读 17_xianyu 项目 About/Help 模块（React+antd）→ 提炼设计原则 → 适配到本项目 Vue3+Element Plus+Fastify | 设计原则映射表 |
| 2. 后端实现 | routes/about.ts（GET /api/about + GET /api/about/check-update，5 分钟缓存）→ index.ts 显式 registerAboutRoute | 后端接口 |
| 3. 前端实现 | About.vue（品牌卡+8 项菜单+5 态更新按钮+开源声明 Modal）+ Help.vue（12 章节侧栏+内容卡片）→ App.vue 注册导航 | 前端视图 |
| 4. SPA 内部跳转 | About→Help 通过 CustomEvent 派发 `karpathy:navigate`，App.vue 监听切换视图 | 内部跳转链路 |
| 5. 类型检查 | vue-tsc + tsc 双重门禁 | 类型通过证明 |
| 6. 编码体检 | node scripts/check-encoding.js（76→79 文件无 GBK 乱码） | 编码通过证明 |
| 7. 接口测试 | Invoke-WebRequest 验证 /api/about 与 /api/about/check-update 返回 200 | API 验证证明 |
| 8. 浏览器验证 | browser_use 子代理验证 10 项 UI 检查 + 控制台无错误 | 端到端证明 |
| 9. 修复迭代 | 发现章节卡片仅显示标题 → 定位双重滚动根因 → 最小化修复 → 重验证 | 修复后证明 |

**详细操作要点**：

- **步骤 1 - 跨技术栈适配**：闲鱼项目是 React+antd，本项目是 Vue3+Element Plus，需将 React 模式适配为 Vue 3 Composition API（useState → ref，useEffect → onMounted/onBeforeUnmount）
- **步骤 4 - SPA 跳转**：闲鱼有独立路由 /about 和 /help，本项目是 SPA 单视图切换（currentView ref），需通过 CustomEvent 实现 About→Help 内部跳转
- **步骤 6 - 编码体检**：新增 3 个文件后扫描范围从 76 → 79，确保新文件均 UTF-8 无 BOM
- **步骤 8 - 浏览器代理验证**：用 DOM 快照替代截图作为证据，验证 12 章节锚点完整性 + 搜索过滤 + 锚点跳转

### 二、不确定性与失败点

#### 1. 双重滚动裁切（critical）

**现象**：每个章节卡片只显示图标+标题一行，下方 intro/blocks 全部不可见，标题文字"快速开始使用文档"被截断为"快速开始"等

**根因**：三层嵌套导致 flex 子项被压缩到 min-content 高度
- `.app-shell` 有 `height: 100vh + display: flex + flex-direction: column`
- `.content` 是 `flex: 1 + overflow-y: auto`
- `.help-content-area` 又设了 `flex: 1 + overflow-y: auto`（与外层形成双重滚动）
- `.glass-card` 全局有 `overflow: hidden`
- flex 子项默认 `flex: 0 1 auto`，在双重滚动嵌套中被等比压缩到约 50px

**解决方案**：参见 [scroll-container-rule.md](scroll-container-rule.md)
- 移除内层 `overflow-y: auto`，让外层 `.content` 统一接管滚动
- 给 `.intro-card`/`.section-card` 加 `flex-shrink: 0`，按内容自然高度撑开

#### 2. dev 端口冲突（suggestion）

**现象**：第二次启动 `pnpm --filter @karpathy-wiki/web run dev` 时 5173 被占用，Vite 自动改用 5174

**根因**：第一次 dev 服务未正确停止，进程残留（PID 4156 仍监听 5173）

**解决方案**：
- 用 `Get-NetTCPConnection -LocalPort 5173` 查询占用进程
- 因旧 dev 有 HMR 已应用代码改动，可复用而无需强制重启
- 强制重启：`Stop-Process -Id <PID> -Force` 后重新启动

#### 3. 浏览器代理无法截图（suggestion）

**现象**：browser_use 子代理报告"浏览器环境限制导致无法生成截图文件"

**根因**：headless 浏览器在沙箱环境无文件写入权限

**解决方案**：用页面快照（DOM 结构检查 + bounding-rect + computed style）作为替代证据

#### 4. Vue 3 ref 不支持函数式更新（suggestion）

**现象**：`updateState.value = (prev) => prev.kind === 'latest' ? { kind: 'idle' } : prev` 报错

**根因**：Vue 3 ref 不支持 setState 函数式更新（与 React useState 不同）

**解决方案**：
```typescript
// 错误：函数式更新
updateState.value = (prev) => /* ... */

// 正确：直接读取当前值判断后赋值
if (updateState.value.kind === 'latest') {
  updateState.value = { kind: 'idle' };
}
```

#### 5. 模板表达式不支持全局对象直接调用（suggestion）

**现象**：`@click="globalThis.open(url, '_blank', 'noopener,noreferrer')"` 在模板中无效

**根因**：Vue 模板表达式有作用域限制，不支持全局对象直接调用

**解决方案**：抽出方法
```typescript
function openReleaseUrl(url: string) {
  globalThis.open(url, '_blank', 'noopener,noreferrer');
}
```

### 三、可抽象的固定流程

#### 1. 滚动容器单一职责流程

```
检查外层 .content 是否已设 overflow-y: auto
   ↓ 是
内层容器不得再设 overflow-y: auto → 移除
   ↓
给内容卡片加 flex-shrink: 0
   ↓
验证卡片高度从 ~50px 变为内容自然高度
```

详见 [scroll-container-rule.md](scroll-container-rule.md)。

#### 2. SPA 跨组件跳转流程

```
派发方：CustomEvent 派发（globalThis.dispatchEvent）
   ↓
入口组件：onMounted 中 addEventListener（具名函数）
   ↓
入口组件：监听到事件 → 校验 detail 在允许视图名列表内 → 切换 currentView
   ↓
onBeforeUnmount：removeEventListener（同名具名函数）
```

详见 [spa-navigation-rule.md](spa-navigation-rule.md)。

#### 3. 检查更新状态机流程

```
页面加载 → 延迟 5 秒 → 首次 checkUpdate
   ↓
状态：idle → loading → (latest | newer | error)
   ↓
latest → 3 秒后自动回 idle
newer → 显示更新按钮
error → 用户可重试
   ↓
轮询：每 5 分钟 checkUpdate（≥ 后端缓存 TTL）
   ↓
后端：缓存命中 → 返回 cache 数据；缓存失效 → 发起外部请求；离线模式 → 固定 has_update=false
```

详见 [update-check-rule.md](update-check-rule.md)。

#### 4. 跨技术栈适配流程

```
阅读参考项目（如闲鱼 React+antd）
   ↓
提炼设计原则（模块划分、状态机、缓存策略）
   ↓
映射到本项目技术栈：
  - React useState → Vue ref
  - React useEffect → Vue onMounted/onBeforeUnmount
  - antd Modal → Element Plus Dialog
  - 独立路由 → SPA CustomEvent 跳转
  - GitHub API → 离线模式降级
   ↓
按本项目编码规范实现
```

### 四、适用场景与不适用场景

#### 适用场景

- Vue 3 + Element Plus + Fastify 全栈模块开发
- flex 布局的多卡片长内容页面（如帮助文档、设置面板）
- SPA 手动路由项目的跨组件跳转
- 内网部署项目的"检查更新"功能（无外网通道）
- Windows 环境下的 dev 服务管理

#### 不适用场景

- CSS Grid 布局（grid 子项默认不收缩，无需 flex-shrink 守卫）
- vue-router / react-router 项目（直接用 router.push）
- 公网开源项目的检查更新（需要真实 GitHub API 调用）
- 容器化部署（服务由编排器管理，无端口冲突）

---

## v2 导航栏改造复盘（2026-07-22）

> 基于知识库问答窗口 UI 改造与 E2E 测试验证复盘提炼。涉及类型系统稳定性、Composable 调用可靠性、UI 阅读视野优化、E2E 测试同步性等 7 类工程问题。

### 一、成功执行任务的完整步骤

| 步骤 | 动作 | 产出物 |
|------|------|--------|
| 1. 需求理解 | 用户反馈问答窗口过小、菜单可收缩、图标重设计、输入框固定底部、去除标题头 | 明确 5 项改造需求 |
| 2. 代码探索 | Read App.vue / Query.vue / InputToolbar.vue / AttachmentUploader.vue 现有结构 | 现状分析报告 |
| 3. 导航栏改造 | App.vue 新增 navCollapsed ref + watch + localStorage 持久化 + 自定义 SVG 折叠按钮 | 双模式导航栏 |
| 4. 工具栏图标重设计 | InputToolbar.vue / AttachmentUploader.vue 完全重写，emoji 改为 currentColor + drop-shadow 主题感知 SVG | 3 套主题图标 |
| 5. 去除标题头 + 扩大阅读区 | Query.vue 删除 .query-head → 替换为极简 .query-topbar（仅 ModelSelector + 新会话按钮），height calc 减少 80px | 阅读视野扩大 |
| 6. 输入框固定底部 | .input-bar 改为 position: sticky; bottom: 0 + 毛玻璃背景 + z-index: 2 | 输入框滚动可见 |
| 7. 类型检查 | vue-tsc --noEmit + tsc --noEmit 双重门禁 | 类型通过证明 |
| 8. E2E 测试更新 | test_full_e2e.py 将 .query-head 检查替换为 .query-topbar + 导航栏折叠/展开测试 | 85/85 测试通过 |
| 9. 构建验证 | pnpm build 成功 + 截图保存 | 改造完成证明 |

### 二、不确定性与失败点

#### 1. vue-tsc 报告幽灵错误（critical）

**现象**：修改 InputToolbar.vue 后，vue-tsc 仍报"Object is possibly null"于某行，但 Read 该行发现代码已用局部变量收窄。

**根因**：vue-tsc 增量缓存（`tsconfig.tsbuildinfo`）+ Vite `.vite` 缓存返回旧版本类型信息；src 下还存在 `.ts` 对应的 `.js` 旧编译产物，Vite 优先加载 `.js`。

**解决方案**：参见 [typecheck-cache-rule.md](typecheck-cache-rule.md) CODING-026
- 删除 `tsconfig.tsbuildinfo` + `.vite` 目录 + `src/**/*.js` 编译产物
- 重新运行 `npx vue-tsc --noEmit` → 幽灵错误消失
- 禁止用 `as any` / `! postfix` / `@ts-ignore` 绕过

#### 2. useTTS composable 调用方法缺失（critical）

**现象**：调用 `useTTS()` 后 `setRate` 方法 undefined，但类型检查通过。

**根因**：未读 useTTS 源码就基于命名约定假设 API 形状；同时诊断脚本调用 `$dispose` + `_s.delete('tts')` 重建 store 导致运行时方法丢失。

**解决方案**：参见 [composable-api-rule.md](composable-api-rule.md) CODING-027
- 使用前必须 Read 源码确认导出形状、方法签名、setup 顺序
- 诊断代码禁止调用 `$dispose` / `_s.delete` 重建 store

#### 3. 工具栏 tools 数组类型升级后渲染失败（critical）

**现象**：tools 元素类型从 `string` 升级为 `{ key, icon, label }` 后，v-for 中 `tool.icon` 在旧字符串元素上调用失败。

**根因**：未做运行时类型分流，假设所有元素都是新对象类型。

**解决方案**：参见 [mixed-type-dispatch-rule.md](mixed-type-dispatch-rule.md) CODING-028
- 定义 `isObjectTool(tool): tool is { key: string, ... }` type guard helper
- v-for 中用 `isObjectTool(tool) ? tool.icon : undefined` 分流
- 禁止用 `as any` / `as unknown as U` 强制断言

#### 4. InputToolbar.vue 双 script 块冲突（suggestion）

**现象**：重写时混合 `<script>` + `<script setup lang="ts">`，vue-tsc 报错且组件状态不共享。

**根因**：迁移时未全量迁移到 Composition API，遗留 Options API 块。

**解决方案**：参见 [sfc-single-script-rule.md](sfc-single-script-rule.md) CODING-029
- `.vue` 文件只能有一个 `<script setup lang="ts">` 块
- 例外情况（如 name 导出）必须显式注释 `// 例外：` 说明

#### 5. E2E 测试首条用例 ERR_CONNECTION_REFUSED（critical）

**现象**：UI 改造后运行 test_full_e2e.py，首条用例即报连接拒绝。

**根因**：改造前未确认服务状态，automation.ps1 启动失败但未察觉。

**解决方案**：参见 [e2e-precheck-rule.md](e2e-precheck-rule.md) CODING-030
- 运行 E2E 测试前必须检查 `required_ports` 监听 + `/health` 健康检查
- 失败时中止测试并提示 `automation.ps1 -Action start`

#### 6. E2E 测试用例引用已删除的 .query-head（critical）

**现象**：去除 .query-head 后，测试仍 `page.locator(".query-head")`，导致用例全部失败。

**根因**：代码变更影响 DOM 结构时未同步更新测试选择器。

**解决方案**：参见 [test-case-sync-rule.md](test-case-sync-rule.md) CODING-031
- 代码变更影响 DOM 时必须 Grep 测试脚本同步更新选择器
- 禁止 try/except 静默吞错，必须 `record(..., False, str(e))` 标记失败
- 代码与测试用例必须在同一 commit

#### 7. 标题头占比过大 + 输入框未固定底部（suggestion）

**现象**：原 .query-head 含 RobotAvatar + 大标题 + 描述 + 多按钮，占比约 17%；输入框用普通 margin-top，滚动时不可见。

**根因**：未按阅读视野优化原则设计；输入框缺少 sticky 定位。

**解决方案**：参见 [reading-viewport-rule.md](reading-viewport-rule.md) CODING-032
- 标题头占比 ≤ 15%，去无非必要元素
- 内容区 ≥ 75%，调整 calc() 公式
- 输入区 `position: sticky; bottom: 0` + 毛玻璃背景 + `z-index: 2`

### 三、可抽象的固定流程

#### 1. 类型系统稳定性流程

```
vue-tsc / tsc 报告错误
   ↓
Read 源文件对应行号，确认错误是否真实
   ↓
错误真实 → 修复源文件
   ↓
错误不存在（幽灵错误）→ 清理增量缓存 + Vite 缓存 + src/**/*.js 产物
   ↓
重新运行类型检查
   ↓
错误消失 → 完成
   ↓
仍存在 → 重新审视源文件（可能误判）
```

#### 2. Composable 调用可靠性流程

```
要使用 useXxx() / store 的方法
   ↓
判断是否为自己编写
   ↓
否 → Read 源码，确认 API 形状 + 方法签名 + setup 顺序
   ↓
运行时方法缺失 → 检查 store 是否被诊断代码重建
   ↓
是 → 移除诊断代码中的 $dispose / _s.delete 调用
   ↓
否 → 检查 src/**/*.js 编译产物污染（与 CODING-026 联动）
```

#### 3. UI 改造影响 E2E 测试流程

```
修改 .vue / .tsx 文件 template
   ↓
识别变更的 DOM 选择器（class / id / 层级）
   ↓
Grep 测试脚本中是否引用了这些选择器
   ↓
命中 → 同步更新测试用例选择器与断言
   ↓
运行 E2E 测试前先检查服务状态（端口 + /health）
   ↓
测试用例全部通过 → 提交代码与测试（同一 commit）
```

### 四、适用场景与不适用场景

#### 适用场景

- Vue 3 + TypeScript + Vite 项目的类型系统稳定性维护
- 使用 Pinia store 的项目，跨组件调用 composable
- 涉及工具栏图标重设计、UI 视野优化的改造任务
- E2E 测试与代码结构同步的工程实践
- 任何引入"类型升级 T → U"的渐进式重构

#### 不适用场景

- 纯 JavaScript 项目（无类型检查，CODING-026 / 028 不适用）
- 无 store / composable 的简单组件项目（CODING-027 不适用）
- React / Svelte / Angular 项目（CODING-029 不适用，但其他规则可适配）
- 无自动化测试的项目（CODING-030 / 031 不适用，但建议补充）
- 移动端 App（CODING-032 阅读视野规则需独立设计）

---

## v3 媒体生成工具复盘（2026-07-31）

> 本复盘基于 v3 媒体生成工具（PPT/图像/视频）开发过程，提炼 CODING-056~067 共 12 条编码规范，覆盖外部 API 集成、超时分级、密钥解析、长任务架构、归档 frontmatter、会话存储、prompt 存储、SSE 事件分发、SSE 流错误处理、长任务轮询 UI、事件委托、重库加载十二大主题。

### 一、成功执行任务的完整步骤

| 步骤 | 动作 | 产出物 |
|------|------|--------|
| 1. 需求确认 | 明确三种输出模式（PPT/图像/视频）+ 输出归档路径 + SSE/独立端点选择 | 功能边界清单 |
| 2. 架构选型 | 秒级任务（PPT/图像）走 SSE 流，分钟级任务（视频）走独立 JSON 端点 + 轮询 | 架构决策文档 |
| 3. 后端工作流 | 实现 media-generation-workflow.ts，含 fetchWithDiagnostics 包装 + 超时分级 + 密钥三级回退 | 后端工作流代码 |
| 4. 路由层 | routes/media.ts 含限流分级（破坏性 5/min，轮询 60/min）+ 错误码区分 + 双日志 + 顶部注释 | 后端路由代码 |
| 5. 前端 store | query.ts 用对象映射表处理 SSE 事件，5 状态机驱动长任务 UI | 前端状态管理 |
| 6. SSE handler | consumeSSEStream 吞掉 AbortError + finally reader.cancel + signal 可空 | SSE 消费函数 |
| 7. 视图组件 | Query.vue 用 setInterval 轮询 + 三态区分 + 函数拆分 + onBeforeUnmount 清理 | 前端视图代码 |
| 8. 归档实现 | 媒体产物归档到 vault/queries/，统一 frontmatter（type/output_mode/generated_at）+ 文件名时间戳 | 归档代码 |
| 9. 重库加载 | mermaid/marp 动态 import + 模块级加载标志 + 实例缓存 + 五层错误防护 | 重库加载服务 |
| 10. 验证 | tsc + vue-tsc 双重门禁 + 端到端 API 验证（PPT/图像/视频三模式） | 验证证明 |

**详细操作要点**：

- **步骤 2 - 架构选型**：任务预估耗时 > `long_task.sse_threshold_ms`（默认 30s）必须走独立端点 + 轮询，禁止走 SSE 流（视频生成需 5 分钟，SSE 60s 超时会中断）
- **步骤 3 - 后端工作流**：所有外部 API 调用必须用 fetchWithDiagnostics 包装（禁止原生 fetch），按 err.cause.code 分类翻译为可读诊断信息；响应字段双重路径兼容（`data.url || data.metadata?.url`）
- **步骤 4 - 路由层**：破坏性端点限流 ≤ `long_task.destructive_rate_limit`（默认 5/min），轮询端点限流 = `long_task.poll_rate_limit`（默认 60/min）；错误码区分配置缺失（400）与 API 失败（500）
- **步骤 5 - 前端 store**：SSE 事件处理器用 `Record<string, Handler>` 对象映射表替代 if/else 链，控制 SonarQube S3776 认知复杂度 < 15
- **步骤 7 - 视图组件**：长任务用 5 状态机（`idle | queued | processing | completed | failed`），轮询单次失败不终止（连续 3 次才终止）；超时用 setTimeout 而非 AbortSignal.timeout（因需同步设 abortReason 标记）
- **步骤 9 - 重库加载**：体积 > 200KB 的库必须动态 import；mermaid 11.x 错误 SVG 注入需五层防护（库选项抑制 + parse 预验证 + 渲染前清空 + catch 清空 + CSS 隐藏错误元素）

### 二、不确定性与失败点

#### 1. Node.js fetch 无法访问外网（critical）

**现象**：Node.js 原生 fetch 调用 Agnes API 报 `TypeError("fetch failed")`，真因藏在 `err.cause.code` 里。

**根因**：Node.js 原生 fetch 不自动读取 HTTPS_PROXY 环境变量，需显式配置 undici ProxyAgent。

**解决方案**：参见 [external-api-contract-rule.md](external-api-contract-rule.md) CODING-056
- 在 api/src/index.ts 中设置 `setGlobalDispatcher(new ProxyAgent(process.env.HTTPS_PROXY))`
- 用 fetchWithDiagnostics 包装 fetch，按 `err.cause.code` 分类翻译错误
- 生产环境必须在 api/.env 中设置 HTTPS_PROXY

#### 2. /api/files 返回 JSON 而非二进制（critical）

**现象**：图像/视频归档后，前端通过 /api/files 下载时收到 JSON 而非二进制流。

**根因**：VaultService 缺少二进制读取方法，files.ts 路由用 readFile（返回字符串）而非 readFileBuffer。

**解决方案**：参见 [media-archive-frontmatter-rule.md](media-archive-frontmatter-rule.md) CODING-060
- VaultService 新增 `readFileBuffer()` 方法返回 Buffer
- files.ts 路由按文件扩展名判断返回类型（.png/.mp4 用 Buffer，.md 用字符串）

#### 3. 视频创建 400 错误 - seconds 字段类型（critical）

**现象**：调用 Agnes Video API 创建任务返回 400，错误提示 seconds 字段类型错误。

**根因**：Agnes Video API 的 Go 后端要求 seconds 字段为 string 类型，但前端传的是 number。

**解决方案**：参见 [external-api-contract-rule.md](external-api-contract-rule.md) CODING-056
- 调用方后端语言要求的字段类型必须显式转换：`seconds: String(mediaConfig.agnes.defaultVideoSeconds)`
- 禁止假设 JSON 序列化会自动适配

#### 4. 视频轮询 URL 字段路径变更（critical）

**现象**：视频生成完成后，轮询接口返回的 URL 字段有时在 `data.url`，有时在 `data.metadata.url`。

**根因**：Agnes API 版本升级时字段路径变更，未向后兼容。

**解决方案**：参见 [external-api-contract-rule.md](external-api-contract-rule.md) CODING-056
- 响应字段双重路径兼容：`const videoUrl = data.url || data.metadata?.url`
- 关键业务字段必须用双重路径兼容，避免 API 升级导致字段消失时业务失败

#### 5. 视频轮询 fetch 超时（critical）

**现象**：视频轮询接口偶发超时，导致轮询中断。

**根因**：所有调用用同一超时值（30s），但视频下载需 120s，导致正常请求被误判超时。

**解决方案**：参见 [timeout-tier-rule.md](timeout-tier-rule.md) CODING-057
- 按预估耗时分级设置 AbortSignal.timeout：
  - 任务创建：30s（应秒级返回）
  - 任务轮询：30s（应秒级返回，代理场景兜底）
  - 图像生成：60s（10-30s 常见，60s 兜底）
  - 视频下载：120s（大文件下载）
  - LLM 单轮调用：按 tokenBudget 分级（4k→60s, 16k→180s）

#### 6. query.ts outputMode 类型缺失 image/ppt（suggestion）

**现象**：前端类型检查报错，outputMode 类型不包含 'image' / 'ppt'。

**根因**：新增媒体生成功能时，未同步更新 outputMode 联合字面量类型。

**解决方案**：参见 [sse-event-dispatch-rule.md](sse-event-dispatch-rule.md) CODING-063
- outputMode 用 TypeScript 联合字面量类型：`type OutputMode = 'normal' | 'mindmap' | 'image' | 'ppt' | 'video'`
- 新增模式追加字面量不破坏旧客户端
- outputMode（结构模式）与 outputModes（事件可见性）正交分离

#### 7. SSE 流 AbortError 污染 errorMessage（suggestion）

**现象**：用户主动停止生成时，AbortController 触发 AbortError，错误处理逻辑把 AbortError 当作真实错误显示给用户。

**根因**：SSE 流消费函数未区分主动停止与真实错误。

**解决方案**：参见 [sse-stream-error-rule.md](sse-stream-error-rule.md) CODING-064
- SSE 流消费函数吞掉 AbortError（`err.name === 'AbortError'` 直接 return）
- 调用方用 `abortReason: 'user' | 'timeout' | null` 区分停止原因
- finally 中再次 `reader.cancel()` 兜底释放

#### 8. mermaid 11.x 错误 SVG 注入（suggestion）

**现象**：mermaid 解析失败时注入 .error-icon / .error-text SVG 元素，污染 UI 显示"Syntax error in text"。

**根因**：mermaid 11.x 默认错误渲染行为不可控，解析失败时自动注入错误 SVG。

**解决方案**：参见 [heavy-library-rule.md](heavy-library-rule.md) CODING-067
- 五层防护：①`suppressErrorRendering: true` ②`parse()` 预验证 ③渲染前清空容器 ④catch 清空容器 ⑤CSS 全局隐藏 `.error-icon / .error-text`
- 渲染失败降级显示原始内容（`<pre>{{ raw }}</pre>`）

### 三、可抽象的固定流程

#### 1. 外部 API 集成流程

```
调用外部 API
   ↓
1. fetchWithDiagnostics 包装（禁止原生 fetch）
   ↓
2. 超时分级（task_creation/task_polling/image_generation/video_download/llm_small/llm_large）
   ↓
3. 密钥三级回退（专用段→共享段→环境变量）
   ↓
4. 字段类型显式转换（Go/Rust 后端要求 string 等）
   ↓
5. 响应字段双重路径兼容（data.x || data.y?.x）
   ↓
6. 错误码分类翻译（UND_ERR_CONNECT_TIMEOUT/ENOTFOUND/ECONNREFUSED 等）
```

详见 [external-api-contract-rule.md](external-api-contract-rule.md)、[timeout-tier-rule.md](timeout-tier-rule.md)、[api-key-resolution-rule.md](api-key-resolution-rule.md)。

#### 2. 长任务架构选择流程

```
新增异步任务
   ↓
预估任务耗时
   ↓
≤ 30s（秒级）→ SSE 同步流（复用 query 通道）
   ↓
> 30s（分钟级）→ 独立 JSON 端点 + 前端轮询
   ↓
破坏性端点限流 ≤ 5/min（触发外部 API 成本）
   ↓
轮询端点限流 = 60/min（与前端 5s 间隔匹配）
   ↓
错误码区分：配置缺失 400 / API 失败 500
   ↓
双日志通道：JSON 响应 + request.log.error
   ↓
路由文件顶部"设计要点"块注释
```

详见 [long-task-architecture-rule.md](long-task-architecture-rule.md)。

#### 3. 媒体归档流程

```
LLM 生成产物（图像/PPT/视频）
   ↓
归档到 vault/queries/（WRITE_ALLOWED_DIRS 白名单）
   ↓
frontmatter 必备字段：type / output_mode / generated_at
   ↓
业务字段同 frontmatter（image_file / video_file / task_id / source_url）
   ↓
文件名格式：<output_mode>-YYYYMMDD-HHmmss.<ext>
   ↓
Marp 类归档：marp 字段合并到归档 frontmatter（禁止双重 frontmatter）
```

详见 [media-archive-frontmatter-rule.md](media-archive-frontmatter-rule.md)。

#### 4. SSE 事件分发流程

```
后端 SSE 流写入
   ↓
按 chunk 字段独立 if 分发（新增类型追加 if 分支）
   ↓
前端事件处理器
   ↓
事件类型 ≥ 3 → Record<string, Handler> 对象映射表
   ↓
outputMode 联合字面量类型（新增模式追加字面量）
   ↓
outputMode（结构模式）与 outputModes（事件可见性）正交分离
   ↓
未知事件默认 handler（console.warn，禁止静默吞掉）
```

详见 [sse-event-dispatch-rule.md](sse-event-dispatch-rule.md)。

#### 5. 长任务轮询 UI 流程

```
长任务启动
   ↓
5 状态机：idle → queued → processing → completed/failed
   ↓
setInterval(poll_interval_ms) 轮询
   ↓
单次失败不终止（仅更新 error 文案，连续 3 次才终止）
   ↓
完成/失败显式 stopPolling()
   ↓
超时用 setTimeout（非 AbortSignal.timeout）以同步设 abortReason
   ↓
"关闭对话框"与"重置状态保持对话框"拆为两个函数
   ↓
onBeforeUnmount 清理 abortController + addEventListener + setInterval
```

详见 [long-task-polling-ui-rule.md](long-task-polling-ui-rule.md)。

#### 6. 重库加载流程

```
引入第三方库
   ↓
体积 > 200KB → 动态 import() 加载
   ↓
模块级 xxxLoaded 标志避免重复加载
   ↓
实例缓存复用（marpInstance 等）
   ↓
CJS 命名导出兼容：mod.X ?? mod.default?.X
   ↓
不可控库错误行为 → 五层防护
   ↓
渲染失败降级显示 <pre>{{ raw }}</pre>
   ↓
动态 import + watch 回调中 await nextTick()
```

详见 [heavy-library-rule.md](heavy-library-rule.md)。

### 四、适用场景与不适用场景

#### 适用场景

- v3 媒体生成工具（PPT/图像/视频）开发与维护
- 调用第三方/外部 API 的全栈项目（fetchWithDiagnostics + 超时分级 + 密钥三级回退）
- 长任务异步处理（视频生成、批量处理、文件转码等）
- LLM 多模态生成产物归档（统一 frontmatter + 文件名时间戳）
- SSE 流式响应（对象映射表事件分发 + AbortError 处理）
- 前端长任务 UI（5 状态机 + 容错轮询 + 三态区分）
- v-html 渲染内容的事件绑定（事件委托 + 生命周期清理）
- 重库动态加载（mermaid/marp/monaco 等，五层错误防护）

#### 不适用场景

- 内部微服务调用（同源、同语言、字段路径稳定，CODING-056 部分不适用）
- 浏览器端 fetch（错误语义不同，CODING-056 针对Node.js undici fetch）
- 同步函数调用（无网络 IO，CODING-057 超时分级不适用）
- 短小的格式化字符串（可直接内联，CODING-062 prompt 存储不适用）
- 单事件类型的简单 SSE（无需对象映射表，CODING-063 部分不适用）
- 一次性 JSON 请求（无流消费，CODING-064 不适用）
- 秒级任务（直接用 SSE 流或单次请求，CODING-065 轮询 UI 不适用）
- Vue 模板中的原生事件绑定（用 @click 等指令，CODING-066 事件委托不适用）
- 体积小的工具库（< 50KB，可静态 import，CODING-067 不适用）
