# 媒体归档 Markdown frontmatter 审查规则（BR-058）

> 复盘来源：v3 媒体生成工具开发中，LLM 生成的图像/PPT/视频产物需归档到 vault 供后续检索与展示。早期归档文件 frontmatter 字段散乱（有的写 `image_path`、有的写 `file`），导致前端解析逻辑需多种 fallback；文件命名也无规则，无法按时间排序。统一为 `type: query` + `output_mode` + `generated_at` 三必备字段，文件名 `<output_mode>-YYYYMMDD-HHmmss.<ext>`（CODING-060）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"媒体归档 frontmatter 审查参数（media_archive_frontmatter）"章节读取，禁止在本规则文件硬编码目录名或字段名。

## Trigger Keywords

frontmatter, type: query, output_mode, generated_at, image_file, video_file, task_id, source_url, vault/queries/, archive, writeFileSync, writeFile, marp: true, 双重 frontmatter, 文件名, YYYYMMDD, ISO8601

## Rules

### BR-058-1：归档目录必须在 WRITE_ALLOWED_DIRS 白名单中

- **Severity**: critical
- **Description**: LLM 生成产物归档目录必须为 `media_archive_frontmatter.archive_dir`（默认 `vault/queries/`），且该目录必须在 `WRITE_ALLOWED_DIRS` 白名单中。归档到未授权目录会导致写入失败或安全风险（AI 写入敏感目录）。评审时确认：归档目录路径从 config 读取，且在白名单中。
- **Suggested fix**:

```typescript
// 错误：归档到未授权目录
writeFileSync(`./output/${filename}`, content); // ❌ 不在 WRITE_ALLOWED_DIRS 白名单

// 正确：归档到 vault/queries/（已在白名单）
const ma = config.media_archive_frontmatter;
writeFileSync(path.join(ma.archive_dir, filename), content); // ✅
```

### BR-058-2：frontmatter 必须含三个必备字段（type / output_mode / generated_at）

- **Severity**: critical
- **Description**: 归档 .md 文件 frontmatter 必须含 `media_archive_frontmatter.frontmatter_required_fields`（默认 `type,output_mode,generated_at`）全部字段。`type: query` 标识为查询产物；`output_mode` 标识产物类型（image/ppt/video/podcast）供前端分发渲染；`generated_at` 为 ISO8601 时间戳供排序。缺失任一字段会导致前端解析失败或无法排序。评审时确认：归档 .md 文件 frontmatter 含三个必备字段。
- **Suggested fix**:

```typescript
// 错误：frontmatter 缺少必备字段 output_mode
const frontmatter = `---
type: query
generated_at: ${ts}
---`; // ❌ 前端无法按 output_mode 分发渲染逻辑

// 正确：三个必备字段齐全
const frontmatter = `---
type: query
output_mode: ${opts.outputMode}
generated_at: ${ts}
---`; // ✅
```

### BR-058-3：文件名必须匹配 filename_pattern，禁止随机 UUID

- **Severity**: critical
- **Description**: 归档文件名必须匹配 `media_archive_frontmatter.filename_pattern`（默认 `^(image|ppt|video)-\d{8}-\d{6}\.(md|png|mp4)$`），格式为 `<output_mode>-YYYYMMDD-HHmmss.<ext>`，按时间排序友好。随机 UUID 文件名无法按生成时间排序，列表展示时顺序混乱。评审时确认：归档文件名匹配正则，含 output_mode 前缀 + 时间戳。
- **Suggested fix**:

```typescript
// 错误：文件名用随机 UUID，无法按时间排序
const filename = `${crypto.randomUUID()}.md`; // ❌ 列表展示时无法按生成时间排序

// 正确：文件名按 <output_mode>-YYYYMMDD-HHmmss.<ext> 格式
const ts = new Date().toISOString();
const filenameTs = ts.replace(/[-:T]/g, '').slice(0, 15).replace(/^(\d{8})(\d{6})/, '$1-$2');
const filename = `${opts.outputMode}-${filenameTs}.md`; // ✅ image-20260731-120000.md
```

### BR-058-4：业务字段必须放 frontmatter，禁止散落到正文

- **Severity**: suggestion
- **Description**: 业务字段（如 `image_file` / `video_file` / `task_id` / `source_url`）必须放在同一 frontmatter 中，禁止散落到正文。散落到正文会导致前端解析需读全文提取字段，增加复杂度；且正文可能被 Marp 等工具解析干扰。评审时确认：业务字段在 frontmatter 中，不在正文。
- **Suggested fix**:

```typescript
// 错误：业务字段散落到正文
const content = `---
type: query
output_mode: image
generated_at: ${ts}
---

# 图像产物

