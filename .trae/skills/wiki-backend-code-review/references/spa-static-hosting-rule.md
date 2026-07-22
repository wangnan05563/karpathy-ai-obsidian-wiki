# SPA 静态资源托管规则

> 基于单端口部署（前端构建产物输出到后端 public 目录）复盘提炼，防止后端未正确托管 SPA 静态资源导致 404、JS bundle 加载失败等问题。

## 触发场景

- 评审涉及 `api/src/index.ts` 或入口文件中的静态资源托管逻辑
- 评审涉及 `@fastify/static` / `express.static` 等静态资源中间件
- 评审涉及 SPA fallback（所有未匹配路由返回 index.html）
- 评审涉及 vite 构建产物输出目录配置

## 规则

### SH-1：SPA 静态资源托管必须实现多候选路径探测

后端入口文件托管 SPA 静态资源时，必须实现多候选路径探测逻辑，覆盖开发模式、打包模式、CWD 漂移等场景：

```typescript
// 合规示例：多候选路径探测
const spaCandidates = [
  path.resolve(process.cwd(), 'public'),
  path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../public'),
  path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../static/spa'),
];
const spaRoot = spaCandidates.find(p => fs.existsSync(path.join(p, 'index.html')));
if (!spaRoot) {
  app.log.warn('SPA 静态资源目录未找到，前端页面不可用');
}
```

**违规示例**：仅依赖 `process.cwd()` 作为唯一路径锚点（CWD 受启动方式影响会漂移）。

### SH-2：构建产物必须输出到后端 public 目录

vite.config.ts / webpack.config.js 必须配置 `outDir` 指向后端 public 目录，实现单端口部署：

```typescript
// vite.config.ts 合规示例
export default defineConfig({
  build: {
    outDir: '../api/public',  // 输出到后端 public 目录
    emptyOutDir: true,        // 构建前清空目录，避免残留旧产物
  },
});
```

**违规示例**：输出到默认 `dist/` 目录，需要额外配置静态资源服务器。

### SH-3：必须配置 emptyOutDir 避免残留旧产物

构建脚本必须配置 `emptyOutDir: true`，避免旧 hash 文件名的产物残留导致后端加载到过期 bundle：

```typescript
// 合规示例
build: {
  outDir: '../api/public',
  emptyOutDir: true,
}
```

**违规示例**：未配置 `emptyOutDir`，旧 `index-oldHash.js` 残留，后端可能加载到过期版本。

### SH-4：后端 watch 模式重新构建后必须重启

`tsx watch` / `nodemon` 在 vite 重新构建后（特别是 hash 文件名变化时），可能未自动加载新产物，导致返回 404。评审时确认：
- vite 构建完成后，后端必须重启（通过端口反查 PID + Stop-Process + 重新启动）
- 重启后必须轮询端口进入 Listen 状态
- 必须验证健康检查端点返回 200

### SH-5：SPA fallback 必须返回 index.html

SPA 路由的所有未匹配路径（如 `/dashboard`、`/config`）必须 fallback 到 `index.html`，由前端路由处理：

```typescript
// 合规示例（Fastify）
app.setNotFoundHandler((request, reply) => {
  if (request.url.startsWith('/api/') || request.url.startsWith('/assets/')) {
    return reply.code(404).send({ error: 'Not Found' });
  }
  return reply.sendFile('index.html');
});
```

**违规示例**：所有 404 都返回 JSON 错误响应，导致前端路由刷新页面时显示 `{"error":"Not Found"}`。

## 检测方法

1. 扫描入口文件 `index.ts`，检查是否有 `@fastify/static` / `express.static` 注册
2. 验证静态资源路径解析是否实现多候选路径探测（至少 2 个候选路径）
3. 扫描 `vite.config.ts` / `webpack.config.js`，验证 `outDir` 是否指向后端 public 目录
4. 验证 `emptyOutDir` 是否为 `true`
5. 扫描 `setNotFoundHandler` / 404 处理逻辑，验证 SPA fallback 是否返回 index.html
6. 验证 `/api/*` 路径不触发 SPA fallback（避免 API 404 返回 HTML）

## 配置参数

所有参数见 [config/review-config.md](../config/review-config.md) 的"SPA 静态资源托管审查参数"段。

## 适配说明

- 多端口部署（前后端分离）：`enabled` 设为 `false`，前端由 nginx/CDN 托管
- SSR 应用：本规则不适用，SSR 无静态 bundle
- Next.js / Nuxt.js：由框架自动处理，`enabled` 设为 `false`
