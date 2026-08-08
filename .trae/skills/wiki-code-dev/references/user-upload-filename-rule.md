# User Upload Filename Rule（用户输入作文件名 / 路径）

## 触发关键词

用户输入, 文件名, 上传, archiveRaw, sanitize, basename, 中文, CJK, 汉字, 全角,
prefix, wiki-batch, wiki-compile, internal prefix, stripInternalPrefix, 原始文件名

## 规则

### UF-1：用户输入作文件名须 Unicode 感知清洗（保留合法脚本字符）

**严重级别**：critical

用户输入的文件名/原始资料名常含中文、日文、全角字符。清洗正则必须 **Unicode 感知**，
保留 `\p{L}`（字母，含 CJK）、`\p{N}`（数字）等合法脚本字符，仅将非法字符（控制符、空白、
路径分隔符等）替换为 `_`。

**为什么**：早期用 ASCII 导向的正则 `/[^\w.-]/`（`\w` 仅 `[A-Za-z0-9_]`）会把中文整体替换成
下划线，导致"wiki-batch-1785896202865-0-00_______________20240822.md"——用户完全无法识别原文件。
这是生产环境真实事故的根因。

**错误示例**：

```typescript
// ❌ ASCII 导向：中文被整体替换成下划线
const safeName = filename.replace(/[^\w.-]/g, '_');
```

**正确示例**：

```typescript
// ✅ Unicode 感知：保留中英文与数字，仅替换非法字符
const safeName = path.basename(filename).replace(/[^\p{L}\p{N}._-]/gu, '_');
```

> 允许字符集（含中文/字母/数字/点/下划线/短横线）必须来自 config，不同业务可配置，见 wiki-backend-code-review `path_traversal_strict.name_whitelist_regex` 与 `review-config.md` 的"路径遍历防护"段。

### UF-2：系统自身写入的内部前缀须在落盘/展示前剥离

**严重级别**：critical

后端在编译/归档时给临时文件附加的 **内部前缀**（如 `wiki-batch-<ts>-<i>-`、`wiki-compile-<ts>-`、
`input-`）属于实现细节，禁止泄漏到用户可见的文件名与展示名。须在推导展示名前统一剥离。

**为什么**：内部前缀泄漏会让用户看到"wiki-batch-1785896202865-0-00..."这类无意义长串，无法对应原始上传。

**正确示例**（剥离函数，正则须参数化）：

```typescript
// 去掉编译路由写入临时文件时附加的内部前缀
function stripInternalPrefix(name: string): string {
  return name
    .replace(/^wiki-batch-\d+-\d+-/, '')
    .replace(/^wiki-compile-\d+-/, '');
}
// 前端展示 / 落盘 raw 时一律先 stripInternalPrefix(input.originalName ?? basename)
```

> 前缀模式（如 `wiki-batch-`、`wiki-compile-`）应在 config 中维护 `internal_prefix_patterns` 列表，新增前缀类型时只改配置。

### UF-3：清洗后须二次校验路径穿越（`..` 与 `isAbsolute`）

**严重级别**：critical

`path.basename()` 仅剥离目录分隔符，但文件名本身若为 `..`（或 `a/../b`），`path.resolve('raw/..')`
会跳到 `vault` 根目录乃至更上层。白名单保留 `.` 是为了扩展名，故必须 **单独拦截路径穿越片段**。

**正确示例**：

```typescript
const safeName = path.basename(filename).replace(/[^\p{L}\p{N}._-]/gu, '_');
// 二次防护：basename 仅剥离目录分隔符，文件名若为 '..' 仍会经 resolve('raw/..') 跳到 vault 根
if (/(^|\/)\.\.(\/|$)/.test(safeName) || path.isAbsolute(safeName)) {
  throw new Error(`非法文件名（疑似路径穿越）: ${filename}`);
}
const rel = `raw/${safeName}`;
```

> 本规则与 wiki-backend-code-review **BR-067（严格路径穿越审查）** 一致：`path_traversal_strict.traversal_regex = (^\|\/)\.\.(\/\|$)`、`require_isabsolute_check = true`。新增文件名处理点须同时过本规则与 BR-067。

### UF-4：原始文件名须在前端/后端之间透传，避免二次丢失

**严重级别**：suggestion

原始上传名经 `CompileInput.originalName` 透传到落盘逻辑；该字段应为 **可选** 且后端自备兜底
（`input.originalName ?? path.basename(input.content)`），前端不消费该内部字段时不会破坏契约。
详见 wiki-frontend-code-review **FR-066** 与 wiki-backend-code-review **BR-026（类型同步）**。

## 检查清单

- [ ] 文件名清洗是否 Unicode 感知（保留 `\p{L}\p{N}`，中文不被变下划线）
- [ ] 系统内部前缀（wiki-batch-/wiki-compile-/input-）是否在落盘/展示前剥离
- [ ] 清洗后是否二次拦截 `..` 路径穿越片段 + `isAbsolute`
- [ ] 清洗/前缀白名单正则是否来自 config（非硬编码）
- [ ] 原始文件名是否经 optional 字段透传且后端有 `??` 兜底