file: ./image-001.png  // ⚠️ 业务字段应在 frontmatter
task_id: abc-123       // ⚠️ 业务字段应在 frontmatter
`;

// 正确：业务字段同 frontmatter
const frontmatter = [
  '---',
  'type: query',
  'output_mode: image',
  'generated_at: ' + ts,
  'image_file: ' + opts.file, // ✅ 业务字段在 frontmatter
  'task_id: ' + opts.taskId,  // ✅
  '---',
].join('\n');
```

### BR-058-5：Marp 类归档必须合并 frontmatter，禁止双重 frontmatter

- **Severity**: suggestion
- **Description**: Marp 类归档文件 frontmatter 可合并 marp 字段（`marp: true` + 归档字段），避免双重 frontmatter。双重 frontmatter 会导致 Marp 解析失败（Marp 只读第一个 frontmatter）。`media_archive_frontmatter.allow_marp_merge`（默认 `true`）启用时，Marp 类归档必须合并 frontmatter。评审时确认：Marp 类归档文件只有一处 frontmatter，含 marp 字段 + 归档字段。
- **Suggested fix**:

```typescript
// 错误：Marp 类归档双重 frontmatter
const content = `---
marp: true
---

---
type: query
output_mode: ppt
generated_at: ${ts}
---

${marpMarkdown}`; // ❌ 双重 frontmatter 导致 Marp 解析失败

// 正确：合并 frontmatter
const content = `---
marp: true
type: query
output_mode: ppt
generated_at: ${ts}
---

${marpMarkdown}`; // ✅ 单一 frontmatter
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `media_archive_frontmatter.enabled` | `true` | 是否启用本组规则（BR-058） |
| `media_archive_frontmatter.severity_br058_1` | `critical` | BR-058-1 目录未在白名单违规严重级别 |
| `media_archive_frontmatter.severity_br058_2` | `critical` | BR-058-2 缺少必备字段违规严重级别 |
| `media_archive_frontmatter.severity_br058_3` | `critical` | BR-058-3 文件名不匹配违规严重级别 |
| `media_archive_frontmatter.severity_br058_4` | `suggestion` | BR-058-4 业务字段散落违规严重级别 |
| `media_archive_frontmatter.severity_br058_5` | `suggestion` | BR-058-5 双重 frontmatter 违规严重级别 |
| `media_archive_frontmatter.archive_dir` | `vault/queries/` | 归档目录（必须在 WRITE_ALLOWED_DIRS 白名单） |
| `media_archive_frontmatter.frontmatter_required_fields` | `type,output_mode,generated_at` | frontmatter 必备字段列表 |
| `media_archive_frontmatter.allowed_output_modes` | `image,ppt,video,podcast` | 允许的 output_mode 枚举 |
| `media_archive_frontmatter.filename_pattern` | `^(image\|ppt\|video)-\d{8}-\d{6}\.(md\|png\|mp4)$` | 文件名正则 |
| `media_archive_frontmatter.timestamp_format` | `YYYYMMDD-HHmmss` | 文件名时间戳格式 |
| `media_archive_frontmatter.generated_at_format` | `ISO8601` | generated_at 字段格式 |
| `media_archive_frontmatter.allow_marp_merge` | `true` | 是否允许 marp 字段合并到归档 frontmatter |

## 检查方式

1. **目录白名单检查**：用 Grep 检索归档代码中的 `writeFileSync` / `writeFile` 调用，确认路径为 `media_archive_frontmatter.archive_dir`，且该目录在 `WRITE_ALLOWED_DIRS` 白名单中。归档到未授权目录 → **BR-058-1 违规**。
2. **必备字段检查**：用 Grep 检索归档代码中 frontmatter 字符串构造，确认含 `type: query` / `output_mode:` / `generated_at:` 三个字段。缺失任一 → **BR-058-2 违规**。
3. **文件名检查**：用 Grep 检索归档代码中文件名构造，确认匹配 `filename_pattern` 正则（含 output_mode 前缀 + 时间戳）。随机 UUID 或无时间戳 → **BR-058-3 违规**。
4. **业务字段检查**：用 Grep 检索归档 .md 文件内容，确认 `image_file` / `video_file` / `task_id` / `source_url` 等业务字段在 frontmatter（`---` 之间）而非正文。散落到正文 → **BR-058-4 违规**（suggestion）。
5. **Marp 合并检查**：用 Grep 检索含 `marp: true` 的归档文件，确认只有一处 frontmatter（`---` 出现 2 次，非 4 次）。双重 frontmatter → **BR-058-5 违规**（suggestion）。
6. **output_mode 枚举检查**：用 Grep 检索 `output_mode:` 字段值，确认在 `allowed_output_modes` 列表中。非法值 → **BR-058-2 违规**。

## 正确示例

```typescript
// services/api/src/workflows/media-generation-workflow.ts
import { writeFileSync } from 'fs';
import path from 'path';
import { config } from '../config.js';

