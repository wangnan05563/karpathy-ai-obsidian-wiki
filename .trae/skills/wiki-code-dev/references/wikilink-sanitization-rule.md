# CODING-WIKILINK-SANITIZATION — 注入 Obsidian 链接前的引用清洗

> 来源：归档路由把 `refs` 拼进 `[[wikilink]]` 写入 vault。若 ref 含换行/回车/多余空白，会破坏 `[[...]]` 链接语法、污染知识图谱关系；空串则生成 `[[ ]]` 空链接。
> 对应审查规则：后端 BR-084（建议级）。

## 触发关键词

`[[wikilink]]` / `refs` / 引用注入 / vault write / `replace(/[\r\n]/` / 控制字符 / markdown 链接 / `[[ ]]`

## 严重级别

🟢 Suggestion（破坏链接语法 / 污染图谱，非崩溃）

## 规则

- **WLS-1**：注入 `[[wikilink]]` / markdown 链接前，须对每个 ref 字符串剥离控制/空白字符（`replace(/[\r\n]/g, ' ').trim()`），去掉换行/回车/多余空白，防止破坏链接语法。
- **WLS-2**：清洗后 `filter(Boolean)` 丢弃空串，避免生成 `[[ ]]` 空链接或孤立 `,` 分隔。
- **WLS-3**：若 ref 可能含 `]` / `|` 等破坏 Obsidian 语法的字符，按 `config.wikilink.sanitize_regex` 额外清洗（与 BR-067 路径穿越防护同一纵深，但作用于**链接文本**而非路径）。
- **WLS-4**：清洗须集中在一处（循环/map 内），不得逐字段散落 `trim()`，避免遗漏。

## 正 / 误示例

```ts
// ❌ 误：ref 含换行 → [[a\nb]] 破坏链接；空串 → 脏链接
const refsSection = refs.map((r) => `[[${r}]]`).join(', ');

// ✅ 正：先清洗换行/空白 + 去空
refs = refs
  .map((r) => r.replace(/[\r\n]/g, ' ').trim())
  .filter(Boolean);
const refsSection = refs.map((r) => `[[${r}]]`).join(', ');
```

## 检查清单

- [ ] 所有写入 vault 的 refs / 引用串是否经换行清洗 + 去空？
- [ ] 清洗是否集中处理（而非逐字段 `trim`）？
- [ ] 是否覆盖 `]` / `|` 等语法破坏字符（按 config 正则）？
