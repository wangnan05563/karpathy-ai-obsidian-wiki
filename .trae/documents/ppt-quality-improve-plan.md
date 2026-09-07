# 知识库问答页面 PPT 质量提升：内置 pptx-skill-for-trae 能力（预览 + .pptx 下载）

## Context（背景与目标）

用户反馈知识库问答页面 `PPT` 模式生成质量较差。经调研，后端其实**已经在 prompt（`api/src/prompts/ppt-generation.md` v4）中吸收了 `D:\code\Data_Trae\.trae-cn\skills\pptx-skill-for-trae` 的排版规范**，并将其映射为 Marp Markdown 的质量约束。当前链路是：

`后端 generatePpt() 用 LLM 生成 Marp Markdown → 归档 queries/ppt-*.md → SSE ppt 事件 → 前端 marpit(marpit) 在浏览器内联渲染`

但该 skill 的真实能力是「**用 pptxgenjs + python 脚本生成原生 .pptx 文件**」，交付物是可编辑的 PowerPoint/WPS 文件——与现有「浏览器内联渲染」是两种交付形态。

**用户已确认方向**：
1. 交付形态：**两者都要** —— 在线预览（沿用 marpit）+ 可下载的原生 `.pptx` 文件。
2. 集成方式：**移植 skill 资产进本项目，并落地为后端代码**（真正内置，不依赖外部路径 `D:\code\Data_Trae`）。

目标：PPT 模式输出在浏览器可预览、同时可下载原生 `.pptx`，排版质量按 skill 规范显著提升。

## 现状梳理（已读代码）

