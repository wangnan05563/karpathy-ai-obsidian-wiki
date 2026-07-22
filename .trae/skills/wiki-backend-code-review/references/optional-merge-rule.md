# 配置字段 optional 合并非空断言（BR-028）

> 复盘来源：配置合并函数中使用 `!` 后缀非空断言或 `as` 强转绕过 TS 类型检查，当可选字段实际为 `undefined` 时运行时抛 `Cannot read properties of undefined` 或写入 `undefined` 到配置文件，破坏配置完整性。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"optional_merge"章节读取，禁止在本规则文件硬编码具体字段名或合并函数名。

## Trigger Keywords
updateConfig, merge, optional, ??, !, non-null assertion, as, mergeConfig, mergeConfigSection, shallow merge, deep merge, Partial<T>, config spread

## Rules

### BR-028-1: 合并可选配置字段时禁止用 `!` 后缀断言

- **Severity**: suggestion
- **Description**: 在配置合并函数（如 `updateConfig` / `mergeConfigSection`）中访问可选字段（类型为 `T | undefined`）时，禁止用 `field!` 后缀断言绕过 TS 检查。`!` 断言仅在编译期消除告警，运行时若字段为 `undefined` 仍会传递 `undefined` 给下游或抛错——典型后果是 `undefined` 被序列化写入配置文件，下次读取时 `JSON.parse` 虽不报错但字段语义错误（如 `port: undefined` 被写为缺失字段，运行时退回默认值）。必须用 `??` 默认值或 `if` 守卫显式处理 `undefined` 分支。
- **Suggested fix**:
```typescript
// 配置合并：可选字段用 ?? 提供默认值
interface AiConfig {
  provider?: string;
  baseUrl?: string;
  model?: string;
  timeout?: number;
}

function mergeAiConfig(partial: Partial<AiConfig>, base: AiConfig): AiConfig {
  return {
    provider: partial.provider ?? base.provider,
    baseUrl: partial.baseUrl ?? base.baseUrl,
    model: partial.model ?? base.model,
    // 数值字段必须显式默认值，禁止 undefined 透传
    timeout: partial.timeout ?? base.timeout ?? 30000,
  };
}
```

### BR-028-2: 合并可选配置字段时禁止用 `as` 强转绕过类型检查

- **Severity**: suggestion
- **Description**: 配置合并函数中禁止用 `as` 强转将 `T | undefined` 断言为 `T`（如 `partial.field as string`）。`as` 同样仅编译期生效，运行时 `undefined` 仍会传递，且比 `!` 更隐蔽——`as` 可能让 TS 推断出更宽的类型签名，让下游代码"看起来"类型安全实则运行时崩。必须用类型守卫（`if (typeof x === 'string')`）、`??` 默认值或显式 `if (x === undefined)` 分支处理。
- **Suggested fix**:
```typescript
// 错误：as 强转绕过类型检查
function mergeTunnelConfig(partial: Partial<TunnelConfig>, base: TunnelConfig): TunnelConfig {
  return {
    ...base,
    // ❌ as string 强转，partial.authtoken 可能是 undefined
    authtoken: partial.authtoken as string,
  };
}

// 正确：用 ?? 或类型守卫
function mergeTunnelConfig(partial: Partial<TunnelConfig>, base: TunnelConfig): TunnelConfig {
  return {
    ...base,
    // 用 ?? 提供回退值
    authtoken: partial.authtoken ?? base.authtoken,
  };
}

// 或用类型守卫显式处理 undefined 分支
function mergeTunnelConfigGuarded(
  partial: Partial<TunnelConfig>,
  base: TunnelConfig,
): TunnelConfig {
  const next: TunnelConfig = { ...base };
  if (typeof partial.authtoken === 'string' && partial.authtoken.length > 0) {
    next.authtoken = partial.authtoken;
  }
  if (typeof partial.port === 'number' && Number.isFinite(partial.port)) {
    next.port = partial.port;
  }
  return next;
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `optional_merge.enabled` | `true` | 是否启用本规则 |
| `optional_merge.severity` | `suggestion` | 违规严重级别 |
| `optional_merge.config_merge_function_patterns` | `updateConfig,mergeConfig,mergeConfigSection,saveAiConfig,saveConfig` | 配置合并函数名匹配模式（逗号分隔，正则字面量） |
| `optional_merge.forbidden_assertion_operators` | `!,as` | 禁用的断言操作符（逗号分隔） |
| `optional_merge.recommended_operators` | `??,if guard,typeof guard` | 推荐的替代写法 |
| `optional_merge.scan_scope_glob` | `api/src/**/*.ts` | 扫描范围（glob 模式） |
| `optional_merge.allow_as_in_migration` | `false` | 迁移期代码是否允许 `as` 强转（临时豁免） |

## 检查方式

1. 用 Grep 检索 `optional_merge.scan_scope_glob` 下所有 `.ts` 文件，匹配 `optional_merge.config_merge_function_patterns` 中的函数名定义（如 `function\s+(updateConfig|mergeConfig|mergeConfigSection)`）。
2. 在匹配函数体内，用 Grep 检索 `!\.`（非空断言后缀访问）和 `as\s+\w+`（as 强转）。
3. 排除场景：
   - 函数签名中 `as` 用于类型 narrowing 且目标类型是源类型的超集（如 `as const`）
   - `optional_merge.allow_as_in_migration` 为 `true` 且文件路径在迁移目录下
   - 第三方库类型不完整时的临时 `as` 强转（须有 `// FIXME: 移除第三方库类型修复后删除` 注释）
