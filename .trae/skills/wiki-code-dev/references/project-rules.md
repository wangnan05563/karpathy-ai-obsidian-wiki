# 项目硬约束

> ⚠️ **项目特定知识库文档**：本文档含硬编码项目路径（如 `karpathy-wiki/`），这些值来源于项目实际约束沉淀，非配置化参数。可配置的约束参数见 `config/coding-standards-config.md`。

本文档记录项目的强制性编码约束，违反将导致构建失败或运行时错误。

## 前端约束

### 1. Vue 组件必须使用 `<script setup lang="ts">`

```vue
<!-- 正确 -->
<script setup lang="ts">
import { ref } from 'vue';
</script>

<!-- 错误：禁止使用 Options API -->
<script>
export default {
  data() { return {}; }
};
</script>
```

### 2. SSE 路由必须使用 reply.raw.write()

```typescript
// 正确
app.get('/api/wiki/compile', async (request, reply) => {
  reply.raw.writeHead(200, { 'Content-Type': 'text/event-stream', ... });
  reply.raw.write('event: progress\ndata: {...}\n\n');
  reply.raw.end();
});

// 错误：禁止在 SSE 路由中使用 return reply.send()
```

### 3. 必须使用 ref/onMounted/onBeforeUnmount 管理生命周期

```typescript
import { ref, onMounted, onBeforeUnmount } from 'vue';

const cleanup = ref<(() => void) | null>(null);

onMounted(() => {
  cleanup.value = setupSSEListener();
});

onBeforeUnmount(() => {
  cleanup.value?.();
});
```

## 后端约束

### 4. 后端错误必须用 err instanceof Error 守卫

```typescript
try {
  await someAsyncOp();
} catch (err) {
  const msg = err instanceof Error ? err.message : 'Unknown error';
  throw new Error(msg);
}
```

### 5. API Key 仅通过环境变量引用

```typescript
// 正确
const apiKey = process.env.OPENAI_API_KEY;

// 错误：禁止硬编码
const apiKey = 'sk-xxx...';
```

### 6. localOnly 默认 true

所有开发服务器默认只监听 localhost：

```typescript
const server = await app.listen({ port: 3000, host: '127.0.0.1' });
```

### 7. 文件编码必须是 UTF-8 无 BOM

**所有源代码文件**（`.vue` / `.ts` / `.tsx` / `.json` / `.md`）必须以 **UTF-8 无 BOM** 编码保存。
原因：Vite 加载源文件时按 UTF-8 解析，若文件实际是 GBK，浏览器会看到乱码。

**硬性范围（全部都必须是 UTF-8 无 BOM）**：
- ✅ **源码**：`.vue` / `.ts` / `.tsx` / `.js`
- ✅ **元配置**：`.gitignore` / `.editorconfig` / `.vscode/settings.json` / `tsconfig.json` / `package.json`
- ✅ **文档**：根目录所有 `*.md`（`DELIVERY.md` / `README.md` / 概要设计说明书 等）
- ❌ 不允许任何项目级文本文件以 GBK 编码保存

**反面教材（2026-07-10 复发根因）**：
之前修复仅覆盖了 `packages/web/src` 与 `services/api/src` 下的 `.vue` / `.ts`，
但项目根的 `.gitignore` / `.editorconfig` / `.vscode/settings.json` / `DELIVERY.md`
**本身是 GBK 字节流**。Trae / VSCode 重新保存这些文件时按 GBK 写入，
使得"配置已经改为 utf8"但**配置文件的字节流仍是 GBK**，
形成"修了又复发"的死循环。

**多层防御**（缺一不可，v1.2.0 新增提交前 + CI 门禁）：

