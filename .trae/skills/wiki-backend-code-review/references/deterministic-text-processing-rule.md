# 确定性文本处理审查规则（BR-064）

> 复盘来源：两处确定性文本处理 bug。(1) 去重 / 分词的正则字符类写成 `/[㐀-鿿　-〿＀-￯]/`，其中 `　-〿`（全角空格到日式标点）与 `＀-￯`（全角片假名半形到全角）区间把全角标点也圈了进来，导致中文标点被当作"表意文字"参与 token 估计与去重，污染结果。(2) 去重误把"较短但信息完整的片段"判为低价值删除，破坏上下文连贯性；压缩预算未保证净 token 下降。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"确定性文本处理审查参数（deterministic_text_processing）"章节读取，禁止在本规则文件硬编码阈值。

## Trigger Keywords

regex, unicode, CJK, 表意文字, char class, /[㐀-鿿　-〿＀-￯]/, codepoint range, ideograph, 全角标点, tokenizer, token estimate, 中文 token, dedup, 去重, Jaccard, 杰卡德, 相似度, coherence, 连贯性, compression budget, 压缩预算, recency window, 驱逐, minFloor, 最小地板

## Rules

### BR-064-1：CJK/Unicode 正则须用精确码点区间（仅表意文字，排除标点）

- **Severity**: critical
- **Description**: 匹配 CJK 的字符类必须只覆盖表意文字（CJK Unified Ideographs `U+4E00`–`U+9FFF`、扩展 A `U+3400`–`U+4DBF` 等），显式排除全角标点 / 全角空格 / 片假名半形等。禁止用 `　-〿`、`＀-￯` 这类会把全角标点也纳入的宽泛区间。评审时确认：中文相关正则只用表意文字区间，不含全角标点段；如需匹配标点应单列区间。
- **Suggested fix**:

```typescript
// 错误：区间吞掉全角标点（　-〿 含全角空格/句号，＀-￯ 含全角片假名）
const CJK_BAD = /[㐀-鿿　-〿＀-￯]/; // ❌ 全角标点被当作表意文字

// 正确：仅表意文字区间（CJK 基本 + 扩展 A），标点单列
const IDEOGRAPH = /[㐀-鿿㐀-䶿]/; // 或明确 U+4E00-U+9FFF + U+3400-U+4DBF
const FULLWIDTH_PUNCT = /[　-〿＀-￯]/; // 标点单独处理，不参与"是否为中文"判断
```

### BR-064-2：去重须实体感知（Jaccard ≥ 阈值 且 无显著数字/[[ref]] 差异）

- **Severity**: critical
- **Description**: 片段去重不能只看文本表面相似。必须实体感知：Jaccard 相似度 ≥ `jaccard_threshold` 且两侧不含"显著数字差异"或"[[ref]] 引用差异"时才合并——因为数字与文献引用是语义关键，相似文本换了数字 / 引用即为不同实体，误合并会丢信息。评审时确认：去重判定同时检查相似度与关键实体（数字串、`[[...]]` 引用）一致性。
- **Suggested fix**:

```typescript
// 错误：仅按文本相似度去重，把"增长率 12%"与"增长率 87%"当重复删掉
if (jaccard(a, b) >= 0.9) drop(b); // ❌ 数字差异被忽略

// 正确：相似度 + 实体一致性双判
function canDedup(a: string, b: string): boolean {
  const j = jaccard(a, b);
  if (j < config.deterministic_text_processing.jaccard_threshold) return false;
  const numDiff = hasSignificantDigitDiff(a, b);   // 显著数字差异
  const refDiff = hasRefDiff(a, b);                // [[ref]] 引用差异
  return !numDiff && !refDiff;                      // ✅ 实体一致才合并
}
```

### BR-064-3：低价值判定须为"空 / 纯标点 / 问候黑名单"，禁止仅按短

- **Severity**: critical
- **Description**: "低价值片段"只能定义为：空串、纯标点 / 纯空白、命中问候黑名单（如"你好""谢谢"）。绝对不能因为"短"就判为低价值删除——短句常承载关键信息（命令、参数、结论）。评审时确认：低价值分类函数不含"长度 < N 即删"的短路逻辑。
- **Suggested fix**:

```typescript
// 错误：短即删，丢掉"停止服务""端口 3000"等关键短句
if (text.trim().length < 6) drop(text); // ❌ 误删关键信息

// 正确：仅空/纯标点/问候黑名单
const GREET = config.deterministic_text_processing.greeting_blacklist;
function isLowValue(t: string): boolean {
  const s = t.trim();
  if (s.length === 0) return true;
  if (/^[\s\p{P}]+$/u.test(s)) return true;        // 纯标点/空白
  if (GREET.some(g => s === g || s.includes(g))) return true;
  return false;                                     // ✅ 短但不空/不纯标点/非问候 → 保留
}
```

### BR-064-4：压缩预算须保证净 token 下降（max(floor(len*0.3), minFloor)）

- **Severity**: critical
- **Description**: 上下文压缩 / 摘要预算必须为 `max(floor(len * ratio), minFloor)`，保证净 token 下降（压缩后 ≤ 原长 × ratio，且不低于 `minFloor` 以保留最少信息）。预算逻辑若用固定上限或不保证下降，会产生"越压越长"的反效果。token 估算：CJK ≈ 1 token/字，Latin ≈ 4 token/词（按 `cjk_token_ratio` / `latin_token_ratio`）。评审时确认：预算函数满足 `compressed ≤ max(floor(len*ratio), minFloor)` 且 token 估算区分 CJK/Latin。
- **Suggested fix**:

