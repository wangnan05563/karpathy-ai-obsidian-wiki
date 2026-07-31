# prompt 单点存储规则（CODING-062）

> 复盘来源：v3 媒体生成工具开发中，LLM prompt 模板散落在多个工作流文件中（query-workflow.ts 内联一段、media-generation-workflow.ts 内联一段、podcast-workflow.ts 内联一段），修改 prompt 需重新编译且易遗漏。统一收敛到 `prompts/*.md` 单一目录，运行时按需 `fs.readFile` 加载，热加载生效，多个工作流共用同一目录。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `prompt_store` 字段读取，禁止在规则文件中硬编码目录名或文件名模式。

## 规则

**LLM prompt 模板管理必须遵守四项契约**：

1. **单点存储**：所有 LLM prompt 模板存放在 `prompt_store.directory`（默认 `prompts/`）单一目录
2. **运行时加载**：运行时按需 `fs.readFile` 加载，禁止在源码中内联 prompt 字符串
3. **多工作流共用**：多个工作流（query/multimodal/podcast/media）共用同一目录，按文件名区分用途
4. **热加载生效**：修改 prompt 不需重新编译，文件改动后下次加载即生效（带缓存的可配置 TTL）

## 适用场景

- LLM prompt 模板管理（系统提示词、few-shot 示例、输出格式约束等）
- 多个 workflow 共用 prompt 目录（避免重复内联）
- 需要 prompt 工程师独立维护 prompt（不修改源码）
- A/B 测试 prompt（替换文件即生效，无需发版）

## 不适用场景

- 短小的格式化字符串（如 `请把以下内容翻译为英文: ${text}`，可直接内联）
- 包含敏感信息的 prompt（如 API key，应从环境变量读取）
- 编译时确定的常量字符串（如错误消息模板，可内联）
- 动态拼接的 SQL（应用参数化查询，非 prompt 模板）
- 客户端可见的文案（应用 i18n 资源文件，非 prompt 模板）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `prompt_store.enabled` | `true` | 是否启用 prompt 单点存储守卫 |
| `prompt_store.severity` | `error` | 违规严重级别 |
| `prompt_store.directory` | `prompts/` | prompt 模板存放目录（相对项目根） |
| `prompt_store.file_pattern` | `*.md` | prompt 模板文件名模式 |
| `prompt_store.cache_ttl_ms` | `0` | 加载缓存 TTL（0 = 不缓存，每次读盘；>0 = 缓存 N 毫秒） |
| `prompt_store.encoding` | `utf-8` | prompt 文件编码 |
| `prompt_store.allow_inline_threshold` | `200` | 内联允许阈值（≤ 此字符数的短 prompt 可内联，单位：字符） |

## 检查方式

1. **目录检查**：所有 prompt 模板必须在 `prompt_store.directory` 目录下，禁止散落到 src/ 各处
2. **运行时加载检查**：源码中不得出现长度 > `allow_inline_threshold` 的 prompt 字符串字面量，必须改为 `fs.readFile` 加载
3. **多工作流共用检查**：query/multimodal/podcast/media 等 workflow 的 prompt 加载函数必须指向同一 `prompt_store.directory`
4. **热加载检查**：`cache_ttl_ms` 为 0 时每次读盘（最热加载）；>0 时缓存过期后重新读盘；禁止用 `require()` / `import` 静态加载（无法热加载）
5. **编码检查**：prompt 文件必须用 `prompt_store.encoding`（默认 utf-8）保存，含中文时严格 UTF-8 无 BOM

## 正确示例

```typescript
// services/api/src/services/prompt-loader.ts
import { readFileSync } from 'fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from '../config.js';

const ps = config.prompt_store;
const dirname = path.dirname(fileURLToPath(import.meta.url));
const promptDir = path.resolve(dirname, '../../', ps.directory);

const cache = new Map<string, { content: string; loadedAt: number }>();

/**
 * 加载 prompt 模板——单点存储 + 热加载
 * 为什么用 fs.readFile 而非 import：import 是静态加载，编译时确定，
 * 修改 prompt 需重新编译；fs.readFile 运行时加载，修改文件后下次调用即生效。
 */
export function loadPrompt(name: string): string {
  const filePath = path.join(promptDir, `${name}.md`);
  const now = Date.now();
  const cached = cache.get(name);

  // ✅ 缓存未过期则用缓存
  if (cached && ps.cache_ttl_ms > 0 && now - cached.loadedAt < ps.cache_ttl_ms) {
    return cached.content;
  }

  // ✅ 运行时加载，热加载生效
  const content = readFileSync(filePath, ps.encoding as BufferEncoding);
  cache.set(name, { content, loadedAt: now });
  return content;
}

/**
 * 清除缓存（手动触发热加载）
 */
export function clearPromptCache(): void {
  cache.clear();
}
```

