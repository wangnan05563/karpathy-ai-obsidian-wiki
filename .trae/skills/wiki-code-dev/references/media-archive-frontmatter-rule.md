# 媒体归档 Markdown frontmatter 标准化规则（CODING-060）

> 复盘来源：v3 媒体生成工具开发中，LLM 生成的图像/PPT/视频产物需归档到 vault 供后续检索与展示。早期归档文件 frontmatter 字段散乱（有的写 `image_path`、有的写 `file`），导致前端解析逻辑需多种 fallback；文件命名也无规则，无法按时间排序。统一为 `type: query` + `output_mode` + `generated_at` 三必备字段，文件名 `<output_mode>-YYYYMMDD-HHmmss.<ext>`，与 podcast-workflow 保持一致。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `media_archive` 字段读取，禁止在规则文件中硬编码目录名或字段名。

## 规则

**LLM 生成产物（图像/PPT/视频/播客等）归档到 vault 必须遵守五项契约**：

1. **归档目录**：统一归档到 `media_archive.archive_dir`（默认 `vault/queries/`），该目录必须在 `WRITE_ALLOWED_DIRS` 白名单中
2. **frontmatter 必备字段**：必须包含 `media_archive.frontmatter_required_fields` 列表中的所有字段（默认 `type` / `output_mode` / `generated_at`）
3. **业务字段同 frontmatter**：业务字段（如 `image_file` / `video_file` / `task_id` / `source_url`）放在同一 frontmatter 中，禁止散落到正文
4. **文件名格式**：必须匹配 `media_archive.filename_pattern`（默认 `^(image|ppt|video)-\d{8}-\d{6}\.(md|png|mp4)$`），按时间排序友好
5. **Marp 类合并 frontmatter**：Marp 类归档文件 frontmatter 可合并 marp 字段（`marp: true` + 归档字段），避免双重 frontmatter

## 适用场景

- LLM 多模态生成产物归档（图像 / PPT / 视频 / 播客 / 音频）
- 需要后续按时间排序、按类型检索的归档场景
- 多种生成产物共用同一归档目录（统一 frontmatter 降低前端解析复杂度）
- Marp / reveal.js 等需自带 frontmatter 的归档文件

## 不适用场景

- 用户手动创建的笔记（非 LLM 生成，frontmatter 自由）
- 临时缓存文件（如 `.cache/` 目录下的中间产物）
- 二进制产物本身（如 `.png` / `.mp4` 不写 frontmatter，归档元数据写在同目录的 `.md` 中）
- 不需检索的归档（如日志文件，按行时间戳检索即可）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `media_archive.enabled` | `true` | 是否启用归档守卫 |
| `media_archive.severity` | `error` | 违规严重级别 |
| `media_archive.archive_dir` | `vault/queries/` | 归档目录（必须在 WRITE_ALLOWED_DIRS 白名单） |
| `media_archive.frontmatter_required_fields` | `type,output_mode,generated_at` | frontmatter 必备字段列表 |
| `media_archive.allowed_output_modes` | `image,ppt,video,podcast` | 允许的 output_mode 枚举 |
| `media_archive.filename_pattern` | `^(image\|ppt\|video)-\d{8}-\d{6}\.(md\|png\|mp4)$` | 文件名正则 |
| `media_archive.timestamp_format` | `YYYYMMDD-HHmmss` | 文件名时间戳格式 |
| `media_archive.generated_at_format` | `ISO8601` | generated_at 字段格式 |
| `media_archive.allow_marp_merge` | `true` | 是否允许 marp 字段合并到归档 frontmatter |

## 检查方式