| 层 | 位置 | 作用 |
|---|---|---|
| 工作区根 | `<workspace>/.vscode/settings.json` | `files.encoding: "utf8"` |
| 项目级 | `karpathy-wiki/.vscode/settings.json` | 项目级覆盖工作区设置 |
| 项目级 | `karpathy-wiki/.editorconfig` | `charset = utf-8`（跨编辑器通用） |
| 项目级 | `karpathy-wiki/.gitattributes` | `working-tree-encoding=UTF-8`（Git 层面强制编码） |
| Pre-commit | `karpathy-wiki/.git/hooks/pre-commit` | **提交前拦检**：GBK 文件直接阻断，给出修复命令 |
| 工具 | `karpathy-wiki/scripts/check-encoding.js` | CI/手动扫描（支持 `--ci` / `--fix` / `--json`） |
| CI 门禁 | `karpathy-wiki/scripts/encode-check.sh` | GitHub Actions 入口，`--ci` 单行 JSON 输出 |
| 工具 | `karpathy-wiki/scripts/fix-encoding-all.ps1` | 智能 GBK → UTF-8 转码，覆盖源码 + 元配置 + 根 .md |
| 工具 | `karpathy-wiki/scripts/clean-volar.js` | 清理 vue-tsc 生成的 Volar 预转换副本 |

**防御时间线**（GBK 文件被阻断的时机）：

```
代码保存 → .editorconfig + .vscode/settings.json 约束 IDE 编码
         → .gitattributes 声明 working-tree-encoding=UTF-8
         → git add → pre-commit hook 扫描暂存区，GBK 文件阻断
         → git push → CI 门禁（encode-check.sh → check-encoding.js --ci）兜底
```

**检测命令**（一个命令查全部）：
```powershell
cd karpathy-wiki
node scripts/check-encoding.js
# 输出示例：扫描 62 个文件（源码 57 + 元配置 5），未发现 GBK 乱码。
# exit 0 = 全部 UTF-8；exit 1 = 有问题文件

node scripts/check-encoding.js --fix
# 自动转码纯 GBK 文件（混合编码文件自动 SKIP）
# 修复范围：源码 + .gitignore + .editorconfig + .vscode/*.json + 根 *.md

node scripts/check-encoding.js --ci
# CI 模式：单行 JSON 输出 {"outcome":"PASS","total":62,"problem":0,"files":[]}
# 用于 GitHub Actions / GitLab CI 日志聚合
```

**故障排查 Checklist**（页面又乱码时按顺序查）：
1. `node scripts/check-encoding.js` → exit 0？
2. 若 exit 1，看输出是 `[META]` 还是 `[SRC]` 问题
3. `[META]` = 元配置/文档是 GBK → 跑 `--fix` 即可
4. `[SRC]` = 源码是 GBK → 跑 `--fix`，或检查 Volar 副本是否需要 `clean-volar.js`
5. 检查 `karpathy-wiki/.editorconfig` 是否存在且字节流是 UTF-8（非 GBK）
6. 检查 `karpathy-wiki/.gitattributes` 是否存在且 `working-tree-encoding=UTF-8`
7. 检查 `<workspace>/.vscode/settings.json` 是否是 `"files.encoding": "utf8"`
8. 检查 `karpathy-wiki/.git/hooks/pre-commit` hook 是否可执行
9. 浏览器强制刷新（Ctrl+Shift+R）清缓存

**违规后果**：
- Vite 加载的 `.vue` / `.ts` 在浏览器显示乱码（0xFFFD 或"锟斤拷"）
- 同一症状会跨页面、跨组件反复出现，难以定位单点原因
- Volar 生成的 `*.vue.js` / `*.ts.js` 预转换副本同样按 GBK 写出，加剧乱码扩散
- `.gitignore` / `.editorconfig` 注释乱码会让 git 排除规则失效、编辑器配置不生效

## 开发流程约束

### 8. 设计文档驱动

任何功能开发必须遵循：
1. 先更新《概要设计说明书》中对应章节
2. 再进行编码实现
3. 最后更新 DELIVERY.md 记录交付清单

### 9. 验证闭环