```typescript
// services/api/src/workflows/media-generation-workflow.ts
import { loadPrompt } from '../services/prompt-loader.js';

// ✅ 从 prompts/ 目录加载，不内联
const imagePromptTemplate = loadPrompt('media-image-generation');
const videoPromptTemplate = loadPrompt('media-video-generation');

async function generateImage(prompt: string): Promise<string> {
  // ✅ 用模板拼接，prompt 内容来自文件
  const finalPrompt = imagePromptTemplate.replace('{user_prompt}', prompt);
  return await callLLM(finalPrompt);
}
```

```
prompts/
├── media-image-generation.md      # 图像生成 prompt
├── media-video-generation.md      # 视频生成 prompt
├── media-ppt-generation.md        # PPT 生成 prompt
├── query-default.md               # 默认查询 prompt
├── query-mindmap.md               # 思维导图 prompt
└── podcast-generation.md          # 播客生成 prompt
```

## 错误示例

```typescript
// ❌ 错误：prompt 内联在源码中，修改需重新编译
const imagePrompt = `
你是一个图像生成助手。
请根据用户的描述生成图像。
用户描述: {user_prompt}
要求:
1. 风格: 写实
2. 尺寸: 1024x1024
3. 质量: 高
`; // ⚠️ 长达 200+ 字符的 prompt 内联，修改需重新编译

// ❌ 错误：prompt 散落在多个工作流文件，无统一目录
// query-workflow.ts
const queryPrompt = '你是一个查询助手...';
// media-generation-workflow.ts
const mediaPrompt = '你是一个媒体生成助手...'; // ⚠️ 散落，难维护

// ❌ 错误：用 import 静态加载，无法热加载
import imagePrompt from '../../prompts/media-image-generation.md'; // ⚠️ 编译时确定，无法热加载

// ❌ 错误：缓存永不过期，修改 prompt 不生效
let cachedPrompt: string | null = null;
function getPrompt() {
  if (cachedPrompt) return cachedPrompt; // ⚠️ 永久缓存，热加载失效
  cachedPrompt = readFileSync('prompts/x.md', 'utf-8');
  return cachedPrompt;
}

// ❌ 错误：prompt 文件用 GBK 编码，含中文时乱码
const content = readFileSync('prompts/x.md', 'gbk'); // ⚠️ 应用 utf-8
```

## 适配新项目

- 适配多语言 prompt：`directory` 改为 `prompts/{lang}/`，按 Accept-Language 加载
- 适配 prompt 版本管理：`directory` 改为 `prompts/v1/`、`prompts/v2/`，配置指定当前版本
- 适配数据库存储：prompt 存到数据库 `prompts` 表，按 name 查询，支持版本回滚
- 适配 prompt 工程平台：prompt 存到 LangSmith / Promptflow 等平台，运行时 API 拉取
- 适配加密 prompt：prompt 文件加密存储，运行时解密加载（保护知识产权）

## 与其他规则的关系

- 与 CODING-060（媒体归档 frontmatter 标准化）联动：归档 frontmatter 中的 prompt 字段值从 prompts/ 目录加载
- 与 CODING-061（会话存储双层淘汰）联动：会话中存储的 prompt 内容从 prompts/ 目录加载，不在源码内联
- 与 CODING-001（路径解析禁用 CWD）联动：prompts 目录路径必须基于 `import.meta.url` 或配置锚点，禁止依赖 `process.cwd()`
- 与 CODING-002（写后即刷）联动：若 prompts 目录有内存缓存，修改 prompt 文件后需手动 clearPromptCache() 刷新
- 与 CODING-020（编码守卫）联动：prompt 文件含中文时必须 UTF-8 无 BOM，避免 LLM 接收到乱码