```typescript
// 错误：固定上限，长文压缩后反而超过原文
function budget(len: number) { return 500; } // ❌ 原文 2000 也压到 500？但短文 600 也压到 500，无净下降

// 正确：比例 + 地板，保证净下降
function budget(len: number): number {
  const r = config.deterministic_text_processing.compression_ratio; // 0.3
  const floor = config.deterministic_text_processing.min_floor;     // 200
  return Math.max(Math.floor(len * r), floor);
}
function estimateTokens(s: string): number {
  const cjk = (s.match(config.deterministic_text_processing.ideograph_regex) ?? []).length;
  const latin = s.replace(config.deterministic_text_processing.ideograph_regex, ' ')
    .split(/\s+/).filter(Boolean).length;
  return cjk * config.deterministic_text_processing.cjk_token_ratio   // 1
       + latin * config.deterministic_text_processing.latin_token_ratio; // 4
}
```

### BR-064-5：驱逐须保护连贯性地板 min(recencyWindow, K)，禁止低于地板

- **Severity**: critical
- **Description**: 记忆 / 上下文窗口驱逐时，必须保留"连贯性地板"——最近 `min(recencyWindow, K)` 条条目永不裁掉，避免把正在进行的对话 / 任务上下文清空导致回答断裂。评审时确认：驱逐逻辑有 `coherence_floor = min(recency_window, k)` 的保护，且实际删除数不超过"总数 − floor"。
- **Suggested fix**:

```typescript
// 错误：按全局预算无脑裁掉最旧，正在进行的对话上下文被清空
items.sort(byOldest);
while (estimateTokens(items) > budget) items.shift(); // ❌ 可能删到当前轮

// 正确：保留连贯性地板
const floor = Math.min(
  config.deterministic_text_processing.recency_window,
  config.deterministic_text_processing.coherence_k);
const protectedItems = items.slice(-floor);          // 最近 floor 条受保护
const evictable = items.slice(0, Math.max(0, items.length - floor));
let evicted = 0;
for (const it of evictable) {
  if (estimateTokens(items) <= budget) break;
  removeItem(it); evicted++;
}
// ✅ 永远保留 protectedItems
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `deterministic_text_processing.enabled` | `true` | 是否启用本组规则（BR-064） |
| `deterministic_text_processing.severity_br064_1` | `critical` | BR-064-1 宽泛 Unicode 区间违规级别 |
| `deterministic_text_processing.severity_br064_2` | `critical` | BR-064-2 非实体感知去重违规级别 |
| `deterministic_text_processing.severity_br064_3` | `critical` | BR-064-3 仅按短删违规级别 |
| `deterministic_text_processing.severity_br064_4` | `critical` | BR-064-4 预算不保证净下降违规级别 |
| `deterministic_text_processing.severity_br064_5` | `critical` | BR-064-5 跌破连贯性地板违规级别 |
| `deterministic_text_processing.ideograph_regex` | `[㐀-鿿㐀-䶿]` | 仅表意文字区间（不含标点） |
| `deterministic_text_processing.jaccard_threshold` | `0.9` | 去重 Jaccard 阈值 |
| `deterministic_text_processing.greeting_blacklist` | `你好,谢谢,hi,hello` | 问候黑名单 |
| `deterministic_text_processing.compression_ratio` | `0.3` | 压缩比例 |
| `deterministic_text_processing.min_floor` | `200` | 压缩最小地板（token） |
| `deterministic_text_processing.cjk_token_ratio` | `1` | CJK token 估算（1/字） |
| `deterministic_text_processing.latin_token_ratio` | `4` | Latin token 估算（4/词） |
| `deterministic_text_processing.recency_window` | `8` | 连贯性最近窗口 |
| `deterministic_text_processing.coherence_k` | `12` | 连贯性地板 K |

## 检查方式

1. **Unicode 区间检查**：Grep 中文相关正则，确认仅表意文字区间、不含全角标点段（`　-〿` / `＀-￯`）；命中宽泛区间 → **BR-064-1 违规**。
2. **去重实体检查**：Grep 去重函数，确认 Jaccard 之外检查数字 / `[[ref]]` 差异；仅相似度 → **BR-064-2 违规**。
3. **低价值检查**：Grep 低价值判定，确认无"长度 < N 即删"短路；含 → **BR-064-3 违规**。
4. **预算检查**：Grep 压缩预算，确认 `max(floor(len*ratio), minFloor)` 形态且 token 估算区分 CJK/Latin；不保证净下降 → **BR-064-4 违规**。
5. **地板检查**：Grep 驱逐逻辑，确认有 `min(recency_window, K)` 保护且实际删除不超过总数 − 地板；可能跌破 → **BR-064-5 违规**。

## 与其他规则的关系

- 与 BR-035（路径解析三级策略）/ BR-066（可移植配置默认）联动：确定性文本处理依赖稳定可重放的输入，配置路径须可重放。
- 与 BR-059（会话存储双层淘汰）联动：驱逐地板思想一致（TTL + 连贯性地板）。
- 与 CODING-DETERMINISTIC-TEXT（确定性文本处理）对应：本规则是 CODING-DETERMINISTIC-TEXT 的后端审查视角。