每次代码变更后必须执行：
```powershell
# 后端类型检查
cd karpathy-wiki/services/api
npx tsc --noEmit

# 前端类型检查
cd karpathy-wiki/packages/web
npx vue-tsc --noEmit
```

两个检查必须 exit 0 才能继续。

### 10. 禁止硬编码主题色值

所有跨主题可见的颜色必须通过 CSS 变量引用，禁止在 `.vue` / `.ts` / `.css` 中硬编码 `rgba(R, G, B, A)` 或 `#hex` 色值。

**允许硬编码的白名单**：
- `rgba(255, 255, 255, X)` 纯白高光（所有主题通用）
- `transparent` / `inherit` / `currentColor`

**检测方式**：
```powershell
# 搜索 packages/web/src/views/ 下的硬编码 rgba
# 排除 rgba(255, 255, 255, X) 白名单
```
使用 Grep 工具搜索 `rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,` 模式，排除 255, 255, 255 的纯白高光。

详细规范参见 [theming-and-css-variables.md](theming-and-css-variables.md)。

## 配置管理约束

### 11. 多实例配置必须按维度独立持久化（CODING-011）

同一系统中存在多个同类配置实例（如多 LLM 预设、多账号、多环境）时，必须按维度独立持久化，localStorage key 必须包含维度标识（如 `prefix:${dimensionKey}`），禁止共享单一存储位置。

**原因**：共享单一 key 会导致切换实例时覆盖彼此数据，后切换的实例覆盖前一个，用户再次切回时数据已丢失。

**检查方式**：使用 Grep 工具搜索 `localStorage.setItem` 调用，确认多实例场景的 key 是否包含维度标识。

详细规范参见 [multi-instance-config.md](multi-instance-config.md)。

### 12. 脱敏值回传必须用正向匹配判断（CODING-012）

敏感字段（密码/API Key）以脱敏形式显示时，提交判断必须用 `value.startsWith('****')` 正向匹配识别脱敏值，禁止用 `value && !value.startsWith('****')` 这类 truthy 反向匹配。

**原因**：truthy 反向匹配会把空串误判为"未修改"（空串是 falsy，短路后进入 else 分支），导致用户清空字段时无法提交空值。

**检查方式**：使用 Grep 工具搜索 `startsWith\('\*\*\*\*'\)` 或 `startsWith\("\*\*\*\*"\)` 附近的判断逻辑，确认是正向匹配而非 truthy 反向匹配。

详细规范参见 [multi-instance-config.md](multi-instance-config.md)。

### 13. 前端影响后端的状态变更必须同步后端（CODING-013）

前端本地状态（localStorage/内存）如果影响后端行为，变更后必须同步到后端。同步失败不阻断用户操作，使用 try-catch 降级处理。

**原因**：前端切换状态后若不同步后端，后端 SSE 流式响应仍按旧状态处理，导致用户感知与实际行为不一致；同步失败直接抛错会阻断用户操作，体验更差。

**检查方式**：审查前端 localStorage 写入逻辑，确认是否伴随后端同步调用；确认同步调用是否包裹在 try-catch 中。

详细规范参见 [multi-instance-config.md](multi-instance-config.md)。

### 14. 可编辑配置必须提供恢复默认值能力（CODING-014）

所有可编辑配置必须提供恢复默认值的能力，包含五要素：后端 `defaultConfig()` 函数 + reset 接口 + 前端恢复按钮 + 确认对话框 + 恢复后清除前端持久化。

**原因**：用户配置错误时若无恢复机制，系统可能不可用且无法回退；缺少确认对话框易误操作，缺少前端持久化清除会导致旧值残留、恢复后状态不一致。

**检查方式**：审查配置页面是否同时存在保存按钮和恢复按钮；确认后端是否有 reset 接口和 `defaultConfig()` 函数；确认恢复逻辑是否清除 localStorage。

详细规范参见 [multi-instance-config.md](multi-instance-config.md)。

