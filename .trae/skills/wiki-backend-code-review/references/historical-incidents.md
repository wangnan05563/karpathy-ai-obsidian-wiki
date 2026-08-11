# 历史事故覆盖（完整记录）

> 从 SKILL.md 拆分而来。每条规则对应一次或多次历史复盘，记录了事故编号、现象和提炼出的审查规则。

## 复盘来源总表

| 规则编号 | 事故编号 | 复盘来源 | 现象摘要 |
|---|---|---|---|
| BR-034~037 | CODING-041~046 | 主题色变量映射 | 前端硬编码 rgba() 颜色在浅色主题下辨识度低，后端同理存在硬编码 API Key/port/path/timeout 问题 |
| BR-048~049 | CODING-054 | Skill 导入模块开发 | `/api/auth/me` 误放入 publicPaths 导致 RBAC 401 |
| BR-050~051 | CODING-055 | Skill 导入模块开发 | deleteSkill 用 fs.rm 静默失败导致目录残留 |
| BR-052 | PL-1~5 | MCP 并行加载和超时阈值问题 | MCP 工具串行加载 2×30s=60s 触发前端 60s 超时，AI 回复被丢弃 |
| BR-053 | TC-1~5 | MCP 并行加载和超时阈值问题 | 多层调用链超时未自下而上递增覆盖，前端 60s = 后端 60s 无余量导致回复被丢弃 |
| BR-054 | CODING-056 | v3 媒体生成工具开发 | Node.js 原生 fetch 网络失败只抛 TypeError("fetch failed")，真因藏在 err.cause.code 里；Go 后端要求 seconds 字段为 string 类型 |
| BR-055 | CODING-057 | v3 媒体生成工具开发 | 五类操作（任务创建/轮询/图像生成/视频下载/LLM）耗时差异巨大，统一用一个超时值导致短任务等待过久或长任务误判超时 |
| BR-056 | CODING-058 | v3 媒体生成工具开发 | Agnes API key 可能配在三个位置（专用段/共享段/环境变量），只查一个位置会导致历史配置不兼容 |
| BR-057 | CODING-059 | v3 媒体生成工具开发 | 视频生成需数分钟超出 query SSE 流 60 秒超时，改用独立 JSON 端点 + 前端轮询 |
| BR-058 | CODING-060 | v3 媒体生成工具开发 | 归档文件 frontmatter 字段散乱导致前端解析需多种 fallback，统一为 type/output_mode/generated_at 三必备字段 |
| BR-059 | CODING-061 | v3 媒体生成工具开发 | 内存 Map 无限增长导致内存溢出，前端归档接口接收客户端传内容存在篡改风险 |
| BR-060 | CODING-063 | v3 媒体生成工具开发 | SSE 后端事件分发用 if/else 链新增事件需修改 else 分支，前端认知复杂度 > 15，改用对象映射表 |
| BR-038~047 | — | Tauri 2.x 桌面应用集成 | Tauri 2.x 桌面应用集成历史问题复盘提炼（构建脚本、capability 配置、PowerShell stderr 处理） |
| BR-061 | CODING-059 | PowerShell 长时进程管道陷阱 | PowerShell 中运行 vue-tsc/orchestrator.py 等长时进程时，管道导致 EPIPE broken pipe 错误（退出码 -1） |
| BR-062 | CODING-060 | 功能回滚最小化 | 恢复已删除代码时，按删除反向顺序用 Edit 精准替换，禁止 Write 重写整个文件 |
| BR-089 | CODING-ROUTE-RETURN-COMPLETENESS | 登录路由漏 return 双发响应 | auth.ts 登录路由某分支漏 return，Fastify 隐式再发响应导致前端登录异常/超时 |
| BR-090 | CODING-RESPONSE-HOOK-SAFE | compression onSend 钩子挂死 | compression.ts 的 onSend 钩子未 fail-open，异常/阻塞使所有 API 全部挂死 |
| BR-091 | CODING-COMPRESSION-DEFAULT-OFF | 压缩默认注册致钩子挂死 | @fastify/compress 默认注册且 enable 被忽略，onSend 异常挂死所有 API |
| BR-092 | CODING-USER-STORE-INIT | users.json 空壳致登录失败 | data/users.json 落成 0 字节，loadUsers JSON.parse 抛错未兜底 → 登录失败无告警 |

## 事故编号含义

- **CODING-xxx**：对应 wiki-code-dev 编码规范中的编号
- **PL-x**：Parallel Loading（并行加载）问题编号
- **TC-x**：Timeout Chain（超时链）问题编号