4. 对剩余命中项，检查是否提供了 `??` 默认值或 `if` 守卫替代路径：
   - 命中 `!` 且无 `??` 替代 → BR-028-1 违规
   - 命中 `as T` 且无类型守卫 → BR-028-2 违规

## 正确示例

```typescript
// 配置合并：可选字段全部用 ?? 或 if 守卫
interface ServerConfig {
  host?: string;
  port?: number;
  timeout?: number;
}

const DEFAULT_SERVER_CONFIG: Required<ServerConfig> = {
  host: '127.0.0.1',
  port: 3000,
  timeout: 30000,
};

function mergeServerConfig(partial: Partial<ServerConfig> = {}): Required<ServerConfig> {
  return {
    // 用 ?? 提供默认值，处理 undefined 分支
    host: partial.host ?? DEFAULT_SERVER_CONFIG.host,
    port: partial.port ?? DEFAULT_SERVER_CONFIG.port,
    timeout: partial.timeout ?? DEFAULT_SERVER_CONFIG.timeout,
  };
}

// 复杂场景：用 if 守卫显式校验类型
function mergeAiConfig(
  partial: Partial<AiConfig>,
  base: AiConfig,
): AiConfig {
  const next: AiConfig = { ...base };
  if (typeof partial.provider === 'string' && partial.provider.length > 0) {
    next.provider = partial.provider;
  }
  if (typeof partial.apiKey === 'string' && partial.apiKey.length > 0) {
    next.apiKey = partial.apiKey;
  }
  if (typeof partial.timeout === 'number' && Number.isFinite(partial.timeout)) {
    next.timeout = partial.timeout;
  }
  return next;
}
```

## 错误示例

```typescript
// 错误 1：用 ! 后缀断言绕过 undefined 检查
function mergeServerConfig(partial: Partial<ServerConfig>): Required<ServerConfig> {
  return {
    // ❌ partial.host! 断言，运行时仍可能是 undefined
    host: partial.host!,
    port: partial.port!,
    timeout: partial.timeout!,
  };
}

// 错误 2：用 as 强转把可选断言为必填
function mergeAiConfig(partial: Partial<AiConfig>): AiConfig {
  return {
    // ❌ as string 强转，partial.provider 可能是 undefined
    provider: partial.provider as string,
    apiKey: partial.apiKey as string,
    timeout: partial.timeout as number,
  };
}

// 错误 3：对象展开后用 ! 访问可选字段
function mergeTunnelConfig(partial: Partial<TunnelConfig>): TunnelConfig {
  const merged = { ...DEFAULT_TUNNEL, ...partial };
  // ❌ merged.authtoken! 断言，若 partial.authtoken 显式传 undefined 会被展开覆盖
  return {
    ...merged,
    authtoken: merged.authtoken!,
  };
}
```

## 适配新项目

- **Express 项目**：配置合并函数签名不变，`config_merge_function_patterns` 调整为项目实际函数名（如 `loadConfig, mergeEnv`），其余规则不变。
- **NestJS 项目**：配置通过 `@Injectable()` ConfigService 管理，`config_merge_function_patterns` 调整为 `set,databaseOptions,mergeConfig`，扫描范围改为 `src/config/**/*.ts`；NestJS 的 `@nestjs/config` 已用 `??` 模式可作正面参考。
- **Koa 项目**：与 Express 相同，调整函数名匹配模式即可。
- **zod / joi 校验项目**：若配置合并前已用 schema 校验（`schema.parse(partial)`），校验后的对象类型已收敛为必填，本规则可对校验后代码豁免——在 `allow_as_in_migration` 设为 `true` 并加注释说明已通过 schema 校验。
- **迁移期项目**：若正在从 JS 迁移到 TS，可在 `allow_as_in_migration` 设为 `true` 临时豁免 `as` 强转，但要求每个 `as` 都带 `// FIXME` 注释标记迁移完成后清理。