### 15. 同类功能多入口必须共享同一存储 key（CODING-015）

同类功能如果有多个入口（如 Config.vue 的 applyPreset 和 model.ts 的 switchModel），必须共享同一存储 key，一个入口更新后另一个入口能读取到最新值。

**原因**：不同入口写入不同 key 会导致状态分叉，A 入口切换后 B 入口读取的还是旧值，用户感知混乱、行为不一致。

**检查方式**：使用 Grep 工具搜索同类功能的 localStorage 操作，确认是否引用同一 key 常量；审查是否存在硬编码不同 key 的情况。

详细规范参见 [multi-instance-config.md](multi-instance-config.md)。

### 16. 预设列表必须集中管理（CODING-016）

预设列表（如 LLM 预设）应集中管理在配置文件或常量中，业务代码通过引用该常量获取预设列表，禁止在多个文件硬编码预设。

**原因**：预设散落在多个文件时，新增/删除预设需改多处，容易遗漏导致校验逻辑与展示逻辑脱节；集中管理后修改只需改一处。

**检查方式**：使用 Grep 工具搜索预设 ID 字符串（如 `'gpt4'`），确认是否只出现在集中定义的常量文件中，业务代码是否通过引用常量获取。

详细规范参见 [multi-instance-config.md](multi-instance-config.md)。

## 违反后果

| 违反项 | 后果 |
|---|---|
| 不使用 `<script setup lang="ts">` | vue-tsc 类型检查失败 |
| SSE 路由使用 reply.send() | 流提前关闭，客户端收不到增量数据 |
| 不使用 err instanceof Error | TypeScript strict 模式报错 |
| 硬编码 API Key | 安全风险，CI/CD 扫描会阻断 |
| 跳过设计文档更新 | 文档与代码不一致，后续维护困难 |
| 跳过类型检查 | 运行时类型错误概率增加 |
| 硬编码主题色值 | 切换主题后背景/文字不可读，需逐文件排查替换 |

## 配置读取一致性（复盘新增）

### 规则：同一配置项的所有读取入口必须使用统一函数

```typescript
// 正确：新增 getEffectiveApiKey() 后，所有入口都使用它
import { getEffectiveApiKey } from './config.js';
const apiKey = getEffectiveApiKey(config);  // 启动入口
const isSet = Boolean(getEffectiveApiKey(config));  // API GET 入口

// 错误：新增函数后启动入口仍用旧逻辑
const apiKey = process.env[config.llm.apiKeyRef];  // 忽略了 config.json 的 apiKey
```

**检查清单**：新增配置读取函数后，必须 grep 所有读取入口确认一致。

## 热更新闭环（复盘新增）

### 规则：可热更新字段必须同时更新 updateConfig + 路由层调用

```typescript
// 正确：保存后调用 adapter.updateConfig 热更新
const merged = await saveAiConfig(updates);
adapter.updateConfig({
  provider: merged.llm.provider,
  baseUrl: merged.llm.baseUrl,
  model: merged.llm.model,
  apiKey: getEffectiveApiKey(merged),
});

// 错误：只保存到文件，不热更新 adapter
const merged = await saveAiConfig(updates);
// 缺少 adapter.updateConfig()，需重启才生效
```

## 脱敏值回传处理（复盘新增）

### 规则：前端回传脱敏值时，后端必须正确识别为"未修改"

```typescript
// 正确：识别脱敏值
if (body.apiKey.startsWith('****')) {
  apiKey = undefined;  // 不修改
}

// 错误：脱敏值当新值写入
const apiKey = body.apiKey;  // 把 ****xxxx 当真实 Key 存储
```

## 预设配置外置（复盘新增）

### 规则：预设列表集中定义在后端常量，前端通过 API 获取

