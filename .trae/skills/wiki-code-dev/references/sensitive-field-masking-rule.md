# Sensitive Field Masking Rule

## 触发关键词

token, secret, password, authtoken, API Key, apiKey, GET, /config, 脱敏, masked, configured, 明文, 敏感字段

## 规则描述

### SFM-1：GET 接口返回敏感字段必须脱敏

**严重级别**：critical

GET 配置类接口返回的字段名匹配 `sensitive_field_patterns`（默认 `key|token|secret|password|authtoken`，不区分大小写）时，必须以脱敏后的字符串返回，并附带 `configured` 布尔标志表示该字段是否已配置。禁止原样返回明文。

**为什么**：浏览器 DevTools 的 Network 面板、日志采集器、CDN 边缘日志、错误上报系统都会记录响应体。明文 token 一旦泄露，攻击者可在 token 失效前完全冒用用户身份。脱敏后前端仍能通过 `configured` 标志判断"是否已设置"，不影响 UI 显示。

### SFM-2：POST 更新时空串等于"不修改"

**严重级别**：critical

POST / PUT 更新配置接口中，敏感字段若传入空串 `""`，必须解释为"不修改原值"，禁止解释为"清空"。前端表单只显示脱敏占位符，用户不修改时提交空串。

**为什么**：前端无法获取敏感字段的原值（已被脱敏），只能提交空串表示"不修改"。若后端把空串当作清空，用户每次保存其他字段都会把 token 清掉，导致配置丢失。

## 判断逻辑

```
1. 识别接口性质：路由方法为 GET 且 path 形如 /config /settings /profile → 进入敏感字段检查
2. 遍历响应体字段名，匹配 sensitive_field_patterns（默认 key|token|secret|password|authtoken，大小写不敏感）
3. 匹配到的字段：
   - 已配置（原值非空）→ 返回 mask 后的字符串 + configured: true
   - 未配置（原值为空 / undefined）→ 返回空串 + configured: false
4. POST / PUT 同接口的写入分支：
   - 字段值为空串 → 跳过更新（保留原值）
   - 字段值为非空字符串 → 更新为新值
   - 字段值为 null / undefined → 不修改（与空串等价处理）
5. mask_strategy（默认 '末4位+padStart'）：
   - 原值长度 ≤ 4：返回全 '*' 的等长字符串
   - 原值长度 > 4：保留末 4 位，前面用 '*' padStart 到原长度
```

## 适用场景

- 用户配置类接口（API Key / authtoken / OAuth secret）
- 系统凭证管理（数据库密码 / SMTP 密码 / 第三方 SDK Key）
- 用户个人信息接口（密码 / 安全问题答案 / 二次验证密钥）
- 任何字段名匹配 `sensitive_field_patterns` 的 GET 响应

## 不适用场景

- 非敏感公开字段（用户名 / 邮箱 / 显示名 / 头像 URL）
- 后端内部服务间调用（service-to-service，无前端展示需求）
- 调试日志输出（属于日志脱敏范畴，由 logging 规则覆盖）
- 一次性签发的临时令牌（如 OAuth code，本身设计为短期使用）

## 配置参数

> 所有参数从 `config/coding-standards-config.md` 的 `sensitive_field_masking` 段读取。

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `sensitive_field_patterns` | `key\|token\|secret\|password\|authtoken` | 敏感字段名匹配模式（正则，大小写不敏感） |
| `mask_strategy` | `last4-padstart` | 脱敏策略：保留末 4 位 + 前置 `*` padStart 到原长 |
| `mask_char` | `*` | 脱敏占位字符 |
| `mask_visible_suffix` | `4` | 末尾保留可见字符数 |
| `min_mask_length` | `4` | 原值长度 ≤ 此值时全部脱敏（不保留末尾） |
| `empty_value_semantics` | `no-change` | POST 空串语义：`no-change`（不修改）/ `clear`（清空） |

## 示例

### 错误示例

```typescript
// GET /api/config
app.get('/api/config', async (req, res) => {
  const config = await loadConfig();
  // ❌ 直接返回明文 token
  return res.send({
    apiUrl: config.apiUrl,
    authToken: config.authToken,  // 明文泄露
    openaiKey: config.openaiKey,  // 明文泄露
  });
});

// POST /api/config
app.post('/api/config', async (req, res) => {
  const updates = req.body;
  // ❌ 空串被当作清空，用户保存其他字段时 token 被意外清掉
  await saveConfig({
    apiUrl: updates.apiUrl,
    authToken: updates.authToken,
    openaiKey: updates.openaiKey,
  });
  return res.send({ ok: true });
});
```

### 正确示例

```typescript
import { maskSensitive, pickDefinedSensitive } from './sensitive-utils.js';

// GET /api/config
app.get('/api/config', async (req, res) => {
  const config = await loadConfig();
  // ✅ 敏感字段脱敏 + configured 标志
  return res.send({
    apiUrl: config.apiUrl,
    authToken: {
      value: maskSensitive(config.authToken),  // "********abcd"
      configured: Boolean(config.authToken),
    },
    openaiKey: {
      value: maskSensitive(config.openaiKey),
      configured: Boolean(config.openaiKey),
    },
  });
});

// POST /api/config
app.post('/api/config', async (req, res) => {
  const updates = req.body;
  const patch: Record<string, string> = {};
  // ✅ 空串 / undefined / null 都视为"不修改"
  if (updates.apiUrl !== undefined && updates.apiUrl !== '') {
    patch.apiUrl = updates.apiUrl;
  }
  // 敏感字段单独处理：仅当用户填写新值时才更新
  for (const field of ['authToken', 'openaiKey']) {
    const v = updates[field];
    if (typeof v === 'string' && v.length > 0) {
      patch[field] = v;
    }
  }
  await saveConfig(patch);
  return res.send({ ok: true });
});
```

### 脱敏工具函数

```typescript
// mask_strategy、mask_char、mask_visible_suffix、min_mask_length 由 config 提供
export function maskSensitive(
  value: string | undefined,
  opts: { char: string; visibleSuffix: number; minMaskLength: number }
): string {
  if (!value) return '';
  if (value.length <= opts.minMaskLength) {
    return opts.char.repeat(value.length);
  }
  const suffix = value.slice(-opts.visibleSuffix);
  return suffix.padStart(value.length, opts.char);
}
```

## 检查清单

- [ ] GET 接口响应中字段名匹配敏感模式时是否脱敏
- [ ] 脱敏后是否附带 `configured` 布尔标志
- [ ] POST / PUT 接口中空串是否被解释为"不修改"
- [ ] POST / PUT 接口中 undefined / null 是否被解释为"不修改"
- [ ] 脱敏策略是否从 config 读取（不硬编码）
- [ ] 是否避免在日志 / 错误上报中输出敏感字段原值
