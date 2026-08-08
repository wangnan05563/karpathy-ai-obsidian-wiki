# SPA 实时部署解析规则

> 基于单端口部署（前端构建产物输出到后端 public 目录、按时间戳切换最新部署、静态资源服务须防路径穿越）复盘提炼。
> 本规则是 [references/spa-static-hosting-rule.md](spa-static-hosting-rule.md)（SH-1~SH-5）的**实时部署扩展**：SH-1 解决"多候选路径探测"，本规则解决"候选之一是带时间戳的部署目录时，如何选最新且完整的一份、并防止半写入目录与路径穿越"。
> 所有阈值 / 目录命名 / 正则 / 严重级别一律从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `spa_live_deploy.*` 读取，规则文件只描述模式。

## 触发场景

- 评审 `api/src/index.ts` 或入口文件中 SPA 静态资源托管目录（`spaRoot` / `spaCandidates`）的解析逻辑
- 评审 `/wiki/*`（或等价静态资源前缀）的 `sendFile` / 资源定位逻辑是否防穿越
- 评审部署脚本（如 `_deploy_live.mjs`）是否把构建产物写入全新目录、是否产出完整性标记
- 评审"修改前端后是否需要重启后端"的闭环（spaRoot 在启动时计算一次）

## 规则

### CODING-SPA-LIVE-DEPLOY-1：托管根目录必须从候选中选「最新且完整」的时间戳部署目录

当部署采用"每次构建写入全新 `public_live_<ts>` 目录、后端动态选最新"的模式时，入口文件必须从候选列表中选出**数值时间戳最大**且**通过完整性门禁**的目录作为 `spaRoot`：

```typescript
// 合规示例：按时间戳选最新 + 完整性门禁
const livePattern = spa_live_deploy.live_dir_pattern; // 如 'public_live_'
async function resolveSpaRoot(): Promise<string> {
  const base = path.resolve(process.cwd(), spa_live_deploy.public_base_dir); // 如 'api'
  const entries = (await fs.readdir(base)).filter(
    (n) => n.startsWith(livePattern) && !n.includes(spa_live_deploy.quarantine_keyword),
  );
  const candidates = entries
    .map((n) => ({ name: n, ts: Number(n.slice(livePattern.length)) }))
    .filter((e) => Number.isFinite(e.ts))
    .sort((a, b) => b.ts - a.ts); // 数值降序，最新在前
  for (const c of candidates) {
    const dir = path.join(base, c.name);
    if (await isDeployComplete(dir)) return dir; // 完整性门禁：index.html + 完成标记
  }
  // 兜底：legacy 固定目录（如 api/public）
  const legacy = path.join(base, spa_live_deploy.legacy_dir);
  return (await isDeployComplete(legacy)) ? legacy : '';
}
```

**违规示例**：`spaCandidates.find(p => existsSync(join(p, 'index.html')))` 仅取"第一个存在 index.html 的候选"——当并存多个 `public_live_<ts>` 目录时，顺序不确定，可能选到旧目录或尚未写完整的半写入目录。

### CODING-SPA-LIVE-DEPLOY-2：选定部署目录前必须做完整性门禁

半写入目录（构建进行中、仅部分文件落地）一旦被选中托管，会导致页面 404 / JS 加载一半 / 白屏。完整性门禁须同时校验：

```typescript
// 合规示例：index.html 存在 + 部署完成标记文件存在
async function isDeployComplete(dir: string): Promise<boolean> {
  const indexOk = await existsSafe(path.join(dir, spa_live_deploy.index_file)); // index.html
  const markerOk = await existsSafe(path.join(dir, spa_live_deploy.complete_marker)); // 如 .deploy-complete
  return indexOk && markerOk;
}
```

**违规示例**：仅靠 `existsSync(index.html)` 判定——构建工具往往先写出 `index.html` 再写 hash bundle，存在 `index.html` 不等于产物完整。

### CODING-SPA-LIVE-DEPLOY-3：静态资源解析必须 normalize + within-root 防穿越

`/wiki/*` 等静态资源前缀下的请求路径必须规范化，并以 `spaRoot` 为根做"是否逃逸出根"的二次校验，与泛型路径穿越防护（security-rule / BR-067）同一防御纵深：

```typescript
// 合规示例：normalize + within-root
function resolveSpaAsset(root: string, reqPath: string): string | null {
  const rel = path.normalize(reqPath);               // 消去 /./ 与 /../ 等
  const abs = path.resolve(root, '.' + rel);          // 锚定于 spaRoot
  const escaped = path.relative(root, abs);           // 若以 .. 开头即逃逸
  if (escaped.startsWith('..') || path.isAbsolute(escaped)) return null;
  return abs;
}
```

**违规示例**：直接 `path.join(spaRoot, reqPath)` 后 `sendFile`——`reqPath` 含 `../` 可读取 `spaRoot` 之外任意文件（如 `../../api/data/...`）。

### CODING-SPA-LIVE-DEPLOY-4：部署须写入全新目录、不覆盖已存在目录；切换须重启后端

- 部署脚本把构建产物写入**全新时间戳目录**（`public_live_<Date.now()>`），整目录 create + write，绝不 rename/覆盖已存在的 `public_live_*` 或 legacy 目录（规避 safe-delete 钩子的 overwrite 拦截，也避免清空正在服务的目录）。
- `spaRoot` 在后端**启动时计算一次**：写完新目录后**必须重启后端**才能切到最新目录；仅改前端产物、不重启后端不会生效。
- 旧目录保留作降级兜底（新目录完整性校验失败时回退 legacy），由定时/人工清理，清理也走"新建隔离目录 → 移动"而非原地 rm。

**违规示例**：`vite build --outDir ../api/public` 直接覆盖固定目录——既触发 safe-delete 钩子拦截，又会清空正在服务的目录导致瞬时 404。

## 检测方法

1. 扫描入口文件 `index.ts`，定位 `spaRoot` / `spaCandidates` 解析函数。
2. 若存在带时间戳的部署目录候选，确认是否按**数值时间戳降序**选取 + **完整性门禁**（index.html + 完成标记）。
3. 扫描 `/wiki/*`（或等价前缀）资源定位逻辑，确认 `path.normalize` + `path.relative(root,...)` 的 within-root 逃逸拦截（逃逸即拒绝）。
4. 扫描部署脚本，确认写入**全新**时间戳目录、不覆盖已存在目录、写完要求后端重启。
5. 确认 legacy 固定目录仅作兜底，且同样走完整性门禁。

## 配置参数

所有参数见 [config/coding-standards-config.md](../config/coding-standards-config.md) 的"SPA 实时部署"段（`spa_live_deploy.*`）。

## 适配说明

- 固定单目录部署（无时间戳切换）：本规则降级为 SH-1~SH-5 的"多候选路径探测"，无需时间戳排序与完整性门禁。
- 多后端实例 / 容器挂载：各实例须各自独立解析 spaRoot；共享存储场景下时间戳目录须保证原子可见性（`isDeployComplete` 标记文件最后写）。
- SSR 应用：本规则不适用（无静态 bundle 目录）。