```typescript
// 正确：后端定义预设常量
const LLM_PRESETS = [...];
app.get('/api/ai/presets', () => LLM_PRESETS);

// 前端通过 API 获取
const presets = await fetch('/api/ai/presets').then(r => r.json());

// 错误：前端硬编码预设列表
const PRESETS = [{ key: 'openai', ... }];  // 与后端重复
```

## Vue 3 类型收窄（复盘新增）

### 规则：ref<T|null> 在 await 后访问必须用局部变量或计算属性

```typescript
// 正确：用局部变量收窄类型
const result: AiTestResult = await res.json();
aiTestResult.value = result;
if (result.ok) { ... }  // 局部变量已收窄

// 正确：模板中用计算属性
const testResultText = computed(() => {
  const r = aiTestResult.value;
  return r ? (r.ok ? '成功' : r.detail) : '';
});

// 错误：await 后直接访问 ref
aiTestResult.value = await res.json();
if (aiTestResult.value.ok) { ... }  // vue-tsc 报错 possibly null
```

## ESM 与模块接线约束（复盘新增）

> 4 条规则的完整版参见 [esm-module-guard-rule.md](esm-module-guard-rule.md)。所有可变参数从 `config/tech-stack.json` 的 `esm` 字段读取，禁止在业务代码或规则文件硬编码。

### 17. ESM 模块下禁止使用 `__dirname` / `__filename`（CODING-017）

**规则**：Node.js ESM 模式下禁止以任何形式引用 `config.esm.forbidden_globals` 列表中的全局变量，必须改用 `config.esm.dirname_derive_pattern` 派生当前目录，并确保 `config.esm.required_imports` 已导入。

**检查方式**：Grep `__dirname|__filename` 在 `.ts` / `.mts` / `.js` / `.mjs` 文件中的引用，命中的全部违规。

### 18. 静态分析建议必须人工验证运行时语义（CODING-018）

**规则**：`config.esm.static_analysis_tools` 列表工具产出的修复建议必须按 `config.esm.manual_verification_checklist` 三项（`operand_throws_on_reference` / `type_guard_bypassed` / `side_effect_changed`）逐项人工验证，禁止盲目采纳"语义等价"的自动修复。

**检查方式**：审查近期合入的"简化三元为 `?? `" 类提交，确认每条建议都有验证结论。

### 19. 新增模块必须完成接线三步骤（CODING-019）

**规则**：新增 routes / workflows / services 模块后，必须在 `config.esm.wiring_entry_file`（默认 `src/index.ts`）中完成 `config.esm.wiring_required_steps` 三步：① `import` 语句 ② `instantiate` 实例化 ③ `registerRoute` 注册调用。

**检查方式**：Grep 新增模块的导出函数名（如 `registerTunnelRoute`）在 `wiring_entry_file` 中是否被调用，未命中即为接线遗漏。

### 20. Edit / Write 后必须验证文件编码未损坏（CODING-020）

**规则**：Edit / Write 修改含非 ASCII 字符（中文/日文/韩文/Emoji）的文件后，必须立即按 `config.esm.encoding_verification_method`（`UTF8Encoding(false, true)` 严格解码）验证编码未损坏。检测失败时按 `config.esm.encoding_failure_recovery` 五步（`git stash` → `git checkout HEAD` → `git stash pop` → `re-edit` → `re-verify`）恢复后重新编辑。

**检查方式**：Edit / Write 后立即运行 `Test-FileUtf8Strict` 复检；UI 出现"???"或"锟斤拷"时回溯最近一次 Edit 操作。

## Async 可靠性约束（复盘新增）

> 5 条规则的完整版参见 [async-reliability-rule.md](async-reliability-rule.md)。所有可变参数从 `config/tech-stack.json` 的 `async_reliability` 字段读取，禁止在业务代码或规则文件硬编码。

### 21. async 调用必须设置超时（CODING-021）

**规则**：禁止直接 `await` 任何可能阻塞的 async 调用（IPC、网络、文件 I/O、外部进程通信）。必须用 `asyncio.wait_for(coro, timeout=config.async_reliability.default_call_timeout_sec)`（Python）或 `Promise.race([promise, timeout])`（TypeScript）包裹。