1. **目录白名单检查**：归档目录必须在 `WRITE_ALLOWED_DIRS` 白名单中，禁止写到未授权目录
2. **必备字段检查**：归档 .md 文件 frontmatter 必须含 `frontmatter_required_fields` 全部字段
3. **output_mode 枚举检查**：`output_mode` 字段值必须在 `allowed_output_modes` 列表中
4. **文件名检查**：文件名必须匹配 `filename_pattern` 正则
5. **时间戳格式检查**：`generated_at` 字段必须为 ISO8601 格式（`new Date().toISOString()`）
6. **Marp 合并检查**：Marp 类归档文件不得有双重 frontmatter，必须合并到一处

## 正确示例

```typescript
// services/api/src/workflows/media-generation-workflow.ts
import { writeFileSync } from 'fs';
import { config } from '../config.js';

const ma = config.media_archive;

/**
 * 归档媒体产物到 vault——统一 frontmatter 降低前端解析复杂度
 * 为什么用统一 frontmatter：早期字段散乱（image_path / file 混用），
 * 前端解析需多种 fallback；统一后只需读 output_mode 分发，新增类型追加枚举即可。
 */
function archiveMediaProduct(opts: {
  outputMode: 'image' | 'ppt' | 'video';
  prompt: string;
  file: string;
  taskId?: string;
  sourceUrl?: string;
}): string {
  const ts = new Date().toISOString();
  // ✅ 文件名按 <output_mode>-YYYYMMDD-HHmmss.<ext> 格式，排序友好
  const filenameTs = ts.replace(/[-:T]/g, '').slice(0, 15).replace(/^(\d{8})(\d{6})/, '$1-$2');
  const filename = `${opts.outputMode}-${filenameTs}.md`;
  const filePath = path.join(ma.archive_dir, filename);

  // ✅ frontmatter 必备字段 + 业务字段同处
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
// Marp 类归档：合并 frontmatter，避免双重
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
// ❌ 错误：frontmatter 缺少必备字段 output_mode
const frontmatter = `---
type: query
generated_at: ${ts}
---`;
// ⚠️ 前端无法按 output_mode 分发渲染逻辑

// ❌ 错误：文件名用随机 UUID，无法按时间排序
const filename = `${crypto.randomUUID()}.md`;
// ⚠️ 列表展示时无法按生成时间排序

// ❌ 错误：业务字段散落到正文，不在 frontmatter
const content = `---
type: query
output_mode: image
generated_at: ${ts}
---

# 图像产物

file: ./image-001.png  ⚠️ 业务字段应在 frontmatter
task_id: abc-123       ⚠️ 业务字段应在 frontmatter
`;

// ❌ 错误：Marp 类归档双重 frontmatter
const content = `---
marp: true
---

---
type: query
output_mode: ppt
generated_at: ${ts}
---

${marpMarkdown}`;
// ⚠️ 双重 frontmatter 导致 Marp 解析失败
```

## 适配新项目

- 适配静态站点生成（SSG）：归档目录改为 `content/generated/`，frontmatter 字段追加 `slug` / `draft` 等 SSG 必需字段
- 适配 CMS 系统：归档目录改为 CMS API 上传，frontmatter 改为 CMS 字段 schema
- 适配对象存储（S3/OSS）：归档路径改为 `s3://bucket/queries/`，元数据放入对象 metadata
- 适配多租户：归档目录追加租户前缀 `vault/queries/{tenantId}/`，frontmatter 追加 `tenant_id` 字段

## 与其他规则的关系

- 与 CODING-059（长/短任务架构分离）联动：长任务产物归档必须用本规则统一 frontmatter
- 与 CODING-061（会话存储双层淘汰）联动：归档接口不接收客户端传内容，只接收引用（sessionId + messageIndex），内容从服务端 sessions 取
- 与 CODING-062（prompt 单点存储）联动：归档 frontmatter 中的 prompt 字段值从 prompts/ 目录加载，不在源码内联
- 与 CODING-001（路径解析禁用 CWD）联动：归档目录路径必须基于 `import.meta.url` 或配置锚点，禁止依赖 `process.cwd()`
- 与项目硬约束（WRITE_ALLOWED_DIRS 白名单）联动：归档目录必须在白名单中，否则写入会失败
