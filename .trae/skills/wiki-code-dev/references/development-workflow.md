# 开发工作流复盘（项目级）

本文件记录 Karpathy-Wiki 项目级开发工作流的复盘，按"成功步骤 / 不确定性与失败点 / 可抽象流程 / 适用场景"四维度提炼。每次复盘日期以章节标题标注，新复盘追加在文件末尾。

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