**检查方式**：Grep `await\s+\w+\.` 在 async 函数中的调用，确认是否被 `wait_for` / `Promise.race` 包裹。白名单见 `config.async_reliability.timeout_whitelist`。

### 22. 事件循环阻塞场景必须使用线程级保护（CODING-022）

**规则**：当 async 调用可能阻塞整个事件循环（如 Playwright IPC、Node.js native addon）时，心跳/看门狗逻辑必须用 `threading.Thread`（Python）或 `worker_threads`（Node.js）实现，禁止用 `asyncio.Task` / `Promise.then`。

**检查方式**：审查心跳/看门狗逻辑，若涉及 `config.async_reliability.blocking_risk_apis` 列表中的 API，必须确认心跳使用线程实现。

### 23. 状态文件通信必须独立于业务事件循环（CODING-023）

**规则**：子进程通过状态文件与主进程通信时，状态文件的 `ts` 字段更新逻辑必须由独立线程写入，或由业务循环内的同步代码写入且循环间隔 ≤ `config.async_reliability.heartbeat_max_interval_sec`。

**检查方式**：Grep 状态文件写入函数（如 `_write_status`、`_emit_status`），确认调用方在独立线程中或循环间隔达标。

### 24. async 调用超时必须提供兜底数据（CODING-024）

**规则**：`asyncio.wait_for` / `Promise.race` 超时后必须有兜底数据返回，禁止直接抛错终止流程。兜底数据通过 `best_holder` 模式（可变容器）或闭包变量传递。

**检查方式**：审查 `asyncio.wait_for` 的 except 分支，确认有兜底数据赋值而非直接 raise。

### 25. 长时 async 任务必须多层超时防护（CODING-025）

**规则**：长时 async 任务必须设置多层超时：单次调用超时（`default_call_timeout_sec`）+ 阶段硬超时（`stage_hard_timeout_sec`）+ 整体任务超时（`task_total_timeout_sec`）。

**检查方式**：审查长时 async 任务的超时配置，确认至少有 2 层超时保护。

## 工程稳定性约束（v1.8.0 复盘新增）

> 7 条规则的完整版参见对应规则文件。所有可变参数从 `config/coding-standards-config.md` 的对应字段读取，禁止在业务代码或规则文件硬编码。

### 26. 类型检查缓存清理（CODING-026）

**规则**：vue-tsc / tsc 报告与源文件当前内容不一致的"幽灵错误"时，必须先清理 `typecheck_cache.incremental_cache_files`（如 `tsconfig.tsbuildinfo`）+ `vite_cache_dirs`（如 `.vite`）+ `stale_artifact_patterns`（如 `src/**/*.js` 旧编译产物）再重新运行 `typecheck_cache.typecheck_command`，禁止用 `typecheck_cache.prevent_bypass_assertions` 中的断言（`as any` / `! postfix` / `@ts-ignore`）绕过。

**检查方式**：当 vue-tsc 报错但 Read 源文件对应行号显示代码已正确收窄类型时，判定为幽灵错误，必须清缓存而非加断言。

详细规范参见 [typecheck-cache-rule.md](typecheck-cache-rule.md)。

### 27. Composable API 先读后用（CODING-027）

**规则**：使用非自己编写的 composable / hook / store 前，必须 Read 源码确认 `composable_api.required_confirmation`（导出形状、方法签名、setup 顺序）。诊断代码禁止调用 `$dispose` / `_s.delete` 重建运行时 store（`composable_api.diagnostic_code_must_not_rebuild`）。

**检查方式**：对调用 `useXxx()` 的位置，检查是否有最近的 Read 源码记录；Grep `\$dispose|_s\.delete` 调用确认是否在测试/诊断脚本中误重建 store。

