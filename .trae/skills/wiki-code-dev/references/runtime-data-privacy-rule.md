# 运行时数据隐私规则（.gitignore / 持久化默认）

**代码**：CODING-RUNTIME-DATA-PRIVACY
**严重级别**：critical

## 问题（Problem）

`data/threads/`（含 `session.json` / `memory.json`，存储用户问答）未被加入 `.gitignore`，而其兄弟目录 `data/conversations/` 却已被忽略。结果用户隐私会话可能被误提交到仓库。

## 规则（Rule）

### R-1：每个新增磁盘运行时数据目录必须随兄弟目录一起 gitignore
新增任何 on-disk 运行时数据目录时，必须检查其所有 sibling 数据目录的 gitignore 状态，并把新目录加入 `.gitignore`（用 `git verify_command` 校验生效）。遗漏一个 sibling 即视为违规。

### R-2：持久化默认必须保守
- 会话（sessions）默认**不**在服务端落盘存储，除非显式开启；
- 任何默认开启的持久化都应视为隐私风险，需评审。

## 适用 / 不适用

- **适用**：新增 `data/*` 等运行时数据目录、会话/记忆持久化、`.gitignore` 维护。
- **不适用**：纯内存缓存（未落盘）、静态资源、公开文档。

## 检查清单
- [ ] 新增数据目录是否已被 `.gitignore` 覆盖（对照兄弟目录）
- [ ] 会话是否默认不在服务端存储
- [ ] 是否用 `git check-ignore -v` 验证忽略规则生效