const ma = config.media_archive_frontmatter;

function archiveMediaProduct(opts: {
  outputMode: 'image' | 'ppt' | 'video';
  prompt: string;
  file: string;
  taskId?: string;
  sourceUrl?: string;
}): string {
  const ts = new Date().toISOString();
  // ✅ 文件名按 <output_mode>-YYYYMMDD-HHmmss.<ext> 格式（BR-058-3）
  const filenameTs = ts.replace(/[-:T]/g, '').slice(0, 15).replace(/^(\d{8})(\d{6})/, '$1-$2');
  const filename = `${opts.outputMode}-${filenameTs}.md`;
  const filePath = path.join(ma.archive_dir, filename); // ✅ 归档目录在白名单（BR-058-1）

  // ✅ frontmatter 必备字段 + 业务字段同处（BR-058-2, BR-058-4）
  const frontmatter = [
    '---',
    `type: query`,
    `output_mode: ${opts.outputMode}`,
    `generated_at: ${ts}`,
    `prompt: ${JSON.stringify(opts.prompt)}`,
    `${opts.outputMode}_file: ${opts.file}`,
  ];
  if (opts.taskId) frontmatter.push(`task_id: ${opts.taskId}`);
  if (opts.sourceUrl) frontmatter.push(`source_url: ${opts.sourceUrl}`);
  frontmatter.push('---', '', `# ${opts.outputMode} 生成产物`, '', `![${opts.outputMode}](${opts.file})`);

  writeFileSync(filePath, frontmatter.join('\n'), 'utf8');
  return filePath;
}
```

```typescript
// Marp 类归档：合并 frontmatter（BR-058-5）
function archiveMarpPpt(prompt: string, marpMarkdown: string): string {
  const ts = new Date().toISOString();
  const filename = `ppt-${ts.slice(0,10).replace(/-/g,'')}-${ts.slice(11,19).replace(/:/g,'')}.md`;
  // ✅ marp 字段与归档字段合并到同一 frontmatter
  const merged = `---
marp: true
type: query
output_mode: ppt
generated_at: ${ts}
---

${marpMarkdown}`;
  writeFileSync(path.join(ma.archive_dir, filename), merged, 'utf8');
  return filename;
}
```

## 错误示例

```typescript
// 错误 1：归档到未授权目录（BR-058-1 违规）
writeFileSync(`./output/${filename}`, content); // ❌ 不在 WRITE_ALLOWED_DIRS 白名单

// 错误 2：frontmatter 缺少必备字段（BR-058-2 违规）
const frontmatter = `---
type: query
generated_at: ${ts}
---`; // ❌ 缺少 output_mode

// 错误 3：文件名用随机 UUID（BR-058-3 违规）
const filename = `${crypto.randomUUID()}.md`; // ❌ 无法按时间排序

// 错误 4：业务字段散落到正文（BR-058-4 违规，suggestion）
const content = `---
type: query
output_mode: image
generated_at: ${ts}
---

file: ./image-001.png  // ⚠️ 业务字段应在 frontmatter
`;

// 错误 5：Marp 双重 frontmatter（BR-058-5 违规，suggestion）
const content = `---
marp: true
---

---
type: query
output_mode: ppt
generated_at: ${ts}
---

${marpMarkdown}`; // ❌ 双重 frontmatter 导致 Marp 解析失败
```

## 适配新项目

- **静态站点生成（SSG）项目**：归档目录改为 `content/generated/`，frontmatter 字段追加 `slug` / `draft` 等 SSG 必需字段
- **CMS 系统项目**：归档目录改为 CMS API 上传，frontmatter 改为 CMS 字段 schema
- **对象存储（S3/OSS）项目**：归档路径改为 `s3://bucket/queries/`，元数据放入对象 metadata
- **多租户项目**：归档目录追加租户前缀 `vault/queries/{tenantId}/`，frontmatter 追加 `tenant_id` 字段
- **Python 项目**：`writeFileSync` 改为 `pathlib.Path.write_text`，`path.join` 改为 `pathlib.Path /`

## 与其他规则的关系

- 与 BR-057（长/短任务架构分离）联动：长任务产物归档必须用本规则统一 frontmatter
- 与 BR-059（会话存储双层淘汰）联动：归档接口不接收客户端传内容，只接收引用（sessionId + messageIndex），内容从服务端 sessions 取
- 与 BR-001（路径解析禁用 CWD）联动：归档目录路径必须基于 `import.meta.url` 或配置锚点，禁止依赖 `process.cwd()`
- 与 filesystem-vault 规则联动：归档目录必须在 `WRITE_ALLOWED_DIRS` 白名单中
- 与 CODING-060（媒体归档 frontmatter 标准化）对应：本规则是 CODING-060 的后端审查视角
