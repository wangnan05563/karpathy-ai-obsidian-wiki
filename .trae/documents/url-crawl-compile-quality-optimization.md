# URL 爬取与编译链路质量优化计划

## Context（为什么做这个改动）

基于对 `http://www.shcpe.com.cn/content/shcpe/index.html` 爬取编译结果的审查，发现"编译完成"流程真实跑通但产物质量差，三个根因：

1. **P1 爬取噪声**：shcpe 是 Ajax 动态站，`renderJs: false` 下 `extractHtmlContent`（[url-crawl.ts:253](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/utils/url-crawl.ts#L253)）未过滤 `<script>/<style>/<template>` 和 Handlebars 模板，原始数据充斥 JS 代码与 `{{#if data}}` 模板语法，LLM 从中抽取出空洞概念页。
2. **P2 实体重复**：compile 经 harness LLM 执行，LLM 每次自选 slug（`shanghai-commercial-paper-exchange` vs `上海票据交易所` vs `shanghai-bill-exchange`），且 [appendIndex](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/vault/vault-service.ts#L349) 直接 appendFile 无查重，导致 index.md 同实体 10+ 条目。
3. **P3 日志缺失**：[index.ts:179](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/index.ts#L179) pino logger 无 file transport，`logs/api-dev.log` 为 0 字节，运行时无法事后排障。

用户已确认方案：P1 轻量 HTML 解析增强（零依赖）、P2 index 查重 + 实体 title 去重。P3 日志落盘（双写 stream，无新依赖）。

预期结果：爬取文本去除 JS/CSS/模板噪声；编译不再产生重复实体与 index 条目；后端 HTTP 日志落盘可查。

---

## P1：轻量 HTML 解析增强

**文件**：[api/src/utils/url-crawl.ts](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/utils/url-crawl.ts)

**改动函数**：`extractHtmlContent`（line 253-267）

**当前流程**：去注释 → h1-6 转 markdown → 去闭合标签 → 去标签 → 解码实体 → 压缩空白

**增强点**（在"去注释"之后、"h1-6 转换"之前插入）：
1. 移除 `<script[\s\S]*?<\/script>` 块（JS 代码）
2. 移除 `<style[\s\S]*?<\/style>` 块（CSS 样式）
3. 移除 `<noscript[\s\S]*?<\/noscript>` 块
4. 移除 `<template[\s\S]*?<\/template>` 块（Vue/Handlebars 模板占位）
5. 移除 `<svg[\s\S]*?<\/svg>` 块（内联图标，无文本价值）
6. 移除 Handlebars 模板语法 `{{[\s\S]*?}}`（shcpe 用 Handlebars 渲染，模板占位符 `{{#if data}} {{title}} {{/if}}` 无语义）

**为什么这样做**：shcpe 首页 91KB HTML 中 JS+CSS+模板占 80%+，当前 extractHtmlContent 只去标签不去块，导致 JS 代码（`$(".eui-header-wrapper")...`）和模板（`{{#each data}}`）混入正文。移除块级元素后，剩余文本是真实可见内容（导航菜单、标题、友情链接），虽仍拿不到 Ajax 正文，但 LLM 抽取质量显著提升。

**不做什么**：不引入 Playwright/Puppeteer（用户已选轻量方案）。Ajax 动态正文问题留待后续单独立项。

**测试**：对 shcpe 首页 HTML 片段跑 extractHtmlContent，断言输出不含 `$(".`、`{{#if`、`function(`、`background:` 等噪声 token。

---

## P2：index 查重 + 实体 title 去重

### P2.1 appendIndex 查重

**文件**：[api/src/vault/vault-service.ts](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/vault/vault-service.ts)

**改动函数**：`appendIndex`（line 349-353）

**当前实现**：直接 `fs.appendFile` 写入 `- [[${pageName}]] — ${summary}\n`

**改造**：
1. 读取 index.md 当前内容（用 `this.readFile('index.md')` 复用 mtime 缓存）
2. 正则检查 `^\- \[\[${pageName}\]\]` 是否已存在（按行匹配，pageName 做 regex escape）
3. 已存在则跳过追加，返回 `{ ok: true, skipped: true, reason: 'duplicate' }`
4. 不存在则追加，返回 `{ ok: true, skipped: false }`

**返回值变更**：`appendIndex` 当前返回 `Promise<void>`，改为 `Promise<{ ok: boolean; skipped: boolean }>`。调用方 `append_index` 工具 handler（[compile-workflow.ts:198-202](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/workflows/compile-workflow.ts#L198-L202)）透传返回值，让 LLM 知道是否跳过。

**为什么按 pageName 而非 summary 查重**：pageName 是 `[[...]]` 内的页面标识，summary 是描述文本。同一实体多次编译 summary 可能不同，但 pageName 稳定。按 pageName 查重避免误判，又能拦住"上海票据交易所"10+ 条目这类重复。

### P2.2 实体 title 去重（write_file 前重定向）

**文件**：[api/src/workflows/compile-workflow.ts](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/workflows/compile-workflow.ts)

**改动位置**：`write_file` 工具 handler（line 177-186）

**当前实现**：`ensurePageTypeField` → `ensureEntitiesField` → `vault.writeFile(p, finalContent)`

**改造**（在 writeFile 前插入去重重定向）：
1. 解析 content 的 frontmatter `title` 字段
2. 调用 `vault.findPageByTitle(title, targetDir)`（新增方法，见下）
3. 若命中已有页面（且非当前 path 本身），则把 `p` 重定向到已有路径（覆盖更新已有文件，而非新建重复文件）
4. 日志记录重定向行为（供排障）

**VaultService 新增方法** `findPageByTitle(title: string, dir: string): Promise<string | null>`：
- 扫描指定目录下所有 .md 文件
- 解析每个文件的 frontmatter title
- 规范化比对（`normalizeTitle`：小写 + 去空格 + 去标点 + 去括号内英文别名）
- 返回命中文件的相对路径，无命中返回 null

**normalizeTitle 规则**（覆盖中英文同实体场景）：
1. 小写 + 去首尾空格
2. 去标点（`()`、`（）`、`-`、`—`、`:`、`：`）
3. 若 title 含括号内英文（如 `上海票据交易所 (Shanghai Commercial Paper Exchange)`），提取括号内英文单独规范化
4. 比对时：主名称规范化相同 OR 一方括号内英文与另一方主名称规范化相同

**为什么不强制合并内容**：重定向 path 后，`writeFile` 覆盖已有文件。LLM 生成的新内容会覆盖旧内容。这是"以新替旧"的合并策略，简单且符合"最新编译优先"语义。若需保留旧内容的部分字段（如 tags），属后续增强。

**边界**：仅对 `entities/`、`concepts/` 目录做 title 去重（这两个目录重复最严重）。`qa/`、`solutions/` 按 rawId 命名天然不重复，跳过。

---

## P3：后端日志落盘

**文件**：[api/src/index.ts](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/index.ts)

**改动位置**：Fastify logger 配置（line 178-191）

**当前实现**：`logger: { level, serializers }`，pino 默认输出 stdout，tsx 运行时未重定向。

**改造**（自定义双写 stream，无新依赖）：
1. 在 logger 配置前，创建 `logs/api-dev.log` 的 `fs.createWriteStream(dest, { flags: 'a' })`
2. 创建自定义 Writable `dualStream`：`write(chunk)` 时同时写 `process.stdout` 和文件流
3. logger 配置加 `stream: dualStream`

**为什么用自定义双写而非 pino transport**：
- pino `transport: { target: 'pino/file' }` 在 ESM + tsx 下用 worker thread，有兼容性风险
- pino multistream 需要额外了解 pino 内部 API
- 自定义 Writable 是 Node.js 原生 stream，零依赖、零兼容性风险、最可控
- 双写保证控制台仍可见（开发体验）+ 文件持久化（事后排障）

**路径解析**（CODING-001 硬约束：禁用 CWD）：
- logFilePath 用 `path.join(dirname, '..', 'logs', 'api-dev.log')`，其中 `dirname` 已在 index.ts:50 由 `fileURLToPath(import.meta.url)` 解析
- 启动时 `fs.mkdir` 确保 logs 目录存在

**优雅停止**（CODING-013）：文件流在进程退出时需 end()。在现有 shutdown 钩子（若有）或 `process.on('SIGINT'/'SIGTERM')` 中加 `fileStream.end()`。需检查 index.ts 是否已有 shutdown 钩子，有则复用，无则新增。

**配置化**（CODING-007）：logFilePath 从 `config.logging.logFilePath` 读取，默认 `logs/api-dev.log`。在 [api/config.json](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/config.json) 的 `logging` 字段加 `logFilePath` 项。

### P3.2 悬空链接（仅报告，不自动改）

**范围**：本轮不做代码改动。`buildLinkGraph`（[vault-service.ts:455](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/vault/vault-service.ts#L455)）已能识别悬空链接（`nameToPath.get(target)` 为 null）。后续可在 health-check 路由报告悬空链接清单，或提供清理脚本。自动改写悬空 `[[...]]` 风险高（破坏 LLM 前向链接意图），本轮不做。

---

## 涉及文件清单

| 文件 | 改动 | P 级 |
|------|------|------|
| [api/src/utils/url-crawl.ts](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/utils/url-crawl.ts) | `extractHtmlContent` 增加 script/style/template/svg/handlebars 过滤 | P1 |
| [api/src/vault/vault-service.ts](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/vault/vault-service.ts) | `appendIndex` 加查重；新增 `findPageByTitle` + `normalizeTitle` | P2 |
| [api/src/workflows/compile-workflow.ts](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/workflows/compile-workflow.ts) | `write_file` handler 加 title 去重重定向；`append_index` handler 透传 skipped | P2 |
| [api/src/index.ts](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src/index.ts) | logger 加双写 stream + 文件流优雅关闭 | P3 |
| [api/config.json](file:///d:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/config.json) | logging 字段加 logFilePath | P3 |

---

## 验证方案

### 1. 类型检查门禁（CODING-046）
```powershell
# 后端
cd d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\api
npx tsc --noEmit
```
退出码必须为 0。

### 2. 编码门禁（CODING-008/009）
```powershell
node scripts/check-encoding.js
```
所有改动文件 UTF-8 无 BOM。

### 3. P1 单元测试
对 `extractHtmlContent` 喂入 shcpe 首页 HTML 片段（含 `<script>`、`{{#if}}`），断言输出不含：
- `$(".` / `function(` / `var `（JS）
- `{{` / `}}`（Handlebars）
- `background:` / `filter:`（CSS）

### 4. P2 集成测试
- `appendIndex('上海票据交易所', '描述A')` → 追加，skipped=false
- `appendIndex('上海票据交易所', '描述B')` → 跳过，skipped=true
- 检查 index.md 只新增 1 条
- `write_file` 写 `entities/test-entity.md`（title: 测试实体）→ 正常写入
- 再写 `entities/test-entity-2.md`（title: 测试实体）→ 重定向到 `entities/test-entity.md`，不新建文件

### 5. P3 日志落盘验证
- 启动服务后 `Invoke-WebRequest http://localhost:3000/api/about`
- 检查 `logs/api-dev.log` 非空且含 `incoming request` / `request completed`
- 控制台仍同步输出（双写验证）

### 6. 端到端回归
重新爬取 shcpe 首页（小范围 maxPages=3），检查：
- 原始数据 `raw/input-*.md` 不含 JS 代码块（P1 生效）
- 编译产物无重复实体文件（P2 生效）
- index.md 无重复条目（P2 生效）
- `logs/api-dev.log` 记录了爬取与编译请求（P3 生效）
