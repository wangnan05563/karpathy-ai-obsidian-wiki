# Rule Catalog — 配置合并保留

## Scope

- Covers: 后端保存配置到文件时必须保留其他段不动，仅覆盖目标段，避免整体覆盖导致其他模块配置丢失。
- 适用对象：所有分段配置文件（如 `config.json` 的 `tunnel` / `llm` / `server` / `engine` 段）的写盘逻辑。
- Does NOT cover: 全量覆盖的配置文件（如临时配置、缓存文件）；二进制配置文件；单段配置文件（无其他段需保留）。

> 所有配置文件路径、合并策略、保留段名列表均从 [config/review-config.md](../config/review-config.md) 的"配置合并保留参数"节读取，本规则文件不硬编码任何具体值。

## Rules

### CMP-1 保存配置时必须保留其他段，仅覆盖目标段

- Category: correctness
- Severity: critical
- Description: 分段配置文件（如 `config.json` 包含 `tunnel` / `llm` / `server` / `engine` 多段）的保存接口若直接 `writeFile(JSON.stringify(newConfig))` 整体覆盖，会把其他段的用户定制全部抹掉。典型场景：tunnel 配置页面保存 authtoken 时，若 `newConfig` 只含 tunnel 段，llm/server/engine 段全部丢失，用户对其他模块的定制化为乌有。必须读取原文件后按 `merge_strategy` 合并——默认 `shallow`：`{ ...original, [targetSection]: newSection }`；嵌套段用 `deep`：递归合并。`preserve_sections` 列表中的段必须出现在最终写入对象中且值与原文件一致，否则视为不通过。
- Judgment logic:
  1. 用 `Grep` 检索写盘逻辑（`fs.writeFile` / `fs.promises.writeFile`），定位配置文件写盘函数。
  2. 检查写盘前是否读取原文件（`fs.readFile` / `JSON.parse`），缺失即视为整体覆盖缺陷。
  3. 检查合并语句是否符合 `merge_strategy`：`shallow` 用对象展开 `{ ...original, [target]: newSection }`；`deep` 用递归合并工具（如 lodash `merge` / 自实现 deepMerge）。
  4. 验证 `preserve_sections` 列表中的段名在最终写入对象中存在，且值与原文件对应段一致（可通过读后回读对比）。
  5. 排除场景：若配置文件本身是单段（无其他段需保留）或临时文件（路径在 `exempt_paths`），跳过本规则。
- Applicable scenarios: 分段配置文件（`config.json` 含 `tunnel` / `llm` / `server` / `engine` 等多段）；多模块共享同一配置文件的场景；配置接口按模块独立保存（如 `PUT /api/tunnel/config` 只改 tunnel 段）。
- Not applicable: 全量覆盖的配置文件（如临时缓存、构建产物）；二进制配置文件；单段配置文件（无其他段需保留）；显式重置接口（如 `POST /api/reset-config` 整体回到默认值，由 [config-management-rule.md](config-management-rule.md) 的"配置恢复须仅重置目标字段"覆盖）。
- Configuration parameters: 见 [config/review-config.md](../config/review-config.md) 的"配置合并保留参数"节——`config_file_path` / `merge_strategy` / `preserve_sections` / `exempt_paths`。
- Suggested fix: 提供统一的 `mergeConfigSection(target: string, section: unknown): Promise<AppConfig>` 工具——内部读原文件、按 `merge_strategy` 合并、写回、返回完整配置；所有模块的保存接口统一调用此工具。
- Example:
  - Bad:
    ```typescript
    // PUT /api/tunnel/config —— 直接整体覆盖
    app.put('/api/tunnel/config', async (request, reply) => {
      const body = request.body as TunnelConfig;
      // newConfig 只含 tunnel 段，整体覆盖后 lll/server/engine 段全部丢失
      await fs.writeFile(CONFIG_PATH, JSON.stringify({ tunnel: body }));
      return reply.send({ ok: true });
    });
    ```
  - Good:
    ```typescript
    // 统一的段级合并工具
    async function mergeConfigSection(
      target: string,
      section: unknown
    ): Promise<AppConfig> {
      // 读原文件，按 merge_strategy 合并，仅覆盖目标段
      const raw = await fs.readFile(CONFIG_PATH, 'utf-8');
      const original = JSON.parse(raw) as AppConfig;
      const next = { ...original, [target]: section }; // shallow merge
      await fs.writeFile(CONFIG_PATH, JSON.stringify(next, null, 2));
      return next;
    }

    // PUT /api/tunnel/config —— 仅覆盖 tunnel 段，保留其他段
    app.put('/api/tunnel/config', async (request, reply) => {
      const body = request.body as TunnelConfig;
      const next = await mergeConfigSection('tunnel', body);
      // lll/server/engine 段保留原值，仅 tunnel 段被覆盖
      return reply.send({ ok: true, config: next });
    });
    ```
- Checklist:
  - [ ] 写盘前读取原文件，不存在时降级为"仅写目标段"或返回 500。
  - [ ] 合并策略符合 `merge_strategy`（`shallow` 用对象展开，`deep` 用递归合并）。
  - [ ] `preserve_sections` 列表中的段在写入对象中存在且值与原文件一致。
  - [ ] 多模块共享同一配置文件时，统一调用 `mergeConfigSection` 工具，避免各模块各自实现合并逻辑。
- Related rules: 配置恢复须仅重置目标字段见 [config-management-rule.md](config-management-rule.md)；写盘后刷新缓存见 [persistence-cache-rule.md](persistence-cache-rule.md) 的"PC-2 写盘函数必须立即刷新内存缓存"。
