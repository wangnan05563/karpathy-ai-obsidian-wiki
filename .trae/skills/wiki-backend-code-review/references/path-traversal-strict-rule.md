# 严格路径穿越审查规则（BR-067）

> 复盘来源：安全规则（security-rule.md）已要求"用户输入文件名/路径须正则校验，禁止 `..` 和绝对路径"，但实际出现过白名单 sanitize 后拼接 `path.join` 时仍被 `..` 序列绕过的边角案例——正则白名单漏匹配某种编码 / 大小写变体，sanitize 后又未做二次兜底，导致路径穿越。本规则在 security-rule 的白名单 sanitize 之后，追加两道强制二次校验：`/(^|\/)\.\.(\/|$)/` 负向匹配 + `path.isAbsolute` 二次检查。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"严格路径穿越审查参数（path_traversal_strict）"章节读取。

## Trigger Keywords

path.join, sanitize, whitelist, 白名单, .., dot dot, isAbsolute, 路径穿越, path traversal, 二次校验, secondary check, 正则白名单, 拼接, vault, 用户可控路径

## Rules

### BR-067-1：白名单 sanitize 后须二次负向匹配 `/(^|\/)\.\.(\/|$)/`

- **Severity**: critical
- **Description**: 即便已用正则白名单对用户输入做 sanitize，拼接进文件系统前仍须再做一次"路径段穿透"负向校验：拒绝任何含 `..` 作为独立路径段的输入（正则 `/(^|\/)\.\.(\/|$)/`）。白名单可能因编码 / 大小写 / 变体漏判，二次校验是纵深防御。评审时确认：所有 `path.join(vaultRoot, userInput)` 之前，对 `userInput` 调用了 `assertNoTraversal(userInput)` 且包含 `..` 段检测。
- **Suggested fix**:

```typescript
// 错误：仅白名单后直接拼接，白名单漏判即穿越
const NAME_RE = /^[A-Za-z0-9_][A-Za-z0-9._-]*$/;
if (!NAME_RE.test(name)) throw new Error('非法');
const file = path.join(vaultRoot, name); // ❌ 白名单一旦漏判即穿越

// 正确：白名单 + 二次 .. 段检测（纵深防御）
const TRAVERSAL_RE = /(^|\/)\.\.(\/|$)/;
function assertSafeName(name: string): void {
  if (!NAME_RE.test(name)) throw new Error(`非法文件名: ${name}`);
  if (TRAVERSAL_RE.test(name) || name.includes('..')) { // ✅ 二次兜底
    throw new Error(`路径穿越: ${name}`);
  }
}
assertSafeName(name);
const file = path.join(vaultRoot, name);
```

### BR-067-2：拼接前须 `path.isAbsolute` 二次检查

- **Severity**: critical
- **Description**: 在 `path.join` 拼接用户可控段之前，必须对该段调用 `path.isAbsolute()` 二次确认其非绝对路径。即使白名单已禁止绝对路径前缀，绝对路径检测是独立、正交的兜底（覆盖盘符 / 根 `/` / 协议前缀等白名单可能遗漏的形态）。评审时确认：拼接前对 dedup/normalize 后的用户输入执行 `path.isAbsolute()` 检查，命中即拒绝。
- **Suggested fix**:

```typescript
// 错误：无 isAbsolute 兜底，绝对路径前缀绕过白名单
const file = path.join(vaultRoot, userInput); // ❌ userInput='/etc/passwd' 若不命中白名单仍可进

// 正确：isAbsolute 二次检查
function assertSafeName(name: string): void {
  if (!NAME_RE.test(name)) throw new Error(`非法文件名: ${name}`);
  if (TRAVERSAL_RE.test(name)) throw new Error(`路径穿越: ${name}`);
  if (path.isAbsolute(name)) throw new Error(`绝对路径禁止: ${name}`); // ✅ 正交兜底
}
assertSafeName(userInput);
const file = path.join(vaultRoot, userInput);
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `path_traversal_strict.enabled` | `true` | 是否启用本组规则（BR-067，扩展 security-rule） |
| `path_traversal_strict.severity_br067_1` | `critical` | BR-067-1 缺 .. 段二次校验违规级别 |
| `path_traversal_strict.severity_br067_2` | `critical` | BR-067-2 缺 isAbsolute 检查违规级别 |
| `path_traversal_strict.name_whitelist_regex` | `^[A-Za-z0-9_][A-Za-z0-9._-]*$` | 文件名白名单（与 security-rule 一致） |
| `path_traversal_strict.traversal_regex` | `(^\|\/)\.\.(\/\|$)` | `..` 段负向匹配 |
| `path_traversal_strict.require_isabsolute_check` | `true` | 拼接前须 isAbsolute 检查 |

## 检查方式

1. **二次穿越检查**：Grep `path.join(` 且参数含用户可控段，确认拼接前对输入调用了 `..` 段正则（`traversal_regex`）；仅有白名单无二次校验 → **BR-067-1 违规**。
2. **isAbsolute 检查**：Grep 同上，确认有 `path.isAbsolute()` 二次检查；缺失 → **BR-067-2 违规**。

## 与其他规则的关系

- 与 security-rule.md（API Key / 路径遍历）联动：本规则是其"路径遍历防护"的强化（白名单之后的二次兜底）。
- 与 BR-035（路径解析三级策略）联动：路径安全是路径解析正确性的前提。
- 与 security-rule / input-validation-rule 对应：本规则是路径穿越防护的后端审查视角（扩展，无新增 wiki-code-dev 编码规范）。