详细规范参见 [composable-api-rule.md](composable-api-rule.md)。

### 28. 混合类型运行时分流（CODING-028）

**规则**：类型从 T 升级为 U（如 `string` → `{ key: string, ... }`）且代码需同时处理新旧版本时，必须用 `isXxx` helper 函数 + `mixed_type_dispatch.required_type_guards`（`typeof` / `in` / `instanceof`）运行时分流，禁止用 `mixed_type_dispatch.forbidden_assertions`（`as any` / `as unknown as U`）强制断言。

**检查方式**：Grep `forbidden_assertions` 中的模式，在涉及类型升级的代码段中命中即违规；数组元素 / 函数参数类型为 `T | U` 联合类型时必须有对应 `isU` helper 函数。

详细规范参见 [mixed-type-dispatch-rule.md](mixed-type-dispatch-rule.md)。

### 29. Vue SFC 单 script 块（CODING-029）

**规则**：`.vue` 文件只能有 `sfc_script_block.allowed_blocks`（默认 `<script setup lang="ts">`）单 script 块。例外情况（`sfc_script_block.exception_conditions`：name 导出 / inheritAttrs:false / 自定义选项 / 第三方库）必须显式注释 `sfc_script_block.exception_comment_pattern`（`// 例外：`）说明用途。

**检查方式**：对 `.vue` 文件用正则 `<script(\s|>)` 匹配统计块数量；双 script 块时检查首行是否包含例外注释。

详细规范参见 [sfc-single-script-rule.md](sfc-single-script-rule.md)。

### 30. E2E 测试前置服务检查（CODING-030）

**规则**：运行 E2E 测试前必须遍历 `e2e_precheck.required_ports` 检查端口监听（状态为 `port_check_state`），并调用 `e2e_precheck.health_check_endpoint` 验证返回 `health_check_expected_status`。检查失败时中止测试并提示 `service_start_script`，禁止直接运行用例。`auto_start_on_failure: true` 时自动启动服务。

**检查方式**：测试套件入口文件必须包含前置检查代码；前置检查失败时必须中止测试（避免误报"全部失败"）。

详细规范参见 [e2e-precheck-rule.md](e2e-precheck-rule.md)。

### 31. 测试用例与代码结构同步（CODING-031）

**规则**：代码变更影响 DOM 结构（class / id / 层级）时，必须 Grep `test_case_sync.test_file_patterns` 中的测试文件，同步更新引用了被删除选择器的测试用例。禁止 `try/except` 静默吞掉选择器失效错误（`test_case_sync.silent_failure_forbidden: true`），必须 `record(..., False, str(e))` 标记失败。代码与测试用例必须在同一 commit（`test_case_sync.require_same_commit: true`）。

**检查方式**：`git diff` 识别 template 段 class / id 变更 → Grep 测试脚本中是否引用被删除的选择器 → 检查 except 分支是否静默吞错。

详细规范参见 [test-case-sync-rule.md](test-case-sync-rule.md)。

### 32. 阅读视野优化与输入区固定（CODING-032）

**规则**：阅读型视图（`reading_viewport.applicable_views`：Query / Reader / Document / Chat / Browse）必须满足：① 标题头区域高度 ≤ `reading_viewport.max_header_ratio`（默认 15%）× 可视高度 ② 内容区域 ≥ `reading_viewport.min_content_ratio`（默认 75%）× 可视高度 ③ 输入区 `position: sticky; bottom: 0` + 毛玻璃背景 + `z-index` ≥ `reading_viewport.input_bar_z_index`（默认 2）。

**检查方式**：视图文件名匹配 `applicable_views` 时启用检查；通过 DevTools 测量标题头 / 内容区 / 输入区比例；CSS 中 `.input-bar` 必须有 `position: sticky; bottom: 0` + 半透明 + `backdrop-filter: blur()`。

详细规范参见 [reading-viewport-rule.md](reading-viewport-rule.md)。
