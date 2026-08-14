# CODING-CONFIG-DRIVEN — 配置驱动与泛化（零硬编码元规则）

> 配套判断逻辑：**J-CONFIG-FIRST**（参数全配置、零硬编码、registry 泛化）。本规则是所有具体 CODING-* 规则的**上位元规则**：任何阈值 / 路径 / 端口 / 命名空间 / 攻击向量 / payload 模板 / 扫描范围，一律从配置读取，禁止在规则文件、技能脚本、业务代码中硬编码字面量。

## 问题背景（为什么需要这条元规则）

在多轮复盘（限流真实 IP、超时分级、压缩阈值、清洗正则、静态守卫 pattern、测试端点清单等）中反复出现同一类返工：

- 把 `30000` / `0.3` / `['application/json']` / `taskkill` / `1.5` 等**业务参数内联**进代码或规则文件，导致调优须改代码、换项目须 fork。
- 把「Karpathy-Wiki 特有路径 / 端口 / 表名」写死，使规则/技能**无法泛化**到其他业务场景。
- 规则文件硬编码严重级别文案或阈值，破坏「规则描述通用模式、具体值来自 config」的分层约定。

这些返工的共性不是某个具体缺陷，而是**缺乏"参数外置 + 泛化"的纪律**。故抽出本元规则，作为所有 CODING-* 的前置约束。

## 规则（Rule）

1. **参数全配置（J-CONFIG-FIRST）**：所有可变参数（超时、阈值、端口、路径锚点、正则、白名单、扫描目录、severity 文案、端点清单、payload 模板）集中在配置层（`coding-standards-config.md` / `review-config.md` / `defaults.yaml` / `config.yaml` / 各 `examples/*.example.yaml`），代码与规则文件只读取、不内联。
2. **禁止硬编码字面量**：业务代码中禁止出现裸 `30000`、`'application/json'`、`'/api'` 等可通过配置表达的值；规则文件中禁止硬编码严重级别文案或具体阈值数字。
3. **泛化而非特判（registry 模式）**：新增一类规范 = 在配置里加一组（如 `groups[]` 的一项 `{name, patterns, severity, rule_ref}`），**引擎/主流程代码不动**；用 registry + 配置遍历替代 `if (kind === 'x')` 特判。
4. **配置分层清晰**：默认值（`defaults.yaml`）+ 项目覆盖（`config.yaml`）+ 示例（`examples/*.example.yaml`）三层；改项目只动覆盖层，不碰默认值与引擎。
5. **参数命名语义化**：配置键用 `kind_timeout_ms` / `margin_multiplier` / `scan_dirs` / `file_glob` 等自解释命名，避免 `param1` / `opt2` 之类无意义键。
6. **跨技能一致**：同一参数在三技能（wiki-code-dev / wiki-frontend-code-review / wiki-backend-code-review / wiki-auto-testing）的 config 中命名与含义一致，编号（BR-/FR-/CODING-）顺延不漂移。

## 正例（Good）

```ts
// 超时从配置读取，多层递增 × margin_multiplier
const t = cfg.edgeTtsTimeoutMs;                 // 来自 config，非 30000 字面量
const outer = t * cfg.timeout.margin_multiplier; // 1.5，来自 config

// 压缩阈值 / 白名单 content-type 全部来自 config
if (payload.length >= cfg.compress.minBytes && cfg.compress.whitelist.includes(contentType)) { ... }

// 静态守卫：新规范 = 加一组配置，引擎不变
groups.push({ name: 'process_cleanup_safe', patterns: ['taskkill'], severity: 'warn', rule_ref: 'BR-093' });
```

```yaml
# defaults.yaml（默认值层）
timeout:
  edge_tts_ms: 30000
  margin_multiplier: 1.5
compress:
  min_bytes: 1024
  level: 0.3
  whitelist: ["application/json"]
scan_dirs: ["karpathy-wiki/api/src"]
file_glob: "*.ts"
```

## 误例（Bad）

```ts
// ❌ 硬编码超时字面量，调优须改代码
const t = 30000;
setTimeout(fn, t);

// ❌ 硬编码 content-type 白名单，换项目须改代码
if (contentType === 'application/json') { ... }

// ❌ 规则文件内联严重级别与具体数值（破坏分层）
// BR-XXX: 压缩最小字节数 1024 为严重问题   ← 应来自 config.compress.min_bytes + severity 参数
```

```yaml
# ❌ 把项目特有路径写死进引擎默认值，无法泛化
scan_dirs: ["D:/code/otherProjects/19_Karpathy-AI+Obsidian知识库/karpathy-wiki/api/src"]
```

## 适用与不适用（Applicability）

- **适用**：任何可变参数（超时/阈值/端口/路径/正则/白名单/severity/payload/扫描范围）；需要跨项目复用的规则与技能；CI / 多业务场景泛化。
- **不适用**：编译期真常量（如数学常数 `Math.PI`、协议固定枚举值 `['GET','POST']` 这类**不会随部署变化**的协议级固定集合，可内联但建议仍进 config 以便审计）；纯算法内部临时变量（非对外可配置项）。**注意**：`['GET','POST']` 等若未来可能因协议扩展变化，仍建议配置化。

## 对应 config 参数（Parameter Mapping）

| 参数 | 所在配置 | 说明 |
|------|---------|------|
| `timeout.*` / `margin_multiplier` | coding-standards-config.md / review-config.md / defaults.yaml | 超时键与递增倍数，禁硬编码字面量 |
| `compress.*` | review-config.md（BR-091-2） | 压缩阈值/级别/白名单，禁硬编码 |
| `scan_dirs` / `file_glob` / `groups[]` | defaults.yaml / config.yaml（wiki-auto-testing `backend_review_static_check`） | 静态守卫扫描范围与规范组，全配置化 |
| `severity_*` | review-config.md（每条 BR-/FR- 的 severity 参数） | 严重级别文案与阻断策略，禁规则文件内联 |
| `auth.*` / `service.*` / `api_tests.endpoints` | config.yaml（wiki-auto-testing） | 地址/端口/端点清单，全参数化 |

## 审查要点（Review Hooks）

- 前端 / 后端评审须把「配置可移植性 / 硬编码阈值 / 非泛化特判」作为独立扫描维度（见 wiki-frontend-code-review / wiki-backend-code-review 的「配置化与泛化审查」Quick-Check 段）。
- 命中硬编码字面量（超时/路径/端口/阈值）→ 建议改为配置键引用。
- 命中 `if (kind === 'x')` 式特判且可 registry 化 → 建议改为配置组遍历。