- **后端 PPT 生成**：[media-generation-workflow.ts](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\api\src\workflows\media-generation-workflow.ts#L377-L432) `generatePpt()` → 返回 `{ markdown, title, archivePath }`（Marp Markdown + frontmatter，归档 `queries/ppt-*.md`）。
- **注入 answer 流**：[query-workflow.ts](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\api\src\workflows\query-workflow.ts#L848-L863) → yield `{ ppt: { markdown, title, archivePath } }`。
- **前端组装**：[Query.vue](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\frontend\src\views\Query.vue#L1313-L1316) → `{ type:'ppt', content:title, pptMarkdown:markdown }` 交给 `MultimodalOutputCard`。
- **前端渲染**：[MultimodalOutputCard.vue](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\frontend\src\components\MultimodalOutputCard.vue#L93-L137) 用 `@marp-team/marpit` 内联渲染。
- **下载/服务二进位能力**：[files.ts](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\api\src\routes\files.ts#L102-L135) 已有「公开媒体服务路由 `GET /api/media/file/*`」供浏览器 `<img>/<video>` 无需认证加载，image 模式即用此先例（`imageUrl`）。但当前 `BINARY_EXTENSIONS` **不含 `.pptx`**；想用公开路由服务 .pptx 需先补该集合。
- **前端类型**：[types.ts](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\frontend\src\types.ts#L1174-L1179) `MultimodalOutput` 与 [#L145](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\frontend\src\types.ts#L145) `msg.ppt`，均需增加 `pptxUrl`。

## 推荐方案

**保留 Marp Markdown 预览，后端额外生成原生 .pptx 供下载。** 不发起第二次 LLM 调用——直接从已生成且质量受控的 Marp Markdown 中**解析出结构化页纲**，再用 pptxgenjs（`^3.12.0`，skill 的运行时依赖）程序化排版生成 `.pptx`。理由：Marp 已含封面/目录/内容/总结/结语 + 每页 `##` 标题 + `-` 要点（两级），结构化程度足够，避免重复消耗 token 与延迟。

### 后端改动

1. **新增依赖**：`karpathy-wiki/api/package.json` 加入 `pptxgenjs@^3.12.0`，执行 `npm install`（唯一需联网步骤）。参考 skill 的 `package.json`。（python 编辑脚本 `scripts/*.py` 不迁移——后端为 Node/TS，且我们的生成是从零创建、不涉及离线 .pptx 解锁编辑。）

2. **新增模块** `api/src/workflows/pptx-renderer.ts`：
   - `parseMarpSlides(markdown): Slide[]`：剥离 frontmatter（首个 `---`）后按 `---` 分页；每页提取标题（`#`/`##`）与要点（`- `，保留两级缩进做子点）。
   - `renderPptx(slides, title, filename): Promise<Buffer>`：用 pptxgenjs 生成 .pptx。将 skill 的排版规范落地为代码：
     - 主题色/字体抽为常量（贴合项目浅色清新 UI：浅蓝/浅紫主色系，`#165DFF`/`#722ED1` 类），覆盖标题色块、要点对齐、底部页码。
     - 封面/目录/内容/总结/结语五种布局分设模板；每页**至少一个可见元素**（消灭空页，skill 硬性要求）。
     - 溢出控制（skill 的防溢出原则）：按每页要点数/字数动态缩放字号、限制要点行数，标题 ≤ 设定宽度。
   - `generatePptxFile(markdown, title): Promise<{ archivePath, url }>`：渲染 Buffer → 写入 `queries/media/ppt-<uuid>.pptx`（复用 randomMediaId 风格命名，UUID 防枚举），返回 `url = /api/media/file/<basename>`（与 image 公开路由同款）。

3. **接入生成流程**：改造 `media-generation-workflow.ts` `generatePpt()` 的返回，在归档 Marp Markdown **之后**调用 `generatePptxFile(...)`，返回增补 `pptxUrl`，避免丢失异常（.pptx 生成失败仅降级为"无下载按钮"，不影响预览）。返回值变为 `{ markdown, title, archivePath, pptxUrl }`。

4. **补充二进制放行**：`files.ts` 的 `BINARY_EXTENSIONS` 与 `BINARY_CONTENT_TYPES` 增加 `.pptx`（mime `application/vnd.openxmlformats-officedocument.presentationml.presentation`），使公开媒体路由 `GET /api/media/file/ppt-<uuid>.pptx`（以及 `GET /api/files/download`）能正确服务 .pptx。

5. **类型同步**：`api/src/types.ts` 中 `AnswerChunk.ppt` 增加 `pptxUrl?: string`。

6. **移植 skill 资产为文档**：复制 skill 关键资产到项目文档目录（沿用项目 docs 集中规范，例如 `karpathy-wiki/docs/`）：
   - `pptxgenjs.md`（pptxgenjs 用法/API）、`SKILL.md` 的设计规范部分 → 作为「内置技能」参考文档，供后续维护引用。
   - 说明 `.py` 脚本未迁移原因（Node 栈、用不到离线编辑）。

### 前端改动

1. **类型**：[types.ts](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\frontend\src\types.ts#L1174-L1179) `MultimodalOutput` 增加 `pptxUrl?: string`；[#L145](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\frontend\src\types.ts#L145) `msg.ppt` 增加 `pptxUrl?: string`。

2. **传递**：[Query.vue](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\frontend\src\views\Query.vue#L1313-L1316) 组装时带上 `pptxUrl: msg.ppt.pptxUrl`。

3. **下载按钮**：[MultimodalOutputCard.vue](file:///d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\karpathy-wiki\frontend\src\components\MultimodalOutputCard.vue#L197-L208) ppt 分支底部增加下载入口：
   - 有 `pptxUrl` 时渲染 `<a :href="pptxUrl" download="知识库PPT.pptx">下载 .pptx</a>`（公开路由无需认证，与 image 加载一致）。
   - 无 `pptxUrl`（生成降级）时不渲染按钮，保留 marpit 预览与错误兜底展示。

## 不复用 / 拒绝项

- 不引入 python 脚本（`unpack/pack/fix/validate_layout`）——Node 栈不适用离线 .pptx 编辑。
- 不二次调用 LLM 生成独立 JSON 大纲——直接解析既有 Marp，省 token、省延迟。
- 不改动现有 mindmap/faq/timeline/image 逻辑；仅增补 ppt 模式。

## 验证

1. **单元级**：`parseMarpSlides` 用现有示例 markdown（含 frontmatter、封面/目录/多内容页/总结/结语）做解析断言；`renderPptx` 输出的 Buffer 以 `PK`（zip）开头、能被 `unzip -t` / 简单读取验证为合法 pptx 结构。
2. **接口级**：发起一次 `outputMode=ppt` 问答，确认 SSE `ppt` 事件携带 `pptxUrl`；直接 GET `/api/media/file/ppt-<uuid>.pptx` 返回 200 + 正确 Content-Type，可下载。
3. **端到端（Playwright）**：问答页面 PPT 模式 → 页面显示 marpit 预览（不改动原有渲染）→ 出现「下载 .pptx」链接 → 点击可下载合法文件。
4. **降级路径**：人为让 .pptx 渲染抛错，确认仍显示 marpit 预览、无下载按钮、无报错崩溃。

## 影响面

- 后端新增 1 依赖（pptxgenjs）、1 个渲染模块、`generatePpt()` 返回字段扩展、files.ts 扩展 .pptx。
- 前端 3 类文件小改（types / Query.vue / MultimodalOutputCard.vue）。
- 不改动问答主流程与其它多模态模式。